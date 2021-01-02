############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from OFS.Folder import Folder

from zopra.core import ZM_PM
from zopra.core.interfaces import ISecurityManager
from zopra.core.interfaces import IZopRAProduct
from zopra.core.interfaces import IZopRATable
from zopra.core.tables.Table import Table
from zopra.core.utils import getASTFromXML


E_TABLE_EXPECTED = "A table object was expected but got %s."


class TableHandler(Folder):
    """The TableHandler class provides a specialized folder which contains
        Table objects.

    The Table Handler contains functions that are related to table management
    in the database. The class objects are meant to be placed inside a
    corresponding manager.
    """

    _className = "TableHandler"
    _classType = [_className]

    #
    # Instance Methods
    #

    def __init__(self):
        """ This method constructs a TableHandler object."""
        Folder.__init__(self, "tableHandler")
        self.tableCounter = 0

    def xmlInit(self, xml, nocreate=False):
        """This method initializes all tables specified in the XML-string.

        @param xml - string containing the XML table model.
        @param nocreate - boolean flag if set to True the table information will
               be read but no table will be created
        """

        tmp_obj = getASTFromXML(xml)

        # iterate over tables
        for table_idx in tmp_obj.table:
            table = tmp_obj.table[table_idx]
            table_name = table.getName().encode("utf-8")
            ebase = False

            if table.getEbase():
                ebase = True

            label = ""

            # TODO: take out old ebase handling, then reactivate this switch
            # if table.getEbase():
            #     ebase = True

            if table.getLabel():
                label = table.getLabel()

            uniqueid = table.getUid().encode("utf-8")
            new_dict = {}

            # iterate over columns
            for column_idx in table.column:

                column = table.column[column_idx]
                column_name = column.getName().encode("utf-8")
                new_type = column.getType()
                invisible = False

                if column.getInvisible():
                    invisible = True

                if not new_type == "multilist" and not new_type == "hierarchylist":
                    new_dict[column_name] = {}
                    new_dict[column_name][ZC.COL_TYPE] = column.getType().encode(
                        "utf-8"
                    )
                    new_dict[column_name][ZC.COL_LABEL] = column.getLabel()
                    new_dict[column_name][ZC.COL_INVIS] = invisible

            self.addTable(
                table_name, new_dict, nocreate, True, ebase, label, long(uniqueid)
            )

    def __getitem__(self, key):
        """ This method handles the collection getter operator."""
        try:
            return getattr(self, key)
        except:
            raise TypeError('Table "%s" does not exist' % key)

    def __setitem__(self, key, value):
        """ This method handles the collection assignment operator."""

        if not IZopRATable.providedBy(value):
            raise ValueError(E_TABLE_EXPECTED % type(value))

        setattr(self, key, value)

    def __contains__(self, key):
        """ This method handles the collection in-operator."""
        return self.hasObject(key)

    def get(self, key, default=None):
        """This method retrieves the table given by key, otherwise returns the
            value given by default

        @returns Table
        """
        if key not in self:
            return default

        return self[key]

    def getTableIDs(self):
        """This method returns all the IDs for the handled table.

        @return List - list of Zope IDs
        """
        return self.objectIds(Table.meta_type)

    def getTables(self):
        """This method returns all the Table objects which are contained in
            this TableHandler object.

        @return List - list of Table objects.
        """
        return self.objectItems(Table.meta_type)

    def addTable(
        self,
        tablename,
        tabledict,
        nocreate,
        log=True,
        ebase=False,
        label=None,
        uniqueid=None,
    ):
        """\brief create table, add it to handler,
        eventually create it in the database as well
        """
        mgr = self.getParentNode()
        m_product = mgr.getManager(ZM_PM)

        # SCM-logging causes loop, turn log off for SCM
        if ISecurityManager.providedBy(mgr):
            log = False

        if ebase:
            # add ACL column to tabledict
            tabledict["acl"] = {
                ZC.COL_TYPE: "int",
                ZC.COL_LABEL: "EBaSe acl",
                ZC.COL_INVIS: True,
            }

        if not nocreate and m_product:
            m_product.addTable(mgr.id + tablename, tabledict, log=log)

        tab = Table(tablename, tabledict, ebase, label, uniqueid)

        # put table as zope-object in folder
        self._setObject(tablename, tab)
        return tab

    def delTable(self, name, log=True):
        """This method deletes the table given by name and logs the event
            in the ProductManager if log is set to true (default).

        @param tablename
        """
        if name in self:
            mgr = self.getParentNode()

            # do not log it its the security manager
            # TODO: check if this is necessary and why
            if ISecurityManager:
                log = False

            # do not log if its the product manager itself
            if IZopRAProduct.providedBy(mgr):
                log = False

            m_product = mgr.getManager(ZM_PM)
            m_product.delTable(mgr.id + name, log)
