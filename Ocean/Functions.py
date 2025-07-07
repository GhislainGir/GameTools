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
import bmesh
import os
import platform
import sys
import mathutils
import xml.etree.ElementTree as ET
import uuid
import time
import ctypes
from ctypes import *

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
    settings = context.scene.OceanBakerSettings

    reset_bake_report()

    add_bake_report("baked", True)
    add_bake_report("ID", uuid.uuid4().hex)
    add_bake_report("unit_system", context.scene.unit_settings.system)
    add_bake_report("unit_unit", context.scene.unit_settings.length_unit)
    add_bake_report("unit_length", context.scene.unit_settings.scale_length)
    add_bake_report("unit_scale", settings.unit_scale)
    add_bake_report("unit_invert_u", settings.unit_invert_u)
    add_bake_report("unit_invert_v", settings.unit_invert_v)

def reset_bake_report():
    """
    Set all report properties to their default values

    :return: None
    :rtype: None
    """
    report = bpy.context.scene.OceanBakerReport
    report.baked = False
    report.success = False
    report.msg = ""
    report.name = ""
    report.ID = ""
    
    report.unit_system = ""
    report.unit_unit = ""
    report.unit_length = 0.0
    report.unit_scale = 0.0
    report.unit_invert_u = False
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
    report.mesh_path = ""
    report.mesh_min_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.mesh_max_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))

    report.tex_width = 0
    report.tex_height = 0

    report.tex_mode = ""
    report.tex_offset = None
    report.tex_offset_export = False
    report.tex_offset_path = ""
    report.tex_offset_remapped = False
    report.tex_offset_range_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.tex_offset_range = mathutils.Vector((1.0, 1.0, 1.0))
    report.tex_normal = None
    report.tex_normal_export = False
    report.tex_normal_path = ""
    report.tex_normal_remapped = False
    report.tex_crest = None
    report.tex_crest_export = False
    report.tex_crest_path = ""
    report.tex_crest_threshold = 0

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
    setattr(bpy.context.scene.OceanBakerReport, prop_name, prop_value)

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
def get_packed_11_10_10_xyz(x: float, x_offset: float, x_range: float, y: float, y_offset: float, y_range: float, z: float, z_offset: float, z_range: float) -> float:  
    """ 
    Algorithm to pack three floats into one, using 11, 10 and 10 bits of precision while preventing NaNs.

    32bit float NaNs are encoded with the exponent field filled with ones.
      SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
    > S11111111MMMMMMMMMMMMMMMMMMMMMMM = NAN
    > XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ

    We'd like to pack the three floats ideally using 11, 11 and 10 bits of precision, totalling 32 bits.
    We may however only use 31 bits and split the bits of the first float into two groups of bits, as to
    ensure the exponent field isn't filled with ones, thus using 11, 10 and 10 bits of precision.
    
      XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ

    :param x: first float to pack
    :param x_offset: 
    :param x_range: 
    :param y: second float to pack
    :param y_offset: 
    :param y_range: 
    :param z: third float to pack
    :param z_offset: 
    :param z_range: 
    :return: bit-packed float
    :rtype: float
    """

    a = min(1.0, max(0.0, (x - x_offset) / x_range))
    bitstring_a = str(bin(math.floor(a * ((1 << 11) - 1))))
    bitstring_a = bitstring_a[2:] # get rid of 0b
    bitstring_a = bitstring_a.zfill(11) # ensure it's 11 char long

    bitstring_a_a = bitstring_a[:8] # get first 8 characters
    bitstring_a_b = bitstring_a[-3:] # get last 3 characters
    bitstring_a = bitstring_a_a + "0" + bitstring_a_b # reconstruct 12 bits integer with the last exponent bit as 0 to prevent NaNs

    b = min(1.0, max(0.0, (y - y_offset) / y_range))
    bitstring_b = str(bin(math.floor(b * ((1 << 10) - 1))))
    bitstring_b = bitstring_b[2:] # get rid of 0b
    bitstring_b = bitstring_b.zfill(10) # ensure it's 10 char long

    c = min(1.0, max(0.0, (z - z_offset) / z_range))
    bitstring_c = str(bin(math.floor(c * ((1 << 10) - 1))))
    bitstring_c = bitstring_c[2:] # get rid of 0b
    bitstring_c = bitstring_c.zfill(10) # ensure it's 10 char long

    bits_string = "0b" + bitstring_a + bitstring_b + bitstring_c
    cp = pointer(c_int(int(bits_string, 0)))
    fp = cast(cp, POINTER(c_float))
    return fp.contents.value

def get_packed_16_15_xy(x: float, x_offset: float, x_range: float, y: float, y_offset: float, y_range: float) -> float:
    """ 
    Algorithm to pack two floats into one, using 15 and 16 bits of precision while preventing NaNs.

    32bit float NaNs are encoded with the exponent field filled with ones.
      SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
    > S11111111MMMMMMMMMMMMMMMMMMMMMMM = NAN

    We'd like to pack two 16 bits value (x,y) into the 32 bits of the float but we may only pack a
    16-bit and 15-bit values and split the first 16 bits into two groups of bits, as to ensure the
    exponent field isn't filled with ones.

    > XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY

    max - min is assumed to be non-zero!

    :param x: first float to pack
    :param x_offset: 
    :param x_range: 
    :param y: second float to pack
    :param y_offset: 
    :param y_range: 
    :return: bit-packed float
    :rtype: float
    """

    a = min(1.0, max(0.0, (x - x_offset) / x_range))
    bitstring_a = str(bin(math.floor(a * ((1 << 16) - 1))))
    bitstring_a = bitstring_a[2:] # get rid of '0b'
    bitstring_a = bitstring_a.zfill(16) # ensure it's 16 char long

    bitstring_a_a = bitstring_a[:8] # get first 8 characters
    bitstring_a_b = bitstring_a[-8:] # get last 8 characters
    bitstring_a = bitstring_a_a + "0" + bitstring_a_b # use 17 bits integer with the last exponent bit as 0 to prevent NaNs

    b = min(1.0, max(0.0, (y - y_offset) / y_range))
    bitstring_b = str(bin(math.floor(b * ((1 << 15) - 1))))
    bitstring_b = bitstring_b[2:] # get rid of '0b'
    bitstring_b = bitstring_b.zfill(15) # ensure it's 15 char long

    bits_string = "0b" + bitstring_a + bitstring_b

    cp = pointer(c_int(int(bits_string, 0)))
    fp = cast(cp, POINTER(c_float))
    return fp.contents.value

############
### BAKE ###
def get_bake_frames(context: bpy.types.Context) -> tuple[bool, str, list, int, int, int]:
    """
    Return the list of frames to bake and the start/end frames.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of frames in order, number of frames, bake start & end frames
    :rtype: tuple
    """

    settings = context.scene.OceanBakerSettings

    add_bake_report("frame_rate", (context.scene.render.fps / context.scene.render.fps_base))

    if settings.frame_range_mode == "SCENE":
        frames_to_bake = list(range(context.scene.frame_start, context.scene.frame_end + 1, context.scene.frame_step))
        add_bake_report("frame_step", context.scene.frame_step)
    else: # CUSTOM
        frames_to_bake = list(range(settings.frame_range_custom_start, settings.frame_range_custom_end + 1, settings.frame_range_custom_step))
        add_bake_report("frame_step", settings.frame_range_custom_step)

    bake_frame_start = min(frames_to_bake)
    bake_frame_end = max(frames_to_bake)

    add_bake_report("start_frame", bake_frame_start)
    add_bake_report("end_frame", bake_frame_end)

    num_frames = len(frames_to_bake)
    add_bake_report("num_frames", num_frames)
    if num_frames <= 0:
        return (False, "Too few frames to bake", [], 0, 0)

    return (True, "", frames_to_bake, num_frames, bake_frame_start, bake_frame_end)

def get_bake_frame_size(context: bpy.types.Context) -> int:
    """
    Return the size of each frame. Size is both the width & height since frame are squared
    
    :param context: Blender current execution context
    :return: frame size (width & height)
    :rtype: int
    """
    
    settings = context.scene.OceanBakerSettings
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
    settings = context.scene.OceanBakerSettings
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

    settings = context.scene.OceanBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.FFT"
    return name

