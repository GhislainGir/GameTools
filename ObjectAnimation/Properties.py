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

import mathutils
from typing import NamedTuple

class ProcessedTransform(NamedTuple):
    loc: mathutils.Vector
    Quaternion: mathutils.Quaternion
    RotationAxis: mathutils.Vector
    RotationAngle: float
    Scale: mathutils.Vector

#############################################################################################
###################################### PROPERTY GROUPS ######################################
#############################################################################################

################
### SETTINGS ###
class OATBAKER_PG_SettingsTexChannel(PropertyGroup):
    """ """
    channel_modes = [
        ("NONE", "None", "Write 0 to the channel"),
        ("POSITION", "Position", "Object position"),
        ("ROTATION", "Rotation", "Object rotation"),
        ("SCALE", "Scale", "Object scale"),
        ("AXIS", "Axis", "Object axis"),
        ("CUSTOM_PROP", "Custom Property", "Object custom property"),
    ]
    channel_mode: EnumProperty(items=channel_modes, name="Mode", default="NONE", description="")

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
        ("XYZW", "XYZW", "The quaternion's XYZW components bit-packed into a single float using the smallest-three method. This requires a 32-bit HDR texture!"),
    ]
    quat: EnumProperty(name="Component", items=quat_x_y_z_w, default="XYZW", description="Component to bake")

    quat_xyz_orders = [
         ("XYZ", "XYZ", "XYZ"),
         ("XZY", "XZY", "XZY"),
         ("YXZ", "YXZ", "YXZ"),
         ("YZX", "YZX", "YZX"),
         ("ZXY", "ZXY", "ZXY"),
         ("ZYX", "ZYX", "ZYX")
    ]
    quat_xyz_order: EnumProperty(name="Order", items=quat_xyz_orders, default="XYZ", description="Basis for the quaternion")
    override_xyz_order: BoolProperty(name="Override", default=False, description="Override the global mesh axis order setting")

    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied before global X/Y/Z axis inversion)")

    quat_angle_unit_modes = [
        ("UNIT", "Unit", "Angle is normalized in [0:1] range, 1.0 for 360 degrees"),
        ("DEGREES", "Degrees", "Angle is in degrees in [0:360] range"),
        ("RADIANS", "Radians", "Angle is in radians in [0:TwoPi] range")
    ]
    quat_angle_unit_mode: EnumProperty(name="Unit", items=quat_angle_unit_modes, default="UNIT", description="Select the type of unit for the angle: unit, degrees or radians")

    rot_modes = [
        ("QUAT", "Quaternion", ""),
        ("AXIS_ANGLE", "Axis & Angle", ""),
    ]
    rot_mode: EnumProperty(name="Mode", items=rot_modes, default="AXIS_ANGLE", description="")

    axis_x_y_z = [
        ("X", "Forward (X)", "X-axis"),
        ("Y", "Right (Y)", "Y-axis"),
        ("Z", "Up (Z)", "Z-axis")
    ]
    axis: EnumProperty(name="Axis", items=axis_x_y_z, default="X", description="Axis to bake")

    axis_angle_modes = [
        ("AXIS_X", "Axis X", ""),
        ("AXIS_Y", "Axis Y", ""),
        ("AXIS_Z", "Axis Z", ""),
        ("ANGLE", "Angle", ""),
    ]
    axis_angle_mode: EnumProperty(name="Component", items=axis_angle_modes, default="AXIS_X", description="")

    axis_scaled: BoolProperty(name="Scale", default=False, description="Include object scale in forward/right/up axes. Rotation can still be applied by normalizing vectors")

    remapping: BoolProperty(name="Remap", default=False, description="Enable to remap values stored in this channel from their initial [-min:max] range to [0:1] which can later be brought back to their initial range using the reported offset and range values. This may allow 8-bit RGBA textures to be used for storing data.")

    name: StringProperty(name="Name", default="", description="")

    obj_modes = [
        ("SELF", "Self", "Data is fetched from the object itself"),
        ("PARENT", "Parent", "Data is fetched from the object's parent, if it has at least one, at the specified depth, if possible: 1 is the immediate parent, 2 grandparent, etc. It stops at the last valid parent and falls back to itself if no parent at all"),
        ("CUSTOM", "Custom", "Data is fetched from the a shared, user-specified object. Falls back to itself if none is set"),
        ("PROPERTY", "Property", "Data is fetched from the object targeted by a custom object property stored in the object itself. Falls back to itself if no property name is set, or if said property isn't itself set to point to a valid object")
    ]
    obj_mode: EnumProperty(name="Source", items=obj_modes, default="SELF", description="Source object to use. This will account for any depth limit set, meaning it'll try to walk up the hierarchy to find the first valid parent, regardless of what the source is or if it is even parented to begin with. Falls back to 'Self' is other source can't be resolved")
    obj: PointerProperty(type=bpy.types.Object, name="Object", description="Target object")
    obj_prop: StringProperty(name="Property", default="SourceObject", description="Name of the custom property stored in the objects to bake, to point to the desired targets")

