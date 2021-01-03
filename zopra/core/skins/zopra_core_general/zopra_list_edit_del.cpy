## Controller Python Script "zopra_list_edit_del"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=listname, edit_autoid=[]
##title=
##
# coding: utf-8
from zopra.core import zopraMessageFactory as _


request = context.REQUEST
if not edit_autoid:
    message = _("zopra_list_edit_nothing", default=u"Nothing changed.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
if not same_type(edit_autoid, []):
    edit_autoid = [edit_autoid]
lobj = context.listHandler[listname]
done = False
for oneid in edit_autoid:
    lobj.delValue(int(oneid))
    done = True

if done:
    message = _("zopra_lsit_edit_deleted", default=u"Deleted entries.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
else:
    message = _("zopra_list_edit_nothing", default=u"Nothing changed.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
