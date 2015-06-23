############################################################################
#    Copyright (C) 2003 by Ingo Keller                                     #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from PyHtmlGUI.dialogs.hgWizard         import hgWizard

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgRadioButton    import hgRadioButton
from PyHtmlGUI.widgets.hgButtonGroup    import hgButtonGroup
from PyHtmlGUI.widgets.hgMultiList      import hgMultiList

from zopra.core.constants                   import TCN_AUTOID
from zopra.core.dialogs.guiHandler          import guiHandler
from zopra.core.widgets.hgComplexMultiList  import hgComplexMultiList


class dlgMoveListValuePrivate:
    """\class dlgNewGelPlatePrivate
       \brief data container for dlgNewGelPlate
    """
    def __init__(self):
        """\brief Initialize content"""
        self.old_vals        = []
        self.value_map       = {}
        self.extra_val_map   = {}
        self.from_list       = None
        self.to_list         = None
        self.move            = False
        # list of updatedTable objects
        self.updateTabs      = []


class updateTable:
    """\class updatedTable
       \brief data container for undo operation
    """
    def __init__(self, manager_type, manager_id, table):
        """\brief Initialize content"""
        # type and id of the manager
        self.manager_type    = manager_type
        self.manager_id      = manager_id
        # name of the table
        self.table           = table
        # list for original entries
        self.entries         = []
        # name of from and to list for this table
        self.from_list       = None
        self.to_list         = None

# this was never finished
#TODO: Finish this dialog, adjust to new listHandling

