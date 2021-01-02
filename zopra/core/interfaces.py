from OFS.interfaces import IFolder
from zope.interface import Interface


class IAddOnInstalled(Interface):
    """A layer specific for this add-on product.

    This interface is referred in browserlayer.xml.

    All views and viewlets register against this layer will appear on
    your Plone site only when the add-on installer has been run.
    """


class IZopRAManager(IFolder):
    """The IZopRAManager interface marks a class to be a ZopRA manager.

    The ManagerPart class implements the interface. If your manager class is
    derived from the zopra.core.ManagerPart then you do not have to implement it
    on your own.
    """

    def getZopraType(self):
        """Returns the internal type of the manager (to have different handling
            for same managers with different type).

        @result string - zopratyp
        """

    def getClassName(self):
        """Returns the class name.

        @result string - class name (self.__class__.__name__)
        """

    def getClassType(self):
        """This method returns a list of the class names of all ancestors and the current class"""


class IZopRAProduct(IZopRAManager):
    """The IZopRAProduct interface marks a class to be a ZopRA product manager."""


class IGenericManager(IZopRAManager):
    """The IGenericManager interface marks a class to be derived from the class
    zopra.core.tools.GenericManager.GenericManager.
    """

    def installConfig(self, REQUEST):
        """This hook method gets called after object creation by
        manageAddGeneric on each install.

        The hook can be used to get DTML-form values from the REQUEST.
        For database action (only on first install) see startupConfig Hook
        """


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
