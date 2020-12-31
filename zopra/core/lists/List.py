"""Basic List Handling and List Entry Management."""

from copy import deepcopy
from operator import itemgetter
from types import IntType
from types import ListType
from types import StringType
from types import UnicodeType

from PyHtmlGUI import E_PARAM_TYPE
from PyHtmlGUI.kernel.hgTable import hgTable
from PyHtmlGUI.widgets.hgCheckBox import hgCheckBox
from PyHtmlGUI.widgets.hgLabel import hgLabel
from PyHtmlGUI.widgets.hgLabel import hgNEWLINE
from PyHtmlGUI.widgets.hgLabel import hgSPACE
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from PyHtmlGUI.widgets.hgTextEdit import hgTextEdit
from zopra.core import HTML
from zopra.core import ZC
from zopra.core.dialogs import getStdDialog
from zopra.core.elements.Buttons import BTN_L_ADD
from zopra.core.elements.Buttons import BTN_L_DELETE
from zopra.core.elements.Buttons import BTN_L_RESET2
from zopra.core.elements.Buttons import BTN_L_UPDATE
from zopra.core.elements.Buttons import DLG_FUNCTION
from zopra.core.elements.Buttons import getPressedButton
from zopra.core.elements.Buttons import mpfAddButton
from zopra.core.elements.Buttons import mpfDeleteButton
from zopra.core.elements.Buttons import mpfReset2Button
from zopra.core.elements.Buttons import mpfUpdateButton
from zopra.core.lists.GenericList import GenericList
from zopra.core.lists.GenericList import _list_definition
from zopra.core.dialogs import dlgLabel


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
            ldef[ZC.VALUE + '_' + translation] = {ZC.COL_TYPE: 'string'}
        self._list_definition = ldef


    def createTable(self):
        """\brief Create the database table."""

        # try to create the list
        mgr = self.getManager()
        m_product = mgr.getManager(ZC.ZM_PM)
        # only create table if it is a local list

        # create all
        m_product.addTable( mgr.id + self.listname,
                            self._list_definition )



    def deleteTable(self, omit_log = None):
        """\brief Create the database table."""

        mgr       = self.getManager()
        m_product = mgr.getManager(ZC.ZM_PM)
        my_id     = mgr.getId()
        log = True

        for ident in omit_log:
            if ident in mgr.getClassType():
                log = False

        m_product.delTable( my_id + self.listname, log )


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
                          ZC.VALUE:    value,
                          ZC.NOTES:    notes,
                          ZC.RANK:     rank,
                          ZC.SHOW:     show
                         }
            for trans in self.translations:
                key = ZC.VALUE + '_' + trans
                if kwargs.get(key):
                    entry_dict[key] = kwargs[key]
            m_product = mgr.getManager(ZC.ZM_PM)
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
        mgr.getManager(ZC.ZM_PM).simpleDelete( mgr.id + self.listname,
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
        cols = [ZC.TCN_AUTOID, ZC.VALUE, ZC.NOTES, ZC.RANK, ZC.SHOW]
        # copy list definition (for language enhancement)
        list_definition = {}
        for item in _list_definition:
            list_definition[item] = _list_definition[item]

        # language handling
        for translation in self.translations:
            name = '%s_%s' % (ZC.VALUE, translation)
            # add to columns and into list_definition
            cols.append(name)
            list_definition[name] = list_definition[ZC.VALUE]
        where_dict = {ZC.TCN_AUTOID: autoid}

        m_product = mgr.getManager(ZC.ZM_PM)
        my_id     = mgr.getId()
        results = m_product.simpleSelectFrom( my_id + self.listname,
                                    cols,
                                    list_definition,
                                    where_dict)
        entry_dict = {}
        if results:
            # language values are in already
            entry_dict = results[0]
            # just convert the rank type (not entirely sure why, this should be int already)
            if entry_dict.get(ZC.RANK):
                entry_dict[ZC.RANK] = int(entry_dict[ZC.RANK])
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
            # search for value
            where = ''
            if value:
                # *-search is allowed (using %), remove ' from value
                # TODO: use checkType for sql check
                value = value.replace('*', '%').replace("'", "")
                where = " WHERE value like '%s'" % value

            sql = 'SELECT %s FROM %s%s%s;'
            sql = sql % (ZC.TCN_AUTOID, mgr.id, self.listname, where)
            results = mgr.getManager(ZC.ZM_PM).executeDBQuery(sql)
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
            completelist = [entry for entry in completelist if entry.get(ZC.SHOW) != 'no']

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
        results = mgr.getManager(ZC.ZM_PM).executeDBQuery(sql)
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
            m_product = mgr.getManager(ZC.ZM_PM)

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
                val2entry[entry.get(ZC.VALUE)] = entry

            # get the autoid for each value
            for val in values:
                autoid = None
                entry  = val2entry.get(val, None)

                if entry:
                    # added rank == '' test to avoid empty rank which doesn't match
                    if rank is None or rank == '' or entry.get(ZC.RANK) == rank:
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
                    # allow *-search, remove ' chars
                    # TODO: use checkType
                    val = val.replace('*', '%').replace("'", "")
                    result = mgr.getManager(ZC.ZM_PM).executeDBQuery(query_text % val)

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

        results = mgr.getManager(ZC.ZM_PM).executeDBQuery( query_text )
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

        return mgr.getManager(ZC.ZM_PM).getRowCount(mgr.id + self.listname)


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
                        value = lang and entry.get(ZC.VALUE + '_' + lang) or entry.get(ZC.VALUE)
                else:
                    sel = lang and ZC.VALUE + '_' + lang + ', ' or ''
                    query_text = "SELECT %svalue FROM %s%s WHERE autoid = %s;" \
                                 % (sel, mgr.getId(), self.listname, aid)
                    result = mgr.getManager(ZC.ZM_PM).executeDBQuery(query_text)

                    if result:
                        value = result[0][0]
                        if not value and lang:
                            value = result[0][1]

            retlist.append(value)

        return retlist if is_list else retlist[0]

    ##########################################################################
    #
    # Legacy editForm Stub for patching
    #
    ##########################################################################

    def editForm(self, REQUEST = None):
        """\brief Return the html source of the edit list form."""
        return 'Legacy method. Not implemented.'

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
        tab[2, 2] = self.label.encode('utf8')
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

    # TODO: what about translation-columns?
    def editTab(self, REQUEST):
        """\brief List edit tab."""
        message = ''

        # test Request for edit
        mgr = self.getManager()

        buttons = getPressedButton(REQUEST)
        if len(buttons) > 0:
            button = buttons[0]
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
                    self.updateEntry( {ZC.SHOW: 'yes'}, changed_id )

            # switch show -> hide
            elif button == 'Hide':
                for changed_id in changedIds:
                    self.updateEntry( {ZC.SHOW: 'no'}, changed_id )
            # update function
            elif button == BTN_L_UPDATE:
                map( lambda changed_id:
                            self.updateEntry( { ZC.VALUE:
                                                REQUEST.get(self.listname +
                                                            changed_id),
                                                ZC.RANK:
                                                REQUEST.get(ZC.RANK + changed_id),
                                                ZC.NOTES:
                                                REQUEST.get(ZC.NOTES + changed_id)
                                                },
                                              changed_id ),
                    changedIds )

        # interface building
        entry_list = self.getEntries(with_hidden=True)
        # sort by value
        entry_list = sorted(entry_list, key=itemgetter(ZC.TCN_AUTOID))

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
            rank = entry.get(ZC.RANK) or u''
            value = entry.get(ZC.VALUE) or ''
            notes = entry.get(ZC.NOTES) or u''
            tab[row, 1] = entry.get(ZC.TCN_AUTOID)
            tab[row, 4] = entry.get(ZC.SHOW)

            tab[row, 0] = hgCheckBox('', entry.get(ZC.TCN_AUTOID), name = 'entry')

            tab[row, 2] = hgTextEdit( value.encode('utf8'),
                                      name = self.listname +
                                      str(entry.get(ZC.TCN_AUTOID)))
            tab[row, 3] = hgTextEdit( rank,
                                      name = ZC.RANK + str(entry.get(ZC.TCN_AUTOID)))
            tab[row, 5] = hgTextEdit( notes.encode('utf8'),
                                      name = ZC.NOTES + str(entry.get(ZC.TCN_AUTOID)))
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
