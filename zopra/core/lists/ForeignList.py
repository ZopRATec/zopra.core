############################################################################
#    Copyright (C) 2004 by Ingo Keller                                     #
#    <webmaster@ingo-keller.de>                                            #
#                                                                          #
# Copyright: See COPYING file that comes with this distribution            #
#                                                                          #
############################################################################
"""\brief Basic List Handling for Dropdownlists, List Entry Management."""

from types                                  import StringType, \
                                                   ListType, \
                                                   UnicodeType, \
                                                   IntType

from PyHtmlGUI                              import E_PARAM_TYPE
from PyHtmlGUI.kernel.hgTable               import hgTable
from PyHtmlGUI.widgets.hgComboBox           import hgComboBox
from PyHtmlGUI.widgets.hgLabel              import hgLabel, hgProperty

#
# ZopRA Imports
#
from zopra.core                             import HTML, ZM_PM
from zopra.core.constants                   import VALUE, SHOW, WIDGET_CONFIG, TCN_AUTOID
from zopra.core.dialogs                     import getStdDialog
from zopra.core.elements.Buttons            import DLG_CUSTOM
from zopra.core.lists.GenericList           import GenericList
from zopra.core.widgets                     import dlgLabel
from zopra.core.widgets.hgFilteredRangeList import hgFilteredRangeList
from zopra.core.widgets.hgFilteredComboBox  import hgFilteredComboBox, \
                                                   FILTER_EDIT,        \
                                                   FCB_DEFAULT_FILTER_TEXT
from zopra.core.widgets.hgShortenedComboBox import hgShortenedComboBox

# function prefixes for foreign funtions
F_VALUE  = 'Value'
F_SELECT = 'Select'
F_LINK   = 'Link'

SUFFIXES = [F_VALUE, F_SELECT, F_LINK]


