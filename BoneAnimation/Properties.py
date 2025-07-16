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
class BATBAKER_PG_SettingsSkinningTexChannel(PropertyGroup):
    """ """
    channel_modes = [
        ("NONE", "None", "Write 0 to the channel"),
        ("INDEX", "Index", "Bone index"),
        ("WEIGHT", "Weight", "Bone weight"),
    ]
    channel_mode: EnumProperty(items=channel_modes, name="Mode", default="NONE", description="Select the type of skinning data to write")
    index: IntProperty(name="Index", min=1, default=0, description="1 - most influential bone\n2 - second most influential bone\n3 - third most...")

    remapping: BoolProperty(name="Remap", default=False, description="Remap indices to [0:1] range to experiment with using an 8-bit skinning texture. This can only be done if number of deforming bones to bake is less than 256")

class BATBAKER_PG_SettingsSkinningTexRow(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Row", description="")

    R: PointerProperty(type=BATBAKER_PG_SettingsSkinningTexChannel)
    G: PointerProperty(type=BATBAKER_PG_SettingsSkinningTexChannel)
    B: PointerProperty(type=BATBAKER_PG_SettingsSkinningTexChannel)
    A: PointerProperty(type=BATBAKER_PG_SettingsSkinningTexChannel)

class BATBAKER_PG_SettingsSkinningTexLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="", description="")

    storage_modes = [
        ("TEXTURE", "Texture", ""),
        ("VCOL", "Vertex Color", ""),
    ]
    storage_mode: EnumProperty(name="Storage", items=storage_modes, default="TEXTURE", description="")

    rows: CollectionProperty(type=BATBAKER_PG_SettingsSkinningTexRow)
    rows_selected_index: IntProperty(name="Selected", default=0)

