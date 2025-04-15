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

from bpy.props import PointerProperty, BoolProperty, FloatProperty, EnumProperty, StringProperty, IntProperty, CollectionProperty, FloatVectorProperty
from bpy.types import PropertyGroup

#############################################################################################
###################################### PROPERTY GROUPS ######################################
#############################################################################################
class SDFBAKER_PG_SettingsPropertyGroup(PropertyGroup):
    """ """

    sdf_modes = [
        ("BOUNDS", "Selection Bounds", "Automatically derive SDF bounds from selection bounds, with optional offset"),
        ("CUSTOM", "Custom", "Use the bounds of a mesh")
    ]
    sdf_mode: EnumProperty(name="Mode", items=sdf_modes, default="BOUNDS", description="")
    sdf_bounds: PointerProperty(name="Bounds", type=bpy.types.Object, description="Custom mesh to use for computing bounds. Empty may be used, in which case bounds will be derived from empty's display size, multiplied by the empty's scale. This object will be excluded from the bake!")

    frames: IntProperty(name="Slices Per Row", min=2, max=1024, default=8, description="How many Z slices to distribute along the U axis in the texture. Assuming you want to bake 64 voxels in Z, a value of 8 will generate an evenly distributed 8 by 8 texture. A value 10 will generate a 10 by 7 texture with 4 empty tiles in the last row")
    x: IntProperty(name="X", min=2, max=1024, default=32, description="")
    y: IntProperty(name="Y", min=2, max=1024, default=32, description="")
    z: IntProperty(name="Z", min=2, max=1024, default=64, description="")

    offset: FloatVectorProperty(name="Offset", default=(1.0, 1.0, 1.0), description="How much bounds are extended, allowing to generate voxels outside the selection (in Blender unit, on each side)")
    normalize: BoolProperty(name="Normalize", default=False, description="Normalize the signed distance field to a [-1:1] range")
    remap: BoolProperty(name="Remap", default=False, description="Remap the signed distance field to a [0:1] range. 0.5 on the surface, 1 the most distant, outside, 0 the most distant, inside")

    tile_sort_modes = [
        ('TB_LR', 'Top Bottom, Left Right', ''),
        ('TB_RL', 'Top Bottom, Right Left', ''),
        ('BT_LR', 'Bottom Top, Left Right', ''),
        ('BT_RL', 'Bottom Top, Right Left', '')
    ]
    tile_sort_mode: EnumProperty(name="Slices", items=tile_sort_modes, default="BT_LR", description="Control how the tiles/z-slices are distributed in the texture")
    invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip each tile upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.SDF", description="Name of the resulting baked mesh")
    gen_selection_mesh: BoolProperty(name="Keep Copy", default=True, description="Keep mesh resulting from the bake")
    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the SDF bounds to an FBX file upon bake completion")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="Name for the exported FBX file (without the .fbx extension). <ObjectName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved, or absolute otherwise", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")

    scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended)")
    export_xml_modes = [
        ("TEXPATH", "Texture Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the xml file name & path is computed")
    export_xml_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="XML file name, without extension")
    export_xml_file_path: StringProperty(name="Path", default="//", description="XML file path, not including file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="True to override any existing .xml file")

    # textures
    tex_file_name: StringProperty(name="Filename", default="T_<ObjectName>", description="Name for the vertex offset texture file (without the .exr extension)")
    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved, or absolute otherwise", subtype='FILE_PATH')
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")

class SDFBAKER_PG_ReportPropertyGroup(PropertyGroup):
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

    frames: IntProperty(name="Z Slices Per Row", min=2, max=1024, default=8, description="How many Z slices to distribute along the U axis in the texture. Assuming you want to bake 64 voxels in Z, a value of 8 will generate an evenly distributed 8 by 8 texture. A value 10 will generate a 10 by 7 texture with 4 empty tiles in the last row")
    x: IntProperty(name="X", min=2, max=1024, default=32, description="")
    y: IntProperty(name="Y", min=2, max=1024, default=32, description="")
    z: IntProperty(name="Z", min=2, max=1024, default=64, description="")
    max_dist: FloatProperty(name="Max", default=0.0)

    offset: FloatVectorProperty(name="Offset", default=(1.0, 1.0, 1.0))
    normalize: BoolProperty(name="Normalize", default=False, description="Normalize the signed distance field to a [-1:1] range")
    remap: BoolProperty(name="Remap", default=False, description="Remap the signed distance field to a [0:1] range, 0.5 is on the surface, 1 is the most distant, outside, 0 is the most distant inside")

    tile_sort_mode: StringProperty(name="Tile Sort Mode", default="")
    invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip each tile upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps.")

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

    scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

    tex: PointerProperty(type=bpy.types.Image)
    tex_width: IntProperty(name="Texture Width", default=0)
    tex_height: IntProperty(name="Texture Height", default=0)
    tex_slices: IntProperty(name="Slices Per Row", default=0)
    tex_export: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion")
    tex_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved, or absolute otherwise", subtype='FILE_PATH')

def register():
    bpy.types.Scene.SDFBakerSettings = PointerProperty(type=SDFBAKER_PG_SettingsPropertyGroup)
    bpy.types.Scene.SDFBakerReport = PointerProperty(type=SDFBAKER_PG_ReportPropertyGroup)

def unregister():
    del bpy.types.Scene.SDFBakerSettings
    del bpy.types.Scene.SDFBakerReport
