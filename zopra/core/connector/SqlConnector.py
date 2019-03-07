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
from importlib    import import_module
from time         import strftime, strptime
from types        import StringType, IntType, DictType, ListType

from zopra.core   import SimpleItem, ZC

# date mapping for convertDate
format_list = [ '%d-%m-%y',
                '%d-%m-%Y',
                '%d.%m.%y',
                '%d.%m.%Y',
                '%d %m %y',
                '%d %m %Y',
                '%d/%m/%y',
                '%d/%m/%Y',
                '%m.%y',
                '%m.%Y',
                '%m/%d/%y',
                '%m/%d/%Y',
                '%d\%m\%y',
                '%d\%m\%Y',
                ]


# dict of available connector classes and the corresponding db name (see DBInfo)
connectors = { 'Psycopg':  'PostgresConnector',
               'Psycopg2': 'PostgresConnector',
               'PyGreSQL': 'PostgresConnector',
               'PoPy':     'PostgresConnector',
               'MySQL':    'MySqlConnector',  }

# why is string converted to COL_TEXT (text)? shouldn't this be VARCHAR(255)? does this harm database speed?


def getConnector(context, connector_id, connection_id):
    """ This method creates and returns a new connector object for the available
        connection

    @param context
    @param connector_id
    @param connection_id
    @result SqlConnector
    """

    # works with aquisition
    connection = getattr(context, connection_id)

    # any way try parent
    if not connection:
        connection = getattr(context.getParentNode(), connection_id)

    # get the connector name, default is the base class
    name           = connectors.get(connection.database_type, 'SqlConnector')
    conmod         = import_module('zopra.core.connector.%s' % name)
    connectorClass = getattr(conmod, name)

    # create and return the connectorClass object
    return connectorClass(connector_id, connection_id)



