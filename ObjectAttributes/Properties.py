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

class OBJECTATTRIBUTES_PG_TexChannelPropertyGroup(PropertyGroup):
    """ """
    channel_modes = [
        ("NONE", "None", "Write 0 to the channel"),
        ("POSITION", "Position", "X/Y/Z component of the object's position"),
        ("AXIS", "Axis", "X/Y/Z component of the object's forward/right/up vector"),
        ("EXTENTS", "Extents", "Length of the object along its forward/right/up vector"),
        ("HIERARCHY", "Hierarchy", "Object's linear index in the hierarchy"),
        ("CUSTOM_PROP", "Custom Property", "Object's Float/Integer custom property"),
        ("QUATERNION", "Quaternion", "X/Y/Z/W component of the object's orientation, or the XYZW components bit-packed into a single float using the smallest-three method")
    ]
    channel_mode : EnumProperty( items=channel_modes, name="Mode", description= "", default="NONE")

    component_x_y_z = [
        ("X", "X", "The vector's X component"),
        ("Y", "Y", "The vector's Y component"),
        ("Z", "Z", "The vector's Z component")
    ]
    component: EnumProperty(name="Component", items=component_x_y_z, default="X", description="Component to bake")

    quat_x_y_z_w = [
        ("X", "X", "The quaternion's X component"),
        ("Y", "Y", "The quaternion's Y component"),
        ("Z", "Z", "The quaternion's Z component"),
        ("W", "W", "The quaternion's W component"),
        ("XYZW", "XYZW", "The quaternion's XYZW components bit-packed into a single float using the smallest-three method"),
    ]
    quat: EnumProperty(name="Component", items=quat_x_y_z_w, default="XYZW", description="Component to bake")

    axis_x_y_z = [
        ("X", "Forward (X)", "X-axis"),
        ("Y", "Right (Y)", "Y-axis"),
        ("Z", "Up (Z)", "Z-axis")
    ]
    axis: EnumProperty(name="Axis", items=axis_x_y_z, default="X", description="Axis to bake")

    obj_modes = [
        ("SELF", "Self", "Each object gets data from itself, accounting for hierarchy depth limit, if any has been set. If the object is too deep in the hierarchy, the tree will be walked up to get its first available parent instead."),
        ("PARENT", "Parent", "Each object gets data from its parent, *not* accounting for hierarchy depth limit, if any has been set. Use with caution."),
        ("CUSTOM", "Custom", "Each object gets data from a user-specified object, if specified, from itself otherwise."),
    ]
    obj_mode: EnumProperty(name="Source", items=obj_modes, default="SELF", description="Source object to use")
    obj: PointerProperty(type=bpy.types.Object, name="Object", description="")

    depth: IntProperty(name="Depth", default=1, min=1, description="1 to bake the element index of the parent, 2 for the grand-parent, etc.")

    name: StringProperty(name="Name", default="")

    remapping: BoolProperty(name="Remap", default=False, description="Enable to remap values stored in this channel from their initial [-min:max] range to [0:1] which can later be brought back to their initial range using the reported offset and range values. This may allow 8-bit RGBA textures to be used for storing data.")

class OBJECTATTRIBUTES_PG_TexLayerPropertyGroup(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")

    R: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    G: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    B: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    A: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)

