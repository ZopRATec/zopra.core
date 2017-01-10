############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from types                           import StringTypes, \
                                            IntType,     \
                                            LongType,    \
                                            ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                       import E_PARAM_TYPE

from PyHtmlGUI.kernel.hgTable        import hgTable

from PyHtmlGUI.widgets.hgLabel       import hgLabel,   \
                                            hgSPACE,   \
                                            hgNEWLINE, \
                                            hgProperty
from PyHtmlGUI.widgets.hgTextEdit    import hgTextEdit
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgDateEdit    import hgDateChooser
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox
from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox
from PyHtmlGUI.widgets.hgTimeChooser import hgTimeChooser


#
# ZopRA Imports
#
from zopra.core.dialogs.Dialog       import Dialog


class TableEntryPrivate:
    """\class TableEntryPrivate"""

    def __init__(self):
        """\brief Constructs a TableEntryPrivate object."""
        # static information
        self.tableName   = None
        self.columnNames = None

        # dynamic information
        self.autoid      = None   # current autoid
        self.row         = None   # current row
        self.count       = None   # current row count
        self.entry       = None   # current entry dictionary


class TableEntryDialog(Dialog):
    """\class TableEntryDialog

    \brief TableEntryDialog is a dialog for generic table entry handling.
    """
    _className = 'ZMOMTableEntryDialog'
    _classType = Dialog._classType + [_className]

    # functional labels
    BACK_ALL   = '|<'
    BACK_ONE   = '<'
    ENTRY_ID   = '$1'
    FOR_ALL    = '>|'
    FOR_ONE    = '>'
    NEW        = '>*'
    FORM_TABLE = '$2'
    GO         = 'Go'
    CURRENT_ID = '$3'
    HIDDEN_ID  = '$4'
    ROW_COUNT  = '$5'
    ADD        = 'Add'
    UPDATE     = 'Update'


    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
    # enum FunctionMode
    Disable          = 0x0000
    EnableNavigation = 0x0001   # dlg with navigation function
    EnableInsert     = 0x0002   # dlg with insert function
    EnableUpdate     = 0x0004   # dlg with change function
    EnableDelete     = 0x0008   # dlg with delete function
    EnableFunctions  = EnableInsert    | EnableUpdate | EnableDelete
    EnableAll        = EnableFunctions | EnableNavigation
    FunctionMode     = [ Disable,      EnableNavigation, EnableInsert,
                         EnableUpdate, EnableDelete,     EnableFunctions,
                         EnableAll ]

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def setCurrentAutoid(self, autoid):
        """\brief Sets the currentAutoid property."""
        assert autoid == None or isinstance(autoid, IntType), \
               E_PARAM_TYPE % ('autoid', 'IntType or None', autoid)
        self.content.autoid = autoid

    def getCurrentAutoId(self):
        """\brief Returns the currentAutoid property."""
        return self.content.autoid

    currentAutoid = property(getCurrentAutoId, setCurrentAutoid)


    def getCurrentEntry(self):
        """\brief Extracts entry information from the dialog."""
        entry_dict = {}
        for item in self.content.columnNames:
            if item in self.columnOrder:
                obj = self.getForm().child( item )

                if isinstance(obj, hgLineEdit) or isinstance(obj, hgTextEdit):
                    entry_dict[item] = obj.getText()

                elif isinstance(obj, hgComboBox):
                    entry_dict[item] = obj.getCurrentItem()

                elif isinstance(obj, hgCheckBox):
                    entry_dict[item] = obj.isChecked()

                elif isinstance(obj, hgDateChooser):
                    entry_dict[item] = str( obj.getDate() )

                elif isinstance(obj, hgTimeChooser):
                    entry_dict[item] = str( obj.getTime() )

                else:
                    entry_dict[item] = 'NULL'

