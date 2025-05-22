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
import math
import os
import sys
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

    :param context: Blender current execution context
    :return: None
    :rtype: None
    """
    settings = context.scene.FFTOCEANBAKERSettings

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
    report = bpy.context.scene.FFTOCEANBAKERReport
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

    report.start_frame = 0
    report.end_frame = 0
    report.num_frames = 0
    report.frame_step = 0
    report.frame_size = 0
    report.frame_rate = 0
    
    report.frame_sort_mode = ""
    report.frames_per_row = 0
    report.frame_padding = 0
    
    report.subd = 0
    report.ocean_time = 0.0
    report.ocean_size = 0.0
    report.ocean_spatial_size = 0
    report.ocean_depth = 0.0
    report.ocean_seed = 0
    report.ocean_scale = 0.0
    report.ocean_smallest_wave = 0.0
    report.ocean_choppiness = 0.0
    report.ocean_wind_vel = 0.0
    report.ocean_alignment = 0.0
    report.ocean_direction = 0.0
    report.ocean_damping = 0.0
    report.ocean_clear = False
    report.ocean_from_active = False

    report.mesh = None
    report.mesh_export = False
    report.mesh_generate = False
    report.mesh_path = ""
    report.mesh_min_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.mesh_max_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))

    report.tex_width = 0
    report.tex_height = 0

    report.tex_mode = ""
    report.tex_offset = None
    report.tex_offset_mode = ""
    report.tex_offset_export = False
    report.tex_offset_path = ""
    report.tex_offset_remapped = False
    report.tex_offset_range_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.tex_offset_range = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_normal = None
    report.tex_normal_export = False
    report.tex_normal_path = ""
    report.tex_normal_remapped = False

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

def export_bake_report(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    return(export_xml(context))

############
### BAKE ###
def get_bake_frames(context: bpy.types.Context) -> tuple[list, int, int]:
    """
    Return the list of frames to bake and the start/end frames.

    :param context: Blender current execution context
    :return: list of frames in order, bake start & end frames
    :rtype: tuple
    """

    settings = context.scene.FFTOCEANBAKERSettings

    add_bake_report("frame_rate", (context.scene.render.fps / context.scene.render.fps_base))

    if settings.frame_range_mode == "SCENE":
        frames_to_bake = list(range(context.scene.frame_start, context.scene.frame_end + 1, context.scene.frame_step))
        add_bake_report("frame_step", context.scene.frame_step)
    else: # CUSTOM
        frames_to_bake = list(range(settings.frame_range_custom_start, settings.frame_range_custom_end + 1, settings.frame_range_custom_step))
        add_bake_report("frame_step", settings.frame_range_custom_step)

    return (frames_to_bake, min(frames_to_bake), max(frames_to_bake))

def get_bake_frame_size(context: bpy.types.Context) -> int:
    """
    Return the size of each frame. Size is both the width & height since frame are squared
    
    :param context: Blender current execution context
    :return: frame size (width & height)
    :rtype: int
    """
    
    settings = context.scene.FFTOCEANBAKERSettings
    if settings.frame_size_mode == "SUBDIVISIONS":
        subd = max(2, settings.subd)
        return subd * subd
    else: # CUSTOM
        return max(2, settings.frame_size_custom)

def get_bake_frame_padding(context: bpy.types.Context, clamp=bool) -> int:
    """
    Return the amount of padding to add to each frame, in pixels, on one side

    :param context: Blender current execution context
    :param clamp: Enable to clamp the padding as to not exceed the frame's resolution
    :return: amount of padding to add to each frame, in pixels, on one side
    :rtype: int
    """
    settings = context.scene.FFTOCEANBAKERSettings
    if settings.frame_padding_mode == "MIPLEVEL":
        padding = pow(2, max(0, settings.frame_padding_mips - 1))
    elif settings.frame_padding_mode == "PIXELS":
        padding = max(0, settings.frame_padding_pixels)
    else: # NONE
        padding = 0

    if clamp:
        subd = max(2, settings.subd)
        res = subd * subd
        return min(padding, res)
    else:
        return padding

def get_bake_name(context: bpy.types.Context) -> str:
    """
    Return the name to give to the bake operation.

    :param context: Blender current execution context
    :return: the bake operation's 'name'
    :rtype: string
    """

    settings = context.scene.FFTOCEANBAKERSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.FFT"
    return name

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings
    new_bake_report(context)

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #

    bake_start_time = time.time()

    frames_to_bake, bake_frame_start, bake_frame_end = get_bake_frames(context)
    add_bake_report("start_frame", bake_frame_start)
    add_bake_report("end_frame", bake_frame_end)
    
    num_frames = len(frames_to_bake)
    add_bake_report("num_frames", num_frames)
    if num_frames <= 0:
        add_bake_report("success", False)
        add_bake_report("msg", "Too few frames to bake")
        return (False, "ERROR", "Too few frames to bake")

    wm.progress_update(5)

    bake_name = get_bake_name(context)
    add_bake_report("name", bake_name)

    wm.progress_update(7)

    #########
    # OCEAN #

    success, msg, obj = generate_ocean_mesh(context, bake_name)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    wm.progress_update(8)

    for selected_obj in context.selected_objects:
        selected_obj.select_set(False)

    active_obj = context.view_layer.objects.active
    context.view_layer.objects.active = None # blank canvas

    success, msg, extents = setup_ocean_modifiers(context, obj, active_obj, bake_frame_start, bake_frame_end)
    if not success:
        clear_ocean_mesh(obj)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    wm.progress_update(10)

    ########
    # BAKE #

    success, msg, tex_offsets, tex_normals = generate_frames(context, obj, frames_to_bake, extents)
    if settings.ocean_clear:
        clear_ocean_mesh(obj)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    ############
    # TEXTURES #

    add_bake_report("tex_mode", settings.tex_mode)
    if settings.tex_mode == "FLIPBOOK":
        success, msg, num_frames_x, num_frames_y, tex_width, tex_height = get_flipbook_frames(context, num_frames)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, "ERROR", msg)
        
        add_bake_report("tex_width", tex_width)
        add_bake_report("tex_height", tex_height)
        add_bake_report("frame_size", get_bake_frame_size(context))

        if settings.offset_tex:
            success, msg, buffer_offset = get_flipbook_buffer(context, tex_offsets, num_frames_x, num_frames_y, tex_width, tex_height)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            success, msg, tex_offset = generate_texture("offset", buffer_offset, tex_width, tex_height)
            clear_textures(tex_offsets)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)
            
            add_bake_report("tex_offset", tex_offset)

            if settings.export_tex:
                success, msg, tex_offset_path = export_texture(context, tex_offset, settings.export_tex_file_path, settings.offset_tex_file_name, bake_name, settings.export_tex_override)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, 'ERROR', msg)
                add_bake_report("tex_offset_export", True)
                add_bake_report("tex_offset_path", tex_offset_path)

        if settings.normal_tex:
            success, msg, buffer_normal = get_flipbook_buffer(context, tex_normals, num_frames_x, num_frames_y, tex_width, tex_height)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            success, msg, tex_normal = generate_texture("normal", buffer_normal, tex_width, tex_height)
            clear_textures(tex_normals)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            add_bake_report("tex_normal", tex_normal)

            if settings.export_tex:
                success, msg, tex_normal_path = export_texture(context, tex_normal, settings.export_tex_file_path, settings.normal_tex_file_name, bake_name, settings.export_tex_override)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, 'ERROR', msg)
                add_bake_report("tex_normal_export", True)
                add_bake_report("tex_normal_path", tex_normal_path)
    else:
        add_bake_report("tex_offset", tex_offsets[0])
        add_bake_report("tex_normal", tex_normals[0])

        num_frames_x = 1
        num_frames_y = 1

    ########
    # MESH #

    if settings.generate_mesh:
        add_bake_report("mesh_generate", settings.generate_mesh)

        success, msg, obj_to_export = generate_mesh(context, bake_name, num_frames_x, num_frames_y)
        if success:
            add_bake_report("mesh", obj_to_export)
    else:
        obj_to_export = None

    wm.progress_update(92)

    if obj_to_export and settings.export_mesh:
        success, msg, mesh_path = export_mesh_selection(context, bake_name)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("mesh_export", True)
        add_bake_report("mesh_path", mesh_path)

    
    wm.progress_update(94)

    #######
    # XML #

    if settings.export_xml:
        success, msg, path = export_xml(context)
        add_bake_report("xml", True)
        add_bake_report("xml_path", path)

    wm.progress_update(98)

    ######
    # UX #
    if obj_to_export:
        obj_to_export.select_set(True)

    context.scene.frame_start = bake_frame_start
    context.scene.frame_end = bake_frame_end

    add_bake_report("success", True)
    wm.progress_update(99)
    wm.progress_end()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

#############
### OCEAN ###
def generate_ocean_mesh(context: bpy.types.Context, bake_name: str):
    """
    Generate the empty mesh that is going to receive the ocean modifier
    
    :param context: Blender current execution context
    :param bake_name: the bake operation's 'name'
    :return: the function's success, potential error message, generated mesh
    """

    name = bake_name if bake_name != "" else "BakedFFTOcean"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    context.scene.collection.objects.link(obj)

    return (True, "", obj)

def clear_ocean_mesh(obj: bpy.types.Object):
    """
    Remove the ocean mesh

    :param obj: ocean mesh object to get rid of
    :return: None
    :rtype: None
    """

    if obj:
        bpy.data.objects.remove(obj)

def add_ocean_modifier(context: bpy.types.Context, obj: bpy.types.Object, first_frame: int, last_frame: int, flip=bool):
    """
    Add and configure an ocean mesh to the given object
    
    :param context: Blender current execution context
    :param obj: object to receive the ocean modifier
    :param first_frame: the animation's start frame (inclusive)
    :param last_frame: the animation's end frame (inclusive)
    :param flip: flip the ocean modifier's animation to create the time loop mechanism
    :return: the function's success, potential error message, the ocean modifier added
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings

    ocean_modifier = obj.modifiers.new(name="Ocean", type='OCEAN')
    ocean_modifier.geometry_mode = "DISPLACE" if flip else "GENERATE"
    ocean_modifier.repeat_x = 1
    ocean_modifier.repeat_y = 1

    subd = max(2, settings.subd)
    ocean_modifier.viewport_resolution = subd
    ocean_modifier.resolution = subd
    ocean_modifier.size = settings.ocean_size
    ocean_modifier.spatial_size = settings.ocean_spatial_size
    ocean_modifier.depth = settings.ocean_depth
    ocean_modifier.random_seed = settings.ocean_seed
    ocean_modifier.wave_scale_min = settings.ocean_smallest_wave
    ocean_modifier.choppiness = settings.ocean_choppiness
    ocean_modifier.wind_velocity = settings.ocean_wind_vel
    ocean_modifier.wave_alignment = settings.ocean_alignment
    ocean_modifier.wave_direction = settings.ocean_direction
    ocean_modifier.damping = settings.ocean_damping

    ocean_modifier.time = 0.0 if flip else settings.ocean_time
    ocean_modifier.keyframe_insert(data_path="time", frame=first_frame)
    ocean_modifier.time = settings.ocean_time if flip else (settings.ocean_time * 2)
    ocean_modifier.keyframe_insert(data_path="time", frame=last_frame + 1) # offset by one frame to avoid duplicating start/end frames

    debug = False
    if debug:
        ocean_modifier.wave_scale = 0.0
    else:
        ocean_modifier.wave_scale = 0.0 if flip else settings.ocean_scale
        ocean_modifier.keyframe_insert(data_path="wave_scale", frame=first_frame)
        ocean_modifier.wave_scale = settings.ocean_scale if flip else 0.0
        ocean_modifier.keyframe_insert(data_path="wave_scale", frame=last_frame + 1) # offset by one frame to avoid duplicating start/end frames

    return (True, "", ocean_modifier)

