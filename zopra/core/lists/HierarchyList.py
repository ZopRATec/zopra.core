###########################################################################
#    Copyright (C) 2004 by Ingo Keller
#    <webmaster@ingo-keller.de>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

#
# Python Language Imports
#
from types                  import ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgComboBox   import hgComboBox
from PyHtmlGUI.widgets.hgLabel      import hgSPACE,   \
                                           hgNEWLINE, \
                                           hgLabel,   \
                                           hgProperty
from PyHtmlGUI.kernel.hgTable       import hgTable
from PyHtmlGUI.widgets.hgTextEdit   import hgTextEdit
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from PyHtmlGUI.widgets.hgCheckBox   import hgCheckBox

#
# ZopRA Imports
#
from zopra.core                     import HTML, ZC
from zopra.core.dialogs             import getStdDialog
from zopra.core.elements.Buttons    import mpfAddButton,     \
                                                     mpfDeleteButton,  \
                                                     mpfSelectHLButton,\
                                                     mpfRemoveHLButton,\
                                                     mpfUpdateButton,  \
                                                     DLG_FUNCTION,     \
                                                     DLG_CUSTOM,       \
                                                     BTN_L_ADD,        \
                                                     BTN_L_DELETE,     \
                                                     BTN_HL_SELECT,    \
                                                     BTN_L_UPDATE
from zopra.core.lists.MultiList     import MultiList
from zopra.core.widgets             import dlgLabel