def bake_frames(context: bpy.types.Context, obj: bpy.types.Object, frames_to_bake: list, extents: float, bake_name: str) -> tuple[bool, str, list, list]:
    """
    Generate and output a list of images, one per frame to bake, containing the baked positional & normal data. Amount of images should equal amount of frames to bake.
    Each frame is initially sized according to the amount of subdivisions set in the ocean modifier (e.g. 5 for 25x25 vertices), and then possibly rescaled to match the
    custom frame size set by the user, if any.

    :param context: Blender current execution context
    :param obj: the ocean object
    :param frames_to_bake: list of frames to loop through
    :param extents: the ocean's modifier extents
    :param bake_name: the bake operation's 'name'
    :return: the function's success, potential error message, offset image(s), normal image(s)
    """

    settings = context.scene.OceanBakerSettings
    
    """
    offset global min/max & remap
    """

    # if buffer_x_min and buffer_x_max:
    #     if abs(buffer_x_max - buffer_x_min) < 0.0001:
    #         buffer_x_range = 1.0
    #     else:
    #         buffer_x_range = buffer_x_max - buffer_x_min
    #     buffer_x_offset = buffer_x_min
    # else:
    #     buffer_x_range = 1.0
    #     buffer_x_offset = 0.0

    # if buffer_y_min and buffer_y_max:
    #     if abs(buffer_y_max - buffer_y_min) < 0.0001:
    #         buffer_y_range = 1.0
    #     else:
    #         buffer_y_range = buffer_y_max - buffer_y_min
    #     buffer_y_offset = buffer_y_min
    # else:
    #     buffer_y_range = 1.0
    #     buffer_y_offset = 0.0

    # if buffer_z_min and buffer_z_max:
    #     if abs(buffer_z_max - buffer_z_min) < 0.0001:
    #         buffer_z_range = 1.0
    #     else:
    #         buffer_z_range = buffer_z_max - buffer_z_min
    #     buffer_z_offset = buffer_z_min
    # else:
    #     buffer_z_range = 1.0
    #     buffer_z_offset = 0.0

    # add_bake_report("mesh_min_bounds_offset", mathutils.Vector((abs(buffer_x_min), abs(buffer_y_min), abs(buffer_z_min))))
    # add_bake_report("mesh_max_bounds_offset", mathutils.Vector((abs(buffer_x_max), abs(buffer_y_max), abs(buffer_z_max))))

    # offset_range_offset = mathutils.Vector((buffer_x_offset, buffer_y_offset, buffer_z_offset))
    # offset_range = mathutils.Vector((buffer_x_range, buffer_y_range, buffer_z_range))

    # bpy.context.window_manager.progress_update(91)

    #     add_bake_report("tex_offset_remapped", True)
    #     add_bake_report("tex_offset_range_offset", offset_range_offset)
    #     add_bake_report("tex_offset_range", offset_range)

    return (True, "", 0, 0, 0)

