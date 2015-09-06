## Script (Python) "path2ob"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=path=""
##title=Utility Script
##
# use path to navigate to object starting in context
paths = path.split('/')
step = context
try:
    for onepath in paths:
        if onepath in ['Sites', 'TUD']:
            continue
        if onepath:
            step = getattr(step, onepath)
except:
    return None

return step