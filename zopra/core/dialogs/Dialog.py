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
# PyHtmlGUI Imports
#
from PyHtmlGUI.dialogs.hgDialog import hgDialog
from PyHtmlGUI.widgets.hgLabel import hgProperty
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
#
# ZopRA Imports
#
from zopra.core.dialogs.guiHandler import guiHandler
from zopra.core.elements.Styles.Default import ssiA
from zopra.core.elements.Styles.Default import ssiA_VISITED


class Dialog(hgDialog, guiHandler):
    """\class Dialog"""

    # class variables
    _className = 'Dialog'
    _classType = hgDialog._classType + [_className]

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
    # Instance Methods
    #
    ##########################################################################
    def __init__( self,
                  manager = None,
                  title   = 'Dialog',
                  parent  = None,
                  name    = None,
                  flags   = guiHandler.Standalone ):
        """\brief Constructs a Dialog."""

        hgDialog.__init__(self, parent, None, title, name, name)

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
