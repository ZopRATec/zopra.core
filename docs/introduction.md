\page introduction Introduction


The Zope Research Architecture (ZopRA) is a web-based data management framework for Zope/Plone using 
relational databases for data storage. The framework consists of multiple packages. The zopra.core 
package is the heart of the framework and provides the database wrapper and data handling layer that
provide access to the database and is responsible for handling data entries. Another part of 
zopra.core deals with the Graphical User Interface (GUI), user dialogs and visualization, using the 
PyHtmlGUI framework, which is a visualization toolkit for rendering and handling dialogs. Recent 
developments have lead to a template based visualization for ZopRA as an alternative to PyHtmlGUI. 
As objects are derived from the data structures rather than the other way around, ZopRA can be seen
as an Object-Relation-Mapper (ORM). ZopRA can be used to handle any kind of data that can be 
structured in a relational way. This document will explain how to create your own ZopRA packages to
manage your data and install it in a Zope/Plone environment.
