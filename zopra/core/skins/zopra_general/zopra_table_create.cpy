## Controller Python Script "zopra_table_create"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table
##title=
##
request = context.REQUEST
#try:

entry = context.getTableEntryFromRequest(table, request)
# set initial language
if context.doesTranslations(table):
    entry['language'] = context.lang_default

# call prepare_hook
context.prepareDict(table, entry, request)
# call pre_add_hook
context.actionBeforeAdd(table, entry, request)

# add entry
tmainobj = context.tableHandler[table]
autoid = tmainobj.addEntry(entry)
entry['autoid'] = autoid

# add repeatable fields
autoidlist = [str(autoid)]
if request.has_key('repeats') and request['repeats']>1:
    fieldsets = context.getLayoutInfo(table, 'create')
    #get repeatable fields
    r_fields = []
    for element in fieldsets:
        if element.has_key('repeatfields'):
            r_fields.extend(element['repeatfields'])
  
    for i in range(2,int(request['repeats'])+1):
        add = False
        for field in r_fields:
            if request.has_key(field+'_'+str(i)) and request[field+'_'+str(i)]:
                entry[field] = request[field+'_'+str(i)]
                add = True
        if add:
            entry['autoid'] = ''
            autoidlist.append(str(tmainobj.addEntry(entry)))
    # TODO: postprocessing for repeated entries is missing!
   
# call postprocessing for original entry
msg = context.actionAfterAdd(table, entry, request) or ''

# dependent-entries hack (tell the main-entry that is has a new dependent multilist entry)
if request.get('origtable') and request.get('origid') and request.get('origattribute'):
    message = ''
    origid = int(request.get('origid'))
    attr = request.get('origattribute')
    otab = request.get('origtable')
    tobj = context.tableHandler[otab]
    orig = tobj.getEntry(origid)
    orig = context.zopra_forceCopy(otab, orig)
    origid = orig.get('autoid')
    # get the multilist object
    mlobj = context.listHandler.getList(otab, attr)
    # if working copies are enabled for this table, get or create the working copy before changing anything
    if context.doesWorkingCopies(otab):
        if not orig.get('iscopyof'):
            
            # create a copy with iscopyof - attribute (set to original autoid)
            orig['iscopyof'] = orig['autoid']
            # clear autoid for new entry
            orig['autoid'] = None
            # add the new dependent entry
            orig[attr].append(autoid)
            # save the copy, get a new autoid
            origid = int(tobj.addEntry(orig))
            # set the autoid in the entry
            orig['autoid'] = origid
            # create a fitting message
            message = 'Neuer Eintrag (%s) wurde angelegt und verknüpft. Arbeitskopie für Haupteintrag (%s) wurde erzeugt. Original-Id: %s. ' % (tmainobj.getLabel(), tobj.getLabel(), orig.get('iscopyof'))
        else:
            # copy exists, we have it already (forceCopy was called above)
            # add the new dependent entry to the attr
            #orig[attr].append(autoid)
            # update the working copy
            #tobj.updateEntry({attr: orig[attr]}, origid)
            # directly add the ref (this does not create any log)
            mlobj.addMLRef( orig['autoid'], autoid)
            # take care of the cache
            if tobj.do_cache:
                tobj.cache.invalidate(orig['autoid'])
            # jump to referring entry
            message = 'Neuer Eintrag (%s) wurde angelegt und verknüpft. Arbeitskopie für Haupteintrag (%s) wurde aktualisiert. Original-Id: %s.' % (tmainobj.getLabel(), tobj.getLabel(), orig.get('iscopyof'))
    else:
        # set new value
        #orig[attr].append(autoid)
        #tobj.updateEntry({attr: orig[attr]}, origid)
        # directly add the ref (this does not create any log)
        mlobj.addMLRef(orig['autoid'], autoid)
        # take care of the cache
        if tobj.do_cache:
            tobj.cache.invalidate(orig['autoid'])
        # jump to referring entry
        message = 'Neuer Eintrag (%s) wurde angelegt und mit Haupteintrag (%s) verknüpft.' % (tmainobj.getLabel(), tobj.getLabel())
    # jump to message window stating the creation
    request.RESPONSE.redirect('zopra_table_created_dependency?table=%s&autoid=%s&portal_status_message=%s' % (table, autoid, message))

# overwrite in request for formcontroller traversal
request.form['autoid'] = autoid
request.other['autoid'] = autoid
if request.form.has_key('form.submitted'):
    del request.form['form.submitted']

if len(autoidlist) > 1:
    request.form['autoidlist'] = autoidlist
    return state.set(status='success', context=context , portal_status_message='Neue Einträge angelegt. %sInterne Ids: %s' % (msg, ', '.join(autoidlist)))
else:
    return state.set(status='success', context=context , portal_status_message='Neuer Eintrag angelegt. %sInterne Id: %s' % (msg, autoid))
#except:
#    return state.set(status='failure', context=context, portal_status_message='Fehler beim Anlegen. Korrigieren Sie die angezeigten Fehler.')
