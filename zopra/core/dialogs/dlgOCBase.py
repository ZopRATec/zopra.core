############################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                    #
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

from PyHtmlGUI.widgets.hgLabel              import hgLabel
from PyHtmlGUI.widgets.hgPushButton         import hgPushButton
from PyHtmlGUI.dialogs.hgDialog             import hgDialog
from PyHtmlGUI.kernel.hgWidget              import hgWidget

from zopra.core.dialogs.guiHandler          import guiHandler

# buttons
OK         = 'OK'
CANCEL     = 'Cancel'
CLOSE      = 'Close'
UNDO       = 'Undo'

# states
ST_WORK     = 0
ST_FINALIZE = 1
ST_FINAL    = 2
ST_UNDO    = 3

class dlgOCBase(hgDialog, guiHandler):
    """\brief A Basic Okay-Cancel-Dialog with a layout and a
            finalLayout (second page) for results. An undo-button is also available.
            The hook functions can be overwritten for dialog action."""
    _className = "dlgOCBase"
    _classType = hgDialog._classType + [_className]

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a dlgOCBase, call this after attribute init."""
        hgDialog.__init__(self)
        guiHandler.__init__(self)

        #TODO make undo optional
        self.enable_undo = False
        if param_dict.get('undo'):
            self.enable_undo = True
        # state
        self.internalState = ST_WORK
        # message
        self.messageLabel  = None
        # alternative after-finalize-target url
        self.target_url    = None

        # init functions
        self.initWidgets()
        self.buildLayout(manager, self.usr_workWidget)
        self.buildFinalLayout(manager, self.usr_endWidget)
        self.showWork()

    def initWidgets(self):
        """\brief Constructs the common widgets."""
        # main work Widget
        self.workWidget = hgWidget(parent = self)
        self.usr_workWidget = hgWidget(parent = self.workWidget)

        # main final widget
        self.endWidget  = hgWidget(parent = self)
        self.usr_endWidget = hgWidget(parent = self.endWidget)

        # message Label
        self.messageLabel1 = hgLabel(parent = self.workWidget)
        self.messageLabel2 = hgLabel(parent = self.endWidget)

        # horizontal rows
        hgLabel('<hr>', parent = self.workWidget)
        hgLabel('<hr>', parent = self.endWidget)

        # ok apply settings and show results
        self._btn_ok     = hgPushButton(OK, parent = self.workWidget)
        self._btn_ok.setToolTip('Save and show final report.')
        hgPushButton.connect(self._btn_ok.clicked, self._sl_finalize)

        # close dialog without saving settings
        self._btn_cancel = hgPushButton(CANCEL, parent = self.workWidget)
        self._btn_cancel.setToolTip('Do not save and close the dialog.')
        hgPushButton.connect(self._btn_cancel.clicked, self._sl_reject)

        # apply settings and close dialog
        self._btn_close  = hgPushButton(CLOSE, parent = self.endWidget)
        self._btn_close.setToolTip('Close the dialog.')
        hgPushButton.connect(self._btn_close.clicked, self._sl_accept)

        if self.enable_undo:
            # undo changes and return to normal screen
            self._btn_undo   = hgPushButton(UNDO, parent = self.endWidget)
            self._btn_undo.setToolTip('Undo changes.')
            hgPushButton.connect(self._btn_undo.clicked, self._sl_undo)


    def showWork(self):
        """\brief Initialise the dialogs buttons"""

        # activate
        self.endWidget.hide()
        self.workWidget.show()
        self.workWidget.showChildren(True)


    def showFinal(self):
        """\brief Initialise the final page"""

        # activate
        self.workWidget.hide()
        self.endWidget.show()
        self.endWidget.showChildren(True)


    def setTargetUrl(self, url):
        self.target_url = url


    def buildLayout(self, manager, widget):
        """\brief Initialise the dialogs layout"""
        pass


    def updateLayout(self, manager, widget):
        """\brief change layout"""
        pass

    def buildFinalLayout(self, manager, widget):
        """\brief Show report."""
        pass

    def updateFinalLayout(self, manager, widget):
        """\brief Update report."""
        pass

    def setMessage(self, message):
        """\brief Set message."""
        self.messageLabel1.setText(message)
        self.messageLabel2.setText(message)


    def execDlg(self, manager = None, REQUEST = None):
        """\brief overwrites execDlg of parent class to get access to the manager."""
        # call parent function (processes REQUEST, changes widgets)
        guiHandler.execDlg(self, manager, REQUEST)

        # own calculations between signals and state evaluation / layout update
        self.execHook(manager, REQUEST)

        # updateLayout and state reset according to state
        # hide and show functions to ease layouting
        # because new children of visible widgets would be invisible

        if self.internalState == ST_FINALIZE:

            done = self.performDo(manager, REQUEST)
            if done:
                self.usr_endWidget.hide()
                self.updateFinalLayout(manager, self.usr_endWidget)
                self.showFinal()
                self.internalState = ST_FINAL
            else:
                self.internalState = ST_WORK
                self.usr_workWidget.hide()
                self.updateLayout(manager, self.usr_workWidget)
                self.showWork()
        elif self.internalState == ST_UNDO and self.enable_undo:
            undone = self.performUndo(manager, REQUEST)
            if undone:
                self.usr_workWidget.hide()
                self.updateLayout(manager, self.usr_workWidget)
                self.showWork()
                self.internalState = ST_WORK
            else:
                self.internalState = ST_FINAL
        elif self.internalState == ST_FINAL:
            self.usr_endWidget.hide()
            self.updateFinalLayout(manager, self.usr_endWidget)
            self.showFinal()
        elif self.internalState == ST_WORK:
            # layout update
            self.usr_workWidget.hide()
            self.updateLayout(manager, self.usr_workWidget)
            self.showWork()

# Slot functions

    def _sl_finalize(self):
        """\brief Set finalize flag."""
        self.internalState = ST_FINALIZE

    def _sl_undo(self):
        """\brief Set undo flag."""
        if self.enable_undo:
            self.internalState = ST_UNDO

    def _sl_reject(self):
        """\brief End of Dialog. Unsuccessful."""
        # reject hook
        self.performReject()
        # dispose and close (hgDialog function)
        self.reject()

    def _sl_accept(self):
        """\brief End of Dialog. Successful."""
        # accept hook
        self.performAccept()
        # dispose and close (hgDialog function)
        self.accept()


    def execHook(self, manager, REQUEST):
        """\brief Exec Hook for own calculations between signal-eval and
                 state-eval/layout-update."""
        pass

    def performDo(self, manager, REQUEST):
        """\brief Database action."""
        return True


    def performUndo(self, manager, REQUEST):
        """\brief Undo Database action."""
        return True

    def performAccept(self):
        """\brief Hook for final cleanup in accepted Dialog."""
        pass


    def performReject(self):
        """\brief Hook for final cleanup in rejected Dialog."""
        pass
