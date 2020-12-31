\page getting_started Getting Started

\tableofcontents

\section package The Package

TODO: Workover zopra packaging and basic configuration

This section covers the creation of a new ZopRA package.
First you need to create an empty Subfolder in the ZMOM Package on your hard disk. The example package is called "Examples". To make this folder a module, you need to create an empty __init__.py file in the subfolder.
The next step is to create a managers.py file in that folder looking like this, for the beginning:

\code{.py}
manager_dict = {
    'mgrGeometry' : '',
}
\endcode

In order to make your new package known to ZopRA, you need to edit the packages.py file in the ZMOM main folder.  This part is not automated in order to be able to specifically not load some of the packages that exist.

The minimal version containing the Examples package looks like that:

\code{.py}
package_list = ['AuditAndSecurity',
                'Examples',
                'Tools']
\endcode

All packages in the packages.py file will be loaded, when your Zope instance starts. The Tools package needs to be loaded as it contains the generic base class for your manager and the product manager, that will be explained later on. The AutidAndSecurity package contains managers for persons, users and security settings. They are not necessary in a template based environment, but are still intertwined with the core components which makes them mandatory for ZMOM to load.

To make it work, you finally have to create the manager, that is referenced in the managers.py file. The manager is the central concept of ZMOM, collecting tables and lists and giving you access to them. The convention is that the manager class name needs to start with "mgr" (or end on "Manager", which is the old style). In our example, we create a file called mgrGeometry.py containing the mgrGeometry class.

To allow this manager class to be found and installed by ZopRA, you need the class itself with some basic attributes. To ease programming a new Manager, we provide a ZMOMGenericManager baseclass which has a lot of generic functions that will be helpful to set up your own manager. Your class needs to extend it.

\code{.py}
from Products.ZMOM.Tools.ZMOMGenericManager import ZMOMGenericManager

class mgrGeometry(ZMOMGenericManager):
    """ ZMOM Geometry Manager """
    _className    = 'mgrGeometry'
    _classType    = ZMOMGenericManager._classType + [_className]
    meta_type     = _className

    # generic addForm hints
    suggest_id = 'geometry'
    suggest_name = 'Geometry Application'
\endcode

The form which will be used to add a manager instance into your zope folder structure is generated automatically. You need to provide the attributes suggest_id and suggest_name as default values for the form.
Now you can restart your zope instance to load your new package. Congratulations, you programmed your first own ZopRA package.

\section manager The Manager
Before you continue to install and test your manager  you need to configure the database model. This will help us to show you how easy and fast you can set up a specific scenario.

TODO: WORKOVER model and list types
\subsection database_model The Database Model
Edit the managers.py file again. In order to have tables with attributes, you need to add those to the xml configuration string.

\code{.xml}
table_dict = {
'mgrGeometry' : """<?xml version="1.0"?>
  <Tabledefinition>
    <Table name="point" label="Point"
           uid="116497999940">
      <Column name="x" label="X-Value" type="int" />
      <Column name="y" label="Y-Value" type="int" />
      <Column name="label" label="Label" type="string" />
      <Column name="quadrant" label="Quadrant" type="singlelist" />
    </Table>
    <List name="quadrant" label="Quadrants" />
  </Tabledefinition>""",
}
\endcode

Each manager has one configuration string containing the xml definition for its tables and lists. Each table has a set of columns. Using your manager later on, each entry in a table will be represented by a dictionary, whereas each column's name is a key in that dictionary (we call it attribute of the entry) with the column content as value. Each attribute has a datatype.

The basic datatypes are:

| Type  | Description                    |
| ----- | ------------------------------ |
| String | One line of text with up to 255 characters |
| Memo   | Multiline text |
| Int    | Integer value |
| Float  | Floating point value |
| Bool   | Truth value |

Additionally, ZopRA can deal with two complex extension types, singlelist and multilist. These reference a value table, the difference is that singlelists reference one value, multilists can reference many. The original idea of these lists is to make value selection available for attributes. In order to match an attribute to a list, the attribute name needs to match the name of the list defined with the "List"-Tag. The ZMOM List classes have been extended to also reference other tables, thereby enabling complex table relations. The keyword "function" is used to configure a singlelist or multilist pointing to another table.
\code{.xml}
<Table name="rectangle" label="Rectangle"
           uid="116497999950">
  <Column name="point1" label="Point 1" type="singlelist"
          function="point(x, y, label)" />
  <Column name="point2" label="Point 2" type="singlelist"
          function="point()" />
  <Column name="point3" label="Point 3" type="singlelist"
          function="point()" />
  <Column name="point4" label="Point 4" type="singlelist"
          function="point()" />
  <Column name="label" label="Label" type="string" />
