############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

import os
import os.path as op
import string
from types      import ListType


from PyHtmlGUI.kernel.hgTable           import hgTable
from PyHtmlGUI.widgets.hgLabel          import hgLabel,         \
                                               hgNEWLINE,       \
                                               hgSPACE,         \
                                               hgProperty
from PyHtmlGUI.widgets.hgTextEdit       import hgTextEdit
from PyHtmlGUI.widgets.hgCheckBox       import hgCheckBox

from zopra.core                         import HTML, ZC
from zopra.core.tools.GenericManager    import GenericManager

from zopra.core.dialogs                 import getStdDialog

from zopra.core.tools.managers          import TCN_IMAGEID,   \
                                               TCN_NAME,      \
                                               TCN_ALT,       \
                                               TCN_DESCR,     \
                                               TCN_PATH,      \
                                               TCN_TYPE,      \
                                               TN_IMAGE

from zopra.core.elements.Buttons        import BTN_L_ADD,        \
                                               BTN_L_DELETE,     \
                                               BTN_L_RESET2,     \
                                               mpfAddButton,     \
                                               mpfDeleteButton,  \
                                               mpfResetButton,   \
                                               mpfReset2Button
from zopra.core.widgets                 import dlgLabel
from zopra.core.utils.PersistentCache   import PersistentCache

FILE_ERROR = 'File not found.'


