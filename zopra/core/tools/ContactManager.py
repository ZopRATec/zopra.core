############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from types                                   import DictType,   \
                                                    StringType, \
                                                    ListType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI                               import E_PARAM_FAIL, \
                                                    checkType

from PyHtmlGUI.kernel.hgTable                import hgTable
from PyHtmlGUI.widgets.hgLabel               import hgLabel
from PyHtmlGUI.widgets.hgLineEdit            import hgLineEdit
from PyHtmlGUI.widgets.hgVBox                import hgVBox

#
# ZopRA Imports
#
from zopra.core                              import HTML, ZM_CM, ZM_SCM, ZM_MM
from zopra.core.constants                    import TCN_AUTOID
from zopra.core.dialogs                      import getStdZMOMDialog
from zopra.core.widgets                      import dlgLabel
from zopra.core.CorePart                     import MASK_ADD,    \
                                                    MASK_EDIT,   \
                                                    MASK_SHOW

from zopra.core.dialogs.Dialog               import Dialog

from zopra.core.tools.GenericManager         import GenericManager,  \
                                                    GEN_LABEL

from zopra.core.tools.managers               import TN_ORG,             \
                                                    TN_PERSON,          \
                                                    TN_USER,            \
                                                    TCN_ORG,            \
                                                    TCN_NAME,           \
                                                    TCN_USERID,         \
                                                    TCN_FIRSTNAME,      \
                                                    TCN_INITIALS,       \
                                                    TCN_LASTNAME,       \
                                                    TCN_ADDRESS,        \
                                                    TCN_PHONE,          \
                                                    TCN_EMAIL,          \
                                                    TCN_FAX,            \
                                                    TCN_TFP,            \
                                                    TCN_URI,            \
                                                    TCN_PARENT,         \
                                                    TCN_LOGIN,          \
                                                    TCN_GROUPS

from zopra.core.vCard                        import vcType, \
                                                    vCard


CM_ANONYMOUS = 'Anonymous'


class ContactManager(GenericManager):
    """ The ContactManager class provides a simple contact manager.

    \brief Base class for all user managment interfaces.
    """
    _className          = ZM_CM
    _classType          = GenericManager._classType + [_className]
    meta_type           = _className

    _properties     = GenericManager._properties
    _generic_config = GenericManager._generic_config
    _dlgs           = GenericManager._dlgs + ( ( 'dlgSendMail',
                                                 'AuditAndSecurity' ), )

    # generic config
    _generic_config = {}
    _generic_config[TN_ORG]    = { 'basket_active': False,
                                   'required' : [TCN_NAME],
                                   'show_fields' : ( TCN_NAME,
                                                     TCN_EMAIL, 
                                                     TCN_URI ) }
    _generic_config[TN_PERSON] = { 'basket_active': False,
                                   'required' : [TCN_FIRSTNAME, TCN_LASTNAME],
                                   'show_fields' : ( TCN_FIRSTNAME,
                                                     TCN_LASTNAME,
                                                     TCN_EMAIL,
                                                     TCN_PHONE ),
                                   'labelsearchfields': [TCN_LASTNAME, TCN_FIRSTNAME] }

    # adjust cache
    def manage_afterAdd(self, item, container):
        """\brief Call super function, then resize cache"""
        GenericManager.manage_afterAdd(self, item, container)
        self.tableHandler[TN_PERSON].cache.item_count = 500
        self.tableHandler[TN_ORG].cache.item_count = 300

    def getPerson(self, person_id, idfield = TCN_AUTOID):
        """\brief Returns a person entry with id \a person_id and
                  idfield \a idfield.

        \param id  The argument \a id is a value that contains a person id.

        \return Description dictionary, otherwise None.
        """
        assert person_id is not None, E_PARAM_FAIL % 'person_id'
        assert checkType( 'idfield', idfield, StringType )

        tobj = self.tableHandler[TN_PERSON]
        person = tobj.getEntryBy(person_id, idfield)
        return person


    def getOrganisation(self, org_id, idfield = TCN_AUTOID):
        """\brief Returns a organisation entry with id \a org_id and
                  idfield \a idfield.

        \param id  The argument \a id is a value that contains
                   an organisation id.

        \return Description dictionary
        """
        assert org_id is not None, E_PARAM_FAIL % 'org_id'
        assert checkType( 'idfield', idfield, StringType )
        tobj = self.tableHandler[TN_ORG]
        org  = tobj.getEntryBy(org_id, idfield)
        return org


    def addPerson(self, descr_dict):
        """\brief Adds a person to the database with the information
                  from \a descr_dict.
        """
        assert checkType( 'descr_dict', descr_dict, DictType )
        return self.tableHandler[TN_PERSON].addEntry( descr_dict )



