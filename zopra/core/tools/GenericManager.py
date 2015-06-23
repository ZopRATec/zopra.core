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

from copy       import copy, deepcopy
import re
from time       import strftime
from types      import ListType, StringTypes, IntType, DictType

from zope.interface.declarations import implements
#
# PyHtmlGUI Imports
#
from PyHtmlGUI                       import hg

from PyHtmlGUI.kernel.hgTable        import hgTable
from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout
from PyHtmlGUI.kernel.hgWidget       import hgWidget


from PyHtmlGUI.widgets.hgLabel       import hgLabel,   \
                                            hgNEWLINE, \
                                            hgProperty

from PyHtmlGUI.widgets.hgLineEdit    import hgLineEdit
from PyHtmlGUI.widgets.hgTextEdit    import hgTextEdit
from PyHtmlGUI.widgets.hgCheckBox    import hgCheckBox
from PyHtmlGUI.widgets.hgGroupBox    import hgGroupBox
from PyHtmlGUI.widgets.hgDateEdit    import hgDateEdit
from PyHtmlGUI.widgets.hgHBox        import hgHBox
from PyHtmlGUI.widgets.hgVBox        import hgVBox
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton

#
# ZMOM Imports
#
from zopra.core                      import HTML, ClassSecurityInfo, viewPermission, modifyPermission, ZM_SCM, ZM_CM, ZM_PM, ZM_IM
from zopra.core.ImportHandler        import ImportHandler

from zopra.core.constants            import TCN_DATE, \
                                            TCN_EDATE,      \
                                            TCN_EDITOR,     \
                                            TCN_OWNER

from zopra.core.CorePart             import MASK_REDIT,     \
                                            ZCOL_DATE,      \
                                            ZCOL_MEMO,      \
                                            ZCOL_SLIST,     \
                                            ZCOL_MLIST,     \
                                            ZCOL_HLIST,     \
                                            ZCOL_BOOL,      \
                                            ZCOL_INT,       \
                                            ZCOL_FLOAT,     \
                                            ZCOL_CURR,      \
                                            COL_TYPE,       \
                                            MASK_ADD,       \
                                            MASK_EDIT,      \
                                            MASK_SEARCH,    \
                                            MASK_SHOW

from zopra.core.ManagerPart                         import ManagerPart
from zopra.core.dialogs                             import getStdDialog, \
                                                           getPlainDialog
from zopra.core.elements.Buttons                    import BTN_L_UPDATE,  \
                                                           BTN_L_REFRESH, \
                                                           BTN_L_ADD,     \
                                                           BTN_L_RESET,   \
                                                           BTN_L_ADDITEM, \
                                                           BTN_L_REMOVE,  \
                                                           BTN_L_EDIT,    \
                                                           BTN_L_FILTER,  \
                                                           BTN_FRL_NEXT,  \
                                                           BTN_FRL_PREV,  \
                                                           BTN_L_CLOSE,   \
                                                           BTN_HL_SELECT, \
                                                           BTN_HL_REMOVE, \
                                                           BTN_BASKET_ADD,\
                                                           BTN_BASKET_POP,\
                                                           BTN_FREETEXT,  \
                                                           DLG_CUSTOM,    \
                                                           DLG_FUNCTION,  \
                                                           mpfAddButton,  \
                                                           getPressedButton
from zopra.core.elements.Styles.Default             import ssiDLG_LABEL
from zopra.core.security                            import SC_READ
from zopra.core.security.GUIPermission              import GUIPermission
from zopra.core.tools.managers                      import TCN_CREATOR,     \
                                                           TCN_AUTOID,      \
                                                           TCN_FILE
from zopra.core.widgets                             import dlgLabel, \
                                                           dlgActionLabel

from zopra.core.interfaces                          import IGenericManager



ZLISTS = [ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST]
GEN_LABEL = '$_l_'

# pattern for simple detection of internal links
INTERNAL_LINK_PATTERN = re.compile(r'&lt;a class=\"s[0-9]*\" href=\"http:\/\/.*?&lt;\/a&gt;')

#
# some dlg handling constants
#
DLG_NEW    = 1
DLG_SHOW   = 2
DLG_EDIT   = 3
DLG_SEARCH = 4
DLG_DELETE = 5
DLG_IMPORT = 6
DLG_LIST   = 7

DLG_TYPES = [DLG_SHOW, DLG_EDIT, DLG_NEW, DLG_DELETE, DLG_IMPORT, DLG_LIST]

# names of core dialogs
DLG_ALLIMPORT   = 'dlgImport'
DLG_ALLDELETE   = 'dlgDelete'
DLG_MULDELETE   = 'dlgMultiDelete'
DLG_TREEEDIT    = 'dlgTreeEdit'
DLG_MULTIEDIT   = 'dlgMultiEdit'

#
# some button handling constants (have to be distinct from dlg constants)
#

ACTION_SEARCH    = 'search'
ACTION_LIST      = 'list'
ACTION_CREATE    = 'create'
ACTION_IMPORT    = 'import'
ACTION_EXPORT    = 'export'
ACTION_SHOW_NEXT = 'shownext'
ACTION_SHOW_PREV = 'showprev'
ACTION_INFO      = 'info'
ACTION_DBADD     = 'dbadd'
ACTION_SHOW      = 'show'
ACTION_EDIT      = 'edit'


class GenericManager(ManagerPart):
    """ Generic Manager """
#
# Class Properties
#
    _className = 'GenericManager'
    _classType = ManagerPart._classType + [_className]
    meta_type  = _className

    implements(IGenericManager)

    basket_active = False

    """ usage: _generic_config = {table: {key:value}}
        keys: basket_to     (True / False) - for showForm/showList-BasketButton
              basket_from   (True / False) - for newForm-BasketButton
              basket_active (True / False) - show basket at all
              visible       (True / False) - visible in zopra_manager_main_form
              show_fields   ([attrs])      - attributes for showList
              required      ([attrs])      - required attributes for new/edit
              importable    (True / False) - show in importForm for Import
        access via getGenericConfig(table)
    """
    _generic_config = {}

    # lookup map for dlg handling for basic operations through dialogs
    # _dlg_map = { table: { DLG_NEW:    'dlgNewTable',
    #                      DLG_SHOW:   'dlgShowTable',
    #                      DLG_EDIT:   'dlgEditTable',
    #                      DLG_SEARCH: 'dlgSearchTable',
    #                      DLG_DELETE: 'dlgDeleteTable',
    #                      DLG_IMPORT: None }
    #           }
    #

    _dlg_map = { }

    ACTION_DICT = { ACTION_SEARCH:      ManagerPart.IMG_SEARCH,
                    ACTION_LIST:        ManagerPart.IMG_LIST,
                    ACTION_CREATE:      ManagerPart.IMG_CREATE,
                    ACTION_IMPORT:      ManagerPart.IMG_IMPORT,
                    ACTION_EXPORT:      ManagerPart.IMG_EXPORT,
                    ACTION_DBADD:       ManagerPart.IMG_DBADD,
                    ACTION_INFO:        ManagerPart.IMG_INFO,
                    ACTION_SHOW_NEXT:   ManagerPart.IMG_SHOW_NEXT,
                    ACTION_SHOW_PREV:   ManagerPart.IMG_SHOW_PREV,
                    ACTION_EDIT:        ManagerPart.IMG_EDIT,
                    ACTION_SHOW:        ManagerPart.IMG_SHOW,
                    DLG_NEW:            ManagerPart.IMG_CREATE,
                    DLG_SEARCH:         ManagerPart.IMG_SEARCH,
                    DLG_IMPORT:         ManagerPart.IMG_IMPORT,
                    DLG_LIST:           ManagerPart.IMG_LIST,
                    DLG_SHOW:           ManagerPart.IMG_INFO }

    # for now, multiedit dialog is added in each manager that uses it
    # adding it generally could lead to security holes
    # _dlgs      = ZMOMManagerPart._dlgs + (('dlgMultiEdit',  ''),)

#
# Security
#
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__( self,
                  title     = '',
                  id        = None,
                  nocreate  = 0,
                  zopratype = ''):
        ManagerPart.__init__( self,     title,     id,
                                  nocreate, zopratype )

        # overwritable attributes to control generic behavior

        # disable basket
        # DEPRECATED
        self.basket_active = False


    def getGenericConfig(self, table):
        """\brief Retrieve the generic config for the table"""
        return self._generic_config.get(table, {})


    def getConfigShowFields(self, table):
        """\brief Retrieve the show_fields option from the generic config for the table
                  if it exists, otherwise return a list of the names of all visible columns"""
        conf = self.getGenericConfig(table)
        fields = conf.get('show_fields')
        if not fields:
            fields = self.tableHandler[table].getColumnDefs().keys()
        return fields


    def doesTranslations(self, table):
        """\brief Translation indicator, should be overwritten to return True for tables that handle translations.
            The translation handling is still not incorporated in the ZMOM Core."""
        return False


    def doesWorkingCopies(self, table):
        """\brief working copy indicator, should be overwritten to return True for tables that handle working copies.
            The working copy handling is still not incorporated in the ZMOM Core."""
        return False

##########################################################
# Manager Part Virtual functions                         #
#   - overwritten here to have a collection in one place #
#   some do some default handling or at least return     #
##########################################################

    def _addTable(self):
        """\brief Virtual function for extra table magic on add."""
        pass


    def _delTable(self):
        """\brief Virtual function for extra table magic on delete."""
        pass


    def _index_html(self, REQUEST, parent = None, border = True):
        """\brief Virtual function for manager main entrance html view.
                Returns a widget to be dislpayed on the main screen.
                Not overwriting it results in a generic overview (that
                might be enough for small standard managers)."""
        return self._index_html_generic(REQUEST, parent, border)


    def setDebugOutput(self):
        """\brief Virtual function for manager specific debug output.
                    Overwrite this function to return additional info for the
                    view manage-tab as html text"""
        return ''


    def contextMenuCustom(self, REQUEST, parent):
        """\brief Virtual function for manager specific context menu.
                    Overwrite this function to create a widget with context menu info
                    using parent as the widget-parent. Return the widget."""
        return None


    def navigationMenuCustom(self, menubar, REQUEST):
        """\brief Function for customizable part of navigation.
                    Overwrite this function to add navigation items to the menubar.
                    Return True to indicate that something was added."""
        return None


    def prepareEntryBeforeShowList(self, table, dict, REQUEST):
        """\brief Hook function called by getTableEntryListHtml to preprocess each entry.
                    Overwrite this function to process each single entry before it is
                    displayed row-wise by getTableEntryListHtml. This can be useful to
                    substitute id's with labels / links in cases where singlelists are
                    not possible and the 'static' way using param[links] in
                    actionBeforeShowList is not wanted."""
        pass


