############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from types import ListType

from zope.interface.declarations import implements

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                               import hg
from PyHtmlGUI.kernel.hgGridLayout           import hgGridLayout
from PyHtmlGUI.widgets.hgLabel               import hgLabel,    \
                                                    hgProperty
from PyHtmlGUI.widgets.hgLineEdit            import hgLineEdit
from PyHtmlGUI.widgets.hgCheckBox            import hgCheckBox
from PyHtmlGUI.widgets.hgGroupBox            import hgGroupBox
from PyHtmlGUI.widgets.hgPushButton          import hgPushButton
from PyHtmlGUI.widgets.hgComboBox            import hgComboBox

#
# ZopRA Imports
#
from zopra.core                              import HTML, getSecurityManager, ZM_CM,       \
                                                    ZM_SCM,      \
                                                    ZM_MM,       \
                                                    ZM_PM,       \
                                                    ZM_MBM


from zopra.core.elements.Buttons             import DLG_FUNCTION,    \
                                                    getPressedButton
from zopra.core.constants                    import TCN_AUTOID
from zopra.core.dialogs                      import getStdDialog, getPlainDialog
from zopra.core.widgets                      import dlgLabel
from zopra.core.interfaces                   import ISecurityManager
from zopra.core.CorePart                     import MASK_ADD,    \
                                                    MASK_EDIT,   \
                                                    MASK_SHOW

from zopra.core.LevelCache                   import LevelCache

from zopra.core.tools.GenericManager         import GenericManager, \
                                                    GEN_LABEL

from zopra.core.tools.managers               import TN_USER,        \
                                                    TN_GROUP,       \
                                                    TN_USER_GROUP,  \
                                                    TN_EBASE,       \
                                                    TN_PERSON,      \
                                                    TN_ACCESS,      \
                                                    TN_ACL,         \
                                                    TN_SCOPE,       \
                                                    TN_SCOPEDEF,    \
                                                    TN_ROLESCOPE,   \
                                                    TCN_TABID,      \
                                                    TCN_ZTYPE,      \
                                                    TCN_ROLE,       \
                                                    TCN_SCOPEID,    \
                                                    TCN_CONTENT,    \
                                                    TCN_EGROUP,     \
                                                    TCN_EUSER,      \
                                                    TCN_USERID,     \
                                                    TCN_NAME,       \
                                                    TCN_GROUPS,     \
                                                    TCN_LOGIN,      \
                                                    TCN_LEVEL,      \
                                                    TCN_LASTLOGIN,  \
                                                    TCN_EBASE,      \
                                                    TCN_FIRSTNAME,  \
                                                    TCN_LASTNAME,   \
                                                    TCN_EMAIL

from zopra.core.security                     import SC_LREAD, SC_READ, SC_WRITE


class SecurityManager(GenericManager):
    """ Security Manager """
    _className          = ZM_SCM
    _classType          = GenericManager._classType + [_className]
    meta_type           = _className

    implements(ISecurityManager)

    _properties = GenericManager._properties + (
                {'id': 'system',    'type': 'string',     'mode': 'w'},)

    system = ''

    _generic_config = { TN_USER: { 'basket_to':     False,
                                   'basket_from':   False,
                                   'basket_active': False },
                        TN_GROUP:{ 'basket_to':     False,
                                   'basket_from':   False,
                                   'basket_active': False },
                        TN_EBASE:{ 'basket_to':     False,
                                   'basket_from':   False,
                                   'basket_active': False }}
    """ usage: _generic_config = {table: {key:value}}
        keys: basket_to     (True / False) - for showForm/showList-BasketButton
              basket_from   (True / False) - for newForm-BasketButton
              basket_active (True / False) - show basket at all
              show_fields   ([attrs])      - attributes for showList
              required      ([attrs])      - required attributes for new/edit
    """

    def __init__( self,
                  title     = '',
                  id        = None,
                  nocreate  = 0,
                  zopratype = ''):
        GenericManager.__init__( self,     title,     id,
                                  nocreate, zopratype )
        self._aclcache = {}

    # adjust cache
    def manage_afterAdd(self, item, container):
        """\brief Call super function, then resize cache"""
        GenericManager.manage_afterAdd(self, item, container)
        self.tableHandler[TN_USER].cache.item_count = 500


#
# user related security functions
#

    def getCurrentLogin(self):
        """\brief login"""
        return str(getSecurityManager().getUser())


    def getUserByLogin(self, login):
        """\brief Return the User with the given Login."""
        if login:
            tobj = self.tableHandler[TN_USER]
            return tobj.getEntryBy(str(login), TCN_LOGIN)
        return {}


    def getUserByCMId(self, id):
        """\brief Return the User with the given CM-ID."""
        # the handling looks cruel, but getEntry may return None and we need {}
        # at least.
        if id:
            tobj = self.tableHandler[TN_USER]
            return tobj.getEntryBy(id, TCN_USERID)

        return {}


    def getCurrentUser(self):
        # implementation without permissions (to avoid recursion loading permissions)
        tobj = self.tableHandler[TN_USER]
        login = self.getCurrentLogin()
        uid = tobj.getEntryAutoid(login, TCN_LOGIN)
        # security check (acl_users-user without zopra-user-entry has no uid)
        if not uid:
            msg = 'You do not have a valid zopra login or are not logged in correctly. Sorry.'
            dlg = self.getUnauthorizedErrorDialog(msg)
            raise ValueError(dlg)

        user = tobj.getEntry(uid, None, None, True)
        return user



    def getCurrentCMId(self):
        """\brief Return the CMId of the current user."""
        login = self.getCurrentLogin()
        user  = self.getUserByLogin(login)
        cmid  = user.get(TCN_USERID)
        return cmid


    def getUserFolder(self):
        """\brief Search for acl_users in folder hierarchy."""
        fold = self.getContainer()
        ready = False
        while not ready:
            if hasattr (fold, 'objectValues'):

                # iterate over container content
                for obj in fold.objectValues():
                    if str(obj.id) == 'acl_users':
                        return obj

            if not ready:
                if fold == None or fold.isTopLevelPrincipiaApplicationObject:
                    ready = True
                else:
                    fold = fold.getParentNode()
        return None


    def addUser(self, login, password):
        """\brief register user."""
        usrfold = self.getUserFolder()

        if usrfold:
            if not usrfold.getUser(login):
                usrfold.userFolderAddUser(login, password, [], [])
                return True
        return False


    def removeUser(self, login):
        usrfold = self.getUserFolder()
        if usrfold and usrfold.getUser(login):
            usrfold.userFolderDelUsers([login])


    def updatePassword(self, descr_dict):
        """\brief This function should not be callable via html, so it gets
                  no brief.
        """
        login    = descr_dict.get(TCN_LOGIN)
        if not login:
            user_id = descr_dict.get(TCN_USERID)
            if user_id:
                entry = self.getUserByCMId( user_id )
                login = entry.get(TCN_LOGIN)
        if not login:
            error = 'Error finding user info.'
            raise ValueError(self.getErrorDialog(error))

        password = descr_dict.get('password')
        check    = descr_dict.get('check')

        if not password:
            error  = '[Error] SecurityManager.updatePassword(): '
            error += 'Empty Password is not allowed.'
            raise ValueError(self.getErrorDialog( error ))

        if password != check:
            error  = '[Error] SecurityManager.updatePassword(): '
            error += 'Password mismatch. Please try again.'
            raise ValueError(self.getErrorDialog( error ))

        usrfold = self.getUserFolder()

        if usrfold and usrfold.getUser(login):
            roles = usrfold.getUser(login).getRoles()
            usrfold.userFolderEditUser(login, password, roles, [])
            return True
        return False


    def prepareDelete( self, table, id, REQUEST = None ):
        """\brief Removes the user from acl_users
        """
        if table == TN_USER:
            # delete the user objects
            user = self.getEntry(TN_USER, id)
            if user:
                self.removeUser( user.get(TCN_LOGIN) )

