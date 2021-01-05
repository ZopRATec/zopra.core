from builtins import object

from PyHtmlGUI.kernel.hgTable import hgTable
from PyHtmlGUI.widgets.hgLabel import hgLabel
from PyHtmlGUI.widgets.hgLabel import hgNEWLINE
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from zopra.core import HTML
from zopra.core import ZC
from zopra.core import ClassSecurityInfo
from zopra.core import managePermission
from zopra.core.dialogs import dlgLabel
from zopra.core.dialogs import getStdDialog


#
# ZopRA imports
#


class ManagerManageTabsMixin(object):
    """The ManagerManageTabsMixin class provides display and helper methods
    for the management tabs of ZopRA managers."""

    #
    # Security
    #
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    security.declareProtected(managePermission, "setDebugOutput")

    def setDebugOutput(self):
        """Hook method for manager specific debug output.

        This function is called by the management view-tab to display further
        debug output."""
        return ""

    ###########################################################################
    #                                                                         #
    # Management Tab Views                                                    #
    #                                                                         #
    ###########################################################################

    security.declareProtected(managePermission, "viewTab")

    def viewTab(self, REQUEST=None):
        """Returns the HTML source for the view form."""
        dlg = getStdDialog("Debug Output", "%s/viewTab" % self.absolute_url())
        dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
        dlg.setFooter("<dtml-var manage_page_footer>")

        dlg.add(self.getDebugOutput(REQUEST))
        return HTML(dlg.getHtml())(self, REQUEST)

    security.declareProtected(managePermission, "updateTab")

    def updateTab(self, REQUEST=None):
        """Returns the html source for the view form."""
        dlg = getStdDialog("Update Version", "%s/updateTab" % self.absolute_url())
        dlg.setHeader("<dtml-var manage_page_header><dtml-var manage_tabs>")
        dlg.setFooter("<dtml-var manage_page_footer>")

        dlg.add(hgLabel("<br/>"))

        # update handling
        if REQUEST is not None:
            if REQUEST.form.get("update"):
                report = self.updateVersion()

                dlg.add(hgLabel("<b>Update Report</b>"))
                dlg.add(hgLabel("<br/>"))
                dlg.add(str(report))
                dlg.add(hgLabel("<br/>"))
                dlg.add(hgLabel("<br/>"))

        version = self.zopra_version
        from zopra.core.Manager import Manager

        newver = Manager.zopra_version

        tab = hgTable()

        tab[0, 0] = hgLabel("<b>Current Manager Version:<b>")
        tab[0, 1] = hgLabel(str(version))
        tab[1, 0] = hgLabel("<b>Installed Version:<b>")
        tab[1, 1] = hgLabel(str(newver))

        dlg.add(tab)

        if newver > version:
            dlg.add(hgPushButton("Update", name="update"))
        else:
            dlg.add(hgLabel("No update required"))

        return HTML(dlg.getHtml())(self, REQUEST)

    security.declareProtected(managePermission, "getDebugOutput")

    def getDebugOutput(self, REQUEST):
        """Returns the HTML source of the debug output view."""
        html = []

        additional = self.setDebugOutput()
        if additional:
            html.append("<h2>Manager specific Debug Output</h2>" + str(hgNEWLINE))
            html.append(additional)
            html.append(str(hgNEWLINE))

        html.append(str(dlgLabel("<h2> Debug Output </h2>") + hgNEWLINE))

        tab = hgTable()

        # show tables information
        tab[0, 0] = dlgLabel("<h3>Table Overview</h3>")

        tab[1, 0] = dlgLabel("Table Name")
        tab[1, 1] = dlgLabel("Column Name")
        tab[1, 2] = dlgLabel("Column Type")
        tab[1, 3] = dlgLabel("Column Label")

        row = 2
        for table in self.tableHandler.keys():
            tab[row, 0] = dlgLabel("<b>%s</b>" % table)
            offset = 1
            for col in self.tableHandler[table].getMainColumnNames():
                tab[row + offset, 1] = col
                colobj = self.tableHandler[table].getField(col)
                tab[row + offset, 2] = colobj.get(ZC.COL_TYPE)
                tab[row + offset, 3] = colobj.get(ZC.COL_LABEL, col).encode("utf8")
                offset += 1
            row += offset
        row += 1

        # show db list information
        if len(self.listHandler.keys()) > 0:
            # here we only show info about the db lists
            tab[row, 0] = dlgLabel("<h3>List (Basic Lists with dbtable) Overview</h3>")
            row += 1
            tab[row, 0] = dlgLabel("List Name")
            tab[row, 1] = dlgLabel("List Label")
            tab[row, 2] = dlgLabel("Value Count")
            row += 1
            for list_entry in self.listHandler.keys():
                lobj = self.listHandler[list_entry]
                tab[row, 0] = "<b>" + list_entry + "</b>"
                tab[row, 1] = lobj.getLabel().encode("utf8")
                tab[row, 2] = lobj.getValueCount()
                row += 1
            row += 1
        row += 1

        # show access list information
        tab[row, 0] = dlgLabel("<h3>List References Overview</h3>")
        row += 2
        tab[row, 0] = dlgLabel("Table Name")
        tab[row, 1] = dlgLabel("Column Name")
        tab[row, 2] = dlgLabel("Column Label")
        tab[row, 3] = dlgLabel("List Type")
        tab[row, 4] = dlgLabel("Referenced Manager")
        tab[row, 5] = dlgLabel("List Function")
        tab[row, 6] = dlgLabel("Foreign List")
        row += 1

        for table in self.tableHandler.keys():
            tablelists = self.listHandler.getLists(table)

            for lobj in tablelists:
                tab[row, 0] = dlgLabel("<b>%s</b>" % table)
                tab[row, 1] = dlgLabel(lobj.listname)
                tab[row, 2] = dlgLabel(lobj.getLabel().encode("utf8"))
                tab[row, 3] = dlgLabel(lobj.listtype)
                try:
                    tab[row, 4] = dlgLabel(lobj.getResponsibleManagerId())
                except Exception:
                    tab[row, 4] = dlgLabel('<font color="red">not found</font>')
                tab[row, 5] = dlgLabel(lobj.function)
                tab[row, 6] = dlgLabel(lobj.foreign)
                row += 1

        html.append(str(tab))

        return "\n".join(html)
