############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
# TODO: Move to booking package
#
# PyHtmlGUI Import
#
from PyHtmlGUI                       import E_PARAM_TYPE

from PyHtmlGUI.kernel.hgDate         import hgDate
from PyHtmlGUI.kernel.hgDateTime     import hgDateTime
from PyHtmlGUI.kernel.hgTable        import hgTable
from PyHtmlGUI.kernel.hgTime         import hgTime

from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgSPACE, hgNEWLINE
from PyHtmlGUI.widgets.hgTextEdit    import hgTextEdit
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgTabWidget   import hgTabWidget
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton
from PyHtmlGUI.widgets.hgDateEdit    import hgDateEdit, hgDateChooser
from PyHtmlGUI.widgets.hgTimeChooser import hgTimeChooser
from PyHtmlGUI.widgets.hgMultiList   import hgMultiList
from PyHtmlGUI.widgets.hgVBox        import hgVBox
from PyHtmlGUI.widgets.hgHBox        import hgHBox
from PyHtmlGUI.widgets.hgFrame       import hgFrame
from PyHtmlGUI.widgets.hgGroupBox    import hgGroupBox

#
# ZopRA Imports
#
from zopra.core.dialogs              import getStdDialog
from zopra.core.dialogs.Dialog       import Dialog
from zopra.core.elements.Buttons     import getBackButtonStr

from zopra.Booking.Event             import Event


class EventEditDialogPrivate:

    def __init__(self):
        self.eventId = None


