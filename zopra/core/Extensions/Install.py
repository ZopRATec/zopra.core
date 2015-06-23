##################################################################################
#
#    Copyright (C) 2010 ZopRATec, All rights reserved.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
##################################################################################
# TODO: Check what really belongs here

from StringIO                               import StringIO

from Products.Archetypes.Extensions.utils   import install_subskin


def install(self):
    """ External Method to install ZopRA into a CMF Site """

    out = StringIO()
    print >> out, "Installation log of ZMOM:"

    globals()['__name__'] = 'zopra.core'
    install_subskin(self, out, globals())
    print >> out, "Installed subskin"

    return out.getvalue()


def uninstall(self):
    pass
