## Controller Python Script "zopra_table_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, confirm_ids, REQUEST
##title=
##
from zopra.core import zopraMessageFactory as _
request = REQUEST
tobj = context.tableHandler[table]
for autoid in confirm_ids:
    copyentry = tobj.getEntry(autoid)

    if not copyentry.get('iscopyof'):
        label = context.getLabelString(table, None, copyentry)
        message = _('zopra_multiconfirm_abort_no_copy',
                    default = u"Only working copies can be released. The entry '${entry_label}' is up-to-date. Release was cancelled.",
                    mapping = {u'entry_label': label})
        context.plone_utils.addPortalMessage(context.translate(message), 'info')
        return state.set(status='failure', context=context)

    origentry = context.tableHandler[table].getEntry(copyentry.get('iscopyof'))

    if not origentry:
        label = context.getLabelString(table, None, copyentry)
        message = _('zopra_multiconfirm_abort_not_found',
                    default = u"Original entry '${entry_label}' could not be found. Release was cancelled.",
                    mapping = {u'entry_label': label})
        context.plone_utils.addPortalMessage(message, 'info')
        return state.set(status='failure', context=context)

    origautoid = origentry['autoid']

    # language switch: english language -> only save the text values
    if not context.doesTranslations(table) or copyentry.get('language') == context.lang_default:
        # original entry is updated
        for key in copyentry.keys():
            if key not in ['hastranslation', 'language']:
                origentry[key] = copyentry[key]

    else:
        # english copy stays the same except for text and string values
        types = tobj.getColumnTypes()
        for key in copyentry.keys():
            if types.get(key) in ['string', 'memo']:
                origentry[key] = copyentry[key]

    origentry['autoid'] = origautoid
    origentry['iscopyof'] = 'NULL'

    # call prepare_hook
    context.prepareDict(table, origentry, request)
    # call pre_add_hook
    context.actionBeforeEdit(table, origentry, request)
    # update entry
    done = tobj.updateEntry(origentry, origautoid)
    if done == True:
        # update the nontext values of the english version if it exists
        en_msg = u''
        # check for translations
        if origentry.get('language') == context.lang_default and origentry.get('hastranslation'):
            # updateTranslation also updates the working copy of the translation, if it exists
            translated = context.updateTranslation(table, origentry)
            if translated:
                en_msg = _('zopra_edit_translation_updated',
                                default = u'Non-text fields of the translated version have been saved additionally. ')
        # check if this is a translation (for msg only, action done already)
        elif origentry.get('language') in context.lang_additional:
            en_msg = _('zopra_edit_translation_saved', default = 'Only the text fields have been saved (because this is a translation). ')
        if en_msg:
            en_msg = context.translate(en_msg)
        # delete copy without deleting anything else (except multilists)
        done = context.tableHandler[table].deleteEntry(int(autoid))
        # build and deliver message
        label = context.getLabelString(table, None, origentry)
        if done == True:
            message = _('zopra_multiconfirm_success',
                        default = u"Entry '${entry_label}' has been released. ${additional_msg}Internal Id: ${internal_id}.",
                        mapping = {u'entry_label': label, u'internal_id': origautoid, u'additional_msg': en_msg})
        else:
            message = _('zopra_multiconfirm_almost_success',
                        default = u"Entry '${entry_label}' has been released. ${additional_msg}Error during deletion of working copy. Internal Id: ${internal_id}.",
                        mapping = {u'entry_label': label, u'internal_id': origautoid, u'additional_msg': en_msg})
        context.plone_utils.addPortalMessage(context.translate(message), 'info')
    else:
        message = _('zopra_multiconfirm_failure',
                    default = u"Error during release of entry '${entry_label}': ${reason}",
                    mapping = {u'entry_label': label, u'reason': done})
        context.plone_utils.addPortalMessage(context.translate(message), 'info')
# there is only the success state, even if all confirm_ids ended up in error
return state.set(status = 'success', context = context)
