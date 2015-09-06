############################################################################
#    Copyright (C) 2003 by Ingo Keller                                     #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from types                                   import IntType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.kernel.hgTime                 import hgTime
from PyHtmlGUI.kernel.hgTable                import hgTable

from PyHtmlGUI.stylesheet.hgStyleSheetItem   import hgStyleSheetItem

from PyHtmlGUI.widgets.hgLabel               import hgLabel, hgSPACE
from PyHtmlGUI.widgets.hgDateEdit            import hgDate
from PyHtmlGUI.widgets.hgVBox                import hgVBox

#
# ZopRA Imports
#
from zopra.core.dialogs.Dialog               import Dialog

#
# Default StyleSheetItems
#
ssiTIME_PICKER  = hgStyleSheetItem('.time_picker')
ssiTIME_PICKER.background().setColor('#FFFFFF')
ssiTIME_PICKER.border().setAll( '#7B86BF', 'solid', '1 px' )

ssiCell = hgStyleSheetItem()
ssiCell.border().setRight( '#000000', 'solid', '1px' )

ssiCellOdd = hgStyleSheetItem()
ssiCellOdd.border().setTop ( '#000000', 'dashed', '1px' )
ssiCellOdd.border().setLeft( '#000000', 'solid',  '1px' )

ssiCellEven = hgStyleSheetItem()
ssiCellEven.border().setTop ( '#000000', 'solid', '1px' )
ssiCellEven.border().setLeft( '#000000', 'solid', '1px' )


class ZMOMTimePickerPrivate:
    """\class ZMOMTimePicker"""

    def __init__(self):
        """\brief Constructs a ZMOMTimePickerPrivate object."""
        self.date        = hgDate()
        self.time        = hgTime()
        self.time_events = []
        self.date_events = []
        self.time_slots  = {}
        self.day_slot    = hgVBox()


    def empty(self):
        """\brief Empty the data structure."""
        self.time_events = []
        self.date_events = []
        self.time_slots  = {}
        self.day_slot    = hgVBox()


class ZMOMTimePicker(Dialog):
    """\brief MonthView class"""
    _className = 'TimePicker'
    _classType = Dialog._classType + [_className]

    TABLE = _className + 'table'

    NEXT_MONTH = '>'
    NEXT_YEAR  = '>>'

    PREV_MONTH = '<'
    PREV_YEAR  = '<<'
    TODAY      = '|->'
    SET        = 'Set'

    FULLDAY    = 'All Day'

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
    def getDate(self):
        """\brief Returns the date property."""
        return self._data.date.getDate()

    def setDate(self, date = None):
        """\brief Sets the date property."""
        assert date == None or isinstance(date, hgDate), \
               self.E_PARAM_TYPE % ('date', 'hgDate or None', date)

        if date == None:
            date = hgDate.today()
        self._data.date.setDate( date )

    date = property(getDate, setDate)


    def getTime(self):
        """\brief Returns time."""
        return self._data.time.getTime()

    time = property(getTime)


    def isTimeRowEnabled(self):
        """\brief Returns the timeRowEnabled property."""
        return self.__timeRowEnabled

    def setTimeRowEnabled(self, enabled):
        """\brief Sets the timeRowEnabled property to \a enabled."""
        assert enabled == True or enabled == False, \
               self.E_PARAM_TYPE % ('enabled', 'BooleanType', enabled)

        if self.__timeRowEnabled != enabled:
            self.__timeRowEnabled = enabled
            self._initTable()

    timeRowEnabled = property(isTimeRowEnabled, setTimeRowEnabled)
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, title = None, parent = None, name = None):
        """\brief Constructs a ZMOMTimePicker dialog."""
        Dialog.__init__( self, None, title, parent, name, self.Embedded )

        self.getForm().setSsiName( '.time_picker' )
        self.getForm().style().stylesheet().getSsiName( ssiTIME_PICKER )

        self._data            = ZMOMTimePickerPrivate()
        self.__full_day       = False
        self.__timeRowEnabled = False

        # layout
        vBox = hgVBox()
        self._date_label           = hgLabel( parent = vBox )
        self._day_events           = hgTable( spacing = '0',
                                              padding = '0',
                                              parent  = vBox )
        self._day_events.old_style = False
        self._day_table            = hgTable( spacing = '0',
                                              padding = '0',
                                              parent  = vBox )
        self._day_table.old_style  = False

        self.getForm().add( vBox )

        self._initTable()
        self.erase()


        # connect signals
        hgTime.connect(self._data.time.valueChanged, self.valueChanged )
        hgDate.connect(self._data.date.valueChanged, self.erase        )

        # button_full_day            = hgPushButton( self.FULLDAY )
        # hgDate.connect(button_full_day.clicked, self.switchFullDay     )


    def _initTable(self):
        """\brief Initialise the day view table."""
        style_cell = str(ssiCell)
        style_cell = style_cell.split('{')[1]
        style_cell = style_cell.split('}')[0]

        style_odd  = str(ssiCellOdd)
        style_odd  = style_odd.split('{')[1]
        style_odd  = style_odd.split('}')[0]

        style_even = str(ssiCellEven)
        style_even = style_even.split('{')[1]
        style_even = style_even.split('}')[0]

        self._day_table.emptyTable()
        self._day_events.emptyTable()
        self._day_events[0, 0] = hgVBox()

        # time row
        if self.__timeRowEnabled:

            # even row
            for row in xrange(0, 48, 2):
                self._day_table[row, 0] = '%02.i:00' % (row / 2)
                self._day_table.setCellBackgroundColor (row, 0, '#EEEEE6')
                self._day_table.setCellStyle(row, 0, style_even)

            # odd row
            for row in xrange(1, 48, 2):
                self._day_table[row, 0] = hgSPACE
                self._day_table.setCellBackgroundColor (row, 0, '#EEEEE6')
                self._day_table.setCellStyle(row, 0, style_odd)

        # init slots
        for row in xrange(48):
            self._day_table[row, 1] = hgSPACE
            self._day_table.setCellBackgroundColor (row, 1, '#FFFFFF')
            self._day_table.setCellStyle(row, 1, style_cell)


        self._day_table[row + 1, 1] = hgSPACE.getHtml() * 30


    def _updateSlots(self):
        """\brief"""
        slots = self._data.time_slots
        table = self._day_table
        for index in xrange(48):
            table[index, 1] = slots.get(index)

        self._day_events[0, 0] = self._data.day_slot


    def _addEventToSlot(self, event, slot_start = None, slot_end = None):
        """\brief """
        assert isinstance (slot_start, IntType) or slot_start == None, \
              self.E_PARAM_TYPE % ('slot_start', 'IntType or None', slot_start)
        assert isinstance (slot_end, IntType) or slot_end == None, \
              self.E_PARAM_TYPE % ('slot_end', 'IntType or None', slot_end)

        if slot_end > 48:
            slot_end = 48

        if slot_start != None and slot_start < 0:
            slot_start = 0

        # information
        text = event.getOwnerName()
        link = 'showEvent?event_id=%s' % event.getId()
        if not text:
            text = 'Booked Event'

        # slot by number time
        if slot_start != None:

            # more than one slot
            if slot_end:
                for index in xrange(slot_start, slot_end):
                    hgLabel( text, link, parent = self._getSlotBox(index) )

            # just one slot
            else:
                hgLabel( text, link, parent = self._getSlotBox(slot_start) )


        # slot for whole day
        else:
            hgLabel( text, link, parent = self._data.day_slot )


    def _getSlotBox(self, box_number):
        """\brief Returns a hgVBox with the content of one slot."""
        assert isinstance (box_number, IntType), \
               self.E_PARAM_TYPE % ('box_number', 'IntType', box_number)

        box = self._data.time_slots.get(box_number)
        if not box:
            box = hgVBox()
            self._data.time_slots[box_number] = box
        return box


    def _getSlotBoxSize(self, box_number):
        """\brief Returns the height of the slot hgVBox."""
        pass


