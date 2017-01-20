###########################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                   #
#    <webmaster@ingo-keller.de>                                           #
# Copyright: See COPYING file that comes with this distribution           #
#                                                                         #
###########################################################################
"""\brief Provides Joined Database Searches"""
import string
from copy                               import copy
from types                              import StringType, ListType

from PyHtmlGUI                          import E_PARAM_TYPE
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.widgets.hgLabel          import hgNEWLINE

from zopra.core                         import SimpleItem, ZC
from zopra.core.tables.Filter           import Filter
from zopra.core.elements.Buttons        import DLG_CUSTOM


ALLLISTS = ['multilist', 'hierarchylist', 'singlelist']
MULLISTS = ['multilist', 'hierarchylist']


class TablePrivate:
    """\class TablePrivate

       \brief Contains the static information about a database table.
    """

    # TODO: why do we store an own listHandler? This gets cached and updateVersion forgets those.
    # TODO: Either flush searchTreeTemplate Cache on updateVersion or restructure here
    # TODO: get ListHandler on the fly from manager instead of storing it?
    def __init__(self):
        """\brief Constructs a TablePrivate object."""
        self.tablename   = None
        self.tabledict   = None
        self.listHandler = None


    def getField(self, name):
        """\brief Returns the definition dict for a single column.
        """
        if not name:
            return {}
        
        # shortcut for ordinary autoid field
        if name == 'autoid':
            return { ZC.COL_TYPE:  'int',
                     ZC.COL_LABEL: 'Automatic No.' }

        # get field description from manager tables
        elif self.tabledict.get(name):
            return self.tabledict[name]

        elif self.listHandler.hasList(self.tablename, name):
            lobj = self.listHandler.getList(self.tablename, name)
            # singlelists are covered above, the other lists
            # are handled seperately
            # but this function is used to test for existence,
            # so we return something!
            # patch peter 11/2008 we never need the label in sql-statements, so don't try to get it
            # lead to error on foreign lists anyway (seems stored listhandler forgot its manager)
            return { ZC.COL_TYPE:  lobj.listtype,
                     ZC.COL_LABEL: name}

        # get field description from edit tracking fields
        elif ZC._edit_tracking_cols.get(name):
            return ZC._edit_tracking_cols[name]

        # nothing really found
        return {}


