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
from ctypes import POINTER, pointer, c_int, c_uint, cast, c_float
import bmesh
import math
import os
import sys
import mathutils
from mathutils.bvhtree import BVHTree
import xml.etree.ElementTree as ET
import uuid
import time

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################

##############
### REPORT ###
def new_bake_report(context: bpy.types.Context):
    """
    Reset the bake report and start a new one

    :param context: Blender current execution context
    :return: None
    :rtype: None
    """
    settings = context.scene.BATBakerSettings

    reset_bake_report()

    add_bake_report("baked", True)
    add_bake_report("ID", uuid.uuid4().hex)
    add_bake_report("unit_system", context.scene.unit_settings.system)
    add_bake_report("unit_unit", context.scene.unit_settings.length_unit)
    add_bake_report("unit_length", context.scene.unit_settings.scale_length)
    add_bake_report("unit_scale", settings.unit_scale)
    add_bake_report("unit_invert_x", settings.unit_invert_x)
    add_bake_report("unit_invert_y", settings.unit_invert_y)
    add_bake_report("unit_invert_z", settings.unit_invert_z)
    add_bake_report("unit_invert_v", settings.unit_invert_v)

def reset_bake_report():
    """
    Set all report properties to their default values

    :return: None
    :rtype: None
    """
    report = bpy.context.scene.BATBakerReport
    report.baked = False
    report.success = False
    report.msg = ""
    report.name = ""
    report.ID = ""
    
    report.unit_system = ""
    report.unit_unit = ""
    report.unit_length = 0.0
    report.unit_scale = 0.0
    report.unit_invert_x = False
    report.unit_invert_y = False
    report.unit_invert_z = False
    report.unit_invert_v = False

    report.padded = False
    report.padding = 0
    report.padding_mode = "SUFFIX"
    report.ref_mode = ""
    report.ref_custom = 0
    report.anims.clear()
    report.selected_anim = 0
    
    report.start_frame = 0
    report.end_frame = 0
    report.num_frames = 0
    report.num_frames_padded = 0
    report.frame_step = 0
    report.frame_step_mode = "GLOBAL"
    report.frame_height = 0.0
    report.frame_width = 0.0
    report.frame_rate = 0
    report.frame_ref = 0
    report.frame_ref_mode = ""
    
    report.num_bones = 0
    report.num_bones_max = 0
    report.num_verts = 0
    
    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_uvmap_index = 0
    report.mesh_min_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.mesh_max_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))

    report.animation_textures.clear()
    report.animation_textures_selected_index = 0
    report.animation_tex_width = 0
    report.animation_tex_height = 0
    report.animation_tex_underflow = False
    report.animation_tex_overflow = False
    report.animation_tex_sampling_mode = ""
    report.animation_tex_packing_stack_mode = "ADJACENT"

    report.skinning_textures.clear()
    report.skinning_textures_selected_index = 0
    report.skinning_tex_width = 0
    report.skinning_tex_height = 0
    report.skinning_tex_rows = 0
    report.skinning_tex_res_mode = ""

    report.xml = False
    report.xml_path = ""

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """
    Set a value in the bake report

    :param prop_name: report property to set
    :param prop_value: value to assign to the property
    :return: None
    :rtype: None
    """
    setattr(bpy.context.scene.BATBakerReport, prop_name, prop_value)

def add_bake_skinning_texture_report(texture: object, img: bpy.types.Image) -> object:
    """
    Create a new texture in the bake report

    :param texture: texture to generate report for
    :param img: image generated for baking
    :return: the report texture object created
    :rtype: object
    """
    report = bpy.context.scene.BATBakerReport

    report_skinning_texture = report.skinning_textures.add()
    report_skinning_texture.name = texture.name
    report_skinning_texture.exported = False
    report_skinning_texture.path = ""
    report_skinning_texture.img = img
    report_skinning_texture.storage_mode = texture.storage_mode

    # copy all texture attributes
    if hasattr(texture, "__annotations__"):
        for prop_name in texture.__annotations__.keys():
            try:
                setattr(report_skinning_texture, prop_name, getattr(texture, prop_name))
            except (AttributeError, TypeError):
                pass

    # for each row in the texture
    for texture_row in texture.rows:
        # create row in report texture
        report_texture_row = report_skinning_texture.rows.add()

        # copy all row attributes
        if hasattr(texture_row, "__annotations__"):
            for prop_name in texture_row.__annotations__.keys():
                try:
                    setattr(report_texture_row, prop_name, getattr(texture_row, prop_name))
                except (AttributeError, TypeError):
                    pass

        # for all channels in texture row
        row_channels = [texture_row.R, texture_row.G, texture_row.B, texture_row.A]
        report_row_channels = [report_texture_row.R, report_texture_row.G, report_texture_row.B, report_texture_row.A]
        for row_channel_index, row_channel in enumerate(row_channels):
            if hasattr(row_channel, "__annotations__"):
                for prop_name in row_channel.__annotations__.keys():
                    try:
                        setattr(report_row_channels[row_channel_index], prop_name, getattr(row_channels[row_channel_index], prop_name))
                    except (AttributeError, TypeError):
                        pass

    return report_skinning_texture

def edit_bake_skinning_texture_report_prop(texture: object, value, prop_name: str) -> bool:
    """
    Edit a texture in the report to modify the value stored in a property of a given name

    :param texture: texture to edit in the report
    :param value: value to tweak
    :param prop_name: property to tweak in the report texture PropertyGroup
    :return: True if edited
    :rtype: bool
    """
    report = bpy.context.scene.BATBakerReport

    for report_texture in report.skinning_textures:
        if report_texture == texture:
            setattr(report_texture, prop_name, value)
            return True

    return False

def edit_bake_skinning_texture_report_path(texture: object, path: str) -> bool:
    """
    Edit a texture in the report to modify its path

    :param texture: texture to edit in the report
    :param path: new path to set
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_skinning_texture_report_prop(texture, path, "path")

def edit_bake_skinning_texture_report_exported(texture: object, exported: bool):
    """
    Edit a texture in the report to modify its 'exported' status

    :param texture: texture to edit in the report
    :param exported: new 'exported' status
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_skinning_texture_report_prop(texture, exported, "exported")

def clear_bake_skinning_texture_report(texture: object) -> bool:
    """
    Remove a texture from the report
    
    :param texture: texture to remove from the report
    :return: True if cleared/removed
    :rtype: bool
    """
    report = bpy.context.scene.BATBakerReport
    
    for report_texture in report.skinning_textures:
        if report_texture == texture:
            report.skinning_textures.remove(report_texture)

    return True

def add_bake_animation_texture_report(texture: object, img: bpy.types.Image, buffer_ranges_offsets: list, buffer_ranges: list, buffer_ranges_valid: list) -> object:
    """
    Create a new texture in the bake report

    :param texture: texture to generate report for
    :param img: image generated for baking
    :param buffer_ranges_offsets: min value. One value per RGBA channel
    :param buffer_ranges: range is describe as (max value - min value). One value per RGBA channel
    :param buffer_ranges_valid: true if range is valid, aka (max - min) is not null. One value per RGBA channel
    :return: the report texture object created
    :rtype: object
    """
    report = bpy.context.scene.BATBakerReport

    report_texture = report.animation_textures.add()
    report_texture.name = texture.name
    report_texture.exported = False
    report_texture.path = ""
    report_texture.img = img

    report_texture.R_range_offset = buffer_ranges_offsets[0]
    report_texture.R_range = buffer_ranges[0]
    report_texture.R_range_valid = buffer_ranges_valid[0]
    report_texture.G_range_offset = buffer_ranges_offsets[1]
    report_texture.G_range = buffer_ranges[1]
    report_texture.G_range_valid = buffer_ranges_valid[0]
    report_texture.B_range_offset = buffer_ranges_offsets[2]
    report_texture.B_range = buffer_ranges[2]
    report_texture.B_range_valid = buffer_ranges_valid[0]
    report_texture.A_range_offset = buffer_ranges_offsets[3]
    report_texture.A_range = buffer_ranges[3]
    report_texture.A_range_valid = buffer_ranges_valid[0]

    # copy all attributes
    if hasattr(texture, "__annotations__"):
        for prop_name in texture.__annotations__.keys():
            try:
                setattr(report_texture, prop_name, getattr(texture, prop_name))
            except (AttributeError, TypeError):
                pass

        channels = [texture.R, texture.G, texture.B, texture.A]
        report_channels = [report_texture.R, report_texture.G, report_texture.B, report_texture.A]
        for channel_index, channel in enumerate(channels):
            for prop_name in channel.__annotations__.keys():
                try:
                    setattr(report_channels[channel_index], prop_name, getattr(channels[channel_index], prop_name))
                except (AttributeError, TypeError):
                    pass

    return report_texture

def edit_bake_animation_texture_report_prop(texture: object, value, prop_name: str) -> bool:
    """
    Edit a texture in the report to modify the value stored in a property of a given name

    :param texture: texture to edit in the report
    :param value: value to tweak
    :param prop_name: property to tweak in the report texture PropertyGroup
    :return: True if edited
    :rtype: bool
    """
    report = bpy.context.scene.BATBakerReport
    
    for report_texture in report.animation_textures:
        if report_texture == texture:
            setattr(report_texture, prop_name, value)
            return True

    return False

def edit_bake_animation_texture_report_path(texture: object, path: str) -> bool:
    """
    Edit a texture in the report to modify its path
    
    :param texture: texture to edit in the report
    :param path: new path to set
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_animation_texture_report_prop(texture, path, "path")

def edit_bake_animation_texture_report_exported(texture: object, exported: bool):
    """
    Edit a texture in the report to modify its 'exported' status
    
    :param texture: texture to edit in the report
    :param exported: new 'exported' status
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_animation_texture_report_prop(texture, exported, "exported")

def clear_bake_animation_texture_report(texture: object) -> bool:
    """
    Remove a texture from the report
    
    :param texture: texture to remove from the report
    :return: True if cleared/removed
    :rtype: bool
    """
    report = bpy.context.scene.BATBakerReport
    
    for report_texture in report.animation_textures:
        if report_texture == texture:
            report.animation_textures.remove(report_texture)

    return True

def add_bake_report_anim(name: str, frame_start: int, frame_end: int):
    """
    Set values in the bake report to describe an animation clip

    :param name: animation's name
    :param frame_start: animation's start frame
    :param frame_end: animation's end frame
    :return: None
    :rtype: None
    """
    settings = bpy.context.scene.BATBakerSettings
    report = bpy.context.scene.BATBakerReport

    report_anim = report.anims.add()
    report_anim.name = name
    report_anim.start_frame = frame_start
    report_anim.end_frame = frame_end