def cubic_bezier(P0, P1, P2, P3, t):
    """
    Interpolate a cubic Bézier curve.

    Parameters:
    - P0, P1, P2, P3: Control points (each a tuple/list of x, y or x, y, z)
    - t: Parameter between 0 and 1

    Returns:
    - A point on the curve at parameter t (same dimension as input points)
    """
    def lerp(A, B, t):
        return [a + (b - a) * t for a, b in zip(A, B)]

    A = lerp(P0, P1, t)
    B = lerp(P1, P2, t)
    C = lerp(P2, P3, t)

    D = lerp(A, B, t)
    E = lerp(B, C, t)

    point = lerp(D, E, t)
    return point

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    settings = context.scene.OceanBakerSettings
    new_bake_report(context)

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #

    bake_start_time = time.time()

    success, msg, frames_to_bake, num_frames, bake_frame_start, bake_frame_end = get_bake_frames(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)

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

    success, msg, extents, ocean_modifier_a, ocean_modifier_b = setup_ocean_modifiers(context, obj, active_obj, bake_frame_start, bake_frame_end)
    if not success:
        clear_ocean_mesh(obj)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)


    wm.progress_update(10)

    success, msg, obj_to_export = NEW_generate_mesh(context, obj, bake_name, bake_frame_start)
    if success:
        add_bake_report("mesh", obj_to_export)

    set_ocean_modifier_time(settings.ocean_time, False, bake_frame_start, bake_frame_end, ocean_modifier_a)
    set_ocean_modifier_wave_scale(settings.ocean_scale, False, bake_frame_start, bake_frame_end, ocean_modifier_a)

    set_ocean_modifier_time(settings.ocean_time, True, bake_frame_start, bake_frame_end, ocean_modifier_b)
    set_ocean_modifier_wave_scale(settings.ocean_scale, True, bake_frame_start, bake_frame_end, ocean_modifier_b)

    modify_ocean_modifiers_interp(obj, ocean_modifier_a, ocean_modifier_b)

    subdivisions = max(2, settings.subd)
    add_bake_report("subd", subdivisions)  

    num_verts_row_unique = 128#subdivisions*subdivisions
    num_verts_unique = num_verts_row_unique * num_verts_row_unique
    num_verts_row = num_verts_row_unique + 1
    num_verts = num_verts_row * num_verts_row

    padding = get_bake_frame_padding(context, clamp=True)
    num_padding_x = padding
    num_padding_y = padding
    add_bake_report("frame_padding", padding)

    if settings.frame_size_mode == "CUSTOM":
        frame_size = settings.frame_size_custom
    else:
        frame_size = get_bake_frame_size(context)
    add_bake_report("frame_size", frame_size)
    
    frame_size_inner = frame_size - (padding * 2)
    num_samples_x = frame_size_inner
    num_samples_y = frame_size_inner
    
    add_bake_report("frame_sort_mode", settings.frame_sort_mode)

    success, msg, num_frames_x, num_frames_y, tex_width, tex_height = get_flipbook_frames(context, num_frames)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)
    
    crest_threshold = -0.5
    
    ########
    # BAKE #
    

    dgraph = context.evaluated_depsgraph_get()

    # Determine correct library name and extension
    system = platform.system()
    if system == 'Linux':
        libname = './OceanBakerDLL.so'
    elif system == 'Darwin':  # macOS
        libname = './OceanBakerDLL.dylib'
    elif system == 'Windows':
        libname = 'OceanBakerDLL.dll'
    else:
        raise RuntimeError(f'Unsupported platform: {system}')

    # Load the shared library
    try:
        OceanBakerDLL = ctypes.CDLL(r"G:\BlenderGameTools\Ocean\OceanBakerDLL\x64\Release\OceanBakerDLL.dll")
    except:
        return (False, "ERROR", "no DLL")

    # Define argument and return types
    OceanBakerDLL.BakeOcean.argtypes = [ctypes.c_int, # inNumPoints
                                          ctypes.c_float, # inSpatialSize
                                          ctypes.c_float, # inWindSpeed
                                          ctypes.c_float, # inSmallestWave
                                          ctypes.c_float, # inWaveAngle
                                          ctypes.c_float, # inDamp
                                          ctypes.c_float, # inAlignment
                                          ctypes.c_float, # inDepth
                                          ctypes.c_float, # inDuration
                                          ctypes.c_float, # inChopAmount
                                          ctypes.c_int,  # inSpectrum
                                          ctypes.c_float, # inFetchJONSWAP
                                          ctypes.c_float, # inSharpenPeakJONSWAP
                                          ctypes.c_int, # inSeed
                                          ctypes.POINTER(ctypes.c_float), # outMinMaxBuffer
                                          ctypes.POINTER(ctypes.c_float), # outPixelBuffer
                                          ctypes.POINTER(ctypes.c_float), # outVertexBuffer
                                          ctypes.POINTER(ctypes.c_float), # outSplashBuffer
                                          ctypes.POINTER(ctypes.c_int), # outNumSplashes
                                          ctypes.POINTER(ctypes.c_float), # outSplashFrameBuffer
                                          ctypes.POINTER(ctypes.c_float), # outCrestBuffer
    ]
    OceanBakerDLL.BakeOcean.restype = ctypes.c_int

    h0_px_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_row_unique * num_verts_row_unique * 8 * 8
    h0_vtx_buffer = [0.0, 0.0, 0.0] * num_verts_row_unique * num_verts_row_unique * 8 * 8
    splash_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_row_unique * num_verts_row_unique * 8 * 8
    splash_framebuffer = [0.0, 0.0] * 8 * 8
    crest_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_row_unique * num_verts_row_unique * 8 * 8
    minmax_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_row_unique * num_verts_row_unique * 8 * 8
    minmax_buffer_ptr = (ctypes.c_float*len(minmax_buffer))(*minmax_buffer)
    h0_px_buffer_ptr = (ctypes.c_float*len(h0_px_buffer))(*h0_px_buffer)
    h0_vtx_buffer_ptr = (ctypes.c_float*len(h0_vtx_buffer))(*h0_vtx_buffer)
    splash_buffer_ptr = (ctypes.c_float*len(splash_buffer))(*splash_buffer)
    splash_framebuffer_ptr = (ctypes.c_float*len(splash_framebuffer))(*splash_framebuffer)
    crest_buffer_ptr = (ctypes.c_float*len(crest_buffer))(*crest_buffer)
    num_splashes = c_int(0)
    num_splashes_ptr = ctypes.pointer(num_splashes)
    

    ChopAmount = 1.0
    Duration = 10
    Spectrum = 0
    JSON_FETCH = 0.0
    JSON_PEAK = 120


    OceanBakerDLL.BakeOcean(num_verts_row_unique,
                              settings.ocean_spatial_size,
                              settings.ocean_wind_vel,
                              settings.ocean_smallest_wave,
                              settings.ocean_direction,
                              settings.ocean_damping,
                              settings.ocean_alignment,
                              settings.ocean_depth,
                              Duration,
                              ChopAmount,
                              Spectrum,
                              JSON_FETCH,
                              JSON_PEAK,
                              settings.ocean_seed,
                              minmax_buffer_ptr,
                              h0_px_buffer_ptr,
                              h0_vtx_buffer_ptr,
                              splash_buffer_ptr,
                              num_splashes_ptr,
                              splash_framebuffer_ptr,
                              crest_buffer_ptr)
    
    h0_px_buffer = list(h0_px_buffer_ptr)
    h0_vtx_buffer = list(h0_vtx_buffer_ptr)

    success, msg, tex = generate_texture(bake_name, "crest", list(crest_buffer_ptr), num_verts_row_unique * 8, num_verts_row_unique * 8)
    success, msg, tex = generate_texture(bake_name, "bitpack_x", h0_px_buffer, num_verts_row_unique * 8, num_verts_row_unique * 8)
    success, msg, path = export_texture(context, tex, settings.export_tex_file_path, "bitpack_x", bake_name, settings.export_tex_override)


    num_splashes_sqrt = math.sqrt(num_splashes.value)
    num_splashes_x = math.ceil(num_splashes_sqrt)
    num_splashes_y = math.ceil(num_splashes_sqrt)
    print(str(num_splashes_x * num_splashes_y * 4))
    splash_buffer = list(splash_buffer_ptr)
    splash_buffer = splash_buffer[:num_splashes_x * num_splashes_y * 4]

    splash_buffer = get_inverted_buffers(splash_buffer, num_splashes_x, num_splashes_y)

    success, msg, tex = generate_texture(bake_name, "splash", splash_buffer, num_splashes_x, num_splashes_y)
    success, msg, path = export_texture(context, tex, settings.export_tex_file_path, "splash", bake_name, settings.export_tex_override)

    splash_framebuffer = list(splash_framebuffer_ptr)
    splash_truc = []
    splash_info = []
    for i in range(8*8):
        splash_info.append(splash_framebuffer_ptr[i*2 + 0])
        splash_truc.extend((splash_framebuffer_ptr[i*2 + 0], splash_framebuffer_ptr[i*2 + 1], 0, 1))

    splash_truc = get_inverted_buffers(splash_truc, 1, (8*8))

    print(splash_info)
    success, msg, tex = generate_texture(bake_name, "splash_buffer", splash_truc, 1, (8*8))
    success, msg, path = export_texture(context, tex, settings.export_tex_file_path, "splash_buffer", bake_name, settings.export_tex_override)

    #OceanBakerDLL.do_bezier()

    del OceanBakerDLL

    debug_verts = []
    for frame_index, frames in enumerate(range(8*8)):
        vertex_index = (frame_index * 3) + (8*8 * 3)
        debug_verts.append(mathutils.Vector((h0_vtx_buffer[vertex_index + 0], h0_vtx_buffer[vertex_index + 1], h0_vtx_buffer[vertex_index + 2])))

    verts_x = [v.x for v in debug_verts]
    verts_y = [v.y for v in debug_verts]
    verts_z = [v.z for v in debug_verts]

    mesh = bpy.data.meshes.new(name="CustomMesh")
    obj = bpy.data.objects.new(name="CustomObject", object_data=mesh)
    collection = bpy.context.collection
    collection.objects.link(obj)
    mesh.from_pydata(debug_verts, [], [])
    mesh.update()

    # Use bmesh to create vertices and edges
    bm = bmesh.new()

    # Create a list of bmesh verts
    bm_verts = [bm.verts.new(co) for co in debug_verts]

    # Ensure bmesh internal tables are updated
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()

    # Create edges connecting each vertex to the next
    for i in range(len(bm_verts)):
        bm.edges.new((bm_verts[i], bm_verts[(i + 1) % len(bm_verts)]))

    # Write the bmesh to the mesh
    bm.to_mesh(mesh)
    bm.free()



    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))







    new_px_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_unique * num_frames
    offset = []
    maxoffset = mathutils.Vector((float('-INF'), float('-INF'), float('-INF')))
    minoffset = mathutils.Vector((float('+INF'), float('+INF'), float('+INF')))

    for frame_index, frame in enumerate(frames_to_bake):
        context.scene.frame_set(frame)
        obj_eval = obj.evaluated_get(dgraph)
        obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

        frame_float_offset = frame * num_verts_unique * 3
        for vert_x in range(num_verts_row_unique):
            for vert_y in range(num_verts_row_unique):
                vertex_index = vert_x + (vert_y * num_verts_row)
                buff_index = vert_x + (vert_y * num_verts_row_unique)
                i = frame_float_offset + (buff_index * 3)
                offset_vec = (obj_eval_mesh.vertices[vertex_index].co.copy() - obj_to_export.data.vertices[vertex_index].co) * settings.unit_scale
                maxoffset.x = max(offset_vec.x, maxoffset.x)
                maxoffset.y = max(offset_vec.y, maxoffset.y)
                maxoffset.z = max(offset_vec.z, maxoffset.z)

                minoffset.x = min(offset_vec.x, minoffset.x)
                minoffset.y = min(offset_vec.y, minoffset.y)
                minoffset.z = min(offset_vec.z, minoffset.z)
                #new_px_buffer[i] = offset_vec
   
    offset_range = maxoffset - minoffset
    print(offset_range)
    print(minoffset)

    for frame_index, frame in enumerate(frames_to_bake):
        context.scene.frame_set(frame)
        obj_eval = obj.evaluated_get(dgraph)
        obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

        frame_float_offset = frame * num_verts_unique * 3

        frame_x = frame_index % num_frames_x
        frame_y = num_frames_y - 1 - (frame_index // num_frames_x)
        for vert_x in range(num_verts_row_unique):
            for vert_y in range(num_verts_row_unique):
                vertex_index = vert_x + (vert_y * num_verts_row)
                offset_vec = (obj_eval_mesh.vertices[vertex_index].co.copy() - obj_to_export.data.vertices[vertex_index].co) * settings.unit_scale

                i = (vert_x * 4) + (vert_y * num_verts_row_unique * num_frames_x * 4) + (frame_x * num_verts_row_unique * 4) + (frame_y * num_verts_unique * num_frames_x * 4)
                new_px_buffer[i] = get_packed_11_10_10_xyz(offset_vec.z, minoffset.z, offset_range.z, offset_vec.y, minoffset.y, offset_range.y, offset_vec.x, minoffset.x, offset_range.x)



    startctrlpts_buffer= get_inverted_buffers(new_px_buffer, num_verts_row_unique * num_frames_x,  num_verts_row_unique * num_frames_y)

    success, msg, tex_startctrlpts = generate_texture(bake_name, "bitpack_x", new_px_buffer, num_verts_row_unique * num_frames_x, num_verts_row_unique * num_frames_y)

    success, msg, tex_offset_path = export_texture(context, tex_startctrlpts, settings.export_tex_file_path, "bitpack_x", bake_name, settings.export_tex_override)


    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))







    debug_verts = []
    if False:
        #num_frames = 64 - ((64/8) - 1) # 57
        num_frames = 57 # frames range must be [1 - 56]
        num_segments = (num_frames - 1) // 8
        float_buffer = [0.0] * num_frames * num_verts_unique * 3
        for frame in range(num_frames):
            context.scene.frame_set(frame + 1)
            obj_eval = obj.evaluated_get(dgraph)
            obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

            frame_float_offset = frame * num_verts_unique * 3
            for vert_x in range(num_verts_row_unique): # skip last duplicated vert (tiling mesh)
                for vert_y in range(num_verts_row_unique): # skip last duplicated vert (tiling mesh)
                    vertex_index = vert_x + (vert_y * num_verts_row)
                    buff_index = vert_x + (vert_y * num_verts_row_unique)
                    i = frame_float_offset + (buff_index * 3)
                    offset = (obj_eval_mesh.vertices[vertex_index].co.copy() - obj_to_export.data.vertices[vertex_index].co) * settings.unit_scale
                    float_buffer[i:i+3] = offset

        vertexbuffer = (ctypes.c_float*len(float_buffer))(*float_buffer)

    clear_ocean_mesh(obj_to_export)
    #clear_ocean_mesh(obj)

    startctrlpts = [0.0, 0.0, 0.0] * num_verts_unique * num_segments
    starttangents = [0.0, 0.0, 0.0] * num_verts_unique * num_segments
    endtangents = [0.0, 0.0, 0.0] * num_verts_unique * num_segments
    endctrlpts = [0.0, 0.0, 0.0] * num_verts_unique * num_segments
    bitpacked_data = [0.0, 0.0, 0.0, 0.0] * num_verts_unique * num_segments

    test_vbuffer = (ctypes.c_float*len(vertexbuffer))(*vertexbuffer)
    test_startctrlpts = (ctypes.c_float*len(startctrlpts))(*startctrlpts)
    test_starttangents = (ctypes.c_float*len(starttangents))(*starttangents)
    test_endtangents = (ctypes.c_float*len(endtangents))(*endtangents)
    test_endctrlpts = (ctypes.c_float*len(endctrlpts))(*endctrlpts)
    test_bitpacked_data = (ctypes.c_float*len(bitpacked_data))(*bitpacked_data)

    OceanBakerDLL.BakeSplineApproximation(num_verts_row_unique, num_frames, num_segments, test_vbuffer, test_startctrlpts, test_starttangents, test_endtangents, test_endctrlpts, test_bitpacked_data)

    del OceanBakerDLL

    startctrlpts = list(test_startctrlpts)
    starttangents = list(test_starttangents)
    endtangents = list(test_endtangents)
    endctrlpts = list(test_endctrlpts)
    bitpacked_data = list(test_bitpacked_data)

    num_segments_sqrt = math.ceil(math.sqrt(num_segments))
    num_frames_x = num_segments_sqrt
    num_frames_y = num_segments_sqrt

    startctrlpts_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_unique * num_frames_x * num_frames_y
    starttangents_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_unique * num_frames_x * num_frames_y
    endtangents_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_unique * num_frames_x * num_frames_y
    endctrlpts_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_unique * num_frames_x * num_frames_y
    bitpacked_data_buffer = [0.0, 0.0, 0.0, 1.0] * num_verts_unique * num_frames_x * num_frames_y

    for vert_x in range(num_verts_row_unique):
        for vert_y in range(num_verts_row_unique):
            vertex_index = vert_x + vert_y * num_verts_row_unique
            for frame_x in range(num_frames_x):
                for frame_y in range(num_frames_y):
                    frame_index = frame_x + frame_y * num_frames_x
                    if frame_index >= (num_segments):
                        continue
                    
                    ctrlpt_index = (vertex_index * num_segments * 3) + (frame_index * 3)
                    pixel_index = (vert_x * 4) + (vert_y * num_verts_row_unique * num_frames_x * 4) + (frame_x * num_verts_row_unique * 4) + (frame_y * num_verts_row_unique * num_verts_row_unique * num_frames_x * 4)
                    
                    try:
                        startctrlpts_buffer[pixel_index + 0] = startctrlpts[ctrlpt_index + 0]
                        if ctrlpt_index == (num_verts_unique * num_frames_x * num_frames_y) - 1:
                            print(str(ctrlpt_index))
                    except:
                        print(str(ctrlpt_index))
                        print(str(ctrlpt_index))
                        print(str(len(startctrlpts)))
                        print(str(len(startctrlpts)))

                        continue

                    startctrlpts_buffer[pixel_index + 1] = startctrlpts[ctrlpt_index + 1]
                    startctrlpts_buffer[pixel_index + 2] = startctrlpts[ctrlpt_index + 2]

                    starttangents_buffer[pixel_index + 0] = starttangents[ctrlpt_index + 0]
                    starttangents_buffer[pixel_index + 1] = starttangents[ctrlpt_index + 1]
                    starttangents_buffer[pixel_index + 2] = starttangents[ctrlpt_index + 2]

                    endtangents_buffer[pixel_index + 0] = endtangents[ctrlpt_index + 0]
                    endtangents_buffer[pixel_index + 1] = endtangents[ctrlpt_index + 1]
                    endtangents_buffer[pixel_index + 2] = endtangents[ctrlpt_index + 2]

                    endctrlpts_buffer[pixel_index + 0] = endctrlpts[ctrlpt_index + 0]
                    endctrlpts_buffer[pixel_index + 1] = endctrlpts[ctrlpt_index + 1]
                    endctrlpts_buffer[pixel_index + 2] = endctrlpts[ctrlpt_index + 2]

                    ctrlpt_index = (vertex_index * num_segments * 4) + (frame_index * 4)
                    bitpacked_data_buffer[pixel_index + 0] = bitpacked_data[ctrlpt_index + 0]
                    bitpacked_data_buffer[pixel_index + 1] = bitpacked_data[ctrlpt_index + 1]
                    bitpacked_data_buffer[pixel_index + 2] = bitpacked_data[ctrlpt_index + 2]
                    bitpacked_data_buffer[pixel_index + 3] = bitpacked_data[ctrlpt_index + 3]

    # startctrlpts_buffer = list(startctrlpts_buffer)
    # starttangents_buffer = list(starttangents_buffer)
    # endtangents_buffer = list(endtangents_buffer)
    # endctrlpts_buffer = list(endctrlpts_buffer)

    startctrlpts_buffer= get_inverted_buffers(startctrlpts_buffer, num_verts_row_unique * num_frames_x,  num_verts_row_unique * num_frames_y)
    starttangents_buffer = get_inverted_buffers(starttangents_buffer, num_verts_row_unique * num_frames_x,  num_verts_row_unique * num_frames_y)
    endtangents_buffer = get_inverted_buffers(endtangents_buffer, num_verts_row_unique * num_frames_x,  num_verts_row_unique * num_frames_y)
    endctrlpts_buffer= get_inverted_buffers(endctrlpts_buffer, num_verts_row_unique * num_frames_x,  num_verts_row_unique * num_frames_y)
    bitpacked_data_buffer= get_inverted_buffers(bitpacked_data_buffer, num_verts_row_unique * num_frames_x,  num_verts_row_unique * num_frames_y)

    success, msg, tex_startctrlpts = generate_texture(bake_name, "startctrlpts", startctrlpts_buffer, num_verts_row_unique * num_frames_x, num_verts_row_unique * num_frames_y)
    success, msg, tex_starttangents = generate_texture(bake_name, "starttangents", starttangents_buffer, num_verts_row_unique * num_frames_x, num_verts_row_unique * num_frames_y)
    success, msg, tex_endtangents = generate_texture(bake_name, "endtangents", endtangents_buffer, num_verts_row_unique * num_frames_x, num_verts_row_unique * num_frames_y)
    success, msg, tex_endctrlpts = generate_texture(bake_name, "endctrlpts", endctrlpts_buffer, num_verts_row_unique * num_frames_x, num_verts_row_unique * num_frames_y)
    success, msg, tex_bitpacked = generate_texture(bake_name, "bitpacked", bitpacked_data_buffer, num_verts_row_unique * num_frames_x, num_verts_row_unique * num_frames_y)

    success, msg, tex_offset_path = export_texture(context, tex_startctrlpts, settings.export_tex_file_path, "startctrlpts", bake_name, settings.export_tex_override)
    success, msg, tex_offset_path = export_texture(context, tex_starttangents, settings.export_tex_file_path, "starttangents", bake_name, settings.export_tex_override)
    success, msg, tex_offset_path = export_texture(context, tex_endtangents, settings.export_tex_file_path, "endtangents", bake_name, settings.export_tex_override)
    success, msg, tex_offset_path = export_texture(context, tex_endctrlpts, settings.export_tex_file_path, "endctrlpts", bake_name, settings.export_tex_override)
    success, msg, tex_offset_path = export_texture(context, tex_bitpacked, settings.export_tex_file_path, "bitpacked", bake_name, settings.export_tex_override)


    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

    test_inputs = [0.0, 0.0, 0.0, 0.0561969168484211, 0.11522816866636276, -0.01085176132619381, 0.12684419751167297, 0.38062530755996704, 0.07358774542808533, 0.06502671539783478, 0.6757602691650391, 0.42881065607070923, -0.21285921335220337, 0.9035319685935974, 1.1322699785232544, -0.5371711254119873, 1.060158610343933, 1.8692622184753418, -0.7198415994644165, 1.1743383407592773, 2.313441276550293, -0.7523500919342041, 1.311371088027954, 2.48404860496521, -0.6710625886917114, 1.5457063913345337, 2.4867236614227295, -0.5044344067573547, 1.9116953611373901, 2.4003050327301025, -0.24927812814712524, 2.2832934856414795, 2.1964316368103027, 0.10550446063280106, 2.4943573474884033, 1.8199424743652344, 0.5360726714134216, 2.4510178565979004, 1.2693169116973877, 0.8788304924964905, 2.348505735397339, 0.7575936317443848, 0.99153071641922, 2.3881828784942627, 0.4879916310310364, 0.9570770263671875, 2.5068438053131104, 0.40988993644714355]
    test_num_inputs = len(test_inputs)
    test_num_points = test_num_inputs // 3
    test_num_segments = test_num_points // 8
    test_num_ctrl_points = test_num_segments * 4
    test_outputs = [0.0, 0.0, 0.0] * test_num_ctrl_points

    test_inputs_buffer = (ctypes.c_float*len(test_inputs))(*test_inputs)
    test_outputs_buffer = (ctypes.c_float*len(test_outputs))(*test_outputs)

    OceanBakerDLL.SplineApproximation(test_inputs_buffer, test_num_inputs, test_outputs_buffer)

    debug_verts = []
    for i in range(test_num_points):
        debug_verts.append((test_inputs[i * 3 + 0], test_inputs[i * 3 + 1], test_inputs[i * 3 + 2]))

    mesh = bpy.data.meshes.new(name="CustomMesh")
    obj = bpy.data.objects.new(name="CustomObject", object_data=mesh)
    collection = bpy.context.collection
    collection.objects.link(obj)
    mesh.from_pydata(debug_verts, [], [])
    mesh.update()

    test_outputs = list(test_outputs_buffer)

    # ctrl_point = 2
    # CP2 = mathutils.Vector((test_outputs[ctrl_point * 3 + 0], test_outputs[ctrl_point * 3 + 1], test_outputs[ctrl_point * 3 + 2]))
    # ctrl_point = 3
    # CP3 = mathutils.Vector((test_outputs[ctrl_point * 3 + 0], test_outputs[ctrl_point * 3 + 1], test_outputs[ctrl_point * 3 + 2]))
    # ctrl_point = 5
    # CP5 = mathutils.Vector((test_outputs[ctrl_point * 3 + 0], test_outputs[ctrl_point * 3 + 1], test_outputs[ctrl_point * 3 + 2]))
    # CP5 -= CP3
    # CP5 *= -1
    # CP5 += CP3

    # CPAverage = mathutils.Vector.lerp(CP2, CP5, 0.5)
    # ctrl_point = 2
    # test_outputs[ctrl_point * 3 + 0] = CPAverage[0]
    # test_outputs[ctrl_point * 3 + 1] = CPAverage[1]
    # test_outputs[ctrl_point * 3 + 2] = CPAverage[2]

    # ctrl_point = 2
    # CP2 = mathutils.Vector((test_outputs[ctrl_point * 3 + 0], test_outputs[ctrl_point * 3 + 1], test_outputs[ctrl_point * 3 + 2]))
    # ctrl_point = 3
    # CP3 = mathutils.Vector((test_outputs[ctrl_point * 3 + 0], test_outputs[ctrl_point * 3 + 1], test_outputs[ctrl_point * 3 + 2]))
    # ctrl_point = 5
    # CP5 = mathutils.Vector((test_outputs[ctrl_point * 3 + 0], test_outputs[ctrl_point * 3 + 1], test_outputs[ctrl_point * 3 + 2]))
    # CP2 -= CP3
    # CP2 *= -1
    # CP2 += CP3
    # CPAverage = mathutils.Vector.lerp(CP2, CP5, 0.5)
    # ctrl_point = 5
    # test_outputs[ctrl_point * 3 + 0] = CPAverage[0]
    # test_outputs[ctrl_point * 3 + 1] = CPAverage[1]
    # test_outputs[ctrl_point * 3 + 2] = CPAverage[2]

    debug_verts = []
    for i in range(test_num_ctrl_points):
        debug_verts.append((test_outputs[i * 3 + 0], test_outputs[i * 3 + 1], test_outputs[i * 3 + 2]))

    mesh = bpy.data.meshes.new(name="CustomMeshBezier")
    obj = bpy.data.objects.new(name="CustomObjectBezier", object_data=mesh)
    collection = bpy.context.collection
    collection.objects.link(obj)
    mesh.from_pydata(debug_verts, [], [])
    mesh.update()

    debug_verts = []
    for i in range(test_num_segments):
        offset = (i * 4 * 3)
        y = 0
        P0 = [test_outputs[offset + (y * 3) + 0], test_outputs[offset + (y * 3) + 1], test_outputs[offset + (y * 3) + 2]]

        y = 1
        P1 = [test_outputs[offset + (y * 3) + 0], test_outputs[offset + (y * 3) + 1], test_outputs[offset + (y * 3) + 2]]

        y = 2
        P2 = [test_outputs[offset + (y * 3) + 0], test_outputs[offset + (y * 3) + 1], test_outputs[offset + (y * 3) + 2]]

        y = 3
        P3 = [test_outputs[offset + (y * 3) + 0], test_outputs[offset + (y * 3) + 1], test_outputs[offset + (y * 3) + 2]]

        for t in range(10):
            debug_verts.append(cubic_bezier(P0, P1, P2, P3, t/9))

    mesh = bpy.data.meshes.new(name="CustomMeshBezierInterp")
    obj = bpy.data.objects.new(name="CustomMeshBezierInterp", object_data=mesh)
    collection = bpy.context.collection
    collection.objects.link(obj)
    mesh.from_pydata(debug_verts, [], [])
    mesh.update()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

    buffer_length = len(frames_to_bake) * frame_size * frame_size * 4
    offsetbuffer = (ctypes.c_float * buffer_length)(0.0)
    normalbuffer = (ctypes.c_float * buffer_length)(0.0)
    crestbuffer = (ctypes.c_float * buffer_length)(0.0)
    
    num_splash = settings.splash_num # candidates per frame
    buffer_length = len(frames_to_bake) * num_splash * 4
    splashbuffer = (ctypes.c_float * buffer_length)(0.0)

    OceanBakerDLL.Bake(ctypes.c_int(subdivisions),
                       ctypes.c_int(num_frames_x),
                       ctypes.c_int(num_frames_y),
                       ctypes.c_int(num_samples_x),
                       ctypes.c_int(num_samples_y),
                       ctypes.c_int(num_padding_x),
                       ctypes.c_int(num_padding_y),
                       ctypes.c_float(extents),
                       ctypes.c_float(settings.crest_threshold),
                       ctypes.c_float(settings.splash_threshold),
                       ctypes.c_int(num_splash),
                       vertexbuffer,
                       offsetbuffer,
                       normalbuffer,
                       crestbuffer,
                       splashbuffer)



    add_bake_report("tex_mode", settings.tex_mode)
    if settings.tex_mode == "FLIPBOOK":
        add_bake_report("tex_width", tex_width)
        add_bake_report("tex_height", tex_height)

        if settings.offset_tex:
            success, msg, tex_offset = generate_texture(bake_name, settings.offset_tex_file_name, list(offsetbuffer), tex_width, tex_height)
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
            success, msg, tex_normal = generate_texture(bake_name, settings.normal_tex_file_name, list(normalbuffer), tex_width, tex_height)
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
    
        if settings.crest_tex:
            success, msg, tex_crest = generate_texture(bake_name, settings.crest_tex_file_name, list(crestbuffer), tex_width, tex_height)
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            add_bake_report("tex_crest", tex_crest)

            if settings.export_tex:
                success, msg, tex_crest_path = export_texture(context, tex_crest, settings.export_tex_file_path, settings.crest_tex_file_name, bake_name, settings.export_tex_override)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, 'ERROR', msg)
                add_bake_report("tex_crest_export", True)
                add_bake_report("tex_crest_path", tex_crest_path)

        if settings.crest_tex and settings.splash_tex:
            success, msg, tex_splash = generate_texture(bake_name, settings.splash_tex_file_name, list(splashbuffer), num_splash, len(frames_to_bake))
            if not success:
                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, "ERROR", msg)

            add_bake_report("tex_splash", tex_splash)

            if settings.export_tex:
                success, msg, tex_splash_path = export_texture(context, tex_splash, settings.export_tex_file_path, settings.splash_tex_file_name, bake_name, settings.export_tex_override)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, 'ERROR', msg)
                add_bake_report("tex_splash_export", True)
                add_bake_report("tex_splash_path", tex_splash_path)

    else:
        tex_width = frame_size
        tex_height = frame_size
        add_bake_report("tex_width", tex_width)
        add_bake_report("tex_height", tex_height)

        num_frames_x = 1 # override this for mesh uvs
        num_frames_y = 1

        for frame_index, frame_to_bake in enumerate(frames_to_bake):
            frame_buffer_length = frame_size * frame_size * 4

            frame_name_suffix = str(frame_to_bake)
            frame_name_suffix = frame_name_suffix.zfill(4)
            
            if settings.offset_tex:
                frame_offsetbuffer = (ctypes.c_float * frame_buffer_length)(0.0)
                OceanBakerDLL.GetFramePixelBuffer(ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), offsetbuffer, frame_offsetbuffer)

                success, msg, tex_offset = generate_texture(bake_name, settings.offset_tex_file_name + frame_name_suffix, list(frame_offsetbuffer), tex_width, tex_height)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, "ERROR", msg)

                if frame_index == 0:
                    add_bake_report("tex_offset", tex_offset)

                if settings.export_tex:
                    name = tex_offset.name[:-4] if len(tex_offset.name) > 4 else ''
                    success, msg, tex_offset_path = export_texture(context, tex_offset, settings.export_tex_file_path, name, bake_name, settings.export_tex_override)
                    if not success:
                        add_bake_report("success", False)
                        add_bake_report("msg", msg)
                        return (False, 'ERROR', msg)
                    if frame_index == 0:
                        add_bake_report("tex_offset_export", True)
                        add_bake_report("tex_offset_path", tex_offset_path)

            if settings.normal_tex:
                frame_normalbuffer = (ctypes.c_float * frame_buffer_length)(0.0)
                OceanBakerDLL.GetFramePixelBuffer(ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), normalbuffer, frame_normalbuffer)

                success, msg, tex_normal = generate_texture(bake_name, settings.normal_tex_file_name + frame_name_suffix, list(frame_normalbuffer), tex_width, tex_height)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, "ERROR", msg)

                if frame_index == 0:
                    add_bake_report("tex_normal", tex_normal)

                if settings.export_tex:
                    name = tex_normal.name[:-4] if len(tex_normal.name) > 4 else ''
                    success, msg, tex_normal_path = export_texture(context, tex_normal, settings.export_tex_file_path, name, bake_name, settings.export_tex_override)
                    if not success:
                        add_bake_report("success", False)
                        add_bake_report("msg", msg)
                        return (False, 'ERROR', msg)
                    if frame_index == 0:
                        add_bake_report("tex_normal_export", True)
                        add_bake_report("tex_normal_path", tex_normal_path)

            if settings.crest_tex:
                frame_crestbuffer = (ctypes.c_float * frame_buffer_length)(0.0)
                OceanBakerDLL.GetFramePixelBuffer(ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), crestbuffer, frame_crestbuffer)

                success, msg, tex_crest = generate_texture(bake_name, settings.crest_tex_file_name + frame_name_suffix, list(frame_crestbuffer), tex_width, tex_height)
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, "ERROR", msg)

                if frame_index == 0:
                    add_bake_report("tex_crest", tex_crest)

                if settings.export_tex:
                    name = tex_crest.name[:-4] if len(tex_crest.name) > 4 else ''
                    success, msg, tex_crest_path = export_texture(context, tex_crest, settings.export_tex_file_path, name, bake_name, settings.export_tex_override)
                    if not success:
                        add_bake_report("success", False)
                        add_bake_report("msg", msg)
                        return (False, 'ERROR', msg)
                    if frame_index == 0:
                        add_bake_report("tex_crest_export", True)
                        add_bake_report("tex_crest_path", tex_crest_path)

            if settings.crest_tex and settings.splash_tex:
                frame_buffer_length = num_splash, len(frames_to_bake) * 4
                frame_splashbuffer = (ctypes.c_float * frame_buffer_length)(0.0)
                OceanBakerDLL.GetFramePixelBuffer(ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), splashbuffer, frame_splashbuffer)

                success, msg, tex_splash = generate_texture(bake_name, settings.splash_tex_file_name + frame_name_suffix, list(frame_splashbuffer), num_splash, len(frames_to_bake))
                if not success:
                    add_bake_report("success", False)
                    add_bake_report("msg", msg)
                    return (False, "ERROR", msg)

                if frame_index == 0:
                    add_bake_report("tex_splash", tex_splash)

                if settings.export_tex:
                    name = tex_splash.name[:-4] if len(tex_splash.name) > 4 else ''
                    success, msg, tex_splash_path = export_texture(context, tex_splash, settings.export_tex_file_path, name, bake_name, settings.export_tex_override)
                    if not success:
                        add_bake_report("success", False)
                        add_bake_report("msg", msg)
                        return (False, 'ERROR', msg)
                    if frame_index == 0:
                        add_bake_report("tex_splash_export", True)
                        add_bake_report("tex_splash_path", tex_splash_path)

    del OceanBakerDLL

    ########
    # MESH #

    if False:
        if settings.generate_mesh:
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
    if False:
        if obj_to_export:
            obj_to_export.select_set(True)

    context.scene.frame_start = bake_frame_start
    context.scene.frame_end = bake_frame_end

    add_bake_report("success", True)
    wm.progress_update(99)
    wm.progress_end()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

