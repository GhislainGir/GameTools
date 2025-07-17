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
    settings = context.scene.VATBakerSettings

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
    report = bpy.context.scene.VATBakerReport
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
    report.frame_height = 0.0
    report.frame_width = 0.0
    report.frame_rate = 0
    
    report.num_verts = 0
    
    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_uvmap_index = 0
    report.unit_invert_v = False
    report.mesh_min_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.mesh_max_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))

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
    report.tex_packing_stack_mode = "ADJACENT"

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
    setattr(bpy.context.scene.VATBakerReport, prop_name, prop_value)

def add_bake_report_anim(objs: list, name: str, frame_start: int, frame_end: int, frame_start_time: float, frame_end_time: float):
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
    settings = bpy.context.scene.VATBakerSettings
    report = bpy.context.scene.VATBakerReport

    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    report_anim = report.anims.add()
    for obj in objs:
        report_anim_obj = report_anim.objs.add()
        report_anim_obj.obj = obj
        report_anim_obj.target_obj = obj.get(custom_prop, None)
    report_anim.name = name
    report_anim.start_frame = frame_start
    report_anim.start_time = frame_start_time
    report_anim.end_frame = frame_end
    report_anim.end_time = frame_end_time

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
    else: # else, check object's modifiers and get the first armature modifier that targets an armature that do have an NLA track
        armature_mods = [mod for mod in obj_to_bake.modifiers if mod.type == "ARMATURE"]
        for armature_mod in armature_mods:
            if (armature_mod.object and armature_mod.object.animation_data and armature_mod.object.animation_data.nla_tracks):
                return armature_mod.object.animation_data.nla_tracks

    return None

def get_obj_nla_start_end_frames(obj_to_bake: bpy.types.Object) -> list:
    """
    Return the list of the object's NLA strips start/end frames, or the armature's NLA strips it may be parented to
    
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
                unique_nla_strips.append((strip, objs_to_bake))

    return unique_nla_strips

def get_bake_apply_padding(context: bpy.types.Context, objs_to_bake: list) -> bool:
    """
    Examine if user asks for frame padding to be added and if it safe to do so (objects all share the same NLA clips)

    :objs_to_bake: objects included in the bake
    :return: True if frame padding should and can be applied
    :rtype: bool
    """

    settings = context.scene.VATBakerSettings

    return (settings.bake_mode == 'ANIMATION') and (settings.frame_range_mode == "NLA") and get_objs_nla_allow_padding(objs_to_bake) and (settings.frame_padding > 0) #and (settings.tex_packing_mode == "STACK")

############
### BAKE ###
def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object]:
    """
    Modify & ensure the active & selected objects can lead to a valid bake and return the list of objects to include in the bake.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of objects to bake (filtered selection), active object
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    if context.view_layer.objects.active == None:
        return (False, "No active object", None, None)

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
    This is only relevant for non mesh-sequence bakes.
    """
    if settings.bake_mode == 'ANIMATION':
        target_objs = []
        for selected_obj in context.selected_objects:
            target_obj = selected_obj.get(custom_prop, None)
            if target_obj and target_obj.type == "MESH":
                if target_obj not in target_objs:
                    target_objs.append(target_obj)
                else:
                    return (False, "Remapping multiple source objects to the same target is unsupported: " + selected_obj.name + " retargeted to " + target_obj.name + " which is already targeted", None, None)

        for target_obj in target_objs:
            target_obj.select_set(False)

    if not context.selected_objects:
        return (False, "No object selected once filtered out", None, None)
    
    """
    2b. this used to be a requirement for mapping source to target vertices, but no more thanks to barycentric coords computation no longer limited to
    triangles. This may still be relevant in case barycentric coords don't behave as expected on n-gons or weird geometries. This check ensures SOURCE
    & TARGET objects have a triangulate modifier at the top of their modifier stacks. This is of course only relevant for objects being retargeted!
    We might also allow a 'weak check', meaning allow SOURCE & TARGET objects *not* having a triangulate modifier as long as they all contain triangles
    to begin with. I consider this a 'weak check' because this doesn't account for modifiers and some modifiers might generate non-triangulate faces so
     checking the source mesh isn't bullet proof.
    """
    if settings.bake_mode == 'ANIMATION' and settings.require_triangulation:
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
                                    return (False, "Object " + selected_obj.name + " has a triangulate modifier but it isn't at the top of the modifier stack, which may lead to uncorrect retargeting with the mesh " + target_obj.name, None, None)
                    
                    if not selected_obj_meet_triangulated_cond:
                        return (False, "Object " + selected_obj.name + " has no triangulate modifier. Please add one at the top of its modifier stack to ensure correct retargeting with the mesh " + target_obj.name, None, None)

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
                                    return (False, "Object " + selected_obj.name + " has a target mesh " + target_obj.name + " that has a triangulate modifier that isn't at the top of the modifier stack. This may lead to uncorrect retargeting", None, None)

                    if not target_obj_meet_triangulated_cond:
                        return (False, "Object " + selected_obj.name + " has a target mesh " + target_obj.name + " that has no triangulate modifier. Please add one at the top of its modifier stack to ensure correct retargeting", None, None)

    """
    2c. cache selection
    """
    objs_to_bake = [] # cache selection
    if settings.bake_mode == 'ANIMATION':
        objs_to_bake = context.selected_objects
    else: # settings.bake_mode == 'MESHSEQUENCE'
        names_of_objects_to_bake = [obj.name for obj in context.selected_objects]
        names_of_objects_to_bake.sort() # sort selected objects by name to deduce 'frame order'

        for name in names_of_objects_to_bake:
            objs_to_bake.append(context.scene.objects[name])

    """
    3a. we'll need to create a UVMap to assign a texel per vertex so we need to ensure objects can be safely merged without creating UVMap conflicts.
    This involves gathering uvmaps of all selected objects to build a list of maps as if objects were joined and checking if the amount of uvmaps
    exceed the maximum amount in case we need to create one.
    """
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.VAT"
    if settings.bake_mode == 'ANIMATION':
        uvmaps = []

        for selected_obj in objs_to_bake:
            target_obj = selected_obj.get(custom_prop, None)
            uv_object = target_obj if target_obj and target_obj.type == "MESH" else selected_obj

            if mesh_uvmap_name not in [uvlayer.name for uvlayer in uv_object.data.uv_layers]: # can't find target UVMap?
                if len(uv_object.data.uv_layers) >= 8: # ensure UVMap can be created
                    return (False, uv_object.name + " has the maximum amount of uvmaps already", None, None)

            for uvlayer in uv_object.data.uv_layers: # gather uvmaps as if objects were joined
                if uvlayer.name not in uvmaps:
                    uvmaps.append(uvlayer.name)

        if mesh_uvmap_name not in uvmaps: # can't find target UVMap?
            if len(uvmaps) >= 8: # ensure UVMap can be created
                return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None)
    else: # settings.bake_mode == 'MESHSEQUENCE'
        if mesh_uvmap_name not in [uvlayer.name for uvlayer in objs_to_bake[0].data.uv_layers]: # can't find target UVMap?
            if len(objs_to_bake[0].data.uv_layers) >= 8: # ensure UVMap can be created
                return (False, objs_to_bake[0].name + " has the maximum amount of uvmaps already", None, None)

    """
    3b. if we're working with a mesh sequence, we need to ensure each mesh is actually the 'same' mesh, meaning at least check if vertex count is
    consistent once modifiers are applied. Vertex order will have to be assumed, I think.
    """
    if settings.bake_mode == 'MESHSEQUENCE':
        dgraph = context.evaluated_depsgraph_get()

        last_eval_mesh_vertex_count = 0
        for obj_index, obj_to_bake in enumerate(objs_to_bake):
            eval_obj = obj_to_bake.evaluated_get(dgraph)
            eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            eval_mesh_vertex_count = len(eval_mesh.vertices)
            
            if obj_index == 0:
                last_eval_mesh_vertex_count = eval_mesh_vertex_count
            elif last_eval_mesh_vertex_count != eval_mesh_vertex_count:
                eval_obj.to_mesh_clear()
                return (False, obj_to_bake.name + " has " + str(eval_mesh_vertex_count) + " vertices whereas " + str(last_eval_mesh_vertex_count) + " were last counted. Mesh sequence must have same vertex count & order", None, None)

            eval_obj.to_mesh_clear()

    """
    4. deselect everything
    """
    for obj_to_bake in objs_to_bake: # deselect objects for now
        obj_to_bake.select_set(False)

    active_obj = context.view_layer.objects.active # cache active object
    if settings.bake_mode == 'MESHSEQUENCE':
        active_obj = objs_to_bake[0]

    context.view_layer.objects.active = None # blank canvas

    return (True, "", objs_to_bake, active_obj)

def get_nla_strips_raw_frame_buffer(context: bpy.types.Context, nla_strips: list) -> list:
    """
    Compute a raw frame buffer from a list of NLA strips

    :param context: Blender current execution context
    :param nla_strips: list of NLA strips contributing to the overall animation 'range'
    """
    settings = context.scene.VATBakerSettings

    frames_to_bake = []
    frames_to_bake_indices = []
    frame_step = settings.frame_range_custom_step if settings.frame_range_custom_step_mode == "NLACLIP" and settings.frame_range_custom_step > 1 else 1

    # for each nla_strip, get its [start:end] range
    for nla_strip in nla_strips:
        strip, objs = nla_strip

        frame_start = int(strip.frame_start)
        frame_end = int(strip.frame_end)

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
    strip, objs = nla_strip

    start = int(strip.frame_start)
    end = int(strip.frame_end)

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

def get_bake_frames_animation(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, tuple[list, int, int]]:
    """
    Return the list of frames to bake and the start/end frames for a bake in 'animation' mode.

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
    :return: the function's success, potential error message, list of frames in order, bake start & end frames
    :rtype: tuple
    """
    settings = context.scene.VATBakerSettings

    nla_strips = get_bake_nla_strips(objs_to_bake)
    nla_strips = [nla_strip for nla_strip in nla_strips if nla_strip[0].name not in [nla_strip_excluded.name for nla_strip_excluded in settings.frame_range_nla_exclusion]] # exclude user-specified black-listed strips

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
                strip, objs = nla_strip

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
            for nla_strip in nla_strips:
                strip, objs = nla_strip

                start_index, end_index = get_nla_strip_start_end_indices(nla_strip, frames_to_bake)

                # 0-based indices are converted to the actual 1-based frame count
                start_frame = start_index + 1
                end_frame = end_index + 1
                start_time = (start_frame - 1) / num_frames
                end_time = end_frame / num_frames
                add_bake_report_anim(objs, strip.name, start_frame, end_frame, start_time, end_time)

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
        add_bake_report("num_frames_padded", num_frames)

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
                    strip, objs = nla_strip

                    start = int(strip.frame_start)
                    end = int(strip.frame_end)

                    # NLA strip start or end frame included in range?
                    if start <= frame_end or end >= frame_start:
                        frame_nla_strips.append(nla_strip)

                        # clamp start/end frames
                        start_frame = min(frame_end, max(frame_start, start))
                        end_frame = min(frame_end, max(frame_start, end))
                        start_time = (start_frame - 1) / num_frames
                        end_time = end_frame / num_frames
                        add_bake_report_anim(objs, strip.name, start_frame, end_frame, start_time, end_time)

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

        return (True, "", (frames_to_bake, start_frame, end_frame, ref_frame))

def get_bake_frames_sequence(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, tuple[list, int, int]]:
    """
    Return the list of frames to bake and the start/end frames for a bake in 'sequence' mode.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: the function's success, potential error message, list of frames in order, bake start & end frames
    :rtype: tuple
    """
    settings = context.scene.VATBakerSettings

    frames_to_bake = list(range(len(objs_to_bake))) # one frame per object
    add_bake_report("frame_step", 1)

    num_frames = len(frames_to_bake)
    add_bake_report("num_frames", num_frames)

    if num_frames < 2:
        return (False, str(num_frames) + " frames detected: too few frames to bake or no animation data found from NLA track(s)", (frames_to_bake, 0, 0, 0))

    start_frame = min(frames_to_bake)
    add_bake_report("start_frame", start_frame)

    end_frame = max(frames_to_bake)
    add_bake_report("end_frame", end_frame)

    # no padding in sequence mode
    add_bake_report("padded", False)
    add_bake_report("padding", 0)
    add_bake_report("padding_mode", "SUFFIX")

    """
    add reference frame
    """
    ref_frame = start_frame
    if settings.frame_ref_mode == "END":
        ref_frame = end_frame
    elif settings.frame_ref_mode == "CUSTOM":
        ref_frame = settings.frame_ref_custom
    
    return (True, "", (frames_to_bake, start_frame, end_frame, ref_frame))

def get_bake_frames(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, tuple[list, int, int]]:
    """
    Return the list of frames to bake and the start/end frames.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: the function's success, potential error message, list of frames in order, bake start & end frames
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings

    add_bake_report("frame_rate", (context.scene.render.fps / context.scene.render.fps_base))

    if settings.bake_mode == "ANIMATION":
        return get_bake_frames_animation(context, objs_to_bake)
    else: # sequence
        return get_bake_frames_sequence(context, objs_to_bake)