#    def _foundWidgetFunction(self, widget, value, manager):
#        """\brief Should handle widget changes."""
#        if isinstance(widget, hgPushButton):
#            widget.clicked()


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""
        Dialog.execDlg(self, manager, REQUEST)

        if REQUEST                  and \
           REQUEST.has_key('hour')  and \
           REQUEST.has_key('minute'):
            self._data.time.setTime( (REQUEST['hour'], REQUEST['minute']) )

#
# Public Functions
#
    def erase(self):
        """\brief """
        self._data.empty()

        self._date_label.text = str( self._data.date )
        for index in xrange(0, 48):
            self._day_table[index, 1] = hgSPACE


    def setEvents(self, event_list):
        """\brief Sets the events of the day given by the \a event_list."""

        # remove old events
        self._data.empty()

        # sort for no time
        for event in event_list:
            if event.no_time == True:
                self._data.date_events.append(event)
            else:
                self._data.time_events.append(event)

        # clear table
        self._initTable()

        # current date
        current_date = self.date

        # find the right place for event
        for event in self._data.time_events:

            # calc right slots

            # just one day
            if event.start_date == event.end_date:
                slot_start = ( event.start_time.getHour() * 2    ) + \
                             (( event.start_time.getMinute() / 30) % 2 )

                slot_end   = ( event.end_time.getHour() * 2    ) + \
                             (( event.end_time.getMinute() / 30 ) % 2)

                if slot_start > slot_end:
                    raise ValueError('Start time later than end time.')

            # for events over more than days
            else:
                # is start_date
                if event.start_date == current_date:
                    slot_start = ( event.start_time.getHour() * 2    ) + \
                                 (( event.start_time.getMinute() / 30) % 2 )
                    slot_end   = 48

                # is end_date
                elif event.end_date == current_date:
                    slot_start = 0
                    slot_end   = ( event.end_time.getHour() * 2    ) + \
                                 (( event.end_time.getMinute() / 30 ) % 2)

                # is in between
                else:
                    slot_start = 0
                    slot_end   = 48

            self._addEventToSlot(event, slot_start, slot_end + 1)

        # insert all events for the whole day
        for event in self._data.date_events:
            self._addEventToSlot(event)

        self._updateSlots()
        self.setInvalid()
        self.getForm().setInvalid()


    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################
    def hideTimeRow(self):
        """\brief Switches to show time row."""
        self.setTimeRowEnabled( False )


    def showTimeRow(self):
        """\brief Switches to show time row."""
        self.setTimeRowEnabled( True )


    def switchFullDay(self):
        """\brief Switches between full day and working hour view."""
        self.__full_day = not self.__full_day
        self._initTable()

    ##########################################################################
    #
    # Signal Methods
    #
    ##########################################################################
    def timeChanged(self, time):
        """\brief Returns the current date settings if the time changed.

        Don't use the hgTime that is delivered!
        """
        self._fireSignal(self.timeChanged, time)
    Dialog._addSignal(timeChanged)


    def valueChanged(self):
        """\brief Signal is emitted if the date value changes."""
        self._fireSignal(self.valueChanged)
    Dialog._addSignal(valueChanged)
