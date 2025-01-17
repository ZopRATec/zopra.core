"""Provides module functions to automatically load all available ZopRA
SubModules and manually add them to Zope-Folders.
"""
from __future__ import print_function

import inspect
import os
from importlib import import_module

import pkg_resources
# Zope Imports (some for reimport)
from AccessControl import ClassSecurityInfo
from AccessControl import allow_module
from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from App.special_dtml import HTML
from App.special_dtml import DTMLFile
from OFS.DTMLDocument import DTMLDocument
from OFS.interfaces import IObjectManager
from OFS.SimpleItem import SimpleItem
from zope.i18nmessageid import MessageFactory
from zopra.core.constants import ZC
from zopra.core.interfaces import IZopRAProduct


# check for plone (Robot tests only run with plone, some functionality is removed when installing ZopRA as Plone Plugin)
# use pkg_resources.parse_version(vstring) to compare Versions
try:
    PLONE_VERSION = pkg_resources.parse_version(pkg_resources.get_distribution("plone").version)
    HAVE_PLONE = True
except pkg_resources.DistributionNotFound:
    PLONE_VERSION = pkg_resources.parse_version("0")
    HAVE_PLONE = False

# check for WebCMS (for WebCMS dependent subpackages using NavigationExtender, Byline, etc)
# use pkg_resources.parse_version(vstring) to compare Versions
try:
    WEBCMS_VERSION = pkg_resources.parse_version(pkg_resources.get_distribution("tud.profiles.webcms").version)
    HAVE_WEBCMS = True
except pkg_resources.DistributionNotFound:
    WEBCMS_VERSION = pkg_resources.parse_version("0")
    HAVE_WEBCMS = False

# allow redirects via raise
allow_module("zExceptions.Redirect")

# build message factory
zopraMessageFactory = _ = MessageFactory("zopra")
# make import of MessageFactory possible from PythonScripts
allow_module("zopra.core.zopraMessageFactory")
# make import of plone.api.portal possible from PythonScripts (for getting current language)
allow_module("plone.api.portal")
# allow type import from skin scripts for type checks with isinstance (shortcuts like 'list' wont work)
allow_module("types.ListType")

modifyPermission = "Modify ZopRA Content"
addPermission = "Add ZopRA Managers"
viewPermission = "View"
managePermission = "Manage ZopRA"

zopra_permissions = (
    (modifyPermission, ("ZopRAAdmin", "ZopRAAuthor", "ZopRAReviewer")),
    (addPermission, ("Manager",)),
    (managePermission, ("Manager",)),
)

# load the generic DTML text
# via DTMLFile (automatic path handling / formatting)
GENERIC_ADD_FORM = DTMLFile("dtml/GenericAdd", globals())
GENERIC_PRODUCT_ADD_FORM = DTMLFile("dtml/GenericProductAdd", globals())

# Testing Constants
DBDA_ID = "zmysqlconnection"


def initialize(context):
    """Initialize ZopRA with all managers"""

    from zopra.core.tools.ZopRAProduct import ZopRAProduct
    from zopra.core.Manager import Manager
    from zopra.core.tools.mgrTest import mgrTest
    from zopra.core.tools.TemplateBaseManager import TemplateBaseManager

    registerManager(context, ZopRAProduct)
    registerManager(context, Manager)
    registerManager(context, TemplateBaseManager)
    registerManager(context, mgrTest)


