############################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from PyHtmlGUI.kernel.hgBoxLayout   import hgHBoxLayout, hgVBoxLayout

from PyHtmlGUI.widgets.hgLabel      import hgLabel
from PyHtmlGUI.widgets.hgLineEdit   import hgLineEdit
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from PyHtmlGUI.widgets.hgScrollBar  import hgScrollBar


class zraNavBar( hgScrollBar ):
    """\class zraNavBar"""

    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
    # enum Buttons
    First    = 0
    PrevPage = 1
    PrevLine = 2
    NextLine = 3
    NextPage = 4
    Last     = 5
    Go       = 6
    New      = 7
    Buttons  = [ First,    PrevPage, PrevLine, NextLine,
                 NextPage, Last,     Go,       New       ]

    # enum Labels
    CurrentLine = 0
    LastLine    = 1
    Labels      = [ CurrentLine, LastLine ]

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self,
                  minValue      = 0,
                  maxValue      = 99,
                  lineStep      = 1,
                  pageStep      = 10,
                  value         = 0,
                  orientation   = hgScrollBar.Horizontal,
                  parent        = None,
                  name          = None ):
        """\reimp"""

        self.go = None

        hgScrollBar.__init__( self,  minValue,    maxValue, lineStep, pageStep,
                              value, orientation, parent,   name )



    def init(self):
        """\brief Initialise the button field."""
        hgScrollBar.init(self)

        # LineEdit
        self.go = hgLineEdit( parent = self )
        self.go.setSize(5)
        self.go.setToolTip( 'Enter a valid entry number to jump there. ' +
                            'You have to press the Go Button.' )

        # First
        btn = hgPushButton( '|<', parent = self     )
        btn.setToolTip( 'Go to first entry.'        )
        btn.connect( btn.clicked, self.jumpToFirst  )
        btn.connect( btn.clicked, self.firstLine    )
        self.buttons[self.First] = btn

        # PrevPage
        btn = hgPushButton( '<<', parent = self     )
        btn.setToolTip( 'Go back some entries.'     )
        btn.connect( btn.clicked, self.subtractPage )
        btn.connect( btn.clicked, self.prevPage     )
        self.buttons[self.PrevPage] = btn

        # PrevLine
        btn = hgPushButton( '<', parent = self      )
        btn.setToolTip( 'Go to previous entry.'     )
        btn.connect( btn.clicked, self.subtractLine )
        btn.connect( btn.clicked, self.prevLine     )
        self.buttons[self.PrevLine] = btn

        # NextLine
        btn = hgPushButton( '>', parent = self      )
        btn.setToolTip( 'Go to next entry.'         )
        btn.connect( btn.clicked, self.addLine      )
        btn.connect( btn.clicked, self.nextLine     )
        self.buttons[self.NextLine] = btn

        # NextPage
        btn = hgPushButton( '>>', parent = self     )
        btn.setToolTip( 'Go forth some entries.'    )
        btn.connect( btn.clicked, self.addPage      )
        btn.connect( btn.clicked, self.nextPage     )
        self.buttons[self.NextPage] = btn

        # Last
        btn = hgPushButton( '>|', parent = self     )
        btn.setToolTip( 'Go to last entry.'         )
        btn.connect( btn.clicked, self.jumpToLast   )
        btn.connect( btn.clicked, self.lastLine     )
        self.buttons[self.Last] = btn

        # Go
        btn = hgPushButton( 'Go', parent = self     )
        btn.setToolTip( 'Go to specified entry.'    )
        self.buttons[self.Go] = btn

        # New
        btn = hgPushButton( '>*', parent = self     )
        btn.setToolTip( 'Creates a new entry.'      )
        btn.connect( btn.clicked, self.jumpToNew    )
        btn.connect( btn.clicked, self.newLine      )
        self.buttons[self.New] = btn

        # CurrentLine
        label = hgLabel( parent = self )
        label.setToolTip('Current Position')
        self.labels[self.CurrentLine] = label

        # LastLine
        label = hgLabel( parent = self )
        label.setToolTip('Last Position')
        self.labels[self.LastLine] = label


    def initLayout(self):
        """\reimp"""
        if self.orient == self.Horizontal:
            layout = hgHBoxLayout(self)

        else:
            layout = hgVBoxLayout(self)

        layout.addWidget( self.buttons[self.First]        )
        layout.addWidget( self.buttons[self.PrevPage]     )
        layout.addWidget( self.buttons[self.PrevLine]     )
        layout.addWidget( hgLabel('&nbsp;', self)         )
        layout.addWidget( self.labels[self.CurrentLine]   )
        layout.addWidget( hgLabel('&nbsp;of&nbsp;', self) )
        layout.addWidget( self.labels[self.LastLine]      )
        layout.addWidget( hgLabel('&nbsp;', self)         )
        layout.addWidget( self.buttons[self.NextLine]     )
        layout.addWidget( self.buttons[self.NextPage]     )
        layout.addWidget( self.buttons[self.Last]         )
        layout.addWidget( self.buttons[self.New]          )
        layout.addWidget( hgLabel('&nbsp;|&nbsp;', self)  )
        layout.addWidget( self.go                         )
        layout.addWidget( self.buttons[self.Go]           )


    def jumpToFirst(self):
        """\brief Go to the first line."""
        hgScrollBar.setValue( self, self.minValue() )


    def jumpToLast(self):
        """\brief Go to the last line."""
        hgScrollBar.setValue( self, self.maxValue() )


    def jumpToNew(self):
        """\brief Go to a new line."""
        self.labels[self.CurrentLine].text = '*'


    def rangeChange(self):
        """\reimp"""
        hgScrollBar.rangeChange(self)
        self.labels[self.LastLine].text = str( self.maxValue() )


    def valueChange(self):
        """\reimp"""
        hgScrollBar.valueChange(self)
        self.labels[self.CurrentLine].text = str( self.value() )

    ##########################################################################
    #
    # Signal Methods
    #
    ##########################################################################
    def firstLine(self):
        """\brief This signal is emitted when the navigation bar scrolls
                  to the first line up or left.
        """
        self._fireSignal(self.firstLine)
    hgScrollBar._addSignal(firstLine)


    def lastLine(self):
        """\brief This signal is emitted when the navigation bar scrolls
                  to the last line down or right.
        """
        self._fireSignal(self.lastLine)
    hgScrollBar._addSignal(lastLine)


    def newLine(self):
        """\brief This signal is emitted when the navigation bar wants to
                  have a new line.
        """
        self._fireSignal(self.newLine)
    hgScrollBar._addSignal(newLine)
