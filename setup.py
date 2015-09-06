import os

from setuptools import setup, find_packages

version = open(os.path.join("zopra", "core", "version.txt")).read().strip()

setup( name                 = 'zopra.core',
       version              = version,
       description          = "ZopRATec's ZopRA middleware",
       long_description     = open("README.txt").read() + "\n" +
                              open(os.path.join("docs", "HISTORY.txt")).read(),
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
           'importlib',
           'PyHtmlGUI'
       ],
       entry_points         = """
       # -*- Entry points: -*-
       """,
     )
