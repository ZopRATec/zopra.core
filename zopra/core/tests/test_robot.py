import os
import unittest

import robotsuite
from plone.testing import layered

from zopra.core.testing import ROBOT_TESTING


def test_suite():
    """Provides a test suite of robot tests for zopra.core.

    Loads all files starting with `test_` and ending on `.robot` from the 
    `robot` subdirectory as tests in the suite.

    :return: test suite
    :rtype: unittest.suite.TestSuite
    """

    suite = unittest.TestSuite()
    current_dir = os.path.abspath(os.path.dirname(__file__))

    robot_dir = os.path.join(current_dir, 'robot')
    robot_tests = [
        os.path.join('robot', doc) for doc in os.listdir(robot_dir)
        if doc.endswith('.robot') and doc.startswith('test_')
    ]

    for test in robot_tests:
        suite.addTests([
            layered(robotsuite.RobotTestSuite(test),
                    layer=ROBOT_TESTING),
        ])
    return suite