def setup_ocean_modifiers(context: bpy.types.Context, obj: bpy.types.Object, active_obj: bpy.types.Object, first_frame: int, last_frame: int):
    """
    Add and configure the two ocean modifiers required to bake the time-looped FFT ocean
    
    :param context: Blender current execution context
    :param obj: object to receive the ocean modifier
    :param active_obj: active object serving as the target for searching an active ocean modifier to copy settings from
    :param first_frame: the animation's start frame (inclusive)
    :param last_frame: the animation's end frame (inclusive)
    :return: the function's success, potential error message, the ocean's extents
    :rtype: tuple
    """
    modifier_names = []
    modifiers_param_name = ["time", "wave_scale"]
    
    settings = context.scene.FFTOCEANBAKERSettings
    
    """
    inherit settings from active object, assuming we're able to find an ocean modifier in object
    """
    active_object_modifier = None
    if settings.ocean_from_active and active_obj and active_obj.type == "MESH":
        for modifier in active_obj.modifiers:
            if modifier.type == "OCEAN":
                active_object_modifier = modifier
                break

    if active_object_modifier:
        settings.subd = max(2, active_object_modifier.resolution)
        settings.ocean_time = active_object_modifier.time
        settings.ocean_size = active_object_modifier.size
        settings.ocean_spatial_size = active_object_modifier.spatial_size
        settings.ocean_depth = active_object_modifier.depth
        settings.ocean_seed = active_object_modifier.random_seed
        settings.ocean_smallest_wave = active_object_modifier.wave_scale_min
        settings.ocean_choppiness = active_object_modifier.choppiness
        settings.ocean_wind_vel = active_object_modifier.wind_velocity
        settings.ocean_alignment = active_object_modifier.wave_alignment
        settings.ocean_direction = active_object_modifier.wave_direction
        settings.ocean_damping = active_object_modifier.damping

    add_bake_report("ocean_time", settings.ocean_time)
    add_bake_report("ocean_size", settings.ocean_size)
    add_bake_report("ocean_spatial_size", settings.ocean_spatial_size)
    add_bake_report("ocean_depth", settings.ocean_depth)
    add_bake_report("ocean_seed", settings.ocean_seed)
    add_bake_report("ocean_scale", settings.ocean_scale)
    add_bake_report("ocean_smallest_wave", settings.ocean_smallest_wave)
    add_bake_report("ocean_choppiness", settings.ocean_choppiness)
    add_bake_report("ocean_wind_vel", settings.ocean_wind_vel)
    add_bake_report("ocean_alignment", settings.ocean_alignment)
    add_bake_report("ocean_direction", settings.ocean_direction)
    add_bake_report("ocean_damping", settings.ocean_damping)
    add_bake_report("ocean_clear", settings.ocean_clear)
    add_bake_report("ocean_from_active", settings.ocean_from_active)

    success, msg, ocean_modifier = add_ocean_modifier(context, obj, first_frame, last_frame, flip=False)
    if not success:
        return (False, msg, 0)
    modifier_names.append('modifiers["' + ocean_modifier.name + '"].')
    
    success, msg, ocean_modifier = add_ocean_modifier(context, obj, first_frame, last_frame, flip=True)
    if not success:
        return (False, msg, 0)
    modifier_names.append('modifiers["' + ocean_modifier.name + '"].')
    
    for modifier_name in modifier_names:
        for modifier_param_name in modifiers_param_name:
            name = modifier_name + modifier_param_name

            anim_data = obj.animation_data
            if anim_data and anim_data.action:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path == name:
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'LINEAR'
                            keyframe.handle_left_type = 'VECTOR'
                            keyframe.handle_right_type = 'VECTOR'
    
    extents = ocean_modifier.spatial_size * ocean_modifier.size

    return (True, "", extents)

