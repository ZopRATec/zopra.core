## Script (Python) "isOldPlone"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
# need metadata proxy role of Manager to access coreVersions
from Products.CMFCore.utils import getToolByName

# check for migration tool
mig = getToolByName(context, 'portal_migration')
if not mig:
    return True
# get core versions
versions = mig.coreVersions()
# check for Plone
if not versions.has_key('Plone'):
    return True
pv = versions['Plone']
if pv.startswith('2.'):
    return True

return False