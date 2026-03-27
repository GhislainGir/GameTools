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
class TATBAKER_PG_SettingsNLAClip(PropertyGroup):
    """ """
    name: StringProperty(name="Name", default="")

class TATBAKER_PG_Settings(PropertyGroup):
    """ """

    bake_modes = [
        ("ANIMATION", "Animation", "Bake triangle animation data based on the selected object evaluated at each frame. Triangle count may vary across frames; the frame with the most triangles determines the texture width"),
        ("MESHSEQUENCE", "Mesh Sequence", "Bake triangle animation data based on the selected mesh sequence. Frame order must be deducible from the objects names (.000, .001 etc). Triangle count may vary across meshes")
    ]
    bake_mode: EnumProperty(name="Mode", items=bake_modes, default=0, description="Select how the triangle animation data is baked")

    # scene
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip the TAT texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied after inversion)")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.TAT", description="Name of the baked object")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData.TAT", description="Name of the UVMap created on the generated triangle buffer mesh")
    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")
    previz_bounds: BoolProperty(name="Bounds", default=True, description="Enable to display the animation bounds after bake completion")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="Enable to export an XML file containing information about the bake process (recommended). Only available if the Blender file is saved")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same FBX file name and path for the XML file. Defaults to 'Custom' if mesh is not exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom XML file name and path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the XML file name and path are generated")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported XML file (without the .xml extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_xml_file_path: StringProperty(name="Path", default="//", description="Path for the exported XML file, excluding the file name", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    export_xml_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .xml file")

    # frames
    frame_range_modes = [
            ("NLA", "NLA", "Use the frame range from the NLA track of the animation. This mode works if the mesh is in an NLA track or parented to an armature with one. This will also apply the frame step per animation, ensuring the first frame is included"),
            ("SCENE", "Scene", "Use the scene's frame range (start and end frames are inclusive)"),
            ("CUSTOM", "Custom", "Use a custom frame range (start and end frames are inclusive)"),
        ]
    frame_range_mode: EnumProperty(name="Mode", items=frame_range_modes, default=0, description="Select how the frame range is derived")
    frame_range_nla_exclusion: CollectionProperty(type=TATBAKER_PG_SettingsNLAClip)
    frame_range_nla_exclusion_selected_index: IntProperty(name="Selected", min=0, default=0, description="")
    frame_range_nla_exclusion_selected: StringProperty(name="Name", default="Clip", description="")
    frame_range_custom_start: IntProperty(name="Start", min=1, default=1, description="Start frame (inclusive)")
    frame_range_custom_end: IntProperty(name="End", min=2, default=25, description="End frame (inclusive)")
    frame_range_custom_step: IntProperty(name="Step", min=1, default=1, description="Bake every nth frame")
    frame_range_custom_step_modes = [
        ("GLOBAL", "Global", "Bake every nth frame, starting from the Start Frame"),
        ("NLACLIP", "NLA Clip", "Bake every nth frame, starting from each NLA clip's Start Frame. This ensures the first frame of each animation clip is included, which *may* cause issues when baking multiple objects with different NLA strips")
    ]
    frame_range_custom_step_mode: EnumProperty(name="Mode", items=frame_range_custom_step_modes, default="NLACLIP", description="Select how the frame step is applied")

    # textures
    position_tex: BoolProperty(name="Position", default=True, description="Enable to bake the triangle position texture")
    position_tex_remap: BoolProperty(name="Remap", default=False, description="Enable to remap the positions within a [0:1] range. This requires a multiplier and bias to remap the positions in your shader or game engine. It is NOT recommended unless you intend to experiment with storing positions in 8-bit RGBA textures, as this will likely result in significant precision loss and visible deformation. Proceed at your own risk")
    position_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Position", description="Name for the triangle position texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    normal_tex: BoolProperty(name="Normal", default=True, description="Enable to bake the triangle normal texture (face normals)")
    normal_tex_remap: BoolProperty(name="Remap", default=True, description="Enable to remap the normals within a [0:1] range. This requires a constant bias to remap the normals in your shader or game engine")
    normal_tex_remap_biasscale: BoolProperty(name="Bias Scale", default=True, description="Remap normals using a simple constant bias and scale, assuming they fully span the [-1, 1] range")
    normal_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Normal", description="Name for the triangle normal texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion. Only available if the Blender file is saved")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")
    export_tex_max_width: IntProperty(name="Max Width", min=2, max=8192, default=4096, description="Maximum allowed texture width. Exceeding this may cancel the bake due to an excess of triangles or frames")
    export_tex_max_height: IntProperty(name="Max Height", min=2, max=8192, default=4096, description="Maximum allowed texture height. Exceeding this may cancel the bake due to an excess of triangles or frames")

    tex_force_power_of_two: BoolProperty(name="Power of Two", default=False, description="Force textures to be power-of-two sizes")
    tex_force_power_of_two_square: BoolProperty(name="Square", default=False, description="Force texture width and height to be equal if 'Power of Two' is enabled")

