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
import math
import mathutils
import bmesh
import os
import uuid
import numpy as np
import time
import xml.etree.ElementTree as ET

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
    settings = context.scene.OATBakerSettings

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
    add_bake_report("unit_axis_order", settings.unit_axis_order)

def reset_bake_report():
    """
    Set all report properties to their default values

    :return: None
    :rtype: None
    """
    report = bpy.context.scene.OATBakerReport
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
    report.unit_axis_order = "XYZ"

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
    report.tex_frame_height = 0.0
    report.tex_frame_width = 0.0
    report.frame_rate = 0
    report.frame_ref = 0
    report.frame_ref_mode = ""

    report.num_verts = 0

    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_uvmap_index = 0
    report.unit_invert_v = False
    report.mesh_min_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.mesh_max_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))

    report.textures.clear()
    report.textures_selected_index = 0

    report.tex_width = 0
    report.tex_height = 0
    report.tex_underflow = False
    report.tex_overflow = False
    report.tex_offset = None
    report.tex_offset_mode = ""
    report.tex_offset_export = False
    report.tex_offset_path = ""
    report.tex_offset_remapped = False
    report.tex_offset_range_offset = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_offset_range = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_normal = None
    report.tex_normal_export = False
    report.tex_normal_path = ""
    report.tex_normal_remapped = False
    report.tex_normal_range_offset = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_normal_range = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_sampling_mode = "STACK_SINGLE"
    report.tex_sampling_stack_mode = "ADJACENT"

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
    setattr(bpy.context.scene.OATBakerReport, prop_name, prop_value)

def add_bake_texture_report(texture: object, img: bpy.types.Image, buffer_ranges_offsets: list, buffer_ranges: list, buffer_ranges_valid: list) -> object:
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
    report = bpy.context.scene.OATBakerReport

    report_texture = report.textures.add()
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

    # copy all texture attributes
    if hasattr(texture, "__annotations__"):
        for prop_name in texture.__annotations__.keys():
            try:
                setattr(report_texture, prop_name, getattr(texture, prop_name))
            except (AttributeError, TypeError):
                pass

    # for all channels in texture row
    row_channels = [texture.R, texture.G, texture.B, texture.A]
    report_row_channels = [report_texture.R, report_texture.G, report_texture.B, report_texture.A]
    for row_channel_index, row_channel in enumerate(row_channels):
        if hasattr(row_channel, "__annotations__"):
            for prop_name in row_channel.__annotations__.keys():
                try:
                    setattr(report_row_channels[row_channel_index], prop_name, getattr(row_channels[row_channel_index], prop_name))
                except (AttributeError, TypeError):
                    pass

    return report_texture

def edit_bake_texture_report_prop(texture: object, value, prop_name: str) -> bool:
    """
    Edit a texture in the report to modify the value stored in a property of a given name

    :param texture: texture to edit in the report
    :param value: value to tweak
    :param prop_name: property to tweak in the report texture PropertyGroup
    :return: True if edited
    :rtype: bool
    """
    report = bpy.context.scene.OATBakerReport

    for report_texture in report.textures:
        if report_texture == texture:
            setattr(report_texture, prop_name, value)
            return True

    return False

def edit_bake_texture_report_path(texture: object, path: str) -> bool:
    """
    Edit a texture in the report to modify its path

    :param texture: texture to edit in the report
    :param path: new path to set
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_texture_report_prop(texture, path, "path")

def edit_bake_texture_report_exported(texture: object, exported: bool):
    """
    Edit a texture in the report to modify its 'exported' status

    :param texture: texture to edit in the report
    :param exported: new 'exported' status
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_texture_report_prop(texture, exported, "exported")

def clear_bake_texture_report(texture: object) -> bool:
    """
    Remove a texture from the report
    
    :param texture: texture to remove from the report
    :return: True if cleared/removed
    :rtype: bool
    """
    report = bpy.context.scene.OATBakerReport
    
    for report_texture in report.textures:
        if report_texture == texture:
            report.textures.remove(report_texture)

    return True

def add_bake_report_anim(name: str, frame_start: int, frame_end: int):
    """
    Set values in the bake report to describe an animation clip

    :param objs: objects that made use of this animation
    :param name: animation's name
    :param frame_start: animation's start frame
    :param frame_end: animation's end frame
    :param frame_start_time: animation's start normalized time
    :param frame_end_time: animation's end normalized time
    :return: None
    :rtype: None
    """
    settings = bpy.context.scene.OATBakerSettings
    report = bpy.context.scene.OATBakerReport

    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

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

###########
### NLA ###
def get_obj_nla_tracks(obj_to_bake: bpy.types.Object) -> bpy.types.NlaTrack:
    """
    Return the list of NLA tracks the given object has, if any

    :obj_to_bake: object to search NLA tracks for
    :return: list of NLA tracks the object has, if any, None otherwise
    :rtype: NlaTrack
    """
    if not obj_to_bake:
        return None

    if (obj_to_bake and obj_to_bake.animation_data and obj_to_bake.animation_data.nla_tracks): # check NLA track on object itself
        return obj_to_bake.animation_data.nla_tracks
    elif (obj_to_bake.parent and obj_to_bake.parent.animation_data and obj_to_bake.parent.animation_data.nla_tracks): # else, check NLA track on object's parent, if it is parented at all
        return obj_to_bake.parent.animation_data.nla_tracks

    return None

