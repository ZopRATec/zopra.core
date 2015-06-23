## Controller Python Script "zopra_list_edit_upd"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=listname, edit_autoid=[]
##title=
##
request = context.REQUEST
if not edit_autoid:
    return state.set(status='success', context=context , portal_status_message='Keine Änderungen vorgenommen.')
if not same_type(edit_autoid, []):
    edit_autoid = [edit_autoid]
lobj = context.listHandler[listname]
done = False
for oneid in edit_autoid:
    value = request.get('edit_value_%s' % oneid, '')
    rank = request.get('edit_rank_%s' % oneid, None)
    entry = lobj.getEntry(oneid)
    entry['value'] = value
    entry['rank'] = rank
    for translation in lobj.translations:
        entry['value_'+translation] = request.get('edit_value_%s_%s' % (oneid, translation), '')
    lobj.updateEntry(entry, int(oneid))
    done = True

if done:
    return state.set(status='success', context=context , portal_status_message='Einträge gespeichert.')
else:
    return state.set(status='success', context=context, portal_status_message='Keine Änderungen vorgenommen.')
