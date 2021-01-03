"""The ZopRAProduct is the center of a ZopRA installation and handles the
database connection."""

import pickle
from datetime import datetime
from difflib import HtmlDiff
from time import strftime

from zope.interface import implements

from PyHtmlGUI.kernel.hgTable import hgTable
from PyHtmlGUI.widgets.hgCheckBox import hgCheckBox
from PyHtmlGUI.widgets.hgLabel import hgLabel
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from PyHtmlGUI.widgets.hgVBox import hgVBox
from zopra.core import HAVE_PLONE
from zopra.core import HTML
from zopra.core import ZC
from zopra.core import ZM_CM
from zopra.core import ZM_IM
from zopra.core import ZM_PM
from zopra.core import ZM_PNM
from zopra.core import ClassSecurityInfo
from zopra.core import getSecurityManager
from zopra.core import managePermission
from zopra.core import modifyPermission
from zopra.core import viewPermission
from zopra.core.connector.SqlConnector import getConnector
from zopra.core.dialogs import dlgLabel
from zopra.core.dialogs import getStdDialog
from zopra.core.interfaces import IZopRAManager
from zopra.core.interfaces import IZopRAProduct
from zopra.core.lists.ListHandler import ListHandler
from zopra.core.Manager import Manager
from zopra.core.tables.TableHandler import TableHandler
from zopra.core.utils import getZopRAPath


TN_LOG = "log"
TCN_TABLE = "tabid"
TCN_ACTION = "action"
TCN_ENTRYID = "entryid"
TCN_BACKUP = "backup"


