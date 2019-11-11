# -*- coding: utf-8 -*-
'''
Created on 7 Nov 2019

@author: peterseifert
'''

from zopra.core.tests import StandaloneTestCase

class TableNodeTest(StandaloneTestCase):
    """Unittest Testcases for the tables.TableNode.TableNode and tables.Filter.Filter classes (standalone, no db)"""

    def test_SingleTableNode(self):
        from zopra.core.tools.mgrTest import mgrTest
        mgr = mgrTest('Testtitle', 'testid', 1, '')
        mgr.manage_afterAdd(None, None)
        table = mgr.tableHandler['test']
        tableNode = table.getTableNode()
        self.assertEqual(tableNode.name, 'test')

    # what can we test on the TableNode object?
    # - setConstraints
    # - setFilter
    # - setOrder
    # - reset
    # - getSQL