#############################################
# Generic Manager Hook Functions            #
#   - to be overwritten for custom handling #
#   they do nothing on their own!           #
#############################################

    def prepareDict(self, table, descr_dict, REQUEST = None):
        """\brief Hook Function called before edit and add
                    In contrary to actionBeforeAdd and actionBeforeEdit,
                    this hook gets called everytime that a button was pressed on the
                    edit and add forms. It can be used for verification and preview.
                    When the real edit or add happens, prepareDict gets called first.
                    Overwriting the hook: return values will be ignored.
                    The REQUEST can be used to obtain non-standard form
                    values (the standard table attribute values are already in descr_dict)."""
        pass


    def actionBeforeAdd(self, table, descr_dict, REQUEST):
        """\brief Hook Function called before add
                    This function can be used to adjust the to-be-saved entry
                    before it gets added to the database. It does not have an autoid yet.
                    For custom handling that needs an autoid, use actionAfterAdd.
                    Overwriting the hook: make sure to return nothing or a message to be displayed.
                    The REQUEST can be used to obtain non-standard form
                    values (the standard table attribute values are already in descr_dict)."""
        # expected to return None or message string about operations
        # performed (usually only in case of errors)
        return None


    def actionBeforeEdit(self, table, descr_dict, REQUEST):
        """\brief Hook Function called before edit
                    This function can be used to adjust the entry before it gets saved
                    or to adjust dependent entries. Since the entry already exists, you find
                    it's autoid in the descr_dict. 
                    Overwriting the hook: make sure to return nothing or a message to be displayed.
                    The REQUEST can be used to obtain non-standard form
                    values (the standard table attribute values are already in descr_dict)."""
        # expected to return None or message string about operations
        # performed (usually only in case of errors)
        return None


    def actionAfterAdd(self, table, descr_dict, REQUEST):
        """\brief Hook Function called after adding an entry to the database
                    This function can be used to create dependent entries or adjust the new entry.
                    For custom changes that do not need an autoid, use actionBeforeAdd. 
                    The descr_dict contains the newly assigned autoid of the new entry.
                    Overwriting the hook: make sure to return nothing or a message to be displayed.
                    The REQUEST can be used to obtain non-standard form
                    values (the standard table attribute values are already in descr_dict)."""
        # expected to return None or message string about operations
        # performed (usually only in case of errors)
        return None


    def actionBeforeSearch(self, table, REQUEST, descr_dict, firstSearch = True, prefix = ''):
        """\brief Hook Function called by searchForm and showList.
                This hook is invoked on first search by searchForm and later on 
                by showList after its searchForm handling.
                Use it to determine if a custom searchForm button was pressed and
                perform custom search - related handling, that needs
                to be done before displaying the search Form.
                Return a dictionary to indicate that showList should call searchForm
                with this dictionary.
                Otherwise, the normal showList handling is done, using getTableEntryListHtml,
                unless some of the standard searchForm-Buttons are evaluated.
            \param firstSearch is False when this call is done by showList, 
                meaning that the searchForm was submitted.
            \param prefix is given for multi-table search requests
                If your searchForms only apply to one table each, you can ignore it,
                otherwise it indicates which values of the REQUEST are relevant on each call
                (since they should be prefixed accordingly)
        """
        return None


    def actionBeforeShowList(self, table, param, REQUEST):
        """\brief Hook Function called before listing-relevant showList Handling
           \param param is a dict which can be filled with default flags
                        changing the showList behaviour.
                        Non-present keys will be filled in by showList with own default values.
                    Available keys for param-dict:
                    with_edit: True or False
                    with_show: True or False
                    with_delete: True or False
                    with_basket: True or False
                    with_autoid_navig: True or False
                    show_fields: [fieldlist]
                    constraints: additional constraints {key:value}
                    links: {name: link_dict} (additional link for each entry in the
                                            following format)
                        { link: url_base (leave out for label instead link),
                           field:<attr> (for url_addition / display),
                           check:<func_name> (for calcs/checks,
                                             returns new id or label)
                         }
                    special_field: name of the main attribute (used for col 1 and initial ordering)
        """
        pass


    def startupConfig(self, REQUEST):
        """\brief Hook Function called after first creation by manageAddGeneric
                    This function can be used to create standard entries for noneditable lists, 
                    it is only called if the database tables were created, not on reinstallation.
                    So it should not be used to configure the manager, just the database."""
        pass


    def installConfig(self, REQUEST):
        """\brief Hook Function called after creation by manageAddZMOMGeneric on each install.
            Use it to get dtml-form values from REQUEST.
            For database action (only on first install) see startupConfig Hook"""
        pass


    def prepareDelete(self, table, id, REQUEST):
        """\brief Hook Function called before delete
                    This function is for cleaning up the database where custom cleaning is necessary.
                    Entries that depend on the to-be-deleted entry have
                    to be adjusted here. REQUEST might be None (parameter added later on).
                    To indicate an error, return an error message (preferrably) or raise an error.
        """
        return None


    def hook_buttonForwardForm(self, table, action, REQUEST):
        """\brief Function Stub for manual button handling for forwards to
            achieve link-like function"""
        # we got forwarded here but didn't find anything
        msg = 'hook_buttonForwardForm (Table: %s, Action: %s) was '
        msg += 'used without being overwritten in %s'
        msg = msg % (table, action, self._className)
        error = self.renderError(msg, 'Button Error')
        raise ValueError(self.getErrorDialog(error))


############################################
# Generic Manager generic basic functions  #
#   - providing basic handling for entries #
#   Overwrite them with caution            #
############################################

    security.declareProtected(modifyPermission, 'deleteEntries')
    def deleteEntries( self,
                       table,
                       idlist,
                       REQUEST = None ):
        # Entry deletion, make sure to call superclass if overwritten.
        #            Does the calling of the prepareDelete hook and forwards 
        #            to ZMOMTable.deleteEntries.
        if table not in self.tableHandler:
            return

        if not idlist:
            return

        if not isinstance(idlist, ListType):
            idlist = [idlist]

        # make sure we properly handle the delete operation
        for oneid in idlist:
            msg = self.prepareDelete(table, oneid, REQUEST)
            if msg and msg is not True:
                return msg

        self.tableHandler[table].deleteEntries(idlist)
        return True


    def getEntry(self, table, autoid, lang = None):
        """\brief calls tableHandlers getEntry, overwrite for special functionality."""
        if autoid and table and table in self.tableHandler:
            try:
                autoid = int(autoid)
            except:
                errstr = 'Generic Manager Autoid Problem: %s' % autoid
                err    = self.getErrorDialog(errstr)
                raise ValueError(err)
            tobj = self.tableHandler[table]
            entry = tobj.getEntry(autoid)
            if entry:
                if self.doesTranslations(table) and lang:
                    if entry['language'] != lang:
                        cons = {'istranslationof': autoid,
                                'language': lang}
                        entries = tobj.getEntryList(constraints = cons)
                        if entries:
                            entry = entries[0]
                return entry
        return {}


    def getSearchPattern(self, table):
        """\brief called before REQUEST is analysed by showList
                    This function is used to define how the generic search mask
                    will look like. While all other masks are simple single
                    masks showing one entry of one table (in the generic case),
                    a generic search mask can consist of masks for different
                    tables of different managers. Each row in the list that is returned
                    is a tuple (manager-className, tablename, prefix).
                    The search tree template produced by generateTableSearchTreeTemplate
                    should match the tables and prefixes used here so the values entered into
                    the masks will be matched correctly.
           \return a list of tuples looking like that: (manager, table, prefix)"""
        return [(self._className, table, '')]


    def generateTableSearchTreeTemplate(self, table):
        """\brief Virtual function for manager specific searchTree called by ZMOMTable.getSearchTreeTemplate.
                    The standard search tree is just the corresponding
                    TableNode for the table. This function forwards to the
                    overwritten version in ZMOMManagerPart which returns
                    the ZMOMTableNode. Overwrite it to produce a custom
                    search tree and return the root node. To get the template for custom searches,
                    use ZMOMTable.getSearchTreeTemplate (caching is done there)."""
        return ManagerPart.generateTableSearchTreeTemplate(self, table)


    def basketAdd(self, table, descr_dict, REQUEST):
        """\brief Hook function called by showList / showForm, adds entry to the basket.
                  Standard implementation uses getLabelString for basket-label."""
        # label = self.getLabelString(table, None, descr_dict)
        return self.basket.addEntryToBasket( REQUEST.SESSION,
                                             self,
                                             table,
                                             descr_dict[TCN_AUTOID],
                                             descr_dict )


    def basketMoveFrom(self, mgr_id, table, descr_dict, REQUEST):
        """\brief Hook function called by NewForm (on click). Move top entry from basket.
                  Standard implementation copies all attributes with same name."""
        # NOTE: for new basket we need to specify mgr and table
        session = REQUEST.SESSION
        entry   = self.basket.popFirstActiveEntryFromBasket(session, mgr_id, table, True)
        # standard behaviour: get empty entry, move all values with same name
        cols = self.tableHandler[table].getColumnTypes().keys()
        for key in cols:
            if key in entry:
                descr_dict[key] = copy(entry[key])


    def getLabelString(self, table, autoid = None, descr_dict = None):
        """\brief Return label for entry, overwrite for special functionality."""
        # return autoid, no matter what table
        if descr_dict:
            autoid = descr_dict.get(TCN_AUTOID, '')
        elif not autoid:
            return ''
        return str(autoid)


    def getLink(self, table, autoid = None, descr_dict = None, parent = None):
        """\brief Return link to that entry, overwrite for special functionality.
            Note that either autoid or descr_dict is given."""
        # parent is a widget for display
        # get autoid / descr_dict
        if descr_dict:
            autoid = descr_dict.get( TCN_AUTOID )
            ddict  = descr_dict
        elif autoid:
            ddict  = self.getEntry( table, autoid )
        else:
            return hgLabel('', parent = parent)
        # get label and base url
        label = self.getLabelString( table, None, ddict )
        base  = self.absolute_url()
        # build link
        link = '%s/showForm?table=%s&id=%s' % (base, table, autoid)

        # return a widget
        if label:
            return hgLabel(label, link, parent = parent)
        else:
            return hgLabel('', parent = parent)


    # NOTE: give desired max number of strings
    #       give start, stop number
    #       return total number, and found ids
    # NOTE: now used for improved getAutoidByValue in ZMOMForeignList
    #       list object must have set option labelsearch == True to use this function
    def searchLabelStrings(self, table, search, start = 0, show = -1, tolerance = 0):
        """\brief Returns autoid list whose labels match search.
                    Search should cover wildcards *, ?
                    Generic search calls prepare_labelstringsearch hook, which uses
                    _generic_config->labelsearchfields. For own search functionality,
                    overwrite prepare_labelstringsearch"""

        if show is None:
            show = -1

        if start is None:
            start = 0

        if table not in self.tableHandler:
            return None

        if search:
            search = search.replace('*', '%')
            search = search.replace('?', '_')

        # use the tablenode to search for labelstrings
        # we use the complete template because an overwritten prepare-function could return constraints for subtables
        root = self.tableHandler[table].getSearchTreeTemplate()

        # now we need the column or columns to search, this is done via hook
        # root-fiddling is done in there
        self.prepare_labelstringsearch(table, search, root)

        # get row count right away to provide value for BTN_L_LAST
        func = 'count(distinct %sautoid)'

        total = self.getManager(ZM_PM).\
                         executeDBQuery( root.getSQL(function = func, checker = self)
                                            )[0][0]

        if show > -1 and tolerance > 0 and show + tolerance >= total:
            show += tolerance

        if show == 0:
            return ([], total)

        # unlimited
        if show == -1:
            show = None

        if start == 0:
            start = None

        # FIXME: why is distinct False? this could generate a lot of double autoid entries
        # which are filtered then into a distinct list. can't remember why. maybe due to ordering
        sql = root.getSQL(show, start, distinct = False, checker = self)
        cache = self.tableHandler[table].cache
        autoidlist = deepcopy(cache.getItem(cache.IDLIST, sql))

        if not autoidlist:
            autoidlist = []
            results = self.getManager(ZM_PM).\
                            executeDBQuery( sql )

            # this is done to have distinct values but intact order
            tmp_dict = {}
            for result in results:
                autoid = int(result[0])
                if autoid not in tmp_dict:
                    tmp_dict[autoid] = None
                    autoidlist.append(autoid)
            # caching (need to check if the int values could harm anything)
            cache.insertItem( cache.IDLIST,
                                sql,
                                autoidlist )

        return (autoidlist, total)


    def prepare_labelstringsearch(self, table, searchterm, root):
        """\brief Basic Generic Function, overwrite for special functionality.
                Implementation builds constraints and order for search and puts them
                into the TableNode named root for the searchLabelStrings function to use.
                The information is taken from _generic_config with key 'labelsearchfields'
                """
        # default behaviour is to look into _generic_config for a main column
        fields = self._generic_config.get(table, {}).get('labelsearchfields', [])

        cons = {}
        # empty searchterm returns everything -> no cons
        if searchterm:
            for field in fields:
                # for now, use searchterm for each field
                cons[field] = '*' + searchterm + '*'

        if fields:
            order = fields
        else:
            order = TCN_AUTOID

        # multiple fields each have the same searchterm in the constraints
        # for multifield, we need to either break the term apart or simply build a filter for or-search
        # the latter is done for now
        root.setConstraints(cons)
        if len(cons.keys()) > 1:
            root.filterTree.setOperator(root.filterTree.OR)
        if order:
            root.setOrder(order)


    def getAttributeEditPermissions(self, table):
        """\brief Return List of editable attributes for current user (used by multiedit)
                    Overwrite to specify which permission is needed to edit which attributes.
                    The dlgMultiEdit uses this function to determine which attributes to
                    display in edit-mode and which not."""
        # get current userlevel
        m_security = self.getHierarchyUpManager(ZM_SCM)
        tobj = self.tableHandler[table]
        if not m_security:
            return tobj.getColumnTypes(True).keys()
        # get level
        level = m_security.getCurrentLevel()
        # < 6 don't edit
        if level < 6:
            return []
        # normal attributes available for everybody
        elif level < 20:
            return tobj.getColumnTypes(True).keys()
        # admins edit all
        else:
            attrs = tobj.getColumnTypes().keys()
            m_product = self.getManager(ZM_PM)
            for column in m_product._edit_tracking_cols:
                if column not in attrs:
                    attrs.append(column)
            return attrs


    def getRequiredFields(self, table):
        """\brief Get the required attributes for the table"""

        if table not in self.tableHandler:
            self.displayError('Table \'%s\' does not exist in %s' % (table, self.getTitle()),
                              'Internal Error.')

        required = []

        # simple managers do not need a _generic_config, so check for existence
        if self._generic_config.get(table):
            if self._generic_config[table].get('required'):
                required = self._generic_config[table]['required']

        return required


    def checkRequiredFields(self, table, dict):
        """\brief Checks required attributes in dict to be accepted by table"""

        if table not in self.tableHandler:
            self.displayError('Table \'%s\' does not exist in %s' % (table, self.getTitle()),
                              'Internal Error.')

        if dict is None or not isinstance(dict, DictType):
            dict = {}

        missing  = []
        required = self.getRequiredFields(table)

        for field in required:
            # field is not in entry_dict and no multilist
            if not dict.get(field):
                missing.append( field )
            elif dict.get(field) == 'NULL':
                if self.listHandler.hasList(table, field):
                    missing.append( field )

        return missing


    def handleFreeText(self, table, REQUEST, ddict, prefix = None):
        """\brief Check REQUEST for freetext keys (with prefix),
                  resolve and put into ddict."""
        if not prefix:
            prefix = ''
        start = prefix + 'freetext'
        # test all keys in REQUEST
        for key in REQUEST.form.keys():
            if key[:len(start)] == start:
                # try to find the list
                lname = key[len(start):]
                lobj = self.listHandler.getList(table, lname)
                if lobj:
                    cons = lobj.getAutoidsByFreeText(REQUEST[key])
                    # test for list:
                    if lobj.listtype in ['multilist', 'hierarchylist']:
                        old = ddict.get(lname)
                        if not old:
                            old = []
                        if not isinstance(old, ListType):
                            old = [old]
                        for entry in cons:
                            if entry and not str(entry) in old:
                                old.append(entry)
                        old.sort()
                        ddict[lname] = old
                    elif lobj.listtype == 'singlelist':
                        # problem with single lists (can't select more than 1)
                        if len(cons) > 1:
                            errs = 'Too many freetext results'
                            err  = self.getErrorDialog(errs)
                            raise ValueError(err)
                        else:
                            ddict[lname] = cons[0]


    def getDialogName(self, table, dlg_type):
        """\brief Returns dlg identifier for requested table and dlg type
            Specify table and operation to get the dialog name. Checks
            _dlg_map for the table and type.
            Returns None if no dialogname was found.
        """
        if table in self._dlg_map:
            if dlg_type in self._dlg_map[table]:
                return self._dlg_map[table][dlg_type]

        return None


