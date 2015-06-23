############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    webmaster@ingo-keller.de                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################
"""\brief Contains the default style schema"""

from PyHtmlGUI.stylesheet.hgStyleSheet  import hgStyleSheetItem
from PyHtmlGUI.kernel.hgSize            import hgSize

#
# Default StyleSheetItems
#
ssiA            = hgStyleSheetItem( 'a' )
ssiA_VISITED    = hgStyleSheetItem( 'a:visited' )

ssiA.font().setTextDecoration( 'none'    )
ssiA.font().setColor( '#0000C0' )

ssiA_VISITED.font().setTextDecoration( 'none'    )
ssiA_VISITED.font().setColor( '#0000C0' )

# dialog styles
ssiDLG          = hgStyleSheetItem( 'body'          )
ssiDLG_FORM     = hgStyleSheetItem( '.dlg_form'     )
ssiDLG_LABEL    = hgStyleSheetItem( '.dlg_label'    )
ssiDLG_LABEL_HL = hgStyleSheetItem( '.dlg_label_hl' )
ssiDLG_TITLE    = hgStyleSheetItem( '.dlg_title'    )
ssiDLG_SHADE    = hgStyleSheetItem( '.dlg_shade'    )
ssiDLG_ACTION   = hgStyleSheetItem( '.dlg_action'   )
ssiDLG_MINI_SPACER = hgStyleSheetItem( '.dlg_mini_spacer' )
ssiDLG_NOBORDER = hgStyleSheetItem( '.dlg_noborder' )
ssiDLG_TOPBORDER = hgStyleSheetItem( '.dlg_topborder')

ssiDLG.background().setColor(0xf5f9ff)

ssiDLG_FORM.background().setColor( 0xe6eaee        )
ssiDLG_FORM.border().setAll( 0x000000, 'solid', '1px' )

ssiDLG_LABEL.font().setColor(0x004488)

ssiDLG_LABEL_HL.font().setColor(0xff0000)

# action label
ssiDLG_ACTION.font().setColor( 0x004488        )
ssiDLG_ACTION.font().setSize( '9pt' )
ssiDLG_ACTION.paragraph().setHorAlign( 'center'  )

# mini spacer
ssiDLG_MINI_SPACER.font().setSize( '4pt' )

# borderless dialog
ssiDLG_NOBORDER.border().setAll( 0x000000, 'none', '0px')

# borderless dialog with top border
ssiDLG_TOPBORDER.border().setAll( 0x000000, 'none', '0px')
ssiDLG_TOPBORDER.border().setTop(0x000000, 'solid', '1px')

# center has no effect - unknown why
ssiDLG_TITLE.paragraph().setHorAlign( 'center'  )
ssiDLG_TITLE.background().setColor( 0xd5d9ef        )
ssiDLG_TITLE.border().setBottom( 0x000000, 'solid', '1px' )
ssiDLG_TITLE.font().setWeight( 'bold'    )
ssiDLG_TITLE.font().setSize( '16pt'    )
ssiDLG_TITLE.font().setColor( 0x003366  )

ssiDLG_SHADE.background().setColor( 0xe0e0da  )

# ancestor tree styles
ssiTREE_PANEL = hgStyleSheetItem()
ssiTREE_PANEL.border().setAll( 0x000000, 'solid', '1px' )
ssiTREE_PANEL.background().setColor( 0xd5d9ef )

ssiTREE_CUTT = hgStyleSheetItem()
ssiTREE_CUTT.border().setAll( 0x000000, 'solid', '1px' )
ssiTREE_CUTT.background().setColor( 0xaaaa88  )

# navigation menu styles
ssiNAV_FORM  = hgStyleSheetItem( '.nav_form'  )
ssiNAV_TITLE = hgStyleSheetItem( '.nav_title' )

ssiNAV_FORM.background().setColor( 0xe6eaee  )
ssiNAV_FORM.border().setAll( 0x000000, 'solid', '1px' )

