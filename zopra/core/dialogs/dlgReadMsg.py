############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgReadMsg.py
__revision__ = '0.1'

from PyHtmlGUI                          import hg

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgGroupBox       import hgGroupBox
from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgComboBox       import hgComboBox
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from PyHtmlGUI.stylesheet.hgStyleSheet  import hgStyleSheetItem

from zopra.core.elements.Styles.Default import ssiDLG_LABEL

from zopra.core.constants               import TCN_AUTOID
from zopra.core.CorePart                import MASK_SHOW
                                               
from zopra.core.dialogs.guiHandler      import guiHandler

from zopra.core.secGUIPermission        import secGUIPermission

from zopra.core.tools.managers          import TN_LOCAL,       \
                                                    TN_FOLDER,      \
                                                    TCN_CONTENT,    \
                                                    TCN_SUBJECT,    \
                                                    TCN_LSENDER,    \
                                                    TCN_LRECEIVER,  \
                                                    TCN_OWNER,      \
                                                    TCN_READ,       \
                                                    TCN_TRASH,      \
                                                    TCN_FOLDER,     \
                                                    TCN_SORTID,     \
                                                    TCN_FOLDERNAME, \
                                                    IMG_BWD,        \
                                                    IMG_FWD,        \
                                                    IMG_BWD_INACT,  \
                                                    IMG_FWD_INACT



OP_REPLY    = 'reply'
OP_REPLYALL = 'replyall'
OP_FORWARD  = 'forward'

SEND_OPS = [OP_REPLY, OP_REPLYALL, OP_FORWARD]

class dlgReadMsgPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.page           = None
        self.folderbox      = None
        self.functionbox    = None
        self.databox        = None
        self.btnbox         = None
        self.msg_count      = None
        self.replyButton    = None
        self.replyAllButton = None
        self.forwardButton  = None
        self.deleteButton   = None
        self.moveButton     = None
        self.prevButton     = None
        self.nextButton     = None
        self.uprevButton    = None
        self.unextButton    = None
        self.closeButton    = None
        self.closeAccel     = None
        self.folderList     = None


