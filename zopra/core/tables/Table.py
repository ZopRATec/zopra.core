###########################################################################
#    Copyright (C) 2004 by by ZopRATec GbR                                #
#    <webmaster@ingo-keller.de>                                           #
# Copyright: See COPYING file that comes with this distribution           #
#                                                                         #
###########################################################################

from copy     import deepcopy
from types    import StringType, ListType, TupleType, DictType, BooleanType

from zope.interface.declarations            import implements

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                              import E_PARAM_TYPE, E_PARAM_FAIL
from PyHtmlGUI.kernel.hgTable               import hgTable

from PyHtmlGUI.widgets.hgLabel              import hgLabel, hgSPACE
from PyHtmlGUI.widgets.hgPushButton         import hgPushButton
from PyHtmlGUI.widgets.hgMultiList          import hgMultiList
from PyHtmlGUI.stylesheet.hgStyleSheetItem  import hgStyleSheetItem

#
# ZopRA Imports
#
from zopra.core import HTML, ZM_PM, ZM_SCM, SimpleItem, PropertyManager
from zopra.core.constants                   import TCN_AUTOID,     \
                                                   TCN_OWNER,      \
                                                   TCN_DATE,       \
                                                   TCN_CREATOR
from zopra.core.elements.Buttons            import mpfReset2Button, \
                                                   BTN_L_RESET2,    \
                                                   getPressedButton

from zopra.core.elements.Styles.Default     import ssiDLG_LABEL

from zopra.core.CorePart                    import COL_TYPE,       \
                                                   COL_LABEL,      \
                                                   COL_INVIS,      \
                                                   ZCOL_DATE,      \
                                                   ZCOL_SLIST,     \
                                                   ZCOL_INT
from zopra.core.tables.Filter               import Filter
from zopra.core.tables.TableCache           import TableCache
from zopra.core.tables.TableNode            import TableNode, TablePrivate

from zopra.core.dialogs                     import getStdDialog
from zopra.core.dialogs.TableEntryDialog    import TableEntryDialog
from zopra.core.security                    import SC_READ, SC_LREAD, SC_WRITE
from zopra.core.security.EntryPermission    import EntryPermission
from zopra.core.interfaces                  import IZopRATable, IGenericManager
from zopra.core.utils import getParentManager


# deprecated -> Table.ExportFlags
TE_TAB         = 0x0001
TE_XML         = 0x0002
TE_WITHHEADER  = 0x0004
TE_LOOKUPDATA  = 0x0008
TE_TRACKING    = 0x0010

# how much info will xml export provide
# table -> least, instance -> most info
# values are organized that if flag contains a certain lvl x
# all flag & y == True for all lvl y <= x
TE_LVLTABLE    = 0x0020
TE_LVLMGR      = 0x0060
TE_LVLPRODUCT  = 0x00e0
TE_LVLINSTANCE = 0x01e0

# continue at 0x0200 with unique flags
TE_WITHPROPERTIES = 0x0200


