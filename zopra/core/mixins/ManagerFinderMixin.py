from OFS.interfaces         import IObjectManager

from zopra.core.constants   import ZC
from zopra.core.interfaces  import IZopRAManager, IZopRAProduct


class ManagerFinderMixin(object):
    """ The ManagerFinderMixin class provides methods to find managers. """


    def getHierarchyUpManager(self, name, obj_id = None):
        """ Returns the specified manager out of the Folder Hierarchy.

        @param name  The argument \a name is the name of the manager.
        @param id    The argument \a id is to specify a manager id in an
                     environment where more than one manager of a special type
                     is instanciated.

        @return a manager object if one was found, otherwise None.
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
            except:
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


    def getHierarchyDownManager(self, name, obj_id = None, zopratype = ''):
        """ Returns the specified manager out of the Folder Hierarchy.

        @param name  The argument \a name is the name of the manager.
        @param id    The argument \a id is to specify a manager id in an
                     environment where more than one manager of a special type
                     is instantiated.

        @return a manager object if one was found, otherwise None.
        """
        assert ZC.checkType('name', name, type(''))
        print 'Search for ', name, obj_id, zopratype
        print '-------------------------------------'
        # go back until we find a folder
        # for older zope versions that have a problem with redirection and
        # getParentNode
        # we have to look upwards for a folder, because getParentNode might be
        # another manager
        folder = self.getParentNode()
        while IZopRAManager.providedBy(folder):
            folder = folder.getParentNode()

        # start the loop on this folder
        return self.getManagerDownLoop( folder,
                                        name,
                                        obj_id,
                                        zopratype )

    def getManagerDownLoop( self,
                            folder,
                            name,
                            obj_id    = None,
                            zopratype = None ):
        """ Helper method to loop through children of a folder. """

        if not IObjectManager.providedBy(folder):
            return None

        # iterate over container content
        for obj in folder.objectValues():
            # we found a ZopRAManager
            if IZopRAManager.providedBy(obj):
                # check if we found the correct one
                if ( name in obj.getClassType()                         and
                     (not zopratype or obj.getZopraType() == zopratype) and
                     (not obj_id    or str(obj.id)        == obj_id   ) ):
                    return obj

            # no recursive lookup into a manager
            elif IObjectManager.providedBy(obj):
                obj2 = self.getManagerDownLoop(obj, name, obj_id, zopratype)
                if obj2:
                    return obj2
                # else stay in the loop

        return None


    def getAllManagersDownLoop( self,
                                folder,
                                zopratype   = '',
                                result_dict = None,
                                classname   = None ):
        """ Helper method to loop through children of a folder.

        @param folder      - object that implements IObjectManager
        @param zopratype   - string containing the zopratype
        @param result_dict - if provided the results will be added
        @param classname   - specifies a particular class
        @result { <ID> : <IZopRAManager> }
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
                if ( (zopratype is None or obj.getZopraType() == zopratype)  and
                     (classname is None or obj.getClassName() == classname) ):
                    result_dict[obj.id] = obj

            # no recursive lookup into a manager
            elif IObjectManager.providedBy(obj):
                self.getAllManagersDownLoop( obj,
                                             zopratype,
                                             result_dict,
                                             classname )
        return result_dict


    def getAllManagersHierarchyDown(self, zopratype = '', classname = None):
        """ Returns an unordered list with all manager objects found downward in
            the hierarchy.

        @param zopratype   - string containing the zopratype
        @param classname   - specifies a particular class
        @return [ <IZopRAManager>* ]
        """
        return self.getAllManagersDownLoop( self.getParentNode(),
                                            zopratype,
                                            classname = classname
                                            ).values()


    def getAllManagers(self, type_only = True, objects = False):
        """ Returns a list with all managers of a special type.

        @param type_only - boolean. If True the result contains the meta_types
                          of the manager; otherwise contains the IDs of the
                          managers (default is True).
        @param objects -  boolean. If True the result contains the manager
                          objects; otherwise the IDs or meta_types (default is
                          False).
        @result [ <_>* ] - A list of meta_types, IDs or objects of the managers
                           from the actual container and above.
        """
        result_dict = {}

        # we use a dictionary to receive only one manager per type
        # now managers in the hierarchy
        folder = self.getParentNode()

        # go up as long as we have a parent object
        while folder:

            # iterate over container content
            for obj in folder.objectValues():
                if ( IZopRAManager.providedBy(obj) and
                     not IZopRAProduct.providedBy(obj) ):

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


    def topLevelProduct(self, zopratype = None):
        """ Returns the hierarchy's topmost product manager.
        """
        # TODO: switch to path-related traversal (see getHierarchyUpManager)
        product = None
        folder  = self.getContainer()

        while folder:
            # iterate over container content
            for obj in folder.objectValues():
                if ( IZopRAProduct.providedBy(obj) and
                     (zopratype is None or obj.getZopraType() == zopratype) ):
                    product = obj

            folder = None if folder.isTopLevelPrincipiaApplicationObject else folder.getParentNode()

        return product
