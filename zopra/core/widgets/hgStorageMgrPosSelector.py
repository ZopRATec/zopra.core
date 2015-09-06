##############################################################################
#    Copyright (C) 2006 by Bernhard Voigt                                    #
#    bernhard.voigt@lrz.uni-muenchen.de                                      #
#                                                                            #
#    This program is free software; you can redistribute it and#or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
##############################################################################
# TODO: Move dialog to package

from types                           import IntType
from PyHtmlGUI.kernel.hgGridLayout   import hgGridLayout
from PyHtmlGUI.kernel.hgWidget       import hgWidget

from PyHtmlGUI.widgets.hgPushButton  import hgPushButton
from PyHtmlGUI.widgets.hgLabel       import hgLabel, hgProperty
from PyHtmlGUI.widgets.hgComboBox    import hgComboBox

from zopra.core.Storage.managers              import TN_CONTAINER, \
                                                        TN_BOX,       \
                                                        TN_POSITION

from zopra.core.Storage                       import nsStorage 

from zopra.core.elements.Buttons      import DLG_FUNCTION, \
                                                        BTN_HL_SELECT

#from zopra.core.Storage.StorageManager    import StorageManager

from zopra.core.CorePart  import MASK_ADD,       \
                                        MASK_EDIT,      \
                                        MASK_SEARCH,    \
                                        MASK_SHOW


CONTAINER_SELECT = '_conselect'
BOX_SELECT       = '_boxselect'
POSITION_SELECT  = '_posselect'
SELECT_TEXT      = 'Select'




SWDG_HORIZONTAL = 0x0000
SWDG_VERTICAL   = 0x0100
SWDG_OPTIONAL   = 0x0200


HORIZONTAL = SWDG_HORIZONTAL
VERTICAL   = SWDG_VERTICAL
OPTIONAL   = SWDG_OPTIONAL


