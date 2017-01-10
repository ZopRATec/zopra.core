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
                                                    TCN_GSENDER,    \
                                                    IMG_BWD,        \
                                                    IMG_FWD,        \
                                                    IMG_BWD_INACT,  \
                                                    IMG_FWD_INACT


OP_FORWARD  = 'forward_sent'

SEND_OPS = [OP_FORWARD]

class dlgReadGMsgPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.page           = None
        self.folderbox      = None
        self.databox        = None
        self.btnbox         = None
        self.msg_count      = None
        self.deleteButton   = None
        self.replyButton    = None
        self.prevButton     = None
        self.nextButton     = None
        self.closeButton    = None
        self.closeAccel     = None
        self.folderList     = None


class dlgReadGMsg( hgDialog, guiHandler ):
    """\class dlgReadGMsg

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgReadGMsg'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Reply    =  3
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

        self.caption             = 'Read Global Message'

        # dlg private data
        self.data = dlgReadGMsgPrivate()

        # init values
        self.resetData()
        
        # get the security lvl
        zopratype = manager.getZopraType()
        perm = manager.getGUIPermission()
        self.super = perm.hasMinimumRole(perm.SC_SUPER)
        self.super = self.super or perm.hasSpecialRole(zopratype + 'Superuser')

        self.muser = manager.getCurrentMUser()[TCN_AUTOID]

        try:
            self.id = int( param_dict.get('id') )
        except:
            manager.displayError('No valid message id provided', 'Error')
        
        if self.id:            
            self.msg = manager.tableHandler[TN_GLOBAL].getEntry(self.id)
            
            if not self.msg:
                manager.displayError('No valid message id provided', 'Error')
                
        else:
            manager.displayError('No valid message id provided', 'Error')


        # init buttons
        fwd_icon = manager.iconHandler.get(IMG_FWD, path=True).getIconDict()
        bwd_icon = manager.iconHandler.get(IMG_BWD, path=True).getIconDict()        

        self.data.prevButton      = hgPushButton( parent = self, name = 'prev',  icon = fwd_icon )
        self.data.nextButton      = hgPushButton( parent = self, name = 'next',  icon = bwd_icon )
        self.data.deleteButton    = hgPushButton( parent = self, name = 'delete' )
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'  )
        self.data.replyButton     = hgPushButton( parent = self, name = 'reply'  )

        self.data.nextButton.setText     ( '&Next'      )
        self.data.prevButton.setText     ( '&Prev'      )
        self.data.deleteButton.setText   ( '&Delete'    )
        self.data.closeButton.setText    ( '&Close'     )
        self.data.replyButton.setText    ( '&Reply'     )

        self.data.nextButton.setToolTip     ( 'Next Message'     )
        self.data.prevButton.setToolTip     ( 'Previous Message' )
        self.data.deleteButton.setToolTip   ( 'Delete'           )
        self.data.closeButton.setToolTip    ( 'Close'            )
        self.data.replyButton.setToolTip    ( 'Reply'            )

        # connect the signals to the slots
        self.connect( self.data.prevButton.clicked,     self.prev       )
        self.connect( self.data.nextButton.clicked,     self.next       )
        self.connect( self.data.deleteButton.clicked,   self.delete     )
        self.connect( self.data.closeButton.clicked,    self.reject     )
        self.connect( self.data.replyButton.clicked,    self.reply      )
        
        # init layout
        self.initLayout(manager)
        

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


    def layoutFolder(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        tobj = manager.tableHandler[TN_GLOBAL]

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
        foldlab = hgLabel(manager.FLD_GLOBAL, parent = widget)
        wlay.addWidget( foldlab, 0, c )

        c += 1

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), 0, c)
        
        c += 1
        
        # get the message counts
        total    = manager.tableHandler[TN_GLOBAL].getRowCount( )
        
        constraints = { }
        constraints[TCN_AUTOID] = '_<=_' + str(self.id)
        current  = manager.tableHandler[TN_GLOBAL].getRowCount( constraints )
        
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
        
        widget.add( self.data.replyButton   )
        widget.add( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget)     )        
        widget.add( self.data.deleteButton   )
        self.data.deleteButton.setEnabled(self.super)

        return widget

    
    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        msg = self.getDataDict()
        tobj = manager.tableHandler[TN_GLOBAL]
            
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
        entry = manager.getFunctionWidget(TN_GLOBAL,
                                          TCN_SUBJECT,
                                          widget,
                                          MASK_SHOW,
                                          msg)
        wlay.addWidget(entry, r, 2)
        r += 1
        
        # from
        label = tobj.getLabelWidget(TCN_GSENDER, parent = widget)
        label.setToolTip('Sender of the Message') 
        label.setText('From:')
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_GLOBAL,
                                          TCN_GSENDER,
                                          widget,
                                          MASK_SHOW,
                                          msg)
        wlay.addWidget(entry, r, 2)
        r += 1
                
        # date
        # just get any label widget and set desired text afterwards (saves label formatting)
        label = tobj.getLabelWidget(TCN_GSENDER, parent = widget)
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
        entry = manager.getFunctionWidget(TN_GLOBAL,
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
            manager.checkGUIPermission(TN_GLOBAL, secGUIPermission.SC_VIEW)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Reply:
            self.performReply(manager)
        elif self.result() == self.Delete:
            self.performDelete(manager)
        elif self.result() == self.Prev:
            self.performPrev(manager)
            self.setResult(self.Running)
        elif self.result() == self.Next:
            self.performNext(manager)
            self.setResult(self.Running)
        
        
    # button callbacks stubs
    def reply(self):
        """"""
        self.setResult(self.Reply)


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
        # set dlg target
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgGMessageCenter/show' % (url)

        self.setTarget(target)
        self.target_url = target


    def performReply(self, manager):
        """\reimp"""

        # set send dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgSendMsg/show?id=%s&op=%s' % (url, self.msg[TCN_AUTOID], manager.FLD_GLOBAL)

        self.setTarget(target)
        self.target_url = target


    def performDelete(self, manager):
        """\reimp"""
        
        if not self.super:
            manager.displayError('You are not permitted to delete global messages.', 'Security Error')

        manager.deleteEntries( TN_GLOBAL, self.msg[TCN_AUTOID] )
                    
        # set dlg target
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgGMessageCenter/show' % (url)

        self.setTarget(target)
        self.target_url = target

    
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
        
        tobj = manager.tableHandler[TN_GLOBAL]        
        
        newmsg = tobj.getEntryList(show_number = 1, constraints = constraints, direction = direction)
        
        if not newmsg:
            manager.displayError('Couldn\'t find message.', 
                                 'Database error')
            
        self.id  = newmsg[0][TCN_AUTOID]
        self.msg = newmsg[0]
    
        self.initLayout(manager)


