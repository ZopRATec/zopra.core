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

#
# ZMOM Imports
#
from zopra.core           import SimpleItem
from zopra.core.CorePart  import COL_FLOAT,       \
                                 COL_TYPE,        \
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

E_PARAM_TYPE   = '[Error] Parameter %s has to be %s, but got %s.'

_edit_tracking_cols = { TCN_CREATOR: { COL_TYPE:    'singlelist',
                                       COL_LABEL:   'Creator'},
                        TCN_DATE:    { COL_TYPE:    'date',
                                       COL_LABEL:   'Entry Date',
                                       COL_DEFAULT: 'now()'},
                        TCN_EDITOR:  { COL_TYPE:    'singlelist',
                                       COL_LABEL:   'Last edited by'},
                        TCN_EDATE:   { COL_TYPE:    'date',
                                       COL_LABEL:   'Last edited on',
                                       COL_DEFAULT: 'now()'},
                        TCN_OWNER:   { COL_TYPE:    'singlelist',
                                       COL_LABEL:   'Owner'},
                        }

# dict of available connector classes and the corresponding db name (see DBInfo)
connectors = { 'Psycopg':  'PostgresConnector',
               'PyGreSQL': 'PostgresConnector',
               'PoPy':     'PostgresConnector',
               'MySQL':    'MySqlConnector',  }

type_map = { 'string':      COL_TEXT,
             'memo':        COL_TEXT,
             'int':         COL_INT4,
             'singlelist':  COL_INT4,
             'date':        COL_DATE,
             'float':       COL_FLOAT,
             'bool':        COL_INT4,
             'int8':        COL_INT8,
             'currency':    COL_CURRENCY
             }


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
    """\brief SQL Connector Base Class"""
    _className = 'SqlConnector'
    _classType = [_className]

    # different database use different LIKE operators for case insensitivity
    LIKEOPERATOR = 'LIKE'

    # date format for database operations
    format_new  = '%d.%m.%Y'


    def __init__ (self, id, connection_id):
        """\brief Initialise the ZMOM SQL Part

        \param connection_id   The argument \a connection_id contains the id of
                               the connection object that should be used.
        \param shared_connection_id The argument \a shared_connection_id
                               contains as well a id to a connection object but
                               for one that can handle queries system wide.
        """
        SimpleItem.__init__(self, id, id)
        self.connection_id        = connection_id
        self.conn                 = None


    def _getConnection(self):
        """ This method returns the correct connection object.

        @result SQLConnector
        """
        return getattr(self, self.connection_id)


    def query(self, query_text):
        """ This method executes a SQL query.

        Note that this function sets the environment to german, european for
        the date handling.

        @param query_text  - The argument \a query_text contains the complete
                             SQL query string.
        """

        conDA       = self._getConnection()
        connection  = conDA()

        # fetch info and result, but return the result only
        return connection.query(query_text)[1]

