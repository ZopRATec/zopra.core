"""The Manager is the basic manager class."""

from copy import deepcopy

from zope.interface import implementer

from zopra.core import ZC
from zopra.core import ClassSecurityInfo
from zopra.core import Folder
from zopra.core import managePermission
from zopra.core import modifyPermission
from zopra.core import viewPermission
from zopra.core.elements.Buttons import DLG_CUSTOM
from zopra.core.interfaces import IZopRAManager
from zopra.core.interfaces import IZopRAProduct
from zopra.core.lists.ListHandler import ListHandler
from zopra.core.mixins.ManagerFinderMixin import ManagerFinderMixin
from zopra.core.mixins.ManagerManageTabsMixin import ManagerManageTabsMixin
from zopra.core.tables.TableHandler import TableHandler
from zopra.core.types import DictType
from zopra.core.types import ListType
from zopra.core.types import TupleType
from zopra.core.utils import getTableDefinition
from zopra.core.utils.Classes import Column


SEARCH_KEYWORDS = ["NULL", "_not_", "_<_", "_>_", "_to_", "__"]


@implementer(IZopRAManager)
class Manager(Folder, ManagerFinderMixin, ManagerManageTabsMixin):
    """Manager class provides basic entry and request Handling, manager
    object location and install methods."""

    # _className and _classType are deprecated for Manager classes, we can throw them out in all packages
    # TODO: cleanup _className and _classType for all Manager classes
    _className = "Manager"
    _classType = [_className]

    meta_type = ""

    manage_options = (
        Folder.manage_options[0],
        {"label": "Overview", "action": "viewTab"},
        {"label": "Update", "action": "updateTab"},
    ) + tuple(Folder.manage_options[1:])

    #
    # Properties
    #
    _properties = Folder._properties + (
        {"id": "delete_tables", "type": "int", "mode": "w"},
        {"id": "zopra_version", "type": "float", "mode": "w"},
        {"id": "zopratype", "type": "string", "mode": "w"},
    )

    #
    # Property default settings
    #

    # should manage_beforeDelete delete the database tables? 0/1
    delete_tables = 0

    # the overall uptodate version number
    # set as class variable -> comparable to instance variable of same name
    zopra_version = 1.8

    # the property for distinguishing multiple instances of one manager class
    zopratype = ""

    """:generic configuration dict
    usage: _generic_config = {table: {key:value}}
    keys: visible       (True / False) - visible in zopra_manager_main_form
            show_fields   ([attrs])      - attributes for search result listing (editorial)
            required      ([attrs])      - required attributes for new/edit
            check_fields  ([{fieldname: function}] - call the module function for the field check when adding / editing an entry, function parameters are: attr_name, entry, mgr
            links         ([{'label':'<label>', 'link': '...%s', 'field': '<fieldname>', 'iconclass': 'icon-xyz'}]) - use info to add a link column to search result listing (editorial), linking to the given url (enhanced by the content of the field with the given fieldname), using the given label and icon class [url needs exactly one %s, normally used with the autoid field]
            specials      ([{'label': '<label>', fieldname: function}] - call the module function on every displayed entry in search result listing (editorial) to calculate the html content for a special column, label is used for table head, function parameters are: mgr, table, entry, lang, html
            importable    (True / False) - show in importForm for Import
            show_table_options    ({'create':1, 'search':1, 'list':1, 'import': (<target>, <label>), ...}) - define options for generic table overview (on manager_main_form)
            dependent     (True / False) - set to True to not show the create button on zopra_table_show_form / zopra_table_edit_form
    legacy keys:
            basket_to     (True / False) - for showForm/showList-BasketButton
            basket_from   (True / False) - for newForm-BasketButton
            basket_active (True / False) - show basket at all
    access via getGenericConfig(table)
    """
    _generic_config = {}

    #
    # Security
    #
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    security.declareProtected(managePermission, "__init__")

    def __init__(self, title="", id=None, nocreate=0, zopratype=""):
        """Constructs a Manager."""
        self.title = title
        self.id = id

        self.nocreate = nocreate
        self.zopratype = zopratype
        self.tableHandler = None
        self.listHandler = None

        # security switches
        self.ebase = False
        self.sbar = False

        self.zopra_version = self.__class__.zopra_version

    ###########################################################################
    #                                                                         #
    # basic methods for manager object handling                               #
    #                                                                         #
    ###########################################################################

    def getClassName(self):
        """This method returns the class name.

        :result: class name
        :rtype: string
        """
        return self.__class__.__name__

    def getClassType(self):
        """This method returns a list of the class names of all ancestors and the current class"""
        return [onetype.__name__ for onetype in self.__class__.__bases__] + [
            self.getClassName()
        ]

    def getTitle(self):
        """Returns the title of the object.

        :return: the title of the manager if it exists, otherwise an empty string.
        :rtype: string"""
        return self.title if hasattr(self, "title") else ""

    def getId(self):
        """Returns the id of the object.

        :return: the id of the manager if it exists, otherwise an empty string.
        :rtype: string
        """
        return self.id if hasattr(self, "id") else ""

    security.declareProtected(viewPermission, "getZopraType")

    def getZopraType(self):
        """Returns the internal type of the manager (to have different handling
        for same managers with different type)."""
        return self.zopratype

    ###########################################################################
    #                                                                         #
    #  generic config helper methods                                          #
    #                                                                         #
    ###########################################################################

    def getGenericConfig(self, table):
        """ Retrieve the generic config for the table """
        return self._generic_config.get(table, {})

    def getConfigShowFields(self, table):
        """Retrieve the show_fields option from the generic config for the
        table if it exists; otherwise return a list of the names of all
        visible columns
        """
        conf = self.getGenericConfig(table)
        fields = conf.get("show_fields")
        if not fields:
            fields = self.tableHandler[table].getColumnDefs().keys()
        return fields

    def getRequiredFields(self, table):
        """Get the required attributes for the table"""

        if table not in self.tableHandler:
            raise ValueError(
                "Table '%s' does not exist in %s" % (table, self.getTitle())
            )

        required = []

        # simple managers do not need a _generic_config, so check for existence
        if self._generic_config.get(table):
            if self._generic_config[table].get("required"):
                required = self._generic_config[table]["required"]

        return required

    def checkRequiredFields(self, table, dict):
        """Checks required attributes in dict to be accepted by table"""

        if table not in self.tableHandler:
            raise ValueError(
                "Table '%s' does not exist in %s" % (table, self.getTitle())
            )

        if dict is None or not isinstance(dict, DictType):
            dict = {}

        missing = []
        required = self.getRequiredFields(table)

        for field in required:
            # field is not in entry_dict and no multilist
            if not dict.get(field):
                missing.append(field)
            elif dict.get(field) == "NULL":
                if self.listHandler.hasList(table, field):
                    missing.append(field)

        return missing

    ###########################################################################
    #                                                                         #
    #  language / translations / working copies switched off                  #
    #                                                                         #
    ###########################################################################

    def getCurrentLanguage(self):
        """ Language default is en, overridden in TemplateBaseManager"""
        return "en"

    def doesTranslations(self, table):
        """Translation indicator, should be overwritten to return True for
            tables that handle translations.

        The translation handling is still not incorporated in the ZopRA Core.
        """
        return False

    def doesWorkingCopies(self, table):
        """Working copy indicator, should be overwritten to return True for
            tables that handle working copies.

        The working copy handling is still not incorporated in the ZopRA Core.
        """
        return False

    ###########################################################################
    #                                                                         #
    # Generic Manager Hook Functions - to be overwritten for custom handling  #
    # (abstract, no implementation here)                                      #
    #                                                                         #
    ###########################################################################

    def prepareDict(self, table, descr_dict, REQUEST=None):
        """Hook Function called before edit and add

        In contrary to actionBeforeAdd and actionBeforeEdit,
        this hook gets called every time that a button was pressed on the
        edit and add forms. It can be used for verification and preview.

        When the real edit or add happens, prepareDict gets called first.
        Overwriting the hook: return values will be ignored.

        The REQUEST can be used to obtain non-standard form values (the standard
        table attribute values are already in descr_dict).
        """
        pass

    def actionBeforeAdd(self, table, descr_dict, REQUEST):
        """Hook Function called before add

        This function can be used to adjust the to-be-saved entry
        before it gets added to the database. It does not have an autoid yet.
        For custom handling that needs an autoid, use actionAfterAdd.

        Overwriting the hook: make sure to return nothing or a message to be
        displayed.

        The REQUEST can be used to obtain non-standard form values (the standard
        table attribute values are already in descr_dict).
        """
        # expected to return None or message string about operations
        # performed (usually only in case of errors)
        return None

    def actionBeforeEdit(self, table, descr_dict, REQUEST):
        """Hook Function called before edit
        This function can be used to adjust the entry before it gets saved
        or to adjust dependent entries. Since the entry already exists, you find
        it's autoid in the descr_dict.

        Overwriting the hook: make sure to return nothing or a message to be
        displayed.

        The REQUEST can be used to obtain non-standard form values (the standard
        table attribute values are already in descr_dict).
        """
        # expected to return None or message string about operations
        # performed (usually only in case of errors)
        return None

    def actionAfterAdd(self, table, descr_dict, REQUEST):
        """Hook Function called after adding an entry to the database

        This function can be used to create dependent entries or adjust the new
        entry.
        For custom changes that do not need an autoid, use actionBeforeAdd.
        The descr_dict contains the newly assigned autoid of the new entry.

        Overwriting the hook: make sure to return nothing or a message to be
        displayed.

        The REQUEST can be used to obtain non-standard form
        values (the standard table attribute values are already in descr_dict).
        """
        # expected to return None or message string about operations
        # performed (usually only in case of errors)
        return None

    def actionBeforeSearch(
        self, table, REQUEST, descr_dict, firstSearch=True, prefix=""
    ):
        """Hook Function called by zopra_table_search_result (and legacy searchForm and showList).

        This hook is invoked on first search by searchForm and later on by
        showList after its searchForm handling.
        Use it to determine if a custom searchForm button was pressed and
        perform custom search - related handling, that needs to be done before
        displaying the search Form.

        Return a dictionary to indicate that showList should call searchForm
        with this dictionary.
        Otherwise, the normal showList handling is done, using
        getTableEntryListHtml, unless some of the standard searchForm-Buttons
        are evaluated.

        @param firstSearch is False when this call is done by showList,
               meaning that the searchForm was submitted.
        @param prefix is given for multi-table search requests
               If your searchForms only apply to one table each, you can ignore
               it, otherwise it indicates which values of the REQUEST are
               relevant on each call (since they should be prefixed accordingly)
        """
        return None

    def startupConfig(self, REQUEST):
        """Hook Function called after first creation by manageAddGeneric
        This function can be used to create standard entries for noneditable lists,
        it is only called if the database tables were created, not on reinstallation.
        So it should not be used to configure the manager, just the database."""
        pass

    def installConfig(self, REQUEST):
        """Hook Function called after creation by manageAddGeneric on each install.
        Use it to get dtml-form values from REQUEST.
        For database action (only on first install) see startupConfig Hook"""
        pass

    def prepareDelete(self, table, id, REQUEST):
        """Hook Function called before delete
        This function is for cleaning up the database where custom cleaning is necessary.
        Entries that depend on the to-be-deleted entry have
        to be adjusted here. REQUEST might be None (parameter added later on).
        To indicate an error, return an error message (preferrably) or raise an error.
        """
        return None

    def hook_buttonForwardForm(self, table, action, REQUEST):
        """Function Stub for manual button handling for forwards to achieve
        link-like function
        """

        # we got forwarded here but didn't find anything
        msg = "hook_buttonForwardForm (Table: %s, Action: %s) was "
        msg += "used without being overwritten in %s"
        msg = msg % (table, action, self.getClassName())
        error = self.renderError(msg, "Button Error")
        raise ValueError(error)

    security.declareProtected(modifyPermission, "_addTable")

    def _addTable(self):
        """Hook method for extra table magic on add.
        Called by manage_afterAdd if table creation is enabled via DTML add form."""
        pass

    security.declareProtected(modifyPermission, "_addTable")

    def _delTable(self):
        """Hook method for extra table magic on delete.
        Called by manage_beforeDelete if delete_tables option is set via properties screen."""
        pass

    security.declareProtected(viewPermission, "prepareFieldForExport")

    def prepareFieldForExport(self, table, column, value, entry):
        """Hook method called by Table.exportTab to preprocess each column
        of each entry to be exported.
        The value is already processed (translated ids into values for lists)
        and will be escaped after being returned here.
        Overwrite this function to process each single value (or replace it
        entirely) if you need special display for export. This is for example
        used to unscramble scrambled E-Mails from the database before putting
        them into the export file."""
        return value

    security.declareProtected(viewPermission, "getListSelectionConstraints")

    def getListSelectionConstraints(self, listname, lang="de"):
        """Basic Function for List Selection Constraining.
        This function can be overwritten to constrain foreign table based lists
        based on their name by returning a constraints dictionary that will be
        used by the entry gathering mechanisms of the list objects."""
        return {}

    security.declareProtected(viewPermission, "checkDefaultWildcardSearch")

    def checkDefaultWildcardSearch(self, table):
        """Toggle for Wildcard Search. Overwrite this function and return True
        for the tables that will then automatically use wildcard search for all text fields."""
        return False

    ###########################################################################
    #                                                                         #
    # Generic Basic Methods - to be overwritten for custom handling           #
    # (basic implementation provided here)                                    #
    #                                                                         #
    ###########################################################################

    def getSearchPattern(self, table):
        """called before REQUEST is analysed by showList
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
        return [(self.getClassName(), table, "")]

    security.declareProtected(viewPermission, "generateTableSearchTreeTemplate")

    def generateTableSearchTreeTemplate(self, table):
        """Virtual function for manager specific searchTree called by Table.getSearchTreeTemplate.
        The standard search tree is just the corresponding
        TableNode for the table. This method returns
        the TableNode. Overwrite it to produce a custom
        search tree and return the root node. To get the template for custom searches,
        use Table.getSearchTreeTemplate (caching is done there)."""
        return self.tableHandler[table].getTableNode()

    def getLabelString(self, table, autoid=None, descr_dict=None, lang=None):
        """Return label for entry, overwrite for special functionality."""
        # we either get the autoid (to retrieve the ddict) or the descr_dict (which is the ddict, but might be in the wrong language)
        if descr_dict:
            ddict = descr_dict
            # check for translations
            # this did not work for working-copies, because we should not jump to the english version if we want to load a copy
            # lang is given, translations are on, lang is not the default, lang is in the additional languages (meaning no fallback), ddict is in the wrong language, ddict has a translation
            if (
                lang
                and self.doesTranslations(table)
                and lang != self.lang_default
                and lang in self.lang_additional
                and ddict["language"] != lang
                and ddict["hastranslation"]
            ):
                # look for translation
                entries = self.tableHandler[table].getEntryList(
                    constraints={
                        "istranslationof": ddict.get(ZC.TCN_AUTOID),
                        "language": lang,
                    },
                    ignore_permissions=True,
                )
                # check if we found anything (if entry is a working-copy, no translation can be found, which is okay)
                if entries:
                    ddict = entries[0]
        elif autoid:
            # directly retrieve the entry in the correct language
            ddict = self.getEntry(table, autoid, lang, ignore_permissions=True)
        else:
            return ""
        if not ddict:
            return ""
        # return autoid, no matter what table
        autoid = ddict.get(ZC.TCN_AUTOID, "")
        return str(autoid)

    def prepare_labelstringsearch(self, table, searchterm, root):
        """Basic Generic Function, overwrite for special functionality.
        Implementation builds constraints and order for search and puts them
        into the TableNode named root for the searchLabelStrings function to use.
        The information is taken from _generic_config with key 'labelsearchfields'
        """
        # default behaviour is to look into _generic_config for a main column
        fields = self._generic_config.get(table, {}).get("labelsearchfields", [])

        cons = {}
        # empty searchterm returns everything -> no cons
        if searchterm:
            for field in fields:
                # for now, use searchterm for each field
                cons[field] = "*" + searchterm + "*"

        if fields:
            order = fields
        else:
            order = ZC.TCN_AUTOID

        # multiple fields each have the same searchterm in the constraints
        # for multifield, we need to either break the term apart or simply build a filter for or-search
        # the latter is done for now
        root.setConstraints(cons)
        if len(cons) > 1:
            root.filterTree.setOperator(root.filterTree.OR)
        if order:
            root.setOrder(order)

    def getHierarchyListConfig(self, table, name):
        """Get a default config for hierarchylists. Overwrite for special settings."""
        # TODO: right now, the Plone templates only allow working with the exact settings below, different combinations have not been implemented yet.
        # multivalued: multiple values can be set on edit
        # multisearch: search allows to select multiple (leaf)nodes
        # nonleaf-search: search allows to select nodes, that are no leafs
        # nonleaf-search-expand: search for all nodes/leafs below the chosen one (and the node itself), only applies when nonleaf-search is True
        # nonleaf-edit: allow the autoid of a node as value, that is not a leaf node
        return {
            "multivalued": False,
            "multisearch": False,
            "nonleaf-search": True,
            "nonleaf-search-expand": True,
            "nonleaf-edit": True,
        }

    ###########################################################################
    #                                                                         #
    # Generic basic methods for entry handling                                #
    #                                                                         #
    ###########################################################################

    def getEntry(self, table, autoid, lang=None, ignore_permissions=False):
        """Calls tableHandlers getEntry"""

        # check input
        if autoid is None or table is None or table not in self.tableHandler:
            raise RuntimeError("Missing parameter")

        # check autoid
        try:
            autoid = int(autoid)
        except Exception:
            raise ValueError("Generic Manager Autoid Problem: %s" % autoid)

        # get entry
        tobj = self.tableHandler[table]
        entry = tobj.getEntry(autoid, ignore_permissions=ignore_permissions)

        # return empty dictionary if no entry was found
        if entry is None:
            return {}

        # do translation if we have a translation for the table
        if lang and self.doesTranslations(table) and entry["language"] != lang:
            result = tobj.getEntryList(
                constraints={"istranslationof": autoid, "language": lang},
                ignore_permissions=ignore_permissions,
            )
            if result:
                entry = result[0]

        # return result
        return entry

    security.declareProtected(modifyPermission, "deleteEntries")

    def deleteEntries(self, table, idlist, REQUEST=None):
        """Basic function, forwards deletion request to Table object named table.
        This function is called by all deletion methods and dialogs (single / multi)
        and adds checks and a call to the deletion hook which
        has to be used for custom deletion handling before calling the deleteEntries of the Table."""
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

    def searchLabelStrings(self, table, search, start=0, show=-1, tolerance=0):
        """Returns autoid list whose labels match search.
        Search should cover wildcards *, ?
        Generic search calls prepare_labelstringsearch hook, which uses
        labelsearchfields from _generic_config. For own search functionality,
        overwrite prepare_labelstringsearch.
        Used for improved getAutoidByValue in ForeignList.
        List object must have set option labelsearch == True to use this method.

        :return: tuple of list of found ids and total number
        """
        if show is None:
            show = -1

        if start is None:
            start = 0

        if table not in self.tableHandler:
            return None

        if search:
            search = search.replace("*", "%")
            search = search.replace("?", "_")

        # use the tablenode to search for labelstrings
        # we use the complete template because an overwritten prepare-function could return constraints for subtables
        root = self.tableHandler[table].getSearchTreeTemplate()

        # now we need the column or columns to search, this is done via hook
        # root-fiddling is done in there
        self.prepare_labelstringsearch(table, search, root)

        # get row count right away to provide value for BTN_L_LAST
        func = "count(distinct %sautoid)"

        total = self.getManager(ZC.ZM_PM).executeDBQuery(
            root.getSQL(function=func, checker=self)
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

        # FIXME: distinct is False due to ordering. But we do not have an order. Strange.
        sql = root.getSQL(show, start, distinct=False, checker=self)
        cache = self.tableHandler[table].cache
        autoidlist = deepcopy(cache.getItem(cache.IDLIST, sql))

        if not autoidlist:
            autoidlist = []
            results = self.getManager(ZC.ZM_PM).executeDBQuery(sql)

            # this is done to have distinct values but intact order
            tmp_dict = {}
            for result in results:
                autoid = int(result[0])
                if autoid not in tmp_dict:
                    tmp_dict[autoid] = None
                    autoidlist.append(autoid)
            # caching
            cache.insertItem(cache.IDLIST, sql, autoidlist)

        return (autoidlist, total)

    def prepare_zopra_currency_value(self, value):
        """Format a currency value according to german standard or return as is
        (for edit validation / search validation)
        """
        if value is None:
            return ""

        try:
            res = ("%.2f" % float(str(value).replace(",", "."))).replace(".", ",")
        except Exception:
            res = str(value)

        return res

    def getAttributeEditPermissions(self, table):
        """Return List of editable attributes for current user (used by multiedit)
        Overwrite to specify which permission is needed to edit which attributes.
        The dlgMultiEdit uses this function to determine which attributes to
        display in edit-mode and which not."""

        # get current userlevel
        m_security = self.getHierarchyUpManager(ZC.ZM_SCM)
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
            m_product = self.getManager(ZC.ZM_PM)
            for column in m_product._edit_tracking_cols:
                if column not in attrs:
                    attrs.append(column)
            return attrs

    security.declareProtected(viewPermission, "forwardCheckType")

    def forwardCheckType(
        self, value, column_type, operator=False, label=None, do_replace=True
    ):
        """forward the type check call to the next ZopRAProduct"""
        m_prod = self.getManager(ZC.ZM_PM)
        # m_prod could be self, but doesnt matter
        return m_prod.checkType(value, column_type, operator, label, do_replace)

    # REQUEST handling
    security.declareProtected(viewPermission, "getTableEntryFromRequest")

    def getTableEntryFromRequest(self, table, REQUEST, prefix="", search=False):
        """Builds a dict from a REQUEST object.
        The function tries to filter all key,
        value pairs where a key matches
        with a column name of the specified table
        (maybe prefixed with DLG_CUSTOM and the given prefix).
        It also looks for special keys for search (ANDconcat)

        :param table: a string with the table name without id prefix.

        :param REQUEST:  REQUEST object that
        contains the key - value pairs of the fields from the html form.

        :param prefix: makes this method only filter keys that start with DLG_CUSTOM+prefix,
        the results are unprefixed however

        :param search: indicates whether caller is the search machinery

        :return: The method will return a description dictionary with the
        found key - value pairs.
        :rtype: dict
        """
        descr_dict = {}
        pre = ""
        if prefix:
            pre = DLG_CUSTOM + prefix

        tobj = self.tableHandler[table]

        # wildcard search check
        do_wilds = search and self.checkDefaultWildcardSearch(table)
        typedefs = tobj.getColumnTypes()

        # handling without a session object
        for name in tobj.getMainColumnNames():

            if pre + name in REQUEST:
                value = REQUEST[pre + name]

                if isinstance(value, ListType) and value:
                    # this is unnecessary for main columns, they should only
                    # appear once but this check is needed for bool searches
                    # (true-checkbox / false-checkbox)
                    value = value[0]

                # unicode conversion
                if typedefs[name] in [ZC.ZCOL_STRING, ZC.ZCOL_MEMO]:
                    try:
                        value = value.decode("utf-8")
                    except Exception:
                        pass

                # wildcard search
                if (
                    value
                    and do_wilds
                    and typedefs[name] in [ZC.ZCOL_STRING, ZC.ZCOL_MEMO, ZC.ZCOL_DATE]
                ):
                    wcs = True
                    for skw in SEARCH_KEYWORDS:
                        if value.find(skw) != -1:
                            wcs = False
                    # wrap with '*', unless it's been already wrapped;
                    # prevents cases like ******x******
                    if wcs and not (value[0] == value[-1] == "*"):
                        value = "*%s*" % value
                descr_dict[name] = value

        # get all lists
        tablelists = self.listHandler.getLists(table)

        for listobj in tablelists:
            name = listobj.listname
            pre_name = pre + name

            entry = REQUEST.get(pre_name)

            if listobj.listtype in ["multilist", "hierarchylist"]:
                if entry:
                    # the entry has to be a list
                    if not isinstance(entry, ListType) and not isinstance(
                        entry, TupleType
                    ):
                        entry = [entry]

                    # we take the note-entries from the REQUEST as well
                    pre_name_notes = pre_name + "notes"
                    name_notes = name + "notes"
                    new_entry = []
                    for item in entry:
                        # unicode conversion
                        try:
                            item = item.decode("utf-8")
                        except Exception:
                            pass
                        if item and item != u"NULL":
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
                                    itemval = REQUEST.get(key, u"")
                                    # unicode conversion
                                    try:
                                        itemval = itemval.decode("utf-8")
                                    except Exception:
                                        pass
                                    descr_dict[key1] = itemval
                    entry = new_entry
                else:
                    # this should lead to correct empty multilists on edit
                    entry = []

                if search:
                    # widget check
                    # check AND/OR concatenation for search
                    if (
                        REQUEST.get(pre_name + "_AND") is True
                        or REQUEST.get(pre_name + "_AND") == "True"
                        or REQUEST.get(pre_name + "_AND") == "1"
                    ):
                        descr_dict[name + "_AND"] = True
                    else:
                        descr_dict[name + "_AND"] = False

            # put list value entry in dict
            if pre_name in REQUEST:
                descr_dict[listobj.listname] = entry

        return descr_dict

    security.declareProtected(viewPermission, "getValueListFromRequest")

    def getValueListFromRequest(self, REQUEST, field):
        """Filters multiple IDs out of the REQUEST Handler.

        :return: list with values from the REQUEST if there are any, otherwise empty list.
        """
        if not hasattr(REQUEST, field):
            return []

        values = REQUEST[field]
        if not isinstance(values, ListType):
            values = [values]
        return values

    ###########################################################################
    #                                                                         #
    # SimpleItem manage hooks overrides (deprecated but still in use)         #
    #                                                                         #
    ###########################################################################

    security.declareProtected(managePermission, "manage_afterAdd")

    def manage_afterAdd(self, item, container):
        """Manage the normal manage_afterAdd method of a SimpleItem.
        1. The Method looks for an existing instance of an Product Manager. If
           there is no Product Manager the function will raise a Programming Error.
        2. All forms defined in _dtml_dict will be installed.
        3. All tables defined in the model xml will be created.
        4. All manager lists defined in the manager xml will be created.
        5. If all went good the Manager will register himself at the Product Manager."""

        m_product = self.getManager(ZC.ZM_PM)

        # copy hack to avoid errors on copy/paste
        if not m_product:
            self.nocreate = 1

        # on copy, the tableHandler is there already
        if not hasattr(self, "tableHandler") or not self.tableHandler:

            # create table Handler
            tableHandler = TableHandler()
            table_def = getTableDefinition(self)

            # store it as subfolder
            self._setObject("tableHandler", tableHandler)

            # create list Handler
            listHandler = ListHandler()

            # store it as subfolder
            self._setObject("listHandler", listHandler)

            # initialize tables
            self.tableHandler.xmlInit(table_def, self.nocreate)

            # initialize lists
            self.listHandler.xmlInit(table_def, self.nocreate)

            # edit tracking lists
            self.createEditTrackingLists()

        # more manager specific _addTables
        if not self.nocreate:
            self._addTable()

        # register manager as child at product manager
        if IZopRAProduct.providedBy(self) and m_product:
            # we only register additional products as children
            m_product.registerChild(self)

    security.declareProtected(managePermission, "manage_beforeDelete")

    def manage_beforeDelete(self, item, container):
        """Clean up before deletion."""
        m_product = self.getManager(ZC.ZM_PM)

        # delete the manager owned tables from the database
        if self.delete_tables:
            self._delTable()

            # delete tables
            for table in self.tableHandler.getTableIDs():
                try:
                    self.tableHandler.delTable(table)
                except Exception:
                    # something went wrong (e.g. new table), ignore
                    pass

            # delete list references (multi and hierarchylists get their db tables deleted)
            for (table, column) in self.listHandler.getReferences():
                try:
                    self.listHandler.disconnectList(table, column, True)
                except Exception:
                    pass

            # delete lists
            for entry in self.listHandler.keys():
                try:
                    self.listHandler.delList(entry, True)
                except Exception:
                    pass

        # fi delete_tables

        # remove child manager
        m_product.removeChild(self)

    security.declareProtected(managePermission, "createEditTrackingLists")

    def createEditTrackingLists(self):
        """Create List objects for creator, editor and owner"""
        lobj = self.listHandler

        # all lists are singlelists pointing to table 'person' in ContactManager
        list_def = Column(None, "singlelist")
        list_def.setManager("ContactManager")
        list_def.setFunction("person()")
        labels = {"creator": "Creator", "editor": "Editor", "owner": "Owner"}

        # set up foreign lists if missing
        for listname in labels:

            # bind cols for each table
            list_def.setName(listname)
            list_def.setLabel(labels[listname])
            # edittrackers are invisible (except creator)
            if listname != "creator":
                list_def.setInvisible("1")

            for table in self.tableHandler.getTableIDs():
                # but check whether it exists before (some managers still overwrite those lists :/)
                # TODO: remove creator from tabledef of all managers, it is implicit
                # (but for generic masks they have to be defined extra to show up)
                if not lobj.hasList(table, listname):
                    lobj.connectList(self, table, list_def)

    ###########################################################################
    #                                                                         #
    # Additional Utility methods for mail handling                            #
    #                                                                         #
    ###########################################################################

    security.declareProtected(modifyPermission, "sendSimpleMail")

    def sendSimpleMail(self, mto, mfrom, subject, body):
        """Tries to send a email via the next available host."""
        mailHost = self.getObjByMetaType("Mail Host")
        if mailHost:
            try:
                mailHost.simple_send(mto, mfrom, subject, body)
                return True
            except Exception as exc:
                msg = "E-Mail Error: Could not send email %s from %s to %s: Error %s"
                msg = msg % (subject, mfrom, mto, str(exc))
                self.getManager(ZC.ZM_PM).writeLog(msg)
        else:
            msg = "E-Mail Error: Could not send email %s from %s to %s: No Mailhost found."
            msg = msg % (subject, mfrom, mto)
            self.getManager(ZC.ZM_PM).writeLog(msg)

        return False

    def sendSecureMail(
        self, mto, mfrom, subject="", message="", mcc=None, mbcc=None, charset="utf-8"
    ):
        """Tries to send a email via the next available secure mail host."""
        mailHost = self.getObjByMetaType("Secure Mail Host")
        if not mailHost:
            # try normal Mail Host, that was unified with SMH (after Plone 2)
            mailHost = self.getObjByMetaType("Mail Host")
        if mailHost:
            try:
                mailHost.secureSend(
                    message=message,
                    mto=mto,
                    mfrom=mfrom,
                    subject=subject,
                    mcc=mcc,
                    mbcc=mbcc,
                    charset=charset,
                )
                return True
            except Exception as exc:
                msg = "E-Mail Error: Could not send email %s from %s to %s: Error %s"
                msg = msg % (subject, mfrom, mto, str(exc))
                self.getManager(ZC.ZM_PM).writeLog(msg)
        else:
            msg = "E-Mail Error: Could not send email %s from %s to %s: No Mailhost found."
            msg = msg % (subject, mfrom, mto)
            self.getManager(ZC.ZM_PM).writeLog(msg)

        return False

    ###########################################################################
    #                                                                         #
    # Manager retrieval helper functions                                      #
    #                                                                         #
    ###########################################################################
    # those are in a mixin now (TODO: do we need the security declarations here?)
    security.declarePrivate("getManagerDownLoop")
    security.declarePrivate("getAllManagersDownLoop")

    security.declareProtected(viewPermission, "getHierarchyUpManager")
    security.declareProtected(viewPermission, "getHierarchyDownManager")
    security.declareProtected(viewPermission, "getAllManagersHierarchyDown")
    security.declareProtected(viewPermission, "getAllManagers")
    security.declareProtected(viewPermission, "topLevelProduct")

    ###########################################################################
    #                                                                         #
    # Update Handling                                                         #
    #   - do not forget to alter zopra_version (class attr) to new version    #
    ###########################################################################

    security.declareProtected(managePermission, "updateVersion")

    def updateVersion(self):
        """The general update function that is called by
        the ZopRAProduct or the manager management screen on update.
        Updates the manager."""
        # get class-version (new) and instance-version (old)
        version = self.zopra_version
        newver = Manager.zopra_version

        # try to get newver from manager-class
        # can be used to hold some managers back on an old version ... but why?
        if hasattr(self.__class__, "zopra_version"):
            newver = self.__class__.zopra_version

        # return string
        name = "%s: %s (%s)" % (self._class__.__name__, self.id, version)
        if self.getZopraType():
            name += " (%s)" % self.getZopraType()

        ret = [name]
        if newver != version:
            # we update
            if version < 1.8:
                # update eight: icon handler and new list handler
                did = self.toVersion1_8()
                for item in did:
                    ret.append(item)
            self.zopra_version = newver
            ret.append("Finished update to Version %s" % self.zopra_version)
        else:
            ret.append("No updates necessary")
        return "<br>".join(ret)

    #
    # Update single version functions (one per version, old versions should be removed someday)
    #

    security.declareProtected(managePermission, "toVersion1_8")

    def toVersion1_8(self):
        """Update to version 1.8 (only recreate table and list handlers)

        :return: message to signal update did happen
        :rtype: string"""
        msg = []

        # xml definition changes for different managers (maxshown / labelsearch options)
        # -> effective after reinstall of tablehandler/listhandler
        # replace table handler
        self.recreateTableHandlers()
        msg.append("Table Handler has been reinstalled.")

        # replace list handler
        self.recreateListHandlers()
        msg.append("List Handler has been reinstalled.")

        # dialog reload still manually

        msg.append("Updated to Version 1.8.")

        return msg

    #
    # Update helper functions
    #

    security.declareProtected(managePermission, "recreateTableHandlers")

    def recreateTableHandlers(self):
        """ Recreate table handler and reload all table objects with XML from table_dict."""

        # remove tableHandler
        self._delObject("tableHandler")
        self.tableHandler = None

        # create table Handler and store it as subfolder
        self._setObject("tableHandler", TableHandler())

        # initialize tables
        self.tableHandler.xmlInit(getTableDefinition(self), True)

    security.declareProtected(managePermission, "recreateListHandlers")

    def recreateListHandlers(self):
        """Recreate the list handler and reload all list objects with XML from
        table_dict as well as the editTracking Lists
        """

        # remove old listhandler
        self._delObject("listHandler")
        self.listHandler = None

        # create list Handler and store it as subfolder
        self._setObject("listHandler", ListHandler())

        # do not create tables in db (they already exist)
        self.listHandler.xmlInit(getTableDefinition(self), True)

        # edit tracking lists
        self.createEditTrackingLists()

        # reset table node caches (since tableprivate holds own listhandler copy -> wah!)
        for tabname in self.tableHandler:
            tobj = self.tableHandler[tabname]
            tobj.resetSearchTreeTemplate()
