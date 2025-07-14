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
class VATBAKER_PG_SettingsNLAClip(PropertyGroup):
    """ """
    name: StringProperty(name="Name", default="")

class VATBAKER_PG_Settings(PropertyGroup):
    """ """

    bake_modes = [
        ("ANIMATION", "Animation", "Bake vertex animation data based on the selected objects vertices movement inherited from armatures, shapekeys, transforms or any other animation methods. Vertex count AND order must be maintained during the animation"),
        ("MESHSEQUENCE", "Mesh Sequence", "Bake vertex animation data based on the selected mesh sequence. Frame order must be deducible from the objects names (.000, .001 etc). Vertex count AND order must be maintained during the animation")
    ]
    bake_mode: EnumProperty(name="Mode", items=bake_modes, default=0, description="Select how the vertex animation data is baked")

    # scene 
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip the VAT texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")
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
    mesh_name: StringProperty(name="Name", default="BakedMesh.VAT", description="Name of the baked object")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData.VAT", description="Name of the UVMap to be created or used for baking mesh UVs")
    mesh_target_prop: StringProperty(name="Property", default="BakeTarget", description="Custom property name for the retargeting feature (to bake a high-res animated mesh to a low-res mesh)")
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
    frame_range_nla_exclusion: CollectionProperty(type=VATBAKER_PG_SettingsNLAClip)
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
    frame_ref_modes = [
        ("START", "Start", "Use the start frame as the reference frame"),
        ("END", "End", "Use the end frame as the reference frame"),
        ("CUSTOM", "Custom", "Use a custom frame as the reference frame"),
    ]
    frame_ref_mode: EnumProperty(name="Mode", items=frame_ref_modes, default="START", description="Select how the reference frame is computed")
    frame_ref_custom: IntProperty(name="Reference", default=1, description="Frame to use as the reference 'pose,' from which mappings and offsets are computed. Specifying a frame outside the animation range is allowed to specify a T-pose frame that should otherwise be excluded from the bake")

    # textures    
    offset_tex_modes = [
        ('OFFSET', 'Offset', 'Store the vertices offset from the base pose in the VAT texture (recommended)'),
        ('POSITION', 'Position', 'Store the vertices\' local position in the VAT texture'),
    ]
    offset_tex_mode: EnumProperty(name="Tex Mode", items=offset_tex_modes, default=0, description="Select the positional data to store in the texture: offset (recommended) or local position")
    offset_tex: BoolProperty(name="Offset", default=True, description="Enable to bake the vertex offset texture")
    offset_tex_remap: BoolProperty(name="Remap", default=False, description="Enable to remap the offsets within a [0:1] range. This requires a multiplier and bias to remap the offsets in your shader or game engine. It is NOT recommended unless you intend to experiment with storing positions/offsets in 8-bit RGBA textures, as this will likely result in significant precision loss and visible deformation. Proceed at your own risk")
    offset_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Offset", description="Name for the vertex offset texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    normal_tex: BoolProperty(name="Normal", default=True, description="Enable to bake the vertex normal texture")
    normal_tex_remap: BoolProperty(name="Remap", default=True, description="Enable to remap the normals within a [0:1] range. This requires a constant bias to remap the normals in your shader or game engine. It is likely safe to do so, as normal VAT may be stored in an 8-bit RGBA texture without noticeable precision loss")
    normal_tex_remap_biasscale: BoolProperty(name="Bias Scale", default=True, description="Remap normals using a simple constant bias and scale, assuming they fully span the [-1, 1] range. This approach is recommended to keep the remapping process straightforward, as normals in most meshes are typically varied enough to cover the entire range. Using their actual min/max values to extract maximum precision is usually unnecessary")
    normal_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Normal", description="Name for the vertex normal texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion. Only available if the Blender file is saved")
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

    tex_packing_stack_modes = [
        ('ADJACENT', 'Adjacent', 'Rows are stacked on top of each other, which simplifies playback in the vertex shader but prevents the use of pixel interpolation for frame interpolation'),
        ('OFFSET', 'Offset', 'Rows are offset by the full animation length, making playback in the vertex shader more complex but allowing pixel interpolation to be used for frame interpolation'),
    ]
    tex_packing_stack_mode: EnumProperty(name="Stack Mode", items=tex_packing_stack_modes, default="OFFSET", description="Select the stack method")