class EventEditDlg(Dialog):
    """\class EventEditDlg"""
    _className  = 'EventEditDlg'
    _classType  = Dialog._classType + [_className]

    # Buttons
    ADD         = ' Add '
    DELETE      = ' Delete '

    # Recurrence Rules
    REC_ENABLE  = ' Enable recurrence'
    REC_DISABLE = ' Disable recurrence'
    REC_DAILY   = ' Daily '
    REC_WEEKLY  = ' Weekly '
    REC_MONTHLY = ' Monthly '
    REC_YEARLY  = ' Yearly '

    # Labels
    L_ToBeBooked   = 'to be booked: '
    L_DateAndTime  = 'Date & Time'
    L_Start        = 'Start: '
    L_DaysOn       = 'day(s)'
    L_WeeksOn      = 'week(s) on:'
    L_MonthsOn     = 'month(s)'
    L_YearsOn      = 'year(s)'

    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
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
    def __init__( self, manager,
                        title  = '',
                        parent = None,
                        name   = _className,
                        flags  = Dialog.Standalone,
                        event  = None ):
        """\brief Constructs a new event edit dialog; \a manager, \a title,
                  \a parent, \a name and \a flags are passed to the ZMOMDialog
                  constructor.
        """
        Dialog.__init__( self, manager, title, parent, name, flags )
        assert event == None or isinstance(event, Event), \
               E_PARAM_TYPE % ('event', 'Event or None', event)

        #
        # Dialog Data Fields
        #
        self.data = EventEditDialogPrivate()

        if event != None:
            self.data.eventId = event.getId()
        else:
            self.data.eventId = 0

        # Event Start Date / Time
        startBox = hgHBox()
        self._start_date_edit  = hgDateChooser( parent = startBox,
                                                name   = 'startDate',
                                                flags  = hgDateChooser.F_SHORT)
        hgLabel('Time', parent = startBox )
        self._start_time_edit  = hgTimeChooser( parent   = startBox,
                                                name     = 'startTime',
                                                stepFlag = hgTimeChooser.SF_M10 )
        self.__startBox        = startBox

        # Event End Date / Time
        endBox   = hgHBox()
        self._end_date_edit    = hgDateChooser( parent = endBox,
                                                flags  = hgDateChooser.F_SHORT )
        hgLabel('Time', parent = endBox )
        self._end_time_edit    = hgTimeChooser( parent = endBox,
                                                stepFlag = hgTimeChooser.SF_M10 )
        end_time = self._start_time_edit.getTime() + hgTime(2)
        self.__endBox = endBox

        # correct for midnight
        if end_time < self._start_time_edit.getTime():
            end_time = hgTime(23, 59)

        self._end_time_edit.setTime( end_time )

        # Purpose of the Event
        self._purpose = hgTextEdit( flags = hgTextEdit.MULTILINE)
        self._purpose.setSize(40, 8)

        # No time associated (in the case where only whole days count)
        self._no_time     = hgCheckBox()

        # Second Page

        # Enable recurrence (default is off)
        self._recurrence  = hgPushButton(self.REC_ENABLE)

        # Recurrence Rule Choices / if enabled default is REC_DAILY
        self._r_daily     = hgPushButton(self.REC_DAILY)
        self._r_weekly    = hgPushButton(self.REC_WEEKLY)
        self._r_monthly   = hgPushButton(self.REC_MONTHLY)
        self._r_yearly    = hgPushButton(self.REC_YEARLY)

        # Recurrence Count
        self._r_count     = hgTextEdit()

        # Recurrence ...
        # ...

        # Recurrence Range
        self._r_no_ending   = hgRadioButton( '1',
                                             'No ending Date ',
                                             name = 'r_range'  )
        self._r_after_occ   = hgRadioButton( '2',
                                             'End after ',
                                             name = 'r_range' )
        self._r_after_count = hgTextEdit()
        self._r_end_by      = hgRadioButton( '3',
                                             'End by ',
                                             name = 'r_range' )
        self._r_end_date    = hgDateEdit()

        # Exceptions
        self._r_exception   = hgDateEdit()
        self._r_exception_list = hgMultiList()

        # Other Buttons

        # add recurrence exception
        self._r_add         = hgPushButton(self.ADD)

        # delete recurrence exception
        self._r_delete      = hgPushButton(self.DELETE)

        # Other Labels
        self._l_duration    = hgLabel()
        self._start_label   = hgLabel()
        self._end_label     = hgLabel()

        # other empty stuff
        self._recCount        = None
        self._tabWidget       = None
        self.firstPageInfoBox = None
        self.__owner_label    = None
        self._recCountLabel   = None
        self._ruleFrame       = None
        self._recRuleTable    = None
        self._exceptionFrame  = None

        # Init Dialog
        self._initTabWidget()
        self._setDefaultValues()

        # connect signals

        # self.datetimeChanged
        hgDate.connect( self._start_date_edit.valueChanged,
                        self.datetimeChanged )
        hgDate.connect( self._end_date_edit.valueChanged,
                        self.datetimeChanged )
        hgTime.connect( self._start_time_edit.valueChanged,
                        self.datetimeChanged )
        hgTime.connect( self._end_time_edit.valueChanged,
                        self.datetimeChanged )

        hgPushButton.connect(self._recurrence.clicked, self.toggleRecurrence)

        hgPushButton.connect( self._r_daily.clicked,
                              self.setRecurrenceRuleDaily )
        hgPushButton.connect( self._r_weekly.clicked,
                              self.setRecurrenceRuleWeekly )
        hgPushButton.connect( self._r_monthly.clicked,
                              self.setRecurrenceRuleMonthly )
        hgPushButton.connect( self._r_yearly.clicked,
                              self.setRecurrenceRuleYearly )
        hgPushButton.connect( self._next.clicked, self.nextTab )

        if event:
            self.setEvent(event)


    def _setDefaultValues(self):
        """\brief Resets a dialog back to its defaults."""
        self.setRecurrenceEnable(False)
        self.setRecurrenceRuleDaily()
        self.datetimeChanged()


    def _initTabWidget(self):
        """\brief Initialise the dialog forms."""

        # First Tab
        firstTab = hgFrame()

        vBox = hgVBox( firstTab )
        self.__owner_label    = hgLabel( parent = vBox )
        self.firstPageInfoBox = hgHBox ( vBox          )

        # Date & Time
        new_frame = hgGroupBox(title = self.L_DateAndTime )

        vBox      = hgVBox( new_frame )
        hBox      = hgHBox( vBox      )

        box       = hgVBox( hBox )
        hgLabel ( 'Start ', parent = box )
        hgLabel ( 'End ',   parent = box )

        box       = hgVBox( hBox )
        box.add ( self.__startBox )
        box.add ( self.__endBox   )

        box       = hgHBox( vBox )
        box.add ( self._no_time )
        box.add ( hgLabel( 'No time associated ' ) )

        vBox = hgVBox( firstTab )
        vBox.add( new_frame             )
        vBox.add( hgLabel('Purpose: ' ) )
        vBox.add( self._purpose         )
        vBox.add( hgSPACE               )

        hBox = hgHBox( vBox )
        hBox.add( self._ok      )
#        hBox.add( self._apply   )
        hBox.add( self._cancel  )
