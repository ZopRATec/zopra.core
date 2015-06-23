##############################################################################
#    Copyright (C) 2003-2005 by Ingo Keller                                  #
#    ingo.keller@pyhtmlgui.org                                               #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################

from copy                            import deepcopy

from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout
from PyHtmlGUI.kernel.hgWidget       import hgWidget

from PyHtmlGUI.widgets.hgMultiList   import hgMultiList
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgProperty
from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox

from zopra.core.elements.Styles.Default import ssiDLG_CLXMULTILIST, ssiDLG_CLXMULTIBUTTON

DLG_FUNCTION = 'f_'
NOTES = 'notes'


class hgComplexMultiList(hgWidget):
    """\class hgComplexMultiList

    The hgComplexMultiList widget provides a complex multilist selection view.

    """
    _className = 'hgComplexMultiList'
    _classType = hgWidget._classType + [ _className ]


    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self,
                  name        = None,
                  parent      = None,
                  prefix      = None,
                  notes       = None,
                  notesLabel  = None,
                  doProps     = False,
                  doSearch    = False ):
        """\brief  Constructs a widget with gridlayout holding the necessary
                   multilists and buttons.

        The \a parent and \a name arguments are passed to the hgWidget
        constructor.
        """

        hgWidget.__init__(self, parent, name)

        self.notes       = notes
        self.notesStore  = {}
        self.doProps     = doProps
        if notes:
            if notes is True:
                self.notesLabel = 'Notes'
            else:
                # notes is a widget
                self.notesLabel  = notesLabel
        else:
            self.notesLabel = None

        # for stateless handling (old)
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = ''

        self.doSearch   = doSearch
        self.concat_and = False

        self.buildLayout()

    def buildLayout(self):
        """\brief builds layout for complex multilist."""
        # layout
        layout = hgGridLayout(self, 4, 4)

        # make sure ssi is registered globally
        self._styleSheet.add(ssiDLG_CLXMULTILIST)
        self._styleSheet.add(ssiDLG_CLXMULTIBUTTON)

        # complex multilist building
        layout.addWidget( hgLabel('available:', parent = self), 0, 0)
        self.allList = hgMultiList(self, 'new' + self.prefix + self.name)

        # set ssi for use
        self.allList.setSsiName( ssiDLG_CLXMULTILIST.name() )
        layout.addWidget( self.allList, 1, 0)

        layout.addWidget( hgLabel('selected:', parent = self), 0, 1)
        self.selList = hgMultiList(self, 'del' + self.prefix + self.name)
        # set ssi for use
        self.selList.setSsiName( ssiDLG_CLXMULTILIST.name() )
        layout.addWidget( self.selList, 1, 1)

        # buttons
        add = 'Add Item'
        rem = 'Remove Item'
        self.addbtn = hgPushButton( add,
                                    parent = self,
                                    name = DLG_FUNCTION + add )
        self.rembtn = hgPushButton( rem,
                                    parent = self,
                                    name = DLG_FUNCTION + rem )
        self.addbtn.setSsiName(ssiDLG_CLXMULTIBUTTON.name())
        self.rembtn.setSsiName(ssiDLG_CLXMULTIBUTTON.name())
        layout.addWidget( self.addbtn, 2, 0)
        layout.addWidget( self.rembtn, 2, 1)

        # search concat
        if self.doSearch:
            # checkbox
            bname = self.prefix + self.name + '_AND'
            box = hgCheckBox( name   = bname,
                              text   = 'AND Concatenation',
                              value  = "1",
                              parent = self )
            layout.addMultiCellWidget(box, 3, 3, 0, 1)
            box.connect( box.toggled, self.toggleAndConcat )
            self.concatBox = box
        self.notesPanel = hgWidget(parent = self)
        layout.addMultiCellWidget(self.notesPanel, 0, 2, 2, 2)

        if self.doProps:
            self.propsWidget = hgWidget(parent = self)
            layout.addWidget(self.propsWidget, 0, 3)

        # signals
        self.allList.connect( self.allList.valueSelectionChanged, self.selectItems )
        self.selList.connect( self.selList.valueSelectionChanged, self.deselectItems )


    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################


    def selectItems(self, text):
        """\brief Slot Function. Add item to selList.
                  Fires selectionValueAdded signal."""
        if text:
            self.allList.resetSelected()
            for item in text:
                # we use real integers, in case there are integers
                try:
                    item = int(item)
                except:
                    # no integer
                    pass
                stritem = self.allList.getStringByValue(item)
                done = self.selList.insertSecureItem( stritem, item)

                if done:
                    # update notes
                    self.addNote(item)
                    # fire signal
                    self.selectionValueAdded(item)
            self.refreshNotes()
            # properties are only for one-time-usage-lists
            # so we need no property-add/rem, just put them in
            if self.doProps:
                self.refreshProps()


    def deselectItems(self, text):
        """\brief Slot Function. Remove item from selList.
                  Fires selectionValueRemoved signal."""
        if text:
            self.selList.resetSelected()
            for item in text:
                # type of item doesn't matter for remove
                done = self.selList.removeItemByValue(item)
                if done:
                    self.remNote(item)
                    # fire signal
                    self.selectionValueRemoved(item)
            self.refreshNotes()
            # properties are only for one-time-usage-lists
            # so we need no property-add/rem, just put them in
            if self.doProps:
                self.refreshProps()


    def toggleAndConcat(self, check):
        """\brief Slot Function. Switch concatenation method AND/OR.
        """
        self.concat_and = check
        self.andStateChanged(check)


    ##########################################################################
    #
    # Redirected Multilist Methods
    #
    ##########################################################################

    def copy(self):
        """\brief create a copy of the complex multilist."""
        # create widget
        cop = self.__class__( self.getName(),
                              None,
                              self.prefix,
                              deepcopy(self.notes),
                              self.notesLabel,
                              self.doProps,
                              self.doSearch
                              )
        # AND concatenation
        cop.setAndConcat(self.checkAndConcat())
        # the items
        for item in self.getItemList():
            cop.insertItem(item[0], item[1])
        # the selected items
        cop.setSelectedValueList(self.getSelectedValues())
        # the notes values
        if cop.notes:
            for autoid in self.notesStore:
                widg = cop.notesStore[autoid]
                old  = self.notesStore[autoid]
                if cop.notes is True:
                    # text widget
                    widg.setText(old.getText())
                else:
                    # combobox widget
                    widg.setCurrentValue(old.getCurrentValue())
            cop.refreshNotes()

        return cop


    def setListSize(self, size = 5):
        """\brief Set the size of the list."""
        self.allList.setListSize(size)
        self.selList.setListSize(size)


    def getListSize(self):
        """\brief Get the size of the list widget."""
        return self.allList.getListSize()


    def getCount(self):
        """\brief Returns the count of the items in the combobox."""
        return self.allList.getCount()


    def getItemList(self):
        """\brief Returns a list of item tuples (string, value)."""
        return self.allList.getItemList()


    def getValueList(self):
        """\brief Returns a list of values."""
        return self.allList.getValueList()


    def insertItem(self, item, value = None, index = None):
        """\brief Insert an item into the combobox"""
        return self.allList.insertItem(item, value, index)


    def insertSecureItem(self, item, value = None, index = None):
        """\brief Insert an item if its value doesn't exist in the list."""
        return self.allList.insertSecureItem(item, value, index)


    def removeItem(self, index):
        """\brief Removes an item at the specified <code>index</code> from
                  this combobox."""
        # FIXME: check for selection

        return self.allList.removeItem(index)


    def clearList(self):
        """\brief Removes all item from this mutilist."""
        sels = self.getSelectedValues()
        if sels:
            self.deselectItems(sels)
        while self.allList.getCount() > 0:
            self.allList.removeItem(0)


    def removeItemByValue(self, value):
        """\brief Removes an item with the specified value."""
        # FIXME: check for selection

        return self.allList.removeItemByValue(value)


    def setSelectedStringList(self, string_list):
        """\brief select all items in list.
                  Fires text/valueSelectionChanged signal."""

        return self.allList.setSelectedStringList(string_list)


    def setSelectedValueList(self, value_list):
        """\brief select all items in list.
                  Fires text/valueSelectionChanged signal."""

        return self.allList.setSelectedValueList(value_list)


    def getStringByValue(self, value):
        """\brief Return the string of the item that has the specified
                  value.

        The first item that appears in the list with the specified value is
        used.
        """
        return self.allList.getStringByValue(value)


    def resetSelected(self):
        """\brief Resets the selection of the list.
                  Fires value/textSelectionChanged signal."""
        values = self.selList.getValueList()
        for entry in values:
            self.selList.removeItemByValue(entry)


    def getSelectedValues(self):
        """\brief Returns all selected values (the ones in the selection list)."""
        return self.selList.getValueList()


    def checkAndConcat(self):
        """\brief Returns True, if AND-Concatenation is active."""
        return self.concat_and


    def setAndConcat(self, concat):
        """\brief Sets AND-Concatenation True / False."""
        self.concatBox.setChecked(concat)

