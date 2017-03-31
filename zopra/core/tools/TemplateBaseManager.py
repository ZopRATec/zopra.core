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
from binascii   import hexlify
from copy       import deepcopy
from random     import randint
import re
from sets       import Set as set
from types      import ListType, StringType
import json
#
# ZopRA Imports
#
from zopra.core                         import ClassSecurityInfo, \
                                               getSecurityManager, \
                                               ZC
from zopra.core.CorePart                import MASK_SHOW
from zopra.core.tools.GenericManager    import GenericManager

protection_expression = re.compile(r'(mailto\:)?[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})')


class TemplateBaseManager(GenericManager):
    """ StudienInfo Manager """
    _className    = 'TemplateBaseManager'
    _classType    = GenericManager._classType + [_className]
    meta_type     = _className

#
# Security
#
    security = ClassSecurityInfo()
    security.declareObjectPublic()



    # languages v1
    _properties = GenericManager._properties + (
            {'id': 'lang_default',    'type': 'string',     'mode': 'w'},
            {'id': 'lang_additional', 'type': 'lines',     'mode': 'w'},)

    lang_default = 'de'
    lang_additional =()


    def startupConfig(self, REQUEST):
        """\brief Function called after creation by manageAddGeneric"""
        # add table constraints
        pass


    def index_html(self, REQUEST):
        """\brief forward one level up"""
        parent = self.aq_parent
        REQUEST.RESPONSE.redirect(parent.absolute_url())


    def consistencyCheckTranslations(self, do = None):
        """Consistency Checker for translations"""
        special_fields = ['autoid', 'hastranslation', 'istranslationof', 'iscopyof', 'language']
        import logging
        logger = logging.getLogger('ZopRA')
        for tablename in self.tableHandler.keys():
            if self.doesTranslations(tablename):
                count = 0
                logger.info('Checking {}'.format(tablename))
                tobj = self.tableHandler[tablename]
                coldefs = tobj.getColumnDefs()
                translations = tobj.getEntryList(constraints = {'istranslationof': '_not_NULL', 'iscopyof': 'NULL'})
                for translation in translations:
                    entry_diff = {}
                    log_diff = {}
                    orig = tobj.getEntry(translation['istranslationof'])
                    for key in coldefs:
                        thetype = coldefs.get(key)['TYPE']
                        if thetype not in ['string', 'memo'] and key not in special_fields:
                            val_orig = orig[key]
                            val_tran = translation[key]
                            if thetype in ['multilist', 'hierarchylist']:
                                val_orig = sorted(val_orig)
                                val_tran = sorted(val_tran)
                            if val_orig != val_tran:
                                entry_diff[key] = orig[key]
                                log_diff[key] = orig[key]
                                log_diff['{}_trans'.format(key)] = translation[key]
                                log_diff['{}_type'.format(key)] = thetype
                    if entry_diff:
                        entry_diff['autoid'] = orig['autoid']
                        log_diff['autoid'] = orig['autoid']
                        log_diff['trans_autoid'] = translation['autoid']
                        if do:
                            self.updateTranslation(tablename, entry_diff)
                        logger.info('diff found: {}'.format(str(log_diff)))
                        count += 1
                if count:
                    logger.info('Corrected {} entries with differences for table {}'.format(count, tablename))
        logger.info('Done')


    def doesWorkflows(self, table):
        """\brief """
        return False


    def getStateTransferInfo(self, table, entry):
        """\brief Overwrite for determining label and action for stateswitch button."""
        return {}


    def getListOwnUsers(self, table):
        """\brief returns constraints if the user should only see own entries"""
        user = getSecurityManager().getUser()
        return {'user_login': user.getUserName()}


    def getPermissionInfo(self, table, permission):
        """\brief Overwrite for special permission settings. Returns list of allowed roles."""
        # Standarddefinition
        # permissions: list_edit, table_create, table_show, table_edit, table_list, table_delete, table_show_own, table_list_own, table_edit_own, table_delete_own
        # "own" permissions are checked via userlogin field
        # -> extra field for transition phase, later integrated into edit_tracking_fields

        # ZopRAAuthor can list_edit, table_show / table_edit / table_list
        # ZopRAReviewer can publish if publishing is active
        stddef = {'list_edit': ['ZopRAAdmin', 'ZopRAAuthor', 'ZopRAReviewer'],
                  'table_create': ['ZopRAAdmin', 'ZopRAAuthor', 'ZopRAReviewer'],
                  'table_show': ['ZopRAAdmin', 'ZopRAAuthor', 'ZopRAReviewer'],
                  'table_edit': ['ZopRAAdmin', 'ZopRAAuthor', 'ZopRAReviewer'],
                  'table_list': ['ZopRAAdmin', 'ZopRAAuthor', 'ZopRAReviewer'],
                  'table_delete': ['ZopRAAdmin', 'ZopRAReviewer'],
                  'table_publish': ['ZopRAAdmin', 'ZopRAReviewer']}
        # check for these roles
        roles = stddef.get(permission, [])
        if not roles:
            return False
        user = getSecurityManager().getUser()
        return user.has_role(roles, self)


    def getPermissionEntryInfo(self, table, entry):
        """\brief Return permissions that current user with his roles has for an entry in a certain state"""
        # we add additional security handling for template based managers
        # this isn't the final solution, this should be integrated with entry-permissions and gui-permissions
        # which were used before, unfortunately the handling was centered around the security-manager
        # this handling works with zope roles only, but covers workflows and working copies

        # no workflows
            # working copies -> author can do show / edit, Reviewer can delete
            # no working copies -> author can do anything (show / edit / delete)
        user = getSecurityManager().getUser()
        perms = []

        if not self.doesWorkingCopies(table):
            # check Author
            if user.has_role(['ZopRAAuthor', 'ZopRAAdmin'], self):
                perms = ['show', 'edit', 'delete']
        else:
            # check Author
            if user.has_role('ZopRAAuthor', self):
                perms = ['show', 'edit']
            # check Reviewer (for del)
            if user.has_role(['ZopRAReviewer', 'ZopRAAdmin'], self):
                perms = ['show', 'edit', 'delete']

        return perms


    def doesWorkingCopies(self, table):
        """\brief """
        return False


    def getWorkingCopies(self, table):
        """\brief """
        tobj = self.tableHandler[table]
        cons = {'iscopyof': '_not_NULL'}
        return tobj.getEntryList(constraints = cons, ignore_permissions = True)


    def getWorkingCopy(self, table, autoid):
        """\brief Return the working copy or None"""
        if self.doesWorkingCopies(table):
            copy = self.tableHandler[table].getEntryList(constraints = {'iscopyof' : autoid}, ignore_permissions = True)
            if copy:
                return copy[0]
        return None


    def createWorkingCopy(self, table, entry):
        # used to create a working copy of an entry
        tobj = self.tableHandler[table]

        # check if a WoCo exists, return it instead of creating
        check = tobj.getEntries(entry['autoid'], 'iscopyof')
        if check:
            return check[0]

        # copy the objects
        copy = deepcopy(entry)
        # set copy data
        copy['iscopyof'] = copy['autoid']
        copy['autoid'] = None
        # add to database
        autoid = tobj.addEntry(copy)
        # fill new autoid
        copy['autoid'] = int(autoid)
        # return copy for further usage
        return copy


    def updateWorkingCopy(self, table, entry_diff):
        # this is useful when the edit-functionality of another table makes changes to entries of a table using working copies
        # and when a working copy is confirmed and there is a translation of the entry that also has a working copy
        autoid = entry_diff.get('autoid')
        cons = {'iscopyof': autoid}
        tobj = self.tableHandler[table]
        types = tobj.getColumnTypes()
        res = tobj.getEntryList(constraints = cons, ignore_permissions = True)
        if res:
            wc = res[0]
            for key in entry_diff.keys():
                if key not in ['autoid', 'iscopyof']:
                    wc[key] = entry_diff[key]
            # update the working copy entry
            tobj.updateEntry(wc, wc['autoid'])
            return True


    # the working copy machinery needs the deepcopy python func in scripts
    def deepcopy(self, obj):
        return deepcopy(obj)

    def doesTranslations(self, table):
        """\brief """
        return False


    def updateTranslation(self, table, entry_diff):
        # this is useful when the edit-functionality of another table makes changes to entries of a table using translations
        autoid = entry_diff.get('autoid')
        cons = {'istranslationof': autoid}
        tobj = self.tableHandler[table]
        types = tobj.getColumnTypes()
        res = tobj.getEntryList(constraints = cons, ignore_permissions = True)
        if res:
            eng = res[0]
            # need a dict for the changed stuff to not accidentally overwrite the working copy values on updateWorkingCopy
            eng_diff = {}
            for key in entry_diff.keys():
                if types.get(key) not in ['string', 'memo'] and key not in ['autoid', 'hastranslation', 'istranslationof', 'iscopyof', 'language']:
                    eng[key] = entry_diff[key]
                    eng_diff[key] = entry_diff[key]
            # update the english entry
            tobj.updateEntry(eng, eng['autoid'])
            eng_diff['autoid'] = eng['autoid']

            self.updateWorkingCopy(table, eng_diff)
            return True


    def getTranslation(self, table, autoid, lang):
        # retrieve translation of the entry with the autoid, if available
        # check if trenslations are activated
        if not self.doesTranslations(table):
            return autoid
        # check if lang is valid and not default
        if lang == self.lang_default or lang not in self.lang_additional:
            return autoid
        # build constraints
        cons = {'istranslationof': autoid, 'language': lang}
        # make sure we get the original entry
        if self.doesWorkingCopies(table):
            cons['iscopyof'] = 'NULL'
        tobj = self.tableHandler[table]
        res = tobj.getEntryAutoidList(constraints = cons)
        if res:
            return res[0]
        else:
            # fallback to original entry
            return autoid


    def removeTranslationInfo(self, table, autoid):
        """\brief after deleting a translation entry, the orginal entry needs to be corrected (removing the hastranslation marker)"""
        # the entry with autoid is a default language entry, whose translation was deleted
        tobj = self.tableHandler[table]
        entry = tobj.getEntry(autoid, ignore_permissions = True)
        # check for remaining translations
        translations = tobj.getEntryAutoidList(constraints = {'istranslationof': autoid})
        if not translations:
            # remove the hastranslation marker
            entry['hastranslation'] = 0
            tobj.updateEntry(entry, autoid)
            # check for working copies
            workingcopy = self.getWorkingCopy(table, autoid)
            if workingcopy:
                # use the original autoid and the change as entry_diff
                self.updateWorkingCopy(table, {'autoid': autoid, 'hastranslation': 0})


    def correctTranslationInfo(self):
        """\brief update step for correcting translation info"""
        # deleting language copies did not reset the hastranslation marker before, so we have to correct entries on db level
        # attention: working copies are problematic and are left out. Better make sure there are non when using this function.
        from zopra.core import ZC
        done = []
        pm = self.getManager(ZC.ZM_PM)
        for table in self.tableHandler.getTableIDs():
            if self.doesTranslations(table):
                sql1 = 'SELECT istranslationof from {}{} where istranslationof != 0'.format(self.getId(), table)
                res = pm.executeDBQuery(sql1)
                origids = [row[0] for row in res]
                if not origids:
                    continue
                idstring = ', '.join([str(orid) for orid in origids])
                # exclude working copies:
                wc = self.doesWorkingCopies(table)
                sql2 = 'SELECT COUNT(*) FROM {}{} WHERE hastranslation > 0 AND autoid NOT IN ({})'.format(self.getId(), table, idstring)
                if wc:
                    sql2 = sql2 + ' AND iscopyof IS NULL'
                res = pm.executeDBQuery(sql2)
                done.append('Removed {} hastranslation markers for {}.'.format(res[0][0], table))
                sql3 = 'UPDATE {}{} SET hastranslation = 0 WHERE hastranslation > 0 AND autoid NOT IN ({})'.format(self.getId(), table, idstring)
                if wc:
                    sql3 = sql3 + ' AND iscopyof IS NULL'
                pm.executeDBQuery(sql3)
        return '\n'.join(done)

