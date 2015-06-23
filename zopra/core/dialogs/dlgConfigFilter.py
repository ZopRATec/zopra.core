############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgConfigFilter.py
__revision__ = '0.1'

from types                              import StringType
from copy                               import copy

from PyHtmlGUI                          import hg

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgGroupBox       import hgGroupBox
from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgComboBox       import hgComboBox
from PyHtmlGUI.widgets.hgCheckBox       import hgCheckBox
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgLineEdit       import hgLineEdit
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from Products.ZMOM.ZMOMElements.Styles.Default   import ssiDLG_LABEL

from Products.ZMOM.ZMOMCorePart         import MASK_EDIT,   \
                                               TCN_AUTOID
                                               
from Products.ZMOM.dialogs.guiHandler   import guiHandler

from Products.ZMOM.secGUIPermission     import secGUIPermission

from Products.ZMOM.AuditAndSecurity.managers import TN_FILTER,       \
                                                    TN_RULEBLOCK,    \
                                                    TN_RULE,         \
                                                    TN_MUSER,        \
                                                    TN_FOLDER,       \
                                                    TN_LOCAL,        \
                                                    TCN_SUBJECT,     \
                                                    TCN_CONTENT,     \
                                                    TCN_LSENDER,     \
                                                    TCN_OWNER,       \
                                                    TCN_NAME,        \
                                                    TCN_SORTID,      \
                                                    TCN_TARGET,      \
                                                    TCN_BLOCKS,      \
                                                    TCN_KNF,         \
                                                    TCN_RULES,       \
                                                    TCN_FIELD,       \
                                                    TCN_VALUE,       \
                                                    TCN_NOT,         \
                                                    TCN_PREDICATE,   \
                                                    IMG_EDIT,     \
                                                    IMG_DELETE




class dlgConfigFilterPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.msgbox        = None
        self.btnbox        = None
        self.msg_count     = None
        self.saveButton    = None
        self.closeButton   = None
        self.helpButton    = None
        self.closeAccel    = None
        self.helpAccel     = None
        self.knf_cb        = None
        self.target_cb     = None
        self.name_entry    = None


