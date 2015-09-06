############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from types                      import ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.dialogs.hgDialog      import hgDialog
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgLabel       import hgProperty

#
# ZopRA Imports
#
from zopra.core.dialogs.guiHandler      import guiHandler
from zopra.core.elements.Styles.Default import ssiA, ssiA_VISITED


class Dialog(hgDialog, guiHandler):
    """\class Dialog"""

    # class variables
    _className = 'Dialog'
    _classType = hgDialog._classType + [_className]
    _stdHeader = '<dtml-var standard_html_header>'
    _stdFooter = '<dtml-var standard_html_footer>'

    # button labels
    OK         = 'OK'
    APPLY      = 'Apply'
    CANCEL     = 'Cancel'
    NEXT       = 'Next'
    PREV       = 'Prev'
    BACK       = 'Back'

    EMBEDDED   = 2
    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
    # enum DialogType
    Standalone = 1
    Embedded   = 2
    DialogType = [ Standalone, Embedded ]

    ##########################################################################
    #
    # Static Methods
    #
    ##########################################################################
    def getBackButtonStr(REQUEST = None, prop = True):
        """\brief Returns a back button string.

        The function tries to keep track of how often a user should go back to a
        specific site. But it only works if the function gets a REQUEST object.

        \n
        \return back button string.
        """
        if REQUEST:

            if 'go' in REQUEST:
                number  = REQUEST['go']

                if isinstance(number, ListType):
                    number = number[0]

                back_go = int(number) - 1

            else:
                back_go -= 1

            btn_go = hgPushButton(' Back ')
            btn_go.setFunction('history.go(%s)' % back_go, True)
            retstr = btn_go.getHtml()

            if prop:
                retstr += hgProperty('go', back_go)

            return retstr

        else:
            btn_go = hgPushButton(' Back ')
            btn_go.setFunction('history.back()', True)
            return btn_go.getHtml()
    getBackButtonStr = staticmethod(getBackButtonStr)


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self,
                  manager = None,
                  title   = None,
                  parent  = None,
                  name    = None,
                  flags   = Standalone ):
        """\brief Constructs a ZMOMDialog."""

        # default title
        if title is None:
            title = 'Dialog'

        hgDialog.__init__(self, parent, None,
                          title  = title,
                          action = name,
                          name   = name)

        if flags & self.Standalone:
            self.setHeader( self._stdHeader )
            self.setFooter( self._stdFooter )

        elif flags & self.Embedded:
            self.setHeader('')
            self.setFooter('')
            self.setCaption('')

        self.error = None

        self._styleSheet.getSsiName( ssiA         )
        self._styleSheet.getSsiName( ssiA_VISITED )
        self.setSsiName( '.dlg_form'  )

        self.add( hgProperty( 'uid', self.name )  )

        # Next tab and save actual settings of the previous tab
        self._next          = hgPushButton(self.NEXT, parent = self)
        self._next.setToolTip('Save the settings and show the next tab.')

        # apply the settings to the current tab
        self._apply         = hgPushButton(self.APPLY, parent = self)
        self._apply.setToolTip('Save the settings of the current tab.')
        hgPushButton.connect(self._apply.clicked, self.applied)

        # ok apply settings and close dialog
        self._ok            = hgPushButton(self.OK, parent = self)
        self._ok.setToolTip('Save the settings and close the dialog.')
        hgPushButton.connect(self._ok.clicked, self.applied)
        hgPushButton.connect(self._ok.clicked, self.accept)

        # close dialog without saving settings
        self._cancel        = hgPushButton(self.CANCEL, parent = self)
        self._cancel.setToolTip('Do not save the settings and close the dialog')
        hgPushButton.connect(self._cancel.clicked, self.reject)


    def setName(self, name = None):
        """\brief Sets the name of the dialog."""
        hgDialog.setName(self, name)
        self.getForm().setAction(name)


    def applied(self):
        """\brief Abstract function will be called if signal applied is issued.
        """
        pass


    def setParam(self, key, value, manager):
        """\brief Virtual function to set arbitrary dialog parameter."""
        pass
