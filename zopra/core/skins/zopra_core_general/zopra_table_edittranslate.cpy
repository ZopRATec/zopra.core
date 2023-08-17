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

if not context.doesTranslations(table):
    message = _(
        "zopra_translation_not_supported",
        default=u"This table does not support translations. Translation process was cancelled.",
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)

# for now, we just create an english version with all original values, if it does not exist and update the orginal entry (hastranslation)
origentry = context.tableHandler[table].getEntry(autoid)

if not origentry:
    message = _(
        "zopra_translation_orig_not_found",
        default=u"Original entry could not be found. Translation process was cancelled.",
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)

if origentry.get("hastranslation"):
    message = _(
        "zopra_translation_exists",
        default=u"Translation exists already. The translation process has been cancelled.",
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)

target_language = context.selectAdditionalLanguage(request)
if not target_language:
    message = _(
        "zopra_translation_language_unknown",
        default=u"Requested language unknown. The translation process has been cancelled.",
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="failure", context=context)

# use original entry if translating a working copy
origentry = context.zopra_forceOriginal(table, origentry)

# create translation
entry = {}
for key in origentry.keys():
    entry[key] = origentry[key]

entry["istranslationof"] = origentry["autoid"]

entry["language"] = target_language
entry["iscopyof"] = "NULL"

# save entry
entry["autoid"] = None

# add to database
newautoid = context.tableHandler[table].addEntry(entry)

# update orginal entry
origentry["hastranslation"] = 1
# just to be safe, set lang_default in orig entry
origentry["language"] = context.lang_default
context.tableHandler[table].updateEntry(origentry, origentry["autoid"])

# overwrite in request for formcontroller traversal
request.form["autoid"] = newautoid
request.other["autoid"] = newautoid
message = _(
    "zopra_translation_created",
    default=u"Translation created. Translation Id: ${translation_id}",
    mapping={u"translation_id": newautoid},
)
context.plone_utils.addPortalMessage(context.translate(message), "info")
return state.set(status="success", context=context)