def NEW_gather_mesh_data(context: bpy.types.Context, sudb: int, obj: bpy.types.Object, obj_to_export, frames_to_bake: list):

    settings = context.scene.OceanBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    dgraph = context.evaluated_depsgraph_get()

    num_verts = ((sudb*sudb)+1) * ((sudb*sudb)+1) # @TODO subd
    float_buffer = [0.0] * len(frames_to_bake) * num_verts * 6

    for frame_index, frame in enumerate(frames_to_bake):
        # set frame and get evaluated ocean object to account for its ocean modifiers (it's an empty mesh otherwise)
        context.scene.frame_set(frame)
        obj_eval = obj.evaluated_get(dgraph)
        obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

        frame_float_offset = frame_index * num_verts * 6

        for y in range(65):
            for x in range(65):
                vertex_index = x + (y * 65)

                i = frame_float_offset + (vertex_index * 6)

                float_buffer[i:i+3] = (obj_eval_mesh.vertices[vertex_index].co - obj_to_export.data.vertices[vertex_index].co) * signed_scale
                float_buffer[i+3:i+6] = obj_eval_mesh.vertices[vertex_index].normal

    return float_buffer

#############
### OCEAN ###
def generate_ocean_mesh(context: bpy.types.Context, bake_name: str):
    """
    Generate the empty mesh that is going to receive the ocean modifiers
    
    :param context: Blender current execution context
    :param bake_name: the bake operation's 'name'
    :return: the function's success, potential error message, generated mesh
    """

    name = bake_name if bake_name != "" else "BakedFFTOcean"
    mesh = bpy.data.meshes.new(name + ".ocean")
    obj = bpy.data.objects.new(name + ".ocean", mesh)
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
    settings = context.scene.OceanBakerSettings

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

    ocean_modifier.time = 0.0
    ocean_modifier.wave_scale = 0.0

    #set_ocean_modifier_time(settings.ocean_time, flip, first_frame, last_frame, ocean_modifier)
    #set_ocean_modifier_wave_scale(settings.ocean_scale, flip, first_frame, last_frame, ocean_modifier)

    return (True, "", ocean_modifier)