class Table(SimpleItem, PropertyManager):
    """\brief Table

    The Table contains functions that are related to table
    querying in the database.
    """
    _className = 'Table'
    _classType = [_className]

    meta_type  = 'ZopRATable'

    do_cache   = True

    implements(IZopRATable)

    manage_options = (  {'label': 'Overview',    'action': 'viewTab' },
                        {'label': 'Edit',        'action': 'editTab' },
                        {'label': 'Statistic',   'action': 'statsTab' },
                        {'label': 'Table Cache', 'action': 'cacheTab' },
                        {'label': 'Search Tree', 'action': 'searchTreeTab' },
                        # {'label': 'Management',  'action': 'managementTab' },
                     ) + PropertyManager.manage_options + SimpleItem.manage_options

    _properties = ({'id': 'do_cache',    'type': 'boolean',     'mode': 'w'},)

    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
    # enum ExportFlags
    Tab          = 0x0001
    Xml          = 0x0002
    WithHeader   = 0x0004
    LookupData   = 0x0008

    Full         = Xml | WithHeader | LookupData
    ExportFlags  = [ Tab, Xml, WithHeader, LookupData, Full ]

    # enum Order
    Asc          = 'asc'
    Desc         = 'desc'
    Order        = [ Asc, Desc ]

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def getName(self):
        """\brief Returns the tableName property."""
        return self.tablename

    def setName(self, name):
        """\brief Sets the table name to \a name."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        self.tablename = name

    name = property(getName, setName)

    # for security and logging, we need globally unique ids for tables
    # they are given via the table xml definition
    # there is a script somewhere to generate them, but I can't find it
    # it is a 12-digit string, use str(long(time.time() * 100))
    def setUId(self, uid):
        self._uid = uid


    def getUId(self):
        if hasattr(self, '_uid') and self._uid:
            return long(self._uid)


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__(self, name, tabledict = None, ebase = False, label = None, uid = None):
        """\brief Constructs a Table."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        assert tabledict == None or isinstance(tabledict, DictType), \
               E_PARAM_TYPE % ('tabledict', 'DictType or None', tabledict)

        # FIXME: What is this? shouldn't the tabledict be an empty dict if none is given?
        # the dict contains dicts like that one, but with key columnname
        if not tabledict:
            tabledict = { COL_TYPE: 'string',
                          COL_LABEL: '',
                          COL_INVIS: False }

        self._uid         = uid
        self.tablename    = name
        self.tabledict    = tabledict
        self.cache        = TableCache()
        self.treeTemplate = None
        self.ebase        = ebase
        self.do_cache     = True
        if label is not None:
            self.label = label
        else:
            self.label = ''


    def getManager(self):
        """ This method returns the owning manager.

        In very old installations the table was placed inside the manager
        directly.

        @deprecated This method exists for backwards compatibility and should be
                    removed as soon as possible.
        """
        message = 'No Manager found for Table Object via getParentNode()'
        return getParentManager(self, message)


    def processWhereString(self, idvalue, idfield):
        """\brief Build where-string from given id-value list pairs."""

        if not idvalue:
            return ''

        if not isinstance(idfield, ListType):
            # we have only one idfield
            idvalue = [idvalue]
            idfield = [idfield]

        mgr = self.getManager()

        if not len(idvalue) == len(idfield):
            raise ValueError(
                mgr.getErrorDialog('Internal Error. Lists do not match.') )

        wherepart = []

        for i in xrange(len(idvalue)):
            field       = self.getField(idfield[i])

            if not field:
                raise ValueError('Unknown field %s' % idfield[i])

            value, operator = mgr.forwardCheckType( idvalue[i],
                                         field[COL_TYPE],
                                         True,
                                         field.get(COL_LABEL) )
            wherepart.append('%s %s %s' % (idfield[i], operator, value))

        return ' WHERE %s' % (' and '.join(wherepart) )


    def getEmptyEntry(self):
        """\brief Returns an empty table entry
                  containing all keys but no values.
        """
        mgr   = self.getManager()
        entry = {}

        # normal cols

        cols_dict = self.getColumnTypes()

        # edit tracking

        m_product = mgr.getManager(ZM_PM)
        edit = m_product._edit_tracking_cols
        for field in edit:
            cols_dict[field] = self.getField(field)[COL_TYPE]

        # fill dict

        for field in cols_dict:
            ctype = cols_dict[field]
            if ctype == 'string' or ctype == 'memo':
                entry[field] = ''
            elif ctype == 'multilist':
                entry[field] = []
            else:
                entry[field] = None

        return entry


    def getEntry( self,
                  entry_id   = None,
                  data_tuple = None,
                  col_list   = None,
                  ignore_permissions = False ):
        """\brief Returns a table entry.

        If no entry was found the function will return \em None. For more than
        one entry it will throw an exception because only one entry for a
        primary key is expected.

        \param entry_id The argument \a entry_id contains the unique key for
                        the table.

        \param data_tuple
        \param col_list
        \param ignore_permissions The entry will not have a permission object and
        thus be useless for the generic GUI and entry functions, this option should
        be used by statistics and the security handling itself only!

        \return a description dictionary for the entry where the column names
        are the keys, otherwise None.

        \throw RuntimeError if the table or list wasn't found.
        \throw ValueError   if more than one entry was returned. Could be
                            something wrong with the index.
        """
        assert ( entry_id is not None or
                 (data_tuple is not None and col_list is not None)
                 )

        mgr = self.getManager()
        entry = None

        # caching first:
        if self.do_cache and entry_id:
            entry = self.cache.getItem(self.cache.ITEM, int(entry_id))

        if not entry:

            entry = {}

            # no luck
            assert mgr.id,         E_PARAM_FAIL % 'mgr.id'
            assert self.tabledict, E_PARAM_FAIL % 'tabledict'

            if not data_tuple or not col_list:

                # normal behaviour
                m_product  = mgr.getManager(ZM_PM)

                # get table definition
                cols_list   = self.tabledict.keys()

                entry_id = int(entry_id)

                # build query text
                query_text = ['SELECT ']

                # add edit tracking cols
                tracking = m_product._edit_tracking_cols
                for tfield in tracking.keys():
                    if tfield not in self.tabledict:
                        cols_list.append(tfield)

                # autoid
                if TCN_AUTOID not in self.tabledict:
                    cols_list.append(TCN_AUTOID)

                # get fields
                query_text.append(', '.join(cols_list))
                query_text.append(' FROM %s WHERE %s = %s' % (
                                                    mgr.id + self.tablename,
                                                    TCN_AUTOID,
                                                    entry_id ) )
                query_text = ''.join(query_text)

                # execute query
                results = m_product.executeDBQuery(query_text)

                # result handling

                # test for no result
                if not results:
                    return None

                # test result count
                if len(results) > 1:

                    # more than one result
                    msg = "More than one entry with the same index id %s in table %s"
                    msg = msg % ( entry_id, self.tablename )
                    raise ValueError( mgr.getErrorDialog(msg) )

                result = results[0]

            else:
                # data_tuple and col_list given to use directly
                cols_list = col_list
                result = data_tuple

            count = 0
            for field in cols_list:
                if not result[count] is None:
                    entry[field] = result[count]

                    # TODO: better date time handling necessary
                    if hasattr( entry[field], 'strftime'):
                        entry[field] = entry[field].strftime('%d.%m.%Y')

                else:
                    # empty entry
                    ftype = self.getField(field)[COL_TYPE]
                    if ftype == 'singlelist':
                        entry[field] = None
                    else:
                        entry[field] = ''

                count += 1

            # add multilist ids
            autoid = entry[TCN_AUTOID]

            multilists = mgr.listHandler.getLists(self.tablename, types = ['singlelist'], include = False)

            for multilist in multilists:
                field = multilist.listname
                entry[field] = multilist.getMLRef(autoid)

                # and the notes if enabled
                if multilist.notes:
                    for item in entry[field]:
                        key = field + 'notes' + str(item)
                        entry[key] = multilist.getMLNotes(autoid, item)

            # caching
            if self.do_cache:
                self.cache.insertItem( self.cache.ITEM,
                                       int(autoid),
                                       entry )

        # copy entry
        entry = deepcopy(entry)

        # because security settings can change without inducing cache reload,
        # we decided to not have security objects cached
        # they have to be reloaded each time, but they use caching too

        if ignore_permissions:
            return entry

        # get the entrypermissions based on ebase and SBAR security settings
        perms = mgr.getEntryPermissions(entry.get('acl'), self.tablename)

        # add permissions if the owner is requesting the entry
        if self.isOwner(entry):
            perms.extend([SC_READ, SC_LREAD, SC_WRITE])
            owner = True
        else:
            owner = False

        # create entry permission object
        pobj = EntryPermission(entry, perms, owner)

        # TODO: raise Error when permissions don't fit? should this be done here?
        # a lot of testing is necessary before we can activate this in a live system
        # check permissions
        # if not (pobj.hasPermission(SC_READ) or pobj.hasPermission(SC_LREAD)):
        #    pass

        # set entry permission
        entry['permission'] = pobj

        return entry


    def isOwner(self, entry):
        """\brief Checks for creator permissions on the entry
        """
        # security handling with security manager
        m_sec = self.getManager().getHierarchyUpManager(ZM_SCM)

        # check ownerid of the entry
        if m_sec:
            ownerid      = entry.get(TCN_OWNER)
            owner        = m_sec.getUserByCMId(ownerid).get('login')

            return m_sec.getCurrentLogin() == owner

        # no security management, can't distinguish users -> everybody is owner
        return True


    def getField(self, name):
        """\brief Returns the definition dict for a single column.

        \param name   The argument \a name contains the name of the specified
                      column.

        \return The definition dictionary; otherwise a emtpy dictionary
        """
        mgr       = self.getManager()
        m_product = mgr.getManager(ZM_PM)

        # shortcut for ordinary autoid field
        if name == TCN_AUTOID:
            return { COL_TYPE:  'int',
                     COL_LABEL: 'Automatic No.',
                     COL_INVIS: True }

        # get field description from manager tables
        elif self.tabledict.get(name):
            return self.tabledict[name]

        elif mgr.listHandler.hasList(self.tablename, name):
            # singlelists are covered above, the other lists are handled
            # seperately but this function is used to test for existence,
            # so we return something!
            lobj = mgr.listHandler.getList(self.tablename, name)
            return { COL_TYPE:  lobj.listtype,
                     COL_LABEL: lobj.getLabel(),
                     COL_INVIS: lobj.invisible }

        # get field description from edit tracking fields
        # no elif here (else same-name cols will be ignored)
        if m_product._edit_tracking_cols.get(name):
            return m_product._edit_tracking_cols[name]

        # nothing really found
        return {}


    def getEntryBy(self, entry_id, idfield):
        """\brief get one entry by other field than autoid"""
        autoid = self.getEntryAutoid(entry_id, idfield)
        if autoid:
            return self.getEntry(autoid)
        return {}


    def getEntryAutoid(self, entry_id, idfield):
        """\brief Shortcut to get the autoid for a field that uses selfmade ids.

        \return The autoid of the field, otherwise None.
        """
        # TODO: convert to tableNode usage!
        # faster with direct implementation
        mgr       = self.getManager()
        m_product = mgr.getManager(ZM_PM)

        # caching first (not entirely sure where this is needed, why ask for the
        # autoid if the autoid is given?)
        if self.do_cache and idfield == TCN_AUTOID and entry_id:
            item = self.cache.getItem(self.cache.ITEM, int(entry_id))
            if item:
                return item.get(TCN_AUTOID)

        where = self.processWhereString(entry_id, idfield)
        query = 'select %s from %s%s%s'
        query = query % ( TCN_AUTOID,
                          mgr.id,
                          self.tablename,
                          where )
        results = m_product.executeDBQuery(query)
        if results:
            if len(results) > 1:
                errstr = 'getEntryAutoid got id which is not unique: %s %s'
                errstr = errstr % (idfield, entry_id)
                err = mgr.getErrorDialog(errstr)
                raise ValueError(err)
            else:
                return results[0][0]


    def addEntry( self,
                  descr_dict,
                  required         = None,
                  overwrite_autoid = False,
                  log              = True ):
        """\brief Adds an entry to a specified table.

        The function get the table definition from the
        \c _manager_table_dict. If it fails it will raise a
        \em RuntimeError.\n

        The \c table_entry information will be extracted from the \c descr_dict
        and the \c required fields will be tested if they are available. If a
        required field entry is missing the function will raise a
        \em ValueError.\n

        If a contact manager is available it will also store the creator and
        editor information. The creator and editor is every time the logged in
        user.\n

        After the insert the function writes a entry to the product manager
        log.\n

        \param table  The argument \a table specifies the table where the entry
                      should be inserted into. But it doesn't have already the
                      manager id prefix.

        \param descr_dict  The \a descr_dict can contain more than the
                           necessary fields but only the fields from the table
                           definition will be saved.

        \param required  The argument \a required is a list of column names
                         which specify the necessary filled fields. But it is
                         not limited to the fields from the table definition.

        \param overwrite_autoid  Deprecated. If the descr_dict contains a key
                                 'autoid', its value will be used for the new
                                 entry.

        \param log  The \a log argument is boolean and can be used to turn off
                    logging (for a huge number of inserts to speed up).

        \throw RuntimeError if no table definition was found
        \throw ValueError if a required field is not filled
        """
        assert isinstance(log, BooleanType)
        assert isinstance(overwrite_autoid, BooleanType)
        if required is None:
            required = []

        mgr       = self.getManager()
        m_product = mgr.getManager(ZM_PM)

        # build the table entry
        entry_dict = {}
        for name in self.tabledict.keys():
            entry_dict[name] = descr_dict.get(name)

        # this is to get date and creator for import correct
        for name in m_product._edit_tracking_cols:
            entry_dict[name] = descr_dict.get(name)

        # autoid - workaround
        if overwrite_autoid and descr_dict.get(TCN_AUTOID):
            entry_dict[TCN_AUTOID] = descr_dict.get(TCN_AUTOID)

        # check if all required fields are present
        missing = []
        for field in required:

            # field is not in entry_dict and no multilist
            if not ( ( entry_dict.get(field, None) is not None and
                       entry_dict.get(field, None) != 'NULL' ) or
                     ( mgr.listHandler.hasList(self.tablename, field) and
                       descr_dict.get(field) ) ):
                missing.append( field )

        if missing:

            if len(missing) > 1:
                plural = 's'

            else:
                plural = ''

            missing = ', '.join(missing)
            error   = 'Field%s %s required.' % ( plural, missing )
            dialog  = mgr.getErrorDialog( error )
            raise ValueError( dialog )

        # TODO: check insert permission

        # check ebase, get acl
        if mgr.checkEBaSe(self.tablename):
            m_sec = mgr.getHierarchyUpManager(ZM_SCM)
            acl = m_sec.getCreationAcl(self.getUId(), mgr.getZopraType())
            if acl:
                entry_dict['acl'] = acl
        lastid = m_product.simpleInsertInto( mgr.id + self.tablename,
                                             self.tabledict,
                                             entry_dict,
                                             log,
                                             self._uid )

        # handle multilist entries
        multilists = mgr.listHandler.getLists(self.tablename, types = ['singlelist'], include = False)

        for multilist in multilists:
            name = multilist.listname
            if name in descr_dict:
                valuelist = descr_dict[name]
                if not isinstance(valuelist, ListType):
                    valuelist = [valuelist]

                # insert all entries in valuelist
                for value in valuelist:
                    notes = descr_dict.get(name + 'notes' + str(value), '')
                    multilist.addMLRef( lastid, value, notes )

        # invalidate cache
        if self.do_cache:
            self.cache.invalidate()

        return lastid


    def deleteEntry( self, entry_id, idfield = TCN_AUTOID ):
        """\brief delete one entry with given id from table.
                  Does no cascation. For that, overwrite the manager's
                  prepareDelete hook.
        """
        mgr    = self.getManager()
        m_prod = mgr.getManager(ZM_PM)

        if not entry_id:
            return False

        if idfield != TCN_AUTOID:
            # this works for lists of idfield/entry_id as well
            entries = self.getEntries( entry_id,
                                       idfield )
            if entries:
                autoid = entries[0][TCN_AUTOID]
            else:
                return False
        else:
            autoid = entry_id

        # get entry for logging
        name = mgr.id + self.tablename
        entry = self.getEntry(autoid, ignore_permissions = True)

        if not entry:
            return False

        # handle multilists
        multilists = mgr.listHandler.getLists(self.tablename, types = ['singlelist'], include = False)

        for multilist in multilists:
            multilist.delMLRef(autoid)

        # cache invalidation (has to be done after getEntry!)
        if self.do_cache:
            self.cache.invalidate(autoid)

        # deletion in db, logging and return
        return m_prod.simpleDelete(name, autoid, self._uid, entry)


    def updateEntry( self,
                     descr_dict,
                     entry_id,
                     idfield = TCN_AUTOID,
                     required = None,
                     orig_entry = None ):
        """\brief inserts changed values into the database"""
        mgr = self.getManager()
        if not required:
            required = []

        # check descr_dict
        # self.checkDescrDict(table, descr_dict)

        # bug: update only updates given fields (this part would have deleted
        #      entries in not-given multilist)
        # emptied multilists have to be checked in edit-function

        if entry_id   and \
           descr_dict:

            # check if all required fields are present
            missing = []
            for field in required:
                if not ( ( descr_dict.get(field, None) is not None and
                           descr_dict.get(field, None) != 'NULL' ) or
                         ( mgr.listHandler.hasList(self.tablename, field) and
                           descr_dict.get(field) ) ):
                    missing.append( field )

            if missing != []:
                if len(missing) > 1:
                    plural = 's'
                else:
                    plural = ''
                missing = ', '.join(missing)
                error   = 'Field%s %s required.' % ( plural, missing )
                dialog  = mgr.getErrorDialog( error )
                raise ValueError( dialog )

            # get autoid if necessary

            if idfield != TCN_AUTOID:
                # this works for lists of idfield/entry_id as well
                entries = self.getEntries( entry_id,
                                           idfield )
                # more than one entry should never happen
                if len(entries) != 1:
                    msg = 'Database integrity seems compromised, more than one entry found:'
                    msg += ' Idfield: %s Id: %s NumEntries: %s Table: %s'
                    msg = msg % (idfield, entry_id, len(entries), self.tablename)
                    raise ValueError(msg)

                autoid = entries[0][TCN_AUTOID]

            else:
                autoid = entry_id

            # get ProductManager
            m_product = mgr.getManager(ZM_PM)

            # old entry (for now without permissions to be faster)
            # using the orig_entry param to speed up this part
            entry = orig_entry or self.getEntry(autoid, ignore_permissions = True)

            # check permission of db entry
            # TODO: implement permission check

            try:
                # update Entry
                res = m_product.simpleUpdate( mgr.id + self.tablename,
                                            self.tabledict,
                                            descr_dict,
                                            autoid,
                                            self._uid,
                                            entry )

                # update Multi/Hierarchy-Lists
                multilists = mgr.listHandler.getLists(self.tablename, types = ['singlelist'], include = False)

                for multilist in multilists:
                    # only update multi lists, if key in dict
                    if multilist.listname in descr_dict:
                        # we have a multiselectlist/hierarchylist as attribute
                        valuelist = descr_dict[multilist.listname]
                        # make sure we really have a list (this is deprecated and only viable for old plugins)
                        if not valuelist:
                            valuelist = []
                        # make sure it is not just one string entry (this is deprecated and only viable for old plugins)
                        if not isinstance(valuelist, ListType):
                            valuelist = [valuelist]
                        # turn the id values into int
                        valuelist = [int(a) for a in valuelist]

                        # compare descr_dict->valuelist with entry->attr
                        target = entry[multilist.listname]

                        for item in target:
                            # item has been removed, delete the MLRef
                            if item not in valuelist:
                                multilist.delMLRef(autoid, item)
                                res = True
                            else:
                                # item still in there, check notes
                                if multilist.notes:
                                    notes_new = descr_dict.get(multilist.listname + 'notes' + unicode(item))
                                    notes_new = notes_new != 'NULL' and notes_new or None
                                    notes_old = multilist.getMLNotes(autoid, item)
                                    # notes differ, change them in the DB
                                    if notes_new != notes_old:
                                        multilist.updateMLNotes(autoid, item, notes_new)

                                # remove the item (remaining items will be added)
                                valuelist.remove(item)
                        # insert remaining new items
                        for item in valuelist:
                            # check for notes
                            notes = descr_dict.get(multilist.listname + 'notes' + unicode(item), '')
                            multilist.addMLRef( autoid, item, notes )
                            res = True
            except Exception, all_:
                # overwrite the args tuple with a new tuple containing the descr_dict
                all_.args = all_.args + (descr_dict,)
                raise

            # caching
            if self.do_cache:
                self.cache.invalidate(autoid)

            return res


    def validateEntry(self, descr_dict, required = None):
        """\brief validate the entry (required fields and type check)"""
        mgr = self.getManager()
        if not required:
            required = []

        # get ProductManager
        m_product = mgr.getManager(ZM_PM)

        errors = m_product.simpleValidate( self.tabledict,
                                           descr_dict)

        # check if all required fields are present
        for field in required:
            if not ( descr_dict.get(field) not in [None, '', 'NULL'] or
                     ( mgr.listHandler.hasList(self.tablename, field) and
                       descr_dict.get(field) ) ):
                errors[field] = ('Input required', '')
        return errors
