############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgSendMsg.py
__revision__ = '0.1'

from PyHtmlGUI                          import hg

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgCheckBox       import hgCheckBox
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.elements.Styles.Default   import ssiDLG_LABEL

from zopra.core.constants               import TCN_AUTOID
from zopra.core.CorePart                import MASK_SHOW
                                               
from zopra.core.dialogs.guiHandler   import guiHandler

from zopra.core.secGUIPermission     import secGUIPermission

from zopra.core.tools.managers import TN_THREAD,      \
                                                    TN_GLOBAL,      \
                                                    TN_LOCAL,       \
                                                    TN_SENT,        \
                                                    TN_MUSER,       \
                                                    TCN_GSENDER,    \
                                                    TCN_ORIGIN,     \
                                                    TCN_MSENT,      \
                                                    TCN_MRECV,      \
                                                    TCN_CONTENT,    \
                                                    TCN_SUBJECT,    \
                                                    TCN_SSENDER,    \
                                                    TCN_SRECEIVER,  \
                                                    TCN_REPLIESTO,  \
                                                    TCN_DRAFT,      \
                                                    TCN_LSENDER,    \
                                                    TCN_LRECEIVER,  \
                                                    TCN_OWNER,      \
                                                    TCN_READ,       \
                                                    TCN_TRASH,      \
                                                    TCN_THREAD,     \
                                                    TCN_FOLDER,     \
                                                    TCN_SIGNATURE


class dlgSendMsgPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.btnbox        = None
        self.sendButton    = None
        self.draftButton   = None
        self.closeButton   = None
        self.sendAccel     = None
        self.draftAccel    = None
        self.closeAccel    = None