class dlgReadMsg( hgDialog, guiHandler ):
    """\class dlgReadMsg

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgReadMsg'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Send     =  3
    Delete   =  4
    Move     =  5
    Prev     =  6
    Next     =  7
    UPrev    =  8
    UNext    =  9
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Read Message'

        # dlg private data
        self.data = dlgReadMsgPrivate()

        # init values
        self.resetData()
        
        self.muser = manager.getCurrentMUser()[TCN_AUTOID]

        try:
            self.id = int( param_dict.get('id') )
        except:
            manager.displayError('No valid message id provided', 'Error')
        
        if self.id:            
            self.msg = manager.tableHandler[TN_LOCAL].getEntry(self.id)
            
            if not self.msg:
                manager.displayError('No valid message id provided', 'Error')
                
            if self.msg[TCN_OWNER] != self.muser:
                manager.displayError('Message belongs to another user. Access denied.', 'Security Error')
                
            if self.msg.get(TCN_TRASH):
                self.folder = manager.FLD_TRASH
            else:
                self.folder = self.msg.get(TCN_FOLDER, None)
                
        else:
            manager.displayError('No valid message id provided', 'Error')


        # init buttons
        fwd_icon = manager.iconHandler.get(IMG_FWD, path=True).getIconDict()
        bwd_icon = manager.iconHandler.get(IMG_BWD, path=True).getIconDict()        
        
        self.data.replyButton     = hgPushButton( parent = self, name = 'reply'    )
        self.data.replyAllButton  = hgPushButton( parent = self, name = 'replyall' )
        self.data.forwardButton   = hgPushButton( parent = self, name = 'forward'  )
        self.data.deleteButton    = hgPushButton( parent = self, name = 'delete'   )
        self.data.moveButton      = hgPushButton( parent = self, name = 'move'     )
        self.data.prevButton      = hgPushButton( parent = self, name = 'prev',  icon = bwd_icon )
        self.data.nextButton      = hgPushButton( parent = self, name = 'next',  icon = fwd_icon )
        self.data.uprevButton     = hgPushButton( parent = self, name = 'uprev', icon = bwd_icon )
        self.data.unextButton     = hgPushButton( parent = self, name = 'unext', icon = fwd_icon )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'    )

        self.data.replyButton.setText    ( '&Reply'       )
        self.data.replyAllButton.setText ( 'Reply &all'   )
        self.data.forwardButton.setText  ( '&Forward'     )
        self.data.deleteButton.setText   ( '&Delete'      )
        self.data.moveButton.setText     ( '&Move to'     )
        self.data.nextButton.setText     ( '&Next'        )
        self.data.prevButton.setText     ( '&Prev'        )
        self.data.unextButton.setText    ( 'Ne&xt Unread' )
        self.data.uprevButton.setText    ( 'Pre&v Unread' )
        self.data.closeButton.setText    ( '&Close'       )

        self.data.replyButton.setToolTip    ( 'Reply'       )
        self.data.replyAllButton.setToolTip ( 'Reply all'   )
        self.data.forwardButton.setToolTip  ( 'Forward'     )
        self.data.deleteButton.setToolTip   ( 'Delete'      )
        self.data.moveButton.setToolTip     ( 'Move to selected Folder' )
        self.data.nextButton.setToolTip     ( 'Next Message'            )
        self.data.prevButton.setToolTip     ( 'Previous Message'        )
        self.data.unextButton.setToolTip    ( 'Next Unread Message'     )
        self.data.uprevButton.setToolTip    ( 'Previous Unread Message' )
        self.data.closeButton.setToolTip    ( 'Close'       )

        # connect the signals to the slots
        self.connect( self.data.replyButton.clicked,    self.reply      )
        self.connect( self.data.replyAllButton.clicked, self.replyAll   )
        self.connect( self.data.forwardButton.clicked,  self.forward    )
        self.connect( self.data.deleteButton.clicked,   self.delete     )
        self.connect( self.data.moveButton.clicked,     self.move       )
        self.connect( self.data.prevButton.clicked,     self.prev       )
        self.connect( self.data.nextButton.clicked,     self.next       )
        self.connect( self.data.uprevButton.clicked,    self.unreadPrev )
        self.connect( self.data.unextButton.clicked,    self.unreadNext )
        self.connect( self.data.closeButton.clicked,    self.reject     )
        
        # init layout
        self.initLayout(manager)

        # set dlg target
        url    = manager.absolute_url()
        if self.folder:
            self.closetarget = '%s/dlgHandler/dlgMessageCenter/show?folder=%s' % (url, self.folder)
        else:
            self.closetarget = '%s/dlgHandler/dlgMessageCenter/show' % (url)
        

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
        
        self.markAsRead(manager)
        



    def layoutFolder(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        msg = self.getDataDict()
        tobj = manager.tableHandler[TN_LOCAL]

        # general information  
        if not widget:      
            widget = hgGroupBox(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
            # basket button fixed-with style
            ssiMSG_HEADLINE = hgStyleSheetItem( '.%s_headline' % manager.getId()  )
            ssiMSG_HEADLINE.position().size().setWidth( '100%' )
            widget._styleSheet.getSsiName( ssiMSG_HEADLINE )
            wlay.setSsiName( ssiMSG_HEADLINE.name() )            
        else:
            widget.removeChildren()
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        c = 0
        
        # print foldername
        if not self.folder:
            foldlab = hgLabel(manager.FLD_INBOX, parent = widget)
        elif self.folder == manager.FLD_TRASH:
            foldlab = hgLabel(manager.FLD_TRASH, parent = widget)
        else:
            fname = manager.getLabelString(TN_FOLDER, self.folder)
            foldlab = hgLabel(fname, parent = widget)
        
        wlay.addWidget( foldlab, 0, c )

        c += 1

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c)
        
        c += 1
        
        # get the message counts
        if not self.folder:
            constraints = { TCN_FOLDER: 'NULL', 
                            TCN_TRASH:  0,
                            TCN_OWNER:  self.muser } 
        elif self.folder == manager.FLD_TRASH:
            constraints = { TCN_TRASH:  1,
                            TCN_OWNER:  self.muser } 
        else:
            constraints = { TCN_FOLDER: self.folder, 
                            TCN_TRASH:  0 } 
            
        total    = manager.tableHandler[TN_LOCAL].getRowCount( constraints )
        
        constraints[TCN_AUTOID] = '_<=_' + str(self.id)
        current  = manager.tableHandler[TN_LOCAL].getRowCount( constraints )
        
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
        
        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c)
        c += 1
        
        # unread navig
        # get the message counts
        if not self.folder:
            constraints = { TCN_FOLDER: 'NULL', 
                            TCN_TRASH:  0,
                            TCN_OWNER:  self.muser } 
        elif self.folder == manager.FLD_TRASH:
            constraints = { TCN_TRASH:  1,
                            TCN_OWNER:  self.muser } 
        else:
            constraints = { TCN_FOLDER: self.folder, 
                            TCN_TRASH:  0 } 
        constraints[TCN_READ] = 0
        utotal = manager.tableHandler[TN_LOCAL].getRowCount( constraints )

        if self.msg.get(TCN_READ):
            ucurrent   = 0
        else:
            constraints[TCN_AUTOID] = '_<=_' + str(self.id)
            ucurrent   = manager.tableHandler[TN_LOCAL].getRowCount( constraints )
                
        box = hgHBox( parent = widget )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        if ucurrent <= 1:
            img = manager.iconHandler.getImageObject(IMG_BWD_INACT)            
            bwd = hgLabel(img.tag(), parent = box)
        else:
            bwd = self.data.uprevButton
            self.data.uprevButton.reparent(box)

        box.add( bwd )

        box.add( hgLabel('&nbsp;%s of %s unread&nbsp;' % (ucurrent, utotal), parent = widget) )        

        if ucurrent == utotal:
            img = manager.iconHandler.getImageObject(IMG_FWD_INACT)            
            fwd = hgLabel(img.tag(), parent = box)
        else:
            fwd = self.data.unextButton
            self.data.unextButton.reparent(box)
        box.add( fwd )

        wlay.addWidget( box, 0, c )
        c += 1

        return widget
    

    def layoutFunctions(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        #if not widget:      
        widget = hgHBox(parent=parent)
        widget.layout().data.expanding = hgSizePolicy.NoDirection
        #else:
        #    widget.removeChildren()
        
        widget.add( self.data.replyButton   )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.replyAllButton   )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.forwardButton   )
        widget.add( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget)     )
        widget.add( self.data.deleteButton   )
        widget.add( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget)     )
        
        # move selection box
        self.data.folderList = hgComboBox(name = 'movetarget', parent = widget)

        self.data.folderList.insertItem('Inbox', 'NULL')
        self.data.folderList.insertItem('Trash', 'Trash')
        
        folders = manager.tableHandler[TN_FOLDER].getEntries([self.muser], [TCN_OWNER], order = TCN_SORTID)
        
        for folder in folders:
            self.data.folderList.insertItem(folder[TCN_FOLDERNAME], folder[TCN_AUTOID])
            
        # select current folder
        if not self.folder:
            self.data.folderList.setCurrentValue('NULL')
        elif self.folder == manager.FLD_TRASH:
            self.data.folderList.setCurrentValue(self.folder)
        else:
            self.data.folderList.setCurrentValue(self.folder)
            
        self.connect( self.data.folderList.valueChanged, self.setFolder )
        
        widget.add( self.data.folderList   )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.moveButton   )

        return widget

    
    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        msg = self.getDataDict()
        tobj = manager.tableHandler[TN_LOCAL]

        # another check
        if msg.get(TCN_OWNER) != self.muser:
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
        label = hgLabel('Subject:' , parent = widget)
        label.setToolTip('Subject of the Message') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_LOCAL,
                                          TCN_SUBJECT,
                                          widget,
                                          MASK_SHOW,
                                          msg)
        wlay.addWidget(entry, r, 2)
        r += 1
        
        # from
        label = hgLabel('From:' , parent = widget)
        label.setToolTip('Sender of the Message') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_LOCAL,
                                          TCN_LSENDER,
                                          widget,
                                          MASK_SHOW,
                                          msg)
        wlay.addWidget(entry, r, 2)
        r += 1
        
        # recipients
        label = hgLabel('To:' , parent = widget)
        label.setToolTip('Recipients of the Message') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget( label, r, 0, hg.AlignTop)
        entry = manager.getFunctionWidget(TN_LOCAL,
                                          TCN_LRECEIVER,
                                          widget,
                                          MASK_SHOW,
                                          msg)

        wlay.addWidget(entry, r, 2)
        r += 1
        
        # date
        # just get any label widget and set desired text afterwards (saves label formatting)
        label = hgLabel('Date:' , parent = widget)
        label.setToolTip('Receive date of the Message') 
        label.setSsiName( ssiDLG_LABEL.name() )
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
        entry = manager.getFunctionWidget(TN_LOCAL,
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
    def setFolder(self, value):
        """\brief Sets the new folder for msg."""

        self.movetofolder = value


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        return self.msg
        
        
    def resetData(self):
        """"""

        self.op           = ''
        self.movetofolder = ''
        
        
    def markAsRead(self, manager):
        """"""
        
        if not self.msg.get(TCN_READ):
            manager.markAsRead(self.id)
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_LOCAL, secGUIPermission.SC_VIEW)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Send:
            self.performSend(manager)
        elif self.result() == self.Delete:
            self.performDelete(manager)
        elif self.result() == self.Move:
            self.performMove(manager)
            self.setResult(self.Running)
        elif self.result() == self.Prev:
            self.performPrev(manager)
            self.setResult(self.Running)
        elif self.result() == self.Next:
            self.performNext(manager)
            self.setResult(self.Running)
        elif self.result() == self.UNext:
            self.performUnreadNext(manager)
            self.setResult(self.Running)
        elif self.result() == self.UPrev:
            self.performUnreadPrev(manager)
            self.setResult(self.Running)
        
        
    # button callbacks stubs
    def reply(self):
        """"""
        self.op = OP_REPLY
        self.setResult(self.Send)


    def replyAll(self):
        """"""
        self.op = OP_REPLYALL
        self.setResult(self.Send)


    def forward(self):
        """"""
        self.op = OP_FORWARD
        self.setResult(self.Send)


    def delete(self):
        """"""
        self.setResult(self.Delete)


    def move(self):
        """"""
        self.setResult(self.Move)


    def prev(self):
        """"""
        self.setResult(self.Prev)


    def next(self):
        """"""
        self.setResult(self.Next)


    def unreadPrev(self):
        """"""
        self.setResult(self.UPrev)


    def unreadNext(self):
        """"""
        self.setResult(self.UNext)


    # callback implementations
    def performRejected(self, manager):
        """\reimp"""
        # set dlg target
        self.setTarget(self.closetarget)
        self.target_url = self.closetarget


    def performSend(self, manager):
        """\reimp"""
        
        if not self.op in SEND_OPS:
            return

        # set send dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, self.id, self.op)

        self.setTarget(target)
        self.target_url = target
        

    def performDelete(self, manager):
        """\reimp"""
        
        manager.deleteEntries(TN_LOCAL, [self.id])

        # set dlg target
        self.setTarget(self.closetarget)
        self.target_url = self.closetarget


    def performMove(self, manager):
        """\reimp"""
        
        if not self.movetofolder:
            manager.displayError('No target folder specified.', 'Error')
        
        if self.movetofolder == manager.FLD_TRASH:
            self.msg[TCN_TRASH]  == 1
        else:
            if self.movetofolder != 'NULL':
                try:
                    self.movetofolder = int(self.movetofolder)
                except:
                    manager.displayError('Unknown target folder specified.', 'Error')
            
                if not manager.tableHandler[TN_FOLDER].getEntry(self.movetofolder):
                    manager.displayError('Unknown target folder specified.', 'Error')
            
            self.msg[TCN_FOLDER] = self.movetofolder
        
        if not manager.tableHandler[TN_LOCAL].updateEntry(self.msg, self.id):
            manager.displayError('An error occured while moving message.', 
                                 'Database error')
            
        self.folder = self.movetofolder
        
        if self.folder == 'NULL':
            self.folder = None
        
        # update dlg target
        url    = manager.absolute_url()
        if self.folder:
            target = '%s/dlgHandler/dlgMessageCenter/show?folder=%s' % (url, self.folder)
        else:
            target = '%s/dlgHandler/dlgMessageCenter/show' % (url)

        self.setTarget(target)
        self.target_url = target

        self.initLayout(manager)
            
        
    def performPrev(self, manager):
        """\reimp"""
        
        # get 1 entry with aid < self.id sort aid desc
        constraints = { TCN_AUTOID: '_<_' + str(self.id) }

        self.loadNewMsg(manager, constraints, 'desc')


    def performNext(self, manager):
        """\reimp"""
        
        # get 1 entry with aid > self.id sort aid desc
        constraints = { TCN_AUTOID: '_>_' + str(self.id) }

        self.loadNewMsg(manager, constraints, 'asc')


    def performUnreadPrev(self, manager):
        """\reimp"""
        
        constraints = { TCN_AUTOID: '_<_' + str(self.id),
                        TCN_READ:   0 }

        self.loadNewMsg(manager, constraints, 'desc')


    def performUnreadNext(self, manager):
        """\reimp"""
        
        constraints = { TCN_AUTOID: '_>_' + str(self.id),
                        TCN_READ:   0 }
        
        self.loadNewMsg(manager, constraints, 'asc')


    def loadNewMsg(self, manager, constraints, direction):
        """\reimp"""
        
        tobj = manager.tableHandler[TN_LOCAL]        
        
        constraints[TCN_OWNER]  = self.muser

        if self.folder == manager.FLD_TRASH:
            constraints[TCN_TRASH]  = 1
        else:
            constraints[TCN_TRASH]  = 0 
            constraints[TCN_FOLDER] = self.folder
                
        newmsg = tobj.getEntryList(show_number = 1, constraints = constraints, direction = direction)
        
        if not newmsg:
            manager.displayError('Couldn\'t find message.', 
                                 'Database error')
            
        self.id  = newmsg[0][TCN_AUTOID]
        self.msg = newmsg[0]
    
        self.initLayout(manager)