class TableNode(SimpleItem):
    """ Table Node

    The Table Node generates SQL for or directly delivers the IDs that
    are the result to a constrained search. To search different tables joined
    together, each node can have child-nodes which results in a search tree.

    """
    _className = 'TableNode'
    _classType = [_className]

    ##########################################################################
    #
    # Property Methods
    #
    ##########################################################################

    def getName(self):
        """\brief Returns the tableName property."""
        return self.data.tablename


    def setName(self, name):
        """\brief Sets the table name to \a name."""
        assert isinstance(name, StringType), \
               E_PARAM_TYPE % ('name', 'StringType', name)
        self.data.tablename = name

    name = property(getName, setName)

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__(self, data, mgr, prefix = ''):
        """\brief Constructs a table."""
        # prefix must not be None!
        assert isinstance(prefix, StringType), \
               E_PARAM_TYPE % ('prefix', 'StringType', prefix)
        assert isinstance(data, TablePrivate), \
               E_PARAM_TYPE % ('data', 'TableNode', data)    
        self.data           = data
        self.prefix         = prefix
        self.children       = []
        self.joinAttrParent = None
        self.joinAttrSelf   = None
        self.mgr            = mgr
        self.mgrType        = copy(mgr.getClassName())
        self.mgrId          = mgr.id
        self.sql            = ''
        self.valid          = False
        self.filterTree     = Filter(Filter.AND)
        self.manualFilter   = False
        self.order          = []
        self.orderDirection = []
        self.temporary      = False


    def copy(self, mgr, zopratype = None):
        """\brief returns a copy of the complete NodeTree.
                  zopratyped managers have to deliver the type,
                  nontyped managers using typed managers
                  inside the tree have to deliver their type.
                  Joins over different-zopratype-managers are not possible.
                  mgr has to be present as hook to find other managers."""

        # get manager
        ownMgr = mgr.getHierarchyUpManager(self.mgrType, self.mgrId)
        if not ownMgr:
            if not zopratype:
                errstr = 'Manager not found and no zopratype available.'
                err    = mgr.getErrorDialog(errstr)
                raise ValueError(err)
            ownMgr = mgr.getHierarchyDownManager( self.mgrType,
                                                  obj_id    = self.mgrId,
                                                  zopratype = zopratype )
        if not ownMgr:
            raise ValueError('Manager not found. Aborting.')

        # copy node with found manager
        # (manager-link gets lost on refresh sometimes)
        cop = TableNode(self.data, ownMgr, self.prefix)
        if self.isTemporary():
            cop.setTemporary()
        if self.filterTree:
            cop.setFilter(self.filterTree.copy())
        for entry in self.children:
            cop.addChild( entry.copy(ownMgr, zopratype),
                          entry.joinAttrParent,
                          entry.joinAttrSelf )
        return cop


    def reset(self):
        """\brief reset the attributes of this node object
            (filterTree, sql-validation, order, direction)"""
        self.valid          = False
        self.order          = []
        self.orderDirection = []
        self.filterTree     = Filter(Filter.AND)


    def resetTree(self):
        """\brief resets the complete join Tree
            (itself and propagates to its children)"""
        self.reset()
        for entry in self.children:
            if entry.isTemporary():
                self.removeChild(entry)
            else:
                entry.resetTree()


    def setPrefix(self, prefix):
        """\brief set a String prefix to identify constraints
            for this node object"""
        assert isinstance(prefix, StringType), \
               E_PARAM_TYPE % ('prefix', 'StringType', prefix)
        self.prefix = prefix


    def getPrefix(self):
        """\brief return the actual prefix"""
        return self.prefix

    p_prefix = property(getPrefix, setPrefix)


    def invalidate(self):
        """\brief sets the valid-attribute for the
            pregenerated sql-parts to False"""
        self.valid = False


    def isValid(self):
        """\brief tests the valid-attribute for the pregenerated sql-parts"""
        return self.valid


    def setFilter(self, filterTree):
        """\brief for complex where-clause, filter trees can be set manually"""
        self.filterTree   = filterTree
        self.invalidate()


    def getFilter(self):
        """\brief"""
        return self.filterTree


    def setConstraints(self, consdict):
        """\brief Stores matching constraints (including [DLG_CUSTOM+]prefix)
            from the dictionary, propagates it to its children and
            invalidates itself if a constraint change happened 
            (allows adding constraints without complete tree-invalidation)."""

        invalidChild = False
        # go through children, propagate constraints,
        # invalidate if child invalidated
        for child in self.children:
            if child.isTemporary():
                self.removeChild(child)
                continue
            invalidate = child.setConstraints(consdict)
            if invalidate:
                invalidChild = True

        if not self.filterTree:
            self.filterTree = Filter(Filter.AND)

        change = self.filterTree.setConstraints(consdict, self.prefix, self.data)

        # check own multi and hierarchy lists for AND-concat, check filter
        # each value has to be joined via extra tableNode with one value
        # values have to be removed / double-checked in filter.setConstraints

        tobj = self.mgr.tableHandler[self.data.tablename]
        multilists = self.mgr.listHandler.getLists( self.data.tablename,
                                                    types = [ 'multilist',
                                                              'hierarchylist'] )

        for lobj in multilists:
            lname = lobj.listname
            if self.prefix:
                pre = DLG_CUSTOM + self.prefix
            else:
                pre = ''
            if consdict.get(pre + lname + '_AND') and consdict.get(pre + lname):
                values = consdict.get(pre + lname)
                if not isinstance(values, ListType) or len(values) < 2:
                    continue
                # for each value, add one child
                for val in values:
                    node = tobj.getTableNode()
                    # node.setPrefix(str(val))
                    self.addChild(node, ZC.TCN_AUTOID, ZC.TCN_AUTOID)
                    # key = DLG_CUSTOM + str(val) + lname
                    node.setConstraints({lname: val})
                    node.setTemporary()

                change = True

        if change or invalidChild:
            self.invalidate()

        # propagate invalidation back up the tree
        return change or invalidChild


    def getConstraints(self):
        """\brief return the set constraints from this node object
            and all children"""
        cons = {}
        pre  = ''

        for child in self.children:
            tempcons = child.getConstraints()
            # AND-concat test
            if child.isTemporary():
                lname = tempcons.keys()[0]
                if self.prefix:
                    prefix = DLG_CUSTOM + self.prefix
                else:
                    prefix = ''
                cons[prefix + lname + '_AND'] = "1"
            else:
                prefix = ''
            for entry in tempcons:
                if prefix + entry not in cons:
                    cons[prefix + entry] = tempcons[entry]
                else:
                    if entry[-4:] == '_AND':
                        continue
                    if not isinstance(cons[prefix + entry], ListType):
                        cons[prefix + entry] = [cons[prefix + entry]]
                    cons[prefix + entry].append(tempcons[entry])

        if self.prefix and not self.isTemporary():
            pre = DLG_CUSTOM + self.prefix

        constraints = self.filterTree.getConstraints()

        for entry in constraints:
            cons[pre + entry] = constraints[entry]

        return cons


    def isConstrained(self):
        """\brief indicates whether this node object
            or the children are constrained or not."""
        if self.filterTree and self.filterTree.isConstrained():
            return True
        else:
            for child in self.children:
                if child.isConstrained():
                    return True
            # no constraints found in children as well
            return False


    def setTemporary(self):
        """\brief Mark node as temporary.
                  Temporary Nodes will be deleted on reset / setConstraints.
        """
        self.temporary = True


    def isTemporary(self):
        """\brief check whether node is temporary."""
        return self.temporary if hasattr(self, 'temporary') else False


    def setJoinAttrParent(self, attribute):
        """\brief set the name of the attribute of the parent
            which is used for joining
            (only 1 attribute joins allowed)"""
        # no check possible, object doesn't know its parent
        self.joinAttrParent = attribute


    def setJoinAttrSelf(self, attribute):
        """\brief set the name of the attribute of this node object
            which is used for joining it to its parent."""
        assert self.data.getField(attribute), \
            'JoinAttribute %s not found in table %s' % ( attribute,
                                                         self.data.tablename)
        self.joinAttrSelf = attribute


    def addChild(self, node, joinAttrParent, joinAttrChild):
        """\brief Add a child to this node object
            using the joinAttrs on parent and child side
            to make the join."""
        assert isinstance(node, TableNode), \
            'Child has to a TableNode object'
        self.children.append(node)
        node.setJoinAttrParent(joinAttrParent)
        node.setJoinAttrSelf(joinAttrChild)


    def removeChild(self, child):
        """\brief remove child"""
        if child in self.children:
            self.children.remove(child)


    def getChild(self, prefix):
        """\brief Search for a child with the given prefix
            in the join Tree beneath this node object."""
        for entry in self.children:
            if entry.getPrefix() == prefix:
                return entry
            else:
                child = entry.getChild(prefix)
                if child:
                    return child
                else:
                    # stay in for-loop
                    pass


    def getAllChildren(self):
        """\brief return the list of child-TableNode-objects"""
        return self.children


    def setOrder(self, order, direction = None):
        """\brief set the attribute name which should be used
            to sort the result, as well as its direction"""
        # TODO: allow child-columns to be used for sorting
        assert isinstance(direction, ListType) or direction in ['asc', 'desc', None], \
               'Wrong value for order direction.'
        assert order, 'Order has to be given using setOrder, got %s.' % order
        if isinstance(order, ListType):
            if isinstance(direction, ListType):
                assert len(order) == len(direction)
            # correct direction into list
            else:
                direction = len(order) * [direction]
            orders = order
            directions = direction
        else:
            orders = [order]
            directions = [direction]

        # check for double values
        already = {}
        neworders = []
        newdirections = []
        for index, order in enumerate(orders):
            if order not in already:
                neworders.append(order)
                already[order] = None
                newdirections.append(directions[index])

        orders = neworders
        directions = newdirections

        # order for multilists or hierarchylists force sql-regeneration
        # to join unconstrained lists,
        # only when order differs or a list was/is used for ordering

        oldorders = self.order
        if orders != oldorders:
            allorders = list(set(orders).union(set(oldorders)))
            for order in allorders:
                orderfield = self.data.getField(order)
                if not orderfield:
                    raise ValueError('Unknown order field %s.' % str(order))
                if orderfield[ZC.COL_TYPE] in ALLLISTS:
                    # to order by lists, we have to join the list-table -> new sql query
                    self.invalidate()
                # otherwise, the tree doesn't have to be invalidated
                # since order and direction are added after sql-caching
        self.order = orders
        self.orderDirection = directions


    def getOrder(self):
        """\brief return the list of sorting attributes"""
        return self.order


    def getOrderDirection(self):
        """\brief return the sorting direction as list of ('asc', 'desc', None)"""
        return self.orderDirection


    def getStructureHtml(self):
        """\brief Generates an html-overview of the tree structure"""
        tab = hgTable(border = 1)
        tab[0, 0] = self.getName() \
                    + hgNEWLINE    \
                    + self.mgrType \
                    + hgNEWLINE    \
                    + self.prefix  \
                    + hgNEWLINE    \
                    + self.mgr.id
        if self.filterTree:
            tab[0, 0] += hgNEWLINE + self.filterTree.getStructureHtml()
        if self.children:
            tab[0, 1] = 'Children:'
            row = 1
            for entry in self.children:
                tab[row, 1] = entry.getStructureHtml()
                row += 1
            tab.setCellSpanning(0, 0, row, 1)
        return tab


    def getSQL( self,
                limit    = None,
                offset   = None,
                function = None,
                col_list = None,
                distinct = True,
                checker  = None):
        """\brief generate the sql query, using the cached parts,
            involving all constrained children.
            limit and offset can be used to select only a range of results,
            function can be used to select a function over the results ['[count(*)'] or
            a certain column (use %s notation to fill in id+tablename)
            ['max(%s.somefield)' or 'distinct count(%s.otherfield)']
            alternatively, col_list is a list of columns to select exclusively,
            distinct is used to indicate distinction for normal select
            and col_list-selection. checker is used to forward the manager used for typechecking"""
        assert self.mgr

        if not self.valid or not self.sql:
            # generate sql
            fromlist = []
            select   = ''
            where    = ''

            # FROM CLAUSE
            fromlist.append(' FROM %s%s' % (self.mgr.id, self.data.tablename) )
            for count, child in enumerate(self.children):
                if child.isConstrained():

                    # child sql, join attrs
                    subsql = '(%s) as child%s' % (child.getSQL(checker = checker), count)
                    pJoin = child.joinAttrParent
                    cJoin = child.joinAttrSelf
                    plist = None
                    clist = None
                    if self.mgr.listHandler.hasList(self.data.tablename, pJoin):
                        plist = self.mgr.listHandler.getList(self.data.tablename,  pJoin)
                    if child.mgr.listHandler.hasList(child.data.tablename, cJoin):
                        clist = child.mgr.listHandler.getList(child.data.tablename, cJoin)
                    if plist and clist and plist.listtype in MULLISTS and clist.listtype in MULLISTS:
                        # double mullist join on multitables (no value comparison)
                        # three joins for this child
                        # multi table
                        pmulTab = plist.dbname  # '%smulti%s' % (self.mgr.id, pJoin)
                        cmulTab = clist.dbname  # '%smulti%s' % (child.mgr.id, cJoin)
                        # joins
                        tmpsql  = ' INNER JOIN %s on %s%s.autoid = %s.tableid '
                        tmpsql += 'INNER JOIN %s on %s.%s = %s.%s '
                        tmpsql += 'INNER JOIN %s on %s.tableid = child%s.autoid'
                        # replace
                        tmpsql = tmpsql % ( pmulTab,
                                            self.mgr.id,
                                            self.data.tablename,
                                            pmulTab,
                                            cmulTab,
                                            cmulTab,
                                            cJoin,
                                            pmulTab,
                                            pJoin,
                                            subsql,
                                            cmulTab,
                                            count )

                    elif plist and plist.listtype in MULLISTS:
                        # two joins for this child
                        # multi table
                        mulTab = plist.dbname  # '%smulti%s' % (self.mgr.id, pJoin)
                        # joins
                        tmpsql  = ' INNER JOIN %s on %s%s.autoid = %s.tableid '
                        tmpsql += 'INNER JOIN %s on %s.%s = child%s.%s'
                        # replace
                        tmpsql = tmpsql % ( mulTab,
                                            self.mgr.id,
                                            self.data.tablename,
                                            mulTab,
                                            subsql,
                                            mulTab,
                                            pJoin,
                                            count,
                                            cJoin )

                    elif clist and clist.listtype in MULLISTS:
                        # two joins for this child
                        # multi table
                        mulTab = clist.dbname  # '%smulti%s' % (child.mgr.id, cJoin)
                        # joins
                        tmpsql  = ' INNER JOIN %s on %s%s.%s = %s.%s '
                        tmpsql += 'INNER JOIN %s on %s.tableid = child%s.autoid'
                        # replace
                        tmpsql = tmpsql % ( mulTab,
                                            self.mgr.id,
                                            self.data.tablename,
                                            pJoin,
                                            mulTab,
                                            cJoin,
                                            subsql,
                                            mulTab,
                                            count )

                    else:
                        # normal handling
                        tmpsql = ' INNER JOIN %s on %s%s.%s = child%s.%s'


                        tmpsql = tmpsql % ( subsql,
                                            self.mgr.id,
                                            self.data.tablename,
                                            child.joinAttrParent,
                                            count,
                                            cJoin )

                    fromlist.append( tmpsql )

            # test all lists whether they need to be joined (for ordering / constraining)
            tablelists = self.mgr.listHandler.getLists(self.data.tablename, types = [], include = False)
            for listobj in tablelists:
                xlist = listobj.listname
                if listobj.listtype in MULLISTS:
                    # constrained or ordered by multilists have to be joined (multitable)
                    if xlist in self.filterTree.getConstraints() or xlist in self.order:
                        # we have to join the multitable
                        # (outer join for NULL-searches and to
                        # not loose values when only ordering)
                        tmpsql  = ' LEFT OUTER JOIN %s '
                        tmpsql += 'on %s%s.autoid = %s.tableid'
                        fromlist.append( tmpsql % ( listobj.dbname,
                                                    self.mgr.id,
                                                    self.data.tablename,
                                                    listobj.dbname,
                                                    ) )
                # all lists that are used for ordering have to  be joined (listtable)
                if xlist in self.order:
                    if listobj.isFunctionReference():
                        msg = 'Sorting results by %s is not possible.' % self.order
                        raise ValueError(self.mgr.getErrorDialog(msg))

                    else:
                        # function lists and table-reference lists without col def should
                        # be joined as TableNode Objects to order them by value
                        # for all other lists:
                        # for the orderclause we have to join the listtables as well
                        # (for all types)

                        # if cols are not defined on a foreign table ref list, we do not need to join the table
                        if listobj.isTableReference() and not listobj.cols:
                            # ordering is done on the list id
                            pass

                        else:

                            # singlelists join with main table,
                            # multilists join with multitable (aliased)
                            if listobj.listtype in MULLISTS:
                                # join using multitable
                                tabstr = '%s.%s' % (listobj.dbname, xlist)

                            else:
                                # join directly
                                tabstr = '%s%s.%s' % ( self.mgr.id,
                                                       self.data.tablename,
                                                       xlist )
                            # get the foreign Manager
                            othermgr = listobj.getResponsibleManagerId()

                            # this works for lists as well as foreign tables
                            tmpsql = ' LEFT OUTER JOIN %s%s on %s = %s%s.autoid'
                            fromlist.append( tmpsql % ( othermgr,
                                                        listobj.foreign,
                                                        tabstr,
                                                        othermgr,
                                                        listobj.foreign
                                                        ) )

            # WHERE CLAUSE
            where = self.processWhereString(checker)

            # FROM and WHERE get cached
            self.sql = '%s%s' % (string.join(fromlist, ''), where)
            self.valid = True

        # SELECT CLAUSE (generated each time)

        # distinct selection
        # (default: True due to multi-list-joins for search on multilists)
        if distinct:
            dist = 'DISTINCT '
        else:
            dist = ''

        # this is necessary to get the order-fields into the select statement (done in any case)
        order, do_group = self.generateOrder(dist)

        # this is not the root of the tree, select the joinattr
        if self.joinAttrSelf:
            # joinAttr test
            jlist = None
            if self.mgr.listHandler.hasList(self.data.tablename, self.joinAttrSelf):
                jlist = self.mgr.listHandler.getList(self.data.tablename, self.joinAttrSelf)
            if jlist and jlist.listtype in MULLISTS:
                # joinAttr is a list, select autoid
                select = 'SELECT %s%s%s.%s' % ( dist,
                                                self.mgr.id,
                                                self.data.tablename,
                                                ZC.TCN_AUTOID )
            else:
                # joinattr is normal attr, select it
                select = 'SELECT %s%s%s.%s' % ( dist,
                                                self.mgr.id,
                                                self.data.tablename,
                                                self.joinAttrSelf )

            return select + self.sql

        # function is given, eventually replace the %s in it
        # FIXME: joined multilists spoil count functions, should use grouping here too
        elif function:
            if function.find('%s') != -1:
                function = function % ('%s%s.' % ( self.mgr.id,
                                                   self.data.tablename )
                                       )
            select = 'SELECT %s' % function

        # col_list is given, use it for selection
        elif col_list:
            sellist = []
            for column in col_list:
                if not self.data.getField(column) or \
                       self.data.getField(column)[ZC.COL_TYPE] in MULLISTS:
                    raise ValueError('Internal Column Selection Error.')
                if column == ZC.TCN_AUTOID:
                    # autoid can be appended without change. Even in case of grouping, it is the grouping column
                    attr = '%s%s.%s' % ( self.mgr.id,
                                         self.data.tablename,
                                         column )
                    sellist.append(attr)
                elif do_group:
                    # there is a grouping used, need to mask the selection cols with functions
                    # FIXME: Ignore this for now, since orderstr might be a dereferenced singlelist value column, which cannot be used in select