#
# User functions
#

    def getCurrentUser(self):
        """\brief Returns a description dictionary for an user entry.

        \param login  The argument \a login is a string that contains the login
        names of the working user.

        \return description dictionary of the user entry, otherwise None
        """
        user_id = self.getCurrentUserId()
        if user_id:
            return self.tableHandler[TN_PERSON].getEntry( user_id )


    def getCurrentUserId(self):
        """\brief Returns the current user id."""
        m_security = self.getManager(ZM_SCM)
        if m_security:
            currentLogin = m_security.getCurrentLogin()
            return m_security.getUserByLogin( currentLogin ).get(TCN_USERID)
        return 0


    def getCurrentUserName(self):
        """ \brief Returns the name of the current user."""
        return self.getUserName( self.getCurrentUserId() )


    def getUserName(self, autoid = None, descr_dict = None):
        """\brief Returns the name of a user specified by \c id.

        \param autoid  The autoid of the user entry.
        \param descr_dict The user entry may be provided instead the autoid.
        \return if user exists function returns a formatted user name,
                otherwise an empty string
        """
        if descr_dict:
            user = descr_dict
        elif autoid:
            user = self.getPerson(autoid)
        else:
            return ''
        if user:
            name = user.get(TCN_LASTNAME, '')

            if user.get(TCN_FIRSTNAME):
                if name:
                    name += ' '
                name += user.get(TCN_FIRSTNAME)

            if user.get(TCN_INITIALS):
                if name:
                    name += ' '
                name += user.get(TCN_INITIALS)
            return name

        return ''


    def newPerson(self, REQUEST):
        """\brief Creates a person entry in the database
                 (on manager creation only).
        """

        # dummy-user erzeugen
        if not self.getPerson('Unknown', TCN_LASTNAME):
            entry_dict = { TCN_AUTOID: 0, TCN_LASTNAME: 'Unknown' }
            self.tableHandler[TN_PERSON].addEntry(entry_dict)

        entry_dict = {}
        entry_dict[TCN_FIRSTNAME]    = REQUEST.get('person_firstname')
        entry_dict[TCN_INITIALS]     = REQUEST.get('person_midinitials')
        entry_dict[TCN_LASTNAME]     = REQUEST.get('person_lastname')
        entry_dict[TCN_ADDRESS]      = REQUEST.get('person_address')
        entry_dict[TCN_PHONE]        = REQUEST.get('person_phone')
        entry_dict[TCN_EMAIL]        = REQUEST.get('person_email')
        entry_dict[TCN_FAX]          = REQUEST.get('person_fax')
        entry_dict[TCN_TFP]          = REQUEST.get('person_tollFreePhone')
        entry_dict[TCN_URI]          = REQUEST.get('person_uri')
        entry_dict[TCN_ORG] = REQUEST.get('person_affiliation')

        if entry_dict.get(TCN_LASTNAME):
            self.tableHandler[TN_PERSON].addEntry(entry_dict)


    def newOrganisation(self, REQUEST):
        """\brief Creates a organisation entry in the database."""
        entry_dict                = {}
        entry_dict[TCN_NAME]      = REQUEST.get('org_name')
        entry_dict[TCN_PARENT]    = REQUEST.get('org_head')
        entry_dict[TCN_ADDRESS]   = REQUEST.get('org_address')
        entry_dict[TCN_EMAIL]     = REQUEST.get('org_email')
        entry_dict[TCN_FIRSTNAME] = REQUEST.get('org_fax')
        entry_dict[TCN_TFP]       = REQUEST.get('org_tollFreePhone')
        entry_dict[TCN_URI]       = REQUEST.get('org_uri')
        entry_dict[TCN_PHONE]     = REQUEST.get('org_phone')

        if entry_dict.get(TCN_NAME):
            autoid = self.tableHandler[TN_ORG].addEntry(entry_dict)
            return autoid


    def getContextTable(self):
        """\brief Returns the context menu of this object."""
        dlg = getStdZMOMDialog('Contact Managing', None, Dialog.Embedded)
        box  = hgVBox()
        box.add( hgLabel( 'Add Person',
                          self.absolute_url() + '/newFormPerson' )
                )
        box.add( hgLabel( 'Add Organisation',
                          self.absolute_url() + '/newFormOrganisation' )
                )
        dlg.add( box )
        return dlg


