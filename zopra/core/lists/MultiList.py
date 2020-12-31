from PyHtmlGUI import E_PARAM_TYPE
from PyHtmlGUI.widgets.hgLabel import hgLabel
from PyHtmlGUI.widgets.hgPushButton import hgPushButton
from zopra.core import ZC
from zopra.core.lists.ForeignList import ForeignList


class MultiList(ForeignList):
    """ Multilist Class - Data handling for multi-selection lists."""

    _className = 'MultiList'
    _classType = ForeignList._classType + [_className]
    listtype = 'multilist'

    def __init__( self,
                  listname,
                  manager  = None,
                  function = None,
                  table    = None,
                  label    = '',
                  map      = None,
                  docache  = True ):
        """\brief Constructs a MultiList
        """
        ForeignList.__init__( self,
                              listname,
                              manager,
                              function,
                              label )

        self.enableCache = docache

        self.map = map
        self.table = table

        # we cannot init this now, since we cannot use getManager() at this point
        # NOTE: getManager() only works if list has been retrieved via getattr() from listHandler
        #       (wrapped by listHandler[])
        self.dbname = None

    # NOTE: cannot be done as property that inits on first call
    #       since property works as decorator that binds on 'compile' time
    #       where (again) getManager() is not functional yet
    # TODO: find a better way
    def initDBName(self):
        """Get database name"""

        if self.dbname:
            return self.dbname

        mgr = self.getManager()

        if self.map:
            self.dbname = '%smulti%s' \
                          % ( mgr.getId(),
                              self.map,
                              )
        else:
            self.dbname = '%smulti%s%s' \
                          % ( mgr.getId(),
                              self.table,
                              self.listname
                              )

        return self.dbname

    def createTable(self):
        """Create the database table."""

        # try to create the list
        mgr = self.getManager()
        m_product = mgr.getManager(ZC.ZM_PM)

        table_dict = {'tableid': {ZC.COL_TYPE: ZC.ZCOL_INT},
                      self.listname: {ZC.COL_TYPE: ZC.ZCOL_INT},
                      'notes': {ZC.COL_TYPE: ZC.ZCOL_STRING}
                      }

        m_product.addTable(self.dbname, table_dict, edit_tracking=False)

    def deleteTable(self, omit_log=None):
        """Delete the database table."""

        mgr       = self.getManager()
        m_product = mgr.getManager(ZC.ZM_PM)
        log       = True

        for ident in omit_log:
            if ident in mgr.getClassType():
                log = False

        m_product.delTable( self.dbname, log )

    def getMLRef(self, tableid=None, listid=None):
        """Returns the notes-entry of the multilist entry specified by tableid / listid."""
        mgr = self.getManager()

        if tableid:
            id1     = tableid
            id1name = 'tableid'
            id2name = self.listname
        elif listid:
            id1     = listid
            id1name = self.listname
            id2name = 'tableid'
        else:
            return []
        query = 'Select %s from %s where %s = %s' % ( id2name,
                                                      self.dbname,
                                                      id1name,
                                                      id1
                                                      )
        # try same container first and then up the hierarchy
        pm = mgr.getManager(ZC.ZM_PM) or mgr.getHierarchyUpManager(ZC.ZM_PM)
        result = pm.executeDBQuery(query)
        return [entry[0] for entry in result]

    def updateMLNotes(self, tableid, listid, notes):
        """ change the notes of one entry"""
        mgr = self.getManager()

        if not tableid or not listid:
            return False
        # replace None or empty list with empty string
        if not notes:
            notes = ''
        if notes is None:
            notes = ''

        # escape notes
        notes = notes.replace( "\'", "\\\'" ).replace( "\\\\'", "\\\'")
        query = "Update %s set notes = '%s' where tableid = %s and %s = %s"
        query = query % (self.dbname,
                         notes,
                         tableid,
                         self.listname,
                         listid)

        mgr.getManager(ZC.ZM_PM).executeDBQuery(query)
        return True

    def getMLNotes(self, tableid, listid):
        """Returns the notes-entry of the multilist entry specified by tableid / listid."""
        mgr = self.getManager()

        if not tableid or not listid:
            return ''
        query = 'Select notes from %s where tableid = %s and %s = %s'
        query = query % (self.dbname,
                         tableid,
                         self.listname,
                         listid)

        result = mgr.getManager(ZC.ZM_PM).executeDBQuery(query)
        if result:
            # make sure we return empty string if result is an empty item
            return result[0][0] or ''
        else:
            return ''

    def delMLRef(self, tableid=None, listid=None):
        """Deletes all rows in table 'multi'+list_name with matching tableid."""
        mgr = self.getManager()

        if tableid and listid:
            query = 'Delete from %s where tableid = %s and %s = %s'
            query = query % ( self.dbname, int(tableid), self.listname, int(listid))
        elif tableid:
            query = 'Delete from %s where tableid = %s'
            query = query % ( self.dbname, int(tableid) )
        elif listid:
            query = 'Delete from %s where %s = %s'
            query = query % ( self.dbname, self.listname, int(listid) )
        else:
            return

        mgr.getManager(ZC.ZM_PM).executeDBQuery(query)

    def addMLRef(self, tableid, value, notes=None):
        """inserts a row with given tableid and value in table 'multi'+list_name"""
        assert value, E_PARAM_TYPE % (ZC.VALUE, 'not None value for %s' % self.listname, value )
        mgr = self.getManager()

        try:
            int(value)
        except ValueError:
            return

        if not notes:
            notes = ''
        query = 'Insert into %s (tableid, %s, notes) values (%s,%s,%s)'
        query = query % (self.dbname,
                         self.listname,
                         tableid,
                         mgr.forwardCheckType(value, 'int', False, 'Value'),
                         mgr.forwardCheckType(notes, 'string', False, 'Notes')
                         )
        return mgr.getManager(ZC.ZM_PM).executeDBQuery(query)

    # overwritten to allow creation of multilisttable
    def getViewTabDialog(self, REQUEST):
        """List overview tab."""
        message = ''
        # check request for create_multilist_table
        if REQUEST.get('create_multilist_table'):
            # create the multilisttable
            self.createTable()

            message = 'Created Multilisttable in database.'

        dlg = ForeignList.getViewTabDialog(self, REQUEST)

        if message:
            # add message
            dlg.add(hgLabel(message, parent = dlg))

        # check for multilisttable
        try:
            # try to fetch a value from it
            self.getMLRef(1)
        except Exception:
            # error -> dbmultitable missing?
            dlg.add(hgLabel('<font color="red">Multitable not found in DB!</font>', parent = dlg))
            # add create button
            dlg.add(hgPushButton('Create Multitable', 'create_multilist_table', parent = dlg))
        return dlg