#        hBox.add( self._next    )

        # Second Tab

        # checkbox recurrence enabled
        recWindow = hgFrame()
        recWindow.add( self._recurrence )
        recWindow.add( hgNEWLINE )

        # Appointment Time
        timeFrame = hgGroupBox(title = 'Appointment Time')
        timeFrame.add( self._l_duration  )
        timeFrame.add( hgNEWLINE         )
        timeFrame.add( hgNEWLINE         )
        timeFrame.add( 'From: '          )
        timeFrame.add( self._start_label )
        timeFrame.add( hgNEWLINE         )
        timeFrame.add( 'To:   '          )
        timeFrame.add( self._end_label   )
        recWindow.add( timeFrame         )

        # Recurrence Rule Window / Buttons
        self._ruleFrame = hgGroupBox(title = 'Recurrence Rule')

        # Recurrence Rule Layout
        layoutTable = hgTable()
        layoutTable._old_style = False

        layoutTable[0, 0] = self._r_daily
        layoutTable[1, 0] = self._r_weekly
        layoutTable[2, 0] = self._r_monthly
        layoutTable[3, 0] = self._r_yearly

        # Recurrence Rule Table
        self._recCount      = hgTextEdit()
        self._recCount.setSize(5)
        self._recCountLabel = hgLabel()

        self._recRuleTable  = hgTable()
        self._recRuleTable._old_style = False
        self._recRuleTable[0, 0] = 'Recur every'
        self._recRuleTable[0, 1] = self._recCount
        self._recRuleTable[0, 2] = self._recCountLabel


        layoutTable[0, 2] = self._recRuleTable
        layoutTable.setAlignment('left', 'center')

        self._ruleFrame.add( layoutTable )
        recWindow.add( self._ruleFrame   )

        # Recurrence Range
        rangeFrame = hgGroupBox(title = 'Recurrence Range')
        rangeFrame.add( 'Begins on ' )
        rangeFrame.add( self._start_label.getText() )
        rangeFrame.add( hgNEWLINE )
        rangeFrame.add( hgRadioButton( 1,
                                       'No ending date',
                                       True,
                                       name = 'rec_range' ) )
        rangeFrame.add( hgNEWLINE )
        rangeFrame.add( hgRadioButton(2, 'End after ', name = 'rec_range') )
        rangeFrame.add( hgTextEdit() )
        rangeFrame.add( ' occurence(s)')
        rangeFrame.add( hgNEWLINE  )
        rangeFrame.add( hgRadioButton(3, 'End by ', name = 'rec_range') )
        rangeFrame.add( hgDateEdit() )

        # Exception Frame
        self._exceptionFrame = hgGroupBox( title = 'Exceptions')
        self._exceptionFrame.add( self._r_add    )
        self._exceptionFrame.add( hgNEWLINE      )
        self._exceptionFrame.add( self._r_delete )

        # Layout Table
        layoutTable = hgTable()
        layoutTable._old_style = False
        layoutTable[0, 0] = rangeFrame
        layoutTable[0, 1] = self._exceptionFrame
        recWindow.add( layoutTable )

        # tabWidget
        self._tabWidget = hgTabWidget()
        self._tabWidget.addTab( firstTab,  'General'    )
