from OFS.interfaces import IFolder
from zope.interface import Interface


class IAddonInstalled(Interface):
    """A layer specific for this add-on product.

    This interface is referred in browserlayer.xml.

    All views and viewlets register against this layer will appear on
    your Plone site only when the add-on installer has been run.
    """


class IZopRAManager(IFolder):
    """The IZopRAManager interface marks a class to be a ZopRA manager.

    The Manager class implements the interface. As your manager class is
    derived from the zopra.core.Manager.Manager you do not have to implement it
    on your own.
    """

    def getZopraType(self):
        """Returns the internal type of the manager (to have different handling
            for same managers with different type).

        @result string - zopratyp
        """

    def getClassName(self):
        """Returns the class name.

        :rtype: str
        :return: class name
        """

    def getClassType(self):
        """This method returns a list of the class names of all ancestors and the current class

        :rtype: str
        :return:  list of str containing the class name
        """


class IZopRAProduct(IZopRAManager):
    """The IZopRAProduct interface marks a class to be a ZopRA product manager."""


# stays for the 2021 zopra core split to make transitions easier
class IGenericManager(IZopRAManager):
    """The IGenericManager interface is deprecated."""


class ILegacyManager(IZopRAManager):
    """Interface to mark the legacy managers in the zopra.legacy package and all subclasses."""


class IZopRATable(Interface):
    """The IZopRATable interface marks a class to be ZopRA table."""


class IZopRAList(Interface):
    """The IZopRAList interface marks a class to be ZopRA list."""


class ISecurityManager(IZopRAManager):
    """The ISecurityManager interface marks a class to provide security related
    managing functionality.
    """


class IContactManager(IZopRAManager):
    """The IContactManager interface marks a class to provide contact related
    managing functionality.
    """
