############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgConfirm.py
__revision__ = '0.1'

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from Products.ZMOM.ZMOMCorePart         import TCN_AUTOID
                                               
from Products.ZMOM.dialogs.guiHandler   import guiHandler

from Products.ZMOM.AuditAndSecurity.managers import TN_MUSER,       \
                                                    TN_GLOBAL,      \
                                                    TN_SENT,        \
                                                    TCN_DRAFT,      \
                                                    TCN_GSENDER,    \
                                                    TCN_SSENDER,    \
                                                    TCN_SRECEIVER



class dlgConfirmPrivate:
    """\class dlgConfirmPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the dlgConfirm."""
        self.mgr           = None
        self.table         = None
        self.id            = None
        self.msg           = None
        self.retmode       = None
        self.rettable      = None
        self.retid         = None
        self.databox       = None
        self.btnbox        = None
        self.okButton      = None


class dlgConfirm( hgDialog, guiHandler ):
    """\class dlgConfirm

    \brief Ask for confirmation for deletion of item.
    """
    _className = 'dlgConfirm'
    _classType = hgDialog._classType + [_className]

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new confirm action dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        assert(manager)

        self.caption             = 'Confirm Action'

        # dlg private data
        self.data = dlgConfirmPrivate()

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
        if not table in [TN_GLOBAL, TN_SENT]:
            manager.displayError('Malformated request.', 'Error')
        
        # check entry
        msg = manager.tableHandler[table].getEntry(id)

        if not msg:
            manager.displayError('Message not found.', 'Database Error')
            
        # check access rigths
        muser = manager.getCurrentMUser()
        if table == TN_GLOBAL:
            if muser[TCN_AUTOID] != msg[TCN_GSENDER]:
                manager.displayError('Anauthorized access.', 'Access Error')
        elif table == TN_SENT:
            if muser[TCN_AUTOID] != msg[TCN_SSENDER]:
                manager.displayError('Anauthorized access.', 'Access Error')
        

        self.data.table     = table
        self.data.id        = id
        self.data.msg       = msg

        # create in nice tab order
        self.data.okButton      = hgPushButton( parent = self, name = 'ok'     )

        self.data.okButton.setText( '&Ok'  )

        # connect the signals to the slots
        self.connect( self.data.okButton.clicked,       self.accept  )

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
        # general information  
        widget = hgWidget(parent=parent)
        wlay = hgGridLayout( widget, 12, 4 )

        # spacing
        msg   = self.getDataDict()
        
        if self.data.table == TN_GLOBAL:
            wlay.addWidget( hgLabel('Global message has been sent.' , parent = widget), 0, 0)
        elif msg.get(TCN_DRAFT, 0):
            wlay.addWidget( hgLabel('Message has been stored in draft.' , parent = widget), 0, 0)
        else:
            wlay.addWidget( hgLabel('Message has been sent to: ' , parent = widget), 0, 0)
            wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;', parent = widget), 0, 1)
            
            for i, receiver in enumerate(msg[TCN_SRECEIVER]):
                wlay.addWidget( manager.getLink(TN_MUSER, receiver, parent = widget), i, 2)

        return widget    

    #   
    def layoutButtons(self, parent = None):
        """\brief Get the button layout."""
        widget = hgHBox(parent=parent)
        widget.layout().data.expanding = hgSizePolicy.NoDirection
        
        widget.add( self.data.okButton     )

        return widget


    def getDataDict(self):
        """\brief Get entry dict from dialog data."""

        return self.data.msg


    # dialog handling
    def performAccepted(self, manager):
        """"""
        # fall back to managers standard page
        url = manager.absolute_url()
        if self.data.table == TN_GLOBAL:
            dname = 'dlgGMessageCenter'
        else:
            dname = 'dlgMessageCenter'
                                        
        url = '%s/dlgHandler/%s/show' % (url, dname)
        
        self.setTarget(url)
        self.target_url = url
