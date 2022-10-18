from builtins import object

import PyHtmlGUI


class ZC(object):

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

    # Globally interesting Manager Name Constants
    ZM_PM = "ZopRAProduct"

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

    # Table Constants
    COL_TYPE = "TYPE"
    COL_LABEL = "LABEL"
    COL_INVIS = "INVIS"
    COL_REFERENCE = "REFERENCE"
    COL_DEFAULT = "DEFAULT"
    COL_PRIMARY_KEY = "PRIMARY KEY"

    # table definition for edit tracking
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

    # Error Messages
    E_CALL_ABSTRACT = "[Error] Call of an abstract method."
    E_PARAM_TYPE = "[Error] Parameter %s has to be %s, but got %s."
    E_PARAM_FAIL = "[Error] Parameter %s has to be given, but got None."

    # type checker e.g. for assertions
    checkType = staticmethod(PyHtmlGUI.hg.checkType)

    # legacy security manager
    ZM_SCM = "SecurityManager"

    # Legacy Security Flags (see Table.py)
    SC_READ = 4
