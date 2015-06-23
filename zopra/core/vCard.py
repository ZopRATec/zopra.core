############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

#   Predefined MIME Directory types used: SOURCE, NAME, PROFILE, BEGIN,
#   END.
#
#   Predefined MIME Directory parameters used: ENCODING, VALUE, CHARSET,
#   LANGUAGE, CONTEXT.
#
#   New types: FN, N, NICKNAME, PHOTO, BDAY, ADR, LABEL, TEL, EMAIL,
#   MAILER, TZ, GEO, TITLE, ROLE, LOGO, AGENT, ORG, CATEGORIES, NOTE,
#   PRODID, REV, SORT-STRING, SOUND, URL, UID, VERSION, CLASS, KEY
#
#   New parameters: TYPE

import string


class vCardTypes:
    FN          = 'FN'
    N           = 'N'
    NICKNAME    = 'NICKNAME'
    PHOTO       = 'PHOTO'
    BDAY        = 'BDAY'
    ADR         = 'ADR'
    LABEL       = 'LABEL'
    TEL         = 'TEL'
    EMAIL       = 'EMAIL'
    MAILER      = 'MAILER'
    TZ          = 'TZ'
    GEO         = 'GEO'
    TITLE       = 'TITLE'
    ROLE        = 'ROLE'
    LOGO        = 'LOGO'
    AGENT       = 'AGENT'
    ORG         = 'ORG'
    CATEGORIES  = 'CATEGORIES'
    NOTE        = 'NOTE'
    PRODID      = 'PROID'
    REV         = 'REV'
    SORT_STRING = 'SORT_STRING'
    SOUND       = 'SOUND'
    URL         = 'URL'
    UID         = 'UID'
    VERSION     = 'VERSION'
    CLASS       = 'CLASS'
    KEY         = 'KEY'

vcType      = vCardTypes()
vcListTypes = []


class vCard:
    """\brief Implements the RFC 2426 (http://www.ietf.org/rfc/rfc2426.txt)
              in a single object.
    """


    def __init__(self):
        """\brief Constructs a vCard object."""
        self._values = { vcType.VERSION: '3.0',
                         vcType.FN:      '',
                         vcType.N:       ''     }
        self._params = { }


    def __str__(self):
        """\brief Implements the string representation of vCard object."""
        string_list = []
        string_list.append('BEGIN:VCARD')

        # generate content lines
        for name in self._values.keys():

            if name not in vcListTypes:
                value = self._values[name]
                param = self._params.get(name, '')
                string_list.append('%s%s:%s' % (name, param, value))

            else:
                for entry in self._values[name]:
                    value, param = entry
                    string_list.append('%s%s:%s' % (name, param, value))

        string_list.append('END:VCARD')
        return string.join(string_list, '\n')


    def setType(self, name, value, param = ''):
        """\brief Sets the type of the vCard to \a value with parameters
                  \a param.
        """
        if value:
            if name not in vcListTypes:
                self._values[name] = value
                if param:
                    self._params[name] = param

            else:
                if not self._values.get(name):
                    self._values[name] = []
                self._values[name] = (value, param)
