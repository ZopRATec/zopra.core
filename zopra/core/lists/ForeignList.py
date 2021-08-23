"""Basic ZopRA list handling and list entry retrieval for lists connected to a table."""

from PyHtmlGUI.kernel.hgTable import hgTable
from PyHtmlGUI.widgets.hgLabel import hgLabel
from zopra.core import HTML
from zopra.core import ZC
from zopra.core.dialogs import getStdDialog
from zopra.core.lists.GenericList import GenericList
from zopra.core.types import IntType
from zopra.core.types import ListType
from zopra.core.types import StringType
from zopra.core.types import UnicodeType


# function prefixes for foreign funtions
F_VALUE = "Value"
F_SELECT = "Select"
F_LINK = "Link"

SUFFIXES = [F_VALUE, F_SELECT, F_LINK]


class ForeignList(GenericList):
    """A single selection list residing in the listHandler of a ZopRA Manager belonging to one table.
    It references a 'zopra.core.lists.List' basic list in the same manager (attribute 'foreign') to use the values from that list.
    It can reference its basic list in another manager (attribute 'manager'). The manager will always
    be looked up by class upwards in the hierarchy (thus only one can be found). If no manager was found, the
    hierarchy downwards is looked through, using the first found manager.
    """

    _className = "ForeignList"
    _classType = GenericList._classType + [_className]

    __notes = None
    __noteslabel = None
    __labelsearch = False
    __invisible = True

    listtype = "singlelist"

    manage_options = (
        {"label": "Overview", "action": "viewTab"},
    ) + GenericList.manage_options

    def __init__(self, listname, manager=None, function=None, label=None):
        """Constructs a ForeignList."""
        GenericList.__init__(self, listname, label)

        self.manager = manager
        self.__notes = None
        self.__noteslabel = None
        self.__labelsearch = False
        self.__invisible = True

        if not function:
            function = ""
        idx = function.find("(")
        if idx == -1:
            # points to a handwritten function
            self.function = function
            self.foreign = None
            self.cols = []
        else:
            # points to a table or a list in another manager
            self.function = None
            self.foreign = function[:idx]

            collist = function[idx + 1 : -1]
            cols = collist.split(",")
            if cols == [""]:
                cols = []

            self.cols = []
            for col in cols:
                self.cols.append(col.strip())

    # no extra database tables for foreign single lists
    def createTable(self):
        """Create the database table."""
        pass

    def deleteTable(self, omit_log=None):
        """Delete the database table."""
        pass

    # notes property methods
    def setNotes(self, notes):
        """Set notes property"""

        if notes:
            self.__notes = notes
        else:
            self.__notes = None

    def getNotes(self):
        """Get notes property"""

        return self.__notes

    notes = property(getNotes, setNotes)

    # noteslabel property methods
    def setNoteslabel(self, noteslabel):
        """Set noteslabel property"""

        if noteslabel:
            self.__noteslabel = noteslabel
        else:
            self.__noteslabel = None

    def getNoteslabel(self):
        """Get noteslabel property"""

        return self.__noteslabel

    noteslabel = property(getNoteslabel, setNoteslabel)

    # labelsearch property methods
    def setLabelSearch(self, labelsearch):
        """Set labelsearch property
        If set, getAutoidByValue will use searchLabelStrings from manager
        which performs a db search based on Value string.
        Also enables filtering for the list (legacy frontend).
        labelsearch is normally used to have a list with searchable values.
        This should speed up the data retrieval considerably compared
        to the standard method of retrieving all entries from db,
        creating their label string and comparing it to the pattern.
        Note: searchLabelStrings defaults to autoid search and must be overwritten in the
                manager, if different behaviour is desired.
        Note: Only a valid option if self.cols is not set since this changes the displayed
                value string and composed strings cannot be searched right now. -> needs to be solved
        """

        if labelsearch:
            self.__labelsearch = True
        else:
            self.__labelsearch = False

    def getLabelSearch(self):
        """Get labelsearch property"""

        return self.__labelsearch

    labelsearch = property(getLabelSearch, setLabelSearch)

    # invisible property methods
    def setInvisible(self, invisible):
        """Set invisible property"""
        if invisible:
            self.__invisible = True
        else:
            self.__invisible = False

    def getInvisible(self):
        """Get invisible property"""

        return self.__invisible

    invisible = property(getInvisible, setInvisible)

    def copy(self):
        """Create a copy of the list."""
        cop = self.__class__(self.listname, self.manager, self.function, self.label)

        cop.notes = self.notes
        cop.labelsearch = self.labelsearch

        return cop

    def getResponsibleManagerId(self):
        """Returns the foreign manager id (or manager id, if no foreign list)."""

        return self.getForeignManager().id

    def getForeignManager(self):
        """Returns the owning manager. If no manager could be found, return None. Callers have to check for that."""
        local = self.getManager()

        if local.getClassName() == self.manager:
            foreign = local
        else:
            # try same container first and then up the hierarchy
            foreign = local.getManager(self.manager) or local.getHierarchyUpManager(
                self.manager
            )
            # if that does not work, try down
            # CAUTION: down could be multiple managers of same type, first found gets returned
            # FIXME: should build in zopratype differentiation somehow
            if not foreign:
                foreign = local.getHierarchyDownManager(self.manager)

        return foreign

    def getLabel(self):
        """Returns the label of the list."""
        if self.label:
            label = self.label
            if self.notes and self.noteslabel:
                label = "%s (%s)" % (label, self.noteslabel)
            return label
        else:
            manager = self.getForeignManager()

            if manager:
                if self.foreign in manager.tableHandler:
                    return manager.tableHandler[self.foreign].getLabel()
                elif self.foreign in manager.listHandler:
                    return manager.listHandler[self.foreign].getLabel()

        return ""

    def isListReference(self):
        """True if the List refers to a list of a foreign manager"""
        return self.foreign in self.getForeignManager().listHandler

    def isTableReference(self):
        """True if the List refers to a table of a foreign manager"""
        return self.foreign in self.getForeignManager().tableHandler

    def isFunctionReference(self):
        """True if the List refers to a set of special functions in a foreign manager"""
        return not not self.function

    def getEntry(self, autoid):
        """Fetches a value from an list lookup table. Local function."""

        manager = self.getForeignManager()

        if not manager:
            return

        autoid = int(autoid)

        # if plain function implemented in manager then return the call result
        if self.function:
            return getattr(manager, self.function + F_VALUE)(autoid)

        # handle foreign table or list
        if self.foreign in manager.tableHandler:
            return manager.tableHandler[self.foreign].getEntry(autoid)

        if self.foreign in manager.listHandler:
            return manager.listHandler[self.foreign].getEntry(autoid)

        raise ValueError("Couldn't find foreign list.")

    def getEntries(self, value=None, with_hidden=False, manager=None, lang=None):
        """Returns all list entries of one list."""
        completelist = []

        if not manager:
            manager = self.getForeignManager()

        if manager:

            # plain function, implemented in manager
            if self.function:
                funcstr = self.function + F_SELECT

                # test
                if not hasattr(manager, funcstr):
                    errstr = "%s missing function: %s" % (manager.id, funcstr)
                    raise ValueError(errstr)

                selfunc = getattr(manager, funcstr)
                reslist = selfunc(lang)

                for result in reslist:
                    if value is None or value in result[1]:
                        # this is not multilingual, target functions neet to supply correct language
                        newentry = {
                            ZC.TCN_AUTOID: result[0],
                            ZC.VALUE: result[1],
                            ZC.SHOW: "yes",
                        }
                        completelist.append(newentry)
            else:
                # table-standard-function used
                if self.foreign in manager.tableHandler:
                    tobj = manager.tableHandler[self.foreign]
                    cons = self.getManager().getListSelectionConstraints(self.listname)
                    tentries = tobj.getEntryList(constraints=cons)
                    completelist = []
                    for entry in tentries:
                        val = ""
                        autoid = entry["autoid"]
                        if not self.cols:
                            # empty, use getLabelString
                            val = manager.getLabelString(
                                self.foreign, None, entry, lang
                            )
                        else:
                            vals = []
                            # switch to translated entry if necessary
                            if manager.doesTranslations(self.foreign):
                                entry = manager.getEntry(self.foreign, autoid, lang)
                            for col in self.cols:
                                col = col.strip()
                                if entry.get(col):
                                    vals.append(unicode(entry.get(col)))
                            val = " ".join(vals)

                        if value is None or value in val:
                            newentry = {
                                ZC.TCN_AUTOID: autoid,
                                ZC.VALUE: val,
                                ZC.SHOW: "yes",
                            }
                            completelist.append(newentry)
                # get data from list
                elif self.foreign in manager.listHandler:
                    lobj = manager.listHandler[self.foreign]
                    # call getEntries of the ZMOMLIst object that is referenced (lang is not necessary, the entries are multilingual anyway)
                    completelist = lobj.getEntries(value, with_hidden)
                else:
                    raise ValueError(
                        "Couldn't find foreign list %s:%s for %s"
                        % (manager.getClassName(), self.foreign, self.listname)
                    )
        else:
            # manager not found
            return []

        return completelist

    def getAutoidByValue(self, value, rank=None):
        """Returns the autoid from an specified list entry."""
        assert (
            isinstance(value, StringType)
            or isinstance(value, ListType)
            or isinstance(value, UnicodeType)
            or value is None
        )

        # NOTE: do not handle lists recursivly:
        #      1) getting the manager is expensive
        #      2) loading all entries of a list from the db for each searched value is wasteful
        if isinstance(value, ListType):
            is_list = True
            values = value
        else:
            is_list = False
            values = [value]

        retlist = []

        manager = self.getForeignManager()

        # foreign manager is not available
        if not manager:
            retlist = len(values) * [None]
        # if it is a real list forward to it
        elif self.foreign in manager.listHandler:
            lobj = manager.listHandler[self.foreign]

            return lobj.getAutoidByValue(value, rank)

        # retrieve data via function
        elif self.function:
            # function or table
            entrylist = self.getEntries(with_hidden=True, manager=manager)

            # NOTE: keep in mind to preserve the order of searched values,
            #       as well as multiple occurences of values

            # build lookup table
            # NOTE: a list should consist of distinct values
            #       so if multiple occurences of the same value occur the autoid which is actually mapped is undefined
            #       in this case the last of the same values in the entrylist wins
            val2autoid = {}

            for entry in entrylist:
                val2autoid[entry[ZC.VALUE]] = entry[ZC.TCN_AUTOID]

            # get the autoid for each value
            for val in values:
                retlist.append(val2autoid.get(val, None))

        # retrieve data via table
        elif self.foreign in manager.tableHandler:

            if self.labelsearch:
                # Note: expensive if values contains a high number of entries
                for val in values:
                    (ids, count) = manager.searchLabelStrings(self.foreign, val)
                    # count should be 0 or 1
                    # print str((ids, count))
                    if count:
                        retlist.append(ids[0])
                    else:
                        retlist.append(None)
            else:
                # Note: this is horribly expensive for big tables, use label search if possible
                entrylist = self.getEntries(with_hidden=True, manager=manager)

                # NOTE: look at note of function section above
                val2autoid = {}

                for entry in entrylist:
                    val2autoid[entry[ZC.VALUE]] = entry[ZC.TCN_AUTOID]

                # get the autoid for each value
                for val in values:
                    retlist.append(val2autoid.get(val, None))

        # manager is available but list cannot be found - error
        else:
            raise ValueError("Couldn't find foreign list.")

        return retlist if is_list else retlist[0]

    # freetextsearch
    def getAutoidsByFreeText(self, value):
        """Returns the autoid from any fitting list entry."""
        reslist = []
        upval = value.upper()

        manager = self.getForeignManager()

        if manager:
            if self.function or self.foreign in manager.tableHandler:
                # function or table
                resultlist = self.getEntries(with_hidden=True, manager=manager)
                for entry in resultlist:
                    if entry[1].upper().find(upval) != -1:
                        reslist.append(entry[0])

            else:
                # foreign list
                if self.foreign in manager.listHandler:
                    lobj = manager.listHandler[self.foreign]
                    reslist = lobj.getAutoidsByFreeText(value)
                else:
                    raise ValueError("Couldn't find foreign list.")

        return reslist

    def crossLookupList(self, entry1, entry2, crossString):
        """gets the values for the entries calls crossValue and
                  inserts the result into the list.

        Returns the new or existing id.
        """
        if self.function:
            raise ValueError("Cannot cross foreign function-based lists.")

        manager = self.getForeignManager()

        if manager:
            # handle foreign table or list
            if self.foreign in manager.tableHandler:
                raise ValueError("Cannot cross foreign table-based lists.")
            elif self.foreign in manager.listHandler:
                return manager.listHandler[self.foreign].crossLookupList(
                    entry1, entry2, crossString
                )
            else:
                raise ValueError("Couldn't find foreign list.")

    def getValueCount(self):
        """Returns the number of entries in this list.

        :return: The number of entries.
        """
        manager = self.getForeignManager()

        if not manager:
            return 0

        if self.function:

            # NOTE: expensive, but the only way
            return len(self.getEntries(manager=manager))
        else:

            # handle foreign table or list
            if self.foreign in manager.tableHandler:
                cons = self.getManager().getListSelectionConstraints(self.listname)
                return manager.tableHandler[self.foreign].getEntryListCount(cons)
            elif self.foreign in manager.listHandler:
                return manager.listHandler[self.foreign].getValueCount()

        raise ValueError("Couldn't find foreign list.")

    def getValueByAutoid(self, autoid, lang=None):
        """Returns the value from an specified list entry/entries."""
        # additional check for None to avoid fetching foreign manager etc.
        if autoid is None:
            return ""

        # NOTE: do not handle lists recursivly since getting the
        #       manager is expensive
        if isinstance(autoid, ListType):
            is_list = True
            autoids = autoid
        else:
            is_list = False
            autoids = [autoid]

        retlist = []

        manager = self.getForeignManager()

        if not manager:
            # manager not found -> ignore and return empty values
            value = ["" for aid in autoids]
            if is_list:
                return value
            else:
                return value[0]
        for aid in autoids:
            value = ""
            # not existing values
            if aid is None or aid == "":
                value = None
            # no value
            elif aid == "NULL":
                pass
            elif aid == "_not_NULL":
                # TODO: use translation (Plone 4)
                if lang == "de":
                    value = "beliebig"
                else:
                    value = "any"
            elif manager:
                assert isinstance(aid, IntType) or isinstance(
                    aid, StringType
                ), ZC.E_PARAM_TYPE % ("aid", "IntType/StringType", aid)

                aid = int(aid)

                if self.function:
                    funcstr = self.function + F_VALUE
                    assert hasattr(manager, funcstr)
                    valfunc = getattr(manager, funcstr)
                    value = valfunc(aid, lang)
                else:
                    # collist given, table-standard-function used
                    if self.foreign in manager.tableHandler:
                        tobj = manager.tableHandler[self.foreign]
                        value = tobj.getEntryValue(aid, self.cols, lang)
                    elif self.foreign in manager.listHandler:
                        lobj = manager.listHandler[self.foreign]
                        value = lobj.getValueByAutoid(aid, lang)
                    else:
                        raise ValueError(
                            "Couldn't find foreign list '%s'." % self.foreign
                        )

            retlist.append(value)

        if is_list:
            return retlist
        else:
            return retlist[0]

    ##########################################################################
    #
    # Manage Tab Methods
    #
    ##########################################################################
    def viewTab(self, REQUEST):
        """List overview tab."""
        dlg = self.getViewTabDialog(REQUEST)
        return HTML(dlg.getHtml())(self, REQUEST)

    def getViewTabDialog(self, REQUEST):
        """view tab dialog creation is extra for overwriting and extending the dialog in multilist"""
        dlg = getStdDialog("", "viewTab")
        dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
        dlg.setFooter("<dtml-var manage_page_footer>")

        tab = hgTable()
        tab._old_style = False

        # show tables information
        tab[0, 0] = "<h3>List Overview</h3>"
        tab.setCellSpanning(0, 0, colspan=3)

        tab[1, 0] = "<b>Name</b>"
        tab[1, 1] = "<b>Type</b>"
        tab[1, 2] = "<b>Label</b>"
        tab[1, 4] = "<b>Manager</b>"
        tab[1, 5] = "<b>Reference Type</b>"
        tab[1, 6] = "<b>Target</b>"
        tab[1, 7] = "<b>Columns</b>"
        tab[1, 8] = "<b>Notes</b>"
        tab[1, 9] = "<b>Invisible</b>"

        list_mgr = self.getForeignManager()

        if list_mgr:
            lab = list_mgr.getId() + " (" + list_mgr.getClassName() + ")"
            url = "%s/manage_main" % list_mgr.absolute_url()

            lab_mgr = hgLabel(lab, url)
        else:
            # external mgr not present
            lab_mgr = hgLabel('<span style="color:red;">%s</span>' % self.manager)

        tab[2, 0] = self.listname
        tab[2, 1] = self.listtype
        tab[2, 2] = self.label.encode("utf8")
        tab[2, 4] = lab_mgr

        if self.function:
            target_type = "Function"
            lab_target = self.function
        else:
            target_type = "List or Table"

            if list_mgr:
                if self.foreign in list_mgr.tableHandler:
                    target_type = "Table"

                    url = "%s/%s/manage_workspace" % (
                        list_mgr.tableHandler[self.foreign].absolute_url(),
                        self.foreign,
                    )
                    lab_target = hgLabel(self.foreign, url)
                    if self.cols:
                        tab[2, 7] = str(self.cols)
                elif self.foreign in list_mgr.listHandler:
                    target_type = "List"

                    url = "%s/%s/manage_workspace" % (
                        list_mgr.listHandler[self.foreign].absolute_url(),
                        self.foreign,
                    )
                    lab_target = hgLabel(self.foreign, url)
                else:
                    target_type = "Missing"
                    lab_target = hgLabel(
                        '<span style="color:red;">%s</span>' % self.foreign
                    )
            else:
                lab_target = hgLabel(
                    '<span style="color:red;">%s</span>' % self.foreign
                )

        tab[2, 5] = target_type
        tab[2, 6] = lab_target

        if isinstance(self.notes, StringType):
            tab[2, 8] = self.notes
        else:
            tab[2, 8] = (self.notes and "yes") or "no"
        tab[2, 9] = (self.invisible and "yes") or "no"

        dlg.add(tab)
        return dlg
