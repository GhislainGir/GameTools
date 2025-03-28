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
class DATABAKER_PG_SettingsPropertyGroup(PropertyGroup):  
    """Settings for DataBaker."""

    modes = [
        ("UV", "UV Map", "Bake data into a UV map"),
        ("VCOL", "Vertex Color", "Bake data into vertex colors")
    ]

    axis_xyz = [
        ("X", "X", "X-axis"),
        ("Y", "Y", "Y-axis"),
        ("Z", "Z", "Z-axis")
    ]

    uv = [
        ("U", "U", "U channel of UV map"),
        ("V", "V", "V channel of UV map")
    ]

    rgba = [
        ("R", "R", "Red channel"),
        ("G", "G", "Green channel"),
        ("B", "B", "Blue channel"),
        ("A", "A", "Alpha channel")
    ]

    pos_channels = [
        ("INDIVIDUAL" , "Individual ", "Bake each X/Y/Z component separately into its own channel"),
        ("AB_PACKED", "AB Packed", "Pack two components (e.g., X/Y) into a single float with moderate precision loss. Multiplier & 32-bit UVs required! See @doc for more info"),
        ("XYZ_PACKED", "XYZ Packed", "Pack all three components into a single float with severe precision loss. Multiplier & 32-bit UVs required! See @doc for more info"),
    ]

    axis_modes = [
        ("INDIVIDUAL" , "Individual ", "Bake each X/Y/Z component separately into its own channel"),
        ("AB_PACKED", "AB Packed", "Pack two components (e.g., X/Y) into a single float with minimal precision loss. 32-bit UVs required! See @doc for more info"),
        ("XYZ_PACKED", "XYZ Packed", "Pack all three components into a single float with severe precision loss. 32-bit UVs required! See @doc for more info"),
        ("POSITION_PACKED", "Packed with Position", "Pack axis data into the fractional part of position data. Axis is remapped and position XYZ components are rounded to integers which could be an issue depending on the scale (safe-ish with centimeters). See @doc for more info"),
        #("OCTAHEDRAL", "Octahedral", "Use octahedral encoding for efficient vector storage (ideal for unit vectors)") @TODO
    ]

    # transform
    transform_obj: PointerProperty(type=bpy.types.Object, name="Object", description="Defaults to 'self'. Use this in the rare occasion that you want to bake the position/axis of a specific object into another object. Usually using 'self' is what you want (meaning, leave this empty)")

    # position
    position: BoolProperty(name="Position", default=False, description="Bake object position data? Further actions are required depending on the selected mode. See @doc for more info")
    position_channel_mode: EnumProperty(name="Mode", items=pos_channels, default="INDIVIDUAL", description="Method for baking position data")

    position_x: BoolProperty(name="X", default=True, description="Bake X component of position")
    position_x_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake X component")
    position_x_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for X")
    position_x_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for X")
    position_x_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel for X")

    position_y: BoolProperty(name="Y", default=True, description="Bake Y component of position")
    position_y_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Y component")
    position_y_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for Y")
    position_y_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for Y")
    position_y_rgba: EnumProperty(name="Channel", items=rgba, default="G", description="Target RGBA channel for Y")

    position_z: BoolProperty(name="Z", default=True, description="Bake Z component of position")
    position_z_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Z component")
    position_z_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for Z")
    position_z_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for Z")
    position_z_rgba: EnumProperty(name="Channel", items=rgba, default="B", description="Target RGBA channel for Z")

    position_packed_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map for packed position")
    position_packed_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for packed position")
    position_pack_only_if_non_null: BoolProperty(name="Pack Only If Non-Zero", default=True, description="Pack only if the position is not (0,0,0), as it involves bit-packing and further 0-testing of the unpacked value in shaders could prove to be an unreliable operation. This is recommended, although it may lead to a false positive if the position to pack happens to be close enough to (0,0,0)")
    position_ab_packed_a_comp: EnumProperty(name="A Component", items=axis_xyz, default="X", description="First component for AB packing")
    position_ab_packed_b_comp: EnumProperty(name="B Component", items=axis_xyz, default="Y", description="Second component for AB packing")

    # axis
    axis: BoolProperty(name="Axis", default=False, description="Bake object axis data? Further actions are required depending on the selected mode. See @doc for more info")
    axis_component: EnumProperty(name="Axis", items=axis_xyz, default="Z", description="Primary axis to bake (e.g., forward vector)")
    axis_channel_mode: EnumProperty(name="Mode", items=axis_modes, default="INDIVIDUAL", description="Method for baking axis data")

    axis_x: BoolProperty(name="X Component", default=True, description="Bake X component of axis")
    axis_x_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake X component")
    axis_x_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for X")
    axis_x_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for X")
    axis_x_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel for X")

    axis_y: BoolProperty(name="Y Component", default=True, description="Bake Y component of axis")
    axis_y_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Y component")
    axis_y_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for Y")
    axis_y_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for Y")
    axis_y_rgba: EnumProperty(name="Channel", items=rgba, default="G", description="Target RGBA channel for Y")

    axis_z: BoolProperty(name="Z Component", default=True, description="Bake Z component of axis")
    axis_z_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Z component")
    axis_z_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for Z")
    axis_z_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for Z")
    axis_z_rgba: EnumProperty(name="Channel", items=rgba, default="B", description="Target RGBA channel for Z")

    axis_packed_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map for packed axis")
    axis_packed_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for packed axis")
    axis_ab_packed_a_comp: EnumProperty(name="A Component", items=axis_xyz, default="X", description="First component for AB packing")
    axis_ab_packed_b_comp: EnumProperty(name="B Component", items=axis_xyz, default="Y", description="Second component for AB packing")

    # shapekey
    shapekey_name: StringProperty(name="Shape Key", default="Key 1", description="Name of the shape key to bake")
    shapekey_rest_name: StringProperty(name="Rest Shape Key", default="Basis", description="Name of the rest shape key for offset/normal calculation")

    # shapekey offset
    shapekey_offset: BoolProperty(name="Shape Key Offset", default=False, description="Bake shape key offset data? Further actions are required depending on the selected mode. See @doc for more info")
    shapekey_offset_channel_mode: EnumProperty(name="Mode", items=pos_channels, default="INDIVIDUAL", description="Method for baking offset")

    shapekey_offset_x: BoolProperty(name="X", default=True, description="Bake X component of shape key offset")
    shapekey_offset_x_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake X component")
    shapekey_offset_x_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for X")
    shapekey_offset_x_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for X")
    shapekey_offset_x_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel for X")

    shapekey_offset_y: BoolProperty(name="Y", default=True, description="Bake Y component of shape key offset")
    shapekey_offset_y_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Y component")
    shapekey_offset_y_uv_index: IntProperty(name="UV Map", min=0, max=7, default=3, description="Target UV map index for Y")
    shapekey_offset_y_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for Y")
    shapekey_offset_y_rgba: EnumProperty(name="Channel", items=rgba, default="G", description="Target RGBA channel for Y")

    shapekey_offset_z: BoolProperty(name="Z", default=True, description="Bake Z component of shape key offset")
    shapekey_offset_z_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Z component")
    shapekey_offset_z_uv_index: IntProperty(name="UV Map", min=0, max=7, default=3, description="Target UV map index for Z")
    shapekey_offset_z_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for Z")
    shapekey_offset_z_rgba: EnumProperty(name="Channel", items=rgba, default="B", description="Target RGBA channel for Z")

    shapekey_offset_packed_uv_index: IntProperty(name="UV Map", min=0, max=7, default=3, description="Target UV map for packed offset")
    shapekey_offset_packed_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for packed offset")
    shapekey_offset_pack_only_if_non_null: BoolProperty(name="Pack Only If Non-Zero", default=True, description="Pack only if offset is not (0,0,0), as it involves bit-packing and further 0-testing of the unpacked value in shaders could prove to be an unreliable operation. This is recommended, although it may lead to a false positive if the offset to pack happens to be close enough to (0,0,0)")
    shapekey_offset_ab_packed_a_comp: EnumProperty(name="A Component", items=axis_xyz, default="X", description="First component for AB packing")
    shapekey_offset_ab_packed_b_comp: EnumProperty(name="B Component", items=axis_xyz, default="Y", description="Second component for AB packing")

    # shapekey normal
    shapekey_normal: BoolProperty(name="Shape Key Normal", default=False, description="Bake shape key normal data? Further actions are required depending on the selected mode. See @doc for more info")
    shapekey_normal_channel_mode: EnumProperty(name="Mode", items=axis_modes, default="INDIVIDUAL", description="Method for baking normals")

    shapekey_normal_x: BoolProperty(name="X", default=True, description="Bake X component of shape key normal")
    shapekey_normal_x_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake X component")
    shapekey_normal_x_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for X")
    shapekey_normal_x_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for X")
    shapekey_normal_x_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel for X")

    shapekey_normal_y: BoolProperty(name="Y", default=True, description="Bake Y component of shape key normal")
    shapekey_normal_y_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Y component")
    shapekey_normal_y_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for Y")
    shapekey_normal_y_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for Y")
    shapekey_normal_y_rgba: EnumProperty(name="Channel", items=rgba, default="G", description="Target RGBA channel for Y")

    shapekey_normal_z: BoolProperty(name="Z", default=True, description="Bake Z component of shape key normal")
    shapekey_normal_z_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Z component")
    shapekey_normal_z_uv_index: IntProperty(name="UV Map", min=0, max=7, default=3, description="Target UV map index for Z")
    shapekey_normal_z_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for Z")
    shapekey_normal_z_rgba: EnumProperty(name="Channel", items=rgba, default="B", description="Target RGBA channel for Z")

    shapekey_normal_packed_uv_index: IntProperty(name="UV Map", min=0, max=7, default=3, description="Target UV map for packed normal")
    shapekey_normal_packed_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for packed normal")
    shapekey_normal_ab_packed_a_comp: EnumProperty(name="A Component", items=axis_xyz, default="X", description="First component for AB packing")
    shapekey_normal_ab_packed_b_comp: EnumProperty(name="B Component", items=axis_xyz, default="Y", description="Second component for AB packing")

    # sphere mask
    sphere_mask: BoolProperty(name="Sphere Mask", default=False, description="Bake a spherical 3D gradient")
    sphere_mask_normalize: BoolProperty(name="Normalize", default=True, description="Normalize distance to [0:1] range based on max distance (mandatory if baked in Vertex Colors)")
    sphere_mask_clamp: BoolProperty(name="Clamp", default=False, description="Clamp values to [0:1] range")
    sphere_mask_origin_modes = [
        ("ORIGIN" , "Origin", "Compute gradient from the world origin, or the specified 'Origin' object"),
        ("SELF" , "Self", "Compute gradient from each object's origin"),
        ("OBJECT" , "Object ", "Compute gradient from a specified object's origin"),
        ("SELECTION" , "Selection Center", "Compute gradient from the center of selected objects"),
        ("PARENT" , "Parent Object", "Compute gradient from each object's parent origin, if any, else from each object's own origin")
    ]
    sphere_mask_origin_mode: EnumProperty(name="Origin", items=sphere_mask_origin_modes, default=1, description="Select the spherical mask origin")
    sphere_mask_origin: PointerProperty(type=bpy.types.Object, name="Object", description="Optional object used to compute the sphere mask origin/center")
    sphere_mask_mode: EnumProperty(name="Mode", items=modes, default="UV", description="Select how the spherical gradient is baked")

    sphere_mask_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UVMap index")
    sphere_mask_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UVMap channel")
    sphere_mask_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel")
    sphere_mask_falloff: FloatProperty(name="Falloff", min=0.0, default=1.0, description="Power curve. 1 - linear falloff, 2 - cubic falloff...")

    # linear mask
    linear_mask: BoolProperty(name="Linear Mask", default=False, description="Bake a linear 2D gradient along an axis")
    linear_mask_normalize: BoolProperty(name="Normalize", default=True, description="Normalize distance to [0:1] range based on max distance (mandatory if baked in Vertex Colors)")
    linear_mask_clamp: BoolProperty(name="Clamp", default=False, description="Clamp values to [0:1] range. Normalization may not ensure this with custom bounds.")
    linear_mask_obj_modes = [
        ("SELECTION", "Selection Bounds", "Gradient based on selection bounds in world space"),
        ("SELF_LOCAL", "Self (Local)", "Gradient along object's local axis"),
        ("SELF_WORLD", "Self (World)", "Gradient along object's world axis"),
        ("OBJECT", "Object", "Gradient based on a specified object's bounds"),
        ("PARENT_LOCAL", "Parent (Local)", "Gradient based on parent's local axis"),
        ("PARENT_WORLD", "Parent (World)", "Gradient based on parent's world axis")
    ]
    linear_mask_obj_mode: EnumProperty(name="Mode", items=linear_mask_obj_modes, default="SELF_LOCAL")
    linear_mask_obj: PointerProperty(type=bpy.types.Object, name="Object", description="Optional mesh object that can be used to specify custom bounds for computing the linear mask. Defaults to self if none is specified")
    linear_mask_mode: EnumProperty(name="Mode", items=modes, default="UV", description="Select how the linear gradient is baked")
    linear_mask_axis: EnumProperty(name="Axis", items=axis_xyz, default="Z", description="Select which axis to use to bake the 2D gradient")

    linear_mask_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UVMap index")
    linear_mask_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UVMap channel")
    linear_mask_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel")
    linear_mask_falloff: FloatProperty(name="Falloff", min=0.0, default=1.0, description="Power curve, only available IF normalized. Clamping is suggested to ensure values don't skyrocket with high falloff exponents & custom bounds. 1 - linear falloff, 2 - cubic falloff...")

    # random
    random_per_collection: BoolProperty(name="Random Per Collection", default=False, description="Bake a random value per collection")
    random_per_collection_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake random values")
    random_per_collection_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index")
    random_per_collection_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel")
    random_per_collection_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel")
    random_per_collection_uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="1.0 for evenly distributed values, 0.0 for full randomness")

    random_per_object: BoolProperty(name="Random Per Object", default=False, description="Bake a random value per object")
    random_per_object_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake random values")
    random_per_object_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index")
    random_per_object_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel")
    random_per_object_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel")
    random_per_object_uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="1.0 for evenly distributed values, 0.0 for full randomness")

    random_per_poly: BoolProperty(name="Random Per Polygon", default=False, description="Bake a random value per polygon (duplicates vertices)")
    random_per_poly_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake random values")
    random_per_poly_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index")
    random_per_poly_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel")
    random_per_poly_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel")
    random_per_poly_uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="1.0 for evenly distributed values, 0.0 for full randomness")

    # parent
    parent_modes = [
        
        ("AUTOMATIC", "Automatic", "Automatically traverse parent hierarchy and bake all levels (up to a specified depth)"),
        ("MANUAL", "Manual", "Manually bake each hierarchy level in separate steps")
    ]
    parent_mode: EnumProperty(name="Mode", items=parent_modes, default="AUTOMATIC", description="Method for baking parent hierarchy")
    parent_depth: IntProperty(name="Current Depth", default=1, min=1, description="Hierarchy depth to bake. Mustn't be greater than 'Depth'")
    parent_max_depth: IntProperty(name="Max Depth", default=2, min=1, max=7, description="Maximum hierarchy depth to bake")
    parent_automatic_uv_index: IntProperty(name="Starting UV Map", min=0, max=7, default=1, description="Starting UV map index")
    parent_automatic_uv_channel: EnumProperty(name="Starting Channel", items=uv, default="U", description="Starting UV channel")

    # parent position
    parent_position: BoolProperty(name="Parent Position", default=False, description="Bake parent position data? Further actions are required depending on the selected mode. See @doc for more info")
    parent_position_channel_mode: EnumProperty(name="Channel Mode", items=pos_channels, default="INDIVIDUAL", description="Method for baking parent position")

    parent_position_x: BoolProperty(name="X", default=True, description="Bake X component of parent position")
    parent_position_x_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake X component")
    parent_position_x_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for X")
    parent_position_x_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for X")
    parent_position_x_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel for X")

    parent_position_y: BoolProperty(name="Y", default=True, description="Bake Y component of parent position")
    parent_position_y_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Y component")
    parent_position_y_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for Y")
    parent_position_y_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for Y")
    parent_position_y_rgba: EnumProperty(name="Channel", items=rgba, default="G", description="Target RGBA channel for Y")

    parent_position_z: BoolProperty(name="Z", default=True, description="Bake Z component of parent position")
    parent_position_z_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Z component")
    parent_position_z_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for Z")
    parent_position_z_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for Z")
    parent_position_z_rgba: EnumProperty(name="Channel", items=rgba, default="B", description="Target RGBA channel for Z")

    parent_position_packed_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map for packed position")
    parent_position_packed_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for packed position")
    parent_position_ab_packed_a_comp: EnumProperty(name="A Component", items=axis_xyz, default="X", description="First component for AB packing")
    parent_position_ab_packed_b_comp: EnumProperty(name="B Component", items=axis_xyz, default="Y", description="Second component for AB packing")

    # parent axis
    parent_axis: BoolProperty(name="Parent Axis", default=False, description="Bake parent axis data? Further actions are required depending on the selected mode. See @doc for more info")
    parent_axis_component: EnumProperty(name="Axis", items=axis_xyz, default="Z", description="Primary axis of the parent to bake")
    parent_axis_channel_mode: EnumProperty(name="Channel Mode", items=axis_modes, default="INDIVIDUAL", description="Method for baking parent axis")

    parent_axis_x: BoolProperty(name="X Component", default=True, description="Bake X component of parent axis")
    parent_axis_x_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake X component")
    parent_axis_x_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for X")
    parent_axis_x_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for X")
    parent_axis_x_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel for X")

    parent_axis_y: BoolProperty(name="Y Component", default=True, description="Bake Y component of parent axis")
    parent_axis_y_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Y component")
    parent_axis_y_uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index for Y")
    parent_axis_y_uv_channel: EnumProperty(name="Channel", items=uv, default="V", description="Target UV channel for Y")
    parent_axis_y_rgba: EnumProperty(name="Channel", items=rgba, default="G", description="Target RGBA channel for Y")

    parent_axis_z: BoolProperty(name="Z Component", default=True, description="Bake Z component of parent axis")
    parent_axis_z_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake Z component")
    parent_axis_z_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index for Z")
    parent_axis_z_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for Z")
    parent_axis_z_rgba: EnumProperty(name="Channel", items=rgba, default="B", description="Target RGBA channel for Z")

    parent_axis_packed_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map for packed axis")
    parent_axis_packed_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel for packed axis")
    parent_axis_ab_packed_a_comp: EnumProperty(name="A Component", items=axis_xyz, default="X", description="First component for AB packing")
    parent_axis_ab_packed_b_comp: EnumProperty(name="B Component", items=axis_xyz, default="Y", description="Second component for AB packing")

    # fixed value
    fixed_value: BoolProperty(name="Fixed Value", default=False, description="Bake a constant value")
    fixed_value_data: FloatProperty(name="Value", default=0.0, description="Value to bake")
    fixed_value_mode: EnumProperty(name="Mode", items=modes, default="UV", description="How to bake the fixed value")
    fixed_value_uv_index: IntProperty(name="UV Map", min=0, max=7, default=2, description="Target UV map index")
    fixed_value_uv_channel: EnumProperty(name="Channel", items=uv, default="U", description="Target UV channel")
    fixed_value_rgba: EnumProperty(name="Channel", items=rgba, default="R", description="Target RGBA channel")

    # direction
    direction: BoolProperty(name="Direction", default=False, description="Bake a directional vector (normalized)")
    direction_modes = [
        ("3DRAND", "Random 3D", "Random 3D unit vector in [-1:1] range"),
        ("2DRAND", "Random 2D", "Random 2D unit vector in [-1:1] range, Z=0"),
        ("3DVECTOR", "3D Vector", "User-specified 3D direction"),
        ("2DVECTOR", "2D Vector", "User-specified 2D direction, Z=0")
    ]

    direction_mode: EnumProperty(name="Vector Mode", items=direction_modes, default="3DRAND", description="Method for generating the direction")
    direction_vector_x: FloatProperty(name="X", default=0.0, description="X component of the direction vector")
    direction_vector_y: FloatProperty(name="Y", default=0.0, description="Y component of the direction vector")
    direction_vector_z: FloatProperty(name="Z", default=1.0, description="Z component of the direction vector")
    direction_pack_modes = [
        ("NORMALS", "Normals", "Store in mesh normals (overrides existing normals)"),
        ("VCOL", "Vertex Color", "Store in vertex colors, remapped to [0:1]"),
    ]
    direction_pack_mode: EnumProperty(name="Mode", items=direction_pack_modes, default="NORMALS", description="Select how the direction is baked")

    # mesh
    duplicate_mesh: BoolProperty(name="Duplicate Mesh", default=True, description="Duplicate mesh before baking to preserve original. Disable at your own risk")
    make_single_user: BoolProperty(name="Make Single-User", default=True, description="Ensure mesh data is unique to avoid conflicts. Ensured if duplicated, else, disable at your own risk")
    merge_mesh: BoolProperty(name="Merge Meshes", default=True, description="Merge all baked meshes into one. Safe to enable if duplicated, else, use at your own risk")
    clean_bake: BoolProperty(name="Clean Up", default=True, description="Remove temporary objects after baking")
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")
    scale: FloatProperty(name="Scale Factor", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")
    invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    origin: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="Optional object to use as baking origin")
    precision_offset: FloatProperty(name="Precision Offset", min=1.0, default=1.0, description="Offset to improve packing precision")

    export_mesh: BoolProperty(name="Export", default=True, description="True to export the mesh to FBX upon bake completion")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="FBX file name, without extension")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="FBX file path, not including file name", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="True to override any existing .fbx file")

    # uv
    uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData", description="UVMap to get or create for setting up the mesh UVs")
    invert_v: BoolProperty(name="Invert V", default=True, description="Invert UVMap's V axis & flip VAT texture(s) upside down (typically True for exporting to UE or DirectX apps in general, False for Unity or OpenGL apps in general)")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended)")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the xml file name & path is computed")
    export_xml_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="XML file name, without extension")
    export_xml_file_path: StringProperty(name="Path", default="//", description="XML file path, not including file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="True to override any existing .xml file")

class DATABAKER_PG_ReportUVMapPropertyGroup(PropertyGroup):
    """Properties for reporting animation-related bake data."""

    ID: StringProperty(name="ID", default="", description="Unique identifier for the animation data")
    name: StringProperty(name="Name", default="", description="Name of the animation data")

class DATABAKER_PG_ReportPropertyGroup(PropertyGroup):
    """Enhanced reporting properties for DataBaker with detailed feedback."""

    baked: BoolProperty(name="Baked", default=False, description="")
    success: BoolProperty(name="Success", default=False, description="")
    msg: StringProperty(name="Message", default="", description="")
    name: StringProperty(name="Name", default="", description="")
    ID: StringProperty(name="ID", default="", description="")

    unit_system: StringProperty(name="Unit System", default="", description="")
    unit_unit: StringProperty(name="Unit", default="", description="")
    unit_length: FloatProperty(name="Unit Length", default=0.0, description="")
    unit_scale: FloatProperty(name="Scale Factor", default=0.0, description="")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="")
    unit_invert_y: BoolProperty(name="Invert Y", default=False, description="")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="")

    position_multiplier: FloatProperty(name="Position Multiplier", default=0.0, description="")
    parent_position_multiplier: FloatProperty(name="Parent Position Multiplier", default=0.0, description="")
    shapekey_offset_multiplier: FloatProperty(name="Shape Key Offset Multiplier", default=0.0, description="")

    mesh: PointerProperty(type=bpy.types.Object, description="")
    mesh_export: BoolProperty(name="Mesh Exported", default=False, description="")
    mesh_path: StringProperty(name="Mesh Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_uvmaps: CollectionProperty(type=DATABAKER_PG_ReportUVMapPropertyGroup, description="")
    select_mesh_uvmap: IntProperty(name="Selected UV Map", default=0, description="")
    mesh_uvmap_invert_v: BoolProperty(name="Invert V", default=False, description="")
    mesh_uvmap_count: IntProperty(name="UV Map Count", default=0, description="")

    meshes_count: IntProperty(name="Mesh Count", default=0, description="")
    empties_count: IntProperty(name="Empty Count", default=0, description="")

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

    transform_obj: PointerProperty(type=bpy.types.Object, name="Object", description="")

    # position
    position: BoolProperty(name="Position", default=False, description="")
    position_channel_mode: StringProperty(name="Mode", default="", description="")
    position_x: BoolProperty(name="X", default=True, description="")
    position_x_mode: StringProperty(name="Mode", default="", description="")
    position_x_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    position_x_uv_channel: StringProperty(name="Channel", default="", description="")
    position_x_rgba: StringProperty(name="Channel", default="", description="")
    position_y: BoolProperty(name="Y", default=True, description="")
    position_y_mode: StringProperty(name="Mode", default="", description="")
    position_y_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    position_y_uv_channel: StringProperty(name="Channel", default="", description="")
    position_y_rgba: StringProperty(name="Channel", default="", description="")
    position_z: BoolProperty(name="Z", default=True, description="")
    position_z_mode: StringProperty(name="Mode", default="", description="")
    position_z_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    position_z_uv_channel: StringProperty(name="Channel", default="", description="")
    position_z_rgba: StringProperty(name="Channel", default="", description="")
    position_packed_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    position_packed_uv_channel: StringProperty(name="Channel", default="", description="")
    position_pack_only_if_non_null: BoolProperty(name="Pack Only If Non-Zero", default=True, description="")
    position_ab_packed_a_comp: StringProperty(name="A Component", default="", description="")
    position_ab_packed_b_comp: StringProperty(name="B Component", default="", description="")

    # axis
    axis: BoolProperty(name="Axis", default=False, description="") #
    axis_component: StringProperty(name="Axis", default="", description="")
    axis_channel_mode: StringProperty(name="Mode", default="", description="")
    axis_x: BoolProperty(name="X Component", default=True, description="")
    axis_x_mode: StringProperty(name="Mode", default="", description="")
    axis_x_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    axis_x_uv_channel: StringProperty(name="Channel", default="", description="")
    axis_x_rgba: StringProperty(name="Channel", default="", description="")
    axis_y: BoolProperty(name="Y Component", default=True, description="")
    axis_y_mode: StringProperty(name="Mode", default="", description="")
    axis_y_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    axis_y_uv_channel: StringProperty(name="Channel", default="", description="")
    axis_y_rgba: StringProperty(name="Channel", default="", description="")
    axis_z: BoolProperty(name="Z Component", default=True, description="")
    axis_z_mode: StringProperty(name="Mode", default="", description="")
    axis_z_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    axis_z_uv_channel: StringProperty(name="Channel", default="", description="")
    axis_z_rgba: StringProperty(name="Channel", default="", description="")
    axis_packed_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    axis_packed_uv_channel: StringProperty(name="Channel", default="", description="")
    axis_ab_packed_a_comp: StringProperty(name="A Component", default="", description="")
    axis_ab_packed_b_comp: StringProperty(name="B Component", default="", description="")
    
    # shapekey
    shapekey_name: StringProperty(name="Shapekey", default="Key 1", description="")
    shapekey_rest_name: StringProperty(name="Rest Shapekey", default="Basis", description="")
    
    # shapekey offset
    shapekey_offset: BoolProperty(name="Shapekey Offset", default=False, description="") #
    shapekey_offset_channel_mode: StringProperty(name="Mode", default="", description="")
    shapekey_offset_x: BoolProperty(name="X", default=True, description="")
    shapekey_offset_x_mode: StringProperty(name="Mode", default="", description="")
    shapekey_offset_x_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    shapekey_offset_x_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_offset_x_rgba: StringProperty(name="Channel", default="", description="")
    shapekey_offset_y: BoolProperty(name="Y", default=True, description="")
    shapekey_offset_y_mode: StringProperty(name="Mode", default="", description="")
    shapekey_offset_y_uv_index: IntProperty(name="UV Map", min=0, default=3, description="")
    shapekey_offset_y_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_offset_y_rgba: StringProperty(name="Channel", default="", description="")
    shapekey_offset_z: BoolProperty(name="Z", default=True, description="")
    shapekey_offset_z_mode: StringProperty(name="Mode", default="", description="")
    shapekey_offset_z_uv_index: IntProperty(name="UV Map", min=0, default=3, description="")
    shapekey_offset_z_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_offset_z_rgba: StringProperty(name="Channel", default="", description="")
    shapekey_offset_packed_uv_index: IntProperty(name="UV Map", min=0, default=3, description="")
    shapekey_offset_packed_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_offset_pack_only_if_non_null: BoolProperty(name="Pack Only If Non-Zero", default=True, description="")
    shapekey_offset_ab_packed_a_comp: StringProperty(name="A Component", default="", description="")
    shapekey_offset_ab_packed_b_comp: StringProperty(name="B Component", default="", description="")

    # shapekey normal
    shapekey_normal: BoolProperty(name="Shapekey Normal", default=False, description="") #
    shapekey_normal_channel_mode: StringProperty(name="Mode", default="", description="")
    shapekey_normal_x: BoolProperty(name="X", default=True, description="")
    shapekey_normal_x_mode: StringProperty(name="Mode", default="", description="")
    shapekey_normal_x_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    shapekey_normal_x_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_normal_x_rgba: StringProperty(name="Channel", default="", description="")
    shapekey_normal_y: BoolProperty(name="Y", default=True, description="")
    shapekey_normal_y_mode: StringProperty(name="Mode", default="", description="")
    shapekey_normal_y_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    shapekey_normal_y_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_normal_y_rgba: StringProperty(name="Channel", default="", description="")
    shapekey_normal_z: BoolProperty(name="Z", default=True, description="")
    shapekey_normal_z_mode: StringProperty(name="Mode", default="", description="")
    shapekey_normal_z_uv_index: IntProperty(name="UV Map", min=0, default=3, description="")
    shapekey_normal_z_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_normal_z_rgba: StringProperty(name="Channel", default="", description="")
    shapekey_normal_xyz_uv_index: IntProperty(name="UV Map", min=0, default=3, description="")
    shapekey_normal_xyz_uv_channel: StringProperty(name="Channel", default="", description="")
    shapekey_normal_ab_packed_a_comp: StringProperty(name="A Component", default="", description="")
    shapekey_normal_ab_packed_b_comp: StringProperty(name="B Component", default="", description="")

    # sphere mask
    sphere_mask: BoolProperty(name="Sphere Mask", default=False, description="") #
    sphere_mask_normalize: BoolProperty(name="Normalize", default=True, description="")
    sphere_mask_clamp: BoolProperty(name="Clamp", default=False, description="")
    sphere_mask_origin_mode: StringProperty(name="Origin", default="", description="")
    sphere_mask_origin: PointerProperty(type=bpy.types.Object, name="Object", description="")
    sphere_mask_mode: StringProperty(name="Mode", default="", description="")
    sphere_mask_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    sphere_mask_uv_channel: StringProperty(name="Channel", default="", description="")
    sphere_mask_rgba: StringProperty(name="Channel", default="", description="")
    sphere_mask_falloff: FloatProperty(name="Falloff", min=0.0, default=1.0, description="")

    # linear mask
    linear_mask: BoolProperty(name="Linear Mask", default=False, description="") #
    linear_mask_normalize: BoolProperty(name="Normalize", default=True, description="")
    linear_mask_clamp: BoolProperty(name="Clamp", default=False, description="")
    linear_mask_obj_mode: StringProperty(name="Mode", default="", description="")
    linear_mask_obj: PointerProperty(type=bpy.types.Object, name="Object", description="")
    linear_mask_mode: StringProperty(name="Mode", default="", description="")
    linear_mask_axis: StringProperty(name="Axis", default="", description="")
    linear_mask_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    linear_mask_uv_channel: StringProperty(name="Channel", default="", description="")
    linear_mask_rgba: StringProperty(name="Channel", default="", description="")
    linear_mask_falloff: FloatProperty(name="Falloff", min=0.0, default=1.0, description="")
    
    # random per collection
    random_per_collection: BoolProperty(name="Random Per Collection", default=False, description="") #
    random_per_collection_mode: StringProperty(name="Mode", default="", description="")
    random_per_collection_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    random_per_collection_uv_channel: StringProperty(name="Channel", default="", description="")
    random_per_collection_rgba: StringProperty(name="Channel", default="", description="")
    random_per_collection_uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="")
    
    # random per object
    random_per_object: BoolProperty(name="Random Per Object", default=False, description="") #
    random_per_object_mode: StringProperty(name="Mode", default="", description="")
    random_per_object_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    random_per_object_uv_channel: StringProperty(name="Channel", default="", description="")
    random_per_object_rgba: StringProperty(name="Channel", default="", description="")
    random_per_object_uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="")
    
    # random per poly
    random_per_poly: BoolProperty(name="Random Per Poly", default=False, description="") #
    random_per_poly_mode: StringProperty(name="Mode", default="", description="")
    random_per_poly_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    random_per_poly_uv_channel: StringProperty(name="Channel", default="", description="")
    random_per_poly_rgba: StringProperty(name="Channel", default="", description="")
    random_per_poly_uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="")

    # parent
    parent_mode: StringProperty(name="Mode", default="", description="") #
    parent_depth: IntProperty(name="Current", default=1, min=1, description="")
    parent_max_depth: IntProperty(name="Depth", default=2, min=1, max=7, description="")
    parent_automatic_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    parent_automatic_uv_channel: StringProperty(name="Channel", default="", description="")

    # parent position
    parent_position: BoolProperty(name="Position", default=False, description="") #
    parent_position_channel_mode: StringProperty(name="Mode", default="", description="")
    parent_position_x: BoolProperty(name="X", description="")
    parent_position_x_mode: StringProperty(name="Mode", default="", description="")
    parent_position_x_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    parent_position_x_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_position_x_rgba: StringProperty(name="Channel", default="", description="")
    parent_position_y: BoolProperty(name="Y", description="")
    parent_position_y_mode: StringProperty(name="Mode", default="", description="")
    parent_position_y_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    parent_position_y_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_position_y_rgba: StringProperty(name="Channel", default="", description="")
    parent_position_z: BoolProperty(name="Z", description="")
    parent_position_z_mode: StringProperty(name="Mode", default="", description="")
    parent_position_z_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    parent_position_z_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_position_z_rgba: StringProperty(name="Channel", default="", description="")
    parent_position_packed_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    parent_position_packed_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_position_ab_packed_a_comp: StringProperty(name="A Component", default="", description="")
    parent_position_ab_packed_b_comp: StringProperty(name="B Component", default="", description="")
    
    # parent axis
    parent_axis: BoolProperty(name="Axis", default=False, description="") #
    parent_axis_component: StringProperty(name="Axis", default="", description="")
    parent_axis_channel_mode: StringProperty(name="Mode", default="", description="")
    parent_axis_x: BoolProperty(name="X Component", description="")
    parent_axis_x_mode: StringProperty(name="Mode", default="", description="")
    parent_axis_x_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    parent_axis_x_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_axis_x_rgba: StringProperty(name="Channel", default="", description="")
    parent_axis_y: BoolProperty(name="Y Component", description="")
    parent_axis_y_mode: StringProperty(name="Mode", default="", description="")
    parent_axis_y_uv_index: IntProperty(name="UV Map", min=0, default=1, description="")
    parent_axis_y_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_axis_y_rgba: StringProperty(name="Channel", default="", description="")
    parent_axis_z: BoolProperty(name="Z Component", description="")
    parent_axis_z_mode: StringProperty(name="Mode", default="", description="")
    parent_axis_z_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    parent_axis_z_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_axis_z_rgba: StringProperty(name="Channel", default="", description="")
    parent_axis_packed_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    parent_axis_packed_uv_channel: StringProperty(name="Channel", default="", description="")
    parent_axis_ab_packed_a_comp: StringProperty(name="A Component", default="", description="")
    parent_axis_ab_packed_b_comp: StringProperty(name="B Component", default="", description="")

    # fixed value
    fixed_value: BoolProperty(name="Fixed Value", default=False, description="") #
    fixed_value_data: FloatProperty(name="Value", default=0.0, description="")
    fixed_value_mode: StringProperty(name="Mode", default="", description="")
    fixed_value_uv_index: IntProperty(name="UV Map", min=0, default=2, description="")
    fixed_value_uv_channel: StringProperty(name="Channel", default="", description="")
    fixed_value_rgba: StringProperty(name="Channel", default="", description="")

    # direction
    direction: BoolProperty(name="Direction", default=False, description="") #
    direction_mode: StringProperty(name="Vector", default="", description="")
    direction_vector_x: FloatProperty(name="X", default=0.0, description="")
    direction_vector_y: FloatProperty(name="Y", default=0.0, description="")
    direction_vector_z: FloatProperty(name="Z", default=1.0, description="")
    direction_pack_mode: StringProperty(name="Mode", default="", description="")

    # mesh
    duplicate_mesh: BoolProperty(name="Duplicate Mesh", default=True, description="")
    make_single_user: BoolProperty(name="Make Single-User", default=True, description="")
    merge_mesh: BoolProperty(name="Merge Meshes", default=True, description="")
    clean_bake: BoolProperty(name="Clean Up", default=True, description="")
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="")
    scale: FloatProperty(name="Scale Factor", min=0.001, default=100.0, description="")
    invert_x: BoolProperty(name="Invert X", default=False, description="")
    invert_y: BoolProperty(name="Invert Y", default=True, description="")
    invert_z: BoolProperty(name="Invert Z", default=False, description="")
    origin: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="")
    precision_offset: FloatProperty(name="Precision Offset", min=1.0, default=1.0, description="")

    export_mesh: BoolProperty(name="Export", default=True, description="")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="")
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="")

def register():
    bpy.types.Scene.DataBakerSettings = PointerProperty(type=DATABAKER_PG_SettingsPropertyGroup)
    bpy.types.Scene.DataBakerReport = PointerProperty(type=DATABAKER_PG_ReportPropertyGroup)

def unregister():
    del bpy.types.Scene.DataBakerSettings
    del bpy.types.Scene.DataBakerReport
