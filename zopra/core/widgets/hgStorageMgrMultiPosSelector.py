##############################################################################
#    Copyright (C) 2006 by Bernhard Voigt (LMU Munich)                       #
#    bernhard.voigt@lrz.uni-muenchen.de                                      #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################
# TODO: Move dialog to package

from copy                            import copy
from types                           import ListType, IntType

from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout
from PyHtmlGUI.kernel.hgWidget       import hgWidget

from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgProperty
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox
from PyHtmlGUI.widgets.hgMultiList   import hgMultiList

from zopra.core.elements.Styles.Default import ssiDLG_CLXMULTILIST

from zopra.core.Storage.managers              import TN_CONTAINER, \
                                                     TN_BOX,       \
                                                     TN_POSITION

from zopra.core.Storage                       import nsStorage 

from zopra.core.elements.Buttons      import DLG_FUNCTION,  \
                                                        BTN_L_ADDITEM, \
                                                        BTN_L_REMOVE, \
                                                        getPressedButton

from zopra.core.CorePart  import MASK_ADD,       \
                                        MASK_EDIT,      \
                                        MASK_SEARCH,    \
                                        MASK_SHOW

CONTAINER_SELECT = '_conselect'
BOX_SELECT       = '_boxselect'
POSITION_SELECT  = '_posselect'
SELECT_TEXT      = 'Select'




MWDG_HORIZONTAL = 0x0000
MWDG_VERTICAL   = 0x0100
MWDG_OPTIONAL   = 0x0200


HORIZONTAL = MWDG_HORIZONTAL
VERTICAL   = MWDG_VERTICAL
OPTIONAL   = MWDG_OPTIONAL

