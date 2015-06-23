############################################################################
#    Copyright (C) 2008 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#
# Python Language Imports
#

from copy         import deepcopy
from types        import StringType, IntType, DictType
from time         import ctime

#
# ZMOM Imports
#
from zopra.core          import E_PARAM_TYPE
from zopra.core.CorePart import COL_TYPE,        \
                                COL_TEXT,        \
                                COL_LABEL,       \
                                COL_DATE,        \
                                COL_CURRENCY,    \
                                COL_DEFAULT,     \
                                COL_REFERENCE,   \
                                COL_PRIMARY_KEY, \
                                COL_INT4,        \
                                COL_INT8
from zopra.core.constants import TCN_AUTOID,      \
                                 TCN_CREATOR,     \
                                 TCN_EDITOR,      \
                                 TCN_OWNER,       \
                                 TCN_DATE,        \
                                 TCN_EDATE

from zopra.core.connector.SqlConnector import SqlConnector

# overwrite _edit_tracking_cols, mysql doesn't like default values for datetime
_edit_tracking_cols = { TCN_CREATOR: { COL_TYPE:   'singlelist',
                                       COL_LABEL:  'Creator'},
                        TCN_DATE:    { COL_TYPE:   'date',
                                       COL_LABEL:  'Entry Date'},
                        TCN_EDITOR:  { COL_TYPE:   'singlelist',
                                       COL_LABEL:  'Last edited by'},
                        TCN_EDATE:   { COL_TYPE:   'date',
                                       COL_LABEL:  'Last edited on'},
                        TCN_OWNER:   { COL_TYPE:   'singlelist',
                                       COL_LABEL:  'Owner'},
                        }


class MySqlConnector(SqlConnector):
    """\brief SQL Connector Base Class"""
    _className = 'MySqlConnector'
    _classType = SqlConnector._classType + [_className]

    format_new  = '%Y-%m-%d'

    def query(self, query_text):
        """\brief Executes a SQL query

        Note that this function sets the environment to german, european for
        the date handling.

        \param string         The argument \a string contains the complete SQL
                              query string.

        \param shared_connect If you want to use a shared connection object
                              you have to set this argument to True.
                              Default is False.
        """

        conDA = self._getConnection()
        conn = conDA()
        # TODO: correct the data style handling
        #       why here setDatestyle and not in _getConnection() ?
        #       because in _getConnection it gets lost before the first query,
        #       don't know why
        # self.conn.query("set datestyle = 'german, european';")

        # added the param res_only to MySQLDA, to suppress the fetching of info into tmp, but that
        # somehow disturbs the transaction handling, so removed it again for now.
        # added parameter "0" for max_rows to avoid double "LIMIT"-spec
        return conn.query( query_text, 0 )[1]
        # self.conn.connection().close()
        # raise ValueError(dir(self.conn.connection._v_database_connection))


