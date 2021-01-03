## Controller Python Script "zopra_table_two_column_import"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, file, encoding, delim
##title=
##
import logging

from zopra.core import zopraMessageFactory as _


logger = logging.getLogger("import")
request = context.REQUEST

# constants
# csv parser cannot operate on unicde, do not translate the delim
# delim = unicode(delim,'unicode-escape')
manager = context
tobj = manager.tableHandler[table]
coltypes = tobj.getColumnDefs(True)
cols = coltypes.keys()
error_message = context.translate(
    _("zopra_form_errors", default="Please correct the indicated errors.")
)
# read data
data = file.read()
if len(data) == 0:
    message = _("zopra_twocol_import_no_csv", default=u"CSV: No file uploaded.")
    state.setError("", manager.translate(message, domain="zopra"), "no_csv_file")
    context.plone_utils.addPortalMessage(error_message, "info")
    return state.set(status="failure", context=context)
try:
    data = data.decode(encoding).encode("utf8")
except UnicodeDecodeError, e:
    message = _(
        "zopra_twocol_import_encoding_error",
        default=u"CSV: Could not decode the file with the given encoding.",
    )
    state.setError(
        "", manager.translate(message, domain="zopra"), "csv_parse_error_wrong_encoding"
    )
    context.plone_utils.addPortalMessage(error_message, "info")
    return state.set(status="failure", context=context)
except LookupError, e:
    message = _("zopra_twocol_import_no_encoding", default=u"CSV: Unknown encoding.")
    state.setError(
        "",
        manager.translate(message, domain="zopra"),
        "csv_parse_error_encoding_not_found",
    )
    context.plone_utils.addPortalMessage(error_message, "info")
    return state.set(status="failure", context=context)
# parses simple two-column CSV
# e.g.: header  :      "autoid", "attribute_name_or_label"
#       content :           123, "abc"
#                           999, "multiline-
#                                 string"
lines = data.splitlines()
try:
    parsedLines = manager.csv_read(lines, delim=delim)
except Exception, e:
    error = _(
        "zopra_twocol_import_cvs_error",
        default=u"CSV: Error during CSV parsing (Error:  ${error})",
        mapping={"error": unicode(e)},
    )
    state.setError("", context.translate(error, domain="zopra"), "csv_parse_error")
    context.plone_utils.addPortalMessage(error_message, "info")
    return state.set(status="failure", context=context)
# separate header / content
header, content = parsedLines[:1][0], parsedLines[1:]
# check that 2 cols are present
if not len(header) > 1:
    error = _(
        "zopra_twocol_import_content_error",
        default=u"CSV: Delimiter wrong or not enough columns found.",
    )
    state.setError("", context.translate(error), "csv_parse_error_header_too_short")
    context.plone_utils.addPortalMessage(error_message, "info")
    return state.set(status="failure", context=context)

attribute = None
# determine attribute
for col in cols:
    # check for column name and column label
    if header[1].lower() in (col.lower(), coltypes[col]["LABEL"].lower()):
        attribute = col
        break
if attribute == None:
    error = _(
        "zopra_twocol_import_attribute_error",
        default=u"CSV: '${attribute}' is not an attribute (or label of an attribute) of table '${table}'.",
        mapping={"attribute": header[1], "table": table},
    )
    state.setError(
        "", context.translate(error), "csv_parse_error_head_attribute_not_found"
    )
    context.plone_utils.addPortalMessage(error_message, "info")
    return state.set(status="failure", context=context)

# construct new values
message = _(
    "zopra_twocol_import_count",
    default=u"Import of ${count} data sets for column ${attribute}:",
    mapping={"count": len(content), "attribute": attribute},
)
context.plone_utils.addPortalMessage(context.translate(message), "info")
done = 0
for index, c in enumerate(content):
    autoid = c[0]
    value = c[1]
    entry_diff = {"autoid": autoid, attribute: value}
    if not autoid:
        message = _(
            "zopra_twocol_import_autoid_missing",
            u"Autoid missing on line ${line}.",
            mapping={"line": index + 1},
        )
        context.plone_utils.addPortalMessage(context.translate(message), "info")
        continue
    # check entry exists
    entry = tobj.getEntry(autoid)
    if not entry:
        message = _(
            "zopra_twocol_import_entry_missing",
            u"Entry not found for autoid ${autoid} on line ${line}",
            mapping={"autoid": autoid, "line": index + 1},
        )
        context.plone_utils.addPortalMessage(context.translate(message), "info")
        continue
    logger.info("Updating %s with %s" % (autoid, value))
    tobj.updateEntry(entry_diff, autoid)
    done += 1
    wc = ""
    tr = ""
    if manager.doesWorkingCopies(table) and manager.updateWorkingCopy(
        table, entry_diff
    ):
        wc = context.translate(
            _("zopra_twocol_import_workingcopy", default=u" + working copy")
        )
    if manager.doesTranslations(table) and manager.updateTranslation(table, entry_diff):
        tr = context.translate(
            _("zopra_twocol_import_translation", default=u" + translation copy")
        )
    message = _(
        "zopra_twocol_import_entry_saved",
        u"- original entry (autoid: ${autoid})${wc}${tr}",
        mapping={"autoid": autoid, "wc": wc, "tr": tr},
    )
    context.plone_utils.addPortalMessage(context.translate(message), "info")
message = _(
    "zopra_twocol_import_success",
    default=u"${count} entries have been updated.",
    mapping={"count": done},
)
context.plone_utils.addPortalMessage(context.translate(message), "info")
return state.set(status="success", context=context)
