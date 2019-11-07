# -*- coding: utf-8 -*-
'''
Created on 7 Nov 2019

@author: peterseifert
'''

import unittest

class TemplateBaseManagerTest(unittest.TestCase):
    """Unittest Testcases for the tools.TemplateBaseManager class"""
    def test_TemplateBaseManager(self):
        from zopra.core.tools.TemplateBaseManager import TemplateBaseManager
        t = TemplateBaseManager('Testtitle', 'testid', nocreate=1, zopratype='')
        self.assertEqual(t.meta_type, 'TemplateBaseManager')
        self.assertEqual(t.title, 'Testtitle')
    
    # what can we test on the TemplateBaseManager object?
    # - getListOwnUsers
    # - getPermissionInfo
    # - doesWorkflows
    # - getStateTransferInfo
    # - doesWorkingCopies
    # - doesTranslations
    # - deepcopy
    # - selectAdditionalLanguage
    # - checkDefaultWildcardSearch
    # - calculatePaginationPages
    # - isHierarchyList
    # - prepareValuesForEdit
    # - prepareConstraintsForOutput
    # - generateMailLink
    # - encrypt_ordtype
    # - emailProtect
    # - getDiff
    # - dictIntersect
    # - alphabeticalSort
    # - reorderColsAccordingly
    # - prepareLinks
    # - removeLinks
    # - py2json
    # - json2py
    # - filterRealSearchConstraints

    # what TemplateBase methods can we test on the mgrTest without db
    # - getPermissionEntryInfo
    # - getFilteredColumnDefs
    # - generateTableSearchTreeTemplate (could be checked by test_unit_tablenode
    # - getLayoutInfo
    # - getHelpTexts
    # - getTableEntryFromRequest
    #the following 3 could be moved to list unit test
    # handleHierarchyListOnSearch
    # prepareHierarchylistDisplayEntries
    # sortListEntriesForDisplay

    # what can we test with mgrTest and db
    # getWorkingCopy
    # getWorkingCopies
    # createWorkingCopy
    # updateWorkingCopy
    # updateTranslation
    # getTranslation
    # removeTranslationInfo
    # - getEntryListCountProxy
    # - getEntryListProxy
    # - getChangeDate
    # - getCopyDiff
    # - getDiffLabels
    # - getRelatedEntries
    # - val_translate