def get_obj_nla_start_end_frames(obj_to_bake: bpy.types.Object) -> list:
    """
    Return the list of the object's NLA strips start/end frames
    
    :param obj_to_bake: object to check
    :return: list of frames, from start to end
    :rtype: list
    """

    nla_frames = []
    
    if obj_to_bake:
        nla_tracks = get_obj_nla_tracks(obj_to_bake)
        if nla_tracks:
            for nla_track in nla_tracks:
                for nla_strip in nla_track.strips:
                    nla_frames.append((int(nla_strip.frame_start), int(nla_strip.frame_end)))

    return nla_frames

def get_objs_nla_allow_padding(objs_to_bake: list) -> bool:
    """
    Iterate objects and compares the NLA strips of two objects at a time and returns false as soon as a NLA strip name, start or end frame isn't similar. This is used to disable the padding feature because it would otherwise lead to unexpected results if selected objects don't all share the same NLA anim strips: padded/duplicated frames for a specific NLA strip by an object may correspond to frames in the middle of a NLA clip used by another object.
    
    :objs_to_bake: objects included in the bake
    :return: uniform
    :rtype: bool
    """
    
    if len(objs_to_bake) <= 1:
        return True

    prev_obj_strips = get_obj_nla_start_end_frames(objs_to_bake[0])
    for obj_index in range(1, len(objs_to_bake)):
        obj_strips = get_obj_nla_start_end_frames(objs_to_bake[obj_index])

        if len(prev_obj_strips) != len(obj_strips):
            return False

        for obj_strip_index in range(len(obj_strips)):
            obj_strip_start_frame, obj_strip_end_frame = obj_strips[obj_strip_index]
            prev_obj_strip_start_frame, prev_obj_strip_end_frame = prev_obj_strips[obj_strip_index]

            if (obj_strip_start_frame != prev_obj_strip_start_frame) or (obj_strip_end_frame != prev_obj_strip_end_frame):
                return False
            
        prev_obj_strips = obj_strips

    return True

def get_bake_nla_strips(objs_to_bake: list) -> list:
    """
    Scan the NLA tracks of the given objects to return a list of unique NLA strips, paired with the list of meshes making use of it in their NLA tracks

    :objs_to_bake: objects included in the bake
    :return: list of (unique strip, [meshes_using_strip]) pairings
    :rtype: list
    """
    nla_strips = []
    for obj in objs_to_bake: # build list
        nla_tracks = get_obj_nla_tracks(obj)
        if nla_tracks:
            for nla_track in nla_tracks:
                for nla_strip in nla_track.strips:
                    nla_strips.append((nla_strip, obj))

    unique_nla_strips = []
    unique_nla_indices = []
    # for each strip/obj pair
    for nla_strip_index, nla_strip in enumerate(nla_strips):
        strip, obj = nla_strip
        objs_to_bake = [obj]

        # check all other strip/obj pairs
        for nla_strip_index_compare, nla_strip_compare in enumerate(nla_strips):
            if nla_strip_index != nla_strip_index_compare:
                strip_compare, obj_compare = nla_strip_compare
                # we found another object that uses the same strip at the same exact position
                if (obj != obj_compare) and (strip.name == strip_compare.name) and (strip.frame_start == strip_compare.frame_start) and (strip.frame_end == strip_compare.frame_end):
                    objs_to_bake.append(obj_compare)
                    unique_nla_indices.append(nla_strip_index_compare)

        if nla_strip_index not in unique_nla_indices:
                unique_nla_strips.append(strip)

    return unique_nla_strips

def get_bake_apply_padding(context: bpy.types.Context, objs_to_bake: list) -> bool:
    """
    Examine if user asks for frame padding to be added and if it safe to do so (objects all share the same NLA clips)

    :objs_to_bake: objects included in the bake
    :return: True if frame padding should and can be applied
    :rtype: bool
    """

    settings = context.scene.OATBakerSettings

    return (settings.frame_range_mode == "NLA") and get_objs_nla_allow_padding(objs_to_bake) and (settings.frame_padding > 0) #and (settings.tex_packing_mode == "STACK")

############
### BAKE ###
def get_bake_selection(context):
    """
    Modify & ensure the active & selected objects can lead to a valid bake and return the list of objects to include in the bake.

    :param context: Blender current execution context
    :return: success, additional message, list of objects to bake (filtered selection), active object
    :rtype: tuple
    """

    settings = context.scene.OATBakerSettings

    # proceed only if we have an active object
    if context.view_layer.objects.active == None:
        return (False, "No active object", None, None)

    # deselect all non-mesh
    for selected_obj in context.selected_objects:
        if selected_obj.type != "MESH":
            selected_obj.select_set(False)

    # double check selection after filter
    if not context.selected_objects:
        return (False, "No object selected once filtered out", None, None)

    # cache selection
    objs_to_bake = context.selected_objects

    # check UVMap can be edited/created
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.OAT"
    uvmaps = []
    # ensure objects can safely be merged without creating UVMap conflicts
    for obj_to_bake in objs_to_bake:
        # if we can NOT find target UVMap name in existing uvmaps, we'll need to create one
        if mesh_uvmap_name not in [uvlayer.name for uvlayer in obj_to_bake.data.uv_layers]:
            if len(obj_to_bake.data.uv_layers) >= 8:
                return (False, obj_to_bake.name + " has the maximum amount of uvmaps already", None, None)

        # gather uvmaps as if objects were joined
        for uvlayer in obj_to_bake.data.uv_layers:
            if uvlayer.name not in uvmaps:
                uvmaps.append(uvlayer.name)

    # if we can NOT find target UVMap name in all existing uvmaps, we'll need to create one
    if mesh_uvmap_name not in uvmaps and len(uvmaps) >= 8:
        return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None)

    # deselect objects for now
    for obj_to_bake in objs_to_bake:
        obj_to_bake.select_set(False)

    active_object = context.view_layer.objects.active
    context.view_layer.objects.active = None # blank canvas

    return (True, "", objs_to_bake, active_object)

