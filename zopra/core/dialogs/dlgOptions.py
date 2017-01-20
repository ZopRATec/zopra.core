############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgOptions.py
__revision__ = '0.1'

from types                              import StringType

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
                                                    TCN_ENTRIESPP,  \
                                                    TCN_THREADVIEW


class dlgOptionsPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.msgbox        = None
        self.btnbox        = None
        self.msg_count     = None
        self.resetButton   = None
        self.updateButton  = None
        self.closeButton   = None
        self.helpButton    = None
        self.resetAccel    = None
        self.updateAccel   = None
        self.closeAccel    = None
        self.helpAccel     = None


class dlgOptions( hgDialog, guiHandler ):
    """\class dlgOptions

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgOptions'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Updated   = 3
    Resetted  = 4
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Options'

        # dlg private data
        self.data = dlgOptionsPrivate()

        # init values
        self.resetData()

        self.muser = manager.getCurrentMUser()
        self.entriespp = self.muser.get(TCN_ENTRIESPP)
        try:
            int(self.entriespp)
        except:
            self.entriespp = -1
        self.threadview = self.muser.get(TCN_THREADVIEW, 0) == 1

        self.data.msg_count       = 0

        # create in nice tab order
        self.data.updateButton    = hgPushButton( parent = self, name = 'update'  )
        self.data.resetButton     = hgPushButton( parent = self, name = 'reset'   )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )
        self.data.helpButton      = hgPushButton( parent = self, name = 'help'    )

        self.data.updateButton.setText ( '&Update'       )
        self.data.resetButton.setText  ( '&Default'      )
        self.data.closeButton.setText  ( '&Close'        )
        self.data.helpButton.setText   ( '&Help'         )

        # connect the signals to the slots
        self.connect( self.data.updateButton.clicked,  self.update  )
        self.connect( self.data.resetButton.clicked,   self.default )
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

        # entries per page
        label = tobj.getLabelWidget(TCN_ENTRIESPP, parent = widget)
        label.setToolTip('# of entries per page in mail folders') 
        wlay.addWidget( label, r, 0)
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        entry = manager.getFunctionWidget(TN_MUSER,
                                          TCN_ENTRIESPP,
                                          widget,
                                          MASK_EDIT,
                                          user_dict)
        entry.setSize(10)
        entry.connect( entry.textChanged, self.setEntriesPP   )
        self.epp_edit = entry

        wlay.addWidget(entry, r, 2)
        r += 1
        
        # threadview
        label = tobj.getLabelWidget(TCN_THREADVIEW, parent = widget)
        label.setToolTip('Group mails by thread') 
        wlay.addWidget( label, r, 0)
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        entry = manager.getFunctionWidget(TN_MUSER,
                                          TCN_THREADVIEW,
                                          widget,
                                          MASK_EDIT,
                                          user_dict)
        entry.connect( entry.stateChanged, self.setThreadview   )
        self.tv_cb = entry

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
        widget.add( self.data.resetButton   )
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
    def setEntriesPP(self, value):
        """\brief Sets number of entries per page for folder view."""

        try:
            value = int(value)
        except:
            #self.epp_edit.setText( str(self.entriespp) )
            return

        if value < 1:
            self.epp_edit.setText('1')
            
        self.entriespp = value


    def setThreadview(self, state):
        """\brief Enables/disables sorting by thread."""

        self.threadview = self.tv_cb.isChecked()


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        self.muser[TCN_ENTRIESPP] = self.entriespp
        if self.threadview:
            self.muser[TCN_THREADVIEW] = 1
        else:
            self.muser[TCN_THREADVIEW] = 0
        
        return self.muser
        
        
    def resetData(self):
        """"""
        self.entriespp  = 20
        self.threadview = False
        
        
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
        elif self.result() == self.Resetted:
            self.performReset(manager)
            self.setResult(self.Running)
        
        
    # button callbacks   
    def update(self):
        """"""
        self.setResult(self.Updated)


    def default(self):
        """"""
        self.setResult(self.Resetted)


    def help(self):
        """"""
        self.resetMessages()
        self.addMessage('Edit settings and press \'Update\' to save.')
        #self.addMessage('Set \'Entries per Page\' to -1 for unlimited.')


    def performRejected(self, manager):
        """\reimp"""
        self.resetMessages()


    def performUpdate(self, manager):
        """\reimp"""
        self.resetMessages()
        
        muser = self.getDataDict()
        
        if muser[TCN_ENTRIESPP] < 1:
            muser[TCN_ENTRIESPP] = 1
            
        
        if not manager.tableHandler[TN_MUSER].updateEntry(muser, muser[TCN_AUTOID]):
            manager.displayError('An error occured while updating settings.', 
                                 'Database error')
            
        self.addMessage('Updated settings.')
              
                    
    def performReset(self, manager):
        """\reimp"""
        self.resetMessages()
        
        self.resetData()
        muser = self.getDataDict()
        
        if not manager.tableHandler[TN_MUSER].updateEntry(muser, muser[TCN_AUTOID]):
            manager.displayError('An error occured while updating settings.', 
                                 'Database error')
            
        # update widgets
        self.epp_edit.setText( '20' )
        self.tv_cb.setChecked( False )
            
        self.addMessage('Updated to default settings.')
              
                    
