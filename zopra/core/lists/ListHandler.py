###########################################################################
#    Copyright (C) 2004 by ZopRATec                                       #
#    <webmaster@ingo-keller.de>                                           #
#                                                                         #
# Copyright: See COPYING file that comes with this distribution           #
#                                                                         #
###########################################################################
import string
from types                           import ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton
from PyHtmlGUI.kernel.hgTable        import hgTable
from PyHtmlGUI.kernel.hgWidget       import hgWidget
from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout
from PyHtmlGUI.widgets.hgLabel       import hgLabel,       \
                                            hgSPACE,       \
                                            hgProperty

#
# ZopRA Imports
#
from zopra.core                     import HTML, Folder, ZM_PM, ZM_SCM, ZC
from zopra.core.dialogs             import getStdDialog,       \
                                           getStdZMOMDialog
from zopra.core.elements.Buttons    import BTN_L_ADDITEM,  \
                                           BTN_L_REMOVE,   \
                                           BTN_L_FILTER,   \
                                           BTN_HL_SELECT,  \
                                           BTN_HL_REMOVE,  \
                                           BTN_FRL_PREV,   \
                                           BTN_FRL_NEXT,   \
                                           DLG_CUSTOM,     \
                                           mpfContinueButton
from zopra.core.lists.GenericList   import GenericList
from zopra.core.lists.List          import List
from zopra.core.lists.ForeignList   import ForeignList
from zopra.core.lists.MultiList     import MultiList
from zopra.core.lists.HierarchyList import HierarchyList
from zopra.core.utils               import getParentManager, getASTFromXML
from zopra.core.widgets             import dlgLabel


LISTTYPES = ['singlelist', 'multilist', 'hierarchylist']