#
# public managing
#
    def _index_html(self, REQUEST, parent):
        """\brief Overwritten entry point"""
        t = hgTable()
        perm = self.getGUIPermission()
        guigranted = perm.hasMinimumRole(perm.SC_VISITOR)

        # zopratype only transported via session
        # because a LotusSuperuser should be able to add Persons (and self.zopratype is None)
        if REQUEST and REQUEST.SESSION and REQUEST.SESSION.get('zopratype'):
            zopratype = REQUEST.SESSION.get('zopratype')
        else:
            zopratype = ''

        super = perm.hasMinimumRole(perm.SC_SUPER)
        super = super or perm.hasSpecialRole(zopratype + 'Superuser')

        if guigranted:
            t[0, 0] = hgLabel('<b>Person Information</b>')

            url = self.absolute_url()

            if super:
                t[2, 0] = hgLabel( 'New Person',
                                   '%s/newForm?table=%s' % (url, TN_PERSON) )

            t[3, 0] = hgLabel( 'Person Search',
                               '%s/searchForm?table=%s' % (url, TN_PERSON) )
            t[4, 0] = hgLabel( 'Person List',
                               '%s/showList?table=%s' % (url, TN_PERSON) )

            t[7, 0] = hgLabel('<b>Organisation Information</b>')

            if super:
                t[9, 0] = hgLabel( 'New Organisation / Department',
                                   '%s/newForm?table=%s' % (url, TN_ORG) )

            t[10, 0] = hgLabel( 'Organisation / Department Search',
                                '%s/searchForm?table=%s' % (url, TN_ORG) )
            t[11, 0] = hgLabel( 'Organisation / Department List',
                                '%s/showList?table=%s' % (url, TN_ORG) )

        return t


