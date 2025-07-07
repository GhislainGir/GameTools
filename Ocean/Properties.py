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
class FFTOCEANBAKER_PG_Settings(PropertyGroup):
    """ """

    # scene 
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_u: BoolProperty(name="Invert U", default=False, description="Flip each frame left to right")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Flip each frame upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps. This only affect each frame individually and doesn't affect the way they are sorted if compacted into a flipbook")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis")

    subd: IntProperty(name="Subdivisions", default=16, description="Specify the subdivision level to use for the ocean modifier. Beware, this results in the (subd ^ 2) resolution and (subd ^ 4) faces")

    # frames
    frame_sort_modes = [
        ('TB_LR', 'Top Bottom, Left Right', ''),
        ('TB_RL', 'Top Bottom, Right Left', ''),
        ('BT_LR', 'Bottom Top, Left Right', ''),
        ('BT_RL', 'Bottom Top, Right Left', '')
    ]
    frame_sort_mode: EnumProperty(name="Frames", items=frame_sort_modes, default="TB_LR", description="Control how the frames are distributed in the flipbook, from the first frame of the animation to the last")
    frames_per_row: IntProperty(name="Frames Per Row", default=8, description="Specify how many frames to distribute along the U axis in the texture. For example, if you're baking 64 frames and set this value to 8, the result will be an evenly distributed 8×8 texture. If set to 10, it will produce a 10×7 layout, with 4 empty frames in the last row")
    frame_padding_modes = [
        ("NONE", "None", ""),
        ("MIPLEVEL", "Mip Level", ""),
        ("PIXELS", "Pixels", ""),
    ]
    frame_padding_mode: EnumProperty(name="Padding Mode", items=frame_padding_modes, default="MIPLEVEL", description="Select how the amount of padding to apply, if any, is computed. Padding can't exceed the frame's size")
    frame_padding_mips: IntProperty(name="Mip", default=2, description="Add enough padding on each side of the frame to fix tiling issues up to a specific mip level.\n\nMip 1 - one pixel of padding on each side.\nMip 2 - two pixels of padding on each side.\nMip 3 - four pixels of padding on each side")
    frame_padding_pixels: IntProperty(name="Pixels", default=4, description="Add X amount of pixels on each side of the frame to fix tiling issues")
    frame_range_modes = [
            ("SCENE", "Scene", "Use the scene's frame range (start and end frames are inclusive)"),
            ("CUSTOM", "Custom", "Use a custom frame range (start and end frames are inclusive)"),
        ]
    frame_range_mode: EnumProperty(name="Mode", items=frame_range_modes, default="CUSTOM", description="Select how the frame range is derived")
    frame_range_custom_start: IntProperty(name="Start", min=1, default=1, description="Start frame (inclusive)")
    frame_range_custom_end: IntProperty(name="End", min=1, default=64, description="End frame (inclusive)")
    frame_range_custom_step: IntProperty(name="Step", min=1, default=1, description="Bake every nth frame")
    frame_size_modes = [
        ("SUBDIVISIONS", "Subdivisions", "The frame size equals the ocean's modifier resolution and contains as much information as could be extracted from it. There's no reason to scale the frame up but to end up with power of two texture(s)"),
        ("CUSTOM", "Custom", "The frame size is first rendered to extract as much information as it can be extracted from the ocean modifier, based on its resolution, and then can be upscaled or downscaled using simple bilinear filtering. This doesn't *NOT* produce in more wave details, as this is driven by the 'Subdivisions' setting. Frame size can be customized, and be downscaled/upscaled, to be of power of two if that's a necessity."),
    ]
    frame_size_mode: EnumProperty(name="Frame Size", items=frame_size_modes, default="SUBDIVISIONS", description="Select how the frame size is computed.")
    frame_size_custom: IntProperty(name="Size", default=128, min=1, description="Custom frame size, in pixels")

    # ocean
    ocean_time: FloatProperty(name="Duration", default=5, description="Animation speed")
    ocean_size: FloatProperty(name="Size", default=0.5, description="Surface scale factor (does not affect the height of the waves)")
    ocean_spatial_size: IntProperty(name="Spatial Size", default=25, description="Size of the simulation domain (in meters)")
    ocean_depth: FloatProperty(name="Depth", default=1.5, description="Depth of the solid ground below the water surface")
    ocean_seed: IntProperty(name="Random Seed", default=11, min=0, description="Seed of the random generator")
    ocean_scale: FloatProperty(name="Scale", default=1, description="Scale of the displacement effect")
    ocean_smallest_wave: FloatProperty(name="Smallest Wave", default=0.01, description="Shortest allowed wavelength")
    ocean_choppiness: FloatProperty(name="Chopiness", default=1, description="Choppiness of the wave's crest (adds some horizontal component to the displacement)")
    ocean_wind_vel: FloatProperty(name="Wind Velocity", default=10, description="Wind speed")
    ocean_alignment: FloatProperty(name="Alignment", default=0, min=0, max=1, description="How much the waves are aligned to each other")
    ocean_direction: FloatProperty(name="Direction", default=0, description="Main direction of the waves when they are (partially) aligned")
    ocean_damping: FloatProperty(name="Damping", default=0.5, description="Damp reflected waves going in opposite direction of the wind")
    ocean_clear: BoolProperty(name="Clear Object", default=True, description="Remove the generated ocean mesh from the scene once bake is complete")
    ocean_from_active: BoolProperty(name="From Active", default=True, description="Inherit settings from the active object's ocean modifier")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.FFT", description="Name of the baked object")
    generate_mesh: BoolProperty(name="Generate", default=True, description="Enables the generation of a subdivided plane mesh whose size matches the ocean modifier's extents and whose vertex density aligns with its resolution. UVs are centered on the first frame. While this isn’t mandatory—since the offset texture can be used as-is on any subdivided plane and projected using world space coordinates at any scale—this mesh can serve as an ideal reference for vertex density")
    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")

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

    # textures
    flipbook_max_size: IntProperty(name="Max Size", default=4096, description="Maximum allowed flipbook size. Bake will be cancelled if it is exceeded.")
    tex_modes = [
        ("FLIPBOOK", "Flipbook", "Exports the baked animation as one single image, where each frame is stored next to each other"),
        ("FRAME", "Frame", "Exports the baked animation as individual images, one per frame"),
    ]
    tex_mode: EnumProperty(name="Output", items=tex_modes, default="FLIPBOOK", description="Select the way to generate and export the textures")
    offset_tex: BoolProperty(name="Offset", default=True, description="Enable to bake the vertex offset texture")
    offset_tex_remap: BoolProperty(name="Remap", default=False, description="Enable to remap the offsets within a [0:1] range. This requires a multiplier and bias to remap the offsets in your shader or game engine. It is NOT recommended unless you intend to experiment with storing positions/offsets in 8-bit RGBA textures, as this will likely result in significant precision loss and visible deformation. Proceed at your own risk")
    offset_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Offset", description="Name for the vertex offset texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    normal_tex: BoolProperty(name="Normal", default=True, description="Enable to bake the vertex normal texture")
    normal_tex_remap: BoolProperty(name="Remap", default=True, description="Enable to remap the normals within a [0:1] range. This requires a constant bias to remap the normals in your shader or game engine. It is likely safe to do so, as normal VAT may be stored in an 8-bit RGBA texture without noticeable precision loss")
    normal_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Normal", description="Name for the vertex normal texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    crest_tex: BoolProperty(name="Crest", default=True, description="Enable to bake the crest texture")
    crest_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Crest", description="Name for the crest texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    crest_threshold: FloatProperty(name="Threshold", default=0.0, description="How much waves need to be compressed to register as a peak")
    splash_tex: BoolProperty(name="Splash", default=True, description="Enable to bake the splash texture")
    splash_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Splash", description="Name for the slpash texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    splash_threshold: FloatProperty(name="Threshold", default=0.2, description="@TODO")
    splash_num: IntProperty(name="Candidates", min=2, max=4096, default=128, description="@TODO")

    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion. Only available if the Blender file is saved")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")

