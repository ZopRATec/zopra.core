# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest

from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from Products.CMFPlone.utils import get_installer

from zopra.core.testing import INTEGRATION_TESTING


class TestSetup(unittest.TestCase):
    """Test that tud.profiles.webcms is properly installed."""

    layer = INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if tud.profiles.webcms is installed."""
        self.assertTrue(self.installer.is_product_installed("zopra.core"))

    def test_browserlayer(self):
        """Test that IAddonInstalled is registered."""
        from zopra.core.interfaces import IAddonInstalled
        from plone.browserlayer import utils

        self.assertIn(IAddonInstalled, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstall_product("zopra.core")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if tud.boxes.webcms is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("zopra.core"))

    def test_browserlayer_removed(self):
        """Test that IAddonInstalled is removed."""
        from zopra.core.interfaces import IAddonInstalled
        from plone.browserlayer import utils

        self.assertNotIn(IAddonInstalled, utils.registered_layers())
