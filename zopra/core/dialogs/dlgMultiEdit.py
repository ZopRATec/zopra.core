############################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from copy import deepcopy
from types import ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgLabel              import hgLabel
from PyHtmlGUI.widgets.hgMultiList          import hgMultiList
from PyHtmlGUI.widgets.hgPushButton         import hgPushButton
from PyHtmlGUI.kernel.hgGridLayout          import hgGridLayout
from PyHtmlGUI.kernel.hgWidget              import hgWidget
from PyHtmlGUI                              import hg

from zopra.core.dialogs.dlgOCBase     import dlgOCBase, ST_WORK, ST_FINALIZE
from zopra.core.widgets.hgFilteredRangeList import hgFilteredRangeList

from zopra.core.elements.Buttons import DLG_FUNCTION

from zopra.core             import ZM_SCM, ZM_IM
from zopra.core.constants   import TCN_CREATOR, TCN_AUTOID
from zopra.core.CorePart    import COL_TYPE,       \
                                   COL_LABEL,      \
                                   MASK_EDIT,      \
                                   MASK_SHOW


ENTRY_EDIT  = 'dlgMul_Edit'
ENTRY_LABEL = 'dlgMul_Label'
ATTR_EDIT   = 'dlgMul_AttrEdit'


class dlgMultiEdit(dlgOCBase):
    """\brief Event View Dialog"""
    _className = "dlgMultiEdit"
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
        self.attribs = {}
        self.widgets = {}
        self.restore = {}
        self.images  = {}
        self.image_attrs = {}
        self.frls_to_update = [] # store for filteredRangeLists needing update
        self.undo_store = {} # preparation for undo option
        self.table   = param_dict.get('table')
        autoids      = param_dict.get('autoid')
        attribs      = param_dict.get('attribute')
        self.allowAt = manager.getAttributeEditPermissions(self.table)
        self.initEntries(manager, autoids)
        self.initAttribs(manager, attribs)
        
        # FIXME: strange handling with undo, better make it settable
        if not param_dict.get('undo'):
            param_dict['undo'] = True

        dlgOCBase.__init__(self, manager, param_dict)

        self.caption     = 'Multi Edit'
        self.do_reset    = False
        self.message     = ''


    def initTargetUrl(self, manager, REQUEST):
        """\brief used to set the target to jump to when dialog is finished.
                Tries to get all params from the REQUEST for search result page."""
        # build base url
        url = '%s/showList?' % manager.absolute_url()
        # add params from request
        for key in REQUEST.form.keys():
            # do not add the multiedit-button
            if key == DLG_FUNCTION + 'Multi Edit':
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
            cop    = deepcopy(entry)
            cop2   = deepcopy(entry)
            autoid = cop[TCN_AUTOID]

            # check edit rights for entry
            creator = entry.get(TCN_CREATOR, -1)
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


    def initAttribs(self, manager, attrs):
        """\brief Test attributes and user rights."""
        if not attrs:
            attrs = []
        if not isinstance(attrs, ListType):
            attrs = [attrs]

        # get table object
        tobj = manager.tableHandler[self.table]

        # get all attribs from manager (returns copy)
        all = deepcopy(tobj.getColumnDefs(True))

        # for active ebase, add ebase attrs
        if manager.checkEBaSe(self.table):
            key1 = '%s_ebase_show' % self.table
            key2 = '%s_ebase_edit' % self.table
            all[key1] = tobj.getField(key1)
            all[key2] = tobj.getField(key2)

        # store attributes with field info
        for attr in all.keys():
            field = all[attr]
            # deprecated way to find invisible lists
            if field.get(COL_LABEL) == '' or field.get(COL_LABEL) == ' ':
                del all[attr]
                continue
            ctype = field.get(COL_TYPE)
            # for the beginning, we can't handle hierarchylists
            if ctype == 'hierarchylist':
                field[ATTR_EDIT] = False
            else:
                if attr in self.allowAt:
                    field[ATTR_EDIT] = True
                else:
                    field[ATTR_EDIT] = False
            if (ctype == 'singlelist' or ctype == 'multilist'):
                lobj = manager.listHandler.getList(self.table, attr)
                if lobj.manager == ZM_IM:
                    if lobj.function == 'getImage':
                        ftype = 'image'
                    else:
                        ftype = 'file'
                    self.image_attrs[attr] = ftype

        self.attribs = all

        # test attrs (shown attributes have to be in all-dict)
        for attr in attrs:
            if not all.has_key(attr):
                attrs.remove(attr)
        # store attrs
        self.showAt       = attrs
        # store again as newSelection to avoid unnecessary updates
        self.newSelection = attrs


    def buildLayout(self, manager, widget):
        """\brief Hook function, Initialise the dialogs layout"""
        layout = hgGridLayout(widget, 2, 5, 0, 4)

        # upper left corner for attr select:
        widg = hgWidget(parent = widget)
        mul = hgMultiList(parent = widg)
        for entry in self.attribs.keys():
            mul.insertItem(self.attribs[entry].get(COL_LABEL), entry)
        mul.setSelectedValueList(self.showAt)
        mul.connect(mul.valueSelectionChanged, self.selectAttributes)

        button = hgPushButton('Select', parent = widg)
        button.connect(button.clicked, self.activateSelect)

        # add to layout
        layout.addWidget(widg, 0, 0)

        # cycle through attribs, build header
        for col, attr in enumerate(self.showAt):
            label = hgLabel(self.attribs[attr].get(COL_LABEL), parent = widget)
            layout.addWidget(label, 0, col + 2, hg.AlignCenter)

        # cycle through entries, build widgets
        keylist = self.entries.keys()
        keylist.sort()
        for row, autoid in enumerate(keylist):
            entry = self.entries[autoid]
            # get and display label
            label = hgLabel(entry[ENTRY_LABEL], parent = widget)
            layout.addWidget(label, row + 1, 0, hg.AlignLeft)
            # layout
            label = hgLabel(':', parent = widget)
            layout.addWidget(label, row + 1, 1)
            if entry.get(ENTRY_EDIT):
                flag = MASK_EDIT
            else:
                flag = MASK_SHOW
            # prepare widgets dict
            self.widgets[autoid] = {}
            for col, attr in enumerate(self.showAt):
                aflag = flag
                # not editable attrs are only shown
                if not self.attribs[attr][ATTR_EDIT]:
                    aflag = MASK_SHOW
                widg = manager.getFunctionWidget( self.table,
                                                  attr,
                                                  widget,
                                                  aflag,
                                                  entry,
                                                  str(autoid) )
                if isinstance(widg, hgFilteredRangeList):
                    widg.connect( widg.updateNeeded, self.frlNeedUpdate )
                layout.addWidget(widg, row + 1, col + 2, hg.AlignCenter)
                self.widgets[autoid][attr] = widg
            if not entry.get(ENTRY_EDIT):
                label = hgLabel('(disabled)', parent = widget)
                layout.addWidget(label, row + 1, col + 3, hg.AlignLeft)


    def buildFinalLayout(self, manager, widget):
        """\brief Hook Function, Show report."""
        pass


    def updateFinalLayout(self, manager, widget):
        """\brief Hook Function, Show report."""
        widget.removeChildren()
        widget.setLayout(None)
        layout = hgGridLayout(widget, 2, 5, 0, 4)

        # cycle through attribs, build header
        for col, attr in enumerate(self.showAt):
            label = hgLabel(self.attribs[attr].get(COL_LABEL), parent = widget)
            layout.addWidget(label, 0, col + 1)

        # cycle through entries, get show-widgets, display
        keylist = self.entries.keys()
        keylist.sort()
        url = '%s/showForm?table=%s&id=' % (manager.absolute_url(), self.table)
        for row, autoid in enumerate(keylist):
            entry = self.entries[autoid]
            label = hgLabel(entry[ENTRY_LABEL], url + str(autoid), parent = widget)
            layout.addWidget(label, row + 1, 0)
            flag = MASK_SHOW
            # prepare widgets dict
            for col, attr in enumerate(self.showAt):
                widg = manager.getFunctionWidget( self.table,
                                                  attr,
                                                  widget,
                                                  flag,
                                                  entry,
                                                  str(autoid) )
                layout.addWidget(widg, row + 1, col + 1)


    def updateLayout(self, manager, widget):
        """\brief Hook called in WORK State when any button pressed, widget is the active widget"""
        # look for hgFilteredRangeLists needing update
        while self.frls_to_update:
            # take it out of the list
            frl = self.frls_to_update.pop()
            # let it update itself with the manager
            frl.updateYourself(manager)


    def resetLayout(self, manager):
        """\brief own reset function, update is not enough after undo / attribute change"""
        # remove children
        self.usr_workWidget.hide()
        self.usr_workWidget.removeChildren()
        # layout has to be reset extra
        self.usr_workWidget.setLayout(None)
        # rebuild
        self.buildLayout(manager, self.usr_workWidget)
        # show main
        self.usr_workWidget.show()
        # show children
        self.usr_workWidget.showChildren(True)

    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################

    def activateSelect(self):
        """\brief Slot Function, select-button pressed, enable attr change."""
        self.do_reset = True


    def selectAttributes(self, selection):
        """\brief Slot Function, set new selected attrs."""
        if not selection:
            selection = []
        self.newSelection = selection


    def frlNeedUpdate(self, frl):
        """\brief Slot Function, hgFilteredRangeList announces update neccessary"""
        self.frls_to_update.append(frl)


    ##########################################################################
    #
    # Dialog handling 
    #
    ##########################################################################


    def execHook(self, manager, REQUEST):
        """\brief overwrites execHook of parent class to get access to the manager.
                This hook gets called by execDlg after the widget handling (signals/value updates) and 
                before the internal state handling"""
        if self.do_reset:
            if self.newSelection != self.showAt:
                # set new selected attributes
                self.showAt = self.newSelection
                self.resetLayout(manager)
            # done
            self.do_reset = False
        else:
            if self.internalState == ST_WORK or self.internalState == ST_FINALIZE:
                # image checks
                widget = self.usr_workWidget
                layout = widget.layout()
                for autoid in self.entries.keys():
                    for attr in self.image_attrs.keys():
                        if attr in self.showAt and self.attribs[attr][ATTR_EDIT]:
                            entry = self.entries[autoid]
                            done  = False
                            # del doesn't work because of request handling
                            # try to get the widget
                            name = 'del' + str(autoid) + attr
                            box  = self.usr_workWidget.child(name)
                            if box and box.isChecked():
                                REQUEST.form[name] = box.getValue()
                                done |= manager.delFileGeneric( REQUEST,
                                                        'del',
                                                        attr,
                                                        entry,
                                                        str(autoid) )
                            done |= manager.addFileGeneric( REQUEST,
                                                    'add',
                                                    attr,
                                                    entry,
                                                    self.image_attrs[attr],
                                                    str(autoid) )
                            # try to update the image mask (it is stateless)
                            if done:
                                # find widget
                                name = str(autoid) + attr
                                widg = widget.child(name)
                                # get the position of the child on the grid
                                row, col = layout.findWidget(widg, 0, 0)
                                # remove child from layout
                                layout.remove(widg)
                                # remove from parent
                                widget.removeChild(widg)
                                # add new mask
                                mask = manager.getFunctionWidget( self.table,
                                                                attr,
                                                                widget,
                                                                MASK_EDIT,
                                                                entry,
                                                                str(autoid) )
                                layout.addWidget(mask, row, col)


    def performDo(self, manager, REQUEST):
        """\brief Hook called when OK-Button was pressed, performs the updates."""
        # cycle through entries, get Values according to field[COL_TYPE]
        tab = manager.tableHandler[self.table]
        for autoid in self.entries.keys():
            entry = self.entries[autoid]
            # entry is still the original db entry -> store copy
            self.undo_store[autoid] = deepcopy(entry)
            # stop if not editable
            if not entry.get(ENTRY_EDIT):
                continue
            widgets = self.widgets[autoid]
            # cycle through attribs, get widgets, get values
            for attr in self.showAt:
                if not self.attribs[attr][ATTR_EDIT]:
                    # not editable
                    continue
                widg  = widgets[attr]
                ctype = self.attribs[attr][COL_TYPE]

                if ctype == 'singlelist':
                    # test for image / file - ugly
                    if manager.listHandler.getList(self.table, attr).manager == 'FileManager':
                        # no change for now, already done
                        value = entry[attr]
                    else:
                        value = widg.getCurrentValue()
                elif ctype == 'multilist':
                    # test for image / file - ugly
                    if manager.listHandler.getList(self.table, attr).manager == 'FileManager':
                        # no change for now, already done
                        value = entry[attr]
                    else:
                        value = widg.getSelectedValues()
                        # notes
                        for val in value:
                            note = widg.getNote(val)
                            key = attr + 'notes' + str(val)
                            entry[key] = note
                elif ctype == 'hierarchylist':
                    value = widg.getSelectedValues()
                elif ctype == 'bool':
                    value = widg.isChecked()
                else:
                    value = widg.getText()
                entry[attr] = value
            # call generic functions
            manager.prepareDict(self.table, entry, REQUEST)
            manager.actionBeforeEdit(self.table, entry, REQUEST)
            # save entry
            tab.updateEntry(entry, autoid)
        return True


    def performUndo(self, manager, REQUEST):
        """\brief Undo Database action."""
        tab = manager.tableHandler[self.table]

        for autoid in self.undo_store.keys():
            entry = self.undo_store[autoid]
            # save this old copy to undo the changes
            tab.updateEntry(entry, autoid)
        self.entries = self.undo_store
        self.undo_store = {}
        self.resetLayout(manager)
        # essential for successful undo: return True
        return True
