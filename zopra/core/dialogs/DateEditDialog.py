############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
# \file ZMOMDialogs.py
__revision__ = '0.1'

#
# PyHtmlGUI Import
#
from PyHtmlGUI.kernel.hgTable        import hgTable

from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgNEWLINE
from PyHtmlGUI.widgets.hgTextEdit    import hgTextEdit
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgTabWidget   import hgTabWidget
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox
from PyHtmlGUI.widgets.hgFrame       import hgFrame
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton
from PyHtmlGUI.widgets.hgDateEdit    import hgDate, hgDateEdit
from PyHtmlGUI.widgets.hgGroupBox    import hgGroupBox

#
# ZopRA Imports
#
from zopra.core.dialogs.Dialog       import Dialog


class ZMOMDateEditDialog(Dialog):
    """\class ZMOMDateEditDialog
    """
    _className  = 'ZMOMDateEditDialog'
    _classType  = Dialog._classType + [_className]

    DELIMITER = 'delimiter'
    NULL      = 'null'
    FILE      = 'file'
    TABLE     = 'table'
    NEXT      = ' Next '
    TAB       = '\\t'
    NEWLINE   = '\\n'
    DONT_CARE = '_don\'t care_'

    # Recurrence Rules
    REC_DAILY   = 'Daily'
    REC_WEEKLY  = 'Weekly'
    REC_MONTHLY = 'Monthly'
    REC_YEARLY  = 'Yearly'

    def __init__(self, manager,
                       parent = None,
                       name   = _className,
                       flags  = Dialog.Embedded ):
        """\brief Constructs a ZMOMDateEditDialog object."""
        Dialog.__init__( self, manager,
                                   'Import - %s' % manager.getTitle(),
                                   parent,
                                   name,
                                   flags )

        # Dates
        self._start_label = hgLabel()
        self._end_label   = hgLabel()
        self.setStart()
        self.setEnd()

        # Working fields
        self._purpose = hgTextEdit( flags = hgTextEdit.MULTILINE)
        self._purpose.setSize(40, 8)

        self._withRecurrence = hgCheckBox('Enable recurrence')

        self._initTabWidget()
        self._setRecurrenceRuleTable(self.REC_DAILY)


    def _initTabWidget(self):

        # generalWindow
        generalWindow = hgFrame()
        generalWindow.add( '' )

        generalTable = hgTable()
        generalTable._old_style = False
        generalTable[0, 0] = 'Purpose of:'
        generalTable[0, 1] = self._purpose

        generalTable[1, 0] = 'Start:'
        generalTable[1, 1] = self._start_label
        generalTable[2, 0] = 'End:'
        generalTable[2, 1] = self._end_label

        generalTable[10, 0] = hgPushButton(self.NEXT)

        # checkbox recurrence enabled
        recWindow = hgFrame()
        recWindow.add( self._withRecurrence )
        recWindow.add( hgNEWLINE )

        # Appointment Time
        timeFrame = hgGroupBox(title = 'Appointment Time')
        timeFrame.add( 'From: ')
        timeFrame.add( self._start_label.getText() )
        timeFrame.add( '   To: ')
        timeFrame.add( self._end_label )
        recWindow.add( timeFrame)

        # Recurrence Rule Window / Buttons
        ruleFrame = hgGroupBox(title = 'Recurrence Rule')
        ruleFrame.add( hgPushButton( self.REC_DAILY   ) )
        ruleFrame.add( hgNEWLINE                        )
        ruleFrame.add( hgPushButton( self.REC_WEEKLY  ) )
        ruleFrame.add( hgNEWLINE                        )
        ruleFrame.add( hgPushButton( self.REC_MONTHLY ) )
        ruleFrame.add( hgNEWLINE                        )
        ruleFrame.add( hgPushButton( self.REC_YEARLY  ) )

        # Recurrence Rule Table
        self._recCount     = hgTextEdit()
        self._recCount.setSize(5)

        self._recRuleTable = hgTable()
        self._recRuleTable._old_style = False
        self._recRuleTable[0, 0] = 'Recur every'
        self._recRuleTable[0, 1] = self._recCount


        # Recurrence Rule Layout
        table = hgTable()
        table._old_style = False
        table[0, 0] = ruleFrame
        table[0, 1] = self._recRuleTable
        table.setAlignment('left', 'center')
        recWindow.add( table )

        # Recurrence Range
        rangeFrame = hgGroupBox(title = 'Recurrence Range')
        rangeFrame.add( 'Begins on ' )
        rangeFrame.add( self._start_label.getText() )
        rangeFrame.add( hgNEWLINE )
        rangeFrame.add( hgRadioButton( 1,
                                       'No ending date',
                                       True,
                                       name = 'rec_range') )
        rangeFrame.add( hgNEWLINE )
        rangeFrame.add( hgRadioButton(2, 'End after ', name = 'rec_range') )
        rangeFrame.add( hgTextEdit() )
        rangeFrame.add( ' occurence(s)')
        rangeFrame.add( hgNEWLINE  )
        rangeFrame.add( hgRadioButton(3, 'End by ', name = 'rec_range') )
        rangeFrame.add( hgDateEdit() )
        recWindow.add( rangeFrame )

        # tabWidget
        self._tabWidget = hgTabWidget(self.getForm())
        self._tabWidget.addTab( generalTable,    'General' )
        self._tabWidget.addTab( recWindow,       'Recurrence' )


    def _setRecurrenceRuleTable(self, rule):
        """\brief Builds the rule table dependend on the rule."""
        table = self._recRuleTable

        # Daily Rule
        if rule == self.REC_DAILY:
            table[0, 2] = 'day(s)'

        # Weekly Rule
        elif rule == self.REC_WEEKLY:
            table[0, 2] = 'week(s) on:'

        # Month Rule
        elif rule == self.REC_MONTHLY:
            table[0, 2] = 'month(s) on:'

        # Year Rule
        elif rule == self.REC_YEARLY:
            table[0, 2] = 'year(s) on:'


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""
        key = self._tabWidget.getName() + '_setCurrentTab'
        if REQUEST.has_key(key):
            self._tabWidget.setCurrentPage( int(REQUEST[key]) )

        return Dialog.execDlg(self, manager, REQUEST)


    def _foundWidgetFunction(self, widget, value):
        """\brief Catch the widgets."""
        if isinstance (widget, hgPushButton):

            # Tab Navigation
            if value == self.NEXT:
                tabWidget = self._tabWidget
                tabWidget.setCurrentPage( tabWidget.getCurrentIndex() + 1 )

            # Recurrence Handling
            if value == self.REC_DAILY:
                self._setRecurrenceRuleTable(self.REC_DAILY)

            elif value == self.REC_WEEKLY:
                self._setRecurrenceRuleTable(self.REC_WEEKLY)

            elif value == self.REC_MONTHLY:
                self._setRecurrenceRuleTable(self.REC_MONTHLY)

            elif value == self.REC_YEARLY:
                self._setRecurrenceRuleTable(self.REC_YEARLY)
        else:
            Dialog._foundWidgetFunction(self, widget, value)

#
# Public Dialog Functions
#
    def setStart(self, date = hgDate.today(), time = None):
        """\brief Sets starting date and time for this event."""
        if time == None:
            time = [9, 0]

        self._start_date = date
        self._start_time = time
        self._start_label.setText( '%s %02i:%02i' % ( self._start_date,
                                                      self._start_time[0],
                                                      self._start_time[1] ) )


    def setEnd(self, date = hgDate.today(), time = None):
        """\brief Sets starting date and time for this event."""
        if time == None:
            time = [9, 0]

        self._end_date = date
        self._end_time = time
        self._end_label.setText( '%s %02i:%02i' % ( self._end_date,
                                                    self._end_time[0],
                                                    self._end_time[1] ) )
