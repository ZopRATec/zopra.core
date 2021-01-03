from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from zopra.core.elements.Styles.Default import ssiB_BUTTON


# dialog prefixes
DLG_CUSTOM = "c_"  # to recognize custom fields
DLG_HIDDEN = "h_"  # to recognize hidden fields

# dialog button prefixes
DLG_FUNCTION = "f_"  # to recognize the pressed buttons
DLG_SWITCH = "s_"  # to recognize the switch buttons
DLG_INC = "i_"  # to recognize the increment buttons in the listview
DLG_DEC = "d_"  # to recognize the decrement buttons in the listview
DLG_ORDER = "o_"  # to recognize the order buttons

# button labels
BTN_L_ADD = "Add to Database"
BTN_L_UPDATE = "Update"
BTN_L_SEARCH = "Search"
BTN_L_DELETE = "Delete"
BTN_L_REFRESH = "Preview"
BTN_L_RESET = "Clear Fields"
BTN_L_NEXT = "Next Entries"
BTN_L_PREV = "Previous Entries"
BTN_L_GO = "Jump to Page"
BTN_L_FIRST = "First Page"
BTN_L_LAST = "Last Page"
BTN_L_PRINT = "Print"
BTN_L_EXPORT = "Export"
BTN_L_IMPORT = "Import"
BTN_L_ADDITEM = "Add Item"
BTN_L_REMOVE = "Remove Item"
BTN_L_MOVEDOWN = "Move Down"
BTN_L_EDIT = "Edit"
BTN_L_LOGIN = "Login"
BTN_L_RESET2 = "Reset"
BTN_L_CONTINUE = "Continue"
BTN_L_FILTER = "Apply Filter"
BTN_FRL_PREV = "frl_prev"
BTN_FRL_NEXT = "frl_next"
BTN_MULTIEDIT = "Multi Edit"
BTN_FREETEXT = "Freetext Search"
BTN_L_CLOSE = "Close"
BTN_L_SHOW_NUMBER = "Item Count"
BTN_L_SELECT_ALL = "All"

# Hierarchylistbuttons
BTN_HL_SELECT = "Select"
BTN_HL_REMOVE = "Remove"

# basketbuttons
BTN_BASKET_ACTIVATE = "Activate"
BTN_BASKET_DEACTIVATE = "Deactivate"
BTN_BASKET_REMOVE = "Remove Selected"
BTN_BASKET_REMOVEALL = "Remove All"
BTN_BASKET_ADD = "Add to Basket"
BTN_BASKET_POP = "Move from Basket"
BTN_BASKET_GET = "Copy from Basket"

