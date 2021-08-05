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
doubles = []
tobj = context.tableHandler[tablename]
lobj = context.listHandler[listname]
url = context.getParentNode().absolute_url()

# get all entries of all doubleids
if not doubleid:
    message = _("zopra_list_unifier_param_error", default="Double list entry IDs are missing.")
    context.plone_utils.addPortalMessage(context.translate(message), "error")
    context.REQUEST.RESPONSE.redirect(
        url + "/zopra_main_form
    )
else:
    doubles = tobj.getEntryList(constraints={listname: doubleid})

if not doubles:
    message = _("zopra_list_unifier_no_table_entries", default="No table entries found for the double list entries.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    # don't return yet, we want to remove the double list entries anyway

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

    message = _("zopra_list_unifier_entries_corrected",
                default="Attribute ${attr} has been corrected in ${count} table entries.",
                mapping={"attr": listname, "count": len(doubles)})
    context.plone_utils.addPortalMessage(context.translate(message), "info")

)
# doublecheck that no entries are left
check = tobj.getEntryList(constraints={listname: doubleid})
if check:
    message = _("zopra_list_unifier_unchanged_table_entries", default="Problem: Some entries seem to have not been corrected.")
    context.plone_utils.addPortalMessage(context.translate(message), "error")

else:
    # remove the double values
    for autoid in doubleid:
        lobj.delValue(autoid)
    msgs.append("Markierte Listeneintraege wurden entfernt.")
    message = _("zopra_list_unifier_done", default="The marked list entries have been removed.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")

context.REQUEST.RESPONSE.redirect(
    url + "/zopra_main_form"
)