#
# Table and Entry centered Functions
#

    def getFilteredColumnDefs(self, table, vis_only = False, edit_tracking = False):
        """\brief Indirection to retrieve column defs, allows addition and removal before listing"""
        tobj = self.tableHandler[table]
        res = tobj.getColumnDefs(vis_only = vis_only, edit_tracking = edit_tracking)
        if 'owner' in res:
            del res['owner']
        if 'creator' in res:
            del res['creator']
        if 'editor' in res:
            del res['editor']
        return res


    def checkDefaultWildcardSearch(self, table):
        """\brief Toggle for Wildcard Search. Overwrite this function and return True
                for the tables that will then automatically use wildcard search for all text
                fields.
        """
        return True


    def generateTableSearchTreeTemplate(self, table):
        """\brief Overwritten to generate a template"""
        return GenericManager.generateTableSearchTreeTemplate(self, table)


    def getEntryListCountProxy(self, table, constraints = None):
        """\brief Proxy for Table.getEntryListCount using searchTreeTemplate"""
        tobj = self.tableHandler[table]
        root = tobj.getSearchTreeTemplate()
        if constraints:
            root.setConstraints(constraints)
        return tobj.requestEntryCount(root)

    def calculatePaginationPages(self, rowcount, count):
        return (rowcount + count - 1) / count

    def getEntryListProxy(self, table,
                      show_number    = None,
                      start_number   = None,
                      idfield        = 'autoid',
                      constraints    = None,
                      order          = None,
                      direction      = None,
                      constr_or       = False
                      ):
        """\brief Proxy for Table.getEntryList using searchTreeTemplate"""
        tobj = self.tableHandler[table]
        root = tobj.getSearchTreeTemplate()
        if order:
            root.setOrder(order, direction)
        else:
            root.setOrder(idfield, direction)
        if constraints:
            root.setConstraints(constraints)
        if constr_or:
            fi = root.getFilter()
            fi.setOperator(fi.OR)
        return tobj.requestEntries(root, show_number, start_number, ignore_permissions = True)

    def handleHierarchyListOnSearch(self, table, cons):
        """\brief Add to given branch item all his possible children"""
        for key in cons:
            if self.isHierarchyList(key):
                selectList = []
                for item in cons[key]:
                    selectList.append(item)
                    selectList = selectList + self.listHandler.getList(table, key).getHierarchyListDescendants(item)
                cons[key] = selectList

    def parseConstraintsForOutput(self, attr_value, attr_type):
        """\brief Search Param Visualisation preparation"""
        # general behaviour: this is called by the search result template to generate
        # nicer values for constraint display
        # problem: complex search with sub-tables is ignored, the prefixed constraints get treated as string
        #  (resulting in empty labels and autoids in the constraint display for lists
        # TODO: Fix the sub-table workaround and check constraints for every sub-table separately -> need sub-table layout for that

        # for memo and string fields, ListTypes can arrive here, and for list fields as well, check type
        if attr_type == 'string' and isinstance(attr_value, ListType):
            # strip the <any>-Operator (*) from each value part and join them by space
            return ' '.join(map (lambda x: str(x).strip('*'), attr_value))
        elif attr_type in ['multilist', 'singlelist']:
            # check multilists, the search widget delivers [None] when item was selected and deselected
            return [value for value in attr_value if value]
        elif attr_value == 'NULL':
            # Wert explizit auf NULL gesetzt (checkbox)
            return 'falsch'
        elif attr_value == '_not_NULL':
            # Wert auf wahr gesetzt (checkbox)
            return 'gesetzt'
        else:
            return attr_value


    def getChangeDate(self, table, autoid):
        """get the last change / creation date of the entry with the given autoid"""
        if not autoid:
            return None
        tobj = self.tableHandler[table]
        root = tobj.getTableNode()
        root.setConstraints({'autoid': autoid})
        sql = root.getSQL(col_list = ['entrydate', 'changedate'],
                          distinct = True,
                          checker = self)
        results = self.getManager(ZC.ZM_PM).executeDBQuery(sql)
        if results:
            # use changedate, if set, entrydate otherwise
            date = results[0][1] or results[0][0]
            # return a user friendly and localization-aware formatted representation using a helper function (plone wrapper)
            return self.toLocalizedTime(date)


    def generateMailLink(self, email):
        """\brief generate link string from email to avoid tal:attributes quoting of scrambled email string"""
        return '<a href="mailto:%s">%s</a>' % (email, email)


    def encrypt_ordtype(self, s):
        # listcomprehensions nested and with evaluation expression for speed
        # using string concat instead of print formatting for speed
        return ''.join([whichCode==0 and ch or whichCode==1 and '&#' + str(ord(ch)) + ';' or '&#x' + str(hexlify(ch)) + ';' for (ch, whichCode) in [(z, randint(0,2)) for z in s.group()]])


    def emailProtect(self, body_txt=''):
        # use protection_expr to replace mailadresses by scrambled strings using encrypt_ordtype
        return protection_expression.sub(self.encrypt_ordtype, body_txt)


    def correctUTF8(self, value):
        # correct a utf8 native string for display on templates
        try:
            value.decode('utf-8')
            # no error means we had latin-1 or ascii, which decodes to utf-8 easily
        except:
            # this is already utf-8, ascii-encoder raised an error
            value = value.decode('latin-1')
        return value


    def isHierarchyList(self, listname):
        # check if a List with that name is referenced by a table attribute
        hlists = []
        for tablename in self.tableHandler.keys():
            hlists.extend(self.listHandler.getLists(tablename, ['hierarchylist']))
        for lobj in hlists:
            if lobj.listname == listname:
                return True
        return False


