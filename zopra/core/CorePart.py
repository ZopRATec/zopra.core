############################################################################
#    Copyright (C) 2004 by Ingo Keller                                     #
#    <webmaster@ingo-keller.de>                                            #
#                                                                          #
# Copyright: See COPYING file that comes with this distribution            #
#                                                                          #
############################################################################
""" Provides functions to get the managers and dialogs and some module
    functions.
"""

#
# Python Language Imports
#
from types                           import ListType


#
# PyHtmlGUI Imports
#
from PyHtmlGUI.kernel.hgWidget       import hgWidget

from PyHtmlGUI.widgets.hgLabel       import hgNEWLINE, hgProperty
from PyHtmlGUI.widgets.hgPushButton  import hgPushButton

#
# ZopRA Imports
#
from zopra.core                      import HTML, Folder
from zopra.core.dialogs              import getStdDialog


# list widget constants for handling

FCB_DEFAULT_FILTER_TEXT = '<Filter Text>'
FILTER_EDIT = 'filter_'

# Mask Types
MASK_ADD    = 0x0001
MASK_ADMIN  = 0x0002
MASK_EDIT   = 0x0004
MASK_SEARCH = 0x0008
MASK_SHOW   = 0x0010
MASK_HEAD   = 0x0020
MASK_REDIT  = 0x0040

# Database Column Types
COL_TEXT        = 'TEXT'
COL_DATE        = 'DATE'
COL_INT4        = 'INT4'
COL_INT8        = 'INT8'
COL_FLOAT       = 'FLOAT'
COL_SEQ         = 'SEQ'
COL_URL         = 'URL'
COL_CURRENCY    = 'NUMERIC(10,2)'
COL_LOOKUPLIST  = 'singlelist'

#
# Table Constants
#
COL_TYPE        = 'TYPE'
COL_LABEL       = 'LABEL'
COL_INVIS       = 'INVIS'
COL_REFERENCE   = 'REFERENCE'
COL_DEFAULT     = 'DEFAULT'
COL_PRIMARY_KEY = 'PRIMARY KEY'

# fill the.getStyleSheet()
dummyWidget = hgWidget()


folder_types = ['Folder', 'ATFolder']