##############
### REPORT ###
class TATBAKER_PG_ReportAnimObj(PropertyGroup):
    """ """
    obj: PointerProperty(type=bpy.types.Object)

class TATBAKER_PG_ReportAnim(PropertyGroup):
    """ """
    objs: CollectionProperty(type=TATBAKER_PG_ReportAnimObj)
    selected_obj: IntProperty(name="Selected Obj", default=0, description="")
    name: StringProperty(name="Name", default="", description="")
    start_frame: IntProperty(name="Start", default=0, description="")
    start_time: FloatProperty(name="Start", default=0.0)
    end_frame: IntProperty(name="End", default=0, description="")
    end_time: FloatProperty(name="End", default=0.0)

class TATBAKER_PG_Report(PropertyGroup):
    """ """
    baked: BoolProperty(name="Baked", default=False, description="")
    success: BoolProperty(name="Success", default=False, description="")
    msg: StringProperty(name="Message", default="", description="")
    name: StringProperty(name="Name", default="", description="")
    ID: StringProperty(name="ID", default="", description="")

    unit_system: StringProperty(name="System", default="", description="")
    unit_unit: StringProperty(name="Unit", default="", description="")
    unit_length: FloatProperty(name="Length", default=0.0, description="")
    unit_scale: FloatProperty(name="Scale", default=0.0, description="")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="")
    unit_invert_y: BoolProperty(name="Invert Y", default=False, description="")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="")
    unit_invert_v: BoolProperty(name="Invert V", default=False, description="")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="")

    anims: CollectionProperty(type=TATBAKER_PG_ReportAnim)
    selected_anim: IntProperty(name="Selected Anim", default=0, description="")

    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")
    num_frames: IntProperty(name="Count", default=0, description="")
    frame_step: IntProperty(name="Frame Step", default=0, description="")
    frame_step_mode: StringProperty(name="Step Mode", default="", description="")
    frame_width: FloatProperty(name="Frame Width", default=0.0, description="")
    frame_height: FloatProperty(name="Frame Height", default=0.0, description="")
    frame_rate: FloatProperty(name="FPS", default=24.0, description="")

    num_triangles: IntProperty(name="Triangles", default=0, description="Maximum triangle count across all frames")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    mesh_uvmap_index: IntProperty(name="UV Index", default=0, description="")
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")
    tex_width: IntProperty(name="Width", default=0, description="")
    tex_height: IntProperty(name="Height", default=0, description="")
    tex_underflow: BoolProperty(name="Underflow", default=False, description="")
    tex_overflow: BoolProperty(name="Overflow", default=False, description="")
    tex_position: PointerProperty(type=bpy.types.Image)
    tex_position_export: BoolProperty(name="Position", default=False, description="")
    tex_position_path: StringProperty(name="Path", default="//", description="", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    tex_position_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_position_range_offset: FloatVectorProperty(name="Offset")
    tex_position_range: FloatVectorProperty(name="Range")

    tex_normal: PointerProperty(type=bpy.types.Image)
    tex_normal_export: BoolProperty(name="Normal", default=False, description="")
    tex_normal_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    tex_normal_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_normal_range_offset: FloatVectorProperty(name="Offset")
    tex_normal_range: FloatVectorProperty(name="Range")

    xml: BoolProperty(name="XML", default=False, description="")
    xml_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})

def register():
    bpy.types.Scene.TATBakerSettings = PointerProperty(type=TATBAKER_PG_Settings)
    bpy.types.Scene.TATBakerReport = PointerProperty(type=TATBAKER_PG_Report)

def unregister():
    del bpy.types.Scene.TATBakerSettings
    del bpy.types.Scene.TATBakerReport
