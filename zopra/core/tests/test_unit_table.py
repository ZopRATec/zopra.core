# -*- coding: utf-8 -*-

from zopra.core.tests import StandaloneTestCase
from zopra.core.tools.mgrTest import mgrTest


class TableTest(StandaloneTestCase):
    """Unittest Testcases for the tables.Table and tables.TableHandler classes (standalone, no db)"""

    def test_Table(self):
        mgr = mgrTest("Testtitle", "testid", 1, "")
        mgr.manage_afterAdd(None, None)
        table = mgr.tableHandler["test"]
        self.assertEqual(table.tablename, "test")

    def test_TableHandler(self):
        mgr = mgrTest("Testtitle", "testid", 1, "")
        mgr.manage_afterAdd(None, None)
        handler = mgr.tableHandler
        self.assertTrue("test" in handler)
        self.assertEqual(handler["test"], handler.get("test"))

    # what can we test on the Table object?
    # - isOwner
    # - buildGetEntriesFilter

    # what can we test on the Table object when having a mgrTest container
    # - getUId
    # - getEntry with cache
    # - getField
    # - getLabel
    # - getColumnTypes
    # - getColumnDefs
    # - getMainColumnNames
    # - getSearchTreeTemplate
    # - resetSearchTreeTemplate

    # what can we test on the Table object when having a mgrTest container and database
    # - getEntry
    # - getEntryBy
    # - getEntryAutoid
    # - addEntry
    # - deleteEntry
    # - updateEntry
    # - validateEntry
    # - exportXML
    # - exportCSV
    # - deleteEntries
    # - filterEntries
    # - requestEntries
    # - requestEntryCount
    # - getEntries
    # - getEntryCount
    # - getEntryList
    # - getEntryDict
    # - getEntryListCount
    # - getEntryAutoidList
    # - getLastId
    # - getRowCount
    # - getEntryValue
    # - getEntrySelect

    # what can we test on the TableHandler object?
    # - addTable, delTable
    # - getTableIds
    # - getTables