#
# Edit Layout Info
#

    def getLayoutInfo(self, table, action):
        """\brief Returns grouping information for layout"""
        # allow external scripts
        res = []
        name = 'getLayoutInfo_%s' % (self._className)
        if hasattr(self, name):
            res = getattr(self, name)(table, action)
        if res:
            return res

        if hasattr(self, 'getLayoutInfoHook'):
            res = self.getLayoutInfoHook(table, action)
        if res:
            return res

        # default
        if action in ['create', 'edit', 'show']:
            fields = self.tableHandler[table].getColumnDefs(vis_only = False, edit_tracking = False).keys()
        else:
            fields = self.tableHandler[table].getColumnDefs(vis_only = True, edit_tracking = False).keys()
        res = [{'label': 'Datenfelder', 'fields': fields}]
        return res


    def getHelpTexts(self, table):
        """\brief helptexts"""
        # allow external scripts
        res = {}
        name = 'getHelpTexts_%s' % (self._className)
        if hasattr(self, name):
            res = getattr(self, name)(table)
        if res:
            return res

        if hasattr(self, 'getHelpTextsHook'):
            res = self.getHelpTextsHook(table)
        if res:
            return res

        return {}


    def getDefaultSearchValues(self, table):
        """\brief return default value dict for search"""
        return {}


    def getDefaultCreateValues(self, table):
        """\brief return default value dict for creation"""
        return {}


