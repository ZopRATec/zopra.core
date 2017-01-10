############################################################################
#    Copyright (C) 2004-2015 by ZopRATec GbR                               #
#    Ingo.Keller@zopratec.de                                               #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

from types                            import ListType

from PyHtmlGUI.widgets.hgCheckBox     import hgCheckBox
from PyHtmlGUI.widgets.hgComboBox     import hgComboBox
from PyHtmlGUI.widgets.hgDateEdit     import hgDateChooser
from PyHtmlGUI.widgets.hgFileSelector import hgFileSelector
from PyHtmlGUI.widgets.hgMultiList    import hgMultiList
from PyHtmlGUI.widgets.hgLabel        import hgProperty
from PyHtmlGUI.widgets.hgLineEdit     import hgLineEdit
from PyHtmlGUI.widgets.hgPushButton   import hgPushButton
from PyHtmlGUI.widgets.hgRadioButton  import hgRadioButton
from PyHtmlGUI.widgets.hgScrollBar    import hgScrollBar
from PyHtmlGUI.widgets.hgTabBar       import hgTab
from PyHtmlGUI.widgets.hgTextEdit     import hgTextEdit
from PyHtmlGUI.widgets.hgTimeChooser  import hgTimeChooser
from PyHtmlGUI.widgets.hgWidgetStack  import hgWidgetStack
from PyHtmlGUI.dialogs.hgWizard       import hgWizard



class guiHandler(object):
    """ The guiHandler class provides a mix-in for the GUI handling in the
        ZopRA infrastructure context.
    """
    _stdHeader = '<dtml-var standard_html_header>'
    _stdFooter = '<dtml-var standard_html_footer>'


    ##########################################################################
    #
    # Enumerations
    #
    ##########################################################################
    # enum DialogType
    Standalone = 1
    Embedded   = 2
    DialogType = [ Standalone, Embedded ]

    ##########################################################################
    #
    # Static Methods
    #
    ##########################################################################
    def _foundWidgetFunction(self, widget, value):
        """ This method is called if a \a widget was found that gets a new
            \a value.

        If you really know what you are doing you can overload this function
        to get different widget behavior.

        @param hgWidget - widget instance
        @param value    - value to update the hgWidget's state
        """
        # standard widget functions
        if isinstance(widget, hgPushButton):
            # only one button will be pushed per request
            # we handle this button at the end of all other things
            # store it for now
            if not hasattr(self, 'guiHandlerButtonPushed'):
                self.guiHandlerButtonPushed = widget
            else:
                if isinstance(widget, hgTab):
                    widget.clickedButton(widget.name)
                else:
                    widget.clicked()
                del self.guiHandlerButtonPushed

        elif isinstance(widget, hgLineEdit) or isinstance(widget, hgTextEdit):
            widget.setText(value)

        elif isinstance(widget, hgCheckBox):
            widget.setChecked(True)

        elif isinstance(widget, hgRadioButton):
            widget.setChecked(True)

        elif isinstance(widget, hgDateChooser):
            widget.setDate(value)

        elif isinstance(widget, hgTimeChooser):
            widget.setTime(value)

        elif isinstance(widget, hgComboBox):
            if value:
                widget.setCurrentValue( value )

        elif isinstance(widget, hgFileSelector):
            widget.setFileHandle(value)

        elif isinstance(widget, hgMultiList):
            if value:
                if not isinstance(value, ListType):
                    value = [value]
                widget.setSelectedValueList( value )

        elif isinstance(widget, hgScrollBar):
            if value == '>' or value == '\/':
                widget.nextLine()

            elif value == '<' or value == '/\\':
                widget.prevLine()


    def _processEvents( self, widget, form ):
        """ This method processes all events that occur on a form."""
        # back to default for all widgets that return no value at all
        # if they are empty -> see hgCheckBox where you don't get a off value
        # back
        # so they have to be set explicitly to a state, otherwise they will
        # be empty
        if isinstance(widget, hgCheckBox):
            widget.setChecked(False)
        elif isinstance(widget, hgRadioButton):
            widget.setChecked(False)
        elif isinstance(widget, hgMultiList):
            widget.resetSelected()

        # hgWizard hgWidgetStack solution
        # better way would be to set invisible pages to invisible
        # and ignore invisible widgets and their children
        if isinstance(widget, hgWidgetStack):
            par = widget.getParent()
            if isinstance(par, hgWizard):

                # the stack manages the children of the wizard
                # get visible page
                current = widget.visibleWidget()

                # jump over this level, continue with current page
                if current:
                    widget = current

        # handle img-buttons
        if isinstance(widget, hgPushButton) and widget._pixmap:
            if not form.has_key(widget.name) and      \
               ( form.has_key(widget.name + '.x') and \
                 form.has_key(widget.name + '.y') ):
                form[widget.name] = widget.btext
                # form[widget.name] = widget.name

        # normal procedure
        if form.has_key(widget.name):

            # radio buttons do all have the same name (same can happen for
            # check boxes)
            if isinstance(widget, hgRadioButton) or isinstance(widget, hgCheckBox):
                if str(widget.getValue()) != str(form[widget.name]):
                    # radioButton/checkBox have no children, we return
                    return

            self._foundWidgetFunction( widget, form[widget.name] )
            del form[widget.name]

        if widget.hasChildren():

            for child in widget.children():
                self._processEvents( child, form )


    ##########################################################################
    #
    # Static Methods
    #
    ##########################################################################
    @staticmethod
    def getBackButtonStr(REQUEST = None, prop = True):
        """\brief Returns a back button string.

        The function tries to keep track of how often a user should go back to a
        specific site. But it only works if the function gets a REQUEST object.

        \n
        \return back button string.
        """
        if not REQUEST:
            btn_go = hgPushButton(' Back ')
            btn_go.setFunction('history.back()', True)
            return btn_go.getHtml()

        if REQUEST.has_key('go'):
            number  = REQUEST['go']

            if isinstance(number, ListType):
                number = number[0]

            back_go = int(number) - 1

        else:
            back_go -= 1

        btn_go = hgPushButton(' Back ')
        btn_go.setFunction('history.go(%s)' % back_go, True)
        retstr = btn_go.getHtml()

        if prop:
            retstr += hgProperty('go', back_go)

        return retstr


    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__(self, flags = Standalone):
        """\brief Initialize the guiHandler."""

        if flags & self.Standalone:
            self.header = self._stdHeader
            self.footer = self._stdFooter

        elif flags & self.Embedded:
            self.header  = ''
            self.footer  = ''
            self.caption = ''

        # this is highly deprecated. The Property for dialog recognition is set
        # in DialogHandler.show(...). Still left it in here for backwards
        # compatibility. Have to check where this is used
        # TODO: check if and where this is used
        self.add( hgProperty( 'uid', self.name ) )


    def execDlg(self, manager, REQUEST):
        """ This method evaluates the \a REQUEST object and determines the
            changes of the widgets.
        """
        # no action on first call (form empty)
        if REQUEST.form:
            self._processEvents(self, REQUEST.form)

            # button gets processed last
            if hasattr(self, 'guiHandlerButtonPushed'):
                self._foundWidgetFunction(self.guiHandlerButtonPushed, None)


    def setParam(self, key, value, manager):
        """\brief Virtual function to set arbitrary dialog parameter."""
        pass


    def performAccepted(self, manager):
        """\brief This function is called after a dialog was accepted."""
        print 'accepted'


    def performRejected(self, manager):
        """\brief This function is called after a dialog was rejected."""
        print 'rejected'
