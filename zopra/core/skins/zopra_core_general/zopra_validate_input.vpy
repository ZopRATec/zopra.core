## Controller Validator "zopra_validate_input"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, REQUEST, searching=False
##title=Validates the input fields
##
# istranslationof and hastranslation need to be present in the field definition for edit-form when table is translatable
tobj = context.tableHandler[table]
entry = context.getTableEntryFromRequest(table, REQUEST)

# strange validation error fix:
if not entry:
    request = context.REQUEST
    entry = context.getTableEntryFromRequest(table, REQUEST)
    # TODO: log this problem?

required = []
# translations can not be validated for required inputs (or could, but needed to be merged onto the real entry before validation)
istranslationof = REQUEST.form.get('istranslationof')
# search input cannot be validated for required inputs
if not searching and not istranslationof:
    required = context.getGenericConfig(table).get('required', [])

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
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure')
else:
    return state.set(status='success')
