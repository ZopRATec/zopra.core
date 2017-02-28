############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
"""\brief The ManagerPart is the basic manager class."""

#
# Python Language Imports
#
import os.path
from types                           import IntType, ListType, \
                                            StringType, TupleType
from copy                            import deepcopy, copy
from importlib                       import import_module

from zope.interface                  import implements

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                       import hg
from PyHtmlGUI.kernel.hgTable        import hgTable
from PyHtmlGUI.kernel.hgWidget       import hgWidget, hgALIGN_CENTER, hgALIGN_LEFT
from PyHtmlGUI.kernel.hgObject       import hgObject
from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout

from PyHtmlGUI.widgets.hgGroupBox    import hgGroupBox
from PyHtmlGUI.widgets.hgMenuBar     import hgMenuBar
from PyHtmlGUI.widgets.hgPopupMenu   import hgPopupMenu
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgLabel       import hgLabel,   \
                                            hgSPACE,   \
                                            hgNEWLINE, \
                                            hgProperty
from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton

#
# ZopRA Imports
#
from zopra.core                      import viewPermission, \
                                            modifyPermission, \
                                            managePermission, \
                                            HTML, \
                                            Image, \
                                            ClassSecurityInfo, \
                                            getSecurityManager,  ZC

from zopra.core.dialogs              import getStdDialog, \
                                            getStdZMOMDialog, \
                                            getEmbeddedDialog
from zopra.core.interfaces           import IZopRAManager, IZopRAProduct

from zopra.core.CorePart             import CorePart, \
                                            FILTER_EDIT,       \
                                            FCB_DEFAULT_FILTER_TEXT

from zopra.core.tables.Table              import TE_LOOKUPDATA,  \
                                                 TE_WITHHEADER,  \
                                                 TE_TRACKING
from zopra.core.elements.Styles.Default   import ssiDLG_LABEL_HL, ssiDLG_TOPBORDER

from zopra.core.Basket                    import Basket
from zopra.core.Classes                   import Column
from zopra.core.IconHandler               import IconHandler
from zopra.core.LevelCache                import LevelCache
from zopra.core.lists.ListHandler         import ListHandler
from zopra.core.tables.TableHandler       import TableHandler

from zopra.core.elements.Buttons          import DLG_FUNCTION, \
                                                 DLG_CUSTOM,   \
                                                 DLG_INC,      \
                                                 DLG_DEC,      \
                                                 BTN_L_NEXT,   \
                                                 BTN_L_PREV,   \
                                                 BTN_L_GO,     \
                                                 BTN_L_FIRST,  \
                                                 BTN_L_LAST,   \
                                                 BTN_L_DELETE, \
                                                 BTN_L_SEARCH, \
                                                 BTN_L_EXPORT, \
                                                 BTN_MULTIEDIT,    \
                                                 BTN_L_SHOW_NUMBER,\
                                                 BTN_L_SELECT_ALL, \
                                                 mpfRefreshButton, \
                                                 mpfAddButton,     \
                                                 mpfResetButton,   \
                                                 mpfUpdateButton,  \
                                                 mpfEditButton,    \
                                                 mpfBasketAddButton,\
                                                 mpfBasketPopButton,\
                                                 mpfSearchButton,  \
                                                 mpfDeleteButton,  \
                                                 mpfExportButton,  \
                                                 mpfCloseButton,   \
                                                 mpfNumberButton,  \
                                                 mpfSelectAllButton, \
                                                 getPressedButton

from zopra.core.dialogs.Dialog             import Dialog
from zopra.core.dialogs.DialogHandler      import DialogHandler

from zopra.core.security.GUIPermission     import GUIPermission

from zopra.core.utils                      import getZopRAPath,\
                                                  getTableDefinition, \
                                                  getIconsDefinition
from zopra.core.widgets.hgSortButton       import hgSortButton
from zopra.core.widgets                    import dlgLabel, dlgMiniSpacer


from zopra.core.dialogs.dlgTableEntry  import dlgTableEntry
from zopra.core.dialogs.dlgMultiDelete import dlgMultiDelete

from zopra.core.mixins import ManagerFinderMixin

#
# help function for letter increasing
#
next_letter = { 'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'F',
                'F': 'G', 'G': 'H', 'H': 'I', 'I': 'J', 'J': 'K',
                'K': 'L', 'L': 'M', 'M': 'N', 'N': 'O', 'O': 'P',
                'P': 'Q', 'Q': 'R', 'R': 'S', 'S': 'T', 'T': 'U',
                'U': 'V', 'V': 'W', 'W': 'X', 'X': 'Y', 'Y': 'Z',
                'Z': 'A' }

# to sort sessionhandling a bit
SESSIONATTRS = ['basket', 'searchTree', 'columnChooser']

# messages
NOT_AUTHORIZED = 'You are not authorized to use this function.'
NO_PERMISSION  = 'You do not have sufficient permissions for this entry.'

# alias for icon constants
PB_PIXMAPSRC = hgPushButton.PB_PIXMAPSRC
PB_PIXMAPW   = hgPushButton.PB_PIXMAPW
PB_PIXMAPH   = hgPushButton.PB_PIXMAPH
PB_PIXMAPALT = hgPushButton.PB_PIXMAPALT

SEARCH_KEYWORDS = ['NULL', '_not_', '_<_', '_>_', '_to_', '__']


class ManagerPart(CorePart, ManagerFinderMixin):
    """ ManagerPart class provides basic Form and Request Handling, Manager
        Location, Navigation and Menu Layout, Install and Uninstall methods.
    """

    implements(IZopRAManager)