</Table>
\endcode

You can specify columns in the brackets behind the table name separated  by comma. Those will be used for the selection labels (also separated by comma). If you need to create special labels for display, use empty brackets indicating the usage of a standard function for creating the labels (getLabelString), which you can overwrite. The details will be explained later on. After specifying all Table and List Entities for your scenario, you can restart your Zope Instance to enable your Manager.

\subsection install Installation
In the ZMI (Zope Management Interface), your new Manager will be available in the Add-Dropdown inside a Folder. Before you can install it, you need to supply an environment in which your manager can work.
Creating the environment

First you should create a folder inside your zope instance via the ZMI, which will contain your manager. Use the Add-Dropdown in the ZMI for example on root level to create a Folder. Inside your folder, you now need to install a dabase connection, the ZMOMProductManager handling the connection and then your own manager, which will use the ProductManager for database access.

ZMOM works with MySQL and PostgreSQL. You need to install the Driver and Adapter Packages, if your zope installation does not contain them. After that, you can add a database adapter via the ZMI to a folder ("Z MySQL Database Connection" for example). Provide it with the necessary connection parameters to get connected to your database.

When a connection exists inside your folder and is able to connect to the database, you can take the next step and install a ZMOMProduct. Add it via the ZMI and give it a name (as a convention, the product managers are called "pm" or alike). After pushing the "Add"-button, you can see the product manager in your folder along with some other new objects. The product manager installed the basic dtml snippets that are needed if you operate inside a zope instance and do not want to use templates. As we are using templates, we do not need those, but they don't disturb us either. Just let them laying around.

Now you can add your own manager to the folder. Select it in the Add-Dropdown of the ZMI. You will see the Add-Form for the managers containing the default values for id and name, that you supplied earlier. The other options don't interest us for now. Push the "Add"-button to install your manager.  In order to access the editorial views of your manager, you will have to create an entry point (or retype the complete url of the template everytime you want to use it)

As the template views were added to ZMOM at a later stage, the manager does not install anything that will lead you to the right entry point to the editorial system (called "zopra_main_form"). The provided index_html is the entry point to the old editorial system. You can delete it. Now create a script with the id "index_html" containing just one line:

\code{.py}
context.REQUEST.RESPONSE.redirect('./zopra_main_form')
\endcode

If you view your folder now (using the view tab or by using its url directly), you will be redirected to the main form on your folder, which just displays links to all managers. As you installed only your manager, you will see one link pointing to it.

We will follow that link later on to examine the editorial views of your tables.

But before, you can now inspect your new manager. Inside the ZMI, click the installed manager (in the ZMI-listing of your folder). Inside, you will find subfolders called tableHandler and listHandler (and some others which are not of interest right now).

\subsection tablehandler TableHandler
The tableHandler of class TableHandler is a container for all tables, that you specified before. Each table is an item inside the handler and can be viewed by clicking on it. Inspect the management tabs for a table to get some info about it. The TableHandler is responsible for parsing the xml and creating the table objects. The SQL-handling (also for table creation) is done by the table objects themselves.

\subsection listhandler ListHandler
The listHandler of class ListHandler is a container for all Lists and List References. Lists are the basic objects that handle the value creation, caching and delivery for selection boxes. Such a list can be referenced by a table-bound list reference (usually of the same name).  The references use the same api as basic lists except for the management tabs. If you need to refer to one basic list several times from one table (meaning that the attribute name can not be the same as the list name), you can use the "function" attribute in the xml with brackets to indicate which list to use. While basic lists are bound to the namespace of the manager (meaning each name has to be unique for a manager), the references are bound to a table (meaning each name has to be unique for that one table). The ListHandler is responsible for the XML Handling and the creation of the list objects. The necessary SQL-handling is done by the list objects themselves.

To get an idea of how tables and lists interact and can be used, we will have a look on the generic editorial views.

\section editorial_views Using the standard editorial views
Go to the index_html for your editorial area to get access to the manager listing. When you click on your manager, you will get the manager�s main form display.

\image html manager_overview.png

Each table is listed here with the generic functionality for creating new entries, searching entries or listing all entries. Below the table listing, you will find a link-list for all of the manager�s lists.

