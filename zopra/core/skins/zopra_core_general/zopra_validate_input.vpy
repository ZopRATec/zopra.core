## Controller Validator "zopra_validate_input"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table=None, REQUEST=None, searching=False
##title=Validates the input fields
##
# coding: utf-8
from zopra.core import zopraMessageFactory as _
# recheck the parameters
if not REQUEST:
    REQUEST = context.REQUEST
if not table:
    table = REQUEST['table']
searching = REQUEST.get('searching', False)

import logging
# istranslationof and hastranslation need to be present in the field definition for edit-form when table is translatable
tobj = context.tableHandler[table]
entry = context.getTableEntryFromRequest(table, REQUEST)

# strange validation error fix:
if REQUEST['PUBLISHED'].getId() == 'zopra_table_edit_form' and (not entry or (table == 'studiengang' and entry and not entry.get('name'))):
    logger = logging.getLogger("Plone")
    logger.info('VALIDATION-ERROR on edit_form: entry: %s' % entry)
    request = context.REQUEST
    logger.info(str(request))
    entry = context.getTableEntryFromRequest(table, request)
    if entry:
        logger.info('FOUND the real entry: %s' % entry)

required = []
# translations are not validated for required inputs (because they save their text fields only)
istranslationof = REQUEST.form.get('istranslationof')
# search input cannot be validated for required inputs
if not searching and not istranslationof:
    required = context.getGenericConfig(table).get('required', [])

# validation is redirected via Table to tools.ZopRAProduct to connector.SQLConnector
# when required is empty, only the type validation is done
errors = tobj.validateEntry(entry, required)


# special validators also do not work when searching or working on a copy
if not searching and not istranslationof:
    check_fields = context.getGenericConfig(table).get('check_fields', {})
    for check_field in check_fields:
        # check always, also on empty entries
        fkt = check_fields[check_field]
        res = fkt(check_field, entry, context)
        if res != True:
            if not res:
                res = 'Invalid input'
            errors[check_field]=res, entry[check_field]

for key in errors:
    error = errors[key]
    state.setError(key, error[0], error[1])

if state.getErrors():
    message = _('zopra_form_errors',
                default = u'Please correct the indicated errors.')
    context.plone_utils.addPortalMessage(context.translate(message), 'info')
    return state.set(status='failure', context=context)
else:
    return state.set(status='success', context=context)
