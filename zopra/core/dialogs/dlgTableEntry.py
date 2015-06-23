##############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                      #
#    webmaster@ingo-keller.de                                                #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################
from types                           import IntType,     \
                                            LongType,    \
                                            ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                       import E_PARAM_TYPE,       \
                                            E_PARAM_FAIL
from PyHtmlGUI.dialogs.hgDialog      import hgDialog

from PyHtmlGUI.kernel.hgTable        import hgTable

from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox
from PyHtmlGUI.widgets.hgDateEdit    import hgDateChooser
from PyHtmlGUI.widgets.hgHBox        import hgHBox
from PyHtmlGUI.widgets.hgLabel       import hgLabel
from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgTextEdit    import hgTextEdit
from PyHtmlGUI.widgets.hgTimeChooser import hgTimeChooser
from PyHtmlGUI.widgets.hgValidator   import hgIntValidator,     \
                                            hgDoubleValidator


#
# ZMOM Imports
#
from zopra.core.dialogs.guiHandler   import guiHandler
from zopra.core.widgets.zraNavBar    import zraNavBar


class dlgTableEntryPrivate:
    """\class dlgTableEntryPrivate"""

    def __init__(self):
        """\brief Constructs a dlgTableEntryPrivate object."""
        # static information
        self.tableName   = None
        self.columnNames = None

        # dynamic information
        self.autoid      = 0      # current autoid
        self.row         = None   # current row
        self.count       = None   # current row count
        self.entry       = None   # current entry dictionary
        self.mode        = None   # current mode of the dialog