class FileManager(GenericManager):
    """ File Manager """

    _className  = ZC.ZM_IM
    # the 'ZMOMTool' entry in the classType has a meaning, tools are not shown somewhere
    # don't know why and where :/
    _classType  = GenericManager._classType + [_className, 'ZMOMTool']
    meta_type   = _className

    _properties = GenericManager._properties + (
            {'id': 'cache_size',    'type': 'int',     'mode': 'w'},
            {'id': 'base_path',     'type': 'string',  'mode': 'w'},
        )

    cache_size      = 20

    _generic_config = {}
    _generic_config[TN_IMAGE] = { 'show_fields': [ TCN_NAME,
                                                   TCN_ALT,
                                                   TCN_DESCR ] }


    def prepareDelete( self,
                       table,
                       id,
                       REQUEST = None ):
        """\brief Deletes Entries"""
        if table == TN_IMAGE:
            image = self.getImage(id)

            # if path: delete the file on disk
            if image and image.get(TCN_PATH):
                path = image.get(TCN_PATH)
                if path in os.listdir(self.base_path):
                    os.remove('%s%s' % (self.base_path, path))

            # remove the image from the cache
            self.cache.remove(id)


    def delImage(self, autoid):
        """\brief Deletes an image entry."""
        if autoid:
            if not isinstance(autoid, ListType):
                autoid = [int(autoid)]
            self.tableHandler[TN_IMAGE].deleteEntries(autoid)


    def getImage(self, autoid):
        """\brief Returns an image entry.

        \param id  The argument \a id is a value that contains an image id.
        \n
        \return image dictionary, otherwise {}
        """
        descr_dict = {}
        if autoid:
            descr_dict = self.tableHandler[TN_IMAGE].getEntry(autoid)
        return descr_dict


    def getImageFile(self, autoid):

        descr_dict = self.tableHandler[TN_IMAGE].getEntry(autoid)

        if not descr_dict.get(TCN_PATH):

            tmp_file = '%s%s' % (self.base_path, autoid)
            query    = "select lo_export(imageid,'%s') " % ( tmp_file )
            query   += "from %s%s where autoid=%s" % ( self.id, TN_IMAGE, autoid )
            result   = self.getManager(ZC.ZM_PM).executeDBQuery(query)

            if result:

                # image laden
                fHandle = open(tmp_file, 'r')
                filestr = fHandle.read()
                fHandle.close()
                os.remove(tmp_file)

        else:
            path = op.join(self.base_path, descr_dict.get(TCN_PATH))
            try:
                with open(path, 'r') as fHandle:
                    filestr = fHandle.read()
            except:
                print 'Error accessing', path
                filestr = ''
        return filestr


    def insertImage(self,
                    insert_file,
                    name        = '',
                    alt         = 'picture',
                    description = 'picture',
                    db          = True,
                    filetype    = 'image'
                    ):
        """\brief Put file on disk or into database."""
        # test file
        if hasattr(insert_file, 'read'):
            filestr = insert_file.read()
        else:
            filestr = insert_file

        # convert name (get from file)
        if not name:
            if hasattr(insert_file, 'filename'):
                tmpname = str(insert_file.filename)
                tmp2    = tmpname.replace('\\', '/')
                tail    = op.split(op.normpath(tmp2))[1]
                name    = self.trimName(tail)
            else:
                name    = ''
        if db:
            # put image as file into path
            tmp_file = self.base_path + 'insert_pic'
            fHandle  = open(tmp_file, 'w')
            fHandle.write(filestr)
            fHandle.close()
            attr1 = TCN_IMAGEID
            val1  = "lo_import('%s')" % (tmp_file)
        else:
            files  = os.listdir(self.base_path)
            if files:
                maxentry = max(files)
                # the insert_pic - tmpfile is in the way
                if maxentry == 'insert_pic':
                    files.remove('insert_pic')
                if files:
                    maxentry = max(files)
                    # get the found file's number
                    numberstr = maxentry.lstrip('image').lstrip('0')
                    maxnumber = int(numberstr)
                else:
                    maxnumber = 0


            else:
                maxnumber = 0
            maxnumber += 1
            filename = 'image' + ( 5 - len(str(maxnumber))) * '0' + str(maxnumber)
            fHandle = open( self.base_path + filename, 'w')
            fHandle.write(filestr)
            fHandle.close()
            attr1 = TCN_PATH
            val1  = "'%s'" % filename

        # the following doesn't use the standard-functions because the type-check
        # doesn't like a string (lo_import) for the id
        cols   = []
        values = []
        cols.append(attr1)
        cols.append(TCN_NAME)
        cols.append(TCN_ALT)
        cols.append(TCN_DESCR)
        cols.append(TCN_TYPE)
        values.append(val1)
        values.append("'%s'" % name)
        values.append("'%s'" % alt)
        values.append("'%s'" % description)
        values.append("'%s'" % filetype)
        query = "Insert into %s%s (%s) values (%s)" % ( self.id,
                                                        TN_IMAGE,
                                                        string.join(cols, ', '),
                                                        string.join(values, ', ')
                                                        )
        self.getManager(ZC.ZM_PM).executeDBQuery(query)
        if hasattr(insert_file, 'close'):
            insert_file.close()
        return self.tableHandler[TN_IMAGE].getLastId()


    def updateImage(self, autoid, insert_file, name, alt, description):
        """\brief Update file attributes and the file itself."""
        # test file
        if hasattr(insert_file, 'read'):
            filestr = insert_file.read()
        else:
            filestr = insert_file

        # get existent entry, erase old file / blob, enter new, update values in db
        # tmp_file = None
        if not autoid:
            return False
        image = self.getImage(autoid)
        filetype = image.get(TCN_TYPE, 'image')
        if file:
            if not image.get(TCN_PATH):
                # delete old blob
                # #BUG not possible? -> postgres problem
                # put image as file into path
                path = '%sinsert_pic' % (self.base_path)
                diskfile = open(path, 'w')
                diskfile.write(filestr)
                diskfile.close()
                attr1 = TCN_IMAGEID
                val1  = "lo_import('%s')" % (path)
            else:
                #
                path = '%s%s' % ( self.base_path,
                                  image.get(TCN_PATH)
                                  )
                os.remove(path)
                diskfile = open(path, 'w')
                diskfile.write(filestr)
                diskfile.close()
                attr1 = TCN_PATH
                val1  = "'%s'" % path
        else:
            attr1 = None
            val1  = None
        # calculate name
        if not name:
            if hasattr(file, 'filename'):
                tmpname = str(file.filename)
                tmp2    = tmpname.replace('\\', '/')
                tail    = op.split(op.normpath(tmp2))[1]
                name    = self.trimName(tail)
            else:
                name    = ''
        # close file
        if hasattr(insert_file, 'close'):
            insert_file.close()
        # the following doesn't use the standard-functions because
        # the type-check doesn't like a string (lo_import) for the id
        values = []
        if val1 and attr1:
            values.append("%s = %s" % (attr1, val1))
        values.append("%s = '%s'" % (TCN_NAME, name))
        values.append("%s = '%s'" % (TCN_ALT, alt))
        values.append("%s = '%s'" % (TCN_DESCR, description))
        values.append("%s = '%s'" % (TCN_TYPE, filetype))
        query = "UPDATE %s%s SET %s WHERE autoid = %s" % ( self.id,
                                                           TN_IMAGE,
                                                           string.join(values, ', '),
                                                           autoid )
        return self.getManager(ZC.ZM_PM).executeDBQuery(query)
