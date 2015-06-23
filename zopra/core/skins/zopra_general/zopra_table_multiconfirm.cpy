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
request = REQUEST
tobj = context.tableHandler[table]
msgs = []
for autoid in confirm_ids:
    copyentry = tobj.getEntry(autoid)

    if not copyentry.get('iscopyof'):
        label = context.getLabelString(table, None, copyentry)
        msg = 'Nur Arbeitskopien können freigegeben werden. Der Eintrag %s ist aktuell, die Freigabe wird abgebrochen.' % label
        return state.set(status='failure', context=context, portal_status_message=msg)

    origentry = context.tableHandler[table].getEntry(copyentry.get('iscopyof'))

    if not origentry:
        label = context.getLabelString(table, None, copyentry)
        msg = 'Originaleintrag zu %s nicht auffindbar, Freigabe abgebrochen.' % label
        return state.set(status='failure', context=context, portal_status_message=msg)

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
    tobj.updateEntry(origentry, origautoid)

    # update the nontext values of the english version if it exists
    en_msg = ''
    # check for translations
    if origentry.get('language') == context.lang_default and origentry.get('hastranslation'):
        # updateTranslation also updates the working copy of the translation, if it exists
        translated = context.updateTranslation(table, origentry)
        if translated:
            en_msg = ' Die Nicht-Text-Felder der englischen Version wurde ebenfalls gespeichert.'
    # check if this is a translation (for msg only, action done already)
    elif origentry.get('language') in context.lang_additional:
        en_msg = ' Lediglich die Textfelder wurden übernommen, da es sich um eine Sprachkopie handelt.'

    # delete copy without deleting anything else (except multilists)
    context.tableHandler[table].deleteEntry(int(autoid))
    # build and append message
    label = context.getLabelString(table, None, origentry)
    msgs.append('Eintrag %s freigegeben.%s Interne Id: %s' % (label, en_msg, origautoid))
    
msg = '<br />'.join(msgs)
return state.set(status='success', context=context, portal_status_message=msg)