class SqlConnector(SimpleItem):
    """ The SqlConnector class provides a base, abstract implementation for a
        database connection.
    """
    _className = 'SqlConnector'
    _classType = [_className]

    # different database use different LIKE operators for case insensitivity
    LIKEOPERATOR = 'LIKE'

    # date format for database operations
    format_new  = '%d.%m.%Y'

    type_map    = { 'string':      ZC.COL_TEXT,
                    'memo':        ZC.COL_TEXT,
                    'int':         ZC.COL_INT4,
                    'singlelist':  ZC.COL_INT4,
                    'date':        ZC.COL_DATE,
                    'float':       ZC.COL_FLOAT,
                    'bool':        ZC.COL_INT4,
                    'int8':        ZC.COL_INT8,
                    'currency':    ZC.COL_CURRENCY
                    }


    def __init__(self, id, connection_id):
        """ Initialize the SQL Part

        @param connection_id   The argument \a connection_id contains the id of
                               the connection object that should be used.
        @param shared_connection_id The argument \a shared_connection_id
                               contains as well a id to a connection object but
                               for one that can handle queries system wide.
        """
        SimpleItem.__init__(self, id, id)
        self.connection_id        = connection_id
        self.conn                 = None


    def _getConnection(self):
        """ This method returns the correct connection object.

        @result SQLConnection
        """
        # get DB adapter
        zcon = getattr(self, self.connection_id)
        # get connectionpool from Adapter
        connection = zcon()
        # connection is a pool representation of the database connection (per Thread) (for mysql)

        return connection


    def query(self, query_text):
        """ This method executes a SQL query.

        The implementation of this method returns the result of the query. 
        It is abstract in SqlConnector baseclass (not implemented).

        @param query_text  - The argument \a query_text contains the complete
                             SQL query string.
        @return result
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def escape_sql_name(self, name):
        """ Escape SQL names (cols and tables), default: do nothing"""
        return name


#
# table handling
#

    def convertDate(self, old_date):
        """\brief Converts different date formats in european standard.

        These function is only for converting date types before inserting in a
        database!

        @param old_date  The argument \a date is a date that should be changed
                           into a new format.
        @result String with new date or 'NULL', otherwise an empty string.
        """
        if not old_date:
            return 'NULL'

        old_date = str(old_date).strip()

        # set this to '' to differentiate between not old_date
        # and no conversion found
        new_date = ''

        for format_old in format_list:
            try:
                return strftime(self.format_new, strptime(old_date, format_old))
            except ValueError:
                pass

        return new_date


    def checkType(self, value, column_type, operator = False, label = None, do_replace = True):
        """\brief makes all standard conversions and checking for supported Types
                    and returns altered value-string.
                    Returns an operator as well, if param operator is True
        """
        # BUG: user can cause misbehaviour by mixing keywords... redesign to brake
        #      non-fitting parts into conjunctions (need col-name for that)

        # first some checks

        # value = None leads to problems with str(value)
        if not (value is None or isinstance(value, ListType)):
            if not isinstance(value, unicode):
                if isinstance(value, str):
                    try:
                        value = unicode(value, 'utf8')
                    except UnicodeDecodeError:
                        pass
                else:
                    value = unicode(value)
            value = value.strip()
            pos_to  = value.find( '_to_' )
            # inserts of __ in text should work -> operator indicates search
            pos_sep = value.find( '__'   ) if operator else -1
            pos_lt  = value.find( '_<_'  )
            pos_lte = value.find( '_<=_'  )
            pos_gt  = value.find( '_>_'  )
            pos_gte = value.find( '_>=_'  )

        # NULL (0 can be ignored because it was converted to '0' which is True
        if not value or value == 'NULL' or value == '_0_' or value == ['NULL']:
            value = 'NULL'
            oper  = 'IS'

        # lists for freetext-search-results
        elif isinstance(value, ListType):
            if '_not_ NULL' in value or '_not_NULL' in value:
                value = 'NOT NULL'
                oper  = 'IS'
            else:
                entry_list = map( lambda onevalue: self.checkType( onevalue,
                                                           column_type,
                                                           False,
                                                           label ),
                                  value
                                  )
                value = u'(%s)' % u', '.join(entry_list)
                oper  = 'IN'

        # check for _not_ NULL
        elif value.replace(' ', '') == '_not_NULL' or value.replace(' ', '') == '_not__0_':
            value = 'NOT NULL'
            oper  = 'IS'

        # we allow range searches with keyword _to_
        elif pos_to != -1:
            value = "%s and %s" % ( self.checkType( value[:pos_to].rstrip(),
                                               column_type,
                                               False,
                                               label ),
                                    self.checkType( value[pos_to + 4:].lstrip(),
                                               column_type,
                                               False,
                                               label )
                                    )
            oper = 'BETWEEN'

        elif pos_sep != -1:
            valuelist = value.split('__')
            oper   = 'IN'
            entry_list = map( lambda onevalue: self.checkType( onevalue.strip(),
                                                           column_type,
                                                           False,
                                                           label ),
                              valuelist
                              )
            value = u'(%s)' % u', '.join(entry_list)

        elif pos_lt != -1:
            oper  = '<'
            value = self.checkType( value[pos_lt + 3:].strip(),
                               column_type,
                               False,
                               label )
        elif pos_lte != -1:
            oper  = '<='
            value = self.checkType( value[pos_lte + 4:].strip(),
                               column_type,
                               False,
                               label )
        elif pos_gt != -1:
            oper  = '>'
            value = self.checkType( value[pos_gt + 3:].strip(),
                               column_type,
                               False,
                               label )
        elif pos_gte != -1:
            oper  = '>='
            value = self.checkType( value[pos_gte + 4:].strip(),
                               column_type,
                               False,
                               label )
        else:
            oper     = ''
            labelstr = ''
            if label:
                labelstr = ' for field %s' % label

            if not column_type:
                raise ValueError( 'No Type found%s.' % labelstr)

            if column_type == 'string' or column_type == 'memo':
                oper  = ''
                if do_replace:
                    # replace wildcards
                    value = value.replace( "*", "%" )

                # escape some characters
                value = value.replace( "\'", "\\\'" )

                # remove double escape for ' in text
                value = value.replace( "\\\\'", "\\\'")

                # we allow not like searches with keyword _not_
                if value.find('_not_') == 0:
                    value = value[5:].lstrip()
                    oper    = 'not '

                oper += self.LIKEOPERATOR
                value = "'" + value + "'"

            elif column_type == 'date':
                oper, value = self.checkDateValue(value, labelstr)

            elif column_type == 'int' or column_type == 'singlelist':

                # we allow != searches with keyword _not_
                if value.find('_not_') == 0:
                    value = value[5:].lstrip()
                    oper  = '<>'
                else:
                    oper  = ' = '
                try:
                    int(value)
                except ValueError:
                    label = "You inserted a wrong value%s: %s (type: %s, datatype: %s)."
                    label = label % (labelstr, value, column_type, str(type(value)))
                    raise ValueError( label )

            elif column_type == 'float' or column_type == 'currency':
                # we allow != searches with keyword _not_
                if value.find('_not_') == 0:
                    value = value[5:].lstrip()
                    oper  = '<>'
                else:
                    oper  = ' = '
                try:
                    float(value)
                except ValueError:
                    label = "You inserted a wrong value%s: %s (type: %s)."
                    label = label % (labelstr, value, column_type)
                    raise ValueError( label )

            elif column_type == 'bool':
                oper = ' = '
                if value and value != 'NULL' and value != '0':
                    value = 1
                else:
                    # for add/edit there is no difference between NULL and not there
                    # it all results to a NULL value in the column
                    # so for search, we can look for anything (True) or NULL (False)
                    # but for add/edit it is important that the int 0 is translated to NULL
                    value = 'NULL'
                    oper = ' IS '

            elif column_type == 'multilist' or column_type == 'hierarchylist':

                raise ValueError('checkType called on multi- or hierarchylist')

            else:
                oper  = '='

        return (unicode(value), unicode(oper)) if operator else unicode(value)


    def checkDateValue(self, value, labelstr = ''):
        """\brief check date values in extra function for overwrite possibility"""
        value = value.replace("*", "%")
        oper  = ''
        if value.find('_not_') == 0:
            value = value[5:].lstrip()
            oper  = 'not '

        if value.find('%') == -1:
            newvalue = self.convertDate(value)
            if not newvalue:
                raise ValueError( 'Wrong Date Format%s (%s).' % (labelstr, value) )
            else:
                value = newvalue

        value = u"'%s'" % value
        oper += self.LIKEOPERATOR
        return oper, value


    def convertType(self, col_type):
        """ This method converts ZopRA-intern types to DB-types.

        If col_type is not available this method will raise a ValueError
        exception.

        @param  coltype - ZopRA column type
        @result string  - database dependent column type
        """
        assert ZC.checkType('col_type', col_type, StringType)

        return self.type_map.get(col_type, ZC.COL_TEXT)


    def getColumnDefinition(self, cols_dict):
        assert ZC.checkType('cols_dict', cols_dict, DictType)

        cols_str = []
        for col in cols_dict:

            # type conversion
            dbtype      = ' %s' % self.convertType(cols_dict[col][ZC.COL_TYPE])

            # default value
            col_default = cols_dict[col].get(ZC.COL_DEFAULT)
            default     = ' DEFAULT %s' % col_default if col_default else ''

            # reference value
            col_ref     = cols_dict[col].get(ZC.COL_REFERENCE)
            reference   = ' REFERENCES %s' % col_ref if col_ref else ''

            # join the column statement
            cols_str.append('%s%s%s%s' % (self.escape_sql_name(col), dbtype, default, reference) )

        return ', '.join(cols_str)


    def testForTable(self, name):
        """ Test if the table already exists.

        @param name           The argument \a name is a string with the
                              full name of a table.

        @return Boolean       Returns True if the table exists; otherwise False.
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def testForColumn(self, mgrid, table, column):
        """ Test if the column already exists in table.

        @param manager        The argument \a manager is a string with the
                              manager id.

        @param table           The argument \a table is a string with the
                              fullname of a table.

        @param column         The argument \a column is a string with the
                              fullname of a column.

        @return Boolean       Returns True if the column exists in table, otherwise False
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def createTable(self, name, cols_dict, edit_tracking = True):
        """ This method adds a SQL table to an existing database.

        @param name          - string containing the table name
        @param cols_dict     - dictionary containing the column definition
        @param edit_tracking - if enabled special columns for tracking the
                               edit changes will be added; default is True.
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def dropTable(self, table_name):
        """ This method drops a table from the database.

        @param table_name - string with the name of the table
        """
        assert ZC.checkType('table_name', table_name, StringType)

        self.query('DROP TABLE %s' % table_name)


    ############################################################################
    #
    # index handling
    #
    ############################################################################
    def createIndex(self, name, column):
        """ This method creates an index for table on the specified \a column.

        @param name   - string containing the table name
        @param column - string containing the column name
        """
        assert ZC.checkType('name', name, StringType)
        assert ZC.checkType('column', column, StringType)

        self.query("CREATE INDEX %s_index_%s ON %s (%s)" % ( name,
                                                             column,
                                                             name,
                                                             column ) )

    ############################################################################
    #
    # select handling
    #
    ############################################################################
    def simpleIns(self, name, origcols_dict, entry_dict):
        """ insert into table """
        assert ZC.checkType('name', name, StringType)

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
            if entry_dict[col] is None         or  \
               entry_dict[col] == 'NULL'       or  \
               entry_dict[col] == 'None':
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
                col_type = 'int'
            else:
                raise ValueError('No ColType found')

            # build proper data entries
            data_list.append( self.checkType( entry_dict[col],
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


    def getLastId(self, id_field, table_name, where = ''):
        """ This method returns the last id from id_field.

        @param  id_field   - name of the field containing the id
        @param  table_name - name of the table
        @param  where      - additional where clause
        @result integer    - max value of the id field
        """
        result = self.query( 'SELECT max(%s) FROM %s%s' % ( id_field,
                                                            table_name,
                                                            where ) )
        return result[0][0] if result and result[0][0] else 0


    def simpleUpd( self,
                   name,
                   origcols_dict,
                   entry_dict,
                   autoid ):
        """\brief insert changed values into the database"""
        if isinstance(autoid, StringType):
            autoid = int(autoid)

        assert ZC.checkType(ZC.TCN_AUTOID, autoid, IntType)
        assert ZC.checkType('name', name, StringType)

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


    def simpleSel( self,
                   name,
                   col_list,
                   origcols_dict,
                   where_dict):
        """\brief select requested columns of entries specified by entry_dict"""
        assert ZC.checkType('name', name, StringType)

        # build select query text
        query = []
        where = []

        query.append('SELECT %s FROM %s' % (', '.join(self.escape_sql_name(col) for col in col_list), name) )
        for colname in where_dict:
            if colname in origcols_dict:
                field = origcols_dict[colname]
            elif colname in ZC._edit_tracking_cols:
                field = ZC._edit_tracking_cols[colname]
            elif colname == ZC.TCN_AUTOID:
                field = { ZC.COL_TYPE:  'int',
                          ZC.COL_LABEL: 'Automatic No.' }
            else:
                # rest is ignored
                field = None
            if field:
                where.append('%s = %s' % ( colname,
                                                 self.checkType(
                                                                where_dict.get(colname),
                                                                field.get(ZC.COL_TYPE),
                                                                False,
                                                                field.get(ZC.COL_LABEL)
                                                                )
                                                )
                                  )
        if where:
            query.append('WHERE ' + ' AND '.join(where) )
        results = self.query( ' '.join(query) )
        res = []
        for result in results:
            entry = {}
            if col_list == ['*']:
                entry[ZC.TCN_AUTOID] = result[0]
            else:
                for index, col in enumerate(col_list):
                    entry[col] = result[index]
            res.append(entry)
        return res


    def simpleVal(self, col_dict, entry_dict):
        """\brief validate the entry against the column definition"""
        errors = {}
        for colname in entry_dict:
            if colname in col_dict:
                field = col_dict[colname]
            elif colname in ZC._edit_tracking_cols:
                field = ZC._edit_tracking_cols[colname]
            elif colname == ZC.TCN_AUTOID:
                # for search, autoid needs to be validated
                # TODO: +1 for autoid in ZC._edit_tracking_cols
                field = { ZC.COL_TYPE:  'int',
                          ZC.COL_LABEL: u'Automatic No.',
                          ZC.COL_INVIS: True }
            else:
                # rest is ignored
                continue

            val = entry_dict.get(colname)

            if field and val:
                try:
                    self.checkType( val,
                                    field.get(ZC.COL_TYPE),
                                    False,
                                    field.get(ZC.COL_LABEL)
                                    )
                except:
                    errors[colname] = ('Invalid input', val)
        return errors


    def simpleDel(self, table_name, autoid):
        """ This method is used to delete the entry with given autoid.

        @param name   - string containing the name of the table
        @param autoid - integer containing the entries autoid
        """
        assert ZC.checkType('table_name', table_name, StringType)
        assert ZC.checkType('autoid',     autoid,     IntType)
        self.query( "DELETE FROM %s where autoid = %s" % (table_name, autoid) )
        return True


    def getRowCount(self, name, where = ''):
        """ This method returns the number of rows matching the where clause.

        @param name  - string containing the table name
        @param where - string containing the where clause
        @result row count
        """
        assert ZC.checkType('name', name, StringType)
        assert ZC.checkType('where', where, StringType)

        # handling of the case that the keyword WHERE is not already included
        if where and where.upper().find('WHERE') == -1:
            where = "WHERE " + where

        result = self.query( 'SELECT count(*) FROM %s %s' % (name, where) )
        return result[0][0] if result else None


    ############################################################################
    #
    # SQL function handling
    #
    ############################################################################
    def addFunctionSql(self, name, param, output, sql):
        """ This method creates a SQL function in the database.

        @param name   - string containing the function name
        @param param  - parameters of the function
        @param output -
        @param sql    -
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def addFunction(self, function):
        """ This method creates a SQL function in the database.

        @param function - string containing a SQL statement to create a stored
                          procedure
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def delFunction(self, name, param):
        """ This method deletes a SQL function from the database.

        @param name  - string containing the function name
        @param param - string containing the function parameters
        """
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)