class CorePart(Folder):
    """ The CorePart class extends the Folder class for all situations that can be handled in the
        context of Zope and without any other ZopRA classes.
    """
    _classType     = ['CorePart']
    _properties    = Folder._properties
    manage_options = Folder.manage_options

    def getClassName(self):
        """ This method returns the class name.

        @result string - class name (self.__class__.__name__)
        """
        return self.__class__.__name__


    def getClassType(self):
        return self._classType


    def __init__(self, title = None, part_id = None):
        """\brief Constructs a CorePart"""
        self.title     = title
        self.id        = part_id


    def getBackButtonStr(self, REQUEST = None, prop = True):
        """ Returns a back button string.

        Wraps getBackButton method.

        @return String - contains the HTML representation for the back button.
        """
        return self.getBackButton(REQUEST, prop).getHtml()


    def getBackButton(self, REQUEST = None, prop = True, parent = None):
        """\brief Returns a back button.

        The function tries to keep track of how often the back button has to be
        pressed to go back to a specific site and emulates this by one button.
        But it only works if the function gets a REQUEST object.

        \n
        \return back button.
        """
        if REQUEST is None:
            btn_go = hgPushButton(' Back ', parent = parent)
            btn_go.setFunction('history.back()', True)
            return btn_go

        if 'go' in REQUEST:
            number  = REQUEST['go']
            if isinstance(number, ListType):
                number = number[0]
            back_go = int(number) - 1
        else:
            back_go = -1
        btn_go = hgPushButton(' Back ')
        btn_go.setFunction('history.go(%s)' % back_go, True)
        ret = btn_go
        if prop:
            ret += hgProperty('go', back_go)
        if parent:
            ret.reparent(parent)
        return ret


    def getContainer(self):
        """ Returns the Zope container where the actual object is in.

        @return Zope Container, otherwise None
        """
        not_found = True
        container = self
        # stack = ['start:']
        while not_found:
            # stack.append('-> ' + str(container))
            # if hasattr(container, 'id'):
            #     stack.append(str(container.id))

            if not container:
                # something went wrong, didn't find container
                # try _container value (set temporarily for startupconfig)
                if hasattr(self, '_container') and self._container:
                    return self._container
                else:
                    # try to get folder name from physical path
                    foldername = self.getPhysicalPath()[-2]
                    container = None

                    if foldername:

                        # getattr uses aquisition
                        container = getattr(self, foldername)

                    else:

                        # top level, get root
                        container = self.restrictedTraverse('/')

                    if not container:
                        raise ValueError('No Container found.')

                    return container

            container = container.getParentNode()
            # first folder is returned
            if hasattr(container, 'meta_type') and container.meta_type in folder_types:
                not_found = False

            # TODO: top level check to stop iteration on top level?

        return container


    def setContainer(self, container):
        """ set a reference to the container.
            Only for temporary container ref!
        """
        self._container = container


    def delContainer(self):
        """ Remove temporary container reference. """
        if hasattr(self, '_container'):
            del self._container


    def getManager(self, name, obj_id = None):
        """ Returns the specified manager.

        If you use DTML to call a manager, be sure to work in the managers directory!
        Use <dtml-with <dirname>> to achieve this. Otherwise, the dtml's directory will
        be misunderstood as container and the searched manager will never be found.

        @param name  The argument \a name is the name of the manager.
        @param id    The argument \a id is to specify a manager id in an
                     environment where more than one manager of a special type
                     is instantiated.

        @return a manager object if one was found, otherwise None.
        """
        container = self.getContainer()
        if name and hasattr(container, 'objectValues'):

            # iterate over container content
            for obj in container.objectValues():

                if hasattr(obj, 'getClassType') and name in obj.getClassType():

                    # if id is given then look also for these
                    if obj_id:
                        if hasattr(obj, 'id') and str(obj.id) == obj_id:
                            return obj

                    # in all other cases return with the first object
                    # that was found
                    else:
                        return obj

        return None


    def getObjByMetaType(self, meta_type, obj_id = None):
        """ Returns a specified object with \a meta_type and \a id.

        @param meta_type   The argument \a name is the name of the manager.
        @param id          The argument \a id is to specify a object id in an
                           environment where more than one object of a special
                           type is instanciated.

        @return a object if one was found, otherwise None.
        """
        container = self.getContainer()

        while container:

            if meta_type and hasattr(container, 'objectValues'):

                # iterate over container content
                for obj in container.objectValues():

                    if hasattr(obj, 'meta_type') and obj.meta_type == meta_type:

                        # if id is given then look also for these
                        if obj_id:
                            if hasattr(obj, 'id') and str(obj.id) == obj_id:
                                return obj

                        # in all other cases return with the first object
                        # that was found
                        else:
                            return obj
            if container is None or container.isTopLevelPrincipiaApplicationObject:
                break
            container = container.getParentNode()
        return None


    def getTitle(self):
        """ Returns the title of the object.

        @return String with the title, otherwise an empty string.
        """
        return self.title if hasattr(self, 'title') else ''


    def getId(self):
        """ Returns the id of the object.

        @return String with the id, otherwise an empty string.
        """
        return self.id if hasattr(self, 'id') else ''


    def getCSS(self):
        """\brief Returns the full css of the system."""
        return dummyWidget._styleSheet.getCss()


    def getErrorDialog(self, message, REQUEST = None, html = True):
        """\brief Returns the html source of an error dialog.

        The error dialog is a simple dialog that only shows the error string
        and a back button.

        \param message   The argument \a message is a string with the error
        message.
        \param REQUEST  (optional)
        \n
        \return error html page
        """
        dlg  = getStdDialog( title = 'Error' )

        dlg.add(hgNEWLINE)
        dlg.add('<center>')
        dlg.add( message )
        dlg.add('</center>')
        dlg.add(hgNEWLINE)
        dlg.add(self.getBackButtonStr(REQUEST))
        return HTML( dlg.getHtml() )(self, None) if html else dlg


    def getUnauthorizedErrorDialog(self, message, REQUEST = None):
        """ Returns the HTML source of an error dialog for unauthorized users.

        The error dialog is a simple dialog that only shows the error string
        and a back button.

        @param message   The argument \a message is a string with the error message.
        @param REQUEST   (optional)
        @return error HTML page
        """
        dlg  = getStdDialog( title = 'Error' )
        # unauthorized errors cannot use the navigation and
        # contextMenu - header/footer
        dlg.setHeader('<dtml-var unauthorized_html_header>')
        dlg.setFooter('<dtml-var unauthorized_html_footer>')

        dlg.add(hgNEWLINE)
        dlg.add('<center>')
        dlg.add( message )
        dlg.add('</center>')
        dlg.add(hgNEWLINE)
        dlg.add(self.getBackButtonStr(REQUEST))
        return HTML( dlg.getHtml() )(self, None)
