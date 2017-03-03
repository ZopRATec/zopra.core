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

origentry = context.zopra_forceOriginal(table, entry)
ak = context.doesWorkingCopies(table) and (entry.get('autoid') != origentry.get('autoid'))
sk = context.doesTranslations(table) and entry.get('istranslationof')

targetid = None
special_message = ''
if ak:
    targetid = origentry.get('autoid')
    special_message = u'Arbeitskopie geloescht.'
elif sk:
    targetid = sk
    special_message = u'Sprachkopie geloescht.'

done = context.deleteEntries(table, [int(autoid)])

if done and sk:
    context.removeTranslationInfo(table, sk)

# dependent-entries handling (tell the main-entry that a dependent multilist entry was removed)
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
            message = u'Verknuepfter Eintrag (%s) wurde entfernt. Arbeitskopie fuer Haupteintrag (%s) wurde erzeugt. Original-Id: %s. ' % (tmainobj.getLabel().decode("utf8"), tobj.getLabel().decode("utf8"), orig.get('iscopyof'))
        else:
            # copy exists, we have it already (forceCopy was called above)
            # directly remove the ref (this does not create any log)
            mlobj.delMLRef( orig['autoid'], autoid)
            # take care of the cache
            if tobj.do_cache:
                tobj.cache.invalidate(orig['autoid'])
            # jump to referring entry
            message = u'Verknuepfter Eintrag (%s) wurde entfernt. Arbeitskopie fuer Haupteintrag (%s) wurde aktualisiert. Original-Id: %s.' % (tmainobj.getLabel().decode("utf8"), tobj.getLabel().decode("utf8"), orig.get('iscopyof'))
    else:
        # remove the deleted dependent entry from attr
        # directly remove the ref (this does not create any log)
        mlobj.delMLRef(orig['autoid'], autoid)
        # take care of the cache
        if tobj.do_cache:
            tobj.cache.invalidate(orig['autoid'])
        # message deletion and deref
        message = u'Verknuepfter Eintrag (%s) wurde geloescht und Haupteintrag (%s) aktualisiert.' % (tmainobj.getLabel().decode("utf8"), tobj.getLabel().decode("utf8"))
    # set message
    if message:
        context.plone_utils.addPortalMessage(message, 'info')
    # jump to message window stating the creation
    request.RESPONSE.redirect('zopra_table_deleted_dependency?table=%s&autoid=%s' % (table, autoid))
    return

if done:
    message = special_message or u'Eintrag geloescht.'
    context.plone_utils.addPortalMessage(message, 'info')
    if targetid:
        # jump to edit form of original
        request.RESPONSE.redirect('zopra_table_edit_form?table=%s&autoid=%s' % (table, targetid))
    return state.set(status='success', context=context)
else:
    message = u'Fehler beim Loeschen.'
    context.plone_utils.addPortalMessage(message, 'info')
    return state.set(status='failure', context=context)
