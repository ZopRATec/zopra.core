dialogs is the package for special Core and Base Dialogs as well as dialog Handling

Recent Changes:
-

ToDo:
- unify with ZMOMDialogs

Contents:

dlgDelete: 
	Delete one entry (don't ask why this is extra and not using dlgMultiDelete with one entry, I do not know)
	In use in ZopRA Core.
	
dlgMoveListValue:
	Intended for copy actions between Lists.
	Never finished, never tested, not in use.
	
dlgMultiDelete:
	Delete multiple entries at once.
	In use in ZopRA Core.

dlgMultiEdit:
    Edit multiple entries at once.
    In use in ZopRA Core, see getTableEntryListHtml -> multiedit part (depends on additional manager functions)

dlgNOCBase:
	Base Dialog for next-okay-cancel[-undo] - dialogs (two-step-dialogs)
	Not used right now, but usable via subclassing.
	
dlgOCBase:
    Base Dialog for okay-cancel[-undo] - dialogs (one-step-dialogs)
    Used by ???
    
dlgSearchResult:
	??? -> maybe intended to become the getTableEntryListHtml replacement when we go all-dialog. Unfinished.
	Not in use.
	
dlgTableEntry:
	???
	Not in use.
	
dlgTableView:
	??? -> maybe intended to become the showForm replacement when we go all-dialog. Unfinished.
	Not in use.

dlgTreeEdit:
	All-in-one edit dialog for hierarchy Lists
	Used by ZMOMPlantManager for phenotype hierarchylist.
	
guiHandler:
	The now one and only source for form processing and widget handling.
	Used by all dialogs as base class.
	
hgEntryList:
	Widget for displaying entries? No idea. Unfinished.
	Not used.
