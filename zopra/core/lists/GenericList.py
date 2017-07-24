############################################################################
#    Copyright (C) 2004 by Ingo Keller                                     #
#    <webmaster@ingo-keller.de>                                            #
#                                                                          #
# Copyright: See COPYING file that comes with this distribution            #
#                                                                          #
############################################################################

from types                                      import ListType

from PyHtmlGUI.widgets.hgComboBox               import hgComboBox

from zopra.core                                 import SimpleItem, ZC
from zopra.core.elements.Buttons                import DLG_CUSTOM
from zopra.core.widgets.hgShortenedComboBox     import hgShortenedComboBox
from zopra.core.widgets.hgFilteredComboBox      import hgFilteredComboBox
from zopra.core.utils                           import getParentManager

_list_definition = {  # value of the list entry
                      ZC.VALUE: { ZC.COL_TYPE: 'string' },

                      # used for sorting the shown list
                      ZC.RANK:  { ZC.COL_TYPE: 'string' },

                      # if false the entry will only be used for lookup
                      ZC.SHOW:  { ZC.COL_TYPE: 'string' },

                      # comments to these entries
                      ZC.NOTES: { ZC.COL_TYPE: 'string' } }


class GenericList(SimpleItem):
    """\brief The class GenericList is the super class for all lists"""

    _className = 'GenericList'
    _classType = [_className]

    # for compatibility
    listtype   = 'singlelist'


    def __init__( self,
                  listname,
                  label    = None):
        """\brief Constructs a GenericList.
        """
        self.listname = listname
        self.label    = label if label else u''


    def createTable(self):
        """\brief Create the database table."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def deleteTable(self, omit_log = None):
        """\brief Create the database table."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def getManager(self):
        """\brief Returns the owning manager."""
        message = 'No Manager found for List Object via getParentNode()'
        return getParentManager(self, message)


    def getResponsibleManagerId(self):
        """\brief Returns the foreign manager (or mgr, if no foreign list).
                  mgr exists only for testing."""

        # on default local manager is assumed
        return self.getManager().id


    def getLabel(self):
        """\brief Returns the label of the listattribute."""
        return self.label


    def addValue( self, value, notes = '', rank  = '', show  = 'yes' ):
        """\brief Adds a value to a list lookup table.
        """
        return 0


    def delValue(self, autoid):
        """\brief Deletes a value from a list lookup table."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def getEntry(self, autoid):
        """\brief Fetches a value from an list lookup table. Local function."""
        return {}


    def getEntries(self, value = None, with_hidden = False):
        """\brief Returns all list entries of one list."""
        return []


    def updateEntry( self,
                     descr_dict,
                     entry_id ):
        """\brief changes list values in the database"""
        return 0


    def getAutoidByValue(self, value, rank = None):
        """\brief Returns the autoid from an specified list entry."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)


    def getAutoidsByFreeText(self, value):
        """\brief Returns the autoid from any fitting list entry."""
        return []


    def crossValue(self, value1, value2, crossString):
        """\brief splits the entries by crossString, combines the lists,
                  joins everything by crossString and returns the new value.
        """

        # empty entries
        if not value1:
            return value2

        if not value2:
            return value1

        # make a cross
        list1 = value1.split(crossString)
        list2 = value2.split(crossString)
        res = {}
        for entry in list1:
            if entry:
                res[entry] = None

        for entry in list2:
            if entry:
                res[entry] = None

        reslist = res.keys()
        reslist.sort()
        return crossString.join(reslist)


    def crossLookupList(self, entry1, entry2, crossString):
        """\brief gets the values for the entries calls crossValue and
                  inserts the result into the list.

        Returns the new or existing id.
        """

        # no entries
        if not entry1:
            return entry2

        if not entry2:
            return entry1

        value1 = self.getValueByAutoid(entry1)
        value2 = self.getValueByAutoid(entry2)
        value  = self.crossValue(value1, value2, crossString)

        # the addListValueFunction only adds,
        # if not present and returns the id
        return self.addValue(value)


    def createWidget( self,
                      name,
                      with_novalue = False,
                      with_null    = False,
                      parent       = None,
                      config       = None):
        """\brief Returns a list combobox."""
        raise ValueError('TESTING REMOVAL OF LIST.CREATEWIDGET')
        # NOTE: defaults to single list

        # load list data and build combobox
        if config and config['type'] == 'filtered':
            if config['direction'] == 'horizontal':
                vertical = False
            else:
                vertical = True
            pattern = config['pattern']
            if config['maxlen'] > 0:
                cbox = hgShortenedComboBox( name     = name,
                                            parent   = parent,
                                            pattern  = pattern,
                                            vertical = vertical )

                cbox.setListLength(config['maxlen'])

                if config['tolerance'] > 0:
                    cbox.setListTolerance(config['tolerance'])
                else:
                    cbox.setListTolerance(10)
            else:
                cbox = hgFilteredComboBox( name     = name,
                                           parent   = parent,
                                           pattern  = pattern,
                                           vertical = vertical )
        else:
            cbox = hgComboBox(name = name, parent = parent)

        # empty value
        if with_novalue:
            cbox.insertItem(' -- no search value -- ', '')

        # null value
        if with_null:
            cbox.insertItem(' -- no value -- ', 'NULL')

        return cbox


    def getWidget( self,
                   with_novalue = False,
                   selected     = None,
                   with_hidden  = False,
                   with_null    = False,
                   prefix       = '',
                   parent       = None,
                   config       = None):
        """\brief Returns a list combobox."""
        raise ValueError('TESTING REMOVAL OF LIST.GETWIDGET')
        # only used by multilist notes widgets
        # check how to remove it from here

        # prefix is only for REQUEST-handling
        pre  = DLG_CUSTOM + prefix if prefix else ''
        cbox = self.createWidget(pre + self.listname,
                                 with_novalue,
                                 with_null,
                                 parent,
                                 config)

        entry_list = self.getEntries()

        for entry in entry_list:
            # test for 'no' in case attribute is missing
            if with_hidden or entry.get(SHOW) != 'no':
                cbox.insertItem(entry[VALUE], entry['autoid'])

        # sort
        cbox.sort()

        # handles the selection of a list entry
        if selected:
            cbox.setCurrentValue(selected)
        else:
            cbox.setCurrentItem(0)

        return cbox


    def getValueCount(self):
        """\briefs Returns the length of a list.

        \param list_name  The argument \a list_name is the name of the list
        without the id prefix.

        \return The number of rows, otherwise None
        """
        return 0


    def getValueByAutoid(self, autoid):
        """\brief Returns the value from an specified list entry/entries."""
        return [ '' for aid in autoid ] if isinstance( autoid, ListType) else ''
