"""The ManagerPart is the basic manager class."""

import os.path
from importlib import import_module
from types import ListType
from types import StringType
from types import TupleType

from zope.interface import implements

from zopra.core import ZC
from zopra.core import ClassSecurityInfo
from zopra.core import Folder
from zopra.core import Image
from zopra.core import getSecurityManager
from zopra.core import managePermission
from zopra.core import modifyPermission
from zopra.core import viewPermission
from zopra.core.Classes import Column
from zopra.core.elements.Buttons import DLG_CUSTOM
from zopra.core.IconHandler import IconHandler
from zopra.core.interfaces import IZopRAManager
from zopra.core.interfaces import IZopRAProduct
from zopra.core.LevelCache import LevelCache
from zopra.core.lists.ListHandler import ListHandler
from zopra.core.mixins.ManagerFinderMixin import ManagerFinderMixin
from zopra.core.mixins.ManagerManageTabsMixin import ManagerManageTabsMixin
from zopra.core.security.GUIPermission import GUIPermission
from zopra.core.tables.TableHandler import TableHandler
from zopra.core.utils import getIconsDefinition
from zopra.core.utils import getTableDefinition
from zopra.core.utils import getZopRAPath


SEARCH_KEYWORDS = ['NULL', '_not_', '_<_', '_>_', '_to_', '__']