#
# global table functions
#


    def exportTab(self, columnList = None, autoidList = None, flags = None, delim = '\t', multilines = 'replace'):
        """\brief Exports a table from the database as tab separeted text file.

        \param tableName  The name of the table without manager prefix.
        \param columnList List of columns to be exported.
        \param autoidList List of autoids for restricted export.
        \param flags      Flags for common parameters.
        \param delim      Delimiter for attributes in one line
        \param multilines remove|replace|keep for handling of linebreaks in attributes
        """

        # TODO: use temporary file to cache the results on harddisk
        mgr       = self.getManager()
        tableName = self.tablename

        if columnList is None:
            columnList = []

        if not autoidList:
            autoidList = []

        m_product   = mgr.getManager(ZM_PM)
        export_list = []

        # check columnList
        for column in columnList:
            if not self.getField(column):
                message = 'Column [%s] not found in table [%s]' % ( column,
                                                                    tableName )
                raise RuntimeError( mgr.getErrorDialog( message ) )

        if not columnList:
            # use all cols
            columnList = ( self.getColumnTypes().keys() )
            # enable tracking cols (autoid is missing from self.getColumnTypes)
            flags = flags | TE_TRACKING

        # add tracking lists always when flag is given
        if flags & TE_TRACKING:
            for col in m_product._edit_tracking_cols:
                if col not in columnList:
                    columnList.append(col)

            # add autoid column if not present
            if TCN_AUTOID not in columnList:
                columnList.insert(0, TCN_AUTOID)

        # get table count
        if autoidList:
            row_count = len(autoidList)

        else:
            row_count = self.getRowCount()

            if isinstance(row_count, StringType):
                row_count = int(row_count)

        lookup_dict = {}

        # find lookup lists
        if flags & TE_LOOKUPDATA:
            for column in columnList:
                if mgr.listHandler.hasList(self.tablename, column):
                    lookup_dict[column] = column
                    # TODO: check for images/files, add to image_cols, check later
                    # maybe use name:url instead of the html-value that comes from generic

        if not autoidList:
            # get all entry autoids
            autoidList = self.getEntryAutoidList()

        if not autoidList:
            # still empty, return nothing
            return export_list

        # write header
        if flags & TE_WITHHEADER:
            export_list.append( delim.join(columnList) )

        # write data to temporary file
        for result in autoidList:

            if isinstance(result, TupleType):
                entry_id = result[0]
            else:
                entry_id = result

            entry      = self.getEntry(entry_id)

            new_result = []

            for col in columnList:

                if flags & TE_LOOKUPDATA and lookup_dict.get(col):
                    colobj = mgr.listHandler.getList(self.tablename, col)
                    value = colobj.getValueByAutoid(entry.get(col, ''))

                    if isinstance(value, ListType):
                        value = ', '.join(value)

                    one_res = unicode(value)

                else:
                    value = entry.get(col, '')

                    if isinstance(value, ListType):
                        # flatten list (remove double, remove empty)
                        value = dict([(unicode(c), None) for c in value if c]).keys()

                        value = ', '.join(value)

                    one_res = unicode(value)
                # call an export preparation hook
                one_res = mgr.prepareFieldForExport(self.tablename, col, one_res, entry)

                # remove carriage return to be on the safe side
                one_res = one_res.replace('\r', '')

                # check for special chars that induce escaping
                if one_res.find(delim) != -1 or one_res.find('"') != -1 or one_res.find('\n') != -1:
                    one_res = '"%s"' % one_res.replace('"', '""')

                # handle linebreaks
                # third option is 'keep' -> do nothing
                if multilines == 'remove':
                    one_res.replace('\n\n', '\n').replace('\n', ' ')
                elif multilines == 'replace':
                    one_res.replace('\n', '\\n')

                new_result.append(one_res)

            # build line
            line = delim.join(new_result)
            export_list.append( line )

        return export_list


    def exportXML(self, columnList = None, autoidList = None, flags = None):
        """\brief Exports database contents to xml.

        \param columnList List of columns to be exported.
        \param autoidList List of autoids for partial export.
        \param flags      Flags for common parameters.
        """
        if flags & TE_WITHHEADER:
            flags = flags | TE_LVLINSTANCE
            flags = flags | TE_WITHPROPERTIES

        # TODO: use temporary file to cache the results on harddisk for speedup

        mgr       = self.getManager()
        tableName = self.tablename

        if columnList is None:
            columnList = []

        if not autoidList:
            autoidList = []

        m_product   = mgr.getManager(ZM_PM)
        export_list = []

        # check columnList
        for column in columnList:
            if not self.getField(column):
                message = 'Column [%s] not found in table [%s]' % ( column,
                                                                    tableName )
                raise RuntimeError( mgr.getErrorDialog( message ) )

        if not columnList:
            # use all columns
            columnList = ( self.getColumnTypes().keys() )

            # enable tracking cols (autoid is missing from self.getColumnTypes)
            flags = flags | TE_TRACKING

        # add tracking lists always when flag is given
        if flags & TE_TRACKING:
            for col in m_product._edit_tracking_cols:
                if col not in columnList:
                    columnList.append(col)

            # add autoid column if not present
            if TCN_AUTOID not in columnList:
                columnList.insert(0, TCN_AUTOID)


        # get table count
        if autoidList:
            row_count = len(autoidList)

        else:
            row_count = self.getRowCount()
            if isinstance(row_count, StringType):
                row_count = int(row_count)

        lookup_dict = {}
        # find lookup lists
        if flags & TE_LOOKUPDATA:
            for column in columnList:
                if mgr.listHandler.hasList(self.tablename, column):
                    lookup_dict[column] = column
                    # TODO: check for images/files, add to image_cols, check later
                    # maybe use name:url instead of the html-value that comes from generic

        if not autoidList:
            autoidList = self.getEntryAutoidList()

        if not autoidList:
            # still nothing, return empty list
            return export_list

        # write data to temporary file
        # build xml
        export_list.append('<?xml version="1.0"?>')

        pad = ''

        # create header
        abs_url = mgr.absolute_url()
        rel_url = mgr.absolute_url(relative = True)

        if flags & TE_LVLINSTANCE:
            export_list.append('<instance>')
            pad += '\t'

            # properties
            if flags & TE_WITHPROPERTIES:
                base_url = abs_url[:-len(rel_url)]

                export_list.append('%s<url>%s</url>' % (pad, base_url ) )

        if flags & TE_LVLPRODUCT:
            export_list.append('%s<product id=\'%s\'>' % (pad, m_product.getId()) )
            pad += '\t'

            # properties
            if flags & TE_WITHPROPERTIES:
                path = m_product.absolute_url(relative = True)
                export_list.append('%s<title>%s</title>' % (pad, m_product.getTitle() ) )
                export_list.append('%s<path>%s</path>' % (pad, path ) )

        if flags & TE_LVLMGR:
            export_list.append('%s<manager id=\'%s\'>' % (pad, mgr.getId()) )
            pad += '\t'

            # properties
            if flags & TE_WITHPROPERTIES:
                export_list.append('%s<title>%s</title>' % (pad, mgr.getTitle() ) )
                export_list.append('%s<class>%s</class>' % (pad, mgr.getClassName() ) )
                export_list.append('%s<zopratype>%s</zopratype>' % (pad, mgr.getZopraType() ) )
                export_list.append('%s<path>%s</path>' % (pad, rel_url ) )

        if flags & TE_LVLTABLE:
            export_list.append('%s<table name=\'%s\'>' % (pad, self.getName()) )
            pad += '\t'

            # properties
            if flags & TE_WITHPROPERTIES:
                export_list.append('%s<label>%s</label>' % (pad, self.getLabel() ) )
                export_list.append('%s<uid>%s</uid>' % (pad, self.getUId() ) )


        for result in autoidList:

            if isinstance(result, TupleType):
                entry_id = result[0]
            else:
                entry_id = result

            export_list.append('%s<entry %s=\'%s\'>' % (pad, TCN_AUTOID, entry_id) )

            entry      = self.getEntry(entry_id)

            # check entry permissions
            pobj = entry['permission']

            if pobj and not pobj.hasPermission(SC_READ):
                continue


            for col in columnList:

                if flags & TE_LOOKUPDATA and lookup_dict.get(col):
                    colobj = mgr.listHandler.getList(self.tablename, col)
                    value = colobj.getValueByAutoid(entry.get(col, ''))
                else:
                    value = entry.get(col, '')

                if isinstance(value, ListType):
                    # flatten list (remove double, remove empty)
                    value = dict([(str(c), None) for c in value if c]).keys()

                    for item in value:
                        export_list.append('\t%s<%s>%s</%s>' % ( pad,
                                                                 col,
                                                                 str(item),
                                                                 col ))
                else:
                    export_list.append('\t%s<%s>%s</%s>' % ( pad,
                                                             col,
                                                             str(value),
                                                             col ))


            export_list.append('%s</entry>' % pad)

        if flags & TE_LVLTABLE:
            pad = pad[1:]
            export_list.append('%s</table>' % pad )

        if flags & TE_LVLMGR:
            pad = pad[1:]
            export_list.append('%s</manager>' % pad )

        if flags & TE_LVLPRODUCT:
            pad = pad[1:]
            export_list.append('%s</product>' % pad )

        if flags & TE_LVLINSTANCE:
            pad = pad[1:]
            export_list.append('</instance>')

        return export_list

    def exportCSV(self, columnList = None, autoidList = None, flags = None, delim = ";", multilines = 'remove'):
        """ This method exports the database contents to csv. It's basically an
            adapter based on exportTab.

        @param columnList List of columns to be exported.
        @param autoidList List of autoids for partial export.
        @param flags      Flags for common parameters.
        @param delim      Delimiter for attributes in one line
        @param multilines remove|replace|keep for handling of linebreaks in attributes
        """
        # this only forwards to exportTab now, no extra handling necessary
        # TODO: exportTab should be renamed to exportCSV, exportCSV-code be
        #       moved here
        return self.exportTab(columnList, autoidList, flags, delim, multilines)


    def getFieldSelectionList(self):
        """\brief Builds a multilist of all columnlabels in table for search.
        """
        mgr       = self.getManager()
        multiList = hgMultiList(name = 'show_fields')
        # no extra invis-check necessary
        collist = self.getColumnTypes(vis_only = True)

        # show_fields
        sfields = []

        if hasattr(mgr, '_generic_config') and \
             mgr._generic_config.get(self.tablename) and \
             mgr._generic_config[self.tablename].get('show_fields'):

            # get fields, select them
            sfields = mgr._generic_config[self.tablename]['show_fields']

        elif hasattr(mgr, 'actionBeforeShowList'):
            param = {}
            mgr.actionBeforeShowList(self.tablename, param, {})
            sfields = param.get('show_fields', [])

        if TCN_AUTOID in sfields:
            collist[TCN_AUTOID] = ''
        if TCN_DATE in sfields:
            collist[TCN_DATE] = ''
        if TCN_CREATOR in sfields:
            collist[TCN_CREATOR] = ''
        if TCN_OWNER in sfields:
            collist[TCN_OWNER] = ''
        for column in collist.keys():
            field = self.getField(column)
            label = field[COL_LABEL]
            if label and label != ' ':
                multiList.insertItem(label, column)

        if sfields:
            multiList.setSelectedValueList( sfields )

        return multiList


    def deleteEntries( self, idlist ):
        """\brief Deletes the entries with the autoids in idlist and
                    their multilist-references, including files / images.
                    Calls genericFileDelete for generic managers and
                    forwards to self.deleteEntry.
        """
        mgr = self.getManager()

        # file deletion for generic managers
        # has to be done here, because entry is needed for that
        if IGenericManager.providedBy(mgr):
            mgr.genericFileDelete( self.tablename, idlist )

        for autoid in idlist:
            autoid = int( autoid )

            self.deleteEntry(autoid)

