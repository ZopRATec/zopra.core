###########################################################################
#    Copyright (C) 2004 by Ingo Keller
#    <webmaster@ingo-keller.de>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from types                  import ListType, IntType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                      import E_PARAM_TYPE
from PyHtmlGUI.kernel.hgWidget      import hgWidget
from PyHtmlGUI.kernel.hgGridLayout  import hgGridLayout
from PyHtmlGUI.widgets.hgLabel      import hgLabel,   \
                                           hgProperty
from PyHtmlGUI.widgets.hgMultiList  import hgMultiList
from PyHtmlGUI.widgets.hgPushButton import hgPushButton

#
# ZopRA Imports
#
from zopra.core                             import ZM_PM
from zopra.core.constants                   import SHOW, VALUE, NOTES, WIDGET_CONFIG, TCN_AUTOID
from zopra.core.CorePart                    import COL_TYPE
from zopra.core.elements.Buttons            import DLG_CUSTOM
from zopra.core.elements.Styles.Default     import ssiDLG_MULTILIST
from zopra.core.lists.ForeignList           import ForeignList, F_LINK
from zopra.core.widgets.hgComplexMultiList  import hgComplexMultiList
from zopra.core.widgets.hgFilteredRangeList import hgFilteredRangeList


class MultiList(ForeignList):
    """ Multilist Class - Data handling for multi-selection lists."""

    _className = 'MultiList'
    _classType = ForeignList._classType + [_className]
    # for compatibility
    listtype   = 'multilist'

    def __init__( self,
                  listname,
                  manager  = None,
                  function = None,
                  table    = None,
                  label    = '',
                  map      = None,
                  docache  = True ):
        """\brief Constructs a MultiList
        """
        ForeignList.__init__( self,
                              listname,
                              manager,
                              function,
                              label )

        # no additional checks for manager / function / table,
        # because of the dummy-usage of this list
        # to create widgets via getSpecialWidget / fillSpecialWidget

        self.enableCache = docache

        self.map   = map
        self.table = table

        # we cannot init this now, since we cannot use getManager() at this point
        # NOTE: getManager() only works if list has been retrieved via getattr() from listHandler
        #       (wrapped by listHandler[])
        self.dbname = None



    # NOTE: cannot be done as property that inits on first call
    #       since property works as decorator that binds on 'compile' time
    #       where (again) getManager() is not functional yet
    # TODO: find a better way
    def initDBName(self):
        """\brief Get database name"""

        if self.dbname:
            return self.dbname

        mgr = self.getManager()

        if self.map:
            self.dbname = '%smulti%s' \
                          % ( mgr.getId(),
                              self.map,
                              )
        else:
            self.dbname = '%smulti%s%s' \
                          % ( mgr.getId(),
                              self.table,
                              self.listname
                              )

        assert ( len(self.dbname) < 33, "database name too long (>32 chars) for %s" % self.dbname )

        return self.dbname


    def createTable(self):
        """\brief Create the database table."""

        # try to create the list
        mgr = self.getManager()
        m_product = mgr.getManager(ZM_PM)

        table_dict = { 'tableid':     { COL_TYPE: 'int'   },
                       self.listname: { COL_TYPE: 'int'   },
                       'notes':       { COL_TYPE: 'string'}
                       }

        m_product.addTable( self.dbname,
                            table_dict,
                            edit_tracking  = False )


    def deleteTable(self, omit_log = None):
        """\brief Create the database table."""

        mgr       = self.getManager()
        m_product = mgr.getManager(ZM_PM)
        log       = True

        for ident in omit_log:
            if ident in mgr.getClassType():
                log = False

        m_product.delTable( self.dbname, log )


    def createWidget( self,
                      name,
                      with_novalue = False,
                      with_null    = False,
                      parent       = None,
                      config       = None):
        """\brief Returns a list combobox."""

        # config not supported so far
        # no special options like horizontal/vertical layout, limiting of entries etc

        mlist = hgMultiList(name = name, parent = parent)

        # make sure ssi is registered globally
        mlist._styleSheet.add(ssiDLG_MULTILIST)
        # set ssi for use
        mlist.setSsiName( ssiDLG_MULTILIST.name() )

        # empty value
        if with_novalue:
            mlist.insertItem(' -- no search value -- ', '')

        # null value
        if with_null:
            mlist.insertItem(' -- no value -- ', 'NULL')

        return mlist


    def getWidget( self,
                   selected    = None,
                   with_hidden = False,
                   prefix      = '',
                   parent      = None ):
        """\brief Returns a list multiselect."""
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix

        manager = self.getForeignManager()

        mul = self.createWidget(name = pre + self.listname, parent = parent)

        if manager:
            # entry handling based on foreign/function is done by getEntries
            completelist = self.getEntries( with_hidden = with_hidden, manager = manager )

            # fill the widget
            for entry in completelist:
                if with_hidden or entry.get(SHOW) != 'no':
                    mul.insertItem(entry[VALUE], entry[TCN_AUTOID])

        else:
            miss_str = 'ListHandling Error finding manager: %s for list %s'
            raise ValueError( miss_str % (self.manager, self.listname))


        # handles the selection of list entries
        if selected is not None:
            if not isinstance(selected, ListType):
                selected = [selected]
            mul.setSelectedValueList(selected)

        return mul


    def getMLRef(self, tableid = None, listid = None):
        # Returns the notes-entry of the multilist entry specified by tableid / listid."""
        mgr = self.getManager()

        if tableid:
            id1     = tableid
            id1name = 'tableid'
            id2name = self.listname
        elif listid:
            id1     = listid
            id1name = self.listname
            id2name = 'tableid'
        else:
            return []
        query = 'Select %s from %s where %s = %s' % ( id2name,
                                                      self.dbname,
                                                      id1name,
                                                      id1
                                                      )

        result = mgr.getHierarchyUpManager(ZM_PM).executeDBQuery(query)
        return [entry[0] for entry in result]


    def updateMLNotes(self, tableid, listid, notes):
        # change the notes of one entry
        mgr = self.getManager()

        if not tableid or not listid:
            return False

        # escape notes
        notes = notes.replace( "\'", "\\\'" ).replace( "\\\\'", "\\\'")
        query = "Update %s set notes = '%s' where tableid = %s and %s = %s"\
                 % ( self.dbname,
                     notes,
                     tableid,
                     self.listname,
                     listid
                    )

        mgr.getManager(ZM_PM).executeDBQuery(query)
        return True


    def getMLNotes(self, tableid, listid):
        """\brief Returns the notes-entry of the multilist
                    entry specified by tableid / listid."""
        mgr = self.getManager()

        if not tableid or not listid:
            return ''
        query = 'Select notes from %s where tableid = %s and %s = %s'\
                 % ( self.dbname,
                     tableid,
                     self.listname,
                     listid
                    )

        result = mgr.getManager(ZM_PM).executeDBQuery(query)
        if result:
            return result[0][0]
        else:
            return ''


    def delMLRef(self, tableid = None, listid = None):
        """\brief deletes all rows in table 'multi'+list_name
                    with matching tableid."""
        mgr = self.getManager()

        # secure the selection strings
        # TODO: securing strings

        if tableid and listid:
            query = 'Delete from %s where tableid = %s and %s = %s'
            query = query % ( self.dbname, int(tableid), self.listname, int(listid))
        elif tableid:
            query = 'Delete from %s where tableid = %s'
            query = query % ( self.dbname, int(tableid) )
        elif listid:
            query = 'Delete from %s where %s = %s'
            query = query % ( self.dbname, self.listname, int(listid) )
        else:
            return

        mgr.getManager(ZM_PM).executeDBQuery(query)


    def addMLRef(self, tableid, value, notes = None):
        """\brief inserts a row with given tableid and value
                    in table 'multi'+list_name"""
        assert value, E_PARAM_TYPE % (VALUE, 'not None value for %s' % self.listname, value )
        mgr = self.getManager()

        try:
            int(value)
        except ValueError:
            return

        if not notes:
            notes = ''
        query = 'Insert into %s (tableid, %s, notes) values (%s,%s,%s)' % (
                                             self.dbname,
                                             self.listname,
                                             tableid,
                                             mgr.forwardCheckType( value,
                                                                   'int',
                                                                   False,
                                                                   'Value' ),
                                             mgr.forwardCheckType( notes,
                                                                   'string',
                                                                   False,
                                                                   'Notes' )
                 )
        return mgr.getManager(ZM_PM).executeDBQuery(query)


    def handleSelectionAdd(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Add-Request for the two-list-Multilist-Handling.
        """
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix
        new = REQUEST.get('new' + pre + self.listname, [])
        if new:
            if not isinstance(new, ListType):
                new = [new]
            selected_list = descr_dict.get(self.listname, [])
            for autoid in new:
                autoid = int(autoid)
                # check 0 (any)
                if autoid == 0:
                    # put all values in
                    selected_list = self.getAutoidsByFreeText('%')
                    # stop here
                    break
                # normal value, put it in, if not present
                if autoid not in selected_list:
                    selected_list.append(autoid)
            descr_dict[self.listname] = selected_list
        # we don't need a return value, because descr_dict is an object


    def handleSelectionRemove(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Delete-Request for the
                    two-list-Multilist-Handling.
        """
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix
        delete = REQUEST.get('del' + pre + self.listname, [])
        if delete:
            if not isinstance(delete, ListType):
                delete = [delete]
            selected_list = descr_dict.get(self.listname, [])
            for autoid in delete:
                if int(autoid) in selected_list:
                    selected_list.remove(int(autoid))
                    # delete notes
                    if (self.listname + 'notes' + str(autoid)) in descr_dict:
                        del descr_dict[self.listname + 'notes' + str(autoid)]
        # we don't need a return value, because descr_dict is an object


    def getComplexWidget( self,
                          with_hidden = False,
                          descr_dict  = None,
                          search      = False,
                          prefix      = None,
                          parent      = None ):
        """\brief Builds a table with one complete multilist and one with the
                    selected values plus buttons.
        """

        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix

        if not descr_dict:
            descr_dict = {}

        # special list options
        # FIXME: correct usage, always use
        confname = WIDGET_CONFIG + self.listname
        if confname in descr_dict:
            config = descr_dict[confname]
            # pattern, direction, type, short, tolerance
            if 'maxlen' not in config or \
               not isinstance( config['maxlen'], IntType ):
                config['maxlen'] = 0
            if 'tolerance' not in config or \
               not isinstance( config['tolerance'], IntType ):
                config['tolerance'] = 0
            if 'type' not in config:
                config['type'] = 'filtered'
            if 'direction' not in config:
                config['direction'] = 'vertical'
            if 'pattern' not in config:
                config['pattern'] = ''
            if 'offset' not in config:
                config['offset'] = 0

        else:
            config = {'type': 'simple'}
            descr_dict[confname] = config

        # the maxshown and labelsearch properties do only steer the
        # behaviour for foreign table lists (for now due to sorting issues)
        # custom stuff for filtering and limit/offset is passed in via config
        # config = { 'type'      : 'simple'|'filtered',
        #            'maxlen'    : <int>
        #            'tolerance' : <int>
        #            'direction' : 'horizontal'|'vertical'
        #            'pattern'   : <string-pattern>
        #            'offset'    : <int>
        #           }

        manager = self.getForeignManager()

        # check foreign lists
        if not manager:
            return hgLabel('%s not found' % self.manager, parent = parent)

        # check self.notes
        if search or not self.notes:
            notes = None
            notesLabel = None
        else:
            if self.notes is True:
                notes = True
                notesLabel = None
            else:
                # get the List for the notes from manager, get its entries, build dummy widget
                # TODO: this restricts notes-lists to basic lists (which is okay for now)
                local = self.getManager()
                ind = self.notes.find('.')
                if ind != -1:
                    # notes list resides in other manager!
                    notesmgr = self.notes[:ind]
                    notes    = self.notes[ind + 1:]
                    foreign = local.getHierarchyUpManager(notesmgr)
                    # if that does not work, try down
                    # CAUTION: down could be multiple managers of same type, first found gets returned
                    # FIXME: should build in zopratype differentiation somehow
                    if not foreign:
                        foreign = local.getHierarchyDownManager(notesmgr)
                else:
                    foreign = local
                    notes = self.notes

                lobj = foreign.listHandler[notes]
                n_entries = lobj.getEntries()
                n_list = [(entry[TCN_AUTOID], entry[VALUE]) for entry in n_entries]
                dummy = ForeignList('dummy')
                # overwrite notes (listname) with widget itself
                notes = dummy.getSpecialWidget( entry_list = n_list, with_null = True)
                notesLabel = lobj.getLabel()

        # differentiate between list types, foreign table list uses hgFilteredRangeList instead hgComplexMultiList
        # additionally use the custom config to determine which widget to use
        if self.foreign in manager.listHandler or self.function:

            widget = self.createStandardMultiWidget(parent, pre, notes, notesLabel, search, descr_dict, with_hidden)


        elif self.foreign in manager.tableHandler:
            # normally same handling as for self.function
            # exception: labelsearch set (using filter widget) or maxshown set (using range widget)
            # or both set (using range widget with filter enabled)
            # maxshown is only used when number of entries exceeds maxshown
            # getListSelectionConstraints manager function is not useable together with maxshown or labelsearch (for now)
            # FIXME: make getListSelectionConstraints transparent (inject it's constraints into constraints created by searchLabelStrings -> needs self.listname param)
            numEntries = self.getValueCount()
            maxshown = self.maxshown or 0
            # tolerance set somewhere?
            tolerance = 10
            if maxshown and maxshown + tolerance < numEntries or self.labelsearch:
                # use a range widget
                # tolerance, maxshown, config.startnumber or 0
                startnumber = config.get('offset', 0)
                pattern = config.get('pattern', '')
                # startnumber was corrected before if button pressed in button handling function
                if not self.labelsearch:
                    # labelsearch is not defined, pattern must be None
                    pattern = None

                # correct startnumber
                if startnumber < 0:
                    startnumber = 0

                # only request some entries determined by maxshown, startnumber and pattern
                partlist, num = manager.searchLabelStrings(self.foreign, pattern, startnumber, maxshown or -1, tolerance)

                # end of list is reached
                if startnumber > num:

                    # correct number one step back, re-request the partlist
                    startnumber -= maxshown

                    # commented because new pattern now leads to offset = 0
                    # a pattern delivers less then maxshown + tolerance entries -> start = 0
                    # if startnumber <= tolerance:
                    #     startnumber = 0

                    # check to not end up negative
                    if startnumber < 0:
                        startnumber = 0
                    partlist, num = manager.searchLabelStrings(self.foreign, pattern, startnumber, maxshown, tolerance)

                widget = hgFilteredRangeList(self.listname,
                                             parent,
                                             pre,
                                             notes,
                                             notesLabel,
                                             pattern = pattern,
                                             single = False,
                                             totalcount = num,
                                             doFilter = self.labelsearch,
                                             startitem = startnumber,
                                             tolerance = tolerance,
                                             showitems = maxshown,
                                             doProps = True,
                                             doSearch = search,
                                             foreignTable = self.foreign,
                                             foreignMgr   = self.manager
                                             )

                # AND-Concat for search
                if search and descr_dict.get(self.listname + '_AND'):
                    widget.setAndConcat(True)

                # fill widget
                for autoid in partlist:
                    label = manager.getLabelString(self.foreign, autoid)
                    widget.insertItem(label, autoid)

                # set Selected Values (and corresponding labels)
                selected = descr_dict.get(self.listname)
                if selected is not None:
                    if not isinstance(selected, ListType):
                        selected = [selected]

                if selected:
                    # set notes first
                    if self.notes:
                        for entry in selected:
                            key = self.listname + NOTES + str(entry)
                            widget.initNote(entry, descr_dict.get(key, ''))
                    # set selection
                    selvals = [manager.getLabelString(self.foreign, onesel) for onesel in selected]
                    widget.setSelectedValueList(selected, selvals)

                widget.finalizeLayout()
                widget.setMaxLength(22)
            else:
                # use normal way
                widget = self.createStandardMultiWidget(parent, pre, notes, notesLabel, search, descr_dict, with_hidden)
        else:
            raise ValueError('Couldn\'t find foreign list.')

        return widget


    def createStandardMultiWidget(self, parent, pre, notes, notesLabel, search, descr_dict, with_hidden):
        """\brief Standard widget creation, filling and selection put extra"""
        # standard handling using hgComplexMultiList
        widget = hgComplexMultiList( self.listname,
                                     parent,
                                     pre,
                                     notes,
                                     notesLabel,
                                     True,
                                     search )

        # any for search
        if search:
            # any value
            widget.insertItem('-any value-', 0)
            # AND concat
            if descr_dict.get(self.listname + '_AND'):
                widget.setAndConcat(True)

        # set Values
        entry_list = self.getEntries()
        for entry in entry_list:
            if with_hidden or entry.get(SHOW) != 'no':
                widget.insertItem(entry[VALUE], entry[TCN_AUTOID])

        # set Selected Values
        selected = descr_dict.get(self.listname)
        if selected is not None:
            if not isinstance(selected, ListType):
                selected = [selected]
            widget.setSelectedValueList(selected)

        # set Notes
        if self.notes and selected:
            for entry in selected:
                key = self.listname + NOTES + str(entry)
                if descr_dict.get(key):
                    widget.initNote(entry, descr_dict[key])
            widget.refreshNotes()

        return widget


    def getShowHtml( self,
                     descr_dict,
                     useProperties = False,
                     parent        = None,
                     prefix = None ):
        """\brief Builds a html-formatted string of value - notes
                    pairs for multilists."""
        if prefix:
            pre = DLG_CUSTOM + prefix
        else:
            pre = ''
        ids = descr_dict.get(self.listname, [])
        if not ids:
            return hgLabel('', parent = parent)

        manager = self.getForeignManager()

        # check foreign lists
        if not manager:
            return hgLabel('%s not found' % self.manager, parent = parent)

        box = hgWidget(parent = parent, name = self.listname)
        lay = hgGridLayout(box, 1, 1, 0, 1)

        # functions with '(' on generic managers use getLink
        generic_fun = False
        user_fun    = False


        if self.function:
            funcstr = self.function + F_LINK
            if hasattr(manager, funcstr):
                user_fun = getattr(manager, funcstr)

        else:
            # we have a table and a autoid ?
            generic_fun = self.foreign in manager.tableHandler

        row = 0
        for item in ids:
            itemvalue = self.getValueByAutoid(item)
            if itemvalue:
                if generic_fun:
                    itemstr = manager.getLink(self.foreign, item, None, box)
                elif user_fun:
                    itemstr = user_fun(item, box)
                else:
                    itemstr = hgLabel(itemvalue, parent = box, name = self.listname + str(item))
                lay.addWidget(itemstr, row, 0)

                if useProperties:
                    prop = hgProperty(pre + self.listname, item, parent = box)
                    lay.addWidget(prop, row, 1)

                key = self.listname + NOTES + str(item)

                if descr_dict.get(key):
                    autoid = descr_dict.get(key)
                    value = ''

                    if self.notes is True:
                        value = autoid
                    elif self.notes:
                        # notes widget
                        local = self.getManager()
                        ind = self.notes.find('.')
                        if ind != -1:
                            # notes list resides in other manager!
                            notesmgr = self.notes[:ind]
                            notes    = self.notes[ind + 1:]
                            foreign = local.getHierarchyUpManager(notesmgr)
                            # if that does not work, try down
                            # CAUTION: down could be multiple managers of same type, first found gets returned
                            # FIXME: should build in zopratype differentiation somehow
                            if not foreign:
                                foreign = local.getHierarchyDownManager(notesmgr)
                        else:
                            foreign = local
                            notes = self.notes

                        lobj = foreign.listHandler[notes]
                        value = lobj.getValueByAutoid(autoid)
                    # else we have no notes -> no value

                    if value:
                        label = '(%s)' % (value)
                        widg  = hgLabel(label, parent = box)
                        lay.addWidget(widg, row, 2)
                        if useProperties:
                            prop = hgProperty(pre + key, value, parent = box)
                            lay.addWidget(prop, row, 3)

                row += 1

        return box

    # DEPRECATED special function to create multiwidgets without a real list
    def getSpecialWidget( self,
                          name,
                          columns  = None,
                          expr     = None,
                          m_list   = None,
                          selected = None,
                          parent   = None ):
        """\brief generates Multilist for columns of a table (named <name>), if
                  expr is given, the values are put into expr, if list is
                  given, the list-values are used instead of database-values.
        """
        reslist = []
        if m_list is not None:
            reslist = m_list

        else:
            mgr = self.getManager()
            if not isinstance(columns, ListType):
                columns = [columns]

            # just testing
            descr_dict = mgr.tableHandler[name]
            if not descr_dict:
                raise ValueError('Unknown Table %s' % name)

            for column in columns:
                col_dict = descr_dict.get(column)
                if not col_dict:
                    raise ValueError(
                            'Unknown Column %s in table %s' % (column, name) )
                # get value list

            query = 'Select autoid, %s from %s' % ( ','.join(columns),
                                                    mgr.getId() + name )
            reslist = mgr.getManager(ZM_PM).executeDBQuery(query)

        mlist = hgMultiList(name = name, parent = parent)

        self.fillSpecialWidget(mlist, reslist, expr)

        # handles the selection of a list entry
        if selected:
            mlist.setSelectedValueList(selected)

        return mlist


    # overwritten to allow creation of multilisttable
    def viewTabFunctionality(self, REQUEST):
        """\brief List overview tab."""
        message = ''
        # check request for create_multilist_table
        if REQUEST.get('create_multilist_table'):
            # create the multilisttable
            self.createTable()

            message = 'Created Multilisttable in database.'

        dlg = ForeignList.viewTabFunctionality(self, REQUEST)

        if message:
            # add message
            dlg.add(hgLabel(message, parent = dlg))

        # check for multilisttable
        try:
            # try to fetch a value from it
            self.getMLRef(1)
        except:
            # error -> dbmultitable missing?
            dlg.add(hgLabel('<font color="red">Multitable not found in DB!</font>', parent = dlg))
            # add create button
            dlg.add(hgPushButton('Create Multitable', 'create_multilist_table', parent = dlg))
        return dlg