def get_bake_vertices(context: bpy.types.Context, objs_to_bake: list) -> int:
    """
    Return the amount of vertices to bake in total, for one frame. This depends on the amount of selected object and their modifier(s)

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: number of vertices
    :rtype: int
    """

    settings = context.scene.VATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    dgraph = context.evaluated_depsgraph_get()

    """
    Gather vertex count for objects to bake. This has to account for modifiers and multiple selection and potential retargeted objects in
    case we're baking an 'animation'. Else, if we're working from a mesh sequence, we only care about the first object in the sequence.
    """
    num_vertices = 0
    if settings.bake_mode == 'ANIMATION':
        for selected_obj in objs_to_bake:
            target_obj = selected_obj.get(custom_prop, None)
            obj = target_obj if target_obj and target_obj.type == "MESH" else selected_obj

            eval_obj = obj.evaluated_get(dgraph)
            eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            num_vertices += len(eval_mesh.vertices)
            eval_obj.to_mesh_clear()
    else:
        eval_obj = objs_to_bake[0].evaluated_get(dgraph)
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

    settings = context.scene.VATBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.VAT"
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

    settings = context.scene.VATBakerSettings
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

    success, msg, bake_frames_info = get_bake_frames(context, objs_to_bake)
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(3)

    num_frames = len(frames_to_bake)
    num_objs = len(objs_to_bake)
    num_verts = get_bake_vertices(context, objs_to_bake)
    add_bake_report("num_verts", num_verts)

    success, msg, tex_width, tex_height, bake_frame_height, bake_frame_width = get_best_texture_resolution(context, num_frames, num_verts)
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

    if settings.bake_mode == 'ANIMATION':
        success, msg, vertices_offsets, vertices_normals, bounds_info = get_animation_vertices_buffers(context, objs_to_bake, bake_frames_info, bake_frame_height, tex_width, tex_height, num_verts)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)

    else: # settings.bake_mode == 'MESHSEQUENCE'
        success, msg, vertices_offsets, vertices_normals, bounds_info = get_sequence_vertices_buffers(context, objs_to_bake, bake_frames_info, bake_frame_height, tex_width, tex_height, num_verts)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)

    if settings.normal_tex_remap:
        vertices_normals, buffer_range_info = get_remapped_vertices_normal_buffer(vertices_normals, settings.normal_tex_remap_biasscale)
        buffer_range_offset, buffer_range_valid, buffer_range = buffer_range_info
        add_bake_report("tex_normal_remapped", True)
        add_bake_report("tex_normal_range_offset", buffer_range_offset)
        add_bake_report("tex_normal_range", buffer_range)

    if settings.offset_tex_remap:
        vertices_offsets, buffer_range_info = get_remapped_vertices_offset_buffer(vertices_offsets)
        buffer_range_offset, buffer_range_valid, buffer_range = buffer_range_info
        add_bake_report("tex_offset_remapped", True)
        add_bake_report("tex_offset_range_offset", buffer_range_offset)
        add_bake_report("tex_offset_range", buffer_range)

    if settings.unit_invert_v:
        vertices_offsets, vertices_normals = get_inverted_buffers(vertices_offsets, vertices_normals, tex_width, tex_height)

    wm.progress_update(92)

    ############
    # TEXTURES #

    img_offset = None
    if settings.offset_tex:
        success, msg, img_offset = generate_texture(bake_name, settings.offset_tex_file_name, vertices_offsets, tex_width, tex_height)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("tex_offset", img_offset)
        add_bake_report("tex_offset_mode", settings.offset_tex_mode)

        img_offset_path = ""
        if settings.export_tex and bpy.data.is_saved:
            success, msg, img_offset_path = export_texture(context, img_offset, settings.export_tex_file_path, settings.offset_tex_file_name, bake_name, settings.export_tex_override)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            add_bake_report("tex_offset_export", True)
            add_bake_report("tex_offset_path", img_offset_path)

    image_nor = None
    if settings.normal_tex:
        success, msg, image_nor = generate_texture(bake_name, settings.normal_tex_file_name, vertices_normals, tex_width, tex_height)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("tex_normal", image_nor)

        image_nor_path = ""
        if settings.export_tex and bpy.data.is_saved:
            success, msg, image_nor_path = export_texture(context, image_nor, settings.export_tex_file_path, settings.normal_tex_file_name, bake_name, settings.export_tex_override)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            add_bake_report("tex_normal_export", True)
            add_bake_report("tex_normal_path", image_nor_path)

    wm.progress_update(94)

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

    if settings.previz_result and (img_offset or image_nor):
        success, msg = generate_mesh_geonodes(context, obj_to_export, num_verts, tex_width, bake_frames_info, bake_frame_height, bounds_info, img_offset, image_nor)

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
def generate_mesh(context: bpy.types.Context, bake_name: str, objs_to_bake: list, tex_width: int, tex_height: int, bake_frame_ref: int, num_frames: int) -> tuple[bool, str, bpy.types.Object, int]:
    """
    Generate the mesh object to export

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :param objs_to_bake: List of objects to bake
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :param bake_frame_ref: Frame considered as the 'reference frame', or 'base pos'
    :return: success, message, generated object, UVMap used to map the VAT texture(s)
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"

    if settings.bake_mode == "ANIMATION":
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
        if settings.bake_mode == "ANIMATION":
            for obj_to_bake in objs_to_bake:
                for material in obj_to_bake.data.materials:
                    if material not in materials:
                        materials.append(material)
        else: # settings.bake_mode == "MESHSEQUENCE"
            for material in objs_to_bake[0].data.materials:
                if material not in materials:
                    materials.append(material)

    """
    In case of baking an 'animation', we need to duplicate all selected objects in their base pos
    and account for their modifier(s) as well. We can't join them yet because we need to process
    their UVs uniquely per mesh. Else, in case of working from a sequence of meshes, we only care
    about the first mesh (aka the base pose mesh).
    """
    if settings.bake_mode == "ANIMATION":
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

            success, msg, last_eval_mesh_uvmap_index = generate_mesh_uvs(context, eval_mesh, tex_width, tex_height, eval_meshes_vertices, num_frames)
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
    else: # settings.bake_mode == "MESHSEQUENCE"
        eval_obj = objs_to_bake[0].evaluated_get(dgraph)
        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph).copy()
        eval_obj.to_mesh_clear()
        eval_mesh.transform(eval_obj.matrix_world)

        success, msg, eval_mesh_uvmap_index = generate_mesh_uvs(context, eval_mesh, tex_width, tex_height, 0, num_frames)
        if not success:
            if eval_mesh.users == 0:
                bpy.data.meshes.remove(eval_mesh)
            return (False, msg, None, -1)
        
        # we only really need the first mesh when using mesh sequence
        eval_meshes.append(eval_mesh)

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
    name = bake_name if bake_name != "" else "BakedMesh.VAT"
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

def generate_mesh_uvs(context: bpy.types.Context, mesh: bpy.types.Mesh, tex_width: int, tex_height: int, vertex_index_offset: int, num_frames: int) -> tuple[bool, str, int]:
    """
    Configure the mesh UVs so that one vertex is located on one unique texel in the VAT texture(s)

    :param context: Blender current execution context
    :param mesh: mesh to edit
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :param vertex_index_offset: Used to uniquely process a selection of meshes
    :return: the function's success, potential error message, index of UVMap used to map the VAT texture(s)
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings

    uvmap = None
    uvmap_index = 0
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.VAT"

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
            vertex_index = loop.vertex_index + vertex_index_offset
            u = (0.5 / float(tex_width)) + (vertex_index % tex_width) / float(tex_width)
            v = (0.5 / float(tex_height)) + (vertex_index // float(tex_width)) / float(tex_height)
            if settings.unit_invert_v:
                v = 1.0 - v

            uvmap.data[loop.index].uv = (u,v)
    else: # STACK & OFFSET
        # set UV
        for loop in mesh.loops:
            vertex_index = loop.vertex_index + vertex_index_offset
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

    settings = context.scene.VATBakerSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

#################
### GEO NODES ###
def generate_mesh_geonodes(context: bpy.types.Context, obj_to_export: bpy.types.Object, num_vertices: int, tex_width: int, bake_frames_info: tuple[list, int, int], bake_frame_height: int, bounds_info: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector], img_offset: bpy.types.Image, img_nor: bpy.types.Image) -> tuple[bool, str]:
    """
    Apply a geometry node modifier to the given object. The required geometry node group either already exist from a previous call and is thus assigned to the modifier or is generated to previsualize the baked VAT texture(s)

    :param context: Blender current execution context
    :param obj_to_export: object to edit
    :param num_vertices: number of vertices to bake per frame
    :param tex_width: VAT texture(s) width
    :param bake_frames_info: frames to bake
    :param bake_frame_height: Amount of lines of pixels per frame
    :param img_offset: VAT texture that stores vertex offset data
    :param img_nor: VAT texture that stores vertex normal data
    :return: the function's success, potential error message
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings

    use_row = (num_vertices == tex_width) or (settings.tex_packing_mode == 'STACK')
    if use_row:
        generate_mesh_geonodes_row(context, obj_to_export, bake_frames_info, bake_frame_height, bounds_info, img_offset, img_nor)
    else:
        generate_mesh_geonodes_partialrow(context, obj_to_export, bake_frames_info, num_vertices / tex_width, bounds_info, img_offset, img_nor)

    return (True, "")

def generate_mesh_geonodes_row(context: bpy.types.Context, obj_to_export: bpy.types.Object, bake_frames_info: tuple[list, int, int], bake_frame_height: int, bounds_info: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector], img_offset: bpy.types.Image, img_nor: bpy.types.Image):
    """
    Apply a geometry node modifier to the given object. The required geometry node group either already exists from a previous call and is thus assigned to the modifier or is generated to previsualize the baked VAT texture(s) using a simple V offset to playback the animation

    :param context: Blender current execution context
    :param obj_to_export: object to edit
    :param bake_frames_info: frames to bake
    :param bake_frame_height: amount of lines of pixels per frame
    :param bounds_info: animation bounds to derive maximum offset
    :param img_offset: VAT texture that stores vertex offset data
    :param img_nor: VAT texture that stores vertex normal data
    :return: None
    :rtype: None
    """

    settings = context.scene.VATBakerSettings

    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset = bounds_info
    max_offset = mathutils.Vector((max(abs(min_bounds.x), abs(max_bounds.x)),
                                  max(abs(min_bounds.y), abs(max_bounds.y)),
                                  max(abs(min_bounds.z), abs(max_bounds.z))))

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "VAT_Row":
            geonode_tree = node_group
            break

    if geonode_tree is None:
        geonode_tree = build_mesh_geonodes_row_group()

    geonode_mod = obj_to_export.modifiers.get("GeometryNodes", None)
    if geonode_mod is None:
        geonode_mod = obj_to_export.modifiers.new(name="GeometryNodes", type='NODES')

    geonode_mod.node_group = geonode_tree

    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetTex"].identifier] = img_offset
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetScale"].identifier] = settings.unit_scale
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetRemap"].identifier] = max_offset if settings.offset_tex_remap else mathutils.Vector((1.0, 1.0, 1.0))
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetRemapped"].identifier] = settings.offset_tex_remap
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetMode"].identifier] = settings.offset_tex_mode == "OFFSET"
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["NormalTex"].identifier] = img_nor
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["NormalScale"].identifier] = 1
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["NormalRemapped"].identifier] = settings.normal_tex_remap
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Normal"].identifier] = True if img_nor else False
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["FrameHeight"].identifier] = bake_frame_height
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["FrameOffset"].identifier] = bake_start_frame
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["UVMap"].identifier] = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.VAT"
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertV"].identifier] = settings.unit_invert_v
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertX"].identifier] = settings.unit_invert_x
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertY"].identifier] = settings.unit_invert_y
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertZ"].identifier] = settings.unit_invert_z

def generate_mesh_geonodes_partialrow(context: bpy.types.Context, obj_to_export: bpy.types.Object, bake_frames_info: tuple[list, int, int], frame_step: float, bounds_info: tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector], img_offset: bpy.types.Image, img_nor: bpy.types.Image):
    """
    Apply a geometry node modifier to the given object. The required geometry node group either already exist from a previous call and is thus assigned to the modifier or is generated to previsualize the baked VAT texture(s) using a complex U & V offset to playback the animation

    :param context: Blender current execution context
    :param obj_to_export: object to edit
    :param bake_frames_info: frames to bake
    :param frame_step: amount of V axis to offset per frame
    :param img_offset: VAT texture that stores vertex offset data
    :param img_nor: VAT texture that stores vertex normal data
    :return: None
    :rtype: None
    """

    settings = context.scene.VATBakerSettings

    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info
    ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset= bounds_info
    max_offset = mathutils.Vector((max(abs(min_bounds.x), abs(max_bounds.x)),
                                  max(abs(min_bounds.y), abs(max_bounds.y)),
                                  max(abs(min_bounds.z), abs(max_bounds.z))))

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "VAT_PartialRow":
            geonode_tree = node_group
            geonode_tree.is_modifier = True
            break

    if geonode_tree is None:
        geonode_tree = build_mesh_geonodes_partialrow_group()

    geonode_mod = obj_to_export.modifiers.get("GeometryNodes", None)
    if geonode_mod is None:
        geonode_mod = obj_to_export.modifiers.new(name="GeometryNodes", type='NODES')

    geonode_mod.node_group = geonode_tree

    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetTex"].identifier] = img_offset
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetScale"].identifier] = settings.unit_scale
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetRemap"].identifier] = max_offset if settings.offset_tex_remap else mathutils.Vector((1.0, 1.0, 1.0))
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetRemapped"].identifier] = settings.offset_tex_remap
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["OffsetMode"].identifier] = settings.offset_tex_mode == "OFFSET"
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["NormalTex"].identifier] = img_nor
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["NormalScale"].identifier] = 1
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["NormalRemapped"].identifier] = settings.normal_tex_remap
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Normal"].identifier] = True if img_nor else False
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Frames"].identifier] = len(frames_to_bake)
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["FrameStep"].identifier] = frame_step
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["FrameOffset"].identifier] = bake_start_frame
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["UVMap"].identifier] = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.VAT"
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertV"].identifier] = settings.unit_invert_v
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertX"].identifier] = settings.unit_invert_x
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertY"].identifier] = settings.unit_invert_y
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["InvertZ"].identifier] = settings.unit_invert_z

def build_mesh_geonodes_row_group():
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    vat_row = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "VAT_Row")

    vat_row.color_tag = 'NONE'
    vat_row.description = ""
    vat_row.default_group_node_width = 140
    

    vat_row.is_modifier = True

    #vat_row interface
    #Socket Geometry
    geometry_socket = vat_row.interface.new_socket(name = "Geometry", in_out='OUTPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'

    #Socket Geometry
    geometry_socket_1 = vat_row.interface.new_socket(name = "Geometry", in_out='INPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket_1.attribute_domain = 'POINT'

    #Panel Offset
    offset_panel = vat_row.interface.new_panel("Offset")
    #Socket OffsetTex
    offsettex_socket = vat_row.interface.new_socket(name = "OffsetTex", in_out='INPUT', socket_type = 'NodeSocketImage', parent = offset_panel)
    offsettex_socket.attribute_domain = 'POINT'

    #Socket OffsetScale
    offsetscale_socket = vat_row.interface.new_socket(name = "OffsetScale", in_out='INPUT', socket_type = 'NodeSocketFloat', parent = offset_panel)
    offsetscale_socket.default_value = 100.0
    offsetscale_socket.min_value = -3.4028234663852886e+38
    offsetscale_socket.max_value = 3.4028234663852886e+38
    offsetscale_socket.subtype = 'NONE'
    offsetscale_socket.attribute_domain = 'POINT'

    #Socket OffsetRemap
    offsetremap_socket = vat_row.interface.new_socket(name = "OffsetRemap", in_out='INPUT', socket_type = 'NodeSocketVector', parent = offset_panel)
    offsetremap_socket.default_value = (1.0, 1.0, 1.0)
    offsetremap_socket.min_value = -3.4028234663852886e+38
    offsetremap_socket.max_value = 3.4028234663852886e+38
    offsetremap_socket.subtype = 'NONE'
    offsetremap_socket.attribute_domain = 'POINT'

    #Socket OffsetRemapped
    offsetremapped_socket = vat_row.interface.new_socket(name = "OffsetRemapped", in_out='INPUT', socket_type = 'NodeSocketBool', parent = offset_panel)
    offsetremapped_socket.default_value = False
    offsetremapped_socket.attribute_domain = 'POINT'

    #Socket OffsetMode
    offsetmode_socket = vat_row.interface.new_socket(name = "OffsetMode", in_out='INPUT', socket_type = 'NodeSocketBool', parent = offset_panel)
    offsetmode_socket.default_value = True
    offsetmode_socket.attribute_domain = 'POINT'
    offsetmode_socket.description = "True if Offset, False if Position"


    #Panel Normal
    normal_panel = vat_row.interface.new_panel("Normal")
    #Socket NormalTex
    normaltex_socket = vat_row.interface.new_socket(name = "NormalTex", in_out='INPUT', socket_type = 'NodeSocketImage', parent = normal_panel)
    normaltex_socket.attribute_domain = 'POINT'

    #Socket NormalScale
    normalscale_socket = vat_row.interface.new_socket(name = "NormalScale", in_out='INPUT', socket_type = 'NodeSocketFloat', parent = normal_panel)
    normalscale_socket.default_value = 1.0
    normalscale_socket.min_value = -3.4028234663852886e+38
    normalscale_socket.max_value = 3.4028234663852886e+38
    normalscale_socket.subtype = 'NONE'
    normalscale_socket.attribute_domain = 'POINT'

    #Socket Normal
    normal_socket = vat_row.interface.new_socket(name = "Normal", in_out='INPUT', socket_type = 'NodeSocketBool', parent = normal_panel)
    normal_socket.default_value = True
    normal_socket.attribute_domain = 'POINT'

    #Socket NormalRemapped
    normalremapped_socket = vat_row.interface.new_socket(name = "NormalRemapped", in_out='INPUT', socket_type = 'NodeSocketBool', parent = normal_panel)
    normalremapped_socket.default_value = True
    normalremapped_socket.attribute_domain = 'POINT'


    #Panel Frames
    frames_panel = vat_row.interface.new_panel("Frames")
    #Socket FrameHeight
    frameheight_socket = vat_row.interface.new_socket(name = "FrameHeight", in_out='INPUT', socket_type = 'NodeSocketFloat', parent = frames_panel)
    frameheight_socket.default_value = 1.0
    frameheight_socket.min_value = -3.4028234663852886e+38
    frameheight_socket.max_value = 3.4028234663852886e+38
    frameheight_socket.subtype = 'NONE'
    frameheight_socket.attribute_domain = 'POINT'

    #Socket FrameOffset
    frameoffset_socket = vat_row.interface.new_socket(name = "FrameOffset", in_out='INPUT', socket_type = 'NodeSocketInt', parent = frames_panel)
    frameoffset_socket.default_value = 0
    frameoffset_socket.min_value = -2147483648
    frameoffset_socket.max_value = 2147483647
    frameoffset_socket.subtype = 'NONE'
    frameoffset_socket.attribute_domain = 'POINT'


    #Panel UV
    uv_panel = vat_row.interface.new_panel("UV")
    #Socket UVMap
    uvmap_socket = vat_row.interface.new_socket(name = "UVMap", in_out='INPUT', socket_type = 'NodeSocketString', parent = uv_panel)
    uvmap_socket.default_value = "UVMap.BakedData.VAT"
    uvmap_socket.subtype = 'NONE'
    uvmap_socket.attribute_domain = 'POINT'

    #Socket InvertV
    invertv_socket = vat_row.interface.new_socket(name = "InvertV", in_out='INPUT', socket_type = 'NodeSocketBool', parent = uv_panel)
    invertv_socket.default_value = True
    invertv_socket.attribute_domain = 'POINT'


    #Panel Invert
    invert_panel = vat_row.interface.new_panel("Invert")
    #Socket InvertX
    invertx_socket = vat_row.interface.new_socket(name = "InvertX", in_out='INPUT', socket_type = 'NodeSocketBool', parent = invert_panel)
    invertx_socket.default_value = False
    invertx_socket.attribute_domain = 'POINT'

    #Socket InvertY
    inverty_socket = vat_row.interface.new_socket(name = "InvertY", in_out='INPUT', socket_type = 'NodeSocketBool', parent = invert_panel)
    inverty_socket.default_value = True
    inverty_socket.attribute_domain = 'POINT'

    #Socket InvertZ
    invertz_socket = vat_row.interface.new_socket(name = "InvertZ", in_out='INPUT', socket_type = 'NodeSocketBool', parent = invert_panel)
    invertz_socket.default_value = False
    invertz_socket.attribute_domain = 'POINT'



    #initialize vat_row nodes
    #node Group Input
    group_input = vat_row.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    #node Group Output
    group_output = vat_row.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    #node Named Attribute
    named_attribute = vat_row.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute.name = "Named Attribute"
    named_attribute.data_type = 'FLOAT_VECTOR'

    #node Separate XYZ
    separate_xyz = vat_row.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.name = "Separate XYZ"

    #node Math
    math = vat_row.nodes.new("ShaderNodeMath")
    math.name = "Math"
    math.operation = 'SUBTRACT'
    math.use_clamp = False

    #node Scene Time
    scene_time = vat_row.nodes.new("GeometryNodeInputSceneTime")
    scene_time.name = "Scene Time"

    #node Math.001
    math_001 = vat_row.nodes.new("ShaderNodeMath")
    math_001.name = "Math.001"
    math_001.operation = 'DIVIDE'
    math_001.use_clamp = False

    #node Math.002
    math_002 = vat_row.nodes.new("ShaderNodeMath")
    math_002.name = "Math.002"
    math_002.operation = 'ADD'
    math_002.use_clamp = False

    #node Math.003
    math_003 = vat_row.nodes.new("ShaderNodeMath")
    math_003.name = "Math.003"
    math_003.operation = 'SUBTRACT'
    math_003.use_clamp = False

    #node Switch
    switch = vat_row.nodes.new("GeometryNodeSwitch")
    switch.name = "Switch"
    switch.input_type = 'FLOAT'

    #node Combine XYZ
    combine_xyz = vat_row.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.name = "Combine XYZ"
    #Z
    combine_xyz.inputs[2].default_value = 0.0

    #node Image Texture.001
    image_texture_001 = vat_row.nodes.new("GeometryNodeImageTexture")
    image_texture_001.name = "Image Texture.001"
    image_texture_001.extension = 'REPEAT'
    image_texture_001.interpolation = 'Closest'
    #Frame
    image_texture_001.inputs[2].default_value = 0

    #node Image Info
    image_info = vat_row.nodes.new("GeometryNodeImageInfo")
    image_info.name = "Image Info"
    #Frame
    image_info.inputs[1].default_value = 0

    #node Math.004
    math_004 = vat_row.nodes.new("ShaderNodeMath")
    math_004.name = "Math.004"
    math_004.operation = 'DIVIDE'
    math_004.use_clamp = False

    #node Math.005
    math_005 = vat_row.nodes.new("ShaderNodeMath")
    math_005.name = "Math.005"
    math_005.operation = 'DIVIDE'
    math_005.use_clamp = False

    #node Math.006
    math_006 = vat_row.nodes.new("ShaderNodeMath")
    math_006.name = "Math.006"
    math_006.operation = 'ADD'
    math_006.use_clamp = False

    #node Math.007
    math_007 = vat_row.nodes.new("ShaderNodeMath")
    math_007.name = "Math.007"
    math_007.operation = 'SUBTRACT'
    math_007.use_clamp = False

    #node Switch.001
    switch_001 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_001.name = "Switch.001"
    switch_001.input_type = 'FLOAT'

    #node Combine XYZ.001
    combine_xyz_001 = vat_row.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_001.name = "Combine XYZ.001"
    #Z
    combine_xyz_001.inputs[2].default_value = 0.0

    #node Image Info.001
    image_info_001 = vat_row.nodes.new("GeometryNodeImageInfo")
    image_info_001.name = "Image Info.001"
    #Frame
    image_info_001.inputs[1].default_value = 0

    #node Math.008
    math_008 = vat_row.nodes.new("ShaderNodeMath")
    math_008.name = "Math.008"
    math_008.operation = 'DIVIDE'
    math_008.use_clamp = False

    #node Image Texture.002
    image_texture_002 = vat_row.nodes.new("GeometryNodeImageTexture")
    image_texture_002.name = "Image Texture.002"
    image_texture_002.extension = 'REPEAT'
    image_texture_002.interpolation = 'Closest'
    #Frame
    image_texture_002.inputs[2].default_value = 0

    #node Switch.002
    switch_002 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_002.name = "Switch.002"
    switch_002.input_type = 'FLOAT'
    #False
    switch_002.inputs[1].default_value = 1.0
    #True
    switch_002.inputs[2].default_value = -1.0

    #node Switch.003
    switch_003 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_003.name = "Switch.003"
    switch_003.input_type = 'FLOAT'
    #False
    switch_003.inputs[1].default_value = 1.0
    #True
    switch_003.inputs[2].default_value = -1.0

    #node Switch.004
    switch_004 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_004.name = "Switch.004"
    switch_004.input_type = 'FLOAT'
    #False
    switch_004.inputs[1].default_value = 1.0
    #True
    switch_004.inputs[2].default_value = -1.0

    #node Combine XYZ.002
    combine_xyz_002 = vat_row.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_002.name = "Combine XYZ.002"

    #node Vector Math
    vector_math = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math.name = "Vector Math"
    vector_math.operation = 'DIVIDE'

    #node Vector Math.001
    vector_math_001 = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math_001.name = "Vector Math.001"
    vector_math_001.operation = 'MULTIPLY'

    #node Vector Math.003
    vector_math_003 = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math_003.name = "Vector Math.003"
    vector_math_003.operation = 'MULTIPLY'

    #node Set Position
    set_position = vat_row.nodes.new("GeometryNodeSetPosition")
    set_position.name = "Set Position"
    #Selection
    set_position.inputs[1].default_value = True
    #Position
    set_position.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Join Geometry
    join_geometry = vat_row.nodes.new("GeometryNodeJoinGeometry")
    join_geometry.name = "Join Geometry"

    #node Switch.005
    switch_005 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_005.name = "Switch.005"
    switch_005.input_type = 'GEOMETRY'

    #node Domain Size
    domain_size = vat_row.nodes.new("GeometryNodeAttributeDomainSize")
    domain_size.name = "Domain Size"
    domain_size.component = 'MESH'

    #node Index
    index = vat_row.nodes.new("GeometryNodeInputIndex")
    index.name = "Index"

    #node Position
    position = vat_row.nodes.new("GeometryNodeInputPosition")
    position.name = "Position"

    #node Sample Index
    sample_index = vat_row.nodes.new("GeometryNodeSampleIndex")
    sample_index.name = "Sample Index"
    sample_index.clamp = False
    sample_index.data_type = 'FLOAT_VECTOR'
    sample_index.domain = 'POINT'

    #node Sample Index.001
    sample_index_001 = vat_row.nodes.new("GeometryNodeSampleIndex")
    sample_index_001.name = "Sample Index.001"
    sample_index_001.clamp = False
    sample_index_001.data_type = 'FLOAT_VECTOR'
    sample_index_001.domain = 'POINT'

    #node Points
    points = vat_row.nodes.new("GeometryNodePoints")
    points.name = "Points"
    #Radius
    points.inputs[2].default_value = 0.10000000149011612

    #node Capture Attribute
    capture_attribute = vat_row.nodes.new("GeometryNodeCaptureAttribute")
    capture_attribute.name = "Capture Attribute"
    capture_attribute.active_index = 0
    capture_attribute.capture_items.clear()
    capture_attribute.capture_items.new('FLOAT', "Value")
    capture_attribute.capture_items["Value"].data_type = 'FLOAT_VECTOR'
    capture_attribute.domain = 'POINT'

    #node Instance on Points
    instance_on_points = vat_row.nodes.new("GeometryNodeInstanceOnPoints")
    instance_on_points.name = "Instance on Points"
    #Selection
    instance_on_points.inputs[1].default_value = True
    #Pick Instance
    instance_on_points.inputs[3].default_value = False
    #Instance Index
    instance_on_points.inputs[4].default_value = 0
    #Rotation
    instance_on_points.inputs[5].default_value = (0.0, 0.0, 0.0)
    #Scale
    instance_on_points.inputs[6].default_value = (1.0, 1.0, 1.0)

    #node Curve Line
    curve_line = vat_row.nodes.new("GeometryNodeCurvePrimitiveLine")
    curve_line.name = "Curve Line"
    curve_line.mode = 'POINTS'
    #Start
    curve_line.inputs[0].default_value = (0.0, 0.0, 0.0)
    #End
    curve_line.inputs[1].default_value = (0.0, 0.0, 0.0)

    #node Realize Instances
    realize_instances = vat_row.nodes.new("GeometryNodeRealizeInstances")
    realize_instances.name = "Realize Instances"
    #Selection
    realize_instances.inputs[1].default_value = True
    #Realize All
    realize_instances.inputs[2].default_value = True
    #Depth
    realize_instances.inputs[3].default_value = 0

    #node Store Named Attribute
    store_named_attribute = vat_row.nodes.new("GeometryNodeStoreNamedAttribute")
    store_named_attribute.name = "Store Named Attribute"
    store_named_attribute.data_type = 'FLOAT_VECTOR'
    store_named_attribute.domain = 'POINT'
    #Selection
    store_named_attribute.inputs[1].default_value = True

    #node Set Position.001
    set_position_001 = vat_row.nodes.new("GeometryNodeSetPosition")
    set_position_001.name = "Set Position.001"
    #Position
    set_position_001.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Set Position.002
    set_position_002 = vat_row.nodes.new("GeometryNodeSetPosition")
    set_position_002.name = "Set Position.002"
    #Selection
    set_position_002.inputs[1].default_value = True
    #Position
    set_position_002.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Endpoint Selection
    endpoint_selection = vat_row.nodes.new("GeometryNodeCurveEndpointSelection")
    endpoint_selection.name = "Endpoint Selection"
    #Start Size
    endpoint_selection.inputs[0].default_value = 0
    #End Size
    endpoint_selection.inputs[1].default_value = 1

    #node Vector Math.004
    vector_math_004 = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math_004.name = "Vector Math.004"
    vector_math_004.operation = 'MULTIPLY'

    #node Vector Math.005
    vector_math_005 = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math_005.name = "Vector Math.005"
    vector_math_005.operation = 'MULTIPLY_ADD'
    #Vector_001
    vector_math_005.inputs[1].default_value = (2.0, 2.0, 2.0)
    #Vector_002
    vector_math_005.inputs[2].default_value = (-1.0, -1.0, -1.0)

    #node Switch.006
    switch_006 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_006.name = "Switch.006"
    switch_006.input_type = 'VECTOR'

    #node Reroute
    reroute = vat_row.nodes.new("NodeReroute")
    reroute.name = "Reroute"
    reroute.socket_idname = "NodeSocketBool"
    #node Reroute.001
    reroute_001 = vat_row.nodes.new("NodeReroute")
    reroute_001.name = "Reroute.001"
    reroute_001.socket_idname = "NodeSocketBool"
    #node Reroute.002
    reroute_002 = vat_row.nodes.new("NodeReroute")
    reroute_002.name = "Reroute.002"
    reroute_002.socket_idname = "NodeSocketBool"
    #node Reroute.003
    reroute_003 = vat_row.nodes.new("NodeReroute")
    reroute_003.name = "Reroute.003"
    reroute_003.socket_idname = "NodeSocketVector"
    #node Reroute.004
    reroute_004 = vat_row.nodes.new("NodeReroute")
    reroute_004.name = "Reroute.004"
    reroute_004.socket_idname = "NodeSocketFloat"
    #node Reroute.005
    reroute_005 = vat_row.nodes.new("NodeReroute")
    reroute_005.name = "Reroute.005"
    reroute_005.socket_idname = "NodeSocketFloat"
    #node Reroute.006
    reroute_006 = vat_row.nodes.new("NodeReroute")
    reroute_006.name = "Reroute.006"
    reroute_006.socket_idname = "NodeSocketInt"
    #node Reroute.007
    reroute_007 = vat_row.nodes.new("NodeReroute")
    reroute_007.name = "Reroute.007"
    reroute_007.socket_idname = "NodeSocketBool"
    #node Reroute.008
    reroute_008 = vat_row.nodes.new("NodeReroute")
    reroute_008.name = "Reroute.008"
    reroute_008.socket_idname = "NodeSocketFloat"
    #node Reroute.009
    reroute_009 = vat_row.nodes.new("NodeReroute")
    reroute_009.name = "Reroute.009"
    reroute_009.socket_idname = "NodeSocketBool"
    #node Reroute.010
    reroute_010 = vat_row.nodes.new("NodeReroute")
    reroute_010.name = "Reroute.010"
    reroute_010.socket_idname = "NodeSocketString"
    #node Reroute.011
    reroute_011 = vat_row.nodes.new("NodeReroute")
    reroute_011.name = "Reroute.011"
    reroute_011.socket_idname = "NodeSocketImage"
    #node Reroute.012
    reroute_012 = vat_row.nodes.new("NodeReroute")
    reroute_012.name = "Reroute.012"
    reroute_012.socket_idname = "NodeSocketImage"
    #node Vector Math.006
    vector_math_006 = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math_006.name = "Vector Math.006"
    vector_math_006.operation = 'MULTIPLY'

    #node Reroute.013
    reroute_013 = vat_row.nodes.new("NodeReroute")
    reroute_013.name = "Reroute.013"
    reroute_013.socket_idname = "NodeSocketGeometry"
    #node Reroute.014
    reroute_014 = vat_row.nodes.new("NodeReroute")
    reroute_014.name = "Reroute.014"
    reroute_014.socket_idname = "NodeSocketVector"
    #node Reroute.015
    reroute_015 = vat_row.nodes.new("NodeReroute")
    reroute_015.name = "Reroute.015"
    reroute_015.socket_idname = "NodeSocketString"
    #node Reroute.016
    reroute_016 = vat_row.nodes.new("NodeReroute")
    reroute_016.name = "Reroute.016"
    reroute_016.socket_idname = "NodeSocketColor"
    #node Reroute.017
    reroute_017 = vat_row.nodes.new("NodeReroute")
    reroute_017.name = "Reroute.017"
    reroute_017.socket_idname = "NodeSocketVector"
    #node Reroute.018
    reroute_018 = vat_row.nodes.new("NodeReroute")
    reroute_018.name = "Reroute.018"
    reroute_018.socket_idname = "NodeSocketFloat"
    #node Reroute.019
    reroute_019 = vat_row.nodes.new("NodeReroute")
    reroute_019.name = "Reroute.019"
    reroute_019.socket_idname = "NodeSocketFloat"
    #node Reroute.020
    reroute_020 = vat_row.nodes.new("NodeReroute")
    reroute_020.name = "Reroute.020"
    reroute_020.socket_idname = "NodeSocketBool"
    #node Reroute.021
    reroute_021 = vat_row.nodes.new("NodeReroute")
    reroute_021.name = "Reroute.021"
    reroute_021.socket_idname = "NodeSocketGeometry"
    #node Reroute.022
    reroute_022 = vat_row.nodes.new("NodeReroute")
    reroute_022.name = "Reroute.022"
    reroute_022.socket_idname = "NodeSocketGeometry"
    #node Vector Math.007
    vector_math_007 = vat_row.nodes.new("ShaderNodeVectorMath")
    vector_math_007.name = "Vector Math.007"
    vector_math_007.operation = 'MULTIPLY_ADD'
    #Vector_001
    vector_math_007.inputs[1].default_value = (2.0, 2.0, 2.0)
    #Vector_002
    vector_math_007.inputs[2].default_value = (-1.0, -1.0, -1.0)

    #node Switch.007
    switch_007 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_007.name = "Switch.007"
    switch_007.input_type = 'VECTOR'

    #node Reroute.023
    reroute_023 = vat_row.nodes.new("NodeReroute")
    reroute_023.name = "Reroute.023"
    reroute_023.socket_idname = "NodeSocketBool"
    #node Switch.008
    switch_008 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_008.name = "Switch.008"
    switch_008.input_type = 'GEOMETRY'

    #node Switch.009
    switch_009 = vat_row.nodes.new("GeometryNodeSwitch")
    switch_009.name = "Switch.009"
    switch_009.input_type = 'GEOMETRY'

    #node Reroute.024
    reroute_024 = vat_row.nodes.new("NodeReroute")
    reroute_024.name = "Reroute.024"
    reroute_024.socket_idname = "NodeSocketBool"
    #node Reroute.025
    reroute_025 = vat_row.nodes.new("NodeReroute")
    reroute_025.name = "Reroute.025"
    reroute_025.socket_idname = "NodeSocketBool"
    #node Reroute.026
    reroute_026 = vat_row.nodes.new("NodeReroute")
    reroute_026.name = "Reroute.026"
    reroute_026.socket_idname = "NodeSocketGeometry"
    #node Set Position.003
    set_position_003 = vat_row.nodes.new("GeometryNodeSetPosition")
    set_position_003.name = "Set Position.003"
    #Selection
    set_position_003.inputs[1].default_value = True
    #Offset
    set_position_003.inputs[3].default_value = (0.0, 0.0, 0.0)

    #node Set Position.004
    set_position_004 = vat_row.nodes.new("GeometryNodeSetPosition")
    set_position_004.name = "Set Position.004"
    #Selection
    set_position_004.inputs[1].default_value = True
    #Offset
    set_position_004.inputs[3].default_value = (0.0, 0.0, 0.0)

    #node Reroute.027
    reroute_027 = vat_row.nodes.new("NodeReroute")
    reroute_027.name = "Reroute.027"
    reroute_027.socket_idname = "NodeSocketGeometry"
    #node Reroute.028
    reroute_028 = vat_row.nodes.new("NodeReroute")
    reroute_028.name = "Reroute.028"
    reroute_028.socket_idname = "NodeSocketVector"
    #node Reroute.029
    reroute_029 = vat_row.nodes.new("NodeReroute")
    reroute_029.name = "Reroute.029"
    reroute_029.socket_idname = "NodeSocketGeometry"




    #Set locations
    group_input.location = (-2003.91455078125, -22.019737243652344)
    group_output.location = (1567.090087890625, 116.38410949707031)
    named_attribute.location = (-1607.960205078125, -496.68597412109375)
    separate_xyz.location = (-1287.5306396484375, -506.1063232421875)
    math.location = (-1455.206787109375, -645.63916015625)
    scene_time.location = (-1613.3565673828125, -643.8672485351562)
    math_001.location = (-1292.7618408203125, -648.5375366210938)
    math_002.location = (-1087.4205322265625, -402.2408447265625)
    math_003.location = (-1087.4205322265625, -552.2408447265625)
    switch.location = (-912.4205322265625, -402.2408447265625)
    combine_xyz.location = (-748.2355346679688, -399.2298889160156)
    image_texture_001.location = (-575.9117431640625, -247.57046508789062)
    image_info.location = (-1717.266357421875, -810.1309204101562)
    math_004.location = (-1457.2037353515625, -807.08544921875)
    math_005.location = (-1291.715576171875, -807.2326049804688)
    math_006.location = (-1087.4205322265625, -702.2408447265625)
    math_007.location = (-1087.4205322265625, -852.2408447265625)
    switch_001.location = (-912.4205322265625, -702.2408447265625)
    combine_xyz_001.location = (-748.2355346679688, -525.47705078125)
    image_info_001.location = (-1718.3126220703125, -1014.6989135742188)
    math_008.location = (-1457.2037353515625, -1004.3265380859375)
    image_texture_002.location = (-578.3154296875, -458.0011901855469)
    switch_002.location = (-806.6097412109375, -1143.0286865234375)
    switch_003.location = (-806.6097412109375, -1293.0286865234375)
    switch_004.location = (-806.6097412109375, -1443.0286865234375)
    combine_xyz_002.location = (-641.39208984375, -1253.9080810546875)
    vector_math.location = (185.8738250732422, -102.34223175048828)
    vector_math_001.location = (345.9124755859375, -103.2374496459961)
    vector_math_003.location = (349.9295959472656, -411.0874938964844)
    set_position.location = (527.5756225585938, 20.547731399536133)
    join_geometry.location = (1215.18310546875, -5.497060775756836)
    switch_005.location = (1391.460693359375, 117.19529724121094)
    domain_size.location = (-1531.03662109375, 473.3587646484375)
    index.location = (-1532.082763671875, 213.04879760742188)
    position.location = (-1531.03662109375, 272.2272033691406)
    sample_index.location = (-1356.03662109375, 422.2272033691406)
    sample_index_001.location = (-1356.03662109375, 222.22720336914062)
    points.location = (-1181.03662109375, 498.3948669433594)
    capture_attribute.location = (-1006.0365600585938, 472.2272033691406)
    instance_on_points.location = (-831.0365600585938, 472.2272033691406)
    curve_line.location = (-1008.2138061523438, 311.0968322753906)
    realize_instances.location = (-656.0364990234375, 472.2272033691406)
    store_named_attribute.location = (-481.0364990234375, 472.2272033691406)
    set_position_001.location = (1043.01220703125, 219.69619750976562)
    set_position_002.location = (526.99365234375, 192.3417510986328)
    endpoint_selection.location = (877.4285888671875, 171.7894744873047)
    vector_math_004.location = (191.4522705078125, -410.7165832519531)
    vector_math_005.location = (-302.170654296875, -246.54029846191406)
    switch_006.location = (26.996484756469727, -42.1993293762207)
    reroute.location = (-1857.2381591796875, -1213.3670654296875)
    reroute_001.location = (-1854.8079833984375, -1512.9178466796875)
    reroute_002.location = (-1857.2381591796875, -1362.9091796875)
    reroute_003.location = (357.5561218261719, -1283.2596435546875)
    reroute_004.location = (-1489.4921875, -1004.259033203125)
    reroute_005.location = (-1715.9273681640625, -1004.5502319335938)
    reroute_006.location = (-1713.917724609375, -777.6637573242188)
    reroute_007.location = (-920.20556640625, -486.0024719238281)
    reroute_008.location = (-779.0745849609375, -536.8558349609375)
    reroute_009.location = (-1707.6868896484375, -489.3146667480469)
    reroute_010.location = (-1708.23828125, -602.5234375)
    reroute_011.location = (-614.9032592773438, -79.63407135009766)
    reroute_012.location = (-611.1529541015625, -180.8931121826172)
    vector_math_006.location = (-136.55911254882812, -158.4019775390625)
    reroute_013.location = (-1796.357177734375, 289.2080383300781)
    reroute_014.location = (-846.7461547851562, 297.47552490234375)
    reroute_015.location = (-1795.2554931640625, 315.19464111328125)
    reroute_016.location = (-293.70782470703125, -148.21913146972656)
    reroute_017.location = (-1695.4234619140625, -248.662353515625)
    reroute_018.location = (-1692.3323974609375, -213.88365173339844)
    reroute_019.location = (-1707.9071044921875, -508.6319885253906)
    reroute_020.location = (-1808.972412109375, 10.686909675598145)
    reroute_021.location = (-1404.554443359375, 288.8647155761719)
    reroute_022.location = (-1531.2645263671875, 290.74493408203125)
    vector_math_007.location = (-299.94287109375, -533.0477905273438)
    switch_007.location = (22.956817626953125, -387.35943603515625)
    reroute_023.location = (-1705.9517822265625, -471.6048583984375)
    switch_008.location = (700.1618041992188, 193.8846893310547)
    switch_009.location = (701.3392333984375, 10.982881546020508)
    reroute_024.location = (-1810.01318359375, 96.4017105102539)
    reroute_025.location = (665.5728759765625, 109.98329162597656)
    reroute_026.location = (1219.783935546875, 11.0499849319458)
    set_position_003.location = (534.169677734375, -313.9549560546875)
    set_position_004.location = (533.5877075195312, -142.1609344482422)
    reroute_027.location = (489.18597412109375, -40.117984771728516)
    reroute_028.location = (1049.3494873046875, -446.175048828125)
    reroute_029.location = (492.77984619140625, 433.09735107421875)

    #Set dimensions
    group_input.width, group_input.height = 140.0, 100.0
    group_output.width, group_output.height = 140.0, 100.0
    named_attribute.width, named_attribute.height = 140.0, 100.0
    separate_xyz.width, separate_xyz.height = 140.0, 100.0
    math.width, math.height = 140.0, 100.0
    scene_time.width, scene_time.height = 140.0, 100.0
    math_001.width, math_001.height = 140.0, 100.0
    math_002.width, math_002.height = 140.0, 100.0
    math_003.width, math_003.height = 140.0, 100.0
    switch.width, switch.height = 140.0, 100.0
    combine_xyz.width, combine_xyz.height = 140.0, 100.0
    image_texture_001.width, image_texture_001.height = 240.0, 100.0
    image_info.width, image_info.height = 240.0, 100.0
    math_004.width, math_004.height = 140.0, 100.0
    math_005.width, math_005.height = 140.0, 100.0
    math_006.width, math_006.height = 140.0, 100.0
    math_007.width, math_007.height = 140.0, 100.0
    switch_001.width, switch_001.height = 140.0, 100.0
    combine_xyz_001.width, combine_xyz_001.height = 140.0, 100.0
    image_info_001.width, image_info_001.height = 240.0, 100.0
    math_008.width, math_008.height = 140.0, 100.0
    image_texture_002.width, image_texture_002.height = 240.0, 100.0
    switch_002.width, switch_002.height = 140.0, 100.0
    switch_003.width, switch_003.height = 140.0, 100.0
    switch_004.width, switch_004.height = 140.0, 100.0
    combine_xyz_002.width, combine_xyz_002.height = 140.0, 100.0
    vector_math.width, vector_math.height = 140.0, 100.0
    vector_math_001.width, vector_math_001.height = 140.0, 100.0
    vector_math_003.width, vector_math_003.height = 140.0, 100.0
    set_position.width, set_position.height = 140.0, 100.0
    join_geometry.width, join_geometry.height = 140.0, 100.0
    switch_005.width, switch_005.height = 140.0, 100.0
    domain_size.width, domain_size.height = 140.0, 100.0
    index.width, index.height = 140.0, 100.0
    position.width, position.height = 140.0, 100.0
    sample_index.width, sample_index.height = 140.0, 100.0
    sample_index_001.width, sample_index_001.height = 140.0, 100.0
    points.width, points.height = 140.0, 100.0
    capture_attribute.width, capture_attribute.height = 140.0, 100.0
    instance_on_points.width, instance_on_points.height = 140.0, 100.0
    curve_line.width, curve_line.height = 140.0, 100.0
    realize_instances.width, realize_instances.height = 140.0, 100.0
    store_named_attribute.width, store_named_attribute.height = 140.0, 100.0
    set_position_001.width, set_position_001.height = 140.0, 100.0
    set_position_002.width, set_position_002.height = 140.0, 100.0
    endpoint_selection.width, endpoint_selection.height = 140.0, 100.0
    vector_math_004.width, vector_math_004.height = 140.0, 100.0
    vector_math_005.width, vector_math_005.height = 140.0, 100.0
    switch_006.width, switch_006.height = 140.0, 100.0
    reroute.width, reroute.height = 16.0, 100.0
    reroute_001.width, reroute_001.height = 16.0, 100.0
    reroute_002.width, reroute_002.height = 16.0, 100.0
    reroute_003.width, reroute_003.height = 16.0, 100.0
    reroute_004.width, reroute_004.height = 16.0, 100.0
    reroute_005.width, reroute_005.height = 16.0, 100.0
    reroute_006.width, reroute_006.height = 16.0, 100.0
    reroute_007.width, reroute_007.height = 16.0, 100.0
    reroute_008.width, reroute_008.height = 16.0, 100.0
    reroute_009.width, reroute_009.height = 16.0, 100.0
    reroute_010.width, reroute_010.height = 16.0, 100.0
    reroute_011.width, reroute_011.height = 16.0, 100.0
    reroute_012.width, reroute_012.height = 16.0, 100.0
    vector_math_006.width, vector_math_006.height = 140.0, 100.0
    reroute_013.width, reroute_013.height = 16.0, 100.0
    reroute_014.width, reroute_014.height = 16.0, 100.0
    reroute_015.width, reroute_015.height = 16.0, 100.0
    reroute_016.width, reroute_016.height = 16.0, 100.0
    reroute_017.width, reroute_017.height = 16.0, 100.0
    reroute_018.width, reroute_018.height = 16.0, 100.0
    reroute_019.width, reroute_019.height = 16.0, 100.0
    reroute_020.width, reroute_020.height = 16.0, 100.0
    reroute_021.width, reroute_021.height = 16.0, 100.0
    reroute_022.width, reroute_022.height = 16.0, 100.0
    vector_math_007.width, vector_math_007.height = 140.0, 100.0
    switch_007.width, switch_007.height = 140.0, 100.0
    reroute_023.width, reroute_023.height = 16.0, 100.0
    switch_008.width, switch_008.height = 140.0, 100.0
    switch_009.width, switch_009.height = 140.0, 100.0
    reroute_024.width, reroute_024.height = 16.0, 100.0
    reroute_025.width, reroute_025.height = 16.0, 100.0
    reroute_026.width, reroute_026.height = 16.0, 100.0
    set_position_003.width, set_position_003.height = 140.0, 100.0
    set_position_004.width, set_position_004.height = 140.0, 100.0
    reroute_027.width, reroute_027.height = 16.0, 100.0
    reroute_028.width, reroute_028.height = 16.0, 100.0
    reroute_029.width, reroute_029.height = 16.0, 100.0

    #initialize vat_row links
    #reroute_010.Output -> named_attribute.Name
    vat_row.links.new(reroute_010.outputs[0], named_attribute.inputs[0])
    #named_attribute.Attribute -> separate_xyz.Vector
    vat_row.links.new(named_attribute.outputs[0], separate_xyz.inputs[0])
    #scene_time.Frame -> math.Value
    vat_row.links.new(scene_time.outputs[1], math.inputs[0])
    #reroute_006.Output -> math.Value
    vat_row.links.new(reroute_006.outputs[0], math.inputs[1])
    #math.Value -> math_001.Value
    vat_row.links.new(math.outputs[0], math_001.inputs[0])
    #separate_xyz.Y -> math_002.Value
    vat_row.links.new(separate_xyz.outputs[1], math_002.inputs[0])
    #math_001.Value -> math_002.Value
    vat_row.links.new(math_001.outputs[0], math_002.inputs[1])
    #separate_xyz.Y -> math_003.Value
    vat_row.links.new(separate_xyz.outputs[1], math_003.inputs[0])
    #math_001.Value -> math_003.Value
    vat_row.links.new(math_001.outputs[0], math_003.inputs[1])
    #math_002.Value -> switch.False
    vat_row.links.new(math_002.outputs[0], switch.inputs[1])
    #math_003.Value -> switch.True
    vat_row.links.new(math_003.outputs[0], switch.inputs[2])
    #reroute_007.Output -> switch.Switch
    vat_row.links.new(reroute_007.outputs[0], switch.inputs[0])
    #reroute_008.Output -> combine_xyz.X
    vat_row.links.new(reroute_008.outputs[0], combine_xyz.inputs[0])
    #switch.Output -> combine_xyz.Y
    vat_row.links.new(switch.outputs[0], combine_xyz.inputs[1])
    #reroute_011.Output -> image_texture_001.Image
    vat_row.links.new(reroute_011.outputs[0], image_texture_001.inputs[0])
    #combine_xyz.Vector -> image_texture_001.Vector
    vat_row.links.new(combine_xyz.outputs[0], image_texture_001.inputs[1])
    #group_input.OffsetTex -> image_info.Image
    vat_row.links.new(group_input.outputs[1], image_info.inputs[0])
    #image_info.Height -> math_004.Value
    vat_row.links.new(image_info.outputs[1], math_004.inputs[0])
    #reroute_004.Output -> math_004.Value
    vat_row.links.new(reroute_004.outputs[0], math_004.inputs[1])
    #math_004.Value -> math_001.Value
    vat_row.links.new(math_004.outputs[0], math_001.inputs[1])
    #math.Value -> math_005.Value
    vat_row.links.new(math.outputs[0], math_005.inputs[0])
    #separate_xyz.Y -> math_006.Value
    vat_row.links.new(separate_xyz.outputs[1], math_006.inputs[0])
    #math_005.Value -> math_006.Value
    vat_row.links.new(math_005.outputs[0], math_006.inputs[1])
    #separate_xyz.Y -> math_007.Value
    vat_row.links.new(separate_xyz.outputs[1], math_007.inputs[0])
    #math_005.Value -> math_007.Value
    vat_row.links.new(math_005.outputs[0], math_007.inputs[1])
    #math_006.Value -> switch_001.False
    vat_row.links.new(math_006.outputs[0], switch_001.inputs[1])
    #math_007.Value -> switch_001.True
    vat_row.links.new(math_007.outputs[0], switch_001.inputs[2])
    #reroute_007.Output -> switch_001.Switch
    vat_row.links.new(reroute_007.outputs[0], switch_001.inputs[0])
    #reroute_008.Output -> combine_xyz_001.X
    vat_row.links.new(reroute_008.outputs[0], combine_xyz_001.inputs[0])
    #switch_001.Output -> combine_xyz_001.Y
    vat_row.links.new(switch_001.outputs[0], combine_xyz_001.inputs[1])
    #group_input.NormalTex -> image_info_001.Image
    vat_row.links.new(group_input.outputs[6], image_info_001.inputs[0])
    #image_info_001.Height -> math_008.Value
    vat_row.links.new(image_info_001.outputs[1], math_008.inputs[0])
    #reroute_004.Output -> math_008.Value
    vat_row.links.new(reroute_004.outputs[0], math_008.inputs[1])
    #math_008.Value -> math_005.Value
    vat_row.links.new(math_008.outputs[0], math_005.inputs[1])
    #reroute_012.Output -> image_texture_002.Image
    vat_row.links.new(reroute_012.outputs[0], image_texture_002.inputs[0])
    #combine_xyz_001.Vector -> image_texture_002.Vector
    vat_row.links.new(combine_xyz_001.outputs[0], image_texture_002.inputs[1])
    #reroute.Output -> switch_002.Switch
    vat_row.links.new(reroute.outputs[0], switch_002.inputs[0])
    #reroute_002.Output -> switch_003.Switch
    vat_row.links.new(reroute_002.outputs[0], switch_003.inputs[0])
    #reroute_001.Output -> switch_004.Switch
    vat_row.links.new(reroute_001.outputs[0], switch_004.inputs[0])
    #switch_002.Output -> combine_xyz_002.X
    vat_row.links.new(switch_002.outputs[0], combine_xyz_002.inputs[0])
    #switch_003.Output -> combine_xyz_002.Y
    vat_row.links.new(switch_003.outputs[0], combine_xyz_002.inputs[1])
    #switch_004.Output -> combine_xyz_002.Z
    vat_row.links.new(switch_004.outputs[0], combine_xyz_002.inputs[2])
    #reroute_018.Output -> vector_math.Vector
    vat_row.links.new(reroute_018.outputs[0], vector_math.inputs[1])
    #vector_math.Vector -> vector_math_001.Vector
    vat_row.links.new(vector_math.outputs[0], vector_math_001.inputs[0])
    #reroute_003.Output -> vector_math_001.Vector
    vat_row.links.new(reroute_003.outputs[0], vector_math_001.inputs[1])
    #reroute_003.Output -> vector_math_003.Vector
    vat_row.links.new(reroute_003.outputs[0], vector_math_003.inputs[1])
    #reroute_027.Output -> set_position.Geometry
    vat_row.links.new(reroute_027.outputs[0], set_position.inputs[0])
    #join_geometry.Geometry -> switch_005.True
    vat_row.links.new(join_geometry.outputs[0], switch_005.inputs[2])
    #reroute_020.Output -> switch_005.Switch
    vat_row.links.new(reroute_020.outputs[0], switch_005.inputs[0])
    #switch_005.Output -> group_output.Geometry
    vat_row.links.new(switch_005.outputs[0], group_output.inputs[0])
    #reroute_022.Output -> domain_size.Geometry
    vat_row.links.new(reroute_022.outputs[0], domain_size.inputs[0])
    #reroute_021.Output -> sample_index.Geometry
    vat_row.links.new(reroute_021.outputs[0], sample_index.inputs[0])
    #reroute_022.Output -> sample_index_001.Geometry
    vat_row.links.new(reroute_022.outputs[0], sample_index_001.inputs[0])
    #position.Position -> sample_index.Value
    vat_row.links.new(position.outputs[0], sample_index.inputs[1])
    #named_attribute.Attribute -> sample_index_001.Value
    vat_row.links.new(named_attribute.outputs[0], sample_index_001.inputs[1])
    #index.Index -> sample_index.Index
    vat_row.links.new(index.outputs[0], sample_index.inputs[2])
    #index.Index -> sample_index_001.Index
    vat_row.links.new(index.outputs[0], sample_index_001.inputs[2])
    #domain_size.Point Count -> points.Count
    vat_row.links.new(domain_size.outputs[0], points.inputs[0])
    #sample_index.Value -> points.Position
    vat_row.links.new(sample_index.outputs[0], points.inputs[1])
    #points.Points -> capture_attribute.Geometry
    vat_row.links.new(points.outputs[0], capture_attribute.inputs[0])
    #sample_index_001.Value -> capture_attribute.Value
    vat_row.links.new(sample_index_001.outputs[0], capture_attribute.inputs[1])
    #capture_attribute.Geometry -> instance_on_points.Points
    vat_row.links.new(capture_attribute.outputs[0], instance_on_points.inputs[0])
    #curve_line.Curve -> instance_on_points.Instance
    vat_row.links.new(curve_line.outputs[0], instance_on_points.inputs[2])
    #instance_on_points.Instances -> realize_instances.Geometry
    vat_row.links.new(instance_on_points.outputs[0], realize_instances.inputs[0])
    #realize_instances.Geometry -> store_named_attribute.Geometry
    vat_row.links.new(realize_instances.outputs[0], store_named_attribute.inputs[0])
    #reroute_015.Output -> store_named_attribute.Name
    vat_row.links.new(reroute_015.outputs[0], store_named_attribute.inputs[2])
    #reroute_014.Output -> store_named_attribute.Value
    vat_row.links.new(reroute_014.outputs[0], store_named_attribute.inputs[3])
    #endpoint_selection.Selection -> set_position_001.Selection
    vat_row.links.new(endpoint_selection.outputs[0], set_position_001.inputs[1])
    #vector_math_001.Vector -> set_position_002.Offset
    vat_row.links.new(vector_math_001.outputs[0], set_position_002.inputs[3])
    #reroute_019.Output -> vector_math_004.Vector
    vat_row.links.new(reroute_019.outputs[0], vector_math_004.inputs[1])
    #image_texture_001.Color -> vector_math_005.Vector
    vat_row.links.new(image_texture_001.outputs[0], vector_math_005.inputs[0])
    #group_input.InvertX -> reroute.Input
    vat_row.links.new(group_input.outputs[14], reroute.inputs[0])
    #group_input.InvertZ -> reroute_001.Input
    vat_row.links.new(group_input.outputs[16], reroute_001.inputs[0])
    #group_input.InvertY -> reroute_002.Input
    vat_row.links.new(group_input.outputs[15], reroute_002.inputs[0])
    #combine_xyz_002.Vector -> reroute_003.Input
    vat_row.links.new(combine_xyz_002.outputs[0], reroute_003.inputs[0])
    #reroute_005.Output -> reroute_004.Input
    vat_row.links.new(reroute_005.outputs[0], reroute_004.inputs[0])
    #group_input.FrameHeight -> reroute_005.Input
    vat_row.links.new(group_input.outputs[10], reroute_005.inputs[0])
    #group_input.FrameOffset -> reroute_006.Input
    vat_row.links.new(group_input.outputs[11], reroute_006.inputs[0])
    #reroute_009.Output -> reroute_007.Input
    vat_row.links.new(reroute_009.outputs[0], reroute_007.inputs[0])
    #separate_xyz.X -> reroute_008.Input
    vat_row.links.new(separate_xyz.outputs[0], reroute_008.inputs[0])
    #group_input.InvertV -> reroute_009.Input
    vat_row.links.new(group_input.outputs[13], reroute_009.inputs[0])
    #group_input.UVMap -> reroute_010.Input
    vat_row.links.new(group_input.outputs[12], reroute_010.inputs[0])
    #group_input.OffsetTex -> reroute_011.Input
    vat_row.links.new(group_input.outputs[1], reroute_011.inputs[0])
    #group_input.NormalTex -> reroute_012.Input
    vat_row.links.new(group_input.outputs[6], reroute_012.inputs[0])
    #group_input.OffsetRemapped -> switch_006.Switch
    vat_row.links.new(group_input.outputs[4], switch_006.inputs[0])
    #vector_math_006.Vector -> switch_006.True
    vat_row.links.new(vector_math_006.outputs[0], switch_006.inputs[2])
    #reroute_016.Output -> switch_006.False
    vat_row.links.new(reroute_016.outputs[0], switch_006.inputs[1])
    #switch_006.Output -> vector_math.Vector
    vat_row.links.new(switch_006.outputs[0], vector_math.inputs[0])
    #vector_math_001.Vector -> set_position.Offset
    vat_row.links.new(vector_math_001.outputs[0], set_position.inputs[3])
    #group_input.Geometry -> reroute_013.Input
    vat_row.links.new(group_input.outputs[0], reroute_013.inputs[0])
    #capture_attribute.Value -> reroute_014.Input
    vat_row.links.new(capture_attribute.outputs[1], reroute_014.inputs[0])
    #group_input.UVMap -> reroute_015.Input
    vat_row.links.new(group_input.outputs[12], reroute_015.inputs[0])
    #reroute_017.Output -> vector_math_006.Vector
    vat_row.links.new(reroute_017.outputs[0], vector_math_006.inputs[0])
    #vector_math_005.Vector -> vector_math_006.Vector
    vat_row.links.new(vector_math_005.outputs[0], vector_math_006.inputs[1])
    #image_texture_001.Color -> reroute_016.Input
    vat_row.links.new(image_texture_001.outputs[0], reroute_016.inputs[0])
    #group_input.OffsetRemap -> reroute_017.Input
    vat_row.links.new(group_input.outputs[3], reroute_017.inputs[0])
    #group_input.OffsetScale -> reroute_018.Input
    vat_row.links.new(group_input.outputs[2], reroute_018.inputs[0])
    #vector_math_004.Vector -> vector_math_003.Vector
    vat_row.links.new(vector_math_004.outputs[0], vector_math_003.inputs[0])
    #reroute_028.Output -> set_position_001.Offset
    vat_row.links.new(reroute_028.outputs[0], set_position_001.inputs[3])
    #group_input.NormalScale -> reroute_019.Input
    vat_row.links.new(group_input.outputs[7], reroute_019.inputs[0])
    #group_input.Normal -> reroute_020.Input
    vat_row.links.new(group_input.outputs[8], reroute_020.inputs[0])
    #reroute_022.Output -> reroute_021.Input
    vat_row.links.new(reroute_022.outputs[0], reroute_021.inputs[0])
    #reroute_013.Output -> reroute_022.Input
    vat_row.links.new(reroute_013.outputs[0], reroute_022.inputs[0])
    #vector_math_007.Vector -> switch_007.True
    vat_row.links.new(vector_math_007.outputs[0], switch_007.inputs[2])
    #image_texture_002.Color -> vector_math_007.Vector
    vat_row.links.new(image_texture_002.outputs[0], vector_math_007.inputs[0])
    #reroute_023.Output -> switch_007.Switch
    vat_row.links.new(reroute_023.outputs[0], switch_007.inputs[0])
    #group_input.NormalRemapped -> reroute_023.Input
    vat_row.links.new(group_input.outputs[9], reroute_023.inputs[0])
    #switch_007.Output -> vector_math_004.Vector
    vat_row.links.new(switch_007.outputs[0], vector_math_004.inputs[0])
    #image_texture_002.Color -> switch_007.False
    vat_row.links.new(image_texture_002.outputs[0], switch_007.inputs[1])
    #set_position_002.Geometry -> switch_008.True
    vat_row.links.new(set_position_002.outputs[0], switch_008.inputs[2])
    #reroute_026.Output -> switch_005.False
    vat_row.links.new(reroute_026.outputs[0], switch_005.inputs[1])
    #switch_009.Output -> join_geometry.Geometry
    vat_row.links.new(switch_009.outputs[0], join_geometry.inputs[0])
    #set_position.Geometry -> switch_009.True
    vat_row.links.new(set_position.outputs[0], switch_009.inputs[2])
    #group_input.OffsetMode -> reroute_024.Input
    vat_row.links.new(group_input.outputs[5], reroute_024.inputs[0])
    #reroute_024.Output -> reroute_025.Input
    vat_row.links.new(reroute_024.outputs[0], reroute_025.inputs[0])
    #reroute_025.Output -> switch_009.Switch
    vat_row.links.new(reroute_025.outputs[0], switch_009.inputs[0])
    #switch_009.Output -> reroute_026.Input
    vat_row.links.new(switch_009.outputs[0], reroute_026.inputs[0])
    #group_input.Geometry -> reroute_027.Input
    vat_row.links.new(group_input.outputs[0], reroute_027.inputs[0])
    #reroute_027.Output -> set_position_003.Geometry
    vat_row.links.new(reroute_027.outputs[0], set_position_003.inputs[0])
    #vector_math_001.Vector -> set_position_004.Position
    vat_row.links.new(vector_math_001.outputs[0], set_position_004.inputs[2])
    #vector_math_001.Vector -> set_position_003.Position
    vat_row.links.new(vector_math_001.outputs[0], set_position_003.inputs[2])
    #set_position_004.Geometry -> switch_008.False
    vat_row.links.new(set_position_004.outputs[0], switch_008.inputs[1])
    #set_position_003.Geometry -> switch_009.False
    vat_row.links.new(set_position_003.outputs[0], switch_009.inputs[1])
    #reroute_025.Output -> switch_008.Switch
    vat_row.links.new(reroute_025.outputs[0], switch_008.inputs[0])
    #reroute_029.Output -> set_position_002.Geometry
    vat_row.links.new(reroute_029.outputs[0], set_position_002.inputs[0])
    #reroute_029.Output -> set_position_004.Geometry
    vat_row.links.new(reroute_029.outputs[0], set_position_004.inputs[0])
    #switch_008.Output -> set_position_001.Geometry
    vat_row.links.new(switch_008.outputs[0], set_position_001.inputs[0])
    #vector_math_003.Vector -> reroute_028.Input
    vat_row.links.new(vector_math_003.outputs[0], reroute_028.inputs[0])
    #store_named_attribute.Geometry -> reroute_029.Input
    vat_row.links.new(store_named_attribute.outputs[0], reroute_029.inputs[0])
    #set_position_001.Geometry -> join_geometry.Geometry
    vat_row.links.new(set_position_001.outputs[0], join_geometry.inputs[0])
    return vat_row

def build_mesh_geonodes_partialrow_group():
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    vat_partialrow = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "VAT_PartialRow")

    vat_partialrow.color_tag = 'NONE'
    vat_partialrow.description = ""
    vat_partialrow.default_group_node_width = 140
    

    vat_partialrow.is_modifier = True

    #vat_partialrow interface
    #Socket Geometry
    geometry_socket = vat_partialrow.interface.new_socket(name = "Geometry", in_out='OUTPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'

    #Socket Geometry
    geometry_socket_1 = vat_partialrow.interface.new_socket(name = "Geometry", in_out='INPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket_1.attribute_domain = 'POINT'

    #Panel Offset
    offset_panel = vat_partialrow.interface.new_panel("Offset")
    #Socket OffsetTex
    offsettex_socket = vat_partialrow.interface.new_socket(name = "OffsetTex", in_out='INPUT', socket_type = 'NodeSocketImage', parent = offset_panel)
    offsettex_socket.attribute_domain = 'POINT'

    #Socket OffsetScale
    offsetscale_socket = vat_partialrow.interface.new_socket(name = "OffsetScale", in_out='INPUT', socket_type = 'NodeSocketFloat', parent = offset_panel)
    offsetscale_socket.default_value = 100.0
    offsetscale_socket.min_value = -3.4028234663852886e+38
    offsetscale_socket.max_value = 3.4028234663852886e+38
    offsetscale_socket.subtype = 'NONE'
    offsetscale_socket.attribute_domain = 'POINT'

    #Socket OffsetRemap
    offsetremap_socket = vat_partialrow.interface.new_socket(name = "OffsetRemap", in_out='INPUT', socket_type = 'NodeSocketVector', parent = offset_panel)
    offsetremap_socket.default_value = (1.0, 1.0, 1.0)
    offsetremap_socket.min_value = -3.4028234663852886e+38
    offsetremap_socket.max_value = 3.4028234663852886e+38
    offsetremap_socket.subtype = 'NONE'
    offsetremap_socket.attribute_domain = 'POINT'

    #Socket OffsetRemapped
    offsetremapped_socket = vat_partialrow.interface.new_socket(name = "OffsetRemapped", in_out='INPUT', socket_type = 'NodeSocketBool', parent = offset_panel)
    offsetremapped_socket.default_value = False
    offsetremapped_socket.attribute_domain = 'POINT'

    #Socket OffsetMode
    offsetmode_socket = vat_partialrow.interface.new_socket(name = "OffsetMode", in_out='INPUT', socket_type = 'NodeSocketBool', parent = offset_panel)
    offsetmode_socket.default_value = True
    offsetmode_socket.attribute_domain = 'POINT'
    offsetmode_socket.description = "True if Offset, False if Position"


    #Panel Normal
    normal_panel = vat_partialrow.interface.new_panel("Normal")
    #Socket NormalTex
    normaltex_socket = vat_partialrow.interface.new_socket(name = "NormalTex", in_out='INPUT', socket_type = 'NodeSocketImage', parent = normal_panel)
    normaltex_socket.attribute_domain = 'POINT'

    #Socket NormalScale
    normalscale_socket = vat_partialrow.interface.new_socket(name = "NormalScale", in_out='INPUT', socket_type = 'NodeSocketFloat', parent = normal_panel)
    normalscale_socket.default_value = 1.0
    normalscale_socket.min_value = -3.4028234663852886e+38
    normalscale_socket.max_value = 3.4028234663852886e+38
    normalscale_socket.subtype = 'NONE'
    normalscale_socket.attribute_domain = 'POINT'

    #Socket Normal
    normal_socket = vat_partialrow.interface.new_socket(name = "Normal", in_out='INPUT', socket_type = 'NodeSocketBool', parent = normal_panel)
    normal_socket.default_value = True
    normal_socket.attribute_domain = 'POINT'

    #Socket NormalRemapped
    normalremapped_socket = vat_partialrow.interface.new_socket(name = "NormalRemapped", in_out='INPUT', socket_type = 'NodeSocketBool', parent = normal_panel)
    normalremapped_socket.default_value = True
    normalremapped_socket.attribute_domain = 'POINT'


    #Panel Frames
    frames_panel = vat_partialrow.interface.new_panel("Frames")
    #Socket Frames
    frames_socket = vat_partialrow.interface.new_socket(name = "Frames", in_out='INPUT', socket_type = 'NodeSocketInt', parent = frames_panel)
    frames_socket.default_value = 0
    frames_socket.min_value = -2147483648
    frames_socket.max_value = 2147483647
    frames_socket.subtype = 'NONE'
    frames_socket.attribute_domain = 'POINT'

    #Socket FrameStep
    framestep_socket = vat_partialrow.interface.new_socket(name = "FrameStep", in_out='INPUT', socket_type = 'NodeSocketFloat', parent = frames_panel)
    framestep_socket.default_value = 0.625
    framestep_socket.min_value = -3.4028234663852886e+38
    framestep_socket.max_value = 3.4028234663852886e+38
    framestep_socket.subtype = 'NONE'
    framestep_socket.attribute_domain = 'POINT'

    #Socket FrameOffset
    frameoffset_socket = vat_partialrow.interface.new_socket(name = "FrameOffset", in_out='INPUT', socket_type = 'NodeSocketInt', parent = frames_panel)
    frameoffset_socket.default_value = 0
    frameoffset_socket.min_value = -2147483648
    frameoffset_socket.max_value = 2147483647
    frameoffset_socket.subtype = 'NONE'
    frameoffset_socket.attribute_domain = 'POINT'


    #Panel UV
    uv_panel = vat_partialrow.interface.new_panel("UV")
    #Socket UVMap
    uvmap_socket = vat_partialrow.interface.new_socket(name = "UVMap", in_out='INPUT', socket_type = 'NodeSocketString', parent = uv_panel)
    uvmap_socket.default_value = "UVMap.BakedData.VAT"
    uvmap_socket.subtype = 'NONE'
    uvmap_socket.attribute_domain = 'POINT'

    #Socket InvertV
    invertv_socket = vat_partialrow.interface.new_socket(name = "InvertV", in_out='INPUT', socket_type = 'NodeSocketBool', parent = uv_panel)
    invertv_socket.default_value = True
    invertv_socket.attribute_domain = 'POINT'


    #Panel Invert
    invert_panel = vat_partialrow.interface.new_panel("Invert")
    #Socket InvertX
    invertx_socket = vat_partialrow.interface.new_socket(name = "InvertX", in_out='INPUT', socket_type = 'NodeSocketBool', parent = invert_panel)
    invertx_socket.default_value = False
    invertx_socket.attribute_domain = 'POINT'

    #Socket InvertY
    inverty_socket = vat_partialrow.interface.new_socket(name = "InvertY", in_out='INPUT', socket_type = 'NodeSocketBool', parent = invert_panel)
    inverty_socket.default_value = True
    inverty_socket.attribute_domain = 'POINT'

    #Socket InvertZ
    invertz_socket = vat_partialrow.interface.new_socket(name = "InvertZ", in_out='INPUT', socket_type = 'NodeSocketBool', parent = invert_panel)
    invertz_socket.default_value = False
    invertz_socket.attribute_domain = 'POINT'



    #initialize vat_partialrow nodes
    #node Group Input
    group_input = vat_partialrow.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    #node Group Output
    group_output = vat_partialrow.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    #node Named Attribute
    named_attribute = vat_partialrow.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute.name = "Named Attribute"
    named_attribute.data_type = 'FLOAT_VECTOR'

    #node Separate XYZ
    separate_xyz = vat_partialrow.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.name = "Separate XYZ"

    #node Math
    math = vat_partialrow.nodes.new("ShaderNodeMath")
    math.name = "Math"
    math.operation = 'SUBTRACT'
    math.use_clamp = False

    #node Scene Time
    scene_time = vat_partialrow.nodes.new("GeometryNodeInputSceneTime")
    scene_time.name = "Scene Time"

    #node Math.001
    math_001 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_001.name = "Math.001"
    math_001.operation = 'MULTIPLY'
    math_001.use_clamp = False

    #node Math.002
    math_002 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_002.name = "Math.002"
    math_002.operation = 'ADD'
    math_002.use_clamp = False

    #node Math.003
    math_003 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_003.name = "Math.003"
    math_003.operation = 'FRACT'
    math_003.use_clamp = False

    #node Math.004
    math_004 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_004.name = "Math.004"
    math_004.operation = 'FLOOR'
    math_004.use_clamp = False

    #node Math.005
    math_005 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_005.name = "Math.005"
    math_005.operation = 'DIVIDE'
    math_005.use_clamp = False

    #node Math.006
    math_006 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_006.name = "Math.006"
    math_006.operation = 'ADD'
    math_006.use_clamp = False

    #node Math.007
    math_007 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_007.name = "Math.007"
    math_007.operation = 'SUBTRACT'
    math_007.use_clamp = False

    #node Switch
    switch = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch.name = "Switch"
    switch.input_type = 'FLOAT'

    #node Combine XYZ
    combine_xyz = vat_partialrow.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.name = "Combine XYZ"
    #Z
    combine_xyz.inputs[2].default_value = 0.0

    #node Image Texture
    image_texture = vat_partialrow.nodes.new("GeometryNodeImageTexture")
    image_texture.name = "Image Texture"
    image_texture.extension = 'REPEAT'
    image_texture.interpolation = 'Closest'
    #Frame
    image_texture.inputs[2].default_value = 0

    #node Image Info
    image_info = vat_partialrow.nodes.new("GeometryNodeImageInfo")
    image_info.name = "Image Info"
    #Frame
    image_info.inputs[1].default_value = 0

    #node Math.008
    math_008 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_008.name = "Math.008"
    math_008.operation = 'DIVIDE'
    math_008.use_clamp = False

    #node Math.009
    math_009 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_009.name = "Math.009"
    math_009.operation = 'ADD'
    math_009.use_clamp = False

    #node Math.010
    math_010 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_010.name = "Math.010"
    math_010.operation = 'SUBTRACT'
    math_010.use_clamp = False

    #node Switch.001
    switch_001 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_001.name = "Switch.001"
    switch_001.input_type = 'FLOAT'

    #node Combine XYZ.001
    combine_xyz_001 = vat_partialrow.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_001.name = "Combine XYZ.001"
    #Z
    combine_xyz_001.inputs[2].default_value = 0.0

    #node Image Texture.001
    image_texture_001 = vat_partialrow.nodes.new("GeometryNodeImageTexture")
    image_texture_001.name = "Image Texture.001"
    image_texture_001.extension = 'REPEAT'
    image_texture_001.interpolation = 'Closest'
    #Frame
    image_texture_001.inputs[2].default_value = 0

    #node Image Info.001
    image_info_001 = vat_partialrow.nodes.new("GeometryNodeImageInfo")
    image_info_001.name = "Image Info.001"
    #Frame
    image_info_001.inputs[1].default_value = 0

    #node Switch.002
    switch_002 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_002.name = "Switch.002"
    switch_002.input_type = 'FLOAT'
    #False
    switch_002.inputs[1].default_value = 1.0
    #True
    switch_002.inputs[2].default_value = -1.0

    #node Switch.003
    switch_003 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_003.name = "Switch.003"
    switch_003.input_type = 'FLOAT'
    #False
    switch_003.inputs[1].default_value = 1.0
    #True
    switch_003.inputs[2].default_value = -1.0

    #node Switch.004
    switch_004 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_004.name = "Switch.004"
    switch_004.input_type = 'FLOAT'
    #False
    switch_004.inputs[1].default_value = 1.0
    #True
    switch_004.inputs[2].default_value = -1.0

    #node Combine XYZ.002
    combine_xyz_002 = vat_partialrow.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_002.name = "Combine XYZ.002"

    #node Vector Math
    vector_math = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math.name = "Vector Math"
    vector_math.operation = 'DIVIDE'

    #node Vector Math.001
    vector_math_001 = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math_001.name = "Vector Math.001"
    vector_math_001.operation = 'MULTIPLY'

    #node Vector Math.003
    vector_math_003 = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math_003.name = "Vector Math.003"
    vector_math_003.operation = 'MULTIPLY'

    #node Set Position
    set_position = vat_partialrow.nodes.new("GeometryNodeSetPosition")
    set_position.name = "Set Position"
    #Selection
    set_position.inputs[1].default_value = True
    #Position
    set_position.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Join Geometry
    join_geometry = vat_partialrow.nodes.new("GeometryNodeJoinGeometry")
    join_geometry.name = "Join Geometry"

    #node Switch.005
    switch_005 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_005.name = "Switch.005"
    switch_005.input_type = 'GEOMETRY'

    #node Domain Size
    domain_size = vat_partialrow.nodes.new("GeometryNodeAttributeDomainSize")
    domain_size.name = "Domain Size"
    domain_size.component = 'MESH'

    #node Index
    index = vat_partialrow.nodes.new("GeometryNodeInputIndex")
    index.name = "Index"

    #node Position
    position = vat_partialrow.nodes.new("GeometryNodeInputPosition")
    position.name = "Position"

    #node Sample Index
    sample_index = vat_partialrow.nodes.new("GeometryNodeSampleIndex")
    sample_index.name = "Sample Index"
    sample_index.clamp = False
    sample_index.data_type = 'FLOAT_VECTOR'
    sample_index.domain = 'POINT'

    #node Sample Index.001
    sample_index_001 = vat_partialrow.nodes.new("GeometryNodeSampleIndex")
    sample_index_001.name = "Sample Index.001"
    sample_index_001.clamp = False
    sample_index_001.data_type = 'FLOAT_VECTOR'
    sample_index_001.domain = 'POINT'

    #node Points
    points = vat_partialrow.nodes.new("GeometryNodePoints")
    points.name = "Points"
    #Radius
    points.inputs[2].default_value = 0.10000000149011612

    #node Capture Attribute
    capture_attribute = vat_partialrow.nodes.new("GeometryNodeCaptureAttribute")
    capture_attribute.name = "Capture Attribute"
    capture_attribute.active_index = 0
    capture_attribute.capture_items.clear()
    capture_attribute.capture_items.new('FLOAT', "Value")
    capture_attribute.capture_items["Value"].data_type = 'FLOAT_VECTOR'
    capture_attribute.domain = 'POINT'

    #node Instance on Points
    instance_on_points = vat_partialrow.nodes.new("GeometryNodeInstanceOnPoints")
    instance_on_points.name = "Instance on Points"
    #Selection
    instance_on_points.inputs[1].default_value = True
    #Pick Instance
    instance_on_points.inputs[3].default_value = False
    #Instance Index
    instance_on_points.inputs[4].default_value = 0
    #Rotation
    instance_on_points.inputs[5].default_value = (0.0, 0.0, 0.0)
    #Scale
    instance_on_points.inputs[6].default_value = (1.0, 1.0, 1.0)

    #node Curve Line
    curve_line = vat_partialrow.nodes.new("GeometryNodeCurvePrimitiveLine")
    curve_line.name = "Curve Line"
    curve_line.mode = 'POINTS'
    #Start
    curve_line.inputs[0].default_value = (0.0, 0.0, 0.0)
    #End
    curve_line.inputs[1].default_value = (0.0, 0.0, 0.0)

    #node Realize Instances
    realize_instances = vat_partialrow.nodes.new("GeometryNodeRealizeInstances")
    realize_instances.name = "Realize Instances"
    #Selection
    realize_instances.inputs[1].default_value = True
    #Realize All
    realize_instances.inputs[2].default_value = True
    #Depth
    realize_instances.inputs[3].default_value = 0

    #node Store Named Attribute
    store_named_attribute = vat_partialrow.nodes.new("GeometryNodeStoreNamedAttribute")
    store_named_attribute.name = "Store Named Attribute"
    store_named_attribute.data_type = 'FLOAT_VECTOR'
    store_named_attribute.domain = 'POINT'
    #Selection
    store_named_attribute.inputs[1].default_value = True

    #node Set Position.001
    set_position_001 = vat_partialrow.nodes.new("GeometryNodeSetPosition")
    set_position_001.name = "Set Position.001"
    #Position
    set_position_001.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Set Position.002
    set_position_002 = vat_partialrow.nodes.new("GeometryNodeSetPosition")
    set_position_002.name = "Set Position.002"
    #Selection
    set_position_002.inputs[1].default_value = True
    #Position
    set_position_002.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Endpoint Selection
    endpoint_selection = vat_partialrow.nodes.new("GeometryNodeCurveEndpointSelection")
    endpoint_selection.name = "Endpoint Selection"
    #Start Size
    endpoint_selection.inputs[0].default_value = 0
    #End Size
    endpoint_selection.inputs[1].default_value = 1

    #node Vector Math.004
    vector_math_004 = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math_004.name = "Vector Math.004"
    vector_math_004.operation = 'MULTIPLY'

    #node Reroute
    reroute = vat_partialrow.nodes.new("NodeReroute")
    reroute.name = "Reroute"
    reroute.socket_idname = "NodeSocketBool"
    #node Reroute.001
    reroute_001 = vat_partialrow.nodes.new("NodeReroute")
    reroute_001.name = "Reroute.001"
    reroute_001.socket_idname = "NodeSocketBool"
    #node Reroute.002
    reroute_002 = vat_partialrow.nodes.new("NodeReroute")
    reroute_002.name = "Reroute.002"
    reroute_002.socket_idname = "NodeSocketBool"
    #node Reroute.003
    reroute_003 = vat_partialrow.nodes.new("NodeReroute")
    reroute_003.name = "Reroute.003"
    reroute_003.socket_idname = "NodeSocketVector"
    #node Reroute.004
    reroute_004 = vat_partialrow.nodes.new("NodeReroute")
    reroute_004.name = "Reroute.004"
    reroute_004.socket_idname = "NodeSocketGeometry"
    #node Reroute.005
    reroute_005 = vat_partialrow.nodes.new("NodeReroute")
    reroute_005.name = "Reroute.005"
    reroute_005.socket_idname = "NodeSocketFloat"
    #node Reroute.006
    reroute_006 = vat_partialrow.nodes.new("NodeReroute")
    reroute_006.name = "Reroute.006"
    reroute_006.socket_idname = "NodeSocketFloat"
    #node Reroute.007
    reroute_007 = vat_partialrow.nodes.new("NodeReroute")
    reroute_007.name = "Reroute.007"
    reroute_007.socket_idname = "NodeSocketImage"
    #node Reroute.008
    reroute_008 = vat_partialrow.nodes.new("NodeReroute")
    reroute_008.name = "Reroute.008"
    reroute_008.socket_idname = "NodeSocketImage"
    #node Reroute.009
    reroute_009 = vat_partialrow.nodes.new("NodeReroute")
    reroute_009.name = "Reroute.009"
    reroute_009.socket_idname = "NodeSocketBool"
    #node Vector Math.005
    vector_math_005 = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math_005.name = "Vector Math.005"
    vector_math_005.operation = 'MULTIPLY_ADD'
    #Vector_001
    vector_math_005.inputs[1].default_value = (2.0, 2.0, 2.0)
    #Vector_002
    vector_math_005.inputs[2].default_value = (-1.0, -1.0, -1.0)

    #node Vector Math.006
    vector_math_006 = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math_006.name = "Vector Math.006"
    vector_math_006.operation = 'MULTIPLY'

    #node Switch.006
    switch_006 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_006.name = "Switch.006"
    switch_006.input_type = 'VECTOR'

    #node Reroute.010
    reroute_010 = vat_partialrow.nodes.new("NodeReroute")
    reroute_010.name = "Reroute.010"
    reroute_010.socket_idname = "NodeSocketColor"
    #node Reroute.011
    reroute_011 = vat_partialrow.nodes.new("NodeReroute")
    reroute_011.name = "Reroute.011"
    reroute_011.socket_idname = "NodeSocketBool"
    #node Vector Math.007
    vector_math_007 = vat_partialrow.nodes.new("ShaderNodeVectorMath")
    vector_math_007.name = "Vector Math.007"
    vector_math_007.operation = 'MULTIPLY_ADD'
    #Vector_001
    vector_math_007.inputs[1].default_value = (2.0, 2.0, 2.0)
    #Vector_002
    vector_math_007.inputs[2].default_value = (-1.0, -1.0, -1.0)

    #node Switch.007
    switch_007 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_007.name = "Switch.007"
    switch_007.input_type = 'VECTOR'

    #node Reroute.012
    reroute_012 = vat_partialrow.nodes.new("NodeReroute")
    reroute_012.name = "Reroute.012"
    reroute_012.socket_idname = "NodeSocketGeometry"
    #node Reroute.013
    reroute_013 = vat_partialrow.nodes.new("NodeReroute")
    reroute_013.name = "Reroute.013"
    reroute_013.socket_idname = "NodeSocketString"
    #node Reroute.014
    reroute_014 = vat_partialrow.nodes.new("NodeReroute")
    reroute_014.name = "Reroute.014"
    reroute_014.socket_idname = "NodeSocketVector"
    #node Reroute.015
    reroute_015 = vat_partialrow.nodes.new("NodeReroute")
    reroute_015.name = "Reroute.015"
    reroute_015.socket_idname = "NodeSocketBool"
    #node Reroute.016
    reroute_016 = vat_partialrow.nodes.new("NodeReroute")
    reroute_016.name = "Reroute.016"
    reroute_016.socket_idname = "NodeSocketImage"
    #node Reroute.017
    reroute_017 = vat_partialrow.nodes.new("NodeReroute")
    reroute_017.name = "Reroute.017"
    reroute_017.socket_idname = "NodeSocketImage"
    #node Reroute.018
    reroute_018 = vat_partialrow.nodes.new("NodeReroute")
    reroute_018.name = "Reroute.018"
    reroute_018.socket_idname = "NodeSocketVector"
    #node Reroute.019
    reroute_019 = vat_partialrow.nodes.new("NodeReroute")
    reroute_019.name = "Reroute.019"
    reroute_019.socket_idname = "NodeSocketVector"
    #node Reroute.020
    reroute_020 = vat_partialrow.nodes.new("NodeReroute")
    reroute_020.name = "Reroute.020"
    reroute_020.socket_idname = "NodeSocketVector"
    #node Switch.008
    switch_008 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_008.name = "Switch.008"
    switch_008.input_type = 'GEOMETRY'

    #node Switch.009
    switch_009 = vat_partialrow.nodes.new("GeometryNodeSwitch")
    switch_009.name = "Switch.009"
    switch_009.input_type = 'GEOMETRY'

    #node Set Position.003
    set_position_003 = vat_partialrow.nodes.new("GeometryNodeSetPosition")
    set_position_003.name = "Set Position.003"
    #Selection
    set_position_003.inputs[1].default_value = True
    #Offset
    set_position_003.inputs[3].default_value = (0.0, 0.0, 0.0)

    #node Set Position.004
    set_position_004 = vat_partialrow.nodes.new("GeometryNodeSetPosition")
    set_position_004.name = "Set Position.004"
    #Selection
    set_position_004.inputs[1].default_value = True
    #Offset
    set_position_004.inputs[3].default_value = (0.0, 0.0, 0.0)

    #node Reroute.021
    reroute_021 = vat_partialrow.nodes.new("NodeReroute")
    reroute_021.name = "Reroute.021"
    reroute_021.socket_idname = "NodeSocketGeometry"
    #node Reroute.022
    reroute_022 = vat_partialrow.nodes.new("NodeReroute")
    reroute_022.name = "Reroute.022"
    reroute_022.socket_idname = "NodeSocketBool"
    #node Reroute.023
    reroute_023 = vat_partialrow.nodes.new("NodeReroute")
    reroute_023.name = "Reroute.023"
    reroute_023.socket_idname = "NodeSocketBool"
    #node Reroute.024
    reroute_024 = vat_partialrow.nodes.new("NodeReroute")
    reroute_024.name = "Reroute.024"
    reroute_024.socket_idname = "NodeSocketGeometry"
    #node Reroute.025
    reroute_025 = vat_partialrow.nodes.new("NodeReroute")
    reroute_025.name = "Reroute.025"
    reroute_025.socket_idname = "NodeSocketVector"
    #node Math.011
    math_011 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_011.name = "Math.011"
    math_011.operation = 'MODULO'
    math_011.use_clamp = False

    #node Reroute.026
    reroute_026 = vat_partialrow.nodes.new("NodeReroute")
    reroute_026.name = "Reroute.026"
    reroute_026.socket_idname = "NodeSocketInt"
    #node Math.012
    math_012 = vat_partialrow.nodes.new("ShaderNodeMath")
    math_012.name = "Math.012"
    math_012.operation = 'MAXIMUM'
    math_012.use_clamp = False
    #Value_001
    math_012.inputs[1].default_value = 0.0





    #Set locations
    group_input.location = (-2051.611572265625, -1.7974562644958496)
    group_output.location = (1724.0400390625, 110.42295837402344)
    named_attribute.location = (-1844.0616455078125, -247.81822204589844)
    separate_xyz.location = (-1671.3238525390625, -235.37094116210938)
    math.location = (-1836.14404296875, -484.94921875)
    scene_time.location = (-2046.3238525390625, -535.3709106445312)
    math_001.location = (-1672.4549560546875, -368.6082763671875)
    math_002.location = (-1497.0809326171875, -307.8634338378906)
    math_003.location = (-1321.3238525390625, -202.13363647460938)
    math_004.location = (-1321.3238525390625, -335.3709716796875)
    math_005.location = (-1160.1927490234375, -413.44940185546875)
    math_006.location = (-996.3238525390625, -285.3709716796875)
    math_007.location = (-996.3238525390625, -435.3709716796875)
    switch.location = (-846.3238525390625, -285.3709716796875)
    combine_xyz.location = (-690.1927490234375, -172.37123107910156)
    image_texture.location = (-527.9943237304688, -178.79232788085938)
    image_info.location = (-1423.585693359375, -494.5289001464844)
    math_008.location = (-1161.3238525390625, -720.6604614257812)
    math_009.location = (-997.4549560546875, -590.3189086914062)
    math_010.location = (-997.4549560546875, -740.3189086914062)
    switch_001.location = (-847.4549560546875, -590.3189086914062)
    combine_xyz_001.location = (-693.5860595703125, -298.531005859375)
    image_texture_001.location = (-533.6497802734375, -383.0303649902344)
    image_info_001.location = (-1424.716796875, -689.7144165039062)
    switch_002.location = (-1840.796630859375, -880.3492431640625)
    switch_003.location = (-1840.796630859375, -1030.3492431640625)
    switch_004.location = (-1840.796630859375, -1180.3492431640625)
    combine_xyz_002.location = (-1665.796630859375, -1030.3492431640625)
    vector_math.location = (245.48776245117188, 13.358413696289062)
    vector_math_001.location = (405.0342712402344, 12.611251831054688)
    vector_math_003.location = (405.5400085449219, -142.21067810058594)
    set_position.location = (677.2388916015625, 25.797771453857422)
    join_geometry.location = (1380.99853515625, -12.534774780273438)
    switch_005.location = (1548.14404296875, 111.77081298828125)
    domain_size.location = (-591.1162719726562, 572.2337036132812)
    index.location = (-592.3390502929688, 306.48687744140625)
    position.location = (-591.1162719726562, 372.23370361328125)
    sample_index.location = (-416.11627197265625, 522.2337036132812)
    sample_index_001.location = (-416.11627197265625, 322.23370361328125)
    points.location = (-247.72598266601562, 596.038818359375)
    capture_attribute.location = (-66.11627197265625, 572.2337036132812)
    instance_on_points.location = (108.88373565673828, 572.2337036132812)
    curve_line.location = (-67.16253662109375, 429.8023681640625)
    realize_instances.location = (283.88372802734375, 572.2337036132812)
    store_named_attribute.location = (458.8836975097656, 572.2337036132812)
    set_position_001.location = (1187.759765625, 218.44805908203125)
    set_position_002.location = (680.404296875, 183.02688598632812)
    endpoint_selection.location = (1017.9910888671875, 170.54150390625)
    vector_math_004.location = (244.91554260253906, -119.66144561767578)
    reroute.location = (-1904.2850341796875, -963.24951171875)
    reroute_001.location = (-1904.2850341796875, -1261.638671875)
    reroute_002.location = (-1904.2850341796875, -1112.444091796875)
    reroute_003.location = (407.4941101074219, -1060.602783203125)
    reroute_004.location = (-599.9059448242188, 386.171142578125)
    reroute_005.location = (-1826.7935791015625, -477.1668395996094)
    reroute_006.location = (-711.0994873046875, -233.2825927734375)
    reroute_007.location = (-1835.8172607421875, -645.1122436523438)
    reroute_008.location = (-1841.5477294921875, -839.636962890625)
    reroute_009.location = (-1826.8551025390625, 13.977813720703125)
    vector_math_005.location = (-253.3356475830078, -205.2415771484375)
    vector_math_006.location = (-92.26495361328125, -131.43692016601562)
    switch_006.location = (81.3905029296875, -39.41553497314453)
    reroute_010.location = (-250.31790161132812, -145.48858642578125)
    reroute_011.location = (-855.66064453125, -300.9414367675781)
    vector_math_007.location = (-252.0805206298828, -488.9002685546875)
    switch_007.location = (81.39470672607422, -192.4459686279297)
    reroute_012.location = (-1794.1900634765625, 385.0114440917969)
    reroute_013.location = (-1796.3768310546875, 419.6842346191406)
    reroute_014.location = (94.2705078125, 397.7276916503906)
    reroute_015.location = (-1843.55712890625, -275.6932678222656)
    reroute_016.location = (-1839.6820068359375, -312.74053955078125)
    reroute_017.location = (-1830.1063232421875, -500.5050048828125)
    reroute_018.location = (-1846.97412109375, -205.34805297851562)
    reroute_019.location = (-1634.97900390625, 162.23098754882812)
    reroute_020.location = (648.1683349609375, -18.61269760131836)
    switch_008.location = (849.8839111328125, 193.30770874023438)
    switch_009.location = (851.061279296875, 10.405899047851562)
    set_position_003.location = (677.1052856445312, -307.7425231933594)
    set_position_004.location = (677.6543579101562, -128.02745056152344)
    reroute_021.location = (645.40185546875, -34.032344818115234)
    reroute_022.location = (816.93994140625, 110.55156707763672)
    reroute_023.location = (-1823.605712890625, 107.86133575439453)
    reroute_024.location = (1377.272705078125, 4.4713029861450195)
    reroute_025.location = (1172.65185546875, -180.82196044921875)
    math_011.location = (-1671.331787109375, -528.819580078125)
    reroute_026.location = (-1838.9593505859375, -660.0022583007812)
    math_012.location = (-1673.1080322265625, -677.8931884765625)

    #Set dimensions
    group_input.width, group_input.height = 140.0, 100.0
    group_output.width, group_output.height = 140.0, 100.0
    named_attribute.width, named_attribute.height = 140.0, 100.0
    separate_xyz.width, separate_xyz.height = 140.0, 100.0
    math.width, math.height = 140.0, 100.0
    scene_time.width, scene_time.height = 140.0, 100.0
    math_001.width, math_001.height = 140.0, 100.0
    math_002.width, math_002.height = 140.0, 100.0
    math_003.width, math_003.height = 140.0, 100.0
    math_004.width, math_004.height = 140.0, 100.0
    math_005.width, math_005.height = 140.0, 100.0
    math_006.width, math_006.height = 140.0, 100.0
    math_007.width, math_007.height = 140.0, 100.0
    switch.width, switch.height = 140.0, 100.0
    combine_xyz.width, combine_xyz.height = 140.0, 100.0
    image_texture.width, image_texture.height = 240.0, 100.0
    image_info.width, image_info.height = 240.0, 100.0
    math_008.width, math_008.height = 140.0, 100.0
    math_009.width, math_009.height = 140.0, 100.0
    math_010.width, math_010.height = 140.0, 100.0
    switch_001.width, switch_001.height = 140.0, 100.0
    combine_xyz_001.width, combine_xyz_001.height = 140.0, 100.0
    image_texture_001.width, image_texture_001.height = 240.0, 100.0
    image_info_001.width, image_info_001.height = 240.0, 100.0
    switch_002.width, switch_002.height = 140.0, 100.0
    switch_003.width, switch_003.height = 140.0, 100.0
    switch_004.width, switch_004.height = 140.0, 100.0
    combine_xyz_002.width, combine_xyz_002.height = 140.0, 100.0
    vector_math.width, vector_math.height = 140.0, 100.0
    vector_math_001.width, vector_math_001.height = 140.0, 100.0
    vector_math_003.width, vector_math_003.height = 140.0, 100.0
    set_position.width, set_position.height = 140.0, 100.0
    join_geometry.width, join_geometry.height = 140.0, 100.0
    switch_005.width, switch_005.height = 140.0, 100.0
    domain_size.width, domain_size.height = 140.0, 100.0
    index.width, index.height = 140.0, 100.0
    position.width, position.height = 140.0, 100.0
    sample_index.width, sample_index.height = 140.0, 100.0
    sample_index_001.width, sample_index_001.height = 140.0, 100.0
    points.width, points.height = 140.0, 100.0
    capture_attribute.width, capture_attribute.height = 140.0, 100.0
    instance_on_points.width, instance_on_points.height = 140.0, 100.0
    curve_line.width, curve_line.height = 140.0, 100.0
    realize_instances.width, realize_instances.height = 140.0, 100.0
    store_named_attribute.width, store_named_attribute.height = 140.0, 100.0
    set_position_001.width, set_position_001.height = 140.0, 100.0
    set_position_002.width, set_position_002.height = 140.0, 100.0
    endpoint_selection.width, endpoint_selection.height = 140.0, 100.0
    vector_math_004.width, vector_math_004.height = 140.0, 100.0
    reroute.width, reroute.height = 16.0, 100.0
    reroute_001.width, reroute_001.height = 16.0, 100.0
    reroute_002.width, reroute_002.height = 16.0, 100.0
    reroute_003.width, reroute_003.height = 16.0, 100.0
    reroute_004.width, reroute_004.height = 16.0, 100.0
    reroute_005.width, reroute_005.height = 16.0, 100.0
    reroute_006.width, reroute_006.height = 16.0, 100.0
    reroute_007.width, reroute_007.height = 16.0, 100.0
    reroute_008.width, reroute_008.height = 16.0, 100.0
    reroute_009.width, reroute_009.height = 16.0, 100.0
    vector_math_005.width, vector_math_005.height = 140.0, 100.0
    vector_math_006.width, vector_math_006.height = 140.0, 100.0
    switch_006.width, switch_006.height = 140.0, 100.0
    reroute_010.width, reroute_010.height = 16.0, 100.0
    reroute_011.width, reroute_011.height = 16.0, 100.0
    vector_math_007.width, vector_math_007.height = 140.0, 100.0
    switch_007.width, switch_007.height = 140.0, 100.0
    reroute_012.width, reroute_012.height = 16.0, 100.0
    reroute_013.width, reroute_013.height = 16.0, 100.0
    reroute_014.width, reroute_014.height = 16.0, 100.0
    reroute_015.width, reroute_015.height = 16.0, 100.0
    reroute_016.width, reroute_016.height = 16.0, 100.0
    reroute_017.width, reroute_017.height = 16.0, 100.0
    reroute_018.width, reroute_018.height = 16.0, 100.0
    reroute_019.width, reroute_019.height = 16.0, 100.0
    reroute_020.width, reroute_020.height = 16.0, 100.0
    switch_008.width, switch_008.height = 140.0, 100.0
    switch_009.width, switch_009.height = 140.0, 100.0
    set_position_003.width, set_position_003.height = 140.0, 100.0
    set_position_004.width, set_position_004.height = 140.0, 100.0
    reroute_021.width, reroute_021.height = 16.0, 100.0
    reroute_022.width, reroute_022.height = 16.0, 100.0
    reroute_023.width, reroute_023.height = 16.0, 100.0
    reroute_024.width, reroute_024.height = 16.0, 100.0
    reroute_025.width, reroute_025.height = 16.0, 100.0
    math_011.width, math_011.height = 140.0, 100.0
    reroute_026.width, reroute_026.height = 16.0, 100.0
    math_012.width, math_012.height = 140.0, 100.0

    #initialize vat_partialrow links
    #group_input.UVMap -> named_attribute.Name
    vat_partialrow.links.new(group_input.outputs[13], named_attribute.inputs[0])
    #named_attribute.Attribute -> separate_xyz.Vector
    vat_partialrow.links.new(named_attribute.outputs[0], separate_xyz.inputs[0])
    #scene_time.Frame -> math.Value
    vat_partialrow.links.new(scene_time.outputs[1], math.inputs[0])
    #group_input.FrameOffset -> math.Value
    vat_partialrow.links.new(group_input.outputs[12], math.inputs[1])
    #separate_xyz.X -> math_002.Value
    vat_partialrow.links.new(separate_xyz.outputs[0], math_002.inputs[0])
    #math_004.Value -> math_005.Value
    vat_partialrow.links.new(math_004.outputs[0], math_005.inputs[0])
    #separate_xyz.Y -> math_006.Value
    vat_partialrow.links.new(separate_xyz.outputs[1], math_006.inputs[0])
    #math_005.Value -> math_006.Value
    vat_partialrow.links.new(math_005.outputs[0], math_006.inputs[1])
    #separate_xyz.Y -> math_007.Value
    vat_partialrow.links.new(separate_xyz.outputs[1], math_007.inputs[0])
    #math_005.Value -> math_007.Value
    vat_partialrow.links.new(math_005.outputs[0], math_007.inputs[1])
    #math_006.Value -> switch.False
    vat_partialrow.links.new(math_006.outputs[0], switch.inputs[1])
    #math_007.Value -> switch.True
    vat_partialrow.links.new(math_007.outputs[0], switch.inputs[2])
    #reroute_011.Output -> switch.Switch
    vat_partialrow.links.new(reroute_011.outputs[0], switch.inputs[0])
    #reroute_006.Output -> combine_xyz.X
    vat_partialrow.links.new(reroute_006.outputs[0], combine_xyz.inputs[0])
    #switch.Output -> combine_xyz.Y
    vat_partialrow.links.new(switch.outputs[0], combine_xyz.inputs[1])
    #reroute_007.Output -> image_info.Image
    vat_partialrow.links.new(reroute_007.outputs[0], image_info.inputs[0])
    #image_info.Height -> math_005.Value
    vat_partialrow.links.new(image_info.outputs[1], math_005.inputs[1])
    #reroute_016.Output -> image_texture.Image
    vat_partialrow.links.new(reroute_016.outputs[0], image_texture.inputs[0])
    #combine_xyz.Vector -> image_texture.Vector
    vat_partialrow.links.new(combine_xyz.outputs[0], image_texture.inputs[1])
    #math_004.Value -> math_008.Value
    vat_partialrow.links.new(math_004.outputs[0], math_008.inputs[0])
    #separate_xyz.Y -> math_009.Value
    vat_partialrow.links.new(separate_xyz.outputs[1], math_009.inputs[0])
    #math_008.Value -> math_009.Value
    vat_partialrow.links.new(math_008.outputs[0], math_009.inputs[1])
    #separate_xyz.Y -> math_010.Value
    vat_partialrow.links.new(separate_xyz.outputs[1], math_010.inputs[0])
    #math_008.Value -> math_010.Value
    vat_partialrow.links.new(math_008.outputs[0], math_010.inputs[1])
    #math_009.Value -> switch_001.False
    vat_partialrow.links.new(math_009.outputs[0], switch_001.inputs[1])
    #math_010.Value -> switch_001.True
    vat_partialrow.links.new(math_010.outputs[0], switch_001.inputs[2])
    #reroute_011.Output -> switch_001.Switch
    vat_partialrow.links.new(reroute_011.outputs[0], switch_001.inputs[0])
    #reroute_006.Output -> combine_xyz_001.X
    vat_partialrow.links.new(reroute_006.outputs[0], combine_xyz_001.inputs[0])
    #switch_001.Output -> combine_xyz_001.Y
    vat_partialrow.links.new(switch_001.outputs[0], combine_xyz_001.inputs[1])
    #reroute_008.Output -> image_info_001.Image
    vat_partialrow.links.new(reroute_008.outputs[0], image_info_001.inputs[0])
    #image_info_001.Height -> math_008.Value
    vat_partialrow.links.new(image_info_001.outputs[1], math_008.inputs[1])
    #reroute_017.Output -> image_texture_001.Image
    vat_partialrow.links.new(reroute_017.outputs[0], image_texture_001.inputs[0])
    #combine_xyz_001.Vector -> image_texture_001.Vector
    vat_partialrow.links.new(combine_xyz_001.outputs[0], image_texture_001.inputs[1])
    #reroute.Output -> switch_002.Switch
    vat_partialrow.links.new(reroute.outputs[0], switch_002.inputs[0])
    #reroute_002.Output -> switch_003.Switch
    vat_partialrow.links.new(reroute_002.outputs[0], switch_003.inputs[0])
    #reroute_001.Output -> switch_004.Switch
    vat_partialrow.links.new(reroute_001.outputs[0], switch_004.inputs[0])
    #switch_002.Output -> combine_xyz_002.X
    vat_partialrow.links.new(switch_002.outputs[0], combine_xyz_002.inputs[0])
    #switch_003.Output -> combine_xyz_002.Y
    vat_partialrow.links.new(switch_003.outputs[0], combine_xyz_002.inputs[1])
    #switch_004.Output -> combine_xyz_002.Z
    vat_partialrow.links.new(switch_004.outputs[0], combine_xyz_002.inputs[2])
    #switch_006.Output -> vector_math.Vector
    vat_partialrow.links.new(switch_006.outputs[0], vector_math.inputs[0])
    #group_input.OffsetScale -> vector_math.Vector
    vat_partialrow.links.new(group_input.outputs[2], vector_math.inputs[1])
    #vector_math.Vector -> vector_math_001.Vector
    vat_partialrow.links.new(vector_math.outputs[0], vector_math_001.inputs[0])
    #reroute_003.Output -> vector_math_001.Vector
    vat_partialrow.links.new(reroute_003.outputs[0], vector_math_001.inputs[1])
    #reroute_003.Output -> vector_math_003.Vector
    vat_partialrow.links.new(reroute_003.outputs[0], vector_math_003.inputs[1])
    #reroute_021.Output -> set_position.Geometry
    vat_partialrow.links.new(reroute_021.outputs[0], set_position.inputs[0])
    #join_geometry.Geometry -> switch_005.True
    vat_partialrow.links.new(join_geometry.outputs[0], switch_005.inputs[2])
    #reroute_009.Output -> switch_005.Switch
    vat_partialrow.links.new(reroute_009.outputs[0], switch_005.inputs[0])
    #switch_005.Output -> group_output.Geometry
    vat_partialrow.links.new(switch_005.outputs[0], group_output.inputs[0])
    #reroute_004.Output -> domain_size.Geometry
    vat_partialrow.links.new(reroute_004.outputs[0], domain_size.inputs[0])
    #reroute_004.Output -> sample_index.Geometry
    vat_partialrow.links.new(reroute_004.outputs[0], sample_index.inputs[0])
    #reroute_004.Output -> sample_index_001.Geometry
    vat_partialrow.links.new(reroute_004.outputs[0], sample_index_001.inputs[0])
    #position.Position -> sample_index.Value
    vat_partialrow.links.new(position.outputs[0], sample_index.inputs[1])
    #reroute_019.Output -> sample_index_001.Value
    vat_partialrow.links.new(reroute_019.outputs[0], sample_index_001.inputs[1])
    #index.Index -> sample_index.Index
    vat_partialrow.links.new(index.outputs[0], sample_index.inputs[2])
    #index.Index -> sample_index_001.Index
    vat_partialrow.links.new(index.outputs[0], sample_index_001.inputs[2])
    #domain_size.Point Count -> points.Count
    vat_partialrow.links.new(domain_size.outputs[0], points.inputs[0])
    #sample_index.Value -> points.Position
    vat_partialrow.links.new(sample_index.outputs[0], points.inputs[1])
    #points.Points -> capture_attribute.Geometry
    vat_partialrow.links.new(points.outputs[0], capture_attribute.inputs[0])
    #sample_index_001.Value -> capture_attribute.Value
    vat_partialrow.links.new(sample_index_001.outputs[0], capture_attribute.inputs[1])
    #capture_attribute.Geometry -> instance_on_points.Points
    vat_partialrow.links.new(capture_attribute.outputs[0], instance_on_points.inputs[0])
    #curve_line.Curve -> instance_on_points.Instance
    vat_partialrow.links.new(curve_line.outputs[0], instance_on_points.inputs[2])
    #instance_on_points.Instances -> realize_instances.Geometry
    vat_partialrow.links.new(instance_on_points.outputs[0], realize_instances.inputs[0])
    #realize_instances.Geometry -> store_named_attribute.Geometry
    vat_partialrow.links.new(realize_instances.outputs[0], store_named_attribute.inputs[0])
    #reroute_013.Output -> store_named_attribute.Name
    vat_partialrow.links.new(reroute_013.outputs[0], store_named_attribute.inputs[2])
    #reroute_014.Output -> store_named_attribute.Value
    vat_partialrow.links.new(reroute_014.outputs[0], store_named_attribute.inputs[3])
    #endpoint_selection.Selection -> set_position_001.Selection
    vat_partialrow.links.new(endpoint_selection.outputs[0], set_position_001.inputs[1])
    #reroute_020.Output -> set_position_002.Offset
    vat_partialrow.links.new(reroute_020.outputs[0], set_position_002.inputs[3])
    #group_input.InvertX -> reroute.Input
    vat_partialrow.links.new(group_input.outputs[15], reroute.inputs[0])
    #group_input.InvertZ -> reroute_001.Input
    vat_partialrow.links.new(group_input.outputs[17], reroute_001.inputs[0])
    #group_input.InvertY -> reroute_002.Input
    vat_partialrow.links.new(group_input.outputs[16], reroute_002.inputs[0])
    #combine_xyz_002.Vector -> reroute_003.Input
    vat_partialrow.links.new(combine_xyz_002.outputs[0], reroute_003.inputs[0])
    #reroute_012.Output -> reroute_004.Input
    vat_partialrow.links.new(reroute_012.outputs[0], reroute_004.inputs[0])
    #reroute_005.Output -> math_001.Value
    vat_partialrow.links.new(reroute_005.outputs[0], math_001.inputs[0])
    #group_input.FrameStep -> reroute_005.Input
    vat_partialrow.links.new(group_input.outputs[11], reroute_005.inputs[0])
    #math_003.Value -> reroute_006.Input
    vat_partialrow.links.new(math_003.outputs[0], reroute_006.inputs[0])
    #group_input.OffsetTex -> reroute_007.Input
    vat_partialrow.links.new(group_input.outputs[1], reroute_007.inputs[0])
    #group_input.NormalTex -> reroute_008.Input
    vat_partialrow.links.new(group_input.outputs[6], reroute_008.inputs[0])
    #group_input.Normal -> reroute_009.Input
    vat_partialrow.links.new(group_input.outputs[8], reroute_009.inputs[0])
    #image_texture.Color -> vector_math_005.Vector
    vat_partialrow.links.new(image_texture.outputs[0], vector_math_005.inputs[0])
    #reroute_018.Output -> vector_math_006.Vector
    vat_partialrow.links.new(reroute_018.outputs[0], vector_math_006.inputs[0])
    #vector_math_005.Vector -> vector_math_006.Vector
    vat_partialrow.links.new(vector_math_005.outputs[0], vector_math_006.inputs[1])
    #vector_math_006.Vector -> switch_006.True
    vat_partialrow.links.new(vector_math_006.outputs[0], switch_006.inputs[2])
    #group_input.OffsetRemapped -> switch_006.Switch
    vat_partialrow.links.new(group_input.outputs[4], switch_006.inputs[0])
    #reroute_010.Output -> switch_006.False
    vat_partialrow.links.new(reroute_010.outputs[0], switch_006.inputs[1])
    #image_texture.Color -> reroute_010.Input
    vat_partialrow.links.new(image_texture.outputs[0], reroute_010.inputs[0])
    #reroute_020.Output -> set_position.Offset
    vat_partialrow.links.new(reroute_020.outputs[0], set_position.inputs[3])
    #group_input.InvertV -> reroute_011.Input
    vat_partialrow.links.new(group_input.outputs[14], reroute_011.inputs[0])
    #image_texture_001.Color -> switch_007.False
    vat_partialrow.links.new(image_texture_001.outputs[0], switch_007.inputs[1])
    #reroute_015.Output -> switch_007.Switch
    vat_partialrow.links.new(reroute_015.outputs[0], switch_007.inputs[0])
    #vector_math_007.Vector -> switch_007.True
    vat_partialrow.links.new(vector_math_007.outputs[0], switch_007.inputs[2])
    #image_texture_001.Color -> vector_math_007.Vector
    vat_partialrow.links.new(image_texture_001.outputs[0], vector_math_007.inputs[0])
    #group_input.Geometry -> reroute_012.Input
    vat_partialrow.links.new(group_input.outputs[0], reroute_012.inputs[0])
    #group_input.UVMap -> reroute_013.Input
    vat_partialrow.links.new(group_input.outputs[13], reroute_013.inputs[0])
    #capture_attribute.Value -> reroute_014.Input
    vat_partialrow.links.new(capture_attribute.outputs[1], reroute_014.inputs[0])
    #vector_math_004.Vector -> vector_math_003.Vector
    vat_partialrow.links.new(vector_math_004.outputs[0], vector_math_003.inputs[0])
    #reroute_025.Output -> set_position_001.Offset
    vat_partialrow.links.new(reroute_025.outputs[0], set_position_001.inputs[3])
    #switch_007.Output -> vector_math_004.Vector
    vat_partialrow.links.new(switch_007.outputs[0], vector_math_004.inputs[1])
    #group_input.NormalScale -> vector_math_004.Vector
    vat_partialrow.links.new(group_input.outputs[7], vector_math_004.inputs[0])
    #group_input.NormalRemapped -> reroute_015.Input
    vat_partialrow.links.new(group_input.outputs[9], reroute_015.inputs[0])
    #group_input.OffsetTex -> reroute_016.Input
    vat_partialrow.links.new(group_input.outputs[1], reroute_016.inputs[0])
    #group_input.NormalTex -> reroute_017.Input
    vat_partialrow.links.new(group_input.outputs[6], reroute_017.inputs[0])
    #group_input.OffsetRemap -> reroute_018.Input
    vat_partialrow.links.new(group_input.outputs[3], reroute_018.inputs[0])
    #named_attribute.Attribute -> reroute_019.Input
    vat_partialrow.links.new(named_attribute.outputs[0], reroute_019.inputs[0])
    #vector_math_001.Vector -> reroute_020.Input
    vat_partialrow.links.new(vector_math_001.outputs[0], reroute_020.inputs[0])
    #set_position_004.Geometry -> switch_008.False
    vat_partialrow.links.new(set_position_004.outputs[0], switch_008.inputs[1])
    #group_input.Geometry -> reroute_021.Input
    vat_partialrow.links.new(group_input.outputs[0], reroute_021.inputs[0])
    #reroute_021.Output -> set_position_003.Geometry
    vat_partialrow.links.new(reroute_021.outputs[0], set_position_003.inputs[0])
    #reroute_020.Output -> set_position_003.Position
    vat_partialrow.links.new(reroute_020.outputs[0], set_position_003.inputs[2])
    #reroute_020.Output -> set_position_004.Position
    vat_partialrow.links.new(reroute_020.outputs[0], set_position_004.inputs[2])
    #reroute_022.Output -> switch_008.Switch
    vat_partialrow.links.new(reroute_022.outputs[0], switch_008.inputs[0])
    #reroute_023.Output -> reroute_022.Input
    vat_partialrow.links.new(reroute_023.outputs[0], reroute_022.inputs[0])
    #reroute_022.Output -> switch_009.Switch
    vat_partialrow.links.new(reroute_022.outputs[0], switch_009.inputs[0])
    #group_input.OffsetMode -> reroute_023.Input
    vat_partialrow.links.new(group_input.outputs[5], reroute_023.inputs[0])
    #reroute_024.Output -> switch_005.False
    vat_partialrow.links.new(reroute_024.outputs[0], switch_005.inputs[1])
    #switch_009.Output -> join_geometry.Geometry
    vat_partialrow.links.new(switch_009.outputs[0], join_geometry.inputs[0])
    #set_position_002.Geometry -> switch_008.True
    vat_partialrow.links.new(set_position_002.outputs[0], switch_008.inputs[2])
    #set_position.Geometry -> switch_009.True
    vat_partialrow.links.new(set_position.outputs[0], switch_009.inputs[2])
    #set_position_003.Geometry -> switch_009.False
    vat_partialrow.links.new(set_position_003.outputs[0], switch_009.inputs[1])
    #switch_009.Output -> reroute_024.Input
    vat_partialrow.links.new(switch_009.outputs[0], reroute_024.inputs[0])
    #switch_008.Output -> set_position_001.Geometry
    vat_partialrow.links.new(switch_008.outputs[0], set_position_001.inputs[0])
    #vector_math_003.Vector -> reroute_025.Input
    vat_partialrow.links.new(vector_math_003.outputs[0], reroute_025.inputs[0])
    #store_named_attribute.Geometry -> set_position_002.Geometry
    vat_partialrow.links.new(store_named_attribute.outputs[0], set_position_002.inputs[0])
    #store_named_attribute.Geometry -> set_position_004.Geometry
    vat_partialrow.links.new(store_named_attribute.outputs[0], set_position_004.inputs[0])
    #math_002.Value -> math_003.Value
    vat_partialrow.links.new(math_002.outputs[0], math_003.inputs[0])
    #math_002.Value -> math_004.Value
    vat_partialrow.links.new(math_002.outputs[0], math_004.inputs[0])
    #reroute_026.Output -> math_011.Value
    vat_partialrow.links.new(reroute_026.outputs[0], math_011.inputs[1])
    #group_input.Frames -> reroute_026.Input
    vat_partialrow.links.new(group_input.outputs[10], reroute_026.inputs[0])
    #math_001.Value -> math_002.Value
    vat_partialrow.links.new(math_001.outputs[0], math_002.inputs[1])
    #math_011.Value -> math_001.Value
    vat_partialrow.links.new(math_011.outputs[0], math_001.inputs[1])
    #math.Value -> math_012.Value
    vat_partialrow.links.new(math.outputs[0], math_012.inputs[0])
    #math_012.Value -> math_011.Value
    vat_partialrow.links.new(math_012.outputs[0], math_011.inputs[0])
    #set_position_001.Geometry -> join_geometry.Geometry
    vat_partialrow.links.new(set_position_001.outputs[0], join_geometry.inputs[0])
    return vat_partialrow

###############
### BUFFERS ###
def get_animation_vertices_buffers(context: bpy.types.Context, objs_to_bake: list, bake_frames_info: tuple[list, int, int], bake_frame_height: int, tex_width: int, tex_height: int, num_vertices: int) -> tuple[bool, str, list, list, tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector]]:
    """
    Iterate objects and frames to build a buffer of vertices offsets & a buffer of vertices normals, keeping track of maximum extended bounds while doing so.
    This method expects objects to be animated using various methods (keyframes, armatures etc). Frames will actually be 'scrubbed' and objects will be evaluated each frame

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :param bake_frames_info: list of frames to bake
    :param bake_frame_height: Amount of lines of pixels per frame
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :param num_vertices: Amount of vertices to bake per frame
    :return: success, message, offset buffer, normal buffer, bounds
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    vertices_offsets = [0.0, 0.0, 0.0, 1.0] * (tex_width * tex_height)
    vertices_normals = [0.0, 0.0, 0.0, 1.0] * (tex_width * tex_height)

    min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
    ref_min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    ref_max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
    
    dgraph = context.evaluated_depsgraph_get()

    buffer_object_offset = 0
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info

    for obj_index, obj_to_bake in enumerate(objs_to_bake):
        ############
        # REF POSE #

        context.scene.frame_set(bake_ref_frame)
        #context.view_layer.update()

        ref_eval_obj = obj_to_bake.evaluated_get(dgraph)
        ref_eval_mesh = ref_eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        ref_eval_mesh.transform(ref_eval_obj.matrix_world)
        
        ref_eval_mesh_vertex_count = len(ref_eval_mesh.vertices)
        # cache SOURCE vertices pos. It has to be copied because it is still accessed after ref_eval_mesh is cleared
        # and it cannot be cleared any later
        ref_eval_mesh_vertices_pos = [v.co.copy() for v in ref_eval_mesh.vertices]

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
        
        ###########
        # MAPPING #

        mappings = []

        target_mesh_vertex_count = ref_eval_mesh_vertex_count
        target_obj = obj_to_bake.get(custom_prop, None)
        if target_obj and target_obj.type == "MESH":
            target_eval_obj = target_obj.evaluated_get(dgraph)
            target_eval_mesh = target_eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            target_eval_mesh.transform(target_eval_obj.matrix_world)
            target_mesh_vertex_count = len(target_eval_mesh.vertices) # override!

            BVH = BVHTree.FromObject(ref_eval_obj, context.view_layer.depsgraph) # create BVH tree for SOURCE object

            mappings = [None] * target_mesh_vertex_count

            for vertex_index, vertex in enumerate(target_eval_mesh.vertices):
                closest_face_pos, closest_face_nor, closest_face_index, closest_face_dist = BVH.find_nearest(vertex.co) # closest position on SOURCE mesh from TARGET vert
                closest_face_vertices_pos = [ref_eval_mesh.vertices[v].co for v in ref_eval_mesh.polygons[closest_face_index].vertices]
                closest_face_vertices_nor = []
                if ref_eval_mesh.has_custom_normals:
                    poly = ref_eval_mesh.polygons[closest_face_index]
                    for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                        closest_face_vertices_nor.append(ref_eval_mesh.loops[loop_index].normal)
                else:
                    closest_face_vertices_nor = [ref_eval_mesh.vertices[v].normal for v in ref_eval_mesh.polygons[closest_face_index].vertices]
                
                closest_face_barycoords = mathutils.interpolate.poly_3d_calc(closest_face_vertices_pos, closest_face_pos) # compute barycoords of closest position on closest face

                # confirm robustness of method
                # say we have a source vertex and we have found the closest surface position on the target mesh. We are next going to track this same
                # surface position during the animation to compute the offset but that does NOT account for the initial offset from the source vertex
                # to the surface position on the target mesh, something that becomes apparent with rotations. So we'll want to carry this offset and
                # project it along the surface normal during the animation. Note that we do *not* use the 'closest_face_nor' to compute the initial
                # offset. We instead compute the vertex normal from the barycentric coordinates, just like we're going to do during the animation,
                # as to ensure a 1:1 correlation between the ref pose and the pose computed on the first frame (which are factually the same frame)
                ref_tri_pos = mathutils.Vector((0,0,0))
                for closest_vertex_index, closest_pos in enumerate(closest_face_vertices_pos):
                    ref_tri_pos += closest_pos * closest_face_barycoords[closest_vertex_index]

                ref_tri_nor = mathutils.Vector((0,0,0))
                for closest_vertex_index, closest_nor in enumerate(closest_face_vertices_nor):
                    ref_tri_nor += closest_nor * closest_face_barycoords[closest_vertex_index]

                ref_tri_offset = mathutils.Vector(vertex.co - ref_tri_pos).dot(ref_tri_nor)
                closest_face_pos += ref_tri_offset * ref_tri_nor # apply initial offset from target vertex projected to source surface along its normal

                mappings[vertex_index] = (ref_tri_offset, # initial offset along SOURCE face normal
                                        closest_face_pos, # SOURCE face position
                                        closest_face_index, # SOURCE face index
                                        closest_face_barycoords # SOURCE face barycentric coord
                                        )

            target_obj.to_mesh_clear()

        ref_eval_obj.to_mesh_clear()

        ########
        # BAKE #

        for frame_index, frame_to_bake in enumerate(frames_to_bake):
            progress = (obj_index * max(1, (len(frames_to_bake) - 1)) + frame_index / max(1, (len(objs_to_bake) + len(frames_to_bake) - 2))) 
            bpy.context.window_manager.progress_update((progress * 80) + 10)

            context.scene.frame_set(frame_to_bake) # advance to frame
            #context.view_layer.update()

            eval_posed_obj = obj_to_bake.evaluated_get(dgraph)

            """
            This step calculates the minimum and maximum bounds of the mesh in its animated pose. These bounds can be then compared to the bounds of the mesh in reference pose to compute
            an offset to apply to the exported mesh's bounding box. This is important for accurate occlusion culling.
            """
            bbox_corners = [(eval_posed_obj.matrix_world @ mathutils.Vector(corner)) * signed_scale for corner in eval_posed_obj.bound_box]
            bbox_corners_x = [corner.x for corner in bbox_corners]
            bbox_corners_y = [corner.y for corner in bbox_corners]
            bbox_corners_z = [corner.z for corner in bbox_corners]

            min_bounds = mathutils.Vector((min(min_bounds.x, min(bbox_corners_x)),
                                           min(min_bounds.y, min(bbox_corners_y)),
                                           min(min_bounds.z, min(bbox_corners_z))))
            max_bounds = mathutils.Vector((max(max_bounds.x, max(bbox_corners_x)),
                                           max(max_bounds.y, max(bbox_corners_y)),
                                           max(max_bounds.z, max(bbox_corners_z))))

            eval_posed_mesh = eval_posed_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            eval_posed_mesh.transform(eval_posed_obj.matrix_world)
            eval_mesh_vertex_count = len(eval_posed_mesh.vertices)

            if eval_mesh_vertex_count != ref_eval_mesh_vertex_count:
                return (False, "Vertex count mismatch in frame " + str(frame_to_bake) + " for object " + obj_to_bake.name + ". It likely has a modifier that changes its topology during animation (i.e. a split edge modifier that suddenly splits an edge due to an increase angle).", [], [], None)

            if settings.tex_packing_mode == 'STACK':
                if settings.tex_packing_stack_mode == 'ADJACENT':
                    buffer_frame_offset = tex_width * bake_frame_height * frame_index * 4
                else:
                    buffer_frame_offset = tex_width * frame_index * 4
            else:
                buffer_frame_offset = num_vertices * frame_index * 4

            if mappings:
                for mapping_index, mapping in enumerate(mappings):
                    if settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "OFFSET":
                        buffer_vertex_index = buffer_frame_offset + ((((buffer_object_offset // 4) + mapping_index) % tex_width) * 4) + ((((buffer_object_offset // 4) + mapping_index) // tex_width) * len(frames_to_bake) * tex_width * 4)
                    else:
                        buffer_vertex_index = buffer_object_offset + buffer_frame_offset + (mapping_index * 4)

                    tri_offset, tri_pos, tri_index, tri_barycoords = mapping
                    # compute posed surface position & normal from mapped face index and barycentric coords
                    posed_tri_pos = mathutils.Vector((0,0,0))
                    posed_tri_nor = mathutils.Vector((0,0,0))
                    for barycoords_index, eval_posed_mesh_vertex_index in enumerate(eval_posed_mesh.polygons[tri_index].vertices):
                        eval_posed_mesh_vertex = eval_posed_mesh.vertices[eval_posed_mesh_vertex_index]
                        posed_tri_pos += eval_posed_mesh_vertex.co * tri_barycoords[barycoords_index]
                        posed_tri_nor += eval_posed_mesh_vertex.normal * tri_barycoords[barycoords_index]

                    posed_tri_pos += (tri_offset * posed_tri_nor) # apply initial offset from target vertex projected to source surface along its normal

                    # offset
                    if settings.offset_tex_mode == "OFFSET":
                        offset = posed_tri_pos - tri_pos # delta with base position
                    else: # settings.offset_tex_mode == "POSITION"
                        offset = posed_tri_pos

                    vector_to_bake = offset * signed_scale
                    if settings.unit_axis_order != "XYZ":
                        vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
                    x, y, z = vector_to_bake
                    vertices_offsets[buffer_vertex_index + 0] = x
                    vertices_offsets[buffer_vertex_index + 1] = y
                    vertices_offsets[buffer_vertex_index + 2] = z
                    #vertices_offsets[buffer_vertex_index + 3] = 1.0

                    # normal
                    vector_to_bake = (posed_tri_nor * signed_axis).normalized()
                    if settings.unit_axis_order != "XYZ":
                        vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
                    x, y, z = vector_to_bake
                    vertices_normals[buffer_vertex_index + 0] = x
                    vertices_normals[buffer_vertex_index + 1] = y
                    vertices_normals[buffer_vertex_index + 2] = z
                    #vertices_normals[buffer_vertex_index + 3] = 1.0
            else: # no mappings
                # custom normals require iterating loops
                if eval_posed_mesh.has_custom_normals:
                    for loop in eval_posed_mesh.loops:
                        vector_to_bake = loop.normal
                        vertex_index = loop.vertex_index

                        if settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "OFFSET":
                            buffer_vertex_index = buffer_frame_offset + ((vertex_index % tex_width) * 4) + ((vertex_index // tex_width) * len(frames_to_bake) * tex_width * 4)
                        else:
                            buffer_vertex_index = buffer_frame_offset + (vertex_index * 4)

                        if settings.unit_axis_order != "XYZ":
                            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
                        x, y, z = vector_to_bake
                        vertices_normals[buffer_vertex_index + 0] = x
                        vertices_normals[buffer_vertex_index + 1] = y
                        vertices_normals[buffer_vertex_index + 2] = z
                        #vertices_normals[buffer_vertex_index + 3] = 1.0

                # for each vertex
                for vertex_index, vertex in enumerate(eval_posed_mesh.vertices):
                    if settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "OFFSET":
                        buffer_vertex_index = buffer_frame_offset + ((((buffer_object_offset // 4) + vertex_index) % tex_width) * 4) + ((((buffer_object_offset // 4) + vertex_index) // tex_width) * len(frames_to_bake) * tex_width * 4)
                    else:
                        buffer_vertex_index = buffer_object_offset + buffer_frame_offset + (vertex_index * 4)

                    # offset
                    if settings.offset_tex_mode == "OFFSET":
                        offset = (vertex.co - ref_eval_mesh_vertices_pos[vertex.index]) # delta with base position
                    else: # settings.offset_tex_mode == "POSITION"
                        offset = vertex.co

                    vector_to_bake = offset * signed_scale
                    if settings.unit_axis_order != "XYZ":
                        vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
                    x, y, z = vector_to_bake
                    vertices_offsets[buffer_vertex_index + 0] = x
                    vertices_offsets[buffer_vertex_index + 1] = y
                    vertices_offsets[buffer_vertex_index + 2] = z
                    #vertices_offsets[buffer_vertex_index + 3] = 1.0

                    # normal (bypass if using custom normals)
                    if not eval_posed_mesh.has_custom_normals:
                        vector_to_bake = (vertex.normal * signed_axis).normalized()
                        if settings.unit_axis_order != "XYZ":
                            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
                        x, y, z = vector_to_bake
                        vertices_normals[buffer_vertex_index + 0] = x
                        vertices_normals[buffer_vertex_index + 1] = y
                        vertices_normals[buffer_vertex_index + 2] = z
                        #vertices_normals[buffer_vertex_index + 3] = 1.0

            eval_posed_obj.to_mesh_clear()

        buffer_object_offset += target_mesh_vertex_count * 4

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

    return (True, "", vertices_offsets, vertices_normals, (ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset))

def get_sequence_vertices_buffers(context: bpy.types.Context, objs_to_bake: list, bake_frames_info: tuple[list, int, int], bake_frame_height: int, tex_width: int, tex_height: int, num_vertices: int) -> tuple[bool, str, list, list, tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector, mathutils.Vector]]:
    """
    Iterate objects and frames to build a buffer of vertices offsets & a buffer of vertices normals, keeping track of maximum extended bounds while doing so.
    This method expects a list of mesh to act as a 'mesh sequence', frames are irrelevant except to get the frame count

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :param bake_frames_info: list of frames to bake
    :param bake_frame_height: Amount of lines of pixels per frame
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :param num_vertices: Amount of vertices to bake per frame
    :return: the function's success, potential error message, offset buffer, normal buffer, bounds
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings
    frames_to_bake, bake_start_frame, bake_end_frame, bake_ref_frame = bake_frames_info

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                        -1.0 if settings.unit_invert_y else 1.0,
                                        -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    ############
    # REF POSE #

    dgraph = context.evaluated_depsgraph_get()

    ref_eval_obj = objs_to_bake[0].evaluated_get(dgraph)
    ref_eval_mesh = ref_eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
    ref_eval_mesh.transform(ref_eval_obj.matrix_world)
    ref_eval_mesh_vertex_count = len(ref_eval_mesh.vertices)
    ref_eval_mesh_vertices_pos = [Vertex.co.copy() for Vertex in ref_eval_mesh.vertices] # cache SOURCE vertices pos
    
    """
    This step calculates the minimum and maximum bounds of the mesh in its reference pose. These bounds serve as a baseline for determining the overall min/max bounds during animation.
    By comparing the animated bounds to the reference pose bounds, an offset can be computed. This offset is later applied to the mesh in its reference pose to ensure that the bounding
    box fully encloses the animated mesh over time. This is crucial for accurate occlusion culling and avoiding visual artifacts during rendering.
    """
    bbox_corners = [(ref_eval_obj.matrix_world @ mathutils.Vector(corner)) * signed_scale for corner in ref_eval_obj.bound_box]
    bbox_corners_x = [corner.x for corner in bbox_corners]
    bbox_corners_y = [corner.y for corner in bbox_corners]
    bbox_corners_z = [corner.z for corner in bbox_corners]

    ref_min_bounds = mathutils.Vector((min(bbox_corners_x),
                                        min(bbox_corners_y),
                                        min(bbox_corners_z)))
    ref_max_bounds = mathutils.Vector((max(bbox_corners_x),
                                        max(bbox_corners_y),
                                        max(bbox_corners_z)))

    ref_eval_obj.to_mesh_clear()

    ########
    # BAKE #

    min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    vertices_offsets = [0.0, 0.0, 0.0, 1.0] * (tex_width * tex_height)
    vertices_normals = [0.0, 0.0, 0.0, 1.0] * (tex_width * tex_height)

    for frame_index, frame_to_bake in enumerate(frames_to_bake):
        progress = (frame_index / (len(frames_to_bake) - 1)) 
        bpy.context.window_manager.progress_update((progress * 80) + 10)

        # no need to advance to frame, our list of objects act as a 'frame sequence'
        eval_obj = objs_to_bake[frame_index].evaluated_get(dgraph)

        """
        This step calculates the minimum and maximum bounds of the mesh in its reference pose. These bounds serve as a baseline for determining the overall min/max bounds during animation.
        By comparing the animated bounds to the reference pose bounds, an offset can be computed. This offset is later applied to the mesh in its reference pose to ensure that the bounding
        box fully encloses the animated mesh over time. This is crucial for accurate occlusion culling and avoiding visual artifacts during rendering.
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

        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        eval_mesh.transform(eval_obj.matrix_world)
        eval_mesh_vertex_count = len(eval_mesh.vertices)

        if eval_mesh_vertex_count != ref_eval_mesh_vertex_count:
            return (False, "Vertex count mismatch in frame " + str(frame_to_bake) + " for object " + objs_to_bake[0].name + ". It likely has a modifier that changes its topology during animation (i.e. a split edge modifier that suddenly splits an edge due to an increase angle).", [], [], None, None)

        if settings.tex_packing_mode == 'STACK':
            if settings.tex_packing_stack_mode == 'ADJACENT':
                buffer_frame_offset = tex_width * bake_frame_height * frame_index * 4
            else:
                buffer_frame_offset = tex_width * frame_index * 4
        else:
            buffer_frame_offset = num_vertices * frame_index * 4

        if eval_mesh.has_custom_normals:
            for loop in eval_mesh.loops:
                normal = loop.normal
                vertex_index = loop.vertex_index

                if settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "OFFSET":
                    buffer_vertex_index = buffer_frame_offset + (((vertex_index) % tex_width) * 4) + (((vertex_index) // tex_width) * len(frames_to_bake) * tex_width * 4)
                else:
                    buffer_vertex_index = buffer_frame_offset + (vertex_index * 4)

                if settings.unit_axis_order != "XYZ":
                    vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
                x, y, z = vector_to_bake
                vertices_normals[buffer_vertex_index + 0] = x
                vertices_normals[buffer_vertex_index + 1] = y
                vertices_normals[buffer_vertex_index + 2] = z
                #vertices_normals[buffer_vertex_index + 3] = 1.0

        for vertex_index, vertex in enumerate(eval_mesh.vertices):
            if settings.tex_packing_mode == "STACK" and settings.tex_packing_stack_mode == "OFFSET":
                buffer_vertex_index = buffer_frame_offset + (((vertex_index) % tex_width) * 4) + (((vertex_index) // tex_width) * len(frames_to_bake) * tex_width * 4)
            else:
                buffer_vertex_index = buffer_frame_offset + (vertex_index * 4)

            # offset
            if settings.offset_tex_mode == "OFFSET":
                offset = (vertex.co - ref_eval_mesh_vertices_pos[vertex.index]) # delta with base position
            else: # settings.offset_tex_mode == "POSITION"
                offset = vertex.co

            vector_to_bake = offset * signed_scale
            if settings.unit_axis_order != "XYZ":
                vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
            x, y, z = vector_to_bake
            vertices_offsets[buffer_vertex_index + 0] = x
            vertices_offsets[buffer_vertex_index + 1] = y
            vertices_offsets[buffer_vertex_index + 2] = z
            #vertices_offsets[buffer_vertex_index + 3] = 1.0

            # normal
            if not eval_mesh.has_custom_normals:
                vector_to_bake = (vertex.normal * signed_axis).normalized()

            if settings.unit_axis_order != "XYZ":
                vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])
            x, y, z = vector_to_bake
            vertices_normals[buffer_vertex_index + 0] = x
            vertices_normals[buffer_vertex_index + 1] = y
            vertices_normals[buffer_vertex_index + 2] = z
            #vertices_normals[buffer_vertex_index + 3] = 1.0

        eval_obj.to_mesh_clear()

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

    return (True, "", vertices_offsets, vertices_normals, (ref_min_bounds, ref_max_bounds, min_bounds, max_bounds, min_bounds_offset, max_bounds_offset))

def get_inverted_buffers(vertices_offsets: list, vertices_normals: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """ 
    Re-order vert buffers so that pixel buffer is flipped in V (aka invert image). Append line of pixels after line in reverse order. Method can likely be pythonified and improved

    :param vertices_offsets: Vertices offsets buffer
    :param vertices_normals: Vertices normals buffer
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :return: processed offset buffer, processed normal buffer
    :rtype: tuple
    """

    vertices_offsets_inv = []
    vertices_normals_inv = []
    for i in reversed(range(tex_height)):
        row = tex_width * 4
        row_offset = i * row
        vertices_offsets_inv.extend(vertices_offsets[row_offset:row_offset + row])
        vertices_normals_inv.extend(vertices_normals[row_offset:row_offset + row])

    return (vertices_offsets_inv, vertices_normals_inv)

def get_remapped_vertices_offset_buffer(vertices_offsets: list) -> list:
    """
    Remap the offset buffer from the range [-min:max] to [0:1]

    :param vertices_offsets: buffer of vertices offsets
    :param bounds_info: min/max values to remap offsets to the range [0:1]
    :return: remapped buffer, absolute maximum offset in X/Y/Z to remap offset back to their initial range
    :rtype: tuple
    """
    
    min_x = min(vertices_offsets[0::4])
    max_x = max(vertices_offsets[0::4])
    min_y = min(vertices_offsets[1::4])
    max_y = max(vertices_offsets[1::4])
    min_z = min(vertices_offsets[2::4])
    max_z = max(vertices_offsets[2::4])

    buffer_range_offset = mathutils.Vector((min_x, min_y, min_z))
    buffer_range_valid = [(True if abs(max_x - min_x) > 0.001 else False),
                   (True if abs(max_y - min_y) > 0.001 else False),
                   (True if abs(max_z - min_z) > 0.001 else False)]
    buffer_range = mathutils.Vector(((max_x - min_x) if buffer_range_valid[0] else 1,
                             (max_y - min_y) if buffer_range_valid[1] else 1,
                             (max_z - min_z) if buffer_range_valid[2] else 1))

    for vertex_index in range(len(vertices_offsets) // 4):
        vertex_buffer_index = (vertex_index * 4)
        vertices_offsets[vertex_buffer_index + 0] = (vertices_offsets[vertex_buffer_index + 0] - buffer_range_offset.x) / buffer_range.x
        vertices_offsets[vertex_buffer_index + 1] = (vertices_offsets[vertex_buffer_index + 1] - buffer_range_offset.y) / buffer_range.y
        vertices_offsets[vertex_buffer_index + 2] = (vertices_offsets[vertex_buffer_index + 2] - buffer_range_offset.z) / buffer_range.z

    return vertices_offsets, (buffer_range_offset, buffer_range_valid, buffer_range)

def get_remapped_vertices_normal_buffer(vertices_normals: list, constantbias: bool) -> list:
    """
    Remap the normal buffer from the range [-1:1] to [0:1]

    :param vertices_normals: buffer of vertices normals
    :return: remapped buffer
    :rtype: list
    """

    if constantbias:
        buffer_range_offset = mathutils.Vector((-1, -1, -1))
        buffer_range_valid = [True, True, True]
        buffer_range = mathutils.Vector((2, 2, 2))
    else:
        min_x = min(vertices_normals[0::4])
        max_x = max(vertices_normals[0::4])
        min_y = min(vertices_normals[1::4])
        max_y = max(vertices_normals[1::4])
        min_z = min(vertices_normals[2::4])
        max_z = max(vertices_normals[2::4])

        buffer_range_offset = mathutils.Vector((min_x, min_y, min_z))
        buffer_range_valid = [(True if abs(max_x - min_x) > 0.001 else False),
                    (True if abs(max_y - min_y) > 0.001 else False),
                    (True if abs(max_z - min_z) > 0.001 else False)]
        buffer_range = mathutils.Vector(((max_x - min_x) if buffer_range_valid[0] else 1,
                                (max_y - min_y) if buffer_range_valid[1] else 1,
                                (max_z - min_z) if buffer_range_valid[2] else 1))

    for vertex_index in range(len(vertices_normals) // 4):
        vertex_buffer_index = (vertex_index * 4)
        vertices_normals[vertex_buffer_index + 0] = (vertices_normals[vertex_buffer_index + 0] - buffer_range_offset.x) / buffer_range.x
        vertices_normals[vertex_buffer_index + 1] = (vertices_normals[vertex_buffer_index + 1] - buffer_range_offset.y) / buffer_range.y
        vertices_normals[vertex_buffer_index + 2] = (vertices_normals[vertex_buffer_index + 2] - buffer_range_offset.z) / buffer_range.z

    return vertices_normals, (buffer_range_offset, buffer_range_valid, buffer_range)

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
def generate_texture(bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate and return a texture containing the provided pixel buffer

    :param bake_name: the bake operation's 'name'
    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: VAT image's width
    :param tex_height: VAT image's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename
    tags = { "BakeName": bake_name}
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

def export_texture(context: bpy.types.Context, image: bpy.types.Image, path: str, name: str, obj_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the offset or normal image

    :param context: Blender current execution context
    :param image: the VAT image to export
    :param path: export path
    :param name: file name
    :param obj_name:
    :param override_file: if an existing .exr file should be overriden
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    tags = {"BakeName": obj_name}
    success, msg, tex_path = get_path(path, name, ".exr", tags, override_file)
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

def get_best_texture_resolution(context: bpy.types.Context, num_frames: int, num_vertices: int) -> tuple[bool, str, int, int]:
    """
    Returns the best texture resolution for a given amount of frames & vertices to bake

    :param context: Blender current execution context
    :param num_frames: Number of frames to bake
    :param num_vertices: Number of vertices to bake per frame
    :return: the function's success, potential error message, texture width, texture height, frame 'height' and 'width'
    :rtype: tuple
    """
    settings = context.scene.VATBakerSettings

    #########
    # WIDTH #

    if (settings.tex_force_power_of_two):
        tex_width = 2
        while (tex_width < num_vertices and tex_width < settings.export_tex_max_width):
            tex_width *= 2
    else:
        tex_width = num_vertices
        if (tex_width > settings.export_tex_max_width):
            tex_width = settings.export_tex_max_width

    # how many lines of pixels per frame?
    bake_frame_height_float = num_vertices / float(tex_width)
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

            bake_frame_height_float = num_vertices / float(tex_width)
            bake_frame_height = math.ceil(bake_frame_height_float) if settings.tex_packing_mode == 'STACK' else bake_frame_height_float # else 'CONTINUOUS'
        elif tex_height < tex_width:
            tex_height = tex_width

    underflow = num_vertices < tex_width
    add_bake_report("tex_underflow", underflow)
    overflow = num_vertices > tex_width
    add_bake_report("tex_overflow", overflow)

    add_bake_report("tex_height", tex_height)
    add_bake_report("tex_width", tex_width)

    bake_frame_width = num_vertices / float(tex_width)
    add_bake_report("frame_width", bake_frame_width)
    add_bake_report("frame_height", bake_frame_height)

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
    settings = context.scene.VATBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeTarget"
    report = context.scene.VATBakerReport

    root = ET.Element("BakedData",
                      type="VertexAnimationTextures",
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
                             width=str(report.frame_width),
                             height=str(report.frame_height),
                             ref=str(report.ref))

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

    # textures info
    if report.tex_offset or report.normal_tex:
        tex_el = ET.SubElement(root, "Textures")

        if report.tex_offset_path != "":
            tex_path_el = ET.SubElement(tex_el, "Texture",
                                        type="Offset",
                                        mode=report.tex_offset_mode,
                                        width=str(report.tex_width),
                                        height=str(report.tex_height),
                                        path=report.tex_offset_path,
                                        remapped=str(report.tex_offset_remapped),
                                        range_x=str(report.tex_offset_range),
                                        range_y=str(report.tex_offset_range),
                                        range_z=str(report.tex_offset_range),
                                        range_offset_x=str(report.tex_offset_range_offset),
                                        range_offset_y=str(report.tex_offset_range_offset),
                                        range_offset_z=str(report.tex_offset_range_offset))
        if report.tex_normal_path != "":
            tex_path_el = ET.SubElement(tex_el, "Texture",
                                        type="Normal",
                                        width=str(report.tex_width),
                                        height=str(report.tex_height),
                                        path=report.tex_normal_path,
                                        remapped=str(report.tex_normal_remapped),
                                        range_x=str(report.tex_normal_range),
                                        range_y=str(report.tex_normal_range),
                                        range_z=str(report.tex_normal_range),
                                        range_offset_x=str(report.tex_normal_range_offset),
                                        range_offset_y=str(report.tex_normal_range_offset),
                                        range_offset_z=str(report.tex_normal_range_offset))

    # anims info
    if report.anims:
        anims_el = ET.SubElement(root, "Animations")
        for anim in report.anims:
            # for obj in anim.objs:
            #     obj_target = obj.get(custom_prop, None)
            #     obj_target = True if obj_target and obj_target.type == "MESH" else False
            anim_el = ET.SubElement(anims_el, "Animation",
                                    name=anim.name,
                                    start_frame=str(anim.start_frame - 1),
                                    #start_time=str(anim.start_time),
                                    end_frame=str(anim.end_frame - 1),
                                    #end_time=str(anim.end_time),
                                    frames=str(anim.end_frame - (anim.start_frame - 1)))

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