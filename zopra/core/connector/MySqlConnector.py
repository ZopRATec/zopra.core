from time import ctime

from zopra.core import ZC
from zopra.core.connector.SqlConnector import SqlConnector
from zopra.core.types import BooleanType
from zopra.core.types import DictType
from zopra.core.types import IntType
from zopra.core.types import StringType


# overwrite _edit_tracking_cols, mysql doesn't like default values for datetime
_edit_tracking_cols = {
    ZC.TCN_CREATOR: {ZC.COL_TYPE: "singlelist", ZC.COL_LABEL: "Creator"},
    ZC.TCN_DATE: {ZC.COL_TYPE: "date", ZC.COL_LABEL: "Entry Date"},
    ZC.TCN_EDITOR: {ZC.COL_TYPE: "singlelist", ZC.COL_LABEL: "Last edited by"},
    ZC.TCN_EDATE: {ZC.COL_TYPE: "date", ZC.COL_LABEL: "Last edited on"},
    ZC.TCN_OWNER: {ZC.COL_TYPE: "singlelist", ZC.COL_LABEL: "Owner"},
}


class MySqlConnector(SqlConnector):
    """SQL Connector for MySQL"""

    _className = "MySqlConnector"
    _classType = SqlConnector._classType + [_className]

    format_new = "%Y-%m-%d"

    #
    # MySQL special: string to varchar(255), float to double
    #
    type_map = SqlConnector.type_map
    type_map["string"] = "VARCHAR(255)"
    type_map["float"] = "DOUBLE"

    def query(self, query_text):
        """Execute the SQL query

        :param query_text: the complete SQL query string."""
        if isinstance(query_text, unicode):
            query_text = query_text.encode("utf8")

        conn = self._getConnection()
        # added the param res_only to MySQLDA, to suppress the fetching of info into tmp, but that
        # somehow disturbs the transaction handling, so removed it again for now.
        # added parameter "0" for max_rows to avoid double "LIMIT"-spec
        return conn.query(query_text, 0)[1]

    def escapeSQLName(self, name):
        """Escape SQL names (cols and tables), overwritten to do escaping

        :param name: column or table name
        :type name: str
        :return: escaped name
        :rtype: str
        """
        return "`%s`" % name

    def escapeSQLValue(self, value):
        """intelligent sql escaping utilizes the DB API

        :param value: value that needs to be sql quoted
        :type value: str
        :return: sql quoted string value
        :rtype: str
        """
        # get DB adapter
        zcon = getattr(self, self.connection_id)
        # method is part of the API, make sure it works for all connectors
        return zcon.sql_quote__(value)

    #
    # table handling
    #
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
        create_text.append("autoid INT auto_increment")

        if edit_tracking:
            create_text.append(", ")
            create_text.append(self.getColumnDefinition(_edit_tracking_cols))

        # we have to take care of columns with the same name as edit_tracking_cols
        cols_copy = {}
        for key in cols_dict:
            if key not in _edit_tracking_cols:
                cols_copy[key] = cols_dict[key]

        add_cols = self.getColumnDefinition(cols_copy)
        if add_cols:
            create_text.append(", ")
            create_text.append(add_cols)

        # add the primary key
        primary_keys = []
        for col in cols_copy:
            if cols_copy[col].get(ZC.COL_PRIMARY_KEY):
                primary_keys.append(col)

        if primary_keys:
            create_text.append(
                ", PRIMARY KEY (%s)"
                % ", ".join([self.escapeSQLName(key) for key in primary_keys])
            )
        else:
            create_text.append(", PRIMARY KEY (autoid)")
        create_text.append(") ENGINE = InnoDB")

        # create table
        self.query(" ".join(create_text))

    #
    # select handling
    #
    def simpleIns(self, name, cols_dict, entry_dict):
        """insert into table"""
        assert ZC.checkType("name", name, StringType)

        insert_text = ["INSERT INTO %s ( " % name]
        cols_list = []
        data_list = []

        cols = cols_dict.keys()
        for col in _edit_tracking_cols:
            if col not in cols:
                cols.append(col)

        for col in cols:
            # don't save NULL values, saves a little bit string length
            # but store 0-values
            val = entry_dict.get(col, None)
            if val == "NULL" or val == "None":
                val = None

            if col == ZC.TCN_DATE and not val:
                # insert date, mysql doesn't like time default values
                val = ctime()

            # if the value is still None, we can skip
            if val is None:
                continue

            # build col_list
            cols_list.append(self.escapeSQLName(col))

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
        insert_text.append(")")

        # query
        try:
            self.query("".join(insert_text))
        except Exception as e:
            raise ValueError("SQL Error in %s: \n%s" % ("".join(insert_text), str(e)))
        # get last id and return it
        return self.getLastId(None, name)

    # the mysql way for fetching the last inserted id
    def getLastId(self, id_field, table_name, where=""):
        """Returns the last id from id_field (by using LAST_INSERT_ID()),
        fallback is the superclass implementation.

        :param id_field: name of the field containing the id
        :param table_name: name of the table
        :param where: additional where clause
        :return: max value (aka last id) of the id field
        :rtype: int
        """
        result = self.query("SELECT LAST_INSERT_ID() FROM %s" % (table_name))
        res = result and result[0][0]
        return res or super(MySqlConnector, self).getLastId(ZC.TCN_AUTOID, table_name)

    def simpleUpd(self, name, origcols_dict, entry_dict, autoid):
        """insert changed values into the database (overwritten for edit-timestamp handling)"""
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
            elif colname in _edit_tracking_cols:
                field = _edit_tracking_cols[colname]
            else:
                # rest is ignored
                field = None

            val = entry_dict.get(colname)
            if colname == ZC.TCN_EDATE and not val:
                # insert date, mysql doesn't like time default values
                val = ctime()

            if field:
                value_text.append(
                    " %s = %s"
                    % (
                        self.escapeSQLName(colname),
                        self.checkType(
                            val, field.get(ZC.COL_TYPE), False, field.get(ZC.COL_LABEL)
                        ),
                    )
                )

        if not value_text:
            return False

        query_text.append(",".join(value_text))
        query_text.append(" WHERE autoid = %s" % autoid)

        self.query("".join(query_text))

        return True
