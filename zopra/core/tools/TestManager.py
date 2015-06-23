############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from zopra.core                      import ZM_TEST
from zopra.core.tools.GenericManager import GenericManager, GEN_LABEL, MASK_SHOW

A = 'frl_singlefilter'
B = 'frl_multifilter'
C = 'frl_singlerange'
D = 'frl_multirange'
E = 'frl_singlerafil'
F = 'frl_multirafil'


class TestManager(GenericManager):
    """ Test Manager """
    _className = ZM_TEST
    _classType = GenericManager._classType + [_className]
    meta_type  = _className

    # generic addForm hints
    suggest_id    = 't_manager'
    suggest_name  = 'Test Manager'

    _dlgs         = GenericManager._dlgs + (('dlgMultiEdit', ''),)

    def getSingleMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None, parent = None):
        """\brief Returns one single Line-Mask."""
        G = GEN_LABEL

        tmp = [ [G + A,  A,    None, G + B,  B   ],
                [None,   None, None, None,   None],
                [G + C,  C,    None, G + D,  D   ],
                [None,   None, None, None,   None],
                [G + E,  E,    None, G + F,  F   ]]
        mask = self.buildSemiGenericMask( table,
                                          tmp,
                                          flag,
                                          descr_dict,
                                          prefix,
                                          parent = parent)
        return mask

    def actionBeforeShowList(self, table, param, REQUEST):
        """\brief Dummy Function called before showList
           \param param is a dict which can be filled with default flags
                        changing the showList behaviour.
                        Non-present keys will be filled in by showList with own default values.
                  Available keys for param-dict:
                  with_edit: True or False
                  with_show: True or False
                  with_delete: True or False
                  with_basket: True or False
                  with_autoid_navig: True or False
                  show_fields: [fieldlist]
                  constraints: additional constraints {key:value}
                  links: {name: link_dict} (additional link for each entry in the
                                            following format)
                         { link: url_base (leave out for label instead link),
                           field:<attr> (for url_addition / display),
                           check:<fun_name> (for calcs/checks,
                                             returns new id or label)
                         }
                  special_field: name of the main attribute (used for col 1 and initial ordering)
        """
        param['with_multiedit'] = True