#
# Entry handling
#

    def filterEntries( self,
                       filterTree = None,
                       order      = None,
                       orderdir   = None,
                       show       = None,
                       start      = None,
                       oneCol     = None ):
        """\brief Returns an entry list (or a list of values of oneCol),
                  constraints are given in Filter (tree) form, order
                  must be an attribute of the table, dir is asc or desc,
                  show and start control offset and number of entries.
                  Can be used to retrieve one col only (using oneCol)"""
        root = self.getTableNode()
        if filterTree:
            root.setFilter(filterTree)
        if order:
            root.setOrder(order, orderdir)
        return self.requestEntries(root, show, start, oneCol)


    def requestEntries( self,
                        treeRoot,
                        show = None,
                        start = None,
                        oneCol = None ):
        """\brief Returns an entry list (or a list of values of oneCol),
                  Constraints and order are transported by treeRoot (TableNode tree),
                  number and offset of entries controlled by show and start."""

        mgr = self.getManager()
        entries = []

        if oneCol:
            # test oneCol
            if not self.getField(oneCol):
                raise ValueError('Table Error: OneCol %s not in table' % oneCol)
            cols = [oneCol]
        else:
            cols = self.getMainColumnNames()
        sql = treeRoot.getSQL( show,
                               start,
                               col_list = cols,
                               distinct = True,
                               checker = mgr )

        # try cache
        if self.do_cache:
            cached = self.cache.getItem(self.cache.IDLIST, sql)
            if cached:
                # added deepcopy call 03/2009 (had some changes to cached-items hanging in the cache)
                return deepcopy(cached)

        results = mgr.getManager(ZM_PM).executeDBQuery( sql )

        # for result in results:
        #     if oneCol:
        #         entries.append(result[0])
        #     else:
        #         # autoid is always first column
        #         # get the entry
        #         # data_tuple parameter speeds up entry creation, contains base values
        #         new_entry = self.getEntry( result[0],
        #                                    data_tuple = result,
        #                                    col_list   = cols )
        #         entries.append( new_entry )

        # the final list is now stored in the cache including security objects
        # because security settings can change without inducing cache reload,
        # we decided to not have security objects cached
        # therefore, only the original database result or an entrylist without security objects
        # should be cached, caught from the cache and then be pimped accordingly

        if oneCol:
            entries = [result[0] for result in results]

        else:
            local_getEntry = self.getEntry
            # autoid is always first column
            # get the entry (for all via map/lambda def)
            # data_tuple parameter speeds up entry creation, contains base values
            entries = map( lambda result, cols = cols: local_getEntry(result[0], data_tuple = result, col_list = cols), results )

        # put complete entries in cache (since list-resolving is done later, this is safe)
        if self.do_cache:
            self.cache.insertItem( self.cache.IDLIST,
                                   sql,
                                   entries )

        # return a deepcopy (origs went in the cache)
        return deepcopy(entries)


    def requestEntryCount( self, treeRoot):
        """\brief Returns the entry count for the TableNode object (constraints have to be set already)"""
        mgr = self.getManager()
        sql = treeRoot.getSQL( function='count(distinct %sautoid)',
                               checker = mgr )
        # no caching for count requests
        results = mgr.getManager(ZM_PM).executeDBQuery( sql )
        if results:
            return int(results[0][0])
        else:
            return 0


    def getEntries( self,
                    idvalue   = None,
                    idfield   = TCN_AUTOID,
                    order     = None,
                    direction = Asc ):
        """\brief Uses requestEntries to return a list of descr_dicts."""
        # should replace getEntries after speed test
        assert direction in self.Order, \
               E_PARAM_TYPE % ('direction', 'Table.Order', direction)
        assert idfield, E_PARAM_FAIL % 'idfield'

        # get TreeRoot
        root = self.getTableNode()
        if order:
            root.setOrder(order, direction)

        # create filter
        fil = Filter(Filter.AND)

        # populate filter
        self.buildGetEntriesFilter(fil, idvalue, idfield)
        root.setFilter(fil)

        # evaluate the tableNode (caching is done in requestEntries)
        return self.requestEntries(root)


    def buildGetEntriesFilter(self, filter, idvalue, idfield):
        """\brief populate the given FilterNode with the values.
                  idvalue and idfield can be lists of same length."""

        # check idvalue / idfield
        if not isinstance(idfield, ListType):
            if idfield == TCN_AUTOID and idvalue is None:
                idfield = []
                idvalue = []
            else:
                idvalue = [idvalue]
                idfield = [idfield]

        # build dicts out of the given field / value lists
        defdict = {}
        multidefdict = {}

        for index, field in enumerate(idfield):

            value = idvalue[index]

            # list values are handled by checktype, not here
            # they will always be evaluated via IN-operator
            # which means OR

            # test defdict
            if field in defdict:
                value2 = defdict[field]
                del defdict[field]
                multidefdict[field] = [value2, value]

            # not in defdict, check multi
            elif field in multidefdict:

                # append to multidefdict-value
                multidefdict[field].append(value)

            else:

                # put into defdict
                defdict[field] = value

        # set single constraints
        filter.setUncheckedConstraints(defdict)

        # set multi constraints
        for key in multidefdict.keys():
            value = multidefdict[key]
            filter.setMultiConstraint(key, value)


    def getEntryCount( self,
                       idvalue   = None,
                       idfield   = TCN_AUTOID):
        """\brief Returns the count for getEntries - old value-handling (simple attrs only)"""
        assert idfield, E_PARAM_FAIL % 'idfield'

        # get TreeRoot
        root = self.getTableNode()

        # create filter
        fil = Filter(Filter.AND)

        # populate filter
        self.buildGetEntriesFilter(fil, idvalue, idfield)
        root.setFilter(fil)

        # evaluate the tableNode
        return self.requestEntryCount(root)


    def getEntryList( self,
                      show_number    = None,
                      start_number   = None,
                      idfield        = TCN_AUTOID,
                      constraints    = None,
                      order          = None,
                      direction      = None,
                      constr_or       = False
                      ):
        """\brief Returns a list of entries, same as getEntries but with constraints, start_number and show_number.
        """
        root = self.getTableNode()
        if order:
            root.setOrder(order, direction)
        else:
            root.setOrder(idfield, direction)
        if constraints:
            root.setConstraints(constraints)
        if constr_or:
            fi = root.getFilter()
            fi.setOperator(fi.OR)
        return self.requestEntries(root, show_number, start_number)


    def getEntryDict(self, idfield = TCN_AUTOID, constraints = None):
        """\brief Returns a dict of entries, key is the idfield (default: autoid), uses getEntryList"""
        res = {}
        tmp = self.getEntryList(constraints = constraints)
        for entry in tmp:
            res[entry[idfield]] = entry
        return res


    def getEntryListCount( self,
                           constraints = None):
        """\brief Returns the complete count for getEntryList."""
        root = self.getTableNode()
        if constraints:
            root.setConstraints(constraints)
        return self.requestEntryCount(root)


    def getEntryAutoidList(self,
                           show_number    = None,
                           start_number   = None,
                           idfield        = TCN_AUTOID,
                           constraints    = None,
                           order          = None,
                           direction      = None,
                           constr_or      = False
                           ):
        """\brief Returns a list of autoids."""
        # caching is done by requestEntries
        root = self.getTableNode()
        if order:
            root.setOrder(order, direction)
        else:
            root.setOrder(idfield, direction)
        if constraints:
            root.setConstraints(constraints)
        if constr_or:
            fi = root.getFilter()
            fi.setOperator(fi.OR)
        return self.requestEntries(root, show_number, start_number, idfield)


    def getLabel(self, column_name = None):
        """\brief Returns a label string for the specified column or
                  the table if no column is specified.

        \return Returns a string with the label, otherwise an empty string
        """
        if column_name:
            return self.getField(column_name).get(COL_LABEL, '')
        else:
            return self.label


    def getLabelWidget( self,
                        column_name = None,
                        style  = ssiDLG_LABEL,
                        prefix = None,
                        suffix = None,
                        parent = None):
        """\brief Returns a label widget for the specified column.

        \return Returns a hgLabel widget if a label exists for the column, otherwise None
        """
        assert isinstance(style, hgStyleSheetItem)

        text = self.getLabel(column_name)

        if prefix:
            text = '%s %s' % (prefix, text)
        if suffix:
            text = '%s %s' % (text, suffix)

        if text and text != ' ':
            label = hgLabel(text, None, parent)
            label._styleSheet.getSsiName( style )
            label.setSsiName( style.name() )
            return label
        else:
            return hgLabel('', parent = parent)


    def getLastId( self,
                   idfield        = TCN_AUTOID,
                   wherefield     = None,
                   wherevalue     = None ):
        """\brief Returns the last id of the specified table.

        The function will use a string comparision to determine the order. So
        be aware that '02' will go before '1'!

        \param idfield  The argument \a idfield is a string that specifies the
        column which should be used as id column.

        \return The last id of the table, otherwise None.
        """
        mgr = self.getManager()
        product = mgr.getManager(ZM_PM)
        wherestr = self.processWhereString( wherevalue, wherefield )

        return product.getLastId( idfield, mgr.id + self.tablename, wherestr )


    def getRowCount( self, constraints = None ):
        """\brief Returns the number of rows in the table that match
                  the constraints.

        \param constraints  The argument \a constraints contains a dictionary
        with key, value pairs that should be used as a constraints for a
        database query.

        \return The number of rows that match, otherwise None
        """
        if constraints is None:
            constraints = {}
        return self.getEntryListCount(constraints)

