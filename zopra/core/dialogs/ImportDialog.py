############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#
# Python Language Imports
#
import os
import string
from types                           import ListType, StringType

#
# PyHtmlGUI Import
#
from PyHtmlGUI.kernel.hgTable        import hgTable
from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgSPACE, hgNEWLINE
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgTabWidget   import hgTabWidget
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox

from PyHtmlGUI.widgets.hgButtonGroup import hgButtonGroup
from PyHtmlGUI.widgets.hgGroupBox    import hgGroupBox
from PyHtmlGUI.widgets.hgHBox        import hgHBox
from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton
from PyHtmlGUI.widgets.hgVBox        import hgVBox

#
# ZopRA Imports
#
from zopra.core                      import ZM_PM
from zopra.core.dialogs.Dialog       import Dialog


class ImportDialog(Dialog):
    """\class ImportDialog"""
    _className  = 'ImportDialog'
    _classType  = Dialog._classType + [_className]

    Delimiter = 'delimiter'
    Null      = 'null'
    FILE      = 'file'
    TABLE     = 'table'
    NEXT      = ' Next '
    TAB       = '\\t'
    NEWLINE   = '\\n'
    DONT_CARE = '_don\'t care_'

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def setDelimiter(self, delimiter):
        """\brief Sets the delimiter property."""
        assert isinstance(delimiter, StringType), \
               self.E_PARAM_TYPE % ('delimiter', 'StringType', delimiter)

        if self.__delimiter != delimiter:
            self.__delimiter = delimiter
            self.child( self.Delimiter ).text = delimiter

    def getDelimiter(self):
        """\brief Returns the delimiter property."""
        return self.__delimiter

    delimiter = property(getDelimiter, setDelimiter)


    def setFileName(self, file_name):
        """\brief Sets the fileName property."""
        assert isinstance(file_name, StringType), \
               self.E_PARAM_TYPE % ('file_name', 'StringType', file_name)

        if self.__fileName != file_name:

            # clean up if we had a previous use of the dialog
            if self.__fileName:
                os.remove( self.__fileName )

            # set the new file name
            self.__fileName == file_name

    def getFileName(self):
        """\brief Returns the fileName property."""
        return self.__fileName

    fileName = property(getFileName, setFileName)


    def setNullValue(self, null_value):
        """\brief Sets the nullValue property."""
        assert isinstance(null_value, StringType), \
               self.E_PARAM_TYPE % ('null_value', 'StringType', null_value)

        if self.__nullValue != null_value:
            self.__nullValue == null_value
            self.child( self.Null ).text = null_value

    def getNullValue(self):
        """\brief Returns the nullValue property."""
        return self.__nullValue

    nullValue = property(getNullValue, setNullValue)


    def setTableNames(self, table_names):
        """\brief Sets the tableNames property."""
        assert isinstance(table_names, ListType), \
               self.E_PARAM_TYPE % ('table_names', 'ListType', table_names)

        if self.__tableNames != table_names:
            self.__tableNames = table_names
            self.__tableNames.sort()

            buttonGroup = self.child( 'tableNameGroup' )
            for tableName in self.__tableNames:
                radioButton = hgRadioButton( tableName,
                                             tableName,
                                             name = buttonGroup.getName() )
                buttonGroup.add( radioButton        )
                buttonGroup.add( hgLabel('<br>')    )

    def getTableNames(self):
        """\brief Returns the tableNames property."""
        return self.__tableNames

    tableNames = property(getTableNames, setTableNames)

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__(self, manager, parent = None):
        """\brief Constructs a ZMOMImportDialog object."""
        Dialog.__init__( self,
                         manager,
                        'Import - %s' % manager.getTitle(),
                         parent )

        # init variables
        self.__delimiter  = None
        self.__fileName   = None
        self.__nullValue  = None
        self.__tableNames = []
        self.__tabWidget  = None

        # init form
        self.__initTabWidget( manager )
        self.__resetDialog  ( manager )

        #
        # Old Stuff
        #
        self._file        = None
        self._table       = None
        self._column_list = []
        self.query        = None


    def __initTabWidget(self):
        """\brief Creates the dialog."""

        # selectBox
        selectBox = hgGroupBox()
        selectBox.setFrameStyle( selectBox.NoFrame | selectBox.Plain   )
        hgLabel( 'Import file',                     parent = selectBox )
        hgLabel( '<input type="file" name="file">', parent = selectBox )

        hgButtonGroup( title  = ' Add data to table ',
                       parent = selectBox,
                       name   = 'tableNameGroup' )

        hgPushButton( self.NEXT, parent = selectBox )

        # parameterBox
        parameterBox = hgGroupBox()

        hBox = hgHBox( parameterBox )
        vBox = hgVBox( hBox         )
        hgLabel    ( 'Delimiter / Separator',  parent = vBox )
        hgLabel    ( 'Null Value',             parent = vBox )

        vBox = hgVBox( hBox )
        hgLineEdit ( name = self.Delimiter,    parent = vBox )
        hgLineEdit ( name = self.Null,         parent = vBox )

        hBox = hgHBox( parameterBox )
        hgPushButton( self.CANCEL, parent = hBox )
        hgPushButton( self.NEXT,   parent = hBox )

        # tabWidget
        self.__tabWidget = hgTabWidget()
        self.__tabWidget.addTab( selectBox,    'File'      )
        self.__tabWidget.addTab( parameterBox, 'Parameter' )
        self.__tabWidget.addTab( hgGroupBox(), 'Columns'   )
        self.__tabWidget.addTab( hgGroupBox(), 'Results'   )
        self.getForm().add(self.__tabWidget)


    def __resetDialog(self, manager):
        """\brief Resets the dialog to the default values."""

        # set default values
        self.__tabWidget.setCurrentPage(0)
        self._file        = None
        self._table       = None
        self._column_list = []
        self.query        = None

        # set default values
        self.setDelimiter ( '\\t'                       )
        self.setEncode    ( self.EncodeMulti           )
        self.setFileName  ( ''                          )
        self.setNullValue ( ''                          )
        self.setTableNames( manager.tableHandler.keys() )


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""
        key = self.__tabWidget.getName() + '_setCurrentTab'
        if REQUEST.form.has_key(key):
            self.__tabWidget.setCurrentPage( int(REQUEST[key]) )

            if str(REQUEST[key]) == str(2):
                self._hitTab3()


        if REQUEST.form.has_key(self.TABLE):
            self._table = REQUEST[self.TABLE]

        if REQUEST.form.has_key(self.FILE):
            self._file = REQUEST[self.FILE]
            self._loadFile()

        Dialog.execDlg(self, manager, REQUEST)


    def _foundWidgetFunction(self, widget, value, manager):
        """\reimp"""
        if isinstance (widget, hgPushButton):
            widget.clicked()

            if value == self.OK:
                self._import(manager)
                self.__resetDialog()
                self.__tabWidget.setCurrentPage(3)

            if value == self.CANCEL:
                self.__resetDialog()

            if value == self.NEXT:
                nextTab = self.__tabWidget.getCurrentIndex() + 1
                self.__tabWidget.setCurrentPage( nextTab )

            if self.__tabWidget.getCurrentIndex() == 2:
                self._hitTab3()

            if self.__tabWidget.getCurrentIndex() == 3:
                self._hitTab4()

        elif isinstance (widget, hgLineEdit):
            widget.setText( value )

        elif isinstance (widget, hgComboBox):

            ##\todo 17.06.2004 if hgTable parent handling is fixed this code
            ##                 should be changed!!!
            col_list = self.getColumnList()
            col_name = col_list[int(value)]
            if col_name != self.DONT_CARE:
                self._column_list.append( col_name )


    def _loadFile(self):
        if self._file:
            name     = '/tmp/ZopRa_%s_%s.tmp' % ( self.name, id(self) )
            tmp_file = open( name, 'w' )
            line     = self._file.readline()

            while line:
                tmp_file.write ( line )
                line = self._file.readline()

            tmp_file.close()
            self.setFileName( name )
            os.chmod(self.__fileName, 0666)
            self._file      = None


    def _hitTab3(self):
        page      = self.__tabWidget.getPage()
        page.clear()

        # ok we have a file
        if self.__fileName:
            item_list = self.getColumnList()

            # show the first 5 lines of the file
            file    = open(self.__fileName, 'r')
            data    = []
            max_len = 0
            for i in xrange(10):
                line = file.readline()
                if line:
                    delimiter = self.child(self.Delimiter).text

                    # correct the escape sequences
                    if delimiter == self.TAB:
                        delimiter = '\t'
                    elif delimiter == self.NEWLINE:
                        delimiter = '\n'

                    entry  = string.split(line,  delimiter)
                    length = len(entry)

                    # only add lines with content
                    if length:
                        data.append( entry )

                        # if the actual line is longer we should keep
                        # that in mind
                        if length > max_len:
                            max_len = length

            # build header chooser
            col_table = hgTable()
            col_table._old_style = False
            for columns in xrange(max_len):

                # build the combobox for a special column
                comboBox              = hgComboBox()
                col_table[0, columns] = comboBox
                for index, item in enumerate(item_list):
                    comboBox.insertItem(item, index)

                # is the case if we have more columns in file then in table
                if not (columns > len(item_list)):
                    comboBox.setCurrentItem(columns)

            # insert data
            for i in xrange(10):
                if i < len(data):
                    for j in xrange( len(data[i]) ):
                        col_table[i +1, j] = data[i][j]


            page.add( col_table )
            page.add( hgPushButton(self.CANCEL) )
            page.add( hgSPACE   )
            page.add( hgPushButton(self.OK) )

        # hmmm, the user didn't upload a file
        else:
            link    = '?' + self.__tabWidget.getName() + '_setCurrentTab=0'
            message = 'You should upload a file. Please go to %s.'
            page.add( message % hgLabel('File', link) )


    def _hitTab4(self):
        pass


    def _import(self, manager):
        """\brief Do the import."""
        # build query
        query = ['COPY']
        query.append(manager.getId() + self._table)
        query.append('(')
        query.append( string.join(self._column_list, ', ') )
        query.append(')')
        query.append('FROM')
        query.append('\'%s\'' % self.__fileName)
        query.append('USING DelimiterS')
        query.append('\'%s\'' % self.child(self.Delimiter).text )

        query = string.join(query, ' ')

        # execute query
        result = manager.getManager(ZM_PM).executeDBQuery(query)

        page = self.__tabWidget.getPage(3)
        page.clear()

        # did we got an result ??? normaly not !
        if result:
            page.add( result    )
            page.add( hgNEWLINE )

        page.add( manager.tableHandler[self._table].getRowCount() )
        page.add( ' entries in the table.' )


    def getColumnList(self):
        if self._table:
            col_list = self._table_dict[self._table].keys()
            col_list.sort()

            # build item list
            column_list = []
            for key in col_list:
                column_list.append(key)
            column_list.append(self.DONT_CARE)
            return column_list
