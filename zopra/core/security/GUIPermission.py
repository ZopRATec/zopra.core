from builtins import object

from zopra.core.types import ListType


class GUIPermission(object):
    """The GUIPermission class provides a container for UI related permission settings.

    It allows to set permissions based on roles.

    Roles:
        Visitor; User; Superuser; Admin

    Permissions:
        View; Insert; Edit; Delete

    Permission Matrix:
        Role      | Permissions
        --------- | -----------
        Visitor   | View
        User      | View, Insert, Edit
        Superuser | View, Insert, Edit
        Admin     | View, Insert, Edit, Delete

    """

    _className = "GUIPermission"
    _classType = [_className]

    roleNames = ["Visitor", "User", "Superuser", "Admin"]
    SC_VISITOR = 1
    SC_USER = 2
    SC_SUPER = 3
    SC_ADMIN = 4
    roles = {"Visitor": 1, "User": 2, "Superuser": 3, "Admin": 4}
    rolenames = {1: "Visitor", 2: "User", 3: "Superuser", 4: "Admin"}

    SC_VIEW = 1
    SC_INSERT = 2
    SC_EDIT = 3
    SC_DELETE = 4

    permissionmapping = {
        SC_VISITOR: (SC_VIEW),
        SC_USER: (SC_VIEW, SC_INSERT, SC_EDIT),
        SC_SUPER: (SC_VIEW, SC_INSERT, SC_EDIT),
        SC_ADMIN: (SC_VIEW, SC_INSERT, SC_EDIT, SC_DELETE),
    }

    def __init__(self, login, global_roles, access_enabled, access_roles):
        """Constructs a GUIPermission object.

        @param login
        @param global_roles
        @param access_enabled - { <unique-table-id>: None | [ zopratype* ] }
        @param access_roles
        """
        # TODO: build checksum
        # TODO: translate table roles to permissions
        self.generalrole = None
        self.specialroles = {}
        self.generalpermissions = {}
        self.tableroles = access_roles
        self.tablepermissions = {}
        self.enabled = access_enabled

        # check global roles (Visitor, User, Superuser, Admin + additional roles)
        for entry in global_roles:
            if entry in self.roles:

                # highest role stored only
                role = self.roles[entry]
                if not self.generalrole or role > self.generalrole:
                    self.generalrole = role
            else:
                # a special role
                self.specialroles[entry] = None

        # translate global roles to permissions
        if self.generalrole:

            for entry in self.permissionmapping[self.generalrole]:
                self.generalpermissions[entry] = None

    def hasPermission(self, permission, tableid=None, zopratype=None):
        """Returns True if the access to the given table and ZopRA-Type can be granted.

        @param permission - Permission to be checked
        @param tableid    - Table ID for the table on which the permission needs to be checked.
        @param zopratype  - ZopRA-Type for which the permission needs to be checked.
        @result boolean - True if permission is valid; otherwise False.
        """
        if self.isAccessEnabled(tableid, zopratype):

            # check for admin
            if self.generalrole == self.SC_ADMIN:
                return True

            # look in tableroles, get role
            role = self.tableroles.get([tableid, zopratype])

            # check permission
            return permission in self.permissionmapping[role] if role else False

        else:

            # look in general permissions
            return permission in self.generalpermissions

    def hasRole(self, role, tableid=None, zopratype=None):
        """Returns whether the user has the given role for the table and ZopRA-Type or not.

        @param role       - Role that needs to be checked.
        @param tableid    - Table ID for the table on which the permission needs to be checked.
        @param zopratype  - ZopRA-Type for which the permission needs to be checked.
        @return boolean   - True if user has the requested role; otherwise False.
        """
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

    def hasMinimumRole(self, role, tableid=None, zopratype=None):
        """Returns for the minimal role of a user.

        Roles are traditionally ordered and higher roles include lower the check is similar to the
        older secMgr.hasMinimumRole but the int values changed

        @param role       - Role that needs to be checked.
        @param tableid    - Table ID for the table on which the permission needs to be checked.
        @param zopratype  - ZopRA-Type for which the permission needs to be checked.
        @return boolean   - True if user has the requested role; otherwise False.
        """
        if self.isAccessEnabled(tableid, zopratype):

            # check for Administrator role or look in table roles
            return (
                self.generalrole == self.SC_ADMIN
                or self.tableroles.get([tableid, zopratype]) >= role
            )

        else:

            # look in general permissions if table is not enabled
            return self.generalrole >= role

    def hasSpecialRole(self, role):
        """Returns whether the user has a special global role.

        This is used to retain the old handling of having ZopRA-Type + 'Superuser' - Roles (used
        like a light-weight SBAR)

        @param  role      - Role that needs to be checked.
        @return boolean   - True if user has a special role; otherwise False.
        """
        return role in self.specialroles

    def isAccessEnabled(self, tableid, zopratype):
        """Returns True if access for the given table and ZopRA-Type can be granted.

        Order of checks:
        1. Is the Table ID in the enabled table?
        2. Is ZopRA-Type ignored or is ZopRA-Type in list of the enabled tables?

        If all conditions are met the access can be granted.

        @param tableid    - Table ID to which the access is requested.
        @param zopratype  - ZopRA-Type to which the access is requested.
        @result boolean   - True if access can be granted; otherwise False
        """

        # check enabled - dict for managerid / zopratype
        if tableid not in self.enabled:
            return False

        ztypes = self.enabled[tableid]

        return not zopratype or (isinstance(ztypes, ListType) and zopratype in ztypes)