class BATBAKER_PG_SettingsAnimationTexChannel(PropertyGroup):
    """ """
    channel_modes = [
        ("NONE", "None", "Write 0 to the channel"),
        ("POSITION", "Position", "Bone position"),
        ("ROTATION", "Rotation", "Bone rotation"),
        ("SCALE", "Scale", "Bone scale"),
        ("AXIS", "Axis", "Bone axis"),
        ("CUSTOM_PROP", "Custom Property", "Bone custom property"),
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

    axis_scaled: BoolProperty(name="Scale", default=False, description="Include bone scale in forward/right/up axes. Rotation can still be applied by normalizing vectors")

    remapping: BoolProperty(name="Remap", default=False, description="Enable to remap values stored in this channel from their initial [-min:max] range to [0:1] which can later be brought back to their initial range using the reported offset and range values. This may allow 8-bit RGBA textures to be used for storing data.")

    name: StringProperty(name="Name", default="", description="")

class BATBAKER_PG_SettingsAnimationTexLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")

    R: PointerProperty(type=BATBAKER_PG_SettingsAnimationTexChannel)
    G: PointerProperty(type=BATBAKER_PG_SettingsAnimationTexChannel)
    B: PointerProperty(type=BATBAKER_PG_SettingsAnimationTexChannel)
    A: PointerProperty(type=BATBAKER_PG_SettingsAnimationTexChannel)

class BATBAKER_PG_SettingsNLAClip(PropertyGroup):
    """ """
    name: StringProperty(name="Name", default="")

class BATBAKER_PG_Settings(PropertyGroup):
    """ """
    skinning_textures: CollectionProperty(type=BATBAKER_PG_SettingsSkinningTexLayer)
    skinning_textures_selected_index: IntProperty(name="Selected", default=0)

    animation_textures: CollectionProperty(type=BATBAKER_PG_SettingsAnimationTexLayer)
    animation_textures_selected_index: IntProperty(name="Selected", default=0)

    # scene
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip the BAT texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.BAT", description="Name of the baked object")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData.BAT", description="Name of the UVMap to be created or used for baking mesh UVs")
    mesh_target_prop: StringProperty(name="Property", default="BakeTarget", description="Custom property name for the retargeting feature (to bake a high-res animated mesh to a low-res mesh)")
    mesh_materials: BoolProperty(name="Materials", default=True, description="Enable to copy materials")
    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")
    require_triangulation: BoolProperty(name="Require Triangulation", default=False, description="Enable to enforce triangulation, potentially improving remapping stability")
    previz_result: BoolProperty(name="Previz", default=True, description="Enable to add a geometry node modifier to the baked mesh for previewing baked bone transforms after bake completion")
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
    frame_range_nla_exclusion: CollectionProperty(type=BATBAKER_PG_SettingsNLAClip)
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
        ('PREFIX', 'Prefix', 'Add the last frame before the first frame. This is applied per NLA clip'),
        ('SUFFIX', 'Suffix', 'Add the first frame after the last frame. This is applied per NLA clip'),
        ('PREFIX_SUFFIX', 'Prefix & Suffix', 'Add both the last frame before the first frame and the first frame after the last frame (recommended if unsure). This is applied per NLA clip')
    ]
    frame_padding_mode: EnumProperty(name="Mode", items=frame_padding_modes, default="PREFIX_SUFFIX", description="Select how padding is applied to frame data")
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

    skinning_tex_max_width: IntProperty(name="Max Width", min=2, max=8192, default=4096, description="Maximum allowed texture width. Exceeding this may cancel the bake due to an excess of vertices")
    skinning_tex_max_height: IntProperty(name="Max Height", min=2, max=8192, default=4096, description="Maximum allowed texture height. Exceeding this may cancel the bake due to an excess of vertices")
    skinning_tex_res_modes = [
        ("ROWS", "Rows", "Each vertex is aligned sequentially in the texture, using one column per vertex and one row per type of skinning data—typically one row for bone indices and another for weights. This results in a texture that is usually very wide but only a few pixels tall (e.g., 4090×2 for a mesh with 4090 vertices).\n\nIf the vertex count exceeds the maximum allowed texture width, the data is wrapped across multiple rows. In such cases, the skinning data for each vertex is still kept vertically aligned—i.e., each vertex’s data is stored in texels directly below one another to maintain a consistent sampling pattern"),
        ("SQRT", "Square Root", "The texture resolution is computed by taking the square root of the vertex count multiplied by the number of skinning data rows per vertex. For example, with a mesh containing 4090 vertices and two rows of skinning data per vertex (e.g., indices and weights), the total number of texels needed is: 8180. Rounding up the square root of the texel count gives 91, resulting in a texture that is 91x91 in resolution. Using a smaller texture width may allow mesh to use 16-bit UVs instead of the 32-bit UVs typically required for texel precision with 4K textures"),
        ("POT", "Power of Two", "Similar to 'SQRT' but ensures texture is of power-of-two, e.g. 128x64 instead of 91x91"),
        ("SQUARE_POT", "Power of Two (Square)", "Similar to 'POT' but ensures texture is of power-of-two AND square, e.g. 128x128 instead of 128x64"),
    ]
    skinning_tex_res_mode: EnumProperty(name="Mode", items=skinning_tex_res_modes, default="ROWS", description="Select how the texture resolution is derived from the vertex count")

    animation_tex_max_width: IntProperty(name="Max Width", min=2, max=8192, default=4096, description="Maximum allowed texture width. Exceeding this may cancel the bake due to an excess of bones or frames")
    animation_tex_max_height: IntProperty(name="Max Height", min=2, max=8192, default=4096, description="Maximum allowed texture height. Exceeding this may cancel the bake due to an excess of bones or frames")
    animation_tex_force_power_of_two: BoolProperty(name="Power of Two", default=False, description="Force textures to be power-of-two sizes. Not recommended, as non-power-of-two textures ensure tight packing and are widely supported. May lead to overflow issues when vertices exceed the image width, resulting in multiple rows per frame. Extra space handling can be controlled with the 'Stack Mode' option")
    animation_tex_force_power_of_two_square: BoolProperty(name="Square", default=False, description="Force texture width and height to be equal if 'Power of Two' is enabled. Typically unnecessary, but provided as an option for specific use cases. Extra space handling can be controlled with the 'Stack Mode' option")

    animation_tex_packing_modes = [
        ('CONTINUOUS', 'Continuous (Experimental)', "Store subsequent frame data directly after the previous frame in the texture, ensuring tight packing but requiring a more complex playback algorithm (frame data may start at arbitrary locations and span multiple lines)"),
        ('STACK', 'Stack', 'Skip remaining pixels and place the next frame on the next line (stack), simplifying playback but reducing packing efficiency and limiting texture space for vertex data')
    ]
    animation_tex_packing_mode: EnumProperty(name="Mode", items=animation_tex_packing_modes, default=1, description="Control how frames are arranged in the texture when there's extra space (underflow) or not enough space (overflow). \n\nUnderflow occurs when the number of bones per frame is less than the image width, causing gaps at the end of the line ('Power of Two' might cause this). \n\nOverflow happens when there are too many bones for a single line, and the data is spread across multiple lines, possibly leaving gaps. \n\nThis setting determines how to handle these empty spaces")

    # Underflow - CONTINUOUS
    # f5 f5 f5 00
    # f3 f4 f4 f4
    # f2 f2 f3 f3
    # f1 f1 f1 f2
    # Underflow - STACK
    # f4 f4 f4 00
    # f3 f3 f3 00
    # f2 f2 f2 00
    # f1 f1 f1 00
    # Overflow - CONTINUOUS
    # f3 f3 f3 00
    # f2 f2 f3 f3
    # f1 f2 f2 f2
    # f1 f1 f1 f1
    # Overflow - STACK
    # f2 00 00 00
    # f2 f2 f2 f2
    # f1 00 00 00
    # f1 f1 f1 f1

    animation_tex_packing_stack_modes = [
        ('ADJACENT', 'Adjacent', 'Rows are stacked on top of each other, which simplifies playback in the vertex shader but prevents the use of pixel interpolation for frame interpolation'),
        ('OFFSET', 'Offset', 'Rows are offset by the full animation length, making playback in the vertex shader more complex but allowing pixel interpolation to be used for frame interpolation'),
    ]
    animation_tex_packing_stack_mode: EnumProperty(name="Stack Mode", items=animation_tex_packing_stack_modes, default="OFFSET", description="Select the stack method")

