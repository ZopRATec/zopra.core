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
request = context.REQUEST

if not context.doesTranslations(table):
    message = 'Diese Tabelle unterstützt keine Übersetzungen. Übersetzung abgebrochen.'
    return state.set(status='failure', context=context, portal_status_message=message)  

# for now, we just create an english version with all original values, if it does not exist and update the orginal entry (hastranslation)
origentry = context.tableHandler[table].getEntry(autoid)

if not origentry:
    message = 'Originaleintrag nicht auffindbar, Übersetzung abgebrochen.'
    return state.set(status='failure', context=context, portal_status_message=message)

if not origentry.get('hastranslation'):
    # use original entry if translating a working copy
    origentry = context.zopra_forceOriginal('studiengang', origentry)
    
    # create translation
    entry = {}
    for key in origentry.keys():
        entry[key] = origentry[key]
    
    entry['istranslationof'] = origentry['autoid']
    entry['language'] = 'en'
    entry['iscopyof'] = 'NULL'
    
    # save entry
    entry['autoid'] = None
    newautoid = context.tableHandler[table].addEntry(entry)
    
    # update orginal entry
    origentry['hastranslation'] = 1
    # just to be safe, set lang_default in orig entry
    origentry['language'] = context.lang_default
    context.tableHandler[table].updateEntry(origentry, origentry['autoid'])
    
    # overwrite in request for formcontroller traversal
    request.form['autoid'] = newautoid
    request.other['autoid'] = newautoid
    
    message = 'Übersetzung erzeugt. Interne Id: %s' % (newautoid)
    return state.set(status='success', context=context, portal_status_message=message)
    
else:
    message = 'Übersetzung existiert bereits. Übersetzung abgebrochen.'
    return state.set(status='failure', context=context, portal_status_message=message)
