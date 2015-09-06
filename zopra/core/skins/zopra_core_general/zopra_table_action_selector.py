## Script (Python) "zopra_table_action_selector"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
req = context.REQUEST
res = req.RESPONSE
table= req.form.get('table', '')
target_template = '/zopra_manager_main_form'
if table:
    key = 'f_%s_intern_' % table

    if req.form.has_key(key + 'create'):
        target_template = '/zopra_table_create_form?table=%s' % table
    elif req.form.has_key(key + 'search'):
        target_template = '/zopra_table_search_form?table=%s' % table
    elif req.form.has_key(key + 'list'):
        target_template = '/zopra_table_search_result?table=%s' % table
    elif req.form.has_key(key + 'import'):
        target_template = '/zopra_table_import_form?table=%s' % table

res.redirect(context.absolute_url() + target_template)