class OATBAKER_PG_SettingsTexLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")

    R: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    G: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    B: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    A: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)

class OATBAKER_PG_SettingsNLAClip(PropertyGroup):
    """ """
    name: StringProperty(name="Name", default="")

class OATBAKER_PG_Settings(PropertyGroup):
    """ """

    textures: CollectionProperty(type=OATBAKER_PG_SettingsTexLayer)
    textures_selected_index: IntProperty(name="Selected", default=0)

    # scene 
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip the OAT texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied after inversion)")
    origin_obj: PointerProperty(type=bpy.types.Object, name="Origin", description="Optional object to use as the baking origin instead of the world origin. It takes into account the object's location, rotation, and scale, which may lead to unexpected results. For this reason, it's considered experimental, but it might be useful in rare cases")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.OAT", description="Name of the baked object")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData.OAT", description="Name of the UVMap to be created or used for baking mesh UVs")
    mesh_target_prop: StringProperty(name="Property", default="BakeTarget", description="Custom property name for the custom source feature (to query data from an object targeted using a data-block custom property in an object)")
    mesh_materials: BoolProperty(name="Materials", default=True, description="Enable to copy materials")
    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")
    require_triangulation: BoolProperty(name="Require Triangulation", default=False, description="Enable to enforce triangulation, potentially improving remapping stability")
    previz_result: BoolProperty(name="Previz", default=False, description="Enable to add a geometry node modifier to the baked mesh for previewing baked offsets and normals after bake completion")
    previz_bounds: BoolProperty(name="Bounds", default=True, description="Enable to display the animation bounds after bake completion")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="Enable to export an XML file containing information about the bake process (recommended). Only available if the Blender file is saved")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same FBX file name and path for the XML file. Defaults to 'Custom' if mesh is not exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom XML file name and path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the XML file name and path are generated")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported XML file (without the .xml extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_xml_file_path: StringProperty(name="Path", default="//", description="Path for the exported XML file, excluding the file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .xml file")

    # frames
    frame_range_modes = [
            ("NLA", "NLA", "Use the frame range from the NLA track of the animation. This mode works if the mesh is in an NLA track or parented to an armature with one. This will also apply the frame step per animation, ensuring the first frame is included"),
            ("SCENE", "Scene", "Use the scene's frame range (start and end frames are inclusive)"),
            ("CUSTOM", "Custom", "Use a custom frame range (start and end frames are inclusive)"),
        ]
    frame_range_mode: EnumProperty(name="Mode", items=frame_range_modes, default=0, description="Select how the frame range is derived")
    frame_range_nla_exclusion: CollectionProperty(type=OATBAKER_PG_SettingsNLAClip)
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
    frame_padding_modes = [
        ('PREFIX', 'Prefix', 'Add the last frame before the first frame'),
        ('SUFFIX', 'Suffix', 'Add the first frame after the last frame'),
        ('PREFIX_SUFFIX', 'Prefix & Suffix', 'Add both the last frame before the first frame and the first frame after the last frame (recommended if unsure)')
    ]
    frame_padding_mode: EnumProperty(name="Mode", items=frame_padding_modes, default=1, description="Select how padding is applied to frame data")
    frame_padding: IntProperty(name="Padding", min=0, default=0, description="Padding used to prevent blending between the end frame of one animation and the start frame of another. One frame of padding is typically enough. Note that this may cause issues if baking multiple objects with different NLA tracks")
    frame_ref_padding: BoolProperty(name="Ref Padding", default=True, description="This setup isolates the baked animation from the reference pose by inserting the last frame before the first, and the first frame after the last. This prevents the reference pose—stored in the very first frame—from being mistakenly interpolated with the first frame of the animation. While this approach duplicates two frames, it enables the use of interpolation without visual artifacts. It's recommended in most cases, but can be disabled if you're using Nearest sampling or if individual padding is applied to each NLA clip")
    frame_ref_modes = [
        ("START", "Start", "Use the start frame as the reference frame"),
        ("END", "End", "Use the end frame as the reference frame"),
        ("CUSTOM", "Custom", "Use a custom frame as the reference frame"),
    ]
    frame_ref_mode: EnumProperty(name="Mode", items=frame_ref_modes, default="START", description="Select how the reference frame is computed")
    frame_ref_custom: IntProperty(name="Reference", default=1, description="Frame to use as the reference 'pose,' from which mappings and offsets are computed. Specifying a frame outside the animation range is allowed to specify a T-pose frame that should otherwise be excluded from the bake")
    
    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion. Only available if the Blender file is saved")
    export_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_<TextureName>", description="Name for the texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name. <TextureName> is a placeholder tag that can be used to be replaced with the texture's custom name")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")
    export_tex_max_width: IntProperty(name="Max Width", min=2, max=8192, default=4096, description="Maximum allowed texture width. Exceeding this may cancel the bake due to an excess of vertices or frames")
    export_tex_max_height: IntProperty(name="Max Height", min=2, max=8192, default=4096, description="Maximum allowed texture height. Exceeding this may cancel the bake due to an excess of vertices or frame")

    tex_force_power_of_two: BoolProperty(name="Power of Two", default=False, description="Force textures to be power-of-two sizes. Not recommended, as non-power-of-two textures ensure tight packing and are widely supported. May lead to overflow issues when vertices exceed the image width, resulting in multiple rows per frame. Extra space handling can be controlled with the 'Stack Mode' option")
    tex_force_power_of_two_square: BoolProperty(name="Square", default=False, description="Force texture width and height to be equal if 'Power of Two' is enabled. Typically unnecessary, but provided as an option for specific use cases. Extra space handling can be controlled with the 'Stack Mode' option")
    tex_packing_modes = [
        ('CONTINUOUS', 'Continuous (Experimental)', "Store subsequent frame data directly after the previous frame in the texture, ensuring tight packing but requiring a more complex playback algorithm (frame data may start at arbitrary locations and span multiple lines)"),
        ('STACK', 'Stack', 'Skip remaining pixels and place the next frame on the next line (stack), simplifying playback but reducing packing efficiency and limiting texture space for vertex data')
    ]

    tex_packing_mode: EnumProperty(name="Mode", items=tex_packing_modes, default=1, description="Control how frames are arranged in the texture when there’s extra space (underflow) or not enough space (overflow). \n\nUnderflow occurs when the number of vertices per frame is less than the image width, causing gaps at the end of the line ('Power of Two' might cause this). \n\nOverflow happens when there are too many vertices for a single line, and the data is spread across multiple lines, possibly leaving gaps. \n\nThis setting determines how to handle these empty spaces")
    
    tex_packing_stack_modes = [
        ('ADJACENT', 'Adjacent', 'Rows are stacked on top of each other, which simplifies playback in the vertex shader but prevents the use of pixel interpolation for frame interpolation'),
        ('OFFSET', 'Offset', 'Rows are offset by the full animation length, making playback in the vertex shader more complex but allowing pixel interpolation to be used for frame interpolation'),
    ]
    tex_packing_stack_mode: EnumProperty(name="Stack Mode", items=tex_packing_stack_modes, default="OFFSET", description="Select the stack method")

