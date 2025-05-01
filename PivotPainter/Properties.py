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

from bpy.props import PointerProperty, BoolProperty, FloatProperty, EnumProperty, StringProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup

class PIVOTPAINTER_PG_TexSettingsPropertyGroup(PropertyGroup):
	""" """
	rgb_modes = [
		("PIVOT", "Pivot Point HDR", 'The origin point of each object.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("ORIGINPOS", "Origin Position HDR", 'The bound box center of each object.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("ORIGINEXTENTS", "Origin Extents HDR", 'The maximum length of every local axis of each object\nValues source are the object Dimensions.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("XAXIS", "X Axis", 'X Axis from rotation.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8.'),
		("YAXIS", "Y Axis", 'Y Axis from rotation.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("ZAXIS", "Z Axis", 'Z Axis from rotation.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("None", "None", 'Will use as rgb values 0')
	]
	rgb_mode : EnumProperty( items=rgb_modes, name="RGB", description= "When you save textures manually,\nIf HDR texture save as OpenEXR, RGBA, Color Depth:Float(Half)\nelse use PNG, RGBA, Color Depth:8\n\nCurrent", default="PIVOT") # Any other way to create multiple of them in loop? And display on the UI.
	
	alpha_modes = [
		("Index", "HDR - Parent Index", 'The index number of each part.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Steps", "HDR - Number of Steps From Root", 'The level in the hierarchy.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Randomhdr", "HDR - Random 0-1 Value Per Element", 'Creates a random number per object.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Diameter", "HDR - Bounding Box Diameter", 'The length of the diagonal of the bound box before scale.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("SelectionOrder", "HDR - Selection Order", 'First create selection order from the extra options.\nAfter you create the order, you can change it.\nYou can also set more objects on the same number,\nor skip numbers to create empty time in the animation.\n\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Hierarchyhdr", "HDR - Normalized 0-1 Hierarchy Position", 'Object number/ Total nubmer of objects.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Xwidth", "HDR - Object X Width", 'The extent of each object on its local X axis.\nValue source is the X Dimension.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Ydepth", "HDR - Object Y Depth", 'The extent of each object on its local Y axis.\nValue source is the Y Dimension.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Zheight", "HDR - Object Z Height", 'The extent of each object on its local Z axis.\nValue source is the Z Dimension.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Hierarchy", "Normalized 0-1 Hierarchy Position", 'Object number/ Total nubmer of objects.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("Random", "Random 0-1 Value Per Element", 'Creates a random number per object.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("Xextent", "X extent", 'The extent of each object on its local X axis.\nValue source is the X Dimension.\nValues between 8-2048 in increments of 8.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("Yextent", "Y extent", 'The extent of each object on its local Y axis.\nValue source is the Y Dimension.\nValues between 8-2048 in increments of 8.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("Zextent", "Z extent", 'The extent of each object on its local Z axis.\nValue source is the Z Dimension.\nValues between 8-2048 in increments of 8.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("Diameterscaledhdr", "HDR - Scaled Bounding Box Diameter", 'The length of the diagonal of the bound box WITH scale taken into calculation.\n\nIf save texture manually, save as OpenEXR, RGBA, Color Depth:Float(Half).'),
		("Diameterscaled", "Scaled Bounding Box Diameter", 'The length of the diagonal of the bound box WITH scale taken into calculation\nValues between 8-2048 in increments of 8.\n\nIf save texture manually, save as PNG, RGBA, Color Depth:8'),
		("None", "None", 'Will use as alpha value 0')
	]
	alpha_mode : EnumProperty( items=alpha_modes, name="Alpha", description = "When you save textures manually,\nIf HDR texture save as OpenEXR, RGBA, Color Depth:Float(Half)\nelse use PNG, RGBA, Color Depth:8\n\nCurrent", default="Index" )

class PIVOTPAINTER_PG_SettingsPropertyGroup(PropertyGroup):
	""" """
	textures: CollectionProperty(type=PIVOTPAINTER_PG_TexSettingsPropertyGroup)

	automaticindexselect : BoolProperty(name = "Auto UVindex", description = ("Creates a new UVMap.\nIf there are already 8 UVMaps, will rewrite the last one.\nDefault DISABLED with UVIndex 1. "))
	uvindex : IntProperty( name="UVIndex", description="UVindex to store the textures coordinates.\nThe Unreal Engine Pivot Painter Tool 2 shaders use UV index 1 by default.\nWill create enough UV maps to reach target. ", default=1,	min=0, max=7)	

	totaltextures : IntProperty( name = "Number of Textures", description = "Number of textures to be created. ", default = 2, min = 0, max = 4)

	firstlevel : BoolProperty(name = "1st", description = "For Use with objects that have 0 rotation.\nCalculate the X Axis properties from the BoundBox for the first level.\nOutcome is not very accurate, but should be sufficient.\nVector from origin point and the furthest vertices of the boundingbox.\nWill not work for Y,Z Axes")
	secondlevel : BoolProperty(name = "2nd", description = "For Use with objects that have 0 rotation.\nCalculate the X Axis properties from the BoundBox for the second level.\nOutcome is not very accurate, but should be sufficient.\nVector from origin point and the furthest vertices of the boundingbox.\nWill not work for Y,Z Axes")
	thirdlevel : BoolProperty(name = "3rd", description = "For Use with objects that have 0 rotation.\nCalculate the X Axis properties from the BoundBox for the third level.\nOutcome is not very accurate, but should be sufficient.\nVector from origin point and the furthest vertices of the boundingbox.\nWill not work for Y,Z Axes")
	fourthlevel : BoolProperty(name = "4th", description = "For Use with objects that have 0 rotation.\nCalculate the X Axis properties from the BoundBox for the fourth level.\nOutcome is not very accurate, but should be sufficient.\nVector from origin point and the furthest vertices of the boundingbox.\nWill not work for Y,Z Axes")
	percentagefreedom : FloatProperty( name="BoundBox Percentage", description="Finds the distance of the furthest vertex of the boundingbox from the origin point.\nThen includes other vertexes that have distance bigger than the percentage given, and estimates an average point to approximate X axis and extent.\nIn almost all cases the default value is strongly advised.\nDefault 90%", default=90,soft_min=50, min=50, max=99.9999, soft_max=99 )

	selectingobjects : BoolProperty( name = "Selecting Objects", default = False, description = ("Press Again to confirm selection, or ESC to cancel.\n\nYou can select more than 1 object each time. "))	
	orderstart : IntProperty( name="Order Start Number", description="The number the order count should start.\nDefault 1", default=1, min=1, soft_max=100, max=30000)	
	dontcount : BoolProperty( name = "Same order number", default = False, description = ("Create the same order number for all selected objects"))	

	savetextures : BoolProperty( name = "Save Textures to folder", default = False, description = ("Will always OVERWRITE texture files with the same name\n\nSave textures to the specified folder location"))
	folderpath : StringProperty( name = "Save location", description="Choose a directory:", default='', maxlen=1024, subtype='DIR_PATH')
	createnew : BoolProperty( name = "Always create new textures", default = True, description = ("Should it create a new texture or use the first one?"))

class PIVOTPAINTERR_PG_ReportPropertyGroup(PropertyGroup):
    """Enhanced reporting properties for DataBaker with detailed feedback."""

    baked: BoolProperty(name="Baked", default=False, description="")
    success: BoolProperty(name="Success", default=False, description="")
    msg: StringProperty(name="Message", default="", description="")
    name: StringProperty(name="Name", default="", description="")
    ID: StringProperty(name="ID", default="", description="")

    unit_system: StringProperty(name="Unit System", default="", description="")
    unit_unit: StringProperty(name="Unit", default="", description="")
    unit_length: FloatProperty(name="Unit Length", default=0.0, description="")
    unit_scale: FloatProperty(name="Unit Scale", default=0.0, description="")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="")
    unit_invert_y: BoolProperty(name="Invert Y", default=False, description="")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="")

    mesh: PointerProperty(type=bpy.types.Object, description="")
    mesh_export: BoolProperty(name="Mesh Exported", default=False, description="")
    mesh_path: StringProperty(name="Mesh Filepath", default="//", description="", subtype='FILE_PATH')
    select_mesh_uvmap: IntProperty(name="Selected UV Map", default=0, description="")
    mesh_uvmap_invert_v: BoolProperty(name="Invert V", default=False, description="")
    mesh_uvmap_count: IntProperty(name="UV Map Count", default=0, description="")

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="")
    scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="")
    invert_x: BoolProperty(name="Invert X", default=False, description="")
    invert_y: BoolProperty(name="Invert Y", default=True, description="")
    invert_z: BoolProperty(name="Invert Z", default=False, description="")
    origin: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="")

    export_mesh: BoolProperty(name="Export", default=True, description="")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="")
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="")

def register():
	bpy.types.Scene.PivotPainterSettings = PointerProperty(type=PIVOTPAINTER_PG_SettingsPropertyGroup)
	bpy.types.Scene.PivotPainterReport = PointerProperty(type=PIVOTPAINTERR_PG_ReportPropertyGroup)

def unregister():
	del bpy.types.Scene.PivotPainterSettings