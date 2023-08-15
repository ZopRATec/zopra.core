# -*- coding: utf-8 -*-
import logging
import os
from MySQLdb import OperationalError

from plone import api
from builtins import object

from zopra.core import DBDA_ID
from zopra.core import HAVE_WEBCMS
from OFS.Folder import manage_addFolder
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "zopra.core:uninstall",
        ]


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def setupTestScenario(context):
    """test setup post handler
    """
    logger = logging.getLogger("zopra.core")
    portal = api.portal.get()

    tenv = ZopRATestEnvironmentMaker(logger, portal)
    logger.info("Setting up ZopRA Test Environment")
    tenv.setup()


class ZopRATestEnvironmentMaker(object):
    """Test Environment Setup via methods in a class so parts of it can be overwritten for the subpackages"""

    def __init__(self, logger, portal):
        self.logger = logger
        self.portal = portal
        self.is_test_mode = False

    def activateTestDatabaseUsage(self):
        """Use this method to activate Test mode for the database connector. The env params used for
        database connectivity will then always use the prefix "ZOPRA_" (instead of individual prefixes for different
        zopra packages)
        """
        self.is_test_mode = True

    def setup(self):
        """Main method calling all other methods."""
        self.createInitialUsers()
        # build zopra environment down to the app folder
        if HAVE_WEBCMS:
            zoprafolder = self.buildWebCMSEnvironment("test")
        else:
            zoprafolder = self.buildEnvironment("test")
        # add database Adapter
        self.addDatabaseAdapter(zoprafolder, "_ZOPRA")
        # add the zopra Product
        self.addProductManager(zoprafolder, DBDA_ID, "pm", "ZopRA Product Manager")
        # set zopra_path in upper structure
        zoprafolder.getParentNode().manage_addProperty("zopra_path", "app/pm", "string")

        # add the test manager
        self.addManager(
            zoprafolder,
            "zopra.core.tools.mgrTest",
            "mgrTest",
            "testapp",
            "Test Manager",
        )

    def buildEnvironment(self, name):
        """Create container structure down to the ZopRA container and the app folder inside.
        Overwrite for special handling (applying interfaces or using special containers).
        Resulting structure is /zopra/<name>/app.

        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """

        # add plone folder ZopRATest
        self.portal.invokeFactory("Folder", "zopra")
        base = self.portal["base"]

        # add plone folder ZopRATest
        base.invokeFactory("Folder", name)
        folder = base["zopra"]

        # add zope folder app via import and manage_addFolder direct call
        manage_addFolder(folder, "app")

        # return the created folder
        return folder["app"]

    def buildWebCMSEnvironment(self, name):
        """Create container structure down to the ZopRA container and the app folder inside.
        Overwrite for special handling (applying interfaces or using special containers).
        Resulting structure is /zopra/<name>/app.

        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """
        # add MainTopicSubsection
        if "zopra" in self.portal:
            base = self.portal["zopra"]
        else:
            base = api.content.create(type="MainTopicSubsection", title="ZopRA", container=self.portal)
            api.content.transition(obj=base, transition="publish")
        # add Subsection
        if name.islower():
            title = name.capitalize()
        else:
            title = name
        subsection = api.content.create(type="Subsection", title=title, container=base)
        api.content.transition(obj=subsection, transition="publish")

        # add zope folder
        manage_addFolder(subsection, "app")

        # return the created folder
        return subsection["app"]

    def cleanupSubstructure(self, name):
        """Remove existing ZopRA project installation of given name, if it exists.

            This will not do any removal from the database.

        :param name: name for the main folder
        :type name: str
        """
        if "zopra" in self.portal:
            base = self.portal["zopra"]
            name = name.lower().replace(' ', '-')
            if name in base:
                # no need to suppress events anymore when deleting ZopRA installations
                base._delObject(name)
                self.logger.info('Deleted {} substructure.'.format(name))

    def readEnvParam(self, name, suffix, default):
        """Try to read an environment parameter with the given name plus suffix.

            If no suffix was given or no environment parameter was found, try to read
            the original name from the environment. If this fails, return the given default.

        :param name: environment parameter name
        :type name: str
        :param suffix: a suffix that will be added to the name directly
        :type suffix: str
        :param default: the default for when everything else fails
        :type default: str
        :return: the looked up value
        :rtype: str
        """
        # first read the param with given suffix
        if suffix:
            res = os.environ.get(name + suffix, None)
            if res:
                return res
        return os.environ.get(name, default)

    def addDatabaseAdapter(self, zoprafolder, suffix=''):
        """Add zmysql object inside the zopra context to provide database access.

        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        :param suffix: env lookup for all database params is first done with suffix, then without
        :type suffix: str
        """
        title = "Z MySQL Database Connection"
        if self.is_test_mode:
            # override the given suffix, always use _ZOPRA
            suffix = "_ZOPRA"
        db_server = self.readEnvParam("DB_SERVER", suffix, "localhost")
        db_user = self.readEnvParam("DB_USER", suffix, "zopratest")
        db_password = self.readEnvParam("DB_PASSWORD", suffix, "zopratest")
        db_name = self.readEnvParam("DB_NAME", suffix, "zopratest")
        connection_string = "{}@{} {} {}".format(
            db_name, db_server, db_user, db_password
        )
        try:
            return zoprafolder.manage_addProduct["ZMySQLDA"].manage_addZMySQLConnection(
                DBDA_ID,
                title,
                connection_string,
                check=True,
                use_unicode=True,
                auto_create_db=True,
            )
        except OperationalError as e:
            msg = e.args[1] + "\n"
            msg += "Hint: You can define environment variables DB_SERVER, DB_USER, DB_PASSWORD and DB_NAME to configure your database connection."
            raise Exception(msg)

    def addManager(
        self,
        zoprafolder,
        module_name,
        manager_classname,
        manager_id,
        manager_title,
        nocreate=False
    ):
        """Add the ZopRA Manager object to zoprafolder using the manage_addGeneric method from zopra.core.__init__.
        Use module_name and manager_classname to identify your module and class. Reuse for installing all ZopRA Managers.

        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        :param module_name: Module path in dot-notation of the Manager Module (down to the py-file)
        :type module_name: string
        :param manager_classname: Class name of the Manager
        :type manager_classname: string
        :param manager_id: ID of the Manager Object to be installed
        :type manager_id: string
        :param manager_title: Title of the Manager Object to be installed
        :type manager_title: string
        """
        dispatcher = zoprafolder.manage_addProduct["zopra.core"]
        dispatcher.manage_addGeneric(
            manager_id,
            manager_title,
            manager_classname,
            module_name,
            nocreate=nocreate,
            zopratype="",
            REQUEST=None,
        )

    def addProductManager(self, zoprafolder, dbda_id, pm_id, pm_title, nocreate=False):
        """

        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        :param dbda_id: ID of the Database Adapter Object in the ZODB
        :type dbda_id: string
        :param pm_id: ID of the Product Manager Object to be installed
        :type pm_id: string
        :param pm_title: Title of the Product Manager Object to be installed
        :type pm_title: string
        """
        dispatcher = zoprafolder.manage_addProduct["zopra.core"]
        dispatcher.manage_addProductGeneric(
            pm_id,
            pm_title,
            "ZopRAProduct",
            "zopra.core.tools.ZopRAProduct",
            dbda_id,
            nocreate=nocreate,
            zopratype="",
            REQUEST=None,
        )

    def createInitialUsers(self):
        """Creates initial users

        :return:
        """
        user_data = [
            {
                "username": "redakteur",
                "password": "redakteur",
                "email": "redakteur@tu-dresden.de",
                "properties": {"fullname": "Redakteur"},
                "roles": ("Contributor", "Editor"),
            },
            {
                "username": "chefredakteur",
                "password": "chefredakteur",
                "email": "chefredakteur@tu-dresden.de",
                "properties": {"fullname": "Chefredakteur"},
                "roles": ("Contributor", "Editor", "Reviewer"),
            },
            {
                "username": "testadmin",
                "password": "testadmin",
                "email": "testadmin@tu-dresden.de",
                "properties": {"fullname": "Testadmin"},
                "roles": ("Contributor", "Editor", "Reviewer", "Section Administrator"),
            },
        ]
        for datum in user_data:
            user = api.user.get(datum["username"])
            if user is None:
                user = api.user.create(**datum)

    @classmethod
    def clearDatabase(cls, database_adapter):
        """Removes all tables in database of given database_adapter.

        :param database_adapter: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type database_adapter: Products.ZMySQLDA.DA.Connection
        """
        dbc = database_adapter()

        tables = [
            table["table_name"]
            for table in dbc.tables()
            if table["table_type"] == "table"
        ]

        for table in tables:
            dbc.query("DROP TABLE {}".format(table.encode("utf-8")))

