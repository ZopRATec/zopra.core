from zopra.core import ZC
from zopra.core.lists.MultiList import MultiList


class HierarchyList(MultiList):
    """Hierarchical Lists (Tree Lists) based on Multilists"""

    _className = "HierarchyList"
    _classType = MultiList._classType + [_className]

    # for compatibility
    listtype = "hierarchylist"

    def __init__(self, listname, manager, function, table, label="", map=None, docache=True):
        """Construct a MultiList."""
        MultiList.__init__(self, listname, manager, function, table, label, map, docache)

    def getHierarchyListParent(self, autoid):
        """Returns the parent-id (stored in rank for the beginning)
        of the entry with autoid in the list."""
        if autoid == 0:
            return None
        entry = self.getEntry(autoid)
        return int(entry.get(ZC.RANK, 0))

    def getHierarchyListAncestors(self, autoid):
        """utility function for new hierarchylist template handling, retrieves
        the ancestor line of an entry with the given autoid"""
        ancestors = []
        # show / list widgets need an empty list, when no value was given (None or '')
        if autoid in (None, ""):
            return []
        # in all other cases, autoid is a number (0 for first level on search)
        autoid = int(autoid)
        ancestor = self.getHierarchyListParent(autoid)
        while ancestor is not None:
            ancestors.append(ancestor)
            ancestor = self.getHierarchyListParent(ancestor)
        ancestors.reverse()
        ancestors.append(autoid)
        return ancestors

    def getHierarchyListDescendants(self, autoid):
        """Get all descendents of the node represented by autoid recursively."""
        descendants = []
        autoid = int(autoid)

        for child in self.getEntriesByParent(autoid):
            descendants.append(child["autoid"])
            descendants = descendants + self.getHierarchyListDescendants(child["autoid"])

        return descendants

    def getAllSubLeafs(self, autoid, entries):
        """Find all leaves of the given branch"""
        children = []
        # search entries
        for entry in entries:
            # test for parent = autoid
            if (entry.get(ZC.RANK) or entry.get(ZC.RANK) == 0) and int(entry[ZC.RANK]) == int(autoid):
                # found a child
                childid = entry.get(ZC.TCN_AUTOID)
                # test it for own children
                newChildren = self.getAllSubLeafs(childid, entries)
                if not newChildren:
                    # this entry is a leaf child
                    children.append(childid)
                else:
                    # there are children, we put them in the result list
                    children.extend(newChildren)
        # return child list
        return children

    def getEntriesByParent(self, parentid=None, with_hidden=False):
        """Returns all entrys connected to a parent, 0 = first level entries without parent"""
        # value - searches are not put in cache and not taken from cache completely
        # only the single entries are later on fetched from cache
        mgr = self.getForeignManager()
        if self.foreign and self.foreign in mgr.listHandler:
            lobj = mgr.listHandler[self.foreign]
            return lobj.getEntriesByParent(parentid, with_hidden)
        completelist = []

        parentid = str(parentid)

        where = ""
        if parentid is not None:
            # search for value
            parentid = parentid.replace("*", "%")
            where = " WHERE rank like '%s'" % parentid
            sort = " ORDER BY value ASC "
        sql = "SELECT %s FROM %s%s%s%s;"
        sql = sql % (ZC.TCN_AUTOID, mgr.id, self.listname, where, sort)
        results = mgr.getManager(ZC.ZM_PM).executeDBQuery(sql)
        for result in results:
            # tell getEntry to fetch from DB instead cache if do_cache is True
            # because then the cache was empty
            # otherwise we can use the cache for getEntry (even for value-searches)
            completelist.append(self.getEntry(result[0]))

        return completelist