#
# generic functions overwritten
#

    def getLabelString(self, table, autoid = None, descr_dict = None):
        """\brief Return label for entry, overwrite for special functionality."""
        #return autoid, no matter what table
        if autoid:
            descr_dict = self.getEntry(table, autoid)
        elif not descr_dict:
            return ''
        if table == TN_PERSON:
            return self.getUserName(None, descr_dict)
        elif table == TN_ORG:
            return descr_dict.get(TCN_NAME)


    def prepareDict(self, table, descr_dict, REQUEST):
        """\brief Dummy Function called before edit and add"""
        if table == TN_PERSON:
            if REQUEST.get(TCN_LOGIN):
                descr_dict[TCN_LOGIN]  = REQUEST.get(TCN_LOGIN)
            if REQUEST.get(TCN_GROUPS):
                groups = REQUEST.get(TCN_GROUPS)
                if not isinstance(groups, ListType):
                    groups = [groups]
                descr_dict[TCN_GROUPS] = groups


    def actionAfterAdd(self, table, descr_dict, REQUEST):
        """\brief hook used to do security manager insert (if password provided)
        """
        if table == TN_PERSON:
            m_security = self.getHierarchyUpManager(ZM_SCM)

            if m_security:

                if REQUEST.get(TCN_LOGIN):
                    # we insert the user in the security manager (button is
                    # still ADD, so this works)
                    REQUEST.form[TCN_USERID] = descr_dict[TCN_AUTOID]
                    m_security.newForm(TN_USER, REQUEST)

    def actionBeforeEdit(self, table, descr_dict, REQUEST):
        """\brief hook used to do security manager update (if password provided)
        """
        if table == TN_PERSON:
            if REQUEST.get('password'):
                ddict = {}
                ddict['password'] = REQUEST.get('password')
                ddict['check']    = REQUEST.get('check'   )
                ddict[TCN_USERID] = descr_dict.get(TCN_AUTOID)
                m_security = self.getHierarchyUpManager(ZM_SCM)
                if m_security:
                    done = m_security.updatePassword(ddict)
                    if done:
                        return 'Password has been updated.'
                    else:
                        return 'Password has not been updated.'


    def actionBeforeShowList(self, table, param, REQUEST):
        """\brief Return the html source of the show organisation list form."""
        m_security = self.getHierarchyUpManager(ZM_SCM)
        if table == TN_PERSON:

            # vCard Export
            link = '%s/getPersonVCardText?person_id=' % self.absolute_url()
            param['links'] = {'vCard 3.0': { 'link': link}}

            # own Buttons in List View
            if REQUEST and REQUEST.SESSION.get('zopratype') and m_security:
                ztype = REQUEST.SESSION.get('zopratype')
                suser = m_security.hasRole( ztype + 'Superuser' )
            else:
                suser = False
            if not m_security or m_security.getCurrentLevel() > 8 or suser:
                # only superusers send mail
                # test for mailhost
                if self.getObjByMetaType('Mail Host'):
                    param['ownButtonActions'] = {'Send Mail': self.sendPersonMail}

        # we want autoidlists for navigation
        param['with_autoid_navig'] = True


    def sendPersonMail(self, autoid, REQUEST):
        """\brief Opens Send Mail Dialog for selected persons (autoid-list)"""
        # we need a dlgSendMail to collect subject and body and send mails.
        # sendSimpleMail(self, mto, mfrom, subject, body)
        attrs = {}
        attrs['send_to'] = autoid
        attrs['sender']  = self.getCurrentUserId()
        # init dialog
        dlg_id = self.dlgHandler.dlgSendMail.getId()
        dlg = self.dlgHandler.getDialog(dlg_id, REQUEST.SESSION, None, attrs)
        dlg.setAction( '%s/dlgHandler/show' % self.absolute_url() )

        # sets the active window
        app = self.dlgHandler.getApplication( REQUEST.SESSION )
        app.active_window = dlg

        # put it back online
        return HTML( dlg.getHtml() )(self, None)


    def getSingleMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None):
        """\brief Returns the mask."""
        if table == TN_PERSON:
            return self.getMaskPerson(flag, descr_dict)

        elif table == TN_ORG:
            return self.getMaskOrganisation(flag, descr_dict)

        else:
            raise ValueError('Internal Contact Error')


    def getMaskPerson(self, flag = MASK_SHOW, descr_dict = None):
        """\brief Returns the mask for the person table"""
        if descr_dict is None:
            person = {}
        else:
            person = descr_dict

        m_security = self.getHierarchyUpManager(ZM_SCM)

        G = GEN_LABEL
        tem = [[G + TCN_FIRSTNAME, TCN_FIRSTNAME],
               [G + TCN_INITIALS,  TCN_INITIALS],
               [G + TCN_LASTNAME,  TCN_LASTNAME],
               [G + TCN_ORG,       TCN_ORG],
               [G + TCN_ADDRESS,   TCN_ADDRESS],
               [G + TCN_PHONE,     TCN_PHONE],
               [G + TCN_EMAIL,     TCN_EMAIL],
               [G + TCN_FAX,       TCN_FAX],
               [G + TCN_URI,       TCN_URI]]

        # link to message center
        if flag & MASK_SHOW:
            m_msgm = self.getHierarchyUpManager(ZM_MM)
        else:
            m_msgm = None

        if m_msgm:
            suser = m_security.getUserByCMId(person[TCN_AUTOID])
            if suser:
                tem.insert(7, [None,  None])

        mask = self.buildSemiGenericMask( TN_PERSON,
                                          tem,
                                          flag,
                                          person )
        layout = mask.layout()

        if m_security        and \
           m_security.getCurrentLevel() > 8:
            stobj = m_security.tableHandler[TN_USER]
            if flag & MASK_ADD:
                # login
                lab  = stobj.getLabelWidget( TCN_LOGIN, parent = mask)
                layout.addWidget(lab, 10, 0)
                widg = m_security.getFunctionWidget( TN_USER,
                                                     TCN_LOGIN,
                                                     mask,
                                                     flag,
                                                     person )
                layout.addWidget(widg, 10, 1)

                # groups
                lab  = stobj.getLabelWidget(TCN_GROUPS, parent = mask)
                layout.addWidget(lab, 11, 0)
                lobj = m_security.listHandler.getList(TN_USER, TCN_GROUPS)
                widg = lobj.getWidget( parent = mask,
                                       selected = person.get(TCN_GROUPS))
                layout.addWidget(widg, 11, 1)

            elif flag & MASK_SHOW:
                # login
                lab = stobj.getLabelWidget(TCN_LOGIN, parent = mask)
                layout.addWidget(lab, 10, 0)

                usr   = m_security.getUserByCMId(person[TCN_AUTOID])
                login = usr.get(TCN_LOGIN)
                usrid = usr.get(TCN_AUTOID)
                if login:
                    link = '%s/editForm?table=%s&id=%s'
                    link = link % ( m_security.absolute_url(),
                                    TN_USER,
                                    usrid )
                    widg = hgLabel(login, link, parent = mask)
                else:
                    link = '%s/newForm?table=%s&userid=%s'
                    link = link % ( m_security.absolute_url(),
                                    TN_USER,
                                    descr_dict[TCN_AUTOID] )
                    widg = hgLabel('Create login', link, parent = mask)
                layout.addWidget(widg, 10, 1)

        # show password input
        showpwd = False
        # for edit for superuser if person has login or if person is editing himself
        if (flag & MASK_EDIT) and m_security                        and \
                (m_security.getCurrentLevel() > 8                   and
                 m_security.getUserByCMId(person.get(TCN_AUTOID))   or
                 str(m_security.getCurrentCMId()) == str(person.get(TCN_AUTOID))):
            showpwd = True
        # for add for superuser
        if (flag & MASK_ADD) and m_security and m_security.getCurrentLevel() > 8:
            showpwd = True

        if showpwd:
            lab  = dlgLabel('Password', parent = mask)
            layout.addWidget(lab, 12, 0)
            widg = hgLineEdit( name   = 'password',
                               parent = mask )
            widg.setEchoMode(widg.Password)
            layout.addWidget(widg, 12, 1)
            lab  = dlgLabel('Reenter Password', parent = mask)
            layout.addWidget(lab, 13, 0)
            widg = hgLineEdit( name   = 'check',
                               parent = mask )
            widg.setEchoMode(widg.Password)
            layout.addWidget(widg, 13, 1)

        # show specials
        if flag & MASK_SHOW:

            # url (get widget, set target)
            if person.get(TCN_URI):
                widg = mask.child(TCN_URI)
                if widg:
                    widg.setUri(person.get(TCN_URI))

            # mail address (get widget, set target)
            if person.get(TCN_EMAIL):
                widg = mask.child(TCN_EMAIL)
                if widg:
                    widg.setUri('mailto:%s' % person.get(TCN_EMAIL))

            # vcard export
            lab  = dlgLabel('Export as', parent = mask)
            if m_msgm:
                # send message link
                if suser:
                    row = 12
                    layout.addWidget(dlgLabel('Message Center', parent = mask), 7, 0)
                    suid  = suser[TCN_AUTOID]
                    msg_link = m_msgm.getSendLink(suid, parent = mask)
                    layout.addWidget(msg_link, 7, 1)
                else:
                    row = 11
            else:
                row = 11
            layout.addWidget(lab, row, 0)
            label = 'vCard 3.0'
            link  = 'getPersonVCardText?person_id=%s'
            link  = link % ( person[TCN_AUTOID] )
            widg  = hgLabel(label, link, parent = mask)
            layout.addWidget(widg, row, 1)

        return mask


