from setuptools import find_packages
from setuptools import setup


version = 2.0

setup(
    name="zopra.core",
    version=version,
    description="ZopRATec's ZopRA middleware",
    long_description=open("README.md").read(),
    # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="",
    author="Ingo Keller & Peter Seifert",
    author_email="Ingo.Keller@zopratec.de",
    url="",
    license="GPL version 2",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["zopra"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "importlib",  # for the generic manager autoloader (because managers are no ContentTypes yet)
        "PyHtmlGUI",  # ZopRA default display generation
        "PyICU",  # for linguistically better alphabetical sorting
    ],
    extras_require={
        "test": ["plone.app.robotframework", "Products.ZMySQLDA", "plone.api", "MySQLdb"]
    },  # Robot Tests with MySQL Adapter
    entry_points="""
       # -*- Entry points: -*-

       [z3c.autoinclude.plugin]
       target = plone
       """,
)
