import inspect
import os.path
import StringIO
import types

import zopra.core
from zopra.core.Classes import XMLHandler
from zopra.core.Classes import make_parser
from zopra.core.interfaces import IZopRAManager


E_FILE_NOT_FOUND = "[Error] File not found: %s"


def getZopRAPath():
    """This method returns the path in of the zopra.core package.

    @return String directory name of the zopra.core package
    """
    return os.path.dirname(zopra.core.__file__)


def getParentManager(context):
    """This method returns the parent manager from the given node.

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
    except Exception:
        raise ValueError("No Manager found via getParentNode()")

    return context


def getASTFromXML(xml):
    """This method reads a XML-string and converts it into an object tree
        representation.

    @param xml - string containing the XML
    @result object - the object tree's root element
    """
    assert isinstance(xml, types.StringType)

    inputFile = StringIO.StringIO(xml)

    # XML handling
    xsHandler = XMLHandler()
    saxParser = make_parser()
    saxParser.setContentHandler(xsHandler)

    # parse file
    saxParser.parse(inputFile)

    # return object-tree
    return xsHandler.getObjectTree()


def getClassPath(obj):
    """This method returns the path of the objects class file.

    @param obj - object for which the class file path should be returned
    @result path object - contains the path to the class file
    """
    return os.path.split(inspect.getfile(obj.__class__))[0]


def getModulePath(cls):
    """This method returns the path of the object's class file.

    @param cls - class for which the class file path should be returned
    @result path object - contains the path to the class file
    """
    _path = inspect.getfile(cls)
    if _path.endswith("pyc"):
        _path = _path[:-1]
    return _path


def getTableDefinition(manager):
    """This method returns the table definition of the given manager.

    @param manager - ZopRA manager
    @result string - XML containing the table definition
    """

    # model loading
    className = manager.getClassName()
    _file = os.path.join(getClassPath(manager), "model", "%s.xml" % className)

    if os.path.exists(_file):
        with open(_file, "r") as fHandle:
            return fHandle.read()

    return '<?xml version="1.0"?><Tabledefinition />'


def getIconsDefinition(manager):
    """This method returns the icon definition of the given manager.

    @param manager - ZopRA manager
    @result string - XML containing the icon definition
    """

    # model loading
    className = manager.getClassName()
    _file = os.path.join(getClassPath(manager), "icons", "%s.xml" % className)

    if os.path.exists(_file):
        with open(_file, "r") as fHandle:
            return fHandle.read()

    return '<?xml version="1.0"?><Icondefinitions />'
