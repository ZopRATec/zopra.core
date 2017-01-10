import PyHtmlGUI


# list widget constants for handling

VALUE = 'value'
RANK  = 'rank'
SHOW  = 'show'  # MySQL reserved "show"
NOTES = 'notes'

WIDGET_CONFIG = 'widget_config'


# edit_tracking
TCN_AUTOID    = 'autoid'
TCN_CREATOR   = 'creator'
TCN_DATE      = 'entrydate'
TCN_EDITOR    = 'editor'
TCN_EDATE     = 'changedate'
TCN_OWNER     = 'owner'


class ZC:

    # edit_tracking
    TCN_AUTOID    = 'autoid'
    TCN_CREATOR   = 'creator'
    TCN_DATE      = 'entrydate'
    TCN_EDITOR    = 'editor'
    TCN_EDATE     = 'changedate'
    TCN_OWNER     = 'owner'

    # list widget constants for handling
    VALUE = 'value'
    RANK  = 'rank'
    SHOW  = 'show'
    NOTES = 'notes'

    WIDGET_CONFIG = 'widget_config'

    #
    # Globally interesting Manager Name Constants
    #
    ZM_PM       = 'ZopRAProduct'
    ZM_CM       = 'ContactManager'
    ZM_IM       = 'FileManager'
    ZM_PNM      = 'PrintManager'
    ZM_MM       = 'MessagingManager'
    ZM_CTM      = 'ContentManager'
    ZM_TEST     = 'TestManager'
    ZM_DEBUG    = 'DebugInfoManager'
    ZM_SCM      = 'SecurityManager'
    ZM_MBM      = 'MessageBoard'

    # Mask Types
    MASK_ADD    = 0x0001
    MASK_ADMIN  = 0x0002
    MASK_EDIT   = 0x0004
    MASK_SEARCH = 0x0008
    MASK_SHOW   = 0x0010
    MASK_HEAD   = 0x0020
    MASK_REDIT  = 0x0040

    # Database Column Types
    COL_TEXT        = 'TEXT'
    COL_DATE        = 'DATE'
    COL_INT4        = 'INT4'
    COL_INT8        = 'INT8'
    COL_FLOAT       = 'FLOAT'
    COL_SEQ         = 'SEQ'
    COL_URL         = 'URL'
    COL_CURRENCY    = 'NUMERIC(10,2)'
    COL_LOOKUPLIST  = 'singlelist'

    # ZopRA Column Types
    ZCOL_STRING = 'string'
    ZCOL_MEMO   = 'memo'
    ZCOL_INT    = 'int'
    ZCOL_LONG   = 'long'
    ZCOL_SLIST  = 'singlelist'
    ZCOL_MLIST  = 'multilist'
    ZCOL_HLIST  = 'hierarchylist'
    ZCOL_DATE   = 'date'
    ZCOL_FLOAT  = 'float'
    ZCOL_BOOL   = 'bool'
    ZCOL_CURR   = 'currency'

    #
    # Table Constants
    #
    COL_TYPE        = 'TYPE'
    COL_LABEL       = 'LABEL'
    COL_INVIS       = 'INVIS'
    COL_REFERENCE   = 'REFERENCE'
    COL_DEFAULT     = 'DEFAULT'
    COL_PRIMARY_KEY = 'PRIMARY KEY'

    #
    # some dialog handling constants
    #
    DLG_NEW    = 1
    DLG_SHOW   = 2
    DLG_EDIT   = 3
    DLG_SEARCH = 4
    DLG_DELETE = 5
    DLG_IMPORT = 6
    DLG_LIST   = 7

    DLG_TYPES = [DLG_SHOW, DLG_EDIT, DLG_NEW, DLG_DELETE, DLG_IMPORT, DLG_LIST]

    #
    # Security Flags
    #
    SC_LREAD = 1
    SC_WRITE = 2
    SC_READ  = 4
    SC_DEL   = 8
    SC_L_ALL = [SC_LREAD, SC_WRITE, SC_READ, SC_DEL]


    _edit_tracking_cols = { TCN_CREATOR: { COL_TYPE:    'singlelist',
                                           COL_LABEL:   'Creator'},
                            TCN_DATE:    { COL_TYPE:    'date',
                                           COL_LABEL:   'Entry Date',
                                           COL_DEFAULT: 'now()'},
                            TCN_EDITOR:  { COL_TYPE:    'singlelist',
                                           COL_LABEL:   'Last edited by'},
                            TCN_EDATE:   { COL_TYPE:    'date',
                                           COL_LABEL:   'Last edited on',
                                           COL_DEFAULT: 'now()'},
                            TCN_OWNER:   { COL_TYPE:    'singlelist',
                                           COL_LABEL:   'Owner'},
                            }

    ############################################################################
    #
    # Error Messages
    #
    ############################################################################
    E_CALL_ABSTRACT = '[Error] Call of an abstract method.'
    E_PARAM_TYPE    = '[Error] Parameter %s has to be %s, but got %s.'


    checkType = staticmethod(PyHtmlGUI.hg.checkType)
