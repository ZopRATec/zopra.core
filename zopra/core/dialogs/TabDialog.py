############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
# \file ZMOMTabDialog.py
__revision__ = '0.1'

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.dialogs.hgTabDialog   import hgTabDialog

from zopra.core.elements.Styles.Default import ssiA, ssiA_VISITED
from zopra.core.dialogs.guiHandler      import guiHandler


class TabDialog(hgTabDialog, guiHandler):
    """\class TabDialog"""

    # class variables
    _className = 'TabDialog'
    _classType = hgTabDialog._classType + [_className]
    _stdHeader = '<dtml-var standard_html_header>'
    _stdFooter = '<dtml-var standard_html_footer>'

    # button labels
    OK         = ' OK '
    APPLY      = ' Apply '
    CANCEL     = ' Cancel '
    NEXT       = ' Next '
    PREV       = ' PREV '
    BACK       = ' Back '

    # enum DialogType
    Standalone = 1
    Embedded   = 2
    DialogType = [ Standalone, Embedded ]


    def __init__( self,
                  title  = 'Dialog',
                  parent = None,
                  name   = _className,
                  flags  = Standalone ):

        hgTabDialog.__init__(self, parent, None,
                                   title  = title,
                                   action = name,
                                   name   = name )

        # modify dialog type
        if flags & self.Standalone:
            self.setHeader(self._stdHeader)
            self.setFooter(self._stdFooter)

        elif flags & self.Embedded:
            self.setHeader('')
            self.setFooter('')
            self.setTitle('')

        self.style().getStyleSheet().getSsiName( ssiA         )
        self.style().getStyleSheet().getSsiName( ssiA_VISITED )
#         self.style().getStyleSheet().getSsiName( ssiDLG       )
#         self.style().getStyleSheet().getSsiName( ssiDLG_TITLE )
#         self.style().getStyleSheet().getSsiName( ssiDLG_FORM  )
#         self.setSsiName      ( '.dlg_form' )
#         self.getForm().setSsiName( '.dlg_form' )

        # Next tab and save actual settings of the previous tab
        self._next          = hgPushButton(self.NEXT)
        self._next.setToolTip('Save the settings and show the next tab.')

        # apply the settings to the current tab
        self._apply         = hgPushButton(self.APPLY)
        self._apply.setToolTip('Save the settings of the current tab.')

        # ok apply settings and close dialog
        self._ok            = hgPushButton(self.OK)
        self._ok.setToolTip('Save the settings and close the dialog.')
        hgPushButton.connect(self._ok.clicked, self.accept)

        # close dialog without saving settings
        self._cancel        = hgPushButton(self.CANCEL)
        self._cancel.setToolTip('Do not save the settings and close the dialog')
        hgPushButton.connect(self._cancel.clicked, self.reject)

        # using those functions from guiHandler now
#    def _foundWidgetFunction(self, widget, value, manager):
#        """\brief Abstract function should be reimplemented in subclasses."""
#        pass
#
#
#    def _processEvents(self, widget, form, manager):
#        """\brief This function processes all events that occure."""
#        if form.has_key(widget.name):
#            self._foundWidgetFunction(widget, form[widget.name], manager)
#            del form[widget.name]
#
#
#        if widget.hasChildren():
#            for child in widget.children():
#                self._processEvents(child, form, manager)
#
#
#    def execDlg(self, manager = None, REQUEST = None):
#        """\brief Evaluates the REQUEST object and determines the next action.
#        """
#        if REQUEST and hasattr(REQUEST, 'form'):
#            self._processEvents(self.getForm(), REQUEST.form, manager)


    def setName(self, name = None):
        """\brief Sets the name of the dialog."""
        hgTabDialog.setName(self, name)
        self.getForm().setAction(name)