#             else:
#                 entry_dict[item] = self.content.entry[item]


        return entry_dict

    def cleanCurrentEntry(self):
        """\brief Removes old information form the dialog"""
        for item in self._column_list:
            obj = self.getForm().child( item )

            if isinstance(obj, hgLineEdit) or isinstance(obj, hgTextEdit):
                obj.setText('')

            elif isinstance(obj, hgComboBox):
                obj.setCurrentValue('NULL')

            elif isinstance(obj, hgCheckBox):
                obj.setChecked( False )

            elif isinstance(obj, hgDateChooser):
                obj.setDate( obj.currentDate() )

            elif isinstance(obj, hgTimeChooser):
                obj.setTime( obj.currentTime() )

    currentEntry = property(getCurrentEntry, None, cleanCurrentEntry)


    def setCurrentRow(self, row):
        """\brief Sets the currentRow property to \a row.

        The property currentRow defines which entry is the actual one.
        """
        assert isinstance(row, IntType) or isinstance(row, LongType), \
               E_PARAM_TYPE % ('row', 'IntType or LongType', row)

        if self.content.row != row:

            if row < self.first_row:
                self.content.row = self.first_row

            elif row > self.content.count + 1:
                self.content.row = self.content.count

            else:
                self.content.row = row

            # update form
            self.getForm().child( self.CURRENT_ID ).text = self.content.row

    def getCurrentRow(self):
        """\brief Returns the currentRow property."""
        return self.content.row

    currentRow = property(getCurrentRow, setCurrentRow)


    def setLastRow(self, row):
        """\brief Sets the lastRow property to \a row."""
        assert isinstance(row, IntType) or isinstance(row, LongType), \
               E_PARAM_TYPE % ('row', 'IntType or LongType', row)


        if self.content.count != row:

            self.content.count = row
            self.getForm().child( self.ROW_COUNT ).text = self.content.count

    def getLastRow(self):
        """\brief Returns the lastRow property."""
        return self.content.count

    lastRow = property(getLastRow, setLastRow)


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__(self, manager, tablename):
        Dialog.__init__(self, manager, tablename)

        assert isinstance(tablename, StringTypes), \
               E_PARAM_TYPE % ('tablename', 'StringTypes', tablename)

        # flags
        self.flags = self.EnableAll

        # private
        self.content             = TableEntryPrivate()
        self.content.tableName   = tablename

        # table information
        table      = self.getTable(manager)
        assert table, 'Table [%s] not found.' % tablename

        self.content.columnNames = table.tabledict.keys()

        # build a column dict
        self._column_list = self.content.columnNames
        self._column_dict = {}
        for name in self.content.columnNames:
            self._column_dict[ name ] = table.tabledict[name]

        # deprecated but didnt want to remove all columnOrder Refs
        self.columnOrder = self.content.columnNames

        self._go          = None
        self.first_row    = 1
        self.newEntry     = False
        self.isAccepted   = False
        rowCount          = table.getRowCount()

        self.init( manager )

        self.content.autoid = 0
        self.setLastRow(0)
        if rowCount:
            self.setCurrentRow(1)
            self.setUpdateMode()
            self.setEntry( manager )

        else:
            self.setCurrentRow(0)
            self.setNewMode()


    def init(self, manager):
        """\brief Initialize the dialogs design."""
        form = self.getForm()

        # build buttons
        form.add( hgLabel('Dataset: ')                         )
        form.add( hgProperty('_table', self.content.tableName) )

        btn = hgPushButton(self.BACK_ALL)
        btn.setToolTip('Go to first entry.')
        btn.connect(btn.clicked, self.goToFirst)
        btn.connect(btn.clicked, self.setUpdateMode)
        form.add( btn )

        btn = hgPushButton(self.BACK_ONE)
        btn.setToolTip('Go to previous entry.')
        btn.connect(btn.clicked, self.goOneBack)
        btn.connect(btn.clicked, self.setUpdateMode)
        form.add( btn )

        test = hgLabel( name = self.CURRENT_ID )
        test.setToolTip('Your current entry.')
        form.add( test )

        btn = hgPushButton(self.FOR_ONE, name = self.FOR_ONE)
        btn.setToolTip('Go to next entry.')
        btn.connect(btn.clicked, self.goOneFor)
        btn.connect(btn.clicked, self.setUpdateMode)
        form.add( btn )

        btn = hgPushButton(self.FOR_ALL)
        btn.setToolTip('Go to last entry.')
        btn.connect(btn.clicked, self.goToLast)
        btn.connect(btn.clicked, self.setUpdateMode)
        form.add( btn )

        btn = hgPushButton(self.NEW, name = self.NEW)
        btn.setToolTip('Create new entry.')
        btn.connect(btn.clicked, self.goNew)
        btn.connect(btn.clicked, self.setNewMode)
        form.add( btn )

        goToEdit = hgLineEdit( name = self.ENTRY_ID )
        goToEdit.setToolTip( 'Enter a valid entry number to jump there. ' + \
                             'You have to press the Go Button.')
        goToEdit.connect( goToEdit.textChanged, self.goTo )

        goBtn = hgPushButton( self.GO )
        goBtn.setToolTip('Go to specified entry.')

        form.add( hgSPACE                          )
        form.add( ' of '                           )
        form.add( hgLabel( name = self.ROW_COUNT ) )
        form.add( hgSPACE                          )
        form.add( hgSPACE                          )
        form.add( '|'                              )
        form.add( hgSPACE                          )
        form.add( hgSPACE                          )
        form.add( goToEdit                         )
        form.add( goBtn                            )
        form.add( hgNEWLINE                        )
        form.add( '<hr/>'                          )

        table = hgTable( name = self.FORM_TABLE )
        table._old_style = False

        updBtn = hgPushButton( self.UPDATE, name = self.UPDATE )
        updBtn.setToolTip('Updates the current entry in the database.')
        updBtn.connect( updBtn.clicked, self.setAccepted )

        addBtn = hgPushButton( self.ADD,    name = self.ADD    )
        addBtn.setToolTip('Adds the new entry to the database.')
        addBtn.connect( addBtn.clicked, self.setAccepted )

        form.add( table )
        form.add( updBtn )
        form.add( addBtn )

        self.updateLayout( manager )


    def updateLayout(self, manager):
        """\brief Updates the layout of the content."""
        # get table
        table = self.child(self.FORM_TABLE)
        table.emptyTable()

        tableobj = self.getTable(manager)

        # for all columns
        for index, column in enumerate(self.columnOrder):

            # column label
            table[index, 0] = tableobj.getLabelWidget(column)

            # column edit field
            col_type = self._column_dict[column]['TYPE']

            if col_type == 'string' or \
               col_type == 'int':
                table[index, 1] = hgLineEdit( name = column )
                table[index, 1].setSize(50)

            elif col_type == 'date':
                table[index, 1] = hgDateChooser( name = column )

            elif col_type == 'singlelist' or col_type == 'multilist':
                _list  = manager.listHandler.getList(tableobj.tablename, column)
                widget = _list.getWidget()
                table[index, 1] = widget

            elif col_type == 'memo':
                table[index, 1] = hgTextEdit(  name   = column,
                                               flags  = hgTextEdit.MULTILINE )
                table[index, 1].setSize(50, 5)


    def getTable(self, manager):
        """\brief Returns the tabel object from the manager."""
        return manager.tableHandler.get( self.content.tableName )


    def setEntry(self, manager):
        """\brief Sets the current entry."""
        # table information
        dbTable = self.getTable(manager)
        if dbTable:

            # get entry from currentRow
            descr_dict = {}
            entry      = dbTable.getEntryList( 1, self.currentRow - 1)
            if entry:
                descr_dict         = entry[0]
                self.setCurrentAutoid( int( descr_dict['autoid'] ) )

            self.content.entry = descr_dict
            self._fillInputFields(manager)

        self.getForm().setInvalid()


    def _fillInputFields(self, manager):
        """\brief Fills the data into the widgets."""

        # get table
        table = self.child(self.FORM_TABLE)

        # build all input fields
        for index, item in enumerate(self.columnOrder):

            widget  = table[index, 1]
            if widget and hasattr(widget, '_classType'):

                content = self.content.entry.get(item)
                if content is None:
                    continue

                if widget._className == 'hgLineEdit' or \
                   widget._className == 'hgTextEdit' or \
                   widget._className == 'hgDateEdit':
                    widget.setText( str(content) )

                elif widget._className == 'hgDateChooser':
                    if content != '':
                        widget.setDate( content )

                elif widget._className == 'hgTimeChooser':
                    widget.setTime( content )

                elif widget._className == 'hgComboBox':

                    ## hmmm, ugly -> should not build widget every time
                    ## but can't get information about list changes from here
                    row, col = table.getIndexOfObj(widget)
                    _list    = manager.listHandler.getList(self.content.tableName, widget.getName())
                    widget   = _list.getWidget( with_null = True )
                    table[row, col] = widget

                    if content:
                        widget.setCurrentValue( content )
                    else:
                        widget.setCurrentItem( 0 )

    def _foundWidgetFunction(self, widget, value):
        """\reimp"""

        # drop down
        if isinstance(widget, hgComboBox):
            if value and value != 'NULL':
                widget.setCurrentItem( int(value) )
            else:
                widget.setCurrentValue( 'NULL' )

        else:
            Dialog._foundWidgetFunction(self, widget, value)


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""

        # update row count
        self.setLastRow( self.getTable(manager).getRowCount() )

        # process events
        Dialog.execDlg(self, manager, REQUEST)

        # adds or updates entries
        if self.isAccepted:
            self.isAccepted = False
            table           = manager.tableHandler[self.content.tableName]

            # new entry accepted
            if self.newEntry:
                table.addEntry( self.currentEntry )
                self.setLastRow( self.getTable(manager).getRowCount() )
                self.setCurrentRow( self.content.count )
                self.setUpdateMode()

            # old entry updated
            else:
                table.updateEntry( self.currentEntry, self.currentAutoid )

        # jumps with go
        elif self._go:
            self.setCurrentRow( self._go )
            self._go        = None

        # cleanup settings
        self.setEntry(manager)


    def setColumnOrder(self, order_list, manager):
        """\brief Sets the column order according to \a order_list."""
        assert isinstance(order_list, ListType), \
               E_PARAM_TYPE % ('order_list', 'ListType', order_list)

        self._column_list = order_list
        self.updateLayout( manager )

    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################
    def goTo(self, toId):
        """\brief Jumps to the row given by \a toId."""
        if toId:
            try:
                self._go = int(toId)
                self.getForm().child(self.ENTRY_ID).text = ''
            except ValueError:
                if __debug__:
                    error  = '[Error] ZMOMTableEntryDialog.goTo: '
                    error += 'Could not convert toId[%s] into IntType' % toId
                    print error


    def goToFirst(self):
        """\brief Jumps to the first entry."""
        self.setCurrentRow( self.first_row )


    def goToLast(self):
        """\brief Jumps to the last entry."""
        self.setCurrentRow( self.content.count )


    def goOneBack(self):
        """\brief Goes one entry back."""
        self.setCurrentRow( self.content.row - 1 )


    def goOneFor(self):
        """\brief Goes one entry for."""
        if self.content.row < self.content.count:
            self.setCurrentRow( self.content.row + 1 )


    def goNew(self):
        """\brief Goes for a new entry."""
        self.setCurrentRow( self.content.count + 1 )


    def setUpdateMode(self):
        """\brief Set the dialog mode to change for the actual widget."""
        self.newEntry   = False
        self.child( self.ADD     ).setDisabled()
        self.child( self.UPDATE  ).setEnabled()
        self.child( self.FOR_ONE ).setEnabled()


    def setNewMode(self):
        """\brief Sets the mode to add entry."""
        self.newEntry   = True
        self.child( self.ADD      ).setEnabled()
        self.child( self.UPDATE   ).setDisabled()
        self.child( self.FOR_ONE  ).setDisabled()


    def setAccepted(self):
        """\brief Sets the accepted state."""
        self.isAccepted = True