class ListHandler(Folder):
    """ List Handler """

    _className = 'ListHandler'
    _classType = [_className]

    manage_options = ( { 'label':  'List Objects',
                         'action': 'manageOverview'   },
                       { 'label':  'List References',
                         'action': 'manageReferences' },
                       ) + Folder.manage_options

    def __init__(self):
        """\brief Constructs a ListHandler.
        """
        Folder.__init__(self, 'listHandler')

        self.mapcol2list    = {}
        self.maptable2lists = {}  # maptable2lists[table][listtype] -> [ lists ]


    def xmlInit(self, xml, nocreate = False):
        """\brief Create list definition objects (List) and
        list access objects (Foreign, Multi and HierarchyList)"""

        tmp_obj = getASTFromXML(xml)

        # setup lists (given as <List> in the xml file)
        for list_idx in tmp_obj.list:
            list_        = tmp_obj.list[list_idx]
            list_name    = list_.getName().encode('utf-8')
            label        = list_.getLabel()
            translations = list_.getTranslations()
            translist    = []
            if translations:
                transtmp = translations.encode('utf-8').split(',')
                for trans in transtmp:
                    trans = trans.strip()
                    if trans not in translist:
                        translist.append(trans)

            # create list objects
            lobj  = self.addList( list_name,
                                  label,
                                  nocreate,
                                  translist)

            # noedit affects the appearance of the column in the
            # listedit-section of _index_html
            if list_.getNoedit():
                lobj.noedit    = True

        # get the manager parent of the list handler
        manager = self.getManager()

        # connect columns to lists
        for table_idx in tmp_obj.table:
            table = tmp_obj.table[table_idx]
            table_name = table.getName().encode('utf-8')

            # iterate over columns
            for column_idx in table.column:
                column      = table.column[column_idx]
                column_type = column.getType().encode('utf-8')

                if column_type in LISTTYPES:
                    lobj  = self.connectList( manager,
                                              table_name,
                                              column,
                                              nocreate )

                    if not lobj:
                        column_name = column.getName().encode('utf-8')
                        raise ValueError('Cannot create list for column \'%s\' in table \'%s\'' % (column_name, table_name) )

                    if column.getNotes():
                        notes    = column.getNotes().encode('utf-8')
                        if notes == '1':
                            notes = True
                        elif notes == '0' or not notes:
                            notes = False
                        lobj.notes = notes

                    if column.getNoteslabel():
                        lobj.noteslabel = column.getNoteslabel()

                    if column.getLabelsearch():
                        lobj.labelsearch = True

                    if column.getMaxshown():
                        lobj.maxshown = int(column.getMaxshown())

                    # FIXME: check if this is necessary, only cols should be invisible, not the foreign lists
                    if column.getInvisible():
                        lobj.invisible = True
        if not nocreate:
            self.addListTableIndexes()


    def addListTableIndexes(self):
        """\brief add DB indexes for list tables and multi tables"""
        # TODO: move SQL to Connector / Product
        manager = self.getManager()
        pm = manager.getManager(ZC.ZM_PM)
        def mapname(lobj, mgr):
            if lobj.map:
                dbname = '%smulti%s' % ( mgr.getId(), lobj.map)
            else:
                dbname = '%smulti%s%s' % ( mgr.getId(), lobj.table, lobj.listname)
            return dbname
        counter1 = 0
        counter2 = 0
        tables = manager.tableHandler.keys()
        # create index for multilists / hierarchylists on multi-table
        for table in tables:
            for lobj in manager.listHandler.getLists(table, ['multilist', 'hierarchylist']):
                try:
                    # add index to multitable for tableid
                    name = mapname(lobj, manager)
                    sql = "ALTER TABLE %s ADD INDEX idxmulti1_%s (tableid)" % (name, lobj.listname)
                    pm.executeDBQuery(sql)
                except Exception, ex:
                    if str(ex).find('Duplicate key name') != -1:
                        pass
                    else:
                        raise
                try:
                    # add index to multitable for listname column
                    sql = "ALTER TABLE %s ADD INDEX idxmulti2_%s (%s)" % (name, lobj.listname, lobj.listname)
                    pm.executeDBQuery(sql)
                except Exception, ex:
                    if str(ex).find('Duplicate key name') != -1:
                        pass
                    else:
                        raise
                counter1 += 1
        # create indexes for all list tables
        for onelist in manager.listHandler.keys():
            lobj = manager.listHandler[onelist]
            try:
                # add index to listtable for value column
                sql = "ALTER TABLE %s%s ADD INDEX idx_%s (value)" % (manager.id, lobj.listname, lobj.listname)
                pm.executeDBQuery(sql)

            except Exception, ex:
                if str(ex).find('Duplicate key name') != -1:
                    pass
                else:
                    raise
            counter2 += 1
        print 'created indexes (table-ref, list-ref) for %s multilists, , created indexes (value) for % lists' % (counter1, counter2)


    def getManager(self):
        """This method returns the owning manager.

        @returns Manager the parent manager of the list
        """
        return getParentManager(self)


    def __getitem__(self, key):
        """\brief the itemgetter (use via listHandler[<listname>]) only returns List objects"""
        if hasattr(self, key):
            return getattr(self, key)
        else:
            raise ValueError('List "%s" does not exist' % key)


    def __setitem__(self, key, value):
        setattr(self, key, value)


    def __delitem__(self, key):
        delattr(self, key)


    def __contains__(self, key):
        return self.hasObject(key)

    def keys(self):
        """\brief returns all names of basic List objects"""
        keylist = []
        for item in dir(self):
            if hasattr(self, str(item)):
                attr = getattr(self, item)
                # just take genuine db lists
                if hasattr(attr, '_classType') and 'List' in attr._classType:
                    keylist.append(item)
        return keylist

    def getListIDs(self):
        """ This method returns all the IDs for the handled table.

        @return List - list of Zope IDs
        """
        return self.objectIds(List.meta_type)


    def addList( self,
                 listname,
                 label          = None,
                 nocreate       = False,
                 translations   = None ):
        """\brief Adds an list lookup table.

        \param list_name  The argument \a list_name is a string with the name
        of the new list without the manager id prefix.
        """
        if listname in self:
            return self.get(listname)

        if not translations:
            translations = []

        lobj = List( listname, label, nocreate, translations )
        self._setObject(listname, lobj)

        lobj_withmgr = self[listname]
        if not nocreate:
            lobj_withmgr.createTable()

        return lobj_withmgr


    def connectList( self,
                     local_manager,
                     table,
                     column,
                     nocreate = False ):
        """\brief Connects a table column to a list.
        """

        # get the parameters
        listname  = column.getName().encode('utf-8')
        listtype  = column.getType().encode('utf-8')

        manager   = function = label = map_ = None
        invisible = False

        if column.getManager():
            manager  = column.getManager().encode('utf-8')
        else:
            manager = local_manager.getClassName()
        if column.getFunction():
            function = column.getFunction().encode('utf-8')
        else:
            function = listname + '()'
        if column.getMap():
            map_  = column.getMap().encode('utf-8')
        if column.getLabel():
            label = column.getLabel()

        if str(column.getInvisible()).upper() in ['1', 'T', 'TRUE', 'Y', 'YES']:
            invisible = True

        # create the list reference
        lobj = None

        if listtype == 'singlelist':
            # use the original list if possible
            lobj = ForeignList(listname, manager, function, label)
        elif listtype == 'multilist':
            lobj = MultiList(listname, manager, function, table, label, map_)
        elif listtype == 'hierarchylist':
            lobj = HierarchyList(listname, manager, function, table, label, map_)
        else:
            raise ValueError("listtype contains invalid type %s" % listtype)

        lobj.invisible = invisible

        # insert list into the listhandler
        self._setObject(str(table) + '_' + listname, lobj)

        # get wrapped list object
        lobj_withmgr = self[str(table) + '_' + listname]

        # operate on wrapped object
        if listtype in ['multilist', 'hierarchylist']:
            lobj_withmgr.initDBName()

        if not nocreate:
            lobj_withmgr.createTable()

        self.mapcol2list[(table, listname)] = listname

        # aux var to simplify access to lists
        if table not in self.maptable2lists.keys():
            self.maptable2lists[table] = {}
            self.maptable2lists[table]['singlelist']    = []
            self.maptable2lists[table]['multilist']     = []
            self.maptable2lists[table]['hierarchylist'] = []

        self.maptable2lists[table][listtype].append(listname)

        return lobj_withmgr


    def delList(self, listname, dboperate = False ):
        """\brief Deletes an list lookup table.

        \param list_name  The argument \a list_name is a string with the name
        of the list which should be deleted.

        \throw ValueError if the list doesn't exist.
        """

        if listname not in self:
            return False

        lobj = self[listname]

        if dboperate:
            lobj.deleteTable( omit_log = [ZM_SCM, ZM_PM] )

        self._delObject(listname)
        return True


    def disconnectList(self, table, column, dboperate = False ):
        """\brief Deletes an list reference object
        """

        if (table, column) not in self.mapcol2list:
            return False

        lobj = self[str(table) + '_' + column]

        if not lobj:
            return

        if dboperate:
            lobj.deleteTable( omit_log = [ZM_SCM, ZM_PM] )

        del self.mapcol2list[ (table, column) ]
        self.maptable2lists[table][lobj.listtype].remove(lobj.listname)

        self._delObject(str(table) + '_' + column)

        return True


    def getList(self, table, column):
        """\brief Access list for column in table"""
        try:
            return self['%s_%s' % (table, column)]  # self.mapcol2list.get( (table, column), None )
        except:
            msg = 'No list found for column [%s] in table [%s]' % (column, table)
            raise ValueError(msg)


    def hasList(self, table, column):
        """\brief Access list for column in table"""

        # TODO: remove this check after successful complete update
        if not hasattr(self, 'mapcol2list'):
            raise ValueError('old listhandler found: %s' % self.absolute_url())

        return (table, column) in self.mapcol2list


    def getLists(self, table, types = ['singlelist', 'multilist', 'hierarchylist'], include = True):
        """\brief Get all lists of a table that match"""
        if table not in self.maptable2lists:
            return []

        lists = []
        types = types if isinstance(types, ListType) else [types]

        for listtype in ['singlelist', 'multilist', 'hierarchylist']:

            process = bool(listtype in types)

            if not include:
                process = not process

            if process:
                for listname in self.maptable2lists[table][listtype]:
                    lists.append(self[str(table) + '_' + listname])

        return lists


    def references(self):
        """\brief returns all list-keys."""
        return self.mapcol2list.keys()


    def emptyListCache(self, listname = None):
        """\brief Empties all cached objects from list handling."""
        listnames = []
        if listname:
            listnames = [listname]
        else:
            listnames = self.keys()

        for entry in listnames:
            self[entry].clearCache()