#
# table handling
#

    def convertType(self, coltype):
        """\brief Converts ZMOM-intern types to db-types. MySQL special: string to varchar(255), float to double"""
        # TODO: should incorporate an exact floating point type (decimal)
        if coltype == 'string':
            return 'VARCHAR(255)'
        elif coltype == 'memo':
            return COL_TEXT
        elif coltype == 'int' or coltype == 'singlelist':
            return COL_INT4
        elif coltype == 'date':
            return COL_DATE
        elif coltype == 'float':
            return 'DOUBLE'
        elif coltype == 'bool':
            return COL_INT4
        elif coltype == 'int8':
            return COL_INT8
        elif coltype == 'currency':
            return COL_CURRENCY
        else:
            return COL_TEXT


    def getColumnDefinition(self, cols_dict):
        assert isinstance(cols_dict, DictType), \
               E_PARAM_TYPE % ('cols_dict', 'DictType', cols_dict)

        cols_str = []
        for col in cols_dict:
            name = col
            try:
                # type conversion
                dbtype  = self.convertType(cols_dict[col][COL_TYPE])
                kind    = ' %s' % dbtype
            except:
                raise ValueError(str(cols_dict) + str(col))
            if cols_dict[col].get(COL_DEFAULT):
                default = ' DEFAULT %s' % cols_dict[col][COL_DEFAULT]
            else:
                default = ''
            if cols_dict[col].get(COL_REFERENCE):
                reference = ' REFERENCES %s' % cols_dict[col][COL_REFERENCE]
            else:
                reference = ''
            cols_str.append('%s%s%s%s' % (name, kind, default, reference) )
        return ', '.join(cols_str)


    def testForTable(self, name):
        """\brief Test if the table already exists.

        \param name           The argument \a name is a string with the
                              fullname of a table.

        \return Boolean       Returns True if the table exists, otherwise False
        """
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        raise ValueError('Not implemented.')


    def testForColumn(self, mgrid, table, column):
        """\brief Test if the column already exists in table.

        \param manager        The argument \a manager is a string with the
                              manager id.

        \param table           The argument \a table is a string with the
                              fullname of a table.

        \param column         The argument \a column is a string with the
                              fullname of a column.

        \return Boolean       Returns True if the column exists in table, otherwise False
        """
        assert isinstance(mgrid, StringType), \
               E_PARAM_TYPE % ('mgrid', 'StringType', mgrid)

        assert isinstance(table, StringType), \
               E_PARAM_TYPE % ('table', 'StringType', table)

        assert isinstance(table, StringType), \
               E_PARAM_TYPE % ('column', 'StringType', column)

        raise ValueError('Not implemented.')


    def createTable(self, name, cols_dict, edit_tracking = True):
        """\brief Adds a SQL table to an existing database."""
        # Tests moved to manage_afterAdd to avoid system specific testForTable

        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(cols_dict, DictType), \
               E_PARAM_TYPE % ('cols_dict', 'DictType', cols_dict)
        assert edit_tracking == True or edit_tracking == False, \
               E_PARAM_TYPE % ('edit_tracking',  'BooleanType', edit_tracking)

        create_text = ['CREATE TABLE %s (' % name]
        create_text.append( "autoid INT auto_increment" )

        if edit_tracking:
            create_text.append(', ')
            create_text.append( self.getColumnDefinition(_edit_tracking_cols) )


        # we have to take care of columns with the same name as edit_tracking_cols
        cols_copy = {}
        for key in cols_dict:
            if key not in _edit_tracking_cols:
                cols_copy[key] = cols_dict[key]

        add_cols = self.getColumnDefinition(cols_copy)
        if add_cols:
            create_text.append( ', '     )
            create_text.append( add_cols )


        # add the primary key
        primary_keys = []
        for col in cols_copy:
            if cols_copy[col].get(COL_PRIMARY_KEY):
                primary_keys.append(col)

        if primary_keys:
            create_text.append( ', PRIMARY KEY (%s)' %
                                ', '.join(primary_keys) )
        else:
            create_text.append(', PRIMARY KEY (autoid)')
        create_text.append(') ENGINE = InnoDB')

        # create table
        self.query(' '.join(create_text))


    def dropTable(self, name):
        """\brief Drops table from a database.
        """
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        self.query('DROP TABLE %s' % name)


#
# index handling
#
    def createIndex(self, table, column):
        """\brief Creates an index for table with specified column."""
        assert isinstance(table, StringType), \
               E_PARAM_TYPE % ('table', 'StringType', table)
        assert isinstance(column, StringType), \
               E_PARAM_TYPE % ('column', 'StringType', column)

        index_text = "CREATE INDEX %s_index_%s ON %s (%s) " % ( table,
                                                                 column,
                                                                 table,
                                                                 column )
        self.query(index_text)