class dlgConfigFilter( hgDialog, guiHandler ):
    """\class dlgConfigFilter

    \brief Filter management for Messaging Manager.
    """
    _className = 'dlgConfigFilter'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Save        =  3
    EditRule    =  4
    DelRule     =  5
    SelectField =  6
    AbortEdit   =  7
    SaveRule    =  8
    AddRule     =  9
    SwitchMode  = 10
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Manage Filters'

        # dlg private data
        self.data = dlgConfigFilterPrivate()

        # init values
        self.default_predicate = manager.FILTER_PRED_CONTAINS
        self.is_predicate      = manager.FILTER_PRED_IS
        self.predicates        = copy(manager.FILTER_PREDICATES)

        self.resetData()

        self.muser  = manager.getCurrentMUser()[TCN_AUTOID]
        self.id     = None
        self.lastId = manager.tableHandler[TN_FILTER].getLastId() + 1

        if param_dict.has_key('id'):
            try:
                self.id = int( param_dict.get('id') )
            except:
                manager.displayError('No valid filter id provided', 'Error')
        
        
        if self.id:
            self.filter = manager.tableHandler[TN_FILTER].getEntry(self.id)
            
            if not self.filter:
                manager.displayError('Filter with id %s not found' % self.id, 'Database Error')
                
            self.filtername = self.filter[TCN_NAME]
            self.knf        = self.filter[TCN_KNF]
            self.target     = self.filter[TCN_TARGET]
            
            # TODO: fix missing blocks/rules
            block_ids = self.filter.get(TCN_BLOCKS, [])
            block_ids.sort()
            
            for block_id in block_ids:
                
                block = manager.tableHandler[TN_RULEBLOCK].getEntry(block_id)
                
                if not block:
                    manager.displayError('Missing rule block', 'Database Error')
                    
                self.block_ids.append(self.current_bid)
                self.id2block[self.current_bid] = block
                block['temp_' + TCN_AUTOID] = self.current_bid
                block['temp_' + TCN_RULES]  = []

                rule_ids = block.get(TCN_RULES, [])
                rule_ids.sort()

                for rule_id in rule_ids:
                    rule = manager.tableHandler[TN_RULE].getEntry(rule_id)

                    if not rule:
                        manager.displayError('Missing rule', 'Database Error')
                        
                    self.rule_ids.append(self.current_rid)
                    block['temp_' + TCN_RULES].append(self.current_rid)
                    
                    self.id2rule[self.current_rid] = rule
                    self.current_rid += 1
                    
                    rule['temp_' + TN_RULEBLOCK] = self.current_bid

                self.current_bid += 1
                
        else:
            self.filtername = 'Filter ' + str(self.lastId)

        
        self.data.msg_count       = 0

        # create in nice tab order
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )
        self.data.helpButton      = hgPushButton( parent = self, name = 'help'    )
        self.data.saveButton      = hgPushButton( parent = self, name = 'save'    )

        self.data.closeButton.setText  ( '&Close'        )
        self.data.helpButton.setText   ( '&Help'         )
        self.data.saveButton.setText   ( '&Save'         )

        # connect the signals to the slots
        self.connect( self.data.helpButton.clicked,    self.help    )
        self.connect( self.data.closeButton.clicked,   self.reject  )
        self.connect( self.data.saveButton.clicked,    self.save    )

        self.initLayout(manager)


    # layout
    def initLayout(self, manager):
        """\brief Initialise the dialog layout."""

        # create layout
        page  = hgTable(parent = self.getForm())
        self.getForm().add(page)
        
        self.data.databox = self.layoutData(manager, parent = page)
        page[0, 0] = self.data.databox

        self.data.msgbox = self.layoutMessages(parent = page)
        page[1, 0] = self.data.msgbox

        self.data.btnbox = self.layoutButtons(parent = page)
        page[2, 0] = self.data.btnbox
        page.setCellAlignment(2, 0, 'center')


    def layoutData(self, manager, widget = None, parent = None):
        """\brief Get the button layout."""
        # get the data
        filter = self.getDataDict()
        tobj = manager.tableHandler[TN_FILTER]

        # general information  
        if not widget:      
            widget = hgGroupBox(parent=parent)
            wlay = hgGridLayout( widget, 12, 4 )
        else:
            widget.removeChildren()
        widget.caption = 'Configuration'
        wlay = widget.layout()

        widget._styleSheet.add(ssiDLG_LABEL)

        r = 0

        # name
        label = tobj.getLabelWidget(TCN_NAME, parent = widget)
        label.setToolTip('Name of the Filter') 
        wlay.addWidget( label, r, 0 )
        entry = manager.getFunctionWidget(TN_FILTER,
                                          TCN_NAME,
                                          widget,
                                          MASK_EDIT,
                                          filter)
        entry.setSize(30)
        entry.connect( entry.textChanged, self.setName   )
        
        self.data.name_entry = entry

        wlay.addWidget(entry, r, 2)
        r += 1
        
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        # target
        label = tobj.getLabelWidget(TCN_TARGET, parent = widget)
        label.setToolTip('Target of the Filter') 
        wlay.addWidget( label, r, 0 )
        
        
        target_cb = hgComboBox(name = 'target', parent = widget)

        target_cb.insertItem( 'Trash', 'Trash' )

        folders = manager.tableHandler[TN_FOLDER].getEntries([self.muser], [TCN_OWNER], order = TCN_SORTID)

        for folder in folders:
            target_cb.insertItem( manager.getLabelString(TN_FOLDER, None, folder), folder[TCN_AUTOID] )

        if self.target:
            target_cb.setCurrentValue(self.target)
        else:
            target_cb.setCurrentItem(0)

        self.connect( target_cb.valueChanged,   self.setTarget )
        
        self.data.target_cb = target_cb

        wlay.addWidget(target_cb, r, 2)
        r += 1
        
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        # mode
        label = tobj.getLabelWidget(TCN_KNF, parent = widget)
        label.setToolTip('Mode of the Filter') 
        wlay.addWidget( label, r, 0 )
        
        knfbox = hgHBox( parent = widget )
        knfbox.layout().data.expanding = hgSizePolicy.NoDirection        
        wlay.addWidget( knfbox, r, 2 )
 
        self.data.knf_cb = hgComboBox(name = 'knf', parent = widget)
        
        self.data.knf_cb.insertItem( 'DNF', 'DNF' )
        self.data.knf_cb.insertItem( 'KNF', 'KNF' )
        
        if self.knf:
            self.data.knf_cb.setCurrentValue('KNF')
        else:
            self.data.knf_cb.setCurrentValue('DNF')
        
        setknf = hgPushButton( parent = self, name = 'setknf'    )
        setknf.setText( 'Set Mode' )
        knfbox.add( self.data.knf_cb  )
        knfbox.add( setknf            )

        self.connect( setknf.clicked,   self.setKNF )

        wlay.addWidget(knfbox, r, 2)
        r += 1
        
        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        # create filters
        label = hgLabel('Rules', parent = widget)
        label.setToolTip('Rules of the Filter.') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget(label, r, 0, hg.AlignTop)

        self.rulebox = hgTable(parent = widget)
        wlay.addMultiCellWidget( self.rulebox, r, r, 2,  5)
        self.displayRules(manager)
        r += 1

        return widget
        

    def layoutMessages(self, widget = None, parent = None):
        """\brief Get the button layout."""
        
        if not widget:      
            widget = hgGroupBox(parent=parent)
            hgGridLayout( widget )
        else:
            widget.removeChildren()
        widget.caption = 'Message'

        return widget
        

    # todo: assert types of widget    
    def layoutButtons(self, widget = None, parent = None):
        """\brief Get the button layout."""
        if not widget:      
            widget = hgHBox(parent=parent)
            widget.layout().data.expanding = hgSizePolicy.NoDirection
        else:
            widget.removeChildren()
        
        widget.add( self.data.helpButton    )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.closeButton   )
        widget.add( hgLabel('&nbsp;', parent = widget)     )
        widget.add( self.data.saveButton    )

        return widget
    

    def displayRules(self, manager):
        """\brief Get the button layout."""
        # NOTE: uncommented line produces unexpected results
        #self.curimodbox.emptyTable()
        tab = hgTable(spacing = '0', parent = self.rulebox)
        self.rulebox[0, 0]   = tab
        self.editbtn2id     = {}
        self.delbtn2id      = {}
        self.newbtn2id      = {}
        
        # TODO: delete old buttons?
        i = -1
        for i, bid in enumerate( self.block_ids ):
            block = self.id2block[bid]
            
            block_widg = hgGroupBox(parent=tab)
            wlay = hgGridLayout( block_widg, 12, 4 )
            
            j = -1
            for j, rid in enumerate( block['temp_' + TCN_RULES] ):
                rule = self.id2rule[rid]
                
                c = 0
                if j != 0:
                    if self.knf:
                        wlay.addWidget(hgLabel('<b>OR</b>', parent = block_widg), j, c)
                    else:
                        wlay.addWidget(hgLabel('<b>AND</b>', parent = block_widg), j, c)
                c += 1

                wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), j, c)
                c += 1
                
                if bid == self.active_bid and rid == self.active_rid:
                    self.displayCurrentRule(manager, block_widg, wlay, j, c)
                else:
                    self.displayRule(manager, rule, rid, block_widg, wlay, j, c)
                
            if bid == self.active_bid and self.active_rid == 0:
                # current rule is new rule
                self.displayCurrentRule(manager, block_widg, wlay, j+1, 2)
            else:
                box = hgHBox( parent = block_widg )
                box.layout().data.expanding = hgSizePolicy.NoDirection
                wlay.addMultiCellWidget(box, j+1, j+1, 2, 5)
                
                # just the add rule btn
                name = 'new_' + str(bid)
                btn = hgPushButton(text = 'Add Rule', name = name, parent = box)
                btn.setToolTip('Add Rule')
                box.add(btn)
                self.connect( btn.clickedButton, self.addRule )
                self.newbtn2id[name] = bid                    
                

            tab[2*i, 0] = block_widg
            if self.knf:
                tab[2*i+1, 0] = hgLabel('<b>AND</b>', parent = tab)
            else:
                tab[2*i+1, 0] = hgLabel('<b>OR</b>', parent = tab)
            
            
        # and the new block
        block_widg = hgGroupBox(parent=tab)
        wlay = hgGridLayout( block_widg, 12, 4 )
        tab[2*(i+1), 0] = block_widg
        
        if self.active_bid == 0 and self.active_rid == 0:
            # current rule is new rule in new block
            self.displayCurrentRule(manager, block_widg, wlay, 0, 2)
        else:
            # just the add rule btn
            name = 'new_0'
            btn = hgPushButton(text = 'Add Rule', name = name, parent = block_widg)
            btn.setToolTip('Add Rule')
            wlay.addWidget(btn, 0, 2)
            self.connect( btn.clickedButton, self.addRule )
            self.newbtn2id[name] = 0                    

        
    def displayRule(self, manager, rule, rid, block_widg, wlay, r, c):
        """\brief Initialise the dialog layout."""
        
        # just display the rule
        field = manager.tableHandler[TN_LOCAL].getLabel(rule[TCN_FIELD])
        wlay.addWidget(hgLabel(field, parent = block_widg), r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
            
        neg = ''
        if rule.get(TCN_NOT):
            neg = 'not'
        wlay.addWidget(hgLabel(neg, parent = block_widg), r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
                    
        wlay.addWidget(hgLabel(rule.get(TCN_PREDICATE), parent = block_widg), r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
                    
        if rule[TCN_FIELD] == TCN_LSENDER:
            link = manager.getLink(TN_MUSER, int(rule[TCN_VALUE]), parent = block_widg)
            
            wlay.addWidget(link, r, c)
        else:
            wlay.addWidget(hgLabel(rule.get(TCN_VALUE), parent = block_widg), r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
                    
                    
        # modify and delete button
        box = hgHBox( parent = block_widg )
        box.layout().data.expanding = hgSizePolicy.NoDirection
                    
        name = 'edit_' + str(rid)
        icon = manager.iconHandler.get(IMG_EDIT, path=True).getIconDict()
        btn = hgPushButton(text = name, name = name, icon = icon, parent = box)
        btn.setToolTip('Edit')
        box.add(btn)
        self.connect( btn.clickedButton, self.editRule )
        self.editbtn2id[name] = rid
            
        name = 'delete_' + str(rid)
        icon = manager.iconHandler.get(IMG_DELETE, path=True).getIconDict()
        btn = hgPushButton(text = name, name = name, icon = icon, parent = box)
        btn.setToolTip('Delete')
        box.add(btn)
        self.connect( btn.clickedButton, self.deleteRule )
        self.delbtn2id[name] = rid                    
                           
        wlay.addWidget(box, r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1


    def displayCurrentRule(self, manager, block_widg, wlay, r, c):
        """\brief Initialise the dialog layout."""
        # new rule in new block
        field_cb = hgComboBox(name = 'rule_field', parent = block_widg)
        for field in [TCN_SUBJECT, TCN_CONTENT, TCN_LSENDER]:
            lab = manager.tableHandler[TN_LOCAL].getLabel(field)
            field_cb.insertItem(lab, field)

        field_cb.setCurrentValue(self.rule_field)
                    
        self.connect( field_cb.valueChanged, self.setField )

        wlay.addWidget(field_cb, r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
                    
        # checkbox for negation
        name = 'rule_not'
        neg_cb = hgCheckBox(text   = 'not', 
                            value  = self.rule_not, 
                            parent = block_widg, 
                            name   = name)

        self.connect( neg_cb.toggled, self.setNegation )
                    
        wlay.addWidget(neg_cb, r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
                    
        # predicate
        pred_cb = hgComboBox(name = 'rule_pred', parent = block_widg)
        for pred in manager.FILTER_PREDICATES:
            pred_cb.insertItem(pred, pred)
                        
        pred_cb.setCurrentValue(self.rule_predicate)
                    
        self.connect( pred_cb.valueChanged, self.setPredicate )

        wlay.addWidget(pred_cb, r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1
                    
        # value
        if self.rule_field == TCN_LSENDER:
            lobj = manager.listHandler.getList(TN_RULE, TCN_OWNER)
            #value_widget = lobj.getComplexWidget( parent = block_widg )
            value_widget = lobj.getWidget( parent = block_widg )
            value_widget.setName('rule_value')
            self.connect( value_widget.valueChanged,   self.selectSender )
            if self.rule_value:
                pred_cb.setCurrentValue(self.rule_value)
            else:
                pred_cb.setCurrentItem(0)
    
            # sender either matches or not predicate -> is
            if self.rule_predicate != self.is_predicate:
                pred_cb.setCurrentValue(self.is_predicate)
            pred_cb.setDisabled()
            
        else:
            value_widget = hgLineEdit(name = 'rule_value', parent = block_widg)
            value_widget.setText(self.rule_value)
            value_widget.setSize(20)
            self.connect( value_widget.textChanged,   self.setValue )

        wlay.addWidget(value_widget, r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1

        # buttons
        box = hgHBox( parent = block_widg )
        box.layout().data.expanding = hgSizePolicy.NoDirection
                    
        if self.select_field:
            neg_cb.setDisabled()
            pred_cb.setDisabled()
            value_widget.setDisabled()
                        
            # select button
            name = 'select_field'
            btn = hgPushButton(text = 'Select', name = name, parent = box)
            btn.setToolTip('Select field for the rule')
            box.add(btn)
            self.connect( btn.clicked, self.selectField )
        else:
            field_cb.setDisabled()

            # set and abort button
            name = 'save_edit'
            btn = hgPushButton(text = 'Set', name = name, parent = box)
            btn.setToolTip('Save Rule')
            box.add(btn)
            self.connect( btn.clicked, self.saveRule )

            box.add( hgLabel('&nbsp;', parent = box) )
            
            name = 'abort_edit'
            btn = hgPushButton(text = 'Abort', name = name, parent = box)
            btn.setToolTip('Abort editing')
            box.add(btn)
            self.connect( btn.clicked, self.abortEdit )

        wlay.addWidget(box, r, c)
        c += 1
        wlay.addWidget(hgLabel('&nbsp;', parent = block_widg), r, c)
        c += 1

    
    def addMessage(self, message):
        """\brief Initialise the dialog layout."""
        
        if not self.data.msgbox:
            return
        
        if isinstance(message, StringType):
            message = hgLabel(message, parent = self.data.msgbox)
            
        assert(isinstance(message, hgWidget))
        
        self.data.msgbox.layout().addWidget(message, self.data.msg_count, 0)

        self.data.msg_count += 1


    def resetMessages(self):
        """\brief Initialise the dialog layout."""
        
        if not self.data.msgbox:
            return
        
        self.data.msgbox.removeChildren()

        self.data.msg_count = 0


    # data manipulation
    def getDataDict(self, id = None, block = True):
        """\brief Get entry dict from dialog data."""
                
        if not id:
            return { TCN_KNF:    self.knf,
                     TCN_NAME:   self.filtername,
                     TCN_TARGET: self.target, 
                   }
        elif block:
            return self.id2block.get(id, {})
        else:
            return self.id2rule.get(id, {})
        
        
    def resetData(self):
        """"""
        self.filter      = { TCN_BLOCKS: [] }

        self.filtername  = ''
        self.target      = None
        self.knf         = 1
        
        self.current_rid = 1
        self.current_bid = 1
        self.block_ids   = []
        self.rule_ids    = []
        self.id2block    = {}
        self.id2rule     = {}
        self.btnname     = None
        
        self.btnname     = None

        self.resetCurrentRule()
        
        
    def resetCurrentRule(self):
        """"""
        
        self.active_rid     = None
        self.active_bid     = None

        self.rule_field     = TCN_SUBJECT
        self.rule_not       = 0
        self.rule_predicate = self.default_predicate
        self.rule_value     = ''
        
        self.select_field   = True
        
        
    def deleteRuleData(self, id):
        """"""
        rule  = self.id2rule[id]
        
        if not rule:
            return
        
        block_id = rule['temp_' + TN_RULEBLOCK]
        block    = self.id2block[block_id]
        
        assert(block)
        
        # remove rule from filter data
        del self.id2rule[id]
        self.rule_ids.remove(id)
        if rule.has_key(TCN_AUTOID):
            block[TCN_RULES].remove(rule[TCN_AUTOID])
        block['temp_' + TCN_RULES].remove(id)
        
        # remove block if empty
        if not block[TCN_RULES]:
            del self.id2block[block_id]
            self.block_ids.remove(block_id)
                        

    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_FILTER, secGUIPermission.SC_EDIT)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Save:
            self.performSave(manager)
            self.setResult(self.Running)
        elif self.result() == self.SwitchMode:
            self.performSwitchMode(manager)
            self.setResult(self.Running)
        elif self.result() == self.AddRule:
            self.performAddRule(manager)
            self.setResult(self.Running)
        elif self.result() == self.EditRule:
            self.performEditRule(manager)
            self.setResult(self.Running)
        elif self.result() == self.DelRule:
            self.performDeleteRule(manager)
            self.setResult(self.Running)
        elif self.result() == self.SelectField:
            self.performSelectField(manager)
            self.setResult(self.Running)
        elif self.result() == self.AbortEdit:
            self.performAbortEdit(manager)
            self.setResult(self.Running)
        elif self.result() == self.SaveRule:
            self.performSaveRule(manager)
            self.setResult(self.Running)
        
        
    # button callbacks   
    def setName(self, name):
        """\brief """

        self.filtername = name

    
    def setTarget(self, target):
        """\brief """

        if target == 'Trash':
            target = 0
        self.target = target

    
    def setKNF(self):
        """\brief """

        self.knf = self.data.knf_cb.getCurrentValue() == 'KNF'
        self.setResult(self.SwitchMode)

    
    def setField(self, field):
        """\brief """

        if field in [TCN_SUBJECT, TCN_CONTENT, TCN_LSENDER]:
            self.rule_field = field

    
    def setNegation(self, set):
        """\brief"""

        self.rule_not = set


    def setPredicate(self, pred):
        """\brief ."""
        
        if pred in self.predicates:
            self.rule_predicate = pred
        

    def setValue(self, value):
        """\brief ."""
        
        if self.rule_field == TCN_LSENDER:
            try:
                value = int(value)
            except:
                return
        
        self.rule_value = value
        

    def selectSender(self, value):
        """\brief ."""
        
        if self.rule_field == TCN_LSENDER:
            try:
                value = int(value)
            except:
                return
        
            self.rule_value = value
            

    def addRule(self, btnname):
        """\brief"""
        self.btnname = btnname
        self.setResult(self.AddRule)


    def deleteRule(self, btnname):
        """\brief"""
        self.btnname = btnname
        self.setResult(self.DelRule)


    def editRule(self, btnname):
        """\brief"""
        self.btnname = btnname
        self.setResult(self.EditRule)


    def selectField(self):
        """\brief"""
        self.setResult(self.SelectField)


    def abortEdit(self):
        """\brief"""

        self.setResult(self.AbortEdit)


    def saveRule(self):
        """\brief"""

        self.setResult(self.SaveRule)


    def save(self):
        """\brief"""

        self.setResult(self.Save)


    def help(self):
        """"""
        self.resetMessages()
        self.addMessage('Configure filter')


    def performRejected(self, manager):
        """\reimp"""
        self.resetMessages()

        # set edit dlg
        url    = manager.absolute_url()
        target = '%s/dlgHandler/dlgMngFilters/show' % (url)

        self.setTarget(target)
        self.target_url = target


    def performSwitchMode(self, manager):
        """\reimp"""
        self.resetMessages()
        self.displayRules(manager)
        
        
    def performSave(self, manager):
        """\reimp"""
        self.resetMessages()

        # check name
        if not self.filtername:
            self.addMessage('Filter name required.')
            return
            
        filters = manager.tableHandler[TN_FILTER].getEntries( [self.filtername, self.muser], 
                                                              [TCN_NAME,        TCN_OWNER] )
        assert( len(filters) < 2 )
        if filters:
            if not self.id or \
               filters[0][TCN_AUTOID] != self.id:
                self.addMessage('Filter name already in use. Please select another one.')
                return
        
        #check target
        if self.target:
            target = manager.tableHandler[TN_FOLDER].getEntry(self.target)
        else:
            target = { TCN_OWNER: self.muser }
        
        if not target or \
           target.get(TCN_OWNER) != self.muser:
            self.data.target_cb.setCurrentItem(0)
            self.addMessage('No valid folder selected')
            return

        # update rules
        for rid in self.rule_ids:
            rule = self.id2rule[rid]

            bid      = rule['temp_' + TN_RULEBLOCK]
            block    = self.id2block[bid]
            
            if not rule.get(TCN_AUTOID):
                rule_id = manager.tableHandler[TN_RULE].addEntry(rule)
                if not rule_id:
                    manager.displayError('An error occured while creating rule.', 
                                         'Database error')
                
                rule[TCN_AUTOID] = rule_id
                
                # add rule_id to block
                block[TCN_RULES].append(rule_id)
            else:
                rule_id = rule[TCN_AUTOID]
                if not manager.tableHandler[TN_RULE].updateEntry(rule, rule_id):
                    manager.displayError('An error occured while updating rule.', 
                                         'Database error')
                    
        # update blocks
        for bid in self.block_ids:
            block    = self.id2block[bid]

            if not block.get(TCN_AUTOID):
                block_id = manager.tableHandler[TN_RULEBLOCK].addEntry(block)
                if not block_id:
                    manager.displayError('An error occured while creating rule block.', 
                                         'Database error')
                
                block[TCN_AUTOID] = block_id

                # add block_id to filter
                self.filter[TCN_BLOCKS].append(block_id)
            else:
                block_id = block[TCN_AUTOID]
                
                orig_block = manager.tableHandler[TN_RULEBLOCK].getEntry(block_id)
                
                if not orig_block:
                    manager.displayError('Missing rule block %s.' % str(block_id), 
                                         'Database error')
                
                # remove deleted rules
                for rule_id in orig_block[TCN_RULES]:
                    if not rule_id in block[TCN_RULES]:
                        manager.tableHandler[TN_RULE].deleteEntry(rule_id)
                
                # update block
                if not manager.tableHandler[TN_RULEBLOCK].updateEntry(block, block_id):
                    manager.displayError('An error occured while updating rule block.', 
                                         'Database error')

            

        # update filter
        self.filter[TCN_KNF]    = self.knf
        self.filter[TCN_NAME]   = self.filtername
        self.filter[TCN_TARGET] = self.target      
                    
        if self.id:
            orig_filter = manager.tableHandler[TN_FILTER].getEntry(self.id)
                
            if not orig_filter:
                manager.displayError('Missing filter %s.' % str(self.id), 
                                     'Database error')
                
            # remove deleted blocks
            for block_id in orig_filter[TCN_BLOCKS]:
                if not block_id in self.filter[TCN_BLOCKS]:
                    manager.tableHandler[TN_RULEBLOCK].deleteEntry(block_id)

            # update filter
            if not manager.tableHandler[TN_FILTER].updateEntry(self.filter, self.id):
                    manager.displayError('An error occured while updating filter.', 
                                         'Database error')

            self.addMessage('Filter updated.')
        else:
            # generate new sort id
            sortid = 1
            constraints = { TCN_OWNER: self.muser }
            max_filter = manager.tableHandler[TN_FILTER].getEntryList(constraints = constraints,
                                                                      show_number = 1,
                                                                      order       = TCN_SORTID, 
                                                                      direction   = 'desc')
            if max_filter:
                sortid += max_filter[0][TCN_SORTID]
                
            self.filter[TCN_OWNER]  = self.muser
            self.filter[TCN_SORTID] = sortid
            
            # create filter
            filter_id = manager.tableHandler[TN_FILTER].addEntry(self.filter)
            if not filter_id:
                manager.displayError('An error occured while creating filter.', 
                                     'Database error')
                
            # register filter id
            self.id = filter_id
            
            self.addMessage('Filter created.')        
            
        
    
    def performAddRule(self, manager):
        """\reimp"""
        self.resetMessages()

        if not self.btnname or not self.newbtn2id.has_key(self.btnname):
            return
        
        self.resetCurrentRule()

        block_id = self.newbtn2id[self.btnname]

        self.btnname = None
        
        self.active_rid = 0
        self.active_bid = block_id
                        
        self.displayRules(manager)


    def performEditRule(self, manager):
        """\reimp"""
        self.resetMessages()

        if not self.btnname or not self.editbtn2id[self.btnname]:
            return
        
        self.resetCurrentRule()

        rule_id = self.editbtn2id[self.btnname] 
        rule  = self.id2rule[rule_id]
        
        block_id = rule['temp_' + TN_RULEBLOCK]
        block    = self.id2block[block_id]

        self.btnname = None
        
        self.active_rid = rule_id
        self.active_bid = block_id
        
        self.rule_field     = rule[TCN_FIELD]
        self.rule_not       = rule.get(TCN_NOT, False)
        self.rule_predicate = rule[TCN_PREDICATE]
        self.rule_value     = rule[TCN_VALUE]
        
        if self.rule_field == TCN_LSENDER:
            self.rule_value = int(self.rule_value)
                
        self.displayRules(manager)

        
    def performDeleteRule(self, manager):
        """\reimp"""
        self.resetMessages()

        if not self.btnname or not self.delbtn2id[self.btnname]:
            return
        
        rule_id = self.delbtn2id[self.btnname] 

        self.btnname = None

        self.deleteRuleData(rule_id)

        self.displayRules(manager)


    def performSelectField(self, manager):
        """\reimp"""
        self.resetMessages()
        
        self.select_field = False

        if self.rule_field == TCN_LSENDER:
            try:
                self.rule_value = int(self.rule_value)
            except:
                self.rule_value = 0
        else:
            try:
                self.rule_value = '' + self.rule_value
            except:
                self.rule_value = ''

        self.displayRules(manager)
            
            
    def performAbortEdit(self, manager):
        """\reimp"""
        self.resetMessages()

        self.resetCurrentRule()

        self.displayRules(manager)


    def performSaveRule(self, manager):
        """\reimp"""
        self.resetMessages()

        if self.active_rid == None:
            return
        
        if self.active_rid:
            rule  = self.id2rule[self.active_rid]
        else:
            # new rule
            rule    = {}
            rule_id = self.current_rid
            
            # new block
            if not self.active_bid:
                block    = {}
                block_id = self.current_bid
                
                # build block
                block['temp_' + TCN_AUTOID] = block_id
                block['temp_' + TCN_RULES]  = []
                block[TCN_RULES] = []

                # update dlg vars
                self.block_ids.append(block_id)
                self.id2block[block_id] = block
                
                self.current_bid += 1
            else:
                block_id = self.active_bid
                block    = self.id2block[block_id]

            # build rule
            rule['temp_' + TN_RULEBLOCK] = block_id

            # register rule in block
            block['temp_' + TCN_RULES].append(rule_id)

            # update dlg vars
            self.rule_ids.append(rule_id)
            self.id2rule[rule_id] = rule
            
            self.current_rid += 1
                    
        # set the rule data        
        rule[TCN_FIELD]     = self.rule_field
        rule[TCN_NOT]       = self.rule_not
        rule[TCN_PREDICATE] = self.rule_predicate
        rule[TCN_VALUE]     = str(self.rule_value)
        
        if self.rule_field == TCN_LSENDER:
            assert(self.rule_predicate == self.is_predicate)
        
        self.resetCurrentRule()                        

        self.displayRules(manager)