###############
### BUFFERS ###
def get_frame_buffers(context: bpy.types.Context, obj: bpy.types.Object, mappings: list, frame: int, subdivisions: int, padding: int, extents: float) -> tuple[bool, str, list, list]:
    """
    Get the positional and normal pixel buffers for the given frame

    :param context: Blender current execution context
    :param obj: the ocean object
    :param mappings: precomputed bilinear interpolation data and reference position
    :param frame: the frame to bake
    :param subdivisions: the ocean's modifier subdivisions
    :param padding: amount of padding to add, in pixels, on one side
    :param extents: the ocean's modifier extents
    :return: the function's success, potential error message, offset pixel buffer, normal pixel buffer
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings

    # set frame and get evaluated ocean object to account for its ocean modifiers (it's an empty mesh otherwise)
    context.scene.frame_set(frame)
    dgraph = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(dgraph)
    obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

    frame_size = subdivisions * subdivisions
    frame_size_inner = frame_size - (padding * 2)

    # check num vertices
    expected_num_vertices = (frame_size + 1) * (frame_size + 1)
    if len(obj_eval_mesh.vertices) != expected_num_vertices:
        return (False, "Error in number of vertices: " + str(len(obj_eval_mesh.vertices)) + " vs " + str(expected_num_vertices), None, None)

    # create pixel buffers    
    buffer_offset = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size
    buffer_normal = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size

    for y in range(frame_size_inner):
        for x in range(frame_size_inner):
            vertex_index = x + (y * frame_size_inner)
            u_index, u_frac, v_index, v_frac, ref_pos = mappings[vertex_index]

            vertex_00_index = u_index + 0 + ((v_index + 0) * (frame_size + 1))
            vertex_01_index = u_index + 1 + ((v_index + 0) * (frame_size + 1))
            vertex_10_index = u_index + 0 + ((v_index + 1) * (frame_size + 1))
            vertex_11_index = u_index + 1 + ((v_index + 1) * (frame_size + 1))

            vertex_00 = obj_eval_mesh.vertices[vertex_00_index]
            vertex_01 = obj_eval_mesh.vertices[vertex_01_index]
            vertex_10 = obj_eval_mesh.vertices[vertex_10_index]
            vertex_11 = obj_eval_mesh.vertices[vertex_11_index]

            pos = mathutils.Vector.lerp(mathutils.Vector.lerp(vertex_00.co, vertex_01.co, u_frac), mathutils.Vector.lerp(vertex_10.co, vertex_11.co, u_frac), v_frac)
            if settings.offset_tex_mode == "OFFSET":
                pos -= ref_pos
            pos *= settings.unit_scale

            nor = mathutils.Vector.lerp(mathutils.Vector.lerp(vertex_00.normal, vertex_01.normal, u_frac), mathutils.Vector.lerp(vertex_10.normal, vertex_11.normal, u_frac), v_frac)
            nor.normalize()

            i = (x * 4) + (padding * 4) + (y * 4 * frame_size) + (frame_size * padding * 4)
            buffer_offset[i:i + 3] = pos
            buffer_normal[i:i + 3] = nor

    obj_eval.to_mesh_clear()

    return (True, "", buffer_offset, buffer_normal)

def apply_frame_padding(subdivisions: int, padding: int, buffer: list) -> list:
    """
    Fill black padded pixels on one side of the frame, with pixels from the other side of the frame
    
    :param subdivisions: the ocean's modifier subdivisions
    :param padding: amount of padding to add, in pixels, on one side
    :param buffer: pixel buffer to add padding to
    :return: padded pixel buffer
    :rtype: list
    """
    frame_size_padded = subdivisions * subdivisions
    frame_size = frame_size_padded - (padding * 2)
    frame_size_buffer_offset = frame_size * 4

    # first X padded pixels, copy the last X pixels in frame, for each row
    # 00000000 > 00000000
    # 00000000 > 00000000
    # 00111100 > AA11AA00
    # 00111100 > AA11AA00
    # 00111100 > AA11AA00
    # 00111100 > AA11AA00
    # 00000000 > 00000000
    # 00000000 > 00000000
    for padding_x in range(padding):
        padding_buffer_offset = padding_x * 4
        for pixel in range(frame_size_padded):
            i = padding_buffer_offset + (pixel * frame_size_padded * 4)
            ii = i + frame_size_buffer_offset
            buffer[i:i + 3] = buffer[ii:ii + 3]

    # last X padded pixels, copy the first X pixels in frame, for each row
    # 00000000 > 00000000
    # 00000000 > 00000000
    # 11111100 > 11AA11AA
    # 11111100 > 11AA11AA
    # 11111100 > 11AA11AA
    # 11111100 > 11AA11AA
    # 00000000 > 00000000
    # 00000000 > 00000000
    for padding_x in range(padding):
        padding_buffer_offset = (padding + frame_size + padding_x) * 4
        for pixel in range(frame_size_padded):
            i = padding_buffer_offset + (pixel * frame_size_padded * 4)
            ii = i - frame_size_buffer_offset
            buffer[i:i + 3] = buffer[ii:ii + 3]

    # first Y padded pixels, copy the last Y pixels in the frame, for each column
    # 00000000 > AAAAAAAA
    # 00000000 > AAAAAAAA
    # 11111111 > 11111111
    # 11111111 > 11111111
    # 11111111 > AAAAAAAA
    # 11111111 > AAAAAAAA
    # 00000000 > 00000000
    # 00000000 > 00000000
    for padding_y in range(padding):
        padding_buffer_offset = (padding_y * frame_size_padded * 4)
        for pixel in range(frame_size_padded):
            i = (pixel * 4) + padding_buffer_offset
            ii = i + (frame_size_padded * frame_size * 4)
            buffer[i:i + 3] = buffer[ii:ii + 3]

    # last Y padded pixels, copy the first Y pixels in the frame, for each column
    # 11111111 > 11111111
    # 11111111 > 11111111
    # 11111111 > AAAAAAAA
    # 11111111 > AAAAAAAA
    # 11111111 > 11111111
    # 11111111 > 11111111
    # 00000000 > AAAAAAAA
    # 00000000 > AAAAAAAA
    for padding_y in range(padding):
        padding_buffer_offset = ((padding + frame_size + padding_y) * frame_size_padded * 4)
        for pixel in range(frame_size_padded):
            i = (pixel * 4) + padding_buffer_offset
            ii = i - (frame_size_padded * frame_size * 4)
            buffer[i:i + 3] = buffer[ii:ii + 3]

    return buffer

def get_flipbook_frames(context: bpy.types.Context, num_frames: int) -> tuple[bool, str, int, int]:
    """

    :param context: Blender current execution context
    :param num_frames: number of frames to bake
    :return: the function's success, potential error message, number of frames in X, number of frames in Y, flipbook resolution in X, flipbook resolution in Y
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings

    frame_size = get_bake_frame_size(context)

    num_frames_x = max(1, min(num_frames, settings.frames_per_row))
    num_frames_y = math.ceil(num_frames / num_frames_x)
    add_bake_report("frames_per_row", num_frames_x)

    tex_width = frame_size * num_frames_x
    if tex_width > settings.flipbook_max_size:
        return (False, "Maximum width", 0, 0, 0, 0)

    tex_height = frame_size * num_frames_y
    if tex_height > settings.flipbook_max_size:
        return (False, "Maximum height", 0, 0, 0, 0)
    
    return (True, "", num_frames_x, num_frames_y, tex_width, tex_height)

