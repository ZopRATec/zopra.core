# manager table names
TN_IMAGE         = 'image'
TN_SIMPLECONTENT = 'simplecontent'
TN_CONTENT       = 'content'
TN_LABELING      = 'labeling'

TCN_AUTOID       = 'autoid'

# manager table column names

# image manager
TCN_MGRID        = 'managerid'
TCN_MGRTYPE      = 'managertype'
TCN_IMAGEID      = 'imageid'
TCN_NAME         = 'name'
TCN_ALT          = 'alt'
TCN_DESCR        = 'description'
TCN_PATH         = 'path'
TCN_TYPE         = 'filetype'

# content manager
TCN_CONTENT      = 'content'
TCN_TOPIC        = 'topic'
TCN_CREATOR      = 'creator'
TCN_DATE         = 'entrydate'
TCN_FILE         = 'file'
TCN_HEADING      = 'heading'
TCN_SORTING      = 'sorting'

# print manager
TCN_MARGIN_TOP      = 'margin_top'
TCN_MARGIN_LEFT     = 'margin_left'
TCN_MARGIN_RIGHT    = 'margin_right'
TCN_MARGIN_BOTTOM   = 'margin_bottom'
TCN_PADDING_ROW     = 'padding_rows'
TCN_PADDING_COL     = 'padding_cols'
TCN_ROW_COUNT       = 'row_count'
TCN_COL_COUNT       = 'col_count'
TCN_CELL_WIDTH      = 'cell_width'
TCN_CELL_HEIGHT     = 'cell_height'
TCN_PAGE_WIDTH      = 'page_width'
TCN_PAGE_HEIGHT     = 'page_height'
TCN_FONT_SIZE       = 'font_size'
TCN_MULTI_LINE      = 'multi_line'
TCN_SHORT_LABEL     = 'short_label'

# manager table names
TN_PERSON       = 'person'
TN_ORG          = 'organisation'
TN_USER         = 'user'
TN_USER_GROUP   = 'multigroups'
TN_GROUP        = 'group'
TN_EBASE        = 'ebasegroup'
TN_ACL          = 'acl'
TN_ACCESS       = 'accessrole'
TN_SCOPE        = 'scope'
TN_SCOPEDEF     = 'scopedef'
TN_ROLESCOPE    = 'rolescope'
TN_THREAD       = 'thread'
TN_GLOBAL       = 'globalmessage'
TN_LOCAL        = 'localmessage'
TN_SENT         = 'sentmessage'
TN_MUSER        = 'messageuser'
TN_FOLDER       = 'msgfolder'
TN_FILTER       = 'filter'
TN_RULEBLOCK    = 'ruleblock'
TN_RULE         = 'rule'

# manager table column names
# person table
TCN_URI          = 'uri'
TCN_ADDRESS      = 'address'
TCN_PHONE        = 'phone'
TCN_TFP          = 'tollfreephone'
TCN_EMAIL        = 'email'
TCN_FAX          = 'fax'
TCN_LOGIN        = 'login'
TCN_LASTNAME     = 'lastname'
TCN_FIRSTNAME    = 'firstname'
TCN_INITIALS     = 'midinitials'
TCN_ORG          = 'organisation'

# organisation table
TCN_NAME         = 'name'
TCN_PARENT       = 'parent'

# user table
TCN_LASTLOGIN    = 'lastlogin'
TCN_USERID       = 'userid'
TCN_GROUPS       = 'groups'
TCN_EBASE        = 'ebasegroups'
TCN_ACCESS       = 'accessgroups'

# group table
TCN_LEVEL        = 'level'

# acl table
TCN_CONTENT      = 'content'

# creationmask table
TCN_EUSER        = 'euser'
TCN_EGROUP       = 'egroup'
TCN_SCOPEID      = 'scopeid'

# scope table
# TCN_USERID       = 'userid'
# TCN_NAME         = 'name'
TCN_ISDEFAULT    = 'isdefault'

# scopedef table
TCN_TABID        = 'tableid'
TCN_ZTYPE        = 'zopratype'

# rolescope table
TCN_ROLE         = 'role'

# thread table
TCN_SUBJECT      = 'subject'
TCN_ORIGIN       = 'origin'
TCN_MSENT        = 'msent'
TCN_MRECV        = 'mlocal'

# globalmessage table
TCN_NOTES        = 'notes'
TCN_GSENDER      = 'gsender'

# sent table
TCN_SSENDER      = 'ssender'
TCN_SRECEIVER    = 'sreceiver'
TCN_THREAD       = 'thread'
TCN_REPLIESTO    = 'repliesto'
TCN_DRAFT        = 'draft'

# localmessage table
TCN_LSENDER      = 'lsender'
TCN_LRECEIVER    = 'lreceiver'
TCN_OWNER        = 'mowner'
TCN_READ         = 'read'
TCN_TRASH        = 'trash'
TCN_FOLDER       = 'folder'

# messageuser table
TCN_SID          = 'sid'
TCN_COUNTER      = 'globalcounter'
TCN_ENTRIESPP    = 'entriespp'
TCN_THREADVIEW   = 'threadview'
TCN_SIGNATURE    = 'signature'
TCN_PRECEDENCE   = 'precedence'

# msgfolder table
TCN_FOLDERNAME   = 'foldername'
TCN_SORTID       = 'sortid'

# filter table
TCN_KNF          = 'knf'
TCN_BLOCKS       = 'blocks'
TCN_TARGET       = 'target'

# ruleblock table
TCN_RULES        = 'rules'

# ruleblock table
TCN_FIELD        = 'field'
TCN_VALUE        = 'value'
TCN_NOT          = 'not'
TCN_PREDICATE    = 'predicate'


# BUG: if we use the same column names in different tables they must have the
#      same specifications

# NOTE: for TN_FILTER NULL as target means Trash not Inbox
#       since Inbox is the default target there are no rules forwarding
#       msg to Inbox

# NOTE: map attribute for multilists assures correct mapping of traditionally
#       named aux tables of multilists in the new listHandler class

# Image definitions
IMG_DELETE      = 'Delete'
IMG_REPLY       = 'Reply'
IMG_REPLIED     = 'Replied'
IMG_FORWARD     = 'Forward Message'
IMG_BWD         = 'Backward'
IMG_FWD         = 'Forward'
IMG_BWD_INACT   = 'Backward (inactive)'
IMG_FWD_INACT   = 'Forward (inactive)'
IMG_FIRST       = 'First'
IMG_LAST        = 'Last'
IMG_FIRST_INACT = 'First (inactive)'
IMG_LAST_INACT  = 'Last (inactive)'
IMG_MAILIN      = 'Mail In'
IMG_MAILOUT     = 'Mail Out'
IMG_MAILREAD    = 'Read Mail'
IMG_MAILUNREAD  = 'Unread Mail'
IMG_THREADON    = 'Thread View on'
IMG_THREADOFF   = 'Thread View off'
IMG_THREAD      = 'Thread'
IMG_MOVEUP      = 'Move Up'
IMG_MOVEDOWN    = 'Move Down'
IMG_SORTNONE    = 'No Sorting'
IMG_SORTASC     = 'Sorted Ascending'
IMG_SORTDESC    = 'Sorted Descending'
IMG_EDIT        = 'Edit'