###########################################################
# Generic Form Handling                                   #
#   - providing generic form functions and their handling #
#   normally not needed to be overwritten                 #
###########################################################

    security.declareProtected(viewPermission, '_index_html_generic')
    def _index_html_generic(self, REQUEST = None, parent = None, border = True):
        """\brief Returns the generic part for the index_html."""
        perm = self.getGUIPermission()

        # use groupboxes in a widget

        table_names = self.tableHandler
        table_names.sort()

        # we need a form but without dlg-caption and other stuff
        dlg, mask = getPlainDialog(self.absolute_url() + '/buttonForwardForm', parent, border)
        lay = mask.layout()

        anysuper = False
        anyperm = False
        row = 0
        col = 0
        for table in table_names:
            # create mask for one table
            tabmask, super, hasperm = self.createOverviewBox(table, perm, mask)

            # store superuser / permission info
            anysuper = super or anysuper
            anyperm  = hasperm or anyperm

            # add table mask to layout
            lay.addWidget(tabmask, row, col)

            # row/col - handling
            col += 1
            if not col % 2:
                # 3rd col, next table goes to next row
                col = 0
                row += 1

        if not anyperm:
            return self.unauthorizedHtml(perm.SC_VIEW)

        # Import / Export for superusers only
        if table_names and anysuper:
            mgmt = hgGroupBox(2, hg.Vertical, 'Management', mask)
            mgmt.margin = 0
            lay.addWidget(mgmt, row, col)
            # import (table isn't used but necessary for button handling
            self.getStandardActionButton(table, ACTION_IMPORT, mgmt)
            self.getStandardActionButton(table, ACTION_EXPORT, mgmt)

            # correct the spacing of all layouts
            iter = mgmt.layout().iterator()
            mgmt.setMargin(0)
            while iter.next():
                laytmp = iter.current()
                laytmp.setSpacing(1)
                iter2 = laytmp.iterator()
                while iter2.next():
                    iter2.current().setAlignment(hg.AlignHCenter)

        return dlg


    security.declareProtected(viewPermission, 'createOverviewBox')
    def createOverviewBox(self, table, perm, parent):
        """\brief Creates the generic index_html-buttonbox for a table"""
        ztype = self.getZopraType()
        tobj    = self.tableHandler[table]
        tabid   = tobj.getUId()
        super = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        super = super or perm.hasSpecialRole(ztype + 'Superuser')
        hasperm = False
        label   = tobj.getLabel()
        if not label:
            label = table

        # build one submask
        tabmask = hgGroupBox(2, hg.Vertical, label, parent)
        tabmask.margin = 0

        if perm.hasPermission(perm.SC_INSERT, tabid, ztype) or super:
            # create entry (button and label created by getStandardActionButton)
            self.getStandardActionButton(table, ACTION_CREATE, tabmask)
            hasperm = True

        if perm.hasPermission(perm.SC_VIEW, tabid, ztype) or super:
            # search entries
            self.getStandardActionButton(table, ACTION_SEARCH, tabmask)

            # list entries
            self.getStandardActionButton(table, ACTION_LIST, tabmask)
            hasperm = True

        if not hasperm:
            hgLabel( 'No access.', parent = tabmask)

        # correct the spacing of all layouts
        iter = tabmask.layout().iterator()
        tabmask.setMargin(0)
        while iter.next():
            laytmp = iter.current()
            laytmp.setSpacing(1)
            iter2 = laytmp.iterator()
            while iter2.next():
                iter2.current().setAlignment(hg.AlignHCenter)

        return tabmask, super, hasperm


    security.declareProtected(viewPermission, 'buttonForwardForm')
    def buttonForwardForm(self, REQUEST):
        """\brief Function that receives the form of the index_html of a manager,
            when a button is pressed."""
        # the product-overview pages might have different forms forwarding button-actions 
        # to this function in the respective manager
        # we do some generic handling here and then call the hook_buttonForwardForm function
        # for managerspecific additional handling
        # manager is always self, table is part of the button name
        # action is part of the button name
        # DLG_FUNCTION + <table> + '_' + <action>
        table = None
        action = None

        # get the pressed button
        blist = getPressedButton(REQUEST)
        # found double buttons sometimes
        if blist:
            bname = blist[0]
            pos = bname.find('_')
            if pos != -1:
                table = bname[:pos]
                action = bname[pos + 1:]

        if table and action:
            # remove the button from REQUEST.form
            del REQUEST.form[DLG_FUNCTION + bname]
            # test dialog buttons
            if action.isdigit():
                dlg_type = int(action)
                name = self.getDialogName(table, dlg_type)
                # call the dialog to return the first page
                dlg = getattr(self.dlgHandler, name)
                return dlg.show(REQUEST)

            # search, list, create actions lead to generic forms
            if action == ACTION_SEARCH:
                return self.searchForm(table, None, REQUEST)
            elif action == ACTION_LIST:
                return self.showList(table, REQUEST)
            elif action == ACTION_CREATE:
                return self.newForm(table, REQUEST)
            elif action == ACTION_IMPORT:
                return self.importForm(REQUEST)
            elif action == ACTION_EXPORT:
                return self.exportForm(REQUEST, REQUEST.RESPONSE)
            # maybe not here
            #elif action == ACTION_SHOW_NEXT:
            #    # get id, get autos, get next id
            #    id = None
            #    auto = []
            #    return self.showForm(id, table, REQUEST, auto)
            #elif action == ACTION_SHOW_PREVIOUS:
            #    # get id, get autos, get prev id
            #    id = None
            #    auto = []
            #    return self.showForm(id, table, REQUEST, auto)
            else:
                return self.hook_buttonForwardForm(table, action, REQUEST)

        # we got until here but didn't find anything
        msg = 'ButtonForwardForm was used without a button pressed.'
        error = self.renderError(msg, 'Button Error')
        raise ValueError(self.getErrorDialog(error))


    def getStandardActionButton(self, table, action, parent, with_text = True, label = ''):
        """\brief create an image button for that action for a table, if with_text is True, returns (button, label)"""
        button = hgPushButton(str(action), DLG_FUNCTION + table + '_' + str(action), parent = parent)

        # addWidget(button, alignment=hg.AlignCenter)
        if action in self.ACTION_DICT:
            # get the image type
            img_type = self.ACTION_DICT[action]
            # set the image
            try:
                button.setIcon( self.iconHandler.get(img_type, path = True).getIconDict() )
            except:
                raise ValueError('No icon found for %s with table %s and action %s' % (img_type, table, action))
            # give the button a slightly darker background ... or a frame?
            button.setPaletteBackgroundColor('#A9A9A9')

            if img_type in self.TOOLTIP_DICT:
                tip = self.TOOLTIP_DICT[img_type]
                if tip.find('%s') != -1:
                    # add table label to text
                    tabLab = self.tableHandler[table].getLabel()
                    tip = tip % (tabLab)
                button.setToolTip( tip)
        if with_text:
            # use action as label for standard functions, label for dialogs, nothing if no label is given
            if not label:
                if type(action) != int:
                    label = action
            text = dlgActionLabel(label, parent = parent)
            return (button, text)
        else:
            return button


    security.declareProtected(modifyPermission, 'genericFileDelete')
    def genericFileDelete(self, table, idlist):
        # Generic File Deletion (called on entry deletion).
        m_image = self.getHierarchyUpManager(ZM_IM)
        if m_image:
            attrs = []

            # get all lists of table that reference ZM_IM
            tablelists = self.listHandler.getLists(table, types = [], include = False)
            for lobj in tablelists:
                if lobj.manager == ZM_IM:
                    attrs.append(lobj.listname)

            if attrs:

                # list building
                for entryid in idlist:
                    entry = self.getEntry(table, entryid)
                    for attr in attrs:
                        if entry.get(attr):
                            m_image.delImage(entry.get(attr))


    security.declareProtected(viewPermission, 'getGenericFileMask')
    def getGenericFileMask( self,
                            flag,
                            descr_dict,
                            table,
                            name    = TCN_FILE,
                            delname = 'del',
                            addname = 'add',
                            prefix  = None,
                            parent  = None
                            ):
        """\brief Returns a tuple containing a label and the mask for
                  the given file attribute."""
        mask = None

        if not prefix:
            prefix = ''
        m_image = self.getHierarchyUpManager(ZM_IM)
        if m_image:
            filelist = self.listHandler.getList(table, name)

            # mask is a widget with grid layout
            mask = hgWidget(parent = parent, name = prefix + name)
            layout = hgGridLayout(mask, 0, 0, 0, 2)
            row = 0
            if flag & (MASK_SHOW | MASK_EDIT):
                # show imagelink
                files = descr_dict.get(name)
                if files:

                    if flag & MASK_EDIT:
                        lab = hgLabel('Check for Deletion', parent = mask)
                        layout.addMultiCellWidget(lab, row, row, 0, 2)
                        row += 1

                    if not isinstance(files, ListType):
                        files = [files]

                    flist = filelist.getValueByAutoid(files)
                    for index, entry in enumerate(flist):
                        if entry:
                            if flag & MASK_EDIT:
                                #deletion checkbox
                                cname   = delname + prefix + name
                                # preparation for value-less checkboxes
                                # needs adaption in editForm to find image lists
                                # + '_' + str(files[index])
                                check = hgCheckBox( name  = cname,
                                                    value = str(files[index]),
                                                    parent = mask )
                                layout.addWidget(check, row, 0)
                            entry.reparent(mask)
                            layout.addWidget( entry, row, 1)
                            # edit tests for empty multilists
                            # to retain id's, we use properties
                            if flag & (MASK_EDIT | MASK_ADD):
                                prop = hgProperty( prefix + name,
                                                   files[index],
                                                   parent = mask )
                                layout.addWidget(prop, row, 2)
                            row += 1
                else:
                    if filelist.listtype == 'singlelist':
                        lab = hgLabel('No Entry', parent = mask)
                    else:
                        lab = hgLabel('No Entries', parent = mask)
                    layout.addWidget(lab, row, 0)
                    row += 1

            #show image add dialog only for multilists or if no image is given
            if ((flag & MASK_EDIT) and \
                (not descr_dict.get(name) or filelist.listtype == 'multilist')) \
                or (flag & MASK_ADD):

                label = '<input type="file" name="%s%s%s">'
                label = label % (addname, prefix, name)
                lab   = hgLabel(label, parent = mask)
                layout.addMultiCellWidget(lab, row, row, 0, 2)

        return mask


    security.declareProtected(modifyPermission, 'delFileGeneric')
    def delFileGeneric( self,
                        REQUEST,
                        delname = 'del',
                        name = TCN_FILE,
                        descr_dict = None,
                        prefix = None ):
        """\brief Manual deletion of file or image."""
        if not prefix:
            pre = ''
        else:
            pre = prefix
        if not descr_dict:
            descr_dict = {}
        image = descr_dict.get(name)
        m_image = self.getHierarchyUpManager(ZM_IM)
        done = False
        if m_image:
            #autoids = []
            key     = delname + pre + name
            # preparation for value-less checkboxes
            #for entry in REQUEST.form:
            #     if entry[:len(key)] == key:
            #         autoids.append(int(entry[len(key)+1:]))

            # normal checkbox-value handling
            autoids = REQUEST.get(key)
            if autoids:
                if not isinstance(autoids, ListType):
                    autoids = [autoids]

                # deletion

                for autoid in autoids:
                    m_image.delImage(autoid)
                    # correct the ddict image values (remove deleted)
                    if isinstance(image, ListType):
                        if int(autoid) in image:
                            image.remove(int(autoid))
                        elif str(autoid) in image:
                            image.remove(str(autoid))
                    else:
                        image = None
                    done = True
                descr_dict[name] = image
        return done


    security.declareProtected(modifyPermission, 'addFileGeneric')
    def addFileGeneric( self,
                        REQUEST,
                        addname = 'add',
                        name = TCN_FILE,
                        descr_dict = None,
                        filetype = 'file',
                        prefix = None ):
        """\brief Adds file, returns new dict with updated image attribute."""
        if not prefix:
            pre = ''
        else:
            pre = prefix
        if not descr_dict:
            descr_dict = {}
        image = descr_dict.get(name)
        m_image = self.getHierarchyUpManager(ZM_IM)
        file = REQUEST.get(addname + pre + name)
        done = False
        if m_image and file:
            #add image
            imgid = m_image.insertImage( file,
                                         None,
                                         '',
                                         '',
                                         False,
                                         filetype )
            if isinstance(image, ListType):
                # TODO: why this test???
                if not imgid in image:
                    image.append(imgid)
            else:
                image = imgid
            descr_dict[name] = image
            done = True
        return done


    security.declareProtected(viewPermission, 'infoForm')
    def infoForm(self, table, id, REQUEST):
        """\brief Returns html of the generic entry info page."""
        # get GUI permission
        perm = self.getGUIPermission()
        ztype = self.getZopraType()
        # get table object
        tobj = self.tableHandler[table]
        tabid = tobj.getUId()

        # check permission
        if not perm.hasPermission(perm.SC_VIEW, tabid, ztype):
            return self.unauthorizedHtml(perm.SC_VIEW)

        # get entry
        entry = self.getEntry(table, id)
        # test entry permission
        if not entry['permission'].hasPermission(SC_READ):
            return self.nopermissionHtml(SC_READ)
        # test owner
        isowner = entry['permission'].isOwner()
        if not isowner:
            # test superuser
            isowner = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)

        # header labels
        elabel = self.getLabelString(table, None, entry)
        tlabel = tobj.getLabel()
        if not tlabel:
            tlabel = table
        heading = '%s Info Page for %s' % (tlabel, elabel)
        url = '%s/showForm' % self.absolute_url()

        # build dialog
        dlg = getStdDialog(heading, url)

        # build mask 
        # NOTE: tracking col lists can not be resolved 
        #       by buildSemiGenericMask with new listHandler
        #       ()
        # TODO: fix it
        tmp = [ [GEN_LABEL + TCN_CREATOR, TCN_CREATOR],
                [GEN_LABEL + TCN_DATE,    TCN_DATE   ],
                [GEN_LABEL + TCN_EDITOR,  TCN_EDITOR ],
                [GEN_LABEL + TCN_EDATE,   TCN_EDATE  ],
                [GEN_LABEL + TCN_OWNER,   TCN_OWNER  ]]

        mask = self.buildSemiGenericMask( table,
                                          tmp,
                                          MASK_SHOW,
                                          entry,
                                          parent = dlg )
                
        layout = mask.layout()

        # owner is true for owner and superusers
        if isowner:
            # TODO: owner change for superusers
            # add owner change selection and button for owner/superuser
            pass
        
        if perm.hasRole(perm.SC_USER, tabid, ztype):
            # add a "takeownership" button for users
            # only if the owner is no user anymore or a visitor
            # get owner info, get group
            ownerid = entry.get(TCN_OWNER)
            m_sec = self.getHierarchyUpManager(ZM_SCM)
            if m_sec:
                lettake = False
                if not ownerid:
                    lettake = True
                else:
                    ownerobj = m_sec.getUserByCMId(ownerid)
                    # how to do this with new handling and not using getCurrentLevel(login)?
            # TODO: implement

        row = 6
        # permissions (per user / group)
        if self.checkEBaSe(table):
            label = dlgLabel('Permissions', mask)
            layout.addMultiCellWidget(label, row, row, 0, 2)
            row += 1
            m_sec = self.getHierarchyUpManager(ZM_SCM)
            acl = entry['acl']
            groups, users = m_sec.unfoldEBaSe(acl)
            # build permission mask
            mask1 = m_sec.getEBaSeMask(users, True, False, mask)
            layout.addMultiCellWidget(mask1, row, row, 0, 2)
            row += 1
            mask2 = m_sec.getEBaSeMask(groups, False, False, mask)
            layout.addMultiCellWidget(mask2, row, row, 0, 2)
            row += 1
            if isowner:
                # edit permission link
                url = '%s/editPermissionForm?table=%s&id=%s'
                url = url % (self.absolute_url(), table, id)
                label = hgLabel('Edit permissions', url, mask)
                layout.addMultiCellWidget(label, row, row, 0, 2)
                row += 1
            row += 1

        # log label
        label = dlgLabel('Logged Events', mask)
        layout.addWidget(label, row, 0)
        row += 1
        # entry log
        m_prod = self.getManager(ZM_PM)
        txt = m_prod.getEntryLogBlock(tobj.getUId(), id)
        #txt = txt.replace('\n', '<br>')
        field = hgTextEdit(txt, parent = mask, flags = hgTextEdit.MULTILINE)
        field.setSize(50, 5)
        layout.addMultiCellWidget(field, row, row, 0, 2)

        # put in table and id
        autoprop = hgProperty('id', id, parent = dlg)
        dlg.add(autoprop)
        tableprop = hgProperty('table', table, parent = dlg)
        dlg.add(tableprop)
 
        # add mask
        dlg.add(mask)

        # add ok-button
        dlg.add('<center>')
        button = hgPushButton('OK', parent = dlg)
        dlg.add(button)
        dlg.add('</center>')

        # return html
        return HTML(dlg.getHtml())(self, None)


    security.declareProtected(modifyPermission, 'editPermissionForm')
    def editPermissionForm(self, table, id, REQUEST):
        """\brief permission editing"""
        # get GUI permission
        perm = self.getGUIPermission()
        # get table object
        tobj = self.tableHandler[table]
        mgrid = None
        tabid = tobj.getUId()
        ztype = self.getZopraType()

        # get entry
        entry = self.getEntry(table, id)

        # test owner
        owner = False
        m_sec = self.getHierarchyUpManager(ZM_SCM)
        if m_sec:
            login = m_sec.getCurrentLogin()
            owner = entry['permission'].isOwner()
        if not owner:
            # test superuser
            owner = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)

        # only owner / superuser can edit permissions
        if not owner:
            return self.nopermissionHtml(SC_READ)

        # check ebase
        if not self.checkEBaSe(table):
            msg = 'EBaSe not activated for table %s' % table
            raise ValueError(self.getErrorDialog(msg))

        # test buttons
        button = self.getPressedButton(REQUEST)
        remove = getPressedButton(REQUEST, 'remove_')
        if button or remove:
            # get groups / users from request
            users = {}
            groups = {}
            glist = REQUEST.get('secg')
            if glist:
                if not isinstance(glist, ListType):
                    glist = [glist]
                for group in glist:
                    perms = REQUEST.get('perm_g%s' % group)
                    padd = []
                    if perms:
                        if not isinstance(perms, ListType):
                            perms = [perms]
                        for single in perms:
                            padd.append(int(single))
                    groups[int(group)] = padd

            ulist = REQUEST.get('secu')
            if ulist:
                if not isinstance(ulist, ListType):
                    ulist = [ulist]
                for user in ulist:
                    perms = REQUEST.get('perm_u%s' % user)
                    padd = []
                    if perms:
                        if not isinstance(perms, ListType):
                            perms = [perms]
                        for single in perms:
                            padd.append(int(single))
                    users[int(user)] = padd

            # now evaluate buttons
            if button == 'sec_gadd':
                # add group
                groupid = REQUEST.get('egroup')
                if groupid != 'NULL':
                    groupid = int(groupid)
                    if groupid not in groups:
                        groups[groupid] = []
            elif button == 'sec_uadd':
                # add user
                userid = REQUEST.get('euser')
                if userid != 'NULL':
                    userid = int(userid)
                    if userid not in users:
                        users[userid] = []
            elif remove:
                remove = remove[0]
                stype = remove[0]
                theid = int(remove[1:])
                if stype == 'g':
                    # remove group
                    if theid in groups:
                        del groups[theid]
                else:
                    # remove user
                    if theid in users:
                        del users[theid]

            elif button == 'OK':
                # store acl
                acl = m_sec.foldEBaSe(groups, users)
                ddict = {'acl': acl}
                self.tableHandler[table].updateEntry(ddict, entry[TCN_AUTOID])
                # forward to info page
                return self.infoForm(table, id, REQUEST)
        else:
            # first call
            acl = entry['acl']
            m_sec = self.getHierarchyUpManager(ZM_SCM)
            groups, users = m_sec.unfoldEBaSe(acl)

        # header labels
        elabel = self.getLabelString(table, None, entry)
        tlabel = tobj.getLabel()
        if not tlabel:
            tlabel = table
        heading = '%s Entry Permissions for %s' % (tlabel, elabel)
        url = '%s/editPermissionForm' % self.absolute_url()

        dlg = getStdDialog(heading, url)
        # build permission mask
        mask1 = m_sec.getEBaSeMask(users, True, True, dlg)
        dlg.add(mask1)
        mask2 = m_sec.getEBaSeMask(groups, False, True, dlg)
        dlg.add(mask2)

        # put in table and id
        autoprop = hgProperty('id', id, parent = dlg)
        dlg.add(autoprop)
        tableprop = hgProperty('table', table, parent = dlg)
        dlg.add(tableprop)

        # ok-button
        button = hgPushButton('OK', DLG_FUNCTION + 'OK', parent = dlg)
        dlg.add(button)

        button = self.getBackButton(parent = dlg)
        dlg.add(button)

        # return html
        return HTML(dlg.getHtml())(self, None)


    security.declareProtected(modifyPermission, 'newForm')
    def newForm(self, table, REQUEST = None):
        """\brief Returns the html source of the generic new form."""
        # first check for create dialogs, if found, return the 
        # dialog-container's show function
        dlgname = self.getDialogName(table, DLG_NEW)
        if dlgname:
            # get the container
            cont = getattr(self.dlgHandler, dlgname)
            # get the show function
            func = getattr(cont, 'show')
            # prepare the function's attributes
            attr = {'REQUEST': REQUEST}
            # return the function call
            return func(**attr)
        
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        if not perm.hasPermission(perm.SC_INSERT, tabid, ztype):
            return self.unauthorizedHtml(perm.SC_INSERT)

        # gathering all informations
        descr_dict = self.getTableEntryFromRequest(table, REQUEST)

        # form functions
        button = self.getPressedButton(REQUEST)
        if button:
            if  button == BTN_L_ADD:
                self.prepareDict(table, descr_dict, REQUEST)
                message1 = self.actionBeforeAdd(table, descr_dict, REQUEST)

                # image action:
                tablelists = self.listHandler.getLists(table, types = [], include = False)
                for lobj in tablelists:
                    lname = lobj.listname
                    if lobj.manager == ZM_IM:

                        # this is an image attribute

                        if REQUEST.get('add' + lname):
                            #file handling
                            if lobj.function == 'getImage':
                                ftype = 'image'
                            else:
                                ftype = 'file'
                            self.addFileGeneric( REQUEST,
                                                'add',
                                                lname,
                                                descr_dict,
                                                ftype )

                # security check (to avoid loosing show rights for creator)
                # security check
                #if self.checkEBaSe(table):
                #    # EBaSE is active, check show permissions
                #    m_security = self.getHierarchyUpManager(ZM_SCM)
                #    # superusers and admins are not affected
                #    if m_security and not m_security.getCurrentLevel() > 8:
                #        if not m_security.matchEBaSe( descr_dict,
                #                                      'show',
                #                                      table ):
                #            # return an errordialog
                #            err  = 'You are going to lose EBaSe show rights '
                #            err += 'with the current setting.'
                #            raise ValueError(self.getErrorDialog(err))

                # required check after all initial (custom) handling was done
                missing = self.checkRequiredFields(table, descr_dict)
        
                if missing:
                    msg = ''
                    tobj = self.tableHandler[table]
                    for field in missing:
                        msg += 'Missing value for field %s.<br>' % tobj.getLabel(field)
                    
                    # raise the error to reverse whatever was done before
                    self.displayError(msg, 'Required fields missing')
                
                autoid = tobj.addEntry(descr_dict)
                descr_dict[TCN_AUTOID] = autoid
                message2 = self.actionAfterAdd(table, descr_dict, REQUEST)
                if message1 or message2:
                    message = ''
                    if message1:
                        message += message1
                    if message2:
                        if message and message[-1] != ' ':
                            message += ' '
                        message += message2
                        
                    REQUEST['zopra_message'] = message
                else:
                    REQUEST['zopra_message']       = True
                    REQUEST['zopra_message_table'] = table
                    REQUEST['zopra_message_id']    = autoid

            elif button == BTN_L_RESET:
                descr_dict = {}

            elif button == BTN_L_CLOSE:
                # close form
                return self.closeForm(table, REQUEST)

            elif button == BTN_L_REFRESH:
                self.prepareDict(table, descr_dict, REQUEST)

            elif button == BTN_BASKET_POP:
                self.basketMoveFrom(table, descr_dict, REQUEST)
                self.prepareDict(table, descr_dict, REQUEST)

            elif self.checkListButtons(button):
                self.listHandler.handleListButtons(table, button, REQUEST, descr_dict)
                self.prepareDict(table, descr_dict, REQUEST)
        # basket-handling
        if self._generic_config.get(table):
            bButton = self._generic_config[table].get('basket_from', False)
        else:
            bButton = False
        mask = self.getMask(table, MASK_ADD, descr_dict)
        tlabel = tobj.getLabel()
        return self.getTableEntryNewDialog( 'New %s' % tlabel,
                                            mask,
                                            'newForm',
                                            True,
                                            REQUEST,
                                            'server',
                                            bButton )


    security.declareProtected(modifyPermission, 'editForm')
    def editForm(self, id, table, REQUEST = None):
        """\brief Returns the html source of the generic edit form."""
        # first check for edit dialogs, if found, return the 
        # dialog-container's show function
        dlgname = self.getDialogName(table, DLG_EDIT)
        if dlgname:
            # get the container
            cont = getattr(self.dlgHandler, dlgname)
            # get the show function
            func = getattr(cont, 'show')
            # prepare the request with id
            REQUEST.form['id'] = id
            # prepare the function's attributes
            attr = {'REQUEST': REQUEST}
            # return the function call
            return func(**attr)
        
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        if not perm.hasPermission(perm.SC_EDIT, tabid, ztype):
            # exception for user editing himself
            # FIXME: sequencing does not have groups -> users have no permissions -> editing themself forbidden
            # same goes for visitors
            # temporary solution: allow view/edit of own person generally here
            # longterm: add user-group to sequencing, allow edit of own person-data
            if self._className == 'ZMOMContactManager' and table == 'person' and self.getCurrentUserId() == int(id):
                # person is allowed to edit himself.
                pass
            else:
                return self.unauthorizedHtml(perm.SC_EDIT)

        ##TODO remove copy here when getEntry only returns copies
        descr_dict = copy(self.getEntry(table, id))

        # check if entry exists
        if not descr_dict:
            errstr = 'The Entry with ID %s for table %s is not in the database.'
            errstr = errstr % (id, table)
            err    = self.getErrorDialog(errstr)
            raise ValueError(err)

        # FIXME: check write permission but make sure persons can edit themself though
        # -> need to check entry-edit-permission and extra if person is editing himself

        # gathering all informations
        edit_dict = self.getTableEntryFromRequest(table, REQUEST)

        # test attributes for bool values if edit_dict is there
        types = tobj.getColumnTypes()
        if edit_dict:
            for entry in types:
                if types[entry] == 'bool':
                    if entry not in edit_dict:
                        edit_dict[entry] = 0
        # merge temporary edit information
        for field in edit_dict:
            descr_dict[field] = edit_dict[field]

        # we had a "bug" with emptied multilists, they don't appear in the edit_dict
        # but not editable multilists as well ... so the getShowHtml uses hgProperty now
        # TODO: somehow make sure that this is only done on follow-up calls to editForm
        # if somehow the edit_dict is not empty on the first call, we end up with missing 
        # multilist values
        # FIXME: introduce oldstyle-list-property for this check, default:false -> no check
        # edittracking cols are always present, so this check can work
        # but is it necessary anymore with complex multilists?
        self.listHandler.checkEmptyEditList(table, edit_dict, descr_dict)

        # form functions
        buttons = getPressedButton(REQUEST)
        runonce = 0
        for button in buttons:
            if button == BTN_L_REFRESH:

                # prepare dict
                self.prepareDict(table, descr_dict, REQUEST)

            elif button == BTN_L_CLOSE:

                # close form
                return self.closeForm(table, REQUEST)

            # update
            elif button == BTN_L_UPDATE:
                self.prepareDict(table, descr_dict, REQUEST)
                message = self.actionBeforeEdit(table, descr_dict, REQUEST)

                # image action:
                tablelists = self.listHandler.getLists(table, types = [], include = False)
                for lobj in tablelists:
                    lname = lobj.listname
                    if lobj.manager == ZM_IM:

                        # this is an image attribute

                        if REQUEST.get('del' + lname):

                            # delete
                            self.delFileGeneric( REQUEST,
                                                'del',
                                                lname,
                                                descr_dict)

                        if REQUEST.get('add' + lname):

                            # get type
                            if lobj.function == 'getImage':
                                ftype = 'image'
                            else:
                                ftype = 'file'

                            # add
                            self.addFileGeneric( REQUEST,
                                                 'add',
                                                 lname,
                                                 descr_dict,
                                                 ftype )

                # required check after all initial (custom) handling was done
                missing = self.checkRequiredFields(table, descr_dict)
        
                if missing:
                    msg = ''
                    tobj = self.tableHandler[table]
                    for field in missing:
                        msg += 'Missing value for field %s.<br>' % tobj.getLabel(field)
                    
                    # raise the error to reverse whatever was done before
                    self.displayError(msg, 'Required fields missing')
                
                # do the update
                tobj.updateEntry( descr_dict,
                                  descr_dict.get(TCN_AUTOID) )

                # reload entry (to make sure everything is alright)
                descr_dict = self.getEntry(table, id)
                # re-prepare (only way to ensure all handling from prepare is always done
                self.prepareDict(table, descr_dict, REQUEST)
                if message:
                    REQUEST['zopra_message'] = message
                else:
                    REQUEST['zopra_message']       = True
                    REQUEST['zopra_message_id']    = descr_dict.get(TCN_AUTOID)
                    REQUEST['zopra_message_table'] = table

            # reset
            elif button == BTN_L_RESET:
                descr_dict = self.getEntry(table, id)

            # multilist action
            elif self.checkListButtons(button):
                self.listHandler.handleListButtons(table, button, REQUEST, descr_dict)
                self.prepareDict(table, descr_dict, REQUEST)

            else:
                # some other button, just prepare dict (once)
                if not runonce:
                    # this is here to be able to check custom buttons in prepare_dict
                    # but sometimes more than one button is in the REQUEST and we do
                    # not want repeatable calls, so runonce is introduced
                    self.prepareDict(table, descr_dict, REQUEST)
                    runonce = 1

        mask   = self.getMask(table, MASK_EDIT, descr_dict)
        label  = self.getLabelString(table, None, descr_dict)
        tlabel = tobj.getLabel()
        return self.getTableEntryEditDialog( 'Edit %s %s' % (tlabel, label),
                                             mask,
                                             'editForm',
                                             True,
                                             REQUEST,
                                             'server',
                                             table,
                                             isGeneric = True )


    security.declareProtected(viewPermission, 'searchForm')
    def searchForm(self, table, descr_dict = None, REQUEST = None):
        """\brief Returns the html source of the generic search form.
           \param descr_dict is one dict or a list of tuples of dicts and
                  prefixes. The number of those tuples and the prefixes are
                  specified in getSearchPattern.
                  Standard behaviour is one dict.
        """
        # first check for search dialogs, if found, return the 
        # dialog-container's show function
        dlgname = self.getDialogName(table, DLG_SEARCH)
        if dlgname:
            # get the container
            cont = getattr(self.dlgHandler, dlgname)
            # get the show function
            func = getattr(cont, 'show')
            # prepare the function's attributes
            attr = {'REQUEST': REQUEST}
            # return the function call
            return func(**attr)
        
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        if not perm.hasPermission(perm.SC_VIEW, tabid, ztype):
            return self.unauthorizedHtml(perm.SC_VIEW)

        # determine first call
        if descr_dict == None:
            # first call
            descr_dict = {}
            descr_dict = self.actionBeforeSearch(table, REQUEST, descr_dict, firstSearch = True)
            # if there is a descr_dict, searchForm was submitted to showList, 
            # which evaluated a standard searchForm button or a custom button etc. via actionBeforeSearch
            # and forwarded to searchForm again. No need to call actionBeforeSearch twice on one call.

        mask = self.getMask(table, MASK_SEARCH, descr_dict)
        if self.basket_active and REQUEST:
            REQUEST.form['repeataction'] = 'searchForm?table=%s' % table
        label = tobj.getLabel()
        return self.getTableEntrySearchDialog( 'Search %s Entries' % label,
                                               mask,
                                               'showList',
                                               table = table )


    security.declareProtected(viewPermission, 'showForm')
    def showForm(self, id, table, REQUEST = None, auto = None):
        """\brief Returns the html source of the generic show form."""
        # first check for show dialogs, if found, return the 
        # dialog-container's show function
        dlgname = self.getDialogName(table, DLG_SHOW)
        if dlgname:
            # get the container
            cont = getattr(self.dlgHandler, dlgname)
            # get the show function
            func = getattr(cont, 'show')
            # prepare the request with id
            REQUEST.form['id'] = id
            # prepare the function's attributes
            attr = {'REQUEST': REQUEST}
            # return the function call
            return func(**attr)
        
        # no dialog found, normal handling
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        super = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        super = super or perm.hasSpecialRole(ztype + 'Superuser')

        if not perm.hasPermission(perm.SC_VIEW, tabid, ztype):
            # exception for user viewing himself
            # FIXME: sequencing does not have groups -> users have no permissions -> editing themself forbidden
            # same goes for visitors
            # temporary solution: allow view/edit of own person generally here
            # longterm: add user-group to sequencing
            if self._className == 'ZMOMContactManager' and table == 'person' and self.getCurrentUserId() == int(id):
                # person is allowed to edit himself.
                pass
            else:
                return self.unauthorizedHtml(perm.SC_VIEW)

        # done later again. removed here.
        #if REQUEST:
        #    # handle button
        #    button = self.getPressedButton(REQUEST)
        #    if button == BTN_L_CLOSE:
        #        # close form
        #        return self.closeForm(table, REQUEST)
            
        descr_dict = self.getEntry(table, id)

        if not descr_dict:
            errstr = 'The Entry with ID %s for table %s is not in the database.'
            errstr = errstr % (id, table)
            err    = self.getErrorDialog(errstr)
            raise ValueError(err)

        # check entry read permission
        if not descr_dict['permission'].hasPermission(SC_READ):
            # exception for user viewing himself
            # FIXME: sequencing does not have groups -> users have no permissions -> editing themself forbidden
            # same goes for visitors
            # temporary solution: allow view/edit of own person generally here
            # longterm: add user-group to sequencing
            if self._className == 'ZMOMContactManager' and table == 'person' and self.getCurrentUserId() == int(id):
                # person is allowed to edit himself.
                pass
            else:
                return self.nopermissionHtml(SC_READ)

        # activate basket
        REQUEST.form['repeataction'] = 'showForm?table=%s&id=%s' % (table, id)

        if REQUEST:
            # handle button
            buttons = getPressedButton(REQUEST)
            for button in buttons:
                if button == BTN_BASKET_ADD:
                    # basket
                    if self._generic_config.get(table):
                        basket = self._generic_config[table].get('basket_active', False)
                    else:
                        basket = self.basket_active
                    if basket:
                        # we add the actual entry
                        self.basketAdd(table, descr_dict, REQUEST)
    
                if button == BTN_L_EDIT:
                    return self.editForm(id, table, REQUEST)
    
                elif button == BTN_L_CLOSE:
                    # close form
                    return self.closeForm(table, REQUEST)
                
                else:

                    # check previous / next buttons
                    prevkey = table + '_prev'
                    nextkey = table + '_next'
                    doforward = False
                    if button.startswith(prevkey):
                        # previous button
                        actid = int(button[len(prevkey):])
                        # remove button
                        try:
                            del REQUEST.form[DLG_FUNCTION + button]
                        except:
                            # getPressedButton now corrects the REQUEST
                            #del REQUEST.form[DLG_FUNCTION + button + '.x']
                            #del REQUEST.form[DLG_FUNCTION + button + '.y']
                            pass
                        doforward = True
                    elif button.startswith(nextkey):
                        # next button
                        actid = int(button[len(nextkey):])
                        # remove button
                        try:
                            del REQUEST.form[DLG_FUNCTION + button]
                        except:
                            # getPressedButton now corrects the REQUEST
                            #del REQUEST.form[DLG_FUNCTION + button + '.x']
                            #del REQUEST.form[DLG_FUNCTION + button + '.y']
                            pass
                        doforward = True
                    if doforward:
                        return self.showForm(actid, table, REQUEST, auto)

        # basket-button
        if self._generic_config.get(table):
            bButton = self._generic_config[table].get('basket_to', False)
        else:
            # deprecated old handling
            if self.basket_active:
                bButton = True
            else:
                bButton = False
        creator = super or tobj.isOwner(descr_dict)
        mask  = self.getMask( table, MASK_SHOW, descr_dict )
        label = self.getLabelString(table, None, descr_dict)
        tlabel = tobj.getLabel()
        return self.getTableEntryShowDialog( '%s %s' % (tlabel, label),
                                             mask,
                                             'showForm',
                                             REQUEST,
                                             table,
                                             auto,
                                             descr_dict.get(TCN_AUTOID),
                                             creator, # user is creator -> edit and delete buttons
                                             True, #isGeneric
                                             bButton #show basket button
                                             )


    security.declareProtected(viewPermission, 'closeForm')
    def closeForm(self, table, REQUEST = None):
        """\brief closes the current form, redirects to manager. Overwrite for special behaviour.
        """
        url = self.absolute_url()
        func = REQUEST.PUBLISHED.__name__
        id = REQUEST.get('id')
        if id:
            if func == 'showForm':
                # do nothing, redirection to manager
                pass
            elif func == 'editForm':
                # redirect to showForm
                return REQUEST.RESPONSE.redirect('%s/showForm?table=%s&id=%s' % (url, table, id))

        return REQUEST.RESPONSE.redirect( url )


    security.declareProtected(viewPermission, 'showList')
    def showList(self, table, REQUEST = None):
        """\brief Returns the html source of the generic show list form."""
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        super = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        super = super or perm.hasSpecialRole(ztype + 'Superuser')

        # m_security = self.getHierarchyUpManager(ZM_SCM)
        root = tobj.getSearchTreeTemplate()
        # basket handling
        if 'repeataction' not in REQUEST.form:
            REQUEST.form['repeataction'] = 'showList?table=%s' % table

        # security check
        # if self.checkEBaSe(table):
            # EBaSE is active, add show constraints
            # not for superusers and admins:
            # if not super:
            #     pass
            #     # TODO: adjust to new ebase handling
            #     key = '%s_ebase_show' % table
            #     cons = {}
            #     cons[key] = groups
            #     cons['creator'] = m_security.getCurrentCMId()
            #     fil = ZMOMFilter(ZMOMFilter.OR, None)
            #     fil.setConstraints(cons, None, root.data)
            #     fil.setFinal()
            #     filRoot = root.getFilter()
            #     if not filRoot:
            #         filRoot = ZMOMFilter(ZMOMFilter.AND)
            #         root.setFilter(filRoot)
            #     filRoot.addChild(fil)
            #      store groups for later
            #     edit = groups

        buttonlist = getPressedButton(REQUEST)
        for button in buttonlist:
            # reset
            if button == BTN_L_RESET:
                # no descr_dict -> evaluated like first search -> actionBeforeSearch called by searchForm
                # reset the requests form to disable all submitted values
                REQUEST.form = {}
                return self.searchForm(table, None, REQUEST)
            # removed deletion preparation from here, peter 02/2009
            # manager.deleteEntries calls prepareDelete, which is a hook for custom deletion stuff
            #elif button == BTN_L_DELETE:
            #    self.actionBeforeDelete(table, None, REQUEST)
            elif button == BTN_L_CLOSE:
                # close form
                return self.closeForm(table, REQUEST)
            #listhandling
            elif self.checkListButtons(button):
                # multi descr_dict handling via getSearchPattern
                pattern = self.getSearchPattern(table)
                # we store each extracted dict with its prefix in a tuple
                dicts = []
                # work through each search-part
                for pat in pattern:
                    manager = pat[0]
                    ptable  = pat[1]
                    prefix  = pat[2]
                    m_some  = self.getHierarchyUpManager(manager)
                    d_some  = m_some.getTableEntryFromRequest(ptable, REQUEST, prefix, True)
                    m_some.listHandler.handleListButtons(ptable, button, REQUEST, d_some, prefix)
                    # need to call actionBeforeSearch now with each dict and prefix
                    tmp = self.actionBeforeSearch(ptable, REQUEST, d_some, firstSearch = False, prefix = prefix)
                    if tmp:
                        # overwrite values?
                        for key in tmp:
                            d_some[key] = tmp[key]
                    dicts.append(d_some)

                if len(pattern) == 1:
                    return self.searchForm(table, dicts[0])
                else:
                    return self.searchForm(table, dicts)
            # we add the checked entries
            elif button == BTN_BASKET_ADD:
                root.setConstraints(REQUEST.form)
                autoidlist = self.getSearchTickAutoidList(table, REQUEST, root)
                if len(autoidlist) > 200:
                    err = 'Too many entries, please select less than 200.'
                    raise ValueError(self.getErrorDialog(err))

                for changed_id in autoidlist:
                    entry = self.getEntry(table, changed_id)
                    if entry:
                        self.basketAdd(table, entry, REQUEST)
            elif button == BTN_FREETEXT:
                # freetext search for lists
                pattern = self.getSearchPattern(table)
                # we store each extracted dict with its prefix in a tuple
                dicts = []
                # work through each search-part
                for pat in pattern:
                    manager = pat[0]
                    ptable  = pat[1]
                    prefix  = pat[2]
                    m_some  = self.getHierarchyUpManager(manager)
                    d_some  = m_some.getTableEntryFromRequest(ptable, REQUEST, prefix, True)
                    m_some.handleFreeText(ptable, REQUEST, d_some, prefix)
                    # need to call actionBeforeSearch now with each dict and prefix
                    tmp = self.actionBeforeSearch(ptable, REQUEST, d_some, firstSearch = False, prefix = prefix)
                    if tmp:
                        # overwrite values?
                        for key in tmp:
                            d_some[key] = tmp[key]
                    dicts.append(d_some)
                if len(pattern) == 1:
                    return self.searchForm(table, dicts[0])
                else:
                    return self.searchForm(table, dicts)

        # custom searchForm handling hook (if we got here, it wasn't called yet)
        descr_dict = {}
        tmp = self.actionBeforeSearch(table, REQUEST, descr_dict, firstSearch = False)
        # if it returns True, and no searchbutton was pressed, we forward to searchForm
        if tmp:
            # if actionBeforeSearch returns True, this is the indicator to call the searchForm
            # this is done extra here to rearrange searchForm/showList handling later
            # then, searchForm leads to searchForm and only if searchButton is pressed, it leads to showList
            # but this handling needs a lot of code-sorting then
            return self.searchForm(table, descr_dict, REQUEST)

        param = {}
        # prepare REQUEST/param Hook
        self.actionBeforeShowList(table, param, REQUEST)

        # we may get additional constraints here
        if 'constraints' in param:
            cons = param['constraints']
            for con in cons:
                REQUEST.form[con] = cons[con]

        if 'show_fields' not in param:
            # try _generic_config
            if self._generic_config.get(table, {}).get('show_fields'):
                field_list = self._generic_config[table]['show_fields']
            # generate
            else:
                field_list = tobj.getColumnTypes(True).keys()

            param['show_fields']  = field_list

        #some defaults
        if super:
            if 'with_delete' not in param:
                param['with_delete'] = True
            if 'with_edit' not in param:
                param['with_edit']   = True
        # disable multiedit (except for enabling manager)
        if 'with_multiedit' not in param:
            param['with_multiedit'] = False
        if 'with_show' not in param:
            param['with_show']    = True

        # basket
        if 'with_basket' not in param:
            # generic config
            if self._generic_config.get(table):
                if self._generic_config[table].get('basket_to'):
                    param['with_basket'] = True
                else:
                    param['with_basket'] = False
            # old manager attribute
            else:
                # old handling, baskebutton shown if active
                if self.basket_active:
                    param['with_basket']  = True
                else:
                    param['with_basket']  = False

        # we want autoidlists for navigation
        if 'with_autoid_navig' not in param:
            param['with_autoid_navig'] = True
        return self.getTableEntryListHtml( root,
                                           param      = param,
                                           REQUEST    = REQUEST,
                                           isGeneric  = True )


    def checkListButtons(self, button):
        """\brief check whether the buttonname is a listbutton (or parts of it)"""
        for btn_name in [BTN_L_ADDITEM, BTN_L_REMOVE, BTN_HL_SELECT, BTN_HL_REMOVE, BTN_L_FILTER, BTN_FRL_NEXT, BTN_FRL_PREV]:
            if button.startswith(btn_name):
                return True