# some special functions for notes

    def refreshNotes(self):
        """\brief"""
        if self.notes:
            # clear notesPanel-layout
            self.notesPanel.hide()
            self.notesPanel.removeChildren()
            self.notesPanel.setLayout(None)
            layout = hgGridLayout(self.notesPanel, 0, 0, 3, 3)
            # test for notes
            autoids = self.selList.getValueList()
            if autoids:
                # put in label
                lab = hgLabel(self.notesLabel, parent = self.notesPanel)
                layout.addWidget(lab, 0, 1)
                # put widgets in again
                row = 1
                for autoid in autoids:
                    autoid = int(autoid)
                    label = self.selList.getStringByValue(autoid)
                    lab   = hgLabel(label, parent = self.notesPanel)
                    layout.addWidget(lab, row, 0)
                    widg  = self.notesStore[autoid]
                    widg.reparent(self.notesPanel)
                    layout.addWidget(widg, row, 1)
                    row += 1
            self.notesPanel.show()


    def addNote(self, autoid, value = None):
        """\brief with activated notes, a selected item gets a noteswidget"""
        # evaluate self.notes
        if self.notes:
            autoid = int(autoid)
            # given with value -> overwrite existing
            if not self.notesStore.get(autoid) or value:
                if self.notes is True:
                    # old handling
                    if self.doProps:
                        name = self.prefix + self.name + NOTES + str(autoid)
                    else:
                        name = None
                    # create TextField, put it in dict
                    oneWidg = hgLineEdit(name = name, parent = self.notesPanel)
                    if value:
                        oneWidg.setText(value)
                else:
                    # notesWidget, copy and remove selection
                    oneWidg = self.notes.copy()
                    # old handling
                    if self.doProps:
                        name = self.prefix + self.name + NOTES + str(autoid)
                        oneWidg.setName(name)
                    if value:
                        oneWidg.setCurrentValue(value)
                    oneWidg.reparent(self.notesPanel)
                self.notesStore[autoid] = oneWidg


    def remNote(self, autoid):
        """\brief Anything to do to remove noteswidget on deselection"""
        pass


    def refreshProps(self):
        """\brief rebuild the property panel."""
        if self.doProps:
            # clear notesPanel-layout
            self.propsWidget.hide()
            self.propsWidget.removeChildren()
            # test for props
            autoids = self.selList.getValueList()
            if autoids:
                # put widgets in again
                for autoid in autoids:
                    widg  = hgProperty( self.prefix + self.name,
                                        str(autoid),
                                        parent = self.propsWidget )
                    widg.show()
            self.propsWidget.show()


    def initNote(self, autoid, note):
        """\brief initial notes"""
        self.addNote(autoid, note)


    def getNote(self, autoid):
        """\brief"""
        widg = self.notesStore.get(autoid)
        if widg:
            if isinstance(widg, hgLineEdit):
                return widg.getText()
            elif isinstance(widg, hgComboBox):
                return widg.getCurrentValue()


    ##########################################################################
    #
    # Signal Methods
    #
    ##########################################################################

    def selectionValueAdded(self, value):
        """\brief This signal is used for complex multilist selection.

        It is emitted whenever a new item is added to the selection list.
        \a list contains the new selected value.
        """
        self._fireSignal( self.selectionValueAdded, value )
    hgWidget._addSignal( selectionValueAdded )

    def selectionValueRemoved(self, value):
        """\brief This signal is used for complex multilist selection.

        It is emitted whenever an item is removed from the selection list.
        \a list contains the deselected value.
        """
        self._fireSignal( self.selectionValueRemoved, value )
    hgWidget._addSignal( selectionValueRemoved )

    def andStateChanged(self, state):
        """\brief This signal is used for tracking complex multilist toggle and-box.

        It is emitted when AND-checkbox is selected/delected.
        provides current state.
        """
        self._fireSignal( self.andStateChanged, state )
    hgWidget._addSignal( andStateChanged )

    ##########################################################################
    #
    # Widget Methods
    #
    ##########################################################################
    def setEnabled(self, enable = True):
        """\brief Enables or disables the hgStorageMgrPosSelector.
        """
        self.allList.setEnabled(enable)
        self.selList.setEnabled(enable)
        self.addbtn.setEnabled(enable)
        self.rembtn.setEnabled(enable)
        self.concatBox.setEnabled(enable)

        hgWidget.setEnabled(self, enable)