def export_bake_report(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    return(export_xml(context))

###############
### PACKING ###
def get_compressed_quat(quat: mathutils.Quaternion) -> float:
    """
    Quaternion packing using the three smallest component method (from quat to 32bits float)
    @NOTE X component precision was reduced from 10 to 9 bits to avoid writing NaNs which IS
    problematic, though it technically shouldn't

    :param quat: WXYZ quaternion to pack
    :return: bit-packed float
    :rtype: float
    """
    abs_quat_component = 0.0
    max_abs_quat_component = -1000.0
    max_abs_quat_component_index = 0

    # re-order quat components... Blender is WXYZ ordered
    quat_components = [
        quat.x,
        quat.y,
        quat.z,
        quat.w
    ]

    # get quat's largest absolute component
    for quat_component_index in range(4):
        abs_quat_component = abs(quat_components[quat_component_index])

        if abs_quat_component > max_abs_quat_component:
            max_abs_quat_component = abs_quat_component

            max_abs_quat_component_index = quat_component_index

    # ensure quat's largest component is positive so we don't have to save sign
    quat_largest_component_sign = -1.0 if quat_components[max_abs_quat_component_index] < 0.0 else 1.0
    quat_components[0] *= quat_largest_component_sign
    quat_components[1] *= quat_largest_component_sign
    quat_components[2] *= quat_largest_component_sign
    quat_components[3] *= quat_largest_component_sign

    packed_quat = mathutils.Vector((0.0,0.0,0.0))
    # pack the smallest 3 components - fourth can be later reconstructed due to quaternions' property
    if max_abs_quat_component_index == 0: # X component is largest!!
        packed_quat = mathutils.Vector((quat_components[1], quat_components[2], quat_components[3]))
        bitstring_index = "00"
    elif max_abs_quat_component_index == 1: # Y component is largest!!
        packed_quat = mathutils.Vector((quat_components[0], quat_components[2], quat_components[3]))
        bitstring_index = "01"
    elif max_abs_quat_component_index == 2: # Z component is largest!!
        packed_quat = mathutils.Vector((quat_components[0], quat_components[1], quat_components[3]))
        bitstring_index = "10"
    else: # W component is largest!!
        packed_quat = mathutils.Vector((quat_components[0], quat_components[1], quat_components[2]))
        bitstring_index = "11"

    # none of the 3 smallest components of a quat can be larger than 1/sqrt(2), so it can be remapped to increase accuracy
    quat_normalization_offset = 0.707106781
    quat_normalization_scale = quat_normalization_offset + quat_normalization_offset

    packed_quat.x = min(1.0, max(0.0, (packed_quat.x + quat_normalization_offset) / quat_normalization_scale))
    packed_quat.y = min(1.0, max(0.0, (packed_quat.y + quat_normalization_offset) / quat_normalization_scale))
    packed_quat.z = min(1.0, max(0.0, (packed_quat.z + quat_normalization_offset) / quat_normalization_scale))

    # XYZ component converted into [0:1023] integer range to be packed into 10 bits
    int_packed_quat_x = math.floor(packed_quat.x * 511)
    int_packed_quat_y = math.floor(packed_quat.y * 1023)
    int_packed_quat_z = math.floor(packed_quat.z * 1023)

    bitstring_x = str(bin(int_packed_quat_x))
    bitstring_x = bitstring_x[2:] # get rid of 0b
    bitstring_x = bitstring_x.zfill(9) # ensure it's 10 char long

    bitstring_y = str(bin(int_packed_quat_y))
    bitstring_y = bitstring_y[2:] # get rid of 0b
    bitstring_y = bitstring_y.zfill(10) # ensure it's 10 char long

    bitstring_z = str(bin(int_packed_quat_z))
    bitstring_z = bitstring_z[2:] # get rid of 0b
    bitstring_z = bitstring_z.zfill(10) # ensure it's 10 char long

    bits_string = bitstring_index + "0" + bitstring_x + bitstring_y + bitstring_z
    bits_string = "0b" + bits_string

    cp = pointer(c_uint(int(bits_string, 0)))
    fp = cast(cp, POINTER(c_float))

    return fp.contents.value

############
### BAKE ###
def get_bake_skinning_textures(context: bpy.types.Context) -> tuple[bool, str, list, int]:
    """
    Scan the skinning textures the user wants to generate, ensuring each has a unique name and contains data in at least one of the RGBA channels.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of textures to generate and bake, max amount of influencing bone
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings

    max_index = 0

    textures = []
    influences = []
    vcol = False
    for texture in settings.skinning_textures:
        """
        ensure textures do not share the same name
        """
        other_tex_names = [other_texture.name for other_texture in settings.skinning_textures if other_texture != texture]
        animation_tex_names = [animation_texture.name for animation_texture in settings.animation_textures] # account for animation textures (there are two separate sets of textures)
        all_other_tex_names = other_tex_names + animation_tex_names
        if texture.name in all_other_tex_names: # texture must be uniquely named
            return (False, "Multiple textures share the same name", None, 0)

        """
        ensure vertex color isn't targeted more than once
        """
        if texture.storage_mode == "VCOL":
            if vcol:
                return (False, "Vertex Color targeted multiple times", None, 0)
            else:
                vcol = True
                if len(texture.rows) > 1:
                    return (False, "Vertex Color can only write one set of RGBA data", None, 0)

        """
        ensure at least one channel outputs something and also make sure that channel aren't targeted more than once
        """
        rows = 0
        for texture_row in texture.rows:
            if texture_row.R.channel_mode == "NONE" and texture_row.G.channel_mode == "NONE" and texture_row.B.channel_mode == "NONE" and texture_row.A.channel_mode == "NONE":
                continue

            rows += 1

            channels = [
                texture_row.R,
                texture_row.G,
                texture_row.B,
                texture_row.A,
            ]

            for channel in channels:
                while len(influences) < channel.index:
                    influences.append([None, None])

                influence = influences[channel.index - 1]

                if channel.channel_mode == "INDEX":
                    if influence[0]:
                        return (False, "Bone influence index " + str(channel.index) + " is baked more than once", None, 0)
                    else:
                        influence[0] = channel.index
                elif channel.channel_mode == "WEIGHT":
                    if influence[1]:
                        return (False, "Bone influence weight " + str(channel.index) + " is baked more than once", None, 0)
                    else:
                        influence[1] = channel.index
                else: # NONE
                    pass

                if channel.channel_mode != "NONE":
                    max_index = max(max_index, channel.index)

        # valid texture!
        if rows > 0:
            textures.append(texture)

    if len(textures) <= 0:
        return (False, "No data to bake in texture(s)", None, 0)

    """
    list all indices that must be accounted for, based on maximum index
    """
    bones_indices = list(range(1, max_index))
    bones_weights = list(range(1, max_index))

    for i, influence in enumerate(influences):
        influence_index, influence_weight = influence

        if influence_index != influence_weight:
            return (False, "Bone influence mismatch: index " + str(influence_index) + " and weight " + str(influence_weight), None, 0)

        if influence_index != None:
            try:
                bones_indices.pop(bones_indices.index(influence_index))
            except:
                pass
        
        if influence_weight != None:
            try:
                bones_weights.pop(bones_weights.index(influence_weight))
            except:
                pass

    if len(bones_indices) > 0:
        return (False, "Bone index(ices) missing", None, 0)
    if len(bones_weights) > 0:
        return (False, "Bone weight(s) missing", None, 0)

    add_bake_report("num_bones_max", max_index)

    return (True, "", textures, max_index)

def get_bake_animation_textures(context: bpy.types.Context) -> tuple[bool, str, list]:
    """
    Scan the animation textures the user wants to generate, ensuring each has a unique name and contains data in at least one of the RGBA channels.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of textures to generate and bake
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings

    textures = []
    for texture in settings.animation_textures:
        other_tex_names = [other_texture.name for other_texture in settings.animation_textures if other_texture != texture]
        skinning_tex_names = [skinning_texture.name for skinning_texture in settings.skinning_textures] # account for index/weight textures (there are two separate sets of textures)
        all_other_tex_names = other_tex_names + skinning_tex_names
        if texture.name in all_other_tex_names: # texture must be uniquely named
            return (False, "Multiple animation textures share the same name", None)

        if texture.R.channel_mode == "NONE" and texture.G.channel_mode == "NONE" and texture.B.channel_mode == "NONE" and texture.A.channel_mode == "NONE":
            continue

        textures.append(texture)

    if len(textures) <= 0:
        return (False, "No data to bake in texture(s)", None)

    return (True, "", textures)

def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object, bpy.types.Armature]:
    """
    Modify & ensure the active & selected objects can lead to a valid bake and return the list of objects to include in the bake.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of objects to bake (filtered selection), active object, target armature
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    if context.view_layer.objects.active == None:
        return (False, "No active object", None, None, None)

    """
    1. deselect non mesh objects & ensure mesh have vertices
    """
    for selected_obj in context.selected_objects:
        if selected_obj.type != "MESH":
            selected_obj.select_set(False)
        elif len(selected_obj.data.vertices) <= 0: # mesh could have no vertices
            selected_obj.select_set(False)

    """
    2a. gather & deselect TARGET objects (remapping feature). They must not be part of the bake.
    """
    target_objs = []
    for selected_obj in context.selected_objects:
        target_obj = selected_obj.get(custom_prop, None)
        if target_obj and target_obj.type == "MESH":
            if target_obj not in target_objs:
                target_objs.append(target_obj)
            else:
                return (False, "Remapping multiple source objects to the same target is unsupported: " + selected_obj.name + " retargeted to " + target_obj.name + " which is already targeted", None, None, None)

    for target_obj in target_objs:
        target_obj.select_set(False)

    if not context.selected_objects:
        return (False, "No object selected once target object were filtered out", None, None, None)

    """
    2b. deselect objects not having an armature modifier, or not pointing to a shared armature
    """
    shared_armature = None
    for selected_obj in context.selected_objects:
        armature_modifier = None
        for modifier in selected_obj.modifiers:
            if modifier.type == "ARMATURE":
                armature_modifier = modifier
                break

        if armature_modifier:
            if shared_armature:
                if armature_modifier.object != shared_armature:
                    selected_obj.select_set(False)
            else:
                shared_armature = armature_modifier.object
        else:
            selected_obj.select_set(False)

    if not context.selected_objects:
        return (False, "No object selected once objects that do not have an armature modifier or share the same armature were filtered out", None, None, None)
    
    """
    2c. check that the armature has deform bones
    """
    deform_bone_names = [bone.name for bone in shared_armature.data.bones if bone.use_deform]
    if not deform_bone_names:
        return (False, "Armature has no deform bones", None, None, None)

    """
    2d. deselect objects not having at least one vertex group pointing to a bone in the shared armature. This is a weak check and could be skipped.
    """
    for selected_obj in context.selected_objects:
        weighted = False
        for vertex_group in selected_obj.vertex_groups:
            if vertex_group.name in deform_bone_names:
                weighted = True
                break

        if not weighted:
            selected_obj.select_set(False)

    if not context.selected_objects:
        return (False, "No object selected once objects that do not have at least one weight group pointing to the shared armature were filtered out", None, None, None)

    """
    2e. this used to be a requirement for mapping source to target vertices, but no more thanks to barycentric coords computation no longer limited to
    triangles. This may still be relevant in case barycentric coords don't behave as expected on n-gons or weird geometries. This check ensures SOURCE
    & TARGET objects have a triangulate modifier at the top of their modifier stacks. This is of course only relevant for objects being retargeted!
    We might also allow a 'weak check', meaning allow SOURCE & TARGET objects *not* having a triangulate modifier as long as they all contain triangles
    to begin with. I consider this a 'weak check' because this doesn't account for modifiers and some modifiers might generate non-triangulate faces so
     checking the source mesh isn't bullet proof.
    """
    if settings.require_triangulation:
        do_weak_check = True # may be disabled

        for selected_obj in context.selected_objects:
            target_obj = selected_obj.get(custom_prop, None)
            if target_obj and target_obj.type == "MESH":
                selected_obj_meet_triangulated_cond = False
                if do_weak_check:
                    selected_obj_meet_triangulated_cond = True # assume true unless proven otherwise
                    for faces in selected_obj.data.polygons:
                        if len(faces.vertices) != 3:
                            selected_obj_meet_triangulated_cond = False
                            break

                if not selected_obj_meet_triangulated_cond:
                    if selected_obj.modifiers:
                        for selected_object_mod_index, selected_object_mod in enumerate(selected_obj.modifiers):
                            if selected_object_mod.type == "TRIANGULATE":
                                if selected_object_mod_index == 0:
                                    selected_obj_meet_triangulated_cond = True
                                    break
                                else:
                                    return (False, "Object " + selected_obj.name + " has a triangulate modifier but it isn't at the top of the modifier stack, which may lead to uncorrect retargeting with the mesh " + target_obj.name, None, None, None)
                    
                    if not selected_obj_meet_triangulated_cond:
                        return (False, "Object " + selected_obj.name + " has no triangulate modifier. Please add one at the top of its modifier stack to ensure correct retargeting with the mesh " + target_obj.name, None, None, None)

                target_obj_meet_triangulated_cond = False
                if do_weak_check:
                    target_obj_meet_triangulated_cond = True # assume true unless proven otherwise
                    for Faces in target_obj.data.polygons:
                        if len(Faces.vertices) != 3:
                            target_obj_meet_triangulated_cond = False
                            break

                if not target_obj_meet_triangulated_cond:
                    if target_obj.modifiers:
                        for target_obj_mod_index, target_obj_mod in enumerate(target_obj.modifiers):
                            if target_obj_mod.type == "TRIANGULATE":
                                if target_obj_mod_index == 0:
                                    target_obj_meet_triangulated_cond = True
                                    break
                                else:
                                    return (False, "Object " + selected_obj.name + " has a target mesh " + target_obj.name + " that has a triangulate modifier that isn't at the top of the modifier stack. This may lead to uncorrect retargeting", None, None, None)

                    if not target_obj_meet_triangulated_cond:
                        return (False, "Object " + selected_obj.name + " has a target mesh " + target_obj.name + " that has no triangulate modifier. Please add one at the top of its modifier stack to ensure correct retargeting", None, None, None)

    """
    2f. cache selection
    """
    objs_to_bake = context.selected_objects

    """
    3a. we'll need to create a UVMap to assign a texel per vertex so we need to ensure objects can be safely merged without creating UVMap conflicts.
    This involves gathering uvmaps of all selected objects to build a list of maps as if objects were joined and checking if the amount of uvmaps
    exceed the maximum amount in case we need to create one.
    """
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.BAT"
    uvmaps = []

    for selected_obj in objs_to_bake:
        target_obj = selected_obj.get(custom_prop, None)
        uv_object = target_obj if target_obj and target_obj.type == "MESH" else selected_obj

        if mesh_uvmap_name not in [uvlayer.name for uvlayer in uv_object.data.uv_layers]: # can't find target UVMap?
            if len(uv_object.data.uv_layers) >= 8: # ensure UVMap can be created
                return (False, uv_object.name + " has the maximum amount of uvmaps already", None, None, None)

        for uvlayer in uv_object.data.uv_layers: # gather uvmaps as if objects were joined
            if uvlayer.name not in uvmaps:
                uvmaps.append(uvlayer.name)

    if mesh_uvmap_name not in uvmaps: # can't find target UVMap?
        if len(uvmaps) >= 8: # ensure UVMap can be created
            return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None, None)

    """
    4. deselect everything
    """
    for obj_to_bake in objs_to_bake: # deselect objects for now
        obj_to_bake.select_set(False)

    active_obj = context.view_layer.objects.active # cache active object

    context.view_layer.objects.active = None # blank canvas

    return (True, "", objs_to_bake, active_obj, shared_armature)

def get_nla_strips_raw_frame_buffer(context: bpy.types.Context, nla_strips: list) -> list:
    """
    Compute a raw frame buffer from a list of NLA strips

    :param context: Blender current execution context
    :param nla_strips: list of NLA strips contributing to the overall animation 'range'
    :return: list of frames to bake
    :rtype: list
    """
    settings = context.scene.BATBakerSettings

    frames_to_bake = []
    frames_to_bake_indices = []
    frame_step = settings.frame_range_custom_step if settings.frame_range_custom_step_mode == "NLACLIP" and settings.frame_range_custom_step > 1 else 1

    # for each nla_strip, get its [start:end] range
    for nla_strip in nla_strips:
        frame_start = int(nla_strip.frame_start)
        frame_end = int(nla_strip.frame_end)

        # for each frame in [start:end] range
        for frame in range(frame_start, frame_end + 1, frame_step):
            # if frame is already in buffer, append nla strip to it
            if frame in frames_to_bake_indices:
                frame_index = frames_to_bake_indices.index(frame)
                frames_to_bake[frame_index][1].append(nla_strip)
            # else append frame to buffer with nla strip appended to it
            else:
                frames_to_bake_indices.append(frame)
                frames_to_bake.append((frame, [nla_strip]))

    # sort frame buffer by frame index
    frames_to_bake.sort(key=lambda x: x[0])

    # apply stepping in entire frame buffer rather than per NLA strip if desired
    if settings.frame_range_custom_step_mode == "GLOBAL" and settings.frame_range_custom_step > 1:
        frames_to_bake = frames_to_bake[::settings.frame_range_custom_step]

    return frames_to_bake

def get_nla_strip_start_end_indices(nla_strip: object, frames_to_bake: list) -> tuple[int, int]:
    """
    Find where the NLA strip starts & ends in the given frame buffer. This iterates the whole frame buffer and
    isn't efficient, but it's the best I could come up with considering the many constraints I'm working with:
    stepping, deduplicating, ordering, padding, etc.

    :param nla_strip: NLA strip to search start & end frames for
    :param frames_to_bake: frame buffer
    :return: the frame buffer indices for the NLA strip start & end frames
    :rtype: tuple
    """
    start = int(nla_strip.frame_start)
    end = int(nla_strip.frame_end)

    start_index = None
    end_index = None

    for frame_index, frame_data in enumerate(frames_to_bake):
        frame, frame_nla_clips = frame_data

        # skip frame that isn't shared by any NLA strips, it means it's padded and must
        # not participate in the search for the actual NLA strip start/end frames.
        if len(frame_nla_clips) <= 0:
            continue

        # start frame?
        if start_index is None:
            if frame == start:
                start_index = frame_index
            elif frame > start: # went too far
                start_index = min(len(frames_to_bake) - 1, max(0, frame_index - 1))
                while len(frames_to_bake[start_index][1]) <= 0: # rewind to find first non-padded frame
                    start_index -= 1
                    if start_index < 0:
                        start_index = 0
                        break

        # end frame?
        if end_index is None:
            if frame == end:
                end_index = frame_index
            elif frame > end: # went too far
                end_index = min(len(frames_to_bake) - 1, max(start_index, frame_index - 1))
                while len(frames_to_bake[end_index][1]) <= 0: # rewind to find first non-padded frame
                    end_index -= 1
                    if end_index < 0:
                        end_index = 0
                        break

    # fallback to first index
    if start_index is None:
        start_index = 0
    # fallback to last index
    if end_index is None:
        end_index = len(frames_to_bake) - 1

    return (start_index, end_index)

def get_nla_strip_suffix_padding_info(frames_to_bake: list, start_index: int, end_index: int) -> tuple[int, int]:
    """
    Determine the frame immediately following the end of the NLA strip.
    If no other NLA strips occupy that frame, it's likely padding.
    In that case, the current end frame probably doesn't need additional padding.

    However, the *next* frame might be part of prefix padding from another strip.
    If so, suffix padding could still be required.

    To detect this, compare the NLA strip's end frame with the next frame.
    If the next frame is numerically smaller than the end frame, it's likely
    the start frame of the current strip—indicating it's part of suffix padding
    and it shouldn't be applied a second time.

    :param frames_to_bake: frame buffer
    :param start_index: frame buffer index of the start frame for the NLA strip
    :param end_index: frame buffer index of the end frame for the NLA strip
    :return: the index where to insert padding, and the frame to insert
    :rtype: tuple
    """
    try:
        next_frame, next_frame_nla_clips = frames_to_bake[end_index + 1]
        if len(next_frame_nla_clips) <= 0:
            frame, frame_nla_clips = frames_to_bake[end_index]
            if next_frame < frame:
                return None
    except:
        pass

    padding_value = frames_to_bake[start_index][0]
    return (end_index + 1, padding_value) # return index + 1 for array insertion *after* end frame

def get_nla_strip_prefix_padding_info(frames_to_bake: list, start_index: int, end_index: int) -> tuple[int, int]:
    """
    Determine the frame immediately preceding the start of the NLA strip.
    If no other NLA strips occupy that frame, it's likely padding.
    In that case, the current start frame probably doesn't need additional padding.

    However, the *previous* frame might be part of suffix padding from another strip.
    If so, prefix padding could still be required.

    To detect this, compare the NLA strip's start frame with the previous frame.
    If the previous frame is numerically greater than the start frame, it's likely
    the end frame of the current strip—indicating it's part of prefix padding
    and it shouldn't be applied a second time.

    :param frames_to_bake: frame buffer
    :param start_index: frame buffer index of the start frame for the NLA strip
    :param end_index: frame buffer index of the end frame for the NLA strip
    :return: the index where to insert padding, and the frame to insert
    :rtype: tuple
    """
    try:
        previous_frame, previous_frame_nla_clips = frames_to_bake[start_index - 1]
        if len(previous_frame_nla_clips) <= 0:
            frame, frame_nla_clips = frames_to_bake[start_index]
            if previous_frame > frame:
                return None
    except:
        pass

    padding_value = frames_to_bake[end_index][0]
    return (start_index, padding_value) # return index as-is for array insertion *before* start frame

def get_bake_frames(context: bpy.types.Context, objs_to_bake: list, armature: bpy.types.Armature) -> tuple[bool, str, tuple[list, int, int, int]]:
    """
    Return the list of frames to bake and the start/end frames.

    The animation 'range' may be computed in several ways:
    1. from the NLA track(s)
    2. from the scene settings
    3. user-specified

    For 1. frame buffer is generated from NLA tracks, which brings many complications because selection may have many
    different NLA tracks with many different, potentially overlapping, NLA strips:
        - frames have to be deduplicated
        - frames have to be sorted
        - frame stepping may need to be applied, either globally or per NLA strip, messing up with the NLA strip start/end frames to report
        - frame padding may need to be applied, per NLA strip, further messing up with the NLA strip start/end frames to report

    I chose a slow, bruteforce approach to solve this. The frame buffer is first build as a list of frames, each frame paired with a list
    of all NLA strips that contain it. This facilitates applying padding and finding the proper start/end frames for each strip.

    For 2. and 3. frame buffer is generated from a known range, facilitating the process. We still want to search for NLA tracks and NLA
    strips included in that range, for report, as it could be very useful information to have.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :param armature: target armature
    :return: the function's success, potential error message, list of frames in order, bake start & end frames
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings

    add_bake_report("frame_rate", (context.scene.render.fps / context.scene.render.fps_base))

    nla_strips_exclusion = [nla_strip_excluded.name for nla_strip_excluded in settings.frame_range_nla_exclusion]
    nla_strips = []
    if armature and armature.animation_data and armature.animation_data.nla_tracks:
        for nla_track in armature.animation_data.nla_tracks:
            for nla_strip in nla_track.strips:
                if nla_strip not in nla_strips and nla_strip.name not in nla_strips_exclusion: # exclude duplicates & user-specified black-listed strips
                    nla_strips.append(nla_strip)

    if settings.frame_range_mode == "NLA":
        if nla_strips:
            """
            1. frame buffer
            """
            frames_to_bake = get_nla_strips_raw_frame_buffer(context, nla_strips)

            add_bake_report("frame_step", settings.frame_range_custom_step)
            add_bake_report("frame_step_mode", settings.frame_range_custom_step_mode)

            num_frames = len(frames_to_bake)
            add_bake_report("num_frames", num_frames)

            if num_frames < 2:
                return (False, str(num_frames) + " frames detected: too few frames to bake", (None, 0, 0, 0))

            """
            2. padding
            """
            padding_apply = (settings.frame_range_mode == "NLA") and (settings.frame_padding > 0) #and (settings.animation_tex_packing_mode == "STACK")
            padding_prefix = padding_apply and settings.frame_padding_mode == 'PREFIX' or settings.frame_padding_mode == 'PREFIX_SUFFIX'
            padding_suffix = padding_apply and settings.frame_padding_mode == 'SUFFIX' or settings.frame_padding_mode == 'PREFIX_SUFFIX'

            add_bake_report("padded", padding_apply)
            add_bake_report("padding", settings.frame_padding)
            add_bake_report("padding_mode", settings.frame_padding_mode)

            for nla_strip in nla_strips:
                start_index, end_index = get_nla_strip_start_end_indices(nla_strip, frames_to_bake)

                if padding_suffix:
                    padding = get_nla_strip_suffix_padding_info(frames_to_bake, start_index, end_index)
                    if padding:
                        padding_index, padding_value = padding
                        for pad in range(settings.frame_padding):
                            frames_to_bake.insert(padding_index, (padding_value, []))

                if padding_prefix:
                    padding = get_nla_strip_prefix_padding_info(frames_to_bake, start_index, end_index)
                    if padding:
                        padding_index, padding_value = padding
                        for pad in range(settings.frame_padding):
                            frames_to_bake.insert(padding_index, (padding_value, []))

            num_frames = len(frames_to_bake)
            add_bake_report("num_frames_padded", num_frames)

            """
            3. report NLA strip start/end frames/time
            """
            ref_pad_offset = 1 if settings.frame_ref_padding else 0
            for nla_strip in nla_strips:
                start_index, end_index = get_nla_strip_start_end_indices(nla_strip, frames_to_bake)

                # 0-based indices are converted to the actual 1-based frame count
                start_frame = start_index + 1 + ref_pad_offset
                end_frame = end_index + 1 + ref_pad_offset
                add_bake_report_anim(nla_strip.name, start_frame, end_frame)

            """
            4. convert frame buffer to int buffer
            """
            # get rid of NLA_strips data from frame buffer and just keep frame int
            frames_to_bake = [frame_data[0] for frame_data in frames_to_bake]

            start_frame = min(frames_to_bake)
            add_bake_report("start_frame", start_frame)

            end_frame = max(frames_to_bake)
            add_bake_report("end_frame", end_frame)

            """
            5. add reference frame
            """
            ref_frame = start_frame
            if settings.frame_ref_mode == "END":
                ref_frame = end_frame
            elif settings.frame_ref_mode == "CUSTOM":
                ref_frame = settings.frame_ref_custom

            add_bake_report("frame_ref_mode", settings.frame_ref_mode)
            add_bake_report("frame_ref", ref_frame)

            if settings.frame_ref_padding:
                frames_to_bake.insert(0, end_frame) # insert last frame before first frame
            frames_to_bake.insert(0, ref_frame) # insert ref frame
            if settings.frame_ref_padding:
                frames_to_bake.append(start_frame) # insert first frame after last frame

            return (True, "", (frames_to_bake, start_frame, end_frame, ref_frame))
        else:
            return (False, "No NLA tracks or strips found", (None, 0, 0, 0))
    else: # CUSTOM or SCENE
        if (settings.frame_range_mode == "CUSTOM"):
            frame_start = settings.frame_range_custom_start
            frame_end = settings.frame_range_custom_end
            frame_step = settings.frame_range_custom_step
        else: # settings.frame_range_mode == "SCENE":
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
            frame_step = context.scene.frame_step

        add_bake_report("frame_step", frame_step)
        add_bake_report("frame_step_mode", "GLOBAL")

        frames_to_bake = []
        frames_to_bake_indices = list(range(frame_start, frame_end + 1, frame_step))

        num_frames = len(frames_to_bake_indices)
        add_bake_report("num_frames", num_frames)
        add_bake_report("num_frames_padded", num_frames + (2 if settings.frame_ref_padding else 0))

        if num_frames < 2:
            return (False, str(num_frames) + " frames detected: too few frames to bake", (None, 0, 0, 0))

        add_bake_report("padded", False)
        add_bake_report("padding", 0)
        add_bake_report("padding_mode", "SUFFIX")

        # if frame range isn't derived from NLA track(s)...
        frame_nla_strips = []
        for frame in frames_to_bake_indices:
            # ... we still want to scan NLA_strips to see if any are in the user-specified frame range because
            # this can be quite useful information to report/output. Any strip that lies in the frame range can
            # be reported right away because the frame_range_mode don't allow for padding to be added.
            if nla_strips:
                for nla_strip in nla_strips:
                    start = int(nla_strip.frame_start)
                    end = int(nla_strip.frame_end)

                    # NLA strip start or end frame included in range?
                    if start <= frame_end or end >= frame_start:
                        if nla_strip not in frame_nla_strips:
                            frame_nla_strips.append(nla_strip)

                            # clamp start/end frames
                            start_frame = min(frame_end, max(frame_start, start))
                            end_frame = min(frame_end, max(frame_start, end))

                            # start/end frames are actually the frame indices!
                            start_index = start_frame
                            while True:
                                try:
                                    start_index = frames_to_bake_indices.index(start_frame)
                                    break
                                except:
                                    start_frame -= 1
                            start_frame = start_index + 2 # extra offset for reference frame & 0-based index

                            end_index = end_frame
                            while True:
                                try:
                                    end_index = frames_to_bake_indices.index(end_frame)
                                    break
                                except:
                                    end_frame -= 1
                            end_frame = end_index + 2 # extra offset for reference frame & 0-based index

                            add_bake_report_anim(nla_strip.name, start_frame, end_frame)

            frames_to_bake.append((frame, frame_nla_strips))

        # get rid of NLA_strips data from frame buffer and just keep frame int
        frames_to_bake = [frame_data[0] for frame_data in frames_to_bake]

        start_frame = min(frames_to_bake)
        add_bake_report("start_frame", start_frame)

        end_frame = max(frames_to_bake)
        add_bake_report("end_frame", end_frame)

        """
        5. add reference frame
        """
        ref_frame = start_frame
        if settings.frame_ref_mode == "END":
            ref_frame = end_frame
        elif settings.frame_ref_mode == "CUSTOM":
            ref_frame = settings.frame_ref_custom

        add_bake_report("frame_ref_mode", settings.frame_ref_mode)
        add_bake_report("frame_ref", ref_frame)

        if settings.frame_ref_padding:
            frames_to_bake.insert(0, end_frame) # insert last frame before first frame
        frames_to_bake.insert(0, ref_frame) # insert ref frame
        if settings.frame_ref_padding:
            frames_to_bake.append(start_frame) # insert first frame after last frame

        return (True, "", (frames_to_bake, start_frame, end_frame, ref_frame))

