############################################################################
#    Copyright (C) 2008 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from copy         import deepcopy
from types        import StringType, IntType, DictType
from time         import ctime

#
# ZopRA Imports
#
from zopra.core                        import ZC
from zopra.core.connector.SqlConnector import SqlConnector

# overwrite _edit_tracking_cols, mysql doesn't like default values for datetime
_edit_tracking_cols = { ZC.TCN_CREATOR: { ZC.COL_TYPE:   'singlelist',
                                          ZC.COL_LABEL:  'Creator'},
                        ZC.TCN_DATE:    { ZC.COL_TYPE:   'date',
                                          ZC.COL_LABEL:  'Entry Date'},
                        ZC.TCN_EDITOR:  { ZC.COL_TYPE:   'singlelist',
                                          ZC.COL_LABEL:  'Last edited by'},
                        ZC.TCN_EDATE:   { ZC.COL_TYPE:   'date',
                                          ZC.COL_LABEL:  'Last edited on'},
                        ZC.TCN_OWNER:   { ZC.COL_TYPE:   'singlelist',
                                          ZC.COL_LABEL:  'Owner'}, }


class MySqlConnector(SqlConnector):
    """\brief SQL Connector Base Class"""
    _className  = 'MySqlConnector'
    _classType  = SqlConnector._classType + [_className]

    format_new  = '%Y-%m-%d'

    #
    # MySQL special: string to varchar(255), float to double
    #
    type_map           = SqlConnector.type_map
    type_map['string'] = 'VARCHAR(255)'
    type_map['float']  = 'DOUBLE'


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

        if(isinstance(query_text, unicode)):
            query_text = query_text.encode("utf8")

        conn = self._getConnection()
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
    def createTable(self, name, cols_dict, edit_tracking = True):
        """\brief Adds a SQL table to an existing database."""
        # Tests moved to manage_afterAdd to avoid system specific testForTable

        assert isinstance(name, StringType), \
               ZC.E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(cols_dict, DictType), \
               ZC.E_PARAM_TYPE % ('cols_dict', 'DictType', cols_dict)
        assert edit_tracking == True or edit_tracking == False, \
               ZC.E_PARAM_TYPE % ('edit_tracking',  'BooleanType', edit_tracking)

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
            if cols_copy[col].get(ZC.COL_PRIMARY_KEY):
                primary_keys.append(col)

        if primary_keys:
            create_text.append( ', PRIMARY KEY (%s)' %
                                ', '.join(primary_keys) )
        else:
            create_text.append(', PRIMARY KEY (autoid)')
        create_text.append(') ENGINE = InnoDB')

        # create table
        self.query(' '.join(create_text))


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

        for col in _edit_tracking_cols:
            if col not in cols_dict:
                cols_dict[col] = ZC._edit_tracking_cols[col]
        cols = cols_dict.keys()

        for col in cols:
            # don't save NULL values, saves a little bit string length
            # but store 0-values
            val = entry_dict.get(col, None)
            if val == 'NULL' or val == 'None':
                val = None

            if col == ZC.TCN_DATE and not val:
                # insert date, mysql doesn't like time default values
                val = ctime()

            # build col_list
            cols_list.append(col)

            # build data_list
            # get type of col
            if cols_dict.get(col):
                col_type = cols_dict[col][ZC.COL_TYPE]

            # this needs to be here to allow autoid overwriting
            elif col == 'autoid':
                col_type = 'int'
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
        result = self.query( 'SELECT LAST_INSERT_ID() FROM %s' % (name) )
        res    = result[0][0] if result and result[0][0] else 0
        return res if res else self.getLastId(ZC.TCN_AUTOID, name)


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
                value_text.append(' %s = %s' % ( colname,
                                                 self.checkType( val,
                                                                 field.get(ZC.COL_TYPE),
                                                                 False,
                                                                 field.get(ZC.COL_LABEL)
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
        """\brief validate the entry against the column definition"""
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
                                    field.get(ZC.COL_TYPE),
                                    False,
                                    field.get(ZC.COL_LABEL) )
                except:
                    errors[colname] = ('Invalid input', val)
        return errors
