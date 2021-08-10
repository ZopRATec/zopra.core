from builtins import object

from zopra.core import IObjectManager
from zopra.core.constants import ZC
from zopra.core.interfaces import IZopRAManager
from zopra.core.interfaces import IZopRAProduct


folder_types = ["Folder", "ATFolder"]


class ManagerFinderMixin(object):
    """The ManagerFinderMixin class provides methods to find managers."""

    def getContainer(self):
        """Returns the Zope container where the actual object is in.

        :return: Zope Container, otherwise None
        """
        not_found = True
        container = self
        # stack = ['start:']
        while not_found:

            if not container:
                # try to get folder name from physical path
                foldername = self.getPhysicalPath()[-2]
                container = None

                if foldername:

                    # getattr uses aquisition
                    container = getattr(self, foldername)

                else:

                    # top level, get root
                    container = self.restrictedTraverse("/")

                if not container:
                    raise ValueError("No Container found.")

                return container

            container = container.getParentNode()
            # first folder is returned
            if hasattr(container, "meta_type") and container.meta_type in folder_types:
                not_found = False

        return container

    def getManager(self, name, obj_id=None):
        """Returns the specified manager.

        If you use DTML to call a manager, be sure to work in the managers directory!
        Use <dtml-with <dirname>> to achieve this. Otherwise, the dtml's directory will
        be misunderstood as container and the searched manager will never be found.

        :param name: The name of the manager.
        :param obj_id: Use obj_id to specify a manager id in an environment where more than
        one manager of a special type is instantiated.
        :return: a manager object if one was found, otherwise None.
        :rtype: zopra.core.Manager.Manager
        """
        container = self.getContainer()
        if name and hasattr(container, "objectValues"):

            # iterate over container content
            for obj in container.objectValues():

                if hasattr(obj, "getClassType") and name in obj.getClassType():

                    # if id is given then look also for these
                    if obj_id:
                        if hasattr(obj, "id") and str(obj.id) == obj_id:
                            return obj

                    # in all other cases return with the first object
                    # that was found
                    else:
                        return obj

        return None

    def getObjByMetaType(self, meta_type, obj_id=None):
        """Returns a specified object with meta_type and obj_id.

        :param meta_type: meta_type / class name of the manager
        :param obj_id: Use obj_id to specify a manager id in an environment where more than
        one manager of a special type is instantiated.
        :return: an object if one was found, otherwise None.
        """
        container = self.getContainer()

        while container:

            if meta_type and hasattr(container, "objectValues"):

                # iterate over container content
                for obj in container.objectValues():

                    if hasattr(obj, "meta_type") and obj.meta_type == meta_type:

                        # if id is given then look also for these
                        if obj_id:
                            if hasattr(obj, "id") and str(obj.id) == obj_id:
                                return obj

                        # in all other cases return with the first object
                        # that was found
                        else:
                            return obj
            if container is None or container.isTopLevelPrincipiaApplicationObject:
                break
            container = container.getParentNode()
        return None

    def getHierarchyUpManager(self, name, obj_id=None):
        """Returns the specified manager out of the Folder Hierarchy.

        :param name: The name of the manager
        :param obj_id: Use obj_id to specify a manager id in an environment where more than
        one manager of a special type is instantiated.
        :return: a manager object if one was found, otherwise None.
        :rtype: zopra.core.Manager.Manager
        """
        if not name:
            return None

        # get path, traverse to each folder beginning at the last
        # then look for manager
        allpath = self.getPhysicalPath()

        for index in xrange(len(allpath) - 1):

            # get the path part without the end (larger index, longer end)
            # loose at least 1 part (last is manager)
            actpath = allpath[: -index - 1]
            try:
                folder = self.unrestrictedTraverse(actpath)
            except Exception:
                raise ValueError([actpath, allpath, index])

            if folder:

                # iterate over container content
                for obj in folder.objectValues():

                    if IZopRAManager.providedBy(obj) and name in obj.getClassType():

                        # if id is given then look also for these
                        if obj_id and str(obj.id) == obj_id:
                            return obj

                        # in all other cases return with the first object
                        # that was found
                        else:
                            return obj

        return None

    def getHierarchyDownManager(self, name, obj_id=None, zopratype=""):
        """Returns the specified manager out of the Folder Hierarchy.

        :param name: The name of the manager
        :param obj_id: Use obj_id to specify a manager id in an environment where more than
        one manager of a special type is instantiated.
        :return: a manager object if one was found, otherwise None.
        :rtype: zopra.core.Manager.Manager
        """
        assert ZC.checkType("name", name, type(""))
        # go back until we find a folder
        # for older zope versions that have a problem with redirection and
        # getParentNode
        # we have to look upwards for a folder, because getParentNode might be
        # another manager
        folder = self.getParentNode()
        while IZopRAManager.providedBy(folder):
            folder = folder.getParentNode()

        # start the loop on this folder
        return self.getManagerDownLoop(folder, name, obj_id, zopratype)

    def getManagerDownLoop(self, folder, name, obj_id=None, zopratype=None):
        """Helper method to loop through children of a folder.

        :param folder: start folder
        :type folder: OFS.ObjectManager
        :param name: Manager Classname
        :type name: string
        :param obj_id: target id, defaults to None
        :type obj_id: string, optional
        :param zopratype: target zopratype, defaults to None
        :type zopratype: string, optional
        :return: target manager
        :rtype: zopra.core.Manager.Manager
        """

        if not IObjectManager.providedBy(folder):
            return None

        # iterate over container content
        for obj in folder.objectValues():
            # we found a ZopRAManager
            if IZopRAManager.providedBy(obj):
                # check if we found the correct one
                if name in obj.getClassType():
                    check_zt = not zopratype or obj.getZopraType() == zopratype
                    if check_zt and (not obj_id or str(obj.id) == obj_id):
                        return obj

            # no recursive lookup into a manager
            elif IObjectManager.providedBy(obj):
                obj2 = self.getManagerDownLoop(obj, name, obj_id, zopratype)
                if obj2:
                    return obj2
                # else stay in the loop

        return None

    def getAllManagersDownLoop(
        self, folder, zopratype="", result_dict=None, classname=None
    ):
        """Helper method to loop through children of a folder.

        :param folder: object that provides IObjectManager
        :type folder: OFS.ObjectManager
        :param zopratype: string containing the zopratype, defaults to ""
        :type zopratype: str, optional
        :param result_dict: if provided, the results will be added, defaults to None
        :type result_dict: dict, optional
        :param classname: specifies a particular class, defaults to None
        :type classname: str, optional
        :return: a dict with the structure { <ID> : <IZopRAManager> }
        :rtype: dict
        """
        # not a folder object return empty dictionary
        if not IObjectManager.providedBy(folder):
            return {}

        # create a dictionary if not provided
        if result_dict is None:
            result_dict = {}

        # iterate over container content
        for obj in folder.objectValues():

            # if we have a origin, the folder of the found manager must
            # have the same id
            if IZopRAManager.providedBy(obj):

                # check also zopratype and classname if present
                check_zt = zopratype is None or obj.getZopraType() == zopratype
                check_cn = classname is None or obj.getClassName() == classname
                if check_zt and check_cn:
                    result_dict[obj.id] = obj

            # no recursive lookup into a manager
            elif IObjectManager.providedBy(obj):
                self.getAllManagersDownLoop(obj, zopratype, result_dict, classname)
        return result_dict

    def getAllManagersHierarchyDown(self, zopratype="", classname=None):
        """Returns an unordered list with all manager objects found downward in the hierarchy.

        :param zopratype: string containing the zopratype, defaults to ""
        :type zopratype: str, optional
        :param classname: specifies a particular class, defaults to None
        :type classname: str, optional
        :return: list of Manager objects
        :rtype: list
        """
        return self.getAllManagersDownLoop(
            self.getParentNode(), zopratype, classname=classname
        ).values()

    def getAllManagers(self, type_only=True, objects=False):
        """Returns a list with all managers of a special type.

        :param type_only:  If True the result contains the meta_types of the manager;
        otherwise contains the IDs of the managers (default is True). Defaults to true.
        :type type_only: bool, optional
        :param objects: If True the result contains the manager objects; otherwise the IDs or meta_types. Defaults to False
        :type objects: bool, optional
        :return:  A list of meta_types, IDs or objects of the managers from the actual container and above.
        :rtype: list
        """
        result_dict = {}

        # we use a dictionary to receive only one manager per type
        # now managers in the hierarchy
        folder = self.getParentNode()

        # go up as long as we have a parent object
        while folder:

            # iterate over container content
            for obj in folder.objectValues():
                if IZopRAManager.providedBy(obj) and not IZopRAProduct.providedBy(obj):

                    if type_only:
                        className = obj.getClassName()
                        if className not in result_dict:
                            result_dict[className] = obj

                    else:
                        result_dict[obj.id] = obj

            if folder.isTopLevelPrincipiaApplicationObject:
                folder = None
            else:
                folder = folder.getParentNode()

        if objects:
            return result_dict.values()

        return result_dict.keys()

    def topLevelProduct(self, zopratype=""):
        """Returns the hierarchy's topmost product manager.

        :param zopratype: string containing the zopratype, defaults to ""
        :type zopratype: str, optional
        :return: Topmost product manager
        :rtype: zopra.core.Manager.Manager
        """
        # TODO: switch to path-related traversal (see getHierarchyUpManager)
        product = None
        folder = self.getContainer()

        while folder:
            # iterate over container content
            for obj in folder.objectValues():
                if IZopRAProduct.providedBy(obj) and (
                    zopratype is None or obj.getZopraType() == zopratype
                ):
                    product = obj

            folder = (
                None
                if folder.isTopLevelPrincipiaApplicationObject
                else folder.getParentNode()
            )

        return product