def get_bake_textures(context: bpy.types.Context) -> tuple[bool, str, list]:
    """
    Scan the animation textures the user wants to generate, ensuring each has a unique name and contains data in at least one of the RGBA channels.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of textures to generate and bake
    :rtype: tuple
    """

    settings = context.scene.OATBakerSettings

    textures = []
    for texture in settings.textures:
        other_tex_names = [other_texture.name for other_texture in settings.textures if other_texture != texture]
        if texture.name in other_tex_names: # texture must be uniquely named
            return (False, "Multiple animation textures share the same name", None)

        if texture.R.channel_mode == "NONE" and texture.G.channel_mode == "NONE" and texture.B.channel_mode == "NONE" and texture.A.channel_mode == "NONE":
            continue

        textures.append(texture)

    if len(textures) <= 0:
        return (False, "No data to bake in texture(s)", None)

    return (True, "", textures)

def get_nla_strips_raw_frame_buffer(context: bpy.types.Context, nla_strips: list) -> list:
    """
    Compute a raw frame buffer from a list of NLA strips

    :param context: Blender current execution context
    :param nla_strips: list of NLA strips contributing to the overall animation 'range'
    :return: list of frames to bake
    :rtype: list
    """
    settings = context.scene.OATBakerSettings

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

def get_bake_frames(context, objs_to_bake):
    """
    Return the list of frames to bake and the resulting frame time.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: success, additional message, list of frames in order, frame time
    :rtype: tuple
    """

    scene = context.scene
    settings = scene.OATBakerSettings

    add_bake_report("frame_rate", (context.scene.render.fps / context.scene.render.fps_base))

    nla_strips = get_bake_nla_strips(objs_to_bake)
    nla_strips = [nla_strip for nla_strip in nla_strips if nla_strip.name not in [nla_strip_excluded.name for nla_strip_excluded in settings.frame_range_nla_exclusion]] # exclude user-specified black-listed strips

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
            padding_apply = get_bake_apply_padding(context, objs_to_bake)
            padding_prefix = padding_apply and settings.frame_padding_mode == 'PREFIX' or settings.frame_padding_mode == 'PREFIX_SUFFIX'
            padding_suffix = padding_apply and settings.frame_padding_mode == 'SUFFIX' or settings.frame_padding_mode == 'PREFIX_SUFFIX'

            add_bake_report("padded", padding_apply)
            add_bake_report("padding", settings.frame_padding if padding_apply else 0)
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

        for frame in frames_to_bake_indices:
            # we still want to scan NLA_strips to see if any fall in the user-specified frame range because
            # this can be quite useful information to report/output. Any strip that lies in the fram range
            # can be reported right away because the frame_range_mode don't allow for padding to be added.
            frame_nla_strips = []
            if nla_strips:
                for nla_strip in nla_strips:
                    start = int(nla_strip.frame_start)
                    end = int(nla_strip.frame_end)

                    # NLA strip start or end frame included in range?
                    if start <= frame_end or end >= frame_start:
                        frame_nla_strips.append(nla_strip)

                        # clamp start/end frames
                        start_frame = min(frame_end, max(frame_start, start))
                        end_frame = min(frame_end, max(frame_start, end))
                        add_bake_report_anim(nla_strip.name, start_frame, end_frame)

            frames_to_bake.append((frame, frame_nla_strips))

        # get rid of NLA_strips data from frame buffer and just keep frame int
        frames_to_bake = [frame_data[0] for frame_data in frames_to_bake]

        start_frame = min(frames_to_bake)
        add_bake_report("start_frame", start_frame)

        end_frame = max(frames_to_bake)
        add_bake_report("end_frame", end_frame)

        """
        add reference frame
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

def get_bake_name(context: bpy.types.Context, active_object: bpy.types.Object) -> str:
    """
    Return the name to give to the bake operation.

    :param context: Blender current execution context
    :param active_object: object to derive name from
    :return: the bake operation's 'name'
    :rtype: string
    """

    settings = context.scene.OATBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.OAT"
    tags = { "BakeName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def bake(context):
    """ Main bake function """
    # bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

    settings = context.scene.OATBakerSettings
    new_bake_report(context)

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #

    bake_start_time = time.time()

    success, msg, objs_to_bake, active_object = get_bake_selection(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(1)

    success, msg, textures = get_bake_textures(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(2)

    success, msg, bake_frames_info = get_bake_frames(context, objs_to_bake)
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(3)

    num_frames = len(frames_to_bake)
    num_objs = len(objs_to_bake)

    success, msg, tex_width, tex_height, bake_frame_height, bake_frame_width = get_best_texture_resolution(context, num_frames, num_objs)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(7)

    bake_name = get_bake_name(context, active_object)
    add_bake_report("name", bake_name)

    wm.progress_update(10)

    ###########
    # BUFFERS #
    success, msg, buffers, buffers_info, bounds_info = get_texture_channel_buffers(context, objs_to_bake, bake_frames_info, textures, tex_width, tex_height, bake_frame_height)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    success, msg = get_texture_buffers(context, bake_name, buffers, buffers_info, textures, tex_width, tex_height)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    ########
    # MESH #

    success, msg, obj_to_export, bake_uvmap_index = generate_mesh(context, bake_name, objs_to_bake, tex_width, tex_height, bake_ref_frame, num_frames)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)
    add_bake_report("mesh", obj_to_export)
    add_bake_report("mesh_uvmap_index", bake_uvmap_index)

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
### BUFFER ###
##############
def get_texture_buffer_obj_source_obj(texture_channel: object, eval_obj_to_bake: int, return_source: bool = True) -> bpy.types.Object:
    """
    Returns the object to get attributes from depending the texture channel's settings. This accounts for a hierarchy depth limit that may have been set (last valid parent will be used).
    Function returns the input object if unable to compute the source object, which may in various cases, for instance if the texture channel's object mode is set to 'Custom' and no custom object is specified

    :param texture_channel: The texture channel currently being processed.
    :param eval_obj_to_bake: object to get source for
    :param depth_limit_use: enable to filter by hierarchy depth
    :param depth_limit: allowed maximum hierarchy depth
    :param return_source: set to true to return the original object, if the computed source object do happen to point to one via its custom properties
    :return: the source object to use for retrieving its attributes (position, axis, scale, etc.)
    :rtype: bpy.types.Object
    """

    source_obj = None

    if texture_channel.obj_mode == "CUSTOM":
        if texture_channel.obj:
            source_obj = texture_channel.obj
    elif texture_channel.obj_mode == "PARENT":
        depth = 0
        source_obj = eval_obj_to_bake
        while source_obj and (depth < max(1, texture_channel.depth)):
            depth += 1
            if source_obj.parent:
                source_obj = source_obj.parent
            else:
                break
    elif texture_channel.obj_mode == "PROPERTY":
        if texture_channel.obj_prop != "" and texture_channel.obj_prop in eval_obj_to_bake:
            source_obj = eval_obj_to_bake[texture_channel.obj_prop]
    else:
        pass

    # fall back to itself
    if source_obj == None or not isinstance(source_obj, bpy.types.Object):
        source_obj = eval_obj_to_bake

    # return original object if desired, or self
    if "BakedSource" in source_obj and return_source:
        return source_obj["BakedSource"]
    else:
        return source_obj
    
def get_texture_channel_allow_remap(texture_channel: object) -> bool:
    """
    Return true if texture channel may allow values to be remapped from range [-min:max] to [0:1] for potential storage in 8-bit RGBA texture(s)

    :param texture_channel: texture channel to validate statement for
    :return: true if channel can be safely remapped
    :rtype: bool
    """
    if texture_channel.channel_mode == "NONE":
        return False
    
    if texture_channel.channel_mode == "HIERARCHY": # indices must not be remapped!
        return False
    
    if texture_channel.channel_mode == "ROTATION" and texture_channel.rot_mode == "QUAT" and texture_channel.quat == "XYZW": # bit-packed quaternions don't allow remapping
        return False
    return True

def get_inverted_buffer(buffer: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """ 
    Re-order buffer so that pixel buffer is flipped in V (aka invert image). Append line of pixels after line in reverse order.

    :param buffer: buffer
    :param tex_width: OAT texture(s) width
    :param tex_height: OAT texture(s) height
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
def get_texture_channel_buffers(context, objs_to_bake, bake_frames_info, textures, tex_width: int, tex_height: int, bake_frame_height: int):
    """ """
    settings = context.scene.OATBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info

    """
    compile linear list of all texture channels. For each, pre-allocate a pixel buffer
    """
    buffer_length = tex_width * tex_height * 4 # RGBA
    buffers = []
    buffers_min = []
    buffers_max = []
    for texture in settings.textures:
        buffers.append([0.0] * buffer_length)
        buffers_min.extend([float('inf'), float('inf'), float('inf'), float('inf')])
        buffers_max.extend([float('-inf'), float('-inf'), float('-inf'), float('-inf')])

    context.scene.frame_set(bake_ref_frame)
    dgraph = context.evaluated_depsgraph_get()

    """
    This step calculates the minimum and maximum bounds of the mesh in its reference pose. These bounds serve as a baseline for determining the overall min/max bounds during animation.
    By comparing the animated bounds to the reference pose bounds, an offset can be computed. This offset is later applied to the mesh in its reference pose to ensure that the bounding
    box fully encloses the animated mesh over time. This is crucial for accurate occlusion culling and avoiding visual artifacts during rendering.
    """
    ref_min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    ref_max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    obj_ref_matrices = [None] * len(objs_to_bake)
    for obj_to_bake_index, obj_to_bake in enumerate(objs_to_bake):
        #uneval_obj_source = get_texture_buffer_obj_source_obj(channel, obj_to_bake) # ref bound isn't based on source obj
        eval_obj_source = obj_to_bake.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        obj_ref_matrices[obj_to_bake_index] = eval_obj_source_mat.copy()

        bbox_corners = [(eval_obj_source_mat @ mathutils.Vector(corner)) * signed_scale for corner in eval_obj_source.bound_box]
        bbox_corners_x = [corner.x for corner in bbox_corners]
        bbox_corners_y = [corner.y for corner in bbox_corners]
        bbox_corners_z = [corner.z for corner in bbox_corners]

        ref_min_bounds = mathutils.Vector((min(ref_min_bounds.x, min(bbox_corners_x)),
                                            min(ref_min_bounds.y, min(bbox_corners_y)),
                                            min(ref_min_bounds.z, min(bbox_corners_z))))
        ref_max_bounds = mathutils.Vector((max(ref_max_bounds.x, max(bbox_corners_x)),
                                            max(ref_max_bounds.y, max(bbox_corners_y)),
                                            max(ref_max_bounds.z, max(bbox_corners_z))))

    bake_progress = 10
    bake_progress_step = (1.0 / (len(frames_to_bake))) * 80
    """
    main loop: for each frame, for each object, for each texture channel to bake
    """
    min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    for frame_index, frame in enumerate(frames_to_bake):
        context.scene.frame_set(frame)
        dgraph = context.evaluated_depsgraph_get()

        bake_progress += bake_progress_step
        context.window_manager.progress_update(bake_progress)

        if settings.tex_packing_mode == 'STACK':
            if settings.tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = frame_index * tex_width * bake_frame_height
            else:
                buffer_frame_offset = tex_width * frame_index
        else:
            buffer_frame_offset = frame_index * len(objs_to_bake)
        buffer_frame_offset *= 4

        for obj_to_bake_index, obj_to_bake in enumerate(objs_to_bake):

            if settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "OFFSET":
                buffer_object_index = buffer_frame_offset + ((obj_to_bake_index % tex_width) * 4) + ((obj_to_bake_index // tex_width) * len(frames_to_bake) * tex_width * 4)
            else:
                buffer_object_index = (obj_to_bake_index * 4) + buffer_frame_offset

            for texture_index, texture in enumerate(textures):
                channels = [texture.R, texture.G, texture.B, texture.A]
                for buffer_channel_index, buffer_channel in enumerate(channels):
                    # get object to bake. Likely self but could be another object because of a custom prop or parent because of user-set option
                    uneval_obj_source = get_texture_buffer_obj_source_obj(buffer_channel, obj_to_bake)
                    eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
                    eval_obj_source_mat = eval_obj_source.matrix_world

                    """
                    This step calculates the minimum and maximum bounds of the mesh in its animated pose. These bounds can be then compared to the bounds of the mesh in reference pose to compute
                    an offset to apply to the exported mesh's bounding box. This is important for accurate occlusion culling.
                    """
                    bbox_corners = [(eval_obj_source_mat @ mathutils.Vector(corner)) * signed_scale for corner in eval_obj_source.bound_box]
                    bbox_corners_x = [corner.x for corner in bbox_corners]
                    bbox_corners_y = [corner.y for corner in bbox_corners]
                    bbox_corners_z = [corner.z for corner in bbox_corners]

                    min_bounds = mathutils.Vector((min(min_bounds.x, min(bbox_corners_x)),
                                                min(min_bounds.y, min(bbox_corners_y)),
                                                min(min_bounds.z, min(bbox_corners_z))))
                    max_bounds = mathutils.Vector((max(max_bounds.x, max(bbox_corners_x)),
                                                max(max_bounds.y, max(bbox_corners_y)),
                                                max(max_bounds.z, max(bbox_corners_z))))

                    if settings.origin_obj:
                        eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat

                    if buffer_channel.channel_mode == "POSITION":
                        ref_obj_source_mat = obj_ref_matrices[obj_to_bake_index]
                        if settings.origin_obj:
                            ref_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ ref_obj_source_mat
                        if frame_index <= 0: # ref frame is the first animation data in list
                            vector_to_bake = ref_obj_source_mat.to_translation()
                        else:
                            vector_to_bake = eval_obj_source_mat.to_translation() - ref_obj_source_mat.to_translation()

                        vector_to_bake *= signed_scale
                        if settings.unit_axis_order != "XYZ":
                            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                        if buffer_channel.component == "X":
                            data_to_bake = vector_to_bake.x
                        elif buffer_channel.component == "Y":
                            data_to_bake = vector_to_bake.y
                        else: # Z
                            data_to_bake = vector_to_bake.z
                    elif buffer_channel.channel_mode == "ROTATION":
                        ref_obj_source_mat = obj_ref_matrices[obj_to_bake_index]
                        if settings.origin_obj:
                            ref_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ ref_obj_source_mat

                        if frame_index <= 0: # ref frame is the first animation data in list
                            eval_obj_source_mat = ref_obj_source_mat
                        else:
                            eval_obj_source_mat = eval_obj_source_mat @ ref_obj_source_mat.inverted()

                        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                                    (-1 if settings.unit_invert_y else 1),
                                                                    (-1 if settings.unit_invert_z else 1), 1))
                        rot_matrix = sign_matrix @ eval_obj_source_mat @ sign_matrix

                        xyz_order = buffer_channel.quat_xyz_order if buffer_channel.override_xyz_order else settings.unit_axis_order
                        euler = rot_matrix.to_euler(xyz_order)

                        if buffer_channel.rot_mode == "QUAT":
                            quat = euler.to_quaternion()

                            if buffer_channel.quat == "X":
                                data_to_bake = quat.x
                            elif buffer_channel.quat == "Y":
                                data_to_bake = quat.y
                            elif buffer_channel.quat == "Z":
                                data_to_bake = quat.z
                            elif buffer_channel.quat == "W":
                                data_to_bake = quat.w
                            else: # XYZW
                                data_to_bake = get_compressed_quat(quat)
                        else: # AXIS_ANGLE
                            axis, angle = euler.to_quaternion().to_axis_angle()

                            if buffer_channel.axis_angle_mode == "AXIS_X":
                                data_to_bake = axis.x
                            elif buffer_channel.axis_angle_mode == "AXIS_Y":
                                data_to_bake = axis.y
                            elif buffer_channel.axis_angle_mode == "AXIS_Z":
                                data_to_bake = axis.z
                            else: # ANGLE
                                if buffer_channel.quat_angle_unit_mode == "DEGREES":
                                    data_to_bake = angle * (180/math.pi)
                                elif buffer_channel.quat_angle_unit_mode == "UNIT":
                                    data_to_bake = angle * (180/math.pi)
                                    data_to_bake /= 360
                                else: # RADIANS
                                    data_to_bake = angle
                    elif buffer_channel.channel_mode == "SCALE":
                        eval_obj_source_mat = eval_obj_source_mat.to_3x3()
                        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                        (-1 if settings.unit_invert_y else 1),
                                                        (-1 if settings.unit_invert_z else 1)))
                        eval_obj_source_mat = sign_matrix @ eval_obj_source_mat @ sign_matrix
                        vector_to_bake = eval_obj_source_mat.to_scale()
                        
                        if settings.unit_axis_order != "XYZ":
                            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                        if buffer_channel.component == "X":
                            data_to_bake = vector_to_bake.x
                        elif buffer_channel.component == "Y":
                            data_to_bake = vector_to_bake.y
                        elif buffer_channel.component == "Z":
                            data_to_bake = vector_to_bake.z
                        else:
                            data_to_bake = 0.0
                    elif buffer_channel.channel_mode == "AXIS":
                        eval_obj_source_mat = eval_obj_source_mat.to_3x3()
                        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                                (-1 if settings.unit_invert_y else 1),
                                                                (-1 if settings.unit_invert_z else 1)))
                        eval_obj_source_mat = sign_matrix @ eval_obj_source_mat @ sign_matrix

                        if buffer_channel.axis == "X":
                            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((1.0, 0.0, 0.0))
                        elif buffer_channel.axis == "Y":
                            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((0.0, 1.0, 0.0))
                        else: # Z
                            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((0.0, 0.0, 1.0))

                        if settings.unit_axis_order != "XYZ":
                            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                        if not buffer_channel.axis_scaled:
                            vector_to_bake.normalize()

                        if buffer_channel.component == "X":
                            data_to_bake = vector_to_bake.x
                        elif buffer_channel.component == "Y":
                            data_to_bake = vector_to_bake.y
                        elif buffer_channel.component == "Z":
                            data_to_bake = vector_to_bake.z
                        else:
                            data_to_bake = 0.0
                    elif buffer_channel.channel_mode == "CUSTOM_PROP":
                        if buffer_channel.name in eval_obj_source:
                            data_to_bake = eval_obj_source[buffer_channel.name]
                        else:
                            data_to_bake = 0
                    else:
                        continue

                    buffers_min[texture_index * 4 + buffer_channel_index] = min(data_to_bake, buffers_min[texture_index * 4 + buffer_channel_index])
                    buffers_max[texture_index * 4 + buffer_channel_index] = max(data_to_bake, buffers_max[texture_index * 4 + buffer_channel_index])

                    try:
                        buffers[texture_index][buffer_object_index + buffer_channel_index] = data_to_bake
                    except:
                        pass

    buffer_ranges_offsets = [0.0] * len(textures) * 4
    buffer_ranges = [1.0] * len(textures) * 4
    buffer_ranges_valid = [False] * len(textures) * 4

    for texture_index, texture in enumerate(textures):
        channels = [texture.R, texture.G, texture.B, texture.A]
        for buffer_channel_index, buffer_channel in enumerate(channels):
            if get_texture_channel_allow_remap(buffer_channel):
                    buffer_min = buffers_min[texture_index * 4 + buffer_channel_index]
                    buffer_max = buffers_max[texture_index * 4 + buffer_channel_index]
                    if abs(buffer_max - buffer_min) < 0.0001:
                        buffer_range = 1.0
                    else:
                        buffer_range = buffer_max - buffer_min
                        buffer_ranges_valid[texture_index * 4 + buffer_channel_index] = True
                    buffer_offset = buffer_min

                    buffer_ranges_offsets[texture_index * 4 + buffer_channel_index] = buffer_offset
                    buffer_ranges[texture_index * 4 + buffer_channel_index] = buffer_range

                    if buffer_channel.remapping:
                        for i in range(buffer_channel_index, tex_width * tex_height * 4, 4):
                            buffers[texture_index][i] = (buffers[texture_index][i] - buffer_min) / buffer_range

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

    return (True, "", buffers, (buffer_ranges, buffer_ranges_offsets, buffer_ranges_valid), (ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset))