def set_ocean_modifier_time(time, flip, first_frame, last_frame, ocean_modifier):
    ocean_modifier.time = 0.0 if flip else time
    ocean_modifier.keyframe_insert(data_path="time", frame=first_frame)
    ocean_modifier.time = time if flip else (time * 2)
    ocean_modifier.keyframe_insert(data_path="time", frame=last_frame + 1) # offset by one frame to avoid duplicating start/end frames

def set_ocean_modifier_wave_scale(wave_scale, flip, first_frame, last_frame, ocean_modifier):
    ocean_modifier.wave_scale = 0.0 if flip else wave_scale
    ocean_modifier.keyframe_insert(data_path="wave_scale", frame=first_frame)
    ocean_modifier.wave_scale = wave_scale if flip else 0.0
    ocean_modifier.keyframe_insert(data_path="wave_scale", frame=last_frame + 1) # offset by one frame to avoid duplicating start/end frames

def modify_ocean_modifiers_interp(obj, ocean_modifier_a, ocean_modifier_b):
    modifier_names = []
    modifiers_param_name = ["time", "wave_scale"]
    modifier_names.append('modifiers["' + ocean_modifier_a.name + '"].')
    modifier_names.append('modifiers["' + ocean_modifier_b.name + '"].')
    # set linear interpolate & vector handles for the keyframes of both modifiers
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
    settings = context.scene.OceanBakerSettings
    
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
        #settings.subd = max(2, active_object_modifier.resolution)
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
        settings.ocean_scale = active_object_modifier.wave_scale

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

    # add modifier A
    success, msg, ocean_modifier_a = add_ocean_modifier(context, obj, first_frame, last_frame, flip=False)
    if not success:
        return (False, msg, 0)

    # add modifier B
    success, msg, ocean_modifier_b = add_ocean_modifier(context, obj, first_frame, last_frame, flip=True)
    if not success:
        return (False, msg, 0)
    
    # output ocean tile extents
    extents = ocean_modifier_b.spatial_size * ocean_modifier_b.size

    return (True, "", extents, ocean_modifier_a, ocean_modifier_b)