#
# EBaSe functions
#


    def getCurrentEBaSeGroups(self):
        """\brief return list of EBaSe groups of current user."""
        login = self.getCurrentLogin()
        user  = self.getUserByLogin( str(login) )
        return user[TCN_EBASE]


    def findEBaSe(self, users, groups, right):
        """\brief """
        # for each user and group, build acl-string and search for it in
        # ebase list
        all = []
        for entry in users:
            search = '(u%s%s)' % (entry[0], entry[1])
            # do something to search value
            # TODO implement

            result = []
            for res in result:
                if not res in all:
                    all.append(res)
        for entry in groups:
            search = '(g%s%s)' % (entry[0], entry[1])
            # do something to search value
            # TODO implement

            result = []
            for res in result:
                if not res in all:
                    all.append(res)
        return all


#    def findCurrentEBaSe(self, right):
#        """\brief right is 'w' or 'r' for now."""
#        # get userid, get groups
#        # TODO peter: seems unused
#        return self.findEBaSe(self, users, groups, right)

# actual implementation

    def foldEBaSe(self, groups, users):
        """\brief Generate EBaSe string, search entry, put it in if not found."""
        all = []
        for key in users.keys():
            user = users[key]
            for entry in user:
                one = 'u%s%s' % (key, entry)
                all.append(one)
        for key in groups.keys():
            group = groups[key]
            for entry in group:
                one = 'g%s%s' % (key, entry)
                all.append(one)
        all.sort()
        value = ':%s:' % ':'.join(all)
        # lookup value
        tobj = self.tableHandler[TN_ACL]
        entries = tobj.getEntries(value, TCN_CONTENT)
        if not entries:
            autoid = tobj.addEntry({TCN_CONTENT: value})
        else:
            autoid = entries[0][TCN_AUTOID]
        return autoid


    def unfoldEBaSe(self, acl):
        """\brief get EBaSe string and translate it into groups / users"""
        if not acl:
            return {}, {}
        entry = self.tableHandler[TN_ACL].getEntry(acl)
        if not entry:
            return {}, {}
        value = entry.get(TCN_CONTENT)
        if not value:
            return {}, {}
        groups = {}
        users  = {}
        if not value:
            return groups, users
        vallist = value.split(':')
        for entry in vallist:
            if not entry:
                # : at first and last index of value
                continue
            # entry is in form (g|u)<id>(2|4|1|8)
            who = entry[0]
            what = int(entry[-1])
            rest = entry[1:-1]
            rest = int(rest)
            if who == 'g':
                target = groups
            else:
                target = users
            if rest in target:
                target[rest].append(what)
            else:
                target[rest] = [what]

        return groups, users


    def getCurrentEBaSePermission(self, acl):
        # temporary check
        if not hasattr(self, '_aclcache'):
            self._aclcache = LevelCache(2, [100, 100], '_aclcache')
        # check acl (ebase-id)
        if not acl:
            return []

        # get user
        user = self.getCurrentUser()
        uid  = user[TCN_AUTOID]

        # check acl cache
        perms = self._aclcache.get([uid, acl])
        if perms:
            return perms

        perms = []
        # get users / groups
        groups, users = self.unfoldEBaSe(acl)
        # check userid
        if uid in users:
            perms = users[uid]
        # match own groups
        gids  = user.get(TCN_EBASE, [])
        for entry in gids:
            if entry in groups:
                perms.extend(groups[entry])
        # put in acl cache
        self._aclcache.insert([uid, acl], perms)

        return perms


    def getPermForScope(self, scopeid):
        cobj = self.tableHandler['creationmask']
        cmasks = cobj.getEntries(scopeid, 'scopeid')
        if cmasks:
            groups, users = self.unfoldEBaSe(cmasks[0]['acl'])
        else:
            groups = {}
            users  = {}

        return groups, users


    def getCreationAcl(self, tableid, ztype):
        """\brief"""
        # look for scope for tableid / ztype
        # look for creationmask for scope
        # look for default scope
        # look for creation mask for scope
        # look for system scope for tableid / ztype
        # look for creationmask for scope
        # look for default system scope
        # look for creation mask for scope
        pass


    def getEBaSeMask(self, perms, users = True, edit = False, parent = None):
        # get label and table
        if users:
            label = 'Users'
            table = TN_USER
            tobj  = self.tableHandler[TN_USER]
            lname = TCN_EUSER
            base  = 'u'
        else:
            label = 'Groups'
            table = TN_EBASE
            tobj  = self.tableHandler[TN_EBASE]
            lname = TCN_EGROUP
            base  = 'g'
        # build mask
        mask = hgGroupBox(title = label, parent = parent)
        layout = hgGridLayout(mask, 1, 1, 0, 2)
        # add Header
        lab = hgLabel('lr', parent = mask)
        #label.setToopTip('LabelRead')
        layout.addWidget(lab, 0, 2)
        lab = hgLabel('r', parent = mask)
        #label.setToopTip('Read')
        layout.addWidget(lab, 0, 3)
        lab = hgLabel('w', parent = mask)
        #label.setToopTip('Write')
        layout.addWidget(lab, 0, 4)

        # order
        rights = [SC_LREAD, SC_READ, SC_WRITE]

        row = 1
        # go through perms
        keys = perms.keys()
        keys.sort()
        for autoid in keys:
            # add label
            lstr = self.getLabelString(table, autoid)
            lab = hgLabel(lstr, parent = mask)
            layout.addWidget(lab, row, 0)

            # property
            prop = hgProperty(name = 'sec%s' % base, value = str(autoid), parent = mask)
            layout.addWidget(prop, row, 1)

            # add perm checkboxes
            single = perms.get(autoid)
            col = 2
            for right in rights:
                name = 'perm_%s%s' % (base, autoid)
                check = hgCheckBox(name = name, value = str(right), parent = mask)
                if not edit:
                    check.setDisabled()
                if right in single:
                    check.setChecked(True)
                layout.addWidget(check, row, col)
                col += 1
            # add remove button
            if edit:
                remove = hgPushButton('Remove', 'remove_%s%s' % (base, autoid), parent = mask)
                layout.addWidget(remove, row, col)
            row += 1
        if not perms:
            lab = hgLabel('No %s selected.' % label, parent = mask)
            layout.addWidget(lab, row, 0)
            row += 1
        if edit:
            # add selector
            lobj = self.listHandler.getList(table, lname)
            selector = lobj.getComplexWidget( parent = mask )
            layout.addWidget(selector, row + 1, 0)
            # add add button
            add = hgPushButton('Add', DLG_FUNCTION + 'sec_%sadd' % base, parent = mask)
            layout.addMultiCellWidget(add, row + 1, row + 1, 1, 4)

        return mask


#
# Global Access Roles (GAR) security functions
#

    def getCurrentLevel(self, login = None):
        """\brief get Access level of current user (or login)"""
        if not login:
            login =  getSecurityManager().getUser()
        #if not self.getUserByLogin(login):
        #    return 0
        query =  "SELECT max(level) FROM %s%s u, %s%s g, %s%s ug WHERE "
        query += "u.autoid = ug.tableid and ug.%s = g.autoid and u.login = '%s'"
        query = query % ( self.id,
                          TN_USER,
                          self.id,
                          TN_GROUP,
                          self.id,
                          TN_USER_GROUP,
                          TCN_GROUPS,
                          login )
        level = self.getManager(ZM_PM).executeDBQuery(query)[0][0]

        if level != None:
            return level

        return 0


    def hasRole(self, role, login = None):
        """\brief test current user (or login) for role"""
        if not login:
            login =  getSecurityManager().getUser()

        user   = self.getUserByLogin( str(login) )
        if user:

            groups = self.listHandler.getList(TN_USER, TCN_GROUPS).getValueByAutoid( user.get(TCN_GROUPS, []) )
            if role in groups:
                return True

        return False


    def getGlobalRoles(self):
        """\brief Return Global Roles of user."""
        user =  self.getCurrentUser()
        if user:
            gids = user[TCN_GROUPS]
            tobj = self.tableHandler[TN_GROUP]
            res  = []
            for gid in gids:
                group = tobj.getEntry(gid, ignore_permissions = True)
                if group:
                    res.append(group.get(TCN_NAME))
            return res
        else:
            raise ValueError('Internal Error: Current User not found.')