#
# List functions
#

    def getImageValue(self, autoid):
        """\brief Other Managers can use image as fake-singlelist, the value to an id is a link."""
        if not autoid:
            return hgLabel('')
        entry = self.tableHandler[TN_IMAGE].getEntry(autoid)
        if entry:
            name = entry.get(TCN_NAME)
            if not name:
                name = entry.get(TCN_TYPE)
            if entry.get(TCN_TYPE) == 'image':
                return hgLabel(name, '%s/showForm?id=%s&table=%s' % (self.absolute_url(), autoid, TN_IMAGE))
            elif entry.get(TCN_TYPE) == 'file':
                return hgLabel(name, '%s/getFileStream?autoid=%s' % (self.absolute_url(), autoid))
        return hgLabel('')


    def getImageSelect(self):
        """\brief dummy function, should never be called, but to avoid bad errors, its here."""
        return []


    def getFileValue(self, autoid):
        """\brief Other Managers can use image as fake-singlelist, the value to an id is a link."""
        return self.getImageValue(autoid)


    def getFileSelect(self):
        """\brief dummy function, should never be called, but to avoid bad errors, its here."""
        return []


    def getImageTag(self, autoid, parent = None):
        """\brief Other Managers can use image as fake-singlelist, the value to an id is a link."""
        label = ''
        link  = None
        if not autoid:
            return hgLabel('', parent = parent)
        entry = self.tableHandler[TN_IMAGE].getEntry(autoid)
        if entry:
            if entry.get(TCN_TYPE) == 'image':
                alt = entry.get(TCN_ALT)
                if not alt:
                    alt = ''
                label = '<img src="%s/getFileStream?autoid=%s" alt="%s">'
                label = label % (self.absolute_url(), autoid, alt)
            elif entry.get(TCN_TYPE) == 'file':
                label = entry.get(TCN_NAME)
                if not label:
                    label = entry.get(TCN_TYPE)
                link = '%s/getFileStream?autoid=%s' % (self.absolute_url(), autoid)
        return hgLabel(label, link, parent = parent)


    def trimName(self, name):
        """\brief Correct names of files for universal use as filename"""
        if not name:
            return ''
        tmp = name.replace('(', '')
        tmp = tmp.replace(')', '')
        tmp = tmp.replace(' ', '')
        tmp = tmp.replace(':', '')
        return tmp


    def getFileStream(self, autoid, REQUEST):
        """\brief caches and delivers a file per REQUEST.RESPONSE"""
        fileentry = self.getImage(autoid)
        if not fileentry:
            err = self.getErrorDialog(FILE_ERROR)
            raise ValueError(err)
        name = fileentry.get(TCN_NAME)

        # look in cache
        if self.cache.has(autoid):
            filestr = self.cache.get(autoid)
        else:
            # not in cache, get it, put it in
            filestr = self.getImageFile(autoid)

            if filestr:

                # put file into cache
                self.cache.set(autoid, filestr)

            else:
                err = self.getErrorDialog(FILE_ERROR + ' Image: ' + str(fileentry) + ' Config:' + str(self.base_path) + ' Please contact the Administrator.')
                raise ValueError(err)
        # prepare RESPONSE
        resp = REQUEST.RESPONSE
        mime_type = 'application/octet-stream'
        # some wild mime type guessing
        if len(name) > 3:
            end  = name[-3:]
            if end == 'doc':
                mime_type = 'application/msword'
            elif end == 'pdf':
                mime_type = 'application/pdf'
            # what about images?
        resp.setHeader('Content-Type', mime_type)
        resp.setHeader('Content-disposition', 'inline; filename="%s"' % name)

        return filestr

#
# Public functions
#

    def buildImage(self, image):
        """\brief builds a image attribute and returns the html-link for the image"""
        if image:
            autoid = image.get('autoid')
            name   = image.get(TCN_NAME)
            if not name:
                name = image.get(TCN_TYPE)
            tab = hgTable()
            tag = '<img src="%s/getFileStream?autoid=%s" alt="%s">' % \
                                                   ( self.absolute_url(),
                                                     autoid,
                                                     image.get(TCN_ALT, '')
                                                     )
            tab[0, 0] = dlgLabel(name)
            tab[1, 0] = tag
            tab[2, 0] = hgLabel(image.get(TCN_DESCR))
            # add table property
            tab[3, 0] = hgProperty('table', TN_IMAGE, parent = tab)
            return tab
        return ''

