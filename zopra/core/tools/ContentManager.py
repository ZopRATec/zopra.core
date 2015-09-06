############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from PyHtmlGUI.widgets.hgTextEdit           import hgTextEdit

from zopra.core                             import ZM_CTM
from zopra.core.CorePart                    import MASK_SHOW,   \
                                                   MASK_ADD,    \
                                                   MASK_EDIT

from zopra.core.tools.GenericManager        import GenericManager, GEN_LABEL
from zopra.core.tools.managers              import TN_CONTENT,             \
                                                   TCN_AUTOID,             \
                                                   TCN_CONTENT,            \
                                                   TCN_TOPIC,              \
                                                   TCN_CREATOR,            \
                                                   TCN_DATE,          \
                                                   TCN_FILE,               \
                                                   TCN_HEADING,            \
                                                   TCN_SORTING
from zopra.core.widgets                     import dlgLabel


class ContentManager(GenericManager):
    """\brief Content Manager for any content (heading, topic, content)
        to be used for news, proposals, or any other categorizable text entries."""
    _className = ZM_CTM
    _classType = GenericManager._classType + [_className]
    meta_type  = _className

    suggest_id   = 'ctm'
    suggest_name = 'Content Manager'

    """ usage:  _generic_config = {table: {key:value}}
        keys:   basket_to     (True / False) - for showForm/showList-BasketButton
                basket_from   (True / False) - for newForm-BasketButton
                basket_active (True / False) - show basket at all
                show_fields   ([attrs])      - attributes for showList
                required      ([attrs])      - required attributes for new/edit
    """
    _generic_config = {TN_CONTENT: { 'basket_active': False,
                                     'show_fields': [ TCN_HEADING,
                                                      TCN_TOPIC,
                                                      TCN_CREATOR,
                                                      TCN_DATE],
                                     'required': [TCN_HEADING, TCN_CONTENT]}
                      }

#
# Own functions
#

    def enterNewTopic(self, REQUEST):
        """\brief enter 'new'+TCN_TOPIC from REQUEST into TOPIC-List"""
        if REQUEST:
            topic = REQUEST.get('new' + TCN_TOPIC)
            if topic:
                return self.listHandler.getList(TN_CONTENT, TCN_TOPIC).addValue(topic)
        return None

#
# Overwrite standard functions
#
    def prepareDict(self, table, descr_dict, REQUEST = None):
        """\brief Overwritten to add new topic if given"""
        if table == TN_CONTENT:
            newtop = self.enterNewTopic(REQUEST)
            if newtop:
                descr_dict[TCN_TOPIC] = newtop


    def getLabelString(self, table, autoid = None, descr_dict = None):
        """\brief Return label for entry, overwritten to return heading"""
        # parent is a widget for display
        # get autoid / descr_dict
        if not descr_dict:
            descr_dict = self.getEntry( table, autoid )
        if table == TN_CONTENT:
            return descr_dict.get(TCN_HEADING)


    def getSingleMask(self, table = None, flag = MASK_SHOW, descr_dict = None, prefix = None):
        """ flags {MASK_SHOW, MASK_EDIT , MASK_ADD, MASK_SEARCH} """
        if not prefix:
            prefix = ''

        if not descr_dict:
            descr_dict = {}
        
        G = GEN_LABEL
        tmp = [[G + TCN_AUTOID, TCN_AUTOID],
               [G + TCN_TOPIC,  TCN_TOPIC],
               [G + TCN_HEADING, TCN_HEADING, None, G + TCN_SORTING, TCN_SORTING],
               [G + TCN_DATE, None, None, G + TCN_CREATOR, None],
               [G + TCN_FILE, TCN_FILE],
               [G + TCN_CONTENT, [TCN_CONTENT, 0, 3]]]

        mask = self.buildSemiGenericMask(table, tmp, flag, descr_dict, None, prefix)
        layout = mask.layout()
        
        # edit -> show creator / date
        # add -> show nothing
        # search / show: standard
        if flag & MASK_EDIT:
            tflag = MASK_SHOW
            
        elif flag & MASK_ADD:
            tflag = None
        
        else:
            tflag = flag
        
        if tflag:
            dwidg = self.getFunctionWidget(table, TCN_DATE, mask, tflag, descr_dict, prefix)
            layout.addWidget(dwidg, 3, 1)
            
            cwidg = self.getFunctionWidget(table, TCN_CREATOR, mask, tflag, descr_dict, prefix)
            layout.addWidget(cwidg, 3, 4)
            
        # edit / add -> resize text field
        if flag & (MASK_ADD | MASK_EDIT):
            mask.child(TCN_CONTENT).setSize(100, 20)
        
        # edit -> new topic widget
        if flag & (MASK_ADD | MASK_EDIT):

            widg = dlgLabel('New Topic', parent = mask)
            layout.addWidget(widg, 1, 3)
            widg = hgTextEdit('', name = 'new' + TCN_TOPIC, parent = mask)
            layout.addWidget(widg, 1, 4)

        return mask