#
# select handling
#
    def simpleIns(self, name, origcols_dict, entry_dict):
        """ insert into table """
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        insert_text = ['INSERT INTO %s ( ' % name]
        cols_list   = []
        data_list   = []
        cols_dict   = deepcopy(origcols_dict)

        for col in _edit_tracking_cols:
            if col not in cols_dict:
                cols_dict[col] = _edit_tracking_cols[col]
        cols = cols_dict.keys()

        for col in cols:
            # don't save NULL values, saves a little bit string length
            # but store 0-values
            val = entry_dict.get(col, None)
            if val == 'NULL' or val == 'None':
                val = None

            if col == TCN_DATE and not val:
                # insert date, mysql doesn't like time default values
                val = ctime()

            # build col_list
            cols_list.append(col)

            # build data_list
            # get type of col
            if cols_dict.get(col):
                col_type = cols_dict[col][COL_TYPE]

            # this needs to be here to allow autoid overwriting
            elif col == 'autoid':
                col_type = 'int'
            else:
                raise ValueError('No ColType found')

            # build proper data entries
            data_list.append( self.checkType( val,
                                              col_type,
                                              False,
                                              cols_dict.get(col, {}).get(COL_LABEL, ''),
                                              False  # no char replacement
                                              )
                              )

        insert_text.append( ', '.join(cols_list) )
        insert_text.append( ') VALUES ( ')
        insert_text.append( ', '.join(data_list) )
        insert_text.append( ')' )

        # query
        try:
            self.query(''.join(insert_text))
        except Exception, e:
            raise ValueError('SQL Error in %s: \n%s' % (''.join(insert_text), str(e)))
        # get last id and return it
        return self.getLastInsertedId(name)


    # the mysql way for fetching the last inserted id
    def getLastInsertedId(self, name):
        """\brief get id of last entry"""
        query_text = 'SELECT LAST_INSERT_ID() FROM %s' % (name)
        result = self.query( query_text )
        res = 0
        if result:
            if result[0][0]:
                res = result[0][0]
        if not res:
            # try old way
            res = self.getLastId(TCN_AUTOID, name)
        return res


    def getLastId(self, idfield, name, wherestr = ''):
        """\brief get max entry of idfield"""
        query_text = 'SELECT max(%s) FROM %s%s' % ( idfield, name, wherestr )
        result = self.query( query_text )
        res = 0
        if result:
            if result[0][0]:
                res = result[0][0]
        return res


    def simpleUpd( self,
                   name,
                   origcols_dict,
                   entry_dict,
                   autoid ):
        """\brief insert changed values into the database"""
        if isinstance(autoid, StringType):
            autoid = int(autoid)

        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(autoid, IntType), \
               E_PARAM_TYPE % ('autoid', 'IntType', autoid)

        # build update query text
        query_text = []
        value_text = []

        query_text.append('UPDATE %s SET' % (name) )
        for colname in entry_dict:
            if colname in origcols_dict:
                field = origcols_dict[colname]
            elif colname in _edit_tracking_cols:
                field = _edit_tracking_cols[colname]
            else:
                # rest is ignored
                field = None

            val = entry_dict.get(colname)
            if colname == TCN_EDATE and not val:
                # insert date, mysql doesn't like time default values
                val = ctime()

            if field:
                value_text.append(' %s = %s' % ( colname,
                                                 self.checkType(
                                                    val,
                                                    field.get(COL_TYPE),
                                                    False,
                                                    field.get(COL_LABEL)
                                                           )
                                                  )
                                 )


        if not value_text:
            return False

        query_text.append( ','.join(value_text) )
        query_text.append( ' WHERE autoid = %s' % autoid )

        self.query( ''.join(query_text) )

        return True


    def simpleVal(self, col_dict, entry_dict):
        """\brief validate the entry agains the column definition"""
        errors = {}
        for colname in entry_dict:
            if colname in col_dict:
                field = col_dict[colname]
            elif colname in _edit_tracking_cols:
                field = _edit_tracking_cols[colname]
            else:
                # rest is ignored
                continue

            val = entry_dict.get(colname)

            if field and val:
                try:
                    self.checkType( val,
                                    field.get(COL_TYPE),
                                    False,
                                    field.get(COL_LABEL)
                                    )
                except:
                    errors[colname] = ('Invalid input', val)
        return errors


    def simpleDel(self, name, autoid):
        """\brief delete the entry with given autoid."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(autoid, IntType), \
               E_PARAM_TYPE % ('autoid', 'IntType', autoid)

        query_text = "DELETE FROM %s where autoid = %s" % (name, autoid)
        self.query( query_text )

        return True


    def getRowCount(self, name, wherestring = ''):
        """\brief Returns the number of rows matching wherestring."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(wherestring, StringType), \
               E_PARAM_TYPE % ('wherestring', 'StringType', wherestring)

        if wherestring and wherestring.upper().find('WHERE') == -1:
            wherestring = "WHERE " + wherestring
        query_text = 'SELECT count(*) FROM %s %s' % (name, wherestring)
        result     = self.query( query_text )
        if result:
            return result[0][0]


#
# Function handling
#
    def addFunctionSql(self, name, param, output, sql):
        """\brief Creates a SQL function in the database."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        # query_text = []
        # query_text.append("CREATE FUNCTION %s(%s)" % (name, param))
        # query_text.append("RETURNS %s" % output)
        # query_text.append("AS '%s'" % sql.replace(';', ''))
        # query_text.append("LANGUAGE 'sql'")
        # self.query( '\n'.join(query_text) )

        # no functions for mysql for now
        pass


    def addFunction(self, function):
        """\brief create a function"""
        # self.query(function)
        pass


    def delFunction(self, name, param):
        """\brief Deletes a function from the database."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        # self.query( 'DROP FUNCTION %s(%s)' % (name, param) )
        pass
