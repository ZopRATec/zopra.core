############################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from types                                  import DictionaryType, \
                                                   IntType,        \
                                                   ListType,       \
                                                   TupleType
#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgLineEdit           import hgLineEdit

# for testing
from PyHtmlGUI.table.hgTableView            import hgTableView

from zopra.core.dialogs.Dialog              import Dialog


class dlgTableViewPrivate:
    """\class dlgTableViewPrivate going to replace
        ManagerPart.getTableEntryListHtml at some point
    """

    def __init__(self):
        """\brief Constructs a dlgTableViewPrivate object."""

        # static information
        self.tableName      = None
        self.columnNames    = None

        # dynamic information
        self.autoid         = None   # current autoid
        self.count          = None   # current row count
        self.entries        = None   # current entries dictionary
        self.start_number   = None   # current starting number of the view
        self.show_number    = None   # how many entries should be shown at once
        self.idfield        = None   # idfield of the table
        self.constraints    = None   # constraints supported by search
        self.contentOrder   = None   # how to order the results
        self.columnOrder    = None   # in which order the columns appear


class dlgTableView(Dialog):
    """\brief Event View """
    _className = "dlgTableView"
    _classType = Dialog._classType + [_className]

    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
    # enum ContentChange
    NoChange        = 0x0000
    ColumnNames     = 0x0001
    RowNames        = 0x0002
    Content         = 0x0004

    ContentChange   = [ NoChange, ColumnNames, RowNames, Content ]

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def setConstraints(self, constraints):
        """\brief Sets the constraints that entries have to match to show up
                  in this dialog.
        """
        assert isinstance( constraints, DictionaryType )
        if self.data.constraints == constraints:
            return None

        self.data.constraints = constraints
        self.contentChanged   = True


    def getConstraints(self):
        """\brief Returns the constraints property of this dialog."""
        return self.data.constraints

    constraints = property(getConstraints, setConstraints)


    def setColumnOrder(self, order_list):
        """\brief Sets the column order of the entries to the order_list."""
        assert isinstance( order_list, ListType  ) or \
               isinstance( order_list, TupleType )

        if self.data.columnOrder == order_list:
            return None

        self.data.columnOrder  = order_list

        # check content
        self.contentChanged = self.contentChanged | self.ColumnNames


    def getColumnOrder(self):
        """\brief Returns the column order property of this dialog.

        The property order is a list of strings with the column names.
        """
        return self.data.columnOrder

    columnOrder = property(getColumnOrder, setColumnOrder)


    def setContentOrder(self, order_list):
        """\brief Sets the order of the entries to the order_list."""
        assert isinstance( order_list, ListType  ) or \
               isinstance( order_list, TupleType )

        if self.data.contentOrder == order_list:
            return None

        self.data.contentOrder  = order_list
        self.contentChanged = self.contentChanged | self.Content

    def getContentOrder(self):
        """\brief Returns the content order property of this dialog.

        The property order is a list of strings with the column names.
        """
        return self.data.contentOrder

    contentOrder = property(getContentOrder, setContentOrder)


    def setShowNumber(self, show_number):
        """\brief Sets the number of shown entries."""
        assert isinstance(show_number, IntType)

        if self.data.show_number == show_number:
            return None

        # if we have already all data then we do not need to reload it
        if self.data.show_number < show_number:
            self.contentChanged = self.contentChanged | self.RowNames

        self.data.show_number = show_number

    def getShowNumber(self):
        """\brief Returns the number of shown entries."""
        return self.data.show_number

    showNumber = property(getShowNumber, setShowNumber)


    def setStartNumber(self, start_number):
        """\brief Sets the number of shown entries."""
        assert isinstance(start_number, IntType)

        if self.data.start_number == start_number:
            return None

        self.data.start_number = start_number
        self.contentChanged = self.contentChanged | self.RowNames

    def getStartNumber(self):
        """\brief Returns the number of shown entries."""
        return self.data.start_number

    startNumber = property(getStartNumber, setStartNumber)


    def getTableName(self):
        """\brief Returns the table name used by this dialog."""
        return self.data.tableName

    tableName = property(getTableName)


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict):
        """\brief Constructs a dlgPlateEditor."""
        Dialog.__init__( self )

        self.contentChanged   = self.Content | self.ColumnNames | self.RowNames

        # check table presents
        tableName = param_dict.get('$table')
        if tableName is None:
            self.initError()

        else:
            # setup dialog content
            db_table            = manager.tableHandler[tableName]
            self.data           = dlgTableViewPrivate()
            self.data.tableName = tableName
            self.data.idfield   = 'autoid'

            # order is deprecated, removed calls to ZMOMTable
            self.data.columnNames = db_table.keys()

            # fill default values
            self.setShowNumber( 20                     )
            self.setStartNumber( 0                     )
            self.setColumnOrder( self.data.columnNames )

            # setup dialog layout
            self.initLayout()



    def initError(self):
        """\brief Initialise the dialog with error message."""
        self.add( 'Missing table name.' )


    def initLayout(self):
        """\brief Initialise the dialogs layout"""
        self.setTitle( '%s - Table View' % self.data.tableName )

        # table widget
        table     = hgTableView( self.showNumber,
                                 len(self.data.columnNames),
                                 name = 'hg_table_view' )
        self.add( table )

        # footer
        self.add( self._ok     )
        self.add( self._cancel )

        # connections
        scrollBar = table.verticalScrollBar()
        self.connect( scrollBar.nextLine, self.scrollRowDown )
        self.connect( scrollBar.prevLine, self.scrollRowUp   )


    def execDlg(self, manager = None, REQUEST = None):
        """\reimp"""

        if self.data                        and \
           hasattr(self.data, 'tableName' ) and \
           self.data.tableName:

            Dialog.execDlg( self, manager, REQUEST )

            self.refreshContent(manager)


    def updateDataFromTable(self, manager):
        """\brief Updates the table properties"""
        table             = manager.tableHandler[self.data.tableName]
        self.data.count   = table.getRowCount()
        self.data.entries = table.getEntryList( self.showNumber,
                                                self.startNumber,
                                                self.data.idfield,
                                                self.constraints,
                                                self.contentOrder )

    def updateLayout(self):
        """\brief Updates the layout before showing the content."""
        pass


    def refreshContent(self, manager):
        """\brief Refreshs the content."""

        if self.contentChanged == self.NoChange:
            return None

        table    = self.child('hg_table_view')
        db_table = manager.tableHandler[self.tableName]

        # build column header new
        if self.contentChanged & self.ColumnNames:
            columnLabels = []
            for column in self.data.columnOrder:
                columnLabels.append( db_table.getLabel(column) )

            table.setColumnLabels( columnLabels )

        # build row header new
        if self.contentChanged & self.RowNames:
            rowLabels = []
            for i in xrange( self.startNumber,
                             self.startNumber + self.showNumber ):
                rowLabels.append( '%04d' % i )
            table.setRowLabels( rowLabels )

        # update content from database
        if self.contentChanged & self.RowNames:
            self.updateDataFromTable(manager)

        columnOrder   = self.columnOrder
        cellWidget    = table.cellWidget
        setCellWidget = table.setCellWidget
        entryCount    = len(self.data.entries)

        for row in xrange(self.showNumber):

            for col, column in enumerate(columnOrder):

                if row < entryCount:
                    item = self.data.entries[row]
                    widget = cellWidget( row, col )

                    if widget:
                        widget.setText( str(item[column]) )

                    else:
                        lineEdit = hgLineEdit()
                        lineEdit.setText( str(item[column]) )
                        setCellWidget( row, col, lineEdit )
                else:
                    setCellWidget( row, col, hgLineEdit() )

        self.contentChanged = self.NoChange

    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################
    def scrollRowDown(self):
        """\brief Scroll down"""
        if self.data.start_number < self.data.count:
            self.data.start_number += 1

    def scrollRowUp(self):
        """\brief Scroll up"""
        if self.data.start_number > 0:
            self.data.start_number -= 1
