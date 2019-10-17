import os
from MySQLdb import OperationalError
from transaction import commit

from plone.testing import z2
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import ploneSite
from plone.app.testing import quickInstallProduct
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.robotframework.remote import RemoteLibraryLayer, RemoteLibrary
from plone.app.robotframework.autologin import AutoLogin
from plone.app.robotframework.content import Content
from plone.app.robotframework.genericsetup import GenericSetup
from plone.app.robotframework.i18n import I18N
from plone.app.robotframework.mailhost import MockMailHost
from plone.app.robotframework.quickinstaller import QuickInstaller
from plone.app.robotframework.server import Zope2ServerRemote
from plone.app.robotframework.users import Users
from Products.CMFCore.utils import getToolByName
from zope.configuration import xmlconfig

from zopra.core import DBDA_ID

class Keywords(RemoteLibrary):
    ZOPRA_BASE = 'http://localhost/'
    
    def get_zopra_base(self):
        return self.ZOPRA_BASE

REMOTE_LIBRARY_BUNDLE_FIXTURE = RemoteLibraryLayer(
    bases=(PLONE_FIXTURE,),
    libraries=(AutoLogin, QuickInstaller, GenericSetup,
               Content, Users, I18N, MockMailHost,
               Zope2ServerRemote, Keywords),
    name="RemoteLibraryBundle:RobotRemote"
)

class PlainZopraCoreLayer(PloneSandboxLayer):
    """Testing Layer for this add-on.
    """

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Method to set up a Zope instance (importing, product installation and loading zcml)

        :param app: Zope application root
        :param configurationContext: ZCML configuration context
        :return:
        """
        import zopra.core

        self.loadZCML(name='testing.zcml', package=zopra.core)

        z2.installProduct(app, 'zopra.core')
        z2.installProduct(app, 'Products.ZMySQLDA')

    def setUpPloneSite(self, portal):
        """Method to set up the Plone Site (installing products and applying Profiles)

        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """
        self.applyProfile(portal, 'zopra.core:default')
        # might not need this
        #wf_tool = getToolByName(portal, 'portal_workflow')
        #wf_tool.updateRoleMappings()
        
        



    def clearDatabase(self, zoprafolder):
        """
        Removes all tables in database of zmysql object, which is determined from given zmysql id.

        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        """
        zmysql = getattr(zoprafolder, DBDA_ID, None)
        if zmysql is None:
            raise Exception('Z MySQL object not found!')

        dbc = zmysql()

        tables = [table['table_name'] for table in dbc.tables() if table['table_type'] == 'table']

        for table in tables:
            dbc.query('DROP TABLE {}'.format(table.encode('utf-8')))

FIXTURE = PlainZopraCoreLayer()

ROBOT_TESTING = FunctionalTesting(
    bases=(REMOTE_LIBRARY_BUNDLE_FIXTURE,
           z2.ZSERVER_FIXTURE,
           FIXTURE),
    name="zopra.core:Robot")
