from PyHtmlGUI.kernel.hgWidget                  import hgWidget
from PyHtmlGUI.dialogs.hgDialog                 import hgDialog
from PyHtmlGUI.dialogs.hgFormlessDialogLayout   import hgFormlessDialogLayout
from PyHtmlGUI.widgets.hgLabel                  import hgNEWLINE, hgProperty
from PyHtmlGUI.widgets.hgPushButton             import hgPushButton

from zopra.core                                 import HTML

from zopra.core.dialogs.Dialog                  import Dialog
from zopra.core.elements.Styles.Default         import ssiA,         \
                                                       ssiA_VISITED, \
                                                       ssiDLG_NOBORDER
from zopra.core.widgets                         import getBackButtonStr


dlgHeader = '<dtml-var standard_html_header>'
dlgFooter = '<dtml-var standard_html_footer>'


def getStdDialog(title = '', action = None, name = None, formless = False):
    """ This method returns a standard ZopRA dialog.

    @param title
    @param action
    @param name
    @param formless
    @return hgDialog
    """
    if formless:
        dlg = hgFormlessDialogLayout(title = title, name = name)
    else:
        dlg = hgDialog(title = title, action = action, name = name)

    dlg.setHeader(dlgHeader)
    dlg.setFooter(dlgFooter)

    # styles
    dlg._styleSheet.getSsiName( ssiA         )
    dlg._styleSheet.getSsiName( ssiA_VISITED )
    return dlg


def getPlainDialog(action, parent, border = True):
    """ This method returns a captionless formcontaining dialog with one
        widget with grid layout inside without header/footer

    @param action
    @param parent
    @param border
    @return hgDialog, hgWidget
    """
    dlg = hgDialog(action = action, parent = parent)
    dlg.setHeader('')
    dlg.setFooter('')

    if not border:
        # FIXME: get rid of border -> new style
        # raise ValueError(len(dlg._styleSheet.getStyleSheetItems()))
        dlg._styleSheet.add(ssiDLG_NOBORDER)
        dlg.setSsiName(ssiDLG_NOBORDER.name())

    # mask
    mask   = hgWidget(parent = dlg)
    dlg.add(mask)
    return dlg, mask


def getStdZMOMDialog(title = '', name = None, flags = 0):
    """ This method returns a standard ZopRA dialog.

    @param title
    @param name
    @param flags
    @return hgDialog
    """
    dlg  = Dialog( name = name, flags = flags )

    # in case of embedded dialog, title has to be set after initialization
    dlg.caption = title

    return dlg


def getEmbeddedDialog( title    = '',
                       action   = None,
                       name     = None,
                       formless = True,
                       parent   = None ):
    """ This method returns a standard ZopRA dialog with empty header
        and footer.

    @param title
    @param action
    @param name
    @param formless
    @param parent
    @return hgDialog
    """
    if formless:
        dlg = hgFormlessDialogLayout( title  = title,
                                      name   = name,
                                      parent = parent )
    else:
        dlg  = hgDialog( title  = title,
                         action = action,
                         name   = name,
                         parent = parent )
    dlg.setHeader( '' )
    dlg.setFooter( '' )

    # styles
    dlg._styleSheet.getSsiName( ssiA         )
    dlg._styleSheet.getSsiName( ssiA_VISITED )
    return dlg


def getAccessDialog(manager):
    """ This method returns the HTML source of an access denied dialog.

    @param manager
    @return String - a HTML page with an access denied dialog
    """
    dlg  = getStdDialog('Access Denied')

    dlg.add(hgNEWLINE)
    dlg.add('<center>')
    dlg.add('Please login to access this function.')
    dlg.add('</center>')
    dlg.add(hgNEWLINE)
    dlg.add(manager.getBackButtonStr())
    return HTML( dlg.getHtml() )(manager, None)