class dlgSendMsg( hgDialog, guiHandler ):
    """\class dlgSendMsg

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgSendMsg'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Send  = 3
    Draft = 4
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Send Message'

        # dlg private data
        self.data = dlgSendMsgPrivate()

        # init values
        self.resetData()
        
        self.sender = manager.getCurrentMUser()[TCN_AUTOID]

        try:
            self.id = int( param_dict.get('id') )
        except:
            self.id = 0
        
        self.draft  = 0
        self.thread = 0
        
        folder = manager.FLD_INBOX
        
        if self.id:
            op = param_dict.get('op', 'reply')
            
            if op == TCN_DRAFT:
                msg = manager.tableHandler[TN_SENT].getEntry(self.id)
                
                if not msg or not msg.get(TCN_DRAFT):
                    manager.displayError('Couldn\'t find draft with specified id', 'Database Error')
                
                # set id to msg that is replied to
                self.draft = self.id
                self.id = msg.get(TCN_REPLIESTO, 0)
                
                self.receiver = msg.get(TCN_SRECEIVER, [])     
                
                # add content       
                self.subject = msg.get(TCN_SUBJECT, '')
                self.content = msg.get(TCN_CONTENT, '')
                
                folder = manager.FLD_DRAFTS
            elif op in ['reply', 'replyall', 'forward', 'forward_sent', manager.FLD_GLOBAL]:
                if op == 'forward_sent':
                    msg = manager.tableHandler[TN_SENT].getEntry(self.id)
                    if not msg:
                        manager.displayError('Couldn\'t find message with specified id', 'Database Error')
                    msg[TCN_LSENDER]   = msg[TCN_SSENDER]
                    msg[TCN_LRECEIVER] = msg[TCN_SRECEIVER]
                    # mark forwarded sent messages
                    self.id *= -1
                    folder = manager.FLD_OUTBOX
                elif op == manager.FLD_GLOBAL:
                    msg = manager.tableHandler[TN_GLOBAL].getEntry(self.id)
                
                    if not msg:
                        manager.displayError('Couldn\'t find message with specified id', 'Database Error')
                    msg[TCN_LSENDER]   = msg[TCN_GSENDER]
                    msg[TCN_THREAD]    = None
                
                    # set id to msg that is replied to
                    self.id    = 0
                
                    self.receiver = [ msg[TCN_GSENDER] ]
                
                    folder = manager.FLD_GLOBAL
                else:
                    msg = manager.tableHandler[TN_LOCAL].getEntry(self.id)
                    if not msg:
                        manager.displayError('Couldn\'t find message with specified id', 'Database Error')
                    
                    if msg.get(TCN_TRASH):
                        self.folder = manager.FLD_TRASH
                    else:
                        self.folder = msg.get(TCN_FOLDER, manager.FLD_INBOX)
                    

                date = msg['entrydate']

                header  = '> From: %s\n' % manager.getLabelString(TN_MUSER, msg[TCN_LSENDER])
                header += '> Date: %s\n' % msg['entrydate']
                if op != manager.FLD_GLOBAL:
                    header += '> To: %s' % manager.getLabelString(TN_MUSER, msg[TCN_LRECEIVER][0])
                    for recipient in msg[TCN_LRECEIVER][1:]:
                        header += ', %s' % manager.getLabelString(TN_MUSER, recipient)
                header += '>\n'
                header += '> Subject: %s\n' % msg.get(TCN_SUBJECT, '')
                header += '>\n'

                if op == 'reply':
                    self.receiver = [ msg[TCN_LSENDER] ]
                elif op == 'replyall':
                    self.receiver = msg[TCN_LRECEIVER]
                    self.receiver.remove(self.sender)

                    self.receiver.append( msg[TCN_LSENDER] )

                self.content = header

                if op in ['forward', 'forward_sent']:
                    self.subject = 'Fwd: ' + msg.get(TCN_SUBJECT, '')
                    self.content += 'Begin forwarded message:\n'
                else:
                    self.subject = 'Re: ' + msg.get(TCN_SUBJECT, '')
                    self.content += 'Begin original message:\n'

                content = msg.get(TCN_CONTENT, '')
                content = content.split('\n')
                for line in content:
                    self.content += '> ' + line + '\n'
            else:
                manager.displayError('Unknown operation', 'Error')   
                    
            self.thread = msg[TCN_THREAD]

        # send msg to user
        if not self.id and not self.draft:
            if param_dict.get(TCN_LRECEIVER):
                try:
                    receiver = int(param_dict[TCN_LRECEIVER])
                except:
                    manager.displayError('Couldn\'t find recipient with specified id', 'Database Error')
                    
                self.receiver = [ receiver ]
                rdict = manager.tableHandler[TN_MUSER].getEntry(receiver)
                if not rdict:
                    manager.displayError('Couldn\'t find recipient with specified id', 'Database Error')

        # create in nice tab order
        self.data.sendButton      = hgPushButton( parent = self, name = 'send'    )
        self.data.draftButton     = hgPushButton( parent = self, name = 'draft'   )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )

        self.data.sendButton.setText   ( '&Send'         )
        self.data.draftButton.setText  ( '&Draft'        )
        self.data.closeButton.setText  ( '&Close'        )

        # connect the signals to the slots
        self.connect( self.data.sendButton.clicked,    self.send     )
        self.connect( self.data.draftButton.clicked,   self.draftMsg )
        self.connect( self.data.closeButton.clicked,   self.reject   )

        self.initLayout(manager)

        # set dlg target
        url    = manager.absolute_url()
        if folder in [manager.FLD_DRAFTS, manager.FLD_OUTBOX]:
            self.closetarget = '%s/dlgHandler/dlgSMessageCenter/show?folder=%s' % (url, folder)
        elif folder == manager.FLD_GLOBAL:
            self.closetarget = '%s/dlgHandler/dlgGMessageCenter/show' % (url)
        else:
            self.closetarget = '%s/dlgHandler/dlgMessageCenter/show?folder=%s' % (url, folder)


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
        msg = self.getDataDict(TN_LOCAL)
        tobj = manager.tableHandler[TN_LOCAL]

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
        r += 1

        # recipients
        label = tobj.getLabelWidget(TCN_LRECEIVER, parent = widget)
        label.setText('To')
        label.setToolTip('Recipients of the Message') 
        wlay.addWidget( label, r, 0, hg.AlignTop )
        entry = manager.getFunctionWidget(TN_LOCAL,
                                          TCN_LRECEIVER,
                                          widget,
                                          MASK_EDIT,
                                          msg)
        entry.connect( entry.selectionValueAdded,   self.addReceiver )
        entry.connect( entry.selectionValueRemoved, self.delReceiver )
        
        # HACK
        entry.addbtn.setText('Add Recipient')
        entry.rembtn.setText('Remove Recipient')

        wlay.addWidget(entry, r, 2)
        r += 1
        
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1
        # subject
        label = tobj.getLabelWidget(TCN_SUBJECT, parent = widget)
        label.setToolTip('Subject of the Message') 
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_LOCAL,
                                          TCN_SUBJECT,
                                          widget,
                                          MASK_EDIT,
                                          msg)
        entry.setSize(70)
        entry.connect( entry.textChanged, self.setSubject   )

        wlay.addWidget(entry, r, 2)
        r += 1
        
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        # content
        entry = manager.getFunctionWidget(TN_LOCAL,
                                          TCN_CONTENT,
                                          widget,
                                          MASK_EDIT,
                                          msg)
        entry.setSize(80, 20)
        entry.connect( entry.textChanged, self.setContent )

        wlay.addMultiCellWidget(entry, r, r, 0, 2)
        r += 1
        
        # signature
        self.sig_cb = hgCheckBox(text = 'Append Signature', value = 'Append Signature', name = 'signature', parent = widget)
        self.sig_cb.setToolTip('Append Signature to Message') 
        wlay.addMultiCellWidget( self.sig_cb, r, r, 0, 2)
        self.connect( self.sig_cb.stateChanged, self.setSignature )
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
        widget.add( self.data.draftButton   )
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


    def addReceiver(self, receiver):
        """\brief Sets the name for the new folder."""

        try:
            int(receiver)
        except:
            return
        
        self.receiver.append(receiver)


    def delReceiver(self, receiver):
        """\brief Sets the name for the new folder."""

        try:
            int(receiver)
            self.receiver.remove(receiver)
        except:
            return
        


    def setSignature(self, state):
        """\brief Sets the name for the new folder."""

        self.signature = self.sig_cb.isChecked()


    def getDataDict(self, table):
        """\brief Get entry dict from dialog data."""
        
        dict = { TCN_SUBJECT: self.subject,
                 TCN_CONTENT: self.content
               }

        if self.thread:        
            dict[TCN_THREAD] = self.thread
            
        if table == TN_SENT:
            dict[TCN_DRAFT] = 0
            if self.id:
                dict[TCN_REPLIESTO] = self.id
            dict[TCN_SSENDER]   = self.sender
            dict[TCN_SRECEIVER] = self.receiver
        elif table == TN_LOCAL:
            dict[TCN_LSENDER]   = self.sender
            dict[TCN_LRECEIVER] = self.receiver
            dict[TCN_TRASH]     = 0
            dict[TCN_READ]      = 0
        else:
            return {}
        
        return dict
        
        
    def resetData(self):
        """"""

        self.receiver  = []           
        self.subject   = ''
        self.content   = ''
        self.signature = False
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_LOCAL, secGUIPermission.SC_INSERT)
            manager.checkGUIPermission(TN_SENT,  secGUIPermission.SC_INSERT)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Send:
            self.performSend(manager)
        elif self.result() == self.Draft:
            self.performDraft(manager)
        
        
    # button callbacks   
    def send(self):
        """"""
        self.setResult(self.Send)


    def draftMsg(self):
        """"""
        self.setResult(self.Draft)


    def performRejected(self, manager):
        """\reimp"""
        self.setTarget(self.closetarget)
        self.target_url = self.closetarget


    def performSend(self, manager):
        """\reimp"""
        
        if not self.receiver:
            manager.displayError('Recipient missing.', 'Error')
        
        # create new thread if necessary
        if not self.thread:
            thread = { TCN_SUBJECT: self.subject, 
                       TCN_ORIGIN:  self.sender,
                       TCN_MSENT:   1,
                       TCN_MRECV:   len(self.receiver)}
            self.thread = manager.tableHandler[TN_THREAD].addEntry(thread)
            if not self.thread:
                manager.displayError('An error occured while creating thread.', 
                                     'Database error')
        else:
            thread = manager.getEntry(TN_THREAD, self.thread)
            
            if not thread:
                manager.displayError('Thread not found.', 
                                     'Database error')
            
            thread[TCN_MSENT] += 1
            thread[TCN_MRECV] += len(self.receiver)
            if not manager.tableHandler[TN_THREAD].updateEntry( thread, thread[TCN_AUTOID] ):
                manager.displayError('An error occured while updating thread.', 
                                     'Database error')
        # sent message 
        smsg = self.getDataDict(TN_SENT)
        
        if self.draft:
            if not manager.tableHandler[TN_SENT].updateEntry(smsg, self.draft):
                manager.displayError('An error occured while saving message.', 
                                     'Database error')
            sid = smsg[TCN_AUTOID]
        else:
            sid = manager.tableHandler[TN_SENT].addEntry(smsg)
            if not sid:
                manager.displayError('An error occured while saving message.', 
                                     'Database error')
                
        # local message
        lmsg = self.getDataDict(TN_LOCAL)
                
        if self.signature:
            lmsg[TCN_CONTENT] += '\n' + manager.getCurrentMUser().get(TCN_SIGNATURE, '')
        
        for receiver in lmsg[TCN_LRECEIVER]:
            lmsg[TCN_OWNER] = receiver
            
            # apply user filters to set target folder
            manager.filterMessage(lmsg)
            
            if not manager.tableHandler[TN_LOCAL].addEntry(lmsg):
                manager.displayError('An error occured while sending message.', 
                                     'Database error')            

        # set confirmation dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgConfirm/show?table=%s&id=%s' % (url, TN_SENT, sid)

        self.setTarget(target)
        self.target_url = target

                    
    def performDraft(self, manager):
        """\reimp"""
        smsg = self.getDataDict(TN_SENT)
        
        smsg[TCN_DRAFT] = 1
        
        if self.draft:
            if not manager.tableHandler[TN_SENT].updateEntry(smsg, self.draft):
                manager.displayError('An error occured while saving message to draft.', 
                                     'Database error')
            sid = self.draft
        else:
            sid = manager.tableHandler[TN_SENT].addEntry(smsg)
            if not sid:
                manager.displayError('An error occured while saving message to draft.', 
                                     'Database error')
            
        # set confirmation dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgConfirm/show?table=%s&id=%s' % (url, TN_SENT, sid)

        self.setTarget(target)
        self.target_url = target
              
                    
