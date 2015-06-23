############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgReadSMsg.py
__revision__ = '0.1'

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

from Products.ZMOM.ZMOMElements.Styles.Default   import ssiDLG_LABEL

from Products.ZMOM.ZMOMCorePart         import MASK_SHOW,   \
                                               TCN_AUTOID
                                               
from Products.ZMOM.dialogs.guiHandler   import guiHandler

from Products.ZMOM.secGUIPermission     import secGUIPermission

from Products.ZMOM.AuditAndSecurity.managers import TN_SENT,        \
                                                    TCN_OWNER,      \
                                                    TCN_DRAFT,      \
                                                    TCN_CONTENT,    \
                                                    TCN_SUBJECT,    \
                                                    TCN_SSENDER,    \
                                                    TCN_SRECEIVER,  \
                                                    IMG_BWD,        \
                                                    IMG_FWD,        \
                                                    IMG_BWD_INACT,  \
                                                    IMG_FWD_INACT


OP_FORWARD  = 'forward_sent'

SEND_OPS = [OP_FORWARD]

class dlgReadSMsgPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.page           = None
        self.folderbox      = None
        self.functionbox    = None
        self.databox        = None
        self.btnbox         = None
        self.msg_count      = None
        self.sendButton     = None
        self.deleteButton   = None
        self.prevButton     = None
        self.nextButton     = None
        self.closeButton    = None
        self.closeAccel     = None
        self.folderList     = None