#
# Diff support for working copies
#

    def getDiff(self, entrya, entryb):
        """\brief extract the keys of differences between two complete entries"""
        diff = {}
        for key in entrya.keys():
            if key in ['autoid', 'permission', 'iscopyof', 'entrydate', 'changedate']:
                continue
            vala = entrya[key]
            # weak fix for multilist notes
            valb = entryb.get(key)
            if isinstance(vala, ListType):
                vala.sort()
            elif isinstance(vala, StringType):
                vala = vala.replace('\r\n', '\n')
            if isinstance(valb, ListType):
                valb.sort()
            elif isinstance(valb, StringType):
                valb = valb.replace('\r\n', '\n')
            if vala != valb:
                diff[key] = 1
        return diff.keys()


    def getCopyDiff(self, table, autoid):
        """\brief find the copy or original and the diff"""
        tobj = self.tableHandler[table]
        entry = tobj.getEntry(autoid, ignore_permissions = True)
        copy = None
        orig = None
        if entry.get('iscopyof'):
            copy = entry
            orig = tobj.getEntry(entry.get('iscopyof'), ignore_permissions = True)
        else:
            orig = entry
            res  = tobj.getEntryList(constraints = {'iscopyof': entry.get('autoid')}, ignore_permissions = True)
            if res:
                copy = res[0]
        if copy and orig:
            return [orig, copy, self.getDiff(orig, copy)]


    def dictIntersect(self, dicta, dictb):
        """\brief intersect the keys of the two dicts, return list"""
        return list(set(dicta).intersection(set(dictb)))


    def getDiffLabels(self, table, entry):
        """\brief get the labels for the diff keys"""
        labels = []
        tobj = self.tableHandler[table]
        for attr in self.getDiff(entry, self.zopra_forceOriginal(table, entry)):
            label = tobj.getLabel(attr)
            if not label:
                pos = attr.find('notes')
                if pos != -1 and attr[pos+5:].isdigit():
                    label = tobj.getLabel(attr[:pos])
            if label not in labels:
                labels.append(label)
        return labels