def get_bake_vertices(context: bpy.types.Context, objs_to_bake: list) -> int:
    """
    Return the amount of vertices to bake in total, for one frame. This depends on the amount of selected object and their modifier(s)

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: number of vertices
    :rtype: int
    """

    settings = context.scene.BATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    dgraph = context.evaluated_depsgraph_get()

    """
    Gather vertex count for objects to bake. This has to account for modifiers and multiple selection and potential retargeted objects.
    Else, if we're working from a mesh sequence, we only care about the first object in the sequence.
    """
    num_vertices = 0
    for selected_obj in objs_to_bake:
        target_obj = selected_obj.get(custom_prop, None)
        obj = target_obj if target_obj and target_obj.type == "MESH" else selected_obj

        eval_obj = obj.evaluated_get(dgraph)
        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        num_vertices += len(eval_mesh.vertices)
        eval_obj.to_mesh_clear()

    return num_vertices

def get_bake_name(context: bpy.types.Context, active_object: bpy.types.Object) -> str:
    """
    Return the name to give to the bake operation.

    :param context: Blender current execution context
    :param active_object: object to derive name from
    :return: the bake operation's 'name'
    :rtype: string
    """

    settings = context.scene.BATBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.BAT"
    tags = { "BakeName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    #bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

    settings = context.scene.BATBakerSettings
    new_bake_report(context)

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #
    
    bake_start_time = time.time()

    success, msg, skinning_textures, max_bones = get_bake_skinning_textures(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(1)

    success, msg, animation_textures = get_bake_animation_textures(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(2)

    success, msg, objs_to_bake, active_object, armature = get_bake_selection(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(3)

    success, msg, bake_frames_info = get_bake_frames(context, objs_to_bake, armature)
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(4)

    num_frames = len(frames_to_bake)
    num_objs = len(objs_to_bake)
    num_verts = get_bake_vertices(context, objs_to_bake)
    add_bake_report("num_verts", num_verts)

    success, msg, skinning_tex_width, skinning_tex_height, skinning_no_uv = get_best_skinning_texture_resolution(context, num_verts)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(6)

    success, msg, bones, skinning_data, bounds_info = get_skinning_data(context, objs_to_bake, armature, bake_frames_info, max_bones)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    num_bones = len(bones)
    add_bake_report("num_bones", num_bones)

    wm.progress_update(8)

    success, msg, animation_tex_width, animation_tex_height, bake_frame_height, bake_frame_width = get_best_animation_texture_resolution(context, num_frames, num_bones)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    bake_name = get_bake_name(context, active_object)
    add_bake_report("name", bake_name)

    wm.progress_update(9)

    success, msg, animation_data = get_animation_data(context, armature, bones, bake_frames_info)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(10)

    #####################
    # SKINNING TEXTURES #

    bake_progress = 10
    bake_progress_step = (1.0 / (len(skinning_textures) * 4 * 3)) * 40
    for skinning_texture in skinning_textures:
        if skinning_texture.storage_mode == "VCOL":
            continue

        success, msg, buffer = get_skinning_texture_buffer(context, skinning_texture, skinning_data, skinning_tex_width, skinning_tex_height, num_verts, False)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.unit_invert_v:
            buffer = get_inverted_buffer(buffer, skinning_tex_width, skinning_tex_height)

        success, msg, tex = generate_texture(skinning_texture.name, bake_name, settings.export_tex_file_name, buffer, skinning_tex_width, skinning_tex_height)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        report_texture = add_bake_skinning_texture_report(skinning_texture, tex)

        tex_path = ""
        if settings.export_tex and bpy.data.is_saved:
            success, msg, tex_path = export_texture(context, tex, settings.export_tex_file_path, settings.export_tex_file_name, skinning_texture.name, bake_name, settings.export_tex_override)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            edit_bake_skinning_texture_report_path(report_texture, tex_path)
            edit_bake_skinning_texture_report_exported(report_texture, True)

    ######################
    # ANIMATION TEXTURES #

    bake_progress = 50
    bake_progress_step = (1.0 / (len(skinning_textures) * 4 * 3)) * 40
    for animation_texture in animation_textures:
        buffer, buffer_ranges_offsets, buffer_ranges, buffer_ranges_valid = get_animation_texture_buffer(context, animation_texture, armature, animation_data, animation_tex_width, animation_tex_height, bake_frame_height, bake_frames_info, num_bones, bones)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.unit_invert_v:
            buffer = get_inverted_buffer(buffer, animation_tex_width, animation_tex_height)

        success, msg, tex = generate_texture(animation_texture.name, bake_name, settings.export_tex_file_name, buffer, animation_tex_width, animation_tex_height)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        report_texture = add_bake_animation_texture_report(animation_texture, tex, buffer_ranges_offsets, buffer_ranges, buffer_ranges_valid)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.export_tex and bpy.data.is_saved:
            success, msg, tex_path = export_texture(context, tex, settings.export_tex_file_path, settings.export_tex_file_name, animation_texture.name, bake_name, settings.export_tex_override)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            edit_bake_animation_texture_report_path(report_texture, tex_path)
            edit_bake_animation_texture_report_exported(report_texture, True)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

    wm.progress_update(92)

    ########
    # MESH #

    success, msg, obj_to_export, bake_uvmap_index = generate_mesh(context, bake_name, objs_to_bake, skinning_tex_width, skinning_tex_height, skinning_no_uv, bake_ref_frame)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)
    add_bake_report("mesh", obj_to_export)
    add_bake_report("mesh_uvmap_index", bake_uvmap_index)

    for skinning_texture in skinning_textures:
        if skinning_texture.storage_mode != "VCOL":
            continue

        success, msg, buffer = get_skinning_texture_buffer(context, skinning_texture, skinning_data, skinning_tex_width, skinning_tex_height, num_verts, True)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        generate_mesh_vcol(context, skinning_texture, obj_to_export, buffer)
        report_texture = add_bake_skinning_texture_report(skinning_texture, tex)
        break # there should only be one texture targeting vertex color

    if settings.export_mesh and bpy.data.is_saved:
        success, msg, mesh_path = export_mesh_selection(context, bake_name)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("mesh_export", True)
        add_bake_report("mesh_path", mesh_path)

    if settings.previz_result:
        #success, msg = generate_mesh_geonodes(context, obj_to_export, num_verts, tex_width, bake_frames_info, bake_frame_height, vertices_bounds, img_offset, image_nor)
        pass
    
    if settings.previz_bounds:
        success, msg = display_bounds(context, bake_name + ".bounds", bounds_info)

    wm.progress_update(96)

    #######
    # XML #

    if settings.export_xml and bpy.data.is_saved:
        success, msg, path = export_xml(context)
        add_bake_report("xml", True)
        add_bake_report("xml_path", path)

    wm.progress_update(98)

    ######
    # UX #
    if obj_to_export:
        obj_to_export.select_set(True)

    context.scene.frame_start = bake_start_frame
    context.scene.frame_end = bake_end_frame

    add_bake_report("success", True)
    wm.progress_update(99)
    wm.progress_end()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

##############
### MESHES ###
def generate_mesh(context: bpy.types.Context, bake_name: str, objs_to_bake: list, tex_width: int, tex_height: int, no_uv: bool, bake_frame_ref: int) -> tuple[bool, str, bpy.types.Object, int]:
    """
    Generate the mesh object to export

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :param objs_to_bake: List of objects to bake
    :param tex_width: BAT texture(s) width
    :param tex_height: BAT texture(s) height
    :param no_uv: skip generating UVs because skinning is exclusively baked into vcol
    :param bake_frame_ref: Frame considered as the 'reference frame', or 'base pos'
    :return: success, message, generated object, UVMap used to map the BAT texture(s)
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    # go to first frame
    context.scene.frame_set(bake_frame_ref)
    #context.view_layer.update()

    dgraph = context.evaluated_depsgraph_get()

    eval_meshes = []

    """
    build unique list of materials as if objects were merged
    """
    if settings.mesh_materials:
        materials = []
        for obj_to_bake in objs_to_bake:
            for material in obj_to_bake.data.materials:
                if material not in materials:
                    materials.append(material)

    """
    we need to duplicate all selected objects in their base pos and account for their modifier(s)
    as well. We can't join them yet because we need to process their UVs uniquely per mesh.
    """
    eval_meshes = [None] * len(objs_to_bake)
    eval_meshes_vertices = 0
    eval_mesh_uvmap_index = 0

    for obj_index, obj_to_bake in enumerate(objs_to_bake):
        obj_target = obj_to_bake.get(custom_prop, None)
        obj = obj_target if obj_target and obj_target.type == "MESH" else obj_to_bake

        eval_obj = obj.evaluated_get(dgraph)
        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph).copy()
        eval_obj.to_mesh_clear()
        eval_mesh.transform(eval_obj.matrix_world)
        eval_meshes[obj_index] = eval_mesh

        if not no_uv: # weights/indices might be exclusively baked into vcol, resulting in no skinning texture and no uvs required
            success, msg, last_eval_mesh_uvmap_index = generate_mesh_uvs(context, eval_mesh, tex_width, tex_height, eval_meshes_vertices)
            if success:
                if obj_index == 0:
                    eval_mesh_uvmap_index = last_eval_mesh_uvmap_index
                elif eval_mesh_uvmap_index != last_eval_mesh_uvmap_index: # double check UVMap consistency
                    success = False
                    msg = "Divergent UVMap indices"

            if not success:
                for eval_mesh in eval_meshes:
                    if eval_mesh.users == 0:
                        bpy.data.meshes.remove(eval_mesh)

                return (False, msg, None, -1)

        eval_meshes_vertices += len(eval_mesh.vertices) # increment vertex count to offset UVs per object

    """
    evaluate each object vertices' face material index and see if it points to the same index
    in list of materials built pre-processed above. If not, it needs to be updated. Reason may
    be simple:

    Mesh_A has one material named Mat_A, face material index is 0
    Mesh_B has one material named Mat_B, face material index is 1

    Once merged, Mesh_C, containing Mesh_A and Mesh_B, have two materials, yet all face material
    indices are 0, so some must be updated
    """
    if settings.mesh_materials and materials and len(materials) > 0:
        for eval_mesh in eval_meshes:
            for poly in eval_mesh.polygons:
                try:
                    material_source = eval_mesh.materials[poly.material_index]
                        
                    material_index_source = poly.material_index
                    material_index_merged = materials.index(material_source)
                    if material_index_source != material_index_merged:
                        poly.material_index = material_index_merged
                except:
                    poly.material_index = 0

    """
    Create a new mesh and object to 'merge' all duplicated meshes
    """
    name = bake_name if bake_name != "" else "BakedMesh.BAT"
    mesh = bpy.data.meshes.new(name)
    if settings.mesh_materials and materials:
        for material in materials:
            mesh.materials.append(material)

    bm = bmesh.new()
    for eval_mesh in eval_meshes:
        bm.from_mesh(eval_mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # clean duplicated mesh
        bpy.data.meshes.remove(eval_mesh)

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    context.scene.collection.objects.link(obj)

    context.view_layer.objects.active = obj
    obj.select_set(True) # for export

    return (True, "", obj, eval_mesh_uvmap_index)

def generate_mesh_uvs(context: bpy.types.Context, mesh: bpy.types.Mesh, tex_width: int, tex_height: int, vertex_index_offset: int) -> tuple[bool, str, int]:
    """
    Configure the mesh UVs so that one vertex is located on one unique texel in the BAT texture(s)

    :param context: Blender current execution context
    :param mesh: mesh to edit
    :param tex_width: BAT texture(s) width
    :param tex_height: BAT texture(s) height
    :param vertex_index_offset: Used to uniquely process a selection of meshes
    :return: the function's success, potential error message, index of UVMap used to map the BAT texture(s)
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings
    rows = len(settings.skinning_textures[0].rows)
    for skinning_texture in settings.skinning_textures:
        if rows != len(skinning_texture.rows):
            return (False, "Can't generate mesh UVs because skinning textures do not share the same row amount", 0)

    uvmap = None
    uvmap_index = 0
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.BAT"

    # attempt to find existing UVMap
    for uvlayer_index, uvlayer in enumerate(mesh.uv_layers):
        if uvlayer.name == mesh_uvmap_name:
            uvmap = uvlayer
            uvmap_index = uvlayer_index
            break

    # else create one, if possible
    if uvmap is None:
        if len(mesh.uv_layers) >= 8:
            return(False, "Too many existing uvmaps", -1)

        mesh.uv_layers.new()
        uvmap_index = len(mesh.uv_layers) - 1
        uvmap = mesh.uv_layers[uvmap_index]
        uvmap.name = mesh_uvmap_name

    # set UV
    for loop in mesh.loops:
        vertex_index = loop.vertex_index + vertex_index_offset
        u = (0.5 / float(tex_width)) + (vertex_index % tex_width) / float(tex_width)
        v = (0.5 / float(tex_height)) + (vertex_index // float(tex_width) * rows) / float(tex_height)
        if settings.unit_invert_v:
            v = 1.0 - v

        uvmap.data[loop.index].uv = (u,v)

    return (True, "", uvmap_index)

def generate_mesh_vcol(context: bpy.types.Context, texture: object, obj_to_bake: bpy.types.Object, vcol_buffer: list):
    """
    Configure the mesh Vertex Colors to store the provided color buffer

    :param context: Blender current execution context
    :param texture: the 'texture' property group responsible for writing to the vertex color
    :param obj_to_bake: the mesh object to modify
    :param vcol_buffer: the vertex color buffer to get values from
    :return: None
    :rtype: None
    """

    try:
        texture_row = texture.rows[0] # vcol texture has only one 'row'
    except:
        texture_row = None

    if texture_row:
        mesh_to_bake = obj_to_bake.data

        if mesh_to_bake.vertex_colors:
            vcol = mesh_to_bake.vertex_colors.active
        else:
            vcol = mesh_to_bake.vertex_colors.new()
            for loop_id in mesh_to_bake.loops:
                vcol.data[loop_id.index].color = [0.0, 0.0, 0.0, 0.0]

        for poly in mesh_to_bake.polygons:
            for loop_index in poly.loop_indices:
                buffer_index = mesh_to_bake.loops[loop_index].vertex_index * 4 # RGBA

                if texture_row.R.channel_mode != "NONE":
                    vcol.data[loop_index].color[0] = vcol_buffer[buffer_index + 0]
                if texture_row.G.channel_mode != "NONE":
                    vcol.data[loop_index].color[1] = vcol_buffer[buffer_index + 1]
                if texture_row.B.channel_mode != "NONE":
                    vcol.data[loop_index].color[2] = vcol_buffer[buffer_index + 2]
                if texture_row.A.channel_mode != "NONE":
                    vcol.data[loop_index].color[3] = vcol_buffer[buffer_index + 3]

def export_mesh_selection(context: bpy.types.Context, bake_name: str):
    """
    Export the current selection to FBX

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

#################
### GEO NODES ###
def generate_mesh_geonodes(context: bpy.types.Context, obj_to_export: bpy.types.Object, num_vertices: int, tex_width: int, bake_frames_info: tuple[list, int, int, int], bake_frame_height: int, vertices_bounds: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector], img_offset: bpy.types.Image, img_nor: bpy.types.Image) -> tuple[bool, str]:
    """
    Apply a geometry node modifier to the given object. The required geometry node group either already exist from a previous call and is thus assigned to the modifier or is generated to previsualize the baked BAT texture(s)

    :param context: Blender current execution context
    :param obj_to_export: object to edit
    :param num_vertices: number of vertices to bake per frame
    :param tex_width: BAT texture(s) width
    :param bake_frames_info: frames to bake
    :param bake_frame_height: Amount of lines of pixels per frame
    :param img_offset: BAT texture that stores vertex offset data
    :param img_nor: BAT texture that stores vertex normal data
    :return: the function's success, potential error message
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings

    use_row = (num_vertices == tex_width) or (settings.animation_tex_packing_mode == 'STACK')
    if use_row:
        generate_mesh_geonodes_row(context, obj_to_export, bake_frames_info, bake_frame_height, vertices_bounds, img_offset, img_nor)
    else:
        generate_mesh_geonodes_partialrow(context, obj_to_export, bake_frames_info, num_vertices / tex_width, vertices_bounds, img_offset, img_nor)

    return (True, "")

def generate_mesh_geonodes_row(context: bpy.types.Context, obj_to_export: bpy.types.Object, bake_frames_info: tuple[list, int, int, int], bake_frame_height: int, vertices_bounds: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector], img_offset: bpy.types.Image, img_nor: bpy.types.Image):
    """
    Apply a geometry node modifier to the given object. The required geometry node group either already exists from a previous call and is thus assigned to the modifier or is generated to previsualize the baked BAT texture(s) using a simple V offset to playback the animation

    :param context: Blender current execution context
    :param obj_to_export: object to edit
    :param bake_frames_info: frames to bake
    :param bake_frame_height: amount of lines of pixels per frame
    :param vertices_bounds: animation bounds to derive maximum offset
    :param img_offset: BAT texture that stores vertex offset data
    :param img_nor: BAT texture that stores vertex normal data
    :return: None
    :rtype: None
    """

    settings = context.scene.BATBakerSettings

    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset = vertices_bounds
    max_offset = mathutils.Vector((max(abs(min_bounds.x), abs(max_bounds.x)),
                                  max(abs(min_bounds.y), abs(max_bounds.y)),
                                  max(abs(min_bounds.z), abs(max_bounds.z))))

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "BAT_Row":
            geonode_tree = node_group
            break

    if geonode_tree is None:
        geonode_tree = build_mesh_geonodes_row_group()

    geonode_mod = obj_to_export.modifiers.get("GeometryNodes", None)
    if geonode_mod is None:
        geonode_mod = obj_to_export.modifiers.new(name="GeometryNodes", type='NODES')

    geonode_mod.node_group = geonode_tree

def generate_mesh_geonodes_partialrow(context: bpy.types.Context, obj_to_export: bpy.types.Object, bake_frames_info: tuple[list, int, int, int], frame_step: float, vertices_bounds: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector], img_offset: bpy.types.Image, img_nor: bpy.types.Image):
    """
    Apply a geometry node modifier to the given object. The required geometry node group either already exist from a previous call and is thus assigned to the modifier or is generated to previsualize the baked BAT texture(s) using a complex U & V offset to playback the animation

    :param context: Blender current execution context
    :param obj_to_export: object to edit
    :param bake_frames_info: frames to bake
    :param frame_step: amount of V axis to offset per frame
    :param img_offset: BAT texture that stores vertex offset data
    :param img_nor: BAT texture that stores vertex normal data
    :return: None
    :rtype: None
    """

    settings = context.scene.BATBakerSettings

    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset= vertices_bounds
    max_offset = mathutils.Vector((max(abs(min_bounds.x), abs(max_bounds.x)),
                                  max(abs(min_bounds.y), abs(max_bounds.y)),
                                  max(abs(min_bounds.z), abs(max_bounds.z))))

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "BAT_PartialRow":
            geonode_tree = node_group
            geonode_tree.is_modifier = True
            break

    if geonode_tree is None:
        geonode_tree = build_mesh_geonodes_partialrow_group()

    geonode_mod = obj_to_export.modifiers.get("GeometryNodes", None)
    if geonode_mod is None:
        geonode_mod = obj_to_export.modifiers.new(name="GeometryNodes", type='NODES')

    geonode_mod.node_group = geonode_tree

def build_mesh_geonodes_row_group():
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    pass

def build_mesh_geonodes_partialrow_group():
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    pass

###############
### BUFFERS ###
def get_skinning_data(context: bpy.types.Context, objs_to_bake: list, armature: bpy.types.Armature, bake_frames_info: tuple[list, int, int, int], max_bones: int) -> tuple[bool, str, list, list, tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector]]:
    """
    Compile and return the list of [vertex_index, [bone_index, bone_weight]], per object. To account for multiple mesh selection, the vertex_index is offset by the number of vertices each mesh has, in increment. Each vertex may list up to 'max_bones' number of bone data.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :param armature: deforming armature
    :param bake_frames_info: list of frames to bake
    :param max_bones: maximum amount of bones allowed to influence a vertex
    :return: the function's success, potential error message, list of bones, list of vertex skinning data, bounds
    :rtype: tuple
    """
    settings = context.scene.BATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    """
    Go to frame of reference to evaluate objects to bake and gather bone & skinning data as well as overall min/max bounds in ref pose
    """

    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info

    context.scene.frame_set(bake_ref_frame)
    dgraph = context.evaluated_depsgraph_get()

    bones = []
    skinning_data = []
    vertex_index_offset = 0

    ref_min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    ref_max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    for obj_to_bake in objs_to_bake:
        # account for modifiers that may change weightgroups & vertex count/order
        ref_eval_obj = obj_to_bake.evaluated_get(dgraph)
        ref_eval_mesh = ref_eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        # eval_mesh.transform(eval_obj.matrix_world) # unecessary, we're just fetching vertex groups
        mesh_skinning_data = []
        target_obj = obj_to_bake.get(custom_prop, None)
        if target_obj and target_obj.type == "MESH":
            """
            The retargeting function transfers the skeletal animation from a high-resolution mesh to a low-resolution mesh. The process involves the following steps:

            Building a BVH Tree:
                A Bounding Volume Hierarchy (BVH) tree is constructed for the high-resolution mesh.
                Each vertex of the low-resolution mesh uses this tree to locate the nearest point on the surface of the high-res mesh.

            Barycentric Mapping:
                Once the nearest point is identified, its corresponding face index on the high-res mesh is retrieved.
                Barycentric coordinates are computed for the point, indicating how the vertex of the low-res mesh relates to the vertices of the high-res face (typically a quad or triangle).

            Skinning Data Transfer:
                The skinning data (bone indices and weights) from the contributing vertices of the high-res mesh are collected.
                Each bone weight is scaled by the corresponding barycentric weight to reflect its influence on the low-res vertex.

            Weight Merging and Optimization:
                Duplicate bones (those influencing multiple contributing vertices) are merged, and their weights summed.
                The combined bone weights are sorted in descending order.
                To limit complexity, only the top N bones are kept, where N is defined by the max_weights parameter.
                The remaining weights are normalized to ensure they sum to 1, forming the final skinning data for the low-res vertex.
            """
            # TARGET is the low poly mesh
            # SOURCE is the high poly mesh

            # evaluate TARGET to account for modifiers that may change weightgroups & vertex count/order
            target_eval_obj = target_obj.evaluated_get(dgraph)

            # get mesh from evaluated TARGET object. Memory has to be cleared
            target_eval_mesh = target_eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            # target_eval_mesh.transform(target_eval_obj.matrix_world) # unecessary, we're just fetching vertex groups

            # create BVH tree for SOURCE object
            BVH = BVHTree.FromObject(ref_eval_obj, dgraph)

            # for each vertex in TARGET mesh
            for vertex_index, vertex in enumerate(target_eval_mesh.vertices):
                # closest position on SOURCE mesh from TARGET vert & compute barycentric weights
                closest_face_pos, closest_face_nor, closest_face_index, closest_face_dist = BVH.find_nearest(vertex.co)
                closest_face_vertices_pos = [ref_eval_mesh.vertices[v].co for v in ref_eval_mesh.polygons[closest_face_index].vertices]
                closest_face_barycoords = mathutils.interpolate.poly_3d_calc(closest_face_vertices_pos, closest_face_pos)

                vertex_groups = []
                # for each SOURCE vertex the *closest face* has
                for closest_face_barycentric_index, closest_vertex_index in enumerate(ref_eval_mesh.polygons[closest_face_index].vertices):
                    # append vertex groups
                    vertex_groups.extend(ref_eval_mesh.vertices[closest_vertex_index].groups)

                # for each vertex groups of all closest vertices on SOURCE mesh
                unique_vertex_groups = []
                vertex_groups_to_skip = []
                for vertex_group in vertex_groups:
                    # list of vertex groups might contain duplicates because vertices on the *closest* face are likely to have similar weights
                    # the weights of these duplicates are accounted for, and thus the duplicated vertex group itself has to be skipped
                    if vertex_group in vertex_groups_to_skip:
                        continue

                    vertex_group_index = vertex_group.group
                    vertex_group_name = ref_eval_obj.vertex_groups[vertex_group_index].name

                    # ensure weight group is named after a deforming bone in armature
                    if vertex_group_name in armature.data.bones:
                        bone = armature.data.bones[vertex_group_name]
                        if not bone.use_deform:
                            continue

                        # get/assign bone index
                        if bone.name not in bones:
                            bones.append(bone.name)
                            bone_index = len(bones) - 1
                        else:
                            bone_index = bones.index(bone.name)

                        # 'merge' vertex groups having the same target - this means averaging their weights
                        bone_weight = 0
                        bone_weight_sum = 0
                        for v in vertex_groups:
                            if ref_eval_obj.vertex_groups[v.group].name == vertex_group_name:
                                vertex_groups_to_skip.append(v)
                                bone_weight += vertex_group.weight
                                bone_weight_sum += 1

                        if bone_weight_sum > 1:
                            bone_weight /= bone_weight_sum
                        unique_vertex_groups.append((bone, bone_index, bone_weight))

                # sort vertex groups by weight, most contributing bone to least
                unique_vertex_groups = sorted(unique_vertex_groups, key=lambda x: x[2], reverse=True)

                # discard least participating vertex groups
                unique_vertex_groups = unique_vertex_groups[0:max_bones]

                # sum of remaining weights must equal 1.0
                normalization_sum = sum([unique_vertex_group[2] for unique_vertex_group in unique_vertex_groups])
                if normalization_sum > 0.0:
                    normalization_factor = 1.0 / normalization_sum
                else:
                    normalization_factor = 1.0

                bone_indices_weights = []
                for unique_vertex_group in unique_vertex_groups:
                    bone, bone_index, bone_weight = unique_vertex_group
                    bone_weight *= normalization_factor

                    bone_indices_weights.append((bone, bone_index, bone_weight))

                mesh_skinning_data.append((vertex.index + vertex_index_offset, bone_indices_weights))

            
            skinning_data.extend(mesh_skinning_data)
            vertex_index_offset += len(target_eval_mesh.vertices)
            target_eval_obj.to_mesh_clear()
        else:
            """
            This step constructs the skinning data buffer, which defines, for each vertex, a list of its most influential bones. For every vertex, the bones are sorted in descending order of influence
            based on their weights. Each entry includes the bone itself, the bone’s index and its corresponding weight. The number of influencing bones can be fine-tuned using a user-defined parameter
            (max_weights). After selecting the top influences, their weights are normalized to ensure they sum to 1. This normalized data allows the skeletal mesh to be reskinned dynamically.
            """
            
            for vertex_index, vertex in enumerate(ref_eval_mesh.vertices):
                # sort vertex groups by weight, most contributing bone to least
                vertex_groups = sorted(vertex.groups, key=lambda x: x.weight, reverse=True)

                # discard least participating vertex groups
                vertex_groups = vertex_groups[0:max_bones]

                # sum of remaining weights must equal 1.0
                normalization_sum = sum([vertex_group.weight for vertex_group in vertex_groups])
                if normalization_sum > 0.0:
                    normalization_factor = 1.0 / normalization_sum
                else:
                    normalization_factor = 1.0

                bone_indices_weights = []
                for vertex_group in vertex_groups:
                    vertex_group_index = vertex_group.group
                    vertex_group_name = ref_eval_obj.vertex_groups[vertex_group_index].name

                    # ensure weight group is named after a deforming bone in armature
                    if vertex_group_name in armature.data.bones:
                        bone = armature.data.bones[vertex_group_name]
                        if not bone.use_deform:
                            continue

                        # get/assign bone index
                        if bone.name not in bones:
                            bones.append(bone.name)
                            bone_index = len(bones) - 1
                        else:
                            bone_index = bones.index(bone.name)

                        bone_weight = vertex_group.weight * normalization_factor # normalize weights

                        # create vertex skinning data
                        bone_indices_weights.append((bone, bone_index, bone_weight))

                mesh_skinning_data.append((vertex.index + vertex_index_offset, bone_indices_weights))

            skinning_data.extend(mesh_skinning_data)
            vertex_index_offset += len(ref_eval_mesh.vertices)

        ref_eval_obj.to_mesh_clear()

        """
        This step calculates the minimum and maximum bounds of the mesh in its reference pose. These bounds serve as a baseline for determining the overall min/max bounds during animation.
        By comparing the animated bounds to the reference pose bounds, an offset can be computed. This offset is later applied to the mesh in its reference pose to ensure that the bounding
        box fully encloses the animated mesh over time. This is crucial for accurate occlusion culling and avoiding visual artifacts during rendering.
        """
        bbox_corners = [(ref_eval_obj.matrix_world @ mathutils.Vector(corner)) * signed_scale for corner in ref_eval_obj.bound_box]
        bbox_corners_x = [corner.x for corner in bbox_corners]
        bbox_corners_y = [corner.y for corner in bbox_corners]
        bbox_corners_z = [corner.z for corner in bbox_corners]

        ref_min_bounds = mathutils.Vector((min(ref_min_bounds.x, min(bbox_corners_x)),
                                           min(ref_min_bounds.y, min(bbox_corners_y)),
                                           min(ref_min_bounds.z, min(bbox_corners_z))))
        ref_max_bounds = mathutils.Vector((max(ref_max_bounds.x, max(bbox_corners_x)),
                                           max(ref_max_bounds.y, max(bbox_corners_y)),
                                           max(ref_max_bounds.z, max(bbox_corners_z))))

    if len(bones) <= 0:
        return (False, "No bones", None, None, None)

    if len(skinning_data) <= 0:
        return (False, "No skinning data", None, None, None)

    """
    Play animation and evaluate objects to bake to compute overall min/max bounds across the entire animation
    """

    min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    for frame_index in range(1, len(frames_to_bake)): # skip ref frame
        frame = frames_to_bake[frame_index]

        context.scene.frame_set(frame)
        dgraph = context.evaluated_depsgraph_get()
        for obj_to_bake in objs_to_bake:
            # evaluate modifiers etc. to calculate bounds
            eval_obj = obj_to_bake.evaluated_get(dgraph)

            """
            This step calculates the minimum and maximum bounds of the mesh in its animated pose. These bounds can be then compared to the bounds of the mesh in reference pose to compute
            an offset to apply to the exported mesh's bounding box. This is important for accurate occlusion culling.
            """
            bbox_corners = [(eval_obj.matrix_world @ mathutils.Vector(corner)) * signed_scale for corner in eval_obj.bound_box]
            bbox_corners_x = [corner.x for corner in bbox_corners]
            bbox_corners_y = [corner.y for corner in bbox_corners]
            bbox_corners_z = [corner.z for corner in bbox_corners]

            min_bounds = mathutils.Vector((min(min_bounds.x, min(bbox_corners_x)),
                                           min(min_bounds.y, min(bbox_corners_y)),
                                           min(min_bounds.z, min(bbox_corners_z))))
            max_bounds = mathutils.Vector((max(max_bounds.x, max(bbox_corners_x)),
                                           max(max_bounds.y, max(bbox_corners_y)),
                                           max(max_bounds.z, max(bbox_corners_z))))

    min_bounds_offset = (min_bounds - ref_min_bounds)
    min_bounds_offset.x = min(0, min_bounds_offset.x)
    min_bounds_offset.y = min(0, min_bounds_offset.y)
    min_bounds_offset.z = min(0, min_bounds_offset.z)
    add_bake_report("mesh_min_bounds_offset", min_bounds_offset)
    max_bounds_offset = (max_bounds - ref_max_bounds)
    max_bounds_offset.x = max(0, max_bounds_offset.x)
    max_bounds_offset.y = max(0, max_bounds_offset.y)
    max_bounds_offset.z = max(0, max_bounds_offset.z)
    add_bake_report("mesh_max_bounds_offset", max_bounds_offset)

    # restore ref frame
    context.scene.frame_set(bake_ref_frame)
    dgraph = context.evaluated_depsgraph_get()

    return (True, "", bones, skinning_data, (ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset))

def get_skinning_texture_buffer_function(texture_channel: object) -> callable:
    """
    Return the buffer function associated with the given texture channel's mode: index or weight.

    :param texture_channel: texture channel to get bake function for
    :return: the buffer function to call for the given texture channel
    :rtype: callable function
    """
    if texture_channel.channel_mode == "INDEX":
        return skinning_texture_buffer_index
    elif texture_channel.channel_mode == "WEIGHT":
        return skinning_texture_buffer_weight
    else:
        pass

    return animation_texture_buffer_zeros

def get_skinning_texture_buffer(context: bpy.types.Context, texture: object, skinning_data: list, tex_width: int, tex_height: int, num_vertices: int, vcol: bool) -> list:
    """
    Intermediate buffer function to return the values to store in the texture RGBA channels

    :param context: Blender current execution context
    :param texture_channel: texture channel to generate buffer for
    :param tex_width: BAT's texture width
    :param tex_height: BAT's texture height
    :param vcol: generate buffer for vcol?
    :return: pixel buffer
    :rtype: list
    """
    if vcol:
        buffer = [0.0, 0.0, 0.0, 0.0] * num_vertices # RGBA
    else:
        buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height # RGBA

    for row_index, row in enumerate(texture.rows):

        texture_channels = [
            (row.R if row.R.channel_mode != "NONE" else None),
            (row.G if row.G.channel_mode != "NONE" else None),
            (row.B if row.B.channel_mode != "NONE" else None),
            (row.A if row.A.channel_mode != "NONE" else None),
            ]

        for texture_channel_index, texture_channel in enumerate(texture_channels):
            if texture_channel is None:
                continue

            pre_bake_func = get_skinning_texture_buffer_function(texture_channel)
            skinning_buffer = pre_bake_func(context, skinning_data, texture_channel, num_vertices)
            if skinning_buffer:
                for index in range(len(skinning_buffer)):
                    data_to_bake = skinning_buffer[index]

                    if vcol:
                        if texture_channel.channel_mode == "INDEX":
                            if data_to_bake > 255 or data_to_bake < 0:
                                return (False, "VCol index overflow: " + str(data_to_bake), None)

                            data_to_bake /= 255 # normalize for vcol!
                        else: # WEIGHT
                            if data_to_bake > 1.0 or data_to_bake < 0.0:
                                return (False, "VCol weight overflow: " + str(data_to_bake), None)
                    elif texture_channel.channel_mode == "INDEX" and texture_channel.remapping:
                        data_to_bake /= 255 # normalize for 8-bit textures

                    if vcol:
                        buffer_index = (index * 4)
                    else:    
                        u = index % tex_width
                        v = math.floor(index / tex_width) * len(texture.rows) + row_index
                        buffer_index = (u * 4) + (v * tex_width * 4)

                    try:
                        buffer[buffer_index + texture_channel_index] = data_to_bake
                    except:
                        return (False, "Invalid buffer index: " + str(buffer_index + texture_channel_index) + " vs " + str(len(buffer)), buffer)

    return (True, "", buffer)

def get_animation_data(context: bpy.types.Context, armature: bpy.types.Armature, bones: list, bake_frames_info: tuple[list, int, int]) -> tuple[bool, str, tuple[list, list]]:
    """
    Compile and return the list of bone matrices, per frame. This only accounts for bones that were listed in weight groups. Order is important and each position in the list describes the linear index at which the transform must be stored in the anim texture(s).

    :param context: Blender current execution context
    :param armature: armature to evaluate
    :param bones: bones to search for in the armature
    :param bake_frames_info: list of frames to bake
    :return: the function's success, potential error message, tuple containing list of posed bone matrices, per frame, and list of bone matrices in ref pose
    :rtype: tuple
    """
    settings = context.scene.BATBakerSettings
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info

    """
    create buffer containing posed & ref bone matrices, per frame.
    Ref matrices are duplicated each frame but that's for convenience.
    They *may* be evaluated at a custom frame that isn't in the frames
    to bake.
    """
    frame_bone_matrix_buffer = [None] * len(frames_to_bake)
    for frame_index, frame in enumerate(frames_to_bake):
        context.scene.frame_set(frame)
        dgraph = context.evaluated_depsgraph_get()
        eval_arm = armature.evaluated_get(dgraph)

        matrix_buffer = [None] * len(bones)
        for bone in eval_arm.pose.bones:
            try:
                bone_index = bones.index(bone.name)
            except:
                continue

            matrix_buffer[bone_index] = eval_arm.matrix_world @ bone.matrix

        frame_bone_matrix_buffer[frame_index] = matrix_buffer

    return (True, "", frame_bone_matrix_buffer)

def get_animation_texture_buffer_function(texture_channel: object) -> callable:
    """
    Return the buffer function associated with the given texture channel's mode: position, rotation & scale.

    :param texture_channel: texture channel to get bake function for
    :return: the buffer function to call for the given texture channel
    :rtype: callable function
    """
    if texture_channel.channel_mode == "POSITION":
        return animation_texture_buffer_position
    elif texture_channel.channel_mode == "ROTATION":
        return animation_texture_buffer_rotation
    elif texture_channel.channel_mode == "SCALE":
        return animation_texture_buffer_scale
    elif texture_channel.channel_mode == "AXIS":
        return animation_texture_buffer_axes
    elif texture_channel.channel_mode == "CUSTOM_PROP":
        return animation_texture_buffer_custom_prop
    else:
        pass

    return animation_texture_buffer_zeros

def get_animation_texture_buffer(context: bpy.types.Context, texture: object, armature: bpy.types.Armature, animation_data: tuple, tex_width: int, tex_height: int, bake_frame_height: int, bake_frames_info: list, num_bones: int, bones: list) -> tuple[list, list, list, list]:
    """
    Intermediate buffer function to return the values to store in the texture RGBA channels

    :param context: Blender current execution context
    :param texture: texture to generate buffer for
    :param animation_data: list of bone matrices, per frame
    :param tex_width: BAT's anim texture(s) width
    :param tex_height: BAT's anim texture(s) height
    :return: pixel buffer
    :rtype: list
    """

    buffer = [0.0] * tex_width * tex_height * 4 # RGBA

    texture_channels = [
        (texture.R if texture.R.channel_mode != "NONE" else None),
        (texture.G if texture.G.channel_mode != "NONE" else None),
        (texture.B if texture.B.channel_mode != "NONE" else None),
        (texture.A if texture.A.channel_mode != "NONE" else None),
        ]

    buffer_ranges_offsets = [0.0] * 4
    buffer_ranges = [1.0] * 4
    buffer_ranges_valid = [False] * 4

    for texture_channel_index, texture_channel in enumerate(texture_channels):
        if texture_channel is None:
            continue

        pre_bake_func = get_animation_texture_buffer_function(texture_channel)
        channel_buffer = pre_bake_func(context, armature, animation_data, texture_channel, (tex_width * tex_height), tex_width, bake_frame_height, bake_frames_info, num_bones, bones)
        if channel_buffer:
            if get_animation_texture_channel_allow_remap(texture_channel):
                buffer_min = min(channel_buffer)
                buffer_max = max(channel_buffer)
                if abs(buffer_max - buffer_min) < 0.0001:
                    buffer_range = 1.0
                else:
                    buffer_range = buffer_max - buffer_min
                    buffer_ranges_valid[texture_channel_index] = True
                buffer_offset = buffer_min

                buffer_ranges_offsets[texture_channel_index] = buffer_offset
                buffer_ranges[texture_channel_index] = buffer_range

                if texture_channel.remapping:
                    channel_buffer = [((data - buffer_min) / buffer_range) for data in channel_buffer]

            for attr_index in range(len(channel_buffer)):
                buffer[(attr_index * 4) + texture_channel_index] = channel_buffer[attr_index]

    return (buffer, buffer_ranges_offsets, buffer_ranges, buffer_ranges_valid)

def get_animation_texture_channel_allow_remap(texture_channel: object) -> bool:
    """
    Return true if texture channel may allow values to be remapped from range [-min:max] to [0:1] for potential storage in 8-bit RGBA texture(s)

    :param texture_channel: texture channel to validate statement for
    :return: true if channel can be safely remapped
    :rtype: bool
    """
    if texture_channel.channel_mode == "NONE":
        return False

    if texture_channel.channel_mode == "ROTATION" and texture_channel.rot_mode == "QUAT" and texture_channel.quat == "XYZW": # bit-packed quaternions don't allow remapping
        return False
    return True

def get_inverted_buffer(buffer: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """ 
    Re-order buffer so that pixel buffer is flipped in V (aka invert image). Append line of pixels after line in reverse order.

    :param buffer: buffer
    :param tex_width: BAT texture(s) width
    :param tex_height: BAT texture(s) height
    :return: processed offset buffer, processed normal buffer
    :rtype: tuple
    """

    buffer_row_offset = tex_width * 4

    buffer_inv = [0.0] * len(buffer)
    for row in reversed(range(tex_height)):
        i = (tex_height - 1 - row) * buffer_row_offset
        ii = row * buffer_row_offset
        buffer_inv[i:i + buffer_row_offset] = buffer[ii:ii + buffer_row_offset]

    return buffer_inv

########################
### BUFFER FUNCTIONS ###
def skinning_texture_buffer_index(context: bpy.types.Context, skinning_data: list, texture_channel: object, buffer_length: int) -> list:
    """
    Compile and return the list of bone weights per vertex, for an influencing bone at a particular index (0 is the most influencal bone)
    
    :param context: Blender current execution context
    :param skinning_data: list containing skinning data per vertex: [bone, bone index, bone weight]
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: length of buffer to create
    :return: buffer containing bone index for an influencing bone at a particular index (0 is the most influencal bone), per vertex
    :rtype: list
    """
    index_buffer = [0.0] * buffer_length

    for vertex_skinning_data in skinning_data:
        vertex_index, bone_info = vertex_skinning_data

        try:
            bone, bone_index, bone_weight = bone_info[texture_channel.index - 1] # index setting is one-based!
            index_buffer[vertex_index] = bone_index
        except:
            continue

    return index_buffer

def skinning_texture_buffer_weight(context: bpy.types.Context, skinning_data: list, texture_channel: object, buffer_length: int) -> list:
    """
    Compile and return the list of bone weights per vertex, for an influencing bone at a particular index (0 is the most influencal bone).
    
    :param context: Blender current execution context
    :param skinning_data: list containing skinning data per vertex: [bone, bone index, bone weight]
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: length of buffer to create
    :return: buffer containing bone influence/weight for an influencing bone at a particular index (0 is the most influencal bone), per vertex
    :rtype: list
    """
    weight_buffer = [0.0] * buffer_length

    for vertex_skinning_data in skinning_data:
        vertex_index, bone_info = vertex_skinning_data

        try:
            bone, bone_index, bone_weight = bone_info[texture_channel.index - 1] # index setting is one-based!
            weight_buffer[vertex_index] = bone_weight
        except:
            continue

    return weight_buffer

def skinning_texture_buffer_zeros(context: bpy.types.Context, skinning_data: list, texture_channel: object, buffer_length: int) -> list:
    """
    Compile and return a list of zero.
    
    :param context: Blender current execution context
    :param skinning_data: list containing skinning data per vertex: [bone, bone index, bone weight]
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: length of buffer to create
    :return: buffer containing zeros
    :rtype: list
    """

    index_buffer = [0.0] * buffer_length
    return index_buffer

def animation_texture_buffer_position(context: bpy.types.Context, armature: bpy.types.Armature, animation_data: list, texture_channel: object, buffer_length: int, tex_width: int, bake_frame_height: int, bake_frames_info: list, num_bones: int, bones: list) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param animation_data: list containing bone matrices per frame
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: number of unique indices to bake
    :return: pixel buffer
    :rtype: list
    """
    settings = context.scene.BATBakerSettings
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    pos_buffer = [0.0] * buffer_length
    bone_ref_matrices = animation_data[0]
    for bone_frame_index, bone_frame_data in enumerate(animation_data):

        if settings.animation_tex_packing_mode == 'STACK':
            if settings.animation_tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = tex_width * bake_frame_height * bone_frame_index
            else:
                buffer_frame_offset = tex_width * bone_frame_index
        else:
            buffer_frame_offset = num_bones * bone_frame_index

        for bone_index, bone_matrix in enumerate(bone_frame_data):

            if settings.animation_tex_packing_mode == "STACK" and settings.animation_tex_packing_stack_mode == "OFFSET":
                buffer_bone_index = buffer_frame_offset + (bone_index % tex_width) + ((bone_index // tex_width) * len(animation_data) * tex_width)
            else:
                buffer_bone_index = buffer_frame_offset + bone_index

            pose_mat = bone_matrix
            ref_mat = bone_ref_matrices[bone_index]

            if bone_frame_index <= 0: # ref frame is the first animation data in list
                vector_to_bake = ref_mat.to_translation() * signed_scale
            else:
                vector_to_bake = (pose_mat.to_translation() - ref_mat.to_translation()) * signed_scale
            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in texture_channel.unit_axis_order])

            if texture_channel.component == "X":
                data_to_bake = vector_to_bake.x
            elif texture_channel.component == "Y":
                data_to_bake = vector_to_bake.y
            elif texture_channel.component == "Z":
                data_to_bake = vector_to_bake.z
            else:
                data_to_bake = 0.0

            try:
                pos_buffer[buffer_bone_index] = data_to_bake
            except:
                pass

    return pos_buffer

def animation_texture_buffer_rotation(context: bpy.types.Context, armature: bpy.types.Armature, animation_data: list, texture_channel: object, buffer_length: int, tex_width: int, bake_frame_height: int, bake_frames_info: list, num_bones: int, bones: list) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param animation_data: list containing bone matrices per frame
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: number of unique indices to bake
    :return: pixel buffer
    :rtype: list
    """
    settings = context.scene.BATBakerSettings

    rot_buffer = [0.0] * buffer_length
    bone_ref_matrices = animation_data[0]
    for bone_frame_index, bone_frame_data in enumerate(animation_data):
        
        if settings.animation_tex_packing_mode == 'STACK':
            if settings.animation_tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = tex_width * bake_frame_height * bone_frame_index
            else:
                buffer_frame_offset = tex_width * bone_frame_index
        else:
            buffer_frame_offset = num_bones * bone_frame_index

        for bone_index, bone_matrix in enumerate(bone_frame_data):

            if settings.animation_tex_packing_mode == "STACK" and settings.animation_tex_packing_stack_mode == "OFFSET":
                buffer_bone_index = buffer_frame_offset + (bone_index % tex_width) + ((bone_index // tex_width) * len(animation_data) * tex_width)
            else:
                buffer_bone_index = buffer_frame_offset + bone_index

            pose_mat = bone_matrix
            ref_mat = bone_ref_matrices[bone_index]

            if bone_frame_index <= 0: # ref frame is the first animation data in list
                rot_matrix = ref_mat
            else:
                rot_matrix = pose_mat @ ref_mat.inverted()

            sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                     (-1 if settings.unit_invert_y else 1),
                                                     (-1 if settings.unit_invert_z else 1), 1))
            rot_matrix = sign_matrix @ rot_matrix @ sign_matrix
            euler = rot_matrix.to_euler(texture_channel.unit_axis_order)

            if texture_channel.rot_mode == "QUAT":
                quat = euler.to_quaternion()

                if texture_channel.quat == "X":
                    data_to_bake = quat.x
                elif texture_channel.quat == "Y":
                    data_to_bake = quat.y
                elif texture_channel.quat == "Z":
                    data_to_bake = quat.z
                elif texture_channel.quat == "W":
                    data_to_bake = quat.w
                else: # XYZW
                    data_to_bake = get_compressed_quat(quat)
            else: # AXIS_ANGLE
                axis, angle = euler.to_quaternion().to_axis_angle()

                if texture_channel.axis_angle_mode == "AXIS_X":
                    data_to_bake = axis.x
                elif texture_channel.axis_angle_mode == "AXIS_Y":
                    data_to_bake = axis.y
                elif texture_channel.axis_angle_mode == "AXIS_Z":
                    data_to_bake = axis.z
                else: # ANGLE
                    if texture_channel.quat_angle_unit_mode == "DEGREES":
                        data_to_bake = angle * (180/math.pi)
                    elif texture_channel.quat_angle_unit_mode == "UNIT":
                        data_to_bake = angle * (180/math.pi)
                        data_to_bake /= 360
                    else: # RADIANS
                        data_to_bake = angle

            try:
                rot_buffer[buffer_bone_index] = data_to_bake
            except:
                pass

    return rot_buffer

def animation_texture_buffer_scale(context: bpy.types.Context, armature: bpy.types.Armature, animation_data: list, texture_channel: object, buffer_length: int, tex_width: int, bake_frame_height: int, bake_frames_info: list, num_bones: int, bones: list) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param animation_data: list containing bone matrices per frame
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: number of unique indices to bake
    :return: pixel buffer
    :rtype: list
    """
    settings = context.scene.BATBakerSettings

    scale_buffer = [0.0] * buffer_length
    for bone_frame_index, bone_frame_data in enumerate(animation_data):
        
        if settings.animation_tex_packing_mode == 'STACK':
            if settings.animation_tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = tex_width * bake_frame_height * bone_frame_index
            else:
                buffer_frame_offset = tex_width * bone_frame_index
        else:
            buffer_frame_offset = num_bones * bone_frame_index

        for bone_index, bone_matrix in enumerate(bone_frame_data):
            
            if settings.animation_tex_packing_mode == "STACK" and settings.animation_tex_packing_stack_mode == "OFFSET":
                buffer_bone_index = buffer_frame_offset + (bone_index % tex_width) + ((bone_index // tex_width) * len(animation_data) * tex_width)
            else:
                buffer_bone_index = buffer_frame_offset + bone_index

            pose_mat = bone_matrix

            sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                     (-1 if settings.unit_invert_y else 1),
                                                     (-1 if settings.unit_invert_z else 1), 1))
            pose_mat = sign_matrix @ pose_mat @ sign_matrix
            vector_to_bake = pose_mat.to_3x3().to_scale()
            if settings.unit_axis_order != "XYZ":
                vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

            if texture_channel.component == "X":
                data_to_bake = vector_to_bake.x
            elif texture_channel.component == "Y":
                data_to_bake = vector_to_bake.y
            elif texture_channel.component == "Z":
                data_to_bake = vector_to_bake.z
            else:
                data_to_bake = 0.0

            try:
                scale_buffer[buffer_bone_index] = data_to_bake
            except:
                pass

    return scale_buffer

def animation_texture_buffer_axes(context: bpy.types.Context, armature: bpy.types.Armature, animation_data: list, texture_channel: object, buffer_length: int, tex_width: int, bake_frame_height: int, bake_frames_info: list, num_bones: int, bones: list) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param animation_data: list containing bone matrices per frame
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: number of unique indices to bake
    :return: pixel buffer
    :rtype: list
    """
    settings = context.scene.BATBakerSettings

    rot_buffer = [0.0] * buffer_length
    bone_ref_matrices = animation_data[0]
    for bone_frame_index, bone_frame_data in enumerate(animation_data):
        
        if settings.animation_tex_packing_mode == 'STACK':
            if settings.animation_tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = tex_width * bake_frame_height * bone_frame_index
            else:
                buffer_frame_offset = tex_width * bone_frame_index
        else:
            buffer_frame_offset = num_bones * bone_frame_index

        for bone_index, bone_matrix in enumerate(bone_frame_data):
            
            if settings.animation_tex_packing_mode == "STACK" and settings.animation_tex_packing_stack_mode == "OFFSET":
                buffer_bone_index = buffer_frame_offset + (bone_index % tex_width) + ((bone_index // tex_width) * len(animation_data) * tex_width)
            else:
                buffer_bone_index = buffer_frame_offset + bone_index

            pose_mat = bone_matrix
            ref_mat = bone_ref_matrices[bone_index]

            if bone_frame_index <= 0: # ref frame is the first animation data in list
                basis_matrix = ref_mat.to_3x3()
            else:
                basis_matrix = pose_mat.to_3x3() @ ref_mat.to_3x3().inverted()

            sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                     (-1 if settings.unit_invert_y else 1),
                                                     (-1 if settings.unit_invert_z else 1)))
            basis_matrix = sign_matrix @ basis_matrix @ sign_matrix

            if texture_channel.axis == "X":
                vector_to_bake = basis_matrix @ mathutils.Vector((1.0, 0.0, 0.0))
            elif texture_channel.axis == "Y":
                vector_to_bake = basis_matrix @ mathutils.Vector((0.0, 1.0, 0.0))
            else: # Z
                vector_to_bake = basis_matrix @ mathutils.Vector((0.0, 0.0, 1.0))

            if texture_channel.unit_axis_order != "XYZ":
                vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

            if not texture_channel.axis_scaled:
                vector_to_bake.normalize()

            if texture_channel.component == "X":
                data_to_bake = vector_to_bake.x
            elif texture_channel.component == "Y":
                data_to_bake = vector_to_bake.y
            elif texture_channel.component == "Z":
                data_to_bake = vector_to_bake.z
            else:
                data_to_bake = 0.0

            try:
                rot_buffer[buffer_bone_index] = data_to_bake
            except:
                pass

    return rot_buffer

def animation_texture_buffer_custom_prop(context: bpy.types.Context, armature: bpy.types.Armature, animation_data: list, texture_channel: object, buffer_length: int, tex_width: int, bake_frame_height: int, bake_frames_info: list, num_bones: int, bones: list) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param animation_data: list containing bone matrices per frame
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: number of unique indices to bake
    :return: pixel buffer
    :rtype: list
    """
    settings = context.scene.BATBakerSettings
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info

    animation_data = [0.0] * len(frames_to_bake)
    """
    create buffer containing posed & ref bone matrices, per frame.
    Ref matrices are duplicated each frame but that's for convenience.
    They *may* be evaluated at a custom frame that isn't in the frames
    to bake.
    """
    for frame_index, frame in enumerate(frames_to_bake):
        context.scene.frame_set(frame)
        dgraph = context.evaluated_depsgraph_get()
        eval_arm = armature.evaluated_get(dgraph)

        frame_buffer = [None] * len(bones)
        for bone in eval_arm.pose.bones:
            try:
                bone_index = bones.index(bone.name)
            except:
                continue

            if texture_channel.name in bone:
                custom_prop = bone[texture_channel.name]
            else:
                custom_prop = 0

            frame_buffer[bone_index] = custom_prop

        animation_data[frame_index] = frame_buffer

    """
    
    """
    custom_prop_buffer = [0.0] * buffer_length
    for bone_frame_index, bone_frame_data in enumerate(animation_data):
        
        if settings.animation_tex_packing_mode == 'STACK':
            if settings.animation_tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = tex_width * bake_frame_height * bone_frame_index
            else:
                buffer_frame_offset = tex_width * bone_frame_index
        else:
            buffer_frame_offset = num_bones * bone_frame_index

        for bone_index, bone_custom_prop in enumerate(bone_frame_data):

            if settings.animation_tex_packing_mode == "STACK" and settings.animation_tex_packing_stack_mode == "OFFSET":
                buffer_bone_index = buffer_frame_offset + (bone_index % tex_width) + ((bone_index // tex_width) * len(animation_data) * tex_width)
            else:
                buffer_bone_index = buffer_frame_offset + bone_index

            data_to_bake = bone_custom_prop

            try:
                custom_prop_buffer[buffer_bone_index] = data_to_bake
            except:
                pass

    return custom_prop_buffer

def animation_texture_buffer_zeros(context: bpy.types.Context, armature: bpy.types.Armature, animation_data: list, texture_channel: object, buffer_length: int, tex_width: int, bake_frame_height: int, frames_to_bake: list, num_bones: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param animation_data: list containing bone matrices per frame
    :param texture_channel: texture channel to generate buffer for
    :param buffer_length: number of unique indices to bake
    :return: pixel buffer
    :rtype: list
    """

    buffer = [0.0] * buffer_length
    return buffer

##############
### BOUNDS ###
def display_bounds(context: bpy.types.Context, bake_name: str, bounds_info: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector]) -> tuple[bool, str]:
    """
    Generate a world aligned bounding box mesh matching the animation's overall 'volume'

    :param context: Blender's current execution context
    :param bake_name: the bake operation's 'name'
    :param corners: tuple containing the 'zero' and 'one' corners
    :param scale: scale to apply to the corners
    :return: the function's success, potential error message, generated object
    :rtype: tuple
    """

    settings = context.scene.BATBakerSettings
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis / settings.unit_scale


    if bake_name is None:
        return (False, "Invalid name")

    ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset = bounds_info

    min_bounds = (ref_min_bounds + min_bounds_offset) * signed_scale
    max_bounds = (ref_max_bounds + max_bounds_offset) * signed_scale

    bounds_verts = [
        mathutils.Vector((min_bounds.x, min_bounds.y, min_bounds.z)),
        mathutils.Vector((min_bounds.x, min_bounds.y, max_bounds.z)),
        mathutils.Vector((min_bounds.x, max_bounds.y, max_bounds.z)),
        mathutils.Vector((min_bounds.x, max_bounds.y, min_bounds.z)),
        mathutils.Vector((max_bounds.x, max_bounds.y, max_bounds.z)),
        mathutils.Vector((max_bounds.x, max_bounds.y, min_bounds.z)),
        mathutils.Vector((max_bounds.x, min_bounds.y, min_bounds.z)),
        mathutils.Vector((max_bounds.x, min_bounds.y, max_bounds.z))
    ]

    bounds_faces = [
            [0, 1, 2, 3],
            [7, 6, 5, 4],
            [6, 7, 1, 0],
            [4, 5, 3, 2],
            [7, 4, 2, 1],
            [0, 3, 5, 6],
        ]

    bounds_obj = bpy.context.scene.objects.get(bake_name, None)
    if bounds_obj is None:
        bounds_mesh = bpy.data.meshes.new(bake_name)
        bounds_mesh.from_pydata(bounds_verts, [], bounds_faces)
        bounds_obj = bpy.data.objects.new(bounds_mesh.name, bounds_mesh)
        bounds_obj.display_type = 'WIRE'

        col = bpy.data.collections.get("ObjAnim", None)
        if col is None:
            col = bpy.data.collections.new("ObjAnim")
            bpy.context.scene.collection.children.link(col)

        col.objects.link(bounds_obj)
    else:
        if bounds_obj.type == "MESH":
            bounds_mesh = bounds_obj.data
            if len(bounds_mesh.vertices) == 8: # does it look like our mesh? update it!
                for bounds_vertex_index, bounds_vertex in enumerate(bounds_mesh.vertices):
                    bounds_vertex.co = bounds_verts[bounds_vertex_index]
            else:
                return (False, "An object named " + bake_name + " already exists but it doesn't look like it's from a previous bake. Unsafe to modify")
        else:
            return (False, "An object named " + bake_name + " already exists but isn't a mesh. Can't modify it")

    return (True, "")

################
### TEXTURES ###
def generate_texture(texture_name: str, bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate and return a texture containing the provided pixel buffer

    :param texture_name: the texture's name
    :param bake_name: the bake operation's 'name'
    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: BAT image's width
    :param tex_height: BAT image's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename
    tags = { "TextureName": texture_name, "BakeName": bake_name}
    image_name = replace_tags(image_name, tags)
    if image_name == "":
        return (True, "Invalid image name", None)
    
    image_name += ".exr"

    image = bpy.data.images.get(image_name, None)
    if image is not None and bpy.data.is_saved:
        if image.packed_file and bpy.data.is_saved:
            #image.unpack() # this isn't necessary and causes images to be saved on disk with wrong path
            pass
        bpy.data.images.remove(image) # remove image if it exists

    image = bpy.data.images.new(name=image_name, width=tex_width, height=tex_height, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.file_format = 'OPEN_EXR'
    image.use_half_precision = False
    image.pixels = buffer
    image.use_fake_user = True
    if bpy.data.is_saved and bpy.data.is_saved:
        image.pack()

    return (True, "", image)

def export_texture(context: bpy.types.Context, image: bpy.types.Image, file_path: str, file_name: str, texture_name: str, bake_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the texture

    :param context: Blender current execution context
    :param image: the object attributes image to export
    :param file_path: export path
    :param file_name: file name
    :param texture_name: texture name
    :param bake_name: the bake operation's 'name'
    :param override_file: if an existing .exr file should be overriden
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    tags = { "TextureName": texture_name, "BakeName": bake_name}
    success, msg, tex_path = get_path(file_path, file_name, ".exr", tags, override_file)
    if success:
        image.filepath_raw = tex_path

        # cache scene render image settings
        FileFormat = context.scene.render.image_settings.file_format
        ColorDepth = context.scene.render.image_settings.color_depth
        EXRCodec = context.scene.render.image_settings.exr_codec
        
        # override scene render image settings
        context.scene.render.image_settings.file_format = 'OPEN_EXR'
        context.scene.render.image_settings.color_depth = '32'
        context.scene.render.image_settings.exr_codec = 'NONE'

        image.save_render(filepath=tex_path)

         # restore scene render image settings
        context.scene.render.image_settings.file_format = FileFormat
        context.scene.render.image_settings.color_depth = ColorDepth
        context.scene.render.image_settings.exr_codec = EXRCodec

        return (True, "", tex_path)
    else:
        return (False, msg, tex_path)

def get_best_skinning_texture_resolution(context: bpy.types.Context, num_vertices: int) -> tuple[bool, str, int, int]:
    """
    Returns the best texture resolution for a given amount of vertices to bake, in order to assign one texel per vertex

    :param context: Blender current execution context
    :param num_vertices: Number of vertices to bake
    :return: the function's success, potential error message, texture width, texture height
    :rtype: tuple
    """
    settings = context.scene.BATBakerSettings

    """
    get how many data to bake in texture per vertex: typically 2
    - one texel for the bone indices
    - one texel for the bone weights (just below)
    This count *may* diverge between textures because of user error
    but it really shouldn't... We use max to prevent buffer overflow
    """
    rows = 0
    for skinning_texture in settings.skinning_textures:
        if skinning_texture.storage_mode == "VCOL":
            continue

        rows = max(rows, len(skinning_texture.rows))

    if rows == 0:
        return (True, "", 0, 0, True)

    """
    compute width/height of texture(s) meant to contain bone indices/weights
    - Power of Two (square)
    - Power of Two
    - Non Power of Two (width dominant)
    """
    if settings.skinning_tex_res_mode == "ROWS":
        tex_width = num_vertices
        if (tex_width > settings.skinning_tex_max_width):
            tex_width = settings.skinning_tex_max_width

        vert_rows = math.ceil(num_vertices / float(tex_width))

        tex_height = rows * vert_rows
        if (tex_height > settings.skinning_tex_max_height):
            return (False, "Invalid tex_height", tex_width, tex_height, False)
    elif settings.skinning_tex_res_mode == "SQRT":
        num_texels = num_vertices * rows
        num_texels_sqrt = math.sqrt(num_texels)
        size = math.ceil(num_texels_sqrt)

        tex_width = size
        if (tex_width > settings.skinning_tex_max_width):
            return (False, "Invalid tex_width", tex_width, tex_height, False)

        vert_rows = math.ceil(num_vertices / float(tex_width))

        tex_height = size
        if (tex_height > settings.skinning_tex_max_height):
            return (False, "Invalid tex_height", tex_width, tex_height, False)
    elif settings.skinning_tex_res_mode == "POT":
        num_texels = num_vertices * rows
        num_texels_sqrt = math.sqrt(num_texels)
        size = math.ceil(num_texels_sqrt)

        tex_width = 2
        while (tex_width < size and tex_width < settings.skinning_tex_max_width):
            tex_width *= 2

        vert_rows = math.ceil(num_vertices / float(tex_width))

        tex_height = 2
        while (tex_height < (num_texels / tex_width)):
            tex_height *= 2

        if (tex_height > settings.skinning_tex_max_height):
            return (False, "Invalid tex_height", tex_width, tex_height, False)
    else: # SQUARE_POT
        num_texels = num_vertices * rows
        num_texels_sqrt = math.sqrt(num_texels)
        size = math.ceil(num_texels_sqrt)

        tex_width = 2
        while (tex_width < size and tex_width < settings.skinning_tex_max_width):
            tex_width *= 2

        vert_rows = math.ceil(num_vertices / float(tex_width))
        tex_height = tex_width

    """
    report necessary data
    """    
    add_bake_report("skinning_tex_rows", vert_rows)
    add_bake_report("skinning_tex_res_mode", settings.skinning_tex_res_mode)
    add_bake_report("skinning_tex_height", tex_height)
    add_bake_report("skinning_tex_width", tex_width)

    return (True, "", tex_width, tex_height, False)

def get_best_animation_texture_resolution(context: bpy.types.Context, num_frames: int, num_bones: int) -> tuple[bool, str, int, int, int, int]:
    """
    Returns the best texture resolution for a given amount of frames & bones to bake, ideally one row per frame & one column per bone

    :param context: Blender current execution context
    :param num_frames: Number of frames to bake
    :param num_bones: Number of bones to bake per frame
    :return: the function's success, potential error message, texture width, texture height, frame 'height' and 'width'
    :rtype: tuple
    """
    settings = context.scene.BATBakerSettings

    #########
    # WIDTH #

    if (settings.animation_tex_force_power_of_two):
        tex_width = 2
        while (tex_width < num_bones and tex_width < settings.animation_tex_max_width):
            tex_width *= 2
    else:
        tex_width = num_bones
        if (tex_width > settings.animation_tex_max_width):
            tex_width = settings.animation_tex_max_width

    # how many lines of pixels per frame?
    bake_frame_height_float = num_bones / float(tex_width)
    bake_frame_height = math.ceil(bake_frame_height_float) if settings.animation_tex_packing_mode == 'STACK' else bake_frame_height_float # else 'CONTINUOUS'

    # fallback to using maximum allowed width if data can no longer fit into the texture based on that width
    if ((num_frames * bake_frame_height) > settings.animation_tex_max_height):
        tex_width = settings.animation_tex_max_width

    if (tex_width > settings.animation_tex_max_width):
        return (False, "Invalid tex_width", tex_width, tex_height, bake_frame_height, 0.0)

    ##########
    # HEIGHT #

    if (settings.animation_tex_force_power_of_two):
        tex_height = 2
        while (tex_height < (num_frames * bake_frame_height)):
            tex_height *= 2
    else:
        tex_height = num_frames * bake_frame_height if settings.animation_tex_packing_mode == 'STACK' else math.ceil(num_frames * bake_frame_height) # else 'CONTINUOUS'

    if (tex_height > settings.animation_tex_max_height):
        return (False, "Invalid tex_height", tex_width, tex_height, bake_frame_height, 0.0)

    ##########

    if (settings.animation_tex_force_power_of_two and settings.animation_tex_force_power_of_two_square):
        if tex_width < tex_height:
            tex_width = tex_height
            
            bake_frame_height_float = num_bones / float(tex_width)
            bake_frame_height = math.ceil(bake_frame_height_float) if settings.animation_tex_packing_mode == 'STACK' else bake_frame_height_float # else 'CONTINUOUS'
        elif tex_height < tex_width:
            tex_height = tex_width

    underflow = num_bones < tex_width
    add_bake_report("animation_tex_underflow", underflow)
    overflow = num_bones > tex_width
    add_bake_report("animation_tex_overflow", overflow)

    bake_frame_width = num_bones / float(tex_width)
    add_bake_report("animation_tex_frame_height", bake_frame_height)
    add_bake_report("animation_tex_height", tex_height)
    add_bake_report("animation_tex_frame_width", bake_frame_width)
    add_bake_report("animation_tex_width", tex_width)

    sampling = "STACK_SINGLE"
    if (underflow or overflow):
        if settings.animation_tex_packing_mode == 'CONTINUOUS':
            sampling = "CONTINUOUS"
        else:
            sampling = "STACK_MULT"

    add_bake_report("animation_tex_sampling_mode", sampling)
    add_bake_report("animation_tex_packing_stack_mode", settings.animation_tex_packing_stack_mode)

    return (True, "", tex_width, tex_height, bake_frame_height, bake_frame_width)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.BATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"
    report = context.scene.BATBakerReport

    root = ET.Element("BakedData",
                      type="BoneAnimationTextures",
                      ID=report.ID,
                      version="1.0")

    # unit
    unit_el = ET.SubElement(root, "Unit",
                            system=report.unit_system,
                            unit=str(report.unit_unit),
                            length=str(report.unit_length),
                            unit_scale=str(report.unit_scale),
                            unit_invert_x=str(report.unit_invert_x),
                            unit_invert_y=str(report.unit_invert_y),
                            unit_invert_z=str(report.unit_invert_z),
                            unit_invert_v=str(report.unit_invert_v))

    # frame
    frame_el = ET.SubElement(root, "Frames",
                             sampling=report.animation_tex_sampling_mode,
                             count=str(report.num_frames),
                             padded=str(report.num_frames_padded),
                             padding=str(report.padding),
                             rate=str(report.frame_rate),
                             ref=str(report.frame_ref),
                             ref_padding=str(report.frame_ref_padding))

    # mesh info
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""

    mesh_el = ET.SubElement(root, "Mesh", path=mesh_export_path,
                             uv_index=str(report.mesh_uvmap_index),
                             bounds_offset_min_x=str(abs(report.mesh_min_bounds_offset[0])),
                             bounds_offset_min_y=str(abs(report.mesh_min_bounds_offset[1])),
                             bounds_offset_min_z=str(abs(report.mesh_min_bounds_offset[2])),
                             bounds_offset_max_x=str(abs(report.mesh_max_bounds_offset[0])),
                             bounds_offset_max_y=str(abs(report.mesh_max_bounds_offset[1])),
                             bounds_offset_max_z=str(abs(report.mesh_max_bounds_offset[2])))

    # vcol info
    if report.skinning_textures:
        for skinning_texture in report.skinning_textures:
            if skinning_texture.storage_mode == "VCOL":
                vcol_el = ET.SubElement(root, "VCol")

                try:
                    skinning_texture_row = skinning_texture.rows[0] # only one texture targetting vcol
                except:
                    skinning_texture_row = None

                if skinning_texture_row:
                    vcol_subel = ET.SubElement(vcol_el, "R",
                                            mode=skinning_texture_row.R.channel_mode,
                                            index=str(skinning_texture_row.R.index)
                                            )
                    vcol_subel = ET.SubElement(vcol_el, "G",
                                            mode=skinning_texture_row.G.channel_mode,
                                            index=str(skinning_texture_row.G.index)
                                            )
                    vcol_subel = ET.SubElement(vcol_el, "B",
                                            mode=skinning_texture_row.B.channel_mode,
                                            index=str(skinning_texture_row.B.index)
                                            )
                    vcol_subel = ET.SubElement(vcol_el, "A",
                                            mode=skinning_texture_row.A.channel_mode,
                                            index=str(skinning_texture_row.A.index)
                                            )
                break
            else:
                continue

    # textures info
    if report.skinning_textures or report.animation_textures:
        tex_el = ET.SubElement(root, "Textures")

        # skinning textures
        if report.skinning_textures:
            for skinning_texture in report.skinning_textures:
                if skinning_texture.storage_mode == "VCOL":
                    continue

                tex_subel = ET.SubElement(tex_el, "Texture",
                                            type="Skinning",
                                            width=str(report.skinning_tex_width),
                                            height=str(report.skinning_tex_height),
                                            rows=str(report.skinning_tex_rows),
                                            mode=str(report.skinning_tex_res_mode),
                                            path=skinning_texture.path,
                                            )

                for skinning_texture_row in skinning_texture.rows:
                    tex_rowel = ET.SubElement(tex_subel, "Row",
                                            name=skinning_texture_row.name,
                                            )

                    tex_rowsubel = ET.SubElement(tex_rowel, "R",
                                            mode=skinning_texture_row.R.channel_mode,
                                            index=str(skinning_texture_row.R.index)
                                            )
                    tex_rowsubel = ET.SubElement(tex_rowel, "G",
                                            mode=skinning_texture_row.G.channel_mode,
                                            index=str(skinning_texture_row.G.index)
                                            )
                    tex_rowsubel = ET.SubElement(tex_rowel, "B",
                                            mode=skinning_texture_row.B.channel_mode,
                                            index=str(skinning_texture_row.B.index)
                                            )
                    tex_rowsubel = ET.SubElement(tex_rowel, "A",
                                            mode=skinning_texture_row.A.channel_mode,
                                            index=str(skinning_texture_row.A.index)
                                            )

        # animation textures
        if report.animation_textures:
            for animation_texture in report.animation_textures:
                tex_subel = ET.SubElement(tex_el, "Texture",
                                            type="Animation",
                                            width=str(report.animation_tex_width),
                                            frame_width=str(report.animation_tex_frame_width),
                                            height=str(report.animation_tex_height),
                                            frame_height=str(report.animation_tex_frame_height),
                                            mode=str(report.animation_tex_sampling_mode),
                                            path=animation_texture.path,
                                            )

                channels = [
                    (animation_texture.R, "R", animation_texture.R_range_offset, animation_texture.R_range, animation_texture.R_range_valid),
                    (animation_texture.G, "G", animation_texture.G_range_offset, animation_texture.G_range, animation_texture.G_range_valid),
                    (animation_texture.B, "B", animation_texture.B_range_offset, animation_texture.B_range, animation_texture.B_range_valid),
                    (animation_texture.A, "A", animation_texture.A_range_offset, animation_texture.A_range, animation_texture.A_range_valid)
                ]
                for channel, channel_name, channel_range_offset, channel_range, channel_range_valid in channels:
                    channel_remapped = channel.remapping and get_animation_texture_channel_allow_remap(channel)

                    if channel.channel_mode == "POSITION":
                        channel_el = ET.SubElement(tex_subel, channel_name,
                                                mode=channel.channel_mode,
                                                axis_order=channel.unit_axis_order,
                                                component=channel.component,
                                                remapped=str(channel_remapped),
                                                range_offset=str(channel_range_offset),
                                                range=str(channel_range),
                                                range_valid=str(channel_range_valid))
                    elif channel.channel_mode == "ROTATION":
                        if channel.rot_mode == "QUAT":
                            channel_el = ET.SubElement(tex_subel, channel_name,
                                                    mode=channel.channel_mode,
                                                    axis_order=channel.unit_axis_order,
                                                    rot_mode=channel.rot_mode,
                                                    quat=channel.quat,
                                                    remapped=str(channel_remapped),
                                                    range_offset=str(channel_range_offset),
                                                    range=str(channel_range),
                                                    range_valid=str(channel_range_valid))
                        else: # AXIS_ANGLE
                            channel_el = ET.SubElement(tex_subel, channel_name,
                                                    mode=channel.channel_mode,
                                                    axis_order=channel.unit_axis_order,
                                                    rot_mode=channel.rot_mode,
                                                    axis_angle=channel.axis_angle_mode,
                                                    angle_mode=channel.quat_angle_unit_mode,
                                                    remapped=str(channel_remapped),
                                                    range_offset=str(channel_range_offset),
                                                    range=str(channel_range),
                                                    range_valid=str(channel_range_valid))
                    elif channel.channel_mode == "AXIS":
                        channel_el = ET.SubElement(tex_subel, channel_name,
                                                    mode=channel.channel_mode,
                                                    axis_order=channel.unit_axis_order,
                                                    component=channel.component,
                                                    axis=channel.axis,
                                                    remapped=str(channel_remapped),
                                                    range_offset=str(channel_range_offset),
                                                    range=str(channel_range),
                                                    range_valid=str(channel_range_valid))
                    else: # SCALE
                        channel_el = ET.SubElement(tex_subel, channel_name,
                                                mode=channel.channel_mode,
                                                axis_order=channel.unit_axis_order,
                                                component=channel.component,
                                                remapped=str(channel_remapped),
                                                range_offset=str(channel_range_offset),
                                                range=str(channel_range),
                                                range_valid=str(channel_range_valid))

    # anims info
    if report.anims:
        anims_el = ET.SubElement(root, "Animations")
        for anim in report.anims:
            anim_el = ET.SubElement(anims_el, "Animation",
                                    name=anim.name,
                                    start_frame=str(anim.start_frame),
                                    end_frame=str(anim.end_frame),
                                    frames=str(anim.end_frame - (anim.start_frame)))

    # write xml
    tree = ET.ElementTree(root)
    if settings.export_xml_mode == "MESHPATH" and report.mesh_path != "":
        export_path = os.path.join(os.path.dirname(report.mesh_path), report.name + ".xml")
        tree.write(export_path)
        return (True, "", export_path)
    else:
        success, msg, export_path = get_path(settings.export_xml_file_path, settings.export_xml_file_name if settings.export_xml_file_name != "" else report.name, ".xml", [], settings.export_xml_override)
        if success:
            tree.write(export_path)
            return (True, "", export_path)
        else:
            return (False, msg, "")

#########################
### PATHS & FILENAMES ###
def get_path(file_path: str, file_name: str, file_ext: str, tags: list, override_file: bool) -> tuple[bool, str, str]:
    """
    Compile path/name/extension into a path on disk, and performs a couples of safety checks
    
    :param file_path: file path
    :param file_name: file name
    :param file_ext: file extention
    :param tags: tags to search for and replace in the file_name
    :param override_file: if False, function fails if computed path lead to an existing file
    :return: the function's success, potential error message, path
    :rtype: tuple
    """
    
    file_exts = [".png", ".exr", ".fbx"]
    if file_ext not in file_exts:
        return (False, "Invalid File Extension", "")

    file_name = replace_tags(file_name, tags)
    export_path = os.path.abspath(os.path.join(bpy.path.abspath(file_path), file_name + file_ext))
    success, msg = check_path(export_path, override_file)
    
    return (success, msg, export_path)

def replace_tags(file_name: str, tags: list) -> str:
    """
    Scan the provided string and replace any <tag> with the provided tags dictionnary
    
    :param file_name: string to modify
    :param tags: tags to search for and replace in the file_name
    :return: the modified file_name
    :rtype: str
    """
    for tag_key, tag_value in tags.items():
        tag = "<"+tag_key+">"
        if (tag in file_name):
            file_name = file_name.replace(tag, tag_value)

    return file_name

def check_path(disk_path: str, override_file: str) -> tuple[bool, str]:
    """
    Check that the directory exists and is writable, and check that the file can be overriden, if any exist at that location

    :param disk_path: path to validate
    :param override_file: if False, function fails if computed path lead to an existing file
    :return: the path's validity, potential error message
    :rtype: tuple
    """
    dir = os.path.dirname(disk_path)
    if not os.path.isdir(dir):
        return (False, f"Directory does not exist: {dir}")
    
    if not os.access(dir, os.W_OK):
        return (False, f"Directory is not writable: {dir}")

    if os.path.isfile(disk_path) and not override_file:
        return (False, f"File already exists: {disk_path}")

    return (True, "")