class dlgReadSMsg( hgDialog, guiHandler ):
    """\class dlgReadSMsg

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgReadSMsg'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Send     =  3
    Delete   =  4
    Prev     =  5
    Next     =  6
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Read Sent Message'

        # dlg private data
        self.data = dlgReadSMsgPrivate()

        # init values
        self.resetData()
        
        self.muser = manager.getCurrentMUser()[TCN_AUTOID]

        try:
            self.id = int( param_dict.get('id') )
        except:
            manager.displayError('No valid message id provided', 'Error')
        
        if self.id:            
            self.msg = manager.tableHandler[TN_SENT].getEntry(self.id)
            
            if not self.msg:
                manager.displayError('No valid message id provided', 'Error')
                
            if self.msg.get(TCN_DRAFT):
                self.draft   = True
                self.caption = 'Read Message Draft'
            else:
                self.draft   = False
                
        else:
            manager.displayError('No valid message id provided', 'Error')


        # init buttons
        fwd_icon = manager.iconHandler.get(IMG_FWD, path=True).getIconDict()
        bwd_icon = manager.iconHandler.get(IMG_BWD, path=True).getIconDict()        

        self.data.sendButton      = hgPushButton( parent = self, name = 'send'     )
        self.data.deleteButton    = hgPushButton( parent = self, name = 'delete'   )
        self.data.prevButton      = hgPushButton( parent = self, name = 'prev',  icon = bwd_icon )
        self.data.nextButton      = hgPushButton( parent = self, name = 'next',  icon = fwd_icon )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'    )

        if self.draft:
            self.data.sendButton.setText    ( '&Edit and Send'     )
        else:
            self.data.sendButton.setText    ( '&Forward'     )
            
        self.data.deleteButton.setText   ( '&Delete'    )
        self.data.nextButton.setText     ( '&Next'      )
        self.data.prevButton.setText     ( '&Prev'      )
        self.data.closeButton.setText    ( '&Close'     )

        self.data.deleteButton.setToolTip   ( 'Delete'           )
        self.data.nextButton.setToolTip     ( 'Next Message'     )
        self.data.prevButton.setToolTip     ( 'Previous Message' )
        self.data.closeButton.setToolTip    ( 'Close'            )

        # connect the signals to the slots
        self.connect( self.data.sendButton.clicked,     self.send      )
        self.connect( self.data.deleteButton.clicked,   self.delete     )
        self.connect( self.data.prevButton.clicked,     self.prev       )
        self.connect( self.data.nextButton.clicked,     self.next       )
        self.connect( self.data.closeButton.clicked,    self.reject     )
        
        # init layout
        self.initLayout(manager)

        # set dlg target
        url    = manager.absolute_url()
        if self.draft:
            self.defaulttarget = '%s/dlgHandler/dlgSMessageCenter/show?folder=%s' % (url, manager.FLD_DRAFTS)
        else:
            self.defaulttarget = '%s/dlgHandler/dlgSMessageCenter/show?folder=%s' % (url, manager.FLD_OUTBOX)
        

    # layout
    def initLayout(self, manager):
        """\brief Initialise the dialog layout."""

        # create layout
        if not self.data.page:
            page   = hgWidget(parent = self.getForm())
            layout = hgGridLayout( page, 3, 2 )

            self.getForm().add(page)
            self.data.page = page
        else:
            page = self.data.page
            page.removeChildren()
            layout = page.layout()
        
        self.data.folderbox = self.layoutFolder(manager, parent = page)
        layout.addWidget(self.data.folderbox, 0, 0)

        self.data.functionbox = self.layoutFunctions(manager, parent = page)
        layout.addWidget(self.data.functionbox, 1, 0)

        self.data.databox = self.layoutData(manager, parent = page)
        layout.addWidget(self.data.databox, 2, 0)

        self.data.btnbox = self.layoutButtons(parent = page)
        layout.addWidget(self.data.btnbox, 3, 0, hg.AlignHCenter)
        #page.setCellAlignment(3, 0, 'center')


    def layoutFolder(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        msg = self.getDataDict()
        tobj = manager.tableHandler[TN_SENT]

        # general information  
        if not widget:      
            widget = hgGroupBox(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        c = 0
        
        # print foldername
        if self.draft:
            foldlab = hgLabel(manager.FLD_DRAFTS, parent = widget)
        else:
            foldlab = hgLabel(manager.FLD_OUTBOX, parent = widget)
        
        wlay.addWidget( foldlab, 0, c )

        c += 1

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c)
        
        c += 1
        
        # get the message counts
        constraints = { TCN_DRAFT:   int(self.draft),
                        TCN_SSENDER: self.muser }
        
        total    = manager.tableHandler[TN_SENT].getRowCount( constraints )
        
        constraints[TCN_AUTOID] = '_<=_' + str(self.id)
        current  = manager.tableHandler[TN_SENT].getRowCount( constraints )
        
        # total navig
        box = hgHBox( parent = widget )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        if current == 1:
            img = manager.iconHandler.getImageObject(IMG_BWD_INACT)
            bwd = hgLabel(img.tag(), parent = box)
        else:
            bwd = self.data.prevButton
            self.data.prevButton.reparent(box)

        box.add( bwd )
        
        box.add( hgLabel('&nbsp;%s of %s&nbsp;' % (current, total), parent = box) )        

        if current == total:
            img = manager.iconHandler.getImageObject(IMG_FWD_INACT)
            fwd = hgLabel(img.tag(), parent = box)
        else:
            fwd = self.data.nextButton
            self.data.nextButton.reparent(box)

        box.add( fwd )
        
        wlay.addWidget( box, 0, c )
        c += 1
        
        return widget
    

    def layoutFunctions(self, widget = None, parent = None):
        """\brief Get the button layout."""
        #if not widget:      
        widget = hgHBox(parent=parent)
        widget.layout().data.expanding = hgSizePolicy.NoDirection
        #else:
        #    widget.removeChildren()
        
        widget.add( self.data.sendButton   )
        widget.add( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget)     )        
        widget.add( self.data.deleteButton   )

        return widget

    
    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        msg = self.getDataDict()
        tobj = manager.tableHandler[TN_SENT]

        # another check
        if msg.get(TCN_SSENDER) != self.muser:
            manager.displayError('You are not owner of this message.', 'Access Error')
            
        # 
        tab = hgTable(parent = parent)
        
        widget = hgWidget(parent=tab)
        wlay   = hgGridLayout( widget, 12, 4 )

        widget._styleSheet.add(ssiDLG_LABEL)

        r = 0
        

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)

        # subject
        label = tobj.getLabelWidget(TCN_SUBJECT, parent = widget)
        label.setToolTip('Subject of the Message') 
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_SENT,
                                          TCN_SUBJECT,
                                          widget,
                                          MASK_SHOW,
                                          msg)
        wlay.addWidget(entry, r, 2)
        r += 1
        
        # from
        label = tobj.getLabelWidget(TCN_SSENDER, parent = widget)
        label.setToolTip('Sender of the Message') 
        label.setText('From:')
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_SENT,
                                          TCN_SSENDER,
                                          widget,
                                          MASK_SHOW,
                                          msg)
        wlay.addWidget(entry, r, 2)
        r += 1
        
        # recipients
        label = tobj.getLabelWidget(TCN_SRECEIVER, parent = widget)
        label.setText('To:')
        label.setToolTip('Recipients of the Message') 
        wlay.addWidget( label, r, 0, hg.AlignTop)
        entry = manager.getFunctionWidget(TN_SENT,
                                          TCN_SRECEIVER,
                                          widget,
                                          MASK_SHOW,
                                          msg)

        wlay.addWidget(entry, r, 2)
        r += 1
        
        # date
        # just get any label widget and set desired text afterwards (saves label formatting)
        label = tobj.getLabelWidget(TCN_SRECEIVER, parent = widget)
        label.setText('Date:')
        label.setToolTip('Sending date of the Message') 
        wlay.addWidget( label, r, 0)
        entry = hgLabel(str(msg['entrydate']), parent = widget)

        wlay.addWidget(entry, r, 2)
        r += 1

        # finish header
        tab[0, 0] = widget
        tab.setCellBackgroundColor(0, 0, '#E0E0DA')

        widget = hgWidget(parent=tab)
        wlay   = hgGridLayout( widget, 12, 4 )
        
        # content
        entry = manager.getFunctionWidget(TN_SENT,
                                          TCN_CONTENT,
                                          widget,
                                          MASK_SHOW,
                                          msg)

        wlay.addMultiCellWidget(entry, r, r, 0, 2)
        r += 1

        # finish body
        tab[1, 0] = widget
                
        return tab
        

    # todo: assert types of widget    
    def layoutButtons(self, widget = None, parent = None):
        """\brief Get the button layout."""
        if not widget:      
            widget = hgHBox(parent=parent)
            widget.layout().data.expanding = hgSizePolicy.NoDirection
        else:
            widget.removeChildren()
        
        widget.add( self.data.closeButton   )

        return widget
    

    # data manipulation
    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        return self.msg
        
        
    def resetData(self):
        """"""
        pass
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_SENT, secGUIPermission.SC_VIEW)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Send:
            self.performSend(manager)
        elif self.result() == self.Delete:
            self.performDelete(manager)
        elif self.result() == self.Prev:
            self.performPrev(manager)
            self.setResult(self.Running)
        elif self.result() == self.Next:
            self.performNext(manager)
            self.setResult(self.Running)
        
        
    # button callbacks stubs
    def send(self):
        """"""
        if self.draft:
            self.op = TCN_DRAFT
        else:
            self.op = OP_FORWARD
        self.setResult(self.Send)


    def delete(self):
        """"""
        self.setResult(self.Delete)


    def prev(self):
        """"""
        self.setResult(self.Prev)


    def next(self):
        """"""
        self.setResult(self.Next)


    # callback implementations
    def performRejected(self, manager):
        """\reimp"""
        self.setTarget(self.defaulttarget)
        self.target_url = self.defaulttarget


    def performSend(self, manager):
        """\reimp"""
        
        if not self.op in [OP_FORWARD, TCN_DRAFT]:
            return

        # set send dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, self.id, self.op)

        self.setTarget(target)
        self.target_url = target
        

    def performDelete(self, manager):
        """\reimp"""
        
        manager.deleteEntries(TN_SENT, [self.id])

        self.setTarget(self.defaulttarget)
        self.target_url = self.defaulttarget


    def performPrev(self, manager):
        """\reimp"""
        
        # get 1. entry with aid < self.id sort aid desc
        constraints = { TCN_AUTOID: '_<_' + str(self.id) }

        self.loadNewMsg(manager, constraints, 'desc')


    def performNext(self, manager):
        """\reimp"""
        
        # get 1. entry with aid > self.id sort aid desc
        constraints = { TCN_AUTOID: '_>_' + str(self.id) }

        self.loadNewMsg(manager, constraints, 'asc')


    def loadNewMsg(self, manager, constraints, direction):
        """\reimp"""
        
        tobj = manager.tableHandler[TN_SENT]        
        
        constraints[TCN_OWNER] = self.muser
        constraints[TCN_DRAFT] = int(self.draft)
        
        newmsg = tobj.getEntryList(show_number = 1, constraints = constraints, direction = direction)
        
        if not newmsg:
            manager.displayError('Couldn\'t find message.', 
                                 'Database error')
            
        self.id  = newmsg[0][TCN_AUTOID]
        self.msg = newmsg[0]
    
        self.initLayout(manager)