class dlgMoveListValue( hgWizard, guiHandler ):
    """\class dlgMoveListValue

    \brief moves and copies list values from one list to another, adjusting the tables
        using those lists
    """
    _className = 'dlgMoveListValue'
    _classType = hgWizard._classType + [_className]

    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################

    # List Types
    SINGLE    = 'singlelist'
    MULTI     = 'multilist'
    HIERARCHY = 'hierarchylist'

    # Warnings
    NOTHING  = ''
    UNDO     = 'All database changes have been undone.'
    INSERT   = 'Database changes have been stored.'
    NOINSERT = 'No actions necessary.'
    WARNINGS = [NOTHING, UNDO, INSERT, NOINSERT]
    
    # page titles
    TITLE1 = 'Select Lists'
    TITLE2 = 'Confirm Tables and Select Values'
    TITLE3 = 'Statistics'
    TITLES = [TITLE1, TITLE2, TITLE3]

    #state
    DO_NOTHING    = 1
    DO_UNDO       = 2
    DO_INSERT     = 4
    DO_REFRESH    = 8
    DID_UNDO      = 16
    DID_INSERT    = 32
    DIDNOT_INSERT = 64
    DID_REFRESH   = 128
     
    STATES = [DO_NOTHING, DO_UNDO, DO_INSERT, DO_REFRESH, DID_UNDO,
              DID_INSERT, DIDNOT_INSERT, DID_REFRESH]

    def setInternalState(self, state):
        """\brief Set the internal state."""
        assert state in self.STATES
        self.int_state = state

    def getInternalState(self):
        """\brief Return the internal state."""
        return self.int_state
    internalState = property(getInternalState, setInternalState)

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new new gelPlate wizard."""
        hgWizard.__init__( self )
        guiHandler.__init__( self )

        self.store = dlgMoveListValuePrivate()

        self.caption             = 'Move / Copy List Values Wizard'
        self.messageLabel1       = hgLabel('')
        self.messageLabel2       = hgLabel('')
        self.messageLabel3       = hgLabel('')
        # dynamic attrs

        self.int_state           = self.DO_NOTHING
        self.actTitle            = self.TITLE1

        self.initLayout(manager)


    def initLayout(self, manager):
        """\brief Initialise the pages."""
        self.setupPage1(manager)
        self.setupPage2(manager)
        self.setupPage3()
        self.connect(self.selected, self.pageChanged)
        self.show()


    def setupPage1(self, manager):
        """\brief Setup the first page of the dialog."""
        page1  = hgWidget()
        layout = hgGridLayout( page1, 2, 5, 3, 3)
        #page1.setLayout( layout )

        # move or copy
        way = hgButtonGroup()
        rad = hgRadioButton('move', 'Move', False, page1, 'way')
        way.insert(rad, 'move')
        layout.addWidget(rad, 0, 0)
        rad = hgRadioButton('copy', 'Copy', True, page1, 'way')
        way.insert(rad, 'copy')
        layout.addWidget(rad, 0, 2)
        way.connect(way.on, self.copyMove)

        # warning that move edits entries (selection moved as well)
        # warning that copy copies the selection

        # choose lists to move from / to
        label = hgLabel('from', parent = page1)
        layout.addWidget(label, 2, 0)
        label = hgLabel('to', parent = page1)
        layout.addWidget(label, 2, 2)
        row = 3
        radio1 = hgButtonGroup()
        radio2 = hgButtonGroup()
        # we are correcting entries, so we need the referencing lists (ForeignList, MultiList, HierarchyList)
        for (table, item) in manager.listHandler.references():
            lobj = manager.listHandler.getList(table, item)
            if not lobj.manager:
                rad = hgRadioButton( item,
                                     lobj.getLabel(),
                                     False,
                                     page1,
                                     'from_list' )
                radio1.insert(rad, item)
                layout.addWidget(rad, row, 0)
                rad = hgRadioButton( item,
                                     lobj.getLabel(),
                                     False,
                                     page1,
                                     'to_list' )
                radio2.insert(rad, item)
                layout.addWidget(rad, row, 2)
                row += 1
        radio1.connect( radio1.on, self.setFromList )
        radio2.connect( radio2.on, self.setToList   )

        row += 1
        self.messageLabel1.reparent(page1)
        layout.addMultiCellWidget(self.messageLabel1, row, row, 0, 2)
        self.addPage( page1, self.TITLE1 )

        self.setHelpEnabled(   page1, False )
        self.setFinishEnabled( page1, False )


    def setupPage2(self, manager):
        """\brief Setup the second page of the dialog."""
        page2  = hgWidget()
        layout = hgGridLayout( page2, 3, 3)

        # init some labels?

        self.addPage( page2, self.TITLE2 )

        self.setHelpEnabled  ( page2, False )
        self.setFinishEnabled( page2, False )

    def setupPage3(self):
        """\brief Shows the summary page for the job creation."""
        page3  = hgWidget()
        layout = hgGridLayout( page3, 3, 3)

        # init some labels?

        self.addPage( page3, self.TITLE3 )
        
        self.setNextEnabled  ( page3, False )
        self.setHelpEnabled  ( page3, False )
        self.setFinishEnabled( page3, True  )

    def refreshPage2(self, manager):
        """\brief refreshes page2 on gelid-change."""
        page2 = self.page(1)
        # only remove selective parts?
        page2.hide()
        page2.removeChildren()
        lay = page2.layout()
        if not lay:
            lay = hgGridLayout(page2, 1, 1, 3, 0)

        # choose values, confirm tables
        errstr = ''
        # no list selected
        if not self.store.from_list or not self.store.to_list:
            errstr = 'Please choose a source and a destination.'
        # same lists selected
        elif self.store.from_list == self.store.to_list:
            errstr = 'Please choose different source and destination.'

        if errstr:
            self.updateWarning(errstr)
            self.showPage(self.page(0))
            self.actTitle = self.TITLE1
            return

        # test list types
        from_obj  = manager.listHandler[self.store.from_list]
        to_obj    = manager.listHandler[self.store.to_list]
        from_type = from_obj.listtype
        to_type   = to_obj.listtype

        # labels
        label = hgLabel('Values', parent = page2)
        lay.addWidget(label, 1, 0)

        label = hgLabel(from_obj.label, parent = page2)
        lay.addWidget(label, 0, 1)

        label = hgLabel( to_obj.label + ' (for comparison only)',
                         parent = page2 )
        lay.addWidget(label, 0, 3)

        # list of to_entries
        mul_to = hgMultiList(parent = page2)
        mul_to.setEnabled(False)
        to_entries = to_obj.getEntries()
        for entry in to_entries:
            mul_to.insertItem(entry['value'])
        lay.addWidget(mul_to, 1, 3)

        # get values, put into complex multilist
        from_entries = from_obj.getEntries()

        mul_from = hgComplexMultiList(parent = page2)
        lay.addWidget(mul_from, 1, 1)
        for entry in from_entries:
            autoid = entry[TCN_AUTOID]
            if from_type == self.HIERARCHY:
                label = from_obj.getHierarchyListEntryString(autoid)
            else:
                label = entry['value']
            mul_from.insertItem(label, autoid)
        self.from_value_list = mul_from

        # label according from and to type
        lab = None
        if from_type == to_type:
            lab  = 'Same type, no value change. Already existing values will'
            lab += ' be reused.'
        elif from_type == self.SINGLE:
            if to_type == self.MULTI:
                lab  = 'Selected values will be added. Already existing '
                lab += 'values will be reused.'
            elif to_type == self.HIERARCHY:
                lab  = 'Selected values will be added to level 0. '
                lab += 'No value reuse.'
        elif from_type == self.MULTI:
            if to_type == self.SINGLE:
                lab  = 'Multiple selections will be transformed to single '
                lab += 'values (using x for multiple selections). Already '
                lab += 'existing values will be reused.'
            elif to_type == self.HIERARCHY:
                lab  = 'Selected values will be added to level 0. '
                lab += 'No value reuse.'
        elif from_type == self.HIERARCHY:
            if to_type == self.SINGLE:
                lab  = 'Selected values (complete path through hierarchy) '
                lab += 'will be transformed to single values (using x for '
                lab += 'multiple selections). Already existing values will '
                lab += 'be reused.'
            elif to_type == self.MULTI:
                lab  = 'Selected values (complete path through hierarchy) will'
                lab += ' be added. Already existing values will be reused.'
        if lab:
            label = hgLabel(lab, parent = page2)
            lay.addMultiCellWidget(label, 2, 2, 0, 4)

        # main table
        label = hgLabel('owning table', parent = page2)

        # check owning table of to/from list
        from_tab = from_obj.table
        to_tab   = to_obj.table


        ownTab = updateTable(manager.getClassType(), manager.id, from_tab)
        ownTab.from_list = self.store.from_list

        # different table, move could hurt
        if from_tab != to_tab:
            lab = ''
            # warn
        else:
            ownTab.to_list = self.store.to_list
        # store
        self.store.updateTabs.append(ownTab)

        # get all managers (hierarchy down,
        # and their tables to check for occurence of from_list)

        mgrs = manager.getAllManagers(objects = True)
        tabs = []
        for man in mgrs:
            # store positive tables
            local_store = []
            # store to_lists
            table_map   = {}
            # only from matters, cycle through all lists
            for (table, listname) in man.listHandler.references():
                lobj = man.listHandler.getList(table, listname)
                found = False
                if lobj.manager == manager.getClassName():
                    # case1: no function, same name
                    if not lobj.function and lobj.listname == self.store.from_list:
                        # same
                        found = True
                    # case2: function == listname+'()'
                    elif lobj.function and lobj.function[:-2] == self.store.from_list:
                        found = True
                    if found:
                        # get Listobj through other manager
                        search = man.getHierarchyUpManager(lobj.manager)
                        # test wether the other manager really uses our manager
                        if search == manager:
                            # the list belongts to a table
                            table = lobj.table
                            # build undo table object
                            tab = updateTable(man.getClassName(), man.id, table)
                            tab.from_list = lobj.listname
                            self.store.updateTabs.append(tab)
                            local_store.append(tab)

                    else:
                        # test to_list
                        # case1: no function, same name
                        if not lobj.function and lobj.listname == self.store.to_list:
                            # same
                            found = True
                        # case2: function == listname+'()'
                        elif lobj.function and lobj.function[:-2] == self.store.to_list:
                            found = True
                        if found:
                            # get Listobj through other manager
                            search = man.getHierarchyUpManager(lobj.manager)
                            # test wether the other manager really uses our manager
                            if search == manager:
                                # the lists belongs to a table
                                table = lobj.table
                                table_map[table] = lobj.listname
            # lists done, test found to_lists
            # works only for one to_list per table!
            for entry in local_store:

                # print a label about that table
                

                if entry.table in table_map.keys():
                    entry.to_list = table_map[entry.table]
                else:
                    # print a label to state the problem
                    pass
        # enable
        page2.show()
        page2.showChildren(True)


###############################################################################
# Slot Functions
###############################################################################

    def copyMove(self, way):
        """\brief Slot function. set move / copy"""
        if way == 'move':
            self.store.move = True
        if way == 'copy':
            self.store.move = False

    def setFromList(self, name):
        """\brief Slot function. Set list from which values will be moved"""
        self.store.from_list = name


    def setToList(self, name):
        """\brief Slot function. Set list to which values should be moved"""
        self.store.to_list = name


    def pageChanged(self, title):
        """\brief Slot function. Set state according to page called"""
        assert title in self.TITLES
        if title == self.TITLE2:
            # test for back - jump from final page
            if self.act_title == self.TITLE3:
                # come from page 3, move to page 2
                self.setInternalState(self.DO_UNDO)
            elif self.act_title == self.TITLE1:
                # come from page 1, move to page 2
                self.setInternalState(self.DO_REFRESH)
        elif title == self.TITLE3:
            if self.act_title == self.TITLE2:
                # come from page 2, move to page 3
                self.setInternalState(self.DO_INSERT)
        self.act_title = title

#
# Other Functions
#

    def updateWarning(self, warning):
        # TODO put warning on all pages
        self.messageLabel1.setText(warning)
        self.messageLabel2.setText(warning)
        self.messageLabel3.setText(warning)


    def checkWarnings(self):
        """\brief Check for something to show in message panel"""
        # undo warnings
        self.updateWarning(self.NOTHING)
        state = self.getInternalState()
        # successful undo
        if state == self.DID_UNDO:
            self.updateWarning(self.UNDO)
            self.setInternalState(self.DO_NOTHING)
        # successful insert
        elif state == self.DID_INSERT:
            self.updateWarning(self.INSERT)
            self.setInternalState(self.DO_NOTHING)
        # nothing inserted
        elif state == self.DIDNOT_INSERT:
            self.updateWarning(self.NOINSERT)
            self.setInternalState(self.DO_NOTHING)


    def execDlg(self, manager = None, REQUEST = None):
        """\brief overwrites execDlg of parent class to get access to the manager."""
        # call parent function (processes REQUEST, changes widgets)

        guiHandler.execDlg(self, manager, REQUEST)

        # own calculations (after signals have been fired)
        state = self.getInternalState()
        if state == self.DO_REFRESH:
            self.checkWarnings()
            self.refreshPage2(manager)
            self.setInternalState(self.DO_NOTHING)
            # to avoid overwritting messages by checkWarnings again
            return
        elif state == self.DO_INSERT:
            if self.performInsert(manager):
                self.setInternalState(self.DID_INSERT)
            else:
                self.setInternalState(self.DIDNOT_INSERT)
        elif state == self.DO_UNDO:
            self.performUndo(manager)
            self.setInternalState(self.DID_UNDO)

        # update message panel (and change state again)
        self.checkWarnings()


    def performUndo(self, manager):
        """\brief Undo Database operations."""
        pass


    def performInsert(self, manager):
        """\brief Does all database action and sets inserted state."""
        # edit page 3
        page3 = self.page(2)
        # only remove selective parts?
        page3.hide()
        page3.removeChildren()
        lay = page3.layout()
        if not lay:
            lay = hgGridLayout(page3, 1, 1, 3, 0)

        # self.from_list, self.to_list
        # self.from_tab, self.to_tab
        # self.from_type, self.to_type
        # self.move (True / False)

        # get values from self.from_value_list
        values = self.from_value_list.getSelectedValues()
        if not values:
            label = hgLabel( 'Please choose at least one value.',
                             parent = page3 )
            lay.addWidget(label, 0, 0)
            # the undo-lists are still empty
            # jump back
            return False

        from_obj = manager.listHandler[self.store.from_list]
        to_obj   = manager.listHandler[self.store.to_list]
        # determine type

        mapping  = {}
        # copy values and create value-mapping
        for valueid in values:
            # get complete entry for store
            from_entry = from_obj.getEnry(valueid)
            self.store.old_vals.append(from_entry)
            if to_obj.listtype == self.HIERARCHY:
                rank = '0'
            else:
                rank = ''
            newid = to_obj.addValue(from_entry.get('value'), rank = rank)
            # store in mapping
            self.store.value_map[entry] = newid
            # transformed values (multi->single) will be added to extra_val_map{value:id}

        # cycle through updateTable object
        for upd in self.store.updateTabs:
            # get Manager

            # get Table

            # from_list

            # to_list

            for oldval in self.store.value_map:
                # use update function of table (automatic cache update)
                # getEntries
                # store them
                # move: remove old value
                # insert new value (add or cross)
                # update
                pass
        if self.move == True:
            #delete old values
            for oldval in self.store.old_vals:
                from_obj.delValue(oldval.get(TCN_AUTOID))

        return True

    def performRejected(self, manager):
        """\brief overwritten rejectmethod from guiHandler, performs undo."""
        # undo
        self.performUndo(manager)
        # delete data
        # del self.store
        # call super function
        guiHandler.performRejected(self, manager)
