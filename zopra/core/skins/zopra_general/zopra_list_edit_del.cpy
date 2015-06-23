## Controller Python Script "zopra_list_edit_del"
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
    return state.set(status='success', context=context , portal_status_message='Keine Aenderungen vorgenommen.')
if not same_type(edit_autoid, []):
    edit_autoid = [edit_autoid]
lobj = context.listHandler[listname]
done = False
for oneid in edit_autoid:
    lobj.delValue(int(oneid))
    done = True

if done:
    return state.set(status='success', context=context , portal_status_message='Eintraege gelöscht.')
else:
    return state.set(status='success', context=context, portal_status_message='Keine Änderungen vorgenommen.')
