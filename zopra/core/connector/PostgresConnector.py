############################################################################
#    Copyright (C) 2008 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from copy import deepcopy
from types import DictType
from types import IntType
from types import StringType

#
# ZopRA Imports
#
from zopra.core import ZC
from zopra.core.connector.SqlConnector import SqlConnector


class PostgresConnector(SqlConnector):
    """\brief SQL Connector Base Class"""
    _className = 'SqlConnector'
    _classType = SqlConnector._classType + [_className]

    LIKEOPERATOR = 'ILIKE'

    def _createSequence(self, table_name, col_name = 'autoid'):
        """\brief Creates a sequence.

        The function gets a name for the sequence, appends the string 'counter'
        and creates the sequence in the database.

        \param name           The argument \a name is a string with the full
                              name for the sequence.
        \param shared_connect If you want to use a shared connection object
                              you have to set this argument to True.
                              Default is False.
        \return String        The return value is the name of the sequence.
        """
        ##\bug This function is Postgres dependent
        assert isinstance(table_name, StringType), \
               ZC.E_PARAM_TYPE % ('table_name', 'StringType', table_name)
        assert isinstance(col_name, StringType), \
               ZC.E_PARAM_TYPE % ('col_name', 'StringType', col_name)

        self.query('CREATE SEQUENCE c_%s_%s;' % (table_name, col_name) )
        return 'c_%s_%s' % (table_name, col_name)


    def _dropSequence(self, table_name, col_name = 'autoid'):
        """\brief Drops a sequence from the database.

        The function gets a name for the sequence, appends the string 'counter'
        and drops the sequence from the database.

        \param name           The argument \a name is a string with the full
                              name for the sequence.
        \param shared_connect If you want to use a shared connection object
                              you have to set this argument to True.
                              Default is False.
        \return Boolean       Returns True if nothing happened
        """
        assert isinstance(table_name, StringType), \
               ZC.E_PARAM_TYPE % ('table_name', 'StringType', table_name)
        assert isinstance(col_name, StringType), \
               ZC.E_PARAM_TYPE % ('col_name', 'StringType', col_name)

        self.query('DROP SEQUENCE c_%s_%s;' % (table_name, col_name) )
        return True


    def query(self, query_text):
        """\brief Executes a SQL query

        Note that this function sets the environment to german, european for
        the date handling.

        \param query_text     The argument \a query_text contains the complete SQL
                              query string.

        """
        connection = self._getConnection()
        connection.query("set datestyle = 'german, european';")

        # fetch info and result but return the result only
        if not query_text.endswith(';'):
            query_text += ';'

        # this is required to handle pickle strings in text fields
        # but I did had not time to check if it breaks some other stuff
        query_text = query_text.replace("\\'", "''")

        try:
            return connection.query(query_text)[1]
        except Exception as e:
            print query_text
            raise e

#
# table handling
#
    def testForTable(self, name):
        """ \see SqlConnector.testForTable """
        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)

        query_text = "SELECT * FROM pg_class WHERE relname LIKE '%s'" % name
        return bool( self.query(query_text) )


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
               ZC.E_PARAM_TYPE % ('mgrid', 'StringType', mgrid)

        assert isinstance(table, StringType), \
               ZC.E_PARAM_TYPE % ('table', 'StringType', table)

        assert isinstance(table, StringType), \
               ZC.E_PARAM_TYPE % ('column', 'StringType', column)

        query_text  = "SELECT count(a.attname) AS tot FROM pg_catalog.pg_stat_user_tables AS t, pg_catalog.pg_attribute a "
        query_text += "WHERE t.relid = a.attrelid AND t.schemaname = 'public' "
        query_text += "AND t.relname = '%s%s'  AND a.attname = '%s';" % (mgrid.lower(), table, column)

        result = self.query(query_text)
        return bool(result[0][0] if result else False)


    def createTable(self, name, cols_dict, edit_tracking = True):
        """\brief Adds a SQL table to an existing database."""
        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(cols_dict, DictType), \
               ZC.E_PARAM_TYPE % ('cols_dict', 'DictType', cols_dict)
        assert edit_tracking == True or edit_tracking == False, \
               ZC.E_PARAM_TYPE % ('edit_tracking',  'BooleanType', edit_tracking)

        create_text = ['CREATE TABLE %s (' % name]
        create_text.append( "autoid INT4 DEFAULT nextval('%s')," % \
                            self._createSequence(name) )

        if edit_tracking:
            create_text.append( self.getColumnDefinition(ZC._edit_tracking_cols) )
            create_text.append(', ')

        # we have to take care of columns with the same name as edit_tracking_cols
        cols_copy = {}
        for key in cols_dict:
            if key not in ZC._edit_tracking_cols:
                cols_copy[key] = cols_dict[key]

        add_cols = self.getColumnDefinition(cols_copy)
        if add_cols:
            create_text.append( add_cols )
            create_text.append( ', '     )

        # add the primary key
        primary_keys = []
        for col in cols_copy:
            if cols_copy[col].get(ZC.COL_PRIMARY_KEY):
                primary_keys.append(col)

        if primary_keys:
            create_text.append( ' PRIMARY KEY (%s)' % \
                                ', '.join(primary_keys) )
        else:
            create_text.append(' PRIMARY KEY (autoid)')
        create_text.append(');')

        # create table
        self.query(' '.join(create_text))


    def dropTable(self, table_name):
        """ \see SqlConnector.dropTable """
        SqlConnector.dropTable(self, table_name)

        # also drop sequences for table
        self._dropSequence(table_name)


