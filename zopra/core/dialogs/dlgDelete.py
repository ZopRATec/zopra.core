############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from PyHtmlGUI.dialogs.hgDialog          import hgDialog

from PyHtmlGUI.kernel.hgGridLayout       import hgGridLayout
from PyHtmlGUI.kernel.hgTable            import hgTable
from PyHtmlGUI.kernel.hgWidget           import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy       import hgSizePolicy

from PyHtmlGUI.widgets.hgLabel           import hgLabel
from PyHtmlGUI.widgets.hgHBox            import hgHBox
from PyHtmlGUI.widgets.hgPushButton      import hgPushButton

from zopra.core.dialogs.guiHandler       import guiHandler

from zopra.core.security                 import SC_DEL

from zopra.core.security.GUIPermission   import GUIPermission

from zopra.core.tools.GenericManager     import DLG_SHOW



class dlgDeletePrivate:
    """\class dlgDeletePrivate"""

    def __init__(self):
        """\brief Constructs the private part of the dlgDelete."""
        self.mgr           = None
        self.table         = None
        self.id            = None
        self.retmode       = None
        self.rettable      = None
        self.retid         = None
        self.data_dict     = None
        self.databox       = None
        self.btnbox        = None
        self.okButton      = None
        self.cancelButton  = None


class dlgDelete( hgDialog, guiHandler ):
    """\class dlgDelete

    \brief Ask for confirmation for deletion of item.
    """
    _className = 'dlgDelete'
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
        self.data = dlgDeletePrivate()

        table = param_dict.get('table', None)
        id    = param_dict.get('id',    None)
        try:
            id = int(id)
        except:
            id = None

        
        # check request
        if not table or not id:
            manager.displayError('Incomplete request.', 'Error')

        # check table
        if not manager.tableHandler.has_key(table):
            manager.displayError('Table %s doesn\'t exist in %s.' % (table, manager.getTitle()), 'Database Error')
        
        # check table access rights
        if not manager or \
           not manager.hasGUIPermission(table, GUIPermission.SC_DELETE):
            manager.displayError('Insufficient access rights.', 'Access Error')

        # check entry
        entry_dict = manager.tableHandler[table].getEntry(id)

        if not entry_dict:
            manager.displayError('Entry with id %s doesn\'t exist in table %s in %s.' % (table, manager.getTitle()), 'Database Error')

        if not manager.hasEntryPermission(table, descr_dict = entry_dict, permission_request = SC_DEL):
            manager.displayError('Insufficient access rights.', 'Access Error')

        self.data.table     = table
        self.data.id        = id
        self.data.data_dict = entry_dict

        self.data.retmode  = param_dict.get('retmode',  DLG_SHOW)
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
        self.getForm().add(page)
        
        self.data.databox = self.layoutData(manager, parent = page)
        page[0, 0] = self.data.databox

        self.data.btnbox = self.layoutButtons(parent = page)
        page[1, 0] = self.data.btnbox
        page.setCellAlignment(1, 0, 'center')



    def layoutData(self, manager, parent = None):
        """\brief Get the button layout."""
        # get the data
        tobj = manager.tableHandler[self.data.table]

        # general information  
        widget = hgWidget(parent=parent)
        wlay = hgGridLayout( widget, 12, 4 )

        # spacing
        dict   = self.getDataDict()
        entity = tobj.getLabel()
        link   = manager.getLink(self.data.table, None, dict) 
        wlay.addWidget( hgLabel('<br>Do you really want to delete %s %s?<br><br>' % (entity, link.getHtml()), parent = widget), 0, 0)

        return widget    

    #   
    def layoutButtons(self, parent = None):
        """\brief Get the button layout."""
        widget = hgHBox(parent=parent)
        widget.layout().data.expanding = hgSizePolicy.NoDirection
        
        widget.add( self.data.okButton     )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.cancelButton )

        return widget


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""

        return self.data.data_dict


    # dialog handling
    def performAccepted(self, manager):
        """"""
        # delete entry
        manager.deleteEntries(self.data.table, self.data.id)
        #manager.tableHandler[self.data.table].deleteEntry(self.data.id)
        # fall back to managers standard page
        url = manager.absolute_url()
        if self.data.rettable and self.data.retid:
            dname = manager.getDialogName(self.data.rettable, self.data.retmode)
            if dname:
                url = '%s/dlgHandler/%s/show?id=%s' % (url, dname, self.data.retid)
        self.setTarget(url)
        self.target_url = url
    

    def performRejected(self, manager):
        """\reimp"""
        # fall back to show entry page
        url   = manager.absolute_url()
        dname = manager.getDialogName(self.data.table, DLG_SHOW)
        if dname:
            url = '%s/dlgHandler/%s/show?id=%s' % (url, dname, self.data.id)
        self.setTarget(url)
        self.target_url = url