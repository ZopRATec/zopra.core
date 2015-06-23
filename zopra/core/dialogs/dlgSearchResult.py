##############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                      #
#    webmaster@ingo-keller.de                                                #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################

from types                              import IntType,     \
                                               ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.dialogs.hgDialog         import hgDialog

#
# ZMOM Imports
#
from zopra.core.dialogs.dlgTableEntry   import dlgTableEntryPrivate
from zopra.core.dialogs.guiHandler      import guiHandler


class dlgSearchResultPrivate:
    """\class dlgTableEntryPrivate Mainly Unimplemented, just a file to remind 
              me of doing this.
    """

    def __init__(self):
        """\brief Constructs a dlgTableEntryPrivate object."""
        # static information
        self.tree  = None
        self.table = None
        self.showNum = 0

        # dynamic information
        self.direction   = None   # current search direction
        self.order       = []     # current order
        self.show_fields = []     # current attributes to show
        self.start_num   = 0      # current start number for display range


class dlgSearchResult(hgDialog, guiHandler):
    """\class SearchResult

    \brief dlgSearchResult is a dialog for generic search result handling.
           The result is a list of entries,
           whose visible attributes and shown range can be changed.
    """
    _className = 'dlgSearchResult'
    _classType = hgDialog._classType + [_className]

    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################

    # enum FunctionMode
    #Disable          = 0x0000
    #EnableNavigation = 0x0001   # dlg with navigation function
    #EnableInsert     = 0x0002   # dlg with insert function
    #EnableUpdate     = 0x0004   # dlg with change function
    #EnableDelete     = 0x0008   # dlg with delete function
    #EnableFunctions  = EnableInsert    | EnableUpdate | EnableDelete
    #EnableAll        = EnableFunctions | EnableNavigation
    #FunctionMode     = [ Disable,      EnableNavigation, EnableInsert,
    #                     EnableUpdate, EnableDelete,     EnableFunctions,
    #                     EnableAll ]

    # enum Buttons
    #Add              = 0
    #Update           = 1
    #Delete           = 2
    #Cancel           = 3
    #Buttons          = [ Add, Update, Delete, Cancel ]

    ## enum Mode
    #Add              = 0
    #Update           = 1
    #Delete           = 2
    #Mode             = [ Add, Update, Delete ]

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################
    def setCurrentAutoid(self, autoid):
        """\brief Sets the currentAutoid property."""
        assert self.checkType('autoid', autoid, IntType, True)
        self.content.autoid = autoid

    def getCurrentAutoId(self):
        """\brief Returns the currentAutoid property."""
        return self.content.autoid

    currentAutoid = property(getCurrentAutoId, setCurrentAutoid)

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict):
        """\brief Constructs a dlgTableEntry.

        param_dict keys:
            $constraint - a constraint dict (optional)
            $startnumber - number of start element of result range
            $table - the table name

        param_dict is only relevant for object instantiation.
        """
        hgDialog.__init__(self)
        guiHandler.__init__(self)

        self.content = dlgTableEntryPrivate()

        # tablename
        table = param_dict.get('table')
        self.content.table = table
        # search tree
        tree = manager.getSearchTreeTemplate(table)
        self.content.tree = tree

        # set name for dialog
        tobj = manager.tableHandler[table]
        self.setCaption( '%s Search' % tobj.getName() )

        # dialog handling
        self.isAccepted = False
        self.buttons    = [ None ] * len( self.Buttons )


    def initLayout(self):
        """\brief Initialise the dialogs design."""
        # use search mask of manager?
        pass


    def updateLayout(self, manager):
        """\brief Updates the layout of the content."""
        pass


    def execDlg(self, manager = None, REQUEST = None):
        """\brief Executes the dialog functions."""
        pass


    def setColumnOrder(self, order_list):
        """\brief Sets the column order according to \a order_list."""
        assert isinstance(order_list, ListType)
        if self.columnOrder != order_list:
            self.columnOrder = order_list
            self.updateLayout( manager )


    ##########################################################################
    #
    # Slot Methods
    #
    ##########################################################################
    def setAccepted(self):
        """\brief Sets the accepted state."""
        self.isAccepted = True