################################################
# Mask preparation functions for entry display #
#   - normally only overwrite getSingleMask / getRowMask #
     
################################################
    security.declareProtected(viewPermission, 'getSingleMask')
    def getSingleMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None):
        """\brief Main mask building function, returns a generic html mask
                    Overwrite this function to build a custom entry mask. Usage of
                    buildSemiGenericMask can aid with the basic mask layout, adding
                    custom parts to the basic mask afterwards. If you are using multi-
                    mask generic handling for the search (overwrote getSearchPattern?),
                    make sure to test for a list as descr_dict and forward to getMultiMask 
                    in that case. This handling sucks, but there is no easy way for now."""
        assert isinstance(table, StringTypes)
        assert isinstance(flag, IntType)

        # descr_dict is None, a dict or a list of dicts
        # (last only if getSearchPattern is overwritten)
        if isinstance(descr_dict, ListType):
            # call getMultiMask for handling
            return self.getMultiMask(flag, descr_dict)

        if not prefix:
            prefix = ''

        if not descr_dict:
            descr_dict = {}

        dbTable = self.tableHandler.get(table)

        if not dbTable:
            raise ValueError(self.getErrorDialog('Severe Error in Generic Manager Part.'))

        # build template
        coltypes = dbTable.getColumnTypes(vis_only = True)
        tmp = [[GEN_LABEL + entry, entry] for entry in coltypes]
        # show link
        if descr_dict.get(TCN_AUTOID):
            tmp.insert(0, [None, TCN_AUTOID])

        # FIXME: what about edit_tracking columns?

        return self.buildSemiGenericMask( table,
                                          tmp,
                                          flag,
                                          descr_dict,
                                          prefix,
                                          fixTracking = True )

    
    def prepareRowMask(self, table, ddict, mask, row, offset, label, flag):
        """\brief hook function for row mask adjustments.
                    This function gets called if you use buildSubMask to get row-wise entry display.
                    buildSubMask uses buildRowMask which calls this hook after each row for custom
                    adjustments."""
        pass


    # the following functions should not be overwritten
    # they are designed to work for all kinds of strange needs
    security.declareProtected(viewPermission, 'getMultiMask')
    def getMultiMask(self, table, flag, dict_list):
        """\brief Return a generic mask consisting of multiple single masks in a vertical layout.
                Overwrite if vertical is not your style and you know what you are doing."""
        # uses original manager's getSingleMask to build all masks
        # can be overwritten to use own special masks for each.
        # is called by getSingleMask, if that function
        # was called with a List of dicts,
        # so no table and autoid handling necessary
        assert isinstance(flag, IntType)

        # multiple tables for search
        pattern = self.getSearchPattern(table)
        keeper  = hgVBox()
        # work through each search-part
        for ddict in dict_list:
            pat = pattern.pop(0)
            manager = pat[0]
            ptable  = pat[1]
            prefix  = pat[2]
            m_some  = self.getHierarchyUpManager(manager)
            mask    = m_some.getSingleMask(ptable, flag, ddict, prefix)
            # reparenting is done automatically by add
            keeper.add(mask)
            mask.show()
        return keeper


    security.declareProtected(viewPermission, 'getMask')
    def getMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None):
        """\brief adds id and table property to getSingleMask-Output"""
        if descr_dict == None:
            descr_dict = {}

        mask = self.getSingleMask( table,
                                   flag,
                                   descr_dict,
                                   prefix )

        # descr_dict might be a list of dicts
        if isinstance(descr_dict, ListType):
            # multiple dicts from search
            # main dict is always first one
            autoid = descr_dict[0].get(TCN_AUTOID)
        else:
            autoid = descr_dict.get(TCN_AUTOID)
        if autoid:
            autoprop = hgProperty('id', autoid, parent = mask)
        tableprop = hgProperty('table', table, parent = mask)

        # check mask type, put in properties
        if isinstance(mask, hgTable):
            row = mask.numRows()
            mask[row, 0] = tableprop
            if autoid:
                mask[row, 1] = autoprop

        # special test for hgWidget, because isinstance is true for all widgets
        elif mask.__class__ == hgWidget or isinstance(mask, hgGroupBox):
            layout = mask.layout()
            if isinstance(layout, hgGridLayout):
                row = layout.numRows()
                layout.addWidget(tableprop, row, 0)
                if autoid:
                    layout.addWidget(autoprop, row, 1)

            else:
                # TODO: non-grid-layout, put in table and id
                # for now: put mask into box and add props
                box = hgVBox()
                mask.reparent(box)
                box.add(mask)
                tableprop.reparent(box)
                box.add(tableprop)
                if autoid:
                    autoprop.reparent(box)
                    box.add(autoprop)
                mask = box


        elif isinstance(mask, hgHBox) or isinstance(mask, hgVBox):
            mask.add(tableprop)
            if autoid:
                mask.add(autoprop)

        else:
            box = hgVBox()
            mask.reparent(box)
            box.add(mask)
            tableprop.reparent(box)
            box.add(tableprop)
            if autoid:
                autoprop.reparent(box)
                box.add(autoprop)
            mask = box
        return mask
    

    security.declareProtected(viewPermission, 'buildSemiGenericMask')
    def buildSemiGenericMask( self,
                              table,
                              template,
                              flag,
                              descr_dict  = None,
                              prefix      = None,
                              widget      = None,
                              parent      = None,
                              fixTracking = False ):
        """\brief Builds a widget with a grid layout representing the template."""
        # template has to be a grid (list of lists (rows))
        # there are two possible entries in the template:
        # GEN_LABEL+<attribute> and <attribute> for labels and widgets

        assert isinstance(template, ListType)
        assert isinstance(template[0], ListType)

        if not descr_dict:
            descr_dict = {}
        lablen = len(GEN_LABEL)
        tobj   = self.tableHandler[table]

        layout = None

        if widget:
            mask = widget
            if mask.layout():
                layout = mask.layout()
        else:
            mask   = hgGroupBox(parent = parent)
        if not layout:
            layout = hgGridLayout( mask, len(template), len(template[0]), 0, 2)

        row = col = 0
        for onerow in template:
            for entry in onerow:
                if entry:
                    if isinstance(entry, ListType):
                        multix = entry[2]
                        multiy = entry[1]
                        entry  = entry[0]
                    else:
                        multix = multiy = False
                    if entry[:lablen] == GEN_LABEL:
                        # build label
                        attr   = entry[lablen:]
                        pre = suf = None
                        # split of prefix and suffix
                        pos = attr.find(' _ ')
                        if pos != -1:
                            # found prefix / suffix
                            fix = attr[pos + 3:]
                            attr = attr[:pos]
                            pos = fix.find(' _ ')
                            if pos != -1:
                                # found both
                                pre = fix[:pos]
                                suf = fix[pos + 3:]
                            else:
                                pre = fix
                        if attr == TCN_AUTOID:
                            if not (flag & MASK_SEARCH):
                                widget = dlgLabel('View', mask)
                        else:
                            widget = tobj.getLabelWidget( attr,
                                                      ssiDLG_LABEL,
                                                      pre,
                                                      suf,
                                                      mask )
                        if not widget:
                            widget = hgLabel('', None, mask)
                    else:
                        new_flag = flag
                        if fixTracking:
                            # for TCN_CREATOR and TCN_DATE, fix flag, choose default
                            if entry == TCN_CREATOR:
                                if not flag & MASK_SEARCH:
                                    new_flag = MASK_SHOW
                                if flag & MASK_ADD and not descr_dict.get(TCN_CREATOR):
                                    m_contact = self.getHierarchyUpManager(ZM_CM)
                                    if m_contact:
                                        descr_dict[TCN_CREATOR] = m_contact.getCurrentUserId()
                                    
                            elif entry == TCN_DATE:
                                if not flag & MASK_SEARCH:
                                    new_flag = MASK_SHOW
                                if flag & MASK_ADD and not descr_dict.get(TCN_DATE):
                                    descr_dict[TCN_DATE] = strftime('%d.%m.%Y')
                        
                        # build widget
                        widget = self.getFunctionWidget( table,
                                                         entry,
                                                         mask,
                                                         new_flag,
                                                         descr_dict,
                                                         prefix )

                    # add widget

                    if multix or multiy:
                        layout.addMultiCellWidget( widget,
                                                   row,
                                                   row + multiy,
                                                   col,
                                                   col + multix )
                    else:
                        layout.addWidget(widget, row, col)
                col += 1
            row += 1
            col  = 0
            
        return mask


    security.declareProtected(viewPermission, 'buildSubMask')
    def buildSubMask( self,
                      table,
                      flag,
                      mainTable = None,
                      mainAttr  = None,
                      mainId    = None,
                      display   = None,
                      prefix    = None,
                      entries   = None,
                      parent    = None ):
        """\brief build a mask for a subtable with header"""
        # get entries
        if not (flag & MASK_SEARCH) and not entries:
            if mainId and mainAttr:
                entries = self.tableHandler[table].getEntries(mainId, mainAttr)
            else:
                # empty entry list given, leave it empty
                pass
        elif not entries:
            # search needs an empty dict
            entries = [{}]
        # attributes
        if not display:
            display = self._generic_config[table]['show_fields']
        # mask
        title = self.tableHandler[table].getLabel()
        mask = hgGroupBox(title = title, parent = parent)
        layout = hgGridLayout(mask, 1, 1, 0, 3)
        # header
        mask = self.buildRowMask( table,
                                  None,
                                  mask,
                                  0,
                                  flag,
                                  None,
                                  display,
                                  True,
                                  mainTable,
                                  mainAttr)
        row = 1
        # content
        for entry in entries:
            pre = None
            if flag & (MASK_EDIT | MASK_REDIT | MASK_SHOW):
                pre = str(entry.get(TCN_AUTOID))
            elif flag & MASK_SEARCH:
                pre = prefix
            self.buildRowMask( table,
                               entry,
                               mask,
                               row,
                               flag,
                               pre,
                               display,
                               False,
                               mainTable,
                               mainAttr )
            row += 1
        return mask


    security.declareProtected(viewPermission, 'buildRowMask')
    def buildRowMask( self,
                      table,
                      ddict,
                      mask,
                      row,
                      flag,
                      prefix,
                      display,
                      label     = False,
                      mainTable = None,
                      mainAttr  = None ):
        """\brief mask for one entry per row, called once per entry"""

        tmp = [ [] for i in xrange(row)]

        if mainTable and mainAttr and not mainAttr in display:
            display.insert(0, mainAttr)
            offset = 1
        else:
            offset = 0

        if label:
            dsp = []
            for entry in display:
                if entry:
                    dsp.append(GEN_LABEL + entry)
                else:
                    dsp.append(None)
            tmp.append(dsp)
        else:
            tmp.append(display)

        mask = self.buildSemiGenericMask( table,
                                          tmp,
                                          flag,
                                          ddict,
                                          prefix,
                                          mask )

        self.prepareRowMask(table, ddict, mask, row, offset, label, flag)

        return mask


    security.declareProtected(viewPermission, 'getFunctionWidget')
    def getFunctionWidget( self,
                           table,
                           attribute,
                           parent,
                           flag = MASK_SHOW,
                           descr_dict = None,
                           prefix     = None ):
        """\brief Returns the widget for the functional part."""
        if descr_dict == None:
            descr_dict = {}

        if prefix:
            wname = DLG_CUSTOM + prefix + attribute

        else:
            wname = attribute

        field = self.tableHandler[table].getField(attribute)
        if not field:
            raise ValueError('ERROR in getFunctionWidget: %s not found in %s' % (attribute, table))
        coltype = field.get(COL_TYPE)

        value  = descr_dict.get(attribute)
        if coltype == ZCOL_INT or coltype == ZCOL_FLOAT:
                if value == 0:
                    value = '0'
        if not value:
            value = ''

        # for autoid, return Link or nothing
        if attribute == TCN_AUTOID:
            if value:
                # container
                inter = hgWidget(parent = parent)
                # view link
                link    = self.getLink(table, None, descr_dict, inter)
                # line break
                breaker = hgLabel('<br />', parent = inter)
                # link to info form
                url = '%s/infoForm?table=%s&id=%s'
                url = url % (self.absolute_url(), table, value)
                label = hgLabel('&rarr; Ownership Info Page', url, inter)
                inter.showChildren(True)

                return inter
            else:
                return hgLabel('', parent = parent)

        if flag & MASK_SHOW:
            if coltype in ZLISTS:
                lobj   = self.listHandler.getList(table, attribute)
                widget = lobj.getShowHtml( descr_dict,
                                           False,
                                           parent )

            elif coltype == ZCOL_DATE:
                widget = hgLabel(value, None, parent, wname)

            elif coltype == ZCOL_MEMO:
                value  = value.replace('<', '&lt;')
                value  = value.replace('>', '&gt;')
                value  = value.replace('\n', '<br>')
                
                # TODO: where is this used? what is an internal link? help?
                # restore internal links
                if value:
                    memo_parts     = INTERNAL_LINK_PATTERN.split(value)
                    internal_links = INTERNAL_LINK_PATTERN.findall(value)
                    
                    for i, link in enumerate(internal_links):
                        newlink = '<' + link[4:-10] + '</a>'
                        newlink = newlink.replace('&gt;', '>', 1)
                        internal_links[i] = newlink
                        
                    if len(internal_links) < len(memo_parts):
                        internal_links.append('')
                        
                    value = ''
                    for i, part in enumerate(memo_parts):
                        value += part + internal_links[i]
                
                widget = hgLabel(value, None, parent, wname)

            elif coltype == ZCOL_BOOL:
                widget = hgCheckBox(name = wname, value = '1', parent = parent)
                if value:
                    widget.setChecked(True)
                widget.setDisabled()
                
            elif coltype == ZCOL_CURR:
                if value:
                    valstr = '%.2f' % value
                else:
                    valstr = ''
                widget = hgLabel(valstr, None, parent, wname)

            else:
                widget = hgLabel(str(value), None, parent, wname)

        elif flag & MASK_SEARCH:
            if coltype in ZLISTS:
                lobj = self.listHandler.getList(table, attribute)
                if lobj.manager == ZM_IM:
                    # Checkbox, value = _not_NULL
                    widget = hgCheckBox(name = wname, value = '_not_NULL', text = 'existing', parent = parent)
                    #widget = hgLabel('', parent = parent)
                else:
                    widget = lobj.getComplexWidget( True,
                                                    descr_dict,
                                                    True,
                                                    prefix,
                                                    parent )

            elif coltype == ZCOL_DATE:
                widget = hgDateEdit( value,
                                     '<font size="-1">(DD.MM.YYYY)</font>',
                                     parent,
                                     wname,
                                     hgTextEdit.LABEL_RIGHT )
                widget.setMaxLength(25)
            elif coltype == ZCOL_MEMO:
                widget = hgTextEdit( value,
                                     '',
                                     parent,
                                     wname,
                                     hgTextEdit.MULTILINE )
                widget.setSize(25, 5)

            elif coltype == ZCOL_BOOL:
                #widget = hgGroupBox(1, hg.Vertical, parent = parent)
                widget1 = hgCheckBox(name = wname, value = '1', text = 'checked')
                if value and value != 'NULL':
                    widget1.setChecked(True)
                widget2 = hgCheckBox(name = wname, value = 'NULL', text = 'not checked')
                if value == 'NULL':
                    widget2.setChecked(True)
                widget = widget1 + widget2
                widget.reparent(parent)
                #widget.show()
                
            else:
                widget = hgLineEdit(str(value), name = wname, parent = parent)

        elif flag & MASK_ADD:
            if coltype in ZLISTS:
                lobj = self.listHandler.getList(table, attribute)

                if lobj.manager == ZM_IM:
                    widget = self.getGenericFileMask( flag,
                                                      descr_dict,
                                                      table,
                                                      attribute,
                                                      prefix = prefix,
                                                      parent = parent )
                    if not widget:
                        widget = hgLabel('', parent = parent)
                else:
                    widget = lobj.getComplexWidget( False,
                                                    descr_dict,
                                                    False,
                                                    prefix,
                                                    parent )

            elif coltype == ZCOL_DATE:
                widget = hgDateEdit( value,
                                     '<font size="-1">(DD.MM.YYYY)</font>',
                                     parent,
                                     wname,
                                     hgTextEdit.LABEL_RIGHT )

            elif coltype == ZCOL_MEMO:
                widget = hgTextEdit( value,
                                     '',
                                     parent,
                                     wname,
                                     hgTextEdit.MULTILINE )
                widget.setSize(25, 5)

            elif coltype == ZCOL_BOOL:
                widget = hgCheckBox(name = wname, value = '1', parent = parent)
                if value:
                    widget.setChecked(True)
            
            elif coltype == ZCOL_CURR:
                if value:
                    valstr = '%.2f' % value
                else:
                    valstr = ''
                widget = hgLineEdit(valstr, name = wname, parent = parent)

            else:
                widget = hgLineEdit(str(value), name = wname, parent = parent)

        elif flag & MASK_EDIT:
            if coltype in ZLISTS:
                lobj   = self.listHandler.getList(table, attribute)
                if lobj.manager == ZM_IM:
                    widget = self.getGenericFileMask( flag,
                                                      descr_dict,
                                                      table,
                                                      attribute,
                                                      prefix = prefix,
                                                      parent = parent )
                    if not widget:
                        widget = hgLabel('', parent = parent)
                else:
                    
                    widget = lobj.getComplexWidget( False,
                                                    descr_dict,
                                                    False,
                                                    prefix,
                                                    parent )

            elif coltype == ZCOL_DATE:
                widget = hgDateEdit( value,
                                     '<font size="-1">(DD.MM.YYYY)</font>',
                                     parent,
                                     wname,
                                     hgTextEdit.LABEL_RIGHT )

            elif coltype == ZCOL_MEMO:
                widget = hgTextEdit( value,
                                     '',
                                     parent,
                                     wname,
                                     hgTextEdit.MULTILINE )
                widget.setSize(25, 5)

            elif coltype == ZCOL_BOOL:
                widget = hgCheckBox(name = wname, value = '1', parent = parent)
                if value:
                    widget.setChecked(True)

            elif coltype == ZCOL_FLOAT:
                # TODO: throw out? seems unwise.
                if not value:
                    value = 0
                widget = hgLineEdit(str(value), name = wname, parent = parent)
            
            elif coltype == ZCOL_CURR:
                if value:
                    valstr = '%.2f' % value
                else:
                    valstr = ''
                widget = hgLineEdit(valstr, name = wname, parent = parent)
            
            else:
                widget = hgLineEdit(str(value), name = wname, parent = parent)

        elif flag & MASK_REDIT:
            # same as show, but multilists use properties to retain their values
            # used for non-editable parts on edit
            if coltype in ZLISTS:
                lobj   = self.listHandler.getList(table, attribute)
                widget = lobj.getShowHtml( descr_dict,
                                           True,
                                           parent )

            elif coltype == ZCOL_DATE:
                widget = hgLabel(value, None, parent, wname)

            elif coltype == ZCOL_MEMO:
                widget = hgTextEdit( value,
                                     '',
                                     parent,
                                     wname,
                                     hgTextEdit.MULTILINE )
                widget.setSize(25, 5)
                widget.setReadOnly()

            elif coltype == ZCOL_BOOL:
                widget = hgCheckBox(name = wname, value = '1', parent = parent)
                if value:
                    widget.setChecked(True)
                widget.setReadOnly()

            elif coltype == ZCOL_CURR:
                if value:
                    valstr = '%.2f' % value
                else:
                    valstr = ''
                widget = hgLabel(valstr, None, parent, wname)

            else:
                widget = hgLabel(str(value), None, parent, wname)

        return widget