##############
### REPORT ###
class OATBAKER_PG_ReportAnim(PropertyGroup):
    """ """
    name: StringProperty(name="Name", default="", description="")
    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")

class OATBAKER_PG_ReportTexLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")
    exported: BoolProperty(name="Exported", default=False)
    path: StringProperty(name="Texture Filepath", default="//", description="", subtype='FILE_PATH')
    img: PointerProperty(type=bpy.types.Image)

    R: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    R_range_offset: FloatProperty(name="Offset", default=0.0)
    R_range: FloatProperty(name="Range", default=1.0)
    R_range_valid: BoolProperty(name="Valid", default=False)
    G: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    G_range_offset: FloatProperty(name="Offset", default=0.0)
    G_range: FloatProperty(name="Range", default=1.0)
    G_range_valid: BoolProperty(name="Valid", default=False)
    B: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    B_range_offset: FloatProperty(name="Offset", default=0.0)
    B_range: FloatProperty(name="Range", default=1.0)
    B_range_valid: BoolProperty(name="Valid", default=False)
    A: PointerProperty(type=OATBAKER_PG_SettingsTexChannel)
    A_range_offset: FloatProperty(name="Offset", default=0.0)
    A_range: FloatProperty(name="Range", default=1.0)
    A_range_valid: BoolProperty(name="Valid", default=False)

