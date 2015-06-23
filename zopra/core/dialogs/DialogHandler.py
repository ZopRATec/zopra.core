############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
import sys
from types                                          import StringType, ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                                      import E_PARAM_FAIL, \
                                                           checkType
from PyHtmlGUI.kernel.hgApplication                 import hgApplication
from PyHtmlGUI.kernel.hgTable                       import hgTable
from PyHtmlGUI.kernel.hgBoxLayout                   import hgBoxLayout
from PyHtmlGUI.kernel.hgGridLayout                  import hgGridLayout

from PyHtmlGUI.widgets.hgLabel                      import hgLabel, hgProperty
from PyHtmlGUI.widgets.hgLineEdit                   import hgLineEdit
from PyHtmlGUI.widgets.hgPushButton                 import hgPushButton


#
# ZMOM Imports
#
from zopra.core                                     import HTML, Folder, ClassSecurityInfo
from zopra.core.dialogs                             import getStdZMOMDialog
from zopra.core.dialogs.DialogContainer             import DialogContainer
from zopra.core.utils                               import getParentManager


class DialogHandler(Folder):
    """\class DialogHandler"""

    # class variables
    _className = 'DialogHandler'
    _classType = [_className]
    meta_type  = _className

    _properties    = Folder._properties
    manage_options = Folder.manage_options + \
                     ( {'label':'Overview', 'action':'manageOverview' },
                     )

    App         = 'hgApplication'
    security = ClassSecurityInfo()
    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################

    def __init__(self, name):
        """\brief Constructs a DialogHandler."""
        Folder.__init__(self, name)
        self.running_apps = {}


    def getApplication(self, session):
        """\brief Checks if the user already has a hgApplication running.

        If not a new hgApplication will be started.
        \return hgApplication
        """
        app = session.get( self.App )

        # do we have already a running application ?
        if app is None:
            app                 = hgApplication()
            session[ self.App ] = app

        return app


    def printApplicationInfo(self, REQUEST):
        """\brief Prints the application info to the command line."""
        app = self.getApplication( REQUEST.SESSION )
        print app.dumpObjectTree()


    def getDialog(self, dlg_name, session, name = None, *params):
        """\brief Returns dialog \a dlg_name from \a session; parameter for the
                  createDialog function are given by \a *param.

        If no dialog is there with given name than try to build one.
        """
        assert session, E_PARAM_FAIL % 'session'
        assert checkType( 'dlg_name', dlg_name, StringType       )
        assert checkType( 'name',     name,     StringType, True )

        # initialise if application not already there and fetch dialog
        app = self.getApplication( session )

        # TODO: application usage was taken out again to allow multibrowser work
        # the app is loaded anyway and ZMOMDialogContainer.show sets the dlg as mainWidget
        # but this is only used as fallback to fetch the dialog later on
        # if the property handling fails

        # if we already have a valid dialog then return it
        if name is not None:

            # name parameter used for dialog uid
            # TODO: Rename name to dlg_uid
            dialog = session.get( str(name) )
            if dialog:
                return dialog

        # otherwise create it
        if hasattr(self, dlg_name):
            # get the container for the dlg_name
            dlgContainer = getattr(self, dlg_name)
            # let the container create a new dialog
            dialog       = dlgContainer.createDialog(*params)
            # TODO: put dialog as child into app to have proper handling?

            # add the uid into its display as hgProperty to later on find 
            # the dialog without the application
            prop = dialog.child('$_dialog_uid_$')
            # findWidget returns the index, -1 indicates notfound
            layprop = prop and dialog.layout() and (dialog.layout().findWidget(prop) != -1)
            if not layprop:
                if not prop:
                    # wizards destroy their layout every turn, so we need to add the child everytime
                    prop = hgProperty('$_dialog_uid_$', dialog.getUid(), parent = dialog)
                    dialog.add(prop)
                layout = dialog.layout()
                # depending on class of layout, add the widget
                if isinstance(layout, hgBoxLayout):
                    layout.insertWidget(-1, prop)
                elif isinstance(layout, hgGridLayout):
                    layout.addWidget(prop, layout.numRows() + 1, 0)
                else:
                    # no layout -> enough to have child in dialog
                    pass

            # manually put dialog into session
            session[ str(dialog.getUid()) ] = dialog
            return dialog

        # we don't know the dialog
        message = 'Dialog %s unknown.' % dlg_name
        raise RuntimeError( message )


    def getDialogContainer( self, name ):
        """\brief Returns the container specified by name."""
        assert checkType( 'name', name, StringType )
        if hasattr( self, name ):
            return getattr( self, name )


    def delDialog(self, name, session):
        """\brief Removes the dialog from the session."""
        assert checkType( 'name', name, StringType )
        assert session, E_PARAM_FAIL

        dlg = session.get(name)

        # destroy the dialog
        dlg.destroy()

        # remove dialog from session / app
        app     = self.getApplication( session )
        dialog  = app.child( name )
        if dialog is not None:
            app.removeChild(dialog)

        # test session for uid
        if session.has_key(name):
            del session[name]


    def installDialog(self, name, package = ''):
        """\brief Install new dialog in the handler."""
        assert checkType( 'name',     name,    StringType )
        assert checkType( 'npackage', package, StringType )

        dialog       = DialogContainer(name, package)
        dialog.title = self.getManager().title
        self._setObject( name, dialog )


    def getManager(self):
        """This method returns the manager that is associated to this dialog
           handler.

        @returns Manager
        """
        return getParentManager(self)


    def manageOverview(self, REQUEST = None):
        """\brief Returns a overview manage tab."""

        # install handling
        if REQUEST is not None:

            if REQUEST.form.get('install'):

                self.installDialog( REQUEST.form.get('name'),
                                    REQUEST.form.get('package') )


        dlg = getStdZMOMDialog('')
        dlg.setHeader( '<dtml-var manage_page_header><dtml-var manage_tabs>' )
        dlg.setFooter( '<dtml-var manage_page_footer>'                       )

        form = dlg.getForm()

        tab             = hgTable()
        tab._old_style  = False
        form.add(tab)

        tab[0, 1] = hgLabel( 'Name'    )
        tab[0, 2] = hgLabel( 'Package' )

        row = 0
        for index, item in enumerate( self.objectValues() ):
            tab[index + 1, 1] = item.getId()
            tab[index + 1, 2] = item.package
            row += 1

        row        += 2
        tab[row, 0] = hgLabel( 'Install Dialog:' )
        tab[row, 1] = hgLineEdit( name = 'name' )
        tab[row, 2] = hgLineEdit( name = 'package' )
        tab[row, 5] = hgPushButton('Install', name = 'install')

        return HTML( dlg.getHtml() )(self, REQUEST)

    security.declareProtected('View', 'show')
    def show(self, REQUEST):
        """\brief Shows the active window of the application."""
        app = self.getApplication( REQUEST.SESSION )

        # TODO Dialog handling bug
        # zur sicherheit zusaetzlich mit der uid arbeiten? -> als Property in hgDialog-Darstellung einbauen?
        # --> Verwendung von browser.back verwirrt die app (neue dialoge angezeigt statt vorhergehenden) net mehr
        # problem bei fehlender uid (weswegen auch immer) -> fallback auf app?
        # problem wenn dialog net mehr existiert-> uid kommt per alter form, dialog schon kaputt
        # solange das net behoben ist, handling net noetig 
        # --> SearchDialoge rueckgebaut auf searchForm voruebergehend

        # dialog handling bug (app / multibrowserwindow problem) fix
        # get the $_dialog_uid_$
        dlg = None
        if REQUEST.form.has_key('$_dialog_uid_$'):
            dlgid = REQUEST.form.get('$_dialog_uid_$')
            if isinstance(dlgid, ListType):
                dlgid = dlgid[0]
            dlg = REQUEST.SESSION.get(str(dlgid))

        if not dlg:
            # FALLBACK TO ONE-WINDOW HANDLING VIA APP
            # shows the active window
            dlg = app.activeWindow()

            # shows the main widget
            if not dlg:
                dlg = app.mainWidget()

        # the url to jump to if dialog is done
        target = None

        # perform dialog functionality
        if dlg:
            uid = str(dlg.getUid())
            # make sure the dlg is from the manager
            # this check is still here just to be sure
            mgr = self.getManager()
            found = False
            for row in mgr._dlgs:
                if row[0] == dlg._className:
                    found = True

            if not found:
                msg = 'Dialog was not found in the manager. Please only operate with one Browserwindow when using dialogs. '
                msg += 'Until further notice, the dialog handling mechanism will not be able to deal with different dialogs '
                msg += 'executed by the same user in different browser windows at the same time.'
                mgr.displayError(msg, 'Dialog handling error')

            try:
                # first of all, refresh it
                dlg.refresh()

                # now set the action (needs only to be done once, how can I check this?)
                dlg.setAction( 'show' )

                dlg.execDlg( self.getManager(), REQUEST )

                # running -> present the dialog again
                if dlg.result() == dlg.Running:
                    # print '#######################################################################'
                    # print dlg.dumpObjectTree()
                    # print '#######################################################################'

                    # the dialog is valid and running, we are through
                    # sometimes between here and next call, it looses its state
                    # to avoid that, we put it into the session again and commit the transaction
                    # removed for testing whether slot/signal bugfix fixed this too
                    # REQUEST.SESSION[str(dlg.getUid())] = dlg

                    # dialog handling bug (app / browser.back problem) fix
                    # set the $_dialog_uid_$
                    prop = dlg.child('$_dialog_uid_$')
                    # findWidget returns the index, -1 indicates notfound
                    layprop = prop and dlg.layout() and (dlg.layout().findWidget(prop) != -1)
                    if not layprop:
                        if not prop:
                            # wizards destroy their layout every turn, so we need to add the child everytime
                            prop = hgProperty('$_dialog_uid_$', dlg.getUid(), parent = dlg)
                            dlg.add(prop)
                        layout = dlg.layout()
                        # depending on layout class, insert the widget
                        if isinstance(layout, hgBoxLayout):
                            layout.insertWidget(-1, prop)
                        elif isinstance(layout, hgGridLayout):
                            layout.addWidget(prop, layout.numRows() + 1, 0)
                        else:
                            # no layout -> enough to have child in dialog
                            pass

                    # create dialog html
                    html = dlg.getHtml()

                    # this part is necessary to have the correct uptodate dialog on next call
                    # and no stupid older memory version that confuses the state handling
                    # store dialog in session again
                    REQUEST.SESSION[uid] = dlg
                    # commit
                    import transaction
                    transaction.commit()

                    # return dialog html
                    return HTML( html )( self, None)

                # finished -> perform the finished state actions and display
                # the main site again
                else:
                    if dlg.result() == dlg.Accepted:
                        dlg.performAccepted( self.getManager() )

                    elif dlg.result() == dlg.Rejected:
                        dlg.performRejected( self.getManager() )

                    # get the target_url from the dialog
                    if hasattr(dlg, 'target_url') and dlg.target_url:
                        target = dlg.target_url

                    # kill the dialog
                    self.delDialog(str(dlg.getUid()), REQUEST.SESSION)

            except Exception, inst:
                # error occured, first argument should be valid html
                # in case of ValueError
                if hasattr(inst, 'args'):
                    attrs = inst.args
                    if len(attrs) > 0:
                        source = str(attrs[0])
                        # source is very ugly normally, check it
                        if source and len(source) > 5 and source[:5] == '<html':
                            # do not need new dialog
                            html = source
                        else:
                            # build dlg with header/footer around source
                            from zopra.core.CorePart import getStdDialog
                            dlgerr  = getStdDialog(title = 'Dialog Handling Error Report')
                            dlgerr.add(source)

                            # add a message to restart the dialog
                            msg = '<br><br><strong>This error was encountered while executing a dialog. '
                            msg += 'The dialog may be invalid now. '
                            msg += 'Please start again and do not use your browser\'s  back-button. <br>'
                            # display a link to the managers index_html
                            mgr = self.getManager()
                            msg += 'Use the following link to get back to the manager\'s start page: '
                            dlgerr.add(hgLabel(msg, parent = dlgerr))
                            link = hgLabel(mgr.getTitle(), mgr.absolute_url(), parent = dlgerr)
                            dlgerr.add(link)
                            dlgerr.add(hgLabel('</strong>', parent = dlgerr))

                            # create html
                            html = dlgerr.getHtml()

                        # but we should log the error anyway
                        if hasattr(mgr, 'error_log'):
                            error_log = getattr(mgr, 'error_log')
                            error_log.raising(sys.exc_info())

                        res = HTML( html )(self, None)

                        # abort transaction (sad but we have to for data consistency)
                        import transaction
                        transaction.abort()

                        # return html
                        return res
                    else:
                        # reraise
                        raise
                else:
                    raise
        if not target:
            # we have nothing -> shows the index_html of the manager
            manager_url = str(REQUEST.URL0).split('/')
            manager_id  = self.getManager().getId()
            new_url     = []

            for item in manager_url:
                new_url.append( item )

                if item == manager_id:
                    break

            target = '/'.join(new_url) + '/'

        return REQUEST.RESPONSE.redirect( target )