class HierarchyList(MultiList):
    """ Hierarchical Lists (based on Multilists) """
    _className = 'HierarchyList'
    _classType = MultiList._classType + [_className]

    # for compatibility
    listtype   = 'hierarchylist'

    def __init__( self,
                  listname,
                  manager,
                  function,
                  table,
                  label    = '',
                  map      = None,
                  docache  = True ):
        """\brief Constructs a MultiList.
        """
        MultiList.__init__( self,
                            listname,
                            manager,
                            function,
                            table,
                            label,
                            map,
                            docache )


    def getWidget( self,
                   par         = 0,
                   with_hidden = False,
                   prefix      = '',
                   parent      = None,
                   search      = False ):
        """\brief Returns the html for a hierarchical list ."""
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix
        manager = self.getForeignManager()

        # check for true list
        if manager:
            if self.function:
                err  = 'Non-simple function-based foreign hierarchical '
                err += 'Lists are not supported yet.'
                raise ValueError(manager.getErrorDialog(err))
            else:
                if self.foreign in manager.tableHandler:
                    err = 'Non-simple table-based foreign hierarchical '
                    err += 'Lists are not supported yet.'
                    raise ValueError(manager.getErrorDialog(err))
        else:
            # manager not found
            return hgLabel('%s not found' % self.manager, parent = parent)

        # load list data and build multiselectlist
        entry_list = self.getEntries()

        # build all comboboxes of entries with different parent

        all_dict = {}
        for entry in entry_list:
            par1 = int(entry.get(ZC.RANK, 0))
            if not all_dict.get(par1):
                cbox = hgComboBox(name = 'level_' + pre + self.listname)
                all_dict[par1]  = cbox
                # any-selection
                if search:
                    cbox.insertItem( '-no selection-', '')
                    cbox.insertItem( '-any subitem-', 0)
            if with_hidden or entry.get(ZC.SHOW) != 'no':
                all_dict[par1].insertItem( entry[ZC.VALUE],
                                           entry[ZC.TCN_AUTOID])

        # insert -top level- : 0 in top widget
        top = all_dict.get(0)
        if not top:
            top = hgComboBox(name = 'level_' + pre + self.listname)
            all_dict[0] = top
        top.insertItem( '-top level-', -1)
        top.sort()

        # build html in a different function...
        return self.buildHierarchyListLevels( all_dict,
                                              int(par),
                                              None,
                                              with_hidden,
                                              None,
                                              parent )

    def buildHierarchyListLevels( self,
                                  all,
                                  par,
                                  selected,
                                  with_hidden,
                                  html,
                                  parent = None):
        """\brief Builds one level of the hierarchylist
                  and calls itself for the next level (bottom-top)."""
        # leaf entry selected->start with its parent
        if par not in all:
            if par == 0:
                # absolutely no values:
                return hgLabel('No values.', parent = parent)
            selected = par
            par   = self.getHierarchyListParent(par)

        # choose the correct list
        cbox = all[par]
        # set the correct selection
        if selected:
            cbox.setCurrentValue(selected)
        else:
            cbox.resetSelected()
        # build own part
        if parent == 0:
            this_par = parent
        else:
            this_par = None
        tab = hgTable(parent = this_par)
        # add list and buttons
        tab[0, 0] = "&gt;"
        tab[0, 1] = cbox
        # add the sub-levels
        if html:
            html.reparent(tab)
            tab[1, 1] = html
            tab.setCellSpanning(1, 1, 1, 2)
        if not par == 0:
            # get the parent of the actual parent
            newparent = self.getHierarchyListParent(par)
            # call the next level
            return self.buildHierarchyListLevels( all,
                                                  int(newparent),
                                                  int(par),
                                                  with_hidden,
                                                  tab,
                                                  parent )
        else:
            # top level
            return tab


    def getHierarchyListParent(self, autoid):
        """\brief Returns the parent-id (stored in rank for the beginning)
                  of the entry with autoid in the list."""
        if autoid == 0:
            return None
        entry = self.getEntry( autoid )
        return int( entry.get(ZC.RANK, 0) )


    def getHierarchyListAncestors(self, autoid):
        """\brief utility function for new hierarchylist template handling, retrieves the ancestor line of an entry with the given autoid"""
        ancestors = []
        # show / list widgets need an empty list, when no value was given (None or '')
        if autoid in (None, ''):
            return []
        # in all other cases, autoid is a number (0 for first level on search)
        autoid = int(autoid)
        ancestor = self.getHierarchyListParent(autoid)
        while ancestor is not None:
            ancestors.append(ancestor)
            ancestor = self.getHierarchyListParent(ancestor)
        ancestors.reverse()
        ancestors.append(autoid)
        return ancestors


    def getHierarchyListDescendants(self, autoid):
        """\brief """
        descendants = []
        autoid = int(autoid)

        for child in self.getEntriesByParent(autoid):
            descendants.append(child['autoid'])
            descendants = descendants + self.getHierarchyListDescendants(child['autoid'])

        return descendants


    def handleSelectionAdd(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Select-Request for the
                  HierarchyList-Handling
        """
        # prefix is only for REQUEST-handling
        if prefix:
            pre = DLG_CUSTOM + prefix
        else:
            pre = ''
        # get the autoids from REQUEST
        add = REQUEST.get('level_' + pre + self.listname, [])
        if not isinstance(add, ListType):
            add = [add]
        # parent 0 is the starting point
        parent = 0
        # only search if -1 wasn't submitted, else parent stays 0
        if '-1' not in add:
            while True:
                found = False
                # check all submitted values
                for entry in add:
                    # one step down - correct entry found, set as parent, stop
                    # proceed with next level
                    if entry:
                        if self.getHierarchyListParent( int(entry) ) == parent:
                            parent = int(entry)
                            found  = True
                            break
                # no entry found in this level, correct level already selected
                if not found:
                    break

        # now parent is the selected autoid
        autoid = parent

        # the autoid is parent of a list (or could become)
        descr_dict['level_' + self.listname] = autoid

        entries = self.getEntries()

        if '0' in add:
            # all sublevels of the autoid will be selected
            new_list = self.getAllSubLeafs(autoid, entries)
            selected_list = descr_dict.get(self.listname, [])
            for autoid in new_list:
                if autoid not in selected_list:
                    selected_list.append(autoid)
            descr_dict[self.listname] = selected_list

        else:
            # normal selection (either sublist or leave)
            # if the autoid is not == the rank of any element
            found   = False
            for entry in entries:
                if entry.get(ZC.RANK) and int(entry[ZC.RANK]) == int(autoid):
                    found = True
            if not found and int(autoid) != 0:
                # autoid is a leaf element, we move it to the selected-list
                selected_list = descr_dict.get(self.listname, [])
                if autoid not in selected_list:
                    selected_list.append(autoid)
                descr_dict[self.listname] = selected_list
        # we don't need a return value, descr_dict is an object


    def getAllSubLeafs(self, autoid, entries):
        """\brief Find all leaves of the given branch"""
        children = []
        # search entries
        for entry in entries:
            # test for parent = autoid
            if (entry.get(ZC.RANK) or entry.get(ZC.RANK) == 0) and int(entry[ZC.RANK]) == int(autoid):
                # found a child
                childid = entry.get(ZC.TCN_AUTOID)
                # test it for own children
                newChildren = self.getAllSubLeafs(childid, entries)
                if not newChildren:
                    # this entry is a leaf child
                    children.append(childid)
                else:
                    # there are children, we put them in the result list
                    children.extend(newChildren)
        # return child list
        return children


    def handleSelectionRemove(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Remove-Request for the
                  HierarchyList-Handling
        """
        # prefix is only for REQUEST-handling
        if prefix:
            pre = DLG_CUSTOM + prefix
        else:
            pre = ''

        # get the autoids from REQUEST
        delete = REQUEST.get('del' + pre + self.listname, [])
        if delete:
            # single-value comes not as list
            if not isinstance(delete, ListType):
                delete = [delete]
            # get the list from descr_dict
            selected_list = descr_dict.get(self.listname, [])
            for autoid in delete:
                # delete the id, if present
                if int(autoid) in selected_list:
                    selected_list.remove(int(autoid))
        # we don't need a return value, because descr_dict is an object


    def getComplexWidget( self,
                          with_hidden = False,
                          descr_dict  = None,
                          search      = False,
                          prefix      = None,
                          parent      = None ):
        """\brief Builds a table with the hierarchy list, the selected values,
                  select-button and remove-button."""
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix
        if not descr_dict:
            descr_dict = {}
        level     = int( descr_dict.get('level_' + self.listname, 0) )
        selected  = descr_dict.get(self.listname, [])
        tab       = hgTable(parent = parent)
        tab[0, 0] = self.getWidget(level, with_hidden, prefix, tab, search)
        if selected:
            subtab = hgTable(parent = tab)
            if not isinstance(selected, ListType):
                selected = [selected]
            row = 0
            for entry in selected:
                subtab[row, 0] = hgCheckBox( name   = 'del' + pre + self.listname,
                                             value  = str(entry),
                                             parent = subtab )
                subtab[row, 2] = hgProperty( pre + self.listname,
                                             entry,
                                             parent = subtab )
                subtab[row, 1] = self.getHierarchyListEntryString( entry )
                subtab.setCellNoWrap(row, 1)
                row  += 1
            # search concat
            if search:
                # checkbox
                bname = pre + self.listname + '_AND'
                box = hgCheckBox(name = bname, value = '1', parent = subtab)
                if descr_dict.get(self.listname + '_AND'):
                    box.setChecked(True)
                subtab[row, 0] = box
                subtab[row, 1] = dlgLabel('AND Concatenation', parent = subtab)

            tab[0, 1] = subtab
        else:
            tab[0, 1] = hgLabel('Nothing selected', parent = tab)
        tab[1, 0] = mpfSelectHLButton
        tab[1, 1] = mpfRemoveHLButton
        return tab


    def editForm(self, REQUEST=None):
        """\brief Edit-Form for Hierarchical lists."""
        mgr = self.getManager()
        # first buttonhandling:
        if not REQUEST:
            REQUEST = {}
        level  = int( REQUEST.get('list_level', 0) )
        button = mgr.getPressedButton(REQUEST)
        if button:
            changedIds = mgr.getValueListFromRequest(REQUEST, 'entry')
            if button == BTN_HL_SELECT:
                # if select-button is pressed, change level
                descr_dict = {}
                self.handleSelectionAdd(REQUEST, descr_dict)
                level = descr_dict.get('level_' + self.listname)
                # a leaf entry has been selected (maybe to create a new sublist)
                if descr_dict.get(self.listname):
                    level = descr_dict[self.listname][0]

            elif button == BTN_L_ADD:
                value = REQUEST.get('new_entry')
                self.addValue(value, rank = level)

            # delete function
            elif button == BTN_L_DELETE:
                for changed_id in changedIds:
                    changed_id = int(changed_id)
                    self.delValue(changed_id)

            # switch hide -> show
            elif button == 'Show':
                for changed_id in changedIds:
                    self.updateEntry( {ZC.SHOW: 'yes'},
                                      changed_id )

            # switch show -> hide
            elif button == 'Hide':
                for changed_id in changedIds:
                    self.updateEntry( {ZC.SHOW: 'no'},
                                      changed_id )

            # update function
            elif button == BTN_L_UPDATE:
                for changed_id in changedIds:
                    self.updateEntry(
                                { ZC.VALUE: REQUEST.get( self.listname +
                                                      changed_id),
                                  ZC.RANK:  REQUEST.get( 'parent' + changed_id, 0)
                                  },
                                changed_id)

        # now the html
        tab = hgTable()
        tab[0, 1] = 'Values'
        tab[0, 2] = 'Show'
        tab[0, 3] = 'Id'
        tab[0, 4] = 'ParentId'

        row = 1
        entries = self.getEntries(with_hidden = True)
        for entry in entries:
            if int(entry.get(ZC.RANK)) == level:
                tab[row, 0] = hgCheckBox( name  = 'entry',
                                          value = entry.get(ZC.TCN_AUTOID) )
                tab[row, 1] = hgTextEdit( entry.get(ZC.VALUE),
                                          name = self.listname +
                                                 str( entry.get(ZC.TCN_AUTOID) )
                                          )
                tab[row, 2] = entry.get( ZC.SHOW )
                tab[row, 3] = entry.get( ZC.TCN_AUTOID )
                tab[row, 4] = hgTextEdit( entry.get(ZC.RANK),
                                          name = 'parent' +
                                                 str( entry.get( ZC.TCN_AUTOID ) )
                                          )
                row += 1

        dlg  = getStdDialog('Edit %s list' % self.label, 'editForm')

        dlg.add( '<center>' )
        dlg.add(self.getWidget(level, True))
        dlg.add(hgNEWLINE)
        dlg.add(mpfSelectHLButton)
        dlg.add(hgNEWLINE)
        dlg.add(hgNEWLINE)
        dlg.add(tab)
        dlg.add(hgNEWLINE)
        dlg.add(hgNEWLINE)
        dlg.add(mpfUpdateButton)
        dlg.add(hgSPACE)
        dlg.add(hgPushButton(' Show ', DLG_FUNCTION + 'Show') )
        dlg.add(hgSPACE)
        dlg.add(hgPushButton(' Hide ', DLG_FUNCTION + 'Hide') )
        dlg.add(hgSPACE)
        dlg.add(mpfDeleteButton )
        dlg.add(hgNEWLINE)
        dlg.add(hgNEWLINE)
        dlg.add(hgProperty('listname', self.listname))
        dlg.add(hgProperty('list_level', level))
        dlg.add(dlgLabel('New Value'))
        dlg.add(hgTextEdit( '', name = 'new_entry' ) )
        dlg.add(hgSPACE)
        dlg.add(mpfAddButton)
        dlg.add( '</center>' )
        dlg.add( hgNEWLINE)
        dlg.add( mgr.getBackButtonStr(REQUEST) )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def getHierarchyListEntryString(self, autoid):
        """\brief Builds a string containing all levels up to 0
                  starting with given id."""
        entry     = self.getEntry(autoid)
        resultstr = ''
        parent    = autoid
        while not int(parent) == 0:
            entry     = self.getEntry(parent)
            if not entry:
                # something wrong, abort
                return resultstr
            resultstr = hgSPACE + '&gt;' + hgSPACE + entry.get(ZC.VALUE) + resultstr
            parent    = entry.get(ZC.RANK)
        return resultstr


    def getShowHtml( self,
                     descr_dict,
                     useProperties = False,
                     parent        = None ):
        """\brief Builds a html-formatted string of values."""
        hlist  = descr_dict.get(self.listname, [])
        tab = hgTable(parent = parent)
        row = 0
        for entry in hlist:
            tab[row, 0] = self.getHierarchyListEntryString(entry)
            if useProperties:
                name  = self.listname
                value = str(entry)
                tab[row, 1] = hgProperty( name   = name,
                                          value  = value,
                                          parent = tab )
            tab.setCellNoWrap(row, 0)
            row += 1

        return tab

    def getEntriesByParent(self, parentid = None, with_hidden = False):
        """\brief Returns all entrys Connected to a Parrent, 0 = First Rank Entries without parent"""
        # value - searches are not put in cache and not taken from cache completely
        # only the single entries are later on fetched from cache
        mgr = self.getForeignManager()
        if self.foreign and self.foreign in mgr.listHandler:
            lobj  = mgr.listHandler[self.foreign]
            return lobj.getEntriesByParent(parentid, with_hidden)
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
