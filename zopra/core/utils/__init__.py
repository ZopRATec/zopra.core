import inspect
import os.path
import StringIO
from xml.sax import make_parser

import zopra.core
from zopra.core.interfaces import IZopRAManager
from zopra.core.types import StringType
from zopra.core.utils.Classes import XMLHandler


def getZopRAPath():
    """Return the path of the zopra.core package.

    :return: directory name of the zopra.core package
    :rtype: string
    """
    return os.path.dirname(zopra.core.__file__)


def getParentManager(context):
    """This method returns the parent manager from the given node.

    The method goes up at least one level. It does not check whether the
    given node is already a manager.

    :param context: Zope element
    :type context: object
    :raises ValueError: if no manager could be found
    :return: the parent manager
    :rtype: zopra.core.Manager.Manager
    """
    context = context.getParentNode()

    try:
        while not IZopRAManager.providedBy(context):
            context = context.getParentNode()
    except Exception:
        raise ValueError("No Manager found via getParentNode()")

    return context


def getASTFromXML(xml):
    """Read a XML-string and convert it into an object tree representation.

    :param xml: the xml string
    :type xml: string
    :return: the objects tree's root element
    :rtype: object
    """
    assert isinstance(xml, StringType)

    inputFile = StringIO.StringIO(xml)

    # XML handling
    xsHandler = XMLHandler()
    saxParser = make_parser()
    saxParser.setContentHandler(xsHandler)

    # parse file
    saxParser.parse(inputFile)

    # return object-tree
    return xsHandler.getObjectTree()


def getModulePath(obj):
    """Return the path up to but not including the object's class file (a.k.a the module path).

    :param obj: object for which the module path should be returned
    :type obj: object
    :return: the module path
    :rtype: string
    """
    return os.path.split(inspect.getfile(obj.__class__))[0]


def getTableDefinition(manager):
    """Return the table definition of the given manager.

    :param manager: ZopRA Manager
    :type manager: zopra.core.Manager.Manager
    :return: the XML table definition
    :rtype: string
    """
    # model loading
    className = manager.getClassName()
    _file = os.path.join(getModulePath(manager), "model", "%s.xml" % className)

    if os.path.exists(_file):
        with open(_file, "r") as fHandle:
            return fHandle.read()

    return '<?xml version="1.0"?><Tabledefinition />'
