from __future__ import print_function
from zopra.core.types import ListType

from PyHtmlGUI.dialogs.hgWizard import hgWizard
from PyHtmlGUI.widgets.hgCheckBox import hgCheckBox
from PyHtmlGUI.widgets.hgComboBox import hgComboBox
from PyHtmlGUI.widgets.hgDateEdit import hgDateChooser
from PyHtmlGUI.widgets.hgFileSelector import hgFileSelector
from PyHtmlGUI.widgets.hgLabel import hgProperty
from PyHtmlGUI.widgets.hgLineEdit import hgLineEdit
from PyHtmlGUI.widgets.hgMultiList import hgMultiList
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from PyHtmlGUI.widgets.hgRadioButton import hgRadioButton
from PyHtmlGUI.widgets.hgScrollBar import hgScrollBar
from PyHtmlGUI.widgets.hgTabBar import hgTab
from PyHtmlGUI.widgets.hgTextEdit import hgTextEdit
from PyHtmlGUI.widgets.hgTimeChooser import hgTimeChooser
from PyHtmlGUI.widgets.hgWidgetStack import hgWidgetStack


class guiHandler(object):
    """The guiHandler class provides a mix-in for the GUI handling in the
    ZopRA infrastructure context."""

    _stdHeader = "<dtml-var standard_html_header>"
    _stdFooter = "<dtml-var standard_html_footer>"

    # enum DialogType
    Standalone = 1
    Embedded = 2
    DialogType = [Standalone, Embedded]

    def _foundWidgetFunction(self, widget, value):
        """This method is called if a widget was found that gets a new value.

        You can overload this method to get different widget behavior.

        :param widget: the widget instance
        :param value: value to update the widget state
        """
        # standard widget functions
        if isinstance(widget, hgPushButton):
            # only one button will be pushed per request
            # we handle this button at the end of all other things
            # store it for now
            if not hasattr(self, "guiHandlerButtonPushed"):
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
                widget.setCurrentValue(value)

        elif isinstance(widget, hgFileSelector):
            widget.setFileHandle(value)

        elif isinstance(widget, hgMultiList):
            if value:
                if not isinstance(value, ListType):
                    value = [value]
                widget.setSelectedValueList(value)

        elif isinstance(widget, hgScrollBar):
            if value == ">" or value == "\\/":
                widget.nextLine()

            elif value == "<" or value == "/\\":
                widget.prevLine()

    def _processEvents(self, widget, form):
        """This method processes all events that occur on a form."""
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
            if widget.name not in form and (
                widget.name + ".x" in form and widget.name + ".y" in form
            ):
                form[widget.name] = widget.btext
                # form[widget.name] = widget.name

        # normal procedure
        if widget.name in form:

            # radio buttons do all have the same name (same can happen for
            # check boxes)
            if isinstance(widget, hgRadioButton) or isinstance(widget, hgCheckBox):
                if str(widget.getValue()) != str(form[widget.name]):
                    # radioButton/checkBox have no children, we return
                    return

            self._foundWidgetFunction(widget, form[widget.name])
            del form[widget.name]

        if widget.hasChildren():

            for child in widget.children():
                self._processEvents(child, form)

    def __init__(self, flags=Standalone):
        """Initialize the guiHandler."""

        if flags & self.Standalone:
            self.header = self._stdHeader
            self.footer = self._stdFooter

        elif flags & self.Embedded:
            self.header = ""
            self.footer = ""
            self.caption = ""

        # this is highly deprecated. The Property for dialog recognition is set
        # in DialogHandler.show(...). Still left it in here for backwards
        # compatibility. Have to check where this is used
        # TODO: check if and where this is used
        self.add(hgProperty("uid", self.name))

    def execDlg(self, manager, REQUEST):
        """This method evaluates the REQUEST object and determines the changes of the widgets."""
        # no action on first call (form empty)
        if REQUEST.form:
            self._processEvents(self, REQUEST.form)

            # button gets processed last
            if hasattr(self, "guiHandlerButtonPushed"):
                self._foundWidgetFunction(self.guiHandlerButtonPushed, None)

    def setParam(self, key, value, manager):
        """Virtual function to set arbitrary dialog parameters."""
        pass

    def performAccepted(self, manager):
        """This function is called after a dialog was accepted."""
        print("accepted")

    def performRejected(self, manager):
        """This function is called after a dialog was rejected."""
        print("rejected")
