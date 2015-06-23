############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    ingo.keller@zopratec.com                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
import imp
import sys
import os.path
from StringIO                                       import StringIO

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.tools.hgWidgetFactory                import hgWidgetFactory

from PyHtmlGUI.widgets.hgLabel                      import hgLabel
from PyHtmlGUI.widgets.hgPushButton                 import hgPushButton
from PyHtmlGUI.widgets.hgTextEdit                   import hgTextEdit


from zopra.core                                     import HTML, \
                                                           SimpleItem, \
                                                           ClassSecurityInfo, \
                                                           PropertyManager
from zopra.core.dialogs                             import getStdDialog, \
                                                           getStdZMOMDialog
from zopra.core.dialogs.Dialog                      import Dialog
from zopra.core.utils                               import getZopRAPath


class DialogContainer(PropertyManager, SimpleItem):
    """\class DialogContainer"""

    # class variables
    _className = 'DialogContainer'
    _classType = [_className]
    meta_type  = _className

    _properties = PropertyManager._properties + \
                  ( {'id': 'id',             'type': 'string',  'mode': 'r'},
                    {'id': 'defaultPy',      'type': 'boolean', 'mode': 'r'},
                    {'id': 'defaultCss',     'type': 'boolean', 'mode': 'r'},
                    {'id': 'defaultXml',     'type': 'boolean', 'mode': 'r'},
                    {'id': 'demo',           'type': 'boolean', 'mode': 'r'},
                  )


    manage_options = ( {'label':'Class',    'action':'manageClass'      },
                       {'label':'CSS',      'action':'manageCSS'        },
                       {'label':'XML',      'action':'manageXML'        },
                       {'label':'Data',     'action':'manageDataSource' },
                     )                              + \
                     PropertyManager.manage_options + \
                     SimpleItem.manage_options

    security = ClassSecurityInfo()


    def __init__(self, dlg_id, package = ''):
        """\brief Constructs a DialogContainer."""
        self.id         = dlg_id
        self.css        = ''
        self.xml        = ''
        self.py         = ''
        self.defaultXml = True
        self.defaultCss = True
        self.defaultPy  = True
        self.package    = package
        self.demo       = None
        self.changed    = False
        self.compiled   = None
        self.classname  = self.id + self.package

        self.loadDefaultClass()
        self.loadDefaultCss()
        self.loadDefaultXml()


    def loadDefaultClass(self):
        """\brief Loads the default class from file."""
        filename = '%s/%s/dialogs/%s.py' % ( getZopRAPath(),
                                             self.package,
                                             self.id )

        if os.path.exists(filename):
            fHandle        = open(filename, 'r')
            self.py        = fHandle.read()
        else:
            self.py        = ''
        self.defaultPy = True
        self.changed   = True


    def loadDefaultCss(self):
        """\brief Loads the default css from file."""

        filename = '%s/%s/dialogs/%s.css' % ( getZopRAPath(),
                                              self.package,
                                              self.id )
        if os.path.exists(filename):
            fHandle         = open(filename, 'r')
            self.css        = fHandle.read()
        else:
            self.css        = ''
        self.defaultCss = True
        self.changed    = True


    def loadDefaultXml(self):
        """\brief Loads the default xml from file."""

        filename = '%s/%s/dialogs/%s.xml' % ( getZopRAPath(),
                                              self.package,
                                              self.id )
        if os.path.exists(filename):
            fHandle  = open(filename, 'r')
            self.xml        = fHandle.read()
        else:
            self.xml        = ''
        self.defaultXml = True
        self.changed    = True


    def createDialog(self, param_dict):
        """\brief Creates a dialog."""

        # check self.py
        if not self.py:
            err = 'Internal Error: Code for instant compilation missing.'
            raise ValueError(err)

        # prepare globals
        # TODO: why globals?
        # globals()['manager']    = self.getParentNode().getManager()
        # globals()['param_dict'] = param_dict
        manager = self.getParentNode().getManager()

        if not hasattr(self, 'classname'):
            self.classname = self.id

        # check to get rid of old name-handling
        if self.classname == self.id + self.package:
            self.classname = self.id

        # prepare dialog

        # create a module for the dialog
        if self.package:
            modname = 'zopra.core.%s.%s' % (self.package, self.classname)
        else:
            modname = 'zopra.core.%s' % (self.classname)
        if sys.modules.has_key(modname):
            mod = sys.modules[modname]
        else:
            # create a module
            mod = imp.new_module(modname)

            # store it in sys.modules
            sys.modules[modname] = mod

            # get the package module
            if self.package:
                packagemodname = 'zopra.core.%s' % self.package
                attr           = self.package
            else:
                packagemodname = 'zopra.core'
                attr           = 'ZMOM'
            packagemod = __import__( packagemodname, globals(), locals(), [attr] )

            # add module there too
            setattr(packagemod, self.classname, mod)

        # our namespace is the module dictionary
        namespace = mod.__dict__

        # set the extensionmodule in the module if not present
        if not namespace.has_key(self.classname) or not namespace.get(self.classname):
            # exec the compiled dialog code in the module
            exec compile(self.py, '<string>', 'exec') in namespace


        extension = namespace.get(self.classname)

        # old global handling
        # if not self.classname in globals():
        #    exec compile(self.py, '<string>', 'exec') in globals()

        # extension = globals().get(self.classname)


        dlg = extension(manager, param_dict)

        # iterate over available settings
        for attr in self._properties:
            dlg.setParam( attr['id'],
                          getattr(self, attr['id']),
                          manager )

        return dlg


    def removeDialogExtensionFromModule(self):
        """\brief remove the dialog module from the parent module for reloading"""
        # create a module for the dialog
        if self.package:
            modname = 'zopra.core.%s.%s' % (self.package, self.classname)
        else:
            modname = 'zopra.core.%s' % (self.classname)
        if sys.modules.has_key(modname):
            mod = sys.modules[modname]

            if hasattr(mod, self.classname):
                delattr(mod, self.classname)


    def createDialogFromXml(self):
        """\brief Creates the dialog from the given xml."""
        dlg  = hgWidgetFactory.create( StringIO(self.xml) )
        zDlg = Dialog()
        return HTML( zDlg.getHtml() )(self)


    def removeFromSessions(self):
        """\brief The function removes all running dialogs from the session
                  object to avoid pickle errors while using to different
                  versions of this dialogs code.

        Warning this function does not care if a user is using the dialog!
        If you choose to remove the dialog from the sessions make sure that
        nobody is using this dialog.

        This function assumes that we have a temp_folder in the root node and
        a session_data container in the temp_folder.
        """
        parent = self.getParentNode()
        while hasattr(parent,                 'getParentNode') and \
              hasattr(parent.getParentNode(), 'getParentNode'):
            parent = parent.getParentNode()

        # we have now the overall parent
        parent.temp_folder.session_data._reset()


    security.declareProtected('View', 'show')
    def show(self, REQUEST):
        """\brief Handles the showing of a dialog."""

        # get dialog handler and session object
        dlgHandler = self.getParentNode()
        session    = REQUEST.SESSION
        form       = REQUEST.form
        name       = REQUEST.form.get('uid')

        if dlgHandler and session:

            # refresh dialog modules with changed basecode
            if self.changed is True:
                # delete Dialog if possible
                if name:
                    dlgHandler.delDialog(name, session)
                # reload the dialog class
                self.removeDialogExtensionFromModule()
                self.changed = False

            # get dialog from session (or reload it)
            dlg = dlgHandler.getDialog(self.getId(), session, name, form)
            dlg.setAction( '%s/dlgHandler/show' % dlgHandler.getManager().absolute_url() )

            # sets the active window
            app = dlgHandler.getApplication( session )
            app.active_window = dlg

            # execute dialog
            dlg.execDlg(dlgHandler.getManager(), REQUEST)

            # dialog handling bug (app / browser.back problem) fix
            # set the $_dialog_uid_$
            # dlg.add(hgProperty('$_dialog_uid_$', dlg.getUid(), parent = dlg)

            # put it back online
            return HTML( dlg.getHtml() )(self, None)

        # error message because of missing dlgHandler or session object
        dlg = getStdDialog('Error Message')
        dlg.add( 'Missing dlgHandler or session object.')
        dlg.add( 'Please report this error message.' )
        return HTML( dlg.getHtml() )(self, None)


    ##########################################################################
    #
    # Manage Methods
    #
    ##########################################################################
    def manageClass(self, REQUEST):
        """\brief Returns a css manage tab."""

        # action handling
        if 'save' in REQUEST.form:
            if 'py' in REQUEST.form:

                # string preparation
                code            = REQUEST.form['py']
                code            = code.replace('\r\n', '\n')
                code           += '\n'
                self.py         = code
                self.defaultPy  = False
                self.changed    = True

        elif 'load' in REQUEST.form:
            self.loadDefaultClass()

        elif 'reset' in REQUEST.form:
            self.removeFromSessions()

        py_edit = hgTextEdit( self.py,
                              name  = "py",
                              flags = hgTextEdit.MULTILINE )
        py_edit.setSize(79, 20)

        dlg        = getStdZMOMDialog()
        dlg.header = '<dtml-var manage_page_header><dtml-var manage_tabs>'
        dlg.footer = '<dtml-var manage_page_footer>'
        dlg.setAction( 'manageClass' )
        dlg.add( 'You may edit the python class for this dialog using the ' )
        dlg.add( 'form below. You may also upload the python class for this')
        dlg.add( ' document from a local file. Click the browse button to ' )
        dlg.add( 'select a local file to upload.' )
        dlg.add( hgLabel('<br>') )
        dlg.add( py_edit        )
        dlg.add( hgLabel('<br>') )
        dlg.add( hgPushButton( 'Save Changes',   name = 'save'  ) )
        dlg.add( hgPushButton( 'Load Default',   name = 'load'  ) )
        dlg.add( hgPushButton( 'Reset Sessions', name = 'reset' ) )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def manageCSS(self, REQUEST):
        """\brief Returns a css manage tab."""

        # action handling
        if 'save' in REQUEST.form:
            if 'css' in REQUEST.form:
                self.css        = REQUEST.form['css']
                self.defaultCss = False
                self.changed    = True

        elif 'load' in REQUEST.form:
            self.loadDefaultCss()


        css_edit = hgTextEdit( self.css,
                               name  = "css",
                               flags = hgTextEdit.MULTILINE )
        css_edit.setSize(79, 20)

        dlg = getStdZMOMDialog()
        dlg.header = '<dtml-var manage_page_header><dtml-var manage_tabs>'
        dlg.footer = '<dtml-var manage_page_footer>'
        dlg.setAction( 'manageCSS' )
        dlg.add( 'You may edit the css settings for this dialog using the ' )
        dlg.add( 'form below. You may also upload the css settings for this' )
        dlg.add( ' document from a local file. Click the browse button to ' )
        dlg.add( 'select a local file to upload.' )
        dlg.add( hgLabel('<br>') )
        dlg.add( css_edit        )
        dlg.add( hgLabel('<br>') )
        dlg.add( hgPushButton( 'Save Changes', name = 'save' ) )
        dlg.add( hgPushButton( 'Load Default', name = 'load' ) )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def manageXML(self, REQUEST):
        """\brief Returns a xml manage tab."""

        # action handling
        if 'save' in REQUEST.form:
            if 'xml' in REQUEST.form:
                self.xml        = REQUEST.form['xml']
                self.defaultXml = False
                self.changed    = True

        elif 'load' in REQUEST.form:
            self.loadDefaultXml()

        xml_edit = hgTextEdit( self.xml, flags = hgTextEdit.MULTILINE )
        xml_edit.setSize(79, 20)

        dlg = getStdZMOMDialog()
        dlg.header = '<dtml-var manage_page_header><dtml-var manage_tabs>'
        dlg.footer = '<dtml-var manage_page_footer>'
        dlg.add( 'You may edit this dialog using the form below.' )
        dlg.add( 'You may also upload the xml for this document'  )
        dlg.add( ' from a local file. Click the browse button to select ' )
        dlg.add( 'a local file to upload.' )
        dlg.add( hgLabel('<br>') )
        dlg.add( xml_edit )
        dlg.add( hgLabel('<br>') )
        dlg.add( hgPushButton( 'Save Changes', name = 'save' ) )
        dlg.add( hgPushButton( 'Load Default', name = 'load' ) )
        return HTML( dlg.getHtml() )(self, REQUEST)


    def manageDataSource(self, REQUEST):
        """\brief Returns a data source manage tab."""
        xml_edit = hgTextEdit( flags = hgTextEdit.MULTILINE )
        xml_edit.setSize(79, 20)

        dlg = getStdZMOMDialog()
        dlg.header = '<dtml-var manage_page_header><dtml-var manage_tabs>'
        dlg.footer = '<dtml-var manage_page_footer>'
        dlg.add( 'You may edit this dialog using the form below.' )
        dlg.add( 'You may also upload the xml for this document'  )
        dlg.add( ' from a local file. Click the browse button to select ' )
        dlg.add( 'a local file to upload.' )
        dlg.add( hgLabel('<br>') )
        dlg.add( xml_edit )
        dlg.add( hgLabel('<br>') )
        dlg.add( hgPushButton( 'Save Changes' ) )
        dlg.add( hgPushButton( 'Load Default' ) )
        return HTML( dlg.getHtml() )(self, REQUEST)