########################################
# generic customizable Import Handling #
########################################

    security.declareProtected(modifyPermission, 'importForm')

    def importForm(self, REQUEST):
        """\brief Returns the html source of an import table dialog."""

        #
        # dialog functions
        #
        import_result = ''
        sel_table     = ''
        button        = self.getPressedButton(REQUEST)

        if REQUEST:

            # get table
            if 'table' in REQUEST:
                sel_table = REQUEST['table']

            # get dialog button
            if button:

                # add button
                if button == BTN_L_ADD:
                    if REQUEST.get('file') and sel_table:
                        import_result = self.importTable(sel_table, REQUEST.get('file'), REQUEST)

        #
        # dialog table
        #
        tab = hgTable()
        row = 0
        tab[row, 0] = '<b>Import file name</b>'
        tab[row, 2] = '<input type="file" name="file">'
        row += 2
        tab[row, 0] = '<b>Add data to table</b>'
        any         = False
        for table in self.tableHandler.getTableIDs():
            # default is True, let all tables be open for import, switch off via _generic_config
            if not self._generic_config.get(table, {}).get('importable', True):
                continue
            if self.hasGUIPermission(table, GUIPermission.SC_INSERT):
                if not sel_table:
                    sel_table = table

                any = True
                tab[row, 2] = hgRadioButton(table,
                                            self.tableHandler[table].getLabel(),
                                            sel_table == table,
                                            name = 'table')
                row += 1

        if not any:
            self.displayError('Your authorization level doesn\'t allow any data import into %s.' % self.getTitle(), 
                              'Insufficient privileges')
        #
        # dialog
        #
        dlg  = getStdDialog('Import Table', '%s/importForm' % self.absolute_url())

        dlg.add('<center>')
        dlg.add( hgNEWLINE )
        dlg.add( tab )
        dlg.add( hgNEWLINE )
        dlg.add( mpfAddButton )
        dlg.add('</center>')
        if import_result:
            dlg.add( hgNEWLINE )
            dlg.add( hgLabel('Import Result') )
            dlg.add( hgNEWLINE )
            dlg.add( import_result )
            dlg.add( hgNEWLINE )
        dlg.add(self.getBackButtonStr(REQUEST))
        return HTML( dlg.getHtml() )(self, None)


    def importCanModifyLists(self, table):
        """\brief Property function, returns the modifyable lists 
                for each table or True for all or False for none."""
        return False

    
    def importKeepsValueForLists(self, table):
        """\brief Property function.
                Importer expects list values and translates them to autoids.
                This function returns names of lists which shouldnt be translated.
        """
        return []
    

    def importAdditionalFields(self, table):
        """\brief Property function.
                Importer accepts only fields of the table.
                This function returns list of field names which should be accepted as well.
        """
        return []
    

    def importExcludeFields(self, table):
        """\brief Property function.
                This function returns list of field names which should be ignored by import.
        """
        return []
    

    def importUniqueTuples(self, table):
        """\brief Property function.
                Returns a list of tuples (may be single fields) that must be unique in dbase
        """
        return []


    def importCheckLine(self, table, entry, line, status = None):
        """\brief checks the current line in import
        """
        # status is a dict of the form
        # {topic: {'msg': 'error messge', 'lines': [ (line, data), ... ]} }
        # NOTE: apart from the 2 reserved fields 'msg' and 'lines' you can
        #       add additional field to carry data across the whole import check

        if status is None:
            status = {}

        return status


    def importPrepareDict(self, table, descr_dict):
        """\brief Dummy Function called to prepare entry before add"""
        pass


    security.declareProtected(modifyPermission, 'importTable')
    def importTable(self, tablename, fHandle, REQUEST = None):
        """\brief Imports tab separated data into the database."""

        if not self._generic_config.get(tablename, {}).get('importable', False):
            return None

        m_security = self.getHierarchyUpManager(ZM_SCM)

        tobj     = self.tableHandler[tablename]
        importer = ImportHandler(self)

        # set the table for the importer
        importer.setTable(tablename)

        # set options
        do_allow = self.importCanModifyLists(tablename)
        if do_allow is True:
            # get all Lists
            alllists = self.listHandler.getLists(tablename)
            do_allow = []
            for lobj in alllists:
                do_allow.append(lobj.listname)

        elif do_allow is False:
            # okay, pass
            pass
        elif isinstance(do_allow, ListType):
            # okay, pass
            pass
        else:
            do_allow = False

        importer.setAllowListModification( do_allow )

        for _list in self.importKeepsValueForLists(tablename):
            importer.setKeepValuesForList(_list)

        add_fields = self.importAdditionalFields(tablename)
        importer.setAdditionalFields(add_fields)

        dont_import = self.importExcludeFields(tablename)

        # list of created ids
        created = []
        doubles = []

        # we only accept import tables that we can completely handle
        tab = self.importCheckLines(importer, fHandle)

        if tab:
            return tab

        unique_fields = self.importUniqueTuples(tablename)

        # NOTE: all checks already done in security run
        #       (still there is a race against changes in the db ^^;)
        for entry in importer.iterateEntries(fHandle):

            line = importer.getLineNumber()

            # remove not importable fields (before beeing filled with sensible data)
            for field in dont_import:
                if field in entry:
                    entry[field] = None

            # owner is a normal list now -> handling is generic
            # the following handling only replaced the owner if the column was in importKeepsValueForLists
            # but this is not what it indicates, so commented out completely by peter
            # handle owner
            # if 'owner' in add_fields:
            #    owner = None

            #    if m_security:
            #        if entry.get('owner') and 'owner' in self.importKeepsValueForLists(tablename):
            #            owner = self.listHandler.getList(tablename, 'owner').getAutoidByValue(entry['owner'])
            #            if owner:
            #                entry['owner'] = owner
            # prepare dict
            # import specific hook
            self.importPrepareDict(tablename, entry)

            # TODO: does it make sence to call the prepare/BeforeAdd/AfterAdd hooks with a REQUEST that
            # didn't come from a form which is expected?
            # generic prepare hook
            self.prepareDict(tablename, entry, REQUEST)

            # generic add hook
            self.actionBeforeAdd(tablename, entry, REQUEST)

            double_found = False
            for utuple in unique_fields:
                constraints = {}
                for field in utuple:
                    if entry.get(field):
                        constraints[field] = entry.get(field)

                # check dbase
                duplicates = self.tableHandler[tablename].getEntryList(show_number = 1, constraints = constraints)
                if duplicates:
                    doubles.append(str(entry))
                    double_found = True
            if double_found:
                continue

            # create entry (no check for reqired fields since we filled them in just now)
            entry_id = tobj.addEntry(entry)

            if not entry_id:
                self.displayError('Fatal error while creating entry in line %s.' %
                                  str(line),
                                  'Database Error')

            entry[TCN_AUTOID] = entry_id

            # generic after-add hook
            self.actionAfterAdd(tablename, entry, REQUEST)

            created.append(entry_id)

        # the really short report
        tab = hgTable()
        tab[0, 0] = hgLabel( '%s entries for %s successfully created.' % 
                             (len(created), self.tableHandler[tablename].getLabel()) )
        if doubles:
            tab[1, 0] = hgLabel('%s double entries for %s found.' %
                                 (len(doubles), self.tableHandler[tablename].getLabel()) )

        return tab


    security.declareProtected(modifyPermission, 'importCheckLines')
    def importCheckLines(self, importer, fHandle):
        """\brief Imports tab separated data into the database."""

        # possibble errors
        wrong_types  = []
        missing_reqs = []
        # listentry_missing          = []
        duplicate_found            = []
        import_duplicate           = []

        custom_status              = {}

        table = importer.table.getName()

        # get table information
        col_types = self.tableHandler[table].getColumnTypes()
        col_fct   = {}
        for col in col_types:
            if col_types[col] in [ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST] and \
               self.listHandler.getList(table, col).function:
                col_fct[col] = True
            else:
                col_fct[col] = False

        # tuples of fields that must have a unique value
        unique_fields = self.importUniqueTuples(table)
        unique_values = {}

        for utuple in unique_fields:
            unique_values[utuple] = []

        m_security = self.getHierarchyUpManager(ZM_SCM)

        for entry in importer.iterateEntries(fHandle):
            line = importer.getLineNumber()

            # check data types
            for field in entry:
                if col_fct.get(field, True):
                    continue
                if col_types[field] in [ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST] and \
                   field in self.importKeepsValueForLists(table):
                    continue
                if col_types[field] == 'multilist':
                    for oneitem in entry[field]:
                        try:
                            self.forwardCheckType(oneitem, 'singlelist')
                        except ValueError:
                            wrong_types.append( (line, field) )
                else:
                    try:
                        self.forwardCheckType(entry[field], col_types[field])
                    except ValueError:
                        wrong_types.append( (line, field) )

            # check required fields
            for req_field in self._generic_config[table]['required']:
                # field is not in entry_dict and no multilist
                if not entry.get(req_field):
                    missing_reqs.append( (line, req_field) )
                else:
                    if col_types[req_field] in [ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST] and \
                       entry.get(req_field) == 'NULL':
                        missing_reqs.append( (line, req_field) )

            # handle owner
            if 'owner' in importer.additionalFields() and \
               'owner' not in self.importKeepsValueForLists(table):
                owner = None

                if m_security:
                    if entry.get('owner'):
                        owner = self.listHandler.getList(table, 'owner').getAutoidByValue(entry['owner'])
                    else:
                        owner = m_security.getCurrentCMId()

                entry['owner'] = owner

            # check unique fields
            for utuple in unique_fields:
                values = []
                constraints = {}
                for field in utuple:
                    values.append(entry.get(field))
                    if entry.get(field):
                        constraints[field] = entry.get(field)

                # check dbase
                duplicates = self.tableHandler[table].getEntryList(show_number = 1, constraints = constraints)

                if duplicates:
                    duplicate_found.append( (line, utuple) )

                # check import lines
                if values in unique_values[utuple]:
                    import_duplicate.append( (line, utuple) )
                else:
                    unique_values[utuple].append(values)
                    unique_values[utuple].sort()

            # custom checks
            custom_status = self.importCheckLine(table, entry, line, custom_status)

        # collect errors and generate report if necessary
        status = importer.status()

        failed = {}
        error  = {}

        if 'bad_lines' in status:
            failed['Invalid lines'] = status['bad lines']
            error['Invalid lines']  = 'Has wrong format: %s'

        status['lost entries'] = status.get('lost entries', [])
        # merge missing entries
        # listentry_missing is still the original empty list! removed this:
        # if listentry_missing:
        #    status['lost entries'].extend(listentry_missing)
        if status.get('lost entries'):
            status['lost entries'].sort()
            failed['Missing list entries'] = status['lost entries']
            error['Missing list entries']  = 'List entry \'%s\' not known to database'

        if missing_reqs:
            failed['Missing requirements'] = missing_reqs
            error['Missing requirements']  = 'Required field \'%s\' is missing'

        if wrong_types:
            failed['Wrong data types'] = wrong_types
            error['Wrong data types']  = 'Field \'%s\' has wrong data type.'

        if duplicate_found:
            failed['Database Duplicate'] = duplicate_found
            error['Database Duplicate']  = 'Duplicate value for unique data tuple \'%s\' found in database.'

        if import_duplicate:
            failed['Import Duplicate'] = import_duplicate
            error['Import Duplicate']  = 'Duplicate value for unique data tuple \'%s\' found in import data.'

        if custom_status:
            for topic in custom_status:
                assert(topic not in failed.keys())

                # filter out status entries used for data transportation
                if not custom_status[topic].get('lines'):
                    continue

                failed[topic] = custom_status[topic]['lines']
                error[topic]  = custom_status[topic]['msg']

        if failed:
            tab  = hgWidget()
            tlay = hgGridLayout( tab )
            r = 0
            tlay.addMultiCellWidget(hgLabel('No data imported. Fix errors listed below first!', parent = tab), r, r, 0, 1)
            r += 1
            tlay.addMultiCellWidget(hgLabel('&nbsp;', parent = tab), r, r, 0, 1)
            r += 1

            for key in failed:
                tlay.addMultiCellWidget(hgLabel('<b>%s</b>' % key, parent = tab), r, r, 0, 1)
                r += 1
                tlay.addMultiCellWidget(hgLabel('&nbsp;', parent = tab), r, r, 0, 1)
                r += 1
                for msg in failed[key]:
                    tlay.addWidget(hgLabel('Line %s:&nbsp;' % str(msg[0]), parent = tab), r, 0)
                    tlay.addWidget(hgLabel(error[key] % str(msg[1]), parent = tab), r, 1)
                    r += 1
                r += 1
                tlay.addMultiCellWidget(hgLabel('&nbsp;', parent = tab), r, r, 0, 1)
                r += 1

            return tab
        else:
            return None
