## Script (Python) "zopra_table_search_export_csv"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table, columns, autoids, REQUEST=None
##title=
##
request = REQUEST
manager = context
lang = manager.getCurrentLanguage()

encoding = 'latin1'       # default encoding
delim = ';'             # default delimiter
TE_WITHHEADER  = 0x0004 # include header
TE_LOOKUPDATA  = 0x0008 # resolve foreign keys

flags = TE_WITHHEADER | TE_LOOKUPDATA


try:

    # list of csv-like entries
    exportList = manager.tableHandler[table].exportCSV( columns, autoids, flags, delim = ';', multilines = 'remove' )

    # replace the header with the human-readable labels
    coltypes = manager.tableHandler[table].getColumnDefs(edit_tracking = True)
    exportList[0] = delim.join([ manager.translate(coltypes.get(a, {}).get('LABEL',''), domain='zopra', target_language=lang) for a in exportList[0].split(delim) ])

    # set proper encoding
    exportList2 = [ line.encode(encoding, 'replace') for line in exportList ]

    # set content-type
    request.RESPONSE.setHeader('Content-Type', 'text/plain;;charset=%s' % encoding)

    # set content-disposition to return a file
    disp = 'attachement; filename="%s.csv"' % table
    request.RESPONSE.setHeader( 'Content-disposition', disp)

    return "\n".join(exportList2)

except Exception, e:
    return "Fehler beim Export: " + str(e)