class ZopRAProduct(Manager):
    """Product class is based on Manager"""

    _className = ZM_PM
    _classType = Manager._classType + [_className]
    meta_type = _className

    suggest_id = "pm"
    suggest_name = "Product Manager"

    implements(IZopRAProduct)

    # make edit_tracking_cols a class variable for access by other managers
    _edit_tracking_cols = ZC._edit_tracking_cols

    _manager_table_dict = {
        "log": {
            "tabid": {ZC.COL_TYPE: "int8", ZC.COL_LABEL: "Table ID"},
            "action": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: "Action"},
            "entryid": {ZC.COL_TYPE: ZC.ZCOL_INT, ZC.COL_LABEL: "Entry Autoid"},
            "backup": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: "Backup"},
            "username": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: "Username"},
            "change_datetime": {
                ZC.COL_TYPE: ZC.ZCOL_STRING,
                ZC.COL_LABEL: "Change Datetime",
            },
            "entrydiff_before": {
                ZC.COL_TYPE: ZC.ZCOL_MEMO,
                ZC.COL_LABEL: "Entry before Change",
            },
            "entrydiff_after": {
                ZC.COL_TYPE: ZC.ZCOL_MEMO,
                ZC.COL_LABEL: "Entry after Change",
            },
        },
        "children": {"id": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""}},
        "config": {
            "config_str": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
            "key1": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
            "value": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
            "mgrtype": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
            "mgrid": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
            "parent": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
            "notes": {ZC.COL_TYPE: ZC.ZCOL_STRING, ZC.COL_LABEL: ""},
        },
    }

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__(self, id=None, title="", connection_id="", nocreate=0, zopratype=""):
        """Constructor"""

        Manager.__init__(self, title, id, nocreate, zopratype)
        self.children = []
        self.connection_id_temp = connection_id

        # later on initialized in manage_afterAdd when access to db is possible
        self.connector = None

    def manage_afterAdd(self, item, container):
        """Manage the normal manage_afterAdd method of a SimpleItem."""

        if not self.connector:
            # create a sql connector
            connector = getConnector(self, "connector", self.connection_id_temp)
            self._setObject("connector", connector)

        # on copy, the handlers are already present
        if not self.tableHandler:
            lHandler = ListHandler()
            self._setObject("listHandler", lHandler)
            tHandler = TableHandler()
            self._setObject("tableHandler", tHandler)

            self._installDefaultFiles()

            # add the manager tables to the database
            # do not log before the creation of the log-table ;)
            for table in self._manager_table_dict:
                self.tableHandler.addTable(
                    table, self._manager_table_dict[table], self.nocreate, log=False
                )

            # we also need the trackinglists for products
            self.createEditTrackingLists()

        # disable cache for log table
        self.tableHandler["log"].manage_changeProperties(do_cache=False)

    def manage_beforeDelete(self, item, container):
        """Manage the normal manage_beforeDelete method of a
        SimpleItem.
        """

        if self.delete_tables:

            # delete the manager tables from the database
            for table in self.tableHandler.keys():
                self.tableHandler.delTable(table, False)

    def manage_afterClone(self, item):
        """Manage the normal manage_afterClone method of a
        SimpleItem.
        """
        self.nocreate = True
        # call parent method
        Manager.manage_afterClone(self, item)

    def _installDefaultFiles(self):
        """Installes the default files like standard_html_header"""
        parent = self.getContainer()
        if not parent:
            return None

        # in plone, most of this is not needed
        if HAVE_PLONE:
            # use python script for redirect
            content = "##title=Redirect to ZopRA Editorial\ncontext.REQUEST.RESPONSE.redirect(container.absolute_url() + '/zopra_main_form')"
            parent.manage_addProduct["PythonScripts"].manage_addPythonScript(
                "index_html"
            )
            script = parent["index_html"]
            script.write(content)
            # set the properties for zopra_path in parent
            # for more complex setups, zopra_path also needs to be set in the parents parent (do so manually)
            parent.manage_addProperty("zopra_path", self.getId(), "string")
        else:
            # standard_html_header DTMLDocument
            self._createDTMLHelper("standard_html_header", parent)

            # standard_html_footer DTMLDocument
            self._createDTMLHelper("standard_html_footer", parent)

            # standard_html_footer DTMLDocument
            self._createDTMLHelper("standard_error_message", parent)

            # standard_html_footer DTMLDocument
            self._createDTMLHelper("unauthorized_html_header", parent)

            # standard_html_footer DTMLDocument
            self._createDTMLHelper("unauthorized_html_footer", parent)

            # index_html DTMLDocument
            content = "<dtml-call expr=\"RESPONSE.redirect('%s')\">"
            content = content % self.virtual_url_path()
            self._createDTMLHelper("index_html", parent, content)

            # logged_out DTMLDocument
            done = self._createDTMLHelper("logged_out", parent)
            if done:
                try:
                    obj = parent.logged_out
                    obj.manage_permission("View", ["Anonymous"], 1)
                except Exception:
                    # ignore
                    pass
        # TODO: check why and for what this is needed
        # dirHome Property
        if "dirHome" not in parent.propertyIds():
            dirHome = parent.virtual_url_path()
            parent.manage_addProperty("dirHome", dirHome, "string")

    def _createDTMLHelper(self, name, parent, content=None):
        """helper method that constructs the dtml objects used by all managers"""
        # get the content from dtml directory and create DTMLDocument
        if name not in parent.objectIds():
            if not content:
                content = open("%s/dtml/%s" % (getZopRAPath(), name), "r")
            parent.manage_addDTMLDocument(name, "ZopRA", content)
            return True
        return False

    #
    # Logging Table Wrapper Functions
    #

    def addTable(self, name, table_dict, edit_tracking=True, log=True):
        # Implements an auditing mechanismen for add database tables.
        self.connector.createTable(name, table_dict, edit_tracking=edit_tracking)

        if log:
            self.writeLog("add table %s" % name)

    def delTable(self, name, log=True):
        # Deletes the database table and logs the action.
        self.connector.dropTable(name)
        if log:
            self.writeLog("delete table %s" % name)

    def createIndex(self, table, column, log=True):
        # forward to connector, handling is done there
        self.connector.createIndex(table, column)
        if log:
            self.writeLog("add index on %s.%s" % (table, column))

    def addFunctionSql(self, name, param, output, sql, log=True):
        # create an sql function
        self.connector.addFunctionSql(name, param, output, sql)
        if log:
            self.writeLog("add sql function %s" % name)

    def addFunction(self, name, function, log=True):
        # add a database function and log the action.
        self.connector.addFunction(function)
        if log:
            self.writeLog("add function %s" % name)

    def delFunction(self, name, param, log=True):
        # delete a database function and log the action
        self.connector.delFunction(name, param)
        if log:
            self.writeLog("del function %s" % name)

    #
    # ZopRA Component registration
    #

    # TODO: do we really need this?
    # DB-Registration didn't work out due to db-reinstall of ProductManagers
    # attribute-Registration (which is done here) won't work out due to zope-reinstall of ProductManagers
    # the get-Functions use live-search in the containing folder anyway.
    def registerChild(self, child):
        """Implements a register method for ZopRA Components."""
        # print 'bchilds: %s' % self.children
        # print 'registerChild: %s' % child.getId()
        child_list = []

        for child_id in self.children:
            child_list.append(child_id)

        child_list.append(child.getId())

        self.children = child_list

    def removeChild(self, child):
        """Implements a register method for ZopRA Components."""
        # print 'bchilds: %s' % self.children
        # print 'removeChild: %s' % child.getId()
        child_list = []

        remove_id = child.getId()
        for child_id in self.children:
            if child_id != remove_id:
                child_list.append(child_id)

        self.children = child_list

        # print 'achilds: %s' % self.children

    def getChild(self, child_id):
        """Looks in the environment and returns the first child that
        has the \a childid.
        """
        container = self.getContainer()
        if container and hasattr(container, "objectValues"):
            for obj in container.objectValues():
                if hasattr(obj, "id") and obj.id == child_id:
                    return obj

    def getChildren(self):
        """Returns all known child manager of the environment."""
        child_list = []

        container = self.getContainer()

        if hasattr(container, "objectValues"):

            for obj in container.objectValues():

                if IZopRAManager.providedBy(obj):
                    child_list.append(obj)
        return child_list

    security.declareProtected(viewPermission, "getNaviManagerUrls")

    def getNaviManagerUrls(self, zopratype, admin):
        """Build dict of manager titles (key) and manager urls (value) for main_form and navigation"""
        alllist = {}
        tmp_list = self.getAllManagers(type_only=False, objects=True)

        def check_manager(mgr):
            if not mgr:
                return False
            if ZC.ZM_PM in mgr.getClassType():
                return False
            return mgr.getClassName() not in [ZM_PNM, ZM_IM] or admin

        if tmp_list:
            for mgr in tmp_list:
                if check_manager(mgr):
                    title = mgr.getTitle()
                    if len(title) > 8 and title[-8:] == " Manager":
                        title = title[:-8]
                    alllist[title] = str(mgr.absolute_url())

        # we still have to find all hierarchy-down managers...
        if zopratype:
            tmp_list2 = self.getAllManagersHierarchyDown(zopratype=zopratype)
            if tmp_list2:
                for mgr in tmp_list2:
                    # make sure we didnt already find that one
                    if check_manager(mgr) and mgr not in tmp_list:
                        title = mgr.getTitle()
                        if len(title) > 8 and title[-8:] == " Manager":
                            title = title[:-8]
                        alllist[title] = str(mgr.absolute_url())

        return alllist

    #
    # other Database functions, forwarded to the connector
    #

    def checkType(
        self, value, column_type, operator=False, label=None, do_replace=True
    ):
        """forwards checkType to connector"""
        return self.connector.checkType(value, column_type, operator, label, do_replace)

    def executeDBQuery(self, query_text):
        # Executes a database query.
        result = None
        try:
            result = self.connector.query(query_text)
        except Exception:
            import sys

            raise ValueError(
                "SQLError: %s|<br>\n%s|<br>\n%s"
                % (query_text, sys.exc_info()[0], sys.exc_info()[1])
            )
        return result

    def getRowCount(self, name, wherestring=""):
        """get the row count (forward to connector)"""
        return self.connector.getRowCount(name, wherestring)

    def getLastId(self, idfield, name, wherestr=""):
        """get the highest autoid number (forward to connector)"""
        return self.connector.getLastId(idfield, name, wherestr)

    #
    # add log capability to sql-part functions
    #
    def simpleUpdate(
        self, name, origcols_dict, entry_dict, autoid, tabid=None, old_entry=None
    ):
        # prepare update and write log
        # edit tracking
        # set changedate
        entry_dict[ZC.TCN_EDATE] = strftime("%d.%m.%Y")

        # set editor
        m_contact = self.getHierarchyUpManager(ZM_CM)
        if m_contact:

            # process all fields in descr_dict
            entry_dict[ZC.TCN_EDITOR] = m_contact.getCurrentUserId()

        done = self.connector.simpleUpd(name, origcols_dict, entry_dict, autoid)
        if done:
            logstr = "update entry %s in %s" % (autoid, name)
            self.writeLog(logstr, tabid, autoid, old_entry, entry_dict)
        return done

    def simpleValidate(self, cols_dict, entry_dict):
        # validate via connector
        return self.connector.simpleVal(cols_dict, entry_dict)

    def simpleDelete(self, name, autoid, tabid=None, entry=None):
        """ Deletes an entry in the database. """
        # prepare delete and write log
        done = self.connector.simpleDel(name, autoid)
        if done:
            logstr = "Deleted entry %s from %s" % (autoid, name)
            self.writeLog(logstr, tabid, autoid, entry)
        return done

    def simpleInsertInto(self, name, origcols_dict, entry_dict, log=True, tabid=None):
        # prepare insert and write log
        # edit tracking
        m_contact = self.getHierarchyUpManager(ZM_CM)
        if m_contact:
            uid = m_contact.getCurrentUserId()
            # creator field
            if entry_dict.get(ZC.TCN_CREATOR) is None:
                entry_dict[ZC.TCN_CREATOR] = uid
            if entry_dict.get(ZC.TCN_OWNER) is None:
                entry_dict[ZC.TCN_OWNER] = uid
        # creation date field
        if not entry_dict.get(ZC.TCN_DATE):
            entry_dict[ZC.TCN_DATE] = strftime("%d.%m.%Y")

        lastid = self.connector.simpleIns(name, origcols_dict, entry_dict)

        # write log
        if log:
            logstr = "add entry %s to %s" % (lastid, name)
            self.writeLog(logstr, tabid, lastid)
        return lastid

    def simpleSelectFrom(self, name, col_list, origcols_dict, where_dict):
        # simple select is done in the connector, no preparation necessary
        # no logging for selects
        return self.connector.simpleSel(name, col_list, origcols_dict, where_dict)

    def writeLog(self, action, tabid=None, entryid=None, backup=None, newentry=None):

        # create diff entrys
        diff_before = {}
        diff_after = {}

        if backup and newentry:
            no_diff_check = [
                "autoid",
                "owner",
                "entrydate",
                "editor",
                "changedate",
                "creator",
                "permission",
            ]
            false_values = ["None", None, "", 0]

            for key in newentry:
                if (
                    key not in no_diff_check
                    and key in backup
                    and backup[key] != newentry[key]
                    and unicode(backup[key]) != newentry[key]
                    and (
                        backup[key] not in false_values
                        or newentry[key] not in false_values
                    )
                ):
                    # ignore different line endings
                    if isinstance(backup[key], basestring) and isinstance(
                        newentry[key], basestring
                    ):
                        # convert str objects to unicode objects if needed
                        if isinstance(backup[key], str):
                            backup_value = unicode(backup[key], "utf8")
                        else:
                            backup_value = backup[key]
                        if isinstance(newentry[key], str):
                            newentry_value = unicode(newentry[key], "utf8")
                        else:
                            newentry_value = newentry[key]

                        backup[key] = "\r\n".join(backup_value.splitlines())
                        newentry[key] = "\r\n".join(newentry_value.splitlines())
                        if backup_value == newentry_value:
                            continue

                    diff_before[key] = (
                        isinstance(backup[key], basestring)
                        and backup[key].splitlines()
                        or [unicode(backup[key])]
                    )
                    diff_after[key] = (
                        isinstance(newentry[key], basestring)
                        and newentry[key].splitlines()
                        or [unicode(newentry[key])]
                    )

        # Writes a string in the log table.
        ddict = {TCN_ACTION: action, TCN_TABLE: tabid, TCN_ENTRYID: entryid}

        ddict["username"] = str(getSecurityManager().getUser())
        ddict["entrydiff_before"] = pickle.dumps(diff_before).replace("\\", "\\\\")
        ddict["entrydiff_after"] = pickle.dumps(diff_after).replace("\\", "\\\\")
        ddict["change_datetime"] = (
            datetime.utcnow().isoformat().split(".")[0].replace("T", " ")
        )
        # ddict[TCN_BACKUP] = str(backup)
        ddict["username"] = unicode(getSecurityManager().getUser())
        ddict["entrydiff_before"] = unicode(
            pickle.dumps(diff_before).replace("\\", "\\\\"), "iso-8859-15"
        )
        ddict["entrydiff_after"] = unicode(
            pickle.dumps(diff_after).replace("\\", "\\\\"), "iso-8859-15"
        )
        ddict["change_datetime"] = unicode(
            datetime.utcnow().isoformat().split(".")[0].replace("T", " ")
        )

        self.simpleInsertInto(
            self.id + TN_LOG, self._manager_table_dict[TN_LOG], ddict, False
        )

    def getEntryLogBlock(self, tabid, entryid):
        if not tabid or not entryid:
            return ""
        result = []
        entries = self.tableHandler[TN_LOG].getEntries(
            [tabid, entryid], [TCN_TABLE, TCN_ENTRYID]
        )
        for entry in entries:
            result.append(entry[TCN_ACTION])
        return "\n".join(result)

    def getEntryLogDiff(self, id):
        tobj = self.tableHandler["log"]
        logentry = tobj.getEntry(id)
        if not logentry.get("entrydiff_before") or not logentry.get("entrydiff_after"):
            return ""
        entrydiff_before = (
            isinstance(logentry["entrydiff_before"], unicode)
            and logentry["entrydiff_before"].encode("iso-8859-15")
            or logentry["entrydiff_before"]
        )
        entrydiff_after = (
            isinstance(logentry["entrydiff_after"], unicode)
            and logentry["entrydiff_after"].encode("iso-8859-15")
            or logentry["entrydiff_after"]
        )
        before = pickle.loads(entrydiff_before)
        after = pickle.loads(entrydiff_after)
        result = ""
        d = HtmlDiff()
        for key in before:
            # convert unicode objects, becuase HtmlDiff class can't handle unicode objects
            for dictionary in [before, after]:
                if isinstance(dictionary[key], unicode):
                    dictionary[key] = dictionary[key].encode("utf8", "replace")
                elif isinstance(dictionary[key], list):
                    for i in range(len(dictionary[key])):
                        if isinstance(dictionary[key][i], unicode):
                            dictionary[key][i] = dictionary[key][i].encode(
                                "utf8", "replace"
                            )
            result += "<h2>" + key + "</h2>"
            # generate diff in html format
            diff = d.make_file(
                isinstance(before[key], list) and before[key] or str(before[key]),
                isinstance(after[key], list) and after[key] or str(after[key]),
                "vorher",
                "nachher",
            )
            linelist = diff.splitlines()
            # delete html header
            del linelist[0:23]
            # delete legend (footer) from html file
            numlines = len(linelist)
            del linelist[numlines - 18 : numlines]
            # build line-wrap
            linelist = [
                x.replace("&nbsp;", " ").replace('<td nowrap="nowrap">', "<td>")
                for x in linelist
            ]
            # delete colgroups
            del linelist[2:4]
            result += "\n".join(linelist)
        return result

    def getKeysFromPickledDict(self, sdict):
        """need as parameter dictonary, that are serialised with pickle"""
        if isinstance(sdict, unicode):
            sdict = sdict.encode("utf8", "replace")
        return ", ".join(pickle.loads(sdict).keys())

    #
    # the config params section
    # (used for defining manager-class or -id specific config params
    # that are to be stored even after manager-reinstall)
    #

    def addConfigParam(self, indict):
        # Adds a line of configuration parameters
        #          to the configtable.
        test1 = indict.get("mgrtype")
        test2 = indict.get("mgrid")
        if test1 and test2:
            if self.getManager(test1).getId() != test2:
                raise ValueError(
                    "Managertype and Id do not match, please select "
                    + "only one of both or matching values."
                )
        indict["notes"] = None
        indict["parent"] = None
        self.tableHandler["config"].addEntry(indict, ["config_str", "value", "key1"])

    def getConfigParams(
        self, autoid=None, config_str=None, key=None, mgrtype=None, mgrid=None
    ):
        # Searches the configuration parameter 'name' optionally
        #          filtered, returns a dict{autoid->(valuetuple)}.

        constraints = {}
        if autoid:
            constraints["autoid"] = autoid
        if config_str:
            constraints["config_str"] = config_str
        if key:
            constraints["key1"] = key
        if mgrtype:
            constraints["mgrtype"] = mgrtype
        if mgrid:
            constraints["mgrid"] = mgrid

        table = self.tableHandler["config"]
        entry_list = table.getEntryList(constraints=constraints, order="config_str")
        if entry_list:
            return entry_list
        else:
            return []

    def editConfigParam(self, edit_dict):
        # Changes the Value of one entry row.
        table = self.tableHandler["config"]
        return table.updateEntry(
            edit_dict, edit_dict.get("autoid"), required=["config_str", "value"]
        )

    def delConfigParam(self, autoid):
        # Deletes one entry row.
        return self.tableHandler["config"].deleteEntry(autoid)

    security.declareProtected(managePermission, "viewForm")

    def viewForm(self, REQUEST=None):
        """Returns the html source for the view form in the managing
        section.
        """
        tab = hgTable()
        row = 0
        col = 0

        # own information
        tab[row, col] = dlgLabel("Id")
        tab[row, col + 1] = self.id

        if self.title:
            row += 1
            tab[row, col] = dlgLabel("Title")
            tab[row, col + 1] = self.title

        row += 2
        tab[row, col] = "<h3>Manager Information</h3>"
        tab.setCellSpanning(row, col, colspan=3)

        row += 1
        tab[row, col] = "<h4>Manager Id</h4>"
        tab[row, col + 1] = "<h4>Manager Title</h4>"
        tab[row, col + 2] = "<h4>Manager Tables</h4>"
        tab[row, col + 3] = "<h4>Manager Lookup Lists</h4>"
        tab[row, col + 4] = "<h4>Manager Lists References</h4>"
        tab[row, col + 5] = "<h4>Manager Multi Lists</h4>"

        row += 2
        maxoffset = 1

        # manager information
        for manager in self.getChildren():
            row += maxoffset
            maxoffset = 0
            tab[row, col] = dlgLabel(manager.id)
            tab[row, col + 1] = manager.title

            # table information
            offset = 0
            for table in manager.tableHandler.keys():
                tab[row + offset, col + 2] = table
                offset += 1

            if offset > maxoffset:
                maxoffset = offset

            # lookup lists
            offset = 0
            for _list in manager.listHandler.keys():
                tab[row + offset, col + 3] = _list
                offset += 1

            if offset > maxoffset:
                maxoffset = offset

            # list references
            # multi lists
            offset = 0
            for (table, column) in manager.listHandler.references():
                tab[row + offset, col + 4] = str(table) + "->" + column
                if manager.listHandler.getList(table, column).listtype != "singlelist":
                    tab[row + offset, col + 5] = "X"

                offset += 1

            if offset > maxoffset:
                maxoffset = offset

        dlg = getStdDialog(self.title)
        dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
        dlg.setFooter("<dtml-var manage_page_footer>")
        dlg.add(tab)
        return HTML(dlg.getHtml())(self, REQUEST)

    security.declareProtected(managePermission, "updateForm")

    def updateForm(self, REQUEST=None):
        """Returns the html source for the view form."""
        perm = self.getGUIPermission()
        if perm.hasRole(perm.SC_ADMIN):
            dlg = getStdDialog("Update Version", "%s/updateForm" % self.absolute_url())
            dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
            dlg.setFooter("<dtml-var manage_page_footer>")

            dlg.add(hgLabel("<br/>"))

            # update handling
            if REQUEST is not None:
                if REQUEST.form.get("update"):
                    report = self.updateVersion(REQUEST.form.get("mgrid"))

                    dlg.add(hgLabel("<b>Update Report</b>"))
                    dlg.add(hgLabel("<br/>"))
                    dlg.add(str(report))
                    dlg.add(hgLabel("<br/>"))
                    dlg.add(hgLabel("<br/>"))

            version = self.zopra_version
            newver = Manager.zopra_version

            update = False
            if newver > version:
                update = True

            # the product itself
            tab = hgTable()

            tab[0, 0] = hgLabel("<b>Current Product Version:<b>")
            tab[0, 1] = hgLabel(str(version))
            tab[1, 0] = hgLabel("<b>Installed Version:<b>")
            tab[1, 1] = hgLabel(str(newver))

            dlg.add(tab)

            dlg.add(hgLabel("<br/>"))
            dlg.add(hgLabel("<br/>"))
            dlg.add(hgLabel("<b>Registered Manager:</b>"))
            dlg.add(hgLabel("<br/>"))

            # the products children
            tab = hgTable()
            r = 0

            for child in self.getChildren():
                if child == self:
                    continue

                ident = child.getId()
                ident += " (" + child.getTitle() + ") "
                cb = hgCheckBox("", child.getId(), name="mgrid")
                if child.zopra_version < newver:
                    info = "Update %s -> %s" % (child.zopra_version, newver)
                    update = True
                    cb.setChecked(True)
                else:
                    cb.setDisabled()
                    info = "Version %s" % child.zopra_version
                tab[r, 0] = cb
                tab[r, 1] = hgLabel(ident)
                tab[r, 2] = hgLabel(info)
                r += 1

            dlg.add(tab)

            if update:
                dlg.add(hgPushButton("Update", name="update"))
            else:
                dlg.add(hgLabel("No update required"))

            return HTML(dlg.getHtml())(self, REQUEST)
        else:
            raise ValueError(
                "Access Denied: Insufficient privileges to access this function"
            )

    security.declareProtected(managePermission, "updateVersion")

    def updateVersion(self, updateChildren=None):
        """update product and all registered managers"""

        if not updateChildren:
            updateChildren = []

        # update product
        report = Manager.updateVersion(self)

        # update children
        for child in self.getChildren():
            if child == self:
                continue

            if not child.getId() in updateChildren:
                continue

            rep = child.updateVersion()

            report += "<br>" + rep

        return report

    security.declareProtected(managePermission, "setDebugOutput")

    def setDebugOutput(self):
        """Overwritten dummy function for manager specific debug output.
        This function is called by the management view-tab to
        display further debug output. Here, the links to updateAllDialogs
        and updateTree are added for the ZopRAProduct ViewTab."""
        # return a vbox with two links
        widget = hgTable()

        url = "%s/updateTree" % self.absolute_url()
        link = hgLabel("> update Version systemwide", url, parent=widget)
        widget[0, 0] = link
        url = "%s/updateAllDialogs" % self.absolute_url()
        link = hgLabel("> update Dialogs systemwide", url, parent=widget)
        widget[1, 0] = link

        return widget.getHtml()

    #
    # two url-callable functions for update
    #

    security.declareProtected(managePermission, "updateAllDialogs")

    def updateAllDialogs(self):
        """reload all dialogs of folder hierarchy and reset sessions"""
        dlg = getStdDialog("Loaded the following dialogs")
        box = hgVBox(parent=dlg)
        dlg.add(box)
        mgrs = self.getAllManagersHierarchyDown()
        for entry in mgrs:
            if hasattr(entry, "dlgHandler"):
                if entry.dlgHandler:
                    dlgh = entry.dlgHandler
                    for dlgCon in dlgh.objectValues():
                        dlgCon.loadDefaultClass()
                        dlgCon.removeDialogExtensionFromModule()
                        dlgCon.removeFromSessions()
                        lab = "%s: %s" % (entry.getClassName(), dlgCon.id)
                        label = hgLabel(lab, parent=box)
                        box.add(label)
                else:
                    lab = "%s has no dlgHandler" % entry.id
                    label = hgLabel(lab, parent=box)
                    box.add(label)
        return HTML(dlg.getHtml())(self, None)

    security.declareProtected(managePermission, "updateTree")

    def updateTree(self):
        """update complete Folder hierarchy to new version."""
        dlg = getStdDialog("Update")
        box = hgVBox(parent=dlg)
        dlg.add(box)
        mgrs = self.getAllManagersHierarchyDown()
        for entry in mgrs:
            did = entry.updateVersion()
            box.add(hgLabel(did, parent=box))
        return HTML(dlg.getHtml())(self, None)

    security.declareProtected(modifyPermission, "showEditFormConfig")

    def showEditFormConfig(self, REQUEST=None):
        """Return the html source for configuration tasks."""
        return "Legacy: Not implemented."

    #
    # public managing
    #
    security.declareProtected(modifyPermission, "_index_html")

    def _index_html(self, REQUEST, parent):
        """Returns the html source for the manager specific part of
        the index_html.
        """
        return "Legacy: Not implemented."
