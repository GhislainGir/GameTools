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
import mathutils
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
    """
    settings = context.scene.TATBakerSettings

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
    """
    report = bpy.context.scene.TATBakerReport
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

    report.anims.clear()
    report.selected_anim = 0

    report.start_frame = 0
    report.end_frame = 0
    report.num_frames = 0
    report.frame_step = 0
    report.frame_step_mode = "GLOBAL"
    report.frame_height = 0.0
    report.frame_width = 0.0
    report.frame_rate = 0

    report.num_triangles = 0

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
    report.tex_position = None
    report.tex_position_export = False
    report.tex_position_path = ""
    report.tex_position_remapped = False
    report.tex_position_range_offset = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_position_range = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_normal = None
    report.tex_normal_export = False
    report.tex_normal_path = ""
    report.tex_normal_remapped = False
    report.tex_normal_range_offset = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_normal_range = mathutils.Vector((1.0, 1.0, 1.0))

    report.xml = False
    report.xml_path = ""

def add_bake_report(prop_name: str, prop_value):
    """
    Set a value in the bake report
    """
    setattr(bpy.context.scene.TATBakerReport, prop_name, prop_value)

def add_bake_report_anim(objs: list, name: str, frame_start: int, frame_end: int, frame_start_time: float, frame_end_time: float):
    """
    Set values in the bake report to describe an animation clip
    """
    report = bpy.context.scene.TATBakerReport

    report_anim = report.anims.add()
    for obj in objs:
        report_anim_obj = report_anim.objs.add()
        report_anim_obj.obj = obj
    report_anim.name = name
    report_anim.start_frame = frame_start
    report_anim.start_time = frame_start_time
    report_anim.end_frame = frame_end
    report_anim.end_time = frame_end_time