##############
### REPORT ###
class BATBAKER_PG_ReportSkinningTexChannel(PropertyGroup):
    """ """
    channel_modes = [
        ("NONE", "None", "Write 0 to the channel"),
        ("INDEX", "Index", "Bone index"),
        ("WEIGHT", "Weight", "Bone weight"),
    ]
    channel_mode: EnumProperty(items=channel_modes, name="Mode", default="NONE", description="")
    index: IntProperty(name="Index", min=1, default=0, description="1 - the bone influencing the vertex the most\n2 - the second most influencing bone\n3 - the third\n4 - ...")

class BATBAKER_PG_ReportSkinningTexRow(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="", description="")

    R: PointerProperty(type=BATBAKER_PG_ReportSkinningTexChannel)
    G: PointerProperty(type=BATBAKER_PG_ReportSkinningTexChannel)
    B: PointerProperty(type=BATBAKER_PG_ReportSkinningTexChannel)
    A: PointerProperty(type=BATBAKER_PG_ReportSkinningTexChannel)

class BATBAKER_PG_ReportSkinningTexLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")
    exported: BoolProperty(name="Exported", default=False)
    path: StringProperty(name="Texture Filepath", default="//", description="", subtype='FILE_PATH')
    img: PointerProperty(type=bpy.types.Image)

    storage_mode: StringProperty(name="Storage", default="", description="")

    rows: CollectionProperty(type=BATBAKER_PG_ReportSkinningTexRow)
    rows_selected_index: IntProperty(name="Selected", default=0)

