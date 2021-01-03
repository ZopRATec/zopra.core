## Controller Python Script "zopra_list_edit_add"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=listname, new_value='', new_rank=None
##title=
##
# coding: utf-8
from zopra.core import zopraMessageFactory as _


if not new_value:
    message = _("zopra_list_edit_nothing", default=u"Nothing changed.")
    context.plone_utils.addPortalMessage(context.translate(message), "info")
    return state.set(status="success", context=context)
lobj = context.listHandler[listname]
request = context.REQUEST
kwargs = {}
for translation in lobj.translations:
    key = "new_value_" + translation
    if request.form.has_key(key):
        kwargs["value_" + translation] = request.form.get(key)
lobj.addValue(new_value, "", new_rank, **kwargs)
message = _("zopra_list_edit_added", default=u"Created entry.")
context.plone_utils.addPortalMessage(context.translate(message), "info")
return state.set(status="success", context=context)
