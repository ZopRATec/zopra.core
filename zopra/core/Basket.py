############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

#
# Python Language Imports
#
import string
from types                                   import ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgCheckBox            import hgCheckBox
from PyHtmlGUI.widgets.hgGroupBox            import hgGroupBox
from PyHtmlGUI.widgets.hgLabel               import hgLabel,   \
                                                    hgProperty
from PyHtmlGUI.kernel.hgGridLayout           import hgGridLayout
from PyHtmlGUI.kernel.hgTable                import hgTable
from PyHtmlGUI.stylesheet.hgStyleSheet       import hgStyleSheetItem

#
# ZopRA Imports
#
from zopra.core                              import HTML, SimpleItem
from zopra.core.dialogs                      import getStdZMOMDialog
from zopra.core.elements.Buttons             import DLG_FUNCTION,             \
                                                    BTN_BASKET_REMOVE,        \
                                                    BTN_BASKET_REMOVEALL,     \
                                                    BTN_BASKET_ACTIVATE,      \
                                                    BTN_BASKET_DEACTIVATE,    \
                                                    BTN_BASKET_ADD,           \
                                                    getPressedButton,         \
                                                    mpfBasketActivateButton,  \
                                                    mpfBasketDeactivateButton, \
                                                    mpfBasketRemoveButton,    \
                                                    mpfBasketRemoveAllButton
from zopra.core.dialogs.Dialog               import Dialog


ssiBASKET_GBOX = hgStyleSheetItem( '.basket_gbox'  )
ssiBASKET_GBOX.position().size().setWidth( '100%' )


# TODO: why is this a simpleitem? __init__ is overwritten -> seems stupid
# but undoing this leads to zope errors, so it stays a simpleitem for now.
class Basket(SimpleItem):
    """ The Basket class handles all basket operations.

        Functionality for an item basket to move items from one part of the
        application to another.
    """