def get_texture_buffers(context, bake_name: str, buffers, buffers_info, textures, frame_width: int, frame_height: int):
    """"""
    settings = context.scene.OATBakerSettings

    buffer_range, buffer_range_offset, buffer_range_valid = buffers_info
    buffer_length = frame_width * frame_height * 4 # RGBA

    for texture_index, texture in enumerate(textures):
        pixels = buffers[texture_index]
        if len(pixels) != buffer_length:
            return (False, "Unexpected pixel buffer length: " + str(len(pixels)) + " vs " + str(buffer_length))

        if settings.unit_invert_v:
            pixels = get_inverted_buffer(pixels, frame_width, frame_height)

        success, msg, tex = generate_texture(texture.name, bake_name, settings.export_tex_file_name, pixels, frame_width, frame_height)
        if not success:
            return (False, msg)

        report_texture = add_bake_texture_report(texture, tex,
                                                 [buffer_range_offset[texture_index * 4 + 0],
                                                  buffer_range_offset[texture_index * 4 + 1],
                                                  buffer_range_offset[texture_index * 4 + 2],
                                                  buffer_range_offset[texture_index * 4 + 3]],
                                                 [buffer_range[texture_index * 4 + 0],
                                                  buffer_range[texture_index * 4 + 1],
                                                  buffer_range[texture_index * 4 + 2],
                                                  buffer_range[texture_index * 4 + 3]],
                                                 [buffer_range_valid[texture_index * 4 + 0],
                                                  buffer_range_valid[texture_index * 4 + 1],
                                                  buffer_range_valid[texture_index * 4 + 2],
                                                  buffer_range_valid[texture_index * 4 + 3]])

        tex_path = ""
        if settings.export_tex and bpy.data.is_saved:
            success, msg, tex_path = export_texture(context, tex, settings.export_tex_file_path, settings.export_tex_file_name, texture.name, bake_name, settings.export_tex_override)
            if not success:
                return (False, msg)
            edit_bake_texture_report_path(report_texture, tex_path)
            edit_bake_texture_report_exported(report_texture, True)

    return (True, "")

