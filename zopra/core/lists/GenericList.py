from types import ListType

from zopra.core import ZC
from zopra.core import SimpleItem
from zopra.core.utils import getParentManager


_list_definition = {  # value of the list entry
    ZC.VALUE: {ZC.COL_TYPE: "string"},
    # used for sorting the shown list
    ZC.RANK: {ZC.COL_TYPE: "string"},
    # if false the entry will only be used for lookup
    ZC.SHOW: {ZC.COL_TYPE: "string"},
    # comments to these entries
    ZC.NOTES: {ZC.COL_TYPE: "string"},
}


class GenericList(SimpleItem):
    """The class GenericList is the super class for all lists"""

    _className = "GenericList"
    _classType = [_className]

    # for compatibility
    listtype = "singlelist"

    def __init__(self, listname, label=None):
        """Constructs a GenericList."""
        self.listname = listname
        self.label = label if label else u""

    def getClassName(self):
        """This method returns the class name.

        :result: string of classes name
        """
        return self.__class__.__name__

    def getClassType(self):
        """This method returns a list of the class names of all ancestors and the current class"""
        return [onetype.__name__ for onetype in self.__class__.__bases__] + [
            self.getClassName()
        ]

    def createTable(self):
        """Create the database table."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def deleteTable(self, omit_log=None):
        """Create the database table."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def getManager(self):
        """Returns the owning manager."""
        message = "No Manager found for List Object via getParentNode()"
        return getParentManager(self, message)

    def getResponsibleManagerId(self):
        """Returns the foreign manager (or mgr, if no foreign list).
        mgr exists only for testing."""

        # on default local manager is assumed
        return self.getManager().id

    def getLabel(self):
        """Returns the label of the listattribute."""
        return self.label

    def addValue(self, value, notes="", rank="", show="yes"):
        """Adds a value to a list lookup table."""
        return 0

    def delValue(self, autoid):
        """Deletes a value from a list lookup table."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def getEntry(self, autoid):
        """Fetches a value from an list lookup table. Local function."""
        return {}

    def getEntries(self, value=None, with_hidden=False):
        """Returns all list entries of one list."""
        return []

    def updateEntry(self, descr_dict, entry_id):
        """changes list values in the database"""
        return 0

    def getAutoidByValue(self, value, rank=None):
        """Returns the autoid from an specified list entry."""
        raise NotImplementedError(ZC.E_CALL_ABSTRACT)

    def getAutoidsByFreeText(self, value):
        """Returns the autoid from any fitting list entry."""
        return []

    def crossValue(self, value1, value2, crossString):
        """splits the entries by crossString, combines the lists,
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
        """gets the values for the entries calls crossValue and
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
        value = self.crossValue(value1, value2, crossString)

        # the addListValueFunction only adds,
        # if not present and returns the id
        return self.addValue(value)

    def getValueCount(self):
        """Returns the number of entries in this list.

        :return: The number of entries.
        """
        return 0

    def getValueByAutoid(self, autoid):
        """Returns the value from an specified list entry/entries."""
        return ["" for aid in autoid] if isinstance(autoid, ListType) else ""
