############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgThreadView.py
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
from PyHtmlGUI.widgets.hgCheckBox       import hgCheckBox
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.elements.Styles.Default   import ssiDLG_LABEL

from zopra.core.constants         import TCN_AUTOID
                                               
from zopra.core.dialogs.guiHandler   import guiHandler

from zopra.core.secGUIPermission     import secGUIPermission

from zopra.core.tools.managers import TN_THREAD,      \
                                                    TN_SENT,        \
                                                    TN_LOCAL,       \
                                                    TN_MUSER,       \
                                                    TN_FOLDER,      \
                                                    TCN_SUBJECT,    \
                                                    TCN_THREAD,     \
                                                    TCN_SSENDER,    \
                                                    TCN_REPLIESTO,  \
                                                    TCN_DRAFT,      \
                                                    TCN_LSENDER,    \
                                                    TCN_OWNER,      \
                                                    TCN_READ,       \
                                                    TCN_TRASH,      \
                                                    TCN_FOLDER,     \
                                                    TCN_SORTID,     \
                                                    TCN_FOLDERNAME, \
                                                    IMG_SORTNONE,   \
                                                    IMG_SORTASC,    \
                                                    IMG_SORTDESC,   \
                                                    IMG_MAILREAD,   \
                                                    IMG_MAILUNREAD, \
                                                    IMG_MAILIN,     \
                                                    IMG_MAILOUT,    \
                                                    IMG_DELETE,     \
                                                    IMG_REPLY,      \
                                                    IMG_FORWARD,    \
                                                    IMG_THREADON,   \
                                                    IMG_THREADOFF



SORT_DIRECTION = ['asc', 'desc']
SORT_FIELDS    = [TCN_READ, TCN_SUBJECT, 'entrydate', TCN_FOLDER, TCN_LSENDER]

MARK_READ      = -1
MARK_UNREAD    = -2
EMPTY_TRASH    = -3
DELETE_MSG     = -4
    
DLG_ACTIONS    = [ MARK_READ, MARK_UNREAD, EMPTY_TRASH, DELETE_MSG ]
    
DLG_ACTLABEL   = { MARK_READ:   'Mark as read', 
                   MARK_UNREAD: 'Mark as unread',
                   EMPTY_TRASH: 'Empty Trash',
                   DELETE_MSG:  'Delete',
                 }

MSG_OP_REPLY   = 'reply'
MSG_OP_FWD   = 'forward_sent'


class dlgThreadViewPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.page              = None
        self.threadbox         = None
        self.functionbox       = None
        self.databox           = None
        self.btnbox            = None
        self.newButton         = None
        self.goButton          = None
        self.sortThreadButton  = None
        self.sortReadButton    = None
        self.sortIOButton      = None
        self.sortSubjectButton = None
        self.sortSenderButton  = None
        self.sortDateButton    = None
        self.sortFolderButton  = None
        self.replyBtnList      = None
        self.deleteBtnList     = None
        self.actionCB          = None
        self.closeButton       = None
        self.closeAccel        = None
        self.msgCBList         = []


