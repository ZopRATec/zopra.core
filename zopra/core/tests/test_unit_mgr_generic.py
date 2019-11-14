# -*- coding: utf-8 -*-
'''
Created on 7 Nov 2019

@author: peterseifert
'''

import unittest
from zopra.core.tools.GenericManager import GenericManager

class GenericManagerTest(unittest.TestCase):
    """Unittest Testcases for the GenericManager class"""
    def test_GenericManager(self):

        t = GenericManager('Testtitle', 'testid', nocreate=1, zopratype='')
        self.assertEqual(t.meta_type, 'GenericManager')
        self.assertEqual(t.title, 'Testtitle')

    # TODO: before any more tests can be implemented, there needs to be a serious clenaup moving all old-style (non-tmeplate) - methods to a separate manager class, cleaning up .tables, .lists and all remaining stuff under zopra.core.*
    # TODO: everything that stays should then be unit-tested
    
    # TODO: generate TestCase modules for
    # - lists
    # - dbconnector
    # - Classes
    # - constants
    # - CorePart
    # - ManagerPart

    # what can we test on the GenericManager object?
    # getCurrentLanguage

    # what TemplateBase methods can we test on the mgrTest without db
    # getGenericConfig
    # getConfigShowFields

    # what can we test with mgrTest and db
    # - startupConfig and installConfig get called
    # - _addTable and _delTable get called 
    # - deleteEntries
    # - getEntry