###############
### BUFFERS ###
def get_frame_buffers(context: bpy.types.Context, obj: bpy.types.Object, frame: int, frame_size: int, padding: int, extents: float) -> tuple[bool, str, list, list]:
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
    settings = context.scene.OceanBakerSettings

    # set frame and get evaluated ocean object to account for its ocean modifiers (it's an empty mesh otherwise)
    context.scene.frame_set(frame)
    dgraph = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(dgraph)
    obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

    # check num vertices
    expected_num_vertices = (frame_size + 1) * (frame_size + 1)
    if len(obj_eval_mesh.vertices) != expected_num_vertices:
        return (False, "Error in number of vertices: " + str(len(obj_eval_mesh.vertices)) + " vs " + str(expected_num_vertices), None, None)

    # create pixel buffers
    buffer_offset = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size
    buffer_normal = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size

    for y in range(frame_size):
        y_index = frame_size - 1 - y if settings.unit_invert_v else y
        for x in range(frame_size):
            x_index = frame_size - 1 - x if settings.unit_invert_u else x

            vertex_00_index = x_index + 0 + ((y_index + 0) * (frame_size + 1))
            vertex_01_index = x_index + 1 + ((y_index + 0) * (frame_size + 1))
            vertex_10_index = x_index + 0 + ((y_index + 1) * (frame_size + 1))
            vertex_11_index = x_index + 1 + ((y_index + 1) * (frame_size + 1))

            vertex_00 = obj_eval_mesh.vertices[vertex_00_index]
            vertex_01 = obj_eval_mesh.vertices[vertex_01_index]
            vertex_10 = obj_eval_mesh.vertices[vertex_10_index]
            vertex_11 = obj_eval_mesh.vertices[vertex_11_index]

            pos = (vertex_00.co + vertex_01.co + vertex_10.co + vertex_11.co) * 0.25
            pos.x -= (((x_index + 0.5) / (frame_size)) * extents) - (extents * 0.5)
            pos.y -= (((y_index + 0.5) / (frame_size)) * extents) - (extents * 0.5)
            pos *= settings.unit_scale
            if settings.unit_axis_order != "XYZ":
                pos = mathutils.Vector([getattr(pos, axis.lower()) for axis in settings.unit_axis_order])

            # average normal with opposite border to fix seam!
            vertex_00_nor = vertex_00.normal
            vertex_01_nor = vertex_01.normal
            vertex_10_nor = vertex_10.normal
            vertex_11_nor = vertex_11.normal
            if x_index == 0:
                vertex_00_index_wrap = frame_size - 1 + ((y_index + 0) * (frame_size + 1))
                vertex_00_nor = vertex_00_nor.lerp(obj_eval_mesh.vertices[vertex_00_index_wrap].normal, 0.5)
                vertex_00_nor.normalize()

                vertex_10_index_wrap = frame_size - 1 + ((y_index + 1) * (frame_size + 1))
                vertex_10_nor = vertex_10_nor.lerp(obj_eval_mesh.vertices[vertex_10_index_wrap].normal, 0.5)
                vertex_10_nor.normalize()
            elif x_index + 1 == frame_size - 1:
                vertex_01_index_wrap = ((y_index + 0) * (frame_size + 1))
                vertex_01_nor = vertex_01_nor.lerp(obj_eval_mesh.vertices[vertex_01_index_wrap].normal, 0.5)
                vertex_01_nor.normalize()

                vertex_11_index_wrap = ((y_index + 1) * (frame_size + 1))
                vertex_11_nor = vertex_11_nor.lerp(obj_eval_mesh.vertices[vertex_11_index_wrap].normal, 0.5)
                vertex_11_nor.normalize()
            if y_index == 0:
                vertex_00_index_wrap = x_index + 0 + ((frame_size - 1) * (frame_size + 1))
                vertex_00_nor = vertex_00_nor.lerp(obj_eval_mesh.vertices[vertex_00_index_wrap].normal, 0.5)
                vertex_00_nor.normalize()

                vertex_01_index_wrap = x_index + 1 + ((frame_size - 1) * (frame_size + 1))
                vertex_01_nor = vertex_01_nor.lerp(obj_eval_mesh.vertices[vertex_01_index_wrap].normal, 0.5)
                vertex_01_nor.normalize()
            elif y_index + 1 == frame_size - 1:
                vertex_10_index_wrap = x_index + 0
                vertex_10_nor = vertex_10_nor.lerp(obj_eval_mesh.vertices[vertex_10_index_wrap].normal, 0.5)
                vertex_10_nor.normalize()

                vertex_11_index_wrap = x_index + 1
                vertex_11_nor = vertex_11_nor.lerp(obj_eval_mesh.vertices[vertex_11_index_wrap].normal, 0.5)
                vertex_11_nor.normalize()

            nor = (vertex_00_nor + vertex_01_nor + vertex_10_nor + vertex_11_nor)
            nor.normalize()
            if settings.unit_axis_order != "XYZ":
                nor = mathutils.Vector([getattr(nor, axis.lower()) for axis in settings.unit_axis_order])

            i = (x * 4) + (y * 4 * frame_size)
            buffer_offset[i:i + 3] = pos
            buffer_normal[i:i + 3] = nor

    obj_eval.to_mesh_clear()

    # if frame == 1:
    #     debug_offsets = []
    #     debug_normals = []
    #     for i in range(frame_size * frame_size):
    #         base_index = i * 4
    #         r,g,b = buffer_offset[base_index:base_index + 3]  # Take R, G, B only
    #         debug_offsets.append(mathutils.Vector((r,g,b)))
    #         r,g,b = buffer_normal[base_index:base_index + 3]  # Take R, G, B only
    #         debug_normals.append(mathutils.Vector((r,g,b)))

    #     vertices = []
    #     edges = []
    #     for i in range(len(debug_normals)):
    #         nor = debug_normals[i]
    #         pos = debug_offsets[i]

    #         start = pos
    #         end = start + nor * 0.5
    #         idx_start = len(vertices)
    #         idx_end = idx_start + 1

    #         vertices.extend([start, end])
    #         edges.append((idx_start, idx_end))

    #     mesh = bpy.data.meshes.new(name="CustomMesh")
    #     obj = bpy.data.objects.new(name="CustomObject", object_data=mesh)
    #     collection = bpy.context.collection
    #     collection.objects.link(obj)
    #     mesh.from_pydata(vertices, edges, [])
    #     mesh.update()

    return (True, "", buffer_offset, buffer_normal)