First we need to add some values to the lists in order to be able to select them on entry creation. Click on one of the lists to get to the list management screen. Add some values using the form and submit it each time. You can also delete and update the existing values later on.

\image html new_list_entry.png

Now we will have a look on the create form, as we need some example entries for this tutorial. On the manager�s main form, click the "create"-Image for one table to get there (the example uses the "point" table). The interface is generated automatically and since we did not specify anything yet, all columns will be rendered automatically.

\image html new_entry.png

Fill in some values and save the entry. You will see the new entry and get a message that it was saved. The workflow does stay on the create form to enable users to add several entries one after the other.

\image html new_entry_created.png

Next, we will have a look on the search form. Click the search image for our table on the manager main form to get there. The interface is generated automatically and since we did not specify anything yet, all columns will be rendered.

\image html search.png

Fill in a value to get exactly the entries you are looking for. Press the "Search"-Button to get to the result list. You can also use the  "list"-Button on the manager main form to get the result list for all entries (unconstrained search).

\image html search_results.png

Each entry is represented by one line. You can use the "anzeigen"-Link to get a detailed display of the entry. Since we did not configure anything, all attributes of the table are used in the listing. We will change that later on to have a more compact list view. The "bearbeiten"-Link can be used to edit the entry and the "l�schen"-Link is used to delete it. Use the "anzeigen"-link to get to the view display of an entry.

\image html show_entry.png

The heading says "Point 1". It is using the table�s label together with the entry�s label (which is the autoid as long as you didn�t overwrite the "getLabelString"-method). You can see that the different types of attributes are rendered differently. Strings will be shown on single lines while memo-attributes are displayed as blocks of text. Singlelists look like normal strings and multilists will be displayed as a list of values.  Push the edit-Button at the bottom of the page to get to the edit display.

\image html edit_entry.png

Here you can see the differences between the attribute types. Singlelists will be shown as dropdown boxes, multilists use a multilist selection view, strings are text input fields, memos are displayed as textareas and bools as checkboxes.

\section extend_views Extending the Standard Views

\subsection generic_config The _generic_config

The _generic_config is a member attribute of your manager. It is an dictionary were you define certain things like

* default fields to display for your list view and your search view
* fields that are required
* set an checker function (see \ref checker)

An example of the structure:

\code
    _generic_config = { 'tablename': { 'required':      ['field_name1','field_name2'],
                                    'show_fields':   [ 'field_name1','field_name2'],
                                    'check_fields':  {'field_name1': check_funktion2_name,'field_name2': check_funktion2_name, }
                                   } }

\endcode

\subsection overwriting_getlablestring Overwriting "getLabelString"

TODO

\subsection overwriting_getentry Overwriting "getEntry"

TODO

\subsection conf_listdisplay Configuration of the fields for list display

\subsection define_forms Define Forms

You can define the fields of a form for each table with the "getLayoutInfoHook". Within you set a Dictionary with all fields you want to have in your Form. The parameter "table" is a string which determines the requested table structure.
\code
    def getLayoutInfoHook(self, table, action):
        """\brief Returns grouping information for layout"""

        tmp = {'arbeit': [
                          {'label': 'Allgemeines',
                           'fields': [
                              'titel',
                              'jahr',
                              'studiengang',
                              'arbeitstyp',
                              ]
                           },

                          {'label': 'Nomenklatur',
                           'fields':[
                              'nomenklatur',
                              'archiv',
                              'ober_nomenklatur',
                              'unter_nomenklatur',
                              'alte_nomenklatur',
                              ]
                           },

                          {'label':'Standort',
                           'fields': [
                              'land',
                              'bundesland',
                              'ort',
                              ],
                           'sortables': ['land','bundesland','ort'],
                           },
                          {'label':'Beteiligte',
                           'fields':[
                              'betreuer',
                              'autoren',
                              ],
                           'sortables': ['betreuer'],
                           },
                          {'label':'Sonstige Angaben',
                           'fields':[
                              'schlagworte',
                              'anmerkung',
                              ]
                           }
                            ]
               }

        if tmp.has_key(table):
            res = tmp[table]
            return res
\endcode

\subsection helptext Add helptexts to an Field

Similar to the definition of an Form you have to add the function "getHelpTexts" which returns a dictionary. This dictionary contains the fieldnames as keys which will get an helptext as the value. The parameter "table" is a string which determines the requested table structure.

