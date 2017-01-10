############################################################################
#    Copyright (C) 2007 by Bernhard Voigt                                  #
#    bernhard.voigt@lrz.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
#\file dlgMngFolder.py
__revision__ = '0.1'

from types                              import StringType

from PyHtmlGUI                          import hg

from PyHtmlGUI.dialogs.hgDialog         import hgDialog

from PyHtmlGUI.kernel.hgGridLayout      import hgGridLayout
from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.kernel.hgWidget          import hgWidget

from PyHtmlGUI.kernel.hgSizePolicy      import hgSizePolicy

from PyHtmlGUI.widgets.hgGroupBox       import hgGroupBox
from PyHtmlGUI.widgets.hgLabel          import hgLabel
from PyHtmlGUI.widgets.hgHBox           import hgHBox
from PyHtmlGUI.widgets.hgLineEdit       import hgLineEdit
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.elements.Styles.Default   import ssiDLG_LABEL

from zopra.core.constants         import TCN_AUTOID
                                               
from zopra.core.dialogs.guiHandler   import guiHandler

from zopra.core.secGUIPermission     import secGUIPermission

from zopra.core.tools.managers import TN_FOLDER,      \
                                                    TN_LOCAL,       \
                                                    TCN_OWNER,      \
                                                    TCN_FOLDERNAME, \
                                                    TCN_SORTID,     \
                                                    TCN_FOLDER,     \
                                                    IMG_MOVEUP,     \
                                                    IMG_MOVEDOWN,   \
                                                    IMG_DELETE



MAILCOUNT = 'mailcount'


class dlgMngFolderPrivate:
    """\class hgWizardPrivate"""

    def __init__(self):
        """\brief Constructs the private part of the hgWizard."""
        self.databox       = None
        self.msgbox        = None
        self.btnbox        = None
        self.msg_count     = None
        self.closeButton   = None
        self.helpButton    = None
        self.closeAccel    = None
        self.helpAccel     = None


