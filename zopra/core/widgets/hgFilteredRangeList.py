############################################################################
#    Copyright (C) 2009 by ZopRATec                                        #
#    peterseifert@gmx.de                                                   #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from types                           import IntType, StringType, ListType

from PyHtmlGUI                       import hg
from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout
from PyHtmlGUI.kernel.hgWidget       import hgWidget

from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgProperty
from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox

from zopra.core.elements.Buttons        import DLG_FUNCTION, \
                                                          BTN_L_FILTER, \
                                                          BTN_FRL_PREV, \
                                                          BTN_FRL_NEXT

from zopra.core.elements.Styles.Default     import ssiFRL_SMALLTEXT, \
                                                          ssiFRL_BUTTONS,   \
                                                          ssiFRL_BOX,       \
                                                          ssiFRL_SMALLBUTTONS

from zopra.core.widgets.hgComplexMultiList         import NOTES
from zopra.core.widgets.hgFilteredComboBox import FCB_DEFAULT_FILTER_TEXT, \
                                                     FILTER_EDIT


class hgFilteredRangeList(hgWidget):
    """\class hgFilteredRangeList

    The hgFilteredRangeList combines a shortened list with filtering for single
    and multi lists.

    In contrast to hgShortenedComboBox and hgFilteredComboBox, not all entries
    of the list get loaded into the widget to display some of them, instead the
    ZopRA Core provides the functionality to only load the requested entries
    (page-wise via limit / offset or optionally via filter). This functionality
    resides in the ForeignList.getWidget and MultiList.getComplexWidget
    functions. The hgFilteredRangeList can be used as single or multilist. The
    filter display has to be activated additionally. Paging through the contents
    of a list with this widget in form based mode requires functionality for the
    rangelist_next and rangelist_prev buttons as well as the rangelist_add,
    rangelist_remove and rangelist_filter buttons. In dialog-mode, these buttons
    trigger signals with according names that have to be handled externally.
    """
    _className = 'hgFilteredRangeList'
    _classType = hgWidget._classType + [ _className ]

    def __init__(self,
                 name        = None,
                 parent      = None,
                 prefix      = None,
                 notes       = None,   # True or a widget for multilist notes display
                 notesLabel  = None,   # a label for the multilist notes
                 doProps     = False,  # add Properties for formbased handling (stateless)
                 doSearch    = False,  # widget used for search -> no search value item
                 doNull      = False,  # show no value item
                 doFilter    = False,  # use filter
                 pattern     = None,   # filter pattern
                 single      = True,   # single / multi switch
                 totalcount  = 0,      # number of total items in db
                 startitem   = 0,      # number of first item (of total)
                 maxLength   = 0,      # infinite length of items in box, minimum 22
                 tolerance   = 10,     # tolerance
                 showitems   = 0,      # number of items to show
                 foreignTable = None,  # only needed for dialog handling (list updates itself)
                 foreignMgr  = None    # for dialog handling (stateful)
                 ):
        """\brief Constructs a hgFilteredRangeList widget."""
        # only handle filter text, no filtering, no internal list
        # display all entries given
        # needs total entry count (or total filtered entry count resp.)
        # needs startitem / showitems numbers
        # init does not layout, layouting done by finalize-function
        # after all things have been set and configured
        # set and add buttons for single / multi usage
        # filter (optional) / prev / next buttons for entry selection

        # for stateless handling (formbased)
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = ''

        hgWidget.__init__(self, parent, self.prefix + name)

        self._isSingle    = single

        # selected items stored by value (autoid) and text, not index
        self._currentText  = []
        self._currentValue = []

        # properties for statefull handling when button meets selection
        self.filterbuttonpressed = False
        self.newfilterpattern    = None

        # item numbering properties
        self.totalcount   = totalcount
        self.startitem    = startitem
        self.showitems    = showitems
        self.tolerance    = tolerance
        self.foreignTable = foreignTable
        self.foreignMgr   = foreignMgr

        # notes related properties (multi only)
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

        # indicate search (-> add -no search value-)
        self.doSearch   = doSearch
        # indicate null usage (-> add -no value-)
        self.doNull = doNull
        # maximum length of items in box for stable layout,
        # minimum 21 (length of nosearch value)
        if maxLength and maxLength < 22:
            maxLength = 22
        self.maxLength = maxLength
        # on search we can switch AND/OR constraints for multi
        self.concat_and = False
        # indicates that rest-value has been added
        self.handled    = False

        # property to switch filter on / off
        self.doFilter = doFilter

        # the set name is [DLG_CUSTOM + prefix] + name
        # buttons do not use prefix -> we need the real name
        self.realname = name

        # store filter here too
        if pattern:
            self.filtertext = pattern
        else:
            self.filtertext = ''

        self.buildLayout()

        # only after buildLayout, the filter widget exists to set the filter
        if doFilter and pattern:
            self.setFilterText(pattern)