\code
    def getHelpTexts(self, table):
        """\brief helptexts"""
        tmp = {'arbeit':
            {
                'autoren':'Schreiben sie eine Zeile je Autor (Nachname, Vorname).',
                'schlagworte':'eine Zeile je Schlagwort',
                'archiv':'Wenn sie dieses Feld frei lassen, so wird eine Archivnummer automatisch generiert.'
            },
        }

        return tmp.get(table)
\endcode

\subsection checker Check fieldvalues before saving
If you want fields to be Checked before saveing you can define checker functions within the "_generic_config" of your manager. Add the Key "check_fields" and set another dictionary as value. The keys of this dictionary are the fieldnames and the vale is an function.

\code
    _generic_config = { 'tablename': {
                                    'check_fields':  {'fieldname': check_function, }
                                   } }
\endcode

Your check function will get the name of the attribute, the entry and the manager as parameter. You can return True if everything is valid or an error message if not.

\code
def check_function(attr_name, entry, mgr):
    if something is False:
        return 'You did somethin wrong.'
    return True
\endcode

\subsection sort_list Sorting lists for the edit display

You can sort a list simply by adding the "sortables" key within the dictionary that you return in the "getLayoutInfoHook". Then you have to add a list of the fields that will be sorted.

\code
    def getLayoutInfoHook(self, table, action):
        """\brief Returns grouping information for layout"""

        tmp = {'arbeit': [


                          {'label':'Standort',
                           'fields': [
                              'land',
                              'bundesland',
                              'ort',
                              ],
                           'sortables': ['land','bundesland','ort'],
                           }
                            ]
               }

        if tmp.has_key(table):
            res = tmp[table]
            return res
\endcode

\subsection overwriting_showeditview Configuration of the fields for show/edit/search display

TODO

\subsection [Example of a field extension]

TODO

\section querys Making Querys

You can make querys from an template by using getEntryList. The parameter "constraints" is an dictionary where the keys are names of the columns on which you want to search. Additional parameters which are usefull are:

* show_number: Number of element that will be returned
* start_number: Offset for your query
* order: Name of the column you want to order your results
* direction: ascendind or descending order ('asc' or 'desv')
* const_or: you can use this parameter on lists.s

\code
    <tal:block tal:define="ilaapp  python: here.ilaapp;
                tobj               python: ilaapp.tableHandler['tablename'];
                entries            python: tobj.getEntryList(constraints = query);>
\endcode

\section manager_template Using the manager in a template
In order to use your manager in a template, you first have to locate it. The following statements are TAL defines, the surrounding statements have been omitted.

Find the Manager

\code{.py}
mgr here/geometry;

Find the table
tablename string:point;
tobj      python: mgr.tableHandler[tablename];

Get all entries and the label for the table
entries python:    tobj.getEntries();
label python:      tobj.getLabel();
attributes python: tobj.getColumnDefs(vis_only=True).keys();
one_entry python:  tobj.getEntry(1);
same_entry python: mgr.getEntry(tablename, 1);
\endcode

The first statement returns all entries in the table "rectangle". The "getLabel"-method returns the label of the table. You can also use it to get the labels of each attribute of the table by calling it with an attribute name as parameter. To get a list of all columns, use the "getColumnDefs"-method. It returns a dictionary with the column names as keys and the column definition dictionary containing more info about each column as values. Since we only need the names, we use the "keys"-method of the dictionary to get the list of keys.

There are two ways to get one exact entry of a table identified by its autoid: You can request it directly from that table (line 4) or use a function in the manager to do the same for you, by giving it the tablename and autoid as parameters (line 5). The difference is that you can�t alter the ZMOMTable "getEntry"-method, but you can overwrite the manager�s "getEntry"-method. In this way, you are for example able to load related entries and store them inside you entry. Since all operations that are using the cache actually deliver copies instead of the cached entries, you do no need to worry about accidentally cached items, but you also cannot use the cache to store anything else then the plain entry.

The return value of the entry gathering functions like "getEntries" (see chapter 9) are lists of entries. Each entry is a dictionary. To display the label and all attributes of all entries, you could use a TAL-statement as follows (in combination with the previous define statements):

\code{.html}
<h1 tal:content="label">Label</h1>
<div tal:repeat="entry entries">
  <h2 tal:content="python:
                   mgr.getLabelString(tablename, entry['autoid'])">
    Entry Label
  </h2>
  <div tal:repeat="attribute attributes">
    <span tal:replace="python: tobj.getLabel(attribute) " />:
    <span tal:replace="python: str(entry.get(attribute)) " />
  </div>