#
# Class Properties
#
    _className = 'ZMOMBasket'
    _classType = [_className]

    def __init__(self):
        """\brief Constructs a Basket."""
        pass


    def getBasketHtml(self, mgr, REQUEST):
        """\brief basket button handling and display.
                Takes care of pressed basket buttons and tries to
                forward to a given "repeataction" (in the session).
                Returns the html source of the basket main page
                or the repeataction page."""

        session = REQUEST.SESSION

        # a list of all buttons for REQUEST-handling
        # basketbuttons = [ DLG_FUNCTION + BTN_BASKET_REMOVE,
        #                  DLG_FUNCTION + BTN_BASKET_REMOVEALL,
        #                  DLG_FUNCTION + BTN_BASKET_ACTIVATE,
        #                  DLG_FUNCTION + BTN_BASKET_DEACTIVATE,
        #                  DLG_FUNCTION + BTN_BASKET_ADD ]

        # reset the basket if we have a different zopratype
        self.checkBasketSanity(mgr, session)

        # if no 'repeataction' was given in the REQUEST, we display the basket
        # on the main screen, and therefore need a dialog with appropriate
        # headers etc.
        # if it was given, we redirect to this action

        buttons = getPressedButton(REQUEST)
        if buttons:
            ownbutton = False

            # test for checked entries (get from request, turn into list)
            checked   = REQUEST.get('basket_checked')
            if not checked:
                checked = []
            else:
                if not isinstance(checked, ListType):
                    checked = [checked]

            if BTN_BASKET_REMOVE in buttons:
                ownbutton = BTN_BASKET_REMOVE

                for key in checked:
                    (mgr_id, table, entry_id) = self.retrieveEntry(key)

                    if mgr_id is None:
                        continue

                    self.removeEntryFromBasket(session, mgr_id, table, entry_id)

            elif BTN_BASKET_REMOVEALL in buttons:
                ownbutton = BTN_BASKET_REMOVEALL
                self.clearBasket(session)

            elif BTN_BASKET_ACTIVATE in buttons:
                ownbutton = BTN_BASKET_ACTIVATE

                for key in checked:
                    (mgr_id, table, entry_id) = self.retrieveEntry(key)

                    if mgr_id is None:
                        continue

                    self.activateEntryFromBasket(session, mgr_id, table, entry_id)

            elif BTN_BASKET_DEACTIVATE in buttons:
                ownbutton = BTN_BASKET_DEACTIVATE

                for key in checked:
                    (mgr_id, table, entry_id) = self.retrieveEntry(key)

                    if mgr_id is None:
                        continue

                    self.deactivateEntryFromBasket(session, mgr_id, table, entry_id)

            else:
                # a button was pressed
                raise ValueError('Forwarded to basket handling, but no basket button was pressed. Strange.')

            if ownbutton:
                # remove the button from request to avoid repeating it with repeataction
                del REQUEST.form[DLG_FUNCTION + ownbutton]
                # remove the checked - value as well to avoid repetition
                if checked:
                    del REQUEST.form['basket_checked']

                # remove basket_add button too (just to make sure we do not add via repeataction)
                if REQUEST.get(DLG_FUNCTION + BTN_BASKET_ADD):
                    del REQUEST.form[DLG_FUNCTION + BTN_BASKET_ADD]

                if REQUEST.get('repeataction'):
                    # we try to build the function-call having the url

                    url     = REQUEST.get('repeataction')
                    pos     = url.find('?')
                    arglist = []
                    if pos > -1:
                        _list = string.split(url[pos + 1:], '&')
                        url  = url[:pos]
                        for entry in _list:
                            pos2 = entry.find('=')
                            if pos2 > -1:
                                value = entry[pos2 + 1:]
                                try:
                                    int(value)
                                except ValueError:
                                    value = '"' + str(value) + '"'
                                arglist.append(entry[:pos2 + 1] + value)
                    args = string.join(arglist, ',')
                    if args:
                        args = ',' + args
                    execstr = 'page = mgr.%s(REQUEST=REQUEST%s)' % ( url,
                                                                     args )

                    # TODO get rid of exec, get func, apply it
                    execcontext = {'mgr': mgr,
                                   'REQUEST': REQUEST}

                    # safe exec in a context
                    exec execstr in execcontext

                    if execcontext['page']:

                        # we managed to call repeataction
                        return execcontext['page']

        dlg = self.getBasketContext(mgr, REQUEST)
        dlg.setHeader(dlg._stdHeader)
        dlg.setFooter(dlg._stdFooter)

        buttons = dlg.child('buttons')
        buttons[4, 0] = mgr.getBackButton()

        return HTML( dlg.getHtml() )(self, REQUEST)


    def getBasketContext(self, mgr, REQUEST):
        """\brief Returns the basket dialog for the context menu"""

        # the basket in the session is a dict containing
        # id:{'entry':{},'active':{}}
        session = REQUEST.SESSION

        # reset the basket if we have a different zopratype
        self.checkBasketSanity(mgr, session)

        # we have a normal form-display (in the
        # context-menu)

        flag = Dialog.Embedded
        link = '%s/getBasketForm' % mgr.absolute_url()
        dlg  = getStdZMOMDialog('Basket', link, flag)
        dlg.setSsiName( '.nav_title' )
        dlg.setSsiName( '.nav_form'  )

        # reformat entry structure table -> mgr -> entry
        names      = {}
        managers   = {}
        tip2tab    = {}
        name2count = {}

        # collect aux infos for each section (table)
        if session.get('basket'):
            basket = session.get('basket')

            mgr_ids   = basket.keys()
            mgr_ids.sort()

            for mgr_id in mgr_ids:
                mgr4entry = mgr.getManager(mgr_id)

                if not mgr4entry:
                    ztype = session.get('basketzopratype')
                    if ztype:
                        # search hierarchy down with zopratype
                        mgr4entry = mgr.getHierarchyDownManager(name = mgr_id, zopratype = ztype)

                if mgr4entry:
                    mgr_name   = mgr4entry.getTitle()
                else:
                    mgr_name   = mgr_id

                tables = basket[mgr_id].keys()
                tables.sort()

                for table in tables:
                    managers[ (mgr_id, table) ] = mgr4entry

                    if mgr4entry:
                        table_name = mgr4entry.tableHandler[table].getLabel()
                    else:
                        table_name = table

                    tip   = table_name + ' (' + mgr_name + ')'
                    label = table_name

                    tip2tab[tip]             = (mgr_id, table)
                    names[ (mgr_id, table) ] = label

                    if label in name2count:
                        name2count[label] += 1
                    else:
                        name2count[label]  = 1

        # building form
        tab         = hgTable(parent = dlg)
        has_content = False

        # display all sections with their entries
        if names:
            has_content = True
            row  = 0

            tips = tip2tab.keys()
            tips.sort()

            for tip in tips:
                (mgr_id, table) = tip2tab[tip]

                mgr4entry = managers[ (mgr_id, table) ]
                label     = names[ (mgr_id, table) ]

                if name2count[label] > 1:
                    label = tip

                # create groupbox
                gbox   = hgGroupBox(title = label, parent = tab)
                boxlay = hgGridLayout( gbox, 1, 1 )
                gbox._styleSheet.getSsiName( ssiBASKET_GBOX )
                boxlay.setSsiName( ssiBASKET_GBOX.name() )
                # since cannot color single cells in group layouts (?)
                gtab = hgTable(spacing = '0', parent = gbox)
                boxlay.addWidget(gtab, 0, 0)

                gbox.setToolTip(tip)

                tab[row, 0] = gbox
                row += 1

                entry_ids = basket[mgr_id][table].keys()

                # NOTE: we assume that the entry labels are unique
                elab2wdg = {}

                for entry_id in entry_ids:
                    entry = basket[mgr_id][table][entry_id]
                    if mgr4entry:
                        link = mgr4entry.getLink(table, None, entry['entry'], parent = gtab)
                    else:
                        link = hgLabel(entry_id, parent = gtab)

                    cb = hgCheckBox('', mgr_id + '.' + table + '.' + entry_id, gbox, 'basket_checked')

                    entry_label = link.getText()
                    cb.setToolTip('Select ' + entry_label)
                    link.setToolTip(entry_label)

                    elab2wdg[entry_label] = (link, cb, entry.get('active'))

                elabs = elab2wdg.keys()
                elabs.sort()

                grow = 0
                for elab in elabs:
                    (link, cb, active) = elab2wdg[elab]

                    gtab[grow, 0] = cb
                    gtab[grow, 1] = link
                    # boxlay.addWidget(cb,   grow, 0)
                    # boxlay.addWidget(link, grow, 1)

                    if active:
                        gtab.setCellBackgroundColor(grow, 0, '#D5D9EF')
                        gtab.setCellBackgroundColor(grow, 1, '#D5D9EF')

                    grow += 1

        if has_content:
            dlg.add(tab)

        # preserve the form values (button pressed -> main page stays the same)
        if REQUEST.get('repeataction'):
            for key in REQUEST.form.keys():
                value = REQUEST.form.get(key, '')
                if isinstance(value, ListType):
                    for entry in value:
                        dlg.add( hgProperty(key, entry, parent = dlg) )
                else:
                    dlg.add( hgProperty(key, value, parent = dlg) )

        # table for button layout
        tab2 = hgTable(name = 'buttons', spacing = 2, padding = 0)

        tab2[0, 0] = mpfBasketActivateButton
        tab2[1, 0] = mpfBasketDeactivateButton
        tab2[2, 0] = mpfBasketRemoveButton
        tab2[3, 0] = mpfBasketRemoveAllButton
        dlg.add(tab2)

        # return a dialog object
        return dlg


    def isNotEmpty(self, mgr, session):
        """\brief check function to determine whether basket is empty,
                also checks for correct zopratype and is
                used by ManagerPart to determine whether to show basket or not."""
        self.checkBasketSanity(mgr, session)

        if self.getAllEntriesListFromBasket(session):
            return True
        return False


    def checkBasketSanity(self, mgr, session):
        """\brief check for correct zopratype (reset basket if necessary)"""
        # reset the basket if we have a different zopratype
        ztype = mgr.getZopraType()
        if ztype and ztype != session.get('basketzopratype'):
            session['basketzopratype'] = ztype
            self.clearBasket(session)
        if not session.get('basket'):
            session['basket'] = {}


    def retrieveEntry(self, entry_string):
        """\brief Retrieve entry config from string."""

        path = entry_string.split('.')

        if len(path) != 3:
            return (None, None, None)

        mgr_id   = path[0]
        table    = path[1]
        entry_id = path[2]

        return (mgr_id, table, entry_id)


    def addEntryToBasket(self, session, mgr, table, entry_id, entry = None):
        """\brief adds an entry to the basket."""
        # check to have a correct basket
        self.checkBasketSanity(mgr, session)

        if entry_id:
            if not entry:
                entry = mgr.getEntry(table, entry_id)

            if not entry:
                return

            mgr_id = mgr.getClassName()

            if mgr_id not in session['basket']:
                session['basket'][mgr_id] = {}

            if table not in session['basket'][mgr_id]:
                session['basket'][mgr_id][table] = {}

            # id is already present
            if str(entry_id) in session['basket'][mgr_id][table]:
                return

            session['basket'][mgr_id][table][str(entry_id)] = { 'entry': entry,
                                                                'active': True }


    def removeEntryFromBasket(self, session, mgr, table, entry_id):
        """\brief deletes an entry from the basket."""
        if session.get('basket'):

            mgr_id   = mgr.getClassName()
            entry_id = str(entry_id)

            try:
                item = session['basket'][mgr_id][table][entry_id]
            except KeyError:
                return

            del session['basket'][mgr_id][table][entry_id]

            if len(session['basket'][mgr_id][table]) == 0:
                del session['basket'][mgr_id][table]

            if len(session['basket'][mgr_id]) == 0:
                del session['basket'][mgr_id]

            return item


    def getAllEntriesListFromBasket(self, session):
        """\brief returns a list of all entries from the basket."""
        tmp_list = []
        if session.get('basket'):
            basket = session.get('basket')

            mgr_ids   = basket.keys()
            mgr_ids.sort()

            for mgr_id in mgr_ids:
                tables = basket[mgr_id].keys()
                tables.sort()

                for table in tables:
                    entry_ids = basket[mgr_id][table]

                    for entry_id in entry_ids:
                        item = basket[mgr_id][table][entry_id]
                        tmp_list.append((mgr_id, table, item['entry']))
        return tmp_list


    def getActiveEntriesListFromBasket(self, session):
        """\brief returns a list of all active entries from the basket."""
        tmp_list = []
        if session.get('basket'):
            basket = session.get('basket')

            mgr_ids   = basket.keys()
            mgr_ids.sort()

            for mgr_id in mgr_ids:
                tables = basket[mgr_id].keys()
                tables.sort()

                for table in tables:
                    entry_ids = basket[mgr_id][table]

                    for entry_id in entry_ids:
                        item = basket[mgr_id][table][entry_id]
                        if item.get('active'):
                            tmp_list.append((mgr_id, table, item['entry']))
                            self.deactivateEntryFromBasket(session, mgr_id, table, entry_id)
        return tmp_list


    def popFirstActiveEntryFromBasket(self, session, mgr_id, table, delete = True):
        """\brief remove and return the first active entry."""
        ret = {}
        if session.get('basket'):
            basket = session.get('basket')

            if mgr_id not in basket:
                return None

            mgrbasket = basket[mgr_id]

            if table not in mgrbasket:
                return None

            entry_ids = mgrbasket[table]

            for entry_id in entry_ids:
                item = basket[mgr_id][table][entry_id]
                if item.get('active'):
                    ret = item.get('entry')
                    if delete:
                        self.removeEntryFromBasket(session, mgr_id, table, entry_id)
                    else:
                        self.deactivateEntryFromBasket(session, mgr_id, table, entry_id)
                    break
        return ret


    def activateEntryFromBasket(self, session, mgr, table, entry_id):
        """\brief set the entry with id to active."""
        if session.get('basket'):

            mgr_id   = mgr.getClassName()
            entry_id = str(entry_id)

            try:
                item = session['basket'][mgr_id][table][entry_id]
            except KeyError:
                return

            item['active'] = True


    def deactivateEntryFromBasket(self, session, mgr, table, entry_id):
        """\brief set the entry with id to active."""
        if session.get('basket'):

            mgr_id   = mgr.getClassName()
            entry_id = str(entry_id)

            try:
                item = session['basket'][mgr_id][table][entry_id]
            except KeyError:
                return

            item['active'] = False


    def clearBasket(self, session):
        """\brief Empty basket."""
        if session.get('basket'):
            session['basket'] = {}