#
# layouting
#

    def buildLayout(self):
        """\brief builds layout for range list (single / multi) with optional filter."""
        # layout
        layout = hgGridLayout(self, 4, 4, 5, 0)

        # add styles
        self._styleSheet.add(ssiFRL_SMALLTEXT)
        self._styleSheet.add(ssiFRL_BUTTONS)
        self._styleSheet.add(ssiFRL_SMALLBUTTONS)
        self._styleSheet.add(ssiFRL_BOX)

        # name of combobox is same as name of complete widget?
        # no, since name of selected properties has to be same as complete
        # widget but selecting an item without hitting the set/add buttons
        # should also select it if nothing else was previously selected
        # prefix is already in self.name
        self.combobox = hgComboBox(name = 'new' + self.name, parent = self)
        layout.addWidget( self.combobox, 0, 2)
        self.combobox.setSsiName(ssiFRL_BOX.name())
        self.combobox.connect(self.combobox.valueChanged, self.slotSelectItem)
        self.initCBItems()

        # filter
        if self.doFilter:
            # filter edit widget (prefix is already in self.name)
            self.editFilter = hgLineEdit(name = FILTER_EDIT + self.name, parent = self)
            self.editFilter.setText(FCB_DEFAULT_FILTER_TEXT)
            layout.addWidget( self.editFilter, 1, 2)
            self.editFilter.setSsiName(ssiFRL_BOX.name())

            # filter apply button
            btnname = DLG_FUNCTION + BTN_L_FILTER + '_' + self.name
            self.applyButton = hgPushButton(BTN_L_FILTER, name = btnname, parent = self)
            layout.addWidget( self.applyButton, 1, 3)
            self.applyButton.setSsiName( ssiFRL_BUTTONS.name() )

            # filter signals
            self.editFilter.connect( self.editFilter.textChanged, self.slotUpdateFilter )
            self.applyButton.connect( self.applyButton.clickedButton, self.slotUpdateFilterButton)

        self.notesPanel = hgWidget(parent = self)
        if self.doFilter:
            row = 2
        else:
            row = 1

        layout.addMultiCellWidget(self.notesPanel, row, row + 1, 2, 3)

        # buttons
        add = 'Add Item'
        rem = 'Remove Item'
        prev = '<'
        nxt  = '>'

        self.addbtn = hgPushButton( add,
                                    parent = self,
                                    name = DLG_FUNCTION + add )
        # remove button is placed on notesPanel
        self.rembtn = hgPushButton( rem,
                                    parent = self.notesPanel,
                                    name = DLG_FUNCTION + rem )

        btnname = DLG_FUNCTION + BTN_FRL_PREV + '_' + self.name
        self.prevbtn = hgPushButton( prev,
                                    parent = self,
                                    name = btnname )

        btnname = DLG_FUNCTION + BTN_FRL_NEXT + '_' + self.name
        self.nextbtn = hgPushButton( nxt,
                                    parent = self,
                                    name = btnname )

        # styles
        self.addbtn.setSsiName(ssiFRL_BUTTONS.name())
        self.rembtn.setSsiName(ssiFRL_BUTTONS.name())
        self.prevbtn.setSsiName(ssiFRL_SMALLBUTTONS.name())
        self.nextbtn.setSsiName(ssiFRL_SMALLBUTTONS.name())

        if self._isSingle:
            # for singlelist, button label is Set Item
            self.addbtn.setText('Set Item')

        # add button added
        layout.addWidget( self.addbtn, 0, 3)

        # next/prev buttons added
        layout.addWidget(self.prevbtn, 0, 0)
        layout.addWidget(self.nextbtn, 0, 1)

        # search concat
        if self.doSearch:
            # checkbox (prefix is already in self.name)
            bname = self.name + '_AND'
            box = hgCheckBox( name   = bname,
                              text   = 'AND Concatenation',
                              value  = "1",
                              parent = self.notesPanel )
            box.connect( box.toggled, self.slotToggleAndConcat )
            self.concatBox = box

        if self.doProps:
            self.propsWidget = hgWidget(parent = self)
            layout.addWidget(self.propsWidget, row + 1, 0)

        # the labels for from/to/all
        self.numlabel = hgLabel(name = 'numlabel', parent = self)
        layout.addMultiCellWidget(self.numlabel, 1, 1, 0, 1, hg.AlignHCenter | hg.AlignTop)
        self.numlabel.setSsiName( ssiFRL_SMALLTEXT.name() )

        # other signals
        # add / remove buttons
        # self.addbtn.connect( self.addbtn.clickedButton, self.slotSelectItemButton)
        # self.rembtn.connect( self.rembtn.clickedButton, self.slotDeselectItemsButton)
        # prev / next buttons
        self.prevbtn.connect( self.prevbtn.clickedButton, self.slotPreviousRange)
        self.nextbtn.connect( self.nextbtn.clickedButton, self.slotNextRange)

        self.combobox.connect( self.combobox.valueChanged, self.slotSelectItem )


    def refreshNotes(self):
        """\brief"""
        # clear notesPanel-layout
        self.notesPanel.hide()
        self.notesPanel.removeChildren()
        self.notesPanel.setLayout(None)
        layout = hgGridLayout(self.notesPanel, 2, 1, 0, 0)

        # selection label
        lab = hgLabel('Selection:&nbsp;', parent = self.notesPanel)
        layout.addWidget(lab, 0, 0)

        # test for notes
        autoids = self.getSelectedValues()
        row = 1
        if autoids and autoids[0] != 'NULL':

            if self._isSingle:
                # only show one value on pos 0,3
                label = self._currentText[0]
                lab = hgLabel(label, parent = self.notesPanel)
                layout.addWidget(lab, 0, 1)
            else:

                # put in notes label
                if self.notes:
                    lab = hgLabel(self.notesLabel, parent = self.notesPanel)
                    layout.addWidget(lab, 0, 1)

                # put widgets in again
                for index, autoid in enumerate(autoids):
                    # autoid = int(autoid)

                    # checkbox for removal (prefix is already in self.name)
                    cname = 'del' + self.name
                    cvalue = str(autoid)
                    text = self._currentText[index]
                    # restrict length ?
                    # if self.maxLength and len(text) > self.maxLength + 10:
                    #    text = text[:self.maxLength + 10]
                    box = hgCheckBox(name = cname, value = cvalue, parent = self.notesPanel, text = text)
                    box.connect(box.buttonOnObject, self.slotDeselectItems)

                    layout.addWidget(box, row, 0)

                    # notes
                    if self.notes:
                        widg  = self.notesStore[autoid]
                        widg.reparent(self.notesPanel)
                        layout.addWidget(widg, row, 1)
                    row += 1

                # put in remove button
                self.rembtn.reparent(self.notesPanel)
                layout.addWidget( self.rembtn, row, 0)

            # AND concat checkbox
            if self.doSearch and not self._isSingle:
                self.concatBox.reparent(self.notesPanel)
                layout.addWidget(self.concatBox, row, 1, hg.AlignRight)
        else:
            # nothing selected
            label = hgLabel('Nothing', parent = self.notesPanel)
            layout.addWidget( label, 0, 1)

        self.notesPanel.show()


    def refreshProps(self):
        """\brief rebuild the property panel."""
        if self.doProps:
            # clear notesPanel-layout
            self.propsWidget.hide()
            self.propsWidget.removeChildren()
            # test for props
            autoids = self.getSelectedValues()
            if autoids:
                # put widgets in again (prefix is already in self.name)
                for autoid in autoids:
                    widg  = hgProperty( self.name,
                                        str(autoid),
                                        parent = self.propsWidget )
                    widg.show()
            # the current startitem
            widg = hgProperty('frl_startitem' + self.name, str(self.startitem), parent = self.propsWidget)
            widg.show()

            # the current filter pattern
            if self.doFilter:
                text = self.getFilterText()
                if text:
                    widg = hgProperty('store_' + FILTER_EDIT + self.name, text, parent = self.propsWidget)
                    widg.show()

            self.propsWidget.show()


    def refreshLabels(self):
        """\brief Update the labels showing numbers"""
        msg = '%s - %s&nbsp;<br>/ %s&nbsp;'
        count = self.getVisibleCount()
        start = self.startitem + 1
        if count == 0:
            start = 0
        msg = msg % (start, self.startitem + count, self.totalcount)
        self.numlabel.setText(msg)


    def finalizeLayout(self):
        """\brief Finish the layout after entries and selections have been set"""
        self.refreshNotes()
        self.refreshProps()
        self.refreshLabels()
        self.appendRest()


    def initCBItems(self):
        """\brief check doNull and doSearch and put labels into combobox"""
        # empty value always there
        # last space to get to 22 letters
        self.combobox.insertItem('-- no selection --    ', '')

        # null value
        if self.doNull and self._isSingle:
            # singlelists can have NULL set (for search and for add/edit)
            # spaces to get to 22 letters (minimum length)
            self.combobox.insertItem('-- no value --        ', 'NULL')


    def appendRest(self):
        """\brief ."""

        if not self.handled and self.getOmitCount() > 0:
            restmsg = '%s more' % str(self.getOmitCount())
            ftext = self.getFilterText()
            if self.doFilter and ftext:
                restmsg += " for '%s'" % ftext  # try without &quot;, makes string too long
            else:
                restmsg += '...'

            self.combobox.insertItem(restmsg, '')

            self.handled = True


    def removeRest(self):
        """\brief ."""

        if self.handled:
            self.combobox.removeItem(self.combobox.getCount() - 1)
            self.handled = False


    def updateRest(self):
        """\brief ."""

        if self.handled:
            self.removeRest()

        self.appendRest()


    def updateYourself(self, manager):
        """\brief Called by dialogs with the manager to let the list update itself"""
        # reset entries (but not selection) -> manual clearList
        self.combobox._item_list   = []
        self.combobox._currentItem = -1
        self.combobox.setInvalid()
        # insert standard items
        self.initCBItems()
        # get foreign manager
        fmgr = manager.getHierarchyUpManager(self.foreignMgr)
        # call labelsearch function
        partlist, num = fmgr.searchLabelStrings( self.foreignTable,
                                                 self.getFilterText(),
                                                 self.startitem,
                                                 self.showitems or -1,
                                                 self.tolerance )
        # set total amount
        self.setTotalCount(num)
        # set unhandled
        self.handled = False
        # add the new entries
        for autoid in partlist:
            label = fmgr.getLabelString(self.foreignTable, autoid)
            self.insertItem(label, autoid)
        # finalize
        self.finalizeLayout()


    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def getDuplicatesEnabled(self):
        """\brief whether duplicates are allowed

        This property only affects user-interaction. You can use
        insertItem() to insert duplicates if you wish regardless of this
        setting.
        """
        return self.combobox.getDuplicatesEnabled()


    def setDuplicatesEnabled(self, enable):
        """\brief whether duplicates are allowed"""
        self.combobox.setDuplicatesEnabled(enable)


    def setDoFilter(self, enabled):
        """\brief property function for filter usage"""
        self.doFilter = enabled


    def checkDoFilter(self):
        """\brief property function for filter usage"""
        return self.doFilter

    # make property


    def getTotalCount(self):
        """\brief the total number of items in the database"""
        return self.totalcount


    def setTotalCount(self, count):
        """\brief set total number of entries in the database"""
        self.totalcount = count

    # make property


    def getVisibleCount(self):
        """\brief the total number of items in the filtered combobox"""
        # -1 always for no value
        if self.handled:
            count = self.combobox.getCount() - 2
        else:
            count = self.combobox.getCount() - 1

        # null value
        if self.doNull and self._isSingle:
                # null value
                count -= 1

        return count


    def getOmitCount(self):
        """\brief returns the number of unshown items"""
        return self.getTotalCount() - self.getVisibleCount()


    def getCount(self):
        """\brief Returns the totalcount of entries. same as getTotalCount"""
        return self.getTotalCount()


    def setListTolerance(self, tolerance):
        """\brief sets tolerance for list
                  extends the length of the list by the specified number of entries
                  if total number of matching entries <= length + tolerance"""
        assert self.checkType( 'tolerance', tolerance, IntType, True )

        if tolerance == self.tolerance:
            return

        if tolerance >= 0:
            self.tolerance = tolerance
        else:
            return


    def getListTolerance(self):
        """\brief gets tolerance setting of list"""
        return self.tolerance


    def checkAndConcat(self):
        """\brief Returns True, if AND-Concatenation is active."""
        return self.concat_and


    def setAndConcat(self, concat):
        """\brief Sets AND-Concatenation True / False."""
        self.concatBox.setChecked(concat)


    def setMaxLength(self, maxLength):
        """\brief set maximum length of strings for display, trim the existing ones
                Minimum is 22 (for own labels)"""
        if maxLength:
            # minimum 21 for nosearch value
            if maxLength < 22:
                maxLength = 22
            self.maxLength = maxLength
            # direct access to list, using function gives us a copy
            allList = self.combobox._item_list
            for item in allList:
                if item[0] and len(item[0]) > maxLength:
                    item[0] = item[0][:maxLength - 3] + '...'
            # self.combobox._item_list = allList
            self.combobox.setInvalid()
            self.setInvalid()


    def getMaxLength(self):
        """\brief get Maximum Length of strings for display"""
        return self.maxLength


    def getMaxShown(self):
        """\brief get maxshown attribute"""
        return self.showitems


    def getStartItem(self):
        """\brief get number of startitem"""
        return self.startitem