def get_flipbook_buffer(context: bpy.types.Context, frames: list, num_frames_x: int, num_frames_y: int, tex_width: int, tex_height: int) -> list:
    """
    Compact the pixel data from frames stored in individual textures into one single flipbook texture, one frame after the other

    :param context: Blender current execution context
    :param frames: list of textures to compact into a flipbook
    :param num_frames_x: amount of frames to create in the X axis
    :param num_frames_y: amount of frames to create in the Y axis
    :param tex_width: flipbook's width
    :param tex_height: flipbook's height
    :return: the function's success, potential error message, pixel buffer
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings

    frame_size = get_bake_frame_size(context)

    flipbook_buffer = [0.0, 0.0, 0.0, 1.0] * tex_width * tex_height

    for frame_y in range(num_frames_y):
        for frame_x in range(num_frames_x):
            # compute linear index from X & Y indices
            frame_index = frame_x + (frame_y * num_frames_x)
    
            # get pixel buffer of texture at given frame index
            try:
                pixels = frames[frame_index].pixels
            except:
                continue

            # compute where this frame starts at in the flipbook pixel buffer
            flip_frame_x = settings.frame_sort_mode == "TB_RL" or settings.frame_sort_mode == "BT_RL"
            if flip_frame_x:
                buffer_frame_offset_x = (num_frames_x - 1 - frame_x) * frame_size * 4
            else:
                buffer_frame_offset_x = frame_x * frame_size * 4
            flip_frame_y = settings.frame_sort_mode == "BT_LR" or settings.frame_sort_mode == "BT_RL"
            if not flip_frame_y:
                buffer_frame_offset_y = (num_frames_y - 1 - frame_y) * frame_size * tex_width * 4
            else:
                buffer_frame_offset_y = frame_y * frame_size * tex_width * 4

            buffer_frame_offset = buffer_frame_offset_x + buffer_frame_offset_y

            # for each row of pixels in the frame texture
            for row in range(frame_size):
                # fetch row of pixels in the frame texture
                row_offset = row * frame_size * 4
                row_of_pixels = pixels[row_offset:row_offset + (frame_size * 4)]
                
                # copy it to the flipbook pixel buffer
                buffer_row_offset = row * tex_width * 4
                buffer_index = buffer_frame_offset + buffer_row_offset
                flipbook_buffer[buffer_index:buffer_index + len(row_of_pixels)] = row_of_pixels

    return (True, "", flipbook_buffer)

def get_inverted_buffers(buffer: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """ 
    Re-order vert buffers so that pixel buffer is flipped in V (aka invert image). Append line of pixels after line in reverse order. Method can likely be pythonified and improved

    :param buffer: pixel buffer
    :param tex_width: texture(s) width
    :param tex_height: texture(s) height
    :return: processed buffer
    :rtype: tuple
    """

    buffer_row_offset = tex_width * 4

    buffer_inv = [0.0] * len(buffer)
    for row in reversed(range(tex_height)):
        i = (tex_height - 1 - row) * buffer_row_offset
        ii = row * buffer_row_offset
        buffer_inv[i:i + buffer_row_offset] = buffer[ii:ii + buffer_row_offset]

    return buffer_inv

def get_remapped_offset_buffer(buffer_offset: list) -> tuple[list, mathutils.Vector]:
    """
    Remap the offset buffer from the range [-min:max] to [0:1]

    :param buffer_offset: offset buffer
    :return: remapped buffer, X/Y/Z offset & range used to remap values to the range [0:1]
    :rtype: tuple
    """
    pixels = range(len(buffer_offset) // 4)
    buffer_x = [buffer_offset[pixel][0] for pixel in pixels]
    buffer_y = [buffer_offset[pixel][1] for pixel in pixels]
    buffer_z = [buffer_offset[pixel][2] for pixel in pixels]

    # X range
    buffer_x_min = min(buffer_x)
    buffer_x_max = max(buffer_x)
    if abs(buffer_x_max - buffer_x_min) < 0.0001:
        buffer_x_range = 1.0
    else:
        buffer_x_range = buffer_x_max - buffer_x_min
    buffer_x_offset = buffer_x_min

    # Y range
    buffer_y_min = min(buffer_y)
    buffer_y_max = max(buffer_y)
    if abs(buffer_y_max - buffer_y_min) < 0.0001:
        buffer_y_range = 1.0
    else:
        buffer_y_range = buffer_y_max - buffer_y_min
    buffer_y_offset = buffer_x_min

    # Z range
    buffer_z_min = min(buffer_z)
    buffer_z_max = max(buffer_z)
    if abs(buffer_z_max - buffer_z_min) < 0.0001:
        buffer_z_range = 1.0
    else:
        buffer_z_range = buffer_z_max - buffer_z_min
    buffer_z_offset = buffer_x_min

    pixel_offset = mathutils.Vector((buffer_x_offset, buffer_y_offset, buffer_z_offset))
    pixel_range = mathutils.Vector((buffer_x_range, buffer_y_range, buffer_z_range))

    for pixel in pixels:
        i = (pixel * 4)
        offset = mathutils.Vector(buffer_offset[i:i + 3])
        offset += pixel_offset
        offset /= pixel_range
        buffer_offset[i:i+3] = offset

    return buffer_offset, pixel_offset, pixel_range

def get_remapped_normal_buffer(buffer_normal: list) -> list:
    """
    Remap the normal buffer from the range [-1:1] to [0:1]

    :param buffer_normal: buffer of normals
    :return: remapped buffer
    :rtype: list
    """

    pixels = range(len(buffer_normal) // 4)
    for pixel in pixels:
        i = (pixel * 4)
        normal = mathutils.Vector(buffer_normal[i:i + 3])
        normal += mathutils.Vector((1.0, 1.0, 1.0))
        normal *= mathutils.Vector((0.5, 0.5, 0.5))
        buffer_normal[i:i+3] = normal

    return buffer_normal

############
### MESH ###
def generate_mesh(context: bpy.types.Context, bake_name: str, num_frames_x: int, num_frames_y: int):
    """
    Generate the a subdivided plane that matches the bake subdivision amount and with the same size as the generated ocean
    
    :param context: Blender current execution context
    :param bake_name: the bake operation's 'name'
    :param num_frames_x: amount of frames to create in the X axis
    :param num_frames_y: amount of frames to create in the Y axis
    :return: the function's success, potential error message, generated object
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings
    
    subdivisions = max(2, settings.subd)
    padding = get_bake_frame_padding(context, clamp=True)
    
    frame_size = subdivisions * subdivisions
    frame_size_ratio = (frame_size - (padding * 2)) / frame_size

    mesh = bpy.data.meshes.new(bake_name)
    obj = bpy.data.objects.new(bake_name, mesh)
    bpy.context.collection.objects.link(obj)

    faces_per_row = (subdivisions * subdivisions)
    verts_per_row = faces_per_row + 1
    size = settings.ocean_spatial_size * settings.ocean_size
    half_size = size / 2
    vertex_spacing = size / (subdivisions * subdivisions)

    """
    1. create vertex buffer
    """
    verts = []
    for y in range(verts_per_row):
        for x in range(verts_per_row):
            verts.append(((x * vertex_spacing) - half_size, (y * vertex_spacing) - half_size, 0))

    """
    2. create face buffer
    """
    faces = []
    for y in range(faces_per_row):
        for x in range(faces_per_row):
            vertex_index = x + (y * verts_per_row)
            faces.append([vertex_index, vertex_index + 1, vertex_index + verts_per_row + 1, vertex_index + verts_per_row])

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    """
    3. UV map
    """
    mesh.uv_layers.new()
    uvmap = mesh.uv_layers[0]
    uvmap.name = "UVMap"

    frame_padding_scale = frame_size_ratio
    frame_padding_bias = padding / frame_size

    """
    4. UVs
    """
    for loop in mesh.loops:
        vertex_index = loop.vertex_index

        vertex_x = vertex_index % verts_per_row
        vertex_y = math.floor(vertex_index / verts_per_row)

        u =  vertex_x / (verts_per_row - 1)
        u *= frame_padding_scale
        u += frame_padding_bias

        v = vertex_y / (verts_per_row - 1)
        v *= frame_padding_scale
        v += frame_padding_bias

        if settings.tex_mode == "FLIPBOOK":
            u /= num_frames_x
            v /= num_frames_y

        if settings.unit_invert_v:
            v = 1.0 - v

        uvmap.data[loop.index].uv = (u,v)

    obj.select_set(True) # for export

    return (True, "", obj)