def export_bake_report(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML
    """
    return(export_xml(context))

###########
### NLA ###
def get_obj_nla_tracks(obj_to_bake: bpy.types.Object):
    """
    Return the list of NLA tracks the given object has, if any
    """
    if not obj_to_bake:
        return None

    if (obj_to_bake and obj_to_bake.animation_data and obj_to_bake.animation_data.nla_tracks):
        return obj_to_bake.animation_data.nla_tracks
    elif (obj_to_bake.parent and obj_to_bake.parent.animation_data and obj_to_bake.parent.animation_data.nla_tracks):
        return obj_to_bake.parent.animation_data.nla_tracks
    else:
        armature_mods = [mod for mod in obj_to_bake.modifiers if mod.type == "ARMATURE"]
        for armature_mod in armature_mods:
            if (armature_mod.object and armature_mod.object.animation_data and armature_mod.object.animation_data.nla_tracks):
                return armature_mod.object.animation_data.nla_tracks

    return None

def get_obj_nla_start_end_frames(obj_to_bake: bpy.types.Object) -> list:
    """
    Return the list of the object's NLA strips start/end frames
    """
    nla_frames = []

    if obj_to_bake:
        nla_tracks = get_obj_nla_tracks(obj_to_bake)
        if nla_tracks:
            for nla_track in nla_tracks:
                for nla_strip in nla_track.strips:
                    nla_frames.append((int(nla_strip.frame_start), int(nla_strip.frame_end)))

    return nla_frames

def get_bake_nla_strips(objs_to_bake: list) -> list:
    """
    Scan the NLA tracks of the given objects to return a list of unique NLA strips,
    paired with the list of meshes making use of it in their NLA tracks
    """
    nla_strips = []
    for obj in objs_to_bake:
        nla_tracks = get_obj_nla_tracks(obj)
        if nla_tracks:
            for nla_track in nla_tracks:
                for nla_strip in nla_track.strips:
                    nla_strips.append((nla_strip, obj))

    unique_nla_strips = []
    unique_nla_indices = []
    for nla_strip_index, nla_strip in enumerate(nla_strips):
        strip, obj = nla_strip
        objs_list = [obj]

        for nla_strip_index_compare, nla_strip_compare in enumerate(nla_strips):
            if nla_strip_index != nla_strip_index_compare:
                strip_compare, obj_compare = nla_strip_compare
                if (obj != obj_compare) and (strip.name == strip_compare.name) and (strip.frame_start == strip_compare.frame_start) and (strip.frame_end == strip_compare.frame_end):
                    objs_list.append(obj_compare)
                    unique_nla_indices.append(nla_strip_index_compare)

        if nla_strip_index not in unique_nla_indices:
                unique_nla_strips.append((strip, objs_list))

    return unique_nla_strips

def get_nla_strips_raw_frame_buffer(context: bpy.types.Context, nla_strips: list) -> list:
    """
    Compute a raw frame buffer from a list of NLA strips
    """
    settings = context.scene.TATBakerSettings

    frames_to_bake = []
    frames_to_bake_indices = []
    frame_step = settings.frame_range_custom_step if settings.frame_range_custom_step_mode == "NLACLIP" and settings.frame_range_custom_step > 1 else 1

    for nla_strip in nla_strips:
        strip, objs = nla_strip

        frame_start = int(strip.frame_start)
        frame_end = int(strip.frame_end)

        for frame in range(frame_start, frame_end + 1, frame_step):
            if frame in frames_to_bake_indices:
                frame_index = frames_to_bake_indices.index(frame)
                frames_to_bake[frame_index][1].append(nla_strip)
            else:
                frames_to_bake_indices.append(frame)
                frames_to_bake.append((frame, [nla_strip]))

    frames_to_bake.sort(key=lambda x: x[0])

    if settings.frame_range_custom_step_mode == "GLOBAL" and settings.frame_range_custom_step > 1:
        frames_to_bake = frames_to_bake[::settings.frame_range_custom_step]

    return frames_to_bake

def get_nla_strip_start_end_indices(nla_strip: object, frames_to_bake: list) -> tuple[int, int]:
    """
    Find where the NLA strip starts & ends in the given frame buffer.
    """
    strip, objs = nla_strip

    start = int(strip.frame_start)
    end = int(strip.frame_end)

    start_index = None
    end_index = None

    for frame_index, frame_data in enumerate(frames_to_bake):
        frame, frame_nla_clips = frame_data

        if len(frame_nla_clips) <= 0:
            continue

        if start_index is None:
            if frame == start:
                start_index = frame_index
            elif frame > start:
                start_index = min(len(frames_to_bake) - 1, max(0, frame_index - 1))

        if end_index is None:
            if frame == end:
                end_index = frame_index
            elif frame > end:
                end_index = min(len(frames_to_bake) - 1, max(start_index if start_index is not None else 0, frame_index - 1))

    if start_index is None:
        start_index = 0
    if end_index is None:
        end_index = len(frames_to_bake) - 1

    return (start_index, end_index)

############
### BAKE ###
def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object]:
    """
    Ensure the active & selected objects can lead to a valid bake and return the list of objects to include.
    TAT does not use retargeting and allows varying topology, so validation is minimal.
    """
    settings = context.scene.TATBakerSettings

    if context.view_layer.objects.active is None:
        return (False, "No active object", None, None)

    # deselect non-mesh objects & empty meshes
    for selected_obj in context.selected_objects:
        if selected_obj.type != "MESH":
            selected_obj.select_set(False)
        elif len(selected_obj.data.vertices) <= 0:
            selected_obj.select_set(False)

    if not context.selected_objects:
        return (False, "No object selected once filtered out", None, None)

    # cache selection
    objs_to_bake = []
    if settings.bake_mode == 'ANIMATION':
        objs_to_bake = list(context.selected_objects)
    else:  # MESHSEQUENCE
        names_of_objects_to_bake = [obj.name for obj in context.selected_objects]
        names_of_objects_to_bake.sort()
        for name in names_of_objects_to_bake:
            objs_to_bake.append(context.scene.objects[name])

    # deselect everything
    for obj_to_bake in objs_to_bake:
        obj_to_bake.select_set(False)

    active_obj = context.view_layer.objects.active
    if settings.bake_mode == 'MESHSEQUENCE':
        active_obj = objs_to_bake[0]

    context.view_layer.objects.active = None

    return (True, "", objs_to_bake, active_obj)

#############
### FRAME ###
def get_bake_frames_animation(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, tuple]:
    """
    Return the list of frames to bake for animation mode.
    TAT version: no padding, no reference frame.
    """
    settings = context.scene.TATBakerSettings

    nla_strips = get_bake_nla_strips(objs_to_bake)
    nla_strips = [nla_strip for nla_strip in nla_strips if nla_strip[0].name not in [s.name for s in settings.frame_range_nla_exclusion]]

    if settings.frame_range_mode == "NLA":
        if nla_strips:
            frames_to_bake = get_nla_strips_raw_frame_buffer(context, nla_strips)

            add_bake_report("frame_step", settings.frame_range_custom_step)
            add_bake_report("frame_step_mode", settings.frame_range_custom_step_mode)

            num_frames = len(frames_to_bake)
            add_bake_report("num_frames", num_frames)

            if num_frames < 2:
                return (False, str(num_frames) + " frames detected: too few frames to bake", (None, 0, 0))

            # report NLA strip start/end
            for nla_strip in nla_strips:
                strip, objs = nla_strip
                start_index, end_index = get_nla_strip_start_end_indices(nla_strip, frames_to_bake)
                start_frame = start_index + 1
                end_frame = end_index + 1
                start_time = (start_frame - 1) / num_frames
                end_time = end_frame / num_frames
                add_bake_report_anim(objs, strip.name, start_frame, end_frame, start_time, end_time)

            # convert to int buffer
            frames_to_bake = [frame_data[0] for frame_data in frames_to_bake]

            start_frame = min(frames_to_bake)
            add_bake_report("start_frame", start_frame)
            end_frame = max(frames_to_bake)
            add_bake_report("end_frame", end_frame)

            return (True, "", (frames_to_bake, start_frame, end_frame))
        else:
            return (False, "No NLA tracks or strips found", (None, 0, 0))
    else:  # CUSTOM or SCENE
        if settings.frame_range_mode == "CUSTOM":
            frame_start = settings.frame_range_custom_start
            frame_end = settings.frame_range_custom_end
            frame_step = settings.frame_range_custom_step
        else:  # SCENE
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
            frame_step = context.scene.frame_step

        add_bake_report("frame_step", frame_step)
        add_bake_report("frame_step_mode", "GLOBAL")

        frames_to_bake = []
        frames_to_bake_indices = list(range(frame_start, frame_end + 1, frame_step))

        num_frames = len(frames_to_bake_indices)
        add_bake_report("num_frames", num_frames)

        if num_frames < 2:
            return (False, str(num_frames) + " frames detected: too few frames to bake", (None, 0, 0))

        # scan NLA strips for reporting purposes
        for frame in frames_to_bake_indices:
            frame_nla_strips = []
            if nla_strips:
                for nla_strip in nla_strips:
                    strip, objs = nla_strip
                    start = int(strip.frame_start)
                    end = int(strip.frame_end)
                    if start <= frame_end or end >= frame_start:
                        frame_nla_strips.append(nla_strip)
                        start_frame_clamped = min(frame_end, max(frame_start, start))
                        end_frame_clamped = min(frame_end, max(frame_start, end))
                        start_time = (start_frame_clamped - 1) / num_frames
                        end_time = end_frame_clamped / num_frames
                        add_bake_report_anim(objs, strip.name, start_frame_clamped, end_frame_clamped, start_time, end_time)

            frames_to_bake.append((frame, frame_nla_strips))

        frames_to_bake = [frame_data[0] for frame_data in frames_to_bake]

        start_frame = min(frames_to_bake)
        add_bake_report("start_frame", start_frame)
        end_frame = max(frames_to_bake)
        add_bake_report("end_frame", end_frame)

        return (True, "", (frames_to_bake, start_frame, end_frame))

def get_bake_frames_sequence(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, tuple]:
    """
    Return the list of frames to bake for sequence mode.
    """
    frames_to_bake = list(range(len(objs_to_bake)))
    add_bake_report("frame_step", 1)

    num_frames = len(frames_to_bake)
    add_bake_report("num_frames", num_frames)

    if num_frames < 2:
        return (False, str(num_frames) + " frames detected: too few frames to bake", (frames_to_bake, 0, 0))

    start_frame = min(frames_to_bake)
    add_bake_report("start_frame", start_frame)
    end_frame = max(frames_to_bake)
    add_bake_report("end_frame", end_frame)

    return (True, "", (frames_to_bake, start_frame, end_frame))

def get_bake_frames(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, tuple]:
    """
    Return the list of frames to bake and the start/end frames.
    """
    settings = context.scene.TATBakerSettings

    add_bake_report("frame_rate", (context.scene.render.fps / context.scene.render.fps_base))

    if settings.bake_mode == "ANIMATION":
        return get_bake_frames_animation(context, objs_to_bake)
    else:
        return get_bake_frames_sequence(context, objs_to_bake)

##################
### TRIANGLES ###
def triangulate_mesh(bm: bmesh.types.BMesh):
    """
    Triangulate all faces of a bmesh in-place.
    """
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')

def get_max_triangle_count(context: bpy.types.Context, objs_to_bake: list, bake_frames_info: tuple) -> int:
    """
    Scan all frames to find the maximum triangle count across all frames and objects.
    This determines the texture width (max_triangles * 3 texels per row).
    """
    settings = context.scene.TATBakerSettings
    frames_to_bake, bake_start_frame, bake_end_frame = bake_frames_info

    max_triangles = 0
    dgraph = context.evaluated_depsgraph_get()

    if settings.bake_mode == 'ANIMATION':
        for frame in frames_to_bake:
            context.scene.frame_set(frame)
            dgraph.update()

            frame_triangles = 0
            for obj_to_bake in objs_to_bake:
                eval_obj = obj_to_bake.evaluated_get(dgraph)
                eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

                bm = bmesh.new()
                bm.from_mesh(eval_mesh)
                triangulate_mesh(bm)
                frame_triangles += len(bm.faces)
                bm.free()

                eval_obj.to_mesh_clear()

            max_triangles = max(max_triangles, frame_triangles)
    else:  # MESHSEQUENCE
        for obj_to_bake in objs_to_bake:
            eval_obj = obj_to_bake.evaluated_get(dgraph)
            eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

            bm = bmesh.new()
            bm.from_mesh(eval_mesh)
            triangulate_mesh(bm)
            max_triangles = max(max_triangles, len(bm.faces))
            bm.free()

            eval_obj.to_mesh_clear()

    return max_triangles

def get_bake_name(context: bpy.types.Context, active_object: bpy.types.Object) -> str:
    """
    Return the name to give to the bake operation.
    """
    settings = context.scene.TATBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.TAT"
    tags = {"BakeName": active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

#####################
### MAIN BAKE ###
def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function for Triangle Animation Textures.

    Bakes per-triangle position and normal data into textures. Each triangle
    occupies 3 consecutive texels. Triangle count may vary across frames;
    the frame with the most triangles determines the texture width. Unused
    triangle slots are filled with degenerate (0,0,0) data.
    """
    settings = context.scene.TATBakerSettings
    new_bake_report(context)

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    bake_start_time = time.time()

    # 1. Selection
    success, msg, objs_to_bake, active_object = get_bake_selection(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(1)

    # 2. Frame range
    success, msg, bake_frames_info = get_bake_frames(context, objs_to_bake)
    frames_to_bake, bake_start_frame, bake_end_frame = bake_frames_info
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(3)

    # 3. Scan all frames to find max triangle count
    num_frames = len(frames_to_bake)
    max_triangles = get_max_triangle_count(context, objs_to_bake, bake_frames_info)
    num_texels = max_triangles * 3
    add_bake_report("num_triangles", max_triangles)

    if max_triangles == 0:
        add_bake_report("success", False)
        msg = "No triangles found in any frame"
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(7)

    # 4. Texture resolution
    success, msg, tex_width, tex_height, bake_frame_height = get_best_texture_resolution(context, num_frames, num_texels)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(10)

    bake_name = get_bake_name(context, active_object)
    add_bake_report("name", bake_name)

    # 5. Buffer generation
    if settings.bake_mode == 'ANIMATION':
        success, msg, positions_buffer, normals_buffer, bounds_info = get_animation_triangles_buffers(
            context, objs_to_bake, bake_frames_info, bake_frame_height, tex_width, tex_height, max_triangles)
    else:  # MESHSEQUENCE
        success, msg, positions_buffer, normals_buffer, bounds_info = get_sequence_triangles_buffers(
            context, objs_to_bake, bake_frames_info, bake_frame_height, tex_width, tex_height, max_triangles)

    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(85)

    # 6. Post-processing
    if settings.normal_tex_remap:
        normals_buffer, buffer_range_info = get_remapped_buffer(normals_buffer, settings.normal_tex_remap_biasscale)
        buffer_range_offset, buffer_range_valid, buffer_range = buffer_range_info
        add_bake_report("tex_normal_remapped", True)
        add_bake_report("tex_normal_range_offset", buffer_range_offset)
        add_bake_report("tex_normal_range", buffer_range)

    if settings.position_tex_remap:
        positions_buffer, buffer_range_info = get_remapped_buffer(positions_buffer, False)
        buffer_range_offset, buffer_range_valid, buffer_range = buffer_range_info
        add_bake_report("tex_position_remapped", True)
        add_bake_report("tex_position_range_offset", buffer_range_offset)
        add_bake_report("tex_position_range", buffer_range)

    if settings.unit_invert_v:
        positions_buffer, normals_buffer = get_inverted_buffers(positions_buffer, normals_buffer, tex_width, tex_height)

    wm.progress_update(90)

    # 7. Generate textures
    img_position = None
    if settings.position_tex:
        success, msg, img_position = generate_texture(bake_name, settings.position_tex_file_name, positions_buffer, tex_width, tex_height)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("tex_position", img_position)

        if settings.export_tex and bpy.data.is_saved:
            success, msg, img_path = export_texture(context, img_position, settings.export_tex_file_path, settings.position_tex_file_name, bake_name, settings.export_tex_override)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            add_bake_report("tex_position_export", True)
            add_bake_report("tex_position_path", img_path)

    img_normal = None
    if settings.normal_tex:
        success, msg, img_normal = generate_texture(bake_name, settings.normal_tex_file_name, normals_buffer, tex_width, tex_height)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("tex_normal", img_normal)

        if settings.export_tex and bpy.data.is_saved:
            success, msg, img_path = export_texture(context, img_normal, settings.export_tex_file_path, settings.normal_tex_file_name, bake_name, settings.export_tex_override)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            add_bake_report("tex_normal_export", True)
            add_bake_report("tex_normal_path", img_path)

    wm.progress_update(93)

    # 8. Generate mesh (synthetic triangle buffer)
    success, msg, obj_to_export, bake_uvmap_index = generate_mesh(context, bake_name, max_triangles, tex_width, tex_height)
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

    wm.progress_update(95)

    if settings.previz_bounds:
        success, msg = display_bounds(context, bake_name + ".bounds", bounds_info)

    # 9. XML export
    if settings.export_xml and bpy.data.is_saved:
        success, msg, path = export_xml(context)
        add_bake_report("xml", True)
        add_bake_report("xml_path", path)

    wm.progress_update(98)

    # UX
    if obj_to_export:
        obj_to_export.select_set(True)

    context.scene.frame_start = bake_start_frame
    context.scene.frame_end = bake_end_frame

    add_bake_report("success", True)
    wm.progress_update(99)
    wm.progress_end()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

################
### MESH ###
def generate_mesh(context: bpy.types.Context, bake_name: str, max_triangles: int, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Object, int]:
    """
    Generate a synthetic triangle buffer mesh. Each triangle has 3 unique vertices
    (no sharing), UV-mapped so each vertex points to its corresponding texel in the
    position texture. The vertex positions are set to the origin since the vertex
    shader will drive them from texture lookups.
    """
    settings = context.scene.TATBakerSettings
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.TAT"

    name = bake_name if bake_name != "" else "BakedMesh.TAT"
    mesh = bpy.data.meshes.new(name)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new(mesh_uvmap_name)

    for tri_index in range(max_triangles):
        texel_base = tri_index * 3

        # create 3 vertices at origin (shader will reposition from texture)
        v0 = bm.verts.new((0.0, 0.0, 0.0))
        v1 = bm.verts.new((0.0, 0.0, 0.0))
        v2 = bm.verts.new((0.0, 0.0, 0.0))

        face = bm.faces.new([v0, v1, v2])

        # UV: map each vertex to its texel center
        for vert_offset, loop in enumerate(face.loops):
            texel_index = texel_base + vert_offset
            u = (0.5 + (texel_index % tex_width)) / tex_width
            v = (0.5 + (texel_index // tex_width)) / tex_height
            if settings.unit_invert_v:
                v = 1.0 - v
            loop[uv_layer].uv = (u, v)

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    context.scene.collection.objects.link(obj)

    context.view_layer.objects.active = obj
    obj.select_set(True)

    # find the UV layer index
    uvmap_index = 0
    for i, uv_layer in enumerate(mesh.uv_layers):
        if uv_layer.name == mesh_uvmap_name:
            uvmap_index = i
            break

    return (True, "", obj, uvmap_index)

############################
### BUFFER GENERATION ###
def get_animation_triangles_buffers(context: bpy.types.Context, objs_to_bake: list, bake_frames_info: tuple,
                                     bake_frame_height: int, tex_width: int, tex_height: int,
                                     max_triangles: int) -> tuple[bool, str, list, list, tuple]:
    """
    Generate position and normal buffers by iterating frames and triangulating the evaluated mesh.
    Each triangle occupies 3 consecutive texels. Unused triangle slots are filled with (0,0,0,1).
    """
    settings = context.scene.TATBakerSettings
    frames_to_bake, bake_start_frame, bake_end_frame = bake_frames_info

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    # initialize RGBA buffers with (0, 0, 0, 1)
    buffer_size = tex_width * tex_height * 4
    positions_buffer = [0.0] * buffer_size
    normals_buffer = [0.0] * buffer_size
    # set alpha to 1.0
    for i in range(3, buffer_size, 4):
        positions_buffer[i] = 1.0
        normals_buffer[i] = 1.0

    # bounds tracking
    min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    dgraph = context.evaluated_depsgraph_get()

    for frame_index, frame in enumerate(frames_to_bake):
        context.scene.frame_set(frame)
        dgraph.update()

        # buffer offset for this frame's row(s)
        buffer_frame_offset = frame_index * tex_width * bake_frame_height * 4

        tri_offset = 0  # cumulative triangle index across all objects in this frame

        for obj_to_bake in objs_to_bake:
            eval_obj = obj_to_bake.evaluated_get(dgraph)
            eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            eval_mesh.transform(eval_obj.matrix_world)

            bm = bmesh.new()
            bm.from_mesh(eval_mesh)
            triangulate_mesh(bm)
            bm.normal_update()

            for face in bm.faces:
                if len(face.verts) != 3:
                    continue

                face_normal = face.normal.copy()

                for vert_offset, vert in enumerate(face.verts):
                    texel_index = (tri_offset * 3) + vert_offset
                    buffer_index = buffer_frame_offset + (texel_index * 4)

                    if buffer_index + 3 >= buffer_size:
                        break

                    # position: world-space, scaled and axis-inverted
                    pos = vert.co * signed_scale

                    # axis order swizzle
                    if settings.unit_axis_order != "XYZ":
                        pos = mathutils.Vector([getattr(pos, axis.lower()) for axis in settings.unit_axis_order])

                    positions_buffer[buffer_index + 0] = pos.x
                    positions_buffer[buffer_index + 1] = pos.y
                    positions_buffer[buffer_index + 2] = pos.z

                    # normal: face normal, inverted axes, normalized
                    nor = face_normal * signed_axis
                    nor.normalize()

                    if settings.unit_axis_order != "XYZ":
                        nor = mathutils.Vector([getattr(nor, axis.lower()) for axis in settings.unit_axis_order])

                    normals_buffer[buffer_index + 0] = nor.x
                    normals_buffer[buffer_index + 1] = nor.y
                    normals_buffer[buffer_index + 2] = nor.z

                    # bounds tracking (on positions)
                    min_bounds.x = min(min_bounds.x, pos.x)
                    min_bounds.y = min(min_bounds.y, pos.y)
                    min_bounds.z = min(min_bounds.z, pos.z)
                    max_bounds.x = max(max_bounds.x, pos.x)
                    max_bounds.y = max(max_bounds.y, pos.y)
                    max_bounds.z = max(max_bounds.z, pos.z)

                tri_offset += 1

            bm.free()
            eval_obj.to_mesh_clear()

    # bounds info tuple (compatible with display_bounds)
    zero = mathutils.Vector((0.0, 0.0, 0.0))
    bounds_info = (min_bounds, max_bounds, min_bounds, max_bounds, zero, zero)

    return (True, "", positions_buffer, normals_buffer, bounds_info)

def get_sequence_triangles_buffers(context: bpy.types.Context, objs_to_bake: list, bake_frames_info: tuple,
                                    bake_frame_height: int, tex_width: int, tex_height: int,
                                    max_triangles: int) -> tuple[bool, str, list, list, tuple]:
    """
    Generate position and normal buffers from a mesh sequence.
    Each object in the selection represents one frame.
    """
    settings = context.scene.TATBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    # initialize RGBA buffers with (0, 0, 0, 1)
    buffer_size = tex_width * tex_height * 4
    positions_buffer = [0.0] * buffer_size
    normals_buffer = [0.0] * buffer_size
    for i in range(3, buffer_size, 4):
        positions_buffer[i] = 1.0
        normals_buffer[i] = 1.0

    min_bounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_bounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    dgraph = context.evaluated_depsgraph_get()

    for frame_index, obj_to_bake in enumerate(objs_to_bake):
        buffer_frame_offset = frame_index * tex_width * bake_frame_height * 4

        eval_obj = obj_to_bake.evaluated_get(dgraph)
        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        eval_mesh.transform(eval_obj.matrix_world)

        bm = bmesh.new()
        bm.from_mesh(eval_mesh)
        triangulate_mesh(bm)
        bm.normal_update()

        tri_offset = 0
        for face in bm.faces:
            if len(face.verts) != 3:
                continue

            face_normal = face.normal.copy()

            for vert_offset, vert in enumerate(face.verts):
                texel_index = (tri_offset * 3) + vert_offset
                buffer_index = buffer_frame_offset + (texel_index * 4)

                if buffer_index + 3 >= buffer_size:
                    break

                pos = vert.co * signed_scale

                if settings.unit_axis_order != "XYZ":
                    pos = mathutils.Vector([getattr(pos, axis.lower()) for axis in settings.unit_axis_order])

                positions_buffer[buffer_index + 0] = pos.x
                positions_buffer[buffer_index + 1] = pos.y
                positions_buffer[buffer_index + 2] = pos.z

                nor = face_normal * signed_axis
                nor.normalize()

                if settings.unit_axis_order != "XYZ":
                    nor = mathutils.Vector([getattr(nor, axis.lower()) for axis in settings.unit_axis_order])

                normals_buffer[buffer_index + 0] = nor.x
                normals_buffer[buffer_index + 1] = nor.y
                normals_buffer[buffer_index + 2] = nor.z

                min_bounds.x = min(min_bounds.x, pos.x)
                min_bounds.y = min(min_bounds.y, pos.y)
                min_bounds.z = min(min_bounds.z, pos.z)
                max_bounds.x = max(max_bounds.x, pos.x)
                max_bounds.y = max(max_bounds.y, pos.y)
                max_bounds.z = max(max_bounds.z, pos.z)

            tri_offset += 1

        bm.free()
        eval_obj.to_mesh_clear()

    zero = mathutils.Vector((0.0, 0.0, 0.0))
    bounds_info = (min_bounds, max_bounds, min_bounds, max_bounds, zero, zero)

    return (True, "", positions_buffer, normals_buffer, bounds_info)

#######################
### POST-PROCESSING ###
def get_inverted_buffers(buffer_a: list, buffer_b: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """
    Re-order buffers so that pixel buffer is flipped in V (invert image vertically).
    """
    buffer_a_inv = []
    buffer_b_inv = []
    for i in reversed(range(tex_height)):
        row = tex_width * 4
        row_offset = i * row
        buffer_a_inv.extend(buffer_a[row_offset:row_offset + row])
        buffer_b_inv.extend(buffer_b[row_offset:row_offset + row])

    return (buffer_a_inv, buffer_b_inv)

def get_remapped_buffer(buffer: list, constantbias: bool) -> tuple[list, tuple]:
    """
    Remap buffer values to [0:1] range.
    If constantbias is True, assume [-1:1] range (useful for normals).
    """
    if constantbias:
        buffer_range_offset = mathutils.Vector((-1, -1, -1))
        buffer_range_valid = [True, True, True]
        buffer_range = mathutils.Vector((2, 2, 2))
    else:
        min_x = min(buffer[0::4])
        max_x = max(buffer[0::4])
        min_y = min(buffer[1::4])
        max_y = max(buffer[1::4])
        min_z = min(buffer[2::4])
        max_z = max(buffer[2::4])

        buffer_range_offset = mathutils.Vector((min_x, min_y, min_z))
        buffer_range_valid = [(abs(max_x - min_x) > 0.001),
                              (abs(max_y - min_y) > 0.001),
                              (abs(max_z - min_z) > 0.001)]
        buffer_range = mathutils.Vector(((max_x - min_x) if buffer_range_valid[0] else 1,
                                         (max_y - min_y) if buffer_range_valid[1] else 1,
                                         (max_z - min_z) if buffer_range_valid[2] else 1))

    for pixel_index in range(len(buffer) // 4):
        idx = pixel_index * 4
        buffer[idx + 0] = (buffer[idx + 0] - buffer_range_offset.x) / buffer_range.x
        buffer[idx + 1] = (buffer[idx + 1] - buffer_range_offset.y) / buffer_range.y
        buffer[idx + 2] = (buffer[idx + 2] - buffer_range_offset.z) / buffer_range.z

    return buffer, (buffer_range_offset, buffer_range_valid, buffer_range)

##############
### BOUNDS ###
def display_bounds(context: bpy.types.Context, bake_name: str, bounds_info: tuple) -> tuple[bool, str]:
    """
    Generate a world aligned bounding box mesh matching the animation's overall volume.
    """
    settings = context.scene.TATBakerSettings
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis / settings.unit_scale

    if bake_name is None:
        return (False, "Invalid name")

    ref_min_bounds, ref_max_bounds, min_bounds_actual, max_bounds_actual, min_bounds_offset, max_bounds_offset = bounds_info

    # for TAT, bounds are already in scaled space, convert back to world space for display
    display_min = ref_min_bounds * signed_scale
    display_max = ref_max_bounds * signed_scale

    bounds_verts = [
        mathutils.Vector((display_min.x, display_min.y, display_min.z)),
        mathutils.Vector((display_min.x, display_min.y, display_max.z)),
        mathutils.Vector((display_min.x, display_max.y, display_max.z)),
        mathutils.Vector((display_min.x, display_max.y, display_min.z)),
        mathutils.Vector((display_max.x, display_max.y, display_max.z)),
        mathutils.Vector((display_max.x, display_max.y, display_min.z)),
        mathutils.Vector((display_max.x, display_min.y, display_min.z)),
        mathutils.Vector((display_max.x, display_min.y, display_max.z))
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

        col = bpy.data.collections.get("TriAnim", None)
        if col is None:
            col = bpy.data.collections.new("TriAnim")
            bpy.context.scene.collection.children.link(col)

        col.objects.link(bounds_obj)
    else:
        if bounds_obj.type == "MESH":
            bounds_mesh = bounds_obj.data
            if len(bounds_mesh.vertices) == 8:
                for bounds_vertex_index, bounds_vertex in enumerate(bounds_mesh.vertices):
                    bounds_vertex.co = bounds_verts[bounds_vertex_index]
            else:
                return (False, "An object named " + bake_name + " already exists but it doesn't look like it's from a previous bake")
        else:
            return (False, "An object named " + bake_name + " already exists but isn't a mesh")

    return (True, "")

################
### TEXTURES ###
def generate_texture(bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Create a Blender image from the given pixel buffer.
    """
    expected_size = tex_width * tex_height * 4
    if len(buffer) != expected_size:
        return (False, "Buffer size mismatch: expected " + str(expected_size) + " but got " + str(len(buffer)), None)

    tags = {"BakeName": bake_name}
    image_name = replace_tags(filename, tags)
    image_name += ".exr"

    # remove existing image
    image = bpy.data.images.get(image_name)
    if image:
        if image.packed_file and bpy.data.is_saved:
            pass
        bpy.data.images.remove(image)

    image = bpy.data.images.new(name=image_name, width=tex_width, height=tex_height, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.file_format = 'OPEN_EXR'
    image.use_half_precision = False
    image.pixels.foreach_set(buffer)
    image.use_fake_user = True
    if bpy.data.is_saved:
        image.pack()

    return (True, "", image)

def export_texture(context: bpy.types.Context, image: bpy.types.Image, file_path: str, file_name: str, bake_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the texture to disk as an EXR file.
    """
    tags = {"BakeName": bake_name}
    success, msg, export_path = get_path(file_path, replace_tags(file_name, tags), ".exr", {}, override_file)
    if not success:
        return (False, msg, None)

    # temporarily override render settings for EXR export
    original_format = context.scene.render.image_settings.file_format
    original_depth = context.scene.render.image_settings.color_depth
    original_codec = context.scene.render.image_settings.exr_codec

    try:
        context.scene.render.image_settings.file_format = 'OPEN_EXR'
        context.scene.render.image_settings.color_depth = '32'
        context.scene.render.image_settings.exr_codec = 'NONE'

        image.save_render(filepath=export_path)
    finally:
        context.scene.render.image_settings.file_format = original_format
        context.scene.render.image_settings.color_depth = original_depth
        context.scene.render.image_settings.exr_codec = original_codec

    return (True, "", export_path)

##########################
### TEXTURE RESOLUTION ###
def get_best_texture_resolution(context: bpy.types.Context, num_frames: int, num_texels: int) -> tuple[bool, str, int, int, int]:
    """
    Returns the best texture resolution for a given amount of frames & texels (max_triangles * 3).
    TAT always uses STACK/ADJACENT layout (one row per frame, no continuous packing).
    """
    settings = context.scene.TATBakerSettings

    # WIDTH
    if settings.tex_force_power_of_two:
        tex_width = 2
        while tex_width < num_texels and tex_width < settings.export_tex_max_width:
            tex_width *= 2
    else:
        tex_width = num_texels
        if tex_width > settings.export_tex_max_width:
            tex_width = settings.export_tex_max_width

    # how many rows per frame?
    bake_frame_height = math.ceil(num_texels / float(tex_width))

    # fallback to max width if data can't fit
    if (num_frames * bake_frame_height) > settings.export_tex_max_height:
        tex_width = settings.export_tex_max_width
        bake_frame_height = math.ceil(num_texels / float(tex_width))

    if tex_width > settings.export_tex_max_width:
        return (False, "Too many triangles for the maximum texture width", 0, 0, 0)

    # HEIGHT
    tex_height = num_frames * bake_frame_height

    if settings.tex_force_power_of_two:
        pot_height = 2
        while pot_height < tex_height:
            pot_height *= 2
        tex_height = pot_height

    if tex_height > settings.export_tex_max_height:
        return (False, "Too many frames for the maximum texture height", 0, 0, 0)

    if settings.tex_force_power_of_two and settings.tex_force_power_of_two_square:
        if tex_width < tex_height:
            tex_width = tex_height
            bake_frame_height = math.ceil(num_texels / float(tex_width))
        elif tex_height < tex_width:
            tex_height = tex_width

    underflow = num_texels < tex_width
    overflow = num_texels > tex_width

    bake_frame_width = min(num_texels, tex_width)

    add_bake_report("tex_width", tex_width)
    add_bake_report("tex_height", tex_height)
    add_bake_report("tex_underflow", underflow)
    add_bake_report("tex_overflow", overflow)
    add_bake_report("frame_width", bake_frame_width)
    add_bake_report("frame_height", bake_frame_height)

    return (True, "", tex_width, tex_height, bake_frame_height)

################
### MESH FBX ###
def export_mesh_selection(context: bpy.types.Context, bake_name: str) -> tuple[bool, str, str]:
    """
    Export the active/selected mesh object to FBX.
    """
    settings = context.scene.TATBakerSettings

    tags = {"BakeName": bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML.
    """
    settings = context.scene.TATBakerSettings
    report = context.scene.TATBakerReport

    root = ET.Element("BakedData",
                      type="TriangleAnimationTextures",
                      ID=report.ID,
                      version="1.0")

    # unit
    ET.SubElement(root, "Unit",
                  system=report.unit_system,
                  unit=str(report.unit_unit),
                  length=str(report.unit_length),
                  unit_scale=str(report.unit_scale),
                  unit_invert_x=str(report.unit_invert_x),
                  unit_invert_y=str(report.unit_invert_y),
                  unit_invert_z=str(report.unit_invert_z),
                  unit_invert_v=str(report.unit_invert_v),
                  unit_axis_order=report.unit_axis_order)

    # frames
    ET.SubElement(root, "Frames",
                  count=str(report.num_frames),
                  rate=str(report.frame_rate),
                  width=str(report.frame_width),
                  height=str(report.frame_height))

    # mesh
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""
    ET.SubElement(root, "Mesh",
                  path=mesh_export_path,
                  uv_index=str(report.mesh_uvmap_index),
                  max_triangles=str(report.num_triangles))

    # textures
    if report.tex_position or report.tex_normal:
        tex_el = ET.SubElement(root, "Textures")

        if report.tex_position_path != "":
            ET.SubElement(tex_el, "Texture",
                          type="Position",
                          width=str(report.tex_width),
                          height=str(report.tex_height),
                          path=report.tex_position_path,
                          remapped=str(report.tex_position_remapped),
                          range_x=str(report.tex_position_range[0]),
                          range_y=str(report.tex_position_range[1]),
                          range_z=str(report.tex_position_range[2]),
                          range_offset_x=str(report.tex_position_range_offset[0]),
                          range_offset_y=str(report.tex_position_range_offset[1]),
                          range_offset_z=str(report.tex_position_range_offset[2]))
        if report.tex_normal_path != "":
            ET.SubElement(tex_el, "Texture",
                          type="Normal",
                          width=str(report.tex_width),
                          height=str(report.tex_height),
                          path=report.tex_normal_path,
                          remapped=str(report.tex_normal_remapped),
                          range_x=str(report.tex_normal_range[0]),
                          range_y=str(report.tex_normal_range[1]),
                          range_z=str(report.tex_normal_range[2]),
                          range_offset_x=str(report.tex_normal_range_offset[0]),
                          range_offset_y=str(report.tex_normal_range_offset[1]),
                          range_offset_z=str(report.tex_normal_range_offset[2]))

    # animations
    if report.anims:
        anims_el = ET.SubElement(root, "Animations")
        for anim in report.anims:
            ET.SubElement(anims_el, "Animation",
                          name=anim.name,
                          start_frame=str(anim.start_frame - 1),
                          end_frame=str(anim.end_frame - 1),
                          frames=str(anim.end_frame - (anim.start_frame - 1)))

    # write xml
    tree = ET.ElementTree(root)
    if settings.export_xml_mode == "MESHPATH" and report.mesh_path != "":
        export_path = os.path.join(os.path.dirname(report.mesh_path), report.name + ".xml")
        tree.write(export_path)
        return (True, "", export_path)
    else:
        success, msg, export_path = get_path(settings.export_xml_file_path, settings.export_xml_file_name if settings.export_xml_file_name != "" else report.name, ".xml", {}, settings.export_xml_override)
        if success:
            tree.write(export_path)
            return (True, "", export_path)
        else:
            return (False, msg, "")

#########################
### PATHS & FILENAMES ###
def get_path(file_path: str, file_name: str, file_ext: str, tags: dict, override_file: bool) -> tuple[bool, str, str]:
    """
    Compile path/name/extension into a path on disk, and perform safety checks.
    """
    file_exts = [".png", ".exr", ".fbx", ".xml"]
    if file_ext not in file_exts:
        return (False, "Invalid File Extension", "")

    file_name = replace_tags(file_name, tags)
    export_path = os.path.abspath(os.path.join(bpy.path.abspath(file_path), file_name + file_ext))
    success, msg = check_path(export_path, override_file)

    return (success, msg, export_path)

def replace_tags(file_name: str, tags: dict) -> str:
    """
    Scan the provided string and replace any <tag> with the provided tags dictionary.
    """
    for tag_key, tag_value in tags.items():
        tag = "<" + tag_key + ">"
        if tag in file_name:
            file_name = file_name.replace(tag, tag_value)

    return file_name

def check_path(disk_path: str, override_file: bool) -> tuple[bool, str]:
    """
    Check that the directory exists and is writable, and check file override.
    """
    dir = os.path.dirname(disk_path)
    if not os.path.isdir(dir):
        return (False, f"Directory does not exist: {dir}")

    if not os.access(dir, os.W_OK):
        return (False, f"Directory is not writable: {dir}")

    if os.path.isfile(disk_path) and not override_file:
        return (False, f"File already exists: {disk_path}")

    return (True, "")
