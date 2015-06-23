############################################################################
#    Copyright (C) 2006 by Bernhard Voigt                                  #
#    bernhard.voigt@lmu.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from types                                  import IntType

from zopra.core.widgets.hgFilteredComboBox  import hgFilteredComboBox


class hgShortenedComboBox(hgFilteredComboBox):
    """\class hgShortenedComboBox

    \brief The hgShortenedComboBox widget provides a ComboBox combined with an entry field and filter button.

    """
    _className = 'hgShortenedComboBox'
    _classType = hgFilteredComboBox._classType + [ _className ]

    def __init__( self,
                  name     = None,
                  parent   = None,
                  prefix   = None,
                  pattern  = None,
                  vertical = False ):
        """\brief Constructs a  hgShortenedComboBox widget."""
        hgFilteredComboBox.__init__(self, name, parent, prefix, None, vertical)

        self.llength   = -1
        self.tolerance = 0
        self.rest      = 0
        self.handled   = True
        self.matchlist = []

        if pattern:
            self.setFilterText(pattern)

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def setListLength(self, length):
        """\brief sets max length of entries displayed in list"""
        assert self.checkType( 'length', length, IntType, True )

        if length == self.llength:
            return

        if length >= -1:
            self.llength = length
        else:
            return

        # NOTE: update could be done with less work
        #       but changes in leit length are expected to be few
        self.updateComboBox()


    def getListLength(self):
        """\brief gets max length of entries displayed in list"""
        return self.llength


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

        # NOTE: update could be done with less work
        #       but changes in leit length are expected to be few
        self.updateComboBox()


    def getListTolerance(self):
        """\brief gets tolerance setting of list"""
        return self.tolerance


    def getVisibleCount(self):
        """\brief the total number of items in the filtered combobox"""
        if self.handled:
            return self.combobox.getCount() - 1
        else:
            return self.combobox.getCount()


    def getOmitCount(self):
        """\brief returns the number of hidden items"""
        return self.rest


    def updateComboBox(self):
        """\brief """
        self.combobox.clearList()
        self.handled = False
        self.rest = 0

        if self.llength >= 0:
            length = self.llength
            if length < len(self.matchlist):
                if length + self.tolerance >= len(self.matchlist):
                    length += self.tolerance
                else:
                    self.rest = len(self.matchlist) - length
        else:
            length = len(self.matchlist)

        for item in self.matchlist[:length + 1]:
            self.combobox.insertItem(item[0], item[1])

        self.appendRest()


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

        if not self.filter or self.filter.match(item):
            if index is None:
                curindex = None
            elif index == 0:
                curindex = 0
            elif index == len(self._item_list) - 1:
                curindex = None
            else:
                curindex = 0
                # find nearest local index
                count = len(self.matchlist)

                for i in xrange(1, index - 1):
                    for j in xrange(curindex, count):
                        if self._item_list[i] == self.matchlist[j]:
                            curindex += 1
                            break

                # we insert after the last found match
                curindex += 1

            # insert into machlist
            mlength = len(self.matchlist)
            if curindex is None:
                self.matchlist.append( [str(item), value] )
            else:
                self.matchlist.insert( curindex, [item, value] )

            # adjust combobox
            if self.llength == -1:
                self.combobox.insertItem(item, value, curindex)
            else:
                if mlength < self.llength + self.tolerance:
                    self.combobox.insertItem(item, value, curindex)
                else:
                    self.removeRest()

                    # throw out tolerance entries if tolerance is exceeded
                    if mlength == self.llength + self.tolerance:
                        for rindex in xrange(self.tolerance):
                            self.combobox.removeItem(self.llength)
                        self.rest = self.tolerance

                    if curindex < self.llength:
                        last = self.combobox.getCount() - 1
                        self.combobox.removeItem(last)
                        self.combobox.insertItem(item, value, curindex)

                    self.rest += 1

                    self.appendRest()


    def removeItem(self, index):
        """\brief Removes an item at the specified <code>index</code> from the
                  combobox.
        """
        assert self.checkType( 'index', index, IntType )

        if index < 0 or index >= len(self._item_list):
            return

        item = self._item_list[index]

        if not self.filter or self.filter.match(item[0]):
            lindex  = 0
            mlength = len(self.matchlist)
            for i, litem in enumerate(self.matchlist):
                if item == litem:
                    lindex = i

            # remove from match list
            self.matchlist.pop(lindex)

            # find in combobox
            if self.llength == -1:
                self.combobox.removeItem(lindex)
            else:
                self.removeRest()

                if mlength <= self.llength + self.tolerance:
                    self.combobox.removeItem(lindex)
                elif lindex < self.llength:
                    self.combobox.removeItem(lindex)


                    item = self.matchlist[self.llength - 1]
                    self.combobox.insertItem(item[0], item[1])

                if mlength == self.llength + self.tolerance + 1:
                    self.rest = 0
                    for litem in self.matchlist[self.combobox.getCount():]:
                        self.combobox.insertItem(litem[0], litem[1])
                elif mlength > self.llength + self.tolerance + 1:
                    self.rest -= 1

                self.appendRest()


        # remove from global list
        self._item_list.pop(index)

        # adjust the current index
        if index < self._currentItem:
            self._currentItem -= 1
        elif index == self._currentItem:
            self.setCurrentItem(-1)


    def clearList(self):
        """\brief Removes all items from the combobox."""
        self._item_list   = []
        self.matchlist    = []
        self.combobox.clearList()
        self.setCurrentItem(-1)
        self.setInvalid()


    def applyFilter(self):
        """\brief sort the internal list."""

        if self.filtered:
            return

        if self.filter:
            locallist = filter(lambda item: self.filter.match(item[0]), self._item_list)
        else:
            locallist = self._item_list

        self.matchlist = locallist

        self.updateComboBox()

        self.setCurrentItem(self._currentItem)

        self.setInvalid()
        self.filtered = True


    def sort(self):
        """\brief sort the internal list."""
        self._item_list.sort()
        self.matchlist.sort()
        self.updateComboBox()
        self.setCurrentItem(-1)


    def appendRest(self):
        """\brief ."""

        if not self.handled and self.rest > 0:
            restmsg = '%s more elements' % str(self.rest)
            if self.filter:
                restmsg += ' matching &quot;%s&quot;' % self.editFilter.getText()
            else:
                restmsg += '...'

            self.combobox.insertItem(restmsg, 'NULL')

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
