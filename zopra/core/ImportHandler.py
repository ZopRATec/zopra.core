############################################################################
#    Copyright (C) 2006 by Bernhard Voigt                                  #
#    bernhard.voigt@lmu.uni-muenchen.de                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

import string

from copy                import copy
from types               import ListType, StringType

from zopra.core.CorePart import ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST
from zopra.core.interfaces import IZopRAManager

ZCOL_LISTTYPES = [ZCOL_SLIST, ZCOL_MLIST, ZCOL_HLIST]

ZM_IMPH = 'ImportHandler'

ZM_IMPH_BAD_LINES    = 'bad lines'
ZM_IMPH_LOST_ENTRIES = 'lost entries'

# TODO: - type checking (optional? own status field?)
#       - type converting
#      (- check required fields?)


class ImportHandler:
    """ Import Handler for tab-separated Tables.

        Uses table description dict to retrieve entries from tab-separated data file.
    """

    _className   = ZM_IMPH
    _classType   = [_className]
    meta_type    = _className


    def __init__(self, mgr, tablename = None):
        """\brief Setup Handler"""

        # check mgr
        if not IZopRAManager.providedBy(mgr):
            raise ValueError( "No valid mgr provided.")

        self.mgr   = mgr
        self.table = None

        if tablename:
            self.setTable(tablename)

        self.setErrorOnBadLines(False)
        self.setKeepValuesForLists([])
        self.setAllowListModification(False)

        self.__additionalFields = []

        # reset status information
        self.reset()


    def setTable(self, tablename):
        """\brief """

        assert(isinstance(tablename, StringType))

        if tablename not in self.mgr.tableHandler:
            raise ValueError( "No table with name %s in Manager %s available" % (tablename, self.mgr.getTitle()) )

        self.table = self.mgr.tableHandler[tablename]


    def setErrorOnBadLines(self, error):
        """\brief """
        self.__errorOnBadLines = error


    def errorOnBadLines(self):
        """\brief """
        return self.__errorOnBadLines


    def setKeepValuesForLists(self, listnames = None):
        """\brief """
        assert(isinstance(listnames, ListType))
        self.__keepValuesForLists = copy(listnames)


    def setKeepValuesForList(self, listname = None):
        """\brief """
        assert(isinstance(listname, StringType))

        if listname not in self.__keepValuesForLists:
            self.__keepValuesForLists.append(listname)


    def keepValuesForList(self, listname):
        """\brief """
        return listname in self.__keepValuesForLists


    def getKeepValuesForLists(self):
        """\brief """
        return copy(self.__keepValuesForLists)


    def setAllowListModification(self, allowmod):
        """\brief """
        if not allowmod:
            self.__allowListModification = []
        elif isinstance(allowmod, ListType):
            self.__allowListModification = allowmod
        else:
            raise ValueError('Internal Error in Import Handling: allowmod has to be List or False')


    def allowListModification(self, columnName):
        """\brief """
        try:
            return columnName in self.__allowListModification
        except:
            return False


    def setAdditionalFields(self, fields):
        """\brief """
        assert(isinstance(fields, ListType))
        for field in fields:
            assert(isinstance(field, StringType))

        self.__additionalFields = copy(fields)


    def additionalFields(self):
        """\brief """
        return copy(self.__additionalFields)


    def reset(self):
        """\brief """
        self.bad_lines    = []
        self.lost_entries = []
        self.line         = 0


    def status(self):
        """\brief """

        status = {}

        if self.bad_lines:
            status[ZM_IMPH_BAD_LINES]    = copy(self.bad_lines)
        if self.lost_entries:
            status[ZM_IMPH_LOST_ENTRIES] = copy(self.lost_entries)

        return status


    def getLineNumber(self):
        """\brief """

        return self.line


    def getEntries(self, fHandle):
        """\brief Get list of valid entries"""

        assert(self.table)

        self.reset()

        header_dict = {}
        lookup_dict = {}

        # get original position in file
        self.pos = fHandle.tell()

        # get data
        # thank you m$
        data = fHandle.read()

        # ismac = data.find('\r') != -1 and data.find('\r') != data.find('\r\n')
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        # if ismac:
        #    data = data.decode('macroman').encode('utf8')

        data = string.split( data, '\n' )

        # get header info
        line_len = self.getDefinition(data[0], header_dict, lookup_dict)

        new_entries = []

        # for every single line
        for i, line in enumerate(data):

            # skip header
            if i == 0:
                continue

            entry = self.getEntry(line, i, line_len, header_dict, lookup_dict)
            if entry:
                new_entries.append( entry )

        self.line = i + 1

        fHandle.seek(self.pos)

        return new_entries


    def iterateEntries(self, fHandle):
        """\brief Get list of valid entries via yield"""
        # while 1:
        self.reset()

        header_dict = {}
        lookup_dict = {}

        # get original position in file
        self.pos = fHandle.tell()

        # get data
        # thank you m$
        data = fHandle.read()
        # ismac = data.find('\r') != -1 and data.find('\r') != data.find('\r\n')
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        # if ismac:
        #    data = data.decode('macroman').encode('utf8')

        data = string.split( data, '\n' )

        # get header info
        line_len = self.getDefinition(data[0], header_dict, lookup_dict)

        # for every single line
        for i, line in enumerate(data):

            # skip header
            if i == 0:
                continue

            self.line = i + 1

            new_entry = self.getEntry(line, i, line_len, header_dict, lookup_dict)

            if new_entry:
                # yield returns new_entry and starts at next iteration call directly here again
                yield new_entry

        fHandle.seek(self.pos)

        raise StopIteration


    def getDefinition(self,
                      header_string,
                      header_dict,
                      lookup_dict):
        """\brief Get layout of import table."""

        table_cols  = self.table.getColumnTypes().keys()

        definition = string.split(header_string, '\t')

        header_len = len(definition)
        for i, item in enumerate(definition):
            if str(item) in table_cols:
                header_dict[i] = str(item)
                if self.mgr.listHandler.hasList(self.table.tablename, str(item)):
                    lookup_dict[i] = self.mgr.listHandler.getList(self.table.tablename, str(item))
            elif str(item) in self.__additionalFields:
                header_dict[i] = str(item)

        return header_len


    def getEntry( self,
                  data_string,
                  line_number,
                  line_len,
                  header_dict,
                  lookup_dict ):
        """\brief Get layout of import table."""

        i = line_number

        # get entry components
        entry = string.split(data_string, '\t')

        if not ''.join(entry).replace(' ', ''):
            return {}

        # check line
        if len(entry) > line_len:
            if self.errorOnBadLines():
                raise ValueError("Invalid line # %s" % i + 1)
            else:
                self.bad_lines.append((i + 1, data_string))
            return {}

        new_entry = {}

        # for all columns in line
        for j, item in enumerate(entry):
            if item:
                item = string.replace(item, '\\n', '\n')
                if len(item) > 1 and item[0] == '"' and item[-1] == '"':
                    item = item[1:-1]
                    item = item.replace('""', '"')

            columnName = header_dict.get(j)
            if columnName:

                # lookup list handling
                lookup = lookup_dict.get(j)
                if lookup:
                    if lookup.listtype == ZCOL_SLIST:

                        if item and item != ' ' and item != 'None':
                            if self.keepValuesForList(columnName):
                                new_entry[columnName] = item
                            else:
                                autoid = lookup.getAutoidByValue(item)

                                if not autoid and \
                                   self.allowListModification(columnName):
                                    autoid = lookup.addValue( item, 'entered by import' )

                                if autoid:
                                    new_entry[columnName] = autoid
                                else:
                                    self.lost_entries.append( (i + 1, '%s:%s' % (columnName, item)) )
                    elif lookup.listtype == ZCOL_MLIST:

                        # replace " (used by excel to mark multiline fields)
                        item = item.replace('"', '')
                        # separate values
                        if item.find('\n') != -1:
                            splitter = '\n'
                        else:
                            splitter = ','
                        itemlist = item.split(splitter)
                        new_entry[columnName] = []

                        for oneitem in itemlist:
                            oneitem = oneitem.strip()

                            if oneitem and oneitem != ' ' and oneitem != 'None':
                                if self.keepValuesForList(columnName):
                                    new_entry[columnName].append(oneitem)
                                else:
                                    autoid = lookup.getAutoidByValue(oneitem)

                                    if not autoid and \
                                       self.allowListModification(columnName):
                                        autoid = lookup.addValue( oneitem, 'entered by import' )

                                    if autoid:
                                        new_entry[columnName].append(autoid)
                                    else:
                                        self.lost_entries.append( (i + 1, '%s:%s' % (columnName, oneitem)) )

                    else:
                        message  = 'Unable to import hierarchic lists:\n'
                        message += ' Not implemented yet.'
                        raise ValueError( message )

                # normal entry column
                else:
                    new_entry[columnName] = item
        # rof

        return new_entry