# button definition
mpfAddButton = hgPushButton(BTN_L_ADD, DLG_FUNCTION + BTN_L_ADD)
mpfUpdateButton = hgPushButton(BTN_L_UPDATE, DLG_FUNCTION + BTN_L_UPDATE)
mpfSearchButton = hgPushButton(BTN_L_SEARCH, DLG_FUNCTION + BTN_L_SEARCH)
mpfDeleteButton = hgPushButton(BTN_L_DELETE, DLG_FUNCTION + BTN_L_DELETE)
mpfRefreshButton = hgPushButton(BTN_L_REFRESH, DLG_FUNCTION + BTN_L_REFRESH)
mpfResetButton = hgPushButton(BTN_L_RESET, DLG_FUNCTION + BTN_L_RESET)
mpfNextButton = hgPushButton(BTN_L_NEXT, DLG_FUNCTION + BTN_L_NEXT)
mpfPrevButton = hgPushButton(BTN_L_PREV, DLG_FUNCTION + BTN_L_PREV)
mpfGoButton = hgPushButton(BTN_L_GO, DLG_FUNCTION + BTN_L_GO)
mpfFirstButton = hgPushButton(BTN_L_FIRST, DLG_FUNCTION + BTN_L_FIRST)
mpfLastButton = hgPushButton(BTN_L_LAST, DLG_FUNCTION + BTN_L_LAST)
mpfPrintButton = hgPushButton(BTN_L_PRINT, DLG_FUNCTION + BTN_L_PRINT)
mpfExportButton = hgPushButton(BTN_L_EXPORT, DLG_FUNCTION + BTN_L_EXPORT)
mpfImportButton = hgPushButton(BTN_L_IMPORT, DLG_FUNCTION + BTN_L_IMPORT)
mpfAddItemButton = hgPushButton(BTN_L_ADDITEM, DLG_FUNCTION + BTN_L_ADDITEM)
mpfRemoveButton = hgPushButton(BTN_L_REMOVE, DLG_FUNCTION + BTN_L_REMOVE)
mpfMoveDownButton = hgPushButton(BTN_L_MOVEDOWN, DLG_FUNCTION + BTN_L_MOVEDOWN)
mpfEditButton = hgPushButton(BTN_L_EDIT, DLG_FUNCTION + BTN_L_EDIT)
mpfLoginButton = hgPushButton(BTN_L_LOGIN, DLG_FUNCTION + BTN_L_LOGIN)
mpfReset2Button = hgPushButton(BTN_L_RESET2, DLG_FUNCTION + BTN_L_RESET2)
mpfContinueButton = hgPushButton(BTN_L_CONTINUE, DLG_FUNCTION + BTN_L_CONTINUE)
mpfFreetextButton = hgPushButton(BTN_FREETEXT, DLG_FUNCTION + BTN_FREETEXT)
mpfFilterButton = hgPushButton(BTN_L_FILTER, DLG_FUNCTION + BTN_L_FILTER)
mpfCloseButton = hgPushButton(BTN_L_CLOSE, DLG_FUNCTION + BTN_L_CLOSE)
mpfNumberButton = hgPushButton(BTN_L_SHOW_NUMBER, DLG_FUNCTION + BTN_L_SHOW_NUMBER)
mpfSelectAllButton = hgPushButton(BTN_L_SELECT_ALL, DLG_FUNCTION + BTN_L_SELECT_ALL)

# hierarchylistbuttons
mpfSelectHLButton = hgPushButton(BTN_HL_SELECT, DLG_FUNCTION + BTN_HL_SELECT)
mpfRemoveHLButton = hgPushButton(BTN_HL_REMOVE, DLG_FUNCTION + BTN_HL_REMOVE)

# basketbuttons
mpfBasketActivateButton = hgPushButton(
    BTN_BASKET_ACTIVATE, DLG_FUNCTION + BTN_BASKET_ACTIVATE
)
mpfBasketDeactivateButton = hgPushButton(
    BTN_BASKET_DEACTIVATE, DLG_FUNCTION + BTN_BASKET_DEACTIVATE
)
mpfBasketRemoveButton = hgPushButton(
    BTN_BASKET_REMOVE, DLG_FUNCTION + BTN_BASKET_REMOVE
)
mpfBasketRemoveAllButton = hgPushButton(
    BTN_BASKET_REMOVEALL, DLG_FUNCTION + BTN_BASKET_REMOVEALL
)
mpfBasketAddButton = hgPushButton(BTN_BASKET_ADD, DLG_FUNCTION + BTN_BASKET_ADD)
mpfBasketPopButton = hgPushButton(BTN_BASKET_POP, DLG_FUNCTION + BTN_BASKET_POP)
mpfBasketGetButton = hgPushButton(BTN_BASKET_GET, DLG_FUNCTION + BTN_BASKET_GET)

# width style for basket buttons
mpfBasketActivateButton._styleSheet.getSsiName(ssiB_BUTTON)
mpfBasketDeactivateButton._styleSheet.getSsiName(ssiB_BUTTON)
mpfBasketRemoveButton._styleSheet.getSsiName(ssiB_BUTTON)
mpfBasketRemoveAllButton._styleSheet.getSsiName(ssiB_BUTTON)
# test
mpfBasketActivateButton.setSsiName(".basket_button")
mpfBasketDeactivateButton.setSsiName(".basket_button")
mpfBasketRemoveButton.setSsiName(".basket_button")
mpfBasketRemoveAllButton.setSsiName(".basket_button")

