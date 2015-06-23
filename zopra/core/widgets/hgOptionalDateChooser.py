##############################################################################
#    Copyright (C) 2003-2005 by Ingo Keller                                  #
#    ingo.keller@pyhtmlgui.org                                               #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################

import string
from types                          import TupleType, ListType, StringType

from PyHtmlGUI.kernel.hgDate        import hgDate
from PyHtmlGUI.widgets.hgDateEdit   import hgDateChooser



def dateTupelContainsUndef(date_list):
    """\brief Checks date tupel for optional date entries."""

    assert isinstance(date_list, TupleType) or \
    isinstance(date_list, ListType),    \
    '[Error] ListType or TupleType required'

    assert len(date_list) == 3, \
    '[Error] List length error, got: %s' % date_list

    for entry in date_list:
        if '--' in entry:
            return True

    return False


def getDateEntry(descr_dict, col, optional = False):
    """\brief Creates correct date entry from hgDateChooser value"""

    date_list = descr_dict.get(col)
    if date_list:
        # we already have a string
        if isinstance(date_list, StringType):
            return
        if not isinstance(date_list, ListType):
            return
        for entry in date_list:
            if not isinstance(entry, StringType):
                raise ValueError( self.getErrorDialog('Value Error: expected string type.') )


        if optional and dateTupelContainsUndef(date_list):
            descr_dict[col] = None
        else:
            descr_dict[col] = string.join(date_list, '.')


class hgOptionalDateChooser(hgDateChooser):
    """\brief class hgDateChooser."""
    _className = 'hgOptionalDateChooser'
    _classType = hgDateChooser._classType + [_className]


    def __init__( self,
                  date   = None,
                  parent = None,
                  name   = None,
                  flags  = hgDateChooser.F_TINY ):
        """\brief Constructs a hgDateChooser."""
        hgDateChooser.__init__(self, date, parent, name, flags)

        self._cb_list[self.DAY].insertItem('--', index=0)
        self._cb_list[self.MONTH].insertItem('--', index=0)
        self._cb_list[self.YEAR].insertItem('----', index=0)

        if date is None:
            self._date = hgDate()

        self._updateCurrentValue()



    def _updateCurrentValue(self):
        """\brief
        """
        if self._date.isNull():
            self._cb_list[self.YEAR].setCurrentValue('----')
            self._cb_list[self.MONTH].setCurrentValue('--')
            self._cb_list[self.DAY].setCurrentValue('--')
            return

        if not self._min_date <= self._date:
            self.outOfRange()
            self._date.setDate(self._min_date)

        elif not self._date <= self._max_date:
            self.outOfRange()
            self._date.setDate(self._max_date)

        self._cb_list[self.YEAR].setCurrentValue(self._date.year)
        self._cb_list[self.MONTH].setCurrentItem(self._date.month)
        self._cb_list[self.DAY].setCurrentItem(self._date.day)


    def setDisplayedYearsRange(self, start, end):
        """\brief Creates combo box for years that ranges from start to end
                  taking to limits of set minimum and maximum date into account.
        """
        super(hgOptionalDateChooser, self).setDisplayedYearsRange(start, end)

        self._cb_list[self.YEAR].insertItem('----', index=0)
        if self._date.isNull():
            self._cb_list[self.YEAR].setCurrentValue('----')
        else:
            self._cb_list[self.YEAR].setCurrentValue(self._date.year)


    def getDate(self):
        """\brief Returns a new hgDate object with the information of the
                  internal one.
        """
        if self._date.isNull():
            tmp_date = hgDate()
        else:
            tmp_date = hgDate(self._date.year, self._date.month, self._date.day)
        tmp_date.setOrder(self._date.getOrder())
        return tmp_date


    def getIsoDate(self):
        """\brief Returns the date of this object."""
        if self._date.isNull():
            return [0, 0, 0]
        else:
            return [self._date.year, self._date.month, self._date.day]


    def setDate(self, date):
        """\brief Sets this hgDateChooser to date."""
        self._date.setDate(date)
        self._updateCurrentValue()

    def unsetDate(self, date):
        """\brief Sets this hgDateChooser to an unspecified date."""
        self._date = hgDate()
        self._updateCurrentValue()
