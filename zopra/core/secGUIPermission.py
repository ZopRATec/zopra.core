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


class secGUIPermission:
    """\brief Entry Permission Class"""
    _className = 'seqGUIPermission'
    _classType = [_className]
    roleNames = ['Visitor', 'User', 'Superuser', 'Admin']
    SC_VISITOR = 1
    SC_USER    = 2
    SC_SUPER   = 3
    SC_ADMIN   = 4
    roles = {   'Visitor':   1,
                'User':      2,
                'Superuser': 3,
                'Admin':     4 }
    rolenames = {1: 'Visitor',
                 2: 'User',
                 3: 'Superuser',
                 4: 'Admin' }
    SC_VIEW   = 1
    SC_INSERT = 2
    SC_EDIT   = 3
    SC_DELETE = 4

    permissionmapping = { SC_VISITOR:   [SC_VIEW],
                          SC_USER:      [SC_VIEW, SC_INSERT, SC_EDIT],
                          SC_SUPER:     [SC_VIEW, SC_INSERT, SC_EDIT],
                          SC_ADMIN:     [SC_VIEW, SC_INSERT, SC_EDIT, SC_DELETE]}

    def __init__(self, login, global_roles, access_enabled, access_roles):
        # #TODO build checksum
        # #TODO translate table roles to permissions
        self.generalrole = None
        self.specialroles = {}
        self.generalpermissions = {}
        self.tableroles = access_roles
        self.tablepermissions = {}
        self.enabled = access_enabled

        # check global roles (Visitor, User, Superuser, Admin + additional roles)
        for entry in global_roles:
            if entry in self.roles:
                # hightest role stored only
                role = self.roles[entry]
                if not self.generalrole or role > self.generalrole:
                    self.generalrole = role
            else:
                # a special role
                self.specialroles[entry] = None
        # translate global roles to permissions
        if self.generalrole:
            permissions = self.permissionmapping[self.generalrole]
            for entry in permissions:
                self.generalpermissions[entry] = None


    def hasPermission(self, permission, tableid = None, zopratype = None):
        if self.isAccessEnabled(tableid, zopratype):
            # check for admin
            if self.generalrole == self.SC_ADMIN:
                return True
            # look in tableroles, get role
            role = self.tableroles.get([tableid, zopratype])
            if role:
                # check permission
                return permission in self.permissionmapping[role]
            else:
                return False
        else:
            # look in general permissions
            return permission in self.generalpermissions


    def hasRole(self, role, tableid = None, zopratype = None):
        if self.isAccessEnabled(tableid, zopratype):
            # check for admin
            if role == self.SC_ADMIN:
                # admin is always allowed, you can never shut out the admin
                return self.generalrole == self.SC_ADMIN
            # look in tableroles
            return self.tableroles.get([tableid, zopratype]) == role
        else:
            # look in general roles
            return self.generalrole == role


    def hasMinimumRole(self, role, tableid = None, zopratype = None):
        # roles are traditionally ordered and higher roles include lower
        # the check is similar to the older secMgr.hasMinimumRole but the int values changed
        if self.isAccessEnabled(tableid, zopratype):
            # check for admin
            if self.generalrole == self.SC_ADMIN:
                return True
            # look in tableroles
            return self.tableroles.get([tableid, zopratype]) >= role
        else:
            # look in general permissions
            return self.generalrole >= role


    def hasSpecialRole(self, role):
        # check special global roles
        # this is here to retain the old handling of having zopratype+'Superuser' - Roles
        # (used like a light-weight SBAR)
        return role in self.specialroles


    def isAccessEnabled(self, tableid, zopratype):
        # check enabled - dict for managerid / zopratype
        if tableid not in self.enabled:
            return False
        else:
            ztypes = self.enabled[tableid]
            if not zopratype:
                return True
            elif isinstance(ztypes, ListType) and zopratype in ztypes:
                return True
            else:
                return False
