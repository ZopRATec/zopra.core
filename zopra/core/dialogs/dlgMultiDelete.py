############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from types                              import ListType

from PyHtmlGUI.dialogs.hgDialog         import hgDialog
from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy
from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgGroupBox       import hgGroupBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.constants               import ZC
from zopra.core.elements.Buttons        import BTN_L_DELETE, \
                                               DLG_FUNCTION
from zopra.core.dialogs                 import DLG_SHOW
from zopra.core.dialogs.guiHandler      import guiHandler
from zopra.core.security.GUIPermission  import GUIPermission


class dlgMultiDeletePrivate:
    """\class dlgMultiDeletePrivate"""

    def __init__(self):
        """\brief Constructs the private part of the dlgMultiDelete."""
        self.mgr           = None
        self.table         = None
        self.ids           = []
        self.retmode       = None
        self.rettable      = None
        self.retid         = None
        self.retdata       = {}
        self.data_dicts    = {}
        self.databox       = None
        self.btnbox        = None
        self.okButton      = None
        self.cancelButton  = None
        self.msgbox        = None


class dlgMultiDelete( hgDialog, guiHandler ):
    """\class dlgMultiDelete

    \brief Ask for confirmation for deletion of items.
    """
    _className = 'dlgMultiDelete'
    _classType = hgDialog._classType + [_className]

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new confirm deletion dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Delete Entry'

        # dlg private data
        self.data = dlgMultiDeletePrivate()

        table = param_dict.get('table', None)
        ids    = param_dict.get('autoids',    None)
        
        if not ids: 
            ids = []
        elif not isinstance(ids, ListType):
            ids = [ids]
        
        int_ids = []
        for id in ids:        
            try:
                int_ids.append(int(id))
            except:
                pass
        
        # check request
        if not table or not int_ids:
            manager.displayError('Incomplete request.', 'Error')

        # check table
        if not manager.tableHandler.has_key(table):
            manager.displayError('Table %s doesn\'t exist in %s.' % (table, manager.getTitle()), 'Database Error')
        
        # check table access rights
        if not manager.hasGUIPermission(table, GUIPermission.SC_DELETE):
            manager.displayError('Insufficient access rights.', 'Access Error')

        # check entry
        for id in int_ids:
            entry_dict = manager.tableHandler[table].getEntry(id)

            if not entry_dict:
                manager.displayError('Entry with id %s doesn\'t exist in table %s in %s.' % (table, manager.getTitle()), 'Database Error')

            if not manager.hasEntryPermission(table, descr_dict = entry_dict, permission_request = ZC.SC_DEL):
                manager.displayError('Insufficient access rights.', 'Access Error')
                
            self.data.data_dicts[id] = entry_dict


        if len(int_ids) == 1:
            self.caption             = 'Delete Entry'
        else:
            self.caption             = 'Delete Entries'

        self.data.table     = table
        self.data.ids       = int_ids

        self.data.retmode  = param_dict.get('retmode',  DLG_SHOW)
        
        # store the search params from the request?
        # they should be accessible in first execDlg - call
        # or in param_dict here
        self.data.rettable = param_dict.get('rettable', None)
        self.data.retid    = param_dict.get('retid',    None)
        
        
        # create in nice tab order
        self.data.okButton      = hgPushButton( parent = self, name = 'ok'     )
        self.data.cancelButton  = hgPushButton( parent = self, name = 'cancel' )

        self.data.okButton.setText(  '&Ok'  )
        self.data.cancelButton.setText( '&Cancel' )

        # connect the signals to the slots
        self.connect( self.data.okButton.clicked,       self.accept  )
        self.connect( self.data.cancelButton.clicked,   self.reject  )

        self.initLayout(manager)


    def initLayout(self, manager):
        """\brief Initialise the dialog layout."""

        # create layout
        page  = hgTable(parent = self.getForm())
        self.add(page)
        
        self.data.page = page
        
        self.data.databox = self.layoutData(manager, parent = page)
        page[0, 0] = self.data.databox

        self.data.btnbox = self.layoutButtons(parent = page)
        page[2, 0] = self.data.btnbox
        page.setCellAlignment(1, 0, 'center')


    def layoutData(self, manager, parent = None):
        """\brief Get the button layout."""
        # get the data
        tobj = manager.tableHandler[self.data.table]

        # general information  
        widget = hgGroupBox(parent=parent)
        wlay = hgGridLayout( widget, 12, 4 )

        # label and question
        entity = tobj.getLabel()
        widget.caption = '%s deletion' % entity
        ask = hgLabel('Do you really want to delete the following %s entries?' % (entity), parent = widget)
        wlay.addWidget( ask, 0, 0)
        spacer = hgLabel('&nbsp;', parent = widget)
        wlay.addWidget( spacer, 1, 0)
        
        r = 2
        for id in self.data.ids:
            entry = self.getDataDict(id)
            link   = manager.getLink(self.data.table, None, entry, parent = widget) 
            wlay.addWidget( link, r, 0)
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


    def layoutButtons(self, parent = None):
        """\brief Get the button layout."""
        widget = hgHBox(parent=parent)
        widget.layout().data.expanding = hgSizePolicy.NoDirection
        
        widget.add( self.data.okButton     )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.cancelButton )

        return widget


    def addMessage(self, message):
        """\brief Initialise the message layout."""
        # for now, after showing the message, nothing else can happen
        # target: a dialog the can be used to unselect some of the entries.
        if not self.data.msgbox:
            self.data.msgbox = self.layoutMessages(parent = self.data.page)
            self.data.page[1, 0] = self.data.msgbox
        
            mwidg = hgLabel(message, parent = self.data.msgbox)
            self.data.msgbox.layout().addWidget(mwidg, 0, 0)


    # the return data needs to be set extra (too many keys to put them into params on init and take them out again
    def setReturnParams(self, REQUEST):
        """\brief set the return params"""
        for key in REQUEST.form.keys():
            self.data.retdata[key] = REQUEST.form[key]


    def getDataDict(self, id):
        """\brief Get entry dict from dialog data."""

        if not id in self.data.ids:
            return {}
        
        return self.data.data_dicts[id]


    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Evaluates the \a REQUEST object and determines the changes
                  of the widgets.
        """
        # call superclass execDlg
        guiHandler.execDlg(self, manager, REQUEST)
        
        if self.result() == self.Accepted:
            # we are accepted, but cannot use performAccepted
            self.performCustomAccepted(manager)
        
    
    def makeTargetUrl(self, manager_url):
        """\brief build the search result page target url"""
        values = []
        # we have the data
        for key in self.data.retdata.keys():
            if key == DLG_FUNCTION + BTN_L_DELETE:
                    continue
            value = self.data.retdata[key]
            if isinstance(value, ListType):
                for onevalue in value:
                    values.append('%s=%s' % (key, onevalue))
            else:
                values.append('%s=%s' % (key, value))
        url = '%s/showList?%s' % (manager_url, '&'.join(values))
        return url
    
    
    def performAccepted(self, manager):
        """\brief only does target url setting"""
        # fall back to managers standard page
        url = manager.absolute_url()
        if self.data.rettable and self.data.retmode and self.data.retid:
            # got called from somewhere, return to an entry
            dname = manager.getDialogName(self.data.rettable, self.data.retmode)
            if dname:
                url = '%s/dlgHandler/%s/show?id=%s' % (url, dname, self.data.retid)
        elif self.data.retdata:
            # got called form search result page (getTableEntryListHtml), return there
            # params are stored in self.data.retdata

            url = self.makeTargetUrl(url)

        self.setTarget(url)
        self.target_url = url
    
    
    def performCustomAccepted(self, manager):
        """\brief custom accepted function that can return the dialog to running state."""
        # acquire REQUEST
        REQUEST = manager.REQUEST
        # delete entries
        msg = manager.deleteEntries(self.data.table, self.data.ids, REQUEST)
        if msg and msg != True:
            # got some error message back -> still running
            self.addMessage(msg + ' Press cancel to return.')
            self.setResult(self.Running)
            return
    

    def performRejected(self, manager):
        """\brief Cancel-Button pressed, return to former page"""
        # retrieving all request info and recalling the search results page seems the way
        # should retain the checked items by passing all REQUEST-contents (except the delete button)
        # done by makeTargetUrl
        
        # manager url
        url   = manager.absolute_url()
        
        # check wether we have the data we need
        if self.data.retdata:
            # we have it, build search results page url
            url = self.makeTargetUrl(url)
      
        else:  
            # fall back to first entry -> doesn't work for non-dialog managers
            dname = manager.getDialogName(self.data.table, DLG_SHOW)
            # if no dialog was found, url is still the manager url (base fallback)
            if dname:
                url = '%s/dlgHandler/%s/show?id=%s' % (url, dname, self.data.ids[0])
        self.setTarget(url)
        self.target_url = url