##############
### REPORT ###
class FFTOCEANBAKER_PG_Report(PropertyGroup):
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
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_u: BoolProperty(name="Invert U", default=False, description="")
    unit_invert_v: BoolProperty(name="Invert V", default=False, description="")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied after inversion)")

    start_frame: IntProperty(name="Start", default=0, description="") #
    end_frame: IntProperty(name="End", default=0, description="")
    num_frames: IntProperty(name="Count", default=0, description="")
    frame_step: IntProperty(name="Frame Step", default=0, description="")
    frame_size: IntProperty(name="Size", default=128, min=1, description="")
    frame_rate: FloatProperty(name="FPS", default=24.0, description="")
    
    frame_sort_mode: StringProperty(name="Frames", default="", description="")
    frames_per_row: IntProperty(name="Frames Per Row", default=8, description="")
    frame_padding: IntProperty(name="Pixels", default=4, description="")
    
    subd: IntProperty(name="Subdivisions", default=5, description="")
    ocean_time: FloatProperty(name="Duration", default=5, description="")
    ocean_size: FloatProperty(name="Size", default=0.5, description="")
    ocean_spatial_size: IntProperty(name="Spatial Size", default=25, description="")
    ocean_depth: FloatProperty(name="Depth", default=1.5, description="")
    ocean_seed: IntProperty(name="Random Seed", default=11, min=0, description="")
    ocean_scale: FloatProperty(name="Scale", default=1, description="")
    ocean_smallest_wave: FloatProperty(name="Smallest Wave", default=0.01, description="")
    ocean_choppiness: FloatProperty(name="Chopiness", default=1, description="")
    ocean_wind_vel: FloatProperty(name="Wind Velocity", default=10, description="")
    ocean_alignment: FloatProperty(name="Alignment", default=0, min=0, max=1, description="")
    ocean_direction: FloatProperty(name="Direction", default=0, description="")
    ocean_damping: FloatProperty(name="Damping", default=0.5, description="")
    ocean_clear: BoolProperty(name="Clear Object", default=True, description="")
    ocean_from_active: BoolProperty(name="From Active", default=True, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")

    tex_width: IntProperty(name="Width", default=0, description="")
    tex_height: IntProperty(name="Height", default=0, description="")

    tex_mode: StringProperty(name="Mode", default="", description="")
    tex_offset: PointerProperty(type=bpy.types.Image)
    tex_offset_export: BoolProperty(name="Offset", default=False, description="")
    tex_offset_path: StringProperty(name="Path", default="//", description="", subtype='FILE_PATH')
    tex_offset_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_offset_range_offset: FloatVectorProperty(name="Offset")
    tex_offset_range: FloatVectorProperty(name="Range")
    tex_normal: PointerProperty(type=bpy.types.Image)
    tex_normal_export: BoolProperty(name="Normal", default=False, description="")
    tex_normal_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    tex_normal_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_crest: PointerProperty(type=bpy.types.Image)
    tex_crest_export: BoolProperty(name="Normal", default=False, description="")
    tex_crest_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    tex_crest_threshold: FloatProperty(name="Threshold", default=0, description="")
    tex_splash: PointerProperty(type=bpy.types.Image)
    tex_splash_export: BoolProperty(name="Normal", default=False, description="")
    tex_splash_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

    xml: BoolProperty(name="XML", default=False, description="")
    xml_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

def register():
    bpy.types.Scene.OceanBakerSettings = PointerProperty(type=FFTOCEANBAKER_PG_Settings)
    bpy.types.Scene.OceanBakerReport = PointerProperty(type=FFTOCEANBAKER_PG_Report)

def unregister():
    del bpy.types.Scene.OceanBakerSettings
    del bpy.types.Scene.OceanBakerReport
