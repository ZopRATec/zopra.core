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
tobj = context.tableHandler[table]
entry = context.getTableEntryFromRequest(table, REQUEST)

required = []
if not searching:
    required = context.getGenericConfig(table).get('required', [])

errors = tobj.validateEntry(entry, required)

if not searching:
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
    return state.set(status='failure', portal_status_message='Please correct the indicated errors.')
else:
    return state.set(status='success')
