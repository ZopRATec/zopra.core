## Controller Python Script "zopra_table_create"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, zopra_popup=None
##title=
##
# coding: utf-8
from zopra.core import zopraMessageFactory as _

request = context.REQUEST

entry = context.getTableEntryFromRequest(table, request)
# set initial language
if context.doesTranslations(table):
    entry["language"] = context.lang_default

# call prepare_hook
context.prepareDict(table, entry, request)
# call pre_add_hook
context.actionBeforeAdd(table, entry, request)

# add entry
tmainobj = context.tableHandler[table]
autoid = tmainobj.addEntry(entry)
entry["autoid"] = autoid

# add repeatable fields
autoidlist = [str(autoid)]
if request.has_key("repeats") and request["repeats"] > 1:
    fieldsets = context.getLayoutInfo(table, "create")
    # get repeatable fields
    r_fields = []
    for element in fieldsets:
        if element.has_key("repeatfields"):
            r_fields.extend(element["repeatfields"])

    for i in range(2, int(request["repeats"]) + 1):
        add = False
        for field in r_fields:
            if request.has_key(field + "_" + str(i)) and request[field + "_" + str(i)]:
                entry[field] = request[field + "_" + str(i)]
                add = True
        if add:
            entry["autoid"] = ""
            autoidlist.append(str(tmainobj.addEntry(entry)))
    # TODO: postprocessing for repeated entries is missing!

# call postprocessing for original entry
msg = context.actionAfterAdd(table, entry, request) or ""

# dependent-entries handling (tell the main-entry that it has a new dependent multilist entry)
if request.get("origtable") and request.get("origid") and request.get("origattribute"):
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
            # add the new dependent entry
            orig[attr].append(autoid)
            # save the copy, get a new autoid
            origid = int(tobj.addEntry(orig))
            # set the autoid in the entry
            orig["autoid"] = origid
            # create a fitting message
            message = _(
                "zopra_create_dependent_create_wc_success",
                default=u"A new entry (${table}) has been created and referenced. A working copy for the main entry (${maintable} with the original Id ${internal_id}) has been created as well.",
                mapping={
                    u"table": tmainobj.getLabel(),
                    u"maintable": tobj.getLabel(),
                    u"internal_id": orig.get("iscopyof"),
                },
            )

        else:
            # copy exists, we have it already (forceCopy was called above)
            # directly add the ref (this does not create any log)
            mlobj.addMLRef(orig["autoid"], autoid)
            # take care of the cache
            if tobj.do_cache:
                tobj.cache.invalidate(orig["autoid"])
            # jump to referring entry
            message = _(
                "zopra_create_dependent_update_wc_success",
                default=u"A new entry (${table}) has been created and referenced. The working copy for the main entry (${maintable} with the original Id ${internal_id}) has been updated.",
                mapping={
                    u"table": tmainobj.getLabel(),
                    u"maintable": tobj.getLabel(),
                    u"internal_id": orig.get("iscopyof"),
                },
            )
    else:
        # directly add the ref (this does not create any log)
        mlobj.addMLRef(orig["autoid"], autoid)
        # take care of the cache
        if tobj.do_cache:
            tobj.cache.invalidate(orig["autoid"])
        # message creation and ref
        message = _(
            "zopra_create_dependent_success",
            default=u"A new entry (${table}) has been created and referenced by the main entry (${maintable}",
            mapping={u"table": tmainobj.getLabel(), u"maintable": tobj.getLabel()},
        )
    # set message
    if message:
        context.plone_utils.addPortalMessage(context.translate(message), "info")
    # jump to message window stating the creation
    popup = ""
    if zopra_popup:
        popup = "&zopra_popup=1"
    request.RESPONSE.redirect(
        "zopra_table_created_dependency?table=%s&autoid=%s%s" % (table, autoid, popup)
    )
    return

# overwrite in request for formcontroller traversal
request.form["autoid"] = autoid
request.other["autoid"] = autoid
if request.form.has_key("form.submitted"):
    del request.form["form.submitted"]

if len(autoidlist) > 1:
    request.form["autoidlist"] = autoidlist
    message = _(
        "zopra_create_new_entries",
        default=u"New entries have been created. ${additional_message}Internal Ids: ${internal_ids}.",
        mapping={u"internal_ids": ", ".join(autoidlist), u"additional_message": msg},
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
else:
    message = _(
        "zopra_create_new_entry",
        default=u"New entry has been created. ${additional_message}Internal Id: ${internal_id}.",
        mapping={u"internal_id": autoid, u"additional_message": msg},
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