#
# select handling
#
    def simpleIns(self, name, origcols_dict, entry_dict):
        """ insert into table """
        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)

        insert_text = ['INSERT INTO %s ( ' % name]
        cols_list   = []
        data_list   = []
        cols_dict   = deepcopy(origcols_dict)

        for col in ZC._edit_tracking_cols:
            if col not in cols_dict:
                cols_dict[col] = ZC._edit_tracking_cols[col]
        cols = entry_dict.keys()

        for col in cols:
            # don't save NULL values, saves a little bit string length
            # but store 0-values
            val = entry_dict.get(col, None)
            if val is None or val == 'NULL' or val == 'None':
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
            elif col == 'autoid':
                col_type = ZC.ZCOL_INT
            else:
                raise ValueError('No ColType found')

            # build proper data entries
            data_list.append( self.checkType( val,
                                              col_type,
                                              False,
                                              cols_dict.get(col, {}).get(ZC.COL_LABEL, ''),
                                              False  # no char replacement
                                              )
                              )

        insert_text.append( ', '.join(cols_list) )
        insert_text.append( ') VALUES ( ')
        insert_text.append( ', '.join(data_list) )
        insert_text.append( ');' )
        # query
        self.query(''.join(insert_text))

        # get last id
        return self.getLastId(ZC.TCN_AUTOID, name)


    def simpleUpd( self,
                   name,
                   origcols_dict,
                   entry_dict,
                   autoid ):
        """\brief insert changed values into the database"""
        if isinstance(autoid, StringType):
            autoid = int(autoid)

        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(autoid, IntType), \
               ZC.E_PARAM_TYPE % ('autoid', 'IntType', autoid)

        # build update query text
        query_text = []
        value_text = []

        query_text.append('UPDATE %s SET' % (name) )
        for colname in entry_dict:
            if colname in origcols_dict:
                field = origcols_dict[colname]
            elif colname in ZC._edit_tracking_cols:
                field = ZC._edit_tracking_cols[colname]
            else:
                # rest is ignored
                field = None
            if field:
                value_text.append(' %s = %s' % ( colname,
                                                 self.checkType(
                                                    entry_dict.get(colname),
                                                    field.get(ZC.COL_TYPE),
                                                    False,
                                                    field.get(ZC.COL_LABEL)
                                                           )
                                                  )
                                 )


        if not value_text:
            return False
        query_text.append( ','.join(value_text) )

        query_text.append( ' WHERE autoid = %s;' % autoid )

        self.query( ''.join(query_text) )

        return True


    ############################################################################
    #
    # SQL function handling
    #
    ############################################################################
    def addFunctionSql(self, name, param, output, sql):
        """ \see SqlConnector.addFunctionSql """
        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)

        # TODO: shared test for existence if shared
        query_text = []
        query_text.append("CREATE FUNCTION %s(%s)" % (name, param))
        query_text.append("RETURNS %s" % output)
        query_text.append("AS '%s'" % sql)
        query_text.append("LANGUAGE 'sql';")
        self.query( '\n'.join(query_text) )


    def addFunction(self, function):
        """ \see SqlConnector.addFunction """
        self.query(function)


    def delFunctionSql(self, name, param):
        """\brief Deletes a SQL function from the database."""
        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)

        # TODO: shared test for other sharing managers
        self.query( 'DROP FUNCTION %s(%s);' % (name, param) )