def apply_new_frame_padding(buffer:list, frame_size:int, padding:int):
    new_width = frame_size + 2 * padding
    new_height = frame_size + 2 * padding

    pad = True
    if pad:
        # Create the padded buffer
        padded_buffer = []

        for y in range(-padding, frame_size + padding):
            # Handle vertical wrap
            wrapped_y = y % frame_size
            row = []

            for x in range(-padding, frame_size + padding):
                # Handle horizontal wrap
                wrapped_x = x % frame_size
                idx = (wrapped_y * frame_size + wrapped_x) * 4
                pixel = list(buffer[idx:idx+4])
                if x < 0 or x >= frame_size:
                    pixel[1] *= 1
                row.extend(pixel)

            if y < 0 or y >= frame_size:
                for i in range(len(row) // 4):
                    row[(i*4)] *= 1
            padded_buffer.extend(row)

        # Verify new buffer size
        assert len(padded_buffer) == new_width * new_height * 4

        return padded_buffer
    else:
        black_pixel = [0, 0, 0, 1]
        pad_row = black_pixel * new_width
        padded_buffer = []

        for _ in range(padding):
            padded_buffer.extend(pad_row)

        # Add side padding to each original row
        for y in range(frame_size):
            row_start = y * frame_size * 4
            row_end = row_start + frame_size * 4
            row = buffer[row_start:row_end]

            # Add 2 black pixels on left and right
            print(black_pixel * padding)
            print(row)
            padded_row = black_pixel * padding + row + black_pixel * padding
            padded_buffer.extend(padded_row)

        # Add bottom padding rows
        for _ in range(padding):
            padded_buffer.extend(pad_row)

        # Verify new buffer size
        assert len(padded_buffer) == new_width * new_height * 4

        return padded_buffer

def apply_frame_padding(subdivisions: int, padding: int, buffer: list) -> list:
    """
    Fill black padded pixels on one side of the frame, with pixels from the other side of the frame
    
    :param subdivisions: the ocean's modifier subdivisions
    :param padding: amount of padding to add, in pixels, on one side
    :param buffer: pixel buffer to add padding to
    :return: padded pixel buffer
    :rtype: list
    """
    frame_size = (subdivisions * subdivisions)
    frame_size_padded = frame_size + (padding * 2)

    # first X padded pixels, copy the last X pixels in frame, for each row
    # 00000000 > 00000000
    # 00000000 > 00000000
    # 00111100 > AA11AA00
    # 00111100 > AA11AA00
    # 00111100 > AA11AA00
    # 00111100 > AA11AA00
    # 00000000 > 00000000
    # 00000000 > 00000000
    if True:
        for padding_x in range(padding):
            padding_buffer_offset = padding_x * 4
            for pixel in range(frame_size_padded):
                i = padding_buffer_offset + (pixel * frame_size_padded * 4)
                ii = i + (frame_size * 4)
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
    if True:
        for padding_x in range(padding):
            padding_buffer_offset = (padding + frame_size + padding_x) * 4
            for pixel in range(frame_size_padded):
                i = padding_buffer_offset + (pixel * frame_size_padded * 4)
                ii = i - (frame_size * 4)
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
    if True:
        for padding_y in range(padding):
            padding_buffer_offset = (padding_y * frame_size_padded * 4)
            for pixel in range(frame_size_padded):
                i = (pixel * 4) + padding_buffer_offset
                ii = i + (frame_size * frame_size_padded * 4)
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
    if True:
        for padding_y in range(padding):
            padding_buffer_offset = ((padding + frame_size + padding_y) * frame_size_padded * 4)
            for pixel in range(frame_size_padded):
                i = (pixel * 4) + padding_buffer_offset
                ii = i - (frame_size * frame_size_padded * 4)
                buffer[i:i + 3] = buffer[ii:ii + 3]

    return buffer

def get_flipbook_frames(context: bpy.types.Context, num_frames: int) -> tuple[bool, str, int, int]:
    """

    :param context: Blender current execution context
    :param num_frames: number of frames to bake
    :return: the function's success, potential error message, number of frames in X, number of frames in Y, flipbook resolution in X, flipbook resolution in Y
    :rtype: tuple
    """
    settings = context.scene.OceanBakerSettings

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

def get_inverted_buffers(buffer: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """ 
    Re-order buffer so that pixel buffer is flipped in V (aka invert image). Append line of pixels after line in reverse order. Method can likely be pythonified and improved

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

def get_remapped_offset_buffer(buffer_offset: list, buffer_range_offset: mathutils.Vector, buffer_range: mathutils.Vector) -> tuple[list, mathutils.Vector]:
    """
    Remap the offset buffer from the range [-min:max] to [0:1]

    :param buffer_offset: offset buffer
    :param buffer_range_offset: min value to use for remapping
    :param buffer_range: max-min to use for remapping
    :return: remapped buffer
    :rtype: tuple
    """
    pixels = range(len(buffer_offset) // 4)

    for pixel in pixels:
        i = pixel * 4

        offset = mathutils.Vector(buffer_offset[i:i + 3])
        offset -= buffer_range_offset
        offset.x /= buffer_range.x
        offset.y /= buffer_range.y
        offset.z /= buffer_range.z
        buffer_offset[i:i+3] = offset

    return buffer_offset

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

def get_crest_buffer_from_offset_buffer(buffer_offset: list, frame_size: int, extents: float, threshold: float, multiplier: float):
    """
    """

    buffer_crest = [0.0, 0.0, 0.0, 1.0] * frame_size * frame_size

    for y in range(frame_size):
        for x in range(frame_size):
            C_i = x + (y * frame_size)
            C_i *= 4

            B_i = x + (((y - 1) % frame_size) * frame_size)
            B_i *= 4

            R_i = ((x + 1) % frame_size) + (y * frame_size)
            R_i *= 4

            C = buffer_offset[C_i:C_i + 3]
            B = buffer_offset[B_i:B_i + 3]
            R = buffer_offset[R_i:R_i + 3]

            if len(B) == 0:
                print(x)
                print(y)
                print(((y - 1) % frame_size))
                print((((y - 1) % frame_size) * frame_size))
                print(B_i)
                print(len(buffer_offset))

            jxx = 1 + (R[0] - C[0]) / extents
            jyy = 1 + (B[1] - C[1]) / extents
            #jyx = (R[1] - C[1]) / extents
            jxy = (B[0] - C[0]) / extents

            jacob_det = jxx*jyy - jxy*jxy
            jacob_det = -jacob_det * threshold
            eigen_val = ((jxx + jyy) * 0.5) - math.pow((jxx-jyy) * (jxx-jyy) + (4 * jxy * jxy), 0.5) * 0.5
            buffer_crest[C_i] = 1 - eigen_val + threshold
    
    return (True, "", buffer_crest)

############
### MESH ###
def NEW_generate_mesh(context, obj, bake_name, ref_frame: int):
    settings = context.scene.OceanBakerSettings

    dgraph = context.evaluated_depsgraph_get()
    context.scene.frame_set(ref_frame)
    obj_eval = obj.evaluated_get(dgraph)
    obj_eval_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)

    mesh = obj_eval_mesh.copy()
    obj = bpy.data.objects.new(bake_name, mesh)
    bpy.context.collection.objects.link(obj)
    
    obj.select_set(True) # for export

    return (True, "", obj)

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
    settings = context.scene.OceanBakerSettings
    
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
    3. grid UV map
    """
    mesh.uv_layers.new()
    uvmap = mesh.uv_layers[0]
    uvmap.name = "UVMap"
    
    for loop in mesh.loops:
        vertex_index = loop.vertex_index

        vertex_x = vertex_index % verts_per_row
        vertex_y = math.floor(vertex_index / verts_per_row)

        u = vertex_x / (verts_per_row - 1)
        v = vertex_y / (verts_per_row - 1)

        if settings.unit_invert_v:
            v = 1.0 - v

        uvmap.data[loop.index].uv = (u,v)

    """
    4. flipbook UVs
    """    

    mesh.uv_layers.new()
    uvmap = mesh.uv_layers[1]
    uvmap.name = "UVMap.FFT"

    frame_padding_scale = frame_size_ratio
    frame_padding_bias = padding / frame_size

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

        if settings.unit_invert_v:
            v = 1.0 - v

        if settings.tex_mode == "FLIPBOOK":
            u /= num_frames_x
            v /= num_frames_y

            if settings.frame_sort_mode == "TB_LR":
                v += (num_frames_y - 1) / num_frames_y
            elif settings.frame_sort_mode == "TB_RL":
                u += (num_frames_x - 1) / num_frames_x
                v += (num_frames_y - 1) / num_frames_y
            elif settings.frame_sort_mode == "BT_LR":
                pass
            else: # BT_RL
                u += (num_frames_x - 1) / num_frames_x

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

    settings = context.scene.OceanBakerSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None, -1)

    return (True, "", export_path)

################
### TEXTURES ###
def generate_texture(bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate and return a texture containing the provided pixel buffer

    :param bake_name: the bake operation's 'name'
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

    image_name = filename if filename != "" else "T_Bake_FFTOcean"
    tags = { "BakeName": bake_name}
    image_name = replace_tags(image_name, tags)
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
        if texture:
            if texture.packed_file and bpy.data.is_saved:
                texture.unpack()        
            bpy.data.images.remove(texture)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.OceanBakerSettings
    report = context.scene.OceanBakerReport

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
                            unit_invert_u=str(report.unit_invert_u),
                            unit_invert_v=str(report.unit_invert_v),
                            unit_axis_order=report.unit_axis_order)

    # @TODO

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