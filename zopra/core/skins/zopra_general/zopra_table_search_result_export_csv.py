## Script (Python) "zopra_table_search_export_csv"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table,columnList,order,cons_key=[]
##title=
##

request = context.REQUEST
manager = context

encoding = 'latin1'       # default encoding
delim = ';'             # default delimiter
TE_WITHHEADER  = 0x0004 # include header
TE_LOOKUPDATA  = 0x0008 # resolve foreign keys

flags = TE_WITHHEADER | TE_LOOKUPDATA

# rebuild constraints from the lists cons_key and corresponding value fields
cons = {}
for key in cons_key:
    cons[key] = request.get(key+'_values')
    if cons[key] == 'False':                # converting string form values
        cons[key] = 0
    if cons[key] == 'True':
        cons[key] = 1
    
try:  
  autoList = manager.tableHandler[table].getEntryAutoidList(constraints = cons, order = order)

  # list of csv-like entries
  exportList = manager.tableHandler[table].exportCSV( columnList, autoList, flags, delim = ';', multilines = 'remove' )

  # replace the header with the human-readable labels
  coltypes = manager.tableHandler[table].getColumnDefs()
  exportList[0] = delim.join([ coltypes.get(a, {}).get('LABEL','') for a in exportList[0].split(delim) ])

  # set proper encoding and replace null values
  # FIXME: None-Replacement should be done in exportCSV, not afterwards
  exportList2 = [ line.encode(encoding, 'replace').replace('None','') for line in exportList ]

  # set content-type
  request.RESPONSE.setHeader('Content-Type', 'text/plain;;charset=%s' % encoding)

  # set content-disposition to return a file
  disp = 'attachement; filename="%s.csv"' % table
  request.RESPONSE.setHeader( 'Content-disposition', disp)

  return "\n".join(exportList2)

except Exception, e:
    return "Fehler beim Export: " + str(e)