#
# public managing
#

    def _index_html(self, REQUEST, parent = None):
        tab = hgTable(parent = parent)
        url = self.absolute_url()
        tab[0, 0] = hgLabel('Upload File/Image', '%s/newForm?table=%s' % (url, TN_IMAGE))
        tab[1, 0] = hgLabel('File/Image List', '%s/showList?table=%s' % (url, TN_IMAGE))
        tab[2, 0] = hgLabel('Cached File/Image List', '%s/showCacheList' % url)
        tab[3, 0] = hgLabel('Check stored files', '%s/checkStore' % url)
        return tab

#
# managing
#


    def showForm(self, id, table = TN_IMAGE, REQUEST = None, auto = None):
        """\brief Returns the html source for an Image."""
        image = self.getImage(id)
        name  = image.get(TCN_NAME)
        if not image:
            err    = self.getErrorDialog(FILE_ERROR)
            raise ValueError(err)
        mask = self.buildImage(image)
        return self.getTableEntryShowDialog('Image %s' % name, mask )


    def editForm(self, id, table = TN_IMAGE, REQUEST = None):
        """\brief Image Edit Form Function."""
        # TODO: implement edit form with mask
        # rerouted to showForm for now
        return self.showForm(id, table, REQUEST)


    def newForm(self, table = TN_IMAGE, REQUEST = None):
        """\brief Returns the image add dialog."""
        button     = self.getPressedButton(REQUEST)
        autoid = ''
        if button:
            if button == BTN_L_ADD:
                if REQUEST.get(TCN_TYPE) == '1':
                    filetype = 'image'
                else:
                    filetype = 'file'
                image_obj = REQUEST.get('file')
                if hasattr(image_obj, 'filename'):
                    name = str(image_obj.filename)
                else:
                    name = filetype
                autoid = self.insertImage( image_obj,
                                           REQUEST.get(TCN_NAME, name),
                                           REQUEST.get(TCN_ALT),
                                           REQUEST.get(TCN_DESCR),
                                           False,
                                           filetype
                                           )
                REQUEST['zopra_message'] = True
        tab = hgTable()
        tobj = self.tableHandler[TN_IMAGE]
        image = {}
        if autoid:
            image = self.getImage(autoid)
            if image:
                if image.get(TCN_TYPE) == 'image':
                    tab[0, 0] = self.buildImage(image)
                else:
                    tab[0, 0] = self.getImageTag(autoid, tab)
                tab.setCellSpanning(0, 0, 1, 2)
        tab[1, 0] = dlgLabel('Upload Image')
        tab[1, 1] = '<input type="file" name="file">'
        tab[2, 0] = tobj.getLabelWidget(TCN_NAME)
        tab[3, 0] = tobj.getLabelWidget(TCN_ALT)
        tab[4, 0] = tobj.getLabelWidget(TCN_DESCR)
        tab[5, 0] = tobj.getLabelWidget(TCN_TYPE)
        tab[2, 1] = hgTextEdit(image.get(TCN_NAME,  ''), name = TCN_NAME)
        tab[3, 1] = hgTextEdit(image.get(TCN_ALT,   ''), name = TCN_ALT)
        tab[4, 1] = hgTextEdit(image.get(TCN_DESCR, ''), name = TCN_DESCR)
        box = hgCheckBox(value = '1', name = TCN_TYPE)
        if image.get(TCN_TYPE) == 'image':
            box.setChecked(True)
        tab[5, 1] = box + 'Image'
        # build the dialog (because of encoding)
        dlg  = getStdDialog('New Image', 'newForm')

        # add property for table
        dlg.add(hgProperty('table', TN_IMAGE, parent = dlg))

        dlg.setEncode(dlg.EncodeMulti)
        dlg.add('<center>')
        dlg.add( str(tab) )
        dlg.add(hgNEWLINE)
        dlg.add(hgNEWLINE)

        # a message if we have recently added something
        if REQUEST.get('zopra_message'):
            dlg.add(dlgLabel('Your values have been added to the DB. You can now add more.'))
            dlg.add(hgNEWLINE)
            dlg.add(hgNEWLINE)

        dlg.add(mpfAddButton)
        dlg.add(hgSPACE)

        mpfResetButton.isLocal = False
        mpfResetButton._valid  = False
        dlg.add(mpfResetButton)
        dlg.add('</center>')
        dlg.add(self.getBackButtonStr(REQUEST))
        return HTML( dlg.getHtml() )(self, None)


    def actionBeforeShowList(self, table, param, REQUEST):
        """\brief Adjust the show List options."""
        m_security = self.getHierarchyUpManager(ZC.ZM_SCM)
        if not m_security or m_security.getCurrentLevel() > 10:
            param['with_delete'] = True

        param['with_show'] = True

        # the check parameter is a function name that is called with the
        # "field"-value to calculate the value for the completion of the
        # link-url. if none is returned, the button will be omitted
        # if no check is given, the "field"-value itself will be used instead
        param['links'] = { 'Picture': { 'link': '',
                                        'field': 'autoid',
                                        'check': 'getImageValue'
                                        }
                           }

        param['special_field']  = TCN_NAME
        # root = self.tableHandler[TN_IMAGE].getSearchTreeTemplate()
        # return self.getTableEntryListHtml( root,
        #                                    param     = param,
        #                                    REQUEST   = REQUEST )


    def showCacheList(self, REQUEST):
        """\brief Returns the html source for the cache list."""
        dlg  = getStdDialog('Image Cache List', 'showCacheList')
        form = dlg.getForm()

        button = self.getPressedButton(REQUEST)
        if button == BTN_L_RESET2:
            self.cache = PersistentCache(FileManager.cache_size)
        tab = hgTable()
        row = 0
        for entry in self.cache.getOrderedKeys():
            tab[row, 0] = self.getImageValue(entry)
            row += 1
        if row == 0:
            tab[0, 0] = hgLabel('No Entries.')

        form.add( '<center>' )
        form.add( tab )
        form.add( str(hgNEWLINE) )
        form.add( hgNEWLINE )
        form.add( mpfReset2Button )
        form.add( self.getBackButtonStr(REQUEST) )
        form.add( '</center>' )
        return HTML( str(dlg) )(self, None)


    def checkStore(self, REQUEST):
        """\brief Returns the html source for the cache list."""
        dlg  = getStdDialog('Stored Files', 'checkStore')
        form = dlg.getForm()

        button = self.getPressedButton(REQUEST)
        if button == BTN_L_DELETE:
            do_del = True
        else:
            do_del = False

        orph = self.searchOrphanedFiles(do_del)

        tab = hgTable()
        if not orph:
            tab[0, 0] = hgLabel('No Orphaned Entries.')
        else:
            if do_del:
                ins = 'deleted'
            else:
                ins = 'found'
            tab[0, 0] = hgLabel('%s Files without db entry %s:' % (len(orph), ins))

        row = 1
        for entry in orph:
            tab[row, 0] = hgLabel(entry)
            row += 1

        form.add( '<center>' )
        form.add( tab )
        form.add( str(hgNEWLINE) )
        form.add( hgNEWLINE )
        form.add( mpfDeleteButton )
        form.add( self.getBackButtonStr(REQUEST) )
        form.add( '</center>' )
        return HTML( str(dlg) )(self, None)


    def searchOrphanedFiles(self, do_del):
        """\brief Tests all files in the storage dir for database entries."""
        files  = os.listdir(self.base_path)
        orph = []
        if files:
            tobj = self.tableHandler[TN_IMAGE]
            for filename in files:
                # the insert_pic - tmpfile is in the way
                if filename == 'insert_pic':
                    continue
                # search database for entry with path = filename
                found = tobj.getEntries(filename, TCN_PATH)
                if not found:
                    orph.append(filename)
                    if do_del:
                        os.remove('%s%s' % (self.base_path, filename))
                elif len(found) > 1:
                    orph.append('Found multiple entries: %s' % filename)
        return orph


    def installConfig(self, REQUEST):
        """\brief Function called after creation by manageGeneric"""

        self.cache  = PersistentCache(FileManager.cache_size)
        base_path   = REQUEST.get('base_path')
        if not base_path:
            base_path = '/tmp/'

        print 'base_path', base_path

        try:
            # we create a folder for our manager
            path = op.join(base_path, str(self.id))
            if not op.exists(path):
                os.mkdir(path)
                print 'create directory', path

            # overwrite base_path attribute in class with final version
            # this makes changes during runtime possible
            self.base_path = path + '/'
            print 'base_path', self.base_path

        except:
            raise ValueError('Error creating file hierarchy in %s' % base_path)
