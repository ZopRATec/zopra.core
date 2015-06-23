############################################################################
#    Copyright (C) 2006 by Bernhard Voigt                                  #
#    bernhard.voigt@lmu.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

import re
from types                              import IntType, StringType

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgLineEdit       import hgLineEdit
from PyHtmlGUI.widgets.hgComboBox       import hgComboBox

from zopra.core.elements.Buttons        import mpfFilterButton

from zopra.core.elements.Styles.Default import ssiDLG_FILTEREDCBOX

from zopra.core.CorePart import FCB_DEFAULT_FILTER_TEXT, FILTER_EDIT

SPECIAL_CHARS = [ '+', '(', ')', '{', '}', '|', '!', '^', '$', ':'
                  '[', ']' ]
EVIL_CHARS    = [ '\\' ]


class hgFilteredComboBox(hgWidget):
    """ hgFilteredComboBox

    The hgFilteredComboBox widget provides a ComboBox combined with an entry
    field and filter button.
    """
    _className = 'hgFilteredComboBox'
    _classType = hgWidget._classType + [ _className ]

    def __init__(self,
                 name     = None,
                 parent   = None,
                 prefix   = None,
                 pattern  = None,
                 vertical = False):
        """\brief Constructs a  hgFilteredComboBox widget."""
        hgWidget.__init__(self, parent, 'fcb_' + name)
        self._item_list   = []
        self._currentItem = -1
        self._isVertical  = vertical
        self.filter       = None
        self.filtered     = True

        # for stateless handling (old)
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = ''

        self.buildLayout()

        if pattern:
            self.setFilterText(pattern)


    def initFilter(self, pattern):
        """\brief builds layout for complex multilist."""

        if pattern == FCB_DEFAULT_FILTER_TEXT:
            pattern = ''

        while '**' in pattern:
            pattern = pattern.replace('**', '*')

        if pattern in ['', '*']:
            if self.filter:
                self.filter    = None
                self.filtered  = False
            return

        # we match everything that includes the input
        if pattern[0] != '*':
            pattern = '*' + pattern
        if pattern[-1] != '*':
            pattern = '*' + pattern

        # TODO: until i get the masking of special characters right this must do
        # match anything for evil chars
        for char in EVIL_CHARS:
            pattern = pattern.replace(char, '?')
        # mask special chars
        for char in SPECIAL_CHARS:
            pattern = pattern.replace(char, '?')

        pattern = pattern.replace('*', '.*')
        pattern = pattern.replace('?', '.')

        self.filter = re.compile(pattern)

        self.filtered = False

    def buildLayout(self):
        """\brief builds layout for complex multilist."""

        row    = 0
        column = 0

        # layout
        layout = hgGridLayout(self, 4, 4)

        self.combobox = hgComboBox(name = self.prefix + self.name[4:], parent=self)
        layout.addWidget( self.combobox, row, column)


        if self._isVertical:
            row    += 1
        else:
            column += 1

        # complex multilist building
        self.editFilter = hgLineEdit(name = FILTER_EDIT + self.prefix + self.name[4:], parent = self)
        self.editFilter.setText(FCB_DEFAULT_FILTER_TEXT)
        layout.addWidget( self.editFilter, row, column)

        if self._isVertical:
            row    += 1
            self.editFilter._styleSheet.add(ssiDLG_FILTEREDCBOX)
            self.editFilter.setSsiName( ssiDLG_FILTEREDCBOX.name() )
            mpfFilterButton.setSsiName( ssiDLG_FILTEREDCBOX.name() )
        else:
            column += 1
            self.editFilter.setSize(20)

        self.applyButton = hgLabel(mpfFilterButton.getHtml(), parent = self)

        layout.addWidget( self.applyButton, row, column)

        # signals
        self.editFilter.connect( self.editFilter.textChanged, self.updateFilter )

        self.combobox.connect( self.combobox.textChanged,  self.textChanged  )
        self.combobox.connect( self.combobox.valueChanged, self.valueChanged )


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


    def getTotalCount(self):
        """\brief the total number of items in the filtered combobox"""
        return len(self._item_list)


    def getVisibleCount(self):
        """\brief the total number of items in the filtered combobox"""
        return self.combobox.getCount()


    def getCurrentItem(self):
        """\brief the index of the current item in the combobox"""
        return self._currentItem


    def setCurrentItem(self, index):
        """\brief Set the current item."""

        if index == self._currentItem:
            return

        if not -2 < index < self.getTotalCount():
            raise ValueError( 'Global index %s out of bounds. [0, %s]' % ( str(index), str(self.getTotalCount()) ) )

        self._currentItem = index

        self.combobox.setCurrentItem(self.translateItemToLocal(index))


    def resetSelected(self):
        """\brief Sets the selection back to none item.

        The method is the same as setCurrentItem( -1 )
        """
        self.setCurrentItem( -1 )


    def currentItemIsVisible(self):
        """\brief Set the current item."""

        return self.translateItemToLocal(self._currentItem) >= 0


    def itemIsVisible(self, index):
        """\brief Set the current item."""

        return self.translateItemToLocal(index) >= 0


    def getCurrentText(self):
        """\brief the text of the combobox's current item"""
        if -1 < self._currentItem < self.getTotalCount():
            try:
                return self._item_list[self._currentItem][0]
            except IndexError:
                pass

        return ''


    def setCurrentText(self, text):
        """\brief the text of the combobox's current item"""
        assert self.checkType( 'text', text, StringType )
        for index, item in enumerate(self._item_list):
            if item[0] == text:
                self.setCurrentItem(index)
                break


    def getCurrentValue(self):
        """\brief Returns the current selected value."""
        if self._currentItem == -1:
            return None
        try:
            if self._item_list[self._currentItem][1]:
                return self._item_list[self._currentItem][1]

            return self._item_list[self._currentItem][0]
        except IndexError:
            # when value is set to -1 on clearList, the signal arrives, the list is empty
            # and getCurrentValue is called to compare, which leads to a index range error
            # avoid it:
            self._currentItem = -1
            return None


    def getItemList(self):
        """\brief Returns a list of item tuples (text, value)."""
        return self._item_list


    def getStringByValue(self, value):
        """\brief Return the string of the item that has the specified
                  value.

        The first item that appears in the list with the specified value is
        used.
        """
        value = str(value)
        for item in self._item_list:
            if str(item[1]) == value:
                return item[0]


    def insertItem(self, item, value = None, index = None):
        """\brief Insert an item into the combobox considering the filter"""
        assert self.checkType( 'index', index, IntType, True )

        if index is None:
            index = len(self._item_list)
            self._item_list.append( [str(item), value] )
        else:
            if index > len(self._item_list):
                index = len(self._item_list)

            if index < 0:
                index = 0

            self._item_list.insert(index,  [str(item), value] )

            # adjust the current index
            if index <= self._currentItem:
                self._currentItem += 1

        # show in combobox if filter is matched
        if self.filter:
            if self.filter.match(str(item)):
                if index is None:
                    curindex = None
                elif index == 0:
                    curindex = 0
                elif index == len(self._item_list) - 1:
                    curindex = None
                else:
                    curindex = 0
                    # find nearest local index
                    litems    = self.combobox.getItemList()
                    litemslen = len(litems)

                    for i in xrange(1, index - 1):
                        for j in xrange(curindex, litemslen):
                            if self._item_list[i] == litems[j]:
                                curindex += 1
                                break

                    # we insert after the last found match
                    curindex += 1

                self.combobox.insertItem(item, value, curindex)
        else:
            self.combobox.insertItem(item, value, index)

        self.setInvalid()


    def removeItem(self, index):
        """\brief Removes an item at the specified <code>index</code> from the
                  combobox.
        """
        assert self.checkType( 'index', index, IntType )

        if index < 0 or index >= len(self._item_list):
            return

        # remove from local list
        local = self.translateItemToLocal(index)

        if local > -1:
            self.combobox.removeItem(local)

        self._item_list.pop(index)

        # adjust the current index
        if index < self._currentItem:
            self._currentItem -= 1
        elif index == self._currentItem:
            self.setCurrentItem(-1)

        self.setInvalid()


    def clearList(self):
        """\brief Removes all items from the combobox."""
        self.combobox.clearList()
        self._item_list   = []
        self.setCurrentItem(-1)
        self.setInvalid()


    def setCurrentValue(self, value):
        """\brief Set the current item to the item that has the specified
                  value.

        The first item that appears in the list with the specified value is
        used.
        """
        value = str(value)
        for index, item in enumerate(self._item_list):
            # TODO: remove or-hack, makes handling ambigous
            if str(item[1]) == value or \
               ( item[1] is None and str(item[0]) == value ):
                self.setCurrentItem(index)
                break


    def sort(self):
        """\brief sort the internal list."""
        self._item_list.sort()
        self.combobox.sort()
        self.setCurrentItem(-1)


    def applyFilter(self):
        """\brief sort the internal list."""

        if self.filtered:
            return

        if self.filter:
            locallist = filter(lambda item: self.filter.match(item[0]), self._item_list)
        else:
            locallist = self._item_list

        self.combobox.clearList()

        for item in locallist:
            self.combobox.insertItem(item[0], item[1])

        self.setCurrentItem(self._currentItem)

        self.setInvalid()
        self.filtered = True


    def translateItemToGlobal(self, index):
        """\brief Translates global item index to local one in filtered combo box."""

        if index == -1:
            return -1
        elif not -1 < index < self.getVisibleCount():
            raise ValueError('Local index %s out of bounds.' % index)

        pos = 0

        locallist = self.combobox.getItemList()

        for item in self._item_list:
            if locallist[index] == item:
                return pos
            pos += 1

        raise ValueError('Item with local index %s not found in global list.' % index)


    def translateItemToLocal(self, index):
        """\brief Translates local item index in combobox to global one."""

        if index == -1 or self.getTotalCount() == 0:
            return -1
        elif not -1 < index < self.getTotalCount():
            raise ValueError('Global index %s out of bounds.' % str(index))

        pos = 0

        for item in self.combobox.getItemList():
            if self._item_list[index] == item:
                return pos
            pos += 1

        return -1


    def getFilterText(self):
        """\brief Returns contents of filter entry widget"""
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


    def updateFilter(self, pattern):
        """\brief Slot function to update filter on change in entry widget"""

        self.initFilter(pattern)
        self.applyFilter()
        self.filterUpdated(self.getFilterText())


    ##########################################################################
    #
    # Signal Methods
    #
    ##########################################################################
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

        if value == cvalue:
            self._fireSignal( self.valueChanged, value )
        else:
            self.setCurrentValue(value)
    hgWidget._addSignal( valueChanged )


    def filterUpdated(self, value):
        """\brief This signal is used for editable comboboxes.

        It is emitted whenever the contents of the text entry field changes.
        \a value contains the new value.
        """

        self._fireSignal( self.filterUpdated, value )
    hgWidget._addSignal( filterUpdated )


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

        hgWidget.setEnabled(self, enable)