class ForeignList(GenericList):
    """ ForeignList

        NOTE: the manager of foreign lists is specified solely by it's class
              name how to handle multiple instances of a certain manager within
              an instance when referencing of one or the other instance is
              required even how to make sure the correct manager is chosen if
              only one foreign list is referenced
    """
    _className = 'ForeignList'
    _classType = GenericList._classType + [_className]

    __notes       = None
    __noteslabel  = None
    __labelsearch = False
    __maxshown    = None
    __invisible   = True

    # for compatibility
    listtype   = 'singlelist'

    manage_options = (  {'label':'Overview',    'action':'viewTab' },
                     ) + GenericList.manage_options


    def __init__( self,
                  listname,
                  manager = None,
                  function = None,
                  label    = None):
        """Constructs a ForeignList."""
        GenericList.__init__( self, listname, label )

        # no additional checks for manager / function, because of the dummy-usage of this list
        # to create widgets via getSpecialWidget / fillSpecialWidget
        self.manager  = manager

        self.__notes       = None
        self.__noteslabel  = None
        self.__labelsearch = False
        self.__maxshown    = None
        self.__invisible   = True

        if not function:
            function = ''
        idx = function.find( '(' )
        if idx == -1:
            # points to a handwritten function
            self.function = function
            self.foreign  = None
            self.cols     = []
        else:
            # points to a table or a list in another manager
            self.function = None
            self.foreign  = function[:idx]

            collist = function[idx + 1: -1]
            cols = collist.split(',')
            if cols == ['']:
                cols = []

            self.cols   = []
            for col in cols:
                self.cols.append(col.strip())


    # no database tables for foreign single lists
    def createTable(self):
        """\brief Create the database table."""
        pass


    def deleteTable(self, omit_log = None):
        """\brief Create the database table."""
        pass


    # notes property methods
    def setNotes(self, notes):
        """\brief Set notes property"""

        if notes:
            self.__notes = notes
        else:
            self.__notes = None


    def getNotes(self):
        """\brief Get notes property"""

        return self.__notes

    notes = property(getNotes, setNotes)

    # noteslabel property methods
    def setNoteslabel(self, noteslabel):
        """\brief Set noteslabel property"""

        if noteslabel:
            self.__noteslabel = noteslabel
        else:
            self.__noteslabel = None


    def getNoteslabel(self):
        """\brief Get noteslabel property"""

        return self.__noteslabel

    noteslabel = property(getNoteslabel, setNoteslabel)


    # labelsearch property methods
    def setLabelSearch(self, labelsearch):
        """\brief Set labelsearch property
                If set, getAutoidByValue will use searchLabelStrings from manager
                which is supposed to perform a db search based on Value string.
                Also enables filtering for the list. labelsearch is normally used in conjunction
                with maxshown to have a reduced size list with searchable values.
                This should speed up the data retrieval considerably compared
                to the standard method of retrieving all entries from db,
                creating their label string and comparing it to the pattern.
                Note: searchLabelStrings defaults to autoid search and must be overwritten in the
                        manager, if different behaviour is desired.
                Note: Only a valid option if self.cols is not set since this changes the displayed
                        value string and composed strings cannot be searched right now. -> needs to be solved
        """

        if labelsearch:
            self.__labelsearch = True
        else:
            self.__labelsearch = False


    def getLabelSearch(self):
        """\brief Get labelsearch property"""

        return self.__labelsearch

    labelsearch = property(getLabelSearch, setLabelSearch)


    def setMaxShown(self, maxshown):
        """\brief Set maxshown property
                If set, list size is reduced to maxshown to increase speed for display.
                The target widget only gets loaded with the needed entries and offers functions
                to determine limit and offset. Used in getWidget and MultiList.getComplexWidget
                to select the target widget (not set -> hgComboBox / hgComplexMultiList or
                set and len(entries) > maxshown -> hgFilteredRangeList)
        """

        if maxshown:
            self.__maxshown = int(maxshown)
        else:
            self.__maxshown = None


    def getMaxShown(self):
        """\brief Get maxshown property"""

        return self.__maxshown

    maxshown = property(getMaxShown, setMaxShown)

    # invisible property methods
    def setInvisible(self, invisible):
        """\brief Set invisible property"""
        if invisible:
            self.__invisible = True
        else:
            self.__invisible = False


    def getInvisible(self):
        """\brief Get invisible property"""

        return self.__invisible

    invisible = property(getInvisible, setInvisible)


    def copy(self):
        """\brief Create a copy of the list."""
        cop = self.__class__( self.listname,
                              self.manager,
                              self.function,
                              self.label )

        cop.notes       = self.notes
        cop.labelsearch = self.labelsearch
        cop.maxshown    = self.maxshown

        return cop


    def getResponsibleManagerId(self):
        """\brief Returns the foreign manager id (or manager id, if no foreign list)."""

        return self.getForeignManager().id


    def getForeignManager(self):
        """\brief Returns the owning manager."""
        local = self.getManager()

        if local.getClassName() == self.manager:
            foreign = local
        else:
            foreign = local.getHierarchyUpManager(self.manager)
            # if that does not work, try down
            # CAUTION: down could be multiple managers of same type, first found gets returned
            # FIXME: should build in zopratype differentiation somehow
            if not foreign:
                foreign = local.getHierarchyDownManager(self.manager)

        # removed Error raising. No manager -> other functions have to check and return empty labels etc.
        # if not foreign:
        #
        #    err = 'Manager %s not found searching by %s' % (self.manager, local.id)
        #    raise ValueError( err )

        return foreign


    def getLabel(self):
        """\brief Returns the label of the list attribute."""
        if self.label:
            label = self.label
            if self.notes and self.noteslabel:
                label = '%s (%s)' % (label, self.noteslabel)
            return label
        else:
            manager = self.getForeignManager()

            if manager:
                if self.foreign in manager.tableHandler:
                    return manager.tableHandler[self.foreign].getLabel()
                elif self.foreign in manager.listHandler:
                    return manager.listHandler[self.foreign].getLabel()

        return ''


    def isListReference(self):
        """True if the List refers to a list of a foreign manager"""
        return self.foreign in self.getForeignManager().listHandler


    def isTableReference(self):
        """True if the List refers to a table of a foreign manager"""
        return self.foreign in self.getForeignManager().tableHandler


    def isFunctionReference(self):
        """True if the List refers to a set of special functions in a foreign manager"""
        return not not self.function


    # NOTE: is it useful to allow add/del of values in foreign lists?
    def addValue( self, value, notes = '', rank  = '', show  = 'yes', **kwargs ):
        """\brief Adds a value to a list lookup table.

        The function adds a new value to a lookup list. It also checks if
        the value is already in the list. If so it won't add the new value but
        also won't give a error message (yet).

        \param list_name The argument \a list_name specifies the list where the
        entry should be inserted.

        \param value  The argument \a value is a string that should be
                      inserted.

        \param notes  The argument \a notes contains a comment if there is one.
        \todo   Handling for comments.

        \param rank  The \a rank should be a number and will be used for
        ordering the entries in the combobox where it will be shown.
        \todo  Handling for ordering lookup list ranking.

        \param show  If \a show is \c 'yes' then the entry will be shown in the
        combobox of the list. If it is no then it won't.

        \throw RuntimeError if list not found.
        """
        if self.function:
            raise ValueError('Non-simple foreign list doesnt support addValue.')

        manager = self.getForeignManager()

        if not manager:
            return

        if self.foreign in manager.tableHandler:
            raise ValueError('Non-simple foreign list doesnt support addValue.')
        elif self.foreign in manager.listHandler:
            _list = manager.listHandler[self.foreign]
            return _list.addValue(value, notes, rank, show, **kwargs)
        else:
            raise ValueError('Couldn\'t find foreign list.')


    def delValue(self, autoid):
        """\brief Deletes a value from a list lookup table."""

        if self.function:
            message = 'Unable to delete from non-simple foreign list %s.'
            raise ValueError( message % self.listname)

        manager = self.getForeignManager()

        if not manager:
            return

        if self.foreign in manager.tableHandler:
            message = 'Unable to delete from non-simple foreign list %s.'
            raise ValueError( message % self.listname)
        elif self.foreign in manager.listHandler:
            manager.listHandler[self.foreign].delValue(autoid)
        else:
            raise ValueError('Couldn\'t find foreign list.')


    def getEntry(self, autoid):
        """\brief Fetches a value from an list lookup table. Local function."""

        manager = self.getForeignManager()

        if not manager:
            return

        autoid = int(autoid)

        # if plain function implemented in manager then return the call result
        if self.function:
            return getattr(manager, self.function + F_VALUE)(autoid)

        # handle foreign table or list
        if self.foreign in manager.tableHandler:
            return manager.tableHandler[self.foreign].getEntry(autoid)

        if self.foreign in manager.listHandler:
            return manager.listHandler[self.foreign].getEntry(autoid)

        raise ValueError('Couldn\'t find foreign list.')


    def getEntries(self, value = None, with_hidden = False, manager = None, lang=None):
        """\brief Returns all list entries of one list."""
        completelist = []

        if not manager:
            manager = self.getForeignManager()

        if manager:

            # plain function, implemented in manager
            if self.function:
                funcstr = self.function + F_SELECT

                # test
                if not hasattr( manager, funcstr):
                    errstr = '%s missing function: %s' % (manager.id, funcstr)
                    raise ValueError(manager.getErrorDialog(errstr))

                selfunc = getattr( manager, funcstr )
                reslist = selfunc(lang)

                for result in reslist:
                    if value is None or \
                       value in result[1]:
                        newentry = { TCN_AUTOID: result[0],
                                     VALUE:      result[1],
                                     SHOW:       'yes' }
                        completelist.append(newentry)
            else:
                # table-standard-function used
                if self.foreign in manager.tableHandler:
                    tobj = manager.tableHandler[self.foreign]
                    cons = self.getManager().getListSelectionConstraints(self.listname)
                    tentries = tobj.getEntryList(constraints = cons)
                    completelist = []
                    for entry in tentries:
                        val = ''
                        autoid = entry['autoid']
                        if not self.cols:
                            # empty, use getLabelString
                            if manager.doesTranslations(self.foreign):
                                # getLabelString does the translation (and switches to translated entry by itself)
                                val = manager.getLabelString(self.foreign, None, entry, lang)
                            else:
                                val = manager.getLabelString(self.foreign, None, entry)
                        else:
                            vals = []
                            # switch to translated entry if necessary
                            if manager.doesTranslations(self.foreign):
                                entry = manager.getEntry(self.foreign, autoid, lang)
                            for col in self.cols:
                                col = col.strip()
                                if entry.get(col):
                                    vals.append(unicode(entry.get(col)))
                            val = ' '.join(vals)

                        if value is None or \
                           value in val:
                            newentry = { TCN_AUTOID: autoid,
                                         VALUE:      val,
                                         SHOW:       'yes' }
                            completelist.append( newentry )
                # get data from list
                elif self.foreign in manager.listHandler:
                    lobj = manager.listHandler[self.foreign]
                    # call getEntries of the ZMOMLIst object that is referenced (lang is not necessary, the entries are multilingual anyway)
                    completelist = lobj.getEntries(value, with_hidden)
                else:
                    raise ValueError('Couldn\'t find foreign list %s:%s for %s' % (manager._className, self.foreign, self.listname))
        else:
            # manager not found
            return []

        return completelist


    def updateEntry( self,
                     descr_dict,
                     entry_id ):
        """\brief changes list values in the database"""

        if self.function:
            raise ValueError('Non-simple foreign list doesnt support updateEntry.')

        manager = self.getForeignManager()

        if manager:
            if self.foreign in manager.tableHandler:
                raise ValueError('Non-simple foreign list doesnt support updateEntry.')
            elif self.foreign in manager.listHandler:
                _list = manager.listHandler[self.foreign]
                return _list.updateEntry(descr_dict, entry_id)
            else:
                raise ValueError('Couldn\'t find foreign list.')


    def getAutoidByValue(self, value, rank = None):
        """\brief Returns the autoid from an specified list entry."""
        assert ( isinstance(value, StringType)   or
                 isinstance(value, ListType)     or
                 isinstance(value, UnicodeType)  or
                 value is None )

        # NOTE: do not handle lists recursivly:
        #      1) getting the manager is expensive
        #      2) loading all entries of a list from the db for each searched value is wasteful
        if isinstance( value, ListType):
            is_list = True
            values = value
        else:
            is_list = False
            values = [ value ]

        retlist = []

        manager = self.getForeignManager()

        # foreign manager is not available
        if not manager:
            retlist = len(values) * [None]
        # if it is a real list forward to it
        elif self.foreign in manager.listHandler:
            lobj = manager.listHandler[self.foreign]

            return lobj.getAutoidByValue(value, rank)

        # retrieve data via function
        elif self.function:
            # function or table
            entrylist = self.getEntries( with_hidden = True, manager = manager )

            # NOTE: keep in mind to preserve the order of searched values,
            #       as well as multiple occurences of values

            # build lookup table
            # NOTE: a list should consist of distinct values
            #       so if multiple occurences of the same value occur the autoid which is actually mapped is undefined
            #       in this case the last of the same values in the entrylist wins
            val2autoid = {}

            for entry in entrylist:
                val2autoid[ entry[VALUE] ] = entry[TCN_AUTOID]

            # get the autoid for each value
            for val in values:
                retlist.append( val2autoid.get(val, None) )

        # retrieve data via table
        elif self.foreign in manager.tableHandler:

            if self.labelsearch:
                # Note: expensive if values contains a high number of entries
                for val in values:
                    (ids, count) = manager.searchLabelStrings(self.foreign, val)
                    # count should be 0 or 1
                    # print str((ids, count))
                    if count:
                        retlist.append(ids[0])
                    else:
                        retlist.append(None)
            else:
                # Note: this is horribly expensive for big tables, use label search if possible
                entrylist = self.getEntries( with_hidden = True, manager = manager )

                # NOTE: look at note of function section above
                val2autoid = {}

                for entry in entrylist:
                    val2autoid[ entry[VALUE] ] = entry[TCN_AUTOID]

                # get the autoid for each value
                for val in values:
                    retlist.append( val2autoid.get(val, None) )

        # manager is available but list cannot be found - error
        else:
            raise ValueError('Couldn\'t find foreign list.')

        if is_list:
            return retlist
        else:
            return retlist[0]


    # freetextsearch
    def getAutoidsByFreeText(self, value):
        """\brief Returns the autoid from any fitting list entry."""
        reslist = []
        upval   = value.upper()

        manager = self.getForeignManager()

        if manager:
            if self.function or \
               self.foreign in manager.tableHandler:
                # function or table
                resultlist = self.getEntries(with_hidden = True, manager = manager)
                for entry in resultlist:
                    if entry[1].upper().find(upval) != -1:
                        reslist.append(entry[0])

            else:
                # foreign list
                if self.foreign in manager.listHandler:
                    lobj = manager.listHandler[self.foreign]
                    reslist = lobj.getAutoidsByFreeText(value)
                else:
                    raise ValueError('Couldn\'t find foreign list.')

        return reslist


    def crossLookupList(self, entry1, entry2, crossString):
        """\brief gets the values for the entries calls crossValue and
                  inserts the result into the list.

        Returns the new or existing id.
        """
        if self.function:
            raise ValueError('Cannot cross foreign function-based lists.')

        manager = self.getForeignManager()

        if manager:
            # handle foreign table or list
            if self.foreign in manager.tableHandler:
                raise ValueError('Cannot cross foreign table-based lists.')
            elif self.foreign in manager.listHandler:
                return manager.listHandler[self.foreign].\
                           crossLookupList( entry1,
                                            entry2,
                                            crossString )
            else:
                raise ValueError('Couldn\'t find foreign list.')


    def handleSelectionAdd(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Set-Request for the filterRangeList
        """
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix
        new = REQUEST.get('new' + pre + self.listname, None)
        if new:
            if new != 'NULL':
                new = int(new)
            descr_dict[self.listname] = new
        # we don't need a return value, because descr_dict is an object


    def handleSelectionRemove(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Delete-Request for the
                    two-list-Multilist-Handling.
        """
        raise ValueError('Shouldnt end up calling handleSelectionRemove on a singlelist')


    def handleFilterApply(self, REQUEST, descr_dict, prefix = None):
        """\brief Handles the Apply-Request for the filter-able list widgets
        """
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix
        # the pattern in REQUEST overwrites the one that might by in the config
        filtertext = REQUEST.get(FILTER_EDIT + pre + self.listname)
        # button was pressed -> something should be in the request, but make sure
        if not filtertext:
            filtertext = ''
        if filtertext == FCB_DEFAULT_FILTER_TEXT:
            filtertext = ''
        if not isinstance(filtertext, StringType):
            filtertext = str(filtertext)
        # prepare the config
        confname = WIDGET_CONFIG + self.listname
        if confname not in descr_dict:
            descr_dict[confname] = {}
        # set new filtertext into config, set offset back to 0
        descr_dict[confname]['pattern'] = filtertext
        descr_dict[confname]['offset']  = 0
        # we don't need a return value, because descr_dict is an object


    def handleRangeSwitch(self, REQUEST, descr_dict, prefix, next = True):
        """\brief Handles the prev/next switch for range lists with filter option"""
        if not prefix:
            pre = ''
        else:
            pre = DLG_CUSTOM + prefix

        # allow actualisation of filtertext
        # -> would need to check store_ + FILTER_EDIT against FILTER_EDIT
        # self.handleFilterApply(REQUEST, descr_dict, prefix)

        confname = WIDGET_CONFIG + self.listname
        config = descr_dict.get(confname, {})
        # get actual number for this list from config (put there by getTableEntryFromRequest)
        actualnumber = config.get('offset')
        if actualnumber or actualnumber == 0:

            # test the number of shown items
            maxshown = config.get('maxlen', self.maxshown)
            if maxshown:
                # the list is limited
                # boundaries are tested later
                if next:
                    actualnumber += maxshown
                else:
                    actualnumber -= maxshown

            # set (might be new dict)
            descr_dict[confname] = config

            descr_dict[confname]['offset'] = actualnumber


    def getComplexWidget( self,
                          with_hidden = False,
                          descr_dict  = None,
                          search      = False,
                          prefix      = None,
                          parent      = None ):
        """\brief For compatibility."""
        if not descr_dict:
            descr_dict = {}

        # check widget configuration
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
            if self.labelsearch:
                config = { 'type': 'filtered',
                           'direction': 'vertical',
                           'pattern': '',
                           'maxlen': None,
                           'tolerance': 5, }
            else:
                config = {'type': 'simple'}

            descr_dict[confname] = config

        return self.getWidget( search,
                               descr_dict.get(self.listname),
                               with_hidden,
                               True,
                               prefix,
                               parent,
                               config )


    def getWidget( self,
                   with_novalue = False,
                   selected     = None,
                   with_hidden  = False,
                   with_null    = False,
                   prefix       = '',
                   parent       = None,
                   config       = None):
        """\brief Returns a list combobox."""
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

        # prefix is only for REQUEST-handling
        if prefix:
            pre = DLG_CUSTOM + prefix
        else:
            pre = ''

        if not config:
            config = {}

        widget = None

        manager = self.getForeignManager()

        # check foreign lists
        if not manager:
            return hgLabel('%s not found' % self.manager, parent = parent)

        # standard case, normal connected list, forward
        # FIXME: we forward to List, would be better to have this done by getEntries
        # and build the widget ourself
#            if manager.listHandler.has_key(self.foreign):
#                _list = manager.listHandler[self.foreign]
#                widget = _list.getWidget( with_novalue,
#                                          selected,
#                                          with_hidden,
#                                          with_null,
#                                          prefix,
#                                          parent,
#                                          config )
#                # replace name of referenced list with own name
#                widget.setName(pre + self.listname)
#
#            # function found, handled by getEntries
#            elif self.function:

        if self.foreign in manager.listHandler or self.function:
            widget = self.createStandardSingleWidget(parent, pre, manager, with_novalue, with_null, with_hidden, selected, config)

        elif self.foreign in manager.tableHandler:
            # normally same handling as for self.function
            # exception: labelsearch set (using filter widget) or maxshown set (using range widget)
            # or both set (using range widget with filter enabled)
            # maxshown is only used when number of entries exceeds maxshown
            numEntries = self.getValueCount()
            maxshown = self.maxshown
            # tolerance set somewhere?
            tolerance = 10

            if maxshown and maxshown + tolerance < numEntries:
                # use a range widget
                # tolerance, maxshown, config.startnumber or 0
                startnumber = config.get('offset', 0)
                pattern = config.get('pattern', '')

                # correct startnumber
                if startnumber < 0:
                    startnumber = 0

                # only request some entries determined by maxshown, startnumber and pattern
                # startnumber was corrected before if button pressed in button handling function
                partlist, num = manager.searchLabelStrings(self.foreign, pattern, startnumber, maxshown, tolerance)

                # this is not ideal, when startitem (from old pattern) is num - 1, you only see 1 entry, while you could see all
                # but one cannot check too much here, since normal handling should still work and not shift when end of list is reached
                # solution would be to reset startnumber on pattern reset, but stateless handling doesn't support that
                if startnumber >= num:
                    # correct number, re-request the partlist
                    startnumber = num - maxshown
                    # new pattern delivers less then maxshown + tolerance entries -> start = 0
                    if startnumber <= tolerance:
                        startnumber = 0
                    # check to not end up negative
                    if startnumber < 0:
                        startnumber = 0
                    partlist, num = manager.searchLabelStrings(self.foreign, pattern, startnumber, maxshown, tolerance)

                # raise ValueError(startnumber)
                widget = hgFilteredRangeList(self.listname,
                                             parent,
                                             pre,
                                             pattern      = pattern,
                                             single       = True,
                                             totalcount   = num,
                                             doFilter     = self.labelsearch,
                                             startitem    = startnumber,
                                             tolerance    = tolerance,
                                             showitems    = maxshown,
                                             doProps      = True,
                                             doSearch     = with_novalue,
                                             doNull       = with_null,
                                             foreignTable = self.foreign,
                                             foreignMgr   = self.manager
                                             )



                # fill widget
                for autoid in partlist:
                    label = manager.getLabelString(self.foreign, autoid)
                    widget.insertItem(label, autoid)

                # can't sort here, items have to come in correct order from searchLabelString
                # widget.sort()

                # selection is tricky
                if selected:
                    if selected != 'NULL':
                        label = manager.getLabelString(self.foreign, selected)
                        widget.setCurrentValue(selected, label)
                    elif with_novalue:
                        # NULL only needed for search, indicated by no_value
                        label = '-- no value --'
                        widget.setCurrentValue(selected, label)

                widget.finalizeLayout()

            else:
                # use normal way
                widget = self.createStandardSingleWidget(parent, pre, manager, with_novalue, with_null, with_hidden, selected, config)
        else:
            raise ValueError('Couldn\'t find foreign list.')

        return widget


    def createStandardSingleWidget(self, parent, pre, manager, with_novalue, with_null, with_hidden, selected, config):
        """\brief Standard widget creation, filling and selection put extra"""
        completelist = self.getEntries(with_hidden = with_hidden, manager = manager)

        widget = self.createWidget(pre + self.listname,
                                   with_novalue,
                                   with_null,
                                   parent,
                                   config)

        # fill it
        for entry in completelist:
            widget.insertItem(entry[VALUE], entry[TCN_AUTOID])

        # sort
        widget.sort()

        # handles the selection of a list entry
        if selected:
            widget.setCurrentValue(selected)

        return widget


    def createWidget( self,
                      name,
                      with_novalue = False,
                      with_null    = False,
                      parent       = None,
                      config       = None):
        """\brief Returns a list combobox."""
        # NOTE: defaults to single list

        # load list data and build combobox
        if config and config['type'] == 'filtered':
            if config['direction'] == 'horizontal':
                vertical = False
            else:
                vertical = True
            pattern = config['pattern']
            if config['maxlen'] > 0:
                cbox = hgShortenedComboBox(name = name, parent = parent, pattern = pattern, vertical = vertical)

                cbox.setListLength(config['maxlen'])

                if config['tolerance'] > 0:
                    cbox.setListTolerance(config['tolerance'])
                else:
                    cbox.setListTolerance(10)
            else:
                cbox = hgFilteredComboBox(name = name, parent = parent, pattern = pattern, vertical = vertical)
        else:
            cbox = hgComboBox(name = name, parent = parent)

        # empty value
        if with_novalue:
            cbox.insertItem(' -- no search value -- ', '')

        # null value
        if with_null:
            cbox.insertItem(' -- no value -- ', 'NULL')

        return cbox


    # DEPRECATED special function to get Combobox widget without a real list
    def getSpecialWidget( self,
                          name         = None,
                          columns      = None,
                          expr         = None,
                          entry_list   = None,
                          with_novalue = False,
                          selected     = None,
                          with_null    = False,
                          parent       = None,
                          config       = None ):
        """\brief Generates Combobox for columns of a table, if
                expr is given, the values are put into expr, if list is
                given, the list-values are used instead of database-values.
        """
        assert isinstance(name, StringType) or name == None, \
               'Name has to be a string or None, got %s.' % name

        if not name:
            name = self.listname

        # get entries
        reslist = []
        if entry_list != None:
            reslist = entry_list
        else:
            mgr = self.getManager()
            if not isinstance(columns, ListType):
                columns = [columns]

            # just testing
            descr_dict = mgr.tableHandler[name].tabledict

            for column in columns:
                col_dict = descr_dict.get(column)
                if not col_dict:
                    raise ValueError('Unknown Column %s in table %s' \
                                      % (column, name) )
            # FIXME: this should use table functions instead of plain sql
            # get value list
            query = 'Select autoid, %s from %s' % ( ','.join(columns),
                                                    mgr.getId() + name )
            reslist = mgr.getManager(ZM_PM).executeDBQuery(query)

        # create widget
        cbox = self.createWidget(name,
                                 with_novalue,
                                 with_null,
                                 parent,
                                 config)

        # fill it
        self.fillSpecialWidget(cbox, reslist, expr)

        # sort
        cbox.sort()

        # handles the selection of a list entry
        if selected:
            cbox.setCurrentValue(selected)

        return cbox


    # DEPRECATED special function to fill the special widget
    # used by ForeignList/MultiList.getSpecialWidget
    def fillSpecialWidget(self, widget, entrylist, expr = None):
        """\brief fill widget with entrylist, evaluating expr, if present"""
        assert isinstance(entrylist, ListType)

        if len(entrylist) == 0:
            return widget

        if expr:

            map ( lambda entry:
                         widget.insertItem( expr % tuple(entry[1:]), entry[0]),
                         entrylist )
        else:

            if isinstance(entrylist[0], StringType):

                for entry in entrylist:
                    widget.insertItem(entry)

            elif len(entrylist[0]) > 2:

                # in this case, for is faster than map/lambda!
                for entry in entrylist:
                    widget.insertItem( ', '.join(entry[1:]),
                                       entry[0] )

            elif len(entrylist[0]) == 2:

                for entry in entrylist:
                    widget.insertItem( entry[1],
                                       entry[0]
                                       )

            else:
                raise ValueError('Programming error: Entrylist not fitting.')

        return widget


    # FIXME: Rename to getEntryCount to distinct from List
    def getValueCount(self):
        """\briefs Returns the length of a list.

        \param list_name  The argument \a list_name is the name of the list
        without the id prefix.

        \return The number of rows, otherwise None
        """
        manager = self.getForeignManager()

        if not manager:
            return 0

        if self.function:

            # NOTE: expensive, but the only way
            return len(self.getEntries(manager = manager))
        else:

            # handle foreign table or list
            if self.foreign in manager.tableHandler:
                cons = self.getManager().getListSelectionConstraints(self.listname)
                return manager.tableHandler[self.foreign].getEntryListCount(cons)
            elif self.foreign in manager.listHandler:
                return manager.listHandler[self.foreign].getValueCount()

        raise ValueError('Couldn\'t find foreign list.')


    def getValueByAutoid(self, autoid, lang=None):
        """\brief Returns the value from an specified list entry/entries."""

        # NOTE: do not handle lists recursivly since getting the
        #       manager is expensive
        if isinstance(autoid, ListType):
            is_list = True
            autoids = autoid
        else:
            is_list = False
            autoids = [autoid]

        retlist = []

        manager = self.getForeignManager()

        if not manager:
            # manager not found -> ignore and return empty values
            value = ['' for aid in autoids]
            if is_list:
                return value
            else:
                return value[0]
        for aid in autoids:
            value  = ''
            # not existing values
            if aid is None or aid == '':
                value = None
            # no value
            elif aid == 'NULL':
                pass
            elif aid == '_not_NULL':
                # TODO: use translation (Plone 4)
                if lang == 'de':
                    value = 'beliebig'
                else:
                    value = 'any'
            elif manager:
                assert isinstance(aid, IntType) or \
                       isinstance(aid, StringType), \
                       E_PARAM_TYPE % ('aid', 'IntType/StringType', aid)

                aid = int(aid)

                if self.function:
                    funcstr = self.function + F_VALUE
                    assert hasattr(manager, funcstr)
                    valfunc = getattr(manager, funcstr)
                    value   = valfunc(aid, lang)
                else:
                    # collist given, table-standard-function used
                    if self.foreign in manager.tableHandler:
                        tobj  = manager.tableHandler[self.foreign]
                        value = tobj.getEntryValue( aid, self.cols, lang )
                    elif self.foreign in manager.listHandler:
                        lobj  = manager.listHandler[self.foreign]
                        value = lobj.getValueByAutoid(aid, lang)
                    else:
                        raise ValueError('Couldn\'t find foreign list \'%s\'.' % self.foreign)

            retlist.append(value)


        if is_list:
            return retlist
        else:
            return retlist[0]


    def getShowHtml( self,
                     descr_dict,
                     useProperties = False,
                     parent        = None,
                     prefix = None ):
        """\brief Builds a html-formatted string of the value."""
        if prefix:
            pre = DLG_CUSTOM + prefix
        else:
            pre = ''
        autoid = descr_dict.get(self.listname, 0)
        ret = None
        if autoid and autoid != 'NULL':
            value = self.getValueByAutoid(autoid)

            manager = self.getForeignManager()

            if not manager:
                return hgLabel('Manager not found', parent = parent)

            if self.function:
                funcstr = self.function + F_LINK
                if hasattr(manager, funcstr):
                    linkfunc = getattr(manager, funcstr)
                    ret      = linkfunc(autoid, parent)
            else:
                if self.foreign in manager.tableHandler:
                    # we have a table and a autoid
                    if hasattr(manager, 'getLink'):
                        ret = manager.getLink(self.foreign, autoid, None, parent)

            if not ret:
                ret = hgLabel(value, parent = parent)
            if useProperties:
                ret += hgProperty(pre + self.listname, autoid)
                if parent:
                    ret.reparent(parent)
        else:
            ret = hgLabel('', parent = parent)
        return ret


    def editForm(self, REQUEST = None):
        """\brief Return the html source of the edit list form."""

        return HTML( dlgLabel('Cannot edit non simple lists.' ))(self, REQUEST)


    ##########################################################################
    #
    # Manage Tab Methods
    #
    ##########################################################################
    def viewTab(self, REQUEST):
        """\brief List overview tab."""
        dlg = self.viewTabFunctionality(REQUEST)
        return HTML( dlg.getHtml() )(self, REQUEST)


    def viewTabFunctionality(self, REQUEST):
        """\put the view tab functionality extra for overwriting in multilist"""
        message = ''

        dlg = getStdDialog('', 'viewTab')
        dlg.setHeader( "<dtml-var manage_page_header><dtml-var manage_tabs>" )
        dlg.setFooter( "<dtml-var manage_page_footer>"                       )

        tab = hgTable()
        tab._old_style = False

        # show tables information
        tab[0, 0] = '<h3>List Overview</h3>'
        tab.setCellSpanning(0, 0, colspan = 3)

        tab[1, 0] = '<b>Name</b>'
        tab[1, 1] = '<b>Type</b>'
        tab[1, 2] = '<b>Label</b>'
        tab[1, 4] = '<b>Manager</b>'
        tab[1, 5] = '<b>Reference Type</b>'
        tab[1, 6] = '<b>Target</b>'
        tab[1, 7] = '<b>Columns</b>'
        tab[1, 8] = '<b>Notes</b>'
        tab[1, 9] = '<b>Invisible</b>'


        list_mgr = self.getForeignManager()

        if list_mgr:
            lab = list_mgr.getId() + ' (' + list_mgr.getClassName() + ')'
            url = '%s/manage_main' % list_mgr.absolute_url()

            lab_mgr = hgLabel(lab, url)
        else:
            # external mgr not present
            lab_mgr = hgLabel('<font color="red">%s</font>' % self.manager)

        tab[2, 0] = self.listname
        tab[2, 1] = self.listtype
        tab[2, 2] = self.label
        tab[2, 4] = lab_mgr

        if self.function:
            target_type = 'Function'
            lab_target  = self.function
        else:
            target_type = 'List or Table'

            if list_mgr:
                if self.foreign in list_mgr.tableHandler:
                    target_type = 'Table'

                    url = '%s/%s/manage_workspace' % (list_mgr.tableHandler[self.foreign].absolute_url(), self.foreign)
                    lab_target = hgLabel(self.foreign, url)
                    if self.cols:
                        tab[2, 7] = str(self.cols)
                elif self.foreign in list_mgr.listHandler:
                    target_type = 'List'

                    url = '%s/%s/manage_workspace' % (list_mgr.listHandler[self.foreign].absolute_url(), self.foreign)
                    lab_target = hgLabel(self.foreign, url)
                else:
                    target_type = 'Missing'
                    lab_target = hgLabel('<font color="red">%s</font>' % self.foreign)
            else:
                lab_target = hgLabel('<font color="red">%s</font>' % self.foreign)

        tab[2, 5] = target_type
        tab[2, 6] = lab_target

        if isinstance(self.notes, StringType):
            tab[2, 8] = self.notes
        else:
            tab[2, 8] = (self.notes and 'yes') or 'no'
        tab[2, 9] = (self.invisible and 'yes') or 'no'

        dlg.add(tab)
        return dlg