</div>
\endcode

Examining a single entry dictionary, you will find that there are some additional attributes in it. First of all, there is always an "autoid"-key that identifies the entry. It is used in the example as parameter for the "getLabelString"-method that generates a display label for each entry. The other columns are used for edit tracking and they are invisible by default. Using the "getColumnDefs"-method with the parameter "vis_only" set to True omits those columns.

- show how to use widgets in templates

\section events Handle events

You can write some default handler methods for certain events. Possible methods are:

* actionBeforeAdd
* actionBeforeEdit
* actionAfterAdd

with the parameters:

* table tablename of your entry
* descr_dict dictionary of your entry( "fieldname":value )
* REQUEST the request object

If you want to handle these events simply add the nessesary methods to your manager. You can then modify your entry by changeing the descr_dict


\section startup_configuration Startup Configuration
Some managers may need default entries or special settings that need to be set. There are to mechanisms to achieve this. For changes that need to be done on manager creation, like for example changing the cache sizes of a table object, you can overwrite the classes manage_afterAdd method.

\code{.py}
def manage_afterAdd(self, item, container):
    """\brief Correct cache sizes."""
    ZMOMGenericManager.manage_afterAdd(self, item, container)
    # adjust caches
    self.tableHandler['point'].cache.item_count    = 1000
    self.tableHandler['point'].cache.idlist_count  = 30
    self.tableHandler['point'].cache.alllist_count = 30
\endcode

As the method is called every time a manager object is created, those changes will only be done once for as long as the manager exists. It is important to call the base classes method before doing anything, as it sets up the handlers and creates the table and list objects.  The rest of the shown function sets cache sizes for the point table. It allows the entry cache for all single entries to keep up to 1000 entries. The idlist and alllist caches contain the results for entry searches to speed up lookup for common search patterns.

Sometimes it is necessary to re-install the manager, for example when you add a new table. You can delete the manager via the ZMI and then add it again. Per default, the tables in the database will not be deleted. Adding the manager again, you have to choose the "do not create tables" option on the install form. In that case, the manage_afterAdd-method will be called, but tables will not be created. If you want to enter default entries into a table or list, you need to do this not every time the manager is created, but instead only when the tables are recreated. In order to also delete the tables on manager deletion, you have to set the "delete tables" property of your manager (via the properties tab) to 1. After that, deletion will also erase the database tables. Installing the manager again without checking the "do not create tables" option will then recreate your tables and after that call the startupConfig-method of your manager. You can overwrite it to put default entries into lists and tables.

\code{.py}
def startupConfig(self, REQUEST):
    """\brief Function called after creation by manageAddZMOMGeneric"""
    # add quadrants
    lobj = self.listHandler.get('quadrant')
    lobj.addValue('Quadrant 0')
    lobj.addValue('Quadrant 1')
    lobj.addValue('Quadrant 2')
    lobj.addValue('Quadrant 3')
\endcode

\section permissons Permissions
You will have sufficient privileges to install a manager or to view it, as Zope�s "Manager" role is automatically given those permissions when ZMOM is installed. ZMOM comes with 4 permissions that can be directly imported into your manager from the ZMOM main package:

\code{.py}
modifyPermission = 'Modify ZopRA Content'
addPermission    = 'Add ZopRA Managers'
viewPermission   = 'View'
managePermission = 'Manage ZopRA'
\endcode

How to use these permissions in your manager is explained in the next chapter. The "View"-permission is the basic permission for all content that someone is allowed to see. Normally, all visitors to your website automatically get the "View" permission via the "Anonymous" role. In order for a normal user to be able to add or edit entries in ZMOM, you need to give the "Modify ZopRA Content" permissions to the user. You could create a role, give the permissions to that role and give the role to all users, who need to use the manager. This is not good if you have thousands of users. The second way is to give the permissions to a role that already exists and all users have (for example, the "Member" role). To create a role, go to the security tab on your folder in the ZMI.  Scroll down to the "User defined roles" section at the bottom and create a role.
- Give permission to role
- give the role to the user

Then scroll up again. The first text includes a link to the "local roles" definition section. Enter the user name and choose the newly created role. Press "Save" to add this role to the user account on your folder.  The user then only has that role inside your folder, not outside of its scope.
