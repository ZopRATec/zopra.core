## Script (Python) "zopra_table_delete"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, del_autoid, offset = 0, zopra_popup=None
##title=
##
from zopra.core import zopraMessageFactory as _


autoid = del_autoid
request = context.REQUEST
done = False

# new permission handling
entry = context.tableHandler[table].getEntry(autoid)
if not "delete" in context.getPermissionEntryInfo(table, entry):
    message = _(
        "zopra_delete_permission_missing",
        default=u"Only editors with delete permission are allowed to delete entries. Aborted.",
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)

origentry = context.zopra_forceOriginal(table, entry)
ak = context.doesWorkingCopies(table) and (
    entry.get("autoid") != origentry.get("autoid")
)
sk = context.doesTranslations(table) and entry.get("istranslationof")

targetid = None
special_message = None
if ak:
    targetid = origentry.get("autoid")
    special_message = _(
        "zopra_deleted_workingcopy", default=u"Working copy has been deleted."
    )
elif sk:
    targetid = sk
    special_message = _(
        "zopra_deleted_translation", default=u"Translation has been deleted."
    )

done = context.deleteEntries(table, [int(autoid)])

if done and sk:
    context.removeTranslationInfo(table, sk)

# dependent-entries handling (tell the main-entry that a dependent multilist entry was removed)
if (
    done
    and request.get("origtable")
    and request.get("origid")
    and request.get("origattribute")
):
    tmainobj = context.tableHandler[table]
    message = u""
    origid = int(request.get("origid"))
    attr = request.get("origattribute")
    otab = request.get("origtable")
    tobj = context.tableHandler[otab]
    orig = tobj.getEntry(origid)
    orig = context.zopra_forceCopy(otab, orig)
    origid = orig.get("autoid")
    # get the multilist object
    mlobj = context.listHandler.getList(otab, attr)
    # if working copies are enabled for this table, get or create the working copy before changing anything
    if context.doesWorkingCopies(otab):
        if not orig.get("iscopyof"):

            # create a copy with iscopyof - attribute (set to original autoid)
            orig["iscopyof"] = orig["autoid"]
            # clear autoid for new entry
            orig["autoid"] = None
            # remove the deleted dependent entry from attr
            orig[attr].remove(autoid)
            # save the copy, get a new autoid
            origid = int(tobj.addEntry(orig))
            # set the autoid in the entry
            orig["autoid"] = origid
            # create a fitting message
            message = _(
                "zopra_delete_dependent_create_wc_success",
                default=u"A dependent entry (${table}) has been deleted. A working copy for the main entry (${maintable} with the original Id ${internal_id}) has been created.",
                mapping={
                    u"table": tmainobj.getLabel(),
                    u"maintable": tobj.getLabel(),
                    u"internal_id": orig.get("iscopyof"),
                },
            )
        else:
            # copy exists, we have it already (forceCopy was called above)
            # directly remove the ref (this does not create any log)
            mlobj.delMLRef(orig["autoid"], autoid)
            # take care of the cache
            if tobj.do_cache:
                tobj.cache.invalidate(orig["autoid"])
            # jump to referring entry
            message = _(
                "zopra_delete_dependent_update_wc_success",
                default=u"A dependent entry (${table}) has been deleted. The working copy for the main entry (${maintable} with the original Id ${internal_id}) has been updated.",
                mapping={
                    u"table": tmainobj.getLabel(),
                    u"maintable": tobj.getLabel(),
                    u"internal_id": orig.get("iscopyof"),
                },
            )
    else:
        # remove the deleted dependent entry from attr
        # directly remove the ref (this does not create any log)
        mlobj.delMLRef(orig["autoid"], autoid)
        # take care of the cache
        if tobj.do_cache:
            tobj.cache.invalidate(orig["autoid"])
        # message deletion and deref
        message = _(
            "zopra_delete_dependent_success",
            default=u"A dependent entry (${table}) has been deleted. The reference from the main entry (${maintable} has been removed.",
            mapping={u"table": tmainobj.getLabel(), u"maintable": tobj.getLabel()},
        )
    # set message
    if message:
        context.plone_utils.addPortalMessage(context.translate(message), "info")
    # jump to message window stating the deletion
    popup = ""
    if zopra_popup:
        popup = "&zopra_popup=1"
    request.RESPONSE.redirect(
        "zopra_table_deleted_dependency?table=%s&autoid=%s%s" % (table, autoid, popup)
    )
    return

if done:
    message = special_message or _(
        "zopra_delete_success", default="Entry has been deleted."
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    # target has been identified and we are not in popup mode
    if targetid and not zopra_popup:
        # jump to edit form of original
        request.RESPONSE.redirect(
            "zopra_table_edit_form?table=%s&autoid=%s" % (table, targetid)
        )
    return state.set(status="success", context=context)
else:
    message = _("zopra_delete_failure", default="Error during deletion.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)
