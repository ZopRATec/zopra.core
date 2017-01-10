############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgMngFilters.py
__revision__ = '0.1'

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

from zopra.core.tools.managers import TN_FILTER,      \
                                                    TN_MUSER,       \
                                                    TN_FOLDER,      \
                                                    TCN_PRECEDENCE, \
                                                    TCN_OWNER,      \
                                                    TCN_NAME,       \
                                                    TCN_SORTID,     \
                                                    TCN_TARGET,     \
                                                    IMG_MOVEUP,     \
                                                    IMG_MOVEDOWN,   \
                                                    IMG_EDIT,       \
                                                    IMG_DELETE




class dlgMngFiltersPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.msgbox        = None
        self.btnbox        = None
        self.msg_count     = None
        self.closeButton   = None
        self.helpButton    = None
        self.closeAccel    = None
        self.helpAccel     = None
        self.labPrecedence = None


class dlgMngFilters( hgDialog, guiHandler ):
    """\class dlgMngFilters

    \brief Filter management for Messaging Manager.
    """
    _className = 'dlgMngFilters'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Created    = 3
    Edit       = 4
    Deleted    = 5
    MovedUp    = 6
    MovedDown  = 7
    Precedence = 8
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Manage Filters'

        # dlg private data
        self.data = dlgMngFiltersPrivate()

        # init values
        self.resetData()

        self.muser = manager.getCurrentMUser()
        filter_dicts = manager.tableHandler[TN_FILTER].getEntries(self.muser[TCN_AUTOID], TCN_OWNER, order = TCN_SORTID)

        for dict in filter_dicts:
            self.sort_ids.append(dict[TCN_SORTID])
            self.sid2filter[dict[TCN_SORTID]] = dict
            self.aid2filter[dict[TCN_AUTOID]] = dict
            
        
        self.data.msg_count       = 0

        # create in nice tab order
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )
        self.data.helpButton      = hgPushButton( parent = self, name = 'help'    )

        self.data.closeButton.setText  ( '&Close'        )
        self.data.helpButton.setText   ( '&Help'         )

        # connect the signals to the slots
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

        # precedence folder
        label = hgLabel('Filtering Rule:', parent = widget)
        label.setToolTip('Filtering rule') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget(label, r, 0)

        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)

        if self.muser.get(TCN_PRECEDENCE):
            rule = hgLabel('First Match', parent = widget)
        else:
            rule = hgLabel('Last Match', parent = widget)
        wlay.addWidget( rule, r, 2)
        self.labPrecedence = rule 

        wlay.addWidget( hgLabel('&nbsp;', parent = widget), r, 3)

        precedence_btn = hgPushButton(text = 'Toggle',  parent = widget, name = 'set_precedence' )
        self.connect( precedence_btn.clicked,    self.setPrecedence  )
        wlay.addWidget( precedence_btn, r, 4)

        r += 1

        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        

        # create filters
        label = hgLabel('Current Filter:', parent = widget)
        label.setToolTip('List of current filters.') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget(label, r, 0, hg.AlignTop)

        self.filterbox = hgTable(parent = widget)
        wlay.addMultiCellWidget( self.filterbox, r, r, 2,  5)
        self.displayFilters(manager)
        r += 1

        # spacing
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        # new filter
        create_btn = hgPushButton(text = 'New Filter',  parent = widget, name = 'create_filter' )
        self.connect( create_btn.clicked,    self.createFilter  )
        wlay.addWidget( create_btn, r, 2)

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
        
        widget.add( self.data.helpButton    )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.closeButton   )

        return widget
    

    def displayFilters(self, manager):
        """\brief Get the button layout."""
        # NOTE: uncommented line produces unexpected results
        #self.curimodbox.emptyTable()
        tab = hgTable(spacing = '0', parent = self.filterbox)
        self.filterbox[0, 0] = tab
        self.editbtn2sid     = {}
        self.delbtn2sid      = {}
        self.upbtn2sid       = {}
        self.downbtn2sid     = {}
        
        # no filters?
        if not self.sort_ids:
            tab[0, 0] = hgLabel('No Filters', parent = tab)
            
        
        # TODO: delete old buttons?
        i = -1
        for i, sid in enumerate(self.sort_ids):
            dict = self.sid2filter[sid]
            
            # filter name
            fname = manager.getFunctionWidget(TN_FILTER,
                                              TCN_NAME,
                                              tab,
                                              MASK_SHOW,
                                              dict)
            tab[i, 0] = fname
            
            tab[i, 1] = hgLabel('&nbsp;', parent = tab)

            # target folder
            if dict.get(TCN_TARGET):
                ftarget = manager.getLink(TN_FOLDER, dict[TCN_TARGET])
            else:
                url    = manager.absolute_url()
                trash = manager.FLD_TRASH
                uri = '%s/dlgHandler/%s/show?folder=%s' % (url, manager.FLD_DLGS[trash], trash)
                ftarget = hgLabel(trash, uri, parent = tab)
                
                
            tab[i, 2] = ftarget

            tab[i, 3] = hgLabel('&nbsp;', parent = tab)
            

            if i != len(self.sort_ids) - 1:
                name = 'down_' + str(sid)
                icon = manager.iconHandler.get(IMG_MOVEDOWN, path=True).getIconDict()
                btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
                btn.setToolTip('Move Filter down')
                tab[i, 4] = btn
                self.connect( btn.clickedButton,    self.moveFilterDown  )
                self.downbtn2sid[name] = sid
            else:
                tab[i, 4] = hgLabel('&nbsp;', parent = tab)
            if i != 0:
                name = 'up_' + str(sid)
                icon = manager.iconHandler.get(IMG_MOVEUP, path=True).getIconDict()
                btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
                btn.setToolTip('Move Filter up')
                tab[i, 5] = btn
                self.connect( btn.clickedButton,    self.moveFilterUp  )
                self.upbtn2sid[name] = sid
            else:
                tab[i, 5] = hgLabel('&nbsp;', parent = tab)
            tab[i, 6] = hgLabel('&nbsp;', parent = tab)

            # delete button
            name = 'edit_' + str(sid)
            icon = manager.iconHandler.get(IMG_EDIT, path=True).getIconDict()
            btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
            btn.setToolTip('Inspect Filter')
            tab[i, 7] = btn
            self.connect( btn.clickedButton,    self.editFilter  )
            self.editbtn2sid[name] = sid

            # delete button
            name = 'del_' + str(sid)
            icon = manager.iconHandler.get(IMG_DELETE, path=True).getIconDict()
            btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
            btn.setToolTip('Delete Filter')
            tab[i, 8] = btn
            self.connect( btn.clickedButton,    self.deleteFilter  )
            self.delbtn2sid[name] = sid

            if not i % 2:
                for c in xrange(0, 9):
                    tab.setCellBackgroundColor(i, c, '#E0E0DA')


        
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
    def getDataDict(self, autoid):
        """\brief Get entry dict from dialog data."""
                
        return self.aid2filter.get(autoid, {})
        
        
    def resetData(self):
        """"""
        self.sort_ids   = []
        self.sid2filter = {}
        self.aid2filter = {}
        self.filtername = ''
        self.btnname    = None
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_FILTER, secGUIPermission.SC_EDIT)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Created:
            self.performCreateFilter(manager)
        elif self.result() == self.Precedence:
            self.performSetPrecedence(manager)
            self.setResult(self.Running)
        elif self.result() == self.Edit:
            self.performEditFilter(manager)
        elif self.result() == self.Deleted:
            self.performDeleteFilter(manager)
            self.setResult(self.Running)
        elif self.result() == self.MovedUp:
            self.performMoveUp(manager)
            self.setResult(self.Running)
        elif self.result() == self.MovedDown:
            self.performMoveDown(manager)
            self.setResult(self.Running)
        
        
    # button callbacks   
    def setPrecedence(self):
        """\brief Creates a filter with the current filtername."""

        self.setResult(self.Precedence)
        

    def createFilter(self):
        """\brief"""

        self.setResult(self.Created)


    def editFilter(self, btnname):
        """\brief"""
        self.btnname = btnname
        self.setResult(self.Edit)


    def deleteFilter(self, btnname):
        """\brief."""
        self.btnname = btnname
        self.setResult(self.Deleted)

    
    def moveFilterUp(self, btnname):
        """\brief."""

        self.btnname = btnname
        self.setResult(self.MovedUp)

    
    def moveFilterDown(self, btnname):
        """\brief."""

        self.btnname = btnname
        self.setResult(self.MovedDown)

    
    def help(self):
        """"""
        self.resetMessages()
        self.addMessage('Manage filters for Messaging manager')
        self.addMessage('&nbsp;')
        self.addMessage('Add filter by pressing \'New Filter\'')
        self.addMessage('Change sorting by klicking the up and down arrows of the filters.')
        self.addMessage('Delete filter by klicking the red cross.')
        self.addMessage('Edit Filter by klicking the edit image.')


    def performRejected(self, manager):
        """\reimp"""
        self.resetMessages()


    def performSetPrecedence(self, manager):
        """\reimp"""
        self.resetMessages()

        if self.muser.get(TCN_PRECEDENCE):
            self.muser[TCN_PRECEDENCE] = 0
            self.labPrecedence.setText('Last Match')
        else:
            self.muser[TCN_PRECEDENCE] = 1
            self.labPrecedence.setText('First Match')
            
        if not manager.tableHandler[TN_MUSER].updateEntry(self.muser, self.muser[TCN_AUTOID]):
            manager.displayError('An error occured while updating settings.', 
                                 'Database error')
            
        self.addMessage('Filtering rule updated.')        
        

    def performCreateFilter(self, manager):
        """\reimp"""
        self.resetMessages()

        # set edit dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgConfigFilter/show' % (url)

        self.setTarget(target)
        self.target_url = target


        
    def performEditFilter(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.editbtn2sid[self.btnname]:
            return
        
        sid = self.editbtn2sid[self.btnname]
        
        filter = self.sid2filter[sid]
        
        self.btnname = None
        
        # set edit dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgConfigFilter/show?id=%s' % (url, sid)

        self.setTarget(target)
        self.target_url = target
                                    
            
    def performDeleteFilter(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.delbtn2sid[self.btnname]:
            return
        
        sid = self.delbtn2sid[self.btnname]
        
        filter = self.sid2filter[sid]
        
        # delete filter
        manager.deleteEntries(TN_FILTER, [ filter[TCN_AUTOID] ])
                    
        # remove entry from local data
        del self.aid2filter[filter[TCN_AUTOID]]
        del self.sid2filter[sid]
        self.sort_ids.remove(sid)
        self.btnname = None
        
        self.displayFilters(manager)
            
                    
    def performMoveUp(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.upbtn2sid[self.btnname]:
            return
        
        sid = self.upbtn2sid[self.btnname]
        
        self.performMove(manager, sid, up=True)
                            
 
    def performMoveDown(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.downbtn2sid[self.btnname]:
            return
        
        sid = self.downbtn2sid[self.btnname]
        
        self.performMove(manager, sid, up=False)
                    
                    
    def performMove(self, manager, sid, up = True):
        """\reimp"""
        filter = self.sid2filter[sid]

        sid2 = 0
        for i, current_sid in enumerate(self.sort_ids):
            if current_sid == sid:
                if not up and i+1 < len(self.sort_ids):
                    sid2 = self.sort_ids[i+1]
                if up and i > 0:
                    sid2 = self.sort_ids[i-1]
                break
                
        if not sid2:
            return
        
        filter2 = self.sid2filter[sid2]
        
        # perform exchange
        filter[TCN_SORTID], filter2[TCN_SORTID] = filter2[TCN_SORTID], filter[TCN_SORTID]
        
        
        if not manager.tableHandler[TN_FILTER].updateEntry(filter, filter[TCN_AUTOID]):
            manager.displayError('An error occured while moving filter', 
                                 'Database error')
        if not manager.tableHandler[TN_FILTER].updateEntry(filter2, filter2[TCN_AUTOID]):
            manager.displayError('An error occured while moving filter', 
                                 'Database error')
        
        self.sid2filter[sid], self.sid2filter[sid2] = self.sid2filter[sid2], self.sid2filter[sid]
        
        # reset btnname
        self.btnname = None
            
        self.displayFilters(manager)
 
                    
