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

    if settings.frame_range_mode == "SCENE":
        frames_to_bake = list(range(context.scene.frame_start, context.scene.frame_end + 1, context.scene.frame_step))
    else: # CUSTOM
        frames_to_bake = list(range(settings.frame_range_custom_start, settings.frame_range_custom_end + 1, settings.frame_range_custom_step))

    return (frames_to_bake, min(frames_to_bake), max(frames_to_bake))

def get_bake_subdivisions(context: bpy.types.Context) -> int:
    """
    Return the subdivision amount to use for generating the ocean mesh and export mesh as well, if any

    :param context: Blender current execution context
    :return: subdivision amount
    :rtype: int
    """

    settings = context.scene.FFTOCEANBAKERSettings

    if settings.subd == "CUSTOM":
        subd = settings.subd_custom_subd
    elif settings.subd == "2":
        subd = 2
    elif settings.subd == "3":
        subd = 3
    elif settings.subd == "4":
        subd = 4
    elif settings.subd == "5":
        subd = 5
    elif settings.subd == "6":
        subd = 6
    elif settings.subd == "7":
        subd = 7
    elif settings.subd == "8":
        subd = 8
    elif settings.subd == "9":
        subd = 9
    elif settings.subd == "10":
        subd = 10
    elif settings.subd == "11":
        subd = 11
    elif settings.subd == "12":
        subd = 12
    else:
        subd = 2

    return max(2, subd)

def get_bake_frame_size(context: bpy.types.Context) -> int:
    """
    Return the size of each frame. Size is both the width & height since frame are squared
    
    :param context: Blender current execution context
    :return: frame size (width & height)
    :rtype: int
    """
    
    settings = context.scene.FFTOCEANBAKERSettings
    if settings.frame_size_mode == "SUBDIVISIONS":
        subd = get_bake_subdivisions(context)
        return subd * subd
    else: # CUSTOM
        return max(2, settings.frame_size_custom)

def get_bake_frame_padding(context: bpy.types.Context) -> int:
    """
    Return the amount of padding to add to each frame, in pixels, on one side

    :return: amount of padding to add to each frame, in pixels, on one side
    :rtype: int
    """
    settings = context.scene.FFTOCEANBAKERSettings
    if settings.frame_padding_mode == "MIPLEVEL":
        return pow(2, max(0, settings.frame_padding_mips - 1))
    elif settings.frame_padding_mode == "PIXELS":
        return max(0, settings.frame_padding_pixels)
    else: # NONE
        return 0

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
    
    num_frames = len(frames_to_bake)
    if num_frames <= 0:
        add_bake_report("success", False)
        add_bake_report("msg", "Too few frames to bake")
        return (False, "ERROR", "Too few frames to bake")
    
    wm.progress_update(5)
    
    bake_name = get_bake_name(context)
    add_bake_report("name", bake_name)

    wm.progress_update(10)
    
    #########
    # OCEAN #

    success, msg, obj = generate_ocean_mesh(context, bake_name)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    success, msg, extents = setup_ocean_modifiers(context, obj, bake_frame_start, bake_frame_end)
    if not success:
        clear_ocean_mesh(obj)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)
    
    ########
    # BAKE #

    success, msg, tex_offsets, tex_normals = generate_frames(context, obj, frames_to_bake, extents)
    if not success:
        clear_ocean_mesh(obj)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    ############
    # TEXTURES #

    if settings.tex_mode == "FLIPBOOK":
        success, msg, num_frames_x, num_frames_y, tex_width, tex_height = get_flipbook_frames(context, num_frames)
        if not success:
            clear_ocean_mesh(obj)

            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, "ERROR", msg)

        if settings.offset_tex:
            success, msg, buffer_offset = get_flipbook_buffer(context, tex_offsets, num_frames_x, num_frames_y, tex_width, tex_height)
            if not success:
                clear_ocean_mesh(obj)

                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)
            
            if settings.unit_invert_v:
                buffer_offset = get_inverted_buffers(buffer_offset, tex_width, tex_height) # @TODO check

            success, msg, tex_offset = generate_texture("offset", buffer_offset, tex_width, tex_height)
            clear_textures(tex_offsets)
            if not success:
                clear_ocean_mesh(obj)

                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            if settings.export_tex:
                success, msg, tex_offset_path = export_texture(context, tex_offset, settings.export_tex_file_path, settings.offset_tex_file_name, bake_name, settings.export_tex_override)
                if not success:
                    clear_ocean_mesh(obj)

                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, 'ERROR', msg)
                add_bake_report("tex_offset_export", True)
                add_bake_report("tex_offset_path", tex_offset_path)

        if settings.normal_tex:
            success, msg, buffer_normal = get_flipbook_buffer(context, tex_normals, num_frames_x, num_frames_y, tex_width, tex_height)
            if not success:
                clear_ocean_mesh(obj)

                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)
            
            if settings.unit_invert_v:
                buffer_offset = get_inverted_buffers(buffer_offset, tex_width, tex_height) # @TODO check

            success, msg, tex_normal = generate_texture("normal", buffer_normal, tex_width, tex_height)
            clear_textures(tex_normals)
            if not success:
                clear_ocean_mesh(obj)

                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            if settings.export_tex:
                success, msg, tex_normal_path = export_texture(context, tex_normal, settings.export_tex_file_path, settings.normal_tex_file_name, bake_name, settings.export_tex_override)
                if not success:
                    clear_ocean_mesh(obj)

                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, 'ERROR', msg)
                add_bake_report("tex_normal_export", True)
                add_bake_report("tex_normal_path", tex_normal_path)
    else:
        num_frames_x = 1
        num_frames_y = 1

    ########
    # MESH #

    if settings.export_mesh:
        success, msg, obj_to_export = generate_mesh(context, bake_name, num_frames_x, num_frames_y)
        if success:
            add_bake_report("mesh", obj_to_export)

    if settings.export_mesh:
        success, msg, mesh_path = export_mesh_selection(context, bake_name)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("mesh_export", True)
        add_bake_report("mesh_path", mesh_path)

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
    subd = get_bake_subdivisions(context)
    time = settings.anim_speed

    ocean_modifier = obj.modifiers.new(name="Ocean", type='OCEAN')
    ocean_modifier.geometry_mode = "DISPLACE" if flip else "GENERATE"
    ocean_modifier.size = 1
    ocean_modifier.repeat_x = 1
    ocean_modifier.repeat_y = 1
    ocean_modifier.viewport_resolution = subd
    ocean_modifier.resolution = subd
    ocean_modifier.size = 0.25
    
    ocean_modifier.time = 0.0 if flip else time
    ocean_modifier.keyframe_insert(data_path="time", frame=first_frame)
    ocean_modifier.time = time if flip else time + time
    ocean_modifier.keyframe_insert(data_path="time", frame=last_frame)
    
    ocean_modifier.wave_scale = 0.0 if flip else 1.0
    ocean_modifier.keyframe_insert(data_path="wave_scale", frame=first_frame)
    ocean_modifier.wave_scale = 1.0 if flip else 0.0
    ocean_modifier.keyframe_insert(data_path="wave_scale", frame=last_frame)

    return (True, "", ocean_modifier)
    
