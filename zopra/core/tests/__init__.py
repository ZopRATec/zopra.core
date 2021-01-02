import unittest

# import from Testing here to work around the testing/Testing problem
# used by zopra.core.testing
from Testing.ZopeTestCase.utils import setupCoreSessions

from zopra.core.tests.mgrTest import mgrTest


# stub method for faking getManager
def getManager(self, name, obj_id=None):
    """returning None leads to fallback behaviour. So the tests that do not need database access can work with None"""
    return None


def fix_getManager(manager_class):
    """put fake getManager in place"""
    if not hasattr(mgrTest, "old_getManager"):
        manager_class.old_getManager = manager_class.getManager
        manager_class.getManager = getManager


def unfix_getManager(manager_class):
    """put original getManager back in place"""
    if hasattr(mgrTest, "old_getManager"):
        manager_class.getManager = manager_class.old_getManager
        del manager_class.old_getManager


# TODO: move the getManager override into a layer setUp (instead Testcase setUp)


class StandaloneTestCase(unittest.TestCase):
    """Test Case for Standalone manager testing, overrides getManager to not lookup anything"""

    def setUp(self):
        """This method is called before each single test."""
        fix_getManager(mgrTest)

    def tearDown(self):
        """This method is called after each single test. It can be used for
        cleanup, if you need it. Note that the test framework will roll back
        the Zope transaction at the end of each test, so tests are generally
        independent of one another. However, if you are modifying external
        resources (say a database) or globals (such as registering a new
        adapter in the Component Architecture during a test), you may want to
        tear things down here.
        """
        unfix_getManager(mgrTest)
