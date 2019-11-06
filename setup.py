import os

from setuptools import setup, find_packages

version = open(os.path.join("zopra", "core", "version.txt")).read().strip()

setup( name                 = 'zopra.core',
       version              = version,
       description          = "ZopRATec's ZopRA middleware",
       long_description     = open("README.md").read(),
       # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
       classifiers          = [
         "Programming Language :: Python",
         "Topic :: Software Development :: Libraries :: Python Modules",
         ],
       keywords             = '',
       author               = 'Ingo Keller',
       author_email         = 'Ingo.Keller@zopratec.de',
       url                  = '',
       license              = 'GPL',
       packages             = find_packages(exclude=['ez_setup']),
       namespace_packages   = ['zopra'],
       include_package_data = True,
       zip_safe             = False,
       install_requires     = [
           'setuptools',
           # -*- Extra requirements: -*-
           'importlib',# for the generic manager autoloader (because managers are no ContentTypes yet)
           'PyHtmlGUI',# ZopRA default display generation
           'PyICU',# for linguistically better alphabetical sorting
       ],
       extras_require={'test': ['plone.app.robotframework', 'Products.ZMySQLDA', 'plone.api']},# Robot Tests with MySQL Adapter
       entry_points         = """
       # -*- Entry points: -*-

       [z3c.autoinclude.plugin]
       target = plone
       """,
     )