##############
### MESHES ###
def generate_mesh(context: bpy.types.Context, bake_name: str, objs_to_bake: list, tex_width: int, tex_height: int, bake_frame_ref: int, num_frames: int) -> tuple[bool, str, bpy.types.Object, int]:
    """
    Generate the mesh object to export

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :param objs_to_bake: List of objects to bake
    :param tex_width: OAT texture(s) width
    :param tex_height: OAT texture(s) height
    :param no_uv: skip generating UVs because skinning is exclusively baked into vcol
    :param bake_frame_ref: Frame considered as the 'reference frame', or 'base pos'
    :return: success, message, generated object, UVMap used to map the OAT texture(s)
    :rtype: tuple
    """

    settings = context.scene.OATBakerSettings
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
    eval_mesh_uvmap_index = 0

    for obj_index, obj_to_bake in enumerate(objs_to_bake):
        obj_target = obj_to_bake.get(custom_prop, None)
        obj = obj_target if obj_target and obj_target.type == "MESH" else obj_to_bake

        eval_obj = obj.evaluated_get(dgraph)
        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph).copy()
        eval_obj.to_mesh_clear()
        eval_mesh.transform(eval_obj.matrix_world)
        eval_meshes[obj_index] = eval_mesh

        success, msg, last_eval_mesh_uvmap_index = generate_mesh_uvs(context, eval_mesh, tex_width, tex_height, obj_index, num_frames)
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
    name = bake_name if bake_name != "" else "BakedMesh.OAT"
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
    
    # make new object relative to custom world origin, if needed
    if settings.origin_obj:
        """ 
        # I prefer not carrying over the world matrix to highlight the fact that the baked data may
        # only be usable if that custom world origin is indeed treated as the world origin. That
        # means the object should have a zero transform and its vertices inverse transformed. The
        # new mesh can be simply 'brought back to its rest pose' by copy/pasting the custom world
        # origin's transform manually.

        obj.matrix_world = settings.origin_obj.matrix_world
        """
        mesh.transform(settings.origin_obj.matrix_world.inverted())

    context.view_layer.objects.active = obj
    obj.select_set(True) # for export

    return (True, "", obj, eval_mesh_uvmap_index)

