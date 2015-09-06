## Script (Python) "zopra_testExistance"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=entry=None
##title=Existance Check
##
# no entry -> forward to not_found template
if not entry:
    raise 'EntryNotFound', str(context.REQUEST.get('autoid') or '')