class hgStorageMgrMultiPosSelector(hgWidget):
    """\class hgStorageMgrMultiPosSelector

    \brief The hgStorageMgrMultiPosSelector widget provides a widget that allows to select positions in storage mgr.

    """
    _className = 'hgStorageMgrMultiPosSelector'
    _classType = hgWidget._classType + [ _className ]
    
    
    def __init__(self, 
                 storagemgr,
                 name     = None, 
                 parent   = None, 
                 prefix   = None,
                 manager  = None,
                 person   = None,
                 flags    = 0):
        """\brief Constructs a hgStorageMgrMultiPosSelector widget."""
        hgWidget.__init__(self, parent, name)

        self.parentmgr  = None
        self.optional   = OPTIONAL
        self.direction  = HORIZONTAL 
        self.mode       = MASK_ADD
        self.person     = person
        
        if flags & VERTICAL:
            self.mode   = VERTICAL

        if flags & OPTIONAL:
            self.mode   = OPTIONAL

        if flags & MASK_EDIT:
            self.mode   = MASK_EDIT
        elif flags & MASK_SEARCH:
            self.mode   = MASK_SEARCH
        elif flags & MASK_SHOW:
            self.mode   = MASK_SHOW
        
        if manager:
            self.parentmgr = manager

        # for stateless handling (old)
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = ''

        self.buildLayout()


    def buildLayout(self):
        """\brief builds layout"""

        if self.mode & MASK_SHOW:
            return

        if self.direction == HORIZONTAL:
            self.buildHorizontalLayout()
        else:
            self.buildVerticalLayout()

        
    def buildHorizontalLayout(self):
        """\brief builds horizontal layout"""
        
        row=0
        column=0
                
        # layout
        layout = hgGridLayout(self, 8, 8)

        # container part
        self.containerlab = hgLabel('Container:', parent=self)
        layout.addWidget( self.containerlab, row, column)
        row += 1
        self.containerbox = hgComboBox(name = self.prefix + self.name + CONTAINER_SELECT, parent=self)
        layout.addWidget( self.containerbox, row, column)
        row += 1
        # add property widget at empty cell property 
        self.properties = hgWidget(parent = self)
        layout.addWidget(self.properties, row, column)
        row += 1
        self.containerbtn = hgPushButton(SELECT_TEXT, name = DLG_FUNCTION + self.prefix + self.name + CONTAINER_SELECT, parent=self)
        layout.addWidget( self.containerbtn, row, column)
        row     = 0
        column += 1

        # spacing
        layout.addWidget( hgLabel('&nbsp;', parent=self), row, column)
        column += 1


        # box part
        self.boxlab = hgLabel('Box:', parent=self)
        layout.addWidget( self.boxlab, row, column )
        row += 1
        self.boxbox = hgComboBox(name = self.prefix + self.name + BOX_SELECT, parent=self)
        layout.addWidget( self.boxbox, row, column )
        row += 2
        self.boxbtn = hgPushButton(SELECT_TEXT, name = DLG_FUNCTION + self.prefix + self.name + BOX_SELECT, parent=self)
        layout.addWidget( self.boxbtn, row, column )
        row     = 0
        column += 1
    
        # spacing
        layout.addWidget( hgLabel('&nbsp;', parent=self), row, column)
        column += 1
        
        # position part
        self.boxlab = hgLabel('Positions:', parent=self)
        layout.addMultiCellWidget( self.boxlab, row, row, column, column+1)
        row += 1
        
        self.allposlist = hgMultiList(name = 'new' + self.prefix + self.name, parent=self)
        # make sure ssi is registered globally
        self.allposlist._styleSheet.add(ssiDLG_CLXMULTILIST)
        # set ssi for use                                
        self.allposlist.setSsiName( ssiDLG_CLXMULTILIST.name() )
        layout.addMultiCellWidget( self.allposlist, row, row+1, column, column)

        self.selposlist = hgMultiList(name = 'del' + self.prefix + self.name, parent=self)
        # set ssi for use                                
        self.selposlist.setSsiName( ssiDLG_CLXMULTILIST.name() )
        layout.addMultiCellWidget( self.selposlist, row, row+1, column+1, column+1)
        

        add = 'Add Item'
        rem = 'Remove Item'
        self.addbtn = hgPushButton( add,
                                    parent = self,
                                    name = DLG_FUNCTION + add )        
        layout.addWidget( self.addbtn, row+2, column)
        self.rembtn = hgPushButton( rem,
                                    parent = self,
                                    name = DLG_FUNCTION + rem )
        
        layout.addWidget( self.rembtn, row+2, column+1)



    def buildVerticalLayout(self):
        """\brief builds vertical layout"""
        
        row=0
        column=0
                
        # layout
        layout = hgGridLayout(self, 8, 8)

        # container part
        self.containerlab = hgLabel('Container:', parent=self)
        layout.addWidget( self.containerlab, row, column)
        column += 1
        layout.addWidget( hgLabel('&nbsp;', parent=self), row, column)
        column += 1            
        self.containerbox = hgComboBox(name = self.prefix + self.name + CONTAINER_SELECT, parent=self)
        layout.addWidget( self.containerbox, row, column)
        column += 1
        self.containerbtn = hgPushButton(SELECT_TEXT, name = DLG_FUNCTION + self.prefix + self.name + CONTAINER_SELECT, parent=self)
        layout.addWidget( self.containerbtn, row, column)
        row    += 1
        column  = 0

        # box part
        self.boxlab = hgLabel('Box:', parent=self)
        layout.addWidget( self.boxlab, row, column)
        column += 1
        # add property widget at empty cell property 
        self.properties = hgWidget(parent = self)
        layout.addWidget(self.properties, row, column)
        column += 1       
        self.boxbox = hgComboBox(name = self.prefix + self.name + BOX_SELECT, parent=self)
        layout.addWidget( self.boxbox, row, column)
        column += 1
        self.boxbtn = hgPushButton(SELECT_TEXT, name = DLG_FUNCTION + self.prefix + self.name + BOX_SELECT, parent=self)
        layout.addWidget( self.boxbtn, row, column)
    
        row    += 1
        column  = 0
        
        # position part
        self.boxlab = hgLabel('Positions:', parent=self)
        layout.addWidget( self.boxlab, row, column)
        column += 2
        
        self.allposlist = hgMultiList(name = 'new' + self.prefix + self.name, parent=self)
        layout.addMultiCellWidget( self.allposlist, row, row+1, column, column)

        self.selposlist = hgMultiList(name = 'del' + self.prefix + self.name, parent=self)
        layout.addMultiCellWidget( self.selposlist, row, row+1, column+1, column+1)
        

        add = 'Add Item'
        rem = 'Remove Item'
        self.addbtn = hgPushButton( add,
                                    parent = self,
                                    name = DLG_FUNCTION + add )        
        layout.addWidget( self.addbtn, row+2, column+1)
        self.rembtn = hgPushButton( rem,
                                    parent = self,
                                    name = DLG_FUNCTION + rem )
        
        layout.addWidget( self.rembtn, row+2, column+1)


    def fillContainers(self, storagemgr, selected_id = None):
        """\brief Get data from storage manager and fill container"""
        
        if storagemgr:
            if self.mode & MASK_SEARCH:
                predicate = lambda set, total: set > 0
            else:
                predicate = lambda set, total: set < total
            containers = storagemgr.getContainers(self.parentmgr, predicate, self.person)
        
            for container in containers:
                self.containerbox.insertItem(containers[container]['name'], container)
            self.containerbox.sort()        

            # null value 
            if self.optional:
                self.containerbox.insertItem(' -- no value -- ', 'NULL', 0)
                
            if self.mode & MASK_SEARCH:
                self.containerbox.insertItem(' -- no search value -- ', '', 0)

            if selected_id:
                self.containerbox.setCurrentValue(selected_id)


    def fillBoxes(self, container, storagemgr, selected_id = None):
        """\brief Get data from storage manager and fill boxes"""

        if storagemgr:
            if self.mode & MASK_SEARCH:
                predicate = lambda set, total: set > 0
            else:
                predicate = lambda set, total: set < total
            # parameter person = None -> get all boxes (boxowner ignored)
            boxes = storagemgr.getBoxesForContainer(container, predicate, None)
        
            for box in boxes:
                self.boxbox.insertItem(boxes[box]['name'], box)
            self.boxbox.sort()        

            # null value 
            if self.optional:
                self.boxbox.insertItem(' -- none -- ', 'NULL', 0)
                
            if selected_id:
                self.boxbox.setCurrentValue(selected_id)


    def fillPositions(self, box, storagemgr):
        """\brief Get data from storage manager and fill positions"""

        if storagemgr:
            if self.mode & MASK_SEARCH:
                predicate = lambda set: set
            else:
                predicate = lambda set: not set
            # parameter person = None -> get all positions (boxowner ignored)
            positions = storagemgr.getPositionsForBox(box, predicate, None)
        
            for position in positions:
                self.allposlist.insertItem(positions[position]['name'], position)
            self.allposlist._item_list.sort()


    def selectPositions(self, storagemgr, selected_ids = None):
        """\brief Fill selected positions"""
        if not selected_ids:
            selected_ids = []
            
        if not isinstance(selected_ids, ListType):
            selected_ids = [selected_ids]
             
        selected_ids.sort()
            
        # remove old selection               
        self.selposlist.clearList()
            
        # select new
        for pos_id in selected_ids:
            name = storagemgr.getLabelString(TN_POSITION, pos_id)
            if self.selposlist.insertSecureItem(name, pos_id):
                self.setValue('', pos_id)
                self.allposlist.removeItemByValue(pos_id)                


    def appendOriginalPositions(self, REQUEST, descr_dict, storagemgr):
        """\brief Insert current value into widget and mark it"""

        if self.mode & MASK_EDIT:
            select = False
            # original position must have been property
            orig_ids = self.getProperty(REQUEST, '')
            
            # if it was not set we have a new edit widget and current pos is the original value
            if not orig_ids:
                orig_ids = descr_dict.get(self.name, [])
                if not orig_ids:
                    return
                select = True
                
            if not isinstance(orig_ids, ListType):
                orig_ids = [orig_ids]
            
            coords               = {}
            coords[TN_CONTAINER] = []
            coords[TN_BOX]       = []
            
            # store original position as property
            # expensive
            for orig_id in orig_ids:
                # original position must have content            
                if not storagemgr.isFull(TN_POSITION, orig_id):
                    continue
                #assert(storagemgr.isFull(TN_POSITION, orig_id))
                self.setProperty('', orig_id)
            
                coord = storagemgr.getCoordsForPosition(orig_id)
                
                if not coord[TN_CONTAINER] in coords[TN_CONTAINER]:
                    coords[TN_CONTAINER].append(coord[TN_CONTAINER])
                if not coord[TN_BOX] in coords[TN_BOX]:
                    coords[TN_BOX].append(coord[TN_BOX])
                            
            
            citem = bitem = pitem = None
            
            # mark container label
            clist = self.containerbox.getItemList()
            missing = copy(coords[TN_CONTAINER])
            
            for i, citem in enumerate(clist):
                if citem[1] in coords[TN_CONTAINER]:
                    clist[i][0] = clist[i][0] + '*'
                    missing.remove(citem[1])

            # fill missing entries
            if missing:
                # save selection
                selection = self.containerbox.getCurrentValue()

                # save special entries
                tmplist = []
                while len(clist) > 0 and not isinstance(clist[0][1], IntType):
                    tmplist.append(clist.pop(0))
                for c_id in missing:
                    # get data for new entry
                    (set, total) = storagemgr.getFillState(TN_CONTAINER, c_id)
            
                    name = storagemgr.getLabelString(TN_CONTAINER, c_id, 
                                                          info = nsStorage.LABEL_WITH_DESCRIPTION | nsStorage.LABEL_WITH_TYPE)
                    name += ' (' + str(total-set) + '/' + str(total) + ')*'

                    clist.append([name, c_id])
                    
                clist.sort()
                clist = tmplist + clist
            
                # restore selection
                self.containerbox.setCurrentValue(selection)
                            
            # if container is selected we have to continue with boxes
            if not self.containerbox.getCurrentValue() in coords[TN_CONTAINER]:
                return
                
                
            # mark box label
            blist = self.boxbox.getItemList()
            missing = copy(coords[TN_BOX])
            
            for i, bitem in enumerate(blist):
                if bitem[1] in coords[TN_BOX]:
                    blist[i][0] = blist[i][0] + '*'
                    missing.remove(bitem[1])

            # fill missing entries
            if missing:
                # save selection
                selection = self.boxbox.getCurrentValue()

                # save special entries
                tmplist = []
                while len(blist) > 0 and not isinstance(blist[0][1], IntType):
                    tmplist.append(blist.pop(0))
                for b_id in missing:
                    # get data for new entry
                    (set, total) = storagemgr.getFillState(TN_BOX, b_id)
            
                    name = storagemgr.getLabelString(TN_BOX, b_id)
                    name += ' (' + str(total-set) + '/' + str(total) + ')*'

                    clist.append([name, b_id])
                    
                blist.sort()
                blist = tmplist + blist
            
                # restore selection
                self.boxbox.setCurrentValue(selection)
                            
            # if box is selected we, have to continue with positions
            if not self.boxbox.getCurrentValue() in coords[TN_BOX]:
                return
            
            # mark position label
            plist = self.allposlist.getItemList()
            missing = copy(orig_ids)

            pad = 0
            if plist:
                pad = len(plist[i][0])
            
            for i, bitem in enumerate(plist):
                if pitem[1] in orig_ids:
                    blist[i][0] = plist[i][0] + '*'
                    missing.remove(pitem[1])
            
                                                     
            # fill missing entries
            if missing:
                for p_id in missing:
                    # get data for new entry
                    name = storagemgr.getLabelString(TN_POSITION, 
                                                          p_id, 
                                                          info = nsStorage.LABEL_SHORT_POSITION, 
                                                          padding = pad) + '*'
                    plist.append([name, p_id])
                    
                plist.sort()

            if select:
                self.selectPositions(storagemgr, orig_ids)
            

    def setProperty(self, name, value):
        """\brief set a property for widget"""

        self.setValue(name + '_store', value)

    
    def getProperty(self, REQUEST, name):
        """\brief set a property for widget"""

        return REQUEST.get(self.prefix + self.name + name + '_store')

    
    def getValue(self, REQUEST, name):
        """\brief set a property for widget"""

        return REQUEST.get(self.prefix + self.name + name)


    def getContainer(self):
        """\brief set a property for widget"""

        return self.containerbox.getCurrentValue()


    def getBox(self):
        """\brief set a property for widget"""

        return self.boxbox.getCurrentValue()


    def getPositions(self):
        """\brief set a property for widget"""

        return self.selposlist.getValueList()

    
    def setValue(self, name, value):
        """\brief set a property for widget"""

        self.properties.hide()
        prop  = hgProperty( self.prefix + self.name + name,
                            str(value),
                            parent = self.properties )
        prop.show()         
        self.properties.show()

    
    def handleRequest(self, REQUEST, descr_dict, storagemgr):
        """\brief Get configuration from REQUEST and fill widget"""
        
        self.handleListButtons(REQUEST)

        if self.mode & MASK_SHOW:
            linklabel = storagemgr.getLink(TN_POSITION, descr_dict.get(self.name), parent = self)
            self.layout().addWidget(linklabel, 0, 0)
            return

        container = self.getValue(REQUEST, CONTAINER_SELECT)
                
        self.fillContainers(storagemgr, container)
        
        if container and container != 'NULL':
            self.boxbtn.setEnabled()
            # store selected container
            self.setProperty(CONTAINER_SELECT, container)
            
            # check if new container was selected   
            old_container = self.getProperty(REQUEST, CONTAINER_SELECT)
    
            box = None
            
            # there is only an active box if no new container was selected
            if old_container and old_container == container:
                box = self.getValue(REQUEST, BOX_SELECT)

            # fill boxes
            self.fillBoxes(container, storagemgr, box)
            
            if box and box != 'NULL':
                self.addbtn.setEnabled()
                # store selected box
                self.setProperty(BOX_SELECT, box)

                self.fillPositions(box, storagemgr)
            else:
                self.addbtn.setDisabled()
        else:
            self.addbtn.setDisabled()
            self.boxbtn.setDisabled()
            
        if self.mode & MASK_EDIT:
            self.appendOriginalPositions(REQUEST, descr_dict, storagemgr)
            
        #if old_box and old_box == box:
        positions = self.getValue(REQUEST, '')
        self.selectPositions(storagemgr, positions)
                    
        if len(self.selposlist.getItemList()) == 0:
            self.rembtn.setDisabled()
        else:
            self.rembtn.setEnabled()
        
        
    def handleListButtons(self, REQUEST):
        """\brief removes or adds values from/to REQUEST.<self.name>
                  according to button/REQUEST."""
        buttons = getPressedButton(REQUEST, DLG_FUNCTION)
        if len(buttons) != 1:
            return
        
        button = buttons[0]
        
        # multilist add
        if button == BTN_L_ADDITEM:
            self.handleSelectionAdd(REQUEST)

        # multilist remove
        elif button == BTN_L_REMOVE:
            self.handleSelectionRemove(REQUEST)

    def handleSelectionAdd(self, REQUEST):
        """\brief Handles the Add-Request
        """
        new = REQUEST.get('new' + self.prefix + self.name, [])
        if new:
            if not isinstance(new, ListType):
                new = [new]
            if not REQUEST.has_key(self.prefix + self.name):
                REQUEST[self.prefix + self.name] = []
            selected_list = REQUEST.get(self.prefix + self.name)
            if not isinstance(selected_list, ListType):
                selected_list = [selected_list]
            for autoid in new:
                #autoid = int(autoid)
                # normal value, put it in, if not present
                if not autoid in selected_list:
                    selected_list.append(autoid)
            
            REQUEST[self.prefix + self.name] = selected_list


    def handleSelectionRemove(self, REQUEST):
        """\brief Handles the Delete-Request
        """
        delete = REQUEST.get('del' + self.prefix + self.name, [])
        if delete:
            if not isinstance(delete, ListType):
                delete = [delete]
            selected_list = REQUEST.get(self.prefix + self.name, [])
            if not isinstance(selected_list, ListType):
                selected_list = [selected_list]
            for autoid in delete:
                if autoid in selected_list:
                    selected_list.remove(autoid)
            
            REQUEST[self.prefix + self.name] = selected_list
