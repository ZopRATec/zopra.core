## Script (Python) "zopra_table_delete"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, del_autoid, offset = 0
##title=
##
autoid = del_autoid
request = context.REQUEST
done = False

# new permission handling
entry = context.tableHandler[table].getEntry(autoid)
if not 'delete' in context.getPermissionEntryInfo(table, entry):
    return state.set(status='failure', context=context, portal_status_message="Nur berechtigte Redakteure dürfen Einträge löschen. Abgebrochen.")

done = context.deleteEntries(table, [int(autoid)])
# look for referring entries
#if done and request.get('origtable'):
#    otab  = request.get('origtable')
#    oid   = request.get('origid')
#    oattr = request.get('origattribute')
#    if otab and oid and oattr:
#        tobj = context.tableHandler[otab]
#        entry = tobj.getEntry(int(oid))
#        if not entry:
#            raise ValueError(['Something wrong!', otab, oid, oattr])
#        attr  = entry.get(oattr)
#        if same_type(attr, []):
#            if int(autoid) in attr:
#                attr.remove(int(autoid))
#        else:
#            entry[oattr] = None
#        tobj.updateEntry(entry, entry.get('autoid'))
#        message='Verknüpfter Eintrag (%s) wurde gelöscht, Haupteintrag (%s) wurde aktualisiert.'
#        request.RESPONSE.redirect('zopra_table_deleted_dependency?table=%s&portal_status_message=%s' % (table, message))

# dependent-entries hack (tell the main-entry that is has a new dependent multilist entry)
if done and request.get('origtable') and request.get('origid') and request.get('origattribute'):
    tmainobj = context.tableHandler[table]
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
            # remove the deleted dependent entry from attr
            orig[attr].remove(autoid)
            # save the copy, get a new autoid
            origid = int(tobj.addEntry(orig))
            # set the autoid in the entry
            orig['autoid'] = origid
            # create a fitting message
            message = 'Verknüpfter Eintrag (%s) wurde entfernt. Arbeitskopie für Haupteintrag (%s) wurde erzeugt. Original-Id: %s. ' % (tmainobj.getLabel(), tobj.getLabel(), orig.get('iscopyof'))
        else:
            # copy exists, we have it already (forceCopy was called above)
            # remove the deleted dependent entry from attr
            #orig[attr].remove(autoid)
            # update the working copy
            #tobj.updateEntry({attr: orig[attr]}, origid)
            # directly add the ref (this does not create any log)
            mlobj.delMLRef( orig['autoid'], autoid)
            # take care of the cache
            if tobj.do_cache:
                tobj.cache.invalidate(orig['autoid'])
            # jump to referring entry
            message = 'Verknüpfter Eintrag (%s) wurde entfernt. Arbeitskopie für Haupteintrag (%s) wurde aktualisiert. Original-Id: %s.' % (tmainobj.getLabel(), tobj.getLabel(), orig.get('iscopyof'))
    else:
        # remove the deleted dependent entry from attr
        #orig[attr].remove(autoid)
        #tobj.updateEntry({attr: orig[attr]}, origid)
        # directly add the ref (this does not create any log)
        mlobj.delMLRef(orig['autoid'], autoid)
        # take care of the cache
        if tobj.do_cache:
            tobj.cache.invalidate(orig['autoid'])
        # jump to referring entry
        message = 'Verknüpfter Eintrag (%s) wurde gelöscht und Haupteintrag (%s) aktualisiert.' % (tmainobj.getLabel(), tobj.getLabel())
    # jump to message window stating the creation
    request.RESPONSE.redirect('zopra_table_created_dependency?table=%s&autoid=%s&portal_status_message=%s' % (table, autoid, message))

if done:
    message='Eintrag gelöscht.'
    return state.set(status='success', context=context , portal_status_message=message)
else:
    message='Fehler beim Löschen.'
    return state.set(status='failure', context=context, portal_status_message=message)
