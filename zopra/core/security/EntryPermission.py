############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################


class EntryPermission:
    """\brief Entry Permission Class"""

    # TODO: adjust the className, the original (secEntryPermission) has a typo
    #       anyways
    _className = 'seqEntryPermission'
    _classType = [_className]

    def __init__(self, entry, permissions, owner = False):
        # build checksum

        # store permissions
        tmp = 0
        for perm in permissions:
            tmp = tmp | perm

        self.permission = tmp
        self.owner = owner


    def hasPermission(self, permission):
        return self.permission & permission


    def isOwner(self):
        return self.owner