#
# Scope Based Access Roles (SBAR) security functions
#

    def getAccessEnabledMgrs(self):
        """\brief Return all tabids (with zopratype)
                  of managers with access roles."""
        tabids = {}
        mgrs = self.getAllManagersHierarchyDown()
        for mgr in mgrs:
            if mgr.checkSBAR():
                # get all tables, get zt, put in tabids
                tabs = mgr.tableHandler.keys()
                ztype = mgr.getZopraType()
                for tab in tabs:
                    tobj = mgr.tableHandler[tab]
                    uid = tobj.getUId()
                    if not ztype:
                        tabids[uid] = None
                    else:
                        if uid in tabids:
                            tabids[uid].append(ztype)
                        else:
                            tabids[uid] = [ztype]
        return tabids


    def getAccessRoles(self):
        """\brief Return Access Roles of user."""
        # get user
        user = self.getCurrentUser()
        uid  = user[TCN_AUTOID]
        # rolescope table
        robj = self.tableHandler[TN_ROLESCOPE]
        # scopedefs table
        sobj = self.tableHandler[TN_SCOPEDEF]
        # user's roles in different scopes, without permissions
        rsids = robj.getEntryAutoidList(constraints = {TCN_EUSER: uid})

        #TODO: use other class than levelCache! write new!
        store = LevelCache(2, [1000, 100], nonpersistent = True)

        for rsid in rsids:
            rsmap = robj.getEntry(rsid, ignore_permissions = True)
            scopeid = rsmap[TCN_SCOPEID]
            role = rsmap[TCN_ROLE]
            # translate scope to tableids/zopratypes
            scopedefids = sobj.getEntryAutoidList(constraints = {TCN_SCOPEID: scopeid})
            for sdefid in scopedefids:
                sdef = sobj.getEntry(sdefid, ignore_permissions = True)
                tabid = sdef[TCN_TABID]
                ztype = sdef[TCN_ZTYPE]
                store.insert([tabid, ztype], role)

        return store


    def getUserRolesForScope(self, scopeid):
        """\brief Return user-role mapping for that scope"""
        robj = self.tableHandler[TN_ROLESCOPE]
        roles = robj.getEntries(scopeid, TCN_SCOPEID)
        users = {}
        for role in roles:
            users[role[TCN_EUSER]] = role[TCN_ROLE]
        return users


    def getSBARMask(self, users, edit = False, parent = None):
        """\brief"""
        # build mask
        mask = hgGroupBox(title = 'User Role Mapping', parent = parent)
        layout = hgGridLayout(mask, 1, 1, 0, 2)
        # add Header
        lab = hgLabel('User', parent = mask)
        layout.addWidget(lab, 0, 0)
        lab = hgLabel('Role', parent = mask)
        layout.addWidget(lab, 0, 1)

        perm = self.getGUIPermission()
        roles = perm.roles
        rolenames = perm.rolenames

        row = 1
        # go through perms
        keys = users.keys()
        keys.sort()
        for autoid in keys:
            # add label
            lstr = self.getLabelString(TN_USER, autoid)
            lab = hgLabel(lstr, parent = mask)
            layout.addWidget(lab, row, 0)

            # property
            prop = hgProperty(name = 'secuser', value = str(autoid), parent = mask)
            layout.addWidget(prop, row, 3)

            # add role selector
            if edit:

                rsel = hgComboBox(name = 'role_%s' % autoid, parent = mask)
                rsel.insertItem('None', 0)
                for role in roles.keys():
                    rsel.insertItem(role, roles[role])
                rsel.setCurrentValue(users[autoid])
                layout.addWidget(rsel, row, 1)

            else:
                label = hgLabel(rolenames.get(users[autoid], 'None'), parent = mask)
                layout.addWidget(label, row, 1)
            # add remove button
            if edit:
                remove = hgPushButton('Remove', 'remove_%s' % (autoid), parent = mask)
                layout.addWidget(remove, row, 2)
            row += 1
        if not users:
            lab = hgLabel('No Users selected.', parent = mask)
            layout.addWidget(lab, row, 0)
            row += 1

        if edit:
            # add selector
            lobj = self.listHandler.getList(TN_USER, TCN_EUSER)
            selector = lobj.getComplexWidget( parent = mask )
            layout.addWidget(selector, row + 1, 0)
            # add add button
            add = hgPushButton('Add', DLG_FUNCTION + 'sec_add', parent = mask)
            layout.addMultiCellWidget(add, row + 1, row + 1, 1, 4)

        return mask


#
# mail login info
#

    def mailLogin(self, REQUEST):
        """\brief Send mail with new login / pw info."""
        doSend   = REQUEST.get('sendmail')
        if not doSend:
            return False
        cmid     = REQUEST.get(TCN_USERID)
        m_contact = self.getManager(ZM_CM)
        if not m_contact:
            return False
        person   = m_contact.getEntry(TN_PERSON, cmid)
        mail     = person.get(TCN_EMAIL)
        if not mail:
            return False
        fname = person.get(TCN_FIRSTNAME)
        lname = person.get(TCN_LASTNAME)
        password = REQUEST.get('password')
        login    = REQUEST.get(TCN_LOGIN)
        base     = REQUEST.BASE1
        if base[-1] != '/':
            base += '/'

        # system name
        system = self.system or 'ZopRASystem'

        # find sender mail adress
        mfrom = None
        usermailadd = False
        cur = m_contact.getCurrentUser()
        if cur:
            mfrom = cur.get(TCN_EMAIL)
            usermailadd = True

        if not mfrom:
            # take system and server to build fake mail adress
            server   = REQUEST.HTTP_HOST
            # check if this is an ip
            first = server[:server.find('.')]
            try:
                int(first)
                # this is an ip
                server = REQUEST.SERVER_URL
                # in this case, the http has to be lost
            except:
                # the string seems to be a hostname
                pass
            # check and remove some parts of the url
            if server.find('//') != -1:
                server = server[server.find('//') + 2:]
            if server.find(':') != -1:
                server = server[:server.find(':')]
            if server[:4] == 'www.':
                server = server[4:]
            # set new mail adress
            mfrom = '%s@%s' % (system, server)

        # message text
        text =  'Hello %s %s\n\n'
        text += 'With this email, you receive your new / updated login information '
        text += 'for the %s at %s.\n'
        text += 'Login: %s\n'
        text += 'Password: %s\n\n'
        if not usermailadd:
            text += 'Do not reply to this mailadress.\n'
        text += 'Have a nice day.\n\nYour ZopRA Security Manager.'
        text = text % (fname, lname, system, base, login, password)
        subject = 'Login Information for %s' % system
        done = self.sendSimpleMail( mail,
                                    mfrom,
                                    subject,
                                    text )
        # confirmation to admin if not same as email
        if usermailadd and mail != mfrom:
            ntext = 'ZopRA Admin Info Mail: The following was sent to %s\n' % (mail)
            ntext += '-----------------------------------------------------\n'
            ntext += text
            self.sendSimpleMail( mfrom, mfrom, subject, ntext)
        if not done:
            return False
        return mail

