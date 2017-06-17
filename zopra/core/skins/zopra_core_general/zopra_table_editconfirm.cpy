## Controller Python Script "zopra_table_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, autoid
##title=
##
from zopra.core import zopraMessageFactory as _
request = context.REQUEST

# for now, we save the request values (which might have been changed by the reviewer)
# so the reviewer does not need to save changes before confirming
# other way is to only get the copy-values from the db and save them
entry = context.tableHandler[table].getEntry(autoid)
copyentry = context.getTableEntryFromRequest(table, request)

# empty bools are disturbing again
# empty lists are disturbing again
# now we have a property with the name to be sure
types = context.tableHandler[table].getColumnTypes()
# get the markers for present special fields
zopra_attr_present = request.get('zopra_attr_present', [])
for attr in types.keys():
    if attr in zopra_attr_present:
        if types[attr] == 'bool':
            if not copyentry.has_key(attr):
                copyentry[attr] = 0
        elif types[attr] == 'multilist':
            if not copyentry.has_key(attr):
                copyentry[attr] = []
        elif types[attr] == 'float':
            if copyentry.has_key(attr):
                copyentry[attr].replace(',', '.')

# check iscopyof (working copy marker) on the db entry (origentry might not include this info)
if not entry.get('iscopyof'):
    message = _('zopra_editconfirm_abort_no_copy', default = u'Only working copies can be released. This entry is up-to-date. Release was cancelled.')
    context.plone_utils.addPortalMessage(message, 'info')
    return state.set(status='failure', context=context)

origentry = context.tableHandler[table].getEntry(entry.get('iscopyof'))

if not origentry:
    message = _('zopra_editconfirm_abort_not_found', default = u'Original entry could not be found. Release was cancelled.')
    context.plone_utils.addPortalMessage(message, 'info')
    return state.set(status='failure', context=context)

origautoid = origentry['autoid']

# language switch: english language -> only save the text values
if not context.doesTranslations(table) or origentry.get('language') == context.lang_default:
    # original entry is updated
    for key in copyentry.keys():
        if key not in ['hastranslation', 'language']:
            origentry[key] = copyentry[key]

else:
    # language copy stays the same except for text and string values
    for key in copyentry.keys():
        if types.get(key) in ['string', 'memo']:
            origentry[key] = copyentry[key]

origentry['autoid'] = origautoid
origentry['iscopyof'] = 'NULL'

# overwrite in request for formcontroller traversal
request.form['autoid'] = origautoid
request.other['autoid'] = origautoid

# call prepare_hook
context.prepareDict(table, origentry, request)
# call pre_add_hook
context.actionBeforeEdit(table, origentry, request)
# update entry
done = context.tableHandler[table].updateEntry(origentry, origautoid)

status = 'failure'
if done == True:
    # update the nontext values of the english version if it exists
    en_msg = ''
    # check for translations
    if origentry.get('language') == context.lang_default and origentry.get('hastranslation'):
        # updateTranslation also updates the working copy of the translation, if it exists
        translated = context.updateTranslation(table, origentry)
        if translated:
            en_msg = _('zopra_editconfirm_translation_okay', default = ' The non-textual fields of the translated version have also been updated.')
    # check if this is a translation (for msg only, action done already)
    elif origentry.get('language') in context.lang_additional:
        en_msg = _('zopra_editconfirm_is_translation', default = ' Only the textual fields have been saved (because this is a translation).')

    # delete copy without deleting anything else (except multilists)
    done = context.tableHandler[table].deleteEntry(int(autoid))
    if done == True:
        message = _('zopra_editconfirm_success',
                    default = u'Entry has been released.${additional_msg} Internal Id: ${internal_id}',
                    mapping = {u'internal_id': origautoid, u'additional_msg': en_msg})
        status = 'success'
    else:
        message = _('zopra_editconfirm_almost_success',
                    default = u'Entry has been released.${additional_msg} Error during deletion of working copy. Internal Id: ${internal_id}',
                    mapping = {u'internal_id': origautoid, u'additional_msg': en_msg})

else:
    message = _('zopra_editconfirm_failure',
                default = u'Error during release: ${reason}',
                mapping = {u'reason': done})

context.plone_utils.addPortalMessage(message, 'info')
return state.set(status = status, context = context)
