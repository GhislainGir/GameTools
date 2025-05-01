# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

from bl_ui.utils import PresetPanel

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class PIVOTPAINTER_MT_Pivot_Presets(bpy.types.Menu):
    bl_label = 'Pivot Painter Presets'
    preset_subdir = 'operator/databaker_pivotpainter'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class PIVOTPAINTER_PT_Pivot_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'Pivot Painter Presets'
    preset_subdir = 'operator/databaker_pivotpainter'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'databaker_pivotpainterpanel.addpreset'

############
### MAIN ###
class PIVOTPAINTER_PT_MainPanel(bpy.types.Panel):
	bl_idname = "PIVOTPAINTER_PT_ppbpanel"
	bl_label = "Pivot Painter"		
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Game Tools"
	bl_order = 1

	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		# prevent parent panel to show in any mode but the object mode
		if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
			return False
		
		return True

	def draw_header_preset(self, _context):
		PIVOTPAINTER_PT_Pivot_Preset.draw_panel_header(self.layout)

	def draw(self, context):
		Layout = self.layout

		PivotPainterSettings = bpy.context.scene.PivotPainterSettings  

		col = Layout.column()

		# 
		if PivotPainterSettings.totaltextures >0 :
			col.label(text="1st Texture:")
			col.prop(PivotPainterSettings, "rgb")
			col.prop(PivotPainterSettings, "alpha")
		if PivotPainterSettings.totaltextures >1 :
			col.label(text="2nd Texture:")
			col.prop(PivotPainterSettings, "rgb2")
			col.prop(PivotPainterSettings, "alpha2")
		if PivotPainterSettings.totaltextures >2 :
			col.label(text="3rd Texture:")
			col.prop(PivotPainterSettings, "rgb3")
			col.prop(PivotPainterSettings, "alpha3")
		if PivotPainterSettings.totaltextures ==4 :
			col.label(text="4th Texture:")
			col.prop(PivotPainterSettings, "rgb4")
			col.prop(PivotPainterSettings, "alpha4")		

		Layout.row().separator()
		row = Layout.row()														# Index options
		row.prop(PivotPainterSettings, "automaticindexselect")
		sub=row.column()
		if PivotPainterSettings.automaticindexselect == True:
			sub.enabled = False
		else:
			sub.enabled = True
		sub.prop(PivotPainterSettings, "uvindex")
		col = Layout.column()

		ext = col.row() # Extra Options 

		box = Layout.box()
		ext = box.row()
		extext = ext.row()
		extext.label(text="Extra Options")

		row = box.row()
		row.prop(PivotPainterSettings, "totaltextures")
								
		row1 = box.column()
		row1.scale_y = 1.5
		if not PivotPainterSettings.selectingobjects: # create select order (flip option to show operation running)
			row1.operator("gametools.pivotpainter_create_select_order")
		else:
			row1.prop(PivotPainterSettings, "selectingobjects", toggle=True)
		row6 = box.row()
		row6.prop(PivotPainterSettings, "orderstart")
		row6.prop(PivotPainterSettings, "dontcount")

		col7 = box.column()			
		ext2 = col7.row() # Experimental Options 			

		extext = ext2.row()
		extext.label(text="Calculate X Axis from BoundBox (Experimental):")
		col = box.column()							
		rows = col.row()
		rows.prop(PivotPainterSettings, "firstlevel")
		rows.prop(PivotPainterSettings, "secondlevel")
		rows.prop(PivotPainterSettings, "thirdlevel")
		rows.prop(PivotPainterSettings, "fourthlevel")
		row = Layout.row()
		per = box.column()
		if ( PivotPainterSettings.firstlevel == True ) or ( PivotPainterSettings.secondlevel == True ) or ( PivotPainterSettings.thirdlevel == True ) or ( PivotPainterSettings.fourthlevel == True ):
				per.enabled = True
		else:
			per.enabled = False	
		per.prop(PivotPainterSettings, "percentagefreedom", slider=True)

		col = Layout.column() # File options
		rows = col.row()
		rows.prop(PivotPainterSettings, "createnew")
		rows.prop(PivotPainterSettings, "savetextures")
		sub2 = Layout.column()
		if PivotPainterSettings.savetextures == True:
			sub2.enabled = True
		else:
			sub2.enabled = False		
		sub2.prop(PivotPainterSettings, "folderpath")
		
		row = Layout.row()
		row.scale_y = 2
		row.operator("gametools.pivotpainter_create_textures")
