from __future__ import print_function

from PyHtmlGUI.kernel.hgTable import hgTable
from PyHtmlGUI.widgets.hgLabel import hgLabel
from zopra.core import HTML
from zopra.core import ZC
from zopra.core import ZM_PM
from zopra.core import ZM_SCM
from zopra.core import Folder
from zopra.core.dialogs.Dialog import Dialog
from zopra.core.lists.ForeignList import ForeignList
from zopra.core.lists.HierarchyList import HierarchyList
from zopra.core.lists.List import List
from zopra.core.lists.MultiList import MultiList
from zopra.core.types import ListType
from zopra.core.utils import getASTFromXML
from zopra.core.utils import getParentManager


class ListHandler(Folder):
    """List Handler"""

    _className = "ListHandler"
    _classType = [_className]

    manage_options = (
        {"label": "List Objects", "action": "manageOverview"},
        {"label": "List References", "action": "manageReferences"},
    ) + Folder.manage_options

    def __init__(self):
        """Constructs a ListHandler."""
        Folder.__init__(self, "listHandler")

        self.mapcol2list = {}
        self.maptable2lists = {}  # maptable2lists[table][listtype] -> [ lists ]

    def xmlInit(self, xml, nocreate=False):
        """Create list definition objects (List) and
        list access objects (Foreign, Multi and HierarchyList)"""

        tmp_obj = getASTFromXML(xml)

        # setup lists (given as <List> in the xml file)
        for list_idx in tmp_obj.list:
            list_ = tmp_obj.list[list_idx]
            list_name = list_.getName().encode("utf-8")
            label = list_.getLabel()
            translations = list_.getTranslations()
            translist = []
            if translations:
                transtmp = translations.encode("utf-8").split(",")
                for trans in transtmp:
                    trans = trans.strip()
                    if trans not in translist:
                        translist.append(trans)

            # create list objects
            lobj = self.addList(list_name, label, nocreate, translist)

            # noedit affects the appearance of the column in the
            # listedit-section of _index_html
            if list_.getNoedit():
                lobj.noedit = True

        # get the manager parent of the list handler
        manager = self.getManager()

        # connect columns to lists
        for table_idx in tmp_obj.table:
            table = tmp_obj.table[table_idx]
            table_name = table.getName().encode("utf-8")

            # iterate over columns
            for column_idx in table.column:
                column = table.column[column_idx]
                column_type = column.getType().encode("utf-8")

                if column_type in ZC.ZCOL_LISTS:
                    lobj = self.connectList(manager, table_name, column, nocreate)

                    if not lobj:
                        column_name = column.getName().encode("utf-8")
                        raise ValueError(
                            "Cannot create list for column '%s' in table '%s'"
                            % (column_name, table_name)
                        )

                    if column.getNotes():
                        notes = column.getNotes().encode("utf-8")
                        if notes == "1":
                            notes = True
                        elif notes == "0" or not notes:
                            notes = False
                        lobj.notes = notes

                    if column.getNoteslabel():
                        lobj.noteslabel = column.getNoteslabel()

                    if column.getLabelsearch():
                        lobj.labelsearch = True

                    # FIXME: check if this is necessary, only cols should be invisible, not the foreign lists
                    if column.getInvisible():
                        lobj.invisible = True
        if not nocreate:
            self.addListTableIndexes()

    def addListTableIndexes(self):
        """add DB indexes for list tables and multi tables"""
        # TODO: move SQL to Connector / Product
        manager = self.getManager()
        pm = manager.getManager(ZC.ZM_PM)

        def mapname(lobj, mgr):
            if lobj.map:
                dbname = "%smulti%s" % (mgr.getId(), lobj.map)
            else:
                dbname = "%smulti%s%s" % (mgr.getId(), lobj.table, lobj.listname)
            return dbname

        counter1 = 0
        counter2 = 0
        # create index for multilists / hierarchylists on multi-table
        for table in manager.tableHandler.keys():
            for lobj in manager.listHandler.getLists(
                table, ["multilist", "hierarchylist"]
            ):
                try:
                    # add index to multitable for tableid
                    name = mapname(lobj, manager)
                    sql = "ALTER TABLE %s ADD INDEX idxmulti1_%s (tableid)" % (
                        name,
                        lobj.listname,
                    )
                    pm.executeDBQuery(sql)
                except Exception as ex:
                    if str(ex).find("Duplicate key name") != -1:
                        pass
                    else:
                        raise
                try:
                    # add index to multitable for listname column
                    sql = "ALTER TABLE %s ADD INDEX idxmulti2_%s (%s)" % (
                        name,
                        lobj.listname,
                        lobj.listname,
                    )
                    pm.executeDBQuery(sql)
                except Exception as ex:
                    if str(ex).find("Duplicate key name") != -1:
                        pass
                    else:
                        raise
                counter1 += 1
        # create indexes for all list tables
        for onelist in manager.listHandler.keys():
            lobj = manager.listHandler[onelist]
            try:
                # add index to listtable for value column
                sql = "ALTER TABLE %s%s ADD INDEX idx_%s (value)" % (
                    manager.id,
                    lobj.listname,
                    lobj.listname,
                )
                pm.executeDBQuery(sql)

            except Exception as ex:
                if str(ex).find("Duplicate key name") != -1:
                    pass
                else:
                    raise
            counter2 += 1

    def getManager(self):
        """This method returns the owning manager.

        :returns: the parent manager of the list
        """
        return getParentManager(self)

    def __getitem__(self, key):
        """the itemgetter (use via listHandler[<listname>]) only returns List objects"""
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
        """Returns all names of basic List objects"""
        keylist = []
        for item in dir(self):
            if hasattr(self, str(item)):
                attr = getattr(self, item)
                # just take genuine db lists
                if hasattr(attr, "getClassType") and "List" in attr.getClassType():
                    keylist.append(item)
        return keylist

    def getListIDs(self):
        """This method returns all the IDs for the handled table.

        :return: list of Zope IDs
        """
        return self.objectIds(List.meta_type)

    def addList(self, listname, label=None, nocreate=False, translations=None):
        """Adds an list lookup table.

        :param list_name: the name of the new list without the manager id prefix."""
        if listname in self:
            return self.get(listname)

        if not translations:
            translations = []

        lobj = List(listname, label, nocreate, translations)
        self._setObject(listname, lobj)

        lobj_withmgr = self[listname]
        if not nocreate:
            lobj_withmgr.createTable()

        return lobj_withmgr

    def connectList(self, local_manager, table, column, nocreate=False):
        """Connects a table column to a list."""

        # get the parameters
        listname = column.getName().encode("utf-8")
        listtype = column.getType().encode("utf-8")

        manager = function = label = map_ = None
        invisible = False

        if column.getManager():
            manager = column.getManager().encode("utf-8")
        else:
            manager = local_manager.getClassName()
        if column.getFunction():
            function = column.getFunction().encode("utf-8")
        else:
            function = listname + "()"
        if column.getMap():
            map_ = column.getMap().encode("utf-8")
        if column.getLabel():
            label = column.getLabel()

        if str(column.getInvisible()).upper() in ["1", "T", "TRUE", "Y", "YES"]:
            invisible = True

        # create the list reference
        lobj = None

        if listtype == "singlelist":
            # use the original list if possible
            lobj = ForeignList(listname, manager, function, label)
        elif listtype == "multilist":
            lobj = MultiList(listname, manager, function, table, label, map_)
        elif listtype == "hierarchylist":
            lobj = HierarchyList(listname, manager, function, table, label, map_)
        else:
            raise ValueError("listtype contains invalid type %s" % listtype)

        lobj.invisible = invisible

        # insert list into the listhandler
        self._setObject(str(table) + "_" + listname, lobj)

        # get wrapped list object
        lobj_withmgr = self[str(table) + "_" + listname]

        # operate on wrapped object
        if listtype in ["multilist", "hierarchylist"]:
            lobj_withmgr.initDBName()

        if not nocreate:
            lobj_withmgr.createTable()

        self.mapcol2list[(table, listname)] = listname

        # aux var to simplify access to lists
        if table not in self.maptable2lists:
            self.maptable2lists[table] = {}
            self.maptable2lists[table]["singlelist"] = []
            self.maptable2lists[table]["multilist"] = []
            self.maptable2lists[table]["hierarchylist"] = []

        self.maptable2lists[table][listtype].append(listname)

        return lobj_withmgr

    def delList(self, listname, dboperate=False):
        """Deletes a list lookup table. Returns True if the list was found and deleted.

        :param list_name: the name of the list which will be deleted."""

        if listname not in self:
            return False

        lobj = self[listname]

        if dboperate:
            lobj.deleteTable(omit_log=[ZM_SCM, ZM_PM])

        self._delObject(listname)
        return True

    def disconnectList(self, table, column, dboperate=False):
        """Deletes a list reference object"""

        if (table, column) not in self.mapcol2list:
            return False

        lobj = self[str(table) + "_" + column]

        if not lobj:
            return

        if dboperate:
            lobj.deleteTable(omit_log=[ZM_SCM, ZM_PM])

        del self.mapcol2list[(table, column)]
        self.maptable2lists[table][lobj.listtype].remove(lobj.listname)

        self._delObject(str(table) + "_" + column)

        return True

    def getList(self, table, column):
        """Get access list for column in table"""
        try:
            return self[
                "%s_%s" % (table, column)
            ]  # self.mapcol2list.get( (table, column), None )
        except Exception:
            msg = "No list found for column [%s] in table [%s]" % (column, table)
            raise ValueError(msg)

    def hasList(self, table, column):
        """check access list for column in table"""
        return (table, column) in self.mapcol2list

    def getLists(self, table, types=ZC.ZCOL_LISTS, include=True):
        """Get all lists of a table that match"""
        if table not in self.maptable2lists:
            return []

        lists = []
        types = types if isinstance(types, ListType) else [types]

        for listtype in ZC.ZCOL_LISTS:

            process = bool(listtype in types)

            if not include:
                process = not process

            if process:
                for listname in self.maptable2lists[table][listtype]:
                    lists.append(self[str(table) + "_" + listname])

        return lists

    def getReferences(self):
        """returns all (table,column)-tuples that reference access lists."""
        return self.mapcol2list.keys()

    def emptyListCache(self, listname=None):
        """Empties all cached objects from list handling."""
        listnames = []
        if listname:
            listnames = [listname]
        else:
            listnames = self.keys()

        for entry in listnames:
            self[entry].clearCache()

    def checkEmptyEditList(self, table, edit_dict, descr_dict):
        """checks wether a list has been edited to emtpy and changes the descr_dict."""
        #
        # \BUG: edit_dict needs at least one other entry for empty lists
        # to be recognized
        # \FIXME: edit_dict has to be empty on first call of function.
        if not edit_dict:
            return
        for (tab, col) in self.mapcol2list:
            if tab != table or col not in descr_dict:
                continue

            lobj = self[tab + "_" + col]
            if lobj.listtype in ["multilist", "hierarchylist"] and col not in edit_dict:

                descr_dict[col] = []
        return

    def manageOverview(self, REQUEST=None):
        """Returns a overview manage tab."""

        dlg = Dialog(name=None, flags=0)
        dlg.caption = ""
        dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
        dlg.setFooter("<dtml-var manage_page_footer>")

        form = dlg.getForm()

        tab = hgTable()
        tab._old_style = False
        form.add(tab)

        r = 0

        tab[r, 1] = hgLabel("<b>List Name</b>")
        tab[r, 2] = hgLabel("<b>Label</b>")
        tab[r, 3] = hgLabel("<b>noedit</b>")

        r += 1

        for listname in self.keys():
            list_obj = self[listname]

            # assert isinstance(list_obj, List), 'Found obj is not of type List: %s (%s)' % (listname, type(list_obj))

            # provide a link to the list reference
            url = "%s/%s/manage_workspace" % (list_obj.absolute_url(), listname)
            lab_list = hgLabel(list_obj.listname, url)

            tab[r, 1] = lab_list
            tab[r, 2] = hgLabel(list_obj.getLabel().encode("utf8"))
            tab[r, 3] = hgLabel(list_obj.getNoEdit())

            r += 1

        return HTML(dlg.getHtml())(self, REQUEST)

    def manageReferences(self, REQUEST=None):
        """Returns a references manage tab."""

        # get the manager parent of the listhandler
        manager = self.getManager()

        dlg = Dialog(name=None, flags=0)
        dlg.caption = ""
        dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
        dlg.setFooter("<dtml-var manage_page_footer>")

        form = dlg.getForm()

        tab = hgTable()
        tab._old_style = False
        form.add(tab)

        r = 0

        tab[r, 1] = hgLabel("<b>Table</b>")
        tab[r, 2] = hgLabel("<b>Column</b>")
        tab[r, 3] = hgLabel("<b>List Type</b>")
        tab[r, 4] = hgLabel("<b>Manager</b>")
        tab[r, 5] = hgLabel("<b>Reference Type</b>")
        tab[r, 6] = hgLabel("<b>Target</b>")
        tab[r, 7] = hgLabel("<b>List Object</b>")

        r += 1

        references = self.getReferences()
        references.sort()

        for (table, column) in references:
            table = str(table)
            list_obj = self[table + "_" + column]

            assert isinstance(
                list_obj, ForeignList
            ), "List object %s should be of type ForeignList, but got %s" % (
                table + "_" + column,
                type(list_obj),
            )

            # provide a link to the list reference
            url = "%s/%s/manage_workspace" % (
                list_obj.absolute_url(),
                table + "_" + column,
            )
            lab_list = hgLabel(list_obj.listname, url)

            # provide a link to the manager
            if hasattr(list_obj, "manager"):
                list_mgr = manager.getHierarchyUpManager(list_obj.manager)

                if list_mgr:
                    lab = list_mgr.getId() + " (" + list_mgr.getClassName() + ")"
                    url = "%s/manage_main" % list_mgr.absolute_url()

                    lab_mgr = hgLabel(lab, url)
                else:
                    # external mgr not present
                    lab_mgr = hgLabel('<font color="red">%s</font>' % list_obj.manager)
            else:
                list_mgr = manager
                lab = manager.getId() + " (" + manager.getClassName() + ")"
                url = "%s/manage_main" % manager.absolute_url()

                lab_mgr = hgLabel(lab, url)

            # provide a link to the table
            if table == "None":
                tobj = None
            else:
                tobj = manager.tableHandler[table]

            if tobj:
                url = "%s/%s/manage_workspace" % (tobj.absolute_url(), table)
                lab_table = hgLabel(table, url)
            else:
                lab_table = hgLabel('<font color="red">%s</font>' % table)

            # provide info about referenced object and a link to it
            if list_obj.function:
                target_type = "Function"
                lab_target = list_obj.function
            else:
                target_type = "List or Table"

                if list_mgr:
                    if list_obj.foreign in list_mgr.tableHandler:
                        target_type = "Table"

                        url = "%s/%s/manage_workspace" % (
                            list_mgr.tableHandler[list_obj.foreign].absolute_url(),
                            list_obj.foreign,
                        )
                        lab_target = hgLabel(list_obj.foreign, url)
                    elif list_obj.foreign in list_mgr.listHandler:
                        target_type = "List"

                        url = "%s/%s/manage_workspace" % (
                            list_mgr.listHandler[list_obj.foreign].absolute_url(),
                            list_obj.foreign,
                        )
                        lab_target = hgLabel(list_obj.foreign, url)
                    else:
                        target_type = "Missing"
                        lab_target = hgLabel(
                            '<font color="red">%s</font>' % list_obj.foreign
                        )
                else:
                    lab_target = hgLabel(
                        '<font color="red">%s</font>' % list_obj.foreign
                    )

            tab[r, 1] = lab_table
            tab[r, 2] = column
            tab[r, 3] = list_obj.listtype
            tab[r, 4] = lab_mgr
            tab[r, 5] = target_type
            tab[r, 6] = lab_target
            tab[r, 7] = lab_list

            r += 1

        return HTML(dlg.getHtml())(self, REQUEST)
