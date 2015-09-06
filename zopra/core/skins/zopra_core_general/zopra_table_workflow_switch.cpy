## Controller Python Script "zopra_table_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=table, autoid, REQUEST
##title=
##
request = REQUEST
wfreq = [1,2,3]
num = 0
for id in wfreq:
    if request.get('form.button.ChangeWorkflowState' + str(id)):
        num = id

if num:

    entry = context.tableHandler[table].getEntry(autoid)
    infos = context.getStateTransferInfo(table, entry)
    info = infos[num - 1]

    action = info.get('action')
    if action:
        executable = getattr(context, action)
        executable(table, entry, info, request)

else:
    raise ValueError('Error in Workflow Transition Determination. Contact Administrator.')
#if done == True:
#    return state.set(status='success', context=context , portal_status_message = message)
#elif done == False:
#    return state.set(status='failure', context=context, portal_status_message=done)
