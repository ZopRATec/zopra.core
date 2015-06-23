from types                              import ListType

from PyHtmlGUI.widgets.hgDateEdit       import hgDateEdit
from PyHtmlGUI.widgets.hgLabel          import hgLabel, hgNEWLINE, hgProperty
from PyHtmlGUI.widgets.hgPushButton     import hgPushButton

from zopra.core.elements.Styles.Default import ssiDLG_LABEL, \
                                               ssiDLG_ACTION, \
                                               ssiDLG_MINI_SPACER


def dlgDateEdit(text, name):
    """ This method returns a data edit widget with the given text and name.

    The dlgDateEdit is per default used with the DD.MM.YYYY format.

    @param  text - gets displayed as default value
    @param  name - the widgets name
    @return hgDateEdit - constructed widget without an associated parent
    """
    return hgDateEdit( text,
                       '<font size="-1">(DD.MM.YYYY)</font>',
                       None,
                       name,
                       hgDateEdit.LABEL_RIGHT
                       )


def dlgLabel(text, parent = None):
    """ This method returns a text label widget with the given name and parent.

    @param text - text that the label will display
    @param parent - parent widget
    @return hgLabel - constructed widget
    """
    label = hgLabel(text, parent = parent)
    label._styleSheet.getSsiName( ssiDLG_LABEL )
    label.setSsiName( '.dlg_label' )
    return label


def dlgActionLabel(text, parent = None):
    """ This method returns a text label widget for dialog actions
        (bold, colored, centered).

    @param text - text that the label will display
    @param parent - parent widget
    @return hgLabel - constructed widget
    """
    label = hgLabel(text, parent = parent)
    label._styleSheet.add( ssiDLG_ACTION )
    label.setSsiName( ssiDLG_ACTION.name() )
    return label


def dlgMiniSpacer(parent):
    """ This method returns a text label widget which contains a unbreakable
        space to be used as a layout widget.

    @param parent - parent widget
    @return hgLabel - constructed widget
    """
    label = hgLabel('&nbsp;', parent = parent)
    label._styleSheet.add( ssiDLG_MINI_SPACER )
    label.setSsiName( ssiDLG_MINI_SPACER.name())
    return label


def getBackButton(self, REQUEST = None, prop = True, parent = None):
    """ This method returns a back button.

    The function tries to keep track of how often the back button has to be
    pressed to go back to a specific site and emulates this by one button.
    But it only works if the function gets a REQUEST object.

    @return hgPushButton - button with the history.back() action
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


def getBackButtonStr(REQUEST = None, prop = True):
    """ This method returns a back button string.

    Wraps getBackButton.

    @return String - back button string
    """
    return getBackButton(REQUEST, prop).getHtml()