ssiNAV_TITLE.background().setColor( 0xd5d9ef )
ssiNAV_TITLE.border().setAll( 0x000000, 'solid', '1px' )
ssiNAV_TITLE.font().setSize( '14pt'    )
ssiNAV_TITLE.font().setColor( '#003366' )

# small text (for tree representation)
ssiTEXT_SMALL = hgStyleSheetItem( '.text_small' )
ssiTEXT_SMALL.font().setSize( '10pt' )

# small text colored (for tree representation)
ssiTEXT_SMALL_COLOR = hgStyleSheetItem( '.text_small_color' )
ssiTEXT_SMALL_COLOR.font().setSize( '10pt' )
ssiTEXT_SMALL_COLOR.background().setColor( '#FF8040' )

# small highlighted text (for population tree)
ssiTEXT_HIGHLIGHT = hgStyleSheetItem( 'a.text_highlight' )
ssiTEXT_HIGHLIGHT.font().setSize( '10pt' )
ssiTEXT_HIGHLIGHT.font().setColor( 'FF0000' )
# basket button fixed-with style
ssiB_BUTTON = hgStyleSheetItem( '.basket_button' )
ssiB_BUTTON.position().size().setWidth( '110px' )

# phenotype multi edit border style
ssiPHEN_TAB    = hgStyleSheetItem( 'table.treelistdlg' )
ssiPHEN_TAB.background().setColor( 0x3d8fe8 )
# ssiPHEN_TAB.border().setCollapse( 'collapse' )
ssiPHEN_TAB_TD = hgStyleSheetItem( 'table.treelistdlg td' )
ssiPHEN_TAB_TD.background().setColor( 0xeeeee6 )

# plant color codes
ssiPLANT_TRANS = hgStyleSheetItem( '.plant_trans' )
ssiPLANT_TRANS.background().setColor( 0x33ffff )
ssiPLANT_MUTAG = hgStyleSheetItem( '.plant_mutag' )
ssiPLANT_MUTAG.background().setColor( 0xffff66 )

# multilist style
ssiDLG_MULTILIST = hgStyleSheetItem( '.dlg_mlist' )
ssiDLG_MULTILIST.position().setMinSize( hgSize( width=100, height=1 ) )

# complex multilist style
ssiDLG_CLXMULTILIST = hgStyleSheetItem( '.dlg_complexmlist' )
ssiDLG_CLXMULTILIST.position().setMinSize( hgSize( width=90, height=1 ) )
ssiDLG_CLXMULTIBUTTON = hgStyleSheetItem( '.dlg_complexmlistbutton'    )
ssiDLG_CLXMULTIBUTTON.position().size().setWidth( '90px' )

# filtered combobox style
ssiDLG_FILTEREDCBOX = hgStyleSheetItem( '.dlg_filteredcbox' )
ssiDLG_FILTEREDCBOX.position().size().setWidth( '120px' )

# hgFilteredRangeList Styles
ssiFRL_SMALLTEXT    = hgStyleSheetItem( '.frl_smalltext'    )
ssiFRL_BUTTONS      = hgStyleSheetItem( '.frl_buttons'      )
ssiFRL_SMALLBUTTONS = hgStyleSheetItem( '.frl_smallbuttons' )
ssiFRL_BOX          = hgStyleSheetItem( '.frl_box'          )

ssiFRL_BUTTONS.position().size().setWidth( '100px' )
ssiFRL_SMALLBUTTONS.position().size().setWidth( '27px' )
ssiFRL_SMALLTEXT.font().setSize( '9pt' )
# ssiFRL_SMALLTEXT.paragraph().setHorAlign( 'right'  )
# ssiFRL_SMALLTEXT.paragraph().setVerAlign( 'top'    )
ssiFRL_BOX.position().setMinSize( hgSize( width=160, height=1 ) )
