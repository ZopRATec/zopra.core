## Script (Python) "zopra_testExistance"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table, entry={},request={}
##title=Existance Check
##
# if the entry is a working copy and force_showcopy is not set in the request, use the original entry instead
if context.doesWorkingCopies(table):
    orig = entry.get('iscopyof')
    if orig and not request.get('force_showcopy'):
        entry = context.tableHandler[table].getEntry(orig)

# FIXME: language check should be build in here as well as soon as translated versions are available

return entry