# Reset Button
mpfResetButton.setFunction(hgPushButton.PB_RESET)

# button tooltips
mpfAddButton.setToolTip("Add information to the database")
mpfUpdateButton.setToolTip("Update information in the database")
mpfSearchButton.setToolTip("Search for information in the database")
mpfDeleteButton.setToolTip("Delete entries from the database")
mpfRefreshButton.setToolTip("Update the view and fill in external information")
mpfResetButton.setToolTip("Reset the entry to database values")
mpfNextButton.setToolTip("Next")
mpfPrevButton.setToolTip("Previous")
mpfExportButton.setToolTip("Exports a specified table")
mpfImportButton.setToolTip("Imports file into specified table")
mpfAddItemButton.setToolTip("Adds marked items to selection list")
mpfRemoveButton.setToolTip("Removes marked item from selection list")
mpfMoveDownButton.setToolTip("Moves entries down to the selected position")
mpfEditButton.setToolTip("Edit the entry")
mpfLoginButton.setToolTip("Login")
mpfReset2Button.setToolTip("Reset")
mpfContinueButton.setToolTip("Proceed to next step")
mpfFreetextButton.setToolTip("Refresh List Values with Freetext Search Result")
mpfFilterButton.setToolTip("Apply filter text to ComboBox")
mpfNumberButton.setToolTip("Set number of items to show on one page")
mpfSelectAllButton.setToolTip("Select all entries.")

mpfBasketActivateButton.setToolTip("Switch selected entries to active state")
mpfBasketDeactivateButton.setToolTip("Switch selected entries to inactive state")
mpfBasketRemoveButton.setToolTip("Remove selected entries from basket")
mpfBasketRemoveAllButton.setToolTip("Remove all entries from basket")
mpfBasketAddButton.setToolTip("Add current or selected")
mpfBasketPopButton.setToolTip("Copy entry from basket to main window")
mpfBasketGetButton.setToolTip("Copy entries from basket to main window")

mpfSelectHLButton.setToolTip("Expand/Add list entry")
mpfRemoveHLButton.setToolTip("Remove list entry")


def getPressedButton(REQUEST=None, buttonType=DLG_FUNCTION):
    """Filteres the pressed button out of the REQUEST Handler.

    Assumtions:
    - 2 characters as prefix
    - more than one button with the same name is present, than they have the
      same meaning and so only one can be presented to the outside.

    :return: button name list
    """
    button_dict = {}
    if REQUEST:
        length = len(buttonType)
        # this is essential: after deleting something from REQUEST.form, it might still be in REQUEST.keys()
        # so we iterate REQUEST.form
        for key in REQUEST.form:
            if key[0:length] == buttonType and key[length:] not in button_dict:
                # FIXME: find a better way to handle img buttons
                if key[-2:] == ".x":
                    del REQUEST.form[key]
                    key = key[:-2]
                    if key not in REQUEST:
                        # add the real one
                        REQUEST.form[key] = ""
                elif key[-2:] == ".y":
                    del REQUEST.form[key]
                    continue

                button_dict[key[length:]] = None

    return button_dict.keys()


def getSpecialField(REQUEST=None, fieldType=DLG_CUSTOM):
    """Filteres the fields with fieldType prefix out of the REQUEST Handler.

    Assumtions:
    - x characters as prefix
    - unique field names

    :return: fieldname->value - dictionary
    """
    field_dict = {}
    if REQUEST:
        length = len(fieldType)
        for key in REQUEST.form:
            if key[0:length] == fieldType and (key[length:] not in field_dict):

                field_dict[key[length:]] = REQUEST.form[key]
    return field_dict