##############
### REPORT ###
class VATBAKER_PG_ReportAnimObj(PropertyGroup):
    """ """
    obj: PointerProperty(type=bpy.types.Object)
    target_obj: PointerProperty(type=bpy.types.Object)

class VATBAKER_PG_ReportAnim(PropertyGroup):
    """ """
    objs: CollectionProperty(type=VATBAKER_PG_ReportAnimObj)
    selected_obj: IntProperty(name="Selected Obj", default=0, description="")
    name: StringProperty(name="Name", default="", description="")
    start_frame: IntProperty(name="Start", default=0, description="")
    start_time: FloatProperty(name="Start", default=0.0)
    end_frame: IntProperty(name="End", default=0, description="")
    end_time: FloatProperty(name="End", default=0.0)

class VATBAKER_PG_Report(PropertyGroup):
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

    padded: BoolProperty(name="Padded", default=False, description="")
    padding: IntProperty(name="Padding", default=0, description="")
    padding_modes = [
        ('PREFIX', 'Prefix', 'Last frame was added before first frame'),
        ('SUFFIX', 'Suffix', 'First frame was added after last frame'),
        ('PREFIX_SUFFIX', 'Prefix & Suffix', 'Last frame was added before first frame AND first frame was added after last frame')
    ]
    padding_mode: EnumProperty(name="Sampling", items=padding_modes, default=0, description="")
    ref_mode: StringProperty(name="Frame Ref Mode", default="", description="")
    ref: IntProperty(name="Frame Ref", default=1, description="")
    anims: CollectionProperty(type=VATBAKER_PG_ReportAnim)
    selected_anim: IntProperty(name="Selected Anim", default=0, description="")

    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")
    num_frames: IntProperty(name="Count", default=0, description="")
    num_frames_padded: IntProperty(name="Padded", default=0, description="")
    frame_step: IntProperty(name="Frame Step", default=0, description="")
    frame_step_mode: StringProperty(name="Step Mode", default="", description="")
    frame_width: FloatProperty(name="Frame Width", default=0.0, description="")
    frame_height: FloatProperty(name="Frame Height", default=0.0, description="")
    frame_rate: FloatProperty(name="FPS", default=24.0, description="")

    num_verts: IntProperty(name="Vertices", default=0, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_uvmap_index: IntProperty(name="UV Index", default=0, description="")
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")
    tex_width: IntProperty(name="Width", default=0, description="")
    tex_height: IntProperty(name="Height", default=0, description="")
    tex_underflow: BoolProperty(name="Underflow", default=False, description="")
    tex_overflow: BoolProperty(name="Overflow", default=False, description="")
    tex_offset: PointerProperty(type=bpy.types.Image)
    tex_offset_mode: StringProperty(name="Offset Mode", default="Offset", description="")
    tex_offset_export: BoolProperty(name="Offset", default=False, description="")
    tex_offset_path: StringProperty(name="Path", default="//", description="", subtype='FILE_PATH')
    tex_offset_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_offset_range_offset: FloatVectorProperty(name="Offset")
    tex_offset_range: FloatVectorProperty(name="Range")

    tex_normal: PointerProperty(type=bpy.types.Image)
    tex_normal_export: BoolProperty(name="Normal", default=False, description="")
    tex_normal_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    tex_normal_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_normal_range_offset: FloatVectorProperty(name="Offset")
    tex_normal_range: FloatVectorProperty(name="Range")
    tex_sampling_mode: StringProperty(name="Sampling", default="", description="")
    tex_packing_stack_mode: StringProperty(name="Stack Mode", default="", description="")

    xml: BoolProperty(name="XML", default=False, description="")
    xml_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

def register():
    bpy.types.Scene.VATBakerSettings = PointerProperty(type=VATBAKER_PG_Settings)
    bpy.types.Scene.VATBakerReport = PointerProperty(type=VATBAKER_PG_Report)

def unregister():
    del bpy.types.Scene.VATBakerSettings
    del bpy.types.Scene.VATBakerReport