#
# Class Properties
#
    _className  = 'ManagerPart'
    _classType  = CorePart._classType + [_className]
    meta_type   = ''

    # contains all dialog that will be installed with the manager
    _dlgs         = ( dlgTableEntry, dlgMultiDelete, )

    # list of image handles for the dialog
    _icons = {}

    # basket is a class variable for the context item basket
    # no members, only functions working on the session and request
    basket = Basket()

    # security switch (can be enabled by __init__)
    ebase = False
    sbar  = False

    manage_options = CorePart.manage_options + (
                        {'label': 'Overview', 'action': 'viewTab'   },
                        {'label': 'Update',   'action': 'updateTab' }, )

    #
    # Properties
    #
    _properties = CorePart._properties + (
            {'id': 'show_number',    'type': 'int',     'mode': 'w'},
            {'id': 'delete_tables',  'type': 'int',     'mode': 'w'},
            {'id': 'email_support',  'type': 'boolean', 'mode': 'w'},
            {'id': 'system_address', 'type': 'string',  'mode': 'w'},
            {'id': 'zopra_version',  'type': 'float',   'mode': 'w'},
            {'id': 'zopratype',      'type': 'string',  'mode': 'w'}, )

    #
    # Property default settings
    #

    # initial number of entries on search results page
    show_number   = 20

    # should manage_beforeDelete delete the database tables? 0/1
    delete_tables = 0

    # email handling
    # TODO: check usage of this
    email_support  = False
    system_address = 'demo@dem.de'

    # the overall uptodate version number
    # set as class variable -> comparable to instance variable of same name
    zopra_version = 1.8

    # the property for distinguishing multiple instances of one manager class
    zopratype     = ''

    #
    # Security
    #
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #
    # Icons for sort buttons for search result page
    #
    IMG_SORTDEACT = 'Field sorting deactivated'
    IMG_SORTNONE  = 'Field not sorted'
    IMG_SORTASC   = 'Field sorted ascending'
    IMG_SORTDESC  = 'Field sorted descending'

    SORTING_FILES = { IMG_SORTDEACT: 'sort_da_20.png',
                      IMG_SORTNONE:  'sort_no_20.png',
                      IMG_SORTASC:   'sort_up_20.png',
                      IMG_SORTDESC:  'sort_down_20.png' }

    #
    # Icons for page buttons for search result page
    #
    IMG_PAGEFWD         = 'Page Forward'
    IMG_PAGEBWD         = 'Page Backward'
    IMG_PAGEFIRST       = 'First Page'
    IMG_PAGELAST        = 'Last Page'
    IMG_PAGEFWD_DEACT   = 'Page Forward (inactive)'
    IMG_PAGEBWD_DEACT   = 'Page Backward (inactive)'
    IMG_PAGEFIRST_DEACT = 'First Page (inactive)'
    IMG_PAGELAST_DEACT  = 'Last Page (inactive)'

    LISTING_FILES = { IMG_PAGEFWD:         'page_fwd.png',
                      IMG_PAGEBWD:         'page_bwd.png',
                      IMG_PAGEFIRST:       'page_first.png',
                      IMG_PAGELAST:        'page_last.png',
                      IMG_PAGEFWD_DEACT:   'page_fwd_deact.png',
                      IMG_PAGEBWD_DEACT:   'page_bwd_deact.png',
                      IMG_PAGEFIRST_DEACT: 'page_first_deact.png',
                      IMG_PAGELAST_DEACT:  'page_last_deact.png' }

    #
    # Icons for entry handling buttons
    #
    IMG_CREATE = 'Create new'
    IMG_LIST   = 'List'
    IMG_SEARCH = 'Search'
    IMG_IMPORT = 'Import'
    IMG_EXPORT = 'Export'
    IMG_INFO   = 'Info'
    IMG_DBADD  = 'Add to Database'
    IMG_SHOW_NEXT = 'Show next'
    IMG_SHOW_PREV = 'Show previous'
    IMG_SHOW_NEXT_DEACT = 'Show next disabled'
    IMG_SHOW_PREV_DEACT = 'Show previous disabled'
    IMG_SHOW      = 'Show'
    IMG_EDIT      = 'Edit'

    HANDLING_FILES = { IMG_CREATE: 'ziCreate.png',
                       IMG_LIST:   'ziList.png',
                       IMG_SEARCH: 'ziSearch.png',
                       IMG_IMPORT: 'ziImport.png',
                       IMG_EXPORT: 'ziExport.png',
                       IMG_INFO:   'ziInfo.png',
                       IMG_DBADD:  'ziDBAdd.png',
                       IMG_SHOW_NEXT: 'ziNext.png',
                       IMG_SHOW_PREV: 'ziPrev.png',
                       IMG_SHOW_NEXT_DEACT: 'ziNextDeact.png',
                       IMG_SHOW_PREV_DEACT: 'ziPrevDeact.png',
                       IMG_SHOW:   'ziShow.png',
                       IMG_EDIT:   'ziEdit.png', }

    #
    # tooltips
    #
    TIP_CREATE = 'Create new %s entry.'
    TIP_LIST   = 'List all %s entries.'
    TIP_SEARCH = 'Search for %s entries.'
    TIP_IMPORT = 'Import data into the database.'
    TIP_EXPORT = 'Export data from the database.'
    TIP_INFO   = 'Get %s info.'
    TIP_DBADD  = 'Add the %s to the database.'
    TIP_SHOW_NEXT = 'Show next %s entry.'
    TIP_SHOW_PREV = 'Show previous %s entry.'
    TIP_SHOW   = 'Show %s entry details.'
    TIP_EDIT   = 'Edit %s entry.'

    TOOLTIP_DICT = { IMG_CREATE: TIP_CREATE,
                     IMG_LIST:  TIP_LIST,
                     IMG_SEARCH: TIP_SEARCH,
                     IMG_IMPORT: TIP_IMPORT,
                     IMG_EXPORT: TIP_EXPORT,
                     IMG_INFO:   TIP_INFO,
                     IMG_DBADD:  TIP_DBADD,
                     IMG_SHOW_NEXT: TIP_SHOW_NEXT,
                     IMG_SHOW_PREV: TIP_SHOW_PREV,
                     IMG_SHOW:   TIP_SHOW,
                     IMG_EDIT:   TIP_EDIT }


    security.declareProtected(managePermission, '__init__')

    def __init__( self,
                  title     = '',
                  part_id   = None,
                  nocreate  = 0,
                  zopratype = ''):
        """\brief Constructs a ManagerPart."""
        CorePart.__init__( self, title, part_id )

        self.nocreate     = nocreate
        self.zopratype    = zopratype
        self.tableHandler = None
        self.listHandler  = None
        self.dlgHandler   = None
        self.iconHandler  = None

        # basket switch
        self.basket_active = False
        # the basket itself is stored as class variable (no members -> only functions)

        # security switches
        self.ebase         = False
        self.sbar          = False

        self.zopra_version = self.__class__.zopra_version

    ###########################################################################
    #                                                                         #
    # Dummy Functions                                                         #
    #   - overwrite for special handling                                      #
    ###########################################################################

    security.declareProtected(modifyPermission, '_addTable')

    def _addTable(self):
        """ Hook method for extra table magic on add.

        Called by manage_afterAdd if table creation is enabled via DTML add
        form.
        """
        pass


    security.declareProtected(modifyPermission, '_addTable')

    def _delTable(self):
        """ Hook method for extra table magic on delete.

        Called by manage_beforeDelete if delete_tables option is set via
        properties screen
        """
        pass


    security.declareProtected(viewPermission, '_index_html')

    def _index_html(self, REQUEST, parent = None):
        """ Hook method for main window on start page.

        This function is overwritten by generic manager and should be
        overwritten again if you want a custom start page
        """
        return ''


    security.declareProtected(managePermission, 'setDebugOutput')

    def setDebugOutput(self):
        """ Hook method for manager specific debug output.

        This function is called by the management view-tab to display further
        debug output."""
        return ''


    security.declareProtected(viewPermission, 'contextMenuCustom')

    def contextMenuCustom(self, REQUEST, parent):
        """ Hook method for manager specific context menu.

        This function is called by contextMenu to display manager specific
        additional context data.
        """
        return None


    security.declareProtected(viewPermission, 'navigationMenuCustom')

    def navigationMenuCustom(self, menubar, REQUEST):
        """ Hook method for customizable part of navigation.

        Return True to indicate that something was added.
        """
        return False


    security.declareProtected(viewPermission, 'prepareEntryBeforeShowList')

    def prepareEntryBeforeShowList(self, table, dict, REQUEST):
        """ Hook method called by getTableEntryListHtml to preprocess each
            entry.

        Overwrite this function to process each single entry before it is
        displayed row-wise by getTableEntryListHtml. This can be useful to
        substitute id's with labels / links in cases where singlelists are
        not possible and the 'static' way using param[links] in
        actionBeforeShowList is not wanted.
        """
        pass


    security.declareProtected(viewPermission, 'prepareFieldForExport')

    def prepareFieldForExport(self, table, column, value, entry):
        """ Hook function called by Table.exportTab to preprocess each column
            of each entry to be exported.

        The value is already processed (translated ids into values for lists)
        and will be escaped after being returned here.

        Overwrite this function to process each single value (or replace it
        entirely) if you need special display for export. This is for example
        used to unscramble scrambled E-Mails from the database before putting
        them into the export file.
        """
        return value

    ###########################################################################
    #                                                                         #
    # Fancy error output                                                      #
    #                                                                         #
    ###########################################################################

    security.declareProtected(viewPermission, 'renderError')

    def renderError(self, msg, topic = None):
        """\brief Creates a simple structured error msg widget"""

        if not isinstance(msg, StringType):
            self.displayError('Expected string type.', 'Value Error.')

        r = 0
        error = hgTable()
        if topic:
            if not isinstance(topic, StringType):
                self.displayError('Expected string type.', 'Value Error.')
            error._styleSheet.add(ssiDLG_LABEL_HL)
            errorlab = hgLabel('Error: %s' % topic)
            errorlab.setSsiName( ssiDLG_LABEL_HL.name() )
            error[0, 0] = errorlab
            r += 2
        error[r, 0] = hgLabel(msg)

        return error


    security.declareProtected(viewPermission, 'displayError')

    def displayError(self, msg, topic = None):
        """\brief Creates a simple structured error msg widget"""
        error = self.renderError(msg, topic)
        raise ValueError(self.getErrorDialog(error))

    ###########################################################################
    #                                                                         #
    # SimpleItem create / copy / delete hooks (deprecated but still in use)   #
    #                                                                         #
    ###########################################################################


    security.declareProtected(managePermission, 'manage_afterAdd')

    def manage_afterAdd(self, item, container):
        """ Manage the normal manage_afterAdd method of a SimpleItem.

        1. The Method looks for an existing instance of an Product Manager. If
           there is no Product Manager the function will raise a
           <code>Programming Error</code>.
        <br>
        2. All forms defined in _dtml_dict will be installed.
        <br>
        3. All tables defined in the manager xml
           (present in the xmltransporter, put there on init) will be created.
        <br>
        4. All manager lists defined in the manager xml will be created.
        <br>
        5. If all went good the Manager will register himself at the Product
           Manager.
        """

        m_product = self.getManager(ZC.ZM_PM)

        # copy hack to avoid errors on copy/paste
        if not m_product:
            self.nocreate = 1

        # on copy, the tableHandler is there already
        if not hasattr(self, 'tableHandler') or not self.tableHandler:

            # create table Handler
            tableHandler = TableHandler()
            table_def    = getTableDefinition(self)

            # store it as subfolder
            self._setObject('tableHandler', tableHandler)

            # create list Handler
            listHandler  = ListHandler()

            # store it as subfolder
            self._setObject('listHandler', listHandler)

            # initialize tables
            self.tableHandler.xmlInit( table_def, self.nocreate )

            # initialize lists
            self.listHandler.xmlInit( table_def, self.nocreate )

            # edit tracking lists
            self.createEditTrackingLists()

        # more manager specific _addTables
        if not self.nocreate:
            self._addTable()

        # register manager as child at product manager
        if IZopRAProduct.providedBy(self) and m_product:
            m_product.registerChild(self)

        # install Icons (all available will be installed, the mapped will have properties)
        self.manage_installIcons()

        # install dialogs (dialogHandler and containers for each dlg)
        self.manage_installDialogs()


    security.declareProtected(managePermission, 'manage_beforeDelete')

    def manage_beforeDelete(self, item, container):
        """\brief Clean up before deletion.
        """
        m_product = self.getManager(ZC.ZM_PM)

        # delete the manager owned tables from the database
        if self.delete_tables:
            self._delTable()

            # delete tables
            for table in self.tableHandler.getTableIDs():
                try:
                    self.tableHandler.delTable(table)
                except:
                    # something went wrong (e.g. new table), ignore
                    pass

            # delete list references (multi and hierarchylists get their db tables deleted)
            for (table, column) in self.listHandler.references():
                try:
                    self.listHandler.disconnectList(table, column, True)
                except:
                    pass

            # delete lists
            for entry in self.listHandler.keys():
                try:
                    self.listHandler.delList(entry, True)
                except:
                    pass

        # fi delete_tables

        # remove child manager
        m_product.removeChild(self)

    ###########################################################################
    #                                                                         #
    # Helper Methods for the manage functions                                 #
    #                                                                         #
    ###########################################################################


    security.declareProtected(managePermission, 'manage_installIcons')

    def manage_installIcons(self):
        """\brief This method will be called in manage_afterAdd to install the
                  icon relevant stuff.
        """

        # init the icon handler

        # icon handler has to be reinstalled
        if hasattr(self, 'iconHandler') and self.iconHandler:
            # remove the damn thing
            self.manage_delObjects(['iconHandler'])

        namespace = self.__module__
        namespace = namespace[:namespace.rfind('.')]

        # setup new icon handler
        iconHandler      = IconHandler('iconHandler', namespace)
        self._setObject( 'iconHandler', iconHandler )
        # to stop pylint from crying
        self.iconHandler = iconHandler

        # load global sorting images
        # TODO: make "default" attribute-dependent to be able to set other themes
        path = os.path.join(getZopRAPath(), 'images')

        if os.path.exists(path):
            icons = {}
            files = []

            for zmom_files in [ self.SORTING_FILES, self.LISTING_FILES, self.HANDLING_FILES ]:
                for title in zmom_files.keys():
                    filename = zmom_files[title]
                    icons[filename] = title
                    files.append(filename)

            for name in os.listdir(path):
                filename = os.path.join(path, name)
                if not os.path.isdir(filename):
                    fHandle = open(filename, 'r')

                    if name in files:
                        title = icons[name]
                        # prefix filename to prevent collisions with more specific files
                        # TODO: find a safe way
                        name  = 'ZMOM_' + name
                        image = Image(name, title, fHandle.read())
                    else:
                        image = Image(name, '', fHandle.read())

                    iconHandler._setObject(name, image)

        # load local images from managers images directory
        if namespace != 'zopra.core':

            # re-import class to get the file location
            module = import_module(self.__module__, self.getClassName())
            path   = module.__file__

            # remove the filename from the path and add the image path location
            path = os.path.join(os.path.split(path)[0], 'images')

            if os.path.exists(path):

                for name in os.listdir(path):
                    filename = os.path.join(path, name)
                    if not os.path.isdir(filename):
                        fHandle = open(filename, 'r')
                        image   = Image(name, '', fHandle.read())

                        iconHandler._setObject(name, image)

        # map icon properties to loaded images
        self.iconHandler.xmlInit( getIconsDefinition(self) )


    security.declareProtected(managePermission, 'manage_installDialogs')

    def manage_installDialogs(self):
        """\brief This method will be called in manage_afterAdd to install the
                  dialog relevant stuff.

        First the dialogs will be installed in the dialog Handler. Then the
        parameters for the dialogs will be set.
        """
        # delete existing dialog handler
        # icon handler has to be reinstalled
        if hasattr(self, 'dlgHandler') and self.dlgHandler:
            # remove the damn thing
            self.manage_delObjects(['dlgHandler'])

        # dialog handler has to be installed
        dlgHandler      = DialogHandler('dlgHandler')
        self._setObject( 'dlgHandler', dlgHandler )

        # to stop pylint from crying
        self.dlgHandler = dlgHandler

        for entry in self._dlgs:
            if isinstance(entry, type(())):
                continue

            if not hasattr(self.dlgHandler, entry.__name__):
                self.dlgHandler.installDialog(entry)

                # set default parameters
                if hasattr( self, entry.__name__ + '_params' ):
                    params = getattr( self, entry.__name__ + '_params' )
                    if params:
                        container = self.dlgHandler.getDialogContainer(entry.__name__)
                        for param in params:
                            try:
                                container._setProperty( param[0], param[1] )
                            except:
                                warning  = '[Warning] manage_installDialogs(): '
                                warning  = ' Duplicate or bad id - %s' % param[0]
                                print warning


    security.declareProtected(managePermission, 'createEditTrackingLists')

    def createEditTrackingLists(self):
        """\brief Create List objects for creator, editor and owner"""
        lobj = self.listHandler

        # all lists are singlelists pointing to table 'person' in ContactManager
        list_def = Column(None, 'singlelist')
        list_def.setManager('ContactManager')
        list_def.setFunction('person()')
        labels = {'creator': 'Creator',
                  'editor':  'Editor',
                  'owner':   'Owner'}

        # set up foreign lists if missing
        for listname in labels.keys():

            # bind cols for each table
            list_def.setName(listname)
            list_def.setLabel(labels[listname])
            # edittrackers are invisible (except creator)
            if listname != 'creator':
                list_def.setInvisible('1')

            for table in self.tableHandler.getTableIDs():
                # but check whether it exists before (some managers still overwrite those lists :/)
                # TODO: remove creator from tabledef of all managers, it is implicit
                # (but for generic masks they have to be defined extra to show up)
                if not lobj.hasList(table, listname):
                    lobj.connectList( self, table, list_def)

    ###########################################################################
    #                                                                         #
    # Basic Helper Functions                                                  #
    #                                                                         #
    ###########################################################################

    security.declareProtected(modifyPermission, 'deleteEntries')

    def deleteEntries( self,
                       table,
                       idlist,
                       REQUEST = None ):
        """ Basic function, forwards deletion request to Table object named
            table.

        This function is called by all deletion methods and dialogs (single / multi)
        and gets overwritten by GenericManager to add a deletion hook which
        has to be used for custom deletion handling.
        @see GenericManager.prepareDelete()
        """
        if table not in self.tableHandler.keys():
            return

        if not idlist:
            return

        if not isinstance(idlist, ListType):
            idlist = [idlist]

        self.tableHandler[table].deleteEntries(idlist)


    security.declareProtected(viewPermission, 'getZopraType')

    def getZopraType(self):
        """ Returns the internal type of the manager (to have different handling
            for same managers with different type).
        """
        return self.zopratype


    # table node creation

    security.declareProtected(viewPermission, 'generateTableSearchTreeTemplate')

    def generateTableSearchTreeTemplate(self, table):
        """\brief Basic Function for search template generation.
                This function can be overwritten to produce complex search trees,
                default returns only main node of given table
                and tries to guess the table, if None is given."""
        if not table:
            tables = self.tableHandler.keys()
            if len(tables) == 1:
                table = tables[0]
            else:
                raise ValueError('No single table found to use for search')
        return self.tableHandler[table].getTableNode()


    security.declareProtected(viewPermission, 'getListSelectionConstraints')

    def getListSelectionConstraints(self, listname, lang = 'de'):
        """\brief Basic Function for List Selection Constraining.
                This function can be overwritten to constrain foreign table based lists
                based on their name by returning a constraints dictionary that will be
                used by the entry gathering mechanisms of the list objects.
        """
        return {}


    security.declareProtected(viewPermission, 'checkDefaultWildcardSearch')

    def checkDefaultWildcardSearch(self, table):
        """\brief Toggle for Wildcard Search. Overwrite this function and return True
                for the tables that will then automatically use wildcard search for all text
                fields.
        """
        return False


    security.declareProtected(viewPermission, 'forwardCheckType')

    def forwardCheckType(self, value, column_type, operator = False, label = None, do_replace = True):
        """\brief forward the type check call to the next ZopRAProduct"""
        m_prod = self.getManager(ZC.ZM_PM)
        # m_prod could be self, but doesnt matter
        return m_prod.checkType(value, column_type, operator, label, do_replace)


    # Button and REQUEST handling
    security.declareProtected(viewPermission, 'getTableEntryFromRequest')

    def getTableEntryFromRequest(self, table, REQUEST, prefix = '', search = False):
        """\brief Builds a \c descr_dict from an REQUEST object.

        The function tries to filter all key,
        value pairs where a key matches
        with a column name of the specified table
        (maybe prefixed with DLG_CUSTOM and the given prefix).
        It also looks for special keys (ANDconcat for multi search / filter)

        \param table  The argument \a table is a string with the table name
               without id prefix.

        \param REQUEST  The argument \a REQUEST is a REQUEST object that
               contains the key, value pairs of the fields from the html form.

        \param prefix The argument \a prefix is a string that makes
               the function only filter keys that
        start with DLG_CUSTOM+prefix, the results are unprefixed however

        \param search indicates whether AND-concatenation should be checked for
               multi and hierarchy lists.

        \return The function will return a description dictionary with the
                found key - value pairs
        """
        # TODO: the parts commented as "widget check" should be moved to an extra function
        # to have only content handling here and config handling somewhere else
        descr_dict = {}
        pre        = ''
        if prefix:
            pre = DLG_CUSTOM + prefix

        tobj = self.tableHandler[table]

        # wildcard search check
        do_wilds = search and self.checkDefaultWildcardSearch(table)
        typedefs = do_wilds and tobj.getColumnTypes()

        # handling without a session object
        for name in tobj.getMainColumnNames():

            if pre + name in REQUEST:
                value = REQUEST[pre + name]

                if isinstance(value, ListType) and value:
                    # this is unnecessary for main columns, they should only
                    # appear once but this check is needed for bool searches
                    # (true-checkbox / false-checkbox)
                    value = value[0]

                # wildcard search
                if value and do_wilds and typedefs[name] in [ZC.ZCOL_STRING, ZC.ZCOL_MEMO, ZC.ZCOL_DATE]:
                    wcs = True
                    for skw in SEARCH_KEYWORDS:
                        if value.find(skw) != -1:
                            wcs = False
                    # wrap with '*', unless it's been already wrapped;
                    # prevents cases like ******x******
                    if wcs and not (value[0] == value[-1] == '*'):
                        value = '*%s*' % value
                descr_dict[name] = value

        # get all lists
        tablelists = self.listHandler.getLists(table)

        for listobj in tablelists:
            name = listobj.listname
            pre_name = pre + name

            entry = REQUEST.get(pre_name)

            if listobj.listtype in ['multilist',  'hierarchylist']:
                if entry:
                    # the entry has to be a list
                    if not isinstance( entry, ListType  ) and \
                       not isinstance( entry, TupleType ):
                        entry = [entry]

                    # we take the note-entries from the REQUEST as well
                    pre_name_notes = pre_name + 'notes'
                    name_notes     = name     + 'notes'
                    new_entry = []
                    for item in entry:
                        if item and item != 'NULL':
                            try:
                                new_entry.append(int(item))
                            except ValueError:
                                if search:
                                    # other values are allowed for search
                                    new_entry.append(item)
                                else:
                                    # the value was nonsense, do not use it
                                    continue
                            # only set notes if enabled
                            if listobj.notes:
                                key = pre_name_notes + str(item)
                                if REQUEST.get(key):
                                    key1 = name_notes + str(item)
                                    descr_dict[key1] = REQUEST.get(key, '')
                    entry = new_entry
                else:
                    # this should lead to correct empty multilists on edit
                    entry = []

                if search:
                    # widget check
                    # check AND/OR concatenation for search
                    if REQUEST.get(pre_name + '_AND') is True or REQUEST.get(pre_name + '_AND') == 'True' or REQUEST.get(pre_name + '_AND') == '1':
                        descr_dict[name + '_AND'] = True
                    else:
                        descr_dict[name + '_AND'] = False

            # handling for all lists ... but single were handled before already?
            # FIXME: could be moved one level right into the if-statement
            if pre_name in REQUEST:
                descr_dict[listobj.listname] = entry

            # widget check
            # check filter setting stored as property
            if 'store_' + FILTER_EDIT + pre_name in REQUEST:
                filtertext = REQUEST['store_' + FILTER_EDIT + pre_name]
                if filtertext and filtertext != FCB_DEFAULT_FILTER_TEXT:
                    if not isinstance(filtertext, StringType):
                        filtertext = str(filtertext)
                    wcname = ZC.WIDGET_CONFIG + name
                    if wcname not in descr_dict:
                        descr_dict[wcname] = {}
                    descr_dict[wcname]['pattern'] = filtertext

            # widget check
            # check startitem (for range lists displaying only some entries)
            if 'frl_startitem' + pre_name in REQUEST:
                startitem = REQUEST['frl_startitem' + pre_name]
                startitem = int(startitem)

                wcname = ZC.WIDGET_CONFIG + name
                if wcname not in descr_dict:
                    descr_dict[wcname] = {}
                descr_dict[wcname]['offset'] = startitem

        return descr_dict


    security.declareProtected(viewPermission, 'quoteConstraints')

    def quoteConstraints(self, constraints):
        """ Converts dictionary into URL-usable parameter string"""
        params = ''
        for key in constraints:
            if key == 'autoid':
                continue
            val = constraints[key]
            if isinstance(val, ListType):
                for oneval in val:
                    params += '%s=%s&' % (key, oneval)
            else:
                params += '%s=%s&' % (key, val)
        return params


    security.declareProtected(viewPermission, 'getPressedButton')

    def getPressedButton(self, REQUEST = None, buttonType = DLG_FUNCTION):
        """\brief Wrapper for getPressedButton from Buttons.py"""
        buttons = getPressedButton(REQUEST, buttonType)
        if buttons:
            # erase double entries
            buttons = dict([(b, None) for b in buttons]).keys()
            if len(buttons) > 1:
                return self.getErrorDialog('More then one button pressed. %s' % buttons)
            return buttons[0]

    security.declareProtected(viewPermission, 'getValueListFromRequest')

    def getValueListFromRequest(self, REQUEST, field):
        """ Filters multiple IDs out of the REQUEST Handler.

        @return [<values>] list with values; otherwise None.
        """
        if not hasattr(REQUEST, field):
            return []

        values = REQUEST[field]
        if not isinstance(values, ListType):
            values = [values]
        return values

    ###########################################################################
    #                                                                         #
    # Additional Utility functions                                            #
    #                                                                         #
    ###########################################################################

    # mail handling
    security.declareProtected(modifyPermission, 'sendSimpleMail')

    def sendSimpleMail(self, mto, mfrom, subject, body):
        """\brief Tries to send a email via the next available host."""
        mailHost = self.getObjByMetaType('Mail Host')
        if mailHost:
            try:
                mailHost.simple_send(mto, mfrom, subject, body)
                return True
            except Exception, exc:
                msg = 'E-Mail Error: Could not send email %s from %s to %s: Error %s'
                msg = msg % (subject, mfrom, mto, str(exc))
                self.getManager(ZC.ZM_PM).writeLog(msg)
        else:
            msg = 'E-Mail Error: Could not send email %s from %s to %s: No Mailhost found.'
            msg = msg % (subject, mfrom, mto)
            self.getManager(ZC.ZM_PM).writeLog(msg)

        return False

    def sendSecureMail(self, mto, mfrom, subject="", message="", mcc=None, mbcc=None, charset="utf-8"):
        """\brief Tries to send a email via the next available secure mail host."""
        mailHost = self.getObjByMetaType('Secure Mail Host')
        if mailHost:
            try:
                mailHost.secureSend(message=message, mto=mto, mfrom=mfrom, subject=subject, mcc=mcc, mbcc=mbcc, charset=charset)
                return True
            except Exception, exc:
                msg = 'E-Mail Error: Could not send email %s from %s to %s: Error %s'
                msg = msg % (subject, mfrom, mto, str(exc))
                self.getManager(ZC.ZM_PM).writeLog(msg)
        else:
            msg = 'E-Mail Error: Could not send email %s from %s to %s: No Mailhost found.'
            msg = msg % (subject, mfrom, mto)
            self.getManager(ZC.ZM_PM).writeLog(msg)

        return False

    def prepare_zopra_currency_value(self, value):
        """ Format a currency value according to german standard or return as is
           (for edit validation / search validation)
        """
        if value is None:
            return ''

        try:
            res = ('%.2f' % float(str(value).replace(',', '.'))).replace('.', ',')
        except:
            res = str(value)

        return res

    ###########################################################################
    #                                                                         #
    # Manager retrieval helper functions                                      #
    #                                                                         #
    ###########################################################################

    security.declarePrivate('getManagerDownLoop')
    security.declarePrivate('getAllManagersDownLoop')

    security.declareProtected(viewPermission, 'getHierarchyUpManager')
    security.declareProtected(viewPermission, 'getHierarchyDownManager')
    security.declareProtected(viewPermission, 'getAllManagersHierarchyDown')
    security.declareProtected(viewPermission, 'getAllManagers')
    security.declareProtected(viewPermission, 'topLevelProduct')

    ###########################################################################
    #                                                                         #
    # Security Functions                                                      #
    #   - EBaSe, SBAR, general permissions (entry / gui), forms               #
    ###########################################################################

    #
    # EBaSe functions
    #

    security.declareProtected(managePermission, 'activateEBaSe')

    def activateEBaSe(self):
        """\brief activate Entry Based Security"""
        self.ebase = True


    security.declareProtected(viewPermission, 'checkEBaSe')

    def checkEBaSe(self, table):
        """\brief check activated Entry Based Security for table
        If manager ebase switch is true and the one from the table then return True.
        """
        return self.ebase and self.tableHandler[table].ebase


    security.declareProtected(managePermission, 'initEBaSe')

    def initEBaSe(self, table):
        """\brief update show-ebase of all entries of table to match creators ebase-groups.
                  Activate Ebase at all."""
        self.ebase = True
        if not self.checkEBaSe(table):
            return self.getErrorDialog('EBaSe not enabled.')

        m_security = self.getHierarchyUpManager(ZC.ZM_SCM)
        users      = {}
        all_group  = m_security.tableHandler['ebasegroup'].getEntryAutoid('All', 'name')
        tobj       = self.tableHandler[table]
        entries    = tobj.getEntries()
        # TODO: create umask

        # TODO: apply umask

        # key = '%s_ebase_show' % table
        count = 0
        # for entry in entries:
        #    creatorid = entry.get(TCN_CREATOR)
        #    if users.has_key(creatorid):
        #        user = users.get(creatorid)
        #    else:
        #        user = m_security.getUserByCMId(creatorid)
        #        users[creatorid] = user
        #    if not user:
        #        # creator has no login, show to all
        #        egroups = [all_group]
        #    else:
        #        egroups = user.get('ebasegroups')
        #        if not egroups:
        #            # forgot to update the user
        #            egroups = [all_group]
        #    ddict = {key:egroups}
        #    tobj.updateEntry(ddict, entry[TCN_AUTOID])
        #    count += 1
        return self.getErrorDialog('%s: %s entries updated.' % (table, count))