def export_mesh_selection(context: bpy.types.Context, bake_name: str):
    """
    Export the current selection to FBX

    :param context: Blender current execution context
    :param bake_name: the bake operation's 'name'
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    settings = context.scene.FFTOCEANBAKERSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None, -1)

    return (True, "", export_path)

################
### TEXTURES ###
def generate_texture(filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate the offset or normal image

    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: texture's width
    :param tex_height: texture's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename if filename != "" else "T_Bake_VertOffsets"
    image_name += ".exr"

    image = bpy.data.images.get(image_name, None)
    if image is not None:
        if image.packed_file and bpy.data.is_saved:
            image.unpack()
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
    Export the image

    :param context: Blender current execution context
    :param image: the image to export
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

def clear_textures(textures: list):
    """
    Clear textures

    :param textures: textures to get rid of
    :return: None
    :rtype: None
    """
    for texture in textures:
        if texture.packed_file and bpy.data.is_saved:
            texture.unpack()
        bpy.data.images.remove(texture)

def generate_frames(context: bpy.types.Context, obj: bpy.types.Object, frames_to_bake: list, extents: float) -> tuple[bool, str, list, list]:
    """
    Generate and output a list of images, one per frame to bake, containing the baked positional & normal data. Amount of images should equal amount of frames to bake.
    Each frame is initially sized according to the amount of subdivisions set in the ocean modifier (e.g. 5 for 25x25 vertices), and then possibly rescaled to match the
    custom frame size set by the user, if any.

    :param context: Blender current execution context
    :param obj: the ocean object
    :param frames_to_bake: list of frames to loop through
    :param extents: the ocean's modifier extents
    """

    settings = context.scene.FFTOCEANBAKERSettings
    
    subdivisions = max(2, settings.subd)
    add_bake_report("subd", subdivisions)

    padding = get_bake_frame_padding(context, clamp=True)
    add_bake_report("frame_padding", padding)

    add_bake_report("frame_sort_mode", settings.frame_sort_mode)
    add_bake_report("tex_offset_mode", settings.offset_tex_mode)

    frame_size = subdivisions * subdivisions
    frame_size_inner = frame_size - (padding * 2)

    tex_offsets = []
    tex_normals = []

    """
    pre-compute mapping data to perform bilinear interpolation
    """
    texel_size = 1.0 / frame_size_inner
    half_texel_size = texel_size * 0.5
    pseudo_texel_size = 1.0 / (frame_size_inner + 1)
    
    mappings = [None] * frame_size_inner * frame_size_inner
    for y in range(frame_size_inner):
        for x in range(frame_size_inner):
            vertex_index = x + (y * frame_size_inner)

            u = (x * pseudo_texel_size) + half_texel_size
            v = (y * pseudo_texel_size) + half_texel_size
            
            u_pos = u * (frame_size + 1)
            v_pos = v * (frame_size + 1)

            u_index = math.floor(u_pos)
            v_index = math.floor(v_pos)

            u_frac = u_pos - u_index
            v_frac = v_pos - v_index

            ref_pos_x = ((x * texel_size) + half_texel_size - 0.5) * extents
            ref_pos_y = ((y * texel_size) + half_texel_size - 0.5) * extents
            ref_pos = mathutils.Vector((ref_pos_x, ref_pos_y, 0.0))

            mappings[vertex_index] = (u_index, u_frac, v_index, v_frac, ref_pos)

    """
    generate offset/normal images
    """
    for frame in frames_to_bake:
        progress = frame / max(1, (len(frames_to_bake) - 1))
        bpy.context.window_manager.progress_update((progress * 80) + 10)

        success, msg, buffer_offset, buffer_normal = get_frame_buffers(context, obj, mappings, frame, subdivisions, padding, extents)
        if not success:
            return (False, msg, None, None)

        if buffer_offset:
            if padding > 0:
                buffer_offset = apply_frame_padding(subdivisions, padding, buffer_offset)

            if settings.offset_tex_remap:
                buffer_offset, remap_range_offset, remap_range = get_remapped_offset_buffer(buffer_offset)
                add_bake_report("tex_offset_remapped", True)
                add_bake_report("tex_offset_range_offset", remap_range_offset)
                add_bake_report("tex_offset_range", remap_range)

            if settings.unit_invert_v:
                buffer_offset = get_inverted_buffers(buffer_offset, frame_size, frame_size)

            success, msg, tex_offset = generate_texture("offset." + str(frame), buffer_offset, frame_size, frame_size)
            if not success:
                return (False, msg, None, None)

            if settings.frame_size_mode == "CUSTOM":
                tex_offset.scale(settings.frame_size_custom, settings.frame_size_custom)

            tex_offsets.append(tex_offset)

        if buffer_normal:
            if padding > 0:
                buffer_normal = apply_frame_padding(subdivisions, padding, buffer_normal)
                    
            if settings.normal_tex_remap:
                buffer_normal = get_remapped_normal_buffer(buffer_normal)
                add_bake_report("tex_normal_remapped", True)

            if settings.unit_invert_v:
                buffer_normal = get_inverted_buffers(buffer_normal, frame_size, frame_size)

            success, msg, tex_normal = generate_texture("normal." + str(frame), buffer_normal, frame_size, frame_size)
            if not success:
                return (False, msg, None, None)
            
            if settings.frame_size_mode == "CUSTOM":
                tex_normal.scale(settings.frame_size_custom, settings.frame_size_custom)

            tex_normals.append(tex_normal)

    if len(tex_offsets) != len(frames_to_bake):
        return (False, "Wrong offset texture count", None, None)

    if len(tex_normals) != len(frames_to_bake):
        return (False, "Wrong normal texture count", None, None)

    return (True, "", tex_offsets, tex_normals)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.FFTOCEANBAKERSettings
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
                            unit_invert_v=str(report.unit_invert_v))

    # write xml
    tree = ET.ElementTree(root)
    if settings.export_xml_mode == "MESHPATH" and report.mesh_path != "":
        export_path = os.path.join(os.path.dirname(report.mesh_path), report.name + ".xml")
        tree.write(export_path)
        return (True, "", export_path)
    else:
        success, msg, export_path = get_path(settings.export_xml_file_path, settings.export_xml_file_name if settings.export_xml_file_name != "" else report.name, ".xml", settings.export_xml_override)
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