#
# public managing
#

    def _index_html(self, REQUEST, parent = None, border = True):
        """\brief Management Overview for security Manager"""
        perm = self.getGUIPermission()
        if perm.hasMinimumRole(perm.SC_SUPER):
            
            dlg, mask = getPlainDialog(self.absolute_url() + '/buttonForwardForm', parent, border)
            lay = mask.layout()
            
            widget, super, hasperm = self.createOverviewBox(TN_USER, perm, mask)
            lay.addWidget(widget, 0, 0)
            widget.setCaption('User Management')
            widget, super, hasperm = self.createOverviewBox(TN_GROUP, perm, mask)
            lay.addWidget(widget, 1, 0)
            widget.setCaption('Global Group Management')
            
            if perm.hasMinimumRole(perm.SC_ADMIN):
                # ebase block 
                widget, super, hasperm = self.createOverviewBox(TN_EBASE, perm, mask)
                lay.addWidget(widget, 0, 1)
                widget.setCaption('EBaSe Group Management')
                
                # extra management block
                tabmask = hgGroupBox(1, hg.Horizontal, 'Additional Management', mask)
                lay.addWidget(tabmask, 1, 1)
                #tabmask.margin = 0
                url = self.absolute_url()
 
                hgLabel ( 'Personal Page',
                          '%s/personalPage' % (url),
                          parent = tabmask )
                hgLabel ( 'Scope Based Access Roles (SBAR)',
                          '%s/sbarPage' % (url),
                          parent = tabmask )
            return dlg
            
#            tab[0, 0]  = dlgLabel( '<b>User Managing</b>'                    )
#            tab[2, 0]  = hgLabel ( 'New User',
#                                   '%s/newForm?table=%s' % (url, TN_USER)    )
#            tab[3, 0]  = hgLabel ( 'User Search',
#                                   '%s/searchForm?table=%s' % (url, TN_USER) )
#            tab[4, 0]  = hgLabel ( 'User List',
#                                   '%s/showList?table=%s' % (url, TN_USER)   )
#
#            tab[7, 0]  = dlgLabel( '<b>Group Managing</b>'                   )
#            tab[9, 0]  = hgLabel ( 'New Group',
#                                   '%s/newForm?table=%s' % (url, TN_GROUP)   )
#            tab[10, 0] = hgLabel ( 'Group Search',
#                                   '%s/searchForm?table=%s' % (url, TN_GROUP))
#            tab[11, 0] = hgLabel ( 'Group List',
#                                   '%s/showList?table=%s' % (url, TN_GROUP)  )
#
#            tab[13, 0] = dlgLabel( '<b>EBaSe Group Managing</b>'             )
#            tab[15, 0] = hgLabel ( 'New Group',
#                                   '%s/newForm?table=%s' % (url, TN_EBASE)   )
#            tab[16, 0] = hgLabel ( 'Group Search',
#                                   '%s/searchForm?table=%s' % (url, TN_EBASE))
#            tab[17, 0] = hgLabel ( 'Group List',
#                                   '%s/showList?table=%s' % (url, TN_EBASE)  )
#
#            tab[19, 0] = hgLabel ( 'Personal Page',
#                                   '%s/personalPage' % (url) )
#            tab[20, 0] = hgLabel ( 'Scope Based Access Roles',
#                                   '%s/sbarPage' % (url)     )
#            return tab

        else:
            return self.personalPage(True)


