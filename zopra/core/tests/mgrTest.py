############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
"""The second test manager for tests with templates, layout is similar to TestManager 
(but reduced, because the options for different list types are reduced with templates)"""

from zopra.core import ZM_TEST2
from zopra.core.tools.TemplateBaseManager import TemplateBaseManager


class mgrTest(TemplateBaseManager):
    """ Test 2 Manager """

    _className = ZM_TEST2
    _classType = TemplateBaseManager._classType + [_className]
    meta_type = _className

    # generic addForm hints
    suggest_id = "testapp"
    suggest_name = "Test Manager"
