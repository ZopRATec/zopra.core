############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
from copy  import copy
from types import ListType

from PyHtmlGUI.kernel.hgTable            import hgTable
from PyHtmlGUI.widgets.hgLabel           import hgSPACE,   \
                                                hgNEWLINE, \
                                                hgProperty

from PyHtmlGUI.widgets.hgCheckBox        import hgCheckBox

from zopra.core                          import HTML, ZM_PNM
from zopra.core.dialogs                  import getStdDialog

from zopra.core.elements.Buttons         import getSpecialField,          \
                                                mpfPrintButton,           \
                                                mpfBasketPopButton,       \
                                                mpfRemoveButton,          \
                                                mpfRefreshButton,         \
                                                mpfMoveDownButton,        \
                                                BTN_L_PRINT,              \
                                                BTN_BASKET_POP,           \
                                                BTN_L_REMOVE,             \
                                                BTN_L_MOVEDOWN,           \
                                                DLG_CUSTOM,               \
                                                getPressedButton
from zopra.core.lists.ForeignList        import ForeignList
from zopra.core.tools.GenericManager     import GenericManager
from zopra.core.tools.managers           import TN_LABELING, \
                                                   TCN_NAME, \
                                                   TCN_COL_COUNT, \
                                                   TCN_ROW_COUNT, \
                                                   TCN_FONT_SIZE, \
                                                   TCN_PADDING_ROW, \
                                                   TCN_PADDING_COL, \
                                                   TCN_CELL_WIDTH, \
                                                   TCN_CELL_HEIGHT, \
                                                   TCN_MARGIN_RIGHT, \
                                                   TCN_MARGIN_LEFT, \
                                                   TCN_MARGIN_TOP, \
                                                   TCN_MARGIN_BOTTOM, \
                                                   TCN_PAGE_WIDTH, \
                                                   TCN_PAGE_HEIGHT, \
                                                   TCN_AUTOID, \
                                                   TCN_SHORT_LABEL, \
                                                   TCN_MULTI_LINE
from zopra.core.widgets                  import dlgLabel



#
# pdf gen
#
try:
    from reportlab.pdfgen       import canvas
    from reportlab.lib.units    import cm, mm
    reportlabfound = True
except:
    reportlapfound = False

class PrintManager(GenericManager):
    """ Print Manager """
    _className = ZM_PNM
    _classType = GenericManager._classType + [_className, 'ZMOMTool']
    meta_type  = _className

    _generic_config = GenericManager._generic_config
    _generic_config[TN_LABELING] = { 'basket_active': True,
                                     'show_fields': ( TCN_NAME,
                                                      TCN_COL_COUNT,
                                                      TCN_ROW_COUNT) }