#
# SBAR functions
#

    security.declareProtected(managePermission, 'activateSBAR')

    def activateSBAR(self):
        """ Activates the scope based access restrictions. """
        self.sbar = True


    security.declareProtected(viewPermission, 'checkSBAR')

    def checkSBAR(self):
        """ Returns whether the scope based access restrictions are enabled for a manager or not.

        @return boolean - True if the scope based access restrictions are enabled; otherwise False.
        """
        if not hasattr(self, 'sbar'):
            self.sbar = False
        return self.sbar


#
# permission check functions
#

    security.declareProtected(viewPermission, 'getGUIPermission')

    def getGUIPermission(self):
        """\brief"""
        obj     = None
        session = None

        # get session
        request = self.REQUEST

        if request and hasattr(request, 'SESSION'):
            session = request.SESSION
            # test session
            obj = session.get('GUIPermission')

        if obj:
            # TODO: test object correctness
            return obj
        else:
            # call creation function
            obj = self._createGUIPermission()
            if session:
                session['GUIPermission'] = obj
            return obj


    security.declareProtected(viewPermission, 'destroyGUIPermission')

    def destroyGUIPermission(self):
        """\brief"""
        # get session
        session = self.REQUEST.SESSION

        # test session
        session['GUIPermission'] = None
        return True


    security.declarePrivate('_createGUIPermission')

    def _createGUIPermission(self):
        """ Returns a new created GUIPermission object. """
        # try to get security manager
        m_sec = self.getHierarchyUpManager(ZC.ZM_SCM)
        if m_sec:

            # get login
            login = m_sec.getCurrentLogin()

            # get global roles
            groles = m_sec.getGlobalRoles()

            # get access roles
            aroles = m_sec.getAccessRoles()

            # get access roles active managers
            active = m_sec.getAccessEnabledMgrs()

        else:

            # get login
            login = getSecurityManager().getUser()

            # no security manager -> everyone is admin
            groles = ['Admin']
            aroles = LevelCache(2, [100, 100], nonpersistent = True)
            active = {}

        # create object
        return GUIPermission(login, groles, active, aroles)


    security.declareProtected(viewPermission, 'hasGUIPermission')

    def hasGUIPermission(self, table, permission_request):
        """\brief Checks permission for table."""
        if table not in self.tableHandler:
            title = self.getTitle()
            self.displayError('Table \'%s\' does not exist in %s' % (table, title),
                              'Internal Error.')

        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        return bool(perm.hasPermission(permission_request, tabid, ztype))


    security.declareProtected(viewPermission, 'checkGUIPermission')

    def checkGUIPermission(self, table, permission_request):
        """\brief Checks permission for table."""

        if not self.hasGUIPermission(table, permission_request):
            return self.unauthorizedHtml(permission_request)


    security.declareProtected(viewPermission, 'isSuperUser')

    def isSuperUser(self, tabid = None, anytab = False):
        """\brief Checks if the actual user is a superuser for table with tabid (or general if no tabid given)"""
        # check permissions
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        suser = False
        if not tabid and anytab:
            for tab in self.tableHandler.getTableIDs():
                tabid = self.tableHandler[tab].getUId()
                suser = suser or perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        else:
            # general role check
            suser = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        return suser or perm.hasSpecialRole(ztype + 'Superuser')


    security.declareProtected(viewPermission, 'hasEntryPermission')

    def hasEntryPermission(self,
                           table,
                           autoid             = None,
                           descr_dict         = None,
                           permission_request = 0):
        """\brief Return label for entry, overwrite for special functionality."""
        if autoid:
            descr_dict = self.tableHandler[table].getEntry(autoid)

        if not descr_dict:
            return False

        if 'permission' in descr_dict:
            tobj = descr_dict['permission']
            return tobj.isOwner() or tobj.hasPermission(permission_request)

        return True


    security.declareProtected(viewPermission, 'getEntryPermissions')

    def getEntryPermissions(self, acl, table):
        # function that collects permissions for an acl
        # get security manager
        m_sec = self.getHierarchyUpManager(ZC.ZM_SCM)
        if m_sec:
            # get GUIPermission object
            perm = self.getGUIPermission()

            # check ebase
            if self.checkEBaSe(table):

                # admin sees all? what about superuser?
                if perm.hasRole(perm.SC_ADMIN):
                    perms = ZC.SC_L_ALL

                else:
                    # get permissions
                    perms = m_sec.getCurrentEBaSePermission(acl)

            else:
                # no ebase, use gui permission object to get permissions
                perms = []
                if perm.hasPermission(perm.SC_VIEW):
                    perms.append(ZC.SC_READ)
                    perms.append(ZC.SC_LREAD)

                if perm.hasMinimumRole(perm.SC_SUPER):
                    perms.append(ZC.SC_DEL)
                    perms.append(ZC.SC_WRITE)

        else:
            # everyone does everything
            perms = ZC.SC_L_ALL

        return perms


    #
    # unauthorized forms
    #

    security.declareProtected(viewPermission, 'unauthorizedHtml')

    def unauthorizedHtml(self, permission, html = True):
        """ Return dialog with unauthorized message (for an application part).
        """
        # TODO: use permission to differentiate messages
        dlg = getStdDialog('Error')
        dlg.add(hgNEWLINE)
        dlg.add('<center>')
        dlg.add( NOT_AUTHORIZED )
        dlg.add('</center>')
        dlg.add(hgNEWLINE)
        dlg.add(self.getBackButtonStr())
        return HTML( dlg.getHtml() )(self, None) if html else dlg


    security.declareProtected(viewPermission, 'nopermissionHtml')

    def nopermissionHtml(self, permission, html = True):
        """ Return dialog with permission message (for an entry).
        """
        # TODO: use permission to differentiate messages
        dlg = getStdDialog('Error')
        dlg.add(hgNEWLINE)
        dlg.add('<center>')
        dlg.add(NO_PERMISSION)
        dlg.add('</center>')
        dlg.add(hgNEWLINE)
        dlg.add(self.getBackButtonStr())
        return HTML( dlg.getHtml() )(self, None) if html else dlg

    ###########################################################################
    #                                                                         #
    # Management Tab Views                                                    #
    #                                                                         #
    ###########################################################################

    security.declareProtected(managePermission, 'viewTab')

    def viewTab(self, REQUEST = None):
        """\brief Returns the HTML source for the view form."""
        perm = self.getGUIPermission()
        dlg = getStdDialog('Debug Output', '%s/viewTab' % self.absolute_url())
        dlg.setHeader('<dtml-var manage_page_header><dtml-var manage_tabs>')
        dlg.setFooter('<dtml-var manage_page_footer>')

        if perm.hasRole(perm.SC_ADMIN):
            dlg.add(self.getDebugOutput(REQUEST))
        else:
            dlg.add(hgLabel('<b>Access denied</b>'))
        return HTML(dlg.getHtml())(self, REQUEST)


    security.declareProtected(managePermission, 'updateTab')

    def updateTab(self, REQUEST = None):
        """\brief Returns the html source for the view form."""
        perm = self.getGUIPermission()
        if perm.hasRole(perm.SC_ADMIN):
            dlg = getStdDialog('Update Version', '%s/updateTab' % self.absolute_url())
            dlg.setHeader('<dtml-var manage_page_header><dtml-var manage_tabs>')
            dlg.setFooter('<dtml-var manage_page_footer>')

            #
            dlg.add(hgLabel('<br/>'))

            # update handling
            if REQUEST is not None:
                if REQUEST.form.get('update'):
                    report = self.updateVersion()

                    dlg.add(hgLabel('<b>Update Report</b>'))
                    dlg.add(hgLabel('<br/>'))
                    dlg.add(str(report))
                    dlg.add(hgLabel('<br/>'))
                    dlg.add(hgLabel('<br/>'))

            version = self.zopra_version
            newver  = ManagerPart.zopra_version

            tab = hgTable()

            tab[0, 0] = hgLabel('<b>Current Manager Version:<b>')
            tab[0, 1] = hgLabel(str(version))
            tab[1, 0] = hgLabel('<b>Installed Version:<b>')
            tab[1, 1] = hgLabel(str(newver))

            dlg.add(tab)

            if newver > version:
                dlg.add( hgPushButton('Update', name = 'update') )
            else:
                dlg.add(hgLabel('No update required'))

            return HTML(dlg.getHtml())(self, REQUEST)
        else:
            self.displayError('Insufficient privileges to access this function', 'Access Denied')


    security.declareProtected(managePermission, 'getDebugOutput')

    def getDebugOutput(self, REQUEST):
        """\brief Returns the HTML source of the debug output view."""
        html = []

        additional = self.setDebugOutput()
        if additional:
            html.append( '<h2>Manager specific Debug Output</h2>' + str(hgNEWLINE) )
            html.append( additional )
            html.append( str(hgNEWLINE) )

        html.append(str(dlgLabel('<h2> Debug Output </h2>') + hgNEWLINE))

        # security
        tab = hgTable()
        html.append(str(dlgLabel('<br>Security Settings')))
        tab[0, 0] = hgLabel('EBaSe:')
        tab[0, 1] = hgLabel(str(self.ebase))
        tab[1, 0] = hgLabel('SBAR:')
        tab[1, 1] = hgLabel(str(self.checkSBAR()))
        html.append(str(tab))

        tab = hgTable()

        # show tables information
        tab[0, 0] = dlgLabel('<h3>Table Overview</h3>')

        tab[1, 0] = dlgLabel('Table Name')
        tab[1, 1] = dlgLabel('Column Name')
        tab[1, 2] = dlgLabel('Column Type')
        tab[1, 3] = dlgLabel('Column Label')

        row = 2
        for table in self.tableHandler.keys():
            tab[row, 0] = dlgLabel('<b>%s</b>' % table)
            offset  = 1
            for col in self.tableHandler[table].getMainColumnNames():
                tab[row + offset, 1] = col
                colobj = self.tableHandler[table].getField(col)
                tab[row + offset, 2] = colobj.get(ZC.COL_TYPE)
                tab[row + offset, 3] = colobj.get(ZC.COL_LABEL, col)
                offset += 1
            row += offset
        row += 1

        # show _list information
        if len(self.listHandler.keys()) > 0:
            # NOTE: right now only true _list that are present with db object
            #       are displayed this way
            #       foreign lists referencing those lists or lists in other managers
            #       are omitted right now
            tab[row, 0] = dlgLabel('<h3>List (Basic Lists with dbtable) Overview</h3>')
            row += 1
            tab[row, 0] = dlgLabel('List Name')
            tab[row, 1] = dlgLabel('Value Count')
            row += 1
            for list_entry in self.listHandler.keys():
                tab[row, 0] = '<b>' + list_entry + '</b>'
                try:
                    cnt = self.listHandler[list_entry].getValueCount()
                    tab[row, 1] = cnt
                except:
                    pass
                row += 1
            row += 1
        row += 1

        # show foreign _list information
        tab[row, 0] = dlgLabel('<h3>List References Overview</h3>')
        row += 2
        tab[row, 0] = dlgLabel('Table Name')
        tab[row, 1] = dlgLabel('Column Name')
        tab[row, 2] = dlgLabel('Column Label')
        tab[row, 3] = dlgLabel('List Type')
        tab[row, 4] = dlgLabel('Referenced Manager')
        tab[row, 5] = dlgLabel('List Function')
        tab[row, 6] = dlgLabel('Foreign List')
        row += 1

        for table in self.tableHandler.keys():
            tablelists = self.listHandler.getLists(table)

            for _list in tablelists:
                tab[row, 0] = dlgLabel('<b>%s</b>' % table)
                tab[row, 1] = dlgLabel(_list.listname)
                tab[row, 2] = dlgLabel(_list.getLabel())
                tab[row, 3] = dlgLabel(_list.listtype)
                try:
                    tab[row, 4] = dlgLabel(_list.getResponsibleManagerId())
                except:
                    tab[row, 4] = dlgLabel('<font color="red">not found</font>')
                tab[row, 5] = dlgLabel(_list.function)
                tab[row, 6] = dlgLabel(_list.foreign)
                row += 1

        html.append( str(tab) )

        return '\n'.join(html)

    ###########################################################################
    #                                                                         #
    # Table Dialogs (simple HTML forms, no real dialogs yet                   #
    #   - new, show, edit, search, _list with helper functions                #
    ###########################################################################

    security.declareProtected(modifyPermission, 'getTableEntryNewDialog')

    def getTableEntryNewDialog( self,
                                title,
                                mask,
                                action  = '',
                                refresh = True,
                                REQUEST = None,
                                reset   = 'client',
                                basket  = False,
                                closeIsClose = False ):
        """\brief returns the standard Html Dialog for new entries."""
        if action and (len(action) < 4 or not action[:4] == 'http'):
            action = '%s/%s' % (self.absolute_url(), action)

        dlg  = getStdDialog(title, action)

        dlg.add('<center>')

        if refresh:
            dlg.add( mpfRefreshButton )
            dlg.add( hgLabel(hgSPACE) )

        dlg.add( mpfAddButton     )
        dlg.add( hgLabel(hgSPACE) )

        if reset == 'client':
            mpfResetButton.isLocal = True
            mpfResetButton._valid  = False
        else:
            mpfResetButton.isLocal = False
            mpfResetButton._valid  = False

        dlg.add( mpfResetButton   )
        dlg.add( hgLabel(hgSPACE) )

        if basket:
            dlg.add( mpfBasketPopButton )
            dlg.add( hgLabel(hgSPACE) )

        if closeIsClose:
            dlg.add(str(mpfCloseButton))
        else:
            dlg.add( self.getBackButtonStr(REQUEST, False) )

        dlg.add( hgLabel(hgNEWLINE) )

        dlg.add( mask )

        dlg.add( hgLabel(hgNEWLINE) )

        # TODO: why is this here? Mixed in GenericManager handling (getLink)
        # TODO: the guessing and attribute fetching is horrible anyway, refactor
        # a message if we have recently added something
        if REQUEST.get('zopra_message'):
            if isinstance(REQUEST.get('zopra_message'), StringType):
                message = REQUEST.get('zopra_message')
            else:
                message  = 'Your values have been added to the DB'
                table  = REQUEST.get('zopra_message_table', None)
                autoid = 0
                try:
                    autoid = int(REQUEST.get('zopra_message_id', 0))
                except:
                    pass
                if not isinstance(table, StringType):
                    table = None
                if table and autoid:
                    message += ': ' + self.getLink(table, autoid).getHtml() + ' '
                else:
                    message += '. '
                message += 'You can now add more.'
            dlg.add( dlgLabel(message, parent = dlg) )
            dlg.add( hgLabel(hgNEWLINE) )
            dlg.add( hgLabel(hgNEWLINE) )

        # for external information
        if refresh:
            dlg.add( str(mpfRefreshButton) )
            dlg.add( hgLabel(hgSPACE)           )

        dlg.add( str(mpfAddButton)   )
        dlg.add( hgLabel(hgSPACE)         )

        dlg.add( str(mpfResetButton) )
        dlg.add( hgLabel(hgSPACE)         )

        if basket:
            dlg.add( str(mpfBasketPopButton) )
            dlg.add( hgLabel(hgSPACE)        )

        if closeIsClose:
            dlg.add(str(mpfCloseButton))
        else:
            dlg.add(self.getBackButtonStr(REQUEST))

        dlg.add('</center>')

        return HTML( dlg.getHtml() )(self, None)


    security.declareProtected(modifyPermission, 'getTableEntryEditDialog')

    def getTableEntryEditDialog( self,
                                 title,
                                 mask,
                                 action    = '',
                                 refresh   = True,
                                 REQUEST   = None,
                                 reset     = 'client',
                                 table     = None,
                                 isGeneric = False,  # obsolete
                                 closeIsClose = False):
        """\brief Returns the standard Html Dialog for editing."""
        if action and (len(action) < 4 or not action[:4] == 'http'):
            action = '%s/%s' % (self.absolute_url(), action)

        dlg  = getStdDialog(title, action)

        dlg.add('<center>')

        if refresh:
            dlg.add(mpfRefreshButton)
            dlg.add(hgLabel(hgSPACE))

        dlg.add(mpfUpdateButton)
        dlg.add(hgLabel(hgSPACE))

        if reset == 'client':
            mpfResetButton.isLocal = True
            mpfResetButton._valid  = False

        else:
            mpfResetButton.isLocal = False
            mpfResetButton._valid  = False

        dlg.add(mpfResetButton)
        dlg.add(hgLabel(hgSPACE))

        if closeIsClose:
            dlg.add(str(mpfCloseButton))
        else:
            dlg.add(self.getBackButtonStr(REQUEST, False))
        dlg.add(hgLabel(hgNEWLINE))

        dlg.add( mask )

        dlg.add(hgLabel(hgNEWLINE))

        # TODO: why is this here? Mixed in GenericManager handling (getLink)
        # TODO: the guessing and attribute fetching is horrible anyway, refactor
        # a message if we have recently saved something
        if REQUEST.get('zopra_message'):
            if isinstance(REQUEST.get('zopra_message'), StringType):
                message = REQUEST.get('zopra_message')
            else:
                message = 'Your values have been saved'
                table  = REQUEST.get('zopra_message_table', None)
                autoid = 0
                try:
                    autoid = int(REQUEST.get('zopra_message_id', 0))
                except:
                    pass
                if not isinstance(table, StringType):
                    table = None
                if table and autoid:
                    message += ': ' + self.getLink(table, autoid).getHtml()
                else:
                    message += '. '
            dlg.add(dlgLabel(message, dlg))
            dlg.add(hgLabel(hgNEWLINE, parent = dlg))
            dlg.add(hgLabel(hgNEWLINE, parent = dlg))

        # for external information
        if refresh:
            dlg.add(str(mpfRefreshButton))
            dlg.add(hgLabel(hgSPACE))

        dlg.add(str(mpfUpdateButton))
        dlg.add(hgLabel(hgSPACE))

        dlg.add(str(mpfResetButton))
        dlg.add(hgLabel(hgSPACE))

        if closeIsClose:
            dlg.add(str(mpfCloseButton))
        else:
            dlg.add(self.getBackButtonStr(REQUEST))

        dlg.add('</center>')
        return HTML( dlg.getHtml() )(self, REQUEST)


    security.declareProtected(viewPermission, 'getTableEntryShowDialog')

    def getTableEntryShowDialog( self,
                                 title,
                                 mask,
                                 action    = '',
                                 REQUEST   = None,
                                 table     = None,
                                 auto      = None,
                                 actid     = None,
                                 edit      = False,
                                 isGeneric = False,  # obsolete
                                 basket    = False,
                                 closeIsClose = False):
        """\brief Returns the html source of an table entry overview."""
        if action and (len(action) < 4 or not action[:4] == 'http'):
            action = '%s/%s' % (self.absolute_url(), action)
        # dialog and main widget
        dlg  = getStdDialog(title, action)

        widget = hgWidget(parent = dlg)
        dlg.add(widget)
        layout = hgGridLayout(widget, 1, 1, 5, 5)

        line = hgWidget(parent = widget)
        lay  = hgGridLayout(line, 1, 1, 5, 5)
        layout.addWidget(line, 0, 0, hg.AlignCenter)
        layout.addWidget(line, 2, 0, hg.AlignCenter)

        # prev / next handling for search results show page
        if auto:
            if not isinstance(auto, ListType):
                auto = [auto]
            # remove double entries, sort the result
            # original sorting gets lost anyway
            auto = list(dict([(a, a) for a in auto]))
            auto.sort()
            # get the index
            ind      = auto.index(str(actid))

            # build the buttons and the properties
            # check for first / last id and get the prev / next ids
            if ind > 0:
                prev = auto[ind - 1]
            else:
                prev = ''
            if ind < len(auto) - 1:
                next = auto[ind + 1]
            else:
                next = ''

            # prev button
            bprev = hgPushButton('previous', DLG_FUNCTION + table + '_prev' + str(prev), parent = line)
            if prev:
                img = self.IMG_SHOW_PREV
            else:
                bprev.setEnabled(False)
                img = self.IMG_SHOW_PREV_DEACT
            # set the image
            bprev.setIcon( self.iconHandler.get(img, path = True).getIconDict() )
            # get tooltip
            tipprev = self.TOOLTIP_DICT[self.IMG_SHOW_PREV]
            # check tip for replacement char
            if tipprev.find('%s') != -1:
                # add table label to text
                tabLab = self.tableHandler[table].getLabel()
                tipprev = tipprev % (tabLab)
            bprev.setToolTip( tipprev )
            # add to layout
            lay.addWidget(bprev, 0, 0)

            # next button
            bnext = hgPushButton('next', DLG_FUNCTION + table + '_next' + str(next), parent = line)
            if next:
                img = self.IMG_SHOW_NEXT
            else:
                bnext.setEnabled(False)
                img = self.IMG_SHOW_NEXT_DEACT
            # set the image
            bnext.setIcon( self.iconHandler.get(img, path = True).getIconDict() )
            # get tooltip
            tipnext = self.TOOLTIP_DICT[self.IMG_SHOW_NEXT]
            # check tip for replacement char
            if tipnext.find('%s') != -1:
                # add table label to text
                tabLab = self.tableHandler[table].getLabel()
                tipnext = tipnext % (tabLab)
            bnext.setToolTip( tipnext)
            # add to layout
            lay.addWidget(bnext, 0, 4)


            # auto properties
            contWidg = hgWidget(parent = dlg)

            for oneid in auto:
                hgProperty('auto', str(oneid), parent = contWidg)
            # layoutless widgets need a hint to show their children
            contWidg.showChildren(False)
            dlg.add(contWidg)

        # TODO: check entryPermission
        # show edit button only if the edit-action is specified
        if action and edit:
            lab = hgLabel(mpfEditButton.getHtml(), parent = line)
            lay.addWidget(lab, 0, 1)

        if basket and REQUEST.get('repeataction'):

            lab = hgLabel(mpfBasketAddButton.getHtml(), parent = line)
            lay.addWidget(lab, 0, 2)

        if closeIsClose:
            lab = hgLabel(mpfCloseButton.getHtml(), parent = line)
        else:
            lab = hgLabel(self.getBackButtonStr(REQUEST), parent = line)
        lay.addWidget(lab, 0, 3)

        if not isinstance( mask, hgWidget):
            mask = hgLabel(mask)

        mask.reparent(widget)
        layout.addWidget(mask, 1, 0, hg.AlignCenter)

        return HTML( dlg.getHtml() )(self, None)


    security.declareProtected(viewPermission, 'getTableEntrySearchDialog')

    def getTableEntrySearchDialog( self,
                                   title,
                                   mask,
                                   action = '',
                                   table = None,
                                   closeIsClose = False ):
        """\brief Returns the html source of an table search form."""
        if action and (len(action) < 4 or not action[:4] == 'http'):
            action = '%s/%s' % (self.absolute_url(), action)

        mpfResetButton.isLocal = False
        mpfResetButton._valid  = False

        dlg  = getStdDialog(title, action)
        dlg.add('<center>')

        # add the top bar
        dlg.add( mpfSearchButton )
        dlg.add( hgLabel(hgSPACE) )
        dlg.add( mpfResetButton     )
        dlg.add( hgLabel(hgSPACE) )
        if closeIsClose:
            dlg.add(str(mpfCloseButton))
        else:
            dlg.add( self.getBackButton()   )
        dlg.add( hgLabel(hgNEWLINE) )

        # add the mask
        if not isinstance( mask, hgObject):
            mask = hgLabel(mask)
        dlg.add( mask )
        dlg.add( hgLabel(hgNEWLINE) )

        # add hint and column selection
        tab = hgTable(parent = dlg)

        tab[0, 0]  = hgLabel('Wildcards: <br>'     +
                            'NOT Operator: <br>'   +
                            'Range Operator: <br>' +
                            'Sequence Op: ')
        tab[0, 1]  = hgSPACE
        tab[0, 2]  = hgLabel('*, %<br>'    +
                            '_not_<br>'    +
                            'A _to_ B<br>' +
                            'A __ B __ D')
        tab[0, 3]  = hgSPACE
        tab[0, 4]  = hgLabel('Less than: <br>'   +
                            'Greater than: <br>' +
                            'Nothing: <br>'      +
                            'Something: ')
        tab[0, 5]  = hgSPACE
        tab[0, 6]  = hgLabel('_<_, _<=_<br>' +
                            '_>_, _>=_<br>'  +
                            '_0_<br>'        +
                            '*')
        tab[0, 7]  = hgSPACE
        tab[0, 8]  = hgLabel( 'Display<br>' +
                            'Field<br>'     +
                            'Selection:' )
        if table:
            tab[0, 9]  = hgSPACE
            tab[0, 10]  = self.tableHandler[table].getFieldSelectionList()
        tab.setRowAlignment(  0,    tab.ALIGN_CENTER, tab.ALIGN_BOTTOM )
        tab.setCellAlignment( 0, 0, tab.ALIGN_LEFT,   tab.ALIGN_BOTTOM )
        tab.setCellAlignment( 0, 2, tab.ALIGN_LEFT,   tab.ALIGN_BOTTOM )
        tab.setCellAlignment( 0, 4, tab.ALIGN_LEFT,   tab.ALIGN_BOTTOM )
        tab.setCellAlignment( 0, 6, tab.ALIGN_LEFT,   tab.ALIGN_BOTTOM )
        tab.setCellAlignment( 0, 8, tab.ALIGN_RIGHT,  tab.ALIGN_BOTTOM )

        dlg.add( tab )

        # add the bottom bar
        dlg.add( hgLabel(mpfSearchButton.getHtml() ))
        dlg.add( hgLabel(hgSPACE) )
        dlg.add( hgLabel(mpfResetButton.getHtml() )  )
        dlg.add( hgLabel(hgSPACE) )
        if closeIsClose:
            dlg.add(hgLabel(mpfCloseButton).getHtml())
        else:
            dlg.add( self.getBackButton()   )

        dlg.add('</center>')

        mpfResetButton.isLocal = True

        return HTML( dlg.getHtml() )(self, None)


    security.declareProtected(viewPermission, 'getSearchTickAutoidList')

    def getSearchTickAutoidList(self, table, REQUEST, treeRoot, row_count = 0, max_rows = 0):
        """\brief Get Autoidlist of ticked or all searched entries"""
        # the result
        autoidlist = []
        # selected entries only
        if 'delete' in REQUEST:
            autoidlist = self.getValueListFromRequest(REQUEST, 'delete')
            # check count
            if max_rows and len(autoidlist) > max_rows:
                if 'Continue' in getPressedButton(REQUEST):
                    return autoidlist
                err = 'Too many entries have been chosen for an operation. '
                err += 'If you are sure and want to continue to work with %s entries, ' % len(autoidlist)
                err += 'press continue.'
                dlg = self.getErrorDialog(err, html = False)
                button = hgPushButton('Continue', DLG_FUNCTION + 'Continue')
                dlg.add(button)
                for formkey in REQUEST.form.keys():
                    formval = REQUEST.form[formkey]
                    if isinstance(formval, ListType):
                        for oneval in formval:
                            dlg.add(hgProperty(formkey, oneval, parent = dlg))
                    else:
                        dlg.add(hgProperty(formkey, formval, parent = dlg))
                return HTML( dlg.getHtml() )(self, None)
        # all entries (search result)
        else:
            # check count
            if max_rows and row_count > max_rows:
                if 'Continue' not in getPressedButton(REQUEST):
                    err = 'Too many entries have been chosen for an operation. '
                    err += 'If you are sure and want to continue to work with %s entries, ' % row_count
                    err += 'press continue.'
                    dlg = self.getErrorDialog(err, html = False)
                    button = hgPushButton('Continue', DLG_FUNCTION + 'Continue')
                    dlg.add(button)
                    for formkey in REQUEST.form.keys():
                        formval = REQUEST.form[formkey]
                        if isinstance(formval, ListType):
                            for oneval in formval:
                                dlg.add(hgProperty(formkey, oneval, parent = dlg))
                        else:
                            dlg.add(hgProperty(formkey, REQUEST.form[formkey], parent = dlg))
                    return HTML( dlg.getHtml() )(self, None)

            autoidlist = []
            # Fixme: why is distinct False? this could generate a lot of double autoid entries
            # which are filtered then into a distinct list. can't remember why.
            sql = treeRoot.getSQL(distinct = False, checker = self)
            cache = self.tableHandler[table].cache
            autoidlist = deepcopy(cache.getItem(cache.IDLIST, sql))

            if not autoidlist:
                results = self.getManager(ZC.ZM_PM).executeDBQuery(sql)
                if results:
                    aiddict = {}
                    for result in results:
                        aiddict[int(result[0])] = None
                    autoidlist = aiddict.keys()
                    # caching
                    cache.insertItem( cache.IDLIST, sql, autoidlist )
        return autoidlist


    security.declareProtected(viewPermission, 'getTableEntryListHtml')

    def getTableEntryListHtml( self,
                               treeRoot,
                               param      = None,
                               REQUEST    = None,
                               isGeneric  = False,  # obsolete
                               closeIsClose = False ):
        """\brief Returns the html source of an table overview.
        param
            start_number
            show_number
            special link
            special link field
            foreign fields definition
        """
        table = treeRoot.getName()

        perm  = self.getGUIPermission()
        ztype = self.getZopraType()

        if not param:
            param = {}

        # show context menu
        if REQUEST:
            REQUEST.SESSION['columnChooser'] = [table, REQUEST.form]

        # now begin
        tablename = table[0].upper() + table[1:]

        if table not in self.tableHandler:
            raise ValueError(
                self.getErrorDialog(
                    dlgLabel('Manager.getTableEntryListHtml') +
                    hgNEWLINE +
                    'Table %s does not exist' % table)
                    )

        # get the table object
        tabobj = self.tableHandler[table]
        tabid  = tabobj.getUId()
        #
        # dialog functions
        #
        show_fields = param.get( 'show_fields', [] )
        show_number = self.show_number

        # acquire request
        if not REQUEST:
            REQUEST = self.REQUEST

        # get the property of show_number, if it is in the request
        if 'show_number_saved' in REQUEST:
            show_number = int(REQUEST['show_number_saved'])

        # function buttons
        # returns list in this case
        buttonlist = getPressedButton(REQUEST)
        inc    = self.getPressedButton(REQUEST, DLG_INC)
        dec    = self.getPressedButton(REQUEST, DLG_DEC)

        # set constraints
        treeRoot.setConstraints(REQUEST.form)

        # fields for list view
        tempshow = REQUEST.get('show_fields')
        if tempshow:
            if not isinstance(tempshow, ListType):
                tempshow = [tempshow]

            tmp2 = []
            # preserver original order of show_fields
            for item in show_fields:
                if item in tempshow:
                    tmp2.append(item)
            for item in tempshow:
                if item not in tmp2:
                    tmp2.append(item)
            show_fields = tmp2

        # special field on col 1
        if 'special_field' in param:
            field = param.get('special_field')
            if field in show_fields:
                show_fields.remove(field)
                show_fields.insert(0, field)

        # order functions
        if inc:
            ordering = [inc]
            orderdir = ['asc']
        elif dec:
            ordering = [dec]
            orderdir = ['desc']
        elif 'order' in REQUEST:
            ordering = REQUEST['order']
            if not isinstance(ordering, ListType):
                ordering = [ordering]
            if 'orderdir' in REQUEST:
                orderdir = REQUEST['orderdir']
                if not isinstance(orderdir, ListType):
                    orderdir = [orderdir]
            else:
                orderdir = len(ordering) * ['asc']
        else:
            ordering = []
            orderdir = []

        # special field ordering is either used as primary or secondary sort order
        if 'special_field' in param:
            ordering.append(param['special_field'])
            orderdir.append('asc')
        elif len(ordering) == 0:
            # nothing set yet, use autoid
            ordering.append(ZC.TCN_AUTOID)
            orderdir.append('asc')
        # set order in TableNode object
        treeRoot.setOrder(ordering, orderdir)

        # get row count right away to provide value for BTN_L_LAST
        func = 'count(distinct %sautoid)'
        # the type checks in getSQL throw ValueErrors for wrong types
        try:
            row_count = self.getManager(ZC.ZM_PM).\
                         executeDBQuery( treeRoot.getSQL(function = func, checker = self)
                                         )[0][0]
        except ValueError, vErr:
            val = str(vErr[0]) if not isinstance(vErr[0], StringType) else vErr[0]
            dlg = val if val.find('hgDialog') != -1 else self.getErrorDialog(val, REQUEST)
            return HTML(dlg)(self, None)

        # names of the show and edit buttons
        showprefix = table + '_show'
        editprefix = table + '_edit'

        # selection marker
        select_all = False

        # check buttons
        for button in buttonlist:

            # check the show buttons
            if button.startswith(showprefix):
                # forward to showForm
                # remove from request
                try:
                    del REQUEST.form[DLG_FUNCTION + button]
                except:
                    # getPressedButton now corrects the REQUEST
                    pass
                id = button[len(showprefix):]
                auto = REQUEST.get('auto', [])
                # do not clear the request to retain the search params for context column chooser
                # put id into request, it could be needed from request later on
                REQUEST.form['id'] = id
                return self.showForm(id, table, REQUEST, auto)

            # check the edit buttons
            elif button.startswith(editprefix):
                # forward to editForm
                # remove from request
                try:
                    del REQUEST.form[DLG_FUNCTION + button]
                except:
                    # getPressedButton now corrects the REQUEST
                    pass
                _id = button[len(editprefix):]
                # clear the request's form (search params could be mistaken as edit params)
                REQUEST.form = {}
                # put id into request, it could be needed from request later on
                REQUEST.form['id'] = _id
                return self.editForm(_id, table, REQUEST)

            # next function
            elif button == BTN_L_NEXT:
                if 'next' in REQUEST:
                    param['start_number'] = REQUEST['next']

            # previous function
            elif button == BTN_L_PREV:
                if 'prev' in REQUEST:
                    param['start_number'] = REQUEST['prev']

            elif button == BTN_L_FIRST:
                param['start_number'] = 0

            # previous function
            elif button == BTN_L_LAST:
                if row_count % show_number == 0:
                    param['start_number'] = row_count - show_number
                else:
                    param['start_number'] = row_count

            elif button == BTN_L_SHOW_NUMBER:
                tmp = REQUEST.get('show_number')
                if tmp:
                    try:
                        tmp = int(tmp)
                        if tmp > 0:
                            # never let it be set to 0
                            show_number = tmp
                    except:
                        # no number given, do nothing
                        pass

            # previous function
            elif button == BTN_L_GO:
                if 'goto_page' in REQUEST:
                    try:
                        page = int(REQUEST['goto_page'])
                    except:
                        pass
                    else:
                        if page < 1:
                            page = 1
                        # check for number's higher than maximum pagecount
                        elif show_number * (page - 1) > row_count:
                            page = row_count / show_number + 1
                        # check for last page with show_number number of entries
                        elif show_number * (page - 1) == row_count:
                            page = row_count / show_number
                        param['start_number'] = show_number * (page - 1)


            # delete function
            elif button == BTN_L_DELETE:

                # get ids to delete
                if 'delete' in REQUEST:
                    changedIds = self.getValueListFromRequest( REQUEST,
                                                               'delete' )

                    # call multi deletion dialog
                    attrs = {}
                    attrs['table']     = table
                    attrs['autoids']   = changedIds

                    # init dialog
                    dlg = self.dlgHandler.getDialog('dlgMultiDelete', REQUEST.SESSION, None, attrs)
                    dlg.setAction( '%s/dlgHandler/show' % self.absolute_url() )

                    # set the REQUEST params for return jump
                    dlg.setReturnParams(REQUEST)

                    # sets the active window
                    app = self.dlgHandler.getApplication( REQUEST.SESSION )
                    app.active_window = dlg

                    # save changed dlg again (for persistence)
                    REQUEST.SESSION[ str(dlg.uid) ] = dlg

                    # put it back online
                    return HTML( dlg.getHtml() )(self, None)

            # search function
            elif button == BTN_L_SEARCH:

                pass

            elif button == BTN_MULTIEDIT:
                # no context columnchooser
                if REQUEST.SESSION.has_key('columnChooser'):
                    del REQUEST.SESSION['columnChooser']

                # get autoidlist
                autoidlist = self.getSearchTickAutoidList(table, REQUEST, treeRoot, row_count, 200)

                attrs = {}
                attrs['table']     = table
                attrs['autoid']    = autoidlist
                attrs['attribute'] = show_fields
                if 'multiedit_restrict' in param:
                    attrs['restriction'] = param['multiedit_restrict']
                # init dialog
                dlg = self.dlgHandler.getDialog('dlgMultiEdit', REQUEST.SESSION, None, attrs)
                dlg.setAction( '%s/dlgHandler/show' % self.absolute_url() )

                # set target url when dialog is finished
                dlg.initTargetUrl(self, REQUEST)

                # sets the active window
                app = self.dlgHandler.getApplication( REQUEST.SESSION )
                app.active_window = dlg

                # put it back online
                return HTML( dlg.getHtml() )(self, None)

            elif button == BTN_L_EXPORT:
                # if nothing is ticked, we export all (the function returns all autoids then)
                autoidlist = self.getSearchTickAutoidList(table, REQUEST, treeRoot, row_count, 200)

                if autoidlist:
                    # forward to the export form with the given autoids
                    return self.exportForm(None, None, autoidlist, show_fields, table)

            # manager-defined buttons
            elif param.get('ownButtonActions') and button in param['ownButtonActions'].keys():
                action = param['ownButtonActions'][button]
                # no context columnchooser
                if  REQUEST.SESSION.has_key('columnChooser'):
                    del REQUEST.SESSION['columnChooser']

                # get choosen or all autoids
                autoidlist = self.getSearchTickAutoidList(table, REQUEST, treeRoot, row_count, 200)

                return action(autoidlist, REQUEST)

            elif button == BTN_L_SELECT_ALL:
                select_all = True
                # pressed two times -> deselect
                if 'delete' in REQUEST:
                    autoidlist = self.getValueListFromRequest( REQUEST,
                                                        'delete' )
                    if len(autoidlist) == show_number:
                        select_all = False

        #
        # data generation
        #

        # get start and end of the list
        start_number = param.get('start_number', 0)
        # show_number was configured before

        # buttons
        next_button  = hgPushButton(BTN_L_NEXT,  DLG_FUNCTION + BTN_L_NEXT )
        prev_button  = hgPushButton(BTN_L_PREV,  DLG_FUNCTION + BTN_L_PREV )
        go_button    = hgPushButton(BTN_L_GO,    DLG_FUNCTION + BTN_L_GO   )
        first_button = hgPushButton(BTN_L_FIRST, DLG_FUNCTION + BTN_L_FIRST)
        last_button  = hgPushButton(BTN_L_LAST,  DLG_FUNCTION + BTN_L_LAST )

        if not isinstance(show_number, IntType):
            try:
                show_number = int(show_number)
            except:
                raise ValueError('show_number is not int but [%s]' % show_number)

        if not isinstance(start_number, IntType):
            try:
                start_number = int(start_number)
            except:
                start_number = 0

        # make sure we are inside of bounds and start at first entry of page
        if start_number < 0:
            start_number = 0
        elif start_number > row_count:
            start_number = (row_count / show_number) * show_number
        else:
            start_number = (start_number / show_number) * show_number

        page  = (start_number / show_number) + 1
        # fix for pagecount displaying last page with exactly matching show_number / len(result_list)
        pages = (row_count    / show_number) + ((row_count % show_number != 0 or row_count == 0 or 0) and 1)

        prev_number = start_number - show_number
        next_number = start_number + show_number

        if row_count <= next_number:
            next_number = None

        # apply button settings
        if prev_number >= 0:
            prev_button.setEnabled(True)
            first_button.setEnabled(True)
            prev_button.setIcon( self.iconHandler.get(self.IMG_PAGEBWD,     path = True).getIconDict() )
            first_button.setIcon( self.iconHandler.get(self.IMG_PAGEFIRST,  path = True).getIconDict() )

        else:
            prev_button.setEnabled(False)
            first_button.setEnabled(False)
            prev_button.setIcon( self.iconHandler.get(self.IMG_PAGEBWD_DEACT,    path = True).getIconDict() )
            first_button.setIcon( self.iconHandler.get(self.IMG_PAGEFIRST_DEACT, path = True).getIconDict() )

        if next_number:
            next_button.setEnabled(True)
            last_button.setEnabled(True)
            next_button.setIcon( self.iconHandler.get(self.IMG_PAGEFWD,  path = True).getIconDict() )
            last_button.setIcon( self.iconHandler.get(self.IMG_PAGELAST, path = True).getIconDict() )

        else:
            next_button.setEnabled(False)
            last_button.setEnabled(False)
            next_button.setIcon( self.iconHandler.get(self.IMG_PAGEFWD_DEACT,   path = True).getIconDict() )
            last_button.setIcon( self.iconHandler.get(self.IMG_PAGELAST_DEACT,  path = True).getIconDict() )

        # entry field for current page
        page_editWidget    = hgLineEdit( str(page), name = 'goto_page' )
        page_editWidget.setSize(5)
        page_editWidget.setAlignment(hg.AlignRight)

        # entry field for page item count
        show_numberWidget = hgLineEdit( str(show_number), name = 'show_number' )
        show_numberWidget.setSize(5)
        show_numberWidget.setAlignment(hg.AlignRight)

        # build table
        tab = hgTable(spacing = '0', padding = '2')

        # autoidlists are only needed if we
        # want to navigate the result's showforms
        entry_list = tabobj.requestEntries(treeRoot, show_number, start_number)

        # for next/prev for show
        autoidlist = []

        if row_count < 200 and param.get( 'with_autoid_navig' ):
            autoidlist = self.getManager(ZC.ZM_PM).\
                          executeDBQuery( treeRoot.getSQL(distinct = True, checker = self) )
            # flatten list
            autoidlist = [oneline[0] for oneline in autoidlist]

        row = 0
        col = 3

        if param.get('ownButtonActions'):
            row += 1
        # data header
        tab[row + 1, 1] = dlgLabel('Sorting')
        # store this row for adding the select_all button later
        row_select_all = row + 1
        tab.setCellNoWrap(row, 1)
        tab.setCellNoWrap(row + 1, 1)
        tab.setCellSpanning(row, 1, 1, 2)
        tab.setCellSpanning(row + 1, 1, 1, 2)
        tab.setCellAlignment(row + 1, 1, hg.AlignRight)

        # get sorting icons
        icon_deact = self.iconHandler.get(self.IMG_SORTDEACT, path = True).getIconDict()
        icon_none  = self.iconHandler.get(self.IMG_SORTNONE,  path = True).getIconDict()
        icon_asc   = self.iconHandler.get(self.IMG_SORTASC,   path = True).getIconDict()
        icon_desc  = self.iconHandler.get(self.IMG_SORTDESC,  path = True).getIconDict()

        sort_icons = { hgSortButton.DISABLED:  icon_deact,
                       hgSortButton.SORT_OFF:  icon_none,
                       hgSortButton.SORT_ASC:  icon_asc,
                       hgSortButton.SORT_DESC: icon_desc
                       }

        ordering = treeRoot.getOrder()
        directions = treeRoot.getOrderDirection()
        for field in show_fields:
            name = tabobj.getField(field).\
                        get(ZC.COL_LABEL, field)
            bnamelab = hgLabel(name, parent = tab)

            sort_btn = hgSortButton(name = field, icons = sort_icons, parent = tab)

            if field in ordering:
                direc = directions[ordering.index(field)]
                if direc == 'desc':
                    sort_btn.setState(hgSortButton.SORT_DESC)
                    sort_btn.setToolTip('Sort field \'%s\' in ascending order' % name)
                else:
                    # 'asc' and None leed to asc-sorting
                    sort_btn.setState(hgSortButton.SORT_ASC)
                    sort_btn.setToolTip('Sort field \'%s\' in descending order' % name)
            else:
                sort_btn.setToolTip('Sort field \'%s\' in ascending order' % name)

            tab[row,     col] = bnamelab
            tab[row + 1, col] = sort_btn

            tab.setCellAlignment(row,     col, tab.ALIGN_CENTER)
            tab.setCellAlignment(row + 1, col, tab.ALIGN_CENTER)

            col += 1

        # function labels
        if param.get('links'):
            for count, name in enumerate(param['links']):
                if count > 0:
                    sign = ' | '
                    tab[row, col - 1] = dlgLabel( sign )

                tab[row, col ] = dlgLabel( name )
                # tab.setCellNoWrap(row, col)
                col += 2

        row += 2

        m_security = self.getHierarchyUpManager(ZC.ZM_SCM)

        # multi-edit flag
        multi_edit = param.get('with_multiedit') is True

        # activate delete button if at least one entry is owned
        owner_delete = False
        check_box_displayed = False

        # prepare list objects
        lobjs = {}
        for field in show_fields:
            if self.listHandler.hasList(table, field):
                lobjs[field] = self.listHandler.getList(table, field)

        # iterate entries
        for entry in entry_list:
            self.prepareEntryBeforeShowList(table, entry, REQUEST)

            row += 1
            col  = 0
            entry_id = entry[ZC.TCN_AUTOID]

            isowner = entry['permission'].isOwner()

            if (isowner and not param.get('with_delete') is False):
                owner_delete = True

            # delete data
            if param.get('with_delete') or \
               param.get('with_multiedit') or \
               (isowner and not param.get('with_delete') is False) or \
               param.get('with_basket') or \
               param.get('ownButtonActions'):
                tab[row, col] = hgCheckBox( '',
                                            str(entry_id),
                                            None,
                                            'delete' )
                # check selection
                if select_all:
                    tab[row, col].setChecked(True)
                # set to show select-all button / export button
                check_box_displayed = True
            col += 1

            # show data
            # no ebase action necessary, search was restricted anyway
            if param.get('with_show') or \
               (isowner and not param.get('with_show') is False):

                # create button
                func = DLG_FUNCTION + table + '_show' + str(entry_id)
                button = hgPushButton('show', func, parent = tab)

                button.setIcon( self.iconHandler.get(self.IMG_SHOW, path = True).getIconDict() )

                tip = self.TOOLTIP_DICT[self.IMG_SHOW]
                if tip.find('%s') != -1:
                    # add table label to text
                    tabLab = self.tableHandler[table].getLabel()
                    tip = tip % (tabLab)
                    button.setToolTip(tip)
                tab[row, col] = button

            col += 1

            # edit data
            # the if-clause has to look exactly like this, to enable
            # suppressing of creator-editing for crf
            if param.get('with_edit') or \
               (isowner and not param.get('with_edit') is False):

                # create button
                func = DLG_FUNCTION + table + '_edit' + str(entry_id)
                button = hgPushButton('edit', func, parent = tab)

                button.setIcon( self.iconHandler.get(self.IMG_EDIT, path = True).getIconDict() )

                tip = self.TOOLTIP_DICT[self.IMG_EDIT]
                if tip.find('%s') != -1:
                    # add table label to text
                    tabLab = self.tableHandler[table].getLabel()
                    tip = tip % (tabLab)
                    button.setToolTip( tip)
                tab[row, col] = button

            # change color
            if not row % 2:
                tab.setCellBackgroundColor(row, col - 2, '#E0E0DA')
                tab.setCellBackgroundColor(row, col - 1, '#E0E0DA')
                tab.setCellBackgroundColor(row, col,     '#E0E0DA')

            col += 1

            # data
            for field in show_fields:
                if field in lobjs:
                    widg = lobjs[field].getShowHtml(entry, False, tab)
                else:
                    value = entry.get(field)
                    if value and isinstance(value, StringType):
                        value  = value.replace('<', '&lt;')
                        value  = value.replace('>', '&gt;')
                        value  = value.replace('\n', '<br>')
                        # check long strings (notes etc)
                        if len(value) > 45:
                            # trim shorter than checked
                            value = value[:40] + '...'
                    # test field type
                    field_info = tabobj.getField(field)
                    print field, field_info
                    ftype      = field_info[ZC.COL_TYPE]

                    if ftype == ZC.ZCOL_BOOL:
                        tab.setCellAlignment(row, col, hgALIGN_CENTER)
                        widg = hgCheckBox(parent = tab)
                        widg.setDisabled()
                        if value:
                            widg.setChecked(True)
                    else:
                        widg = hgLabel( value, parent = tab )
                        # different aligning for different cols is autsch -> commented out
                        # if ftype in [ ZC.ZCOL_INT, ZC.ZCOL_LONG, ZC.ZCOL_DATE, ZC.ZCOL_FLOAT ]:
                        #    tab.setCellAlignment(row, col, hgALIGN_RIGHT)
                        # else:
                        tab.setCellAlignment(row, col, hgALIGN_LEFT)

                tab[row, col] = widg

                if not row % 2:
                    tab.setCellBackgroundColor(row, col, '#E0E0DA')

                col += 1

            # special links
            if param.get('links'):
                for count, name in enumerate(param['links']):
                    linkpart = param['links'][name].get('link')
                    field    = param['links'][name].get('field')
                    if not field:
                        field = ZC.TCN_AUTOID
                    # if check is given, the function with this name
                    # calculates the id (or None) or a label (if link is '')
                    # else we have a normal manager field
                    data     = ''
                    label    = ''
                    checkfun = param['links'][name].get('check')

                    if checkfun:
                        fun = getattr(self, checkfun)
                        data = fun(entry.get(field))
                        # fun can return the id or the label (no link specified) or a tuple (id, label)
                        if isinstance(data, TupleType):
                            label = data[1]
                            data  = data[0]

                    else:
                        data = entry.get(field)

                    if data:
                        if linkpart:
                            link  = linkpart + str(data)
                            if not label:
                                label = name

                        else:
                            link  = None
                            if not label:
                                label = str(data)

                        tab[row, col ] = hgLabel(label, link )

                    if count > 0:
                        sign = ' | '
                        tab[row, col - 1] = hgLabel(sign)
                        if not row % 2:
                            tab.setCellBackgroundColor(row, col - 1, '#E0E0DA')

                    if not row % 2:
                        tab.setCellBackgroundColor(row, col, '#E0E0DA')

                    col += 2

        # for the layout (col distribution)
        off   = 3
        field_length = len(show_fields)
        if param.get('links'):
            # double - 1 because of the spacing cols between the links
            field_length += 2 * (len(param.get('links').keys())) - 1

        if not field_length:
            field_length = 1

        width = str( 80 / field_length ) + '%'
        if hasattr(self, 'listcolwidth'):
            width = getattr(self, 'listcolwidth')

        # BUG: KeyError -> probably no show_fields defined
        for cnt in xrange(field_length):
            if (cnt > (len(show_fields) - 1)) and not (cnt - len(show_fields) + 1) % 2:
                continue
            tab.setColWidth( cnt + off, str(width) )

        # add select_all button
        if check_box_displayed:
            tab[row_select_all, 0] = mpfSelectAllButton

        #
        # layout
        #

        # dialog init
        # the target
        action_method  = '%s/showList' % self.absolute_url()
        # the generic table property
        table_property = hgProperty('table', table)
        # fix for no entries:
        if len(entry_list):
            label = 'Show %s List: Entry %d - %d (%s Entries)' \
                                % ( tablename,
                                    start_number  + 1,
                                    start_number  + len(entry_list),
                                    row_count
                                    )
        else:
            label = 'Show %s List: No entries found.' % (tablename)

        dlg  = getStdDialog(label,
                            action_method )

        dlg.add( '<center>')

        # dialog header
        navig = hgTable(spacing = '0', padding = '2')
        navig[0, 0] = go_button
        navig[0, 1] = page_editWidget
        navig[0, 2] = hgLabel(hgSPACE)
        navig[0, 3] = first_button
        navig[0, 4] = prev_button
        navig[0, 5] = hgLabel(hgSPACE)
        navig[0, 6] = hgLabel('%s / %s' % (page, pages))
        navig[0, 7] = hgLabel(hgSPACE)
        navig[0, 8] = next_button
        navig[0, 9] = last_button
        navig[0, 10] = hgLabel(hgSPACE)
        navig[0, 11] = mpfNumberButton
        navig[0, 12] = show_numberWidget

        dlg.add( navig                   )
        dlg.add( hgLabel(hgNEWLINE)      )
        dlg.add( hgLabel(hgNEWLINE)      )
        dlg.add( tab                     )
        dlg.add( table_property          )
        dlg.add( hgLabel(hgNEWLINE)      )

        # own buttons
        gbox        = hgGroupBox(title = 'Manager Functions')
        boxlay      = hgGridLayout( gbox, 1, 1 )

        if param.get('ownButtonActions'):
            col = 0
            for name in param['ownButtonActions']:
                boxlay.addWidget( hgPushButton(name, DLG_FUNCTION + name, parent = gbox ), 0, col )
                boxlay.addWidget( hgLabel(hgSPACE, parent = gbox), 0, col + 1 )
                col += 2

            dlg.add( gbox             )
            dlg.add( hgLabel(hgNEWLINE)      )

        # standard buttons
        if param.get('with_delete') or owner_delete:
            dlg.add( mpfDeleteButton     )
            dlg.add( hgLabel(hgSPACE)    )

        if ( (not m_security or m_security.getCurrentLevel() > 6) and
             REQUEST.get('repeataction') and
             param.get('with_basket') ):

            dlg.add( mpfBasketAddButton )
            dlg.add( hgLabel(hgSPACE)   )

        if multi_edit and perm.hasPermission(perm.SC_EDIT, tabid, ztype):
            # multi edit button
            mpfMultiEditButton = hgPushButton(BTN_MULTIEDIT, DLG_FUNCTION + BTN_MULTIEDIT)
            mpfMultiEditButton.setToolTip('Edit multiple entries at once.')
            dlg.add( mpfMultiEditButton )
        if check_box_displayed:
            dlg.add( mpfExportButton     )
        dlg.add( hgLabel(hgSPACE)    )
        if closeIsClose:
            dlg.add(str(mpfCloseButton))
        else:
            dlg.add( self.getBackButton( REQUEST, False ) )

        dlg.add( '</center>' )

        #
        # internal values (set as properties)
        #

        # back and forth links
        if prev_number >= 0:
            dlg.add( hgProperty('prev', prev_number, parent = dlg) )

        if next_number:
            dlg.add( hgProperty('next', next_number, parent = dlg) )

        # show_number preservation
        dlg.add( hgProperty('show_number_saved', show_number, parent = dlg) )

        # order preservation
        ordering = treeRoot.getOrder()
        if ordering:
            directions = treeRoot.getOrderDirection()
            for order in ordering:
                dlg.add( hgProperty('order', order, parent = dlg) )
                direction = directions[ordering.index(order)]
                if direction:
                    dlg.add( hgProperty('orderdir', direction, parent = dlg) )

        # search constraints preservation
        cons = treeRoot.getConstraints()
        if cons:
            # need search button to enable the use of the constraints
            dlg.add( hgProperty(DLG_FUNCTION + BTN_L_SEARCH, '', parent = dlg) )
            for entry in cons:
                val = cons[entry]
                if isinstance(val, ListType):
                    for item in val:
                        dlg.add( hgProperty(entry, item, parent = dlg))
                else:
                    dlg.add( hgProperty(entry, val, parent = dlg) )

        # autoid list preservation for prev/next entry
        # empty if not used, no additional check required
        for autoid in autoidlist:
            dlg.add( hgProperty('auto', str(autoid), parent = dlg) )

        # show_fields preservation
        if show_fields:
            for field in show_fields:
                dlg.add( hgProperty('show_fields', field, parent = dlg) )

        return HTML( dlg.getHtml() )(self, None)

    ###########################################################################
    #                                                                         #
    # Main Html (entrance, menues, exit)                                      #
    #   - Navigation, Context, index_html, logout                             #
    ###########################################################################

    security.declareProtected(viewPermission, 'navigationMenu')

    def navigationMenu(self, REQUEST):
        """\brief Create the Navigation Menu for inter-manager-navigation."""
        perm = self.getGUIPermission()
        ztype = self.getZopraType()

        # generate dialog
        dlg = getStdZMOMDialog('Navigation', None, Dialog.Embedded)
        bar = hgMenuBar(dlg)
        bar.setDirection(hg.Vertical)
        dlg.add(bar)
        # get application start url
        base = self.topLevelProduct()
        if base:
            # correct the url
            url = base.absolute_url()
            url = url[:-len(base.id)]
            lab = hgLabel('Main Page', url)
            bar.insertItem(text = str(lab))

        # zopratype - depending sub-application link
        orig  = ''

        if ztype:
            orig = ztype
            if REQUEST:
                REQUEST.SESSION['zopratype'] = orig

        elif REQUEST and REQUEST.SESSION.get('zopratype'):
            # no own zt, but another manager set one
            orig = REQUEST.SESSION.get('zopratype')

        m_product = self.getHierarchyDownManager(ZC.ZM_PM, zopratype = orig)
        if m_product:
            # now we need the toplevel product of that zopratype
            m_product = m_product.topLevelProduct(zopratype = orig)
            lab = hgLabel( orig + ' Overview',
                           str(m_product.absolute_url()))
            bar.insertItem(text = str(lab))

        # link to message center
        m_msgm = self.getHierarchyUpManager(ZC.ZM_MM)
        if m_msgm:
            m_msgm.buildMenuItem(bar, REQUEST)

        # link to message board
        m_zmbm = self.getHierarchyUpManager(ZC.ZM_MBM)
        if m_zmbm:
            m_zmbm.buildMenuItem(bar, REQUEST)

        # security manager personal page
        m_sec = self.getHierarchyUpManager(ZC.ZM_SCM)
        if m_sec:
            url = '%s/personalPage' % m_sec.absolute_url()
            link = hgLabel('Personal Page', url)
            bar.insertItem(text = str(link))

        # logout link
        lab = hgLabel('Logout', '%s/logout' % self.absolute_url())
        bar.insertItem(text = str(lab))

        bar.insertItem(text = '&nbsp;')

        # custom part
        found = self.navigationMenuCustom(bar, REQUEST)
        if not found:
            # there was no custom navigation, try ztype dependent navi (product is selected by ztype)
            if m_product:
                m_product.navigationMenuCustom(bar, REQUEST)

        # this part has to be adapted to access role handling
        # furthermore, only relevant manager's links should appear here
        # the complete manager-list will still be seen on the main page
        bar.insertItem(text = '&nbsp;')

        _super = perm.hasMinimumRole(perm.SC_SUPER)
        _super = _super or perm.hasSpecialRole(ztype + 'Superuser')

        if _super:
            # authorization level high

            alllist = self.getNaviManagerUrls(orig, perm.hasRole(perm.SC_ADMIN))
            keylist = alllist.keys()
            keylist.sort()
            pop = hgPopupMenu(bar)
            # make the Managers Item a link to the admin page
            if m_product:
                link = m_product.absolute_url() + '?adminPage=1'
            else:
                # no downstream product, look upstream
                prod2 = self.getHierarchyUpManager(ZC.ZM_PM)
                link = prod2.absolute_url() + '?adminPage=1'

            bar.insertItem(text = str(hgLabel('Managers', link)), popup = pop)
            for key in keylist:

                pop.insertItem(text = str(hgLabel(key, alllist.get(key))))

        return dlg.getHtml()


    security.declareProtected(viewPermission, 'getNaviManagerUrls')

    def getNaviManagerUrls(self, zopratype, admin):
        alllist        = {}
        tmp_list       = self.getAllManagers( type_only = False,
                                              objects   = True )
        if tmp_list:
            for mgr in tmp_list:
                if mgr                                     and \
                   ZC.ZM_PM not in mgr.getClassType()      and \
                   ('ZMOMTool' not in mgr.getClassType() or admin):

                    title = mgr.getTitle()
                    if len(title) > 8 and title[-8:] == ' Manager':
                        title = title[:-8]
                    alllist[title] = str(mgr.absolute_url())

        # we still have to find all hierarchy-down managers...
        if zopratype:
            tmp_list2 = self.getAllManagersHierarchyDown(zopratype = zopratype)
            if tmp_list2:
                for mgr in tmp_list2:
                    # make sure we didnt already find that one
                    if mgr                                  and \
                       ZC.ZM_PM not in mgr.getClassType()   and \
                       ('ZMOMTool' not in mgr.getClassType() or admin) and \
                       mgr not in tmp_list:

                        title          = mgr.getTitle()
                        if len(title) > 8 and title[-8:] == ' Manager':
                            title = title[:-8]
                        alllist[title] = str(mgr.absolute_url())

        return alllist


    security.declareProtected(viewPermission, 'logout')

    def logout(self, REQUEST, RESPONSE):
        """\brief Logout, display link to main page."""
        realm = RESPONSE.realm
        RESPONSE.setStatus(401)
        # next line means immediate login, which never works
        RESPONSE.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)

        m_prod = self.getHierarchyUpManager(ZC.ZM_PM)
        base2 = str(m_prod.absolute_url())
        if base2[-1] == '/':
            base2 = base2[:-1]
        pos = base2.rfind('/')
        if pos != -1:
            base2 = base2[:pos]

        # redirect doesn't work, so we have to build the body
        base = REQUEST.get('BASE1')
        if not base:
            base = REQUEST.get('BASE0')
        # no base, or base is only http://server -> replace with base2
        if not base or base[base.rfind('/') - 1] == '/':
            base = base2

        # TODO: without a base we don't have a dlg -> error later on
        # do we always have a base or is the else missing?
        dlg  = getStdDialog( title = 'You have been logged out' )

        dlg.setHeader("""<html>
                           <head>
                             <title>ZopRA Logout</title>
                             <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
                             <style type="text/css">
                             <!--
                             %s
                             -->
                             </style>
                           </head>
                           <body bgcolor="#FFFFFF"><center>
                           <table><colgroup><col width="*"><col width="400"><col width="*"><colgroup>
                           <tr><td></td><td>
                      """ % self.getCSS())
        dlg.setFooter("""</td><td></td></tr></center></body></html>""")

        dlg.add(hgNEWLINE)
        dlg.add('<center>')
        dlg.add( hgLabel('To Main Page', base, parent = dlg) )
        dlg.add('</center>')
        dlg.add('<br>')
        dlg.add(hgNEWLINE)

        RESPONSE.setHeader('Location', '%s/logged_out' % base2, 1)
        RESPONSE.setBody( HTML( dlg.getHtml() )(self, None) )

        # invalidate session to force re-login if link clicked
        REQUEST.SESSION.invalidate()


    security.declareProtected(viewPermission, 'contextMenu')

    def contextMenu(self, REQUEST = None):
        """\brief Create the Context Menu for Basket and Search-Management."""
        m_security    = self.getHierarchyUpManager(ZC.ZM_SCM)
        html          = []
        columnChooser = ''
        context       = ''

        if REQUEST:

            if REQUEST.SESSION.get('columnChooser'):
                columnChooser = REQUEST.SESSION.get('columnChooser')
                REQUEST.SESSION['columnChooser'] = None

            if REQUEST.SESSION.get('context'):
                context = REQUEST.SESSION.get('context')
                REQUEST.SESSION['context'] = None

        # managerdependent context, has to be switched on via session['context']
        if not m_security or m_security.getCurrentLevel() > 8:
            if context:
                con = self.contextMenuCustom(REQUEST, None)
                if con:
                    html.append( str(con) )

        # column choosing context
        if columnChooser:

            table  = columnChooser[0]
            tabobj = self.tableHandler.get(table)
            if tabobj:
                if len(columnChooser) > 2:
                    func = columnChooser[2]
                    link = '%s/%s' % (self.absolute_url(), func)
                else:
                    link = '%s/showList' % (self.absolute_url())
                form = getStdZMOMDialog( 'Choose Columns',
                                         link,
                                         Dialog.Embedded )

                oldreq = columnChooser[1]
                tablesaved = False
                for key in oldreq.keys():
                    # table-property conserved
                    if key != 'show_fields':
                        if key == 'table':
                            tablesaved = True
                        val = oldreq.get(key, '')
                        if val:
                            if isinstance(val, ListType):
                                for item in val:
                                    form.add( hgProperty(key, item))
                            else:
                                form.add(hgProperty(key, val))
                # check tablesaved
                if not tablesaved:
                    form.add(hgProperty('table', table))
                sel = tabobj.getFieldSelectionList()
                # set the right show_fields as selection
                show_fields = REQUEST.get('show_fields')
                if show_fields:
                    if not isinstance(show_fields, ListType):
                        show_fields = [show_fields]
                    sel.setSelectedValueList(show_fields)
                form.add(sel)

                update = copy(mpfSearchButton)
                update.setToolTip('Update form with selected columns')
                update.setText('Apply')
                form.add( update )
                form.add( hgNEWLINE       )
                html.append(form.getHtml())

                # the search button
                link = '%s/searchForm' % (self.absolute_url())
                form = getStdZMOMDialog( 'New Search',
                                         link,
                                         Dialog.Embedded )

                # if generic:
                form.add( hgProperty('table', table, parent = form) )

                form.add(mpfSearchButton)
                html.append(form.getHtml())

        # this old check doesn't make much sense, but stays active for now
        if not m_security or m_security.getCurrentLevel() > 6:
            # basket_active switches basket on or off
            if hasattr(self, 'basket_active') and self.basket_active:

                # append basket
                html.append( self.basket.getBasketContext(self, REQUEST).getHtml() )

            elif hasattr(self, '_generic_config'):

                table = REQUEST.get('table')

                # TODO: Fix, if dialog and back button string active at the same
                #       time we end up with [ <table_name>, <table_name> ]
                #       This if statement tries to repair it
                if isinstance(table, ListType) and \
                   len(table) == 2 and table[0] == table[1]:
                    table            = table[0]

                if table                            and \
                   self._generic_config.get(table)  and \
                   self._generic_config[table].get('basket_active'):

                    # append  basket
                    html.append( self.basket.getBasketContext(self, REQUEST).getHtml() )

            elif self.basket.isNotEmpty(self, REQUEST.SESSION):

                    # append  basket
                    html.append( self.basket.getBasketContext(self, REQUEST).getHtml() )

        # list management context
        if not m_security or \
           m_security.getCurrentLevel() > 8 or \
           m_security.hasRole(self.getZopraType() + 'Superuser'):
            # TODO: does this work? doubt it.
            if context and context.get('list edit'):
                form = getStdZMOMDialog( 'List Management',
                                         None,
                                         Dialog.Embedded )

                form.add(self.listHandler.getListContextTable(form))
                html.append(form.getHtml())

        return str('').join(html)


    security.declareProtected(modifyPermission, 'getBasketForm')

    def getBasketForm(self, REQUEST):
        """\brief function that displays the basket using the baskets html function.
                This is only an entry point for the basket, when it is forwarding actions to itself.
                Since the basket is no SimpleItem anymore, it cannot be used directly."""
        return self.basket.getBasketHtml(self, REQUEST)