def manage_addGeneric(
    dispatcher,
    zope_id,
    title,
    manager,
    pkg,
    nocreate=0,
    zopratype="",
    REQUEST=None,
):
    """Create any new Generic Manager and add it to destination."""
    managerClass = getattr(import_module(pkg), manager)
    obj = managerClass(id=zope_id, title=title, nocreate=nocreate, zopratype=zopratype)
    if not REQUEST:
        # set a marker to suppress redirection in manage_afterAdd when there is no REQUEST
        # which means test-installation or showcase installation
        obj.NO_REDIRECT = True
    target = dispatcher.Destination()
    target._setObject(zope_id, obj)

    # call installConfig Hook on each installation
    # (REQUEST for install params from dtml form)
    obj.installConfig(REQUEST)

    # if database gets created (first setup), call startupConfig Hook
    # for initial database entries
    if not nocreate:
        # obj needs to know its acquisition parent (to find ZM_PM for database ops)
        obj = obj.__of__(target)
        obj.startupConfig(REQUEST)

    if not REQUEST:
        del obj.NO_REDIRECT
    else:
        return target.manage_main(target, REQUEST)


def manage_addProductGeneric(
    dispatcher,
    zope_id,
    title,
    manager,
    pkg,
    connection_id,
    nocreate=0,
    zopratype="",
    REQUEST=None,
):
    """Create any new Product Manager and add it to destination."""

    managerClass = getattr(import_module(pkg), manager)

    obj = managerClass(
        id=zope_id,
        title=title,
        connection_id=connection_id,
        nocreate=nocreate,
        zopratype=zopratype,
    )

    target = dispatcher.Destination()
    target._setObject(zope_id, obj)
    if REQUEST:
        return target.manage_main(target, REQUEST)


def registerManager(context, managerClass):
    """This method registers a manager and all of its supporting files in the
    ZopRA environment.

    The registration process is done during Zopes startup phase and
    changes to the registered manager will only be reflected by restarting
    the server instance."""

    # sanity check - we only handle class objects
    if not inspect.isclass(managerClass):
        raise ValueError("%s is not a class object" % managerClass.__class__)

    # initialize class via Zope
    InitializeClass(managerClass)

    # determine manager type
    is_product = IZopRAProduct.implementedBy(managerClass)
    file_path = inspect.getfile(managerClass)
    class_path = os.path.split(file_path)[0]
    manager = managerClass.__name__
    module = managerClass.__module__

    # check if there exists a custom DTML add form for the manager
    dtml_file = os.path.join(class_path, "dtml", "%sAdd" % manager)

    # get DTML add form
    if os.path.exists(dtml_file + ".dtml"):

        # custom form available
        addForm = DTMLFile(dtml_file, globals())

    else:

        # try to get name suggestions
        sid = managerClass.suggest_id if hasattr(managerClass, "suggest_id") else "<insert id>"
        sname = managerClass.suggest_name if hasattr(managerClass, "suggest_name") else manager

        # read from generic file, construct DTML document
        # workaround, because manage_edit of DTMLFile doesn't work

        # determine the corresponding DTML File
        # differentiate between normal managers and products
        # this is done here to allow manual Form with generic function
        addFormDTML = GENERIC_PRODUCT_ADD_FORM if is_product else GENERIC_ADD_FORM
        content = addFormDTML.read() % (sid, sname, manager, module)

        # now build DTMLDocument

        # __name__ is important for registry to differentiate the objects
        addForm = DTMLDocument(id=manager, title=manager, __name__=manager)
        # set the data
        addForm.manage_edit(title=manager, data=content)

    # get adding function
    funcname = "manage_add%s" % manager

    # without func, the generic way is used
    # -> no registration
    if hasattr(managerClass, funcname):
        # manual function
        func = getattr(managerClass, funcname)

    else:
        # generic functions
        func = manage_addProductGeneric if is_product else manage_addGeneric

    context.registerClass(
        managerClass,
        permission=addPermission,
        constructors=(addForm, func),
        permissions=zopra_permissions,
        legacy=(getProductManager,),
    )


def getProductManager(context):
    """Find the Product Manager within the current folder and above."""
    # TODO: find another way then this function to test for ZopRAProduct
    #       in the dtml-addforms
    while context:

        if IObjectManager.providedBy(context):
            for obj in context.objectValues():

                if IZopRAProduct.providedBy(obj):
                    return obj.getId()

        # move one step up once current level is finished
        context = context.aq_parent if hasattr(context, "aq_parent") else None
