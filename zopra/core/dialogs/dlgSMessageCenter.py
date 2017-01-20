############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

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

from PyHtmlGUI.widgets.hgMenuBar        import hgMenuBar

from PyHtmlGUI.stylesheet.hgStyleSheet  import hgStyleSheetItem

from zopra.core.constants               import TCN_AUTOID
                                               
from zopra.core.dialogs.guiHandler      import guiHandler

from zopra.core.secGUIPermission        import secGUIPermission

from zopra.core.tools.managers          import TN_THREAD,      \
                                                    TN_GLOBAL,      \
                                                    TN_SENT,        \
                                                    TN_LOCAL,       \
                                                    TN_MUSER,       \
                                                    TN_FOLDER,      \
                                                    TCN_SUBJECT,    \
                                                    TCN_THREAD,     \
                                                    TCN_SSENDER,    \
                                                    TCN_DRAFT,      \
                                                    TCN_OWNER,      \
                                                    TCN_READ,       \
                                                    TCN_TRASH,      \
                                                    TCN_COUNTER,    \
                                                    TCN_ENTRIESPP,  \
                                                    TCN_THREADVIEW, \
                                                    TCN_FOLDER,     \
                                                    TCN_SORTID,     \
                                                    TCN_FOLDERNAME, \
                                                    IMG_SORTNONE,   \
                                                    IMG_SORTASC,    \
                                                    IMG_SORTDESC,   \
                                                    IMG_THREAD,     \
                                                    IMG_MAILREAD,   \
                                                    IMG_MAILUNREAD, \
                                                    IMG_MAILIN,     \
                                                    IMG_MAILOUT,    \
                                                    IMG_DELETE,     \
                                                    IMG_FORWARD,    \
                                                    IMG_FIRST,      \
                                                    IMG_FIRST_INACT,\
                                                    IMG_BWD,        \
                                                    IMG_FWD,        \
                                                    IMG_BWD_INACT,  \
                                                    IMG_FWD_INACT,  \
                                                    IMG_LAST,       \
                                                    IMG_LAST_INACT


SORT_DIRECTION = ['asc', 'desc']
SORT_FIELDS    = [TCN_SUBJECT, 'entrydate', TCN_SSENDER]

MARK_READ      = -1
MARK_UNREAD    = -2
EMPTY_TRASH    = -3
THREAD_GROUP   = -4
RESTORE_TRASH  = -5
DELETE_MSG     = -6
STD_VIEW       = -7
    
DLG_ACTIONS    = [ MARK_READ, MARK_UNREAD, EMPTY_TRASH, THREAD_GROUP, RESTORE_TRASH, DELETE_MSG, STD_VIEW ]
    
DLG_ACTLABEL   = { MARK_READ:     'Mark as read', 
                   MARK_UNREAD:   'Mark as unread', 
                   EMPTY_TRASH:   'Empty Trash',
                   THREAD_GROUP:  'Group by Thread',
                   RESTORE_TRASH: 'Restore Messages',
                   DELETE_MSG:    'Delete',
                   STD_VIEW:      'Standard View'
                 }

MSG_OP_FWD   = 'forward_sent'


class dlgSMessageCenterPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.page              = None
        self.navibox           = None
        self.folderbox         = None
        self.functionbox       = None
        self.databox           = None
        self.btnbox            = None
        self.newButton         = None
        self.goButton          = None
        self.nextButton        = None
        self.prevButton        = None
        self.firstButton       = None
        self.lastButton        = None
        self.sortReadButton    = None
        self.sortSubjectButton = None
        self.sortSenderButton  = None
        self.sortDateButton    = None
        self.replyBtnList      = None
        self.deleteBtnList     = None
        self.actionCB          = None
        self.closeButton       = None
        self.closeAccel        = None
        self.msgCBList         = []