#
# generic functions overwritten
#

    def getLabelString(self, table, autoid = None, descr_dict = None):
        """\brief Return label for entry, overwrite for special functionality."""
        #return autoid, no matter what table
        if autoid:
            ddict = self.getEntry(table, autoid)
        elif descr_dict:
            ddict = descr_dict
        else:
            return ''
        lab = ''
        if table == TN_USER:
            lab = ddict.get(TCN_LOGIN)
            lobj = self.listHandler.getList(table, TCN_USERID)
            uid = ddict.get(TCN_USERID)
            usr = lobj.getValueByAutoid(uid)
            if usr:
                lab = '%s (%s)' % (lab, usr)
        elif table == TN_GROUP:
            lab = ddict.get(TCN_NAME)
        elif table == TN_EBASE:
            lab = ddict.get(TCN_NAME)
        elif table == TN_ACCESS:
            lab = ddict.get(TCN_NAME)
        elif table == TN_ACL:
            lab = '%s: %s' % (ddict.get(TCN_AUTOID), ddict.get(TCN_CONTENT))
        elif table == 'scope':
            lab = ddict.get('name', 'No Name')
            if ddict.get('isdefault'):
                lab += ' (Default)'
        return lab


    def prepareDict(self, table, descr_dict, REQUEST):
        """\brief Dummy Function called before edit and add"""
        if table == 'scope':
            button = self.getPressedButton(REQUEST)
            if not button:
                return
            if button in ['mgr_select', 'zt_select', 'Add']:
                mgr = REQUEST.get('mgr_select')
                ztype = REQUEST.get('zt_select')
                tab = REQUEST.get('tab_select')
                newdef = {'mgr_select': mgr,
                          'zt_select': ztype,
                          'tab_select': tab}
                if button == 'Add':
                    self.addNewScopeDef(newdef, descr_dict.get(TCN_AUTOID))
                else:
                    descr_dict['newdef'] = newdef
            elif button == 'Discard':
                pass
            elif len(button) > 11 and button[:11] == 'remscopedef':
                self.tableHandler['scopedef'].deleteEntry(int(button[11:]))



    def actionBeforeAdd(self, table, descr_dict, REQUEST):
        """\brief Overwritten generic function called before add, checks login"""
        # login check
        if table == TN_USER:
            login  = descr_dict.get(TCN_LOGIN)
            userid = descr_dict.get(TCN_USERID)
            tobj  = self.tableHandler[TN_USER]
            if tobj.getEntries(login, TCN_LOGIN):
                error = 'Login already exists.'
                raise ValueError(self.getErrorDialog( error ))
            if tobj.getEntries(userid, TCN_USERID):
                error = 'Login for selected Person already exists.'
                raise ValueError(self.getErrorDialog( error ))
        elif table == TN_SCOPE:
            perm = self.getGUIPermission()
            euser = descr_dict.get(TCN_EUSER)
            
            try:
                euser = int(euser)
            except:
                pass

            if euser == 'NULL' or euser == 0 or euser == '0':

                if not perm.hasMinimumRole(perm.SC_SUPER):
                    msg = 'You may not create system or ebase scopes.'
                    raise ValueError(msg)

            else:
                if euser != self.getCurrentUser()[TCN_AUTOID]:
                    raise ValueError('userids do not match.')


    def actionAfterAdd(self, table, descr_dict, REQUEST):
        """\brief Overwritten generic function called after add,
                  checks password, adds zope user"""
        if table == TN_USER:
            password = REQUEST.get('password')
            check    = REQUEST.get('check')
            login    = REQUEST.get(TCN_LOGIN)
            if password and password != check:
                error  = '[Error] SecurityManager: '
                error += 'Password mismatch. Please try again.'
                raise ValueError(self.getErrorDialog( error ))
            
            # create message user if necessary
            m_msgm = self.getHierarchyUpManager(ZM_MM)

            if m_msgm:
                muser = m_msgm.getMUser(descr_dict[TCN_AUTOID])
            

            done = self.addUser(login, password)
            if not done:
                message = 'User was added to database but not to zope '
                message += 'acl_users (already existing or no acl_users found)'
                return message
            else:
                # send mail
                sent = self.mailLogin(REQUEST)
                if sent:
                    message  = 'Login and Password have been '
                    message += 'sent via mail to %s.' % sent
                    return message


    def actionBeforeEdit(self, table, descr_dict, REQUEST):
        """\brief Overwritten generic function called before edit,
                  updates password."""
        if table == TN_USER:
            userid = descr_dict.get(TCN_USERID)
            tobj  = self.tableHandler[TN_USER]
            
            entries = tobj.getEntries(userid, TCN_USERID)
            
            if entries and entries[0][TCN_AUTOID] != descr_dict[TCN_AUTOID]:
                error = 'Login for selected Person already exists.'
                raise ValueError(self.getErrorDialog( error ))
            
            if REQUEST.get('password'):
                done = self.updatePassword(REQUEST.form)
                if done:
                    message = 'Password updated.'
                    # send mail
                    sent = self.mailLogin(REQUEST)
                    if sent:
                        message += ' Login and Password have been '
                        message += 'sent via mail to %s.' % sent
                else:
                    message = 'Password not updated.'
                return message


    def actionBeforeShowList(self, table, param, REQUEST):
        """\brief Overwritten generic function, config the show-list."""
        if table == TN_USER:
            param['show_fields']   = [ TCN_LOGIN,
                                       TCN_USERID,
                                       TCN_LASTLOGIN]
            param['special_field'] = TCN_LOGIN
        elif table == TN_GROUP:
            param['show_fields']   = [ TCN_NAME,
                                       TCN_LEVEL ]
            param['special_field'] = TCN_NAME
        elif table == TN_EBASE:
            param['show_fields']   = [ TCN_NAME ]

        if self.getCurrentLevel() > 8:
            param['with_delete'] = True
            param['with_edit']   = True
        else:
            param['with_delete'] = False
            param['with_edit']   = False
        param['with_show']       = True


    def getSingleMask( self,
                       table,
                       flag = MASK_SHOW,
                       descr_dict = None,
                       prefix = None ):
        """\brief"""
        if table == TN_USER:
            return self.getMaskUser(flag, descr_dict)
        elif table == 'scope':
            return self.getMaskScope(flag, descr_dict)
        else:
            return GenericManager.getSingleMask(self, table, flag, descr_dict, prefix)


    def personalPage(self, embedded = False):
        """\brief"""
        perm = self.getGUIPermission()
        dlg = getStdDialog('Personal Security Page')
        
        # build mask
        mask = hgGroupBox(title = 'General Info', parent = dlg)
        layout = hgGridLayout(mask, 1, 1, 0, 4)
        dlg.add(mask)
        
        # heading
        label = dlgLabel('Messaging and Login Information', parent = mask)
        layout.addMultiCellWidget(label, 0, 0, 0, 3)
        
        row = 1

        # login
        label = dlgLabel('Login', parent = mask)
        layout.addWidget(label, row, 0)
        # get login and name
        login = self.getCurrentLogin()
        user  = self.getUserByLogin(login)
        cmid  = user.get('userid')
        uid   = user[TCN_AUTOID]
        label = hgLabel(login, parent = mask)
        layout.addMultiCellWidget(label, row, row, 2, 3)
        row += 1

        # messages
        m_msgm = self.getManager(ZM_MM)
        if m_msgm:
            label = dlgLabel('Internal Messaging', parent = mask)
            layout.addWidget(label, row, 0)
            link = m_msgm.buildMessageCenterLink(mask)
            if link.getUri():
                # link exists, add '>' to label
                link.setText('> ' + link.getText())
                
            layout.addMultiCellWidget(link, row, row, 2, 3)
            row += 1
            
        # messages
        m_zmbm = self.getManager(ZM_MBM)
        if m_zmbm:
            label = dlgLabel('Internal Forum', parent = mask)
            layout.addWidget(label, row, 0)
            link = hgLabel('> Message Board', m_zmbm.absolute_url(), parent = mask)
            layout.addMultiCellWidget(link, row, row, 2, 3)
            row += 1

        # contact info
        m_contact = self.getManager(ZM_CM)
        if m_contact:
            # mails
            if perm.hasMinimumRole(perm.SC_SUPER):
                # external messaging for superusers
                label = dlgLabel('External Messaging', parent = mask)
                layout.addWidget(label, row, 0)
                url = '%s/dlgHandler/dlgSendMail/show'
                url = url % m_contact.absolute_url()
                link = hgLabel('> Mail Dialog', url, parent = mask)
                layout.addMultiCellWidget(link, row, row, 2, 3)
                row += 1

            # contact info
            label = dlgLabel('Contact Info', parent = mask)
            layout.addWidget(label, row, 0)
            # show
            url = '%s/showForm?table=%s&id=%s'
            url = url % (m_contact.absolute_url(), 'person', cmid)
            link = hgLabel('> Show', url, parent = mask)
            layout.addWidget(link, row, 2)
            # edit
            url = '%s/editForm?table=%s&id=%s'
            url = url % (m_contact.absolute_url(), 'person', cmid)
            link = hgLabel('> Edit', url, parent = mask)
            layout.addWidget(link, row, 3)
            row += 1

        # superuser / admin stuff
        if perm.hasMinimumRole(perm.SC_SUPER):
            # col = 5
            
            # spacer
            #layout.addWidget(hgLabel('&nbsp;', parent = mask), 0, 4)
            layout.setColSpacing(4, 100)
            
            # heading
            label = dlgLabel('Superuser Quicklinks', parent = mask)
            layout.addMultiCellWidget(label, 0, 0, 5, 6)
            
            row = 1
            
            # user list for delete
            url = '%s/showList?table=%s'
            url = url % (self.absolute_url(), TN_USER)
            link = hgLabel('> User List', url, parent = mask)
            layout.addWidget(link, row, 5)
            
            label = dlgLabel('[Delete Logins here]', parent = mask)
            layout.addWidget(label, row, 6)
            row += 1
            
            if m_contact:
                # person list for edit
                url = '%s/showList?table=%s'
                url = url % (m_contact.absolute_url(), 'person')
                link = hgLabel('> Person List', url, parent = mask)
                layout.addWidget(link, row, 5)
                
                label = dlgLabel('[Edit Person Information here]', parent = mask)
                layout.addWidget(label, row, 6)
                
                row += 1
                
                # create person
                url = '%s/newForm?table=%s'
                url = url % (m_contact.absolute_url(), 'person')
                link = hgLabel('> Create Person', url, parent = mask)
                layout.addWidget(link, row, 5)
                
                label = dlgLabel('[Enter new Persons, with login to create a User]', parent = mask)
                layout.addWidget(label, row, 6)
                
                row += 1
                
                # contact manager link
                url = m_contact.absolute_url()
                link = hgLabel('> Contact Manager', url, parent = mask)
                layout.addWidget(link, row, 5)
                
                label = dlgLabel('[Manage Persons / Organisations]', parent = mask)
                layout.addWidget(label, row, 6)
                
                row += 1
            
            # security manager link
            url = self.absolute_url()
            link = hgLabel('> Security Manager', url, parent = mask)
            layout.addWidget(link, row, 5)
            
            label = dlgLabel('[Manage Users / Passwords]', parent = mask)
            layout.addWidget(label, row, 6)

        # ebase scopes
        mask = hgGroupBox(title = 'EBaSe Scopes', parent = dlg)
        layout = hgGridLayout(mask, 1, 1, 0, 4)
        dlg.add(mask)
        self.listScopes(uid, mask)

        # system scopes
        mask = hgGroupBox(title = 'System Scopes', parent = dlg)
        layout = hgGridLayout(mask, 1, 1, 0, 4)
        dlg.add(mask)
        self.listScopes(0, mask)

        mask = hgGroupBox(title = 'Access Roles Settings', parent = dlg)
        layout = hgGridLayout(mask, 1, 1, 0, 4)
        dlg.add(mask)
        # build mask
        # get global role
        groleid = perm.generalrole
        if groleid:
            label = dlgLabel('Global Role', mask)
            layout.addWidget(label, 0, 0)
            grole = perm.rolenames[groleid]
            label = hgLabel(grole, parent = mask)
            layout.addWidget(label, 0, 1)
        # get special roles
        row = 2
        special = perm.specialroles.keys()
        if special:
            label = dlgLabel('Special Roles', mask)
            layout.addWidget(label, row, 0)
        for entry in special:
            label = hgLabel(entry, parent = mask)
            layout.addWidget(label, row, 1)
            row += 1
        row += 1
        # get scopes and roles
        label = dlgLabel('SBAR', mask)
        layout.addWidget(label, row, 0)
        label = hgLabel('scope', parent = mask)
        layout.addWidget(label, row, 1)
        label = hgLabel('role', parent = mask)
        layout.addWidget(label, row, 2)
        sobj = self.tableHandler[TN_ROLESCOPE]
        roles = sobj.getEntries(uid, TCN_EUSER)
        for role in roles:
            row += 1
            scope = self.getLink(TN_SCOPE, role[TCN_SCOPEID], parent = mask)
            layout.addWidget(scope, row, 1)
            role = perm.rolenames.get(role[TCN_ROLE])
            label = hgLabel(role, parent = mask)
            layout.addWidget(label, row, 2)
        if embedded:
            dlg.setHeader('')
            dlg.setFooter('')
            return dlg
        else:
            return HTML(dlg.getHtml())(self, None)


    def listScopes(self, uid, mask):
        """\brief"""
        perm = self.getGUIPermission()
        # edit link for normal user on own scopes
        # or superuser on system scopes
        if (uid != 'NULL' and uid != 0 and uid != '0') or perm.hasMinimumRole(perm.SC_SUPER):
            edit = True
        else:
            edit = False
        # build mask
        layout = mask.layout()
        sobj = self.tableHandler[TN_SCOPE]
        # get scopes
        scopes = sobj.getEntries(uid, TCN_EUSER)
        row = 0

        if not scopes:
            msg = 'No scopes defined.'
            label = hgLabel(msg, parent = mask)
            layout.addWidget(label, row, 0)
            row += 1

        for scope in scopes:
            # name
            label = dlgLabel(scope.get(TCN_NAME), parent = mask)
            layout.addWidget(label, row, 0)
            # show link
            url = '%s/showForm?table=%s&id=%s'
            url = url % (self.absolute_url(), TN_SCOPE, scope[TCN_AUTOID])
            link = hgLabel('show', url, mask)
            layout.addWidget(link, row, 1)
            # edit link
            if edit:
                url = '%s/editForm?table=%s&id=%s'
                url = url % (self.absolute_url(), TN_SCOPE, scope[TCN_AUTOID])
                link = hgLabel('edit', url, mask)
                layout.addWidget(link, row, 2)
                row += 1
        if edit and perm.hasPermission(perm.SC_INSERT):
            # create link
            url = '%s/newForm?table=%s&euser=%s'
            url = url % (self.absolute_url(), TN_SCOPE, uid)
            link = hgLabel('Create New', url, parent = mask)
            layout.addMultiCellWidget(link, row + 1, row + 1, 0, 2)


    def sbarPage(self):
        """\brief"""
        # superuser only
        perm = self.getGUIPermission()
        if not perm.hasMinimumRole(perm.SC_SUPER):
            # raise Error
            pass

        # show sbar scopes
        title = 'Scope Based Access Roles (SBAR)'
        dlg = getStdDialog(title = title)
        mask = hgGroupBox(title = 'Scopes', parent = dlg)
        layout = hgGridLayout(mask, 1, 1, 0, 4)
        dlg.add(mask)
        self.listScopes('NULL', mask)
        # add scope
        

        return HTML(dlg.getHtml())(self, None)


    def getMaskScope(self, flag, descr_dict):
        if descr_dict:
            scope = descr_dict
        else:
            scope = {}
        tem = [[None, None],
               [GEN_LABEL + 'name',      'name'     ],
               [GEN_LABEL + 'isdefault', 'isdefault']]

        mask = self.buildSemiGenericMask( 'scope',
                                          tem,
                                          flag,
                                          scope )
        layout = mask.layout()

        # type for add for superusers
        # superusers / admins see a selection for
        # user scope / EBaSe Creation Mask scope / SBAR-scope
        perm = self.getGUIPermission()
        if perm.hasMinimumRole(perm.SC_SUPER):
            label = hgLabel('Scope Type', parent = mask)
            layout.addWidget(label, 3, 0)
            if flag & MASK_ADD:
                prop = hgProperty('euser', scope.get('euser'), parent = mask)
                layout.addWidget(prop, 3, 2)
            if 'euser' in scope:
                uid = scope['euser']
                if uid == 0 or uid == '0':
                    lab = 'system scope'
                elif uid == 'NULL':
                    lab = 'SBAR scope'
                else:
                    lab = 'user scope'
                label = hgLabel(lab, parent = mask)
                layout.addWidget(label, 3, 1)

        elif flag & MASK_ADD:
            uid = self.getCurrentUser()[TCN_AUTOID]
            prop = hgProperty('euser', str(uid), parent = mask)
            layout.addWidget(prop, 3, 1)

        # show link for edit / add
        if flag & (MASK_EDIT | MASK_ADD) and scope.get(TCN_AUTOID):
            url = '%s/showForm?table=scope&id=%s'
            url = url % (self.absolute_url(), scope[TCN_AUTOID])
            label = hgLabel('Show', url, parent = mask)
            layout.addWidget(label, 0, 1)

        autoid = scope.get(TCN_AUTOID)
        if autoid and (flag & (MASK_SHOW | MASK_EDIT)):
            # get scope defs
            defs = self.tableHandler['scopedef'].getEntries(autoid, 'scopeid')
            sub = self.getMaskScopedef(flag, defs, scope.get('newdef'), mask)
            layout.addMultiCellWidget(sub, 4, 4, 0, 2)

            uid = scope['euser']
            if uid or uid == 0:
                # creation masks
                groups, users = self.getPermForScope(autoid)
                mask1 = self.getEBaSeMask(users, True, False, mask)
                layout.addMultiCellWidget(mask1, 5, 5, 0, 2)
                mask2 = self.getEBaSeMask(groups, False, False, mask)
                layout.addMultiCellWidget(mask2, 6, 6, 0, 2)
                if uid or perm.hasMinimumRole(perm.SC_SUPER):
                    # creation mask edit link
                    label = 'Edit creation mask for this scope'
                    url   = '%s/creationMaskEditForm?scopeid=%s'
                    url   = url % (self.absolute_url(), autoid)
                    lab = hgLabel(label, url, parent = mask)
                    layout.addMultiCellWidget(lab, 7, 7, 0, 2)
            else:
                # SBAR scope
                users = self.getUserRolesForScope(autoid)
                mask1 = self.getSBARMask(users, False, mask)
                layout.addMultiCellWidget(mask1, 5, 5, 0, 2)
                if perm.hasMinimumRole(perm.SC_SUPER):
                    # SBAR edit link
                    label = 'Edit Access Roles for this scope'
                    url   = '%s/sbarEditForm?scopeid=%s'
                    url   = url % (self.absolute_url(), autoid)
                    lab = hgLabel(label, url, parent = mask)
                    layout.addMultiCellWidget(lab, 6, 6, 0, 2)
        return mask


    def getMaskScopedef(self, flag, defs, newdef = None, parent = None):
        mask = hgGroupBox(title = 'Scope Parts', parent = parent)
        layout = hgGridLayout(mask, 1, 1, 0, 4)
        # add scopes
        tabids = self.loadTableIds()
        # header
        

        row = 1
        for entry in defs:
            tabid = entry['tableid']
            ztype = entry['zopratype']
            hint = tabids.get(tabid)
            if hint:
                cname = hint[0]
                tname = hint[1]
            else:
                cname = ''
                tname = ''

            label = hgLabel(cname, parent = mask)
            layout.addWidget(label, row, 0)
            label = hgLabel(ztype, parent = mask)
            layout.addWidget(label, row, 2)
            label = hgLabel(tname, parent = mask)
            layout.addWidget(label, row, 4)

            if flag & MASK_EDIT:
                # remove button
                name = DLG_FUNCTION + 'remscopedef%s' % entry[TCN_AUTOID]
                button = hgPushButton('Remove', name, parent = mask)
                layout.addWidget(button, row, 5)

            row += 1

        # edit
        if flag & MASK_EDIT:
            row += 1
            # new scopedef
            mgr = None
            if newdef:
                if newdef.get('mgr_select'):
                    mgr = newdef['mgr_select']
            else:
                newdef = {}

            # manager select
            if mgr:
                widg = hgProperty('mgr_select', mgr, True, parent = mask)
                layout.addWidget(widg, row, 0)

                # zopratype select
                ztype = newdef.get('zt_select')
                dotable = False
                if ztype:
                    widg = hgProperty('zt_select', ztype, True, parent = mask)
                    layout.addWidget(widg, row, 2)
                    if ztype != '--any--':
                        dotable = True
                elif mgr != '--any--':
                    widg = self.getZopraTypeSelector(mgr, mask)
                    if widg:
                        # zopratype found
                        layout.addWidget(widg, row, 2)
                        button = hgPushButton('>', DLG_FUNCTION + 'zt_select', parent = mask)
                        layout.addWidget(button, row, 3)
                    else:
                        # no zt found, show table selector
                        dotable = True
                if dotable:
                    tabid = newdef.get('tab_select')
                    if tabid:
                        widg = hgProperty('tab_select', tabid, True, parent = mask)
                        layout.addWidget(widg, row, 4)
                    else:
                        widg = self.getTableSelector(mgr, ztype, mask)
                        layout.addWidget(widg, row, 4)
            else:
                widg = self.getManagerSelector(mask)
                layout.addWidget(widg, row, 0)
                button = hgPushButton('>', DLG_FUNCTION + 'mgr_select', parent = mask)
                layout.addWidget(button, row, 1)

            # add button
            button = hgPushButton('Add', DLG_FUNCTION + 'Add', parent = mask)
            layout.addWidget(button, row, 5)
            # discard button
            button = hgPushButton('Discard', DLG_FUNCTION + 'Discard', parent = mask)
            layout.addWidget(button, row, 6)

        return mask


    def addNewScopeDef(self, newdef, scopeid):
        mgr = newdef.get('mgr_select')
        if mgr == '--any--':
            to_add = self.loadTableIds()
        else:
            ztype = newdef.get('zt_select')
            if ztype == '--any--':
                to_add = self.loadTableIds(mgr)
            else:
                tab = newdef.get('tab_select')
                if tab == '--any--':
                    to_add = self.loadTableIds(mgr, ztype)
                else:
                    # one tab, one zt
                    to_add = {tab: (mgr, None, ztype)}

        tobj = self.tableHandler['scopedef']
        for tabid in to_add.keys():
            values = to_add[tabid]
            ztype  = values[2]
            entry = {'scopeid': scopeid,
                     'tableid': tabid,
                     'zopratype': ztype}
            tobj.addEntry(entry)


    def getManagerSelector(self, parent):
        box = hgComboBox(name = 'mgr_select', parent = parent)
        box.insertItem('--any--')
        mgrs = self.getAllManagersHierarchyDown()
        names = {}
        for mgr in mgrs:
            cname = mgr.getClassName()
            if cname not in names:
                names[cname] = None
                box.insertItem(cname)
        return box


    def getZopraTypeSelector(self, manager, parent):
        box = hgComboBox(name = 'zt_select', parent = parent)
        box.insertItem('--any--')
        mgrs = self.getAllManagersHierarchyDown(classname = manager)
        found = False
        for mgr in mgrs:
            ztype = mgr.getZopraType()
            if ztype:
                found = True
                box.insertItem(ztype)
        if not found:
            return None
        return box


    def getTableSelector(self, manager, zopratype, parent):
        box = hgComboBox(name = 'tab_select', parent = parent)
        box.insertItem('--any--')
        mgr = self.getHierarchyDownManager(manager, None, zopratype)
        if mgr:
            for tname in mgr.tableHandler.keys():
                tobj = mgr.tableHandler[tname]
                uid = tobj.getUId()
                label = tobj.getLabel()
                if uid and label:
                    box.insertItem(label, str(uid))
        return box


    def loadTableIds(self, manager = None, zopratype = None):
        # get All Managers
        mgrs = self.getAllManagersHierarchyDown(zopratype, manager)
        res = {}
        for mgr in mgrs:
            # get ztype
            ztype = mgr.getZopraType()
            # get their tables
            for tname in mgr.tableHandler.keys():
                tobj = mgr.tableHandler[tname]
                uid = tobj.getUId()
                if uid:
                    # store id -> classname
                    res[uid] = (mgr.getClassName(), tname, ztype)
        return res


    def creationMaskEditForm(self, scopeid, REQUEST):
        """\brief Creation Mask edit form."""
        # get table object
        cobj = self.tableHandler['creationmask']

        # test buttons
        button = self.getPressedButton(REQUEST)
        remove = getPressedButton(REQUEST, 'remove_')
        if button or remove:
            # get groups / users from request
            users = {}
            groups = {}
            glist = REQUEST.get('secg')
            if glist:
                if not isinstance(glist, ListType):
                    glist = [glist]
                for group in glist:
                    if not group:
                        continue
                    perms = REQUEST.get('perm_g%s' % group)
                    padd = []
                    if perms:
                        if not isinstance(perms, ListType):
                            perms = [perms]
                        for single in perms:
                            padd.append(int(single))
                    groups[int(group)] = padd

            ulist = REQUEST.get('secu')
            if ulist:
                if not isinstance(ulist, ListType):
                    ulist = [ulist]
                for user in ulist:
                    perms = REQUEST.get('perm_u%s' % user)
                    padd = []
                    if perms:
                        if not isinstance(perms, ListType):
                            perms = [perms]
                        for single in perms:
                            padd.append(int(single))
                    users[int(user)] = padd

            # now evaluate buttons
            if button == 'sec_gadd':
                # add group
                groupid = REQUEST.get(TCN_EGROUP)
                if groupid != 'NULL':
                    groupid = int(groupid)
                    if groupid not in groups:
                        groups[groupid] = []
            elif button == 'sec_uadd':
                # add user
                userid = REQUEST.get(TCN_EUSER)
                if userid != 'NULL':
                    userid = int(userid)
                    if userid not in users:
                        users[userid] = []
            elif remove:
                remove = remove[0]
                stype = remove[0]
                theid = int(remove[1:])
                if stype == 'g':
                    # remove group
                    if theid in groups:
                        del groups[theid]
                else:
                    # remove user
                    if theid in users:
                        del users[theid]

            elif button == 'OK':
                # get entry for scopeid
                cmasks = cobj.getEntries(scopeid, 'scopeid')
                # generate acl for groups and users
                acl = self.foldEBaSe(groups, users)
                # test existing creation mask entry
                if cmasks:
                    cmask = cmasks[0]
                    cmask['acl'] = acl
                    cobj.updateEntry(cmask, cmask[TCN_AUTOID])
                else:
                    cmask = { 'scopeid': scopeid,
                              'acl': acl}
                    cobj.addEntry(cmask)

                # forward to scope show form
                return self.showForm(scopeid, 'scope', {})

        else:
            # first call
            groups, users = self.getPermForScope(scopeid)

        # header labels
        slabel = self.getLabelString('scope', scopeid)
        heading = 'Edit EBaSe Creation Mask for Scope %s' % (slabel)
        url = '%s/creationMaskEditForm' % self.absolute_url()

        dlg = getStdDialog(heading, url)
        # build permission mask
        mask1 = self.getEBaSeMask(users, True, True, dlg)
        dlg.add(mask1)
        mask2 = self.getEBaSeMask(groups, False, True, dlg)
        dlg.add(mask2)

        # scopeid
        autoprop = hgProperty('scopeid', scopeid, parent = dlg)
        dlg.add(autoprop)

        # ok-button
        button = hgPushButton('OK', DLG_FUNCTION + 'OK', parent = dlg)
        dlg.add(button)

        button = self.getBackButton(parent = dlg)
        dlg.add(button)

        # return html
        return HTML(dlg.getHtml())(self, None)


    def sbarEditForm(self, scopeid, REQUEST):
        """\brief"""
        # get table object
        robj = self.tableHandler[TN_ROLESCOPE]
        #scopeid, euser, role

        # test buttons
        button = self.getPressedButton(REQUEST)
        remove = getPressedButton(REQUEST, 'remove_')
        if button or remove:
            # get users from request
            users = {}

            ulist = REQUEST.get('secuser')
            if ulist:
                if not isinstance(ulist, ListType):
                    ulist = [ulist]
                for user in ulist:
                    role = REQUEST.get('role_%s' % user, 0)
                    users[int(user)] = role

            if button == 'sec_add':
                # add user
                userid = REQUEST.get(TCN_EUSER)
                if userid != 'NULL':
                    userid = int(userid)
                    if userid not in users:
                        users[userid] = 0

            elif remove:
                rem = int(remove[0])
                # remove user
                if rem in users:
                    del users[rem]

            elif button == 'OK':
                # get entry for scopeid
                rs_map = robj.getEntries(scopeid, TCN_SCOPEID)
                # test existing creation mask entry
                for entry in rs_map:
                    userid = entry['euser']

                    if userid in users:
                        # compare role
                        new_role = users[userid]
                        old_role = entry[TCN_ROLE]
                        if new_role != old_role:
                            # update
                            entry[TCN_ROLE] = new_role
                            robj.updateEntry(entry, entry[TCN_AUTOID])
                        # remove from users
                        del users[userid]

                    else:
                        # delete entry
                        robj.deleteEntry(entry[TCN_AUTOID])

                rest = users.keys()
                # new entries
                for user in rest:
                    # create entry
                   rs_new = { TCN_SCOPEID: scopeid,
                              TCN_EUSER: user,
                              TCN_ROLE: users[user] }
                   robj.addEntry(rs_new)

                # forward to scope show form
                return self.showForm(scopeid, 'scope', {})

        else:
            # first call
            users = self.getUserRolesForScope(scopeid)

        # header labels
        slabel = self.getLabelString('scope', scopeid)
        heading = 'Edit Access Roles for Scope %s' % (slabel)
        url = '%s/sbarEditForm' % self.absolute_url()

        dlg = getStdDialog(heading, url)
        # build permission mask
        mask = self.getSBARMask(users, True, dlg)
        dlg.add(mask)

        # scopeid
        autoprop = hgProperty('scopeid', scopeid, parent = dlg)
        dlg.add(autoprop)

        # ok-button
        button = hgPushButton('OK', DLG_FUNCTION + 'OK', parent = dlg)
        dlg.add(button)

        button = self.getBackButton(parent = dlg)
        dlg.add(button)

        # return html
        return HTML(dlg.getHtml())(self, None)


    def getMaskUser(self, flag = MASK_SHOW, descr_dict = None):

        if descr_dict:
            user = descr_dict
        else:
            user = {}

        G = GEN_LABEL
        tem = [[G + TCN_LOGIN,  TCN_LOGIN  ],
               [None,           None       ],
               [None,           None       ],
               [G + TCN_USERID, None       ],
               [G + TCN_GROUPS, TCN_GROUPS ],
               [G + TCN_EBASE,  TCN_EBASE  ]]
        mask = self.buildSemiGenericMask( TN_USER,
                                          tem,
                                          flag,
                                          user )
        layout = mask.layout()

        if flag & MASK_EDIT:
            # login not editable (except admins)
            if self.getCurrentLevel() < 100:
                widg = mask.child(TCN_LOGIN)
                layout.remove(widg)
                widg = hgProperty(TCN_LOGIN, user.get(TCN_LOGIN), True, mask)
                layout.addWidget(widg, 0, 1)

        # show only contacts not yet assigned
        entry = self.getFunctionWidget(TN_USER,
                                       TCN_USERID,
                                       mask,
                                       flag,
                                       user)
        
        if flag & (MASK_ADD | MASK_EDIT):
            # adjust contact list
            widget_list = entry.getItemList()
            contact_list = []
            for item in widget_list:
                contact_list.append(item[1])
                
            contact_list.sort()
            
            # current db value stays in list
            if flag & MASK_EDIT and \
               user.get(TCN_AUTOID):
                db_user = self.tableHandler[TN_USER].getEntry(user[TCN_AUTOID])
                # should always be true
                if db_user[TCN_USERID] in contact_list:
                    contact_list.remove(db_user[TCN_USERID])
            
            user_list = self.tableHandler[TN_USER].getEntries()
            
            # remove used contacts from contact widget
            for user in user_list:
                cm_id = user.get(TCN_USERID)
                
                if cm_id:
                    if cm_id in contact_list:
                        entry.removeItemByValue(cm_id)
            
            # password
            lab = dlgLabel('Password', parent = mask)
            layout.addWidget(lab, 1, 0)
            lab = dlgLabel('Reenter Password', parent = mask)
            layout.addWidget(lab, 2, 0)

            widg = hgLineEdit(name  = 'password', parent = mask)
            widg.setEchoMode(widg.Password)
            layout.addWidget(widg, 1, 1)

            widg = hgLineEdit(name  = 'check', parent = mask)
            widg.setEchoMode(widg.Password)
            layout.addWidget(widg, 2, 1)

            # mail new password
            lab = dlgLabel('Send Mail with new Password', parent = mask)
            layout.addWidget(lab, 6, 0)
            widg = hgCheckBox('', '1', mask, 'sendmail')
            layout.addWidget(widg, 6, 1)
            
        # add contact selection widget
        layout.addWidget(entry, 3, 1)
            

        return mask

    def test(self):
        """\brief test"""
        usr = self.getEntry(TN_USER, 1)
        raise ValueError(usr)

    def startupConfig(self, REQUEST):
        """\brief Add Admin group and current user as Admin."""

        # Since it is the first user in the DB, we assume the ids as 1
        # (and 2 for CM, where 1 is anonymous)

        # TODO find a way to determine Contact-Manager-Personid
        gobj = self.tableHandler[TN_GROUP]
        auto = gobj.addEntry( { TCN_NAME : 'Admin',     TCN_LEVEL     : 100 } )
        gobj.addEntry( { TCN_NAME : 'Superuser', TCN_LEVEL     : 10 } )
        gobj.addEntry( { TCN_NAME : 'User',      TCN_LEVEL     : 8 } )
        gobj.addEntry( { TCN_NAME : 'Visitor',   TCN_LEVEL     : 4 } )
        #self.tableHandler[TN_EBASE].addEntry( { TCN_NAME : 'All' } )
        self.tableHandler[TN_USER].addEntry( { TCN_LOGIN  : self.getCurrentLogin(),
                                               TCN_USERID : 2,
                                               TCN_GROUPS : [auto] } )
        self.tableHandler[TN_USER].cache.invalidate(1)