class dlgTableEntry(hgDialog, guiHandler):
    """\class dlgTableEntry

    \brief dlgTableEntry is a dialog for generic table entry handling.
    """
    _className = 'dlgTableEntry'
    _classType = hgDialog._classType + [_className]

    # functional labels
    EntryId   = '$1'
    FormTable = '$2'
    HiddenId  = '$4'

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

    # enum Buttons
    Add              = 0
    Update           = 1
    Delete           = 2
    Cancel           = 3
    Buttons          = [ Add, Update, Delete, Cancel ]

    # enum Mode
    Add              = 0
    Update           = 1
    Delete           = 2
    Mode             = [ Add, Update, Delete ]

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def setCurrentAutoid(self, autoid):
        """\brief Sets the currentAutoid property."""
        assert self.checkType('autoid', autoid, IntType, True)
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
                obj = self.child( item )

                if isinstance(obj, hgLineEdit) or isinstance(obj, hgTextEdit):
                    entry_dict[item] = obj.getText()

                elif isinstance(obj, hgComboBox):
                    if obj.getCurrentItem() > -1:
                        entry_dict[item] = obj.getCurrentItem()

                    else:
                        entry_dict[item] = 'NULL'

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
            obj = self.child( item )

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


    def setMode(self, mode):
        """\brief Sets the mode property to \a mode.

        The property mode defines wether the dialog is in the add or update
        mode.
        """
        assert mode in self.Mode, \
               E_PARAM_TYPE % ( 'mode', 'dlgTableEntry.Mode', mode )

        if self.content.mode == mode:
            return

        self.content.mode = mode

        if mode == self.Add:
            self.buttons[ self.Add    ].setEnabled()
            self.buttons[ self.Update ].setDisabled()
            self.buttons[ self.Delete ].setDisabled()

            self.navBar.buttons[ zraNavBar.NextLine ].setDisabled()
            self.navBar.buttons[ zraNavBar.NextPage ].setDisabled()
            self.navBar.buttons[ zraNavBar.Last     ].setDisabled()

        elif mode == self.Update:
            self.buttons[ self.Add    ].setDisabled()
            self.buttons[ self.Update ].setEnabled()
            self.buttons[ self.Delete ].setEnabled()

            self.navBar.buttons[ zraNavBar.NextLine ].setEnabled()
            self.navBar.buttons[ zraNavBar.NextPage ].setEnabled()
            self.navBar.buttons[ zraNavBar.Last     ].setEnabled()

    def getMode(self):
        """\brief Returns the mode property."""
        return self.content.mode

    mode = property(getMode, setMode)


    def setCurrentRow(self, row):
        """\brief Sets the currentRow property to \a row.

        The property currentRow defines which entry is the actual one.
        """
        assert self.checkType( 'row', row, [IntType, LongType] )
        if self.content.row != row:
            self.content.row = row

            # otherwise we don't get
            self.setMode( self.Update )

    def getCurrentRow(self):
        """\brief Returns the currentRow property."""
        return self.content.row

    currentRow = property(getCurrentRow, setCurrentRow)


    def setLastRow(self, row):
        """\brief Sets the lastRow property to \a row."""
        assert self.checkType( 'row', row, [IntType, LongType] )
        if self.content.count != row:
            self.content.count = row

            if row > 0:
                self.navBar.setRange( 1, int(row) )
            else:
                self.navBar.setRange( 0, 0   )


    def getLastRow(self):
        """\brief Returns the lastRow property."""
        return self.content.count

    lastRow = property(getLastRow, setLastRow)

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict):
        """\brief Constructs a dlgTableEntry.

        param_dict keys:
            $table - tablename (required)
            $row   - set to row (optional)

        param_dict is only relevant for object instantiation.
        """
        hgDialog.__init__(self)
        guiHandler.__init__(self)

        self.content = dlgTableEntryPrivate()

        # check table presents
        tableName = param_dict.get('$table')
        if tableName == None:
            self.initError( 1 )

        else:
            self.setCaption( 'Table - %s' % tableName )
            self.content.tableName = tableName
            table                  = self.getTable(manager)

            # check table information
            if table == None:
                self.initError( 2 )

            else:
                self._go        = False
                self.isAccepted = False
                self.flags      = self.EnableAll
                self.buttons    = [ None ] * len( self.Buttons )
                self.navBar     = zraNavBar( 0, 0 )

                # build a column dict
                self.content.columnNames = table.tabledict.keys()
                self._column_list        = self.content.columnNames
                self._column_dict        = {}
                for name in self.content.columnNames:
                    self._column_dict[ name ] = table.tabledict[name]

                # column order is deprecated (and there is no way to get it)
                self.columnOrder = self.content.columnNames # which is random

                self.initLayout()
                self.updateLayout( manager )

                self.setLastRow( 0 )
                if table.getRowCount() > 0:
                    self.setCurrentRow( int( param_dict.get('$row', 1) ) )
                    self.setMode( self.Update )

                else:
                    self.setCurrentRow( 0 )
                    self.setMode( self.Add )

                # navigation buttons
                self.connect( self.navBar.valueChanged, self.setCurrentRow )

                # new button
                self.connect( self.navBar.buttons[zraNavBar.New].clicked,
                              self.setNewMode )
                self.connect( self.navBar.buttons[zraNavBar.Go].clicked,
                              self.setGoMode )


    def initError(self, num):
        """\brief Initialise the dialog with error message."""
        if num == 1:
            self.add( 'Missing table name.' )

        elif num == 2:
            self.add( 'Table [%s] not found.' % self.content.tableName )


    def initLayout(self):
        """\brief Initialise the dialogs design."""

        # create widgets
        table = hgTable( name = self.FormTable )
        table._old_style = False

        btn = hgPushButton( 'Update' )
        btn.setToolTip('Updates the current entry in the database.' )
        btn.connect( btn.clicked, self.setAccepted )
        self.buttons[self.Update] = btn

        btn = hgPushButton( 'Add' )
        btn.setToolTip('Adds the current entry to the database.' )
        btn.connect( btn.clicked, self.setAccepted   )
        self.buttons[self.Add] = btn

        btn = hgPushButton( 'Delete' )
        btn.setToolTip('Delete the current entry from the database.' )
        btn.connect( btn.clicked, self.setAccepted   )
        btn.connect( btn.clicked, self.setDeleteMode )
        self.buttons[self.Delete] = btn

        btn = hgPushButton( 'Cancel' )
        btn.setToolTip('Cancel the dialog.' )
        btn.connect( btn.clicked, self.reject )
        self.buttons[self.Cancel] = btn

        # layout the widgets
        box  = hgHBox()
        box.add( hgLabel('Dataset: ') )
        box.add( self.navBar          )

        self.add( box                       )
        self.add( '<hr/>'                   )
        self.add( table                     )
        self.add( '<hr/>'                   )
        self.add( self.buttons[self.Add]    )
        self.add( self.buttons[self.Update] )
        self.add( self.buttons[self.Delete] )
        self.add( self.buttons[self.Cancel] )


    def updateLayout(self, manager):
        """\brief Updates the layout of the content."""
        # get table
        table = self.child(self.FormTable)
        table.emptyTable()

        # for all columns
        for index, column in enumerate(self.columnOrder):

            tobj = manager.tableHandler[self.content.tableName]
            # column label
            table[index, 0] = tobj.getLabelWidget(column)

            # column edit field
            col_type = self._column_dict[column]['TYPE']

            if   col_type == 'string':
                table[index, 1] = hgLineEdit( name = column )
                table[index, 1].setSize(50)

            elif col_type == 'int':
                table[index, 1] = hgLineEdit( name = column )
                table[index, 1].setSize(50)
                table[index, 1].setValidator( hgIntValidator() )

            elif col_type == 'float':
                table[index, 1] = hgLineEdit( name = column )
                table[index, 1].setSize(50)
                table[index, 1].setValidator( hgDoubleValidator() )

            elif col_type == 'date':
                table[index, 1] = hgDateChooser( name = column )

            elif col_type == 'bool':
                table[index, 1] = hgCheckBox( name = column )

            elif col_type == 'singlelist' or col_type == 'multilist':
                _list  = manager.listHandler.getList(self.content.tableName, column)
                widget = _list.getWidget(with_null    = True)
                table[index, 1] = widget

            elif col_type == 'memo':
                table[index, 1] = hgTextEdit(  name   = column,
                                               flags  = hgTextEdit.MULTILINE )
                table[index, 1].setSize(50, 5)


    def getTable(self, manager):
        """\brief Returns the tabel object from the manager."""
        assert manager, E_PARAM_FAIL % 'manager'
        return manager.tableHandler.get( self.content.tableName )


    def setEntry(self, manager):
        """\brief Sets the current entry."""
        assert manager, E_PARAM_FAIL % 'manager'

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


    def _fillInputFields(self, manager):
        """\brief Fills the data into the widgets."""
        # get table
        table = self.child(self.FormTable)

        # build all input fields
        for index, item in enumerate(self.columnOrder):

            widget  = table[index, 1]
            if widget and hasattr(widget, '_className'):

                content = self.content.entry.get(item)
                if content == None:
                    continue

                if widget._className == 'hgLineEdit' or \
                   widget._className == 'hgTextEdit' or \
                   widget._className == 'hgDateEdit':
                    widget.setText( str(content) )

                elif widget._className == 'hgCheckBox':
                    widget.setChecked( content )

                elif widget._className == 'hgDateChooser':
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


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""

        # stop working if no table name given
        if not self.content.tableName:
            return

        # update row count
        self.setLastRow ( self.getTable(manager).getRowCount() )

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        # adds or updates entries
        if self.isAccepted:
            self.isAccepted = False
            table           = manager.tableHandler[self.content.tableName]

            # new entry accepted
            if self.mode == self.Add:
                table.addEntry( self.currentEntry )
                self.setUpdateMode ()
                self.setLastRow    ( self.getTable(manager).getRowCount() )
                self.setCurrentRow ( self.lastRow )

            # old entry updated
            elif self.mode == self.Update:
                table.updateEntry( self.currentEntry, self.currentAutoid  )

            # old entry deleted
            elif self.mode == self.Delete:
                table.deleteEntry( self.currentAutoid )
                self.setUpdateMode ()
                self.setLastRow    ( self.getTable(manager).getRowCount() )
                self.setCurrentRow ( self.currentRow - 1 )

        # jumps with go
        elif self._go:
            self.goTo()

        # cleanup settings
        self.setEntry( manager )


    def setColumnOrder(self, order_list, manager):
        """\brief Sets the column order according to \a order_list."""
        assert self.checkType( 'order_list', order_list, ListType )
        if self.columnOrder != order_list:
            self.columnOrder = order_list
            self.updateLayout( manager )


    def goTo(self):
        """\brief Go to specified row."""
        # in case of empty field we do nothing
        if not self.navBar.go.getText():
            return

        # otherwise try to get a new row number
        try:
            new_row = int( self.navBar.go.getText() )
        except ValueError:
            if __debug__:
                error  = '[Error] dlgTableEntryDialog.setGoMode: '
                error += 'Could not convert [%s] into IntType' % \
                         self.navBar.go.getText()
                raise ValueError( error )

            else:
                error  = '[Error] Expected line number, '
                error += 'but got ' + self.navBar.go.getText()
                raise ValueError( error )

        # go to our new row
        self.setCurrentRow( new_row )
        self.navBar.setValue( new_row )
        self._go = False


    def setParam(self, key, value, manager):
        """\reimp"""
        if self.content.tableName and self.content.tableName in key:
            parameter = key.split('_')[1]

            if parameter == 'order':
                self.setColumnOrder( value.split(' '), manager )


    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################
    def setAccepted(self):
        """\brief Sets the accepted state."""
        self.isAccepted = True


    def setNewMode(self):
        """\brief Sets the mode to add entry.

        Default behaviour is that the new entry in the dialog will look like
        the last shown entry. So its a kind of copy entry mechanism.
        """
        self.setMode( self.Add )


    def setUpdateMode(self):
        """\brief Set the dialog mode to update for the actual entry."""
        self.setMode( self.Update )


    def setDeleteMode(self):
        """\brief Set the dialog mode to delete for the actual entry."""
        self.setMode( self.Delete )


    def setGoMode(self):
        """\brief Sets the go to line mode."""
        self._go = True