#
# index_html
#


    security.declareProtected(viewPermission, 'index_html')

    def index_html(self, REQUEST = None):
        """ Returns the HTML source of an standard index_html view."""

        # Managing Overview Form
        title = '%s Overview' % self.getTitle()

        # a dialog with header and footer, but we do not want the <form>
        dlg  = getStdDialog(title, formless = True)
        # no boundary please -> new style?

        # messaging test
        m_msg = self.getHierarchyUpManager('MessagingManager')
        if m_msg:
            m_msg.setHeaderPopUp(REQUEST)

        # zopra type handling
        ztype = self.getZopraType()
        if ztype and REQUEST:
            REQUEST.SESSION['zopratype'] = ztype

        # basket
        if REQUEST:
            REQUEST.form['repeataction'] = 'index_html'


        # formA.add('<center>')

        try:
            dlg.add( self._index_html(REQUEST, dlg, border = False))
        except TypeError:
            # border param not known
            dlg.add( self._index_html(REQUEST, dlg))

        # formA.add('</center>')

        # minispacer
        dlg.add(dlgMiniSpacer(dlg))

        # TODO: change list management to work table-wise

        # check for superuser permission
        _super = self.isSuperUser(anytab = True)

        if _super:

            # List Management Form
            if self.listHandler:
                # TODO: get rid of the spacing between form and its surrounding border
                # add manual space outside of border
                # dlg.add(hgSPACE)
                formB = getEmbeddedDialog('List Management', formless = True, parent = dlg)

                # borderless style to fit in parent dlg
                formB._styleSheet.add(ssiDLG_TOPBORDER)
                formB.setSsiName(ssiDLG_TOPBORDER.name())

                # formB.add('<center>')
                listTable = self.listHandler.getListContextTable(formB, 3)
                if listTable:
                    formB.add(listTable)
                else:
                    formB.add(hgLabel('No editable Lists found.', parent = formB))
                # formB.add('</center>')

                dlg.add(formB)

        return HTML( dlg.getHtml() )(self, REQUEST)

    ###########################################################################
    #                                                                         #
    # Export form (Import is in Table)                                        #
    #   - handling is done in Table / GenericManager                          #
    ###########################################################################


    security.declareProtected(viewPermission, 'exportForm')

    def exportForm(self, REQUEST, RESPONSE, autoidlist = None, show_fields = None, table = None):
        """Returns the HTML source of an export table dialog.

        @param REQUEST  The argument \a REQUEST is used for the button handling
                        and should be a ZOPE REQUEST object.
        @param autoidlist If autoidlist, show_fields and table are given, show this params
        @result HTML page - export dialog
        """
        if autoidlist is None:
            autoidlist = []

        if show_fields is None:
            show_fields = []

        #
        # dialog functions
        #
        flags  = 0x0000
        message = None

        if REQUEST:
            buttons = getPressedButton(REQUEST)

            if BTN_L_EXPORT in buttons:
                if not table:
                    return self.getErrorDialog('Please select a table to export.')

                # we need also the admin fields
                allcols = REQUEST.get('all_columns')
                if allcols == '1':
                    # all columns selected
                    columnList = None

                elif allcols == '2':
                    # main table columns selected
                    # (no multi/hierarchylists)
                    columnList = self.tableHandler[table].getMainColumnNames()

                else:
                    # show_field parameter transported
                    columnList = show_fields

                    if allcols == '4':
                        # add edit_tracking
                        flags = flags | TE_TRACKING

                if REQUEST.get('lookup_data') == '1':
                    flags = flags | TE_LOOKUPDATA

                if REQUEST.get('with_header') == '1':
                    flags = flags | TE_WITHHEADER

                autoList = []
                if autoidlist:
                    # got autoidlist from search result page
                    autoList = autoidlist

                if REQUEST.get('set_format') == '1':
                    exportList = self.tableHandler[table].\
                                      exportTab( columnList,
                                                 autoList,
                                                 flags)
                else:
                    exportList = self.tableHandler[table].\
                                      exportXML( columnList,
                                                 autoList,
                                                 flags)

                # return result
                if exportList:

                    # set content-type
                    RESPONSE.setHeader('Content-Type', 'text/plain')

                    if REQUEST.get('set_target') == '2':

                        # set content-disposition to return a file
                        disp = 'attachement; filename="%s.txt"' % table
                        RESPONSE.setHeader( 'Content-disposition', disp)

                    # return the result
                    return '\n'.join(exportList)
                else:
                    message = 'No exportable entries found.'

        #
        # dialog table
        #
        tab = hgTable()

        if not autoidlist:
            tab[0, 0] = hgLabel('<b>Choose table</b>', parent = tab)
            checked     = True
            row = 1
            table_names = self.tableHandler.keys()
            table_names.sort()
            for tname in table_names:
                # get table label
                label = self.tableHandler[tname].getLabel()
                # add radio button for table
                tab[row, 0] = hgRadioButton(tname, label, checked, name = 'table')
                row += 1
                # only first one gets checked
                checked = False
            tab[row, 0] = hgSPACE

        # export values given, present them
        else:
            tobj = self.tableHandler[table]
            tlabel = tobj.getLabel()
            tab[0, 0] = hgLabel('<b>These parameters have been submitted</b>', parent = tab)
            tab.setCellSpanning(0, 0, 1, 2)

            tab[1, 0] = dlgLabel('Table', parent = tab)
            tab[1, 1] = hgLabel(tlabel, parent = tab)
            tab[2, 0] = dlgLabel('Number of entries', parent = tab)
            tab[2, 1] = hgLabel(str(len(autoidlist)), parent = tab)
            tab[3, 0] = dlgLabel('Fields to be exported', parent = tab)
            tab[3, 1] = hgLabel('<br>'.join([tobj.getLabel(field) for field in show_fields]), parent = tab)

            # properties
            fprops = ''.join([hgProperty('show_fields', field).getHtml() for field in show_fields])
            aprops = ''.join([hgProperty('autoidlist', aid).getHtml() for aid in autoidlist])
            tab[3, 2] = hgLabel(fprops, parent = tab)
            tab[2, 2] = hgLabel(aprops, parent = tab)
            tab[1, 2] = hgProperty('table', table, parent = tab)

            # we come from search results page, REQUEST is None, but we need to adjust the columnchooser
            REQUEST = self.REQUEST
            # remove export button if it is there
            form = REQUEST.form
            if DLG_FUNCTION + BTN_L_EXPORT in form:
                del form[DLG_FUNCTION + BTN_L_EXPORT]
            # add show_fields, autoidlist and table
            form['table'] = table
            form['show_fields'] = show_fields
            form['autoidlist'] = autoidlist
            REQUEST.SESSION['columnChooser'] = [table, REQUEST.form, 'exportForm']

        tab2 = hgTable()
        # Header
        tab2[0, 0] = hgLabel('<b>Export Options</b>', parent = tab2)
        tab2.setCellSpanning(0, 0, 1, 2)

        # Options
        if not show_fields:
            tab2[1, 0] = hgRadioButton('1', 'All columns (including lists)', True, name = 'all_columns')
            tab2[1, 1] = hgRadioButton('2', 'Only basic table columns', False, name = 'all_columns')
        else:
            tab2[1, 0] = hgRadioButton('3', 'Preselected Columns', True, name = 'all_columns')
            tab2[1, 1] = hgRadioButton('4', 'Add edit-tracking Columns', False, name = 'all_columns')
        tab2[2, 0] = hgRadioButton('1', 'Use lookup-list Values', True, name = 'lookup_data')
        tab2[2, 1] = hgRadioButton('2', 'Use lookup-list IDs', False, name = 'lookup_data')
        tab2[3, 0] = hgRadioButton('1', 'Export Header Information', True, name = 'with_header')
        tab2[3, 1] = hgRadioButton('2', 'No Header Information', False, name = 'with_header')
        tab2[4, 0] = hgRadioButton('1', 'Tab Separated Format', True, name = 'set_format')
        tab2[4, 1] = hgRadioButton('2', 'XML Format', False, name = 'set_format')
        tab2[5, 0] = hgRadioButton('1', 'Export to screen', True, name = 'set_target')
        tab2[5, 1] = hgRadioButton('2', 'Export to File', False, name = 'set_target')

        #
        # dialog
        #
        dlg  = getStdDialog('Export Table', '%s/exportForm' % self.absolute_url())

        dlg.add(hgLabel('<center>', parent = dlg))

        if message:
            dlg.add(hgNEWLINE.getHtml())
            dlg.add(dlgLabel(message, parent = dlg))
            dlg.add(hgNEWLINE.getHtml())
        dlg.add( hgNEWLINE.getHtml() )
        dlg.add( tab  )
        dlg.add( tab2 )
        dlg.add( hgNEWLINE.getHtml() )
        dlg.add( mpfExportButton )
        dlg.add(self.getBackButtonStr(REQUEST))
        dlg.add(hgLabel('</center>', parent = dlg))
        return HTML( dlg.getHtml() )(self, None)

    ###########################################################################
    #                                                                         #
    # Update Handling                                                         #
    #   - do not forget to alter zopra_version (class attr) to new version    #
    ###########################################################################

    security.declareProtected(managePermission, 'updateVersion')

    def updateVersion(self):
        """\brief   The general update function that is called by
                    the ZopRAProduct or the manager management screen on update.
                    Updates the manager."""
        # get class-version (new) and instance-version (old)
        version = self.zopra_version
        newver  = ManagerPart.zopra_version

        # try to get newver from manager-class
        # can be used to hold some managers back on an old version ... but why?
        if hasattr(self.__class__, 'zopra_version'):
            newver = self.__class__.zopra_version

        # return string
        name = '%s: %s (%s)' % (self._class__.__name__, self.id, version)
        if self.getZopraType():
            name += ' (%s)' % self.getZopraType()

        ret = [name]
        if newver != version:
            # we update
            if version < 1.8:
                # update eight: icon handler and new list handler
                did = self.toVersion1_8()
                for item in did:
                    ret.append(item)
            self.zopra_version = newver
            ret.append('Finished update to Version %s' % self.zopra_version)
        else:
            ret.append('No updates necessary')
        return '<br>'.join(ret)

