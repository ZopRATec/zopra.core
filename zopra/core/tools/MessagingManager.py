############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from types                                   import ListType

#
# PyHtmlGUI Imports
#

from PyHtmlGUI.widgets.hgLabel               import hgLabel,    \
                                                    hgProperty
from PyHtmlGUI.widgets.hgPushButton          import hgPushButton
from PyHtmlGUI.kernel.hgWidget               import hgWidget
from PyHtmlGUI.kernel.hgGridLayout           import hgGridLayout

from PyHtmlGUI.widgets.hgPopupMenu           import hgPopupMenu

from PyHtmlGUI.stylesheet.hgStyleSheet       import hgStyleSheetItem

#
# ZopRA Imports
#
from zopra.core                             import HTML, ZC, ZM_SCM, ZM_CM, ZM_MM

from zopra.core.constants                   import TCN_AUTOID
from zopra.core.dialogs                     import getStdDialog
from zopra.core.dialogs.dlgMessageCenter    import dlgMessageCenter
from zopra.core.dialogs.dlgGMessageCenter   import dlgGMessageCenter
from zopra.core.dialogs.dlgSMessageCenter   import dlgSMessageCenter
from zopra.core.dialogs.dlgReadMsg          import dlgReadMsg
from zopra.core.dialogs.dlgReadGMsg         import dlgReadGMsg
from zopra.core.dialogs.dlgReadSMsg         import dlgReadSMsg
from zopra.core.dialogs.dlgSendMsg          import dlgSendMsg
from zopra.core.dialogs.dlgSendGMsg         import dlgSendGMsg
from zopra.core.dialogs.dlgMngFolder        import dlgMngFolder
from zopra.core.dialogs.dlgSignature        import dlgSignature
from zopra.core.dialogs.dlgOptions          import dlgOptions
from zopra.core.dialogs.dlgThreadView       import dlgThreadView
from zopra.core.dialogs.dlgConfirm          import dlgConfirm
from zopra.core.dialogs.dlgConfigFilter     import dlgConfigFilter
from zopra.core.dialogs.dlgMngFilters       import dlgMngFilters

from zopra.core.CorePart                    import MASK_REDIT

from zopra.core.tools.GenericManager        import GenericManager

from zopra.core.tools.managers import TN_PERSON,          \
                                                    TN_GLOBAL,          \
                                                    TN_THREAD,          \
                                                    TN_SENT,            \
                                                    TN_LOCAL,           \
                                                    TN_MUSER,           \
                                                    TN_FOLDER,          \
                                                    TN_USER,            \
                                                    TN_FILTER,          \
                                                    TN_RULEBLOCK,       \
                                                    TN_RULE,            \
                                                    TCN_USERID,         \
                                                    TCN_CONTENT,        \
                                                    TCN_SUBJECT,        \
                                                    TCN_ORIGIN,         \
                                                    TCN_MSENT,          \
                                                    TCN_MRECV,          \
                                                    TCN_GSENDER,        \
                                                    TCN_SSENDER,        \
                                                    TCN_SRECEIVER,      \
                                                    TCN_THREAD,         \
                                                    TCN_LSENDER,        \
                                                    TCN_LRECEIVER,      \
                                                    TCN_OWNER,          \
                                                    TCN_READ,           \
                                                    TCN_TRASH,          \
                                                    TCN_FOLDER,         \
                                                    TCN_SID,            \
                                                    TCN_COUNTER,        \
                                                    TCN_ENTRIESPP,      \
                                                    TCN_THREADVIEW,     \
                                                    TCN_SIGNATURE,      \
                                                    TCN_PRECEDENCE,     \
                                                    TCN_FOLDERNAME,     \
                                                    TCN_SORTID,         \
                                                    TCN_NAME,           \
                                                    TCN_KNF,            \
                                                    TCN_BLOCKS,         \
                                                    TCN_TARGET,         \
                                                    TCN_RULES,          \
                                                    TCN_FIELD,          \
                                                    TCN_VALUE,          \
                                                    TCN_NOT,            \
                                                    TCN_PREDICATE


# TODO:
# - Dlg showing all threads for user
#   layout like folder dlg (msg center)
# - browse read message dlg thread-based (<< and >> btns)
# - implement service based messaging and abo-system 
# - implement threadview in message center view 
#   grouping messages by thread
# - clean up old msg center functions/dlgs

# style sheet items
ssiFLD_ACTIVE = hgStyleSheetItem( '.fld_active' )
ssiFLD_ACTIVE.border().setAll( 0x000000, 'solid', '1px' )
ssiFLD_ACTIVE.background().setColor( 0xe0e0da )
ssiFLD_ACTIVE.paragraph().setWordWrap( 'nowrap' )

