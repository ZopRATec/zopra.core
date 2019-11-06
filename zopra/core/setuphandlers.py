# -*- coding: utf-8 -*-
import os
import plone.api

from zopra.core import HAVE_WEBCMS, DBDA_ID

def setupTestSzenario(context):
    """setups various when installing add-on

    Ordinarily, GenericSetup handlers check for the existence of XML files.
    Here, we are not parsing an XML file, but we use a text file as a
    flag to check that we actually meant for this import step to be run.
    The file is found in profiles/default.
    """

    if context.readDataFile('zopra.core-test.txt') is None:
        return
    logger = context.getLogger('zopra.core')
    portal = context.getSite()

    tenv = ZopRATestEnvironmentMaker(logger, portal)
    logger.info('Setting up ZopRA Test Environment')
    tenv.setup()


class ZopRATestEnvironmentMaker:
    """ Test Environment Setup via methods in a class so parts of it can be overwritten for the subpackages
    
    """

    def __init__(self, logger, portal):
        self.logger = logger
        self.portal = portal


    def setup(self):
        """ Main method calling all other methods.
        
        """
        self.createInitialUsers()
        # build zopra environment down to the app folder
        if HAVE_WEBCMS:
            zoprafolder = self.buildWebCMSEnvironment()
        else:
            zoprafolder = self.buildEnvironment()
        # add database Adapter
        self.addDatabaseAdapter(zoprafolder)
        # add the zopra Product
        self.addProductManager(zoprafolder, DBDA_ID, 'pm', 'ZopRA Product Manager')
        # set zopra_path in upper structure
        zoprafolder.getParentNode().manage_addProperty('zopra_path', 'app/pm', 'string')
    
        # add the test manager
        self.addManager(zoprafolder, DBDA_ID, 'zopra.core.tools.mgrTest', 'mgrTest', 'testapp', 'Test Manager')


    def buildEnvironment(self):
        """Create container structure down to the ZopRA container and the app folder inside. 
        Overwrite for special handling (applying interfaces or using special containers).
        Resulting structure should be /base/zopra/app.
        
        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """
        
        # add plone folder ZopRATest
        self.portal.invokeFactory('Folder', 'base')
        base = self.portal['base']
        
        # add plone folder ZopRATest
        base.invokeFactory('Folder', 'zopra')
        folder = self.portal['zopra']

        # add zope folder app via import and manage_addFolder direct call
        from OFS.Folder import manage_addFolder
        manage_addFolder( folder, 'app' )

        # return the created folder
        return folder['app']


    def buildWebCMSEnvironment(self):
        """Create container structure down to the ZopRA container and the app folder inside. 
        Overwrite for special handling (applying interfaces or using special containers). 
        Resulting structure should be /base/zopra/app.
        
        :param portal: Plone Site
        :type portal: Products.CMFPlone.Portal.PloneSite
        :return:
        """
        # add Section
        self.portal.invokeFactory('MainTopicSubsection', 'base')
        base = self.portal['base']
        base.setTitle({'en': 'Base'})

        # add Subsection
        base.invokeFactory('Subsection', 'zopra')
        subsection = base['zopra']
        subsection.setTitle({'en': 'ZopRA'})
        # add zope folder app via import and manage_addFolder direct call
        from OFS.Folder import manage_addFolder
        manage_addFolder( subsection, 'app' )

        # return the created folder
        return subsection['app']


    def addDatabaseAdapter(self, zoprafolder):
        """Add zmysql object inside the zopra context to provide database access.
    
        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        """
        title = 'Z MySQL Database Connection'
        db_server = os.environ.get('DB_SERVER', 'localhost')
        db_user = os.environ.get('DB_USER', 'zopratest')
        db_password = os.environ.get('DB_PASSWORD', 'zopratest')
        db_name = os.environ.get('DB_NAME', 'zopratest')
        connection_string = "{}@{} {} {}".format(db_name, db_server, db_user, db_password)
        # tests are dependent on MySQLdb
        from MySQLdb import OperationalError
        try:
            return zoprafolder.manage_addProduct['ZMySQLDA'].manage_addZMySQLConnection(DBDA_ID, title, connection_string, check = True, use_unicode = True, auto_create_db = True)
        except OperationalError as e:
            msg = e.args[1] + "\n"
            msg += "Hint: You can define environment variables DB_SERVER, DB_USER, DB_PASSWORD and DB_NAME to configure your database connection."
            raise Exception(msg)


    def addManager(self, zoprafolder, dbda_id, module_name, manager_classname, manager_id, manager_title):
        """Add the ZopRA Manager object to zoprafolder using the manage_addGeneric method from zopra.core.__init__. 
        Use module_name and manager_classname to identify your module and class. Reuse for installing all ZopRA Managers.
        
        :param zoprafolder: the app folder containing the ZopRA Installation, in which the database adapter will be created
        :type zoprafolder: Folder
        :param dbda_id: ID of the Database Adapter Object in the ZODB
        :type dbda_id: string
        :param module_name: Module path in dot-notation of the Manager Module (down to the py-file)
        :type module_name: string
        :param manager_classname: Class name of the Manager
        :type manager_classname: string
        :param manager_id: ID of the Manager Object to be installed
        :type manager_id: string
        :param manager_title: Title of the Manager Object to be installed
        :type manager_title: string
        """
        dispatcher = zoprafolder.manage_addProduct['zopra.core']
        dispatcher.manage_addGeneric( manager_id,
                                      manager_title,
                                      manager_classname,
                                      module_name,
                                      nocreate     = 0,
                                      zopratype    = '',
                                      ebase        = None,
                                      accessgroups = None,
                                      REQUEST      = None )


    def addProductManager(self, zoprafolder, dbda_id, pm_id, pm_title):
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
        dispatcher = zoprafolder.manage_addProduct['zopra.core']
        dispatcher.manage_addProductGeneric( pm_id,
                                             pm_title,
                                             'ZopRAProduct',
                                             'zopra.core.tools.ZopRAProduct',
                                             dbda_id,
                                             nocreate     = 0,
                                             zopratype    = '',
                                             REQUEST      = None )


    def createInitialUsers(self):
        """Creates initial users
    
        :return:
        """
        user_data = [
            {
                'username': 'user',
                'password': 'user',
                'email': 'user@tu-dresden.de',
                'properties': {
                    'fullname': "User"
                },
                'roles': ('ZopRAUser'),
            },
            {
                'username': 'reviewer',
                'password': 'reviewer',
                'email': 'reviewer@zopratec.de',
                'properties': {
                    'fullname': "Chefredakteur"
                },
                'roles': ('ZopRAUser', 'ZopRAReviewer'),
            },
            {
                'username': 'zopraadmin',
                'password': 'zopraadmin',
                'email': 'zopraadmin@zopratec.de',
                'properties': {
                    'fullname': "ZopRAAdmin"
                },
                'roles': (),
            },
        ]
        for datum in user_data:
            user = plone.api.user.get(datum['username'])
            if user is None:
                user = plone.api.user.create(**datum)