#
# list item functions
#

    # current and selection functions
    # hgCombobox (singlelist)
    def getCurrentItem(self):
        """\brief the index of the current item in the combobox"""
        return self.combobox.getCurrentItem()


    def setCurrentItem(self, index):
        """\brief Set the current item."""
        self.combobox.setCurrentItem(index)

        # use the item at index as selection
        value = self.combobox.getCurrentValue()
        text  = self.combobox.getCurrentText()
        if self._isSingle:
            self._currentValue = [value]
            self._currentText  = [text]
            self.setInvalid()

            if index > -1:
                self.textChanged( text )
                self.valueChanged( value )
        else:
            if index > -1:
                self._currentValue.append(value)
                self._currentText.append(text)
                self.setInvalid()
                self.selectionValueAdded(value)


    def getCurrentText(self):
        """\brief the text of the combobox's current item"""
        if self._isSingle and len(self._currentText) > 0:
            return self._currentText[0]
        else:
            return ''


    def setCurrentText(self, text):
        """\brief the text of the combobox's current item"""
        assert self.checkType( 'text', text, StringType )
        for index, item in enumerate(self.combobox.getItemList()):
            if item[0] == text:
                self.setCurrentItem(index)
                break


    def getCurrentValue(self):
        """\brief Returns the current selected value."""
        if self._isSingle and len(self._currentValue) > 0:
            return self._currentValue[0]
        else:
            return None


    def setCurrentValue(self, value, text = None):
        """\brief Set the current item to the item that has the specified
                  value.

        The first item that appears in the list with the specified value is
        used.
        """
        value = str(value)
        for index, item in enumerate(self.combobox.getItemList()):
            # for comboboxes without values, the text is the value
            if str(item[1]) == value or \
               ( item[1] is None and str(item[0]) == value ):
                self.setCurrentItem(index)
                return

        # still here -> not found
        if value and text:
            self.setSelectedValueList([value], [text])
            return

        raise ValueError('Implementation Error: value not found but also no text given.')


    # hgComplexMultilist (multilist)
    def setSelectedStringList(self, string_list, value_list = None):
        """\brief select all items in list.
                Fires selectionValueAdded signal."""
        # to cope with items that are not shown in the list but are selected
        # and still allow the same interface, value_list = None was added
        self._currentValue = value_list
        self._currentText = string_list
        # redraw the selection panel
        self.refreshNotes()
        # fire the signal
        if value_list:
            self.selectionValueAdded(value_list)


    def setSelectedValueList(self, value_list, string_list = None):
        """\brief select all items in list.
                Fires selectionValueAdded signal."""
        # to cope with items that are not shown in the list but are selected
        # and still allow the same interface, string_list = None was added
        self._currentValue = value_list
        self._currentText = string_list
        # redraw the selection panel
        self.refreshNotes()
        # fire the signal
        if value_list:
            self.selectionValueAdded(value_list)


    def getSelectedValues(self):
        """\brief Returns all selected values (the ones in the _currentValue list)."""
        return self._currentValue


    def resetSelected(self):
        """\brief Sets the selection back to none item.

        The method is the same as setCurrentItem( -1 ) for single mode,
        in multi mode, selection is reset and selectionValueRemoved signal
        emitted for each removed value.
        """
        if self._isSingle:
            self.setCurrentItem( -1 )
        else:
            self.combobox.resetSelected()
            values = self._currentValue
            self._currentText  = []
            self._currentValue = []
            self.setInvalid()
            # fire signals for value removal
            for value in values:
                self.selectionValueRemoved(value)

    # general entry related functions

    def getStringByValue(self, value):
        """\brief Return the string of the item that has the specified
                  value.

        The first item that appears in the list with the specified value is
        used.
        """
        value = str(value)
        for item in self.combobox.getItemList():
            if str(item[1]) == value:
                return item[0]
        # nothing found, try selected items
        if value in self._currentValue:
            index = self._currentValue.index(value)
            return self._currentText(index)
        return ''


    def getItemList(self):
        """\brief Returns a list of item tuples (text, value)."""
        return self.combobox.getItemList()


    def getValueList(self):
        """\brief Returns a list of values."""
        ilist = self.combobox.getItemList()
        return [item[1] for item in ilist if item[1] and item[1] != 'NULL']


    def clearList(self):
        """\brief Removes all items from the combobox."""
        self.resetSelected()
        self.combobox.clearList()
        self.setInvalid()


    def insertItem(self, item, value = None, index = None):
        """\brief Insert an item into the combobox"""
        if self.maxLength and len(item) > self.maxLength:
            item  = item[:self.maxLength - 3] + '...'

        return self.combobox.insertItem(item, value, index)


    def insertSecureItem(self, item, value = None, index = None):
        """\brief Insert an item if its value doesn't exist in the list."""
        assert isinstance(index, IntType) or index is None, \
               self.E_PARAM_TYPE % ('index', 'IntType or None',  index)

        occur = False
        for list_item in self.combobox.getItemList():
            if list_item[1] == value:
                occur = True
                break

        if not occur:
            return self.insertItem(item, value, index)
        else:
            return False


    def removeItem(self, index):
        """\brief Removes an item at the specified <code>index</code> from
                  this list"""
        assert isinstance(index, IntType), \
               self.E_PARAM_TYPE % ('index', 'IntType',  index)
        assert index >= 0
        assert index < self.getCount()

        self.combobox.getItemList().pop(index)
        self.setInvalid()


    def removeItemByValue(self, value):
        """\brief Removes an item with the specified value."""
        for index, item in enumerate(self.combobox.getItemList()):
            if str(item[1]) == str(value):
                self.combobox.getItemList().pop(index)
                self.setInvalid()
                return True


    def sort(self):
        """\brief sort the internal list."""
        self.combobox.sort()
        # sorting does only need a reset of selection in list, not overall selection
        self.combobox.setCurrentItem(-1)


    # filter functions

    def getFilterText(self):
        """\brief Returns contents of filter entry widget"""
        if not self.doFilter:
            return ''

        ftext = self.editFilter.getText()

        if ftext == FCB_DEFAULT_FILTER_TEXT:
            return ''

        return ftext


    def setFilterText(self, pattern):
        """\brief Sets contents of filter entry widget"""
        self.editFilter.setText(pattern)


    def resetFilterText(self):
        """\brief Sets contents of filter entry widget"""
        self.editFilter.setText(FCB_DEFAULT_FILTER_TEXT)


    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################

    def slotSelectItem(self, value):
        """\brief Slot Function. Add item to selList"""
        # we do not allow the nosearch value to be set (it is default)
        if value and value not in self._currentValue:
            # we allow the null value to be set for search only
            stritem = self.combobox.getStringByValue(value)
            if self._isSingle:
                self.setCurrentValue(value)
            else:
                self._currentValue.append(value)
                self._currentText.append(stritem)
                # signal
                self.selectionValueAdded(value)

                if self.notes:
                    # update notes
                    self.addNote(value)

            # this redraws the selected items and their notes
            # for both single / multi
            self.refreshNotes()

            # properties are only for formbased-lists (stateless)
            # so we need no property-add/rem, just put them in
            if self.doProps:
                self.refreshProps()

            self.setInvalid()


    def slotDeselectItems(self, checkbox):
        """\brief Slot Function, Slate item for removal"""
        value = int(checkbox.getValue())
        if value:
            if not isinstance(value, ListType):
                value = [value]

            for val in value:
                # remove from both lists
                index = self._currentValue.index(val)
                self._currentText.pop(index)
                self._currentValue.pop(index)

                if self.notes:
                    self.remNote(val)

                # fire signal
                self.selectionValueRemoved(val)

            self.refreshNotes()
            # properties are only for formbased-lists
            # so we need no property-add/rem, just put them in
            if self.doProps:
                self.refreshProps()

            self.setInvalid()


    def slotToggleAndConcat(self, check):
        """\brief Slot Function. Switch concatenation method AND/OR.
        """
        self.concat_and = check
        self.andStateChanged(check)


    def slotUpdateFilter(self, pattern):
        """\brief Slot function to update filter on change in filter pattern widget"""
        # we only react on filterpattern text and filterbutton pressed
        if self.filterbuttonpressed:
            self.filterbuttonpressed = False
            self.doUpdateFilter(self.getFilterText())
        else:
            self.newfilterpattern = pattern


    def slotUpdateFilterButton(self, button):
        """\brief Slot function for filter button"""
        # we only react on filterpattern text and filterbutton pressed
        if self.newfilterpattern or self.newfilterpattern == '':
            # reset temporary store
            self.newfilterpattern = None
            self.doUpdateFilter(self.getFilterText())
        else:
            self.filterbuttonpressed = True


    def doUpdateFilter(self, filtertext):
        """\brief Store filtertext, reset counts"""
        if self.filtertext != filtertext:
            self.filtertext = filtertext
            if filtertext == '':
                self.editFilter.setText(FCB_DEFAULT_FILTER_TEXT)
            # reset counts
            self.startitem = 0
            # fire signals
            self.filterUpdated(self.filtertext)
            self.updateNeeded(self)


    def slotPreviousRange(self, buttonname):
        """\brief Slot function for prev button, switch range and fire update signal"""
        if self.startitem == 0:
            return
        newstart = self.startitem - self.showitems
        if newstart >= 0:
            self.startitem = newstart
        else:
            self.startitem = 0
        # signal for update
        self.updateNeeded(self)


    def slotNextRange(self, buttonname):
        """\brief Slot function for next button, switch range and fire update signal"""
        if self.showitems:
            newstart = self.startitem + self.showitems
            if newstart <= self.totalcount:
                self.startitem = newstart
                # else do nothing, leave startitem as is
                # signal for update
                self.updateNeeded(self)


    ##########################################################################
    #                                                                        #
    # Signal Methods                                                         #
    #                                                                        #
    ##########################################################################

    # Singlelist Signals (textChanged, valueChanged)
    def textChanged(self, text):
        """\brief This signal is used for editable comboboxes.

        It is emitted whenever the contents of the text entry field changes.
        \a text contains the new text.
        """
        ctext = self.getCurrentText()

        if text == ctext:
            self._fireSignal( self.textChanged, text )
        else:
            self.setCurrentText(text)
    hgWidget._addSignal( textChanged )


    def valueChanged(self, value):
        """\brief This signal is used for editable comboboxes.

        It is emitted whenever the contents of the text entry field changes.
        \a value contains the new value.
        """
        cvalue = self.getCurrentValue()
        # value has already been set in combobox
        if value == cvalue:
            # the values match, fire signal
            self._fireSignal( self.valueChanged, value )
        else:
            # value was set by hand, set it, which fires the cbox-signal
            # which then comes back here
            self.setCurrentValue(value)
    hgWidget._addSignal( valueChanged )


    # Filter Signals (filterUpdated)
    def filterUpdated(self, value):
        """\brief This signal is used for editable comboboxes.

        It is emitted whenever the contents of the text entry field changes.
        \a value contains the new value.
        """

        self._fireSignal( self.filterUpdated, value )
    hgWidget._addSignal( filterUpdated )


    # Multilist Signals (selectionValueAdded, selectionValueRemoved, andStateChanged)
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


    def updateNeeded(self, frl):
        """\brief This signal is emitted when any button was pressed that requires content relaod"""
        self._fireSignal( self.updateNeeded, self)
    hgWidget._addSignal( updateNeeded )


    ##########################################################################
    #
    # Widget Methods
    #
    ##########################################################################
    def setEnabled(self, enable = True):
        """\brief Enables or disables the hgStorageMgrPosSelector.
        """
        self.combobox.setEnabled(enable)
        self.editFilter.setEnabled(enable)
        self.applyButton.setEnabled(enable)

        # FIXME: more enabled calls for other buttons etc.

        hgWidget.setEnabled(self, enable)


# some special functions for notes




    def addNote(self, autoid, value = None):
        """\brief with activated notes, a selected item gets a noteswidget"""
        # evaluate self.notes
        if self.notes:
            autoid = int(autoid)
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