#
# organisation
#


    def getMaskOrganisation(self, flag = MASK_SHOW, descr_dict = None):
        """\brief Returns the mask for organisation """
        if descr_dict is None:
            descr_dict = {}
        template = [
        [None,                    None        ],
        [GEN_LABEL + TCN_NAME,    TCN_NAME    ],
        [GEN_LABEL + TCN_PARENT,  TCN_PARENT  ],
        [GEN_LABEL + TCN_ADDRESS, TCN_ADDRESS ],
        [GEN_LABEL + TCN_PHONE,   TCN_PHONE   ],
        [GEN_LABEL + TCN_TFP,     TCN_TFP     ],
        [GEN_LABEL + TCN_EMAIL,   TCN_EMAIL   ],
        [GEN_LABEL + TCN_FAX,     TCN_FAX     ],
        [GEN_LABEL + TCN_URI,     TCN_URI     ] ]

        mask = self.buildSemiGenericMask( TN_ORG,
                                          template,
                                          flag,
                                          descr_dict,
                                          None )
        layout = mask.layout()
        if descr_dict.get(TCN_AUTOID) and not (flag & MASK_SHOW):
            url    = self.absolute_url()
            autoid = descr_dict.get(TCN_AUTOID)
            label  = 'Show Organisation'
            link   = '%s/showForm?table=%s&id=%s'
            link   = link % (url, TN_ORG, autoid)
            lab = hgLabel(label, link, parent = mask)
            layout.addWidget(lab, 0, 1)

        # show people
        if flag & MASK_SHOW:
            person_list = self.tableHandler[TN_PERSON].getEntries( descr_dict[TCN_AUTOID],
                                                                   TCN_ORG )
            if person_list:
                box = hgVBox(parent = mask)
                box.add(dlgLabel('People'))
                box.add(hgLabel(''))
                # get people
                for person in person_list:
                    lab   = self.getLink(TN_PERSON, None, person, box)
                    box.add(lab)
                layout.addMultiCellWidget(box, 1, 8, 2, 2)

        return mask

