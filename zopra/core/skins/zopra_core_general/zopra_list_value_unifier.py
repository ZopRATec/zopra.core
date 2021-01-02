## Python Script "zopra_list_value_unifier"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=tablename, listname, origid, doubleid=[]
##title=
##
doubleid = [int(a) for a in doubleid]
msgs = []
doubles = []
tobj = context.tableHandler[tablename]
lobj = context.listHandler[listname]

# get all entries of all doubleids
if not doubleid:
    msgs.append("Ids der doppelten Listeneintraege fehlen.")
    context.REQUEST.RESPONSE.redirect(
        url + "/zopra_main_form?portal_status_message=" + "<br />".join(msgs)
    )
else:
    doubles = tobj.getEntryList(constraints={listname: doubleid})

if not doubles:
    msgs.append("Keine Tabelleneintraege zu den doppelten Listeneintraegen gefunden.")
    # no need to jump back, we want to remove the double list entries anyway

# check type of attribute
types = tobj.getColumnTypes()
# TODO: extra handling for diverging listname/attributename structures and for multi-usage lists
attr_name = listname
attr_type = types.get(attr_name)

for double in doubles:
    # set origid in the entries
    if attr_type in ("multilist", "hierarchylist"):
        attr_value = double[attr_name]
        for item in attr_value:
            if item in doubleid:
                attr_value.remove(item)
        attr_value.append(origid)
    elif attr_type == "singlelist":
        double[attr_name] = origid
    # update
    tobj.updateEntry(double, double["autoid"])

msgs.append(
    "Attribut %s wurde in %s Tabelleneintraegen korrigiert." % (listname, len(doubles))
)
# doublecheck that no entries are left
check = tobj.getEntryList(constraints={listname: doubleid})
if check:
    msgs.append("Problem: Einige Eintraege scheinen nicht korrigiert worden zu sein.")

else:
    # remove the double values
    for autoid in doubleid:
        lobj.delValue(autoid)
    msgs.append("Markierte Listeneintraege wurden entfernt.")

url = context.getParentNode().absolute_url()
context.REQUEST.RESPONSE.redirect(
    url + "/zopra_main_form?portal_status_message=" + "<br />".join(msgs)
)