def setup_ocean_modifiers(context: bpy.types.Context, obj: bpy.types.Object, first_frame: int, last_frame: int):
    """
    Add and configure the two ocean modifiers required to bake the time-looped FFT ocean
    
    :param context: Blender current execution context
    :param obj: object to receive the ocean modifier
    :param first_frame: the animation's start frame (inclusive)
    :param last_frame: the animation's end frame (inclusive)
    :return: the function's success, potential error message, the ocean's extents
    :rtype: tuple
    """
    modifier_names = []
    modifiers_param_name = ["time", "wave_scale"]

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
def get_frame_buffers(context: bpy.types.Context, obj: bpy.types.Object, frame: int, subdivisions: int, padding: int, extents: float) -> tuple[bool, str, list, list]:
    """
    Get the positional and normal pixel buffers for the given frame

    :param context: Blender current execution context
    :param obj: the ocean object
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

    # check num vertices
    num_vertices = subdivisions * subdivisions
    expected_num_vertices = ((subdivisions) * (subdivisions) + 1) * ((subdivisions) * (subdivisions) + 1)
    if len(obj_eval_mesh.vertices) != expected_num_vertices:
        return (False, "Error in number of vertices: " + str(len(obj_eval_mesh.vertices)) + " vs " + str(expected_num_vertices), None, None)

    # create pixel buffers
    frame_size = num_vertices
    frame_size_inner = frame_size - (padding * 2)
    buffer_offset = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size
    buffer_normal = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size

    for x in range(frame_size_inner):
        for y in range(frame_size_inner):
            vertex_u = x / frame_size_inner
            vertex_x = math.floor(vertex_u * frame_size)
            vertex_x_frac = (vertex_u * frame_size) - vertex_x
            vertex_x_overflow = (vertex_x + 1) > frame_size
            vertex_x_next = (vertex_x + 1) % frame_size

            vertex_v = y / frame_size_inner
            vertex_y = math.floor(vertex_v * frame_size)
            vertex_y_frac = (vertex_v * frame_size) - vertex_y
            vertex_y_overflow = (vertex_y + 1) > frame_size
            vertex_y_next = (vertex_y + 1) % frame_size

            # compute vertex linear index in mesh
            vertex_index_00 = vertex_x + (vertex_y * (frame_size + 1)) # offset frame size by one to account for last tiling vertex we need to skip each row
            vertex_index_01 = vertex_x_next + (vertex_y * (frame_size + 1))
            vertex_index_10 = vertex_x + (vertex_y_next * (frame_size + 1))
            vertex_index_11 = vertex_x_next + (vertex_y_next * (frame_size + 1))

            try:
                vertex_00 = obj_eval_mesh.vertices[vertex_index_00]
                vertex_01 = obj_eval_mesh.vertices[vertex_index_01]
                vertex_10 = obj_eval_mesh.vertices[vertex_index_10]
                vertex_11 = obj_eval_mesh.vertices[vertex_index_11]
            except:
                return (False, "Invalid vertex index: " + str(vertex_index_11) + " vs " + str(len(obj_eval_mesh.vertices)), None, None)

            # @TODO overflow

            # get pos/offset & nor
            pos_a = vertex_00.co + (vertex_01.co - vertex_00.co) * vertex_x_frac
            pos_b = vertex_10.co + (vertex_11.co - vertex_10.co) * vertex_x_frac
            pos = pos_a + (pos_b - pos_a) * vertex_y_frac
            if settings.offset_tex_mode == "OFFSET":
                ref_pos_x = (vertex_u - 0.5) * extents
                ref_pos_y = (vertex_v - 0.5) * extents
                ref_pos = mathutils.Vector((ref_pos_x, ref_pos_y, 0.0))
                pos -= ref_pos # @TODO
            nor_a = vertex_00.normal + (vertex_01.normal - vertex_00.normal) * vertex_x_frac
            nor_b = vertex_10.normal + (vertex_11.normal - vertex_10.normal) * vertex_x_frac
            nor = nor_a + (nor_b - nor_a) * vertex_y_frac
            nor.normalize()

            # compute where vertex is in buffer of pixels
            buffer_index = (x * 4) + (padding * 4) + (y * 4 * frame_size) + (frame_size * padding * 4)

            # fill pixel buffer with data
            buffer_offset[buffer_index + 0] = pos.x
            buffer_offset[buffer_index + 1] = pos.y
            buffer_offset[buffer_index + 2] = pos.z

            buffer_normal[buffer_index + 0] = nor.x
            buffer_normal[buffer_index + 1] = nor.y
            buffer_normal[buffer_index + 2] = nor.z

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
        for pixel in range(frame_size_padded):
            buffer_index = (padding_x * 4) + (pixel * frame_size_padded * 4)
            buffer[buffer_index + 0] = buffer[buffer_index + 0 + (frame_size * 4)]
            buffer[buffer_index + 1] = buffer[buffer_index + 1 + (frame_size * 4)]
            buffer[buffer_index + 2] = buffer[buffer_index + 2 + (frame_size * 4)]

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
        for pixel in range(frame_size_padded):
            buffer_index = ((padding + frame_size + padding_x) * 4) + (pixel * frame_size_padded * 4)
            buffer[buffer_index + 0] = buffer[buffer_index + 0 - (frame_size * 4)]
            buffer[buffer_index + 1] = buffer[buffer_index + 1 - (frame_size * 4)]
            buffer[buffer_index + 2] = buffer[buffer_index + 2 - (frame_size * 4)]

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
        for pixel in range(frame_size_padded):
            buffer_index = (pixel * 4) + (padding_y * frame_size_padded * 4)
            buffer[buffer_index + 0] = buffer[buffer_index + 0 + (frame_size_padded * frame_size * 4)]
            buffer[buffer_index + 1] = buffer[buffer_index + 1 + (frame_size_padded * frame_size * 4)]
            buffer[buffer_index + 2] = buffer[buffer_index + 2 + (frame_size_padded * frame_size * 4)]

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
        for pixel in range(frame_size_padded):
            buffer_index = (pixel * 4) + ((padding + frame_size + padding_y) * frame_size_padded * 4)
            buffer[buffer_index + 0] = buffer[buffer_index + 0 - (frame_size_padded * frame_size * 4)]
            buffer[buffer_index + 1] = buffer[buffer_index + 1 - (frame_size_padded * frame_size * 4)]
            buffer[buffer_index + 2] = buffer[buffer_index + 2 - (frame_size_padded * frame_size * 4)]

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

    num_frames_x = max(1, settings.frames_per_row)
    tex_width = frame_size * num_frames_x
    if tex_width > settings.flipbook_max_size:
        return (False, "Maximum width", 0, 0, 0, 0)

    num_frames_y = math.floor(num_frames / num_frames_x)
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
                return (False, "Invalid frame index: " + str(frame_index) + " vs " + str(len(frames)), None)

            # compute where this frame starts at in the flipbook pixel buffer
            buffer_frame_offset = (frame_x * frame_size * 4) + (frame_y * frame_size * tex_width * 4)

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

    buffer_inv = []
    vertices_normals_inv = []
    for i in reversed(range(tex_height)):
        row = tex_width * 4
        row_offset = i * row
        buffer_inv.extend(buffer[row_offset:row_offset + row])

    return buffer_inv

def get_remapped_vertices_offset_buffer(buffer_offset: list) -> tuple[list, mathutils.Vector]:
    """
    Remap the offset buffer from the range [-min:max] to [0:1]

    :param buffer_offset: buffer of offsets
    :param min_offset: min values to remap offsets to the range [0:1]
    :param max_offset: max values to remap offsets to the range [0:1]
    :return: remapped buffer, absolute maximum offset in X/Y/Z to remap offset back to their initial range
    :rtype: tuple
    """
    pixel_range = range(len(buffer_offset) // 4)
    buffer_x = [buffer_offset[pixel_index][0] for pixel_index in pixel_range]
    buffer_y = [buffer_offset[pixel_index][1] for pixel_index in pixel_range]
    buffer_z = [buffer_offset[pixel_index][2] for pixel_index in pixel_range]

    max_offset = mathutils.Vector((abs(max(buffer_x, key=abs)),
                                   abs(max(buffer_y, key=abs)),
                                   abs(max(buffer_z, key=abs))))

    for pixel_index in pixel_range:
        pixel_buffer_index = (pixel_index * 4)
        buffer_offset[pixel_buffer_index + 0] = ((buffer_offset[pixel_buffer_index + 0] / max_offset.x) + 1) * 0.5 # x
        buffer_offset[pixel_buffer_index + 1] = ((buffer_offset[pixel_buffer_index + 1] / max_offset.y) + 1) * 0.5 # y
        buffer_offset[pixel_buffer_index + 2] = ((buffer_offset[pixel_buffer_index + 2] / max_offset.z) + 1) * 0.5 # z
        # buffer_offset[pixel_buffer_index + 3] = ((buffer_offset[pixel_buffer_index + 0] / max_offset) * 0.5) + 0.5 # w unused

    return buffer_offset, max_offset

def get_remapped_vertices_normal_buffer(buffer_normal: list) -> list:
    """
    Remap the normal buffer from the range [-1:1] to [0:1]

    :param buffer_normal: buffer of normals
    :return: remapped buffer
    :rtype: list
    """

    for pixel_index in range(len(buffer_normal) // 4):
        pixel_buffer_index = (pixel_index * 4)
        buffer_normal[pixel_buffer_index + 0] = (buffer_normal[pixel_buffer_index + 0] + 1) * 0.5 # x
        buffer_normal[pixel_buffer_index + 1] = (buffer_normal[pixel_buffer_index + 1] + 1) * 0.5 # y
        buffer_normal[pixel_buffer_index + 2] = (buffer_normal[pixel_buffer_index + 2] + 1) * 0.5 # z
        # vertices_offsets[pixel_buffer_index + 3] = (vertices_offsets[pixel_buffer_index + 0] * 0.5) + 0.5 # w unused

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
    
    subdivisions = get_bake_subdivisions(context)
    padding = get_bake_frame_padding(context)
    
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
    
    padding = get_bake_frame_padding(context)
    subdivisions = get_bake_subdivisions(context)

    frame_size = subdivisions * subdivisions
    
    tex_offsets = []
    tex_normals = []

    for frame in frames_to_bake:
        success, msg, buffer_offset, buffer_normal = get_frame_buffers(context, obj, frame, subdivisions, padding, extents)
        if not success:
            return (False, msg, None, None)

        if buffer_offset:
            if padding > 0:
                buffer_offset = apply_frame_padding(subdivisions, padding, buffer_offset)

            if settings.offset_tex_remap:
                buffer_offset, max_offset = get_remapped_vertices_offset_buffer(buffer_offset)
                add_bake_report("tex_offset_remapped", True)
                add_bake_report("tex_offset_remapping", max_offset)

            if settings.unit_invert_v and settings.tex_mode == "FRAME": # flipbook needs to be flipped in its entirety
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
                buffer_normal = get_remapped_vertices_normal_buffer(buffer_normal)
                add_bake_report("tex_normal_remapped", True)

            if settings.unit_invert_v and settings.tex_mode == "FRAME": # flipbook needs to be flipped in its entirety
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