class dlgThreadView( hgDialog, guiHandler ):
    """\class dlgThreadView

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgThreadView'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    New      =  3
    Go       =  4
    Delete   =  5
    Reply    =  6
    Sort     =  7
        
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Thread View'

        # dlg private data
        self.data = dlgThreadViewPrivate()

        # init values
        self.resetData()
        
        self.muser = manager.getCurrentMUser()[TCN_AUTOID]

        try:
            self.id = int( param_dict.get('id') )
        except:
            manager.displayError('No valid message id provided', 'Error')
        
        if self.id:            
            self.thread = manager.tableHandler[TCN_THREAD].getEntry(self.id)
            
            if not self.thread:
                manager.displayError('No valid thread id provided', 'Error')
                                
        else:
            manager.displayError('No valid message id provided', 'Error')
            
            
        self.sent = manager.tableHandler[TN_SENT].getEntries( [self.id,
                                                               self.muser,
                                                               0],
                                                              [TCN_THREAD,
                                                               TCN_SSENDER,
                                                               TCN_DRAFT], 
                                                              order = TCN_AUTOID, 
                                                              direction = 'asc' )
            
        self.received = manager.tableHandler[TN_LOCAL].getEntries( [self.id,
                                                                    self.muser,
                                                                    0],
                                                                   [TCN_THREAD,
                                                                    TCN_OWNER,
                                                                    TCN_TRASH], 
                                                                   order = TCN_AUTOID, 
                                                                   direction = 'asc' )
        
        # basic data orga
        self.setupMessages(manager)
        
        # load icon image properties
        self.icon_sortasc  = manager.iconHandler.get(IMG_SORTASC,  path=True).getIconDict()        
        self.icon_sortdesc = manager.iconHandler.get(IMG_SORTDESC, path=True).getIconDict()        
        self.icon_nosort   = manager.iconHandler.get(IMG_SORTNONE, path=True).getIconDict()        

        thread_off_icon    = manager.iconHandler.get(IMG_THREADOFF, path=True).getIconDict()        
        
        # init buttons
        self.data.newButton         = hgPushButton( parent = self, name = 'new'          )
        self.data.goButton          = hgPushButton( parent = self, name = 'go'           )
        self.data.sortThreadButton  = hgPushButton( parent = self, name = 'sort_thread', icon = thread_off_icon   )
        self.data.sortReadButton    = hgPushButton( parent = self, name = TCN_READ,      icon = self.icon_nosort  )
        self.data.sortIOButton      = hgPushButton( parent = self, name = 'sort_io',     icon = self.icon_nosort  )
        self.data.sortSubjectButton = hgPushButton( parent = self, name = TCN_SUBJECT,   icon = self.icon_nosort  )
        self.data.sortSenderButton  = hgPushButton( parent = self, name = TCN_LSENDER,   icon = self.icon_nosort  )
        self.data.sortDateButton    = hgPushButton( parent = self, name = 'entrydate',   icon = self.icon_nosort  )
        self.data.sortFolderButton  = hgPushButton( parent = self, name = TCN_FOLDER,    icon = self.icon_nosort  )
        self.data.closeButton       = hgPushButton( parent = self, name = 'close'        )

        self.data.newButton.setText         ( '&New Message'    )
        self.data.goButton.setText          ( '&Go'             )
        self.data.sortThreadButton.setText  ( 'Sort Default'    )
        self.data.sortReadButton.setText    ( 'Sort Read'       )
        self.data.sortIOButton.setText      ( 'Sort In/Out'     )
        self.data.sortSubjectButton.setText ( 'Sort Subject'    )
        self.data.sortSenderButton.setText  ( 'Sort Sender'     )
        self.data.sortDateButton.setText    ( 'Sort Date'       )
        self.data.sortFolderButton.setText  ( 'Sort Folder'     )
        self.data.closeButton.setText       ( '&Close'          )

        self.data.sortThreadButton.setToolTip('Display Messages in Thread Order')

        # connect the signals to the slots
        self.connect( self.data.newButton.clicked,               self.new     )
        self.connect( self.data.goButton.clicked,                self.go      )
        self.connect( self.data.sortThreadButton.clickedButton,  self.sort    )
        self.connect( self.data.sortReadButton.clickedButton,    self.sort    )
        self.connect( self.data.sortIOButton.clickedButton,      self.sort    )
        self.connect( self.data.sortSubjectButton.clickedButton, self.sort    )
        self.connect( self.data.sortSenderButton.clickedButton,  self.sort    )
        self.connect( self.data.sortDateButton.clickedButton,    self.sort    )
        self.connect( self.data.sortFolderButton.clickedButton,  self.sort    )
        self.connect( self.data.closeButton.clicked,             self.reject  )
        
        self.order2btn = {}
        self.order2btn['sort_thread'] = self.data.sortThreadButton
        self.order2btn[TCN_READ]      = self.data.sortReadButton
        self.order2btn['sort_io']     = self.data.sortIOButton
        self.order2btn[TCN_SUBJECT]   = self.data.sortSubjectButton
        self.order2btn[TCN_LSENDER]   = self.data.sortSenderButton
        self.order2btn['entrydate']   = self.data.sortDateButton
        self.order2btn[TCN_FOLDER]    = self.data.sortFolderButton
        
        # init layout
        self.initLayout(manager)        


    def setupMessages(self, manager):
        """\brief Initialise the msg setup."""

        self.aid2sent = {}
        self.aid2recv = {}
        
        for sent in self.sent:
            if not sent.get(TCN_REPLIESTO):
                self.root = sent
            else:
                if not self.replies.has_key( sent[TCN_REPLIESTO] ):
                    self.replies[ sent[TCN_REPLIESTO] ] = []
                self.replies[ sent[TCN_REPLIESTO] ].append(sent[TCN_AUTOID])
                self.replies[ sent[TCN_REPLIESTO] ].sort()
            
            self.aid2sent[ sent[TCN_AUTOID] ] = sent

        for recv in self.received:
            self.aid2recv[ recv[TCN_AUTOID] ] = recv
            
        self.sortThread()
        

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
        
        self.data.threadbox = self.layoutThread(manager, parent = page)
        layout.addWidget(self.data.threadbox, 0, 0)

        self.data.functionbox = self.layoutFunctions(manager, parent = page)
        layout.addWidget(self.data.functionbox, 1, 0)

        self.data.databox = self.layoutData(manager, parent = page)
        layout.addWidget(self.data.databox, 2, 0)

        self.data.btnbox = self.layoutButtons(parent = page)
        layout.addWidget(self.data.btnbox, 3, 0, hg.AlignHCenter)


    def layoutThread(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""

        # general information  
        if not widget:      
            widget = hgGroupBox(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        c = 0
        
        wlay.addWidget( hgLabel('Thread&nbsp;', parent = widget), 0, c )

        c += 1

        threadlab = manager.getLabelString(TN_THREAD, None, self.thread)
        
        # split into several lines if necessary
        r   = 0
        pos = 0
        while pos < len(threadlab):
            oldpos = pos
            pos += 50
            newpos = threadlab.find(' ', pos)
            
            if newpos == -1:
                pos = len(threadlab)
            else:
                pos = newpos
                while threadlab[pos] == ' ':
                    pos += 1
                    
            partlab = threadlab[oldpos:pos]
            wlay.addWidget( hgLabel('<b>%s</b>' % partlab, parent = widget), r, c )
            r += 1
        c += 1

        # spacing
        wlay.addWidget( hgLabel('&nbsp;with %s Messages (%s sent / %s received)' % \
                                ( len(self.sent) + len(self.received),
                                  len(self.sent),
                                  len(self.received)), 
                                parent = widget), 0, c)
        
        c += 1

        return widget
    

    def layoutFunctions(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        
        #if not widget:      
        widget = hgHBox(parent=parent)
        widget.layout().data.expanding = hgSizePolicy.NoDirection
        #else:
        #    widget.removeChildren()
        
        widget.add( self.data.newButton   )
        widget.add( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget)     )

        # action selection box
        self.data.actionCB = hgComboBox(name = 'action', parent = widget)

        self.data.actionCB.insertItem('Action...',    ''                       )
        self.data.actionCB.insertItem(DLG_ACTLABEL[MARK_READ],   MARK_READ     )
        self.data.actionCB.insertItem(DLG_ACTLABEL[MARK_UNREAD], MARK_UNREAD   )
        self.data.actionCB.insertItem('------------', ''                       )
        self.data.actionCB.insertItem('Move to...',   ''                       )
        self.data.actionCB.insertItem('Inbox',        'NULL'                   )
        self.data.actionCB.insertItem('Trash',        'Trash'                  )
        
        folders = manager.tableHandler[TN_FOLDER].getEntries([self.muser], [TCN_OWNER], order = TCN_SORTID)
        
        for folder in folders:
            self.data.actionCB.insertItem(folder[TCN_FOLDERNAME], folder[TCN_AUTOID])

        self.data.actionCB.insertItem('------------', '')
        self.data.actionCB.insertItem(DLG_ACTLABEL[EMPTY_TRASH], EMPTY_TRASH   )
            
        self.data.actionCB.setCurrentItem(0)
            
        self.connect( self.data.actionCB.valueChanged,   self.setMsgAction )
        
        widget.add( self.data.actionCB   )
        
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.goButton   )

        return widget

    
    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""

        # general information  
        if not widget:      
            widget = hgWidget(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        r = 0

        # messages
        self.msgbox = hgTable(parent = widget)
        wlay.addWidget( self.msgbox, r, 0)
        self.displayMessages(manager)
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
        
        widget.add( self.data.closeButton   )

        return widget
    

    def displayMessages(self, manager):
        """\brief Get the button layout."""
        print "displayMessages"
        tobj = manager.tableHandler[TN_LOCAL]

        tab = hgTable(spacing = '0', parent = self.msgbox)

        self.msgbox[0, 0] = tab

        self.createSortBar(manager, tab)

        # reset btn to auto id relation
        self.replybtn2aid      = {}
        self.delbtn2aid        = {}
        self.checkbox2aid      = {}
        self.data.msgCBList    = []
        
        # get image properties
        reply_icon  = manager.iconHandler.get(IMG_REPLY,      path=True).getIconDict()        
        fwd_icon    = manager.iconHandler.get(IMG_FORWARD,    path=True).getIconDict()        
        del_icon    = manager.iconHandler.get(IMG_DELETE,     path=True).getIconDict()        
        read_img    = manager.iconHandler.getImageObject(IMG_MAILREAD)
        unread_img  = manager.iconHandler.getImageObject(IMG_MAILUNREAD) 
        in_img      = manager.iconHandler.getImageObject(IMG_MAILIN)
        out_img     = manager.iconHandler.getImageObject(IMG_MAILOUT) 
        
        i = 1
        for i, (aid, type) in enumerate(self.order):
            if type == TN_LOCAL:
                msg = self.aid2recv[aid]
            else:
                msg = self.aid2sent[aid]
                msg[TCN_LSENDER] = msg[TCN_SSENDER]
            
            c = 0
            
            # checkbox
            if type == TN_LOCAL:
                name = 'check_' + str(aid) + '_' + type
                msgcb = hgCheckBox(value  = name, 
                                   parent = tab, 
                                   name   = name)
                tab[i+1, 0] = msgcb
                self.data.msgCBList.append(msgcb)
                self.checkbox2aid[name] = (aid, type)
            
            c += 1

            # read
            if type == TN_LOCAL and not msg.get(TCN_READ, 0):
                read = False
                img = unread_img
            else:
                read = True
                img = read_img
                
            tab[i+1, c] = hgLabel(img.tag(), parent = tab)
            tab.setCellAlignment(i+1, c, tab.ALIGN_CENTER )
            c += 1


            # in/out
            if type == TN_LOCAL:
                img = in_img
            else:
                img = out_img
                
            tab[i+1, c] = hgLabel(img.tag(), parent = tab)
            c += 1
            
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1
            
            # subject
            link = manager.getLink(type, None, msg, parent = tab)
            linktext = link.getText()
            link.setToolTip(linktext)
            if len(linktext) > 50:
                link.setText(linktext[:48] + '...')
            if not read:
                link.setText('<b>' + link.getText() + '</b>')
            tab[i+1, c] = link
            c += 1
            
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # sender
            link = manager.getLink(TN_MUSER, msg[TCN_LSENDER], parent = tab)
            tab[i+1, c] = link
            c += 1
            
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # date
            tab[i+1, c] = hgLabel(msg['entrydate'], parent = tab)
            c += 1
            
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # folder
            url = manager.absolute_url()
            if type == TN_LOCAL:
                if msg.get(TCN_FOLDER):
                    link = manager.getLink(TN_FOLDER, msg[TCN_FOLDER])
                    if not link:
                        manager.displayError('Couldn\'t find folder.', 'Database Error')
                else:
                    uri = '%s/dlgHandler/%s/show?folder=%s' % (url,
                                                               manager.FLD_DLGS[manager.FLD_INBOX], 
                                                               manager.FLD_INBOX)
                    link = hgLabel( manager.FLD_INBOX, 
                                    uri = uri, 
                                    parent = tab )
            else:
                uri = '%s/dlgHandler/%s/show?folder=%s' % (url,
                                                           manager.FLD_DLGS[manager.FLD_OUTBOX], 
                                                           manager.FLD_OUTBOX)
                link = hgLabel( manager.FLD_OUTBOX, 
                                uri = uri, 
                                parent = tab )
                
            tab[i+1, c] = link
            c += 1

            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # reply
            name = 'reply_' + str(aid) + '_' + type
            if type == TN_LOCAL:
                btn = hgPushButton(text = name, name = name, icon = reply_icon, parent = tab)
            else:
                btn = hgPushButton(text = name, name = name, icon = fwd_icon, parent = tab)
            tab[i+1, c] = btn
            self.connect( btn.clickedButton, self.reply )
            self.replybtn2aid[name] = (aid, type)
            
            c += 1

            # delete
            name = 'delete_' + str(aid) + '_' + type
            btn = hgPushButton(text = name, name = name, icon = del_icon, parent = tab)
            tab[i+1, c] = btn
            self.connect( btn.clickedButton, self.delete )
            self.delbtn2aid[name] = (aid, type)
                        
            c += 1
            
            if not i % 2:
                for cc in xrange(0, c):
                    tab.setCellBackgroundColor(i+1, cc, '#E0E0DA')

            i += 1

        
    def createSortBar(self, manager, tab):
        """\brief Get the button layout."""
        
        tobj = manager.tableHandler[TN_LOCAL]

        c = 0
        
        if self.orderfield == 'sort_thread':
            img = manager.iconHandler.getImageObject(IMG_THREADON)
            to_active = hgLabel(img.tag(), parent = tab)
            to_active.setToolTip('Messages Sorted in Thread Order')
            tab[0, c] = to_active
        else:
            # need to set icon every time because of sortThreadBy functionality
            img = manager.iconHandler.get(IMG_THREADOFF, path = True)
            self.data.sortThreadButton.setIcon(img.getIconDict())
            
            tab[0, c] = self.data.sortThreadButton
            
        c += 1
        
        tab[0, c] = self.data.sortReadButton
        c += 1
        
        tab[0, c] = self.data.sortIOButton
        c += 1
        
        tab[0, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
        c += 1

        box = hgHBox( parent = tab )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        label = tobj.getLabelWidget(TCN_SUBJECT, parent = tab)
        box.add( label                       )
        box.add( self.data.sortSubjectButton )
        tab[0, c] = box
        c += 1
        
        tab[0, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
        c += 1

        box = hgHBox( parent = tab )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        label = tobj.getLabelWidget(TCN_LSENDER, parent = tab)
        box.add( label                       )
        box.add( self.data.sortSenderButton )
        tab[0, c] = box
        c += 1
        
        tab[0, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
        c += 1

        box = hgHBox( parent = tab )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        label = tobj.getLabelWidget(TCN_SUBJECT, parent = tab)
        label.setText('Date')
        box.add( label                       )
        box.add( self.data.sortDateButton )
        tab[0, c] = box
        c += 1
        
        tab[0, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
        c += 1

        box = hgHBox( parent = tab )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        label = tobj.getLabelWidget(TCN_FOLDER, parent = tab)
        box.add( label                       )
        box.add( self.data.sortFolderButton )
        tab[0, c] = box
        c += 1
        

    # data manipulation
    def setMsgAction(self, value):
        """\brief Sets the new folder for msg."""

        self.action = value


    def sortThread(self):
        """\brief Sort in original thread order."""
        
        self.orderfield = 'sort_thread'
        self.order = []

        if self.root:
            self.order.append( (self.root[TCN_AUTOID], TN_SENT) )
            
        for recv in self.received:
            self.order.append( (recv[TCN_AUTOID], TN_LOCAL) )
            
            for sent in self.replies.get(recv[TCN_AUTOID], []):
                self.order.append( (sent, TN_SENT) )
                
        print 'order: ' + str(self.order)


    def sortThreadBy(self, manager, order):
        """\brief Sort messages.
                  Sent messages are always first, 
                  order of autoids is kept.
        """
        print 'sortThreadBy: ' + order
        self.order = []

        sorting = []
        
        if order == 'sort_thread':
            self.order2btn[self.orderfield].setIcon(self.icon_nosort)

            self.sortThread()
            
            return
                                   
        if not order in SORT_FIELDS and order != 'sort_io':
            return
        
        print 'set new sort field'
        # handle direction and button images
        if order == self.orderfield:
            self.orderdir = (self.orderdir + 1) % 2
            if self.orderdir:
                self.order2btn[self.orderfield].setIcon(self.icon_sortdesc)
            else:
                self.order2btn[self.orderfield].setIcon(self.icon_sortasc)
        else:
            self.order2btn[self.orderfield].setIcon(self.icon_nosort)
            self.order2btn[order].setIcon(self.icon_sortasc)
            self.orderfield = order
            self.orderdir = 0


        if order == 'sort_io':
            if self.orderdir:
                first  = (self.received, TN_LOCAL)
                second = (self.sent,     TN_SENT)
            else:
                first  = (self.sent,     TN_SENT)
                second = (self.received, TN_LOCAL)
                
            type = first[1]
            
            for msg in first[0]:
                self.order.append( (msg[TCN_AUTOID], type) )
                
            type = second[1]

            for msg in second[0]:
                self.order.append( (msg[TCN_AUTOID], type) )
                
            return
        
        for msg in self.sent:
            if order == TCN_READ:
                sortvalue = 1
            elif order == TCN_LSENDER:
                sortvalue = msg[TCN_SSENDER]
                sortvalue = manager.getLabelString(TN_MUSER, sortvalue) 
            elif order == TCN_FOLDER:
                sortvalue = manager.FLD_OUTBOX
            else:
                sortvalue = msg.get(order, '')
                
            if self.orderdir:
                sorting.append( (sortvalue, -1, TN_SENT, - 1 * msg[TCN_AUTOID]) )
            else:
                sorting.append( (sortvalue,  1, TN_SENT,       msg[TCN_AUTOID]) )
            
        for msg in self.received:
            sortvalue = msg.get(order, '')
                
            if order == TCN_FOLDER:
                if sortvalue:
                    sortvalue = manager.getLabelString(TN_FOLDER, sortvalue)
                else:
                    sortvalue = manager.FLD_INBOX
            elif order == TCN_LSENDER:
                sortvalue = manager.getLabelString(TN_MUSER, sortvalue) 
                    
            if self.orderdir:
                sorting.append( (sortvalue,  1, TN_LOCAL, - 1 * msg[TCN_AUTOID]) )
            else:
                sorting.append( (sortvalue, -1, TN_LOCAL,       msg[TCN_AUTOID]) )

        print 'perform sorting'
        sorting.sort()   
        
        if self.orderdir:
            sorting.reverse()     
        
        for (val, aux_sort, type, aid) in sorting:
            if self.orderdir:
                aid *= -1
                
            self.order.append( (aid, type) )
        

    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        return self.thread
        
        
    def resetData(self):
        """"""
        self.id       = 0
        self.thread   = {}
        self.root     = None
        self.sent     = []
        self.replies  = {}
        self.aid2sent = {}
        self.received = []
        self.aid2recv = {}
        self.sortbtn  = None
        self.order    = []
        self.orderfield = 'sort_thread'
        self.orderdir   = 0
        self.action     = ''      
        
        
    def markAsRead(self, manager, id, read = True):
        """"""
        
        assert ( self.aid2recv.has_key(id) )
        if self.aid2recv[id].get(TCN_READ, 0) != int(read):
            manager.markAsRead(id, read)
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_LOCAL,  secGUIPermission.SC_DELETE)
            manager.checkGUIPermission(TN_SENT,   secGUIPermission.SC_DELETE)
            manager.checkGUIPermission(TN_THREAD, secGUIPermission.SC_VIEW  )

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.New:
            self.performNew(manager)
        elif self.result() == self.Go:
            self.performGo(manager)
            self.setResult(self.Running)
        elif self.result() == self.Sort:
            self.performSort(manager)
            self.setResult(self.Running)
        elif self.result() == self.Reply:
            self.performReply(manager)
        elif self.result() == self.Delete:
            self.performDelete(manager)
            self.setResult(self.Running)
        
        
    # button callbacks stubs
    def reply(self, btnname):
        """"""
        self.btnname = btnname
        self.setResult(self.Reply)


    def delete(self, btnname):
        """"""
        self.btnname = btnname
        self.setResult(self.Delete)


    def new(self):
        """"""
        self.setResult(self.New)


    def go(self):
        """"""
        self.setResult(self.Go)


    def sort(self, btnname):
        """"""
        print 'sort: ' + btnname
        self.sortbtn = btnname
        self.setResult(self.Sort)


    # callback implementations
    def performRejected(self, manager):
        """\reimp"""
        # set dlg target
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgMessageCenter/show' % (url)

        self.setTarget(target)
        self.target_url = target


    def performNew(self, manager):
        """\reimp"""
        # set send dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgSendMsg/show' % (url)

        self.setTarget(target)
        self.target_url = target
        

    def performReply(self, manager):
        """\reimp"""
        
        (msg_id, type) = self.delbtn2aid[self.btnname]
        
        if not msg_id or not type in [TN_LOCAL, TN_SENT]:
            return 
            
        # set send dlg
        url    = manager.absolute_url()
        
        if type == TN_LOCAL:
            manager.markAsRead(msg_id)
            target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, msg_id, MSG_OP_REPLY)
        else:
            target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, msg_id, MSG_OP_FWD)
            

        self.setTarget(target)
        self.target_url = target
        

    def performDelete(self, manager):
        """\reimp"""
        
        (msg_id, type) = self.delbtn2aid[self.btnname]
        
        if msg_id and type == TN_LOCAL:
            msg = self.aid2recv[msg_id]
            msg[TCN_TRASH] = 1
                
            if not manager.tableHandler[TN_LOCAL].updateEntry(msg, msg_id):
                manager.displayError('An error occured while moving message to trash.', 
                                     'Database error')
            
            # adjust local data
            del self.aid2recv[msg_id]
        else:
            manager.tableHandler[type].deleteEntry(msg_id)
            
            # adjust local data
            if self.root and self.root[TCN_AUTOID] == msg_id:
                self.root = None
            del self.aid2sent[msg_id]
        
        
        self.order.remove( (msg_id, type) )
            
        self.initLayout(manager)


    def performGo(self, manager):
        """\reimp"""
        
        if not self.action:
            return
        
        # get checked messages
        msg_ids = []
        
        for cb in self.data.msgCBList:
            if cb.isChecked():
                msg_ids.append( self.checkbox2aid[cb.getName()] )
                cb.setChecked(False)

        # mark messages as read
        if self.action in [ MARK_READ, MARK_UNREAD ]:
            read = self.action == MARK_READ
            
            for (aid, type) in msg_ids:
                if type == TN_LOCAL:
                    self.markAsRead(manager, aid, read)
                    self.aid2recv[aid] = read  

        # empty trash
        elif self.action == EMPTY_TRASH:
            # get autoidlist, delete entries
            constraints = {TCN_OWNER: self.muser,
                           TCN_TRASH: 1}
            trash_ids = manager.tableHandler[TN_LOCAL].getEntryAutoidList(constraints = constraints)
            
            manager.deleteEntries(TN_LOCAL, [trash_ids])            
        # move the messages around
        else:
            for (aid, type) in msg_ids:
                if type == TN_SENT:
                    continue
                
                msg = self.aid2recv[aid]
                
                assert(msg)
        
                if self.action == manager.FLD_TRASH:
                    msg[TCN_TRASH]  == 1
            
                    #TODO remove from data
                    self.order.remove( (aid, type) )
                    del self.aid2recv[aid]
                else:
                    if self.action != 'NULL':
                        try:
                            self.action = int(self.action)
                        except:
                            manager.displayError('Unknown target folder specified.', 'Error')
            
                        if not manager.tableHandler[TN_FOLDER].getEntry(self.action):
                            manager.displayError('Unknown target folder specified.', 'Error')
            
                msg[TCN_FOLDER] = self.action
        
                if not manager.tableHandler[TN_LOCAL].updateEntry(msg, aid):
                    manager.displayError('An error occured while moving message.', 
                                         'Database error')
            
        self.initLayout(manager)
            
        
    def performSort(self, manager):
        """\reimp"""
        
        print 'performSort: ' + self.sortbtn
        
        if not self.sortbtn:
            return

        self.sortThreadBy(manager, self.sortbtn)
        
        self.sortbtn = None

        self.initLayout(manager)
