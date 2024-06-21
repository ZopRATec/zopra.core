# Robot Tests

In order to run the tests, you need to install the "tests" extra, e.g. via buildout: eggs = zopra.core [tests]

Resources:
* zopra/core/tools/model/mgrTest.xml: the data model for the test manager
* zopra/core/tools/mgrTest: test manager class, plain, based on TemplateBaseManager
* zopra/core/testing.zcml: register test profile, add import step that uses the setuphandlers.py
* zopra/core/setuphandlers.py: build test szenario data structures (with datbase adapter, ZopRAProduct and mgrTest) in the portal (that might be a WebCMS or Plone portal)
* zopra/core/testing.py: suite setup, potentially with WebCMS installation. Plone Teardown does cleanup by dropping all the database tables.
* zopra/core/profiles/test: the test profile
* zopra/core/profiles/test/metadata.xml: profile dependencies (on default)
* zopra/core/profiles/test/portal_languages.xml: activate default language en
* zopra/core/tests: test module declaring the test-suite
* zopra/core/tests/__init__.py: defines a Standalone Manager Test Case that allows tests without database involvement
- zopra/core/tests/test_robot.py: test suite definition
- zopra/core/tests/robot: robot test folder
- zopra/core/tests/robot/keywords.robot: basic zopra keywords and variables
- zopra/core/tests/robot/keywords_webcms.robot: webcms specific keywords for extended testing for the zopra subpackages (not needed for the basic zopra.core tests)
- zopra/core/tests/robot/test-zopra_core.robot: zopra.core basic tests using mgrTest

The subpackages use the modules zopra.core.testing and zopra.core.setuphandlers as base.
The test suite relies on a switch between WebCMS and Plone (HAVE_PLONE / HAVE_WEBCMS constants in zopra.core) that was necessary to allow the core tests to run in plain plone.
The core is still working without Plone, but the tests are not (because they use plone.app.robotframework).
The test suite also depends on Products.ZMySQLDA, while the core can be used with different database adapters.

The setuphandlers module defines a class ZopRATestEnvironmentMaker, that is used by the test setup to build the test environment.
Its methods can also be used to create a showcase environment in the project packages (see tud.zopra.studieninfo.showcase).