def generate_mesh_uvs(context: bpy.types.Context, mesh: bpy.types.Mesh, tex_width: int, tex_height: int, vertex_index_offset: int, num_frames: int) -> tuple[bool, str, int]:
    """
    Configure the mesh UVs so that one vertex is located on one unique texel in the OAT texture(s)

    :param context: Blender current execution context
    :param mesh: mesh to edit
    :param tex_width: OAT texture(s) width
    :param tex_height: OAT texture(s) height
    :param vertex_index_offset: Used to uniquely process a selection of meshes
    :return: the function's success, potential error message, index of UVMap used to map the OAT texture(s)
    :rtype: tuple
    """

    settings = context.scene.OATBakerSettings

    uvmap = None
    uvmap_index = 0
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.OAT"

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

    if (settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "ADJACENT") or settings.tex_packing_mode == "CONTINUOUS":
        # set UV
        for loop in mesh.loops:
            vertex_index = vertex_index_offset
            u = (0.5 / float(tex_width)) + (vertex_index % tex_width) / float(tex_width)
            v = (0.5 / float(tex_height)) + (vertex_index // float(tex_width)) / float(tex_height)
            if settings.unit_invert_v:
                v = 1.0 - v

            uvmap.data[loop.index].uv = (u,v)
    else: # STACK & OFFSET
        # set UV
        for loop in mesh.loops:
            vertex_index = vertex_index_offset
            u = (0.5 / float(tex_width)) + (vertex_index % tex_width) / float(tex_width)
            v = (0.5 / float(tex_height)) + ((vertex_index // float(tex_width)) * num_frames) / float(tex_height)
            if settings.unit_invert_v:
                v = 1.0 - v

            uvmap.data[loop.index].uv = (u,v)

    return (True, "", uvmap_index)

def export_mesh_selection(context: bpy.types.Context, bake_name: str):
    """
    Export the current selection to FBX

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    settings = context.scene.OATBakerSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

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

    settings = context.scene.OATBakerSettings
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
    Generate the attributes image of given width and height to contain the provided buffer.

    :param texture_name: the texture's name
    :param bake_name: the bake operation's 'name'
    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: object attributes image's width
    :param tex_height: object attributes image's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Attribute Buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename
    tags = { "TextureName": texture_name, "BakeName": bake_name}
    image_name = replace_tags(image_name, tags)
    if image_name == "":
        return (True, "Invalid image name", None)

    image_name += ".exr"

    image = bpy.data.images.get(image_name, None)
    if image is not None:
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
    if bpy.data.is_saved:
        image.pack()

    return (True, "", image)

def export_texture(context: bpy.types.Context, image: bpy.types.Image, file_path: str, file_name: str, texture_name: str, bake_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the attributes image

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

def get_best_texture_resolution(context: bpy.types.Context, num_frames: int, num_objects: int) -> tuple[bool, str, int, int]:
    """
    Returns the best texture resolution for a given amount of frames & vertices to bake

    :param context: Blender current execution context
    :param num_frames: Number of frames to bake
    :param num_vertices: Number of vertices to bake per frame
    :return: the function's success, potential error message, texture width, texture height, frame 'height' and 'width'
    :rtype: tuple
    """
    settings = context.scene.OATBakerSettings

    #########
    # WIDTH #

    if (settings.tex_force_power_of_two):
        tex_width = 2
        while (tex_width < num_objects and tex_width < settings.export_tex_max_width):
            tex_width *= 2
    else:
        tex_width = num_objects
        if (tex_width > settings.export_tex_max_width):
            tex_width = settings.export_tex_max_width

    # how many lines of pixels per frame?
    bake_frame_height_float = num_objects / float(tex_width)
    bake_frame_height = math.ceil(bake_frame_height_float) if settings.tex_packing_mode == 'STACK' else bake_frame_height_float # else 'CONTINUOUS'

    # fallback to using maximum allowed width if data can no longer fit into the texture based on that width
    if ((num_frames * bake_frame_height) > settings.export_tex_max_height):
        tex_width = settings.export_tex_max_width
    
    if (tex_width > settings.export_tex_max_width):
        return (False, "Invalid tex_width", tex_width, tex_height, bake_frame_height, 0.0)

    ##########
    # HEIGHT #

    if (settings.tex_force_power_of_two):
        tex_height = 2
        while (tex_height < (num_frames * bake_frame_height)):
            tex_height *= 2
    else:
        tex_height = num_frames * bake_frame_height if settings.tex_packing_mode == 'STACK' else math.ceil(num_frames * bake_frame_height) # else 'CONTINUOUS'

    if (tex_height > settings.export_tex_max_height):
        return (False, "Invalid tex_height", tex_width, tex_height, bake_frame_height, 0.0)

    ##########

    if (settings.tex_force_power_of_two and settings.tex_force_power_of_two_square):
        if tex_width < tex_height:
            tex_width = tex_height

            bake_frame_height_float = num_objects / float(tex_width)
            bake_frame_height = math.ceil(bake_frame_height_float) if settings.tex_packing_mode == 'STACK' else bake_frame_height_float # else 'CONTINUOUS'
        elif tex_height < tex_width:
            tex_height = tex_width

    underflow = num_objects < tex_width
    add_bake_report("tex_underflow", underflow)
    overflow = num_objects > tex_width
    add_bake_report("tex_overflow", overflow)

    add_bake_report("tex_height", tex_height)
    add_bake_report("tex_width", tex_width)

    bake_frame_width = num_objects / float(tex_width)
    add_bake_report("tex_frame_width", bake_frame_width)
    add_bake_report("tex_frame_height", bake_frame_height)

    sampling = "STACK_SINGLE"
    if (underflow or overflow):
        if settings.tex_packing_mode == 'CONTINUOUS':
            sampling = "CONTINUOUS"
        else:
            sampling = "STACK_MULT"

    add_bake_report("tex_sampling_mode", sampling)
    add_bake_report("tex_packing_stack_mode", settings.tex_packing_stack_mode)

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

    settings = context.scene.OATBakerSettings
    report = context.scene.OATBakerReport

    root = ET.Element("BakedData",
                      type="OAT",
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
                            unit_invert_v=str(report.unit_invert_v),
                            unit_axis_order=report.unit_axis_order)

    # frame
    frame_el = ET.SubElement(root, "Frames",
                             sampling=report.tex_sampling_mode,
                             stack_mode=report.tex_packing_stack_mode,
                             count=str(report.num_frames),
                             padded=str(report.num_frames_padded),
                             padding=str(report.padding),
                             rate=str(report.frame_rate),
                             ref=str(report.frame_ref))

    # textures
    tex_el = ET.SubElement(root, "Textures",
                           width=str(report.tex_width),
                           frame_width=str(report.tex_frame_width),
                           height=str(report.tex_height),
                           frame_height=str(report.tex_frame_height))
    if report.textures:
        for texture in report.textures:
            tex_subel = ET.SubElement(tex_el, "Texture",
                                      name=texture.name,
                                      path=texture.path)

            channels = [
                (texture.R, "R", texture.R_range_offset, texture.R_range, texture.R_range_valid),
                (texture.G, "G", texture.G_range_offset, texture.G_range, texture.G_range_valid),
                (texture.B, "B", texture.B_range_offset, texture.B_range, texture.B_range_valid),
                (texture.A, "A", texture.A_range_offset, texture.A_range, texture.A_range_valid)
            ]
            for channel, channel_name, channel_range_offset, channel_range, channel_range_valid in channels:
                channel_remapped = channel.remapping and get_texture_channel_allow_remap(channel)
                channel_depth = channel.depth if channel.channel_mode == "HIERARCHY" or channel.obj_mode == "PARENT" else 1
                channel_el = ET.SubElement(tex_subel, channel_name,
                                           mode=channel.channel_mode,
                                           component=channel.component,
                                           axis=channel.axis,
                                           quat=channel.quat,
                                           remapped=str(channel_remapped),
                                           range_offset=str(channel_range_offset),
                                           range=str(channel_range),
                                           range_valid=str(channel_range_valid))

    # mesh info
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""

    mesh_el = ET.SubElement(root, "Mesh", path=mesh_export_path,
                            uv_index=str(report.mesh_uvmap_index),
                            )

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