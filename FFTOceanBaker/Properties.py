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
class FFTOCEANBAKER_PG_SettingsPropertyGroup(PropertyGroup):
    """ """

    # scene 
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Flip the texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")

    subdivisions = [
        ("CUSTOM", "Custom", "Specify the subdivision level to use for the ocean modifier. Beware, this results in the (subd ^ 4) faces"),
        ("2", "4x4", "Generate a 4x4 grid"),
        ("3", "9x9", "Generate a 9x9 grid"),
        ("4", "16x16", "Generate a 16x16 grid"),
        ("5", "25x25", "Generate a 25x25 grid"),
        ("6", "36x36", "Generate a 36x36 grid"),
        ("7", "49x49", "Generate a 49x49 grid"),
        ("8", "64x64", "Generate a 64x64 grid"),
        ("9", "81x81", "Generate a 81x81 grid"),
        ("10", "100x100", "Generate a 100x100 grid"),
        ("11", "121x121", "Generate a 121x121 grid"),
        ("12", "144x144", "Generate a 144x144 grid")
    ]
    subd: EnumProperty(name="Subdivisions", items=subdivisions, default="5", description="Select the subdivision level mode. ")
    subd_custom_subd: IntProperty(name="Subdivisions", default=5, description="")

    frames_per_row: IntProperty(name="Frames Per Row", default=8, description="")
    padding_modes = [
        ("NONE", "None", ""),
        ("MIPLEVEL", "Mip Level", ""),
        ("PIXELS", "Pixels", ""),
    ]
    frame_padding_mode: EnumProperty(name="Padding Mode", items=padding_modes, default="MIPLEVEL", description="Select how padding is applied, if any")
    frame_padding_mips: IntProperty(name="Mip", default=2, description="Add enough padding on each side of the frame to fix tiling issues for a specific mip level.\n\nMip 1 - one pixel of padding on each side.\n\nMip 2 - two pixels of padding on each side.\n\nMip 3 - four pixels of padding on each side")
    frame_padding_pixels: IntProperty(name="Pixels", default=4, description="Add X amount of pixels on each side of the frame to fix tiling issues")

    anim_speed: FloatProperty(name="Wave Speed", default=5, description="")
    ocean_size: FloatProperty(name="Size", default=0.25, description="")
    ocean_spatial_size: FloatProperty(name="Spatial Size", default=50, description="")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.FFT", description="Name of the baked object")
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

    # frames
    frame_range_modes = [
            ("SCENE", "Scene", "Use the scene's frame range (start and end frames are inclusive)"),
            ("CUSTOM", "Custom", "Use a custom frame range (start and end frames are inclusive)"),
        ]
    frame_range_mode: EnumProperty(name="Mode", items=frame_range_modes, default=0, description="Select how the frame range is derived")
    frame_range_custom_start: IntProperty(name="Start", min=1, default=1, description="Start frame (inclusive)")
    frame_range_custom_end: IntProperty(name="End", min=1, default=64, description="End frame (inclusive)")
    frame_range_custom_step: IntProperty(name="Step", min=1, default=1, description="Bake every nth frame")
    frame_size_modes = [
        ("SUBDIVISIONS", "Subdivisions", ""),
        ("CUSTOM", "Custom", ""),
    ]
    frame_size_mode: EnumProperty(name="Frame Size", items=frame_size_modes, default="SUBDIVISIONS", description="")
    frame_size_custom: IntProperty(name="Size", default=128, min=1)
    
    # textures
    flipbook_max_size: IntProperty(name="Max Size", default=4096, description="")
    tex_modes = [
        ("FLIPBOOK", "Flipbook", "Exports the baked animation as one single image, where each frame is stored next to each other"),
        ("FRAME", "Frame", "Exports the baked animation as individual images, one per frame"),
    ]
    tex_mode: EnumProperty(name="Output", items=tex_modes, default="FLIPBOOK", description="Select the way to generate and export the textures")
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
    normal_tex_file_name: StringProperty(name="Filename", default="T_<BakeName>_Normal", description="Name for the vertex normal texture file (without the .exr extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_tex: BoolProperty(name="Export", default=True, description="Enable to export the generated textures to an EXR file upon bake completion. Only available if the Blender file is saved")
    export_tex_file_path: StringProperty(name="Path", default="//", description="Texture file path, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_tex_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .exr file")

class FFTOCEANBAKER_PG_ReportPropertyGroup(PropertyGroup):
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

    start_frame: IntProperty(name="Start", default=0, description="")
    end_frame: IntProperty(name="End", default=0, description="")
    num_frames: IntProperty(name="Count", default=0, description="")
    frame_step: IntProperty(name="Frame Step", default=0, description="")
    frame_width: FloatProperty(name="Frame Width", default=0.0, description="")
    frame_height: FloatProperty(name="Frame Height", default=0.0, description="")
    frame_rate: FloatProperty(name="FPS", default=24.0, description="")

    mesh: PointerProperty(type=bpy.types.Object)
    mesh_export: BoolProperty(name="Export", default=False, description="")
    mesh_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_min_bounds_offset: FloatVectorProperty(name="Min Bounds Offset")
    mesh_max_bounds_offset: FloatVectorProperty(name="Max Bounds Offset")

    tex_width: IntProperty(name="Width", default=0, description="")
    tex_height: IntProperty(name="Height", default=0, description="")

    tex_mode: StringProperty(name="Mode", default="", description="")
    tex_offset: PointerProperty(type=bpy.types.Image)
    tex_offset_mode: StringProperty(name="Offset Mode", default="Offset", description="")
    tex_offset_export: BoolProperty(name="Offset", default=False, description="")
    tex_offset_path: StringProperty(name="Path", default="//", description="", subtype='FILE_PATH')
    tex_offset_remapped: BoolProperty(name="Remapped", default=False, description="")
    tex_offset_remapping: FloatVectorProperty(name="Remapping")
    tex_normal: PointerProperty(type=bpy.types.Image)
    tex_normal_export: BoolProperty(name="Normal", default=False, description="")
    tex_normal_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')
    tex_normal_remapped: BoolProperty(name="Remapped", default=False, description="")

    xml: BoolProperty(name="XML", default=False, description="")
    xml_path: StringProperty(name="Filepath", default="//", description="", subtype='FILE_PATH')

def register():
    bpy.types.Scene.FFTOCEANBAKERSettings = PointerProperty(type=FFTOCEANBAKER_PG_SettingsPropertyGroup)
    bpy.types.Scene.FFTOCEANBAKERReport = PointerProperty(type=FFTOCEANBAKER_PG_ReportPropertyGroup)

def unregister():
    del bpy.types.Scene.FFTOCEANBAKERSettings
    del bpy.types.Scene.FFTOCEANBAKERReport
