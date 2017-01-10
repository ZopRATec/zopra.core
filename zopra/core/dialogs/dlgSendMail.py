############################################################################
#    Copyright (C) 2005 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.kernel.hgGridLayout          import hgGridLayout
from PyHtmlGUI.widgets.hgLabel              import hgLabel
from PyHtmlGUI.widgets.hgLineEdit           import hgLineEdit
from PyHtmlGUI.widgets.hgTextEdit           import hgTextEdit


from zopra.core.dialogs.dlgOCBase           import dlgOCBase

from zopra.core.constants                   import TCN_AUTOID
from zopra.core.interfaces                  import IContactManager

from zopra.core.tools.managers              import TN_PERSON, \
                                                   TCN_EMAIL

from zopra.core.widgets.hgComplexMultiList  import hgComplexMultiList


class dlgSendMail(dlgOCBase):
    """\brief Event View Dialog"""
    _className = "dlgSendMail"
    _classType = dlgOCBase._classType + [_className]

    ##########################################################################
    #
    # Instance Methods
    #
    ##########################################################################
    def __init__( self, manager, param_dict ):
        """\brief Constructs a dlgMultiEdit Object."""
        # Careful with attributes, super.__init__ calls
        # buildLayout and buildFinalLayout

        # test manager
        
        if not IContactManager.providedBy(manager):
            raise ValueError('Wrong Manager')

        self.mail_to   = {}
        self.mail_from = ''
        self.add_to    = []
        self.subject   = ''
        self.text      = ''
        self.did_send  = []
        sendto         = param_dict.get('send_to')
        self.sender    = param_dict.get('sender')

        self.initPersons(manager, sendto)

        dlgOCBase.__init__(self, manager, param_dict)

        self.caption     = 'Send Mail'
        self.enable_undo = False
        self.message     = ''


    def initPersons(self, manager, autoids):
        """\brief Init entries and their widgets."""

        # Person Select List
        persons = manager.tableHandler[TN_PERSON].getEntries('_not_NULL', TCN_EMAIL)
        reslist = []

        # multilist
        mul = hgComplexMultiList('send_to')

        # get mailadresses, remove others from list
        for person in persons:
            self.mail_to[person[TCN_AUTOID]] = person[TCN_EMAIL]
            uname = manager.getUserName(None, person)
            mul.insertItem( uname, person[TCN_AUTOID] )

        # preselect via autoids
        if autoids:
            mul.setSelectedValueList(autoids)

        self.person_select = mul

        # sender
        if self.sender and self.mail_to.get(self.sender):
            self.mail_from = self.mail_to.get(self.sender)


    def buildLayout(self, manager, widget):
        """\brief Initialise the dialogs layout"""
        layout = hgGridLayout(widget, 2, 5, 0, 4)

        lab  = hgLabel('Send to', parent = widget)
        layout.addWidget( lab, 0, 0 )

        # person select complex multilist
        self.person_select.reparent(widget)
        layout.addWidget(self.person_select, 0, 1)

        # additional addresses
        lab  = hgLabel('Additional Addresses', parent = widget)
        widg = hgLineEdit( '', None, widget, 'send_to_additional' )
        layout.addWidget( lab,  1, 0 )
        layout.addWidget( widg, 1, 1 )
        widg.connect(widg.textChanged, self.setAdditionalTo)

        # from address
        lab  = hgLabel('Sender', parent = widget)
        widg = hgLineEdit( self.mail_from, None, widget, 'sender' )
        layout.addWidget( lab,  2, 0 )
        layout.addWidget( widg, 2, 1 )
        widg.connect(widg.textChanged, self.setSender)

        # subject textedit
        lab  = hgLabel('Subject', parent = widget)
        widg = hgLineEdit( '', None, widget, 'subject' )
        layout.addWidget( lab,  3, 0 )
        layout.addWidget( widg, 3, 1 )
        widg.connect(widg.textChanged, self.setSubject)

        # text multiline
        lab  = hgLabel('Message', parent = widget)
        widg = hgTextEdit( '', '', widget, 'text', hgTextEdit.MULTILINE )
        widg.setSize(80, 8)
        layout.addWidget( lab,  4, 0 )
        layout.addWidget( widg, 4, 1 )
        widg.connect(widg.textChanged, self.setText)


    def buildFinalLayout(self, manager, widget):
        """\brief Show report."""
        layout = hgGridLayout(widget, 2, 5, 0, 4)
        lab = hgLabel('Send to', parent = widget)
        layout.addWidget(lab, 0, 0)
        lab = hgLabel('Additionally', parent = widget)
        layout.addWidget(lab, 1, 0)
        lab = hgLabel('Send from', parent = widget)
        layout.addWidget(lab, 2, 0)
        lab = hgLabel('Subject', parent = widget)
        layout.addWidget(lab, 3, 0)
        lab = hgLabel('Message', parent = widget)
        layout.addWidget(lab, 4, 0)

    def updateFinalLayout(self, manager, widget):
        """\brief Show report."""
        layout = widget.layout()

        # show mailadresses
        lab = hgLabel(str(self.did_send), parent = widget)
        layout.addWidget(lab, 0, 1)
        # show additional adresses
        lab = hgLabel(str(self.add_to), parent = widget)
        layout.addWidget(lab, 1, 1)
        # show sender
        lab = hgLabel(self.mail_from, parent = widget)
        layout.addWidget(lab, 2, 1)
        # show subject
        lab = hgLabel(self.subject, parent = widget)
        layout.addWidget(lab, 3, 1)
        # show text
        lab = hgLabel(self.text.replace('\n', '<br>'), parent = widget)
        layout.addWidget(lab, 4, 1)


    def updateLayout(self, manager, widget):
        """\brief change layout."""
        #not necessary
        pass

#
# Slot functions
#

    def setAdditionalTo(self, text):
        """\brief Slot Function. Set additional recipient"""
        if text:
            breaker = ','
            if text.find(breaker) == -1:
                breaker = ';'
                if text.find(breaker) == -1:
                    breaker = ' '
            sto = text.split(breaker)
            for entry in sto:
                self.add_to.append(entry.strip())
        else:
            self.add_to = []


    def setSender(self, text):
        """\brief Slot Function. Set Subject"""
        self.mail_from = text


    def setSubject(self, text):
        """\brief Slot Function. Set Subject"""
        self.subject = text


    def setText(self, text):
        """\brief Slot Function. Set Mail Text"""
        self.text = text

#
# Dialog Execution
#

    def execHook(self, manager, REQUEST):
        """\brief overwrites execHook of parent class to get access to the manager."""
        pass


    def performDo(self, manager, REQUEST):
        """\brief Returns the html source for the pooling dialog."""
        # get selected persons
        to_list = self.person_select.getSelectedValues()
        success = True
        for entry in to_list:
            address = self.mail_to.get(entry)
            self.did_send.append(address)
            done = manager.sendSimpleMail( address,
                                           self.mail_from,
                                           self.subject,
                                           self.text )
            if not done:
                success = False
        for entry in self.add_to:
            done = manager.sendSimpleMail( entry,
                                           self.mail_from,
                                           self.subject,
                                           self.text )
            if not done:
                success = False
        return success