ssiFLD_DEFAULT = hgStyleSheetItem( '.fld_default' )
ssiFLD_ACTIVE.border().setAll( 0x000000, 'solid', '1px' )
ssiFLD_DEFAULT.paragraph().setWordWrap( 'nowrap' )



class MessagingManager(GenericManager):
    """\class ContactManager

    \brief Base class for all user managment interfaces.
    """
    _className          = ZM_MM
    _classType          = GenericManager._classType + [_className]
    meta_type           = _className

    _properties     = GenericManager._properties
    _generic_config = GenericManager._generic_config

    # generic config
    _generic_config[TN_THREAD] = { 'required':     [ TCN_ORIGIN ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_SUBJECT,
                                                     'entrydate' ]}
    _generic_config[TN_GLOBAL] = { 'required':     [ TCN_CONTENT,
                                                     TCN_GSENDER ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_SUBJECT,
                                                     TCN_GSENDER,
                                                     'entrydate' ]}
    _generic_config[TN_SENT]   = { 'required':     [ TCN_CONTENT,
                                                     TCN_SSENDER,
                                                     TCN_SRECEIVER,
                                                     TCN_THREAD ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_SUBJECT,
                                                     TCN_SSENDER,
                                                     TCN_SRECEIVER ] }
    _generic_config[TN_LOCAL]  = { 'required':     [ TCN_CONTENT,
                                                     TCN_LSENDER,
                                                     TCN_LRECEIVER,
                                                     TCN_OWNER,
                                                     TCN_THREAD ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_READ,
                                                     TCN_SUBJECT,
                                                     TCN_LSENDER,
                                                     'entrydate' ] }
    _generic_config[TN_MUSER]  = { 'required':     [ TCN_SID ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_SID,
                                                     TCN_COUNTER ] }
    _generic_config[TN_FOLDER] = { 'required':     [ TCN_OWNER,
                                                     TCN_FOLDERNAME,
                                                     TCN_SORTID ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_FOLDERNAME ] }

    _generic_config[TN_FILTER] = { 'required':     [ TCN_OWNER,
                                                     TCN_NAME,
                                                     TCN_KNF,
                                                     TCN_BLOCKS,
                                                     TCN_SORTID ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_NAME ] }

    _generic_config[TN_RULEBLOCK] = { 'required':  [ TCN_RULES ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_RULES ] }

    _generic_config[TN_RULE]   = { 'required':     [ TCN_FIELD,
                                                     TCN_VALUE,
                                                     TCN_NOT,
                                                     TCN_PREDICATE ],
                                   'basket_active':  False,
                                   'show_fields' : [ TCN_FIELD,
                                                     TCN_VALUE,
                                                     TCN_NOT,
                                                     TCN_PREDICATE ] }

    _dlgs = GenericManager._dlgs + ( dlgMessageCenter, 
                                     dlgGMessageCenter, 
                                     dlgSMessageCenter,
                                     dlgReadMsg,
                                     dlgReadGMsg,
                                     dlgReadSMsg,
                                     dlgSendMsg,
                                     dlgSendGMsg,
                                     dlgMngFolder,
                                     dlgSignature,
                                     dlgOptions,
                                     dlgThreadView,
                                     dlgConfirm,
                                     dlgConfigFilter,
                                     dlgMngFilters )

    _dlg_map = { TN_GLOBAL:         { ZC.DLG_SHOW:   'dlgReadGMsg' },
                 TN_SENT:           { ZC.DLG_SHOW:   'dlgReadSMsg' },
                 TN_LOCAL:          { ZC.DLG_SHOW:   'dlgReadMsg' },
                 TN_MUSER:          { ZC.DLG_SHOW:   'dlgSendMsg' },
                 TN_FOLDER:         { ZC.DLG_SHOW:   'dlgMessageCenter',
                                      ZC.DLG_EDIT:   'dlgMngFolder' },
                 TN_THREAD:         { ZC.DLG_SHOW:   'dlgThreadView' },
                 TN_FILTER:         { ZC.DLG_SHOW:   'dlgConfigFilter',
                                      ZC.DLG_EDIT:   'dlgConfigFilter' },
                 TN_THREAD:         { ZC.DLG_SHOW:   'dlgThreadView' }

               }
    
    suggest_id   = 'msgm'
    suggest_name = 'Messaging Manager'

    simpleHeader = """<html>
 <head>
  <title>&dtml-title_or_id;</title>
  <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
  <link href="getCSS" rel="stylesheet">
 </head>
 <body bgcolor="#FFFFFF"><center>"""
    simpleFooter = """</center></body></html>"""
    
    FLD_GLOBAL = 'Global'
    FLD_INBOX  = 'Inbox'
    FLD_OUTBOX = 'Outbox'
    FLD_DRAFTS = 'Drafts'
    FLD_TRASH  = 'Trash'
    
    SYSTEM_FOLDER = [ FLD_GLOBAL, FLD_INBOX, FLD_OUTBOX, FLD_DRAFTS, FLD_TRASH ]
    
    FLD_DLGS   = { FLD_GLOBAL: 'dlgGMessageCenter',
                   FLD_INBOX:  'dlgMessageCenter',
                   FLD_OUTBOX: 'dlgSMessageCenter',
                   FLD_DRAFTS: 'dlgSMessageCenter',
                   FLD_TRASH:  'dlgMessageCenter'
                 }
    
    FILTER_PRED_CONTAINS = 'contains'
    FILTER_PRED_IS       = 'is'
    FILTER_PRED_STARTS   = 'starts with'
    FILTER_PRED_ENDS     = 'ends with'
    
    FILTER_PREDICATES = [ FILTER_PRED_CONTAINS, FILTER_PRED_IS, FILTER_PRED_STARTS, FILTER_PRED_ENDS ]
    
