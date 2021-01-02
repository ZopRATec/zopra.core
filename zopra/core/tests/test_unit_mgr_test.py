# -*- coding: utf-8 -*-

from zopra.core.tests import StandaloneTestCase
from zopra.core.tests.mgrTest import mgrTest


class TestManagerTest(StandaloneTestCase):
    """Unittest Testcases for the mgrTest Testing class (standalone, no db)"""

    def test_mgrTest(self):
        mgr = mgrTest("Testtitle", "testid", nocreate=1, zopratype="")
        mgr.manage_afterAdd(None, None)
        self.assertEqual(mgr.id, "testid")
        self.assertEqual(mgr.title, "Testtitle")
        self.assertEqual(mgr.meta_type, "mgrTest")

    # what can we test on the mgrTest object?
    # generic config (?)
    # table layout like defined in model

    # a lot of stuff listed in comments in test_unit_mgr_templatebase and test_unit_mgr_generic
