## Script (Python) "zopra_table_search_export_csv"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table, columns, autoids, REQUEST=None
##title=
##
from zopra.core import zopraMessageFactory as _
request = REQUEST
manager = context
lang = manager.getCurrentLanguage()

encoding = 'utf-8'       # default encoding
delim = u';'             # default delimiter
TE_WITHHEADER  = 0x0004 # include header
TE_LOOKUPDATA  = 0x0008 # resolve foreign keys

flags = TE_WITHHEADER | TE_LOOKUPDATA

tobj = manager.tableHandler[table]

try:
    specials = manager.getGenericConfig(table).get('specials', [])
    # list of csv-like entries
    exportList = tobj.exportCSV( columns, autoids, flags, delim = u';', multilines = 'keep', special_columns = specials )

    # replace the header with the human-readable labels
    coltypes = tobj.getColumnDefs(edit_tracking = True)
    exportList[0] = delim.join([ manager.translate(_(coltypes.get(a, {}).get('LABEL','') or a), domain='zopra', target_language=lang) for a in exportList[0].split(delim) ])

    # set content-type
    request.RESPONSE.setHeader('Content-Type', 'text/plain;;charset=%s' % encoding)

    tlabel = tobj.getLabel(lang)

    # set content-disposition to return a file
    disp = 'attachement; filename="%s.csv"' % tlabel.encode(encoding)
    request.RESPONSE.setHeader( 'Content-disposition', disp)

    # manually prepend BOM for utf-8 recognition in excel and encode the joined list
    result = '\xef\xbb\xbf' + u'\n'.join(exportList).encode(encoding, 'replace')

    # set length
    request.RESPONSE.setHeader('content-length', len(result))

    return result

except Exception, e:
    return "Fehler beim Export: " + str(e)