class BATBAKER_PG_ReportAnimationTexChannel(PropertyGroup):
    """ """
    channel_modes = [
        ("NONE", "None", "Write 0 to the channel"),
        ("POSITION", "Position", "Bone position"),
        ("ROTATION", "Rotation", "Bone rotation"),
        ("SCALE", "Scale", "Bone scale"),
        ("AXIS", "Axis", "Bone axis"),
        ("CUSTOM_PROP", "Custom Property", "Bone custom property"),
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

    axis_scaled: BoolProperty(name="Scale", default=False, description="")

    remapping: BoolProperty(name="Remap", default=False, description="Enable to remap values stored in this channel from their initial [-min:max] range to [0:1] which can later be brought back to their initial range using the reported offset and range values. This may allow 8-bit RGBA textures to be used for storing data.")

class BATBAKER_PG_ReportAnimationTexLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    name: StringProperty(name="name", default="Texture", description="")
    exported: BoolProperty(name="Exported", default=False)
    path: StringProperty(name="Texture Filepath", default="//", description="", subtype='FILE_PATH')
    img: PointerProperty(type=bpy.types.Image)

    R: PointerProperty(type=BATBAKER_PG_ReportAnimationTexChannel)
    R_range_offset: FloatProperty(name="Offset", default=0.0)
    R_range: FloatProperty(name="Range", default=1.0)
    R_range_valid: BoolProperty(name="Valid", default=False)
    G: PointerProperty(type=BATBAKER_PG_ReportAnimationTexChannel)
    G_range_offset: FloatProperty(name="Offset", default=0.0)
    G_range: FloatProperty(name="Range", default=1.0)
    G_range_valid: BoolProperty(name="Valid", default=False)
    B: PointerProperty(type=BATBAKER_PG_ReportAnimationTexChannel)
    B_range_offset: FloatProperty(name="Offset", default=0.0)
    B_range: FloatProperty(name="Range", default=1.0)
    B_range_valid: BoolProperty(name="Valid", default=False)
    A: PointerProperty(type=BATBAKER_PG_ReportAnimationTexChannel)
    A_range_offset: FloatProperty(name="Offset", default=0.0)
    A_range: FloatProperty(name="Range", default=1.0)
    A_range_valid: BoolProperty(name="Valid", default=False)

class BATBAKER_PG_ReportAnim(PropertyGroup):
    """ """
    name: StringProperty(name="Name", default="", description="")
    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")

class BATBAKER_PG_Report(PropertyGroup):
    """ """
    skinning_textures: CollectionProperty(type=BATBAKER_PG_ReportSkinningTexLayer)
    skinning_textures_selected_index: IntProperty(name="Selected", default=0)

    animation_textures: CollectionProperty(type=BATBAKER_PG_ReportAnimationTexLayer)
    animation_textures_selected_index: IntProperty(name="Selected", default=0)

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

    padded: BoolProperty(name="Padded", default=False, description="")
    padding: IntProperty(name="Padding", default=0, description="")
    padding_mode: StringProperty(name="Sampling", default="", description="")
    frame_ref_mode: StringProperty(name="Frame Ref Mode", default="", description="")
    frame_ref: IntProperty(name="Frame Ref", default=1, description="")
    frame_ref_padding: BoolProperty(name="Ref Padding", default=False, description="")
    anims: CollectionProperty(type=BATBAKER_PG_ReportAnim)
    selected_anim: IntProperty(name="Selected Anim", default=0, description="")

    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")
    num_frames: IntProperty(name="Count", default=0, description="")
    num_frames_padded: IntProperty(name="Padded", default=0, description="")
    frame_step: IntProperty(name="Frame Step", default=0, description="")
    frame_step_mode: StringProperty(name="Step Mode", default="", description="")
    frame_rate: FloatProperty(name="FPS", default=24.0, description="")

    num_verts: IntProperty(name="Vertices", default=0, description="")
    num_bones: IntProperty(name="Bones", default=0, description="")
    num_bones_max: IntProperty(name="Max Weights", default=4, min=1, max=4, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_uvmap_index: IntProperty(name="UV Index", default=0, description="")
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")
    
    skinning_tex_width: IntProperty(name="Width", default=0, description="")
    skinning_tex_height: IntProperty(name="Height", default=0, description="")
    skinning_tex_rows: FloatProperty(name="Rows of Vertices", default=1, description="")
    skinning_tex_res_mode: StringProperty(name="Mode", default="", description="")
    
    animation_tex_width: IntProperty(name="Width", default=0, description="")
    animation_tex_frame_width: FloatProperty(name="Frame Width", default=0, description="")
    animation_tex_height: IntProperty(name="Height", default=0, description="")
    animation_tex_frame_height: FloatProperty(name="Frame Height", default=0, description="")
    animation_tex_underflow: BoolProperty(name="Underflow", default=False, description="")
    animation_tex_overflow: BoolProperty(name="Overflow", default=False, description="")
    animation_tex_sampling_mode: StringProperty(name="Sampling", default="", description="")
    animation_tex_packing_stack_mode: StringProperty(name="Stack Mode", default="", description="")

    xml: BoolProperty(name="XML", default=False, description="")
    xml_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

def register():
    bpy.types.Scene.BATBakerSettings = PointerProperty(type=BATBAKER_PG_Settings)
    bpy.types.Scene.BATBakerReport = PointerProperty(type=BATBAKER_PG_Report)

def unregister():
    del bpy.types.Scene.BATBakerSettings
    del bpy.types.Scene.BATBakerReport