class hgStorageMgrPosSelector(hgWidget):
    """\class hgStorageMgrPosSelector

    \brief The hgStorageMgrPosSelector widget provides a widget that allows to select positions in storage mgr.

    """
    _className = 'hgStorageMgrPosSelector'
    _classType = hgWidget._classType + [ _className ]
    
    
    def __init__(self, 
                 storagemgr, # for labels on init only, not stored
                 name     = None, 
                 parent   = None, 
                 prefix   = None,
                 manager  = None, # the manager class name
                 person   = None,
                 flags    = 0):
        """\brief Constructs a hgStorageMgrPosSelector widget."""
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
            self.mode       = MASK_EDIT
        elif flags & MASK_SEARCH:
            self.mode       = MASK_SEARCH
        elif flags & MASK_SHOW:
            self.mode       = MASK_SHOW
        
        if manager:
            self.parentmgr = manager

        # for stateless handling (old)
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = ''

        self.buildLayout()


    def buildLayout(self):
        """\brief builds layout for complex multilist."""
        
        row=0
        column=0
                
        # layout
        layout = hgGridLayout(self, 8, 8)

        if self.mode & MASK_SHOW:
            return

        # container part
        self.containerlab = hgLabel('Container:', parent=self)
        layout.addWidget( self.containerlab, row, column)
        if self.direction == HORIZONTAL:
            row += 1
        else:
            column += 1
        self.containerbox = hgComboBox(name = self.prefix + self.name + CONTAINER_SELECT, parent=self)
        layout.addWidget( self.containerbox, row, column )
        if self.direction == HORIZONTAL:
            row += 1
        else:
            column += 1
        
        self.containerbtn = hgPushButton(SELECT_TEXT, name = DLG_FUNCTION + BTN_HL_SELECT, parent=self)
        self.containerbtn.setToolTip('Select Container')
        layout.addWidget( self.containerbtn, row, column)
    
        if self.direction == HORIZONTAL:
            row     = 0
            layout.addWidget( hgLabel('&nbsp;', parent=self), row, column+1)
            column += 2
        else:
            row    += 1
            column  = 0


        # box part
        self.boxlab = hgLabel('Box:', parent=self)
        layout.addWidget( self.boxlab, row, column)
        if self.direction == HORIZONTAL:
            row += 1
        else:
            column += 1
        
        self.boxbox = hgComboBox(name = self.prefix + self.name + BOX_SELECT, parent=self)
        layout.addWidget( self.boxbox, row, column)
        if self.direction == HORIZONTAL:
            row += 1
        else:
            column += 1
        
        self.boxbtn = hgPushButton(SELECT_TEXT, name = DLG_FUNCTION + BTN_HL_SELECT, parent=self)
        self.boxbtn.setToolTip('Select Box')
        layout.addWidget( self.boxbtn, row, column)
    
        if self.direction == HORIZONTAL:
            row     = 0
            layout.addWidget( hgLabel('&nbsp;', parent=self), row, column+1)
            column += 2
        else:
            row    += 1
            column  = 0
        
        # position part
        self.boxlab = hgLabel('Position:', parent=self)
        layout.addWidget( self.boxlab, row, column)
        if self.direction == HORIZONTAL:
            row += 1
        else:
            column += 1
        
        self.positionbox = hgComboBox(name = self.prefix + self.name, parent=self)
        layout.addWidget( self.positionbox, row, column)
        
        if self.direction == HORIZONTAL:
            row += 1
        else:
            column += 1

        self.properties = hgWidget(parent = self)
        layout.addWidget(self.properties, row, column)




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
                # only boxes with content for search
                predicate = lambda set, total: set > 0
                
            else:
                # only boxes with space left for edit/add
                predicate = lambda set, total: set < total
            # parameter person = None -> get all boxes (boxowner ignored)
            boxes = storagemgr.getBoxesForContainer(container, predicate, None)
        
            for box in boxes:
                self.boxbox.insertItem(boxes[box]['name'], box)
            self.boxbox.sort()        

            # null value 
            if self.optional:
                self.boxbox.insertItem('--none--', 'NULL', 0)
            
            if self.mode & MASK_SEARCH:
                # no search value for search
                self.boxbox.insertItem('--nsv--', '', 0)
    
            if selected_id:
                self.boxbox.setCurrentValue(selected_id)


    def fillPositions(self, box, storagemgr, selected_id = None):
        """\brief Get data from storage manager and fill positions"""

        if storagemgr:
            if self.mode & MASK_SEARCH:
                predicate = lambda set: set
            else:
                predicate = lambda set: not set
            # parameter person = None -> get all positions (boxowner ignored)
            positions = storagemgr.getPositionsForBox(box, predicate, None)
        
            for position in positions:
                self.positionbox.insertItem(positions[position]['name'], position)
            self.positionbox.sort()
            
            if self.optional:
                self.positionbox.insertItem('-no-', 'NULL', 0)
            
            if self.mode & MASK_SEARCH:
                # no search value for search
                self.positionbox.insertItem('-nsv-', '', 0)
            
            if selected_id:
                # only empty positions are in the box (add/edit), if an empty pos was selected, it gets selected now
                # for full selected positions (on edit), the full pos is added via appendOriginalPosition later on
                self.positionbox.setCurrentValue(selected_id)


    def appendOriginalPosition(self, REQUEST, descr_dict, storagemgr):
        """\brief Insert current value into widget and mark it with *"""

        select = False
        # original position must have been property
        orig_id = self.getProperty(REQUEST, '')
        
        # if it was not set we have a new edit widget and descr_dict contains the original value
        if not orig_id:
            orig_id = descr_dict.get(self.name)
            select = True

        # check orig_id to be not "NULL"
        if orig_id == 'NULL':
            orig_id = None
        
        # original position must have content (if it exists), otherwise return
        if not orig_id or not storagemgr.isFull(TN_POSITION, orig_id):
            return
        
        # store original position as property
        self.setProperty('', orig_id)
        
        coords = storagemgr.getCoordsForPosition(orig_id)

        if select:
            self.setProperty(CONTAINER_SELECT, coords[TN_CONTAINER])
            self.setProperty(BOX_SELECT, coords[TN_BOX])
        
        citem = bitem = pitem = None
        
        # mark container label
        clist = self.containerbox.getItemList()
        
        for i, citem in enumerate(clist):
            if citem[1] == coords[TN_CONTAINER]:
                clist[i][0] = clist[i][0] + '*'                                            
                break

        # was not in list
        if not citem or citem[1] != coords[TN_CONTAINER]:
            # save selection
            selection = self.containerbox.getCurrentValue()

            # save special entries
            tmplist = []
            while len(clist) > 0 and not isinstance(clist[0][1], IntType):
                tmplist.append(clist.pop(0))
            # get data for new entry
            (set, total) = storagemgr.getFillState(TN_CONTAINER, coords[TN_CONTAINER])
        
            name = storagemgr.getLabelString(TN_CONTAINER, coords[TN_CONTAINER], 
                                                  info = nsStorage.LABEL_WITH_DESCRIPTION | nsStorage.LABEL_WITH_TYPE)
            name += ' (' + str(total-set) + '/' + str(total) + ')*'

            clist.append([name, coords[TN_CONTAINER]])
            clist.sort()
            clist = tmplist + clist
            
            # restore selection
            self.containerbox.setCurrentValue(selection)
            
        if select:
            if self.containerbox.getCurrentValue() != coords[TN_CONTAINER]:
                self.containerbox.setCurrentValue(coords[TN_CONTAINER])
                # we need new box entries
                self.fillBoxes(coords[TN_CONTAINER], storagemgr)
        
        # check if autoid for tower is selected we can enable selection button for boxes
        if isinstance(self.containerbox.getCurrentValue(), IntType):
            self.boxbtn.setEnabled()

        # if container is selected we have to continue with boxes
        if self.containerbox.getCurrentValue() != coords[TN_CONTAINER]:
            return
            
        # mark box label
        blist = self.boxbox.getItemList()

        for i, bitem in enumerate(blist):
            if bitem[1] == coords[TN_BOX]:
                blist[i][0] = blist[i][0] + '*'                                            
                break
        
        # was not in list
        if not bitem or bitem[1] != coords[TN_BOX]:

            # save selection
            selection = self.boxbox.getCurrentValue()
            # save special entries
            tmplist = []
            while len(blist) > 0 and not isinstance(blist[0][1], IntType):
                tmplist.append(blist.pop(0))
            # get data for new entry
            (set, total) = storagemgr.getFillState(TN_BOX, coords[TN_BOX])
        
            name = storagemgr.getLabelString(TN_BOX, coords[TN_BOX])
            name += ' (' + str(total-set) + '/' + str(total) + ')*'

            blist.append([name, coords[TN_CONTAINER]])
            blist.sort()
            blist = tmplist + blist
        
            # restore selection
            self.boxbox.setCurrentValue(selection)

        if select:
            if self.boxbox.getCurrentValue() != coords[TN_BOX]:
                self.boxbox.setCurrentValue(coords[TN_BOX])
                # we need new box entries
                self.fillPositions(coords[TN_BOX], storagemgr)

        # if box is selected we have to continue with boxes
        if self.boxbox.getCurrentValue() != coords[TN_BOX]:
            return
        
        # mark position label
        plist = self.positionbox.getItemList()
        
        pad = 0
        if plist:
            pad = len(plist[-1][0]) - 1
            
        for i, pitem in enumerate(plist):
            if pitem[1] == orig_id:
                plist[i][0] = plist[i][0] + '*'                                            
                break 
                                                 
        # was not in list
        if not pitem or pitem[1] != orig_id:
            selection = self.positionbox.getCurrentValue()
            name = storagemgr.getLabelString(TN_POSITION, 
                                                  orig_id, 
                                                  info = nsStorage.LABEL_SHORT_POSITION, 
                                                  padding = pad) + '*'

            
            self.positionbox.insertItem(name, orig_id)
            self.positionbox.sort()

            # restore selection
            # if there is a orig_id which was selected and is selected again,
            # the positionbox has no selection because the origid was not in before
            # in this case we have to set it here
            if not selection:
                selection = orig_id
            self.positionbox.setCurrentValue(selection)

        if select:
            if self.positionbox.getCurrentValue() != orig_id:
                self.positionbox.setCurrentValue(orig_id)


    def setProperty(self, name, value):
        """\brief set a property for widget"""
        # setting properties twice lead to lists in the request which in turn lead to inconsistencies
        # so we now check for the name and remove the first, when a second arrives
        key = self.prefix + self.name + name +'_store'
        self.properties.hide()
        
        if self.properties.child(key):
            # remove old property
            self.properties.removeChild(self.properties.child(key))
        
        prop  = hgProperty( key,
                            str(value),
                            parent = self.properties )
        prop.show()         
        self.properties.show()

    
    def getProperty(self, REQUEST, name):
        """\brief set a property for widget"""
        if REQUEST:
            return REQUEST.get(self.prefix + self.name + name + '_store')

    
    def getValue(self, REQUEST, name):
        """\brief set a property for widget"""
        if REQUEST:
            return REQUEST.get(self.prefix + self.name + name)

    
    def getContainer(self):
        """\brief set a property for widget"""

        return self.containerbox.getCurrentValue()


    def getBox(self):
        """\brief set a property for widget"""

        return self.boxbox.getCurrentValue()


    def getPosition(self):
        """\brief set a property for widget"""

        return self.positionbox.getCurrentValue()

    
    def getPosFromRequest(self, REQUEST):
        """\brief extracts position value from REQUEST"""
        return self.getValue(REQUEST, '')

        
    def handleRequest(self, REQUEST, descr_dict, storagemgr):
        """\brief Get configuration from REQUEST and fill widget"""
        
        if self.mode & MASK_SHOW:
            pos = descr_dict.get(self.name)
            if pos == 'NULL':
                pos = None
            linklabel = storagemgr.getLink(TN_POSITION, pos, parent = self)
            self.layout().addWidget(linklabel, 0, 0)
            return

        if REQUEST:
            container = self.getValue(REQUEST, CONTAINER_SELECT)
        else:
            container = None
        
        self.fillContainers(storagemgr, container)
        
        if container and container != 'NULL':
            self.boxbtn.setEnabled()
            # store selected container
            self.setProperty(CONTAINER_SELECT, container)
            
            # check if new container was selected   
            old_container = self.getProperty(REQUEST, CONTAINER_SELECT)

            box = None
            
            if old_container and old_container == container:
                box = self.getValue(REQUEST, BOX_SELECT)

            # fill boxes
            self.fillBoxes(container, storagemgr, box)
            
            if box and box != 'NULL':
                # store selected box
                self.setProperty(BOX_SELECT, box)

                # check if new box was selected   
                old_box = self.getValue(REQUEST, BOX_SELECT)
    
                position = None
            
                if old_box and old_box == box:
                    position = self.getValue(REQUEST, '')
                    
        
                self.fillPositions(box, storagemgr, position)

        else:
            self.boxbtn.setDisabled()

        if self.mode & MASK_EDIT:
            self.appendOriginalPosition(REQUEST, descr_dict, storagemgr)
