# /*################################################################################################
#    Copyright (C) 2004-2016 by ZopRATec GbR                                                       #
#    <ingo.keller@zopratec.de>                                                                     #
#                                                                                                  #
#    This file is part of zopra.core (ZopRA).                                                      #
#                                                                                                  #
#    zopra.core is free software: you can redistribute it and/or modify it under the terms of the  #
#    GNU General Public License as published by the Free Software Foundation, either               #
#    version 2 of the License, or (at your option) any later version.                              #
#                                                                                                  #
#    zopra.core is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;       #
#    without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.     #
#    See the GNU General Public License for more details.                                          #
#                                                                                                  #
#    You should have received a copy of the GNU General Public License                             #
#    along with zopra.core.  If not, see <http://www.gnu.org/licenses/>.                           #
####################################################################################################

# TODO: make permission and owner private


class EntryPermission:
    """ The EntryPermission class provides a permission container for the entry based security
        implementation.

    The entry permission object gets created in the Table.getEntry() method and is added to an entry
    dictionary. It can be accessed from the entry dictionary via entry['permission'].

    @see zopra.core.tables.Table.Table
    """

    # TODO: adjust the className, the original (secEntryPermission) has a typo
    #       anyways
    _className = 'seqEntryPermission'
    _classType = [_className]


    def __init__(self, entry, permissions, owner = False):
        """ Constructs an EntryPermission object.

        @param entry        - corresponding entry.
        @param permissions  - list of user permissions.
        @param owner        - True if the entry is owned by the user; default False.
        """
        # build checksum

        # store permissions
        tmp = 0
        for perm in permissions:
            tmp = tmp | perm

        self.permission = tmp
        self.owner      = owner


    def hasPermission(self, permission):
        """ Returns True if the permission is valid for the corresponding entry.

        @param permissions  - permission to be checked for the entry.
        @return boolean     - True if the permission exist in the entry; otherwise False
        """
        return self.permission & permission


    def isOwner(self):
        """ Returns True if the corresponding entry is owned by the user.

        @return boolean - True if the entry is owned by the user; otherwise False
        """
        return self.owner
