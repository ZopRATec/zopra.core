## Script (Python) "zopra_forceCopy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table,entry={},request={}
##title=Existance Check
##
# if the entry is a working copy and force_showcopy is not set in the request, use the original entry instead
if context.doesWorkingCopies(table) and entry and not entry.get("iscopyof"):
    res = context.tableHandler[table].getEntryList(
        constraints={"iscopyof": entry.get("autoid")}
    )
    if res:
        entry = res[0]

return entry
