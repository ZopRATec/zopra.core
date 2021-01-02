# -*- coding: utf-8 -*-

import unittest

from zopra.core.Manager import Manager


class ManagerTest(unittest.TestCase):
    """Unittest Testcases for the Manager class"""

    def test_Manager(self):

        t = Manager("Testtitle", "testid", nocreate=1, zopratype="")
        self.assertEqual(t.meta_type, "")
        self.assertEqual(t.title, "Testtitle")

    # TODO: before any more tests can be implemented, there needs to be a serious clenaup moving all old-style (non-tmeplate) - methods to a separate manager class, cleaning up .tables, .lists and all remaining stuff under zopra.core.*
    # TODO: everything that stays should then be unit-tested

    # TODO: generate TestCase modules for
    # - lists
    # - dbconnector
    # - Classes
    # - constants
    # - Manager

    # what TemplateBase methods can we test on the mgrTest without db
    # getGenericConfig
    # getConfigShowFields

    # what can we test with mgrTest and db
    # - startupConfig and installConfig get called
    # - _addTable and _delTable get called
    # - deleteEntries
    # - getEntry
