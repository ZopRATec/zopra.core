from PyHtmlGUI.dialogs.hgDialog import hgDialog
from PyHtmlGUI.dialogs.hgFormlessDialogLayout import hgFormlessDialogLayout
from PyHtmlGUI.widgets.hgLabel import hgLabel
from zopra.core.elements.Styles.Default import ssiA
from zopra.core.elements.Styles.Default import ssiA_VISITED
from zopra.core.elements.Styles.Default import ssiDLG_LABEL


def getStdDialog(title="", action=None, name=None, formless=False):
    """This method returns a standard ZopRA dialog."""
    if formless:
        dlg = hgFormlessDialogLayout(title=title, name=name)
    else:
        dlg = hgDialog(title=title, action=action, name=name)

    dlg.setHeader("<dtml-var standard_html_header>")
    dlg.setFooter("<dtml-var standard_html_footer>")

    # styles
    dlg._styleSheet.getSsiName(ssiA)
    dlg._styleSheet.getSsiName(ssiA_VISITED)
    return dlg


def dlgLabel(text, parent=None):
    """This method returns a text label widget with the given text and parent.

    :param text: text that the label will display
    :param parent: parent widget
    :return: constructed widget
    :rtype: PyHtmlGI.widgets.hgLabel
    """
    label = hgLabel(text, parent=parent)
    label._styleSheet.getSsiName(ssiDLG_LABEL)
    label.setSsiName(".dlg_label")
    return label