#
# label printing
#

    def getPdfLabel(self, label_def, param, numpages, RESPONSE):
        """\brief Returns a pdf file with the labels."""
        filename = '/tmp/ZMOMPrintManagerTemporaryDocument.pdf'
        c = canvas.Canvas(filename)
        c.translate(0, 0)

        font_size = int(label_def.get(TCN_FONT_SIZE, 8))
        c.setFont('Courier', font_size)

        # start
        offset_hor  = label_def.get(TCN_PADDING_ROW, 0) * mm
        offset_ver  = label_def.get(TCN_PADDING_COL, 0) * mm
        cell_x      = label_def.get(TCN_CELL_WIDTH, 1)  * mm
        cell_y      = label_def.get(TCN_CELL_HEIGHT, 1) * mm

        # maximum line length
        hint = int(4.8 / font_size * label_def.get(TCN_CELL_WIDTH, 1))

        #Margins
        right = label_def.get(TCN_MARGIN_RIGHT, 1) * mm
        left  = label_def.get(TCN_MARGIN_LEFT, 1) * mm
        top   = label_def.get(TCN_MARGIN_TOP, 1)   * mm
        bottom = label_def.get(TCN_MARGIN_BOTTOM, 1) * mm

        # dirty pdf hack
        #left   = left   - 7 * mm
        #top    = top    - 6 * mm
        #right  = right  + 7 * mm
        #bottom = bottom + 6 * mm

        # format
        pagex   = label_def.get(TCN_PAGE_WIDTH, 1) * mm
        pagey   = label_def.get(TCN_PAGE_HEIGHT, 1) * mm
        x       = left
        y       = pagey - top

        row_count = label_def.get(TCN_ROW_COUNT, 1)
        col_count = label_def.get(TCN_COL_COUNT, 1)

        for pageindex in xrange(numpages):

            c.setPageSize( (pagex, pagey) )
            
            y_tmp   = y
        
            # fill cell information
            for row in range(row_count):
                x_tmp	 = x
                for col in range(col_count):
    
                    # draw rectangle
                    
                    #TODO: Find out how to reduce stroke width to fine lines
                    p = c.beginPath()
                    p.rect(x_tmp, y_tmp - cell_y, cell_x, cell_y)
                    c.drawPath(p)
    
                    # pageoffset + rowoffset + col is the number to show
                    number = pageindex * col_count * row_count + row * col_count + col
                    line = param.get(number, [0, ''])[1]
                    linelist = line.split('\n')
                    for index, entry in enumerate(linelist):
                        act_fontsize = int(font_size)
                        if index == 0:
                            # heading
                            act_fontsize = act_fontsize + 2
                            c.setFont('Courier-Bold', act_fontsize)
                            
                        # shorten line
                        if len(entry) > hint:
                            # line too long
                            entry = entry[:hint-1] + '*'
                            # TODO: use stringWidth(self, text, fontName=None, fontSize=None) for this check
                        # draw into box, guessing y is really hard
                        c.drawString( x_tmp + 0.4 * mm, 
                                      y_tmp - 2.6 * mm - index * ((float(act_fontsize) / 3 - 0.5)* mm),
                                      entry )
                        if index == 0:
                            c.setFont('Courier', int(font_size))
    
    
                    x_tmp += cell_x
                    # calculate next position
                    x_tmp += offset_hor
    
                # calculate next position
                y_tmp -= (offset_ver + cell_y)
            # save the page (jumps to next one)
            c.showPage()
        
        # testing
        #p = c.beginPath()
        #p.rect(x, y, pagex - left - right, -y + bottom)
        #c.drawPath(p)

        # save the canvas and read the file
        c.save()
        file = open(filename, 'r')
        data = file.read()
        file.close()
        RESPONSE.setHeader('Content-Type', 'application/pdf')
        RESPONSE.setHeader('Content-disposition', 'attachement; filename="Print.pdf"')
        return data


    def getLabelHtmlSelect(self, selected = None):
        """\brief Returns a ComboBox for label-format selection"""
        entries = self.tableHandler[TN_LABELING].getEntries(order = TCN_NAME)
        values = [(item[TCN_AUTOID], item[TCN_NAME]) for item in entries]

        llist = ForeignList(TN_LABELING)
        box   = llist.getSpecialWidget( entry_list   = values, 
                                        with_novalue = False, 
                                        selected     = selected,
                                        with_null    = False )

        return box


    def showFormPrintLabel(self, labeling, mgr_name, mgr_id, table, REQUEST = None, autoids = None):
        """\brief Returns the html source for a print layout dialog."""
        if not reportlabfound:
            # disable printing
            self.displayError('Missing Import', 'Reportlab is necessary for pdf printing, but was not found.')
        # manager doing the print is needed.
        # manager doing the print has to have a formatting function
        RESPONSE = REQUEST.RESPONSE
        # basket handling
        fun = 'showFormPrintLabel?labeling=%s&mgr_name=%s&mgr_id=%s&table=%s'
        fun = fun % (labeling, mgr_name, mgr_id, table)
        REQUEST.form['repeataction'] = fun 

        if not labeling:
            labeling = self.tableHandler[TN_LABELING].getLastId()
        if not labeling:
            errstr = 'No layout information found.'
            err    = self.getErrorDialog(errstr)
            raise ValueError(err)
        #get labeldict
        label_dict = self.tableHandler[TN_LABELING].getEntry(labeling)

        #get Entries for table (list of autoids)
        entries = getSpecialField(REQUEST, DLG_CUSTOM + 'stored')
        manager  = self.getHierarchyDownManager(mgr_name, mgr_id)
        if not manager:
            raise ValueError(self.getErrorDialog('Internal printing Error: No manager found: %s %s' % (mgr_name, mgr_id)))
        if not hasattr(manager, 'formatPrintLabel'):
            raise ValueError(self.getErrorDialog('Internal printing Error: No print formatting function found.'))

        col_count = label_dict.get(TCN_COL_COUNT)
        row_count = label_dict.get(TCN_ROW_COUNT)

        # if there are no entries, maybe we got autoids
        if not entries:
            if autoids:
                entries = {}
                if not isinstance(autoids, ListType):
                    autoids = [autoids]
                for index, oneid in enumerate(autoids):
                    entries[oneid] = index
                    # removed max-check -> display all now
                    #if index == (row_count * col_count - 1):
                    #    break

        #build param
        param = {}
        for autoid in entries:
            number = entries[autoid]
            param[int(number)] = [ autoid,
                       manager.formatPrintLabel( table,
                                                 int(autoid),
                                                 label_dict.get(TCN_SHORT_LABEL),
                                                 label_dict.get(TCN_MULTI_LINE)
                                                )
                                 ]
        # check maximum number -> no more
        #if param and max(param.keys()) >= row_count * col_count:
        #    msg = 'Selected items do not fit on the selected layout'
        #    raise ValueError(self.getErrorDialog(msg))

        buttons = getPressedButton(REQUEST)
        for button in buttons:

            # print function
            if button == BTN_L_PRINT:
                # calc pagecount
                onepage = row_count * col_count
                if param:
                    maxnum = max(param.keys()) 
            
                    # numbers go from 0 up, so maxnum/onepage is 0 for first page
                    pages = ( maxnum / onepage ) + 1
                else:
                    pages = 1
                    
                return self.getPdfLabel(label_dict, param, pages, RESPONSE)

            elif button == BTN_BASKET_POP:
                #fill table
                start = REQUEST.get('number')
                filllist = None
                if not start:
                    # nothing done, so check entries and append
                    if entries:
                        start = len(entries)
                    else:
                        # page is empty
                        start = 0
                else:
                    # something was checked
                    if not isinstance(start, ListType):
                        # one box checked as start number
                        start = int(start)
                    #else start is a list of numbers
                    else:
                        filllist = [int(oneid) for oneid in start]
                        # append stopper
                        filllist.append(-1)
                while True:
                    
                    if filllist:
                        number = filllist.pop(0)
                        if number == -1:
                            break
                    else:
                        number = start
                        start += 1
                        
                    newdict  = self.basket.popFirstActiveEntryFromBasket(REQUEST.SESSION, mgr_name, table, True)
                    # check if basket gave us something
                    if not newdict:
                        break
                    
                    # get id and formatted string
                    newid    = newdict.get(TCN_AUTOID)
                    formatted = manager.formatPrintLabel(table, newid, label_dict.get(TCN_SHORT_LABEL), label_dict.get(TCN_MULTI_LINE))
                    if not formatted:
                        raise ValueError(self.getErrorDialog('Printing Error: Wrong basket entry.'))
                    #put into param
                    param[number] = [newid, formatted]
                    
                    # don't stop, display several pages
                    #if start == row_count * col_count:
                    #    # stop after one complete page
                    #    break
            elif button == BTN_L_REMOVE:
                #remove entry from label
                rem = REQUEST.get('number')
                if rem:
                    if not isinstance(rem, ListType):
                        rem = [rem]
                    for number in rem:
                        if int(number) in param:
                            del param[int(number)]

            elif button == BTN_L_MOVEDOWN:
                # move items down to selected item
                # check params (else nothing to move)
                if param:
                    
                    rem = REQUEST.get('number')
                    if rem:
                        if isinstance(rem, ListType):
                            rem = int(rem[0])
                        else:
                            rem = int(rem)
                        
                    else:
                        # jump one down
                        rem = min(param.keys()) + 1
                    
                    if rem > min(param.keys()):
                        # move really down
                        plus = -1
                        pop  = -1
                        
                        # jump to last target
                        rem += len(entries) - 1
                        
                        # removed, display many pages now
                        # check that we didn't increase too far
                        #if rem >= row_count * col_count:
                        #    rem = row_count * col_count - 1
                    
                    else:
                        # move up
                        plus = 1
                        pop  = 0
                        # rem is okay
                    
                    # start with the last, move to rem, decrease rem, go on
                    elist = copy(param.keys())
                    elist.sort()
                    par2  = {}
                    while True:
                        if rem < 0:# or rem == row_count * col_count:
                            break
                        
                        if not elist:
                            break
                        
                        old_index = elist.pop(pop)
                        
                        par2[rem] = param[old_index]
                        
                        rem += plus
                    
                    if len(param) == len(par2):
                        # everything went okay, overwrite
                        param = par2

        #
        # get Mask
        #
        
        # get number of pages
        pages = 1
        onepage = row_count * col_count
        if param:
            maxnum = max(param.keys()) 
            
            # numbers go from 0 up, so maxnum/onepage is 0 for first page
            pages = ( maxnum / onepage ) + 1
        
        pagelist = []
        
        # create pages
        for pagecount in xrange(pages):
            pagelist.append(self.prepareTab(pagecount + 1, col_count, row_count))

        for number in param:
            # get page index
            pageindex = number / onepage
            tab = pagelist[pageindex]
            numonpage = number - pageindex * onepage
            tmp = param[number]
            autoid = tmp[0]
            entry  = tmp[1]
            row   = numonpage / col_count
            col   = numonpage % col_count

            #if row > (page * row_count):
            #    page += 1
            #    self.prepareTab(tab, page, col_count, row_count)
            #one free line per page plus title(shifts row)
            #tmpy = page -1 + page + row
            prop = DLG_CUSTOM + 'stored' + str(autoid)
            # rowoffset is 1 (page number is in first row)
            tab[row + 1, col] += entry.replace('\n','<br>') \
                           +  hgProperty(prop, str(number))
            tab.setCellNoWrap(row, col, True)

        url = self.absolute_url()
        dlg  = getStdDialog('Print Layout', '%s/showFormPrintLabel' % url)
        form = dlg.getForm()
        #properties
        form.add( hgProperty('mgr_id', mgr_id) )
        form.add( hgProperty('mgr_name', mgr_name) )
        form.add( hgProperty('table', table) )
        form.add( '<center>')
        form.add( str(hgNEWLINE) )
        form.add( dlgLabel('Label Type ') )
        form.add( self.getLabelHtmlSelect(labeling) )
        form.add( str(hgNEWLINE) )
        form.add( str(hgNEWLINE) )
        form.add( dlgLabel('Label Paper Layout (%s pages)' % pages) )
        form.add( str(hgNEWLINE) )
        
        for tab in pagelist:
            
            form.add( str(hgNEWLINE) )
            form.add( tab )
            form.add( str(hgNEWLINE) )
        
        form.add( str(hgNEWLINE)     )
        form.add( mpfRefreshButton   )
        form.add( mpfBasketPopButton )
        form.add( mpfRemoveButton    )
        form.add( mpfMoveDownButton  )
        form.add( mpfPrintButton     )
        form.add( '</center>' )
        form.add(self.getBackButtonStr(REQUEST))
        return HTML( str(dlg) )(self, REQUEST)


    def prepareTab(self, page, col_count, row_count):
        tab = hgTable()
        tab[0, 0] = dlgLabel('Page %s' % page, parent = tab)
        tab.setCellSpanning(0, 0, 0, col_count + 1)
        start = 1
        for row in xrange(row_count):
            for col in xrange(col_count):
                actnumber = row * col_count + col
                number = (page - 1) * (col_count * row_count) + actnumber
                label = hgCheckBox(name = 'number', value = str(number), parent = tab)
                tab[start + row, col] = label
                tab.setCellAlignment(start + row_count, col_count, tab.ALIGN_LEFT)
        tab[start + row_count, 0] = str(hgSPACE)
        return tab
    
