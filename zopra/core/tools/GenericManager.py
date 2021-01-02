"""The GenericManager adds convenience methods on top of the ManagerPart."""

from copy import deepcopy
from types import DictType
from types import ListType

from zope.interface.declarations import implements

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgLabel import hgLabel

#
# ZopRA Imports
#
from zopra.core import ZC
from zopra.core import ClassSecurityInfo
from zopra.core import modifyPermission
from zopra.core.interfaces import IGenericManager
from zopra.core.ManagerPart import ManagerPart


class GenericManager(ManagerPart):
    """ Generic Manager """

    _className = "GenericManager"
    _classType = ManagerPart._classType + [_className]
    meta_type = _className
    implements(IGenericManager)

    """:generic configuration dict
    usage: _generic_config = {table: {key:value}}
    keys: basket_to     (True / False) - for showForm/showList-BasketButton
            basket_from   (True / False) - for newForm-BasketButton
            basket_active (True / False) - show basket at all
            visible       (True / False) - visible in zopra_manager_main_form
            show_fields   ([attrs])      - attributes for search result listing (editorial)
            required      ([attrs])      - required attributes for new/edit
            check_fields  ([{fieldname: function}] - call the module function for the field check when adding / editing an entry, function parameters are: attr_name, entry, mgr
            links         ([{'label':'<label>', 'link': '...%s', 'field': '<fieldname>', 'iconclass': 'icon-xyz'}]) - use info to add a link column to search result listing (editorial), linking to the given url (enhanced by the content of the field with the given fieldname), using the given label and icon class [url needs exactly one %s, normally used with the autoid field]
            specials      ([{'label': '<label>', fieldname: function}] - call the module function on every displayed entry in search result listing (editorial) to calculate the html content for a special column, label is used for table head, function parameters are: mgr, table, entry, lang, html
            importable    (True / False) - show in importForm for Import
            show_table_options    ({'create':1, 'search':1, 'list':1, 'import': (<target>, <label>), ...}) - define options for generic table overview (on manager_main_form)
            dependent     (True / False) - set to True to not show the create button on zopra_table_show_form / zopra_table_edit_form
    access via getGenericConfig(table)
    """
    _generic_config = {}

    #
    # Security
    #
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    # generic config helper methods

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

    # language / translations / working copies switched off

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

    #############################################
    # Generic Manager Hook Functions            #
    #   - to be overwritten for custom handling #
    #   they do nothing on their own!           #
    #############################################

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

    #############################################
    # Generic Manager Basic Methods             #
    #   - to be overwritten for custom handling #
    #   they provide a basic implementation      #
    #############################################

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

    def generateTableSearchTreeTemplate(self, table):
        """Virtual function for manager specific searchTree called by Table.getSearchTreeTemplate.
        The standard search tree is just the corresponding
        TableNode for the table. This function forwards to the
        overwritten version in ManagerPart which returns
        the TableNode. Overwrite it to produce a custom
        search tree and return the root node. To get the template for custom searches,
        use Table.getSearchTreeTemplate (caching is done there)."""
        return ManagerPart.generateTableSearchTreeTemplate(self, table)

    def getLabelString(self, table, autoid=None, descr_dict=None):
        """Return label for entry, overwrite for special functionality."""
        # return autoid, no matter what table
        if descr_dict:
            autoid = descr_dict.get(ZC.TCN_AUTOID, "")
        elif not autoid:
            return ""
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
        if len(cons.keys()) > 1:
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

    ############################################
    # Generic Manager generic basic functions  #
    #   - providing basic handling for entries #
    #                                          #
    ############################################

    def getEntry(self, table, autoid, lang=None, ignore_permissions=False):
        """Calls tableHandlers getEntry, overwrite for special functionality."""

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
        # Entry deletion, make sure to call superclass if overwritten.
        #            Does the calling of the prepareDelete hook and forwards
        #            to Table.deleteEntries.
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
