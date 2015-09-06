############################################################################
#    Copyright (C) 2003 by Ingo Keller                                     #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#
# PyHtmlGUI Imports
#
from PyHtmlGUI.kernel.hgTable               import hgTable

from PyHtmlGUI.stylesheet.hgStyleSheetItem  import hgStyleSheetItem

from PyHtmlGUI.widgets.hgLabel              import hgLabel
from PyHtmlGUI.widgets.hgPushButton         import hgPushButton
from PyHtmlGUI.widgets.hgDateEdit           import hgDate,        \
                                                   hgDateEdit
from PyHtmlGUI.widgets.hgComboBox           import hgComboBoxWeek

#
# ZopRA Imports
#
from zopra.core.dialogs.Dialog              import Dialog

#
# Default StyleSheetItems
#
ssiDATE_PICKER  = hgStyleSheetItem('.date_picker')
ssiDATE_PICKER.background().setColor('#FFFFFF')
ssiDATE_PICKER.border().setAll( '#7B86BF', 'solid', '1px' )


class ZMOMDatePicker(Dialog):
    """\brief DatePicker class"""
    _className = 'DatePicker'
    _classType = Dialog._classType + [_className]

    TABLE = _className + 'table'

    NEXT_MONTH = '>'
    NEXT_YEAR  = '>>'

    PREV_MONTH = '<'
    PREV_YEAR  = '<<'
    TODAY      = '|->'
    SET        = 'Set'

    SET_DATE   = '$1'
    WEEK       = '$2'


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, title = None, parent = None, name = None ):
        """\brief Constructs a ZMOMDatePicker dialog."""
        Dialog.__init__(self, manager, title, parent, name, self.Embedded)

        # default style
        self.getForm().setSsiName( '.date_picker' )
        self.getForm().style().stylesheet().getSsiName( ssiDATE_PICKER )

        self._day          = hgDate.today()
        self._title_label  = hgLabel()
        self._date_edit    = hgDateEdit()

        # button objects
        btn_prev_year  = hgPushButton( self.PREV_YEAR  )
        btn_prev_month = hgPushButton( self.PREV_MONTH )
        btn_next_month = hgPushButton( self.NEXT_MONTH )
        btn_next_year  = hgPushButton( self.NEXT_YEAR  )
        btn_today      = hgPushButton( self.TODAY, name = self.TODAY )
        btn_set        = hgPushButton( self.SET )

        # button tooltips
        btn_prev_year.setToolTip ('Show previous year.'        )
        btn_prev_month.setToolTip('Show previous month.'       )
        btn_next_month.setToolTip('Show next month.'           )
        btn_next_year.setToolTip ('Show next year.'            )
        btn_today.setToolTip     ('Show today.'                )
        btn_set.setToolTip       ('Set to the specified date.' )

        # layout table
        self._table = hgTable(name = self.TABLE)
        self._table._old_style = False
        self._table[0, 0] = btn_prev_year
        self._table[0, 1] = btn_prev_month
        self._table[0, 2] = self._title_label
        self._table.setCellAlignment(0, 2, 'center', 'center')
        self._table[0, 3] = btn_next_month
        self._table[0, 4] = btn_next_year
        self._table[1, 0] = ''
        self._table.setCellSpanning(1, 0, colspan = 5)
        self._table.setAlignment('center', 'top')

        # fill form
        self.getForm().add( self._table     )
        self.getForm().add( btn_today       )
        self.getForm().add( self._date_edit )
        self.getForm().add( hgComboBoxWeek( name = self.WEEK ) )
        self.getForm().add( btn_set         )
        self._updateDialog()

        # connect signals
        hgDate.connect( self._day.valueChanged, self._updateDialog )
        hgDate.connect( self._day.valueChanged, self.valueChanged  )


    def _updateDialog(self):
        """\brief Updates the control widgets of the dialog."""
        # Month Overview
        self._title_label.setText( '%s %s' % (
                                   hgDate.longMonthName[self._day.month - 1],
                                   self._day.year )
                                  )

        self._table[1, 0] = hgDate.getDayTable( self._day.year,
                                                  self._day.month,
                                                  self._day.day,
                                                  base_link = self.name + '?')
        self._date_edit.setText( self._day )
        self.dateChanged(self._day)


    def _foundWidgetFunction(self, widget, value):
        """\brief Should handle widget changes."""
        Dialog._foundWidgetFunction(self, widget, value)

        if isinstance(widget, hgPushButton):

            # month buttons
            if value == self.PREV_MONTH:
                self._day.setDate( self._day.addMonths( -1 ) )

            elif value == self.PREV_YEAR:
                self._day.setDate( self._day.addYears( -1 ) )

            elif value == self.NEXT_MONTH:
                self._day.setDate( self._day.addMonths( 1 ) )

            elif value == self.NEXT_YEAR:
                self._day.setDate( self._day.addYears( 1 ) )

            elif value == self.TODAY:
                self._day.setDate( hgDate.today() )


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""
        Dialog.execDlg(self, manager, REQUEST)

        if REQUEST                  and \
           REQUEST.has_key('year')  and \
           REQUEST.has_key('month') and \
           REQUEST.has_key('day')   :
            self._day.setDate(
                                hgDate( REQUEST['year'],
                                        REQUEST['month'],
                                        REQUEST['day'] )
                              )


    def getDate(self):
        """\brief Returns the date that is actually set."""
        return self._day.getDate()


    def setDate(self, date):
        """\brief Returns the date that is actually set."""
        return self._day.setDate(date)


    def setName(self, name = None):
        """\brief Sets the name of the dialog."""
        Dialog.setName(self, name)
        self._updateDialog()


    ##########################################################################
    #
    # Signal Methods
    #
    ##########################################################################
    def dateChanged(self, date):
        """\brief Returns the current date settings if the date changed.

        Don't use the hgDate that is delivered!
        """
        self._fireSignal(self.dateChanged, date)
    Dialog._addSignal(dateChanged)


    def valueChanged(self):
        """\brief Signal is emitted if the date value changes."""
        self._fireSignal(self.valueChanged)
    Dialog._addSignal(valueChanged)
