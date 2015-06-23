############################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from copy   import copy
from types  import ListType
#
# PyHtmlGUI Imports
#

from PyHtmlGUI.widgets.hgLabel              import hgLabel
from PyHtmlGUI.widgets.hgComboBox           import hgComboBox
from PyHtmlGUI.widgets.hgPushButton         import hgPushButton
from PyHtmlGUI.kernel.hgGridLayout          import hgGridLayout
from PyHtmlGUI.kernel.hgWidget              import hgWidget
from PyHtmlGUI.widgets.hgCheckBox           import hgCheckBox
from PyHtmlGUI                              import hg

from zopra.core                             import ZM_SCM
from zopra.core.constants                   import TCN_CREATOR, TCN_AUTOID
from zopra.core.CorePart                    import COL_LABEL,      \
                                                   MASK_SHOW
from zopra.core.dialogs.dlgOCBase           import dlgOCBase
from zopra.core.elements.Styles.Default     import ssiPHEN_TAB, ssiPHEN_TAB_TD

ENTRY_EDIT  = 'dlgMul_Edit'
ENTRY_LABEL = 'dlgMul_Label'


class dlgTreeEdit(dlgOCBase):
    """\brief Multi Entry - Hierarchy List Edit Dialog"""
    _className = "dlgTreeEdit"
    _classType = dlgOCBase._classType + [_className]

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a dlgMultiEdit Object."""
        # Careful with attributes, super.__init__ calls
        # buildLayout and buildFinalLayout
        # test for generic manager
        if 'GenericManager' not in manager.getClassType():
            errstr = 'Internal Error: Not available for non-generic managers'
            raise ValueError(manager.getErrorDialog(errstr))
        self.entries = {}
        self.restore = {}
        self.table   = param_dict.get('table')
        self.attrib  = param_dict.get('attribute')
        self.level   = param_dict.get('level', 0)
        autoids = param_dict.get('autoid')
        self.initAttribs(manager)
        self.initEntries(manager, autoids)
        self.do_reset = False
        self.suppress_reset = False

        dlgOCBase.__init__(self, manager, param_dict)

        self.caption     = self.attrLabel + ' Multi Edit'
        self.enable_undo = False

        # remove everything from param_dict
        del param_dict['table']
        del param_dict['attribute']
        if param_dict.has_key('level'):
            del param_dict['level']
        if param_dict.has_key('autoid'):
            del param_dict['autoid']


    def initTargetUrl(self, manager, REQUEST, exclude = []):
        """\brief used to set the target to jump to when dialog is finished.
                Tries to get all params from the REQUEST for search result page."""
        # build base url
        url = '%s/showList?' % manager.absolute_url()
        # add params from request
        for key in REQUEST.form.keys():
            # do not add the multiedit-button
            if key in exclude:
                continue
            value = REQUEST.form[key]
            if isinstance(value, ListType):
                for oneval in value:
                    url += '%s=%s&' % (key, oneval)
            else:
                url += '%s=%s&' % (key, value)
            
        self.setTargetUrl(url)


    def initEntries(self, manager, autoids):
        """\brief Init entries and their widgets."""
        m_security = manager.getHierarchyUpManager(ZM_SCM)
        if not self.table:
            errstr = 'Internal Error: Tableattribute missing.'
            raise ValueError(manager.getErrorDialog(errstr))
        tab = manager.tableHandler[self.table]
        if not tab:
            errstr = 'Internal Error: Table not found.'
            raise ValueError(manager.getErrorDialog(errstr))
        if not autoids:
            errstr = 'No Entries found for editing.'
            raise ValueError(manager.getErrorDialog(errstr))

        # set attrib label
        self.attrLabel   = tab.getField(self.attrib)[COL_LABEL]

        # check edit rights
        if not m_security or m_security.getCurrentLevel() > 8 or \
           m_security.hasRole(manager.getZopraType() + 'Superuser'):
            do_edit = True
        else:
            do_edit = False

        if m_security:
            ownId = m_security.getCurrentCMId()
            # ebase check
            if manager.checkEBaSe(self.table):
                ebase  = True
                groups = m_security.getCurrentEBaSeGroups()
            else:
                ebase = False
        else:
            # doesn't matter because do_edit is True then, but for code style
            ownId = -1
            ebase = False

        # count editable entries
        num_edit = 0

        # autoids can be single id or list, doesn't matter for getEntries
        entries = tab.getEntries(autoids)
        for entry in entries:
            # copy entry
            cop    = copy(entry)
            cop2   = copy(entry)
            autoid = cop[TCN_AUTOID]

            # check edit rights for entry
            creator = entry.get(TCN_CREATOR, -1)
            # ebase check
            if ebase:
                ebase_edit = m_security.matchEBaSe(entry, 'edit', self.table, groups)
            else:
                ebase_edit = False
            if do_edit or str(creator) == str(ownId) or ebase_edit:
                # we have edit-rights
                cop[ENTRY_EDIT]  = True
                cop2[ENTRY_EDIT] = True
                num_edit += 1
                # restore info for editable entries
                self.restore[autoid] = cop2
            label  = manager.getLabelString(self.table, None, cop)
            cop[ENTRY_LABEL]  = label
            cop2[ENTRY_LABEL] = label
            # store
            self.entries[autoid] = cop

        # test number of editable entries
        if num_edit == 0:
            errstr = 'No editable entries found.'
            raise ValueError(manager.getErrorDialog(errstr))


    def initAttribs(self, manager):
        """\brief Test attributes and user rights."""
        if not self.attrib:
            errstr = 'Internal Error: No attributes selected.'
            raise ValueError(manager.getErrorDialog(errstr))

        lobj = manager.listHandler.getList(self.table, self.attrib)

        if not lobj or lobj.listtype != 'hierarchylist':
            errstr = 'Attribute is no HierarchyList'
            raise ValueError(manager.getErrorDialog(errstr))

        # get entrylist
        entries = lobj.getEntries()

        # build list tree and leaf-list
        # dict-tree containing labels only
        self.tree       = {}
        self.treeLabels = {}
        for entry in entries:
            par    = int(entry.get('rank', 0))
            autoid = entry.get(TCN_AUTOID)
            if not self.tree.has_key(par):
                self.tree[par] = []
            self.tree[par].append(autoid)
            self.treeLabels[autoid] = entry.get('value')


    def buildHeader(self, level, widget, row, col):
        """\brief Initialise the table header"""
        if row > self.maxRow:
            self.maxRow = row
        layout = widget.layout()
        sumLen = 0
        if not self.tree.get(level):
            self.leaves.append(int(level))
        else:
            for node in self.tree.get(level):
                length = self.buildHeader(node, widget, row + 1, col + sumLen)
                # add multicellwidget
                sumLen += length
        if sumLen == 0:
            sumLen += 1
        lstr = self.treeLabels.get(level, None)
        if lstr:
            label = hgLabel(lstr, parent = widget)
            # -1 because 4 cols span from 1 to 4 (1 to 1 + 3)
            layout.addMultiCellWidget(label, row, row, col, col + sumLen - 1, hg.AlignCenter)
        return sumLen

    def buildLayout(self, manager, widget):
        """\brief Initialise the dialogs layout"""
        layout = hgGridLayout(widget, 2, 5, 2, 4)

        # style
        layout._styleSheet.getSsiName( ssiPHEN_TAB )
        layout._styleSheet.getSsiName( ssiPHEN_TAB_TD )
        layout.setSsiName( '.treelistdlg' )

        # store depth of tree
        self.maxRow = 0

        # list containing values (ordered acc. to tree)
        self.leaves = []

        # cycle through tree, build header, increases maxRow
        sumLen = self.buildHeader(self.level, widget, 0, 1)

        # build top
        if self.level == 0:
            label = hgLabel(self.attrLabel, parent = widget)
            layout.addMultiCellWidget(label, 0, 0, 1, sumLen, hg.AlignCenter)

        # upper left corner for level select box:
        widg2    = hgWidget(parent = widget)

        # build selector
        sel = self.tree.get(0, [])
        box = hgComboBox(parent = widg2)
        for autoid in sel:
            box.insertItem(self.treeLabels.get(autoid), autoid)
        box.insertItem('-top level-', '0')
        box.sort()
        box.connect(box.valueChanged, self.setLevel)

        button   = hgPushButton('Select', parent = widg2)
        button.connect(button.clicked, self.activateSelect)
        layout.addMultiCellWidget(widg2, 0, self.maxRow, 0, 0)

        self.maxRow += 1

        # store widgets
        self.widgets = {}

        # cycle through entries, build widgets
        keylist = self.entries.keys()
        keylist.sort()
        for row, autoid in enumerate(keylist):
            entry = self.entries[autoid]
            # get and display label
            label = hgLabel(entry[ENTRY_LABEL], parent = widget)
            layout.addWidget(label, row + self.maxRow, 0, hg.AlignLeft)
            # layout
            #label = hgLabel(':', parent = widget)
            #layout.addWidget(label, row + 1, 1)
            # get attrib
            values = entry.get(self.attrib, [])
            # prepare widgets dict
            self.widgets[autoid] = {}

            for col, value in enumerate(self.leaves):
                # build checkbox
                box = hgCheckBox(parent = widget)
                # setChecked
                if value in values:
                    box.setChecked(True)
                # disable, if not editable line
                if not entry.get(ENTRY_EDIT):
                    box.setEnabled(False)
                layout.addWidget(box, row + self.maxRow, col + 1, hg.AlignCenter)
                self.widgets[autoid][value] = box
            if not entry.get(ENTRY_EDIT):
                label = hgLabel('(disabled)', parent = widget)
                layout.addWidget(label, row + self.maxRow, col + 2, hg.AlignLeft)

    def buildFinalLayout(self, manager, widget):
        """\brief Show report."""
        layout = hgGridLayout(widget, 2, 5, 0, 4)
        # no header

    def updateFinalLayout(self, manager, widget):
        """\brief Show report."""
        # reset Message
        self.setMessage('Values saved.')
        # cycle through entries, get show-widgets, display
        layout = widget.layout()
        label = hgLabel(self.attrLabel, parent = widget)
        layout.addWidget(label, 0, 1, hg.AlignCenter)
        keylist = self.entries.keys()
        keylist.sort()
        url = '%s/showForm?table=%s&id=' % (manager.absolute_url(), self.table)
        for row, autoid in enumerate(keylist):
            entry = self.entries[autoid]
            label = hgLabel(entry[ENTRY_LABEL], url + str(autoid), parent = widget)
            layout.addWidget(label, row + 1, 0, hg.AlignLeft)
            # prepare widgets dict
            widg = manager.getFunctionWidget( self.table,
                                              self.attrib,
                                              widget,
                                              MASK_SHOW,
                                              entry )
            layout.addWidget(widg, row + 1, 1, hg.AlignLeft)

    def updateLayout(self, manager, widget):
        """\brief change layout."""
        #not necessary
        pass


    def setLevel(self, level):
        """\brief Change tree root level."""
        level = int(level)
        if level != self.level:
            self.level = level
            if level == 0:
                message = 'Top Level selected, '
            else:
                message = '%s selected, ' % self.treeLabels.get(level)
            self.setMessage('%sall changes reset.' % message)
        else:
            self.suppress_reset = True


    def activateSelect(self):
        """\brief Button pressed."""
        if not self.suppress_reset:
            self.do_reset = True
        self.suppress_reset = False

    def execHook(self, manager, REQUEST):
        """\brief overwrites execHook of parent class to get access to the manager."""
        if self.do_reset:
            # level changed
            self.usr_workWidget.hide()
            # remove children
            self.usr_workWidget.removeChildren()
            # layout has to be removed extra
            #\BUG leads to error at setting new layout
            # self.usr_workWidget.removeChild(self.usr_workWidget.layout())
            # layout has to be reset extra
            self.usr_workWidget.setLayout(None)
            # rebuild
            self.buildLayout(manager, self.usr_workWidget)
            # show main
            self.usr_workWidget.show()
            # show children
            self.usr_workWidget.showChildren(True)
            # done
            self.do_reset = False


    def performDo(self, manager, REQUEST):
        """\brief Returns the html source for the pooling dialog."""
        # cycle through entries, get Values according to field[COL_TYPE]
        tab = manager.tableHandler[self.table]
        for autoid in self.entries.keys():
            # produce storage entry (to avoid errors, only store tree attr)
            entry = {}

            # get real entry
            real = self.entries[autoid]

            # stop if not editable
            if not real.get(ENTRY_EDIT):
                continue

            # get original value-list
            values = real.get(self.attrib)

            # get widgets
            widgets = self.widgets[autoid]

            # cycle through leaves, get widgets, get values
            for value in self.leaves:
                # get single box
                box  = widgets[value]

                # add if checked, else remove
                # to enable partly tree edit
                if box.isChecked():
                    if not value in values:
                        values.append(value)
                else:
                    if value in values:
                        values.remove(value)

            values.sort()
            entry[self.attrib] = values

            # store value in own copy of entry
            real[self.attrib] = values

            # save entry
            tab.updateEntry(entry, autoid)
        return True
