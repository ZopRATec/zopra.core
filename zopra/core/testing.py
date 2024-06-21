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
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.testing.zope import WSGI_SERVER_FIXTURE
from plone.testing.zope import installProduct
from zopra.core import DBDA_ID
from zopra.core import HAVE_WEBCMS
from zopra.core.setuphandlers import ZopRATestEnvironmentMaker
from ZServer.Testing.utils import setupCoreSessions


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

    zoprapath = "zopra/test/app"

    def setUpZopRA(self, app):
        """Install all packages needed for basic WebCMS functionality
        without tud.profiles.webcms dependencies to all ZopRA packages."""
        if HAVE_WEBCMS:
            setupCoreSessions(app)

            # Load ZCML
            import tud.profiles.webcms
            import tud.addons.webcms
            import tud.addons.deepl
            import collective.js.jqueryui
            import tud.theme.webcms2
            import tud.content.webcms
            import tud.boxes.base
            import tud.boxes.webcms
            import tud.addons.ckeditorplugins
            import tud.addons.datagridfield
            import tud.migration.plone52

            # Ensure that all dependencies of tud.profiles.webcms are going to be loaded
            self.loadZCML(name="testing.zcml", package=tud.addons.webcms)
            self.loadZCML(name="testing.zcml", package=tud.addons.deepl)
            self.loadZCML(name="testing.zcml", package=tud.content.webcms)
            self.loadZCML(name="testing.zcml", package=tud.boxes.base)
            self.loadZCML(name="testing.zcml", package=tud.boxes.webcms)
            self.loadZCML(name="testing.zcml", package=tud.addons.ckeditorplugins)
            self.loadZCML(package=collective.js.jqueryui)
            self.loadZCML(name="testing.zcml", package=tud.theme.webcms2)
            self.loadZCML(package=tud.migration.plone52)
            self.loadZCML(package=tud.addons.datagridfield)

            installProduct(app, "Products.ATContentTypes")
            installProduct(app, "tud.migration.plone52")
            installProduct(app, "raptus.multilanguagefields")
            installProduct(app, "collective.workspace")
            installProduct(app, "tud.addons.webcms")
            installProduct(app, "tud.addons.deepl")
            installProduct(app, "tud.content.webcms")
            installProduct(app, "tud.boxes.base")
            installProduct(app, "tud.boxes.webcms")
            installProduct(app, "tud.addons.ckeditorplugins")
            installProduct(app, "Products.DateRecurringIndex")
            installProduct(app, "tud.addons.redirect")
            installProduct(app, "collective.js.jqueryui")
            installProduct(app, "tud.theme.webcms2")
            # do not install profiles to avoid the dependencies on zopra app packages
            # installProduct(app, "tud.profiles.webcms")

        # install zopra package and database adapter
        import zopra.core

        self.loadZCML(name="testing.zcml", package=zopra.core)

        installProduct(app, "zopra.core")
        installProduct(app, "Products.ZMySQLDA")

    def setUpZopRAProfiles(self, portal):
        """Install tud.theme.webcms2:test if available. Then install the zopra.core:default profile.

        :param portal: the portal
        :type portal: Products.CMFPlone.Portal.PloneSite
        """
        # extra WEBCMS setUp (Theme with content and addons)
        if HAVE_WEBCMS:
            applyProfile(portal, "tud.theme.webcms2:test")
        applyProfile(portal, "zopra.core:default")

    def setUpZope(self, app, configurationContext):
        """Method to set up a Zope instance (importing, product installation and loading zcml)

        :param app: Zope application root
        :param configurationContext: ZCML configuration context
        :return:
        """
        # extra WEBCMS setUp (including content, addons and theme) for our zopra packages to use
        self.setUpZopRA(app)

    def setUpPloneSite(self, portal):
        """Method to set up the Plone Site (installing products and applying Profiles)

        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """
        self.setUpZopRAProfiles(portal)
        # installs a test environment and database connectivity
        # (which we do not need in this form for the other apps)
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
        zoprafolder = portal.unrestrictedTraverse(self.zoprapath)
        zmysql = getattr(zoprafolder, DBDA_ID, None)
        if zmysql is None:
            raise Exception("Z MySQL object not found!")
        ZopRATestEnvironmentMaker.clearDatabase(zmysql)


FIXTURE = ZopraCoreLayer()

INTEGRATION_TESTING = IntegrationTesting(bases=(FIXTURE,), name="zopra.core:Integration")

ROBOT_TESTING = FunctionalTesting(
    bases=(REMOTE_LIBRARY_BUNDLE_FIXTURE, WSGI_SERVER_FIXTURE, FIXTURE),
    name="zopra.core:Robot",
)