class ManagerPart(Folder, ManagerFinderMixin, ManagerManageTabsMixin):
    """ ManagerPart class provides basic Form and Request Handling, Manager
        Location, Navigation and Menu Layout, Install and Uninstall methods.
    """

    implements(IZopRAManager)

    # _className and _classType are deprecated for Manager classes, we can throw them out in all packages
    # TODO: cleanup _className and _classType for all Manager classes
    _className = 'ManagerPart'
    _classType = [_className]

    meta_type = ''

    # security switch (can be enabled by __init__)
    ebase = False
    sbar = False

    manage_options = Folder.manage_options + ({'label': 'Overview', 'action': 'viewTab'},
                                                {'label': 'Update', 'action': 'updateTab'}, )

    #
    # Properties
    #
    _properties = Folder._properties + ({'id': 'delete_tables', 'type': 'int', 'mode': 'w'},
                                          {'id': 'zopra_version', 'type': 'float', 'mode': 'w'},
                                          {'id': 'zopratype', 'type': 'string', 'mode': 'w'}, )

    #
    # Property default settings
    #

    # should manage_beforeDelete delete the database tables? 0/1
    delete_tables = 0

    # the overall uptodate version number
    # set as class variable -> comparable to instance variable of same name
    zopra_version = 1.8

    # the property for distinguishing multiple instances of one manager class
    zopratype = ''

    #
    # Security
    #
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    security.declareProtected(managePermission, '__init__')

    def __init__(self, title='', part_id=None, nocreate=0, zopratype=''):
        """Constructs a ManagerPart."""
        self.title = title
        self.id = part_id

        self.nocreate     = nocreate
        self.zopratype    = zopratype
        self.tableHandler = None
        self.listHandler  = None
        self.dlgHandler   = None
        self.iconHandler  = None

        # security switches
        self.ebase         = False
        self.sbar          = False

        self.zopra_version = self.__class__.zopra_version

    ###########################################################################
    #                                                                         #
    #  Core Part basic methods for manager object handling                    #
    #                                                                         #
    ###########################################################################

    def getClassName(self):
        """ This method returns the class name.

        @result string - class name (self.__class__.__name__)
        """
        return self.__class__.__name__

    def getClassType(self):
        """This method returns a list of the class names of all ancestors and the current class"""
        return [onetype.__name__ for onetype in self.__class__.__bases__] + [self.getClassName()]

    def getTitle(self):
        """Returns the title of the object.

        @return String with the title, otherwise an empty string.
        """
        return self.title if hasattr(self, 'title') else ''

    def getId(self):
        """Returns the id of the object.

        @return String with the id, otherwise an empty string.
        """
        return self.id if hasattr(self, 'id') else ''

    ###########################################################################
    #                                                                         #
    # Dummy Functions                                                         #
    #   - overwrite for special handling                                      #
    ###########################################################################

    security.declareProtected(modifyPermission, '_addTable')

    def _addTable(self):
        """ Hook method for extra table magic on add.

        Called by manage_afterAdd if table creation is enabled via DTML add
        form.
        """
        pass


    security.declareProtected(modifyPermission, '_addTable')

    def _delTable(self):
        """ Hook method for extra table magic on delete.

        Called by manage_beforeDelete if delete_tables option is set via
        properties screen
        """
        pass

    security.declareProtected(viewPermission, 'prepareFieldForExport')

    def prepareFieldForExport(self, table, column, value, entry):
        """ Hook function called by Table.exportTab to preprocess each column
            of each entry to be exported.

        The value is already processed (translated ids into values for lists)
        and will be escaped after being returned here.

        Overwrite this function to process each single value (or replace it
        entirely) if you need special display for export. This is for example
        used to unscramble scrambled E-Mails from the database before putting
        them into the export file.
        """
        return value

    ###########################################################################
    #                                                                         #
    # SimpleItem create / copy / delete hooks (deprecated but still in use)   #
    #                                                                         #
    ###########################################################################


    security.declareProtected(managePermission, 'manage_afterAdd')

    def manage_afterAdd(self, item, container):
        """ Manage the normal manage_afterAdd method of a SimpleItem.

        1. The Method looks for an existing instance of an Product Manager. If
           there is no Product Manager the function will raise a
           <code>Programming Error</code>.
        <br>
        2. All forms defined in _dtml_dict will be installed.
        <br>
        3. All tables defined in the manager xml
           (present in the xmltransporter, put there on init) will be created.
        <br>
        4. All manager lists defined in the manager xml will be created.
        <br>
        5. If all went good the Manager will register himself at the Product
           Manager.
        """

        m_product = self.getManager(ZC.ZM_PM)

        # copy hack to avoid errors on copy/paste
        if not m_product:
            self.nocreate = 1

        # on copy, the tableHandler is there already
        if not hasattr(self, 'tableHandler') or not self.tableHandler:

            # create table Handler
            tableHandler = TableHandler()
            table_def    = getTableDefinition(self)

            # store it as subfolder
            self._setObject('tableHandler', tableHandler)

            # create list Handler
            listHandler  = ListHandler()

            # store it as subfolder
            self._setObject('listHandler', listHandler)

            # initialize tables
            self.tableHandler.xmlInit( table_def, self.nocreate )

            # initialize lists
            self.listHandler.xmlInit( table_def, self.nocreate )

            # edit tracking lists
            self.createEditTrackingLists()

        # more manager specific _addTables
        if not self.nocreate:
            self._addTable()

        # register manager as child at product manager
        if IZopRAProduct.providedBy(self) and m_product:
            m_product.registerChild(self)

        # install Icons (all available will be installed, the mapped will have properties)
        self.manage_installIcons()

        # install dialogs (dialogHandler and containers for each dlg)
        self.manage_installDialogs()


    security.declareProtected(managePermission, 'manage_beforeDelete')

    def manage_beforeDelete(self, item, container):
        """\brief Clean up before deletion.
        """
        m_product = self.getManager(ZC.ZM_PM)

        # delete the manager owned tables from the database
        if self.delete_tables:
            self._delTable()

            # delete tables
            for table in self.tableHandler.getTableIDs():
                try:
                    self.tableHandler.delTable(table)
                except:
                    # something went wrong (e.g. new table), ignore
                    pass

            # delete list references (multi and hierarchylists get their db tables deleted)
            for (table, column) in self.listHandler.references():
                try:
                    self.listHandler.disconnectList(table, column, True)
                except:
                    pass

            # delete lists
            for entry in self.listHandler.keys():
                try:
                    self.listHandler.delList(entry, True)
                except:
                    pass

        # fi delete_tables

        # remove child manager
        m_product.removeChild(self)

    ###########################################################################
    #                                                                         #
    # Helper Methods for the manage functions                                 #
    #                                                                         #
    ###########################################################################


    security.declareProtected(managePermission, 'manage_installIcons')

    def manage_installIcons(self):
        """\brief This method will be called in manage_afterAdd to install the
                  icon relevant stuff.
        """

        # init the icon handler

        # icon handler has to be reinstalled
        if hasattr(self, 'iconHandler') and self.iconHandler:
            # remove the damn thing
            self.manage_delObjects(['iconHandler'])

        namespace = self.__module__
        namespace = namespace[:namespace.rfind('.')]

        # setup new icon handler
        iconHandler      = IconHandler('iconHandler', namespace)
        self._setObject( 'iconHandler', iconHandler )
        # to stop pylint from crying
        self.iconHandler = iconHandler

        # load global sorting images
        # TODO: make "default" attribute-dependent to be able to set other themes
        path = os.path.join(getZopRAPath(), 'images')

        if os.path.exists(path):
            icons = {}
            files = []

            for zmom_files in [ZC.SORTING_FILES, ZC.LISTING_FILES, ZC.HANDLING_FILES]:
                for title in zmom_files.keys():
                    filename = zmom_files[title]
                    icons[filename] = title
                    files.append(filename)

            for name in os.listdir(path):
                filename = os.path.join(path, name)
                if not os.path.isdir(filename):
                    fHandle = open(filename, 'r')

                    if name in files:
                        title = icons[name]
                        # prefix filename to prevent collisions with more specific files
                        # TODO: find a safe way
                        name  = 'ZMOM_' + name
                        image = Image(name, title, fHandle.read())
                    else:
                        image = Image(name, '', fHandle.read())

                    iconHandler._setObject(name, image)

        # load local images from managers images directory
        if namespace != 'zopra.core':

            # re-import class to get the file location
            module = import_module(self.__module__, self.getClassName())
            path   = module.__file__

            # remove the filename from the path and add the image path location
            path = os.path.join(os.path.split(path)[0], 'images')

            if os.path.exists(path):

                for name in os.listdir(path):
                    filename = os.path.join(path, name)
                    if not os.path.isdir(filename):
                        fHandle = open(filename, 'r')
                        image   = Image(name, '', fHandle.read())

                        iconHandler._setObject(name, image)

        # map icon properties to loaded images
        self.iconHandler.xmlInit( getIconsDefinition(self) )

    security.declareProtected(managePermission, 'createEditTrackingLists')

    def createEditTrackingLists(self):
        """\brief Create List objects for creator, editor and owner"""
        lobj = self.listHandler

        # all lists are singlelists pointing to table 'person' in ContactManager
        list_def = Column(None, 'singlelist')
        list_def.setManager('ContactManager')
        list_def.setFunction('person()')
        labels = {'creator': 'Creator',
                  'editor':  'Editor',
                  'owner':   'Owner'}

        # set up foreign lists if missing
        for listname in labels.keys():

            # bind cols for each table
            list_def.setName(listname)
            list_def.setLabel(labels[listname])
            # edittrackers are invisible (except creator)
            if listname != 'creator':
                list_def.setInvisible('1')

            for table in self.tableHandler.getTableIDs():
                # but check whether it exists before (some managers still overwrite those lists :/)
                # TODO: remove creator from tabledef of all managers, it is implicit
                # (but for generic masks they have to be defined extra to show up)
                if not lobj.hasList(table, listname):
                    lobj.connectList( self, table, list_def)

    ###########################################################################
    #                                                                         #
    # Basic Helper Functions                                                  #
    #                                                                         #
    ###########################################################################

    security.declareProtected(modifyPermission, 'deleteEntries')

    def deleteEntries( self,
                       table,
                       idlist,
                       REQUEST = None ):
        """ Basic function, forwards deletion request to Table object named
            table.

        This function is called by all deletion methods and dialogs (single / multi)
        and gets overwritten by GenericManager to add a deletion hook which
        has to be used for custom deletion handling.
        @see GenericManager.prepareDelete()
        """
        if table not in self.tableHandler.keys():
            return

        if not idlist:
            return

        if not isinstance(idlist, ListType):
            idlist = [idlist]

        self.tableHandler[table].deleteEntries(idlist)


    security.declareProtected(viewPermission, 'getZopraType')

    def getZopraType(self):
        """ Returns the internal type of the manager (to have different handling
            for same managers with different type).
        """
        return self.zopratype


    # table node creation
    security.declareProtected(viewPermission, 'generateTableSearchTreeTemplate')

    def generateTableSearchTreeTemplate(self, table):
        """\brief Basic Function for search template generation.
                This function can be overwritten to produce complex search trees,
                default returns only main node of given table
                and tries to guess the table, if None is given."""
        if not table:
            tables = self.tableHandler.keys()
            if len(tables) == 1:
                table = tables[0]
            else:
                raise ValueError('No single table found to use for search')
        return self.tableHandler[table].getTableNode()


    security.declareProtected(viewPermission, 'getListSelectionConstraints')

    def getListSelectionConstraints(self, listname, lang = 'de'):
        """\brief Basic Function for List Selection Constraining.
                This function can be overwritten to constrain foreign table based lists
                based on their name by returning a constraints dictionary that will be
                used by the entry gathering mechanisms of the list objects.
        """
        return {}


    security.declareProtected(viewPermission, 'checkDefaultWildcardSearch')

    def checkDefaultWildcardSearch(self, table):
        """\brief Toggle for Wildcard Search. Overwrite this function and return True
                for the tables that will then automatically use wildcard search for all text
                fields.
        """
        return False


    security.declareProtected(viewPermission, 'forwardCheckType')

    def forwardCheckType(self, value, column_type, operator = False, label = None, do_replace = True):
        """\brief forward the type check call to the next ZopRAProduct"""
        m_prod = self.getManager(ZC.ZM_PM)
        # m_prod could be self, but doesnt matter
        return m_prod.checkType(value, column_type, operator, label, do_replace)


    # REQUEST handling
    security.declareProtected(viewPermission, 'getTableEntryFromRequest')

    def getTableEntryFromRequest(self, table, REQUEST, prefix = '', search = False):
        """\brief Builds a \c descr_dict from an REQUEST object.

        The function tries to filter all key,
        value pairs where a key matches
        with a column name of the specified table
        (maybe prefixed with DLG_CUSTOM and the given prefix).
        It also looks for special keys (ANDconcat for multi search / filter)

        \param table  The argument \a table is a string with the table name
               without id prefix.

        \param REQUEST  The argument \a REQUEST is a REQUEST object that
               contains the key, value pairs of the fields from the html form.

        \param prefix The argument \a prefix is a string that makes
               the function only filter keys that
        start with DLG_CUSTOM+prefix, the results are unprefixed however

        \param search indicates whether AND-concatenation should be checked for
               multi and hierarchy lists.

        \return The function will return a description dictionary with the
                found key - value pairs
        """
        # TODO: the parts commented as "widget check" should be moved to an extra function
        # to have only content handling here and config handling somewhere else
        descr_dict = {}
        pre        = ''
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
                        value = value.decode('utf-8')
                    except:
                        pass

                # wildcard search
                if value and do_wilds and typedefs[name] in [ZC.ZCOL_STRING, ZC.ZCOL_MEMO, ZC.ZCOL_DATE]:
                    wcs = True
                    for skw in SEARCH_KEYWORDS:
                        if value.find(skw) != -1:
                            wcs = False
                    # wrap with '*', unless it's been already wrapped;
                    # prevents cases like ******x******
                    if wcs and not (value[0] == value[-1] == '*'):
                        value = '*%s*' % value
                descr_dict[name] = value

        # get all lists
        tablelists = self.listHandler.getLists(table)

        for listobj in tablelists:
            name = listobj.listname
            pre_name = pre + name

            entry = REQUEST.get(pre_name)

            if listobj.listtype in ['multilist',  'hierarchylist']:
                if entry:
                    # the entry has to be a list
                    if not isinstance( entry, ListType  ) and \
                       not isinstance( entry, TupleType ):
                        entry = [entry]

                    # we take the note-entries from the REQUEST as well
                    pre_name_notes = pre_name + 'notes'
                    name_notes     = name     + 'notes'
                    new_entry = []
                    for item in entry:
                        # unicode conversion
                        try:
                            item = item.decode('utf-8')
                        except:
                            pass
                        if item and item != u'NULL':
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
                                    itemval = REQUEST.get(key, u'')
                                    # unicode conversion
                                    try:
                                        itemval = itemval.decode('utf-8')
                                    except:
                                        pass
                                    descr_dict[key1] = itemval
                    entry = new_entry
                else:
                    # this should lead to correct empty multilists on edit
                    entry = []

                if search:
                    # widget check
                    # check AND/OR concatenation for search
                    if REQUEST.get(pre_name + '_AND') is True or REQUEST.get(pre_name + '_AND') == 'True' or REQUEST.get(pre_name + '_AND') == '1':
                        descr_dict[name + '_AND'] = True
                    else:
                        descr_dict[name + '_AND'] = False

            # handling for all lists ... but single were handled before already?
            # FIXME: could be moved one level right into the if-statement
            if pre_name in REQUEST:
                descr_dict[listobj.listname] = entry

            # widget check
            # check filter setting stored as property
            if 'store_' + ZC.FILTER_EDIT + pre_name in REQUEST:
                filtertext = REQUEST['store_' + ZC.FILTER_EDIT + pre_name]
                if filtertext and filtertext != ZC.FCB_DEFAULT_FILTER_TEXT:
                    if not isinstance(filtertext, StringType):
                        filtertext = str(filtertext)
                    wcname = ZC.WIDGET_CONFIG + name
                    if wcname not in descr_dict:
                        descr_dict[wcname] = {}
                    descr_dict[wcname]['pattern'] = filtertext

            # widget check
            # check startitem (for range lists displaying only some entries)
            if 'frl_startitem' + pre_name in REQUEST:
                startitem = REQUEST['frl_startitem' + pre_name]
                startitem = int(startitem)

                wcname = ZC.WIDGET_CONFIG + name
                if wcname not in descr_dict:
                    descr_dict[wcname] = {}
                descr_dict[wcname]['offset'] = startitem

        return descr_dict

    security.declareProtected(viewPermission, 'getValueListFromRequest')

    def getValueListFromRequest(self, REQUEST, field):
        """ Filters multiple IDs out of the REQUEST Handler.

        @return [<values>] list with values; otherwise None.
        """
        if not hasattr(REQUEST, field):
            return []

        values = REQUEST[field]
        if not isinstance(values, ListType):
            values = [values]
        return values

    ###########################################################################
    #                                                                         #
    # Additional Utility functions                                            #
    #                                                                         #
    ###########################################################################

    # mail handling
    security.declareProtected(modifyPermission, 'sendSimpleMail')

    def sendSimpleMail(self, mto, mfrom, subject, body):
        """\brief Tries to send a email via the next available host."""
        mailHost = self.getObjByMetaType('Mail Host')
        if mailHost:
            try:
                mailHost.simple_send(mto, mfrom, subject, body)
                return True
            except Exception, exc:
                msg = 'E-Mail Error: Could not send email %s from %s to %s: Error %s'
                msg = msg % (subject, mfrom, mto, str(exc))
                self.getManager(ZC.ZM_PM).writeLog(msg)
        else:
            msg = 'E-Mail Error: Could not send email %s from %s to %s: No Mailhost found.'
            msg = msg % (subject, mfrom, mto)
            self.getManager(ZC.ZM_PM).writeLog(msg)

        return False

    def sendSecureMail(self, mto, mfrom, subject="", message="", mcc=None, mbcc=None, charset="utf-8"):
        """\brief Tries to send a email via the next available secure mail host."""
        mailHost = self.getObjByMetaType('Secure Mail Host')
        if not mailHost:
            # try normal Mail Host, that was unified with SMH (after Plone 2)
            mailHost = self.getObjByMetaType('Mail Host')
        if mailHost:
            try:
                mailHost.secureSend(message=message, mto=mto, mfrom=mfrom, subject=subject, mcc=mcc, mbcc=mbcc, charset=charset)
                return True
            except Exception, exc:
                msg = 'E-Mail Error: Could not send email %s from %s to %s: Error %s'
                msg = msg % (subject, mfrom, mto, str(exc))
                self.getManager(ZC.ZM_PM).writeLog(msg)
        else:
            msg = 'E-Mail Error: Could not send email %s from %s to %s: No Mailhost found.'
            msg = msg % (subject, mfrom, mto)
            self.getManager(ZC.ZM_PM).writeLog(msg)

        return False

    ###########################################################################
    #                                                                         #
    # Manager retrieval helper functions                                      #
    #                                                                         #
    ###########################################################################

    security.declarePrivate('getManagerDownLoop')
    security.declarePrivate('getAllManagersDownLoop')

    security.declareProtected(viewPermission, 'getHierarchyUpManager')
    security.declareProtected(viewPermission, 'getHierarchyDownManager')
    security.declareProtected(viewPermission, 'getAllManagersHierarchyDown')
    security.declareProtected(viewPermission, 'getAllManagers')
    security.declareProtected(viewPermission, 'topLevelProduct')

    ###########################################################################
    #                                                                         #
    # Security Functions                                                      #
    #   - EBaSe, SBAR, general permissions (entry / gui), forms               #
    ###########################################################################

    #
    # EBaSe functions
    #

    security.declareProtected(managePermission, 'activateEBaSe')

    def activateEBaSe(self):
        """\brief activate Entry Based Security"""
        self.ebase = True


    security.declareProtected(viewPermission, 'checkEBaSe')

    def checkEBaSe(self, table):
        """\brief check activated Entry Based Security for table
        If manager ebase switch is true and the one from the table then return True.
        """
        return self.ebase and self.tableHandler[table].ebase


    security.declareProtected(managePermission, 'initEBaSe')

    def initEBaSe(self, table):
        """\brief update show-ebase of all entries of table to match creators ebase-groups.
                  Activate Ebase at all."""
        self.ebase = True
        if not self.checkEBaSe(table):
            raise ValueError('EBaSe not enabled.')

        m_security = self.getHierarchyUpManager(ZC.ZM_SCM)
        users      = {}
        all_group  = m_security.tableHandler['ebasegroup'].getEntryAutoid('All', 'name')
        tobj       = self.tableHandler[table]
        entries    = tobj.getEntries()
        # TODO: create umask

        # TODO: apply umask

        # key = '%s_ebase_show' % table
        count = 0
        # for entry in entries:
        #    creatorid = entry.get(TCN_CREATOR)
        #    if users.has_key(creatorid):
        #        user = users.get(creatorid)
        #    else:
        #        user = m_security.getUserByCMId(creatorid)
        #        users[creatorid] = user
        #    if not user:
        #        # creator has no login, show to all
        #        egroups = [all_group]
        #    else:
        #        egroups = user.get('ebasegroups')
        #        if not egroups:
        #            # forgot to update the user
        #            egroups = [all_group]
        #    ddict = {key:egroups}
        #    tobj.updateEntry(ddict, entry[TCN_AUTOID])
        #    count += 1
        return '%s: %s entries updated.' % (table, count)

    #
    # SBAR functions
    #

    security.declareProtected(managePermission, 'activateSBAR')

    def activateSBAR(self):
        """ Activates the scope based access restrictions. """
        self.sbar = True

    security.declareProtected(viewPermission, 'checkSBAR')

    def checkSBAR(self):
        """ Returns whether the scope based access restrictions are enabled for a manager or not.

        @return boolean - True if the scope based access restrictions are enabled; otherwise False.
        """
        if not hasattr(self, 'sbar'):
            self.sbar = False
        return self.sbar