#
# Special Exports
#
    ##########################################################################
    #
    # vCard 3.0 Support
    #
    ##########################################################################
    def getPersonVCardText(self, person_id):
        """\brief Returns a vCard for the person, otherwise None.
        """
        descr_dict = self.getPerson(person_id)
        if descr_dict:
            vcard = vCard()

            name = '%s;%s;;;' % ( descr_dict.get(TCN_LASTNAME, ''),
                                  descr_dict.get(TCN_FIRSTNAME, '') )

            fullname = '%s %s %s' % ( descr_dict.get(TCN_FIRSTNAME, ''),
                                      descr_dict.get(TCN_INITIALS, ''),
                                      descr_dict.get(TCN_LASTNAME, '') )

            address = descr_dict.get(TCN_ADDRESS, '')
            if address:
                address = ',%s,,,,,' % address

            vcard.setType( vcType.N,  name       )
            vcard.setType( vcType.FN, fullname   )
            vcard.setType( vcType.EMAIL,
                           descr_dict.get(TCN_EMAIL, ''),
                           ';TYPE=internet'
                            )
            vcard.setType( vcType.TEL,
                           descr_dict.get(TCN_PHONE, ''),
                           ';TYPE=work'
                            )

            vcard.setType( vcType.TEL,
                           descr_dict.get(TCN_FAX, ''),
                           ';TYPE=work,fax'
                            )

            vcard.setType( vcType.URL,
                           descr_dict.get(TCN_URI, ''),
                           ';TYPE=internet' )

            vcard.setType( vcType.ADR,
                           address,
                           ';TYPE=work,postal' )

            vcard.setType( vcType.ORG,
                           self.listHandler.getList(TN_PERSON, TCN_ORG).getValueByAutoid( descr_dict.get(TCN_ORG, '') ) )

            return str(vcard)

    def startupConfig(self, REQUEST):
        """\brief Create Initial User and Organisation"""
        autoid = self.newOrganisation(REQUEST)
        if autoid:
            REQUEST.form['person_affiliation'] = autoid
        self.newPerson(REQUEST)