#
# public managing
#
    def newForm(self, table, REQUEST = None):
        """\brief Override default new form function and forward to appropriate function"""
        self.displayError('Generic forms are disabled', 'Access Denied.')
#
#
#    def showForm(self, id, table, REQUEST = None, auto = None):
#        """\brief Override default show form function and forward to appropriate function"""
#        self.displayError('Generic forms are disabled', 'Access Denied.')
#
#
#    def editForm(self, id, table, REQUEST = None):
#        """\brief Override default edit form function and forward to appropriate function"""
#        self.displayError('Generic forms are disabled', 'Access Denied.')
#
#
    def searchForm(self, table, descr_dict = None, REQUEST = None):
        """\brief Override default edit form function and forward to appropriate function"""
        self.displayError('Generic forms are disabled', 'Access Denied.')


#
# generic functions overwritten
#

    def showForm(self, id, table, REQUEST = None, auto = None):
        """\brief overwritten showForm to have some special handling
        """

        # forward to m_contact - showForm
        if table == TN_MUSER:
            m_sec     = self.getHierarchyUpManager(ZM_SCM)
            m_contact = self.getHierarchyUpManager(ZM_CM)
            
            if m_sec:
                muser  = self.getEntry(TN_MUSER, id)
                sec_id = muser.get(TCN_SID, 0)
                if sec_id and m_contact:
                    suser = m_sec.tableHandler[TN_USER].getEntry(sec_id)
                    cmid  = suser.get(TCN_USERID)
                    
                    if cmid:
                        return m_contact.showForm(cmid, TN_PERSON, REQUEST)
                
            # we got here, something went wrong
            # alter request to forward correctly
            REQUEST.form[TCN_LRECEIVER] = id
        
        # special handling "folder" instead of "id"
        elif table == TN_FOLDER:
            REQUEST.form['folder'] = id
        
        # special handling forward to filter edit dialog
        elif table == TN_RULEBLOCK:
            filter = self.tableHandler[TN_FILTER].getEntries([id], [TCN_BLOCKS])
            
            if len(filter) > 1:
                self.displayError('Rule-block %s found in more than one filter.' % str(id), 'Database Error')
                
            if filter:
                return self.editForm(filter[0][TCN_AUTOID], TN_FILTER, REQUEST)
            else:
                self.displayError('Filter not found.', 'Handling Error')
        
        # special handling forward to ruleblock, that forwards to filter edit
        elif table == TN_RULE:
            blocks = self.tableHandler[TN_RULEBLOCK].getEntries([id], [TCN_RULES])
            
            if len(blocks) > 1:
                self.displayError('Rule %s found in more than one block.' % str(id), 'Database Error')
                
            if blocks:
                return self.showForm(blocks[0][TCN_AUTOID], TN_RULEBLOCK, REQUEST)
            else:
                self.displayError('Ruleblock not found.', 'Handling Error')
        else:
            return GenericManager.showForm(self, id, table, REQUEST, auto)


    def editForm(self, id, table, REQUEST = None):
        """\brief overwritten editForm to only allow edit of folder and filter
        """

        # only folders can be shown and edited
        # messages are read only
        # useroptions are private and for owner always editable
        if table in [TN_FOLDER, TN_FILTER]:
            return GenericManager.editForm(self, id, table, REQUEST)
        else:
            return self.showForm(id, table, REQUEST)


    def getLabelString(self, table, autoid = None, descr_dict = None):
        """\brief Return label for entry, overwrite for special functionality."""
        if autoid:
            ddict = self.getEntry(table, autoid)
        elif descr_dict:
            ddict = descr_dict
        else:
            return ''
        
        label = ''
        
        if table == TN_GLOBAL:
            label = ddict.get(TCN_SUBJECT, u'&lt;No Subject&gt;')
        elif table == TN_SENT:
            label = ddict.get(TCN_SUBJECT, u'&lt;No Subject&gt;')
        elif table == TN_LOCAL:
            label = ddict.get(TCN_SUBJECT, u'&lt;No Subject&gt;')
        elif table == TN_MUSER:
            lobj = self.listHandler.getList(TN_MUSER, TCN_SID)
            label = lobj.getValueByAutoid(ddict.get(TCN_SID))
        elif table == TN_FOLDER:
            label = ddict.get(TCN_FOLDERNAME, '')
        elif table == TN_THREAD:
            label = ddict.get(TCN_SUBJECT, u'&lt;No Subject&gt;')
        elif table == TN_FILTER:
            label = ddict.get(TCN_NAME, u'&lt;No Name&gt;')
        elif table == TN_RULEBLOCK:
            label = u'Rule-block %s' % str(ddict[TCN_AUTOID])
        elif table == TN_RULE:
            if ddict.get(TCN_NOT):
                label += u'not '
            label += ddict[TCN_FIELD] + u' '
            
            label += ddict[TCN_PREDICATE] + u' '

            if ddict[TCN_FIELD] == TCN_LSENDER:
                label += self.getLabelString(TN_MUSER, ddict[TCN_VALUE])
            else:
                label += ddict[TCN_VALUE]
        return label
    

    def actionBeforeShowList(self, table, param, REQUEST):
        """\brief Return the html source of the show organisation list form."""
        #if table == TN_PERSON:

        # we want autoidlists for navigation
        param['with_autoid_navig'] = True


    def prepareDelete(self, table, id, REQUEST = None):
        """\brief Function called before delete"""

        try:
            id = int(id)
        except (ValueError, TypeError):
            self.displayError('\'%s\' is not a numeric id.' % (id), 
                              'Internal Error.')                    
            
        if not table in self.tableHandler.keys():
            self.displayError('Table \'%s\' does not exist in %s' % (table, self.getTitle()), 
                              'Internal Error.')
                    
        entry = self.getEntry(table, id)
        
        if table == TN_GLOBAL:
            # no external dependencies
            pass
        elif table == TN_LOCAL:
            # adjust thread info
            thread = self.tableHandler[TN_THREAD].getEntry(entry[TCN_THREAD])
            assert(thread)
            thread[TCN_MRECV] -= 1
            assert(thread[TCN_MRECV] >= 0)
            if thread[TCN_MRECV] + thread[TCN_MSENT] == 0:
                self.tableHandler[TN_THREAD].deleteEntry(thread[TCN_AUTOID])
            else:
                if not self.tableHandler[TN_THREAD].updateEntry( thread, thread[TCN_AUTOID] ):
                    self.displayError('An error occured while updating thread.', 
                                         'Database error')
        elif table == TN_SENT:
            # adjust thread info
            thread = self.tableHandler[TN_THREAD].getEntry(entry[TCN_THREAD])
            assert(thread)
            thread[TCN_MSENT] -= 1
            assert(thread[TCN_MSENT] >= 0)
            if thread[TCN_MRECV] + thread[TCN_MSENT] == 0:
                self.tableHandler[TN_THREAD].deleteEntry(thread[TCN_AUTOID])
            else:
                if not self.tableHandler[TN_THREAD].updateEntry( thread, thread[TCN_AUTOID] ):
                    self.displayError('An error occured while updating thread.', 
                                         'Database error')
        elif table == TN_MUSER:
            # leave mail infos untouched
            pass
        elif table == TN_FOLDER:
            # move messages from folder to inbox
            messages = self.tableHandler[TN_LOCAL].getEntries([id], [TCN_FOLDER])
            
            for msg in messages:
                msg[TCN_FOLDER] = 'NULL'
                if not self.tableHandler[TN_LOCAL].updateEntry( msg, msg[TCN_AUTOID] ):
                    self.displayError('An error occured while updating message.', 
                                         'Database error')
        elif table == TN_THREAD:
            # NOTE: threads shouldn't be deleted explicitely
            messages = self.tableHandler[TN_SENT].getEntries([id], [TCN_THREAD])
            
            for msg in messages:
                self.tableHandler[TN_SENT].deleteEntry(msg[TCN_AUTOID])
                
            messages = self.tableHandler[TN_LOCAL].getEntries([id], [TCN_THREAD])
            
            for msg in messages:
                self.tableHandler[TN_LOCAL].deleteEntry(msg[TCN_AUTOID])
        elif table == TN_FILTER:
            block_ids = entry.get(TCN_RULES, [])
            
            self.deleteEntries(TN_RULEBLOCK, block_ids)
        elif table == TN_RULEBLOCK:
            rule_ids = entry.get(TCN_RULES, [])
            
            self.deleteEntries(TN_RULE, rule_ids)
        elif table == TN_RULE:
            pass
        

    def index_html(self, REQUEST, parent = None):
        """\brief main window on start page."""

        return self._index_html(REQUEST, parent)
    

    def _index_html(self, REQUEST, parent = None):
        """\brief main window on start page."""

        REQUEST.RESPONSE.redirect( '%s/dlgHandler/dlgMessageCenter/show' % self.absolute_url() )
            


    def buildMessageCenterLink(self, parent):
        """\brief """
        # checkLocalMessages
        count = self.getLocalMessageCount()
        label = 'Message Center'
        if count:
            if count > 1:
                more = 's'
            else:
                more = ''
            label = '%s<br>(<font color="red">%s new message%s</font>)' % (label, count, more)
        # build link
        link = hgLabel(label, self.absolute_url(), parent = parent)
        return link


    def buildMenuItem(self, menubar, REQUEST):
        """\brief managerspecific navigation item"""

        pop   = hgPopupMenu(menubar)
        perm  = self.getGUIPermission()
        ztype = self.getZopraType()

        # general role check
        guigranted = perm.hasMinimumRole(perm.SC_VISITOR)
        guigranted = guigranted or perm.hasSpecialRole(ztype + 'Superuser')
        
        if not guigranted:
            return False

        muser = self.getCurrentMUser()

        url = self.absolute_url()

        # config menu
        msg_pop = hgPopupMenu(menubar)
        
        # add system folders
        for folder in self.SYSTEM_FOLDER:
            new = ''
            if folder == self.FLD_INBOX:
                count = self.tableHandler[TN_LOCAL].getRowCount( { TCN_OWNER:  muser[TCN_AUTOID],
                                                                   TCN_FOLDER: 'NULL', 
                                                                   TCN_READ:   0, 
                                                                   TCN_TRASH:  0 } )
                if count > 0:
                    new += ' (<font color="red">%s new</font>)' % str(count)
            label = hgLabel( folder + new, 
                             '%s/dlgHandler/%s/show?folder=%s' % (url, self.FLD_DLGS[folder], folder) )
            msg_pop.insertItem( text = str( label ) )
            
        # add user folders
        folder_dicts = self.tableHandler[TN_FOLDER].getEntries(muser[TCN_AUTOID], TCN_OWNER, order = TCN_SORTID)
        
        for folder in folder_dicts:
            new = ''
            constraints = { TCN_FOLDER: folder[TCN_AUTOID], 
                            TCN_TRASH:  0,
                            TCN_READ:   0 }
            count = self.tableHandler[TN_LOCAL].getRowCount( constraints )
            if count > 0:
                new += '(<font color="red">%s new</font>)' % str(count)
            label = hgLabel( folder[TCN_FOLDERNAME] + new, 
                             '%s/dlgHandler/dlgMessageCenter/show?folder=%s' % (url, folder[TCN_AUTOID]) )
            msg_pop.insertItem( text = str( label ) )
        

        pop.insertItem( text = str( hgLabel( 'Messages >' ) ), popup = msg_pop )

        # config menu
        conf_pop = hgPopupMenu(menubar)
        conf_pop.insertItem( text = str( hgLabel( 'Manage Folders', '%s/dlgHandler/dlgMngFolder/show' % url) ) )
        conf_pop.insertItem( text = str( hgLabel( 'Manage Filters', '%s/dlgHandler/dlgMngFilters/show' % url) ) )
        conf_pop.insertItem( text = str( hgLabel( 'Signature',      '%s/dlgHandler/dlgSignature/show' % url) ) )
        conf_pop.insertItem( text = str( hgLabel( 'Options',        '%s/dlgHandler/dlgOptions/show'   % url) ) )

        pop.insertItem( text = str( hgLabel( 'Configuration >' ) ), popup = conf_pop )
        
        # add the popup
        link = self.buildMessageCenterLink(None)
        menubar.insertItem(text = str( link ), popup = pop)
            
        return False


    def init_musers(self):
        """\brief One-time-call Init Function to create muser entries for each security user"""
        # get security manager
        m_sec = self.getHierarchyUpManager(ZM_SCM)
        if m_sec:
            # get all user entries
            uobj    = m_sec.tableHandler[TN_USER]
            userids = uobj.getEntryAutoidList()
            # init them all
            for userid in userids:
                self.init_muser(userid)
        else:
            msg = 'Messaging needs Security Manager.'
            err = self.getErrorDialog(msg)
            raise ValueError(err)


    def init_muser(self, userid):
        """\brief """
        # look for muser entry with secid
        mtobj = self.tableHandler[TN_MUSER]
        muser = mtobj.getEntryBy(userid, TCN_SID)
        if not muser:
            # get global message count
            #gtobj = self.tableHandler[TN_GLOBAL]
            #counter = gtobj.getLastId()

            #\TODO change back to actual counter
            # for the start, init with 0
            counter = 0
            # create new muser
            muser = {TCN_SID:        userid, 
                     TCN_COUNTER:    counter,
                     TCN_ENTRIESPP:  20,
                     TCN_THREADVIEW: 0,
                     TCN_SIGNATURE:  ''}

            # return the id returned by addEntry
            return mtobj.addEntry(muser)


    # only for new messages, not for replies, sending drafted messages, forwards
    def sendLocalMessage(self, subject, text, receivers, sender = None):
        """\brief receivers and senders are security mgr ids
                  returns number of sent messages"""
        if not isinstance(receivers, ListType):
            receivers = [receivers]
        
        
        # get sender
        if not sender:
            sender = self.getCurrentMUser().get(TCN_AUTOID)
        else:
            muser = self.getMUser(sender)
            
            if not muser:
                self.displayError('Couldn\t find MUser for sec id %s.' % str(sender) , 
                                  'Database error')
            sender = muser[TCN_AUTOID]

        muids = []
        for sec_id in receivers:
            muser = self.getMUser(sec_id)
            
            if not muser:
                self.displayError('Couldn\t find MUser for sec id %s.' % str(sec_id) , 
                                  'Database error')
            
            muids.append(muser[TCN_AUTOID])
            
        if not text:
            text = ''
        if not subject:
            subject = ''
            
        # create new thread
        thread = { TCN_SUBJECT: subject, 
                   TCN_ORIGIN:  sender,
                   TCN_MSENT:   1,
                   TCN_MRECV:   len(receivers) }
        
        thread_id = self.tableHandler[TN_THREAD].addEntry(thread)
        
        if not thread_id:
            self.displayError('An error occured while creating thread.', 
                              'Database error')
        
        # create sent entry
        msg = { TCN_SSENDER:   sender,
                TCN_CONTENT:   text,
                TCN_SRECEIVER: muids,
                TCN_SUBJECT:   subject,
                TCN_THREAD:    thread_id }
        
        msg_id = self.tableHandler[TN_SENT].addEntry(msg)

        if not msg_id:
            self.displayError('An error occured while creating local message.', 
                              'Database error')

        # create local entry
        msg = { TCN_LSENDER:   sender,
                TCN_CONTENT:   text,
                TCN_LRECEIVER: muids,
                TCN_SUBJECT:   subject,
                TCN_READ:      0,
                TCN_TRASH:     0,
                TCN_THREAD:    thread_id }
        
        # go through receivers
        for muid in muids:
            # put in correct owner
            msg[TCN_OWNER] = muid

            # filter msg to select correct target folder
            self.filterMessage(msg)

            # create the msg        
            msg_id = self.tableHandler[TN_LOCAL].addEntry(msg)
            
            if not msg_id:
                self.displayError('An error occured while creating local message.', 
                                  'Database error')

        return len(receivers)


    def filterMessage(self, msg):
        """\brief 
           returns True  if filtering was executed successful
                   False if processing of msg was rejected 
                         (because owner setting was malformatted) """

        # get sender
        if not msg.get(TCN_OWNER):
            return False
        if not msg[TCN_OWNER] in msg[TCN_LRECEIVER]:
            return False

        # process filters
        muser = self.tableHandler[TN_MUSER].getEntry(msg[TCN_OWNER])
        
        if not muser:
            return False
            
        firstmatch = muser.get(TCN_PRECEDENCE, False)
        
        filters = self.tableHandler[TN_FILTER].getEntries([msg[TCN_OWNER]], [TCN_OWNER], order = TCN_SORTID)
        
        for filter in filters:
            # is filter in konjunctive normal form
            knf = filter.get(TCN_KNF, False)
            
            # get target
            folder_id = filter.get(TCN_TARGET)
            
            # check if target is available
            if folder_id:
                folder = self.tableHandler[TN_FOLDER].getEntry(folder_id)
                
                if not folder:
                    continue
                    
            # get the blocks where rules are
            block_ids = filter.get(TCN_BLOCKS, [])
            block_ids.sort()
            
            # empty rules automatically fail
            # NOTE: maybe they should automatically succeed?
            if not block_ids:
                continue
            
            if knf:
                filter_success = True
            else:
                filter_success = False
                
            for block_id in block_ids:
                block = self.tableHandler[TN_RULEBLOCK].getEntry(block_id)
                
                if not block:
                    self.displayError('Missing rule block %s for filter %s.' % ( str(block_id), 
                                                                                 self.getLabelString(TN_FILTER, None, filter) ), 
                                         'Database error')
                
                rule_ids = block.get(TCN_RULES, [])
                rule_ids.sort()
                
                if knf:
                    block_success = False
                else:
                    block_success = True
                
                for rule_id in rule_ids:
                    rule = self.tableHandler[TN_RULE].getEntry(rule_id)

                    if not rule:
                        self.displayError('Missing rule %s for filter %s.' % ( str(rule_id), 
                                                                               self.getLabelString(TN_FILTER, None, filter) ), 
                                             'Database error')

                    if self.evalRule(msg, rule):
                        if knf:
                            block_success = True
                            break
                    else:
                        if not knf:
                            block_success = False
                            break

                if block_success:
                    if not knf:
                        filter_success = True
                        break
                else:
                    if knf:
                        filter_success = False
                        break
                    
            if filter_success:
                if folder_id:
                    msg[TCN_FOLDER] = folder_id
                else:
                    msg[TCN_TRASH]  = 1
                    
                if firstmatch:
                    break
                
        return True

                
    def evalRule(self, msg, rule):
        """\brief """
        
        type  = rule.get(TCN_FIELD, TCN_CONTENT)
        neg   = rule.get(TCN_NOT, False)
        pred  = rule.get(TCN_PREDICATE, self.FILTER_PRED_CONTAINS)
        value = rule.get(TCN_VALUE)
        
        if not value:
            return False
        
        if not type in [TCN_CONTENT, TCN_SUBJECT, TCN_LSENDER]:
            return False
        
        if not pred in [ self.FILTER_PRED_CONTAINS,
                         self.FILTER_PRED_IS,
                         self.FILTER_PRED_STARTS,
                         self.FILTER_PRED_ENDS]:
            return False
        
        if type == TCN_LSENDER:
            try:
                value = int(value)
            except (ValueError, TypeError):
                return False
            
            if pred != self.FILTER_PRED_IS:
                return False

        if pred == self.FILTER_PRED_CONTAINS:
            match = value in msg.get(type, '')
        elif pred == self.FILTER_PRED_IS:
            match = value == msg.get(type, '')
        elif pred == self.FILTER_PRED_STARTS:
            match = value == msg.get(type, '')[:len(value)]
        elif pred == self.FILTER_PRED_ENDS:
            match = value == msg.get(type, '')[len(value)-1:]
            
        if neg:
            return not match
        else:
            return match


    def sendGlobalMessage(self, subject, text, sender = None):
        """\brief """
        # get sender
        if not sender:
            sender = self.getCurrentMUser().get(TCN_AUTOID)
        else:
            muser = self.getMUser(sender)
            
            if not muser:
                self.displayError('Couldn\t find MUser for sec id %s.' % str(sender) , 
                                  'Database error')
            sender = muser[TCN_AUTOID]
            
        if not subject:
            subject = ''
            
        if not text:
            return False
        
        # create global entry
        msg = { TCN_GSENDER: sender, 
                TCN_SUBJECT: subject, 
                TCN_CONTENT: text }
        
        msg_id = self.tableHandler[TN_GLOBAL].addEntry(msg)
        
        if not msg_id:
            self.displayError('An error occured while creating global message.', 
                              'Database error')
            
        return True


    def getCurrentMUser(self):
        """\brief """
        m_sec = self.getHierarchyUpManager(ZM_SCM)
        if not m_sec:
            msg  = 'No Security Manager found for login validation.'
            errd = self.getErrorDialog(msg)
            raise ValueError(errd)
        user  = m_sec.getUserByLogin(m_sec.getCurrentLogin())
        uid   = user.get(TCN_AUTOID)
        
        if uid:        
            return self.getMUser(uid)
        else:
            return {}


    def getMUser(self, sec_uid):
        """\brief """
        mtobj = self.tableHandler[TN_MUSER]
        muser = mtobj.getEntryBy(sec_uid, TCN_SID)
        if not muser:
            # whoops, no muser
            muid  = self.init_muser(sec_uid)
            muser = mtobj.getEntry(muid)
        return muser


    def getMUserId(self, sec_uid):
        """\brief """
        return self.getMUser(sec_uid).get(TCN_AUTOID)


    def getSendLink(self, sec_uid, parent = None):
        """\brief """
        muser_id = self.getMUserId(sec_uid)
        url = self.absolute_url()
        
        return hgLabel( 'Send Message', '%s/dlgHandler/dlgSendMsg/show?%s=%s' % (url, TCN_LRECEIVER, muser_id), parent = parent )


    def markAsRead(self, msg_id, read = True):
        # only set the flag for header_popup if new global messages
        
        if not msg_id:
            return
        
        msg = self.getEntry(TN_LOCAL, msg_id)
        
        if msg and msg.get(TCN_READ, 0) != int(read):
            msg[TCN_READ] = int(read)
            
            if not self.tableHandler[TN_LOCAL].updateEntry(msg, msg_id):
                if read:
                    self.displayError('Coudn\'t mark message as read.', 'Database Error')
                else:
                    self.displayError('Coudn\'t mark message as unread.', 'Database Error')


    def setHeaderPopUp(self, REQUEST):
        # only set the flag for header_popup if new global messages
        if self.checkForGlobalMessages():
            test = '"%s/showGlobalMessages"' % self.absolute_url()
            REQUEST.SESSION.set('header_popup', test)


    def showGlobalMessages(self):
        """\brief """
        muser = self.getCurrentMUser()
        # get global messages (TCN_COUNTER < TN_GLOBAL.autoid)
        gtobj = self.tableHandler[TN_GLOBAL]
        value = '_>_%s' % muser.get(TCN_COUNTER, 0)
        gmsgs = gtobj.getEntries(value, TCN_AUTOID, TCN_AUTOID)
        # dialog
        url = '%s/showGlobalCounterResetDlg' % self.absolute_url()
        dlg = getStdDialog('System Messages', url)
        # reset Header / Footer
        dlg.setHeader(self.simpleHeader)
        dlg.setFooter(self.simpleFooter)
        dlg.add('<center>')
        widget = hgWidget(parent = dlg)
        dlg.add(widget)
        dlg.add('</center>')
        layout = hgGridLayout(widget, 1, 1, 0, 4)
        row = 0
        # go through global messages
        for msg in gmsgs:
            # text
            widg = self.getFunctionWidget( TN_GLOBAL,
                                           TCN_CONTENT,
                                           widget,
                                           MASK_REDIT,
                                           msg )
            widg.setSize(50, 5)
            layout.addWidget(widg, row, 0)
            row += 2
        # property
        if gmsgs:
            lastid = msg.get(TCN_AUTOID)
            prop = hgProperty(name = 'lastid', value = str(lastid), parent = widget)
            layout.addWidget(prop, row, 0)
            row += 1
        # read button
        button = hgPushButton(text = 'Mark as read', parent = widget)
        layout.addWidget(button, row, 0)
        return HTML(dlg.getHtml())(self, None)


    def showGlobalCounterResetDlg(self, lastid = None):
        """\brief """
        if lastid:
            # set counter to lastid
            mtobj = self.tableHandler[TN_MUSER]
            muid  = self.getCurrentMUser().get(TCN_AUTOID)
            mtobj.updateEntry({TCN_COUNTER: lastid}, muid)
        dlg = getStdDialog ('System Messages')
        dlg.add('<center>')
        dlg.add(hgLabel('System Messages marked as read. You can close the window now.', parent = dlg))
        dlg.add('<br><br>')
        button = hgPushButton('Close', parent = dlg)
        button.setFunction('window.close()', True)
        dlg.add(button)
        dlg.add('</center>')
        dlg.setHeader(self.simpleHeader)
        dlg.setFooter(self.simpleFooter)
        return HTML(dlg.getHtml())(self, None)


    def checkForGlobalMessages(self):
        """\brief"""
        muser = self.getCurrentMUser()
        
        # get global messages (TCN_COUNTER < TN_GLOBAL.autoid)
        gtobj = self.tableHandler[TN_GLOBAL]
        value = '_>_%s' % muser.get(TCN_COUNTER, 0)
        count = gtobj.getRowCount({TCN_AUTOID: value})
            
        if count:
            return True
        else:
            return False


    def getLocalMessageCount(self):
        """\brief"""
        muser = self.getCurrentMUser()
        # get global messages (TCN_COUNTER < TN_GLOBAL.autoid)
        ltobj = self.tableHandler[TN_LOCAL]
        count = ltobj.getRowCount( { TCN_OWNER: muser.get(TCN_AUTOID),
                                     TCN_READ: 0 } )
        return count


#    def getSingleMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None):
#        """\brief Returns the mask."""


#
# service functions
#
    def startupConfig(self, REQUEST):
        """\brief Function called after creation by manageAddGeneric"""
        m_sec = self.getHierarchyUpManager(ZM_SCM)

        if m_sec:
            susers = m_sec.tableHandler[TN_USER].getEntryAutoidList()
            
            for user in susers:
                self.getMUser(user)