#
# permission check functions
#

    security.declareProtected(viewPermission, 'getGUIPermission')

    def getGUIPermission(self):
        """\brief"""
        obj     = None
        session = None

        # get session
        request = self.REQUEST

        if request and hasattr(request, 'SESSION'):
            session = request.SESSION
            # test session
            obj = session.get('GUIPermission')

        if obj:
            # TODO: test object correctness
            return obj
        else:
            # call creation function
            obj = self._createGUIPermission()
            if session:
                session['GUIPermission'] = obj
            return obj


    security.declareProtected(viewPermission, 'destroyGUIPermission')

    def destroyGUIPermission(self):
        """\brief"""
        # get session
        session = self.REQUEST.SESSION

        # test session
        session['GUIPermission'] = None
        return True


    security.declarePrivate('_createGUIPermission')

    def _createGUIPermission(self):
        """ Returns a new created GUIPermission object. """
        # try to get security manager
        m_sec = self.getHierarchyUpManager(ZC.ZM_SCM)
        if m_sec:

            # get login
            login = m_sec.getCurrentLogin()

            # get global roles
            groles = m_sec.getGlobalRoles()

            # get access roles
            aroles = m_sec.getAccessRoles()

            # get access roles active managers
            active = m_sec.getAccessEnabledMgrs()

        else:

            # get login
            login = getSecurityManager().getUser()

            # no security manager -> everyone is admin
            groles = ['Admin']
            aroles = LevelCache(2, [100, 100], nonpersistent = True)
            active = {}

        # create object
        return GUIPermission(login, groles, active, aroles)


    security.declareProtected(viewPermission, 'hasGUIPermission')

    def hasGUIPermission(self, table, permission_request):
        """\brief Checks permission for table."""
        if table not in self.tableHandler:
            title = self.getTitle()
            raise ValueError('Table \'%s\' does not exist in %s' % (table, title))
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        tobj  = self.tableHandler[table]
        tabid = tobj.getUId()

        return bool(perm.hasPermission(permission_request, tabid, ztype))

    security.declareProtected(viewPermission, 'isSuperUser')

    def isSuperUser(self, tabid = None, anytab = False):
        """\brief Checks if the actual user is a superuser for table with tabid (or general if no tabid given)"""
        # check permissions
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()
        suser = False
        if not tabid and anytab:
            for tab in self.tableHandler.getTableIDs():
                tabid = self.tableHandler[tab].getUId()
                suser = suser or perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        else:
            # general role check
            suser = perm.hasMinimumRole(perm.SC_SUPER, tabid, ztype)
        return suser or perm.hasSpecialRole(ztype + 'Superuser')


    security.declareProtected(viewPermission, 'hasEntryPermission')

    def hasEntryPermission(self,
                           table,
                           autoid             = None,
                           descr_dict         = None,
                           permission_request = 0):
        """\brief Return label for entry, overwrite for special functionality."""
        if autoid:
            descr_dict = self.tableHandler[table].getEntry(autoid)

        if not descr_dict:
            return False

        if 'permission' in descr_dict:
            tobj = descr_dict['permission']
            return tobj.isOwner() or tobj.hasPermission(permission_request)

        return True


    security.declareProtected(viewPermission, 'getEntryPermissions')

    def getEntryPermissions(self, acl, table):
        # function that collects permissions for an acl
        # get security manager
        m_sec = self.getHierarchyUpManager(ZC.ZM_SCM)
        if m_sec:
            # get GUIPermission object
            perm = self.getGUIPermission()

            # check ebase
            if self.checkEBaSe(table):

                # admin sees all? what about superuser?
                if perm.hasRole(perm.SC_ADMIN):
                    perms = ZC.SC_L_ALL

                else:
                    # get permissions
                    perms = m_sec.getCurrentEBaSePermission(acl)

            else:
                # no ebase, use gui permission object to get permissions
                perms = []
                if perm.hasPermission(perm.SC_VIEW):
                    perms.append(ZC.SC_READ)
                    perms.append(ZC.SC_LREAD)

                if perm.hasMinimumRole(perm.SC_SUPER):
                    perms.append(ZC.SC_DEL)
                    perms.append(ZC.SC_WRITE)

        else:
            # everyone does everything
            perms = ZC.SC_L_ALL

        return perms

    ###########################################################################
    #                                                                         #
    # Update Handling                                                         #
    #   - do not forget to alter zopra_version (class attr) to new version    #
    ###########################################################################

    security.declareProtected(managePermission, 'updateVersion')

    def updateVersion(self):
        """\brief   The general update function that is called by
                    the ZopRAProduct or the manager management screen on update.
                    Updates the manager."""
        # get class-version (new) and instance-version (old)
        version = self.zopra_version
        newver  = ManagerPart.zopra_version

        # try to get newver from manager-class
        # can be used to hold some managers back on an old version ... but why?
        if hasattr(self.__class__, 'zopra_version'):
            newver = self.__class__.zopra_version

        # return string
        name = '%s: %s (%s)' % (self._class__.__name__, self.id, version)
        if self.getZopraType():
            name += ' (%s)' % self.getZopraType()

        ret = [name]
        if newver != version:
            # we update
            if version < 1.8:
                # update eight: icon handler and new list handler
                did = self.toVersion1_8()
                for item in did:
                    ret.append(item)
            self.zopra_version = newver
            ret.append('Finished update to Version %s' % self.zopra_version)
        else:
            ret.append('No updates necessary')
        return '<br>'.join(ret)

    #
    # Update single version functions (one per version, old versions should be removed someday)
    #

    security.declareProtected(managePermission, 'toVersion1_8')

    def toVersion1_8(self):
        msg = []

        # xml definition changes for different managers (maxshown / labelsearch options)
        # -> effective after reinstall of tablehandler/listhandler
        # replace table handler
        self.recreateTableHandlers()
        msg.append('Table Handler has been reinstalled.')

        # replace list handler
        self.recreateListHandlers()
        msg.append('List Handler has been reinstalled.')

        # dialog reload still manually

        msg.append('Updated to Version 1.8.')

        return msg



#
# Update helper functions
#


    security.declareProtected(managePermission, 'recreateTableHandlers')

    def recreateTableHandlers(self):
        """ Recreate table handler and reload all table objects with XML from
            table_dict
        """

        # remove tableHandler
        self._delObject('tableHandler')
        self.tableHandler = None

        # create table Handler and store it as subfolder
        self._setObject('tableHandler', TableHandler())

        # initialize tables
        self.tableHandler.xmlInit(getTableDefinition(self), True)



    security.declareProtected(managePermission, 'recreateListHandlers')

    def recreateListHandlers(self):
        """ Recreate the list handler and reload all list objects with XML from
            table_dict as well as the editTracking Lists
        """

        # remove old listhandler
        self._delObject('listHandler')
        self.listHandler = None

        # create list Handler and store it as subfolder
        self._setObject('listHandler', ListHandler())

        # do not create tables in db (they already exist)
        self.listHandler.xmlInit(getTableDefinition(self), True)

        # edit tracking lists
        self.createEditTrackingLists()

        # reset table node caches (since tableprivate holds own listhandler copy -> wah!)
        for tabname in self.tableHandler:
            tobj = self.tableHandler[tabname]
            tobj.resetSearchTreeTemplate()
