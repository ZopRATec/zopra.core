## Script (Python) "zopra_testExistence"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=entry=None
##title=Existance Check
##
from zExceptions import Redirect

from zopra.core import zopraMessageFactory as _


if not entry:
    # set a message
    msg = _(
        "zopra_entry_notfound",
        default=u"The requested entry was not found or no id was given.",
    )
    context.plone_utils.addPortalMessage(context.translate(msg), "info")
    # forward to context (because not-found-display is a bit unfitting)
    raise Redirect(context.absolute_url())
