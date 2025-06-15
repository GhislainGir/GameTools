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
################
### SETTINGS ###
class SDFBAKER_PG_Settings(PropertyGroup):
    """ """

    sdf_modes = [
        ("BOUNDS", "Selection", "The volume automatically encapsulates all selected meshes, with an optional extra offset in X, Y, and Z"),
        ("CUSTOM", "Custom", "The volume is based on the bounding box of a specified mesh or empty. If an empty is used, the volume is derived from its display size and scale and centered on its position")
    ]
    sdf_mode: EnumProperty(name="Bounds", items=sdf_modes, default="BOUNDS", description="Control how the sdf volume is computed")
    sdf_bounds: PointerProperty(name="Object", type=bpy.types.Object, description="Custom mesh to use for computing the bounds. An empty can also be used—in that case, the bounds are derived from the empty's display size, multiplied by its scale, and centered on its position. This object will be excluded from the bake!")

    frames: IntProperty(name="Slices Per Row", min=1, max=1024, default=8, description="Specify how many Z slices to distribute along the U axis in the texture. For example, if you're baking 64 voxels in Z and set this value to 8, the result will be an evenly distributed 8×8 texture. If set to 10, it will produce a 10×7 layout, with 4 empty tiles in the last row")
    x: IntProperty(name="X", min=1, max=1024, default=32, description="Amount of voxels to bake in the X axis")
    y: IntProperty(name="Y", min=1, max=1024, default=32, description="Amount of voxels to bake in the Y axis")
    z: IntProperty(name="Z", min=1, max=1024, default=64, description="Amount of voxels to bake in the Z axis")

    offset: FloatVectorProperty(name="Offset", default=(1.0, 1.0, 1.0), description="Specifies how much to extend the bounds, allowing voxels to be generated outside the selection's bounds (in Blender units, on each side)")

    distance_modes = [
        ('REAL', 'Actual', 'Encode distances as-is, using the original units they were computed in'),
        ('NORMALIZED', 'Normalized', 'Normalize distances to the range [-1, 1]. The reported "Maximum Distance" can be used to remap the normalized values back to their original range'),
        ('REMAPPED', 'Normalized & Remapped', 'Normalize and remap distances to the range [0, 1]. The reported "Maximum Distance", along with a constant bias scale, can be used to remap the normalized values back to their original range')
    ]
    distance_mode: EnumProperty(name="Distance", items=distance_modes, default="REAL", description="Control how distances are encoded in the texture")

    tile_sort_modes = [
        ('TB_LR', 'Top Bottom, Left Right', ''),
        ('TB_RL', 'Top Bottom, Right Left', ''),
        ('BT_LR', 'Bottom Top, Left Right', ''),
        ('BT_RL', 'Bottom Top, Right Left', '')
    ]
    tile_sort_mode: EnumProperty(name="Slices", items=tile_sort_modes, default="BT_LR", description="Control how the tiles/z-slices are distributed in the texture. 'Bottom Top' is typically required for Unreal Engine or DirectX apps for the top most slice(s) to end up in the Top row, as the mesh(es) are scanned from bottom to top")
    invert_sign: BoolProperty(name="Invert Sign", default=False, description="Flip the sign of the distance field (inside <> outside). Negative if inside and False, positive otherwise")
    two_sided: BoolProperty(name="Two Sided", default=False, description="Assume mesh(es) are double sided, ignoring sign and computing the absolute distance. Useful for flat geometry, non-closed geometry etc")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.SDF", description="Name of the resulting baked mesh")
    gen_selection_mesh: BoolProperty(name="Create Selection Mesh", default=True, description="Generate the mesh used for SDF computation (internally generated but destroyed afterward if False)")
    gen_debug_mesh: BoolProperty(name="Create Debug Mesh", default=False, description="Generate a mesh with a vertex for each sample point (useful for debugging)")
    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the SDF bounds to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved, or absolute otherwise", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")

    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap for each tile/z-slice. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps. This only affect each tile individually and doesn't affect the way they are sorted")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake. Only available if the Blender file is saved")
    export_xml_modes = [
        ("TEXPATH", "Texture Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if the texture is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the XML file name and path are generated")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported XML file (without the .xml extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_xml_file_path: StringProperty(name="Path", default="//", description="Path for the exported XML file, excluding the file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .xml file")

    # textures
    tex_file_name: StringProperty(name="Filename", default="T_<BakeName>", description="Name for the sdf texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated texture to an EXR file upon bake completion. Only available if the Blender file is saved")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file", subtype='FILE_PATH')
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")

##############
### REPORT ###
class SDFBAKER_PG_Report(PropertyGroup):
    """"""

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
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="")

    x: IntProperty(name="X", min=1, max=1024, default=32, description="")
    y: IntProperty(name="Y", min=1, max=1024, default=32, description="")
    z: IntProperty(name="Z", min=1, max=1024, default=64, description="")
    max_dist: FloatProperty(name="Max", default=0.0)

    distance_mode: StringProperty(name="Distance", default="")
    offset: FloatVectorProperty(name="Offset", default=(1.0, 1.0, 1.0))
    
    tile_sort_mode: StringProperty(name="Tile Sort Mode", default="")
    
    invert_sign: BoolProperty(name="Invert Sign", default=True, description="")
    two_sided: BoolProperty(name="Two Sided", default=False, description="")

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="")

    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="")
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")

    tex: PointerProperty(type=bpy.types.Image)
    tex_width: IntProperty(name="Texture Width", default=0)
    tex_height: IntProperty(name="Texture Height", default=0)
    tex_slices: IntProperty(name="Slices Per Row", default=0)
    tex_export: BoolProperty(name="Export", default=True, description="")
    tex_path: StringProperty(name="Path", default="//", description="")

def register():
    bpy.types.Scene.SDFBakerSettings = PointerProperty(type=SDFBAKER_PG_Settings)
    bpy.types.Scene.SDFBakerReport = PointerProperty(type=SDFBAKER_PG_Report)

def unregister():
    del bpy.types.Scene.SDFBakerSettings
    del bpy.types.Scene.SDFBakerReport