class OBJECTATTRIBUTES_PG_SettingsPropertyGroup(PropertyGroup):
    """ """
    textures: CollectionProperty(type=OBJECTATTRIBUTES_PG_TexLayerPropertyGroup)
    textures_selected_index: IntProperty(name="Selected", default=0)

    depth_limit_use: BoolProperty(name="Limit Depth", default=True, description="Enable this option to prevent the hierarchy from becoming too deep. At the specified depth, children will be treated as part of their parent and will share the parent’s object data—such as position, axis, and more—as if they were part of the same mesh. Non-mesh objects within the hierarchy will be discarded and treated as if they do not exist by the algorithm, without affecting the transforms of their children")
    depth_limit: IntProperty(name="Limit", default=3, min=0, description="Specifies the maximum depth allowed for the hierarchy. A value of 1 allows the tree to contain a parent and its children; a value of 2 includes a parent, children, and grandchildren, and so on")
    use_pivot_painter_packing: BoolProperty(name="Use Pivot Painter Packing", default=True, description="Enable the use of Pivot Painter’s 16-bit integer to 16-bit float packing algorithm to store the index. If disabled, the index will be stored as-is in a float. When packing is enabled, the index must be decoded before use; otherwise, it can be read directly. Note that 16-bit floats can only reliably store integers as-is up to 2048")

    mesh_name: StringProperty(name="Name", default="BakedMesh.OA", description="Name of the resulting baked mesh")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.OA", description="UVMap to get or create for setting up the mesh UVs")
    mesh_count_limit: IntProperty(name="Limit", default=32768, description="Cancel the bake if the amount of objects to bake exceed this limit. This is because Pivot Painter's algorithm has limited precision")
    mesh_merge: BoolProperty(name="Merge", default=True, description="Enable merging of the duplicated selection once baking is complete. Otherwise, keep them separated to allow for additional bakes on the individual objects")
    mesh_duplicate: BoolProperty(name="Duplicate", default=True, description="Enable this option to preserve the original selection and bake data on the duplicated mesh. Disable it at your own risk—doing so will modify the selection, which may lead to unwanted changes to the source data and unpredictable bake results if data blocks are shared")
    mesh_single_user: BoolProperty(name="Single User", default=True, description="If the selection isn't duplicated, the bake may not work as expected when data blocks are shared. This ensures that meshes are made 'single user' to prevent conflicts during the baking process")

    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert UVMap's V axis & flip VAT texture(s) upside down (typically True for exporting to UE or DirectX apps in general, False for Unity or OpenGL apps in general)")
    origin_obj: PointerProperty(type=bpy.types.Object, name="Origin", description="Optional object to use as the baking origin instead of the world origin. It takes into account the object's location, rotation, and scale, which may lead to unexpected results. For this reason, it's considered experimental, but it might be useful in rare cases")

    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")

    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended). Only available if the Blender file is saved")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the XML file name and path are generated")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported XML file (without the .xml extension)")
    export_xml_file_path: StringProperty(name="Path", default="//", description="Path for the exported XML file, excluding the file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .xml file")

    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion. Only available if the Blender file is saved")
    export_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_<TextureName>", description="Name for the texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name. <TextureName> is a placeholder tag that can be used to be replaced with the texture's custom name")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")
    export_tex_max_width: IntProperty(name="Max Width", min=2, max=8192, default=256, description="Maximum allowed texture width. Exceeding this may cancel the bake. 256 is recommended, as 256^2 allows the baking of up to 65K of elements, more than the precision offered by Pivot Painter's packing algorithm")
    export_tex_max_height: IntProperty(name="Max Height", min=2, max=8192, default=256, description="Maximum allowed texture height. Exceeding this may cancel the bake. 256 is recommended, as 256^2 allows the baking of up to 65K of elements, more than the precision offered by Pivot Painter's packing algorithm")

    tex_force_power_of_two: BoolProperty(name="Power of Two", default=False, description="Force textures to be power-of-two sizes. Not recommended, as non-power-of-two textures ensure tight packing and are widely supported")
    tex_force_power_of_two_square: BoolProperty(name="Square", default=False, description="Force texture width and height to be equal if 'Power of Two' is enabled. Typically unnecessary, but provided as an option for specific use cases")

class OBJECTATTRIBUTES_PG_TexLayerReportPropertyGroup(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")
    exported: BoolProperty(name="Exported", default=False)
    path: StringProperty(name="Texture Filepath", default="//", description="", subtype='FILE_PATH')
    img: PointerProperty(type=bpy.types.Image)

    R: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    R_range_offset: FloatProperty(name="Offset", default=0.0)
    R_range: FloatProperty(name="Range", default=1.0)
    R_range_valid: BoolProperty(name="Valid", default=False)
    G: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    G_range_offset: FloatProperty(name="Offset", default=0.0)
    G_range: FloatProperty(name="Range", default=1.0)
    G_range_valid: BoolProperty(name="Valid", default=False)
    B: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    B_range_offset: FloatProperty(name="Offset", default=0.0)
    B_range: FloatProperty(name="Range", default=1.0)
    B_range_valid: BoolProperty(name="Valid", default=False)
    A: PointerProperty(type=OBJECTATTRIBUTES_PG_TexChannelPropertyGroup)
    A_range_offset: FloatProperty(name="Offset", default=0.0)
    A_range: FloatProperty(name="Range", default=1.0)
    A_range_valid: BoolProperty(name="Valid", default=False)

class OBJECTATTRIBUTES_PG_ReportPropertyGroup(PropertyGroup):
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
    unit_invert_v: BoolProperty(name="Invert V", default=False, description="")
    origin_obj: PointerProperty(type=bpy.types.Object, name="Origin", description="")

    depth_limit_use: BoolProperty(name="Limit Depth", default=True, description="")
    depth_limit: IntProperty(name="Limit", default=3, min=1, description="")
    use_pivot_painter_packing: BoolProperty(name="Use Pivot Painter Packing", default=True, description="")

    mesh: PointerProperty(type=bpy.types.Object, description="")
    mesh_export: BoolProperty(name="Mesh Exported", default=False, description="")
    mesh_path: StringProperty(name="Mesh Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_uvmap: IntProperty(name="UV Map", default=0, description="")
    mesh_num_indices: IntProperty(name="Num Indices", default=0, description="")

    tex_width: IntProperty(name="Texture Width", default=0, description="")
    tex_height: IntProperty(name="Texture Height", default=0, description="")
    textures: CollectionProperty(type=OBJECTATTRIBUTES_PG_TexLayerReportPropertyGroup)
    textures_selected_index: IntProperty(name="Selected", default=0)

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

def register():
	bpy.types.Scene.ObjectAttributesSettings = PointerProperty(type=OBJECTATTRIBUTES_PG_SettingsPropertyGroup)
	bpy.types.Scene.ObjectAttributesReport = PointerProperty(type=OBJECTATTRIBUTES_PG_ReportPropertyGroup)

def unregister():
	del bpy.types.Scene.ObjectAttributesSettings