#
# Update single version functions (one per version, old versions should be removed someday)
#

    security.declareProtected(managePermission, 'toVersion1_8')

    def toVersion1_8(self):
        msg = []

        # xml definition changes for different managers (maxshown / labelsearch options)
        # -> effective after reinstall of tablehandler/listhandler
        # replace table handler
        self.recreateTableHandlers()
        msg.append('Table Handler has been reinstalled.')

        # replace list handler
        self.recreateListHandlers()
        msg.append('List Handler has been reinstalled.')

        # dialog reload still manually

        msg.append('Updated to Version 1.8.')

        return msg



#
# Update helper functions
#


    security.declareProtected(managePermission, 'recreateTableHandlers')

    def recreateTableHandlers(self):
        """ Recreate table handler and reload all table objects with XML from
            table_dict
        """

        # remove tableHandler
        self._delObject('tableHandler')
        self.tableHandler = None

        # create table Handler and store it as subfolder
        self._setObject('tableHandler', TableHandler())

        # initialize tables
        self.tableHandler.xmlInit(getTableDefinition(self), True)



    security.declareProtected(managePermission, 'recreateListHandlers')

    def recreateListHandlers(self):
        """ Recreate the list handler and reload all list objects with XML from
            table_dict as well as the editTracking Lists
        """

        # remove old listhandler
        self._delObject('listHandler')
        self.listHandler = None

        # create list Handler and store it as subfolder
        self._setObject('listHandler', ListHandler())

        # do not create tables in db (they already exist)
        self.listHandler.xmlInit(getTableDefinition(self), True)

        # edit tracking lists
        self.createEditTrackingLists()

        # reset table node caches (since tableprivate holds own listhandler copy -> wah!)
        for tabname in self.tableHandler:
            tobj = self.tableHandler[tabname]
            tobj.resetSearchTreeTemplate()
