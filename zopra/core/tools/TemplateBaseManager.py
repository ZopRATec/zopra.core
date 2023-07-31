import json
import re
from binascii import hexlify
from copy import deepcopy
from random import randint
from urllib import quote

from AccessControl import getSecurityManager
from zope.component import getMultiAdapter

import icu
from zopra.core import ZC
from zopra.core import ClassSecurityInfo
from zopra.core import zopraMessageFactory as _
from zopra.core.Manager import Manager
from zopra.core.types import ListType
from zopra.core.types import StringType


protection_expression = re.compile(
    r"(mailto\:)?[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})"
)


class TemplateBaseManager(Manager):
    """Template Base Manager"""

    _className = "TemplateBaseManager"
    _classType = Manager._classType + [_className]
    meta_type = ""

    #
    # Security
    #
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    # languages v1
    _properties = Manager._properties + (
        {"id": "lang_default", "type": "string", "mode": "w"},
        {"id": "lang_additional", "type": "lines", "mode": "w"},
    )

    lang_default = "de"
    lang_additional = ()

    def getCurrentLanguage(self):
        try:
            from plone import api
            return api.portal.get_current_language()
        except Exception:
            return self.lang_default

    def startupConfig(self, REQUEST):
        """Function called after creation by manageAddGeneric"""
        # add table constraints
        pass

    def index_html(self, REQUEST):
        """forward one level up"""
        parent = self.aq_parent
        REQUEST.RESPONSE.redirect(parent.absolute_url())

    # configuration for main_form display (import / export)
    def getMainFormImportData(self, import_data, default_url):
        if isinstance(import_data, tuple):
            title = import_data[1] or "Import"
            url = "{}/{}".format(self.absolute_url(), import_data[0])
        else:
            title = "Import"
            url = default_url
        return (title, url)

    def getMainFormExportData(self, export_data, default_url):
        if isinstance(export_data, tuple):
            title = export_data[1] or "Export"
            url = "{}/{}".format(self.absolute_url(), export_data[0])
        else:
            title = "Export"
            url = default_url
        return (title, url)

    # disable caching
    def manage_afterAdd(self, item, container):
        """Disable Caching for managers running inside Plone."""
        Manager.manage_afterAdd(self, item, container)

        # disable caching for all tables
        for table in self.tableHandler.keys():
            self.tableHandler[table].manage_changeProperties(do_cache=False)

    #
    # Plone 4.3 Integration for Social Links and Content Actions
    #

    def social_links(self, context, REQUEST):
        """get the social links for the context"""
        # TODO: tweak the social links and document actions to display correct titles (e.g. for sins)
        # use special URL (with params) extracted from request instead of base url of the main Folder
        real_url_part1 = REQUEST.get("URL")
        real_url_part2 = REQUEST.get("QUERY_STRING")
        if real_url_part2:
            real_url = quote("%s?%s" % (real_url_part1, real_url_part2), safe="")
            repl_url1 = quote(real_url_part1, safe="")
            repl_url2 = quote(context.absolute_url(), safe="")
        else:
            # no query string -> no url replacement necessary
            real_url = None
        helper = getMultiAdapter((context, REQUEST), name=u"sl_helper")
        if not helper:
            return []
        render_method = "link"  # in original it's depending on Do-Not-Track-Setting; we force it anyway.
        rendered = []
        plugins = helper.plugins()
        for plugin in plugins:
            if plugin and getattr(plugin, render_method)():
                view = context.restrictedTraverse(plugin.view())
                html_generator = getattr(view, render_method, None)
                if html_generator:
                    html = html_generator()
                    if real_url:
                        # replace the url adding parts that are missing
                        html = html.replace(repl_url1, real_url).replace(
                            repl_url2, real_url
                        )
                    rendered.append({"id": plugin.id, "html": html})
        return rendered

    def content_actions(self, context, REQUEST):
        """get the default actions for the context"""
        context_state = getMultiAdapter((context, REQUEST), name=u"plone_context_state")
        result = []
        if context_state:
            # prepare urls
            real_url_part1 = REQUEST.get("URL")
            real_url_part2 = REQUEST.get("QUERY_STRING")
            if real_url_part2:
                real_url = quote("%s?%s" % (real_url_part1, real_url_part2), safe="")
                # longer version with template
                repl_url1 = quote(real_url_part1, safe="")
                # short version
                repl_url2 = quote(context.absolute_url(), safe="")
            else:
                # no query string -> no url replacement necessary
                real_url = None
            # now get actions
            actions = context_state.actions("document_actions")
            for action in actions:
                # replace the url adding parts that are missing
                new_url = action["url"]
                if real_url:
                    new_url = new_url.replace(repl_url1, real_url).replace(
                        repl_url2, real_url
                    )
                # build new dict for the action
                result.append(
                    {
                        "id": action["id"],
                        "url": new_url,
                        "link_target": action["link_target"],
                        "title": action["title"],
                        "description": action["description"],
                    }
                )
        return result

    #
    # Workflow Functions
    #
    def consistencyCheckTranslations(self, do=None):
        """Consistency Checker for translations"""
        special_fields = [
            "autoid",
            "hastranslation",
            "istranslationof",
            "iscopyof",
            "language",
        ]
        import logging

        logger = logging.getLogger("ZopRA")
        for table in self.tableHandler.keys():
            if self.doesTranslations(table):
                count = 0
                logger.info("Checking {}".format(table))
                tobj = self.tableHandler[table]
                coldefs = tobj.getColumnDefs()
                translations = tobj.getEntryList(
                    constraints={"istranslationof": "_not_NULL", "iscopyof": "NULL"}
                )
                for translation in translations:
                    entry_diff = {}
                    log_diff = {}
                    orig = tobj.getEntry(translation["istranslationof"])
                    for key in coldefs:
                        thetype = coldefs.get(key)["TYPE"]
                        if (
                            thetype not in ["string", "memo"]
                            and key not in special_fields
                        ):
                            val_orig = orig[key]
                            val_tran = translation[key]
                            if thetype in ["multilist", "hierarchylist"]:
                                val_orig = sorted(val_orig)
                                val_tran = sorted(val_tran)
                            if val_orig != val_tran:
                                entry_diff[key] = orig[key]
                                log_diff[key] = orig[key]
                                log_diff["{}_trans".format(key)] = translation[key]
                                log_diff["{}_type".format(key)] = thetype
                    if entry_diff:
                        entry_diff["autoid"] = orig["autoid"]
                        log_diff["autoid"] = orig["autoid"]
                        log_diff["trans_autoid"] = translation["autoid"]
                        if do:
                            self.updateTranslation(table, entry_diff)
                        logger.info("diff found: {}".format(str(log_diff)))
                        count += 1
                if count:
                    logger.info(
                        "Corrected {} entries with differences for table {}".format(
                            count, table
                        )
                    )
        logger.info("Done")

    def doesWorkflows(self, table):
        """"""
        return False

    def getStateTransferInfo(self, table, entry):
        """Overwrite for determining label and action for stateswitch button."""
        return {}

    #
    # security and permission functions
    #

    def checkTablePermission(self, table):
        """Table permission check for zopra_manager_main_form, when visibility is False"""
        # default: False means False, leave it at that
        return False

    def getListOwnUsers(self, table):
        """returns constraints if the user should only see own entries"""
        user = getSecurityManager().getUser()
        return {"user_login": user.getUserName()}

    def getPermissionInfo(self, table, permission):
        """Overwrite for special permission settings. Returns True, if user has one of the roles, that have the requested permission."""
        # Default definition
        # permissions: list_edit, table_create, table_show, table_edit, table_list, table_delete, table_show_own, table_list_own, table_edit_own, table_delete_own
        # for details on the "own"-permissions, see tud.zopra.erp

        # ZopRAAuthor can list_edit, table_show / table_edit / table_list
        # ZopRAReviewer can publish if publishing is active
        stddef = {
            "list_edit": ["ZopRAAdmin", "ZopRAAuthor", "ZopRAReviewer"],
            "table_create": ["ZopRAAdmin", "ZopRAAuthor", "ZopRAReviewer"],
            "table_show": ["ZopRAAdmin", "ZopRAAuthor", "ZopRAReviewer"],
            "table_edit": ["ZopRAAdmin", "ZopRAAuthor", "ZopRAReviewer"],
            "table_list": ["ZopRAAdmin", "ZopRAAuthor", "ZopRAReviewer"],
            "table_delete": ["ZopRAAdmin", "ZopRAReviewer"],
            "table_publish": ["ZopRAAdmin", "ZopRAReviewer"],
        }
        # check for these roles
        roles = stddef.get(permission, [])
        if not roles:
            return False
        user = getSecurityManager().getUser()
        return user.has_role(roles, self)

    def getPermissionEntryInfo(self, table, entry):
        """Return permissions that current user with his roles has for an entry in a certain state"""
        # we add additional security handling for template based managers
        # this isn't the final solution, this should be integrated with entry-permissions and gui-permissions
        # which were used before, unfortunately the handling was centered around the security-manager
        # this handling works with zope roles only, but covers workflows and working copies

        # no workflows
        # working copies -> author can do show / edit, Reviewer can delete
        # no working copies -> author can do anything (show / edit / delete)
        user = getSecurityManager().getUser()
        perms = []

        if not self.doesWorkingCopies(table):
            # check Author
            if user.has_role(["ZopRAAuthor", "ZopRAAdmin"], self):
                perms = ["show", "edit", "delete"]
        else:
            # check Author
            if user.has_role("ZopRAAuthor", self):
                perms = ["show", "edit"]
            # check Reviewer (for del)
            if user.has_role(["ZopRAReviewer", "ZopRAAdmin"], self):
                perms = ["show", "edit", "delete"]

        return perms

    #
    # Working Copy Functions
    #

    def doesWorkingCopies(self, table):
        """"""
        return False

    def getWorkingCopies(self, table):
        """"""
        tobj = self.tableHandler[table]
        cons = {"iscopyof": "_not_NULL"}
        return tobj.getEntryList(constraints=cons, ignore_permissions=True)

    def getWorkingCopy(self, table, autoid):
        """Return the working copy or None"""
        if self.doesWorkingCopies(table):
            copy = self.tableHandler[table].getEntryList(
                constraints={"iscopyof": autoid}, ignore_permissions=True
            )
            if copy:
                return copy[0]
        return None

    def createWorkingCopy(self, table, entry):
        # used to create a working copy of an entry
        tobj = self.tableHandler[table]

        # check if a WoCo exists, return it instead of creating
        check = tobj.getEntries(entry["autoid"], "iscopyof")
        if check:
            return check[0]

        # copy the objects
        copy = deepcopy(entry)
        # set copy data
        copy["iscopyof"] = copy["autoid"]
        copy["autoid"] = None
        # add to database
        autoid = tobj.addEntry(copy)
        # fill new autoid
        copy["autoid"] = int(autoid)
        # return copy for further usage
        return copy

    def updateWorkingCopy(self, table, entry_diff):
        # this is useful when the edit-functionality of another table makes changes to entries of a table using working copies
        # and when a working copy is confirmed and there is a translation of the entry that also has a working copy
        autoid = entry_diff.get("autoid")
        cons = {"iscopyof": autoid}
        tobj = self.tableHandler[table]
        res = tobj.getEntryList(constraints=cons, ignore_permissions=True)
        if res:
            wc = res[0]
            for key in entry_diff:
                if key not in ["autoid", "iscopyof"]:
                    wc[key] = entry_diff[key]
            # update the working copy entry
            tobj.updateEntry(wc, wc["autoid"])
            return True

    # the working copy machinery needs the deepcopy python func in scripts
    def deepcopy(self, obj):
        return deepcopy(obj)

    #
    # Translation Functions
    #

    def doesTranslations(self, table):
        """"""
        return False

    def updateTranslation(self, table, entry_diff):
        # this is useful when the edit-functionality of another table makes changes to entries of a table using translations
        autoid = entry_diff.get("autoid")
        cons = {"istranslationof": autoid}
        tobj = self.tableHandler[table]
        types = tobj.getColumnTypes()
        res = tobj.getEntryList(constraints=cons, ignore_permissions=True)
        if res:
            eng = res[0]
            # need a dict for the changed stuff to not accidentally overwrite the working copy values on updateWorkingCopy
            eng_diff = {}
            for key in entry_diff:
                if types.get(key) not in ["string", "memo"] and key not in [
                    "autoid",
                    "hastranslation",
                    "istranslationof",
                    "iscopyof",
                    "language",
                ]:
                    eng[key] = entry_diff[key]
                    eng_diff[key] = entry_diff[key]
            # update the english entry
            tobj.updateEntry(eng, eng["autoid"])
            eng_diff["autoid"] = eng["autoid"]
            if self.doesWorkingCopies(table):
                self.updateWorkingCopy(table, eng_diff)
            return True

    def getTranslation(self, table, autoid, lang):
        # retrieve translation of the entry with the autoid, if available
        # check if trenslations are activated
        if not self.doesTranslations(table):
            return autoid
        # check if lang is valid and not default
        if lang == self.lang_default or lang not in self.lang_additional:
            return autoid
        # build constraints
        cons = {"istranslationof": autoid, "language": lang}
        # make sure we get the original entry
        if self.doesWorkingCopies(table):
            cons["iscopyof"] = "NULL"
        tobj = self.tableHandler[table]
        try:
            res = tobj.getEntryAutoidList(constraints=cons)
            if res:
                return res[0]
        except Exception:
            pass

        # fallback to original entry
        return autoid

    def removeTranslationInfo(self, table, autoid):
        """after deleting a translation entry, the orginal entry needs to be corrected (removing the hastranslation marker)"""
        # the entry with autoid is a default language entry, whose translation was deleted
        tobj = self.tableHandler[table]
        entry = tobj.getEntry(autoid, ignore_permissions=True)
        # check for remaining translations
        translations = tobj.getEntryAutoidList(constraints={"istranslationof": autoid})
        if not translations:
            # remove the hastranslation marker
            entry["hastranslation"] = 0
            tobj.updateEntry(entry, autoid)
            # check for working copies
            workingcopy = self.getWorkingCopy(table, autoid)
            if workingcopy:
                # use the original autoid and the change as entry_diff
                self.updateWorkingCopy(table, {"autoid": autoid, "hastranslation": 0})

    def selectAdditionalLanguage(self, request):
        """Hook for the language switcher on the translation form."""
        # for now, we only allow 1 additional language
        if self.lang_additional:
            return self.lang_additional[0]
        else:
            return None

    #
    # Table and Entry centered Functions
    #

    def getFilteredColumnDefs(self, table, vis_only=False, edit_tracking=False):
        """Indirection to retrieve column defs, allows addition and removal before listing"""
        tobj = self.tableHandler[table]
        res = tobj.getColumnDefs(vis_only=vis_only, edit_tracking=edit_tracking)
        if "owner" in res:
            del res["owner"]
        if "creator" in res:
            del res["creator"]
        if "editor" in res:
            del res["editor"]
        return res

    def checkDefaultWildcardSearch(self, table):
        """Toggle for Wildcard Search. Overwrite this function and return True
        for the tables that will then automatically use wildcard search for all text
        fields.
        """
        return True

    def getEntryListCountProxy(self, table, constraints=None):
        """Proxy for Table.getEntryListCount using searchTreeTemplate"""
        tobj = self.tableHandler[table]
        root = tobj.getSearchTreeTemplate()
        if constraints:
            root.setConstraints(constraints)
        return tobj.requestEntryCount(root)

    def calculatePaginationPages(self, rowcount, count):
        return (rowcount + count - 1) // count

    def getEntryListProxy(
        self,
        table,
        show_number=None,
        start_number=None,
        idfield="autoid",
        constraints=None,
        order=None,
        direction=None,
        constr_or=False,
    ):
        """Proxy for Table.getEntryList using searchTreeTemplate"""
        tobj = self.tableHandler[table]
        root = tobj.getSearchTreeTemplate()
        if order:
            root.setOrder(order, direction)
        else:
            root.setOrder(idfield, direction)
        if constraints:
            root.setConstraints(constraints)
        if constr_or:
            fi = root.getFilter()
            fi.setOperator(fi.OR)
        return tobj.requestEntries(
            root, show_number, start_number, ignore_permissions=True
        )

    def isHierarchyList(self, listname):
        # check if a List with that name is referenced by a table attribute
        hlists = []
        for table in self.tableHandler.keys():
            hlists.extend(self.listHandler.getLists(table, ["hierarchylist"]))
        for lobj in hlists:
            if lobj.listname == listname:
                return True
        return False

    def handleHierarchyListOnSearch(self, table, cons):
        """Add the subtree to a given node for all hierarchy lists of the table (all children of all levels below that node)"""
        # TODO: use Manager.getHierarchyListConfig to steer this behaviour
        hlists = self.listHandler.getLists(table, ["hierarchylist"])
        listnames = [hlist.listname for hlist in hlists]
        for key in cons:
            if key in listnames:
                selectList = []
                for item in cons[key]:
                    selectList.append(item)
                    selectList.extend(
                        self.listHandler.getList(
                            table, key
                        ).getHierarchyListDescendants(item)
                    )
                cons[key] = selectList

    def prepareHierarchylistDisplayEntries(self, entries):
        """sort the entries into a tree, add level key and return flattened and sorted list"""
        # TODO: implement
        # this is used by zopra_list_edit_form
        # TODO: further check why this exists
        for entry in entries:
            entry["level"] = 0
        return entries

    def sortListEntriesForDisplay(self, table, attr_name, entries):
        """sort list entries (for singlelist / multilist edit widget display), overwrite for custom sorting.
        The attribute (attr_name) has to be listed in _generic_config in 'sortables', otherwise this method will not be called."""
        # TODO: use rank as possible sorting field (reintroduce rank to the list edit form, how to indicate rank sorting?)
        # TODO: make sure translations are sorted correctly (sort by value_en e.g.?)
        # Default: sort normally
        return sorted(entries, key=lambda item: item["value"])

    def prepareValuesForEdit(self, attr_name, field, entry, request, validation_errors):
        """Request data only supersedes the entry data when validation errors occured (to retain user input), after saving, the (potentially altered) entry data is used"""
        if not validation_errors:
            return entry.get(attr_name)
        else:
            val = request.get(attr_name)
            if field["TYPE"] in ["multilist", "hierarchylist"]:
                if not val:
                    val = []
                elif not isinstance(val, ListType):
                    val = [val]
            return val

    def prepareConstraintsForOutput(self, attr_value, attr_type):
        """Search Param Visualisation preparation"""
        # general behaviour: this is called by the search result template to generate
        # nicer values for constraint display
        # problem: complex search with sub-tables is ignored, the prefixed constraints get treated as string
        #  (resulting in empty labels and autoids in the constraint display for lists
        # TODO: Fix the sub-table workaround and check constraints for every sub-table separately -> need sub-table layout for that

        # for memo and string fields, ListTypes can arrive here, and for list fields as well, check type
        if attr_type == "string" and isinstance(attr_value, ListType):
            # strip the <any>-Operator (*) from each value part and join them by space
            return " ".join(map(lambda x: str(x).strip("*"), attr_value))
        elif attr_type in ["multilist", "singlelist"]:
            # check multilists, the search widget delivers [None] when item was selected and deselected
            return [value for value in attr_value if value]
        elif attr_value == "NULL":
            # value is explicitly NULL (except for checkboxes)
            if attr_type != "bool":
                message = _("zopra_widget_not_set", default=u"<not set>")
                return self.translate(message, domain="zopra")
        elif attr_value == "_not_NULL":
            # value is explicitly not NULL (except for checkboxes)
            if attr_type != "bool":
                message = _("zopra_widget_set_any", default=u"<any value>")
                return self.translate(message, domain="zopra")
        else:
            return attr_value
        return attr_value

    def getChangeDate(self, table, autoid):
        """get the last change / creation date of the entry with the given autoid"""
        if not autoid or not table:
            return None
        # additionally check for request and not being on search form
        request = self.REQUEST
        if (
            request
            and request.get("PUBLISHED")
            and request.get("PUBLISHED").getId() == "zopra_table_search_form"
        ):
            return None
        tobj = self.tableHandler[table]
        root = tobj.getTableNode()
        root.setConstraints({"autoid": autoid})
        sql = root.getSQL(
            col_list=["entrydate", "changedate"], distinct=True, checker=self
        )
        results = self.getManager(ZC.ZM_PM).executeDBQuery(sql)
        if results:
            # use changedate, if set, entrydate otherwise
            date = results[0][1] or results[0][0]
            # return a user friendly and localization-aware formatted representation using a helper function (plone wrapper)
            return self.toLocalizedTime(date)

    def generateMailLink(self, email):
        """generate link string from email to avoid tal:attributes quoting of scrambled email string"""
        return '<a href="mailto:%s">%s</a>' % (email, email)

    def encrypt_ordtype(self, s):
        # listcomprehensions nested and with evaluation expression for speed
        # using string concat instead of print formatting for speed
        return "".join(
            [
                whichCode == 0
                and ch
                or whichCode == 1
                and "&#" + str(ord(ch)) + ";"
                or "&#x" + str(hexlify(ch)) + ";"
                for (ch, whichCode) in [(z, randint(0, 2)) for z in s.group()]
            ]
        )

    def emailProtect(self, body_txt=""):
        # use protection_expr to replace mailadresses by scrambled strings using encrypt_ordtype
        return protection_expression.sub(self.encrypt_ordtype, body_txt)

    def correctUTF8(self, value):
        # correct a utf8 native string for display on templates
        try:
            value.decode("utf-8")
            # no error means we had latin-1 or ascii, which decodes to utf-8 easily
        except Exception:
            # this is already utf-8, ascii-encoder raised an error
            value = value.decode("latin-1")
        return value

    #
    # Edit Layout Info
    #

    def getLayoutInfo(self, table, action):
        """Returns grouping information for layout"""
        # allow external scripts
        res = []
        name = "getLayoutInfo_%s" % (self.getClassName())
        if hasattr(self, name):
            res = getattr(self, name)(table, action)
        if res:
            return res

        if hasattr(self, "getLayoutInfoHook"):
            res = self.getLayoutInfoHook(table, action)
        if res:
            return res

        # default
        vis_only = action not in ["create", "edit", "show"]
        tobj = self.tableHandler[table]
        fields = tobj.getColumnDefs(vis_only=vis_only, edit_tracking=False).keys()
        res = [{"label": "Datenfelder", "fields": fields}]
        return res

    def getHelpTexts(self, table):
        """helptexts"""
        # allow external scripts
        res = {}
        name = "getHelpTexts_%s" % (self.getClassName())
        if hasattr(self, name):
            res = getattr(self, name)(table)
        if res:
            return res

        if hasattr(self, "getHelpTextsHook"):
            res = self.getHelpTextsHook(table)
        if res:
            return res

        return {}

    def getDefaultSearchValues(self, table):
        """return default value dict for search"""
        return {}

    def getDefaultCreateValues(self, table):
        """return default value dict for creation"""
        return {}

    #
    # Diff support for working copies
    #

    def getDiff(self, entrya, entryb):
        """extract the keys of differences between two complete entries"""
        diff = {}
        for key in entrya:
            if key in ["autoid", "permission", "iscopyof", "entrydate", "changedate"]:
                continue
            vala = entrya[key]
            # weak fix for multilist notes
            valb = entryb.get(key)
            if isinstance(vala, ListType):
                vala.sort()
            elif isinstance(vala, StringType):
                vala = vala.replace("\r\n", "\n")
            if isinstance(valb, ListType):
                valb.sort()
            elif isinstance(valb, StringType):
                valb = valb.replace("\r\n", "\n")
            if vala != valb:
                diff[key] = 1
        return diff.keys()

    def getCopyDiff(self, table, autoid):
        """find the copy or original and the diff"""
        tobj = self.tableHandler[table]
        entry = tobj.getEntry(autoid, ignore_permissions=True)
        copy = None
        orig = None
        if entry.get("iscopyof"):
            copy = entry
            orig = tobj.getEntry(entry.get("iscopyof"), ignore_permissions=True)
        else:
            orig = entry
            res = tobj.getEntryList(
                constraints={"iscopyof": entry.get("autoid")}, ignore_permissions=True
            )
            if res:
                copy = res[0]
        if copy and orig:
            return [orig, copy, self.getDiff(orig, copy)]

    def dictIntersect(self, dicta, dictb):
        """intersect the keys of the two dicts, return list"""
        return list(set(dicta).intersection(set(dictb)))

    def getDiffLabels(self, table, entry):
        """get the labels for the diff keys"""
        labels = []
        tobj = self.tableHandler[table]
        for attr in self.getDiff(entry, self.zopra_forceOriginal(table, entry)):
            label = tobj.getLabel(attr)
            if not label:
                pos = attr.find("notes")
                if pos != -1 and attr[pos + 5 :].isdigit():
                    label = tobj.getLabel(attr[:pos])
            if label not in labels:
                labels.append(label)
        return labels

    #
    # Display Support Functions
    #

    # the really nice formatting is bad for parsing on edit -> dropped it for now
    # def formatCurrency(self, value):
    #    """Format value as currency with 1000er breaker points and one comma"""
    #    return re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1.", ('%.2f' % value).replace('.', ','))

    def alphabeticalSort(self, entries, key_value, lang, fallback_key=None):
        """sort a list of dictionaries alphabetical by one key value"""
        # make sure language is supported
        if not (lang == self.lang_default or lang in self.lang_additional):
            # default is python alphanumerical sorting
            if fallback_key:
                return sorted(entries, key=lambda entry: entry[key_value] or entry[fallback_key])
            else:
                return sorted(entries, key=lambda entry: entry[key_value])
        # use the pretty icu sorting (language dependent)
        collator = icu.Collator.createInstance(icu.Locale(lang))  # language=de, en
        if fallback_key:
            return sorted(entries, key=lambda entry: collator.getSortKey(entry[key_value] or entry[fallback_key] or ""))
        else:
            return sorted(entries, key=lambda entry: collator.getSortKey(entry[key_value] or ""))

    def reorderColsAccordingly(self, cols, order):
        """Order the list cols according to the order in the list order"""
        newlist = []
        for onecol in order:
            if onecol in cols:
                newlist.append(onecol)
        for onecol in cols:
            if onecol not in newlist:
                newlist.append(onecol)
        return newlist

    def getRelatedEntries(self, autoid, table, attribute, lang=None):
        """get Entries of table that are connected to an entry of another
        table with autoid autoid via multilist named attribute (backref).
        If lang is given, the result list will be filtered to contain
        1) only entries of that language (if it is the default language) or
        2) mixed entries of translations and originals (when no translation exists)."""
        #  get list object
        lobj = self.listHandler.getList(table, attribute)
        # get getEntry function of table
        getEntry = self.tableHandler[table].getEntry
        # use list comprehension to get the entries for all references in the multilist
        res = [
            getEntry(otherid, ignore_permissions=True)
            for otherid in lobj.getMLRef(None, autoid)
        ]
        # if lang is given and table allows translations, check to remove the language copies or originals
        if self.doesTranslations(table) and lang:
            if lang == self.lang_default:
                # in the default language, only the entries with that language are selected
                res = [item for item in res if item["language"] == lang]
            elif lang in self.lang_additional:
                rem = []
                for item in res:
                    if item["language"] == lang:
                        # set original for removal
                        rem.append(item["istranslationof"])
                    elif item["language"] != self.lang_default:
                        # other language than default and lang, remove
                        rem.append(item["autoid"])
                # remove the marked entries, resulting in a list of tranlated entries and remaining non-translated originals
                res = [item for item in res if item["autoid"] not in rem]
        return res

    def prepareLinks(self, text):
        """find all links in text starting with www or http and make them into real links"""
        # expression to find mailto and http/https urls, which will be made into real links
        expr = re.compile(r"((?:mailto\:|https?\://){1}\S+)\s*?(\[.*?\])")

        # internal function for link replacement
        def apply(s):
            try:
                # get url and possible label
                url = s.group(1)
                label = s.group(2)

                # use url as label, if no label is given
                if not label or label == "[]":
                    label = url
                else:
                    # label given, remove the parentheses
                    label = label[1:-1]
                # build link, insert url and label
                return '<a href="%s" target="_blank">%s</a>' % (url, label)
            except Exception:
                # something wrong, do not touch the original string
                return s.group()

        # apply the function to all hits of the expression
        return expr.sub(apply, text or "")

    def removeLinks(self, text):
        """find all links in text starting with www or http and remove the []-label"""
        expr = re.compile(r"((?:mailto\:|https?\://){1}\S+)\s*?(\[.*?\])")

        def apply(s):
            try:
                # only extract the url
                url = s.group(1)
                return url
            except Exception:
                # single url found
                return s.group()

        return expr.sub(apply, text)

    def val_translate(self, name, descr_dict, attr_name=None):
        """get list object, translate attr id from dict into value"""
        return (
            self.listHandler[name].getValueByAutoid(
                descr_dict.get(attr_name or name, "")
            )
            or ""
        )

    def py2json(self, object, encoding="utf-8"):
        """translate python object to json"""
        return json.dumps(object).decode("raw-unicode-escape").encode(encoding)

    def json2py(self, jsonstring, encoding="utf-8"):
        """translate json to python object"""
        return json.loads(jsonstring, encoding)

    # Button and REQUEST handling
    def getTableEntryFromRequest(self, table, REQUEST, prefix="", search=False):
        """Builds a dict from a REQUEST object.
        Overridden to correct float and currency values and handle empty lists on search.

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
        entry = Manager.getTableEntryFromRequest(self, table, REQUEST, prefix, search)
        tobj = self.tableHandler[table]
        col_types = tobj.getColumnTypes()
        for col in col_types:
            # comma and point in float and currency values
            if col_types[col] in (ZC.ZCOL_FLOAT, ZC.ZCOL_CURR):
                # only convert if there is something to convert
                if entry.get(col):
                    entry[col] = ("%s" % entry.get(col, "")).replace(",", ".")
            # this removes empty list entries from the resulting entry for search
            # (where adding and removing a selection from a multilist results in an empty list being transmitted as search param)
            if (
                search
                and col_types[col] in (ZC.ZCOL_MLIST, ZC.ZCOL_HLIST)
                and entry.get(col) == []
            ):
                del entry[col]

        return entry

    def filterRealSearchConstraints(self, constraints):
        """check if there are any real constraints in the dictionary"""
        for key in constraints:
            if not key.endswith("_AND"):
                return True
        return False