class dlgSMessageCenter( hgDialog, guiHandler ):
    """\class dlgSMessageCenter

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgSMessageCenter'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    New       =  3
    Go        =  4
    Delete    =  5
    Forward   =  6
    Sort      =  7
    Jump      =  8
    Thread    =  9
        
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Message Center'

        # dlg private data
        self.data = dlgSMessageCenterPrivate()

        # init values
        self.resetData()
        
        # select the current folder
        folder = param_dict.get('folder', None)

        if folder:
            if folder == manager.FLD_DRAFTS:
                self.draft = 1
            elif folder == manager.FLD_OUTBOX:
                self.draft = 0
            else:
                manager.displayError('No valid folder id provided', 'Error')

        # get user settings
        muser = manager.getCurrentMUser()
        
        self.muser      = muser[TCN_AUTOID]
        self.entriespp  = muser.get(TCN_ENTRIESPP, 20)
        self.threadview = muser.get(TCN_THREADVIEW, 0) == 1
        self.gcounter   = muser.get(TCN_COUNTER,    0)
        
        # load icon image properties
        self.icon_sortasc  = manager.iconHandler.get(IMG_SORTASC,  path=True).getIconDict()        
        self.icon_sortdesc = manager.iconHandler.get(IMG_SORTDESC, path=True).getIconDict()        
        self.icon_nosort   = manager.iconHandler.get(IMG_SORTNONE, path=True).getIconDict()        

        fwd_icon    = manager.iconHandler.get(IMG_FWD,      path=True).getIconDict()
        bwd_icon    = manager.iconHandler.get(IMG_FWD,      path=True).getIconDict()        
        first_icon  = manager.iconHandler.get(IMG_FIRST,    path=True).getIconDict()
        last_icon   = manager.iconHandler.get(IMG_LAST,     path=True).getIconDict()        
        
        # init buttons
        self.data.newButton         = hgPushButton( parent = self, name = 'new'          )
        self.data.goButton          = hgPushButton( parent = self, name = 'go'           )
        self.data.nextButton        = hgPushButton( parent = self, name = 'next',        icon = fwd_icon         )
        self.data.prevButton        = hgPushButton( parent = self, name = 'prev',        icon = bwd_icon         )
        self.data.firstButton       = hgPushButton( parent = self, name = 'first',       icon = first_icon       )
        self.data.lastButton        = hgPushButton( parent = self, name = 'last',        icon = last_icon        )
        self.data.sortReadButton    = hgPushButton( parent = self, name = TCN_READ,      icon = self.icon_nosort )
        self.data.sortSubjectButton = hgPushButton( parent = self, name = TCN_SUBJECT,   icon = self.icon_nosort )
        self.data.sortSenderButton  = hgPushButton( parent = self, name = TCN_SSENDER,   icon = self.icon_nosort )
        self.data.sortDateButton    = hgPushButton( parent = self, name = 'entrydate',   icon = self.icon_nosort )

        self.data.newButton.setText         ( '&New Message'    )
        self.data.goButton.setText          ( '&Go'             )
        self.data.nextButton.setText        ( 'Next'            )
        self.data.prevButton.setText        ( 'Previous'        )
        self.data.firstButton.setText       ( 'First'           )
        self.data.lastButton.setText        ( 'Last'            )
        self.data.sortReadButton.setText    ( 'Sort Read'       )
        self.data.sortSubjectButton.setText ( 'Sort Subject'    )
        self.data.sortSenderButton.setText  ( 'Sort Sender'     )
        self.data.sortDateButton.setText    ( 'Sort Date'       )

        self.data.newButton.setToolTip         ( 'New Message'     )
        self.data.goButton.setToolTip          ( 'Execute selected action' )
        self.data.nextButton.setToolTip        ( 'Next Page'       )
        self.data.prevButton.setToolTip        ( 'Previous Page'   )
        self.data.firstButton.setToolTip       ( 'First Page'      )
        self.data.lastButton.setToolTip        ( 'Last Page'       )
        self.data.sortReadButton.setToolTip    ( 'Sort by Read-state' )
        self.data.sortSubjectButton.setToolTip ( 'Sort by Subject'    )
        self.data.sortSenderButton.setToolTip  ( 'Sort by Sender'     )
        self.data.sortDateButton.setToolTip    ( 'Sort by Date'       )

        # connect the signals to the slots
        self.connect( self.data.newButton.clicked,               self.newMsg    )
        self.connect( self.data.goButton.clicked,                self.goAction  )
        self.connect( self.data.nextButton.clicked,              self.next      )
        self.connect( self.data.prevButton.clicked,              self.prev      )
        self.connect( self.data.firstButton.clicked,             self.first     )
        self.connect( self.data.lastButton.clicked,              self.last      )
        self.connect( self.data.sortReadButton.clickedButton,    self.sort      )
        self.connect( self.data.sortSubjectButton.clickedButton, self.sort      )
        self.connect( self.data.sortSenderButton.clickedButton,  self.sort      )
        self.connect( self.data.sortDateButton.clickedButton,    self.sort      )
        
        self.order2btn = {}
        self.order2btn[TCN_SUBJECT]  = self.data.sortSubjectButton
        self.order2btn[TCN_SSENDER]  = self.data.sortSenderButton
        self.order2btn['entrydate']  = self.data.sortDateButton
        
        # set initial sorting
        self.setSorting('entrydate')

        # init layout
        self.initLayout(manager)


    def getMessages(self, manager):
        """\brief Initialise the msg setup."""

        # get msg count
        constraints = { TCN_SSENDER:   self.muser, 
                        TCN_DRAFT:     self.draft }
        self.msgcount = manager.tableHandler[TN_SENT].getRowCount( constraints = constraints )
            
        # get messages
        self.messages = manager.tableHandler[TN_SENT].getEntryList( show_number  = self.entriespp,
                                                                    start_number = self.start,
                                                                    constraints  = constraints,
                                                                    order        = self.orderfield,
                                                                    direction    = SORT_DIRECTION[self.orderdir] )
        
        # create aux msg map
        self.aid2msg = {}
        
        for msg in self.messages:
            self.aid2msg[ msg[TCN_AUTOID] ] = msg
        

    # layout
    def initLayout(self, manager):
        """\brief Initialise the dialog layout."""

        # get the messages according to settings
        self.getMessages(manager)

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
        
        self.data.navibox   = self.layoutNavigation(manager, parent = page)
        layout.addWidget(self.data.navibox, 0, 0, hg.AlignTop  )

        datatab = hgTable(parent = page)
        layout.addWidget(datatab, 0, 1, hg.AlignTop  )

        self.data.folderbox = self.layoutFolder(manager, parent = datatab)
        datatab[0, 0] = self.data.folderbox

        self.data.functionbox = self.layoutFunctions(manager, parent = datatab)
        datatab[1, 0] = self.data.functionbox

        self.data.databox = self.layoutData(manager, parent = datatab)
        datatab[2, 0] = self.data.databox


    def layoutNavigation(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        tobj = manager.tableHandler[TN_FOLDER]

        # general information  
        if not widget:      
            widget = hgMenuBar(parent=parent)
            widget.setDirection(hg.Vertical)
        else:
            widget.removeChildren()
        wlay = widget.layout()

        r = 0
    
        # get user folder
        folders = tobj.getEntries([self.muser], [TCN_OWNER], order = TCN_SORTID)
        
        # genereate folderbar
        url    = manager.absolute_url()

        system_count = {}

        # clobal count
        new   = manager.tableHandler[TN_GLOBAL].getRowCount( { TCN_AUTOID: '_>_' + str(self.gcounter), TCN_TRASH: 0 } )
        total = manager.tableHandler[TN_GLOBAL].getRowCount( )        
        system_count[manager.FLD_GLOBAL] = (new, total)
        
        # inbox count
        new   = manager.tableHandler[TN_LOCAL].getRowCount( { TCN_FOLDER: 'NULL', 
                                                              TCN_TRASH:  0, 
                                                              TCN_READ:   0,
                                                              TCN_OWNER: self.muser } )
        total = manager.tableHandler[TN_LOCAL].getRowCount( { TCN_FOLDER: 'NULL',
                                                              TCN_TRASH: 0,
                                                              TCN_OWNER: self.muser } )        
        system_count[manager.FLD_INBOX] = (new, total)
        
        # trash count
        new   = manager.tableHandler[TN_LOCAL].getRowCount( { TCN_TRASH: 1,
                                                              TCN_READ:  0,
                                                              TCN_OWNER: self.muser } )
        total = manager.tableHandler[TN_LOCAL].getRowCount( { TCN_TRASH: 1,
                                                              TCN_OWNER: self.muser } )        
        system_count[manager.FLD_TRASH] = (new, total)
        
        # sent count
        total = manager.tableHandler[TN_SENT].getRowCount( { TCN_DRAFT:   0,
                                                             TCN_SSENDER: self.muser } )        
        system_count[manager.FLD_OUTBOX] = ('*', total)
        
        # draft count
        total = manager.tableHandler[TN_SENT].getRowCount( { TCN_DRAFT:   1,
                                                             TCN_SSENDER: self.muser } )        
        system_count[manager.FLD_DRAFTS] = ('*', total)
        
        if self.draft:
            current_fld = manager.FLD_DRAFTS
        else:
            current_fld = manager.FLD_OUTBOX
        
        # TODO: nice layout
        for folder in manager.SYSTEM_FOLDER:
            if folder == current_fld:
                start = '<b>'
                end   = '</b>'
            else:
                start = ''
                end   = ''
            uri = '%s/dlgHandler/%s/show?folder=%s' % (url, manager.FLD_DLGS[folder], folder)
            
            label = start + folder + ' (' + str( system_count[folder][0] ) + '/' + str( system_count[folder][1] ) + ')' + end
            
            entry = hgLabel(label, uri = uri, parent = widget)
            widget.insertItem( text = str( entry ) )
            
        for folder in folders:
            uri = '%s/dlgHandler/dlgMessageCenter/show?folder=%s' % (url, str(folder[TCN_AUTOID]))

            constraints = { TCN_FOLDER: folder[TCN_AUTOID], 
                            TCN_TRASH:  0}
            total = manager.tableHandler[TN_LOCAL].getRowCount( constraints )
            constraints[TCN_READ] = 0
            new   = manager.tableHandler[TN_LOCAL].getRowCount( constraints )
            
            label = folder[TCN_FOLDERNAME] + ' (' + str(new) + '/' + str(total) + ')'

            entry = hgLabel(label, uri = uri, parent = widget)
            widget.insertItem( text = str( entry ) )        
        
        return widget
    
        
    def layoutFolder(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
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

        c = 0
        
        # print foldername
        if self.draft:
            foldlab = hgLabel('<b>' + manager.FLD_DRAFTS + '</b>', parent = widget)
        else:
            foldlab = hgLabel('<b>' + manager.FLD_OUTBOX + '</b>', parent = widget)
        
        if self.threadview:
            foldlab += ' (Thread View)'

        wlay.addWidget( foldlab, 0, c )
        c += 1

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c )
        c += 1


        # msg count 
        if self.msgcount == 1:
            countlab = str(self.msgcount) + ' Message'
        else: 
            countlab = str(self.msgcount) + ' Messages'
        wlay.addWidget( hgLabel(countlab, parent = widget), 0, c )
        c += 1
        
        return widget
    

    def layoutFunctions(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        #if not widget:      
        widget = hgWidget(parent=parent)
        wlay   = hgGridLayout( widget, 12, 4 )
        #else:
        #    widget.removeChildren()
        #    wlay = widget.layout()
        
        c = 0
        
        self.data.newButton.reparent(widget)
        wlay.addWidget( self.data.newButton, 0, c )        
        c += 1
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c )
        c += 1

        # action selection box
        self.data.actionCB = hgComboBox(name = 'action', parent = widget)

        self.data.actionCB.insertItem('Action...',    ''                       )
        #if self.threadview:
        #    self.data.actionCB.insertItem(DLG_ACTLABEL[STD_VIEW],     STD_VIEW       )
        #else:
        #    self.data.actionCB.insertItem(DLG_ACTLABEL[THREAD_GROUP], THREAD_GROUP   )
        #self.data.actionCB.insertItem('------------', '')
        self.data.actionCB.insertItem(DLG_ACTLABEL[DELETE_MSG],  DELETE_MSG    )
        self.data.actionCB.insertItem('------------', '')
        self.data.actionCB.insertItem(DLG_ACTLABEL[EMPTY_TRASH], EMPTY_TRASH   )
        
        self.data.actionCB.setCurrentItem(0)
            
        self.connect( self.data.actionCB.valueChanged,   self.setMsgAction )
        
        wlay.addWidget( self.data.actionCB, 0, c )
        c += 1

        wlay.addWidget( hgLabel('&nbsp;', parent = widget), 0, c )
        c += 1
        self.data.goButton.reparent(widget)
        wlay.addWidget( self.data.goButton, 0, c )
        c += 1

        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c )
        c += 1

        # navigation
        # total navig
        if self.start == 0:
            img   = manager.iconHandler.getImageObject(IMG_FIRST_INACT)            
            first = hgLabel(img.tag(), parent = widget)

            img   = manager.iconHandler.getImageObject(IMG_BWD_INACT)            
            bwd   = hgLabel(img.tag(), parent = widget)
        else:
            self.data.firstButton.reparent(widget)
            self.data.prevButton.reparent(widget)
            first = self.data.firstButton
            bwd   = self.data.prevButton

        wlay.addWidget( first, 0, c )
        c += 1
        wlay.addWidget( bwd, 0, c )
        c += 1

        if self.start < self.msgcount:
            start = self.start + 1
            end   = start + len(self.messages) - 1
        else:
            start = self.start
            end   = self.start
            
        wlay.addWidget( hgLabel('&nbsp;%s - %s&nbsp;' % (start, end), parent = widget), 0, c, hg.AlignVCenter )
        c += 1

        if self.start + self.entriespp >= self.msgcount:
            img   = manager.iconHandler.getImageObject(IMG_LAST_INACT)            
            last = hgLabel(img.tag(), parent = widget)

            img   = manager.iconHandler.getImageObject(IMG_FWD_INACT)            
            fwd   = hgLabel(img.tag(), parent = widget)
        else:
            self.data.nextButton.reparent(widget)
            self.data.lastButton.reparent(widget)
            fwd  = self.data.nextButton
            last = self.data.lastButton
        
        wlay.addWidget( fwd, 0, c )
        c += 1
        wlay.addWidget( last, 0, c )
        c += 1

        return widget

    
    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data

        # general information  
        if not widget:      
            widget = hgWidget(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        wlay = widget.layout()

        r = 0

        # messages
        self.msgbox = hgTable(parent = widget)
        wlay.addWidget( self.msgbox, r, 0)
        self.displayMessages(manager)
        r += 1

        # append the all button
        if self.msgcount > 0:
            self.all_cb = hgCheckBox(text = 'Select All', value = 'Select All', name = 'all', parent = widget)
            self.all_cb.setToolTip('Select all Messages') 
            wlay.addWidget( self.all_cb, r, 0)
            self.connect( self.all_cb.stateChanged, self.setSelectAll )
        else:
            wlay.addWidget( hgLabel('<b>No Messages</b>', parent = widget), r, 0)

        r += 1

        return widget
        

    def displayMessages(self, manager):
        """\brief Get the button layout."""
        
        if not self.messages:
            return
        
        tobj = manager.tableHandler[TN_SENT]

        tab = hgTable(spacing = '0', parent = self.msgbox)
        
        self.msgbox[0, 0] = tab

        self.createSortBar(manager, tab)

        # reset btn to auto id relation
        self.data.msgCBList    = []
        self.threadbtn2aid     = {}
        self.fwdbtn2aid        = {}
        self.delbtn2aid        = {}
        self.checkbox2aid      = {}
        
        # get image properties
        thread_icon = manager.iconHandler.get(IMG_THREAD,     path=True).getIconDict()        
        fwd_icon    = manager.iconHandler.get(IMG_FORWARD,    path=True).getIconDict()        
        del_icon    = manager.iconHandler.get(IMG_DELETE,     path=True).getIconDict()        
        
        i = 1
        for i, msg in enumerate(self.messages):
            
            aid = msg[TCN_AUTOID]
            
            c = 0
            
            # checkbox
            name = 'check_' + str(aid)
            msgcb = hgCheckBox(value  = name, 
                               parent = tab, 
                               name   = name)
            tab[i+1, 0] = msgcb
            self.data.msgCBList.append(msgcb)
            self.checkbox2aid[name] = aid
            
            c += 1

            # thread
            constraints = { TCN_THREAD: msg[TCN_THREAD],
                            TCN_OWNER:  self.muser
                          }
            msgin  = manager.tableHandler[TN_SENT].getRowCount( constraints )
            constraints = { TCN_THREAD:  msg[TCN_THREAD],
                            TCN_SSENDER: self.muser
                          }
            msgout = manager.tableHandler[TN_SENT].getRowCount( constraints )
            
            if msgin + msgout > 1:
                name = 'threadof_' + str(aid)
                btn = hgPushButton(text = name, name = name, icon = thread_icon, parent = tab)
                btn.setToolTip('Show Thread')
                tab[i+1, c] = btn
                self.connect( btn.clickedButton, self.thread )
                self.threadbtn2aid[name] = aid
                tab[i+1, c] = btn
            c += 1

            # subject
            link = manager.getLink(TN_SENT, None, msg, parent = tab)
            linktext = link.getText()
            link.setToolTip(linktext)
            if len(linktext) > 50:
                link.setText(linktext[:48] + '...')
            tab[i+1, c] = link
            c += 1
            
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # sender
            link = manager.getLink(TN_MUSER, msg[TCN_SSENDER], parent = tab)
            tab[i+1, c] = link
            c += 1
                        
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # date
            tab[i+1, c] = hgLabel(msg['entrydate'], parent = tab)
            c += 1
            
            tab[i+1, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
            c += 1

            # reply
            name = 'fwd_' + str(aid)
            btn = hgPushButton(text = name, name = name, icon = fwd_icon, parent = tab)
            btn.setToolTip('Forward')
            tab[i+1, c] = btn
            self.connect( btn.clickedButton, self.forward )
            self.fwdbtn2aid[name] = aid
            
            c += 1

            # delete
            name = 'delete_' + str(aid)
            btn = hgPushButton(text = name, name = name, icon = del_icon, parent = tab)
            btn.setToolTip('Delete Message')
            tab[i+1, c] = btn
            self.connect( btn.clickedButton, self.deleteMsg )
            self.delbtn2aid[name] = aid
                        
            c += 1
            
            if not i % 2:
                for cc in xrange(0, c):
                    tab.setCellBackgroundColor(i+1, cc, '#E0E0DA')

            i += 1        

        
    def createSortBar(self, manager, tab):
        """\brief Get the button layout."""
        
        tobj = manager.tableHandler[TN_SENT]

        # leave space for checkbox and threadview
        c = 2
        
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
        label = tobj.getLabelWidget(TCN_SSENDER, parent = tab)
        box.add( label                      )
        box.add( self.data.sortSenderButton )
        tab[0, c] = box
        c += 1
        
        tab[0, c] = hgLabel('&nbsp;&nbsp;', parent = tab)
        c += 1

        box = hgHBox( parent = tab )
        box.layout().data.expanding = hgSizePolicy.NoDirection        
        label = tobj.getLabelWidget(TCN_SUBJECT, parent = tab)
        label.setText('Date')
        box.add( label                    )
        box.add( self.data.sortDateButton )
        tab[0, c] = box
        c += 1

        

    # data manipulation
    def setMsgAction(self, value):
        """\brief Sets the new folder for msg."""

        self.action = value


    def setSelectAll(self, state):
        """\brief Sets the name for the new folder."""

        self.all = self.all_cb.isChecked()


    def setSorting(self, order):
        """\brief Sort messages.
        """
        
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


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""
        
        return self.draft
        
        
    def resetData(self):
        """"""
        self.draft      = 0
        self.all        = False
        self.messages   = []
        self.aid2msg    = {}
        self.sortbtn    = None
        self.start      = 0
        self.msgcount   = 0
        self.orderfield = 'entrydate'
        self.orderdir   = 0
        self.action     = ''      
        
        
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
        elif self.result() == self.Jump:
            self.performJump(manager)
            self.setResult(self.Running)
        elif self.result() == self.Forward:
            self.performForward(manager)
        elif self.result() == self.Delete:
            self.performDelete(manager)
            self.setResult(self.Running)
        elif self.result() == self.Thread:
            self.performThread(manager)
        
        
      # button callbacks stubs
    def newMsg(self):
        """"""
        self.setResult(self.New)


    def forward(self, btnname):
        """"""
        self.btnname = btnname
        self.setResult(self.Forward)


    def deleteMsg(self, btnname):
        """"""
        self.btnname = btnname
        self.setResult(self.Delete)


    def thread(self, btnname):
        """"""
        self.btnname = btnname
        self.setResult(self.Thread)


    def goAction(self):
        """"""
        self.setResult(self.Go)


    def sort(self, btnname):
        """"""
        self.sortbtn = btnname
        self.setResult(self.Sort)


    def first(self):
        """"""
        if self.start > 0:
            self.start = 0
            self.setResult(self.Jump)


    def last(self):
        """"""
        (pages, rest) = divmod(self.msgcount, self.entriespp)
        
        if rest == 0 and pages > 0:
            pages -= 1
        
        if self.start != pages * self.entriespp:
            self.start = pages * self.entriespp
            self.setResult(self.Jump)


    def prev(self):
        """"""
        if self.start >= self.entriespp:
            self.start -= self.entriespp    
            self.setResult(self.Jump)


    def next(self):
        """"""
        if self.start + self.entriespp < self.msgcount:
            self.start += self.entriespp    
            self.setResult(self.Jump)


    # callback implementations
    def performRejected(self, manager):
        """\reimp"""
        pass


    def performNew(self, manager):
        """\reimp"""
        # set send dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgSendMsg/show' % (url)

        self.setTarget(target)
        self.target_url = target
        

    def performJump(self, manager):
        """\reimp"""
        self.initLayout(manager)


    def performForward(self, manager):
        """\reimp"""
        
        msg_id = self.fwdbtn2aid.get(self.btnname, 0)
        
        if not msg_id:
            return 
            
        # set send dlg
        url    = manager.absolute_url()
        if self.draft:
            target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, msg_id, TCN_DRAFT)
        else:
            target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, msg_id, MSG_OP_FWD)

        self.setTarget(target)
        self.target_url = target
        

    def performDelete(self, manager):
        """\reimp"""
        
        msg_id = self.delbtn2aid.get(self.btnname, 0)
        
        if msg_id:
            msg = self.aid2msg[msg_id]
            
            manager.deleteEntries( TN_SENT, [msg_id] )
                    
            # adjust page if necessary
            if len(self.messages) == 1 and \
               self.start > 0:
                self.start -= self.entriespp
                assert(self.start >= 0)
            
            self.initLayout(manager)


    def performThread(self, manager):
        """\reimp"""
        
        msg_id = self.threadbtn2aid.get(self.btnname, 0)
        
        if not msg_id:
            return 
            
        msg = self.aid2msg[msg_id]
        
        # set send dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgThreadView/show?id=%s' % (url, msg[TCN_THREAD])

        self.setTarget(target)
        self.target_url = target
        

    def performGo(self, manager):
        """\reimp"""
        
        if not self.action:
            return
                
        # get checked messages
        msg_ids = []
        
        if self.all:
            msg_ids = self.aid2msg.keys()
        
        for cb in self.data.msgCBList:
            if cb.isChecked():
                if not self.all:
                    msg_ids.append( self.checkbox2aid[cb.getName()] )
                cb.setChecked(False)

        # empty trash
        if self.action == EMPTY_TRASH:
            # get autoidlist, delete entries
            constraints = {TCN_OWNER: self.muser,
                           TCN_TRASH: 1}
            trash_ids = manager.tableHandler[TN_LOCAL].getEntryAutoidList(constraints = constraints)
            
            manager.deleteEntries(TN_LOCAL, [trash_ids])
            
        # delete messages
        elif self.action == DELETE_MSG:
            manager.deleteEntries( TN_SENT, msg_ids )
        # (de)activate threadview
        elif self.action in [ THREAD_GROUP, STD_VIEW ]:
            self.threadview = self.action == THREAD_GROUP
        # nothing else
        else:
            pass
        
        self.initLayout(manager)
            
        
    def performSort(self, manager):
        """\reimp"""
        
        if not self.sortbtn:
            return
        
        self.setSorting(self.sortbtn)
        
        self.sortbtn = None

        self.initLayout(manager)