#
# Display Support Functions
#


    # the really nice formatting is bad for parsing on edit -> dropped it for now
    #def formatCurrency(self, value):
    #    """\brief Format value as currency with 1000er breaker points and one comma"""
    #    return re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1.", ('%.2f' % value).replace('.', ','))


    def reorderColsAccordingly(self, cols, order):
        """\brief Order the list cols according to the order in the list order"""
        newlist = []
        for onecol in order:
            if onecol in cols:
                newlist.append(onecol)
        for onecol in cols:
            if not onecol in newlist:
                newlist.append(onecol)
        return newlist


    def getRelatedEntries(self, autoid, table, attribute, lang = None):
        """\brief get Entries of table that are connected to an entry of another
                  table with autoid autoid via multilist named attribute (backref)"""
        # FIXME: saving such an entry, you have to check the translations and their relations
        # FIXME: Do you? could just jump to the translations every time you call it
        # FIXED: return all entries for all languages, in template select only relevant languages
        lobj = self.listHandler.getList(table, attribute)
        getEntry = self.tableHandler[table].getEntry
        return [getEntry(autoid, lang, ignore_permissions = True) for autoid in lobj.getMLRef(None, autoid)]


    def prepareLinks(self, text):
        """\brief find all links in text starting with www or http and make them into real links"""
        # expression to find mailto and http/https urls, which will be made into real links
        expr = re.compile(r'((?:mailto\:|https?\://){1}\S+)\s*?(\[.*?\])')
        # get the editorial urls
        prop = self.portal_properties.site_properties
        server_urls = prop.hasProperty('editorial_server_urls') and prop.editorial_server_urls or ['https://secure-redaktion.tu-dresden.de', 'https://sins-redaktion.tu-dresden.de', 'https://verw-redaktion.tu-dresden.de']
        server_url = self.REQUEST.SERVER_URL
        # internal function for link replacement
        def apply(s):
            try:
                # get url and possible label
                url = s.group(1)
                label = s.group(2)
                # check the url, make it point to the active damain (for logged-in user)
                if server_url in server_urls:
                    url = url.replace('http://tu-dresden.de', server_url).replace('https://tu-dresden.de', server_url)
                # use url as label, if no label is given
                if not label or label == '[]':
                    label = url
                else:
                    # label given, remove the parentheses
                    label = label[1:-1]
                # build link, insert url and label
                return '<a href="%s" target="_blank">%s</a>' % (url, label)
            except:
                # something wrong, do not touch the original string
                return s.group()
        # apply the function to all hits of the expression
        return expr.sub(apply, text)

    def removeLinks(self, text):
        """\brief find all links in text starting with www or http and remove the []-label"""
        expr = re.compile(r'((?:mailto\:|https?\://){1}\S+)\s*?(\[.*?\])')
        def apply(s):
            try:
                # only extract the url
                url = s.group(1)
                return url
            except:
                # single url found
                return s.group()
        return expr.sub(apply, text)


    def val_translate(self, name, descr_dict, attr_name = None):
        """\brief get list object, translate attr id from dict into value"""
        return self.listHandler[name].getValueByAutoid(descr_dict.get(attr_name or name, '')) or ''


    def py2json(self,object,encoding="utf-8"):
        """\brief translate python object to json"""
        return json.dumps(object).decode('raw-unicode-escape').encode(encoding)


    def json2py(self,json, encoding="utf-8"):   # JSON -> python object
        """\brief translate json to python object"""
        return json.loads(json, encoding)


    # Button and REQUEST handling
    def getTableEntryFromRequest(self, table, REQUEST, prefix = '', search = False):
        """\brief Builds a \c descr_dict from an REQUEST object.

        The function tries to filter all key,
        value pairs where a key matches
        with a column name of the specified table
        (maybe prefixed with DLG_CUSTOM and the given prefix).
        It also looks for special keys (ANDconcat for multi search / filter)

        \param table  The argument \a table is a string with the table name
               without id prefix.

        \param REQUEST  The argument \a REQUEST is a REQUEST object that
               contains the key, value pairs of the fields from the html form.

        \param prefix The argument \a prefix is a string that makes
               the function only filter keys that
        start with DLG_CUSTOM+prefix, the results are unprefixed however

        \param search indicates whether AND-concatenation should be checked for
               multi and hierarchy lists.

        \return The function will return a description dictionary with the
                found key - value pairs
        """
        entry = GenericManager.getTableEntryFromRequest(self, table, REQUEST, prefix, search)
        tobj = self.tableHandler[table]
        col_types = tobj.getColumnTypes()
        for col in col_types:
            if col_types[col] in ('float', 'currency'):
                entry[col] = ('%s' % entry.get(col, '')).replace(',', '.')
            # this removes empty list entries from the resulting entry for search
            # (where adding and removing a selection from a multilist results in an empty list being transmitted as search param)
            if search and col_types[col] in ('multilist', 'hierarchylist') and entry.get(col) == []:
                del entry[col]

        return entry


    def prepareHierarchylistDisplayEntries(self, entries):
        """\brief sort the entries into a tree, add level key and return flattened and sorted list"""
        # TODO: implement
        for entry in entries:
            entry['level'] = 0
        return entries


    # disable basic Display Functions
    def infoForm(self, table, id, REQUEST):
        """\brief Returns html of the generic entry info page."""
        pass

    def newForm(self, table, REQUEST = None):
        """\brief Returns the html source of the generic new form."""
        pass

    def editForm(self, id, table, REQUEST = None):
        """\brief Returns the html source of the generic edit form."""
        pass

    def editPermissionForm(self, table, id, REQUEST):
        """\brief permission editing"""
        pass

    def searchForm(self, table, descr_dict = None, REQUEST = None):
        """\brief Returns the html source of the generic search form.
           \param descr_dict is one dict or a list of tuples of dicts and
                  prefixes. The number of those tuples and the prefixes are
                  specified in getSearchPattern.
                  Standard behaviour is one dict.
        """
        pass

    def showForm(self, id, table, REQUEST = None, auto = None):
        """\brief Returns the html source of the generic show form."""
        pass

    def closeForm(self, table, REQUEST = None):
        """\brief closes the current form, redirects to manager. Overwrite for special behaviour.
        """
        pass

    def showList(self, table, REQUEST = None):
        """\brief Returns the html source of the generic show list form."""
        pass

    def getSingleMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None):
        """\brief Main mask building function, returns a generic html mask
                    Overwrite this function to build a custom entry mask. Usage of
                    buildSemiGenericMask can aid with the basic mask layout, adding
                    custom parts to the basic mask afterwards. If you are using multi-
                    mask generic handling for the search (overwrote getSearchPattern?),
                    make sure to test for a list as descr_dict and forward to getMultiMask
                    in that case. This handling sucks, but there is no easy way for now."""
        pass

    def getMultiMask(self, table, flag, dict_list):
        """\brief Return a generic mask consisting of multiple single masks in a vertical layout.
                Overwrite if vertical is not your style and you know what you are doing."""
        pass

    def getMask(self, table, flag = MASK_SHOW, descr_dict = None, prefix = None):
        """\brief adds id and table property to getSingleMask-Output"""
        pass

    def buildSemiGenericMask( self,
                              table,
                              template,
                              flag,
                              descr_dict  = None,
                              prefix      = None,
                              widget      = None,
                              parent      = None,
                              fixTracking = False ):
        """\brief Builds a widget with a grid layout representing the template."""
        pass

    def buildSubMask( self,
                      table,
                      flag,
                      mainTable = None,
                      mainAttr  = None,
                      mainId    = None,
                      display   = None,
                      prefix    = None,
                      entries   = None,
                      parent    = None ):
        """\brief build a mask for a subtable with header"""
        pass

    def buildRowMask( self,
                      table,
                      ddict,
                      mask,
                      row,
                      flag,
                      prefix,
                      display,
                      label     = False,
                      mainTable = None,
                      mainAttr  = None ):
        """\brief mask for one entry per row, called once per entry"""
        pass

    def getFunctionWidget( self,
                           table,
                           attribute,
                           parent,
                           flag = MASK_SHOW,
                           descr_dict = None,
                           prefix     = None ):
        """\brief Returns the widget for the functional part."""
        pass

    def importForm(self, REQUEST):
        """\brief Returns the html source of an import table dialog."""
        pass

    def importCheckLines(self, importer, fHandle):
        """\brief Imports tab separated data into the database."""
        pass

    def getTableEntryNewDialog( self,
                                title,
                                mask,
                                action  = '',
                                refresh = True,
                                REQUEST = None,
                                reset   = 'client',
                                basket  = False,
                                closeIsClose = False ):
        """\brief returns the standard Html Dialog for new entries."""
        pass

    def getTableEntryEditDialog( self,
                                 title,
                                 mask,
                                 action    = '',
                                 refresh   = True,
                                 REQUEST   = None,
                                 reset     = 'client',
                                 table     = None,
                                 isGeneric = False, # obsolete
                                 closeIsClose = False):
        """\brief Returns the standard Html Dialog for editing."""
        pass

    def getTableEntryShowDialog( self,
                                 title,
                                 mask,
                                 action    = '',
                                 REQUEST   = None,
                                 table     = None,
                                 auto      = None,
                                 actid     = None,
                                 edit      = False,
                                 isGeneric = False, # obsolete
                                 basket    = False,
                                 closeIsClose = False):
        """\brief Returns the html source of an table entry overview."""
        pass

    def getTableEntrySearchDialog( self,
                                   title,
                                   mask,
                                   action = '',
                                   table = None,
                                   closeIsClose = False ):
        """\brief Returns the html source of an table search form."""
        pass

    def getSearchTickAutoidList(self, table, REQUEST, treeRoot, row_count = 0, max_rows = 0):
        """\brief Get Autoidlist of ticked or all searched entries"""
        pass

    def getTableEntryListHtml( self,
                               treeRoot,
                               param      = None,
                               REQUEST    = None,
                               isGeneric  = False,  # obsolete
                               closeIsClose = False ):
        """\brief Returns the html source of an table overview.
        param
            start_number
            show_number
            special link
            special link field
            foreign fields definition
        """
        pass

    def navigationMenu(self, REQUEST):
        """\brief Create the Navigation Menu for inter-manager-navigation."""
        pass

    def contextMenu(self, REQUEST = None):
        """\brief Create the Context Menu for Basket and Search-Management."""
        pass

    def getBasketForm(self, REQUEST):
        """\brief function that displays the basket using the baskets html function.
                This is only an entry point for the basket, when it is forwarding actions to itself.
                Since the basket is no SimpleItem anymore, it cannot be used directly."""
        pass

    def exportForm(self, REQUEST, RESPONSE, autoidlist = [], show_fields = [], table = None):
        """\brief Returns the html source of an export table dialog.

        \param REQUEST  The argument \a REQUEST is used for the button handling
                        and should be a ZOPE REQUEST object.
        \param autoidlist If autoidlist, show_fields and table are given, show this params
        \result html page - export dialog
        """
        pass
