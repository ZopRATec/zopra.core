from importlib import import_module
from time import strftime
from time import strptime
from zopra.core.types import DictType
from zopra.core.types import IntType
from zopra.core.types import ListType
from zopra.core.types import StringType

from zopra.core import ZC
from zopra.core import SimpleItem


# date mapping for convertDate
format_list = [
    "%d-%m-%y",
    "%d-%m-%Y",
    "%d.%m.%y",
    "%d.%m.%Y",
    "%d %m %y",
    "%d %m %Y",
    "%d/%m/%y",
    "%d/%m/%Y",
    "%m.%y",
    "%m.%Y",
    "%m/%d/%y",
    "%m/%d/%Y",
    "%d\\%m\\%y",
    "%d\\%m\\%Y",
]


# dict of available connector classes and the corresponding db name (see DBInfo)
connectors = {
    "Psycopg": "PostgresConnector",
    "Psycopg2": "PostgresConnector",
    "PyGreSQL": "PostgresConnector",
    "PoPy": "PostgresConnector",
    "MySQL": "MySqlConnector",
}

# fallback on meta_type
connectors_by_meta_type = {
    "Z MySQL Database Connection": "MySqlConnector",
}


def getConnector(context, connector_id, connection_id):
    """This method creates and returns a new connector object for the available
    connection by choosing the appropriate connector class based on the
    database_type attribute of the connection. This attribute is not
    specified in the connection interface and might not exist in some connections.
    Therefore fallback is the meta_type of the connection.
    """

    # works with aquisition
    connection = getattr(context, connection_id)

    # any way try parent
    if not connection:
        connection = getattr(context.getParentNode(), connection_id)

    # use database_type to know the correct connector
    try:
        dbtype = connection.database_type
        name = connectors.get(dbtype, "SqlConnector")
    except Exception:
        # fallback on meta_type
        mtype = connection.meta_type
        name = connectors_by_meta_type.get(mtype, "SqlConnector")

    # get the connector name, default is the base class
    conmod = import_module("zopra.core.connector.%s" % name)
    connectorClass = getattr(conmod, name)

    # create and return the connectorClass object
    return connectorClass(connector_id, connection_id)