#
# Foreign List management generic functions
#
    def getEntryValue(self, autoid, cols, lang=None):
        """\brief Returns a Valuestring consisting of the content of cols
                  for the entry with the given autoid.
        """
        assert isinstance(cols, ListType)
        if not autoid or autoid == 'NULL':
            return ''

        entry = self.getEntry(autoid)
        if entry:
            if not cols:
                mgr = self.getManager()
                if IGenericManager.providedBy(mgr):
                    # check for language
                    if mgr.doesTranslations(self.tablename):
                        # TODO: unify getLabelString to always have a lang parameter
                        return mgr.getLabelString(self.tablename, None, entry, lang)
                    else:
                        return mgr.getLabelString(self.tablename, None, entry)
                else:
                    return entry.get(TCN_AUTOID)
            else:
                value = []
                for col in cols:
                    if entry.get(col):
                        value.append( unicode(entry[col]) )
                return ' '.join(value)
        return ''


    def getEntrySelect(self, cols):
        """\brief Returns a list of all entries containing the requested
                  cols plus autoid.
        """
        assert isinstance(cols, ListType)
        reslist = None
        # caching
        if self.do_cache:
            reslist = self.cache.getItem(self.cache.ALLLIST, cols)

        if not reslist:
            mgr = self.getManager()
            reslist = []
            entries = self.getEntries()
            for entry in entries:
                autoid = entry.get(TCN_AUTOID)
                value = []
                if not cols:
                    if IGenericManager.providedBy(mgr):
                        # use getLabelString
                        label = mgr.getLabelString(self.tablename, None, entry)
                        reslist.append([autoid, label])
                    else:
                        reslist.append([autoid, autoid])
                else:
                    for col in cols:
                        if entry.get(col):
                            value.append(str(entry.get(col)))
                    reslist.append([autoid, ' '.join(value)])
            if self.do_cache:
                self.cache.insertItem(self.cache.ALLLIST, cols, reslist)
        return reslist


    def showCache(self):
        """\brief Show all chached items."""
        caches = [self.cache.item, self.cache.idlist, self.cache.alllist]
        counts = [self.cache.item_count, self.cache.idlist_count, self.cache.alllist_count]
        names  = ['Items', 'IDLists', 'All']
        tab = hgTable()
        tab[0, 0] = 'Caching: %s' % self.do_cache
        tab[4, 0] = 'Cache Details'
        row = 5
        for index, cache in enumerate(caches):
            tab[index + 1, 0] = '%s: %s' % (names[index], len(cache))
            tab[index + 1, 1] = 'Maximum: %s' % (counts[index])
            tab[row, 0] = '%s (%s)' % (names[index], len(cache))
            row += 1
            for key in cache.keys():
                tab[row, 0] = key
                tab[row, 1] = cache.get(key)
                row += 1
            tab[row, 0] = hgSPACE
            row += 1
        return tab


    def getColumnTypes(self, vis_only = False):
        """\brief Returns a dict containing all columns as keys
                    and their types as values.
                    vis_only = True returns only visible columns
        """
        mgr     = self.getManager()
        resdict = {}

        # types in list that are not included -> [] -> all list types are included
        tablelists = mgr.listHandler.getLists(self.tablename)
        for listobj in tablelists:
            if not vis_only or listobj.invisible is not True:
                resdict[listobj.listname] = listobj.listtype

        for column in self.tabledict:
            if column not in resdict:
                field = self.tabledict[column]
                if not vis_only or field.get(COL_INVIS) is not True:
                    resdict[column] = field.get(COL_TYPE)

        # edit tracking cols TCN_DATE and TCN_CREATOR are visible too but not in the dict
        if TCN_CREATOR not in resdict:
            resdict[TCN_CREATOR] = ZCOL_SLIST
        if TCN_CREATOR not in resdict:
            resdict[TCN_DATE] = ZCOL_DATE
        # edit tracking col TCN_AUTOID is invis (most of the time)
        if not vis_only:
            resdict[TCN_AUTOID] = ZCOL_INT

        return resdict


    def getColumnDefs(self, vis_only = False, edit_tracking = False):
        """\brief Returns a dict containing all columns as keys
                    and their column definitions as values.
        """
        mgr     = self.getManager()
        resdict = {}

        tablelists = mgr.listHandler.getLists(self.tablename)
        for listobj in tablelists:
            if not vis_only or listobj.invisible is not True:
                resdict[listobj.listname] = self.getField(listobj.listname)

        # copy normal attr info
        for key in self.tabledict.keys():
            if key not in resdict:
                field = self.tabledict[key]
                if not vis_only or field.get(COL_INVIS) is not True:
                    resdict[key] = field

        # add edit_tracking fields creator, creationdate and autoid if requested
        if edit_tracking:
            if TCN_CREATOR not in resdict:
                resdict[TCN_CREATOR] = self.getField(TCN_CREATOR)
            if TCN_DATE not in resdict:
                resdict[TCN_DATE] = self.getField(TCN_DATE)
            if TCN_AUTOID not in resdict:
                resdict[TCN_AUTOID] = self.getField(TCN_AUTOID)

        return resdict


    def getMainColumnNames(self):
        """\brief Returns a list containing all columnnames
                    for the main table
        """
        mgr     = self.getManager()
        m_product = mgr.getManager(ZM_PM)
        reslist = []
        # autoid has to be first column!
        reslist.append(TCN_AUTOID)

        for column in self.tabledict:
            if column != TCN_AUTOID:
                reslist.append(column)

        for column in m_product._edit_tracking_cols:
            if column not in reslist:
                reslist.append(column)

        return reslist

    ##########################################################################
    #
    # Search Tree Methods
    #
    ##########################################################################

    def getSearchTreeTemplate(self):
        """\brief template function for join selection with join-tree caching, is not used by the standard entry functions"""
        # TODO: use this function in all entry requesting functions instead of getTableNode() -> needs testing
        mgr = self.getManager()

        if not self.treeTemplate:
            self.treeTemplate = mgr.\
                     generateTableSearchTreeTemplate(self.tablename)

        return self.treeTemplate.copy(mgr, mgr.getZopraType())


    def resetSearchTreeTemplate(self):
        """\brief reset the template"""
        self.treeTemplate = None


    def getTableNode(self):
        """\brief Builds a new table Node for this Table"""
        mgr = self.getManager()

        # FIXME: having the listHandler set in the TableNode is odd, but acquisition didn't work
        data             = TablePrivate()
        data.tablename   = self.tablename
        data.tabledict   = self.tabledict
        data.listHandler = mgr.listHandler
        return TableNode(data, mgr)

    ##########################################################################
    #
    # Statistics
    #
    ##########################################################################

    def getStatistic(self):
        """\brief Returns a dictionary that contains some statistic
                  about the usage of this particular table.
        """
        manager    = self.getManager()
        mproduct   = manager.getManager( ZM_PM )
        fromPhrase = ' FROM %s ' % ( manager.id + self.tablename )
        stats_dict = {}

        # entry count
        query = 'SELECT count(*)' + fromPhrase
        stats_dict['rowCount'] = mproduct.executeDBQuery( query )

        # new entries in day
        day   = ' date_part(\'day\',   entrydate) AS day   '
        month = ' date_part(\'month\', entrydate) AS month '
        year  = ' date_part(\'year\',  entrydate) AS year  '

        query = 'SELECT count(*) AS count, '     + \
                day + ', ' + month + ', ' + year + \
                fromPhrase                       + \
                ' GROUP BY year, month, day;'
        stats_dict['entriesInDay'] = mproduct.executeDBQuery( query )

        # new entries in month
        query = 'SELECT count(*) AS count, '     + \
                month + ', ' + year              + \
                fromPhrase                       + \
                ' GROUP BY year, month;'
        stats_dict['entriesInMonth'] = mproduct.executeDBQuery( query )

        # new entries in year
        query = 'SELECT count(*) AS count, ' + year + fromPhrase + \
                ' GROUP BY year;'
        stats_dict['entriesInYear'] = mproduct.executeDBQuery( query )

        # active users
        return stats_dict


    ##########################################################################
    #
    # Manage Tab Methods
    #
    ##########################################################################
    def viewTab(self, REQUEST):
        """\brief Table overview tab."""
        message = ''
        # test Request for creation button
        if REQUEST.get('create'):
            # try to create the table
            mgr = self.getManager()
            m_product = mgr.getManager(ZM_PM)
            # no logging for scm due to loops
            if ZM_SCM in mgr.getClassType():
                log = False
            else:
                log = True
            m_product.addTable( mgr.id + self.tablename, self.tabledict, log = log)
            message = 'Table created.'
        dlg = getStdDialog('', 'viewTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        tab = hgTable()
        tab._old_style = False

        # show tables information
        tab[0, 0] = '<h3>Table Overview</h3>'
        tab.setCellSpanning(0, 0, colspan = 3)

        tab[1, 0] = '<b>Column Name</b>'
        tab[1, 1] = '<b>Column Type</b>'
        tab[1, 2] = '<b>Column Label</b>'

        row     = 2
        offset  = 1
        for col in self.getColumnTypes().keys():
            tab[row + offset, 0] = col
            tab[row + offset, 1] = self.getField(col).get(COL_TYPE)
            tab[row + offset, 2] = self.getField(col).get(COL_LABEL, col)
            offset += 1

        row = row + offset + 1
        # try to get rowcount, if error: table may not exist
        try:
            self.getRowCount()
            if message:
                tab[row, 0] = hgLabel(message)
                tab.setCellSpanning(row, 0, colspan = 3)
        except:
            # show table creation button
            tab[row, 0] = hgPushButton('Create Table', 'create')
            tab.setCellSpanning(row, 0, colspan = 3)
        dlg.add( tab )
        return HTML( dlg.getHtml() )(self, REQUEST)


#    def managementTab(self, REQUEST):
#        """\brief Table edit tab."""
#
#        columnOrder = REQUEST.form.get( 'columnOrder' )
#        if columnOrder:
#            self.setDefaultOrder(columnOrder)
#
#        dlg  = getStdDialog('', 'managementTab')
#        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
#        dlg.setFooter( "<dtml-var manage_page_footer>"                       )
#
#        table = hgTable()
#        table._old_style = False
#        dlg.add( table )
#
#        multiList = hgMultiList( name = 'columnOrder' )
#
#        for col in self.tabledict.keys():
#            multiList.insertItem( col, col )
#
#        defOrd = self.getDefaultOrder()
#        if defOrd:
#            multiList.setSelectedStringList(defOrd)
#
#        table[0, 0] = 'Column Order'
#        table[0, 1] = multiList
#
#        dlg.add( hgPushButton('Change') )
#        return HTML( dlg.getHtml() )(self, REQUEST)


    def editTab(self, REQUEST):
        """\brief Returns a show entry dialog."""
        session = REQUEST.SESSION
        mgr = self.getManager()
        key = self.id + TableEntryDialog._className + self.tablename
        dlg = session.get(key)

        # either we didn't have this dlg already or we got a zope refresh !!!
        if not dlg or dlg.uid != id(dlg):
            dlg = TableEntryDialog( mgr, self.tablename )
            dlg.setName('editTab')
            header = "<dtml-var manage_page_header><dtml-var manage_tabs>"
            dlg.setHeader( header )
            dlg.setFooter( "<dtml-var manage_page_footer>" )

            key = mgr.id + TableEntryDialog._className + self.tablename
            session[key] = dlg

        dlg.execDlg( mgr, REQUEST )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def statsTab(self, REQUEST):
        """\brief Show the statics tab."""
        stats_dict  = self.getStatistic()

        table       = hgTable()

        table[0, 0] = '<b>Number of Entries</b>'
        table[0, 1] = stats_dict['rowCount'][0][0]

        table[1, 0] = '<b>New Entries in Year</b>'

        row    = 1
        offset = 0
        for result in stats_dict['entriesInYear']:
            table[row + offset, 1] = '%06d' % result[0]
            table[row + offset, 2] = '%4d' % result[1:]
            offset += 1
        row += offset + 1

        table[row, 0] = '<b>New Entries in Month</b>'

        offset = 0
        for result in stats_dict['entriesInMonth']:
            table[row + offset, 1] = '%06d' % result[0]
            table[row + offset, 2] = '%02d.%4d' % result[1:]
            offset += 1
        row += offset + 1

        table[row, 0] = '<b>New Entries in Day</b>'

        offset = 0
        for result in stats_dict['entriesInDay']:
            table[row + offset, 1] = '%06d' % result[0]
            table[row + offset, 2] = '%02d.%02d.%4d' % result[1:]
            offset += 1
        row += offset + 1

        dlg = getStdDialog('')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )
        dlg.add( table )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def cacheTab(self, REQUEST):
        """\brief Table cache tab."""

        dlg = getStdDialog(action = 'cacheTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        # table cache

        button = getPressedButton(REQUEST)
        if len(button) > 0 and button[0] == BTN_L_RESET2:
            self.cache.clearCache()

        dlg.add(self.showCache())

        dlg.add(mpfReset2Button)

        return HTML( dlg.getHtml() )(self, REQUEST)


    def searchTreeTab(self, REQUEST):
        """\brief TableNode (join Tree) tab."""

        dlg = getStdDialog(action = 'searchTreeTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        if REQUEST.get('f_' + BTN_L_RESET2):
            if hasattr(self, 'treeTemplate'):
                self.treeTemplate = None

        tmp = self.getSearchTreeTemplate()
        if tmp:
            dlg.add( tmp.getStructureHtml() )
            dlg.add( mpfReset2Button )
        else:
            dlg.add( hgLabel('No Template Tree found.'))

        return HTML( dlg.getHtml() )(self, REQUEST)