#
# table handling
#

    def convertDate(self, old_date):
        """\brief Converts different date formats in european standard.

        These function is only for converting date types before inserting in a
        database!

        \param old_date  The argument \a date is a date that should be changed
                           into a new format.
        \result String with new date or 'NULL', otherwise an empty string.
        """
        if not old_date:
            return 'NULL'

        old_date = str(old_date).strip()

        # set this to '' to differentiate between not old_date
        # and no conversion found
        new_date = ''

        for format_old in format_list:
            try:
                new_date = strftime(self.format_new, strptime(old_date, format_old))
                return new_date
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
            value   = str(value).strip()
            pos_to  = value.find( '_to_' )
            # inserts of __ in text should work -> operator indicates search
            if operator:
                pos_sep = value.find( '__'   )
            else:
                pos_sep = -1
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
                oper = 'IS'
            else:
                entry_list = map( lambda onevalue: self.checkType( onevalue,
                                                           column_type,
                                                           False,
                                                           label ),
                                  value
                                  )
                value = '(%s)' % ', '.join(entry_list)
                oper = 'IN'

        # check for _not_ NULL
        elif value.replace(' ', '') == '_not_NULL' or value.replace(' ', '') == '_not__0_':
            value = 'NOT NULL'
            oper    = 'IS'

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
            value = '(%s)' % ', '.join(entry_list)
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
                oper = ''
                value = str(value)
                if do_replace:
                    # replace wildcards
                    value = value.replace( "*", "%" )
                # escape some characters
                value = value.replace( "\'", "\\\'" )
                # remove double escape for ' in text
                value = value.replace( "\\\\'", "\\\'")

                # we allow not like searches with keyword _not_
                if str(value).find('_not_') == 0:
                    value = value[5:].lstrip()
                    oper    = 'not '
                oper += self.LIKEOPERATOR
                value = "'" + value + "'"

            elif column_type == 'date':
                oper, value = self.checkDateValue(value, labelstr)

            elif column_type == 'int' or column_type == 'singlelist':
                # we allow != searches with keyword _not_
                if str(value).find('_not_') == 0:
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
                if str(value).find('_not_') == 0:
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
                value = str(value)
                oper  = '='

        if operator:
            return (str(value), oper)

        else:
            return str(value)


    def checkDateValue(self, value, labelstr = ''):
        """\brief check date values in extra function for overwrite possibility"""
        value = value.replace("*", "%")
        oper  = ''
        if str(value).find('_not_') == 0:
            value = value[5:].lstrip()
            oper  = 'not '

        if value.find('%') == -1:
            newvalue = self.convertDate(value)
            if not newvalue:
                raise ValueError( 'Wrong Date Format%s (%s).' % (labelstr, value) )
            else:
                value = newvalue

        value = "'%s'" % value
        oper += self.LIKEOPERATOR
        return oper, value


    def convertType(self, coltype):
        """ This method converts ZopRA-intern types to DB-types."""
        return type_map.get(coltype, COL_TEXT)


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

        query_text = "SELECT * FROM pg_class WHERE relname LIKE '%s'" % name
        return bool(self.query(query_text))


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

        query_text  = "SELECT count(a.attname) AS tot FROM pg_catalog.pg_stat_user_tables AS t, pg_catalog.pg_attribute a "
        query_text += "WHERE t.relid = a.attrelid AND t.schemaname = 'public' "
        query_text += "AND t.relname = '%s%s'  AND a.attname = '%s';" % (mgrid.lower(), table, column)

        result = self.query(query_text)
        return bool(result[0][0])


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
        create_text.append( "autoid INT4 autoincrement," )

        if edit_tracking:
            create_text.append( self.getColumnDefinition(_edit_tracking_cols) )
            create_text.append(', ')

        # we have to take care of columns with the same name as edit_tracking_cols
        cols_copy = {}
        for key in cols_dict:
            if key not in _edit_tracking_cols:
                cols_copy[key] = cols_dict[key]

        add_cols = self.getColumnDefinition(cols_copy)
        if add_cols:
            create_text.append( add_cols )
            create_text.append( ', '     )

        # add the primary key
        primary_keys = []
        for col in cols_copy:
            if cols_copy[col].get(COL_PRIMARY_KEY):
                primary_keys.append(col)

        if primary_keys:
            create_text.append( ' PRIMARY KEY (%s)' % \
                                ', '.join(primary_keys) )
        else:
            create_text.append(' PRIMARY KEY (autoid)')
        create_text.append(');')

        # create table
        self.query(' '.join(create_text))


    def dropTable(self, name):
        """\brief Drops table from a database.
        """
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        self.query('DROP TABLE %s;' % name)


#
# index handling
#
    def createIndex(self, table, column):
        """\brief Creates an index for table ith specified column."""
        assert isinstance(table, StringType), \
               E_PARAM_TYPE % ('table', 'StringType', table)
        assert isinstance(column, StringType), \
               E_PARAM_TYPE % ('column', 'StringType', column)

        index_text = "CREATE INDEX %s_index_%s ON %s (%s); " % ( table,
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
                col_type = cols_dict[col][COL_TYPE]

            elif _edit_tracking_cols.get(col):
                col_type = _edit_tracking_cols[col][COL_TYPE]

            # this needs to be here to allow autoid overwriting
            elif col == 'autoid':
                col_type = 'int'
            else:
                raise ValueError('No ColType found')

            # build proper data entries
            data_list.append( self.checkType( entry_dict[col],
                                         col_type,
                                         False,
                                         cols_dict.get(col, {}).get(COL_LABEL, ''),
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
        return self.getLastId(TCN_AUTOID, name)


    def getLastId(self, idfield, name, wherestr = ''):
        """\brief get max entry of idfield"""
        query_text = 'SELECT max(%s) FROM %s%s;' % ( idfield,
                                                     name,
                                                     wherestr )
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
            if field:
                value_text.append(' %s = %s' % ( colname,
                                                 self.checkType(
                                                    entry_dict.get(colname),
                                                    field.get(COL_TYPE),
                                                    False,
                                                    field.get(COL_LABEL)
                                                           )
                                                 )
                                  )


        if not value_text:
            return False

        query_text.append( ','.join(value_text) )
        query_text.append( ' WHERE autoid = %s;' % autoid )

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

        query_text = "DELETE FROM %s where autoid = %s;" % (name, autoid)
        self.query( query_text )

        return True


    def getRowCount(self, name, wherestring = ''):
        """\brief Returns the number of rows matching where string."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        assert isinstance(wherestring, StringType), \
               E_PARAM_TYPE % ('wherestring', 'StringType', wherestring)

        if wherestring and wherestring.upper().find('WHERE') == -1:
            wherestring = "WHERE " + wherestring
        query_text = 'SELECT count(*) FROM %s %s;' % (name, wherestring)
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

        # TODO: shared test for existence if shared
        query_text = []
        query_text.append("CREATE FUNCTION %s(%s)" % (name, param))
        query_text.append("RETURNS %s" % output)
        query_text.append("AS '%s'" % sql)
        query_text.append("LANGUAGE 'sql';")
        self.query( '\n'.join(query_text) )

    def addFunction(self, function):
        """\brief create a function"""
        self.query(function)


    def delFunction(self, name, param):
        """\brief Deletes a function from the database."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)

        # TODO: shared test for other sharing managers
        self.query( 'DROP FUNCTION %s(%s);' % (name, param) )
