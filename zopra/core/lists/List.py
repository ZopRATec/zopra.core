############################################################################
#    Copyright (C) 2004 by Ingo Keller                                     #
#    <webmaster@ingo-keller.de>                                            #
#                                                                          #
# Copyright: See COPYING file that comes with this distribution            #
#                                                                          #
############################################################################
"""\brief Basic List Handling for Dropdownlists, List Entry Management."""

#
# Python Language Imports
#
from types                  import ListType, StringType, IntType, UnicodeType
from copy                   import deepcopy

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                      import E_PARAM_TYPE
from PyHtmlGUI.widgets.hgLabel      import hgLabel,   \
                                           hgSPACE,   \
                                           hgNEWLINE, \
                                           hgProperty
from PyHtmlGUI.kernel.hgTable       import hgTable
from PyHtmlGUI.widgets.hgTextEdit   import hgTextEdit
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from PyHtmlGUI.widgets.hgCheckBox   import hgCheckBox

#
# ZopRA Imports
#
from zopra.core                     import HTML, ZM_PM, ZM_SCM, ZC
from zopra.core.constants           import VALUE, NOTES, RANK, SHOW
from zopra.core.elements.Buttons    import mpfAddButton,     \
                                           mpfDeleteButton,  \
                                           mpfUpdateButton,  \
                                           mpfReset2Button,  \
                                           DLG_FUNCTION,     \
                                           BTN_L_ADD,        \
                                           BTN_L_DELETE,     \
                                           BTN_L_UPDATE,     \
                                           BTN_L_RESET2,     \
                                           getPressedButton
from zopra.core.CorePart            import getStdDialog,     \
                                           COL_TYPE
from zopra.core.lists.GenericList   import GenericList, \
                                           _list_definition
from zopra.core.widgets             import dlgLabel