class SqlConnector(SimpleItem):
    """The SqlConnector class provides a base, partly abstract implementation for a
    database connection. All methods that contain plain sql or not sql-related content
    have been implemented here. All methods that need specific programming for the
    target database will be implemented in the specific connector subclasses."""

    _className = "SqlConnector"
    _classType = [_className]

    # different database use different LIKE operators for case insensitivity
    LIKEOPERATOR = "LIKE"

    # date format for database operations
    format_new = "%d.%m.%Y"

    # TODO: why is string converted to COL_TEXT (text)? shouldn't this be VARCHAR(255)? does this harm database speed?
    type_map = {
        "string": ZC.COL_TEXT,
        "memo": ZC.COL_TEXT,
        "int": ZC.COL_INT4,
        "singlelist": ZC.COL_INT4,
        "date": ZC.COL_DATE,
        "float": ZC.COL_FLOAT,
        "bool": ZC.COL_INT4,
        "int8": ZC.COL_INT8,
        "currency": ZC.COL_CURRENCY,
    }

    def __init__(self, id, connection_id):
        """Initialize the Connector

        :param id: The id for this connector.
        :connection_id: The id of the connection object that will be used by this connector.
        """
        self.id = id
        self.title = id
        self.connection_id = connection_id
        self.conn = None

    def _getConnection(self):
        """This method returns the connection object.

        :return: SQLConnection object
        """
        # get DB adapter
        zcon = getattr(self, self.connection_id)
        # get connectionpool from Adapter
        connection = zcon()
        # connection is a pool representation of the database connection (per Thread) (for mysql)

        return connection

    def query(self, query_text):
        """Execute the SQL query

        :param query_text: the complete SQL query string."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def escape_sql_name(self, name):
        """Escape SQL names (cols and tables), default: do nothing"""
        return name

    #
    # table handling
    #

    def convertDate(self, old_date):
        """Converts different date formats in european standard.

        Legacy method for converting date types before inserting in a database.

        :param old_date: date that should be changed into a new format.
        :return: String containing the new date if conversion was successful, otherwise an empty string.
        """
        if not old_date:
            return "NULL"

        old_date = str(old_date).strip()

        # set this to '' to differentiate between not old_date
        # and no conversion found
        new_date = ""

        for format_old in format_list:
            try:
                return strftime(self.format_new, strptime(old_date, format_old))
            except ValueError:
                pass

        return new_date

    def checkType(
        self, value, column_type, operator=False, label=None, do_replace=True
    ):
        """makes all standard conversions and checking for supported Types
        and returns altered value-string. Returns an operator as well, if param operator is True
        """
        # BUG: user can cause misbehaviour by mixing keywords... redesign to brake
        #      non-fitting parts into conjunctions (need col-name for that)

        # first some checks

        # value = None leads to problems with str(value)
        if not (value is None or isinstance(value, ListType)):
            if not isinstance(value, unicode):
                if isinstance(value, str):
                    try:
                        value = unicode(value, "utf8")
                    except UnicodeDecodeError:
                        pass
                else:
                    value = unicode(value)
            value = value.strip()
            pos_to = value.find("_to_")
            # inserts of __ in text should work -> operator indicates search
            pos_sep = value.find("__") if operator else -1
            pos_lt = value.find("_<_")
            pos_lte = value.find("_<=_")
            pos_gt = value.find("_>_")
            pos_gte = value.find("_>=_")

        # NULL (0 can be ignored because it was converted to '0' which is True
        if not value or value == "NULL" or value == "_0_" or value == ["NULL"]:
            value = "NULL"
            oper = "IS"

        # lists for freetext-search-results
        elif isinstance(value, ListType):
            if "_not_ NULL" in value or "_not_NULL" in value:
                value = "NOT NULL"
                oper = "IS"
            else:
                entry_list = map(
                    lambda onevalue: self.checkType(
                        onevalue, column_type, False, label
                    ),
                    value,
                )
                value = u"(%s)" % u", ".join(entry_list)
                oper = "IN"

        # check for _not_ NULL
        elif (
            value.replace(" ", "") == "_not_NULL"
            or value.replace(" ", "") == "_not__0_"
        ):
            value = "NOT NULL"
            oper = "IS"

        # we allow range searches with keyword _to_
        elif pos_to != -1:
            value = "%s and %s" % (
                self.checkType(value[:pos_to].rstrip(), column_type, False, label),
                self.checkType(value[pos_to + 4 :].lstrip(), column_type, False, label),
            )
            oper = "BETWEEN"

        elif pos_sep != -1:
            valuelist = value.split("__")
            oper = "IN"
            entry_list = map(
                lambda onevalue: self.checkType(
                    onevalue.strip(), column_type, False, label
                ),
                valuelist,
            )
            value = u"(%s)" % u", ".join(entry_list)

        elif pos_lt != -1:
            oper = "<"
            value = self.checkType(
                value[pos_lt + 3 :].strip(), column_type, False, label
            )
        elif pos_lte != -1:
            oper = "<="
            value = self.checkType(
                value[pos_lte + 4 :].strip(), column_type, False, label
            )
        elif pos_gt != -1:
            oper = ">"
            value = self.checkType(
                value[pos_gt + 3 :].strip(), column_type, False, label
            )
        elif pos_gte != -1:
            oper = ">="
            value = self.checkType(
                value[pos_gte + 4 :].strip(), column_type, False, label
            )
        else:
            oper = ""
            labelstr = ""
            if label:
                labelstr = " for field %s" % label

            if not column_type:
                raise ValueError("No Type found%s." % labelstr)

            if column_type == "string" or column_type == "memo":
                oper = ""
                if do_replace:
                    # replace wildcards
                    value = value.replace("*", "%")

                # escape some characters
                value = value.replace("'", "\\'")

                # remove double escape for ' in text
                value = value.replace("\\\\'", "\\'")

                # we allow not like searches with keyword _not_
                if value.find("_not_") == 0:
                    value = value[5:].lstrip()
                    oper = "not "

                oper += self.LIKEOPERATOR
                value = "'" + value + "'"

            elif column_type == "date":
                oper, value = self.checkDateValue(value, labelstr)

            elif column_type == "int" or column_type == "singlelist":

                # we allow != searches with keyword _not_
                if value.find("_not_") == 0:
                    value = value[5:].lstrip()
                    oper = "<>"
                else:
                    oper = " = "
                try:
                    int(value)
                except ValueError:
                    label = "You inserted a wrong value%s: %s (type: %s, datatype: %s)."
                    label = label % (labelstr, value, column_type, str(type(value)))
                    raise ValueError(label)

            elif column_type == "float" or column_type == "currency":
                # we allow != searches with keyword _not_
                if value.find("_not_") == 0:
                    value = value[5:].lstrip()
                    oper = "<>"
                else:
                    oper = " = "
                try:
                    float(value)
                except ValueError:
                    label = "You inserted a wrong value%s: %s (type: %s)."
                    label = label % (labelstr, value, column_type)
                    raise ValueError(label)

            elif column_type == "bool":
                oper = " = "
                if value and value != "NULL" and value != "0":
                    value = 1
                else:
                    # for add/edit there is no difference between NULL and not there
                    # it all results to a NULL value in the column
                    # so for search, we can look for anything (True) or NULL (False)
                    # but for add/edit it is important that the int 0 is translated to NULL
                    value = "NULL"
                    oper = " IS "

            elif column_type == "multilist" or column_type == "hierarchylist":

                raise ValueError("checkType called on multi- or hierarchylist")

            else:
                oper = "="

        return (unicode(value), unicode(oper)) if operator else unicode(value)

    def checkDateValue(self, value, labelstr=""):
        """check date values in extra function for overwrite possibility"""
        value = value.replace("*", "%")
        oper = ""
        if value.find("_not_") == 0:
            value = value[5:].lstrip()
            oper = "not "

        if value.find("%") == -1:
            newvalue = self.convertDate(value)
            if not newvalue:
                raise ValueError("Wrong Date Format%s (%s)." % (labelstr, value))
            else:
                value = newvalue

        value = u"'%s'" % value
        oper += self.LIKEOPERATOR
        return oper, value

    def convertType(self, col_type):
        """This method converts ZopRA-intern types to DB-types.

        :param  coltype: ZopRA column type
        :return: database dependent column type
        """
        assert ZC.checkType("col_type", col_type, StringType)

        return self.type_map.get(col_type, ZC.COL_TEXT)

    def getColumnDefinition(self, cols_dict):
        """Generate the SQL column definition for cols_dict.

        :param cols_dict: dictionary containing the columns dicts
        :type cols_dict: dict
        :return: SQL column definition
        :rtype: string
        """
        assert ZC.checkType("cols_dict", cols_dict, DictType)

        cols_str = []
        for col in cols_dict:

            # type conversion
            dbtype = " %s" % self.convertType(cols_dict[col][ZC.COL_TYPE])

            # default value
            col_default = cols_dict[col].get(ZC.COL_DEFAULT)
            default = " DEFAULT %s" % col_default if col_default else ""

            # reference value
            col_ref = cols_dict[col].get(ZC.COL_REFERENCE)
            reference = " REFERENCES %s" % col_ref if col_ref else ""

            # join the column statement
            cols_str.append(
                "%s%s%s%s" % (self.escape_sql_name(col), dbtype, default, reference)
            )

        return ", ".join(cols_str)

    def createTable(self, name, cols_dict, edit_tracking=True):
        """Adds a table to the database.

        :param name: the full table name
        :param cols_dict: dictionary containing the column definition
        :param edit_tracking: if enabled special columns for tracking the
                               edit changes will be added; default is True.
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def dropTable(self, name):
        """This method drops a table from the database.

        :param name: the name of the table
        :type name: string
        """
        assert ZC.checkType("table_name", name, StringType)

        self.query("DROP TABLE %s" % name)

    ############################################################################
    #
    # index handling
    #
    ############################################################################
    def createIndex(self, name, column):
        """Create an index for table on the specified column.

        :param name: the table name
        :param column: the column name
        """
        assert ZC.checkType("name", name, StringType)
        assert ZC.checkType("column", column, StringType)

        self.query("CREATE INDEX %s_index_%s ON %s (%s)" % (name, column, name, column))

    ############################################################################
    #
    # select handling
    #
    ############################################################################
    def simpleIns(self, name, cols_dict, entry_dict):
        """insert into table"""
        assert ZC.checkType("name", name, StringType)

        insert_text = ["INSERT INTO %s ( " % name]
        cols_list = []
        data_list = []

        for col in entry_dict.keys():
            # don't save NULL values, saves a little bit string length
            # but store 0-values
            val = entry_dict.get(col, None)
            if val is None or val == "NULL" or val == "None":
                continue

            # build col_list
            cols_list.append(col)

            # build data_list
            # get type of col
            if cols_dict.get(col):
                col_type = cols_dict[col][ZC.COL_TYPE]

            elif ZC._edit_tracking_cols.get(col):
                col_type = ZC._edit_tracking_cols[col][ZC.COL_TYPE]

            # this needs to be here to allow autoid overwriting
            elif col == ZC.TCN_AUTOID:
                col_type = ZC.ZCOL_INT
            else:
                raise ValueError("No ColType found")

            # build proper data entries
            data_list.append(
                self.checkType(
                    val,
                    col_type,
                    False,
                    cols_dict.get(col, {}).get(ZC.COL_LABEL, ""),
                    False,  # no char replacement
                )
            )

        insert_text.append(", ".join(cols_list))
        insert_text.append(") VALUES ( ")
        insert_text.append(", ".join(data_list))
        insert_text.append(");")

        # query
        self.query("".join(insert_text))

        # get last id
        return self.getLastId(ZC.TCN_AUTOID, name)

    def getLastId(self, id_field, table_name, where=""):
        """Returns the last id from id_field (by using max()).

        :param id_field: name of the field containing the id
        :param table_name: name of the table
        :param where: additional where clause
        :return: max value (aka last id) of the id field
        :rtype: int
        """
        result = self.query("SELECT max(%s) FROM %s%s" % (id_field, table_name, where))
        return result[0][0] if result and result[0][0] else 0

    def simpleUpd(self, name, origcols_dict, entry_dict, autoid):
        """insert changed values into the database"""
        if isinstance(autoid, StringType):
            autoid = int(autoid)

        assert ZC.checkType(ZC.TCN_AUTOID, autoid, IntType)
        assert ZC.checkType("name", name, StringType)

        # build update query text
        query_text = []
        value_text = []

        query_text.append("UPDATE %s SET" % (name))
        for colname in entry_dict:
            if colname in origcols_dict:
                field = origcols_dict[colname]
            elif colname in ZC._edit_tracking_cols:
                field = ZC._edit_tracking_cols[colname]
            else:
                # rest is ignored
                field = None
            if field:
                value_text.append(
                    " %s = %s"
                    % (
                        colname,
                        self.checkType(
                            entry_dict.get(colname),
                            field.get(ZC.COL_TYPE),
                            False,
                            field.get(ZC.COL_LABEL),
                        ),
                    )
                )

        if not value_text:
            return False

        query_text.append(",".join(value_text))
        query_text.append(" WHERE autoid = %s;" % autoid)

        self.query("".join(query_text))

        return True

    def simpleSel(self, name, col_list, origcols_dict, where_dict):
        """select requested columns of entries specified by entry_dict"""
        assert ZC.checkType("name", name, StringType)

        # build select query text
        query = []
        where = []

        query.append(
            "SELECT %s FROM %s"
            % (", ".join(self.escape_sql_name(col) for col in col_list), name)
        )
        for colname in where_dict:
            if colname in origcols_dict:
                field = origcols_dict[colname]
            elif colname in ZC._edit_tracking_cols:
                field = ZC._edit_tracking_cols[colname]
            elif colname == ZC.TCN_AUTOID:
                field = {ZC.COL_TYPE: "int", ZC.COL_LABEL: "Automatic No."}
            else:
                # rest is ignored
                field = None
            if field:
                where.append(
                    "%s = %s"
                    % (
                        colname,
                        self.checkType(
                            where_dict.get(colname),
                            field.get(ZC.COL_TYPE),
                            False,
                            field.get(ZC.COL_LABEL),
                        ),
                    )
                )
        if where:
            query.append("WHERE " + " AND ".join(where))
        results = self.query(" ".join(query))
        res = []
        for result in results:
            entry = {}
            if col_list == ["*"]:
                entry[ZC.TCN_AUTOID] = result[0]
            else:
                for index, col in enumerate(col_list):
                    entry[col] = result[index]
            res.append(entry)
        return res

    def simpleVal(self, col_dict, entry_dict):
        """validate the entry against the column definition"""
        errors = {}
        for colname in entry_dict:
            if colname in col_dict:
                field = col_dict[colname]
            elif colname in ZC._edit_tracking_cols:
                field = ZC._edit_tracking_cols[colname]
            elif colname == ZC.TCN_AUTOID:
                # for search, autoid needs to be validated
                # TODO: +1 for autoid in ZC._edit_tracking_cols
                field = {
                    ZC.COL_TYPE: "int",
                    ZC.COL_LABEL: u"Automatic No.",
                    ZC.COL_INVIS: True,
                }
            else:
                # rest is ignored
                continue

            val = entry_dict.get(colname)

            if field and val:
                try:
                    self.checkType(
                        val, field.get(ZC.COL_TYPE), False, field.get(ZC.COL_LABEL)
                    )
                except Exception:
                    errors[colname] = ("Invalid input", val)
        return errors

    def simpleDel(self, table_name, autoid):
        """This method is used to delete the entry with given autoid.

        :param table_name: the name of the table
        :type table_name: string
        :param autoid: the entry autoid
        :type autoid: int
        :return: True
        """
        assert ZC.checkType("table_name", table_name, StringType)
        assert ZC.checkType("autoid", autoid, IntType)
        self.query("DELETE FROM %s where autoid = %s" % (table_name, autoid))
        return True

    def getRowCount(self, name, where=""):
        """This method returns the number of rows matching the where clause.

        No where clause means all rows.

        :param name: the table name
        :type name: string
        :param where: the where clause (optional)
        :type where: string
        :return: the row count
        """
        assert ZC.checkType("name", name, StringType)
        assert ZC.checkType("where", where, StringType)

        # handling of the case that the keyword WHERE is not already included
        if where and where.upper().find("WHERE") == -1:
            where = "WHERE " + where

        result = self.query("SELECT count(*) FROM %s %s" % (name, where))
        return result[0][0] if result else None

    ############################################################################
    #
    # SQL function handling
    #
    ############################################################################
    def addFunctionSql(self, name, param, output, sql):
        """Create a SQL function in the database.

        :param name: the function name
        :param param: parameters of the function
        :param output: output type
        :param sql: the inner sql of the function
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def addFunction(self, function):
        """This method creates a SQL function in the database.

        :param function: a SQL statement to create a stored procedure
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def delFunction(self, name, param):
        """This method deletes a SQL function from the database.

        :param name: the function name
        :param param: the function parameters
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    # some special queries for table statistics (here for override capability)
    QT_COUNT = """SELECT count(*) FROM %s"""
    QT_COUNT_DMY = """SELECT count(*) AS count,
                             YEAR(entrydate) AS year,
                             MONTH(entrydate) AS month,
                             DAY(entrydate) AS day
                      FROM %s
                      GROUP BY year, month, day
                      ORDER BY year, month, day"""
    QT_COUNT_MY = """SELECT count(*) AS count,
                             YEAR(entrydate) AS year,
                             MONTH(entrydate) AS month
                      FROM %s
                      GROUP BY year, month
                      ORDER BY year, month"""
    QT_COUNT_Y = """SELECT count(*) AS count,
                             YEAR(entrydate)  AS year
                      FROM %s
                      GROUP BY year
                      ORDER BY year"""