class OATBAKER_PG_Report(PropertyGroup):
    """ """

    textures: CollectionProperty(type=OATBAKER_PG_ReportTexLayer)
    textures_selected_index: IntProperty(name="Selected", default=0)

    baked: BoolProperty(name="Baked", default=False, description="")
    success: BoolProperty(name="Success", default=False, description="")
    msg: StringProperty(name="Message", default="", description="")
    name: StringProperty(name="Name", default="", description="")
    ID: StringProperty(name="ID", default="", description="")

    unit_system: StringProperty(name="System", default="", description="")
    unit_unit: StringProperty(name="Unit", default="", description="")
    unit_length: FloatProperty(name="Length", default=0.0, description="")
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip the OAT texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied after inversion)")
    origin_obj: PointerProperty(type=bpy.types.Object, name="Origin", description="Optional object to use as the baking origin instead of the world origin. It takes into account the object's location, rotation, and scale, which may lead to unexpected results. For this reason, it's considered experimental, but it might be useful in rare cases")

    padded: BoolProperty(name="Padded", default=False, description="")
    padding: IntProperty(name="Padding", default=0, description="")
    padding_mode: StringProperty(name="Sampling", default="", description="")
    frame_ref_mode: StringProperty(name="Frame Ref Mode", default="", description="")
    frame_ref: IntProperty(name="Frame Ref", default=1, description="")
    frame_ref_padding: BoolProperty(name="Ref Padding", default=False, description="")
    anims: CollectionProperty(type=OATBAKER_PG_ReportAnim)
    selected_anim: IntProperty(name="Selected Anim", default=0, description="")

    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")
    num_frames: IntProperty(name="Count", default=0, description="")
    num_frames_padded: IntProperty(name="Padded", default=0, description="")
    frame_step: IntProperty(name="Frame Step", default=0, description="")
    frame_step_mode: StringProperty(name="Step Mode", default="", description="")
    frame_rate: FloatProperty(name="FPS", default=24.0, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_uvmap_index: IntProperty(name="UV Index", default=0, description="")
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")

    tex_width: IntProperty(name="Width", default=0, description="")
    tex_frame_width: FloatProperty(name="Frame Width", default=0, description="")
    tex_height: IntProperty(name="Height", default=0, description="")
    tex_frame_height: FloatProperty(name="Frame Height", default=0, description="")
    tex_underflow: BoolProperty(name="Underflow", default=False, description="")
    tex_overflow: BoolProperty(name="Overflow", default=False, description="")
    tex_sampling_mode: StringProperty(name="Sampling", default="", description="")
    tex_packing_stack_mode: StringProperty(name="Stack Mode", default="", description="")

    xml: BoolProperty(name="XML", default=False, description="")
    xml_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

def register():
    bpy.types.Scene.OATBakerSettings = PointerProperty(type=OATBAKER_PG_Settings)
    bpy.types.Scene.OATBakerReport = PointerProperty(type=OATBAKER_PG_Report)

def unregister():
    del bpy.types.Scene.OATBakerSettings
    del bpy.types.Scene.OATBakerReport