class List(GenericList):
    """ List """
    _className = 'List'
    _classType = GenericList._classType + [_className]

    meta_type  = 'ZopRAList'

    # for compatibility
    listtype   = 'singlelist'

    manage_options = (  {'label': 'Overview',    'action': 'viewTab' },
                        {'label': 'Edit',        'action': 'editTab' },
                        {'label': 'List Cache',  'action': 'cacheTab' },
                        ) + GenericList.manage_options


    # debugging flags
    _debug_disable_caching = False

    def __init__( self,
                  listname,
                  label    = None,
                  docache  = True,
                  translations = []):
        """\brief Constructs a List.
        """
        GenericList.__init__( self, listname, label )

        self.cache        = None
        self.enableCache  = docache
        self.__noedit     = False
        self.translations = translations
        # store local copy of list def
        ldef = deepcopy(_list_definition)
        for translation in self.translations:
            ldef[VALUE + '_' + translation] = {COL_TYPE: 'string'}
        self._list_definition = ldef


    def createTable(self):
        """\brief Create the database table."""

        # try to create the list
        mgr = self.getManager()
        m_product = mgr.getManager(ZM_PM)
        # only create table if it is a local list

        # create all
        m_product.addTable( mgr.id + self.listname,
                            self._list_definition )



    def deleteTable(self, omit_log = None):
        """\brief Create the database table."""

        mgr       = self.getManager()
        m_product = mgr.getManager(ZM_PM)
        my_id     = mgr.getId()
        log = True

        for ident in omit_log:
            if ident in mgr.getClassType():
                log = False

        m_product.delTable( my_id + self.listname, log )

        # fname = 'atov' + my_id + self.listname
        # m_product.delFunction( fname,
        #                        'integer',
        #                         log )


    # noedit property methods
    def setNoEdit(self, noedit):
        """\brief Set (no-)edit property"""

        if noedit:
            self.__noedit = True
        else:
            self.__noedit = False


    def getNoEdit(self):
        """\brief Get (no-)edit property"""

        return self.__noedit

    noedit = property(getNoEdit, setNoEdit)


    def copy(self):
        """\brief Create a copy of the list."""
        cop = self.__class__( self.listname,
                              self.label,
                              self.enableCache )

        cop.noedit    = self.noedit

        return cop


    def addValue( self, value, notes = '', rank  = None, show  = 'yes', **kwargs ):
        """\brief Adds a value to a list lookup table.

        The function adds a new value to a lookup list. It also checks if
        the value is already in the list. If so it won't add the new value but
        also won't give a error message (yet).

        \param list_name The argument \a list_name specifies the list where the
        entry should be inserted.

        \param value  The argument \a value is a string that should be
                      inserted.

        \param notes  The argument \a notes contains a comment if there is one.
        \todo   Handling for comments.

        \param rank  The \a rank should be a number and will be used for
        ordering the entries in the combobox where it will be shown.
        \todo  Handling for ordering lookup list ranking.

        \param show  If \a show is \c 'yes' then the entry will be shown in the
        combobox of the list. If it is no then it won't.

        \param use keyword arguments in the form 'value_en' = '<en_value>' to pass in
        translated values, that will be evaluated according to the codes in self.translations

        \throw RuntimeError if list not found.
        """
        mgr = self.getManager()

        # if the value is None then add a Space, correcting html handling
        # for None valued hgTextEdits
        if not value:
            value = ' '

        # checks if the value is already in the list
        result = self.getAutoidByValue(value, rank )
        # if not then add it to the list
        if result is None:
            entry_dict = {
                          VALUE:    value,
                          NOTES:    notes,
                          RANK:     rank,
                          SHOW:     show
                         }
            for trans in self.translations:
                key = VALUE + '_' + trans
                if kwargs.get(key):
                    entry_dict[key] = kwargs[key]
            m_product = mgr.getManager(ZM_PM)
            my_id     = mgr.getId()
            m_product.simpleInsertInto( my_id + self.listname,
                                        self._list_definition,
                                        entry_dict)

            # we better get the id by this function than getTableLastId.
            entry_id = m_product.getLastId(ZC.TCN_AUTOID, my_id + self.listname)
            message  = 'add entry %s to %s' % ( entry_id,
                                                my_id + self.listname )
            m_product.writeLog( message )
            self.clearCache()
            return entry_id

        else:
            return result


    def delValue(self, autoid):
        """\brief Deletes a value from a list lookup table."""
        mgr = self.getManager()

        # now delete
        mgr.getManager(ZM_PM).simpleDelete( mgr.id + self.listname,
                                            autoid )
        self.clearCache()


    def getEntry(self, autoid, use_cache = True):
        """\brief Fetches a value from an list lookup table. Local function.
        use_cache can be set to false to force db-lookup for example for cache-filling"""
        autoid = int(autoid)

        # cache handling, use_cache param to turn if off for cache-filling
        if self.enableCache and use_cache:
            if not self.cache:
                # fill cache (use with_hidden to speed up things)
                self.getEntries(with_hidden = True)
            # look for id
            if autoid in self.cache:
                return self.cache[autoid]
            else:
                # return empty entry for compatibility
                return {}

        # caching turned off, fetch by hand
        mgr    = self.getManager()
        entry_dict = {}
        trans = ''

        # language handling
        for translation in self.translations:
            trans += ', %s_%s' % (VALUE, translation)
        query_text = 'SELECT autoid, value, notes, rank, show%s '\
                     + 'FROM %s%s WHERE autoid = %d;'
        query_text = query_text % ( trans, mgr.getId(),
                         self.listname,
                         autoid )
        result = mgr.getManager(ZM_PM).executeDBQuery(query_text)
        if result:
            entry_dict['autoid'] = result[0][0]
            entry_dict[VALUE]  = result[0][1]
            entry_dict[NOTES]  = result[0][2]
            entry_dict[RANK]   = result[0][3]
            if entry_dict.get(RANK):
                entry_dict[RANK] = int(entry_dict.get(RANK))
            entry_dict[SHOW]   = result[0][4]
            # language handling
            for index, translation in enumerate(self.translations):
                entry_dict[VALUE + '_' + translation] = result[0][5 + index]

            # do not put in cache. cache is either complete or empty, regulated by getEntries

        return entry_dict


    def getEntries(self, value = None, with_hidden = False):
        """\brief Returns all list entries of one list."""
        mgr          = self.getManager()
        completelist = []

        # value - searches are not put in cache and not taken from cache completely
        # only the single entries are later on fetched from cache
        if value:
            do_cache = False
        else:
            do_cache = True
        # caching
        if self.enableCache and self.cache and do_cache:
            # get from cache
            completelist = self.cache.values()
        else:
            where = ''
            if value:
                # search for value
                value = value.replace('*', '%')
                where = " WHERE value like '%s'" % value

            sql = 'SELECT %s FROM %s%s%s;'
            sql = sql % (ZC.TCN_AUTOID, mgr.id, self.listname, where)
            results = mgr.getManager(ZM_PM).executeDBQuery(sql)
            for result in results:
                # tell getEntry to fetch from DB instead cache if do_cache is True
                # because then the cache was empty
                # otherwise we can use the cache for getEntry (even for value-searches)
                completelist.append( self.getEntry(result[0], not do_cache) )

        if self.enableCache and not self.cache and do_cache:
            # put into cache
            self.cache = {}
            for entry in completelist:
                self.cache[entry[ZC.TCN_AUTOID]] = entry

        if not with_hidden:
            completelist = [entry for entry in completelist if entry.get(SHOW) != 'no']

        return completelist


    def getEntriesByParent(self, parentid = None, with_hidden = False):
        """\brief Returns all entrys Connected to a Parent, 0 = First Rank Entries without parent"""
        # helper function used for basic lists that are treated as hierarchylists (when one is connected to this list)
        # value - searches are not put in cache and not taken from cache completely
        # only the single entries are later on fetched from cache
        mgr          = self.getManager()
        completelist = []
        parentid = str(parentid)

        where = ''
        if parentid is not None:
            # search for value
            parentid = parentid.replace('*', '%')
            where = " WHERE rank like '%s'" % parentid
            sort = " ORDER BY value ASC "
        sql = 'SELECT %s FROM %s%s%s%s;'
        sql = sql % (ZC.TCN_AUTOID, mgr.id, self.listname, where, sort)
        results = mgr.getManager(ZM_PM).executeDBQuery(sql)
        for result in results:
            # tell getEntry to fetch from DB instead cache if do_cache is True
            # because then the cache was empty
            # otherwise we can use the cache for getEntry (even for value-searches)
            completelist.append( self.getEntry(result[0]) )

        return completelist



    def updateEntry( self,
                     descr_dict,
                     entry_id ):
        """\brief changes list values in the database"""
        mgr = self.getManager()


        if entry_id   and \
           descr_dict:

            # get ProductManager
            m_product = mgr.getManager(ZM_PM)

            # update Entry
            res = m_product.simpleUpdate( mgr.id + self.listname,
                                          self._list_definition,
                                          descr_dict,
                                          entry_id )

            self.clearCache()
            return res


    def getAutoidByValue(self, value, rank = None, ignore_cache = False):
        """\brief Returns the autoid from an specified list entry."""
        assert (isinstance(value, StringType)  or
                isinstance(value, ListType)    or
                isinstance(value, UnicodeType) or
                value is None), 'Wrong type for parameter value: %s [%s]' % (value, value.__class__)

        # NOTE: do not handle lists recursively:
        #       1) getting the manager is expensive
        #       2) loading all entries of a list from the db for each searched
        #          value is wasteful
        if isinstance( value, ListType):
            is_list = True
            values = value
        else:
            is_list = False
            values = [ value ]

        retlist = []

        mgr = self.getManager()

        # get from cache if caching activated
        if self.enableCache and not ignore_cache:
            # build cache if not done yet
            if not self.cache:
                # use with_hidden to speed things up
                self.getEntries(with_hidden = True)
            val2entry = {}

            # build lookup table
            for entryid in self.cache:
                entry = self.cache[entryid]
                val2entry[entry.get(VALUE)] = entry

            # get the autoid for each value
            for val in values:
                autoid = None
                entry  = val2entry.get(val, None)

                if entry:
                    # added rank == '' test to avoid empty rank which doesn't mach
                    if rank is None or rank == '' or entry.get(RANK) == rank:
                        autoid = entry.get(ZC.TCN_AUTOID)

                retlist.append( autoid )
        # get from db if caching not activated
        else:
            query_text  = "SELECT autoid FROM %s " % (mgr.getId() + self.listname)
            query_text += "WHERE value = '%s'"

            if rank or rank == 0:
                query_text += " and rank = '%s'" % rank

            for val in values:
                autoid = None
                if val is not None:
                    result = mgr.getManager(ZM_PM).executeDBQuery(query_text % val)

                    if result:
                        autoid = result[0][0]

                retlist.append( autoid )

        if is_list:
            return retlist
        else:
            return retlist[0]


    # freetextsearch
    def getAutoidsByFreeText(self, value):
        """\brief Returns the autoid from any fitting list entry."""
        mgr     = self.getManager()
        reslist = []
        upval   = value.upper()

        # normal list, compare uppercase
        query_text = "SELECT autoid FROM "
        upval, operator = mgr.forwardCheckType(upval, 'string', True)
        query_text += "%s WHERE upper(value) %s %s" \
                      % ( mgr.getId() + self.listname,
                          operator,
                          upval)

        results = mgr.getManager(ZM_PM).executeDBQuery( query_text )
        if results:
            reslist = [result[0] for result in results]

        return reslist


    def clearCache(self):
        """\brief Empties all cached objects from list handling."""
        self.cache  = None


    def getValueCount(self):
        """\briefs Returns the length of a list.

        \param list_name  The argument \a list_name is the name of the list
        without the id prefix.

        \return The number of rows, otherwise None
        """
        mgr = self.getManager()

        return mgr.getManager(ZM_PM).getRowCount(mgr.id + self.listname)


    def getValueByAutoid(self, autoid, lang=None):
        """\brief Returns the value from an specified list entry/entries."""
        if isinstance( autoid, ListType):
            is_list = True
            autoids = autoid
        else:
            is_list = False
            autoids = [ autoid ]

        # language fallback: wrong or default lang -> fall back to None
        if lang:
            if lang not in self.translations:
                lang = None

        retlist = []

        mgr = self.getManager()

        for aid in autoids:
            value  = ''

            # not existing values
            if aid is None or aid == '':
                value = None
            # no value
            elif aid == 'NULL':
                pass
            elif aid == '_not_NULL':
                # TODO: use translation (Plone 4)
                if lang == 'de':
                    value = 'beliebig'
                else:
                    value = 'any'
            else:
                assert isinstance(aid, IntType) or \
                       isinstance(aid, StringType) or \
                       isinstance(aid, UnicodeType), \
                       E_PARAM_TYPE % ('aid', 'IntType/StringType', aid)

                aid = int(aid)

                if self.enableCache:
                    if not self.cache:
                        # force caching
                        self.getEntries(with_hidden = True)
                    if aid in self.cache:
                        entry = self.cache[aid]
                        value = lang and entry.get(VALUE + '_' + lang) or entry.get(VALUE)
                else:
                    sel = lang and VALUE + '_' + lang + ', ' or ''
                    query_text = "SELECT %svalue FROM %s%s WHERE autoid = %s;" \
                                 % (sel, mgr.getId(), self.listname, aid)
                    result = mgr.getManager(ZM_PM).executeDBQuery(query_text)

                    if result:
                        value = result[0][0]
                        if not value and lang:
                            value = result[0][1]

            retlist.append(value)

        return retlist if is_list else retlist[0]


    def getEntryFromRequest(self, autoid, REQUEST):
        """\brief get value and translations from REQUEST"""
        entry = { VALUE: REQUEST.get(self.listname + str(autoid))}
        for trans in self.translations:
            key = VALUE + '_' + trans
            keyReq = self.listname + '_' + trans + str(autoid)
            if REQUEST.get(keyReq):
                entry[key] = REQUEST[keyReq]
        return entry


    def editForm(self, REQUEST = None):
        """\brief Return the html source of the edit list form."""
        # if the list is used by a HierarchyList, then we have to forward to its special editForm
        # get all lists connected to this one
        mgr = self.getManager()

        lHandler = mgr.listHandler
        tabname = None
        for table in lHandler.maptable2lists.keys():
            if self.listname in lHandler.maptable2lists[table]['hierarchylist']:
                tabname = table
                break
        if tabname:
            # found hierarchylist using this list -> forward editForm
            # FIXME: this means we need the value functions in ForeignList, needs to be moved here
            fwd = lHandler.absolute_url() + '/' + tabname + '_' + self.listname + '/editForm'
            REQUEST.RESPONSE.redirect(fwd)

        # security manager
        m_sec = mgr.getHierarchyUpManager(ZM_SCM)

        button     = mgr.getPressedButton(REQUEST)
        if button:
            changedIds = mgr.getValueListFromRequest(REQUEST, 'entry')

            # add function
            if button == BTN_L_ADD:
                if 'new_entry' in REQUEST:
                    self.addValue(REQUEST['new_entry'])

            # delete function
            elif button == BTN_L_DELETE:
                for changed_id in changedIds:
                    changed_id = int(changed_id)
                    self.delValue(changed_id)

            # switch hide -> show
            elif button == 'Show':
                for changed_id in changedIds:
                    self.updateEntry( {SHOW: 'yes'},
                                      changed_id )

            # switch show -> hide
            elif button == 'Hide':
                for changed_id in changedIds:
                    self.updateEntry( {SHOW: 'no'},
                                      changed_id )
            # update function
            elif button == BTN_L_UPDATE:
                [self.updateEntry(self.getEntryFromRequest(eid, REQUEST), eid) for eid in changedIds]

        # interface building
        entry_list = self.getEntries(with_hidden = True)
        # sort by value
        own_cmp = lambda x, y: (x[VALUE] < y[VALUE]) and -1 or (x[VALUE] > y[VALUE]) and 1 or 0
        entry_list.sort(own_cmp)

        offset = len(self.translations)

        # build mask
        tab = hgTable()
        tab[0, 4] = dlgLabel('Values')
        for index, trans in enumerate(self.translations):
            tab[0, index + 5] = dlgLabel(trans)
        tab[0, 5 + offset] = dlgLabel('Show')
        row = 2

        # all existing list entries
        for entry in entry_list:
            tab[row, 1] = hgCheckBox('', entry.get('autoid'), name = 'entry')
            tab[row, 4] = hgTextEdit( entry.get(VALUE),
                                      name = self.listname +
                                      str(entry.get('autoid')) )
            for index, trans in enumerate(self.translations):
                formkey = self.listname + '_' + trans + str(entry.get('autoid'))
                key = VALUE + '_' + trans
                tab[row, index + 5] = hgTextEdit( entry.get(key),
                                                  name = formkey )
            tab[row, 5 + offset] = entry.get(SHOW)
            row += 1

        #
        # dialog
        #

        # roc_count
        counttxt = '(%s %s)' % (len(entry_list), len(entry_list) == 1 and 'entry' or 'entries')

        dlg  = getStdDialog('Edit %s List %s' % (self.label, counttxt), 'editForm')

        dlg.add( hgNEWLINE)
        dlg.add( '<center>' )
        dlg.add( tab )
        dlg.add( hgNEWLINE)
        dlg.add( mpfUpdateButton)
        if not m_sec or m_sec.getCurrentLevel() > 8:
            dlg.add( hgSPACE)
            dlg.add( hgPushButton(' Show ', DLG_FUNCTION + 'Show') )
            dlg.add( hgSPACE)
            dlg.add( hgPushButton(' Hide ', DLG_FUNCTION + 'Hide') )
            dlg.add( hgSPACE)
            dlg.add( mpfDeleteButton )
        dlg.add( hgNEWLINE)
        dlg.add( hgNEWLINE)

        # new entry
        dlg.add( 'New Value:')
        dlg.add( hgTextEdit(name = "new_entry"))
        dlg.add( mpfAddButton )
        dlg.add( '</center>' )
        dlg.add( hgNEWLINE)
        dlg.add( hgProperty('listname', self.listname) )
        dlg.add( mgr.getBackButtonStr(REQUEST) )
        return HTML( dlg.getHtml() )(self, REQUEST)


    ##########################################################################
    #
    # Manage Tab Methods
    #
    ##########################################################################
    def viewTab(self, REQUEST):
        """\brief List overview tab."""
        message = ''
        # test Request for creation button
        if REQUEST.get('create'):
            # create dbtable for list
            self.createTable()

            message = 'Database Table created.'

        if REQUEST.get('clear'):
            self.clearCache()
            message = 'Cache cleared.'
        dlg = getStdDialog('', 'viewTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        tab = hgTable()
        tab._old_style = False

        # show tables information
        tab[0, 0] = '<h3>List Overview</h3>'
        tab.setCellSpanning(0, 0, colspan = 3)

        tab[1, 0] = '<b>Name</b>'
        tab[1, 2] = '<b>Label</b>'
        tab[1, 6] = '<b>noedit</b>'


        tab[2, 0] = self.listname
        tab[2, 2] = self.label
        tab[2, 6] = (self.noedit and 'yes') or 'no'

        # try to get rowcount, if error: dbtable for list may not exist
        try:
            self.getValueCount()
            if message:
                tab[4, 0] = hgLabel(message)
                tab.setCellSpanning(4, 0, colspan = 3)
        except:
            # show table creation button for own normal lists
            tab[4, 0] = hgPushButton('Create List Table', 'create')
            tab.setCellSpanning(4, 0, colspan = 3)

        # clear cache
        tab[5, 0] = hgPushButton('Clear List Cache', 'clear')
        tab.setCellSpanning(5, 0, colspan = 3)

        dlg.add( tab )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def editTab(self, REQUEST):
        """\brief List edit tab."""
        message = ''

        # test Request for edit
        mgr = self.getManager()

        button = mgr.getPressedButton(REQUEST)

        if button:
            changedIds = mgr.getValueListFromRequest(REQUEST, 'entry')

            # add function
            if button == BTN_L_ADD:
                if 'new_entry' in REQUEST:
                    self.addValue(REQUEST['new_entry'])

            # delete function
            elif button == BTN_L_DELETE:
                for changed_id in changedIds:
                    changed_id = int(changed_id)
                    self.delValue(changed_id)

            # switch hide -> show
            elif button == 'Show':
                for changed_id in changedIds:
                    self.updateEntry( {SHOW: 'yes'}, changed_id )

            # switch show -> hide
            elif button == 'Hide':
                for changed_id in changedIds:
                    self.updateEntry( {SHOW: 'no'}, changed_id )
            # update function
            elif button == BTN_L_UPDATE:
                map( lambda changed_id:
                            self.updateEntry( { VALUE:
                                                REQUEST.get(self.listname +
                                                            changed_id),
                                                RANK:
                                                REQUEST.get('rank' + changed_id),
                                                NOTES:
                                                REQUEST.get('notes' + changed_id)
                                                },
                                              changed_id ),
                    changedIds )

        # interface building
        entry_list = self.getEntries()
        # sort by value
        own_cmp = lambda x, y: (x[ZC.TCN_AUTOID] < y[ZC.TCN_AUTOID]) and -1 or (x[ZC.TCN_AUTOID] > y[ZC.TCN_AUTOID]) and 1 or 0
        entry_list.sort(own_cmp)

        # build mask
        tab = hgTable()
        tab[0, 1] = dlgLabel('Id')
        tab[0, 2] = dlgLabel('Value')
        tab[0, 3] = dlgLabel('Rank')
        tab[0, 4] = dlgLabel('Show')
        tab[0, 5] = dlgLabel('Notes')
        row = 2

        # all existing list entries
        for entry in entry_list:
            tab[row, 1] = entry.get(ZC.TCN_AUTOID)
            tab[row, 4] = entry.get(SHOW)

            tab[row, 0] = hgCheckBox('', entry.get(ZC.TCN_AUTOID), name = 'entry')

            tab[row, 2] = hgTextEdit( entry.get(VALUE),
                                      name = self.listname +
                                      str(entry.get(ZC.TCN_AUTOID)))
            tab[row, 3] = hgTextEdit( entry.get(RANK),
                                      name = 'rank' + str(entry.get(ZC.TCN_AUTOID)))
            tab[row, 5] = hgTextEdit( entry.get(NOTES),
                                      name = 'notes' + str(entry.get(ZC.TCN_AUTOID)))
            row += 1

        #
        # dialog
        #

        dlg = getStdDialog('', 'editTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        dlg.add( '<center>' )
        dlg.add( tab )
        dlg.add( hgNEWLINE)

        dlg.add( mpfUpdateButton)
        dlg.add( hgSPACE)
        dlg.add( hgPushButton(' Show ', DLG_FUNCTION + 'Show') )
        dlg.add( hgSPACE)
        dlg.add( hgPushButton(' Hide ', DLG_FUNCTION + 'Hide') )
        dlg.add( hgSPACE)
        dlg.add( mpfDeleteButton )
        dlg.add( hgNEWLINE)
        dlg.add( hgNEWLINE)

        # new entry
        dlg.add( 'New Value:')
        dlg.add( hgTextEdit(name = "new_entry"))
        dlg.add( mpfAddButton )
        dlg.add( hgNEWLINE )
        dlg.add( message )
        dlg.add( '</center>' )

        return HTML( dlg.getHtml() )(self, REQUEST)


    def cacheTab(self, REQUEST):
        """\brief Table listcache tab."""

        dlg = getStdDialog(action = 'cacheTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        # table cache

        button = getPressedButton(REQUEST)
        if len(button) > 0 and button[0] == BTN_L_RESET2:
            self.clearCache()

        dlg.add(self.showListCache())

        dlg.add(mpfReset2Button)

        return HTML( dlg.getHtml() )(self, REQUEST)


    def showListCache(self):
        """\brief Show all cached lists belonging to that table."""
        tab = hgTable()
        tab[0, 0] = 'Name'

        tab[0, 1] = self.listname

        tab[2, 0] = '<b>Content</b>'
        entries = self.getEntries()
        row = 3
        for entry in entries:
            tab[row, 0] = entry
            tab.setCellSpanning(row, 0, colspan = 3)
            row += 1
        return tab


    def updateRevision(self):
        """\brief update this object"""
        self.enableCache = True
        self.cache       = None
