############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from types                              import StringType

from PyHtmlGUI                          import hg

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgGroupBox       import hgGroupBox
from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.elements.Styles.Default   import ssiDLG_LABEL

from zopra.core.constants               import TCN_AUTOID
from zopra.core.CorePart                import MASK_SHOW
                                               
from zopra.core.dialogs.guiHandler   import guiHandler

from zopra.core.secGUIPermission     import secGUIPermission

from zopra.core.tools.managers import TN_MUSER,       \
                                                    TCN_SIGNATURE


class dlgSignaturePrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.msgbox        = None
        self.btnbox        = None
        self.msg_count     = None
        self.updateButton  = None
        self.closeButton   = None
        self.helpButton    = None
        self.updateAccel   = None
        self.closeAccel    = None
        self.helpAccel     = None


class dlgSignature( hgDialog, guiHandler ):
    """\class dlgSignature

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgSignature'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Updated   = 3
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Signature'

        # dlg private data
        self.data = dlgSignaturePrivate()

        # init values
        self.resetData()

        self.muser = manager.getCurrentMUser()
        self.signature = self.muser.get(TCN_SIGNATURE, None)

        self.data.msg_count       = 0

        # create in nice tab order
        self.data.updateButton    = hgPushButton( parent = self, name = 'update'  )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )
        self.data.helpButton      = hgPushButton( parent = self, name = 'help'    )

        self.data.updateButton.setText ( '&Update'       )
        self.data.closeButton.setText  ( '&Close'        )
        self.data.helpButton.setText   ( '&Help'         )

        # connect the signals to the slots
        self.connect( self.data.updateButton.clicked,  self.update  )
        self.connect( self.data.helpButton.clicked,    self.help    )
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

        self.data.msgbox = self.layoutMessages(parent = page)
        page[1, 0] = self.data.msgbox

        self.data.btnbox = self.layoutButtons(parent = page)
        page[2, 0] = self.data.btnbox
        page.setCellAlignment(2, 0, 'center')


    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        user_dict = self.getDataDict()
        tobj = manager.tableHandler[TN_MUSER]

        # general information  
        if not widget:      
            widget = hgGroupBox(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        widget.caption = 'Configuration'
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        r = 0

        # signature
        label = tobj.getLabelWidget(TCN_SIGNATURE, parent = widget)
        label.setToolTip('Edit your signature') 
        wlay.addWidget( label, r, 0, hg.AlignTop )
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        entry = manager.getFunctionWidget(TN_MUSER,
                                          TCN_SIGNATURE,
                                          widget,
                                          MASK_EDIT,
                                          user_dict)
        entry.setSize(50, 5)
        entry.connect( entry.textChanged, self.setSignature   )

        wlay.addWidget(entry, r, 2)
        r += 1
        
        return widget
        

    def layoutMessages(self, widget = None, parent = None):
        """\brief Get the button layout."""
        
        if not widget:      
            widget = hgGroupBox(parent=parent)
            hgGridLayout( widget )
        else:
            widget.removeChildren()
        widget.caption = 'Message'

        return widget
        

    # todo: assert types of widget    
    def layoutButtons(self, widget = None, parent = None):
        """\brief Get the button layout."""
        if not widget:      
            widget = hgHBox(parent=parent)
            widget.layout().data.expanding = hgSizePolicy.NoDirection
        else:
            widget.removeChildren()
        
        widget.add( self.data.updateButton  )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.helpButton    )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.closeButton   )

        return widget
    

    def addMessage(self, message):
        """\brief Initialise the dialog layout."""
        
        if not self.data.msgbox:
            return
        
        if isinstance(message, StringType):
            message = hgLabel(message, parent = self.data.msgbox)
            
        assert(isinstance(message, hgWidget))
        
        self.data.msgbox.layout().addWidget(message, self.data.msg_count, 0)

        self.data.msg_count += 1


    def resetMessages(self):
        """\brief Initialise the dialog layout."""
        
        if not self.data.msgbox:
            return
        
        self.data.msgbox.removeChildren()

        self.data.msg_count = 0


    # data manipulation
    def setSignature(self, text):
        """\brief Sets the signature."""

        self.signature = str(text)


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        self.muser[TCN_SIGNATURE] = self.signature        
        
        return self.muser
        
        
    def resetData(self):
        """"""
        self.signature = None
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_MUSER, secGUIPermission.SC_EDIT)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Updated:
            self.performUpdate(manager)
            self.setResult(self.Running)
        
        
    # button callbacks   
    def update(self):
        """"""
        self.setResult(self.Updated)


    def help(self):
        """"""
        self.resetMessages()
        self.addMessage('Edit signature and press \'Update\' to save.')


    def performRejected(self, manager):
        """\reimp"""
        self.resetMessages()


    def performUpdate(self, manager):
        """\reimp"""
        self.resetMessages()
        
        muser = self.getDataDict()
        
        if not manager.tableHandler[TN_MUSER].updateEntry(muser, muser[TCN_AUTOID]):
            manager.displayError('An error occured while updating signature.', 
                                 'Database error')
            
        self.addMessage('Updated signature.')
              
                    