#
# context menu
#
    def getListContextTable(self, parent, multiCol = 1):
        """\brief Returns all available lists in this handler (html)"""

        widg = hgWidget(parent = parent)
        lay  = hgGridLayout(widg, 2, 1, 10, 0)
        row = 0
        col = 0
        ordered_list  = []
        for item in self.getListIDs():
            if self[item].noedit is not True:
                label = self[item].getLabel( )
                if not label or label == ' ':
                    continue
                ordered_list.append( (label, item) )

        ordered_list.sort()
        for (label, listname) in ordered_list:
            link      = 'listHandler/%s/editForm' % listname
            lab = hgLabel( 'Edit List %s' % label, link, parent = widg )
            lay.addWidget(lab, row, col)

            col += 1
            if not col % multiCol:
                col = 0
                row += 1

        if row > 0 or col > 0:
            return widg
        else:
            return None


    def checkEmptyEditList(self, table, edit_dict, descr_dict):
        """\brief checks wether a list has been edited to emtpy
                  and changes the descr_dict."""
        #
        # \BUG: edit_dict needs at least one other entry for empty lists
        # to be recognized
        # \FIXME: edit_dict has to be empty on first call of function.
        if not edit_dict:
            return
        for (tab, col) in self.mapcol2list.keys():
            if tab != table or \
               col not in descr_dict:
                continue

            lobj = self[tab + '_' + col]
            if lobj.listtype in ['multilist', 'hierarchylist'] and \
               col not in edit_dict:

                descr_dict[col] = []
        return


    def handleListButtons(self, table, button, REQUEST, descr_dict, prefix = None):
        """\brief removes or adds values from/to descr_dict
                    according to button/REQUEST."""
        # button might be buttonname + '_' + listname
        # multilist add
        if button.startswith(BTN_L_ADDITEM):
            # only commented once, same for all buttons
            # length mismatch -> listname at end of buttonname
            if len(button) != len(BTN_L_ADDITEM):
                # get the listname
                tmpname = button[len(BTN_L_ADDITEM) + 1:]
                # prefixed lists
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    # rest of name is listname
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    # no prefix, all is listname
                    listname = tmpname
                # for multitable-searchhandling, check whether list exists
                if not self.hasList(table, listname):
                    # list does not belong to this table/manager
                    return
                # get the list object
                listobj = self.getList(table, listname)
                # check listtype to be sure
                if listobj.listtype in ['singlelist', 'multilist']:
                    # handle it
                    listobj.handleSelectionAdd(REQUEST, descr_dict, prefix)
            # lenth match -> listname not given, could be any
            # this allows one button to act for all lists -> sometimes desired behaviour
            else:
                # cycle through lists, check all
                for (tab, col) in self.mapcol2list.keys():
                    # at least we can match the tablename
                    if tab != table:
                        continue
                    # found a matching list, get it
                    listobj = self[tab + '_' + col]
                    # check listtype to be sure
                    if listobj.listtype in ['singlelist', 'multilist']:
                        # handle it
                        listobj.handleSelectionAdd(REQUEST, descr_dict, prefix)

        # multilist remove
        elif button.startswith(BTN_L_REMOVE):
            if len(button) != len(BTN_L_REMOVE):
                tmpname = button[len(BTN_L_REMOVE) + 1:]
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    listname = tmpname
                if not self.hasList(table, listname):
                    return
                listobj = self.getList(table, listname)
                if listobj.listtype == 'multilist':
                    listobj.handleSelectionRemove(REQUEST, descr_dict, prefix)
            else:
                for (tab, col) in self.mapcol2list.keys():
                    if tab != table:
                        continue
                    listobj = self[tab + '_' + col]
                    if listobj.listtype == 'multilist':
                        listobj.handleSelectionRemove(REQUEST, descr_dict, prefix)

        # hierarchylist add
        elif button.startswith(BTN_HL_SELECT):
            if len(button) != len(BTN_HL_SELECT):
                tmpname = button[len(BTN_HL_SELECT) + 1:]
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    listname = tmpname
                if not self.hasList(table, listname):
                    return
                listobj = self.getList(table, listname)
                if listobj.listtype == 'hierarchylist':
                    listobj.handleSelectionAdd(REQUEST, descr_dict, prefix)
            else:
                for (tab, col) in self.mapcol2list.keys():
                    if tab != table:
                        continue
                    listobj = self[tab + '_' + col]
                    if listobj.listtype == 'hierarchylist':
                        listobj.handleSelectionAdd(REQUEST, descr_dict, prefix)

        # hierarchylist remove
        elif button.startswith(BTN_HL_REMOVE):
            if len(button) != len(BTN_HL_REMOVE):
                tmpname = button[len(BTN_HL_REMOVE) + 1:]
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    listname = tmpname
                if not self.hasList(table, listname):
                    return
                listobj = self.getList(table, listname)
                if listobj.listtype == 'hierarchylist':
                    listobj.handleSelectionRemove(REQUEST, descr_dict, prefix)
            else:
                for (tab, col) in self.mapcol2list.keys():
                    if tab != table:
                        continue
                    listobj = self[tab + '_' + col]
                    if listobj.listtype == 'hierarchylist':
                        listobj.handleSelectionRemove(REQUEST, descr_dict, prefix)

        # singlelist filter
        elif button.startswith(BTN_L_FILTER):
            if len(button) != len(BTN_L_FILTER):
                tmpname = button[len(BTN_L_FILTER) + 1:]
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    listname = tmpname
                if not self.hasList(table, listname):
                    return
                listobj = self.getList(table, listname)
                if listobj.listtype in ['singlelist', 'multilist']:
                    listobj.handleFilterApply(REQUEST, descr_dict, prefix)
            else:
                for (tab, col) in self.mapcol2list.keys():
                    if tab != table:
                        continue
                    listobj = self[tab + '_' + col]
                    if listobj.listtype in ['singlelist', 'multilist']:
                        listobj.handleFilterApply(REQUEST, descr_dict, prefix)

        # multi/single range switch to next / prev
        elif button.startswith(BTN_FRL_PREV):
            if len(button) != len(BTN_FRL_PREV):
                tmpname = button[len(BTN_FRL_PREV) + 1:]
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    listname = tmpname
                if not self.hasList(table, listname):
                    return
                listobj = self.getList(table, listname)
                if listobj.listtype in ['singlelist', 'multilist']:
                    # last param is prev -> False
                    listobj.handleRangeSwitch(REQUEST, descr_dict, prefix, False)
            else:
                for (tab, col) in self.mapcol2list.keys():
                    if tab != table:
                        continue
                    listobj = self[tab + '_' + col]
                    if listobj.listtype in ['singlelist', 'multilist']:
                        # last param is prev -> False
                        listobj.handleRangeSwitch(REQUEST, descr_dict, prefix, False)

        elif button.startswith(BTN_FRL_NEXT):
            if len(button) != len(BTN_FRL_NEXT):
                tmpname = button[len(BTN_FRL_NEXT) + 1:]
                if prefix and tmpname.startswith(DLG_CUSTOM + prefix):
                    listname = tmpname[len(DLG_CUSTOM + prefix):]
                else:
                    listname = tmpname
                if not self.hasList(table, listname):
                    return
                listobj = self.getList(table, listname)
                if listobj.listtype in ['singlelist', 'multilist']:
                    listobj.handleRangeSwitch(REQUEST, descr_dict, prefix, True)
            else:
                for (tab, col) in self.mapcol2list.keys():
                    if tab != table:
                        continue
                    listobj = self[tab + '_' + col]
                    if listobj.listtype in ['singlelist', 'multilist']:
                        listobj.handleRangeSwitch(REQUEST, descr_dict, prefix, True)


    def manageOverview(self, REQUEST = None):
        """\brief Returns a overview manage tab."""

        dlg = getStdZMOMDialog('')
        dlg.setHeader( '<dtml-var manage_page_header><dtml-var manage_tabs>' )
        dlg.setFooter( '<dtml-var manage_page_footer>'                       )

        form = dlg.getForm()

        tab             = hgTable()
        tab._old_style  = False
        form.add(tab)

        r = 0

        tab[r, 1] = hgLabel( '<b>List Name</b>'  )
        tab[r, 2] = hgLabel( '<b>Label</b>' )
        tab[r, 3] = hgLabel( '<b>noedit</b>' )

        r += 1

        for listname in self.keys():
            list_obj = self[listname]

            assert isinstance(list_obj, List), 'Found obj is not of type List: %s (%s)' % (listname, type(list_obj))

            # provide a link to the list reference
            url = '%s/%s/manage_workspace' % (list_obj.absolute_url(), listname)
            lab_list = hgLabel(list_obj.listname, url)

            tab[r, 1] = lab_list
            tab[r, 2] = hgLabel(list_obj.getLabel())
            tab[r, 3] = hgLabel(list_obj.getNoEdit())

            r += 1

        return HTML( dlg.getHtml() )(self, REQUEST)


    def manageReferences(self, REQUEST = None):
        """\brief Returns a overview manage tab."""

        # get the manager parent of the listhandler
        manager = self.getManager()

        dlg = getStdZMOMDialog('')
        dlg.setHeader( '<dtml-var manage_page_header><dtml-var manage_tabs>' )
        dlg.setFooter( '<dtml-var manage_page_footer>'                       )

        form = dlg.getForm()

        tab             = hgTable()
        tab._old_style  = False
        form.add(tab)

        r = 0

        tab[r, 1] = hgLabel( '<b>Table</b>'  )
        tab[r, 2] = hgLabel( '<b>Column</b>' )
        tab[r, 3] = hgLabel( '<b>List Type</b>' )
        tab[r, 4] = hgLabel( '<b>Manager</b>' )
        tab[r, 5] = hgLabel( '<b>Reference Type</b>' )
        tab[r, 6] = hgLabel( '<b>Target</b>' )
        tab[r, 7] = hgLabel( '<b>List Object</b>' )

        r += 1

        references = self.mapcol2list.keys()
        references.sort()

        for (table, column) in references:
            table = str(table)
            list_obj = self[table + '_' + column]

            assert isinstance(list_obj, ForeignList), 'List object %s should be of type ForeignList, but got %s' % (table + '_' + column, type(list_obj))

            # provide a link to the list reference
            url = '%s/%s/manage_workspace' % (list_obj.absolute_url(), table + '_' + column)
            lab_list = hgLabel(list_obj.listname, url)

            # provide a link to the manager
            if hasattr(list_obj, 'manager'):
                list_mgr = manager.getHierarchyUpManager(list_obj.manager)

                if list_mgr:
                    lab = list_mgr.getId() + ' (' + list_mgr.getClassName() + ')'
                    url = '%s/manage_main' % list_mgr.absolute_url()

                    lab_mgr = hgLabel(lab, url)
                else:
                    # external mgr not present
                    lab_mgr = hgLabel('<font color="red">%s</font>' % list_obj.manager)
            else:
                list_mgr = manager
                lab = manager.getId() + ' (' + manager.getClassName() + ')'
                url = '%s/manage_main' % manager.absolute_url()

                lab_mgr = hgLabel(lab, url)

            # provide a link to the table
            if table == 'None':
                tobj = None
            else:
                tobj = manager.tableHandler[table]

            if tobj:
                url = '%s/%s/manage_workspace' % (tobj.absolute_url(), table)
                lab_table = hgLabel(table, url)
            else:
                lab_table = hgLabel('<font color="red">%s</font>' % table)

            # provide info about referenced object and a link to it
            if list_obj.function:
                target_type = 'Function'
                lab_target  = list_obj.function
            else:
                target_type = 'List or Table'

                if list_mgr:
                    if list_obj.foreign in list_mgr.tableHandler:
                        target_type = 'Table'

                        url = '%s/%s/manage_workspace' % (list_mgr.tableHandler[list_obj.foreign].absolute_url(), list_obj.foreign)
                        lab_target = hgLabel(list_obj.foreign, url)
                    elif list_obj.foreign in list_mgr.listHandler:
                        target_type = 'List'

                        url = '%s/%s/manage_workspace' % (list_mgr.listHandler[list_obj.foreign].absolute_url(), list_obj.foreign)
                        lab_target = hgLabel(list_obj.foreign, url)
                    else:
                        target_type = 'Missing'
                        lab_target = hgLabel('<font color="red">%s</font>' % list_obj.foreign)
                else:
                    lab_target = hgLabel('<font color="red">%s</font>' % list_obj.foreign)

            tab[r, 1] = lab_table
            tab[r, 2] = column
            tab[r, 3] = list_obj.listtype
            tab[r, 4] = lab_mgr
            tab[r, 5] = target_type
            tab[r, 6] = lab_target
            tab[r, 7] = lab_list

            r += 1

        return HTML( dlg.getHtml() )(self, REQUEST)


    def correctMySQLDB(self, do = False):
        """\brief mysql list tables have the show-column renamed to show1, which is not necessary anymore due to escaping. Rename the column."""
        mgr = self.getManager()
        pm = mgr.getManager(ZM_PM)
        done = 0
        for key in self.getListIDs():
            lobj = self[key]
            sql = 'ALTER TABLE %s%s CHANGE COLUMN `show1` `show` varchar(255)' % (self.getManager().getId(), lobj.listname)
            if do:
                pm.executeDBQuery(sql)
            done += 1
        return '%s Tabellen angepasst.' % done


    # TODO: FIXIT - adapt to new list objects / move to dialog!
    def moveListValues(self, REQUEST):
        """\brief Move values, adjust keys in main-content."""
        print 'ListHandler.moveListValues() broken. FIXME'

        return

        mgr = self.getParentNode()
        if 'step' not in REQUEST:
            step = 0
        else:
            step = int(REQUEST['step'])

        tab = hgTable()
        if step == 0:
            # choose lists to move from / to
            tab[0, 1] = dlgLabel('Choose lists of same type to move')
            tab.setCellSpanning(0, 1, 1, 3)
            tab[1, 1] = dlgLabel('from')
            tab[1, 3] = dlgLabel('to')
            row = 2
            for item in self.keys():

                if not self[item].manager:
                    tab[row, 1]  = hgRadioButton(item, name = 'from_list')
                    tab[row, 1] += self[item].getLabel()
                    tab[row, 3]  = hgRadioButton(item, name = 'to_list')
                    tab[row, 3] += self[item].getLabel()
                    row += 1
            tab[row, 1] = hgSPACE + hgProperty('step', str(step + 1))

        elif step == 1:

            # choose values, confirm tables
            from_list = REQUEST.get('from_list')
            to_list  = REQUEST.get('to_list')
            if not from_list or not to_list:
                errstr = 'Please choose a source and a destination.'
                err    = mgr.getErrorDialog(errstr)
                raise ValueError(err)
            from_obj = self[from_list]
            to_obj   = self[to_list]
            if from_obj.listtype != to_obj.listtype:
                errstr = 'Not implemented for different listtypes.'
                err    = mgr.getErrorDialog(errstr)
                raise ValueError(err)
            # get all managers (hierarchy up,
            # and their tables to check for occurence of from_list)
            mgrs = mgr.getAllManagers(objects = True)
            tabs = []
            for manager in mgrs:

                # only from matters
                if from_list in manager.listHandler:

                    # the manager has a table with that list
                    table = manager.listHandler[from_list].table
                    if not table:

                        for tabname in manager.tableHandler.keys():

                            if manager.tableHandler[tabname].getField(from_list):
                                table = tabname
                                break

                    tabs.append(manager.getClassName() + '___' + table)

            # put tables and from/to lists into tab
            tab[0, 0]  = dlgLabel('from')
            tab[0, 1]  = self[from_list].getLabel()
            tab[0, 1] += hgProperty('from_list', from_list)
            tab[1, 0]  = dlgLabel('to')
            tab[1, 1]  = self[to_list].getLabel()
            tab[1, 1] += hgProperty('to_list', to_list)
            tab[2, 0]  = dlgLabel('tables involved')
            tab[2, 1]  = hgLabel(string.join(tabs, '<br>'))
            props = []
            for entry in tabs:
                props.append(str(hgProperty('table', entry)))
            tab[2, 2] = string.join(props, ' ')
            # show multilist-selection for values of from_list (simple view)
            tab[3, 0] = dlgLabel('select values')
            entries = from_obj.getEntries()
            vals = []
            for entry in entries:
                vals.append([entry.get('autoid'), entry.get('value')])
            mul       = MultiList('dummy')
            widget    = mul.getSpecialWidget('values', m_list = vals)
            tab[3, 1] = widget

            # show move / copy - option
            tab[4, 0]  = hgRadioButton(name = 'action', value = 'move')
            tab[4, 0] += dlgLabel('move')
            tab[4, 1]  = hgRadioButton(name = 'action', value = 'copy')
            tab[4, 1] += dlgLabel('copy')

            tab[5, 0] = hgSPACE + hgProperty('step', str(step + 1))
            tab[6, 0] = mpfContinueButton

        elif step == 2:
            # get tables and lists from request
            values    = REQUEST.get('values')
            if not values:
                errstr = 'Please choose at least one value.'
                err    = mgr.getErrorDialog(errstr)
                raise ValueError(err)
            if not isinstance(values, ListType):
                values = [values]
            action   = REQUEST.get('action')
            if not action:
                raise ValueError(mgr.getErrorDialog('Please choose an action.'))
            from_list = REQUEST.get('from_list')
            to_list  = REQUEST.get('to_list')
            from_obj = self[from_list]
            to_obj   = self[to_list]
            tabs = REQUEST.get('table')
            if not isinstance(tabs, ListType):
                tabs = [tabs]
            # determine type
            listtype = from_obj.listtype
            mapping  = {}
            # copy values and create value-mapping
            for entry in values:
                newid = to_obj.addValue(from_obj.getValueByAutoid(entry))
                mapping[entry] = newid
            # copy or move keys
            # (update tab set [a = NULL, ]b = new where a = old)
            for entry in tabs:
                pos = entry.find('___')
                mgrname = entry[:pos]
                tabname = entry[pos + 3:]
                manager = mgr.getHierarchyUpManager(mgrname)
                field = manager.tableHandler[tabname].getField(to_list)
                if field:
                    mgr_to_obj = manager.listHandler[to_list]
                mgr_from_obj = manager.listHandler[from_list]
                for oldval in mapping:
                    if listtype == 'singlelist':
                        # if to_list belongs to table, we update the table
                        if field:
                            sql  = "update %s%s " % ( manager.id,
                                                      tabname )
                            sql += "set %s = %s " % ( to_list,
                                                      mapping[oldval] )
                            sql += "where %s = %s" % ( from_list,
                                                       oldval )
                            manager.getManager('ZopRAProduct').executeDBQuery(sql)
                        # move means: delete old entries (resp. their keys)
                        if action == 'move':
                            sql  = "update %s%s " % ( manager.id,
                                                      tabname )
                            sql += "set %s = NULL " % ( from_list )
                            sql += "where %s = %s"  % ( from_list,
                                                        oldval )
                            manager.getManager('ZopRAProduct').executeDBQuery(sql)
                    elif listtype == 'multilist':
                        # add new multilist-references
                        if field:
                            # other multitable, so we cant update
                            tabids = mgr_from_obj.getMLRef(None, oldval)
                            for entry in tabids:
                                notes = mgr_from_obj.getMLNotes(entry, oldval)
                                if not notes:
                                    notes = ''
                                if not mapping[oldval] in mgr_to_obj.getMLRef(entry):
                                    mgr_to_obj.addMLRef( entry,
                                                         mapping[oldval],
                                                         notes )
                        # if move -> delete old references
                        if action == 'move':
                            mgr_from_obj.delMLRef(None, oldval)
                    else:
                        errstr = 'Not implemented for hierarchy-lists.'
                        err    = mgr.getErrorDialog(errstr)
                        raise ValueError(err)

                # clear table cache for tables
                manager.tableHandler[tabname].cache.clearCache()
                # clear listcache (to_list / from_list)
                if field:
                    mgr_to_obj.emptyCache()
                mgr_from_obj.emptyCache()
                # clear cache before removing old values ... bad ... but works.
            if action == 'move':
                # delete old values
                for oldval in mapping:
                    from_obj.delValue(int(oldval))
            tab[0, 0] = dlgLabel('Done.')
            # show results
        else:
            raise ValueError('Navig Error.')
        dlg  = getStdDialog('Move List Values Step %s' % step, 'moveListValues')
        dlg.add(tab)
        return HTML( dlg.getHtml() )(self, REQUEST)
