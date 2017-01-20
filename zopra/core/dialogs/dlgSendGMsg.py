############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.elements.Styles.Default   import ssiDLG_LABEL

from zopra.core.constants               import TCN_AUTOID
from zopra.core.CorePart                import MASK_SHOW
                                               
from zopra.core.dialogs.guiHandler   import guiHandler

from zopra.core.secGUIPermission     import secGUIPermission

from zopra.core.tools.managers import TN_GLOBAL,      \
                                                    TCN_CONTENT,    \
                                                    TCN_SUBJECT,    \
                                                    TCN_GSENDER


class dlgSendGMsgPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.btnbox        = None
        self.sendButton    = None
        self.closeButton   = None
        self.sendAccel     = None
        self.closeAccel    = None


class dlgSendGMsg( hgDialog, guiHandler ):
    """\class dlgSendGMsg

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgSendGMsg'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Send  = 3
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        # get the security lvl
        zopratype = manager.getZopraType()
        perm = manager.getGUIPermission()
        self.super = perm.hasMinimumRole(perm.SC_SUPER)
        self.super = self.super or perm.hasSpecialRole(zopratype + 'Superuser')

        if not self.super:
            manager.displayError('You are not permitted to send global messages.', 'Security Error')
        
        self.caption = 'Send Global Message'

        # dlg private data
        self.data = dlgSendGMsgPrivate()

        # init values
        self.resetData()
        
        self.sender = manager.getCurrentMUser()[TCN_AUTOID]

        # create in nice tab order
        self.data.sendButton      = hgPushButton( parent = self, name = 'send'    )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )

        self.data.sendButton.setText   ( '&Send'         )
        self.data.closeButton.setText  ( '&Close'        )

        # connect the signals to the slots
        self.connect( self.data.sendButton.clicked,    self.send    )
        self.connect( self.data.closeButton.clicked,   self.reject  )

        self.initLayout(manager)


    # layout
    def initLayout(self, manager):
        """\brief Initialise the dialog layout."""

        # create layout
        page  = hgTable(parent = self.getForm())
        self.getForm().add(page)
        
        self.data.databox = self.layoutData(manager, parent = page)
        page[0, 0] = self.data.databox

        self.data.btnbox = self.layoutButtons(parent = page)
        page[1, 0] = self.data.btnbox
        page.setCellAlignment(1, 0, 'center')


    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        msg = self.getDataDict()
        tobj = manager.tableHandler[TN_GLOBAL]

        # general information  
        if not widget:      
            widget = hgWidget(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        r = 0

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)

        # subject
        label = tobj.getLabelWidget(TCN_SUBJECT, parent = widget)
        label.setToolTip('Subject of the Message') 
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_GLOBAL,
                                          TCN_SUBJECT,
                                          widget,
                                          MASK_EDIT,
                                          msg)
        entry.setSize(70)
        entry.connect( entry.textChanged, self.setSubject   )

        wlay.addWidget(entry, r, 2)
        r += 1
        
        # content
        entry = manager.getFunctionWidget(TN_GLOBAL,
                                          TCN_CONTENT,
                                          widget,
                                          MASK_EDIT,
                                          msg)
        entry.setSize(80, 10)
        entry.connect( entry.textChanged, self.setContent )

        wlay.addMultiCellWidget(entry, r, r, 0, 2)
        r += 1
        
        return widget
        

    # todo: assert types of widget    
    def layoutButtons(self, widget = None, parent = None):
        """\brief Get the button layout."""
        if not widget:      
            widget = hgHBox(parent=parent)
            widget.layout().data.expanding = hgSizePolicy.NoDirection
        else:
            widget.removeChildren()
        
        widget.add( self.data.sendButton  )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.closeButton   )

        return widget
    

    # data manipulation
    def setSubject(self, text):
        """\brief Sets the name for the new folder."""

        self.subject = str(text)


    def setContent(self, text):
        """\brief Sets the name for the new folder."""

        self.content = str(text)


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        msg = { TCN_SUBJECT: self.subject,
                TCN_CONTENT: self.content,
                TCN_GSENDER: self.sender
              }

        return msg
        
        
    def resetData(self):
        """"""

        self.subject   = ''
        self.content   = ''
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_GLOBAL, secGUIPermission.SC_INSERT)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Send:
            self.performSend(manager)        

        
    # button callbacks   
    def send(self):
        """"""
        self.setResult(self.Send)


    def performRejected(self, manager):
        """\reimp"""
        # set dlg target
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgGMessageCenter/show' % (url)

        self.setTarget(target)
        self.target_url = target


    def performSend(self, manager):
        """\reimp"""
        msg = self.getDataDict()

        msg_id = manager.tableHandler[TN_GLOBAL].addEntry(msg)
        if not msg_id:
            manager.displayError('An error occured while sending message.', 
                                     'Database error')
                
        # set confirmation dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgConfirm/show?table=%s&id=%s' % (url, TN_GLOBAL, msg_id)

        self.setTarget(target)
        self.target_url = target