#        self._tabWidget.addTab( recWindow, 'Recurrence' )
        self.getForm().add(self._tabWidget)


    def applied(self):
        """\brief """
        Dialog.applied(self)

        # build datetime
        start = hgDateTime()
        start.setDate( self._start_date_edit.getDate() )
        start.setTime( self._start_time_edit.getTime() )

        end = hgDateTime()
        end.setDate( self._end_date_edit.getDate() )
        end.setTime( self._end_time_edit.getTime() )

        if start > end:
            error_msg = getStdDialog('A error occured - Please correct')
            form      = error_msg.getForm()
            form.add( hgNEWLINE + hgSPACE )
            form.add( 'Your start date is later than your end date.')
            form.add( hgNEWLINE + hgSPACE )
            form.add( 'Start: %s' % start )
            form.add( hgNEWLINE + hgSPACE )
            form.add( 'End: %s' % end     )
            form.add( hgNEWLINE + hgSPACE )
            form.add( hgNEWLINE + hgSPACE )
            form.add( getBackButtonStr() )
            raise ValueError(error_msg)


    def getDuration(self):
        """\brief Builds the difference between start and end timing."""
        start_date = self._start_date_edit.getDate()
        end_date   = self._end_date_edit.getDate()
        diff_days  = start_date.daysTo( end_date )

        minute = self._end_time_edit.getTime().getMinute()   - \
                 self._start_time_edit.getTime().getMinute()
        hour   = self._end_time_edit.getTime().getHour()   - \
                 self._start_time_edit.getTime().getHour() + ( diff_days * 24 )

        # correct timing
        hour  += minute / 60
        minute = minute % 60

        # nice time description
        if hour == 0:
            if minute != 1:
                description = 'minutes'
            else:
                description = 'minute'
        else:
            description = 'hours'

        return 'Duration: %i:%02.i %s' % (hour, minute, description)


    def datetimeChanged(self):
        """\brief Changes the dialog if the date has changed."""
        self._start_label.setText( '%s %s' % (self._start_date_edit.getDate(),
                                              self._start_time_edit.getTime()))

        self._end_label.setText( '%s %s' % ( self._end_date_edit.getDate(),
                                             self._end_time_edit.getTime() ) )

        self._l_duration.setText( self.getDuration() )



    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""

        key = self._tabWidget.getName() + '_setCurrentTab'
        if REQUEST.form.has_key(key):
            self._tabWidget.setCurrentPage( int(REQUEST[key]) )

        Dialog.execDlg(self, manager, REQUEST)


    def setEvent(self, event):
        """\brief Sets the dialog values to the values of event."""
        assert isinstance(event, Event), \
               self.E_PARAM_TYPE % ('event', 'Event', event)

        self.data.eventId = event.getId()

        # information general tab
        self._start_date_edit.setDate ( event.begin.date() )
        self._end_date_edit.setDate   ( event.end.date()   )

        self._start_time_edit.setTime ( event.begin.time() )
        self._end_time_edit.setTime   ( event.end.time()   )

        self._purpose.setText(event.purpose)
        self._no_time.setChecked(event.no_time)

        # information recurrence tab
        # ...


    def getEvent(self):
        """\brief Returns an event object."""

        # first update the event object
        event = Event( self.data.eventId )

        # information general tab
        event.begin.setDate( self._start_date_edit.getDate() )
        event.end.setDate  ( self._end_date_edit.getDate()   )

        event.begin.setTime( self._start_time_edit.getTime() )
        event.end.setTime  ( self._end_time_edit.getTime()   )

        event.purpose        = self._purpose.getText()
        event.no_time        = self._no_time.isChecked()

        # information recurrence tab
        return event


    def getOwnerLabel(self):
        """\brief Returns the label for the owner field to be field from the
                  manager.
        """
        return self.__owner_label

    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################
    def nextTab(self):
        """\brief Shows the next tab."""
        self._tabWidget.setCurrentPage( self._tabWidget.getCurrentIndex() + 1)


    def setRecurrenceEnable(self, enabled):
        """\brief Set all Widgets enable value for recurrences."""
        assert enabled == True or enabled == False, \
               self.E_PARAM_TYPE % ('enabled', 'BooleanType', enabled)
        if enabled:
            self._recurrence.setText(self.REC_DISABLE)
        else:
            self._recurrence.setText(self.REC_ENABLE)
        self._ruleFrame.setEnabled     (enabled)
        self._exceptionFrame.setEnabled(enabled)


    def setRecurrenceRuleDaily(self):
        """\brief Sets the recurrence rule daily."""
        self._recCountLabel.setText(self.L_DaysOn)


    def setRecurrenceRuleWeekly(self):
        """\brief Sets the recurrence rule daily."""
        self._recCountLabel.setText(self.L_WeeksOn)


    def setRecurrenceRuleMonthly(self):
        """\brief Sets the recurrence rule daily."""
        self._recCountLabel.setText(self.L_MonthsOn)


    def setRecurrenceRuleYearly(self):
        """\brief Sets the recurrence rule daily."""
        self._recCountLabel.setText(self.L_YearsOn)


    def setStartDate(self, date):
        """\brief Sets the start date."""
        assert isinstance(date, hgDate), \
               self.E_PARAM_TYPE % ('date', 'hgDate', date)

        self._start_date_edit.setDate(date)
        self._end_date_edit.setDate(date)
        self._tabWidget.setInvalid()


    def toggleRecurrence(self):
        """\brief Toggles the recurrence ability"""
        self.setRecurrenceEnable( not self._r_daily.isEnabled )