## Controller Python Script "zopra_table_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, autoid, REQUEST
##title=
##
from zopra.core import zopraMessageFactory as _


request = REQUEST
tobj = context.tableHandler[table]

# get original as blueprint from db
entry = tobj.getEntry(autoid)

# make a backup with permissions (for working copy handling and for update log procedure)
oldentry = context.deepcopy(entry)

# get the new values from the request
copyentry = context.getTableEntryFromRequest(table, request)

# empty bools are disturbing again
# empty lists are disturbing again
# now we have a property with the name to be sure
types = context.tableHandler[table].getColumnTypes()
# get the markers for present special fields
zopra_attr_present = request.get("zopra_attr_present", [])
for attr in types.keys():
    # handling via attr in list is faster for small lists than making a dict
    if attr in zopra_attr_present:
        if types[attr] == "bool":
            if attr not in copyentry:
                copyentry[attr] = 0
        elif types[attr] == "multilist":
            if attr not in copyentry:
                copyentry[attr] = []
        elif types[attr] == "float":
            if attr in copyentry:
                copyentry[attr].replace(",", ".")

# merge new values into the copy, oldentry is retained for checks below
for key in copyentry.keys():
    entry[key] = copyentry[key]

# call prepare_hook
context.prepareDict(table, entry, request)

# call pre_edit_hook
msg = context.actionBeforeEdit(table, entry, request) or ""

# check copy status
if not context.doesWorkingCopies(table):
    # normal update entry
    done = tobj.updateEntry(entry, autoid, orig_entry=oldentry)
    # check translations
    en_msg = ""
    if context.doesTranslations(table):
        # check if there are translations of this entry
        if oldentry.get("language") == context.lang_default and oldentry.get(
            "hastranslation"
        ):
            # updateTranslation also updates the working copy of the translation, if it exists
            translated = context.updateTranslation(table, entry)
            if translated:
                en_msg = _(
                    "zopra_edit_translation_updated",
                    default=u"Non-text fields of the translated version have been saved additionally. ",
                )
        # check if this is a translation (for msg only, action done already)
        elif oldentry.get("language") in context.lang_additional:
            en_msg = _(
                "zopra_edit_translation_saved",
                default=u"Only the text fields have been saved (because this is a translation). ",
            )
    if en_msg:
        en_msg = context.translate(en_msg)
    message = _(
        "zopra_edit_saved",
        default=u"Entry has been updated. ${additional_message} ${translation_message} Internal Id: ${internal_id}.",
        mapping={
            u"internal_id": autoid,
            u"additional_message": msg,
            u"translation_message": en_msg,
        },
    )

elif entry.get("iscopyof"):
    # this already is a working copy, just save it
    done = tobj.updateEntry(entry, autoid, orig_entry=oldentry)
    message = _(
        "zopra_edit_wc_saved",
        default=u"Working copy has been updated. ${additional_message} Original internal Id: ${internal_id}.",
        mapping={u"internal_id": entry.get("iscopyof"), u"additional_message": msg},
    )

else:
    # create a working copy from oldentry (first creating a working copy with no changes for logging
    oldentry["iscopyof"] = entry["autoid"]
    oldentry["autoid"] = None
    autoid = tobj.addEntry(oldentry)
    oldentry["autoid"] = autoid
    # now update the new entry (which was prechecked and prepared above)
    # first change it to look like the working copy
    entry["iscopyof"] = entry["autoid"]
    entry["autoid"] = autoid
    # update it, pass oldentry for diff-log
    done = tobj.updateEntry(entry, int(autoid), orig_entry=oldentry)
    message = _(
        "zopra_edit_wc_created",
        default=u"Working copy created. ${additional_message} Original internal Id: ${internal_id}.",
        mapping={u"internal_id": entry.get("iscopyof"), u"additional_message": msg},
    )
if done == True:
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
else:
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)
