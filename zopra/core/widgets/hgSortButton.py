############################################################################
#    Copyright (C) 2008 by Bernhard Voigt                                  #
#    bernhard.voigt@lmu.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from PyHtmlGUI.widgets.hgButton      import hgButton
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton


class hgSortButton(hgPushButton):
    """\class hgSortButton

    The hgSortButton widget provides a ComboBox combined with an entry field
    and filter button.
    """
    _className = 'hgSortButton'
    _classType = hgPushButton._classType + [ _className ]

    SORT_OFF  = 'off'
    SORT_ASC  = 'asc'
    SORT_DESC = 'desc'

    SORT_STATES = [SORT_OFF, SORT_ASC, SORT_DESC]

    DISABLED  = 'disabled'

    # prefix is added to the name and determines the next action on button click
    # the name and prefix is used in list handling by ManagerPart
    # i_ - increasing: on click list will be sorted in increasing order
    # d_ - decreasing: on click list will be sorted in decreasing order
    state2prefix = { SORT_OFF:  'i_',
                     SORT_ASC:  'd_',
                     SORT_DESC: 'i_'  }

    def __init__( self,
                  text     = '',
                  function = None,
                  icons    = None,
                  state    = None,
                  parent   = None,
                  name     = None,
                  flag     = hgButton.NO_FLAG ):
        """\brief """
        hgPushButton.__init__(self, text     = '',
                          function = None,
                          icon     = None,
                          parent   = None,
                          name     = None,
                          flag     = hgButton.NO_FLAG)

        # init members
        self.base_name = name
        self.state     = None
        self.icons     = {}

        for btn_state in self.SORT_STATES:
            assert btn_state in icons

            self.icons[btn_state] = icons[btn_state]

        assert self.DISABLED in icons.keys()
        self.icons[self.DISABLED] = icons[self.DISABLED]

        if state not in self.SORT_STATES:
            state = self.SORT_OFF

        self.setState(state)

        self.connect( self.clicked,  self.updateSorting  )



    def setState(self, state):
        """\brief Set the sorting state"""
        if state not in self.SORT_STATES:
            return self.state

        if state == self.state:
            return

        self.state = state

        self.updateIcon()

        self.setName(self.state2prefix[self.state] + self.base_name)


    def getState(self):
        """\brief Get the sorting state"""
        return self.state


    def updateSorting(self):
        """\brief Get the sorting state"""

        if self.state == self.SORT_ASC:
            self.setState(self.SORT_DESC)
        else:
            self.setState(self.SORT_ASC)


    def updateIcon(self):
        """\brief Set the correct icon"""
        if self.isEnabled():
            self.setIcon(self.icons[self.state])
        else:
            self.setIcon(self.icons[self.DISABLED])


    def setEnabled(self, enable = True):
        """\brief whether the widget is enabled"""
        hgPushButton.setEnabled(self, enable)
        self.updateIcon()
