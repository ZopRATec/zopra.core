############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    Ingo.Keller@zopratec.de                                               #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
""" Provides module functions to automatically load all available ZopRA
    SubModules and manually add them to Zope-Folders.
"""
import inspect
from importlib              import import_module
import os
import types

#
# Zope Imports
#
from AccessControl          import ClassSecurityInfo, getSecurityManager
from AccessControl          import allow_module
from Globals                import DTMLFile, InitializeClass, HTML
from zExceptions            import BadRequest
from zope.i18nmessageid     import MessageFactory

from OFS.DTMLDocument       import DTMLDocument
from OFS.Folder             import Folder
from OFS.Image              import Image
from OFS.PropertyManager    import PropertyManager
from OFS.SimpleItem         import SimpleItem
from OFS.interfaces         import IObjectManager

from PyHtmlGUI              import E_PARAM_TYPE

from zopra.core.interfaces  import IZopRAProduct, IZopRAManager

# allow redirects via raise
allow_module('zExceptions.Redirect')

# build message factory
zopraMessageFactory = MessageFactory('zopra')
# make import of MessageFactory possible from PythonScripts
allow_module('zopra.core.zopraMessageFactory')
#
# Globally interesting Manager Name Constants
#
ZM_PM       = 'ZopRAProduct'
ZM_SM       = 'SeedManager'
ZM_CM       = 'ContactManager'
ZM_PLASMID  = 'PlasmidManager'
ZM_PLM      = 'PlantManager'
ZM_SCM      = 'SecurityManager'
ZM_IM       = 'FileManager'
ZM_PNM      = 'PrintManager'
ZM_MM       = 'MessagingManager'
ZM_P_PUB    = 'Publication'
ZM_L_SEQADM = 'SequencingAdministration'
ZM_S_SM     = 'StorageManager'
ZM_MBM      = 'MessageBoard'
ZM_T_PGM    = 'PrimerGenManager'
ZM_T_GLM    = 'GelManager'
ZM_S_SGM    = 'SequencingManager'
ZM_S_SNM    = 'SnpManager'
ZM_GGM      = 'GeneralGene'
ZM_CTM      = 'ContentManager'
ZM_TEST     = 'TestManager'
ZM_DEBUG    = 'DebugInfoManager'


modifyPermission = 'Modify ZopRA Content'
addPermission    = 'Add ZopRA Managers'
viewPermission   = 'View'
managePermission = 'Manage ZopRA'

zopra_permissions = ( (modifyPermission,  ('ZopRAAdmin', 'ZopRAAuthor', 'ZopRAReviewer')),
                      (addPermission,    ('Manager',)),
                      (managePermission, ('Manager',)),
                      )

# load the generic DTML text
# via DTMLFile (automatic path handling / formatting)
GENERIC_ADD_FORM         = DTMLFile( 'dtml/GenericAdd',        globals() )
GENERIC_PRODUCT_ADD_FORM = DTMLFile( 'dtml/GenericProductAdd', globals() )


def manage_addGeneric( dispatcher,
                       zope_id,
                       title,
                       manager,
                       pkg,
                       nocreate     = 0,
                       zopratype    = '',
                       ebase        = None,
                       accessgroups = None,
                       REQUEST      = None ):
    """ Create any new Generic Manager and add it to destination. """
    managerClass = getattr(import_module(pkg), manager)
    obj          = managerClass( id         = zope_id,
                                 title      = title,
                                 nocreate   = nocreate,
                                 zopratype  = zopratype )
    # set ebase
    if ebase:
        obj.activateEBaSe()

    # set access groups
    if accessgroups:
        obj.activateSBAR()

    target = dispatcher.Destination()
    target._setObject(zope_id, obj)

    # call installConfig Hook on each installation
    # (REQUEST for install params from dtml form)
    obj.installConfig(REQUEST)

    # if database gets created (first setup), call startupConfig Hook
    # for initial db entries
    if not nocreate:
        obj.setContainer(target)
        obj.startupConfig(REQUEST)
        obj.delContainer()

    return target.manage_main(target, REQUEST)


def manage_addProductGeneric( dispatcher,
                              zope_id,
                              title,
                              manager,
                              pkg,
                              connection_id,
                              nocreate     = 0,
                              zopratype    = '',
                              REQUEST      = None ):
    """Create any new Product Manager and add it to destination."""

    managerClass = getattr(import_module(pkg), manager)

    obj = managerClass( id            = zope_id,
                        title         = title,
                        connection_id = connection_id,
                        nocreate      = nocreate,
                        zopratype     = zopratype )

    target = dispatcher.Destination()
    target._setObject(zope_id, obj)
    return target.manage_main(target, REQUEST)


def registerManager(context, managerClass):
    """ This method registers a manager and all of its supporting files in the
        ZopRA environment.

        The registration process is done during Zope's startup phase and
        changes to the registered manager will only be reflected by restarting
        the server instance.
    """

    # sanity check - we only handle class objects
    if not inspect.isclass(managerClass):
        print "%s is not a class object" % managerClass.__class__

    # initialize class via Zope
    InitializeClass(managerClass)

    # determine manager type
    is_product  = IZopRAProduct.implementedBy(managerClass)
    file_path   = inspect.getfile(managerClass)
    class_path  = os.path.split(file_path)[0]
    manager     = managerClass.__name__
    module      = managerClass.__module__

    # check if there exists a custom DTML add form for the manager
    dtml_file   = os.path.join(class_path, 'dtml', '%sAdd' % manager)

    # get DTML add form
    if os.path.exists(dtml_file + '.dtml' ):

        # custom form available
        addForm = DTMLFile( dtml_file, globals() )

    else:

        # generic form needed
        print 'ZopRA Hint: Generic dtml used for %s' % managerClass

        # try to get name suggestions
        if hasattr(managerClass, 'suggest_id'):
            sid = managerClass.suggest_id
        else:
            sid = '<insert id>'

        if hasattr(managerClass, 'suggest_name'):
            sname = managerClass.suggest_name
        else:
            sname = manager

        # read from generic file, construct DTML document
        # workaround, because manage_edit of DTMLFile doesn't work

        # determine the corresponding DTML File
        # differentiate between normal managers and products
        # this is done here to allow manual Form with generic function
        if is_product:
            addFormDTML = GENERIC_PRODUCT_ADD_FORM
        else:
            addFormDTML = GENERIC_ADD_FORM

        content = addFormDTML.read() % (sid, sname, manager, module)

        # now build DTMLDocument

        # __name__ is important for registry to differentiate the objects
        addForm = DTMLDocument( id       = manager,
                                title    = manager,
                                __name__ = manager )
        # set the data
        addForm.manage_edit(title = manager, data = content)

    # get adding function
    funcname = 'manage_add%s' % manager

    # without func, the generic way is used
    # -> no registration
    if hasattr( managerClass, funcname ):
        # manual function
        func = getattr( managerClass, funcname )

    else:
        # generic functions
        if is_product:
            func = manage_addProductGeneric
        else:
            func = manage_addGeneric

    context.registerClass( managerClass,
                           permission    = addPermission,
                           constructors  = (addForm, func),
                           permissions   = zopra_permissions,
                           legacy        = (getProductManager,),
                           )
    print manager, 'registered'


def initialize(context):
    """\brief Initialize ZopRA with all Managers
    """
    print 'Initializing ZopRA'

    from zopra.core.tools.ZopRAProduct          import ZopRAProduct
    from zopra.core.tools.ContactManager        import ContactManager
    from zopra.core.tools.ContentManager        import ContentManager
    from zopra.core.tools.DebugInfoManager      import DebugInfoManager
    from zopra.core.tools.FileManager           import FileManager
    from zopra.core.tools.GenericManager        import GenericManager
    from zopra.core.tools.MessagingManager      import MessagingManager
    from zopra.core.tools.PrintManager          import PrintManager
    from zopra.core.tools.SecurityManager       import SecurityManager
    from zopra.core.tools.TemplateBaseManager   import TemplateBaseManager
    from zopra.core.tools.TestManager           import TestManager

    registerManager(context, ZopRAProduct)
    registerManager(context, ContactManager)
    registerManager(context, ContentManager)
    registerManager(context, DebugInfoManager)
    registerManager(context, FileManager)
    registerManager(context, GenericManager)
    registerManager(context, MessagingManager)
    registerManager(context, PrintManager)
    registerManager(context, SecurityManager)
    registerManager(context, TemplateBaseManager)
    registerManager(context, TestManager)


def getProductManager(context):
    """ This method finds the Product Manager within the current folder and
        above.
    """
    # TODO: find another way then this function to test for ZopRAProduct
    #       in the dtml-addforms
    while context:

        if IObjectManager.providedBy(context):
            for obj in context.objectValues():

                if IZopRAProduct.providedBy(obj):
                    return obj.getId()

        # move one step up once current level is finished
        if hasattr(context, 'aq_parent'):
            context = context.aq_parent
        else:
            context = None
