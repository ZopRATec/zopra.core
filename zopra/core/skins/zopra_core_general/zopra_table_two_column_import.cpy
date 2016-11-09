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

request = context.REQUEST
request.RESPONSE.setHeader('Content-Type','text/html;;charset=utf8')
msg = ""

# constants
linebreak = '\r\n'
quotchar = '\"'
delim = unicode(delim,'unicode-escape')
manager = context.app.infoapp
tobj = manager.tableHandler[table]
coltypes = tobj.getColumnDefs(True)
cols = coltypes.keys()

data = file.read()
if len(data) == 0:
    state.setError('', 'CVS: Keine CSV-Datei hochgeladen.', 'no_csv_file')
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure',context=context)
try:
    data = data.decode(encoding).encode('utf8')
except UnicodeDecodeError, e:
    state.setError('', 'CVS: Konnte Kodierung (%s) nicht anwenden (%s)' % (encoding, e), 'csv_parse_error_wrong_encoding')
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure',context=context)
except LookupError, e:
    state.setError('', 'CVS: Konnte Kodierung (%s) nicht finden' % (encoding), 'csv_parse_error_encoding_not_found')
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure',context=context)

# parses simple two-column CSV
# e.g.: header  :      "autoid", "attribute_name_or_label"
#       content :           123, "abc"
#                           999, "multiline-
#                                 string"
lines = data.splitlines()

try:
    parsedLines = manager.csv_read(lines, delim = str(delim))
except Exception, e:
    state.setError('', 'CVS: Fehler beim Verarbeiten (Error:  %s)' % (e), 'csv_parse_error')
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure',context=context)

header, content = parsedLines[:1][0], parsedLines[1:]

# check that 2 cols are present
if not len(header) > 1:
    state.setError('', 'CVS: Delimiter scheint falsch oder nicht genügend Spalten vorhanden.', 'csv_parse_error_header_too_short')
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure',context=context)

attribute = None
# determine attribute
for col in cols:
    if header[1].lower() in (col.lower(), coltypes[col]['LABEL'].lower()):
        attribute = col
        break
if attribute == None:
    state.setError('', 'CSV: \'' + header[1] + '\' ist kein Attribut der Tabelle \''+table+'\'.', 'csv_parse_error_head_attribute_not_found')
    context.plone_utils.addPortalMessage('Please correct the indicated errors.', 'info')
    return state.set(status='failure',context=context)

# construct new values
context.plone_utils.addPortalMessage(u"Einträge wurden erfolgreich aktualisiert:", 'info')
for c in content:
    autoid = c[0]
    value = c[1]
    entry_diff = { 'autoid': autoid, attribute: value }
    tobj.updateEntry(entry_diff, autoid)
    msg = u"- Originaleintrag mit autoid: %s " % str(autoid)
    if manager.doesWorkingCopies(table) and manager.updateWorkingCopy(table, entry_diff):
        msg = msg + u" +Arbeitskopie"
    if manager.doesTranslations(table) and manager.updateTranslation(table, entry_diff):
        msg = msg + u" +Sprachkopie"
    context.plone_utils.addPortalMessage(msg, 'info')
return state.set(status='success', context=context)
