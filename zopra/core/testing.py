from plone.app.robotframework.autologin import AutoLogin
from plone.app.robotframework.content import Content
from plone.app.robotframework.genericsetup import GenericSetup
from plone.app.robotframework.i18n import I18N
from plone.app.robotframework.mailhost import MockMailHost
from plone.app.robotframework.quickinstaller import QuickInstaller
from plone.app.robotframework.remote import RemoteLibrary
from plone.app.robotframework.remote import RemoteLibraryLayer
from plone.app.robotframework.server import Zope2ServerRemote
from plone.app.robotframework.users import Users
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.testing.zope import WSGI_SERVER_FIXTURE
from plone.testing.zope import installProduct
from ZServer.Testing.utils import setupCoreSessions

from zopra.core import DBDA_ID
from zopra.core import HAVE_WEBCMS


# preparation for keywords implemented in python
class Keywords(RemoteLibrary):
    pass


REMOTE_LIBRARY_BUNDLE_FIXTURE = RemoteLibraryLayer(
    bases=(PLONE_FIXTURE,),
    libraries=(
        AutoLogin,
        QuickInstaller,
        GenericSetup,
        Content,
        Users,
        I18N,
        MockMailHost,
        Zope2ServerRemote,
        Keywords,
    ),
    name="RemoteLibraryBundle:RobotRemote",
)


class ZopraCoreLayer(PloneSandboxLayer):
    """Testing Layer for this add-on."""

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Method to set up a Zope instance (importing, product installation and loading zcml)

        :param app: Zope application root
        :param configurationContext: ZCML configuration context
        :return:
        """
        # extra WEBCMS setUp (including content, addons and theme) for our zopra packages to use
        # TODO: move to zopra.ploned when that is ready
        if HAVE_WEBCMS:
            setupCoreSessions(app)
            # Load ZCML
            import tud.profiles.webcms
            import tud.addons.webcms
            import tud.theme.webcms2
            import tud.content.webcms
            import tud.boxes.base
            import tud.boxes.webcms
            # import tud.addons.ckeditorplugins
            import tud.addons.datagridfield
            import tud.migration.plone52

            # Ensure that all dependencies of tud.profiles.webcms are going to be loaded
            self.loadZCML(name="testing.zcml", package=tud.addons.webcms)
            self.loadZCML(name="testing.zcml", package=tud.content.webcms)
            self.loadZCML(name="testing.zcml", package=tud.boxes.base)
            self.loadZCML(name="testing.zcml", package=tud.boxes.webcms)
            # self.loadZCML(name="testing.zcml", package=tud.addons.ckeditorplugins)
            self.loadZCML(name="testing.zcml", package=tud.theme.webcms2)
            self.loadZCML(package=tud.migration.plone52)
            self.loadZCML(package=tud.addons.datagridfield)

            installProduct(app, 'Products.ATContentTypes')
            installProduct(app, 'tud.migration.plone52')
            installProduct(app, "raptus.multilanguagefields")
            installProduct(app, "collective.workspace")
            installProduct(app, "tud.addons.webcms")
            installProduct(app, "tud.content.webcms")
            installProduct(app, "tud.boxes.base")
            installProduct(app, "tud.boxes.webcms")
            # installProduct(app, "tud.addons.ckeditorplugins")
            installProduct(app, "Products.DateRecurringIndex")
            installProduct(app, "tud.addons.redirect")
            installProduct(app, "tud.theme.webcms2")
            # do not install profiles to avoid the dependencies on zopra app packages
            # installProduct(app, "tud.profiles.webcms")

        import zopra.core

        self.loadZCML(name="testing.zcml", package=zopra.core)

        installProduct(app, "zopra.core")
        installProduct(app, "Products.ZMySQLDA")

    def setUpPloneSite(self, portal):
        """Method to set up the Plone Site (installing products and applying Profiles)

        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """
        # extra WEBCMS setUp (Content + Theme)
        if HAVE_WEBCMS:
            applyProfile(portal, "tud.theme.webcms2:test")
        applyProfile(portal, "zopra.core:test")

        # commit the changes to counteract PloneSandBoxLayer not persisting our changes anymore
        import transaction
        transaction.commit()

    def tearDownPloneSite(self, portal):
        """Tear down the Plone site.

        Implementing this is optional. If the changes made during the
        ``setUpPloneSite()`` method were confined to the ZODB and the global
        component regsitry, those changes will be torn down automatically.
        """
        zoprafolder = "base/zopra/app"
        zfobj = portal.unrestrictedTraverse(zoprafolder)
        self.clearDatabase(zfobj)

    def clearDatabase(self, zoprafolder):
        """
        Removes all tables in database of zmysql object, which is determined from given zmysql id.

        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        """
        zmysql = getattr(zoprafolder, DBDA_ID, None)
        if zmysql is None:
            raise Exception("Z MySQL object not found!")

        dbc = zmysql()

        tables = [
            table["table_name"]
            for table in dbc.tables()
            if table["table_type"] == "table"
        ]

        for table in tables:
            dbc.query("DROP TABLE {}".format(table.encode("utf-8")))


FIXTURE = ZopraCoreLayer()

ROBOT_TESTING = FunctionalTesting(
    bases=(REMOTE_LIBRARY_BUNDLE_FIXTURE, WSGI_SERVER_FIXTURE, FIXTURE),
    name="zopra.core:Robot",
)