#                    if column in self.order:
                        # column is used for ordering, directly append the order term
                        #orderstr =  order[column]['orderstr']
                        # orderstr could be a list but
                        # there will never be a list in a selected ordered-by column since multilists cannot be selected
                        # so append without typecheck
                        #if isinstance(orderstr, ListType):
                        #    # list of orders in case of multilist table ref with cols, last one is real
                        #    sellist.append(orderstr[-1])
                        #else:
#                        sellist.append(orderstr)
#                    else:
                    # generate attribute selector using any function (min is used, no reason)
                    attr = 'min(%s%s.%s)' % (self.mgr.id,
                                             self.data.tablename,
                                             column )
                    sellist.append(attr)
                else:
                    # normal generation
                    attr = '%s%s.%s' % ( self.mgr.id,
                                         self.data.tablename,
                                         column )
                    sellist.append( attr )
            if do_group or (order and dist):
                # autoid and order - attr have to be present in select,
                # append if not the case
                if ZC.TCN_AUTOID not in col_list:
                    attr = '%s%s.%s' % ( self.mgr.id,
                                         self.data.tablename,
                                         ZC.TCN_AUTOID )
                    sellist.append( attr )

                for oneorder in order.values():
                    orderstr = oneorder['orderstr']
                    if isinstance(orderstr, ListType):
                        sellist.extend(orderstr)
                    elif orderstr not in sellist:
                        sellist.append(orderstr)

            # build select string
            select = 'SELECT %s%s' % ( dist, ', '.join(sellist) )

        # just select the autoid and the orderfields, if existing
        else:
            select = 'SELECT %s%s%s.%s' % ( dist,
                                            self.mgr.id,
                                            self.data.tablename,
                                            ZC.TCN_AUTOID )
            if self.order:
                # use the orderstr sql representations of the order attrs in select
                sellist = [select]
                for oneorder in order.values():
                    if oneorder['col'] == ZC.TCN_AUTOID:
                        continue
                    orderstr = oneorder['orderstr']
                    if isinstance(orderstr, ListType):
                        sellist.extend(orderstr)
                    else:
                        sellist.append(orderstr)
                select = ', '.join(sellist)

        if do_group:
            grpstr   = '%s%s.%s' % ( self.mgr.id,
                                     self.data.tablename,
                                     ZC.TCN_AUTOID )
            finalsql = '%s%s GROUP BY %s'
            finalsql = finalsql % ( select,
                                    self.sql,
                                    grpstr )
        else:
            finalsql = '%s%s' % ( select,
                                  self.sql )

        if not function:
            # generate the string part for order limit and offset,
            olo = self.generateOrderLimitOffset( order,
                                                 limit,
                                                 offset )
            finalsql = '%s%s' % (finalsql, olo)

        # finish
        return finalsql


    def getIDs( self,
                limit    = None,
                offset   = None,
                function = None,
                col_list = None,
                distinct = True ):
        """\brief generate an sql query and use it to generate a list of autoids
            (for databases without join-operators)"""
        # FIXME: implement!
        # find out if db supports joins
        # if not joined:
        # use getIDs of children to get their results
        # build sql for this node with the child results
        # execute and return ids
        # else:
        # use getSQL to generate query
        # execute query
        # return ids
        return


    def generateOrderLimitOffset(self, order, limit, offset):
        """\brief return an sql string with the
            ORDER BY, LIMIT and OFFSET keywords"""
        orderstring  = ''
        limitstring  = ''
        offsetstring = ''
        if order:
            orders = []
            # order is a dict, sorting of it is in self.order
            for key in self.order:
                orderobj = order[key]
                direction = orderobj['dir']
                orderstr  = orderobj['orderstr']

                # direction can be None
                dirstring = direction and (' %s' % direction) or ''
                if isinstance(orderstr, ListType):
                    orderstring = ', '.join(['%s%s' % (one, dirstring) for one in orderstr])
                else:
                    orderstring = '%s%s' % (orderstr, dirstring)
                orders.append(orderstring)
            orderstring = ' ORDER BY %s' % (', '.join(orders))

        if limit:
            limitstring  = ' LIMIT %s' % limit
        if offset:
            offsetstring = ' OFFSET %s' % offset
        return '%s%s%s' % (orderstring, limitstring, offsetstring)


    def generateOrder(self, dist):
        """\brief return a dict containing order dicts with sql strings for the
            correct sql representation
            of the order-field (lists / foreign lists / normal) """
        do_group = False
        result = {}
        for index, order in enumerate(self.order):
            orderstring = ''
            orderfield  = self.data.getField(order)
            if not orderfield:
                raise ValueError('Unknown order field: %s' % order)

            # direction is initally stored in another list with same indexes
            direction = self.orderDirection[index]

            # check order column for beeing a list (and having a function)
            function = False
            listobj  = None
            if self.mgr.listHandler.hasList(self.data.tablename, order):
                listobj = self.mgr.listHandler.getList(self.data.tablename, order)
                function = listobj.function

            # order by own attr
            if orderfield[ZC.COL_TYPE] in ALLLISTS and not function:
                # function lists have to be joined as TableNode Objects
                # to order by value
                # normal lists (even foreign) order on mgr+list.value
                # foreign table ref lists without col def order on mgr+tab.list
                # foreign table ref lists with col def order on mgr+tab.cols
                othermgr = listobj.getResponsibleManagerId()
                if not listobj.isTableReference():
                    # normal ordering on list table's value column
                    orderstring = '%s%s.value' % ( othermgr, listobj.foreign )
                elif not listobj.cols:
                    # ordering on main table or multilist table
                    if orderfield[ZC.COL_TYPE] in MULLISTS:
                        # multilist foreign table ref, but no column given
                        # order on multilisttable valueref column (named like column/order)
                        orderstring = '%s.%s' % ( listobj.dbname, order)
                    else:
                        # singlelist -> use orig manager table, not othermgr
                        orderstring = '%s%s.%s' % (self.mgr.id, self.data.tablename, order)
                else:
                    orderstring = ['%s%s.%s' % (othermgr, listobj.foreign, col) for col in listobj.cols]

            elif orderfield[ZC.COL_TYPE] in MULLISTS:
                # multilists, but complex foreign list, so we order by id
                orderstring = '%s.%s' % ( listobj.dbname, order)
            else:
                orderstring = '%s%s.%s' % ( self.mgr.id,
                                            self.data.tablename,
                                            order )
            # only for distinct-queries, we need grouping when ordering on multilists
            if dist and orderfield[ZC.COL_TYPE] in MULLISTS:
                do_group = True
            orderdict = { 'col':      order,
                          'dir':      direction,
                          'minmax':   None,
                          'orderstr': orderstring }
            result[order] = orderdict

        # done generating all order strings, now check grouping and introduce
        # min/max functions if necessary
        if do_group:

            # cycle through all again and wrap the orderstr in the fitting
            # function
            for order in result.values():
                if order['col'] == ZC.TCN_AUTOID:
                    # it is okay, autoid does not need a function, it is the
                    # grouping column
                    continue
                direction = order['dir']
                orderstring  = order['orderstr']
                minmax = (direction == 'desc') and 'max' or 'min'
                # have to use min() or max() for ordering acc. to multilists
                # -> selection handling will use grouping
                if isinstance(orderstring, ListType):
                    orderstring = ['%s(%s)' % ( minmax, oneorder ) for oneorder in orderstring]
                else:
                    orderstring = '%s(%s)' % ( minmax, orderstring )
                order['orderstr'] = orderstring
                order['minmax'] = minmax
        return result, do_group


    def processWhereString(self, checker = None):
        """\brief Build where-string"""
        where = ''
        if self.filterTree:
            newWhere = self.filterTree.getSQL( self.data.tablename,
                                               self.mgr.id,
                                               self.data,
                                               checker )
            if newWhere:
                where = ' WHERE %s' % (newWhere)

        return where
