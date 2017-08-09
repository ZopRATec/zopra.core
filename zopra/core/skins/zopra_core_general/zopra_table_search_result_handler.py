## Script (Python) "zopra_table_search_export_csv"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table,columns,order,cons_key=[]
##title=
##
request = context.REQUEST
manager = context
buttons = manager.getGenericConfig(table).get('ownButtonActions')

# preparation for when we have checkboxes in the list again
autoids = request.get('checked_ids')
if not autoids:
    # no selection -> rebuild constraints from the lists cons_key and corresponding value fields
    cons = {}
    for key in cons_key:
        cons[key] = request.get(key+'_values')
        # TODO: check if this is necessary and make it go away
        if cons[key] == 'False':                # converting string form values
            cons[key] = 0
        if cons[key] == 'True':
            cons[key] = 1
    # TODO: this might not work for subtable constraints -> make it work (ERP Positions)
    autoids = manager.tableHandler[table].getEntryAutoidList(constraints = cons, order = order)

if request.get('form.button.Export'):
    return manager.zopra_table_search_result_export_csv(table, columns, autoids, request)
else:
    for button in buttons:
        if request.get(button['id']):
            # found the pressed button
            target = button.get('target')
            target_func = getattr(manager, target)
            # call target function with table, list of selected columns, current order column and list of constraint keys (with corresponding values in the request)
            return target_func(table, columns, autoids, request)
# nothing found
return 'No target found. Something wrong.'
