from builtins import object

import PyHtmlGUI


class ZC(object):

    # list widget constants for handling
    FCB_DEFAULT_FILTER_TEXT = "<Filter Text>"
    FILTER_EDIT = "filter_"

    # role names
    ROLE_USER = "ZopRAAuthor"
    ROLE_REVIEWER = "ZopRAReviewer"
    ROLE_ADMIN = "ZopRAAdmin"

    # edit_tracking
    TCN_AUTOID = "autoid"
    TCN_CREATOR = "creator"
    TCN_DATE = "entrydate"
    TCN_EDITOR = "editor"
    TCN_EDATE = "changedate"
    TCN_OWNER = "owner"

    # list widget constants for handling
    VALUE = "value"
    RANK = "rank"
    SHOW = "show"
    NOTES = "notes"

    WIDGET_CONFIG = "widget_config"

    #
    # Globally interesting Manager Name Constants
    #
    ZM_PM = "ZopRAProduct"
    ZM_CM = "ContactManager"
    ZM_IM = "FileManager"
    ZM_PNM = "PrintManager"
    ZM_MM = "MessagingManager"
    ZM_CTM = "ContentManager"
    ZM_TEST = "TestManager"
    ZM_DEBUG = "DebugInfoManager"
    ZM_SCM = "SecurityManager"
    ZM_MBM = "MessageBoard"

    # Mask Types
    MASK_ADD = 0x0001
    MASK_ADMIN = 0x0002
    MASK_EDIT = 0x0004
    MASK_SEARCH = 0x0008
    MASK_SHOW = 0x0010
    MASK_HEAD = 0x0020
    MASK_REDIT = 0x0040

    # Database Column Types
    COL_TEXT = "TEXT"
    COL_DATE = "DATE"
    COL_INT4 = "INT4"
    COL_INT8 = "INT8"
    COL_FLOAT = "FLOAT"
    COL_SEQ = "SEQ"
    COL_URL = "URL"
    COL_CURRENCY = "NUMERIC(10,2)"
    COL_LOOKUPLIST = "singlelist"

    # ZopRA Column Types
    ZCOL_STRING = "string"
    ZCOL_MEMO = "memo"
    ZCOL_INT = "int"
    ZCOL_LONG = "long"
    ZCOL_SLIST = "singlelist"
    ZCOL_MLIST = "multilist"
    ZCOL_HLIST = "hierarchylist"
    ZCOL_DATE = "date"
    ZCOL_FLOAT = "float"
    ZCOL_BOOL = "bool"
    ZCOL_CURR = "currency"

    ZCOL_LISTS = [ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST]
    ZCOL_MLISTS = [ZCOL_MLIST, ZCOL_HLIST]

    #
    # Table Constants
    #
    COL_TYPE = "TYPE"
    COL_LABEL = "LABEL"
    COL_INVIS = "INVIS"
    COL_REFERENCE = "REFERENCE"
    COL_DEFAULT = "DEFAULT"
    COL_PRIMARY_KEY = "PRIMARY KEY"

    #
    # some dialog handling constants (legacy)
    #
    DLG_NEW = 1
    DLG_SHOW = 2
    DLG_EDIT = 3
    DLG_SEARCH = 4
    DLG_DELETE = 5
    DLG_IMPORT = 6
    DLG_LIST = 7

    DLG_TYPES = [DLG_SHOW, DLG_EDIT, DLG_NEW, DLG_DELETE, DLG_IMPORT, DLG_LIST]

    # names of core dialogs (legacy)
    DLG_ALLIMPORT = "dlgImport"
    DLG_ALLDELETE = "dlgDelete"
    DLG_MULDELETE = "dlgMultiDelete"
    DLG_TREEEDIT = "dlgTreeEdit"
    DLG_MULTIEDIT = "dlgMultiEdit"

    DLG_CORE = [
        DLG_ALLIMPORT,
        DLG_ALLDELETE,
        DLG_MULDELETE,
        DLG_TREEEDIT,
        DLG_MULTIEDIT,
    ]

    #
    # Security Flags
    #
    SC_LREAD = 1
    SC_WRITE = 2
    SC_READ = 4
    SC_DEL = 8
    SC_L_ALL = [SC_LREAD, SC_WRITE, SC_READ, SC_DEL]

    _edit_tracking_cols = {
        TCN_CREATOR: {COL_TYPE: "singlelist", COL_LABEL: u"Creator"},
        TCN_DATE: {COL_TYPE: "date", COL_LABEL: u"Entry Date", COL_DEFAULT: "now()"},
        TCN_EDITOR: {COL_TYPE: "singlelist", COL_LABEL: u"Last edited by"},
        TCN_EDATE: {
            COL_TYPE: "date",
            COL_LABEL: u"Last edited on",
            COL_DEFAULT: "now()",
        },
        TCN_OWNER: {COL_TYPE: "singlelist", COL_LABEL: u"Owner"},
    }

    #
    # Icons for sort buttons for search result page
    #
    IMG_SORTDEACT = u"Field sorting deactivated"
    IMG_SORTNONE = u"Field not sorted"
    IMG_SORTASC = u"Field sorted ascending"
    IMG_SORTDESC = u"Field sorted descending"

    SORTING_FILES = {
        IMG_SORTDEACT: "sort_da_20.png",
        IMG_SORTNONE: "sort_no_20.png",
        IMG_SORTASC: "sort_up_20.png",
        IMG_SORTDESC: "sort_down_20.png",
    }

    #
    # Icons for page buttons for search result page
    #
    IMG_PAGEFWD = u"Page Forward"
    IMG_PAGEBWD = u"Page Backward"
    IMG_PAGEFIRST = u"First Page"
    IMG_PAGELAST = u"Last Page"
    IMG_PAGEFWD_DEACT = u"Page Forward (inactive)"
    IMG_PAGEBWD_DEACT = u"Page Backward (inactive)"
    IMG_PAGEFIRST_DEACT = u"First Page (inactive)"
    IMG_PAGELAST_DEACT = u"Last Page (inactive)"

    LISTING_FILES = {
        IMG_PAGEFWD: "page_fwd.png",
        IMG_PAGEBWD: "page_bwd.png",
        IMG_PAGEFIRST: "page_first.png",
        IMG_PAGELAST: "page_last.png",
        IMG_PAGEFWD_DEACT: "page_fwd_deact.png",
        IMG_PAGEBWD_DEACT: "page_bwd_deact.png",
        IMG_PAGEFIRST_DEACT: "page_first_deact.png",
        IMG_PAGELAST_DEACT: "page_last_deact.png",
    }

    #
    # Icons for entry handling buttons
    #
    IMG_CREATE = u"Create new"
    IMG_LIST = u"List"
    IMG_SEARCH = u"Search"
    IMG_IMPORT = u"Import"
    IMG_EXPORT = u"Export"
    IMG_INFO = u"Info"
    IMG_DBADD = u"Add to Database"
    IMG_SHOW_NEXT = u"Show next"
    IMG_SHOW_PREV = u"Show previous"
    IMG_SHOW_NEXT_DEACT = u"Show next disabled"
    IMG_SHOW_PREV_DEACT = u"Show previous disabled"
    IMG_SHOW = u"Show"
    IMG_EDIT = u"Edit"

    HANDLING_FILES = {
        IMG_CREATE: "ziCreate.png",
        IMG_LIST: "ziList.png",
        IMG_SEARCH: "ziSearch.png",
        IMG_IMPORT: "ziImport.png",
        IMG_EXPORT: "ziExport.png",
        IMG_INFO: "ziInfo.png",
        IMG_DBADD: "ziDBAdd.png",
        IMG_SHOW_NEXT: "ziNext.png",
        IMG_SHOW_PREV: "ziPrev.png",
        IMG_SHOW_NEXT_DEACT: "ziNextDeact.png",
        IMG_SHOW_PREV_DEACT: "ziPrevDeact.png",
        IMG_SHOW: "ziShow.png",
        IMG_EDIT: "ziEdit.png",
    }

    #
    # tooltips
    #
    TIP_CREATE = u"Create new %s entry."
    TIP_LIST = u"List all %s entries."
    TIP_SEARCH = u"Search for %s entries."
    TIP_IMPORT = u"Import data into the database."
    TIP_EXPORT = u"Export data from the database."
    TIP_INFO = u"Get %s info."
    TIP_DBADD = u"Add the %s to the database."
    TIP_SHOW_NEXT = u"Show next %s entry."
    TIP_SHOW_PREV = u"Show previous %s entry."
    TIP_SHOW = u"Show %s entry details."
    TIP_EDIT = u"Edit %s entry."

    TOOLTIP_DICT = {
        IMG_CREATE: TIP_CREATE,
        IMG_LIST: TIP_LIST,
        IMG_SEARCH: TIP_SEARCH,
        IMG_IMPORT: TIP_IMPORT,
        IMG_EXPORT: TIP_EXPORT,
        IMG_INFO: TIP_INFO,
        IMG_DBADD: TIP_DBADD,
        IMG_SHOW_NEXT: TIP_SHOW_NEXT,
        IMG_SHOW_PREV: TIP_SHOW_PREV,
        IMG_SHOW: TIP_SHOW,
        IMG_EDIT: TIP_EDIT,
    }

    #
    # some button handling constants (have to be distinct from dlg constants)
    #

    ACTION_SEARCH = "search"
    ACTION_LIST = "list"
    ACTION_CREATE = "create"
    ACTION_IMPORT = "import"
    ACTION_EXPORT = "export"
    ACTION_SHOW_NEXT = "shownext"
    ACTION_SHOW_PREV = "showprev"
    ACTION_INFO = "info"
    ACTION_DBADD = "dbadd"
    ACTION_SHOW = "show"
    ACTION_EDIT = "edit"

    ACTION_DICT = {
        ACTION_SEARCH: IMG_SEARCH,
        ACTION_LIST: IMG_LIST,
        ACTION_CREATE: IMG_CREATE,
        ACTION_IMPORT: IMG_IMPORT,
        ACTION_EXPORT: IMG_EXPORT,
        ACTION_DBADD: IMG_DBADD,
        ACTION_INFO: IMG_INFO,
        ACTION_SHOW_NEXT: IMG_SHOW_NEXT,
        ACTION_SHOW_PREV: IMG_SHOW_PREV,
        ACTION_EDIT: IMG_EDIT,
        ACTION_SHOW: IMG_SHOW,
        DLG_NEW: IMG_CREATE,
        DLG_SEARCH: IMG_SEARCH,
        DLG_IMPORT: IMG_IMPORT,
        DLG_LIST: IMG_LIST,
        DLG_SHOW: IMG_INFO,
    }

    ############################################################################
    #
    # Error Messages
    #
    ############################################################################
    E_CALL_ABSTRACT = "[Error] Call of an abstract method."
    E_PARAM_TYPE = "[Error] Parameter %s has to be %s, but got %s."
    E_PARAM_FAIL = "[Error] Parameter %s has to be given, but got None."

    checkType = staticmethod(PyHtmlGUI.hg.checkType)
