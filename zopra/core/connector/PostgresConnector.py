from __future__ import print_function
from zopra.core.types import BooleanType
from zopra.core.types import DictType
from zopra.core.types import IntType
from zopra.core.types import StringType

from zopra.core import ZC
from zopra.core.connector.SqlConnector import SqlConnector


class PostgresConnector(SqlConnector):
    """SQL Connector for POSTGRES"""

    _className = "SqlConnector"
    _classType = SqlConnector._classType + [_className]

    LIKEOPERATOR = "ILIKE"

    def _createSequence(self, table_name, col_name="autoid"):
        """Creates a sequence for the given column of the given table.

        :param table_name: Name of the table
        :param col_name: Name of the column
        :return: The return value is the name of the sequence.
        :rtype: string
        """
        assert isinstance(table_name, StringType), ZC.E_PARAM_TYPE % (
            "table_name",
            "StringType",
            table_name,
        )
        assert isinstance(col_name, StringType), ZC.E_PARAM_TYPE % (
            "col_name",
            "StringType",
            col_name,
        )

        self.query("CREATE SEQUENCE c_%s_%s;" % (table_name, col_name))
        return "c_%s_%s" % (table_name, col_name)

    def _dropSequence(self, table_name, col_name="autoid"):
        """Drops a sequence for the given table and column from the database.

        :param table_name: Name of the table
        :param col_name: Name of the column
        :return: Returns True
        """
        assert isinstance(table_name, StringType), ZC.E_PARAM_TYPE % (
            "table_name",
            "StringType",
            table_name,
        )
        assert isinstance(col_name, StringType), ZC.E_PARAM_TYPE % (
            "col_name",
            "StringType",
            col_name,
        )

        self.query("DROP SEQUENCE c_%s_%s;" % (table_name, col_name))
        return True

    def query(self, query_text):
        """Execute the SQL query

        :param query_text: the complete SQL query string."""
        connection = self._getConnection()
        connection.query("set datestyle = 'german, european';")

        # fetch info and result but return the result only
        if not query_text.endswith(";"):
            query_text += ";"

        # this is required to handle pickle strings in text fields
        # but I did had not time to check if it breaks some other stuff
        query_text = query_text.replace("\\'", "''")

        try:
            return connection.query(query_text)[1]
        except Exception as e:
            print(query_text)
            raise e

    def createTable(self, name, cols_dict, edit_tracking=True):
        """Adds a table to the database.

        :param name: the full table name
        :param cols_dict: dictionary containing the column definition
        :param edit_tracking: if enabled special columns for tracking the
                               edit changes will be added; default is True.
        """
        assert ZC.checkType("name", name, StringType)
        assert ZC.checkType("cols_dict", cols_dict, DictType)
        assert ZC.checkType("edit_tracking", edit_tracking, BooleanType)

        create_text = ["CREATE TABLE %s (" % name]
        create_text.append(
            "autoid INT4 DEFAULT nextval('%s')," % self._createSequence(name)
        )

        if edit_tracking:
            create_text.append(self.getColumnDefinition(ZC._edit_tracking_cols))
            create_text.append(", ")

        # we have to take care of columns with the same name as edit_tracking_cols
        cols_copy = {}
        for key in cols_dict:
            if key not in ZC._edit_tracking_cols:
                cols_copy[key] = cols_dict[key]

        add_cols = self.getColumnDefinition(cols_copy)
        if add_cols:
            create_text.append(add_cols)
            create_text.append(", ")

        # add the primary key
        primary_keys = []
        for col in cols_copy:
            if cols_copy[col].get(ZC.COL_PRIMARY_KEY):
                primary_keys.append(col)

        if primary_keys:
            create_text.append(" PRIMARY KEY (%s)" % ", ".join(primary_keys))
        else:
            create_text.append(" PRIMARY KEY (autoid)")
        create_text.append(");")

        # create table
        self.query(" ".join(create_text))

    def dropTable(self, name):
        """This method drops a table from the database.

        Overridden for sequence handling.

        :param name: the name of the table
        :type name: string
        """
        SqlConnector.dropTable(self, name)

        # also drop sequences for table
        self._dropSequence(name)

    #
    # select handling
    #
    def simpleIns(self, name, cols_dict, entry_dict):
        """insert into table"""
        assert isinstance(name, StringType), ZC.E_PARAM_TYPE % (
            "name",
            "StringType",
            name,
        )

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
            if col in cols_dict:
                col_type = cols_dict[col][ZC.COL_TYPE]

            elif col in ZC._edit_tracking_cols:
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

    def simpleUpd(self, name, origcols_dict, entry_dict, autoid):
        """insert changed values into the database"""
        if isinstance(autoid, StringType):
            autoid = int(autoid)

        assert isinstance(name, StringType), ZC.E_PARAM_TYPE % (
            "name",
            "StringType",
            name,
        )
        assert isinstance(autoid, IntType), ZC.E_PARAM_TYPE % (
            "autoid",
            "IntType",
            autoid,
        )

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

    ############################################################################
    #
    # SQL function handling (looks very legacy)
    #
    ############################################################################
    def addFunctionSql(self, name, param, output, sql):
        """Create a SQL function in the database.

        :param name: the function name
        :param param: parameters of the function
        :param output: output type
        :param sql: the inner sql of the function
        """
        assert isinstance(name, StringType), ZC.E_PARAM_TYPE % (
            "name",
            "StringType",
            name,
        )

        query_text = []
        query_text.append("CREATE FUNCTION %s(%s)" % (name, param))
        query_text.append("RETURNS %s" % output)
        query_text.append("AS '%s'" % sql)
        query_text.append("LANGUAGE 'sql';")
        self.query("\n".join(query_text))

    def addFunction(self, function):
        """This method creates a SQL function in the database.

        :param function: a SQL statement to create a stored procedure
        """
        self.query(function)

    def delFunctionSql(self, name, param):
        """This method deletes a SQL function from the database.

        :param name: the function name
        :param param: the function parameters
        """
        assert isinstance(name, StringType), ZC.E_PARAM_TYPE % (
            "name",
            "StringType",
            name,
        )
        self.query("DROP FUNCTION %s(%s);" % (name, param))

    # some special queries for table statistics (overridden for date_part)
    QT_COUNT = """SELECT count(*) FROM %s"""
    QT_COUNT_DMY = """SELECT count(*) AS count,
                             date_part('year',  entrydate) AS year,
                             date_part('month', entrydate) AS month,
                             date_part('day',   entrydate) AS day
                      FROM %s
                      GROUP BY year, month, day
                      ORDER BY year, month, day"""
    QT_COUNT_MY = """SELECT count(*) AS count,
                             date_part('year',  entrydate) AS year,
                             date_part('month', entrydate) AS month
                      FROM %s
                      GROUP BY year, month
                      ORDER BY year, month"""
    QT_COUNT_Y = """SELECT count(*) AS count,
                             date_part('year', entrydate)  AS year
                      FROM %s
                      GROUP BY year
                      ORDER BY year"""