class dlgMngFolder( hgDialog, guiHandler ):
    """\class dlgMngFolder

    \brief Folder management for Messaging Manager.
    """
    _className = 'dlgMngFolder'
    _classType = hgDialog._classType + [_className]

    # introduced new return code 'Applied' 
    # since it is not recognized outside this class it is for internal use only
    Created   = 3
    Renamed   = 4
    Deleted   = 5
    MovedUp   = 6
    MovedDown = 7
    
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a new edit tube dialog."""
        hgDialog.__init__( self )
        guiHandler.__init__( self )

        self.caption             = 'Manage Folders'

        # dlg private data
        self.data = dlgMngFolderPrivate()

        # init values
        self.resetData()

        self.muser = manager.getCurrentMUser()
        folder_dicts = manager.tableHandler[TN_FOLDER].getEntries(self.muser[TCN_AUTOID], TCN_OWNER, order = TCN_SORTID)

        for dict in folder_dicts:
            self.sort_ids.append(dict[TCN_SORTID])
            self.sid2folder[dict[TCN_SORTID]] = dict
            self.aid2folder[dict[TCN_AUTOID]] = dict
            
            dict[MAILCOUNT] = manager.tableHandler[TN_LOCAL].getRowCount( { TCN_FOLDER: dict[TCN_AUTOID] } )

        
        self.data.msg_count       = 0

        # create in nice tab order
        self.data.closeButton     = hgPushButton( parent = self, name = 'close'   )
        self.data.helpButton      = hgPushButton( parent = self, name = 'help'    )

        self.data.closeButton.setText  ( '&Close'        )
        self.data.helpButton.setText   ( '&Help'         )

        # connect the signals to the slots
        self.connect( self.data.helpButton.clicked,    self.help    )
        self.connect( self.data.closeButton.clicked,   self.reject  )

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

        # new folder
        label = hgLabel('New Folder:', parent = widget)
        label.setToolTip('Create a new folder') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget(label, r, 0)

        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)

        self.create_edit = hgLineEdit(name = 'folder_name', parent = widget)
        self.create_edit.setSize(25)
        self.connect( self.create_edit.textChanged,    self.setFolderName  )
        wlay.addWidget( self.create_edit, r, 2)

        wlay.addWidget( hgLabel('&nbsp;', parent = widget), r, 3)

        create_btn = hgPushButton(text = 'Create',  parent = widget, name = 'create_folder' )
        self.connect( create_btn.clicked,    self.createFolder  )
        wlay.addWidget( create_btn, r, 4)

        r += 1

        wlay.addWidget( hgLabel('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', parent = widget), r, 1)
        r += 1

        # create folders
        label = hgLabel('Current Folder:', parent = widget)
        label.setToolTip('List of current folders.') 
        label.setSsiName( ssiDLG_LABEL.name() )
        wlay.addWidget(label, r, 0, hg.AlignTop)

        self.folderbox = hgTable(parent = widget)
        wlay.addMultiCellWidget( self.folderbox, r, r, 2,  5)
        self.displayFolders(manager)
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

        return widget
    

    def displayFolders(self, manager):
        """\brief Get the button layout."""
        # NOTE: uncommented line produces unexpected results
        #self.curimodbox.emptyTable()
        tab = hgTable(spacing = '0', parent = self.folderbox)
        self.folderbox[0, 0] = tab
        self.delbtn2sid      = {}
        self.upbtn2sid       = {}
        self.downbtn2sid     = {}
        self.sid2edit        = {}
        
        # TODO: delete old buttons?
        i = -1
        for i, sid in enumerate(self.sort_ids):
            dict = self.sid2folder[sid]
            
            
            fname = hgLineEdit(parent = tab)
            fname.setText(dict[TCN_FOLDERNAME])
            fname.setSize(15)
            tab[i, 0] = fname
            
            self.sid2edit[sid] = fname
            
            if dict[MAILCOUNT] == 1:
                tab[i, 1] = hgLabel(' (' + str(dict[MAILCOUNT]) + ' mail)', parent = tab)
            else:
                tab[i, 1] = hgLabel(' (' + str(dict[MAILCOUNT]) + ' mails)', parent = tab)
            tab[i, 2] = hgLabel('&nbsp;', parent = tab)

            if i != len(self.sort_ids) - 1:
                name = 'down_' + str(sid)
                icon = manager.iconHandler.get(IMG_MOVEDOWN, path=True).getIconDict()
                btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
                btn.setToolTip('Move Folder down')
                tab[i, 3] = btn
                self.connect( btn.clickedButton,    self.moveFolderDown  )
                self.downbtn2sid[name] = sid
            else:
                tab[i, 3] = hgLabel('&nbsp;', parent = tab)
            if i != 0:
                name = 'up_' + str(sid)
                icon = manager.iconHandler.get(IMG_MOVEUP, path=True).getIconDict()
                btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
                btn.setToolTip('Move Folder up')
                tab[i, 4] = btn
                self.connect( btn.clickedButton,    self.moveFolderUp  )
                self.upbtn2sid[name] = sid
            else:
                tab[i, 4] = hgLabel('&nbsp;', parent = tab)
            tab[i, 5] = hgLabel('&nbsp;', parent = tab)
            if dict[MAILCOUNT] == 0:
                name = 'del_' + str(sid)
                icon = manager.iconHandler.get(IMG_DELETE, path=True).getIconDict()
                btn = hgPushButton(text = name, name = name, icon = icon, parent = tab)
                btn.setToolTip('Delete Folder')
                tab[i, 6] = btn
                self.connect( btn.clickedButton,    self.deleteFolder  )
                self.delbtn2sid[name] = sid
            else:
                tab[i, 6] = hgLabel('&nbsp;', parent = tab)

            if not i % 2:
                for c in xrange(1, 7):
                    tab.setCellBackgroundColor(i, c, '#E0E0DA')

        if i > -1:
            rename_btn = hgPushButton(text = 'Rename',  parent = tab, name = 'rename_folder' )
            self.connect( rename_btn.clicked,    self.renameFolder  )
            tab[i+1, 0] = rename_btn

        
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
    def setFolderName(self, text):
        """\brief Sets the name for the new folder."""

        self.foldername = text


    def getDataDict(self, autoid):
        """\brief Get entry dict from dialog data."""
                
        return self.aid2folder.get(autoid, {})
        
        
    def resetData(self):
        """"""
        self.sort_ids   = []
        self.sid2folder = {}
        self.aid2folder = {}
        self.foldername = ''
        self.btnname    = None
        
        
    # dialog handling
    def execDlg(self, manager, REQUEST):
        """\brief Executes the dialog functions."""

        # check access rights
        if manager:
            manager.checkGUIPermission(TN_FOLDER, secGUIPermission.SC_EDIT)

        # process events
        guiHandler.execDlg(self, manager, REQUEST)

        if self.result() == self.Created:
            self.performCreateFolder(manager)
            self.setResult(self.Running)
        elif self.result() == self.Renamed:
            self.performRenameFolder(manager)
            self.setResult(self.Running)
        elif self.result() == self.Deleted:
            self.performDeleteFolder(manager)
            self.setResult(self.Running)
        elif self.result() == self.MovedUp:
            self.performMoveUp(manager)
            self.setResult(self.Running)
        elif self.result() == self.MovedDown:
            self.performMoveDown(manager)
            self.setResult(self.Running)
        
        
    # button callbacks   
    def createFolder(self):
        """\brief Creates a folder with the current foldername."""

        if self.foldername:
            self.setResult(self.Created)
        else:
            self.addMessage('You need to specify a folder name.')            


    def renameFolder(self):
        """\brief Renames all folders with changed names."""

        self.setResult(self.Renamed)


    def deleteFolder(self, btnname):
        """\brief Renames all folders with changed names."""

        self.btnname = btnname
        self.setResult(self.Deleted)

    
    def moveFolderUp(self, btnname):
        """\brief Renames all folders with changed names."""

        self.btnname = btnname
        self.setResult(self.MovedUp)

    
    def moveFolderDown(self, btnname):
        """\brief Renames all folders with changed names."""

        self.btnname = btnname
        self.setResult(self.MovedDown)

    
    def help(self):
        """"""
        self.resetMessages()
        self.addMessage('Manage folders for Messaging manager')
        self.addMessage('&nbsp;')
        self.addMessage('Add folder by entering a new foldername and pressing \'Create\'')
        self.addMessage('Change sorting by klicking the up and down arrows of the folders.')
        self.addMessage('Delete folder by klicking the red cross.')
        self.addMessage('Rename Folder by entering a new name for folder and pressing \'Rename\'')


    def performRejected(self, manager):
        """\reimp"""
        self.resetMessages()


    def performCreateFolder(self, manager):
        """\reimp"""
        self.resetMessages()
                    
        if self.foldername in manager.SYSTEM_FOLDER:
            self.addMessage('\'%s\' is a system folder. Rename aborted.' % self.foldername)
            return

        # check for existing name
        for aid in self.aid2folder:
            if self.foldername == self.aid2folder[aid][TCN_FOLDERNAME]:
                self.addMessage('Folder with name %s already present. Please select another name.' % self.foldername)
                return
        
        # get next sid
        if self.sort_ids:
            sid = self.sort_ids[-1] + 1
        else:
            sid = 1
        
        # create new folder
        folder_dict = { TCN_FOLDERNAME: self.foldername,
                        TCN_SORTID:     sid,
                        TCN_OWNER:      self.muser[TCN_AUTOID]
                      }
        
        aid = manager.tableHandler[TN_FOLDER].addEntry(folder_dict)
        
        if not aid:
            manager.displayError('An error occured while creating folder', 
                                 'Database error')
        
        folder_dict[TCN_AUTOID]  = aid
        folder_dict[MAILCOUNT]   = 0 
        
        # update data
        self.sort_ids.append(sid)
        self.sid2folder[sid] = folder_dict
        self.aid2folder[aid] = folder_dict

        self.addMessage('Created folder %s.' % self.foldername)
        
        self.create_edit.setText('')
        
        self.displayFolders(manager)

        
    def performRenameFolder(self, manager):
        """\reimp"""
        self.resetMessages()

        for i, sid in enumerate(self.sort_ids):
            fname = self.sid2edit[sid].getText()
            
            if not fname:
                self.addMessage('You need to specify a folder name.')
                return
                
            if fname in manager.SYSTEM_FOLDER:
                self.addMessage('\'%s\' is a system folder. Rename aborted.' % fname)
                return
            
            # check against all other names
            for sid2 in self.sort_ids[i+1:]:
                if fname == self.sid2edit[sid2].getText():
                    self.addMessage('Folder name %s specified more than once. Please select another name.' % fname)
                    return
                    
                    
        for sid in self.sort_ids:
            fname  = self.sid2edit[sid].getText()
            curname = self.sid2folder[sid][TCN_FOLDERNAME]
            if fname != curname:
                self.sid2folder[sid][TCN_FOLDERNAME] = fname
                if not manager.tableHandler[TN_FOLDER].updateEntry(self.sid2folder[sid], self.sid2folder[sid][TCN_AUTOID]):
                    manager.displayError('An error occured while updating folder names', 
                                         'Database error')
                self.addMessage('Renamed folder \'%s\' to \'%s\'' % (curname, fname))
                    
            
    def performDeleteFolder(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.delbtn2sid[self.btnname]:
            return
        
        sid = self.delbtn2sid[self.btnname]
        
        folder = self.sid2folder[sid]
        
        # delete folder
        manager.deleteEntries(TN_FOLDER, [ folder[TCN_AUTOID] ])
                    
        # remove entry from local data
        del self.aid2folder[folder[TCN_AUTOID]]
        del self.sid2folder[sid]
        self.sort_ids.remove(sid)
        self.btnname = None
        
        self.displayFolders(manager)
            
                    
    def performMoveUp(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.upbtn2sid[self.btnname]:
            return
        
        sid = self.upbtn2sid[self.btnname]
        
        self.performMove(manager, sid, up=True)
                            
 
    def performMoveDown(self, manager):
        """\reimp"""
        self.resetMessages()
        
        if not self.btnname or not self.downbtn2sid[self.btnname]:
            return
        
        sid = self.downbtn2sid[self.btnname]
        
        self.performMove(manager, sid, up=False)
                    
                    
    def performMove(self, manager, sid, up = True):
        """\reimp"""
        folder = self.sid2folder[sid]

        sid2 = 0
        for i, current_sid in enumerate(self.sort_ids):
            if current_sid == sid:
                if not up and i+1 < len(self.sort_ids):
                    sid2 = self.sort_ids[i+1]
                if up and i > 0:
                    sid2 = self.sort_ids[i-1]
                break
                
        if not sid2:
            return
        
        folder2 = self.sid2folder[sid2]
        
        # perform exchange
        folder[TCN_SORTID], folder2[TCN_SORTID] = folder2[TCN_SORTID], folder[TCN_SORTID]
        
        
        if not manager.tableHandler[TN_FOLDER].updateEntry(folder, folder[TCN_AUTOID]):
            manager.displayError('An error occured while moving folder', 
                                 'Database error')
        if not manager.tableHandler[TN_FOLDER].updateEntry(folder2, folder2[TCN_AUTOID]):
            manager.displayError('An error occured while moving folder', 
                                 'Database error')
        
        self.sid2folder[sid], self.sid2folder[sid2] = self.sid2folder[sid2], self.sid2folder[sid]
        
        # reset btnname
        self.btnname = None
            
        self.displayFolders(manager)
 
                    
