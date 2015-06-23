############################################################################
#    Copyright (C) 2007 by Ingo Keller                                     #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
############################################################################

from PyHtmlGUI.kernel.hgTable              import hgTable
from PyHtmlGUI.kernel.hgObject             import hgObject
from PyHtmlGUI.widgets.hgLabel             import hgLabel

from zopra.core                            import HTML
from zopra.core.tools.GenericManager       import GenericManager
from zopra.core.dialogs                    import getStdDialog


class DebugInfoManager(GenericManager):
    """\class DebugInfoManager

    This manager is used to analyze the ZopRA framework in depth.
    """
    _className  = 'DebugInfoManager'
    _classType  = GenericManager._classType + [_className]
    meta_type   = _className

    tConnLabel  = hgLabel('<img src="images/t.gif">')
    lConnLabel  = hgLabel('<img src="images/l.gif">')

    def _index_html(self, REQUEST, parent = None):
        """\brief Virtual function for main window on start page."""
        url = self.absolute_url()
        table = hgTable()
        table[0, 0] = hgLabel( 'Session Container',
                               '%s/showSessionContainer' % url )
        return table

    def showSessionContainer(self, REQUEST):
        """\brief Shows the content of the session container."""
        session = REQUEST.SESSION
        url     = self.absolute_url()

        dlg         = getStdDialog()
        dlg.caption = 'Session Container'

        table = hgTable()
        table[0, 0] = hgLabel(session)

        table[1, 0] = hgLabel('is valid')
        table[1, 1] = hgLabel(session.isValid())

        table[2, 0] = hgLabel('last access')
        table[2, 1] = hgLabel(session.getLastAccessed())
        table[2, 2] = hgLabel('last modified')
        table[2, 3] = hgLabel(session.getLastModified())

        index = 3
        for item in session.keys():
            table[index, 0] = item
            table[index, 1] = session.get(item)
            if ( isinstance(session.get(item), hgObject) ):
                table[index, 2] = hgLabel('object',
                                          '%s/showObject?id=%s' % ( url,
                                                                    item ) )
                table[index, 3] = hgLabel('object tree',
                                          '%s/showObjectTree?id=%s' % ( url,
                                                                        item ) )
            index          += 1

        table.setCellSpanning(0, 0, 1, 4)
        dlg.add(table)
        return HTML(dlg.getHtml())(self, None)


    def showObject(self, REQUEST, id):
        """\brief Shows the content of the session container."""
        session = REQUEST.SESSION
        url     = self.absolute_url()
        obj     = session.get(id)

        dlg         = getStdDialog()
        dlg.caption = 'Object'

        if obj is None:
            dlg.add('No object with id %s.' % id)
            return HTML(dlg.getHtml())(self, None)

        typeList = [type(1), type(0.0), type(""), type([]), type({}), type(())]

        table = hgTable()
        index = 0
        for item in dir(obj):
            if obj is None:
                print item
            attrType        = type( getattr(obj, item) )
            table[index, 0] = item
            table[index, 1] = str(attrType).replace('<', '').replace('>', '')
            if (attrType in typeList and item != '__dict__'):
                table[index, 2] = str(getattr(obj, item)).replace('<', '').replace('>', '')
            index += 1

        dlg.add(table)
        return HTML(dlg.getHtml())(self, None)


    def showObjectTree(self, REQUEST, id):
        """\brief Shows the content of the session container."""
        session = REQUEST.SESSION
        url     = self.absolute_url()
        obj     = session.get(id)

        dlg         = getStdDialog()
        dlg.caption = 'Object Tree'

        if obj is None:
            dlg.add('No object with id %s.' % id)
            return HTML(dlg.getHtml())(self, None)

        dlg.add( self.displayObjectTreeNode(obj) )
        return HTML(dlg.getHtml())(self, None)


    def displayObjectTreeNode(self, obj, lvl = 0):

        table = hgTable()
        label = 'CL[%s] NAME[%s] ID[%s]' % ( obj._className, obj.name, id(obj) )
        table[0, 0] = label
        table.setCellAlignment(0, 0, table.ALIGN_CENTER, table.ALIGN_TOP)

        if obj.childObjects:
            center = table.ALIGN_CENTER
            top    = table.ALIGN_TOP
            for idx, child in obj.childObjects:
                index = idx + 1
                table[index, 1] = DebugInfoManager.tConnLabel
                table[index, 2] = self.displayObjectTreeNode(child, lvl + 1)
                table.setCellAlignment(index, 1, center, top)
                table.setCellAlignment(index, 2, center, top)
            table[index - 1, 1] = DebugInfoManager.lConnLabel
            table.setCellAlignment(index - 1, 1, center, top)

        return table
