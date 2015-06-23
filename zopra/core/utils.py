import os.path
import StringIO
import types

from OFS.interfaces         import IObjectManager

import zopra.core
from zopra.core.interfaces  import IZopRAManager
from zopra.core.Classes     import XMLHandler, make_parser
import inspect


def getZopRAPath():
    """ This method returns the path in of the zopra.core package.

    @return String directory name of the zopra.core package
    """
    return os.path.dirname(zopra.core.__file__)


def getParentManager( context,
                      error_message = 'No Manager found via getParentNode()' ):
    """ This method returns the parent manager from the given node.

    The method goes up at least one level. It does not check whether the
    given node is already a manager.

    @throws ValueError Exception if no manager could be found

    @param  context - Zope element
    @param  error_message - a string which might contain a more specific error
                            message
    @return Manager
    """
    context = context.getParentNode()

    try:
        while not IZopRAManager.providedBy(context):
            context = context.getParentNode()
    except:
        raise ValueError(error_message)

    return context


def gatherManagers(context):
    """ This method finds the Manager instances in the current folder and above

    @return List - unsorted list of IDs
    """
    ids = []

    while context:

        if IObjectManager.providedBy(context):
            for obj in context.objectValues():

                if IZopRAManager.providedBy(obj):
                    ids.append(obj.getId())

        if hasattr(context, 'aq_parent'):
            context = context.aq_parent
        else:
            context = None

    return ids


def getASTFromXML(xml):
    """ This method reads a XML-string and converts it into an object tree
        representation.

    @param xml - string containing the XML
    @result object - the object tree's root element
    """
    assert(isinstance(xml, types.StringType))

    inputFile = StringIO.StringIO(xml)

    # XML handling
    xsHandler  = XMLHandler()
    saxParser = make_parser()
    saxParser.setContentHandler(xsHandler)

    # parse file
    saxParser.parse(inputFile)

    # return object-tree
    return xsHandler.getObjectTree()


def getClassPath(obj):
    """ This method returns the path of the objects class file.

    @param obj - object for which the class file path should be returned
    @result path object - contains the path to the class file
    """
    return os.path.split(inspect.getfile(obj.__class__))[0]


def getTableDefinition(manager):
    """ This method returns the table definition of the given manager.

    @param manager - ZopRA manager
    @result string - XML containing the table definition
    """

    # model loading
    className   = manager.getClassName()
    xml_file    = os.path.join( getClassPath(manager),
                                'model', '%s.xml' % className )

    if os.path.exists(xml_file):
        fHandle     = open(xml_file, 'r')
        result      = fHandle.read()
        fHandle.close()
    else:
        result    = '<?xml version="1.0"?><Tabledefinition />'

    return result


def getIconsDefinition(manager):
    """ This method returns the icon definition of the given manager.

    @param manager - ZopRA manager
    @result string - XML containing the icon definition
    """

    # model loading
    className   = manager.getClassName()
    xml_file    = os.path.join( getClassPath(manager),
                                'icons', '%s.xml' % className )

    if os.path.exists(xml_file):
        fHandle = open(xml_file, 'r')
        result  = fHandle.read()
        fHandle.close()
    else:
        result  = '<?xml version="1.0"?><Icondefinitions />'

    return result
