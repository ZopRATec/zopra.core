##############################################################################
#    Copyright (C) 2003-2005 by Ingo Keller                                  #
#    ingo.keller@pyhtmlgui.org                                               #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################

from types                          import StringTypes

from PyHtmlGUI                      import checkType
from PyHtmlGUI.widgets.hgGroupBox   import hgGroupBox


class hgEntryListPrivate:
    """\class hgEntryListPrivate

    \brief Contains the private information of the class hgEntryList.
    """

    def __init__(self):
        """\brief Constructs hgEntryListPrivate.

        \sa hgEntryList
        """
        self.entries      = None,
        self.attributes   = None,
        self.functions    = None,
        self.show_number  = 0,
        self.start_number = 0,
        self.count        = 0,


class hgEntryList(hgGroupBox):
    """\class hgEntryList

    \brief The hgEntryList widget provides a group box frame with a title.

    """
    _className = 'hgEntryList'
    _classType = hgGroupBox._classType + [ _className ]


    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################

    def setEntries(self, entries):
        """\brief Property function to set the entries"""
        self.tabData.entries = entries

    def getEntries(self):
        """\brief Property function to get the entries"""
        return self.tabData.entries

    entries = property(setEntries, getEntries)

    def setAttributes(self, attributes):
        """\brief Property function to set the show attributes"""
        self.tabData.attributes = attributes

    def getAttributes(self):
        """\brief Property function to get the show attributes"""
        return self.tabData.attributes

    attributes = property(setAttributes, getAttributes)

    def setFunctions(self, functions):
        """\brief Property function to set the linking functions"""
        self.tabData.functions = functions

    def getFunctions(self):
        """\brief Property function to get the linking functions"""
        return self.tabData.functions

    functions = property(setFunctions, getFunctions)

    def setStart(self, start):
        """\brief Property function to set start number"""
        self.tabData.start_number = start

    def getStart(self):
        """\brief Property function to get start number"""
        return self.tabData.start_number

    start = property(setStart, getStart)

    def setShowCount(self, show):
        """\brief Property function to set show count"""
        self.tabData.show_number = show

    def getShowCount(self):
        """\brief Property function to get show count"""
        return self.tabData.show_number

    showCount = property(setShowCount, getShowCount)

    def setCount(self, count):
        """\brief Property function to set the total count"""
        self.tabData.count = count

    def getCount(self):
        """\brief Property function to get the total count"""
        return self.tabData.count
    count = property(setCount, getCount)

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self,
                  title        = None,
                  entries      = None,
                  attributes   = None,
                  functions    = None,
                  show_number  = 0,
                  start_number = 0,
                  count        = 0,
                  parent       = None,
                  name         = None ):
        """\brief  Constructs a group box titled \a title.

        The \a parent and \a name arguments are passed to the hgWidget
        constructor.
        """
        assert checkType('title',  title,  StringTypes, True )

        hgGroupBox.__init__(self, None, None, title, parent, name)

        self.tabData    = hgEntryListPrivate()
        self.entries    = entries
        self.attributes = attributes
        self.functions  = functions
        self.showCount  = show_number
        self.start      = start_number
        self.count      = count

    def buildLayout(self):
        pass

    def updateLayout(self, manager):
        # update attributes
        # update entries
        # update info label
        pass