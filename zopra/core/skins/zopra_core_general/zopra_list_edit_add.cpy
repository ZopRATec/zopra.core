## Controller Python Script "zopra_list_edit_add"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=listname, new_value='', new_rank=None
##title=
##
if not new_value:
    return state.set(status='success', context=context , portal_status_message='Keine Aenderungen vorgenommen.')
lobj = context.listHandler[listname]
request = context.REQUEST
kwargs = {}
for translation in lobj.translations:
    key = 'new_value_' + translation
    if request.form.has_key(key):
        kwargs['value_'+translation] = request.form.get(key)
lobj.addValue(new_value, '', new_rank, **kwargs)
return state.set(status='success', context=context , portal_status_message='Eintrag angelegt.')