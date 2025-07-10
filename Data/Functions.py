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
from mathutils.bvhtree import BVHTree
import random
import numpy as np
import xml.etree.ElementTree as ET
import time
import uuid
import bmesh
from ctypes import POINTER, pointer, c_int, c_uint, cast, c_float

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
    settings = context.scene.DataBakerSettings

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
    add_bake_report("packing_precision", settings.packing_precision)

    add_bake_report("origin_obj", settings.origin_obj)

def reset_bake_report():
    """
    Set all report properties to their default values

    :return: None
    :rtype: None
    """
    report = bpy.context.scene.DataBakerReport

    report.data_layers.clear()
    report.data_layers_selected_index = 0

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
    report.packing_precision = 0.0

    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.unit_invert_v = False

    report.xml = False
    report.xml_path = ""

    report.origin_obj = None

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """
    Set a value in the bake report

    :param prop_name: report property to set
    :param prop_value: value to assign to the property
    :return: None
    :rtype: None
    """
    setattr(bpy.context.scene.DataBakerReport, prop_name, prop_value)

def add_bake_layer_report(data_layer, packing, pack_range = None):
    """
    Set values in the bake report to describe a data layer

    :param data_layer: active data layer to assign properties from
    :param packing: list of layers packed in X/Y/Z components
    :param pack_range: min/max range used for remapping values to the range [0:1] during packing
    :return: None
    :rtype: None
    """
    report = bpy.context.scene.DataBakerReport

    report_data_layer = report.data_layers.add()

    if pack_range:
        pack_valid, pack_offset, pack_range = pack_range
        report_data_layer.range_offset = pack_offset
        report_data_layer.range = pack_range
        report_data_layer.range_valid = pack_valid

    high_precision = False
    packed_mode = ""
    for layer_packed_index, layer_packed in enumerate(packing):
        if layer_packed:
            packed_mode = layer_packed.packing_mode
            if layer_packed.packing_mode == "FRACTION" or layer_packed.packing_mode == "XY_BIT" or layer_packed.packing_mode == "XY_NUM" or layer_packed.packing_mode == "XYZ_BIT" or layer_packed.packing_mode == "XYZ_NUM":
                high_precision = True

            if layer_packed == data_layer:
                report_data_layer.active_layer_ID = data_layer.ID
            packed_layer = report_data_layer.packed_layers.add()

            # copy all attributes
            if hasattr(layer_packed, "__annotations__"):
                for prop_name in layer_packed.__annotations__.keys():
                    try:
                        setattr(packed_layer, prop_name, getattr(layer_packed, prop_name))
                    except (AttributeError, TypeError):
                        pass

    report_data_layer.packed_mode = packed_mode
    report_data_layer.range_high_precision = packed_mode == "FRACTION" or packed_mode == "XY_BIT" or packed_mode == "XY_NUM" or packed_mode == "XYZ_BIT" or packed_mode == "XYZ_NUM" or (data_layer.data == "QUATERNION" and data_layer.quat == "XYZW")

def clear_bake_layer_report(data_layer) -> bool:
    """
    """
    report = bpy.context.scene.DataBakerReport

    # for each layer
    report_data_layers = report.data_layers
    for report_data_layer_index, report_data_layer in enumerate(report_data_layers):
        # for each other layer packed in this layer, including self
        for packed_data_layer in report_data_layer.packed_layers:
            if packed_data_layer.ID == data_layer.ID:
                report_data_layers.remove(report_data_layer_index)
                return True

    return False

def edit_bake_layer_report_range_offset(data_layer, prop_value: mathutils.Vector = mathutils.Vector((0.0, 0.0, 0.0))) -> bool:
    return edit_bake_layer_report_range_prop(data_layer, prop_value, "range_offset")

def edit_bake_layer_report_range(data_layer, prop_value: mathutils.Vector = mathutils.Vector((0.0, 0.0, 0.0))) -> bool:
    return edit_bake_layer_report_range_prop(data_layer, prop_value, "range")

def edit_bake_layer_report_range_valid(data_layer, prop_value: bool) -> bool:
    return edit_bake_layer_report_range_prop(data_layer, prop_value, "range_valid")

def edit_bake_layer_report_range_prop(data_layer, value, prop_name: str = "range_offset") -> bool:
    """ """
    report = bpy.context.scene.DataBakerReport
    # for each layer
    report_data_layers = report.data_layers
    for report_data_layer in report_data_layers:
        # for each other layer packed in this layer, including self
        for packed_data_layer in report_data_layer.packed_layers:
            # in packed layers, find layer we want to edit
            if packed_data_layer.ID == data_layer.ID:
                setattr(report_data_layer, prop_name, value)
                return True

    return False

def get_bake_layer_report_range_offset(data_layer) -> float:
    return get_bake_layer_report_range_prop(data_layer, "range_offset")

def get_bake_layer_report_range(data_layer) -> float:
    return get_bake_layer_report_range_prop(data_layer, "range")

def get_bake_layer_report_range_valid(data_layer) -> bool:
    return get_bake_layer_report_range_prop(data_layer, "range_valid")

def get_bake_layer_report_range_prop(data_layer, prop: str = "range_offset") -> float:
    report = bpy.context.scene.DataBakerReport
    # for each layer
    report_data_layers = report.data_layers
    for report_data_layer in report_data_layers:
        # for each other layer packed in this layer, including self
        for packed_data_layer_index, packed_data_layer in enumerate(report_data_layer.packed_layers):
            # in packed layers, find layer we want to get range from 
            if packed_data_layer.ID == data_layer.ID:
                # get min or max vector
                prop_value = report_data_layer.get(prop, None)
                if prop_value:
                    if isinstance(prop_value, bool) or isinstance(prop_value, int):
                        return True if prop_value == 1 else False
                    else:
                        return prop_value[packed_data_layer_index]

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

def get_packed_frac(x: float, y: float, y_offset: float, y_range: float) -> float:
    """
    Algorithm to pack two floats into one, using its integer and fractional part.

    The value to store in the integer part is floored.

    The value to store in the fractional part has to be normalized and remapped to the range [0:<1],
    because 1.0 can't be encoded in the fractional part, as it would read as .0.
    Remapping is arbitrarily performed based on some kind of precision parameter, as to ensure values
    in the upper range don't get rounded up to 1.0.

    This is lossy and precision loss is greater the bigger the integer number.

    :param x: first float to pack
    :param y: second float to pack
    :param y_offset: 
    :param y_range: 
    :return: frac-packed float
    :rtype: float
    """
    y = (y - y_offset) / y_range # remap frac from [min:max] to [0:<1]
    return  math.floor(x) + y

def get_pack_2(x: float, x_offset: float, x_range: float, y: float, y_offset: float, y_range: float) -> float:
    """ 
    Algorithm to pack two floats into one, using numeric packing

    Range is assumed to be non-zero!

    :param x: first float to pack
    :param x_offset: 
    :param x_range: 
    :param y: second float to pack
    :param y_offset: 
    :param y_range: 
    :return: numerically packed float
    :rtype: float
    """
    margin = 1.0 / 256.0
    scale = 1.0 / (1.0 - 2.0 * margin)
    adjusted_x_range = x_range * scale
    adjusted_x_offset = x_offset - x_range * (scale - 1.0) / 2.0

    a = min(1.0, max(0.0, (x - adjusted_x_offset) / adjusted_x_range))
    
    adjusted_y_range = y_range * scale
    adjusted_y_offset = y_offset - y_range * (scale - 1.0) / 2.0

    b = min(1.0, max(0.0, (y - adjusted_y_offset) / adjusted_y_range))
   
    aq = int(a * 65535.0 + 0.5)
    bq = int(b * 65535.0 + 0.5)

    return aq / 65536.0 + bq / (65536.0 * 65536.0)

def get_pack_3(x: float, x_offset: float, x_range: float, y: float, y_offset: float, y_range: float, z: float, z_offset: float, z_range: float) -> float:
    """ 
    Algorithm to pack three floats into one, using numeric packing

    Range is assumed to be non-zero!

    :param x: first float to pack
    :param x_offset: 
    :param x_range: 
    :param y: second float to pack
    :param y_offset: 
    :param y_range: 
    :param z: third float to pack
    :param z_offset: 
    :param z_range: 
    :return: numerically float
    :rtype: float
    """
    a = min(1.0, max(0.0, (x - x_offset) / x_range))
    b = min(1.0, max(0.0, (y - y_offset) / y_range))
    c = min(1.0, max(0.0, (z - z_offset) / z_range))

    aq = int(a * 250.0 + 0.5)
    bq = int(b * 255.0 + 0.5)
    cq = int(c * 255.0 + 0.5)

    return aq / 256.0 + bq / (256.0 * 256.0) + cq / (256.0 * 256.0 * 256.0)

def get_normalized(x: float, x_min: float, x_max: float, threshold: float = 0.0001) -> float:
    """
    Remap a float to the range [0:1].

    If (x_max - x_min) is too close to the 'default_threshold', the function just returns the input value as-is

    :param x: float to remap
    :param x_min: float used to remap the given float to the range [0:1]
    :param x_max: float used to remap the given float to the range [0:1]
    :param threshold: how close x_max - x_min has to be for the function to return the value as-is instead of remapped
    """
    if abs(x_max - x_min) > threshold:
        return (x - x_min) / (x_max - x_min)
    else:
        return x

def get_normalized_remap(x: float, x_min: float, x_max: float, threshold: float = 0.0001) -> float:
    """
    Remap a float to the range [-1:1].

    If (x_max - x_min) is too close to the 'default_threshold', the function just returns the input value as-is

    :param x: float to remap
    :param x_min: float used to remap the given float to the range [0:1]
    :param x_max: float used to remap the given float to the range [0:1]
    :param threshold: how close x_max - x_min has to be for the function to return the value as-is instead of remapped
    """
    if abs(x_max - x_min) > threshold:
        remap = (x - x_min) / (x_max - x_min)
        return (remap - 0.5) * 2.0
    else:
        return x

def octahedron_normal_octwrap(v):
#     """ https://knarkowicz.wordpress.com/2014/04/16/octahedron-normal-vector-encoding/ """

#     return (1.0 - abs(v.yx)) * (1.0 if v.xy >= 0.0 else -1.0)
    pass

def octahedron_normal_encode(n):
#     """ https://knarkowicz.wordpress.com/2014/04/16/octahedron-normal-vector-encoding/ """

#     n /= (abs(n.x) + abs(n.y) + abs(n.z))
#     n.xy = n.xy if n.z >= 0.0 else octahedron_normal_octwrap(n.xy)
#     n.xy = (n.xy * 0.5) + mathutils.Vector((0.5, 0.5))
#     return n.xy
    pass

def octahedron_normal_decode(f):
#     """ https://knarkowicz.wordpress.com/2014/04/16/octahedron-normal-vector-encoding/ """
#     f = f * 2.0 - mathutils.Vector((1.0, 1.0))
 
#     # https://twitter.com/Stubbesaurus/status/937994790553227264
#     n = mathutils.Vector((f.x, f.y, 1.0 - abs(f.x) - abs(f.y)))
#     t = min(1.0, max(0.0, -n.z))
#     tv = mathutils.Vector((t,t))
#     n.xy += -tv if n.xy >= 0.0 else tv
#     return n.normalized()
    pass

def encode_stereo_proj(normal):
    """ """
    # https://aras-p.info/texts/CompactNormalStorage.html

    scale = 1.7777
    enc = normal.xy / (normal.z + 1)
    enc /= scale
    enc = (enc * 0.5) + 0.5
    return enc

def decode_stereo_proj(enc):
    """ """
    # https://aras-p.info/texts/CompactNormalStorage.html
    
    scale = 1.7777
    nnormal = mathutils.Vector((enc.x, enc.y, 0.0)) * mathutils.Vector((2*scale,2*scale,0)) + mathutils.Vector((-scale,-scale,1))
    g = 2.0 / nnormal.xyz.dot(nnormal.xyz)

    normal = mathutils.Vector((0.0, 0.0, 1.0))
    normal.xy = g * nnormal.xy
    normal.z = g - 1.0
    return normal

def get_packed_xyz_vector_legacy(unit_vector: mathutils.Vector) -> float:
    """ 
    Legacy algorithm used to pack three normalized floats into one. Results in *severe* precision loss and probably isn't practical to encode data like positions

    :param unit_vector: XYZ vector to pack
    :return: bitpacked float
    :rtype: float
    """

    return (math.ceil(unit_vector.x * 100) * 10) + (math.ceil(unit_vector.y * 100) * 0.1) + (math.ceil(unit_vector.z * 100) * 0.001)

def get_packed_ab_vector_legacy(unit_vector: mathutils.Vector, a_component: float, b_component: float) -> float:
    """ 
    Legacy algorithm used to pack two normalized floats into one. Gives acceptable precision loss unless numbers are large-ish

    :param unit_vector: XYZ vector to pack
    :param a_component: which XYZ component to pack in the 'a' component
    :param b_component: which XYZ component to pack in the 'b' component
    :return: bitpacked float
    :rtype: float
    """
    a = unit_vector.x if a_component == "X" else unit_vector.y if a_component == "Y" else unit_vector.z
    a = math.floor(a * (4096 - 1)) * 4096    

    b = unit_vector.x if b_component == "X" else unit_vector.y if b_component == "Y" else unit_vector.z
    b = math.floor(b * (4096 - 1))

    return (a + b)

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
def get_bake_data_layers_info(context: bpy.types.Context) -> tuple[bool, str, list]:
    """
    Compute and return the bake info per data layer.
    
    - if that data layer is to be baked (otherwise included in another layer so it can be skipped)
    - the packing mode if layers has to be packed
    - data layers packed in the X/Y/Z packing components, if any, in the format (layer_a, layer_b, layer_c). It at least contains the data layer itself (in the first available component)

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of data_layer<>data_layer_info pairings
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    ids = []
    layers_info = []
    for data_layer in settings.data_layers:
        if data_layer.ID == "":
            return (False, "Empty ID", None)
        elif data_layer.ID in ids:
            return (False, "Duplicated IDs", None)
        else:
            ids.append(data_layer.ID)

            success, msg, layer_info = get_data_layer_info(data_layer, settings.data_layers)
            if not success:
                return (False, msg, None)

            layers_info.append((data_layer, layer_info))

    return (True, "", layers_info)

def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object]:
    """
    Modify & ensure the active & selected objects can lead to a valid bake and return the list of objects to include in the bake, as well as the active object.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of objects to bake (filtered selection), active object
    :rtype: tuple
    """

    settings = context.scene.DataBakerSettings

    if context.view_layer.objects.active == None:
        return (False, "No active object", None, None)

    for selected_obj in context.selected_objects:
        if selected_obj.type != "MESH" or len(selected_obj.data.vertices) <= 0: # mesh could have no vertices
            selected_obj.select_set(False)

    objs_to_bake = context.selected_objects # cache selection
    if objs_to_bake and len(objs_to_bake) <= 0:
        return (False, "No mesh to bake once filtered out", None, None)

    active_obj = context.view_layer.objects.active

    if settings.unit_invert_v:
        add_bake_report("unit_invert_v", True)

    # blank canvas
    for obj in objs_to_bake:
        obj.select_set(False)

    context.view_layer.objects.active = None

    return (True, "", objs_to_bake, active_obj)

def get_bake_name(context: bpy.types.Context, active_object: bpy.types.Object) -> str:
    """
    Return the name to give to the bake operation.

    :param context: Blender current execution context
    :param active_object: object to derive name from
    :return: the bake operation's 'name'
    :rtype: str
    """

    settings = context.scene.DataBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.Data"
    tags = { "BakeName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def pre_process_bake_selection(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, list]:
    """
    Generate and return a copy of all depsgraph-evaluated meshes to be included in the bake

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to generate duplicates from
    :return: the function's success, potential error message, list of duplicated, evaluated mesh objects to include in the bake
    :rtype: tuple
    """

    settings = context.scene.DataBakerSettings

    """
    scan layers for a shapekey layer! If so we probably want to ensure it is set to 0.0 and assume the baked object
    will have the rest pose so that the baked shapekey does indeed always contain the proper shapekey offset/normal
    """
    shapekey_values_to_restore = []
    for obj_to_bake in objs_to_bake:
        if obj_to_bake.type == "MESH":
            for data_layer in settings.data_layers:
                if data_layer.data == "SHAPEKEY" and data_layer.obj_mode == "SELF" or (data_layer.obj_mode == "CUSTOM" and data_layer.obj == obj_to_bake):
                    if obj_to_bake.data.shape_keys and (data_layer.name in obj_to_bake.data.shape_keys.key_blocks):
                        shapekey = obj_to_bake.data.shape_keys.key_blocks[data_layer.name]
                        shapekey_values_to_restore.append((shapekey, shapekey.value))
                        shapekey.value = 0.0
                        break # move onto next object

    dgraph = bpy.context.evaluated_depsgraph_get() # refresh shapekeys

    if not settings.mesh_duplicate:
        # naming isn't the best... objs are not evaluated here.
        eval_objs_to_bake = objs_to_bake

        if settings.mesh_single_user:
            for eval_obj_to_bake in eval_objs_to_bake:
                mesh_copy = eval_obj_to_bake.data.copy()
                eval_obj_to_bake.data = mesh_copy
    else:
        """
        duplicate depsgraph-evaluated filtered selection & forward initial animation
        """
        source_objs_to_eval = {}
        eval_objs_to_bake = []
        for obj_to_bake in objs_to_bake:
            col = context.scene.collection
            if obj_to_bake.users_collection and len(obj_to_bake.users_collection) > 0:
                col = obj_to_bake.users_collection[0]

            eval_obj = obj_to_bake.evaluated_get(dgraph)
            eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            #eval_mesh.transform(eval_obj.matrix_world) # not needed if matrix_world is forwarded

            eval_obj_to_bake = bpy.data.objects.new(obj_to_bake.name + ".baked", eval_mesh.copy())
            eval_obj_to_bake.matrix_world = eval_obj.matrix_world # forward initial animation

            for key in obj_to_bake.keys():
                if key != "_RNA_UI":
                    eval_obj_to_bake[key] = obj_to_bake[key]

            eval_obj.to_mesh_clear()

            col.objects.link(eval_obj_to_bake)
            eval_objs_to_bake.append(eval_obj_to_bake)

            """
            create pairing with original obj. Ideally, we'd use the evaluated objects as-is, and get the original via their
            built-in .original pointer, but I do prefer to work on actual meshes so I can tweak mesh attributes etc without
            risking modifying the original in a destructive manner
            """
            eval_obj_to_bake["BakedSource"] = obj_to_bake
            eval_obj_to_bake.id_properties_ensure()
            property_manager = eval_obj_to_bake.id_properties_ui("BakedSource")
            property_manager.update(id_type="OBJECT") # dirty hack to prevent weird UI bug

            source_objs_to_eval[obj_to_bake] = eval_obj_to_bake

        """
        iterate depsgraph-evaluated objects to find to which other depsgraph-evaluated objects they need to be parented to.
        this involves getting the unevaluated source object and walking up the hierarchy until we find the first valid parent,
        meaning one that is included in the filtered objs_to_bake list. 
        """
        for eval_obj_to_bake in eval_objs_to_bake:
            obj_parent = eval_obj_to_bake["BakedSource"].parent
            while obj_parent and obj_parent not in objs_to_bake:
                obj_parent = obj_parent.parent

            if obj_parent:
                eval_obj_parent = source_objs_to_eval[obj_parent]
                eval_obj_to_bake.parent = eval_obj_parent
                eval_obj_to_bake.matrix_parent_inverse = eval_obj_parent.matrix_world.inverted()

    """
    restore modified shapekey values, if needed
    """
    if shapekey_values_to_restore:
        for shapekey, shapekey_value in shapekey_values_to_restore:
            shapekey.value = shapekey_value

    return (True, "", eval_objs_to_bake)

def post_process_bake_selection(context: bpy.types.Context, eval_objs_to_bake: list) -> tuple[bool, str]:
    """
    Merge duplicated meshes that were part of the bake and clean duplicated meshes, if any

    :param context: Blender current execution context
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: the function's success and potential error message
    :rtype: tuple
    """

    settings = context.scene.DataBakerSettings

    dgraph = bpy.context.evaluated_depsgraph_get()

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.Data"
    """
    process of merging involves copying data blocks in a single bmesh
    """
    if settings.mesh_merge:
        # get materials to copy (face material indices might have to be modified because of merging process)
        success, msg, materials = generate_mesh_material_indices(eval_objs_to_bake)
        if not success:
            return (False, msg)
        
        # create a new mesh to 'merge' all duplicated meshes
        merged_mesh = bpy.data.meshes.new(name)

        if settings.mesh_materials and materials:
            # copy materials
            for material in materials:
                merged_mesh.materials.append(material)

        bm = bmesh.new()
        for eval_obj_to_bake in eval_objs_to_bake:
            mesh = eval_obj_to_bake.data # they already are evaluated, just need to transformed
            mesh.transform(eval_obj_to_bake.matrix_world)

            bm.from_mesh(eval_obj_to_bake.data)
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        bm.to_mesh(merged_mesh)
        bm.free()

        # create a new object from the new mesh
        obj = bpy.data.objects.new(name, merged_mesh)
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
            merged_mesh.transform(settings.origin_obj.matrix_world.inverted())

        if settings.clear_attributes and merged_mesh.attributes:
            attr_names = [data_layer.ID for data_layer in settings.data_layers]
            for attr_name in attr_names:
                attr = merged_mesh.attributes.get(attr_name, None)
                if attr:
                    merged_mesh.attributes.remove(attr)

        add_bake_report("mesh", obj)

        obj.select_set(True)
        context.view_layer.objects.active = obj

        clear_bake_selection(eval_objs_to_bake)
    elif settings.mesh_duplicate:
        # meshes were already duplicated, simply carry materials
        for eval_obj_to_bake in eval_objs_to_bake:
            if "BakedSource" in eval_obj_to_bake:
                source_obj = eval_obj_to_bake["BakedSource"]
                for material in source_obj.data.materials:
                    eval_obj_to_bake.data.materials.append(material)

        # select duplicated objects (for export)
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_obj_to_bake.select_set(True)

        # pick object to make active and to report. Selection is totally arbitrary, I don't like that
        # pick root object instead? But what if multiple roots?
        obj_to_highlight = eval_objs_to_bake[0]
        context.view_layer.objects.active = obj_to_highlight
        add_bake_report("mesh", obj_to_highlight)
    else:
        # select objects (for export)
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_obj_to_bake.select_set(True)
            context.view_layer.objects.active = eval_obj_to_bake

    return (True, "")

def clear_bake_selection(eval_objs_to_bake: list) -> bool:
    """
    Clear the Blender file of duplicated objects

    :param eval_objs_to_bake: Objects to remove
    :return: success
    :rtype: bool
    """
    for eval_obj_to_bake in eval_objs_to_bake:
        bpy.data.objects.remove(eval_obj_to_bake)

    return True

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    #bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

    settings = context.scene.DataBakerSettings
    new_bake_report(context)

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #

    bake_start_time = time.time()

    success, msg, layers_info = get_bake_data_layers_info(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(1)

    success, msg, objs_to_bake, active_object = get_bake_selection(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(3)

    success, msg, eval_objs_to_bake = pre_process_bake_selection(context, objs_to_bake)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(7)

    bake_name = get_bake_name(context, active_object)
    add_bake_report("name", bake_name)

    wm.progress_update(10)

    ########
    # BAKE #

    success, msg = bake_data_layers(context, layers_info, eval_objs_to_bake)
    if not success:
        if settings.mesh_duplicate:
            clear_bake_selection(eval_objs_to_bake)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    ########
    # MESH #

    success, msg = post_process_bake_selection(context, eval_objs_to_bake)
    if not success:
        if settings.mesh_duplicate:
            clear_bake_selection(eval_objs_to_bake)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(93)

    if settings.export_mesh and bpy.data.is_saved:
        success, msg, mesh_path = export_mesh_selection(context, bake_name)
        if not success:
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("mesh_export", True)
        add_bake_report("mesh_path", mesh_path)

    wm.progress_update(97)

    #######
    # XML #

    if settings.export_xml and bpy.data.is_saved:
        success, msg, path = export_xml(context)
        add_bake_report("xml", True)
        add_bake_report("xml_path", path)

    add_bake_report("success", True)
    wm.progress_update(99)
    wm.progress_end()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

##################
### DATA LAYER ###
def get_data_layer_info(data_layer: object, data_layers: list) -> tuple[bool, str, tuple[bool, str, tuple[object, object, object]]]:
    """
    Perform a large number of checks on the given data layer to return if it is safe to bake, as well as packing information
    
    Potential failures:
    - layer might be asking to be packed into another layer that is itself also asking to be packed into another layer
    - layer might be asking to be packed into another layer that is itself stored in a way that doesn't allow bitpacking
    - layer might be asking to be packed into another layer but fails to provide a valid target
    - layer might be asked to pack too many data layers
    - layer might be asked to pack data layers in the same X/Y/Z packing component
    - layer might be asked to pack data layers while stored in a way that doesn't allow bitpacking
    - layer might be asking to be stored in a UV channel/index that is already targeted by another layer
    - layer might be asking to be stored in a Vertex Color channel that is already targeted by another layer
    - layer might be asking to be stored in a Normal component that is already targeted by another layer
    - ...

    :param data_layer: the data layer to get info for
    :param data_layers: list of data layers to scan
    :return: the data layer's validity, potential error message, if the layer itself has to be packed (included in another layer otherwise), the packing mode, and the list of data layers to pack in each X/Y/Z packing component
    :rtype: tuple
    """
    if not data_layer:
        err_msg = "Invalid data layer"
        return (False, err_msg, None)

    err_base_msg = "Packing error with " + get_data_layer_name(data_layer) + ": "

    if not data_layers or len(data_layers) == 0:
        err_msg = err_base_msg + "data layers list is empty"
        return (False, err_msg, None)

    #################################################
    # DATA LAYER MIGHT BE PACKED INTO ANOTHER LAYER #
    targeting = data_layer.packing_mode == "FRACTION" or data_layer.packing_mode == "XY_BIT" or data_layer.packing_mode == "XY_NUM" or data_layer.packing_mode == "XYZ_BIT" or data_layer.packing_mode == "XYZ_NUM"
    if targeting:
        success, msg, data_layer_target = get_data_layer_targeting_info(data_layer, data_layers)
        if not success:
            return (False, err_base_msg + msg, None)

        try:
            for other_data_layer_index, other_data_layer in enumerate(data_layers):
                if other_data_layer == data_layer_target:
                    target_index = other_data_layer_index
                    break
        except:
            return (False, err_base_msg + "error searching target layer's index", None)

        # gather sibling(s) (aka, all layers that have the same target than us, including us)
        layers_sharing_target = [layer for layer in data_layers if layer.ptr == target_index and (layer.packing_mode == "XY_BIT" or layer.packing_mode == "XY_NUM" or layer.packing_mode == "XYZ_BIT" or layer.packing_mode == "XYZ_NUM" or layer.packing_mode == "FRACTION")]
        if layers_sharing_target:
            # check sibling(s) and build packing info
            success, msg, packing_mode, packing_info = get_data_layer_packing_info(data_layer_target, layers_sharing_target)
            if not success:
                return (False, err_base_msg + msg, None)

            return (True, "", (False, packing_mode, packing_info))
        else: # no sibling(s), not even ourself! critical fail (shouldn't happen but check still)
            return (False, err_base_msg + "error searching for siblings", None)
    ############################################
    # DATA LAYER MIGHT BE PACKING OTHER LAYERS #
    else:
        success, msg = get_data_layer_non_targeting_info(data_layer, data_layers)
        if not success:
            return (False, err_base_msg + msg, None)

        try:
            for other_data_layer_index, other_data_layer in enumerate(data_layers):
                if other_data_layer == data_layer:
                    self_index = other_data_layer_index
                    break
        except:
            return (False, err_base_msg + "error searching layer's index", None)

        # gather child(s) (aka, all layers that *may* target us)
        layers_targeting_self = [layer for layer in data_layers if layer.ptr == self_index and (layer.packing_mode == "XY_BIT" or layer.packing_mode == "XY_NUM" or layer.packing_mode == "XYZ_BIT" or layer.packing_mode == "XYZ_NUM" or layer.packing_mode == "FRACTION")]
        if layers_targeting_self:
            # check childs(s) and build packing info
            success, msg, packing_mode, packing_info = get_data_layer_packing_info(data_layer, layers_targeting_self)
            if not success:
                return (False, err_base_msg + msg, None)

            return (True, "",  (True, packing_mode, packing_info))
        else: # data_layer is on its own, all good!
            return (True, "", (True, data_layer.packing_mode, [data_layer, None, None]))

def get_data_layer_targeting_info(data_layer: object, data_layers: list) -> tuple[bool, str, object]:
    """
    Perform a number of checks on the given data layer to return if it successfully targets another data layer without conflict, and the targeted data layer

    :param data_layer: the data layer to get info for
    :param data_layers: list of data layers to scan
    :return: True if the data layer is targeting another data layer in a non-conflicting way, potential error message, targeted daya layer
    :rtype: tuple
    """
    try:
        for other_data_layer_index, other_data_layer in enumerate(data_layers):
            if other_data_layer == data_layer:
                self_index = other_data_layer_index
                break
    except:
        return (False, "error searching for self in layers list", None)

    # check that we're not asking to be packed into another layer while other layers are asking us to pack them
    layers_targeting_self = [layer for layer in data_layers if layer.ptr == self_index]
    if len(layers_targeting_self) > 0:
        return (False, "layer is itself targeted by other layers", None)

    # check ptr ID isn't empty
    if data_layer.ptr < 0:
        return (False, "no target specified", None)
    # make sure ptr ID isn't self ID
    if data_layer.ptr == self_index:
        return (False, "targeting itself", None)

    # gather target(s)
    try:
        data_layer_target = data_layers[data_layer.ptr]
    except:
        return (False, "couldn't find data layer target in layers list", None)

    if data_layer_target:
        # make sure we haven't found self
        if data_layer == data_layer_target:
            return (False, "targeting itself (Layer)", None)
        # make sure target's storage mode allow bit-packing
        mode = data_layer_target.packing_mode
        if mode == "FRACTION" or mode == "XY_BIT" or mode == "XY_NUM" or mode == "XYZ_BIT" or mode == "XYZ_NUM" or mode == "VCOL" or mode == "NORMAL":
            return (False, "is targeted by " + get_data_layer_name(data_layer) + " but don't allow bit-packing", None)
        elif data_layer_target.data == "QUATERNION" and data_layer_target.quat == "XYZW":
            return (False, "is targeted by " + get_data_layer_name(data_layer) + " but don't allow bit-packing", None)

        return (True, "", data_layer_target)
    else:
        return (False, "target specified couldn't be found", None)

def get_data_layer_non_targeting_info(data_layer: object, data_layers: list) -> tuple[bool, str]:
    """
    Perform a number of checks on the given data layer to return if it can be successfully stored either in UVs, Vertex Color or Normal, assuming it is not targeted by any other layer

    :param data_layer: the data layer to get info for
    :param data_layers: list of data layers to scan
    :return: True if the data layer can be successfully stored and the potential error message
    :rtype: tuple
    """
    # check if targeted UV channel/index is free
    if data_layer.packing_mode == "UV":
        if data_layer.uv_index > 7:
            return (False, "can't have " + str(data_layer.uv_index + 1) + " UVMaps")

        uv_components = []
        for data_layer in data_layers:
            layer_index = data_layer.uv_index * 2 + (0 if data_layer.uv_channel == "U" else 1)
            if data_layer.packing_mode == "UV":
                if (layer_index in uv_components):
                    return (False, "UVMap " + str(data_layer.uv_index) + " channel " + data_layer.uv_channel + " is already targeted")
                else:
                    uv_components.append(layer_index)
    # check if targeted VCOL RGBA channel is free                    
    elif data_layer.packing_mode == "VCOL":
        if data_layer.data == "QUATERNION" and data_layer.quat == "XYZW":
            return (False, "Bit-packed quaternion must be stored in 32-bit UVs")

        vcol_components = []
        for data_layer in data_layers:
            if data_layer.packing_mode == "VCOL":
                if (data_layer.vcol_rgba in vcol_components):
                    return (False, data_layer.vcol_rgba + " already targeted")
                else:
                    vcol_components.append(data_layer.vcol_rgba)
    # check if targeted NORMAL XYZ component is free
    elif data_layer.packing_mode == "NORMAL":
        if data_layer.data == "QUATERNION" and data_layer.quat == "XYZW":
            return (False, "Bit-packed quaternion must be stored in 32-bit UVs")

        normal_components = []
        for data_layer in data_layers:
            if data_layer.packing_mode == "NORMAL":
                if (data_layer.normal_xyz in normal_components):
                    return (False, "Normal " + str(data_layer.normal_xyz) + " is already targeted")
                else:
                    normal_components.append(data_layer.normal_xyz)

    return (True, "")

def get_data_layer_packing_info(data_layer_target, data_layers_to_pack: list) -> tuple[bool, str, str, tuple[object, object, object]]:
    """
    Ensure the data layer can pack all data layers targeting it without conflict

    :param data_layer_target: the data layer being targeted by at least another layer
    :param data_layers_to_pack: the list of layers targeting the provided data layer
    :return: True if the data layer can pack the given layers, potential error message, the packing mode and the sorted list of layers to pack in the X/Y/Z packing components
    :rtype: tuple
    """
    layers_packed_in_x = []
    layers_packed_in_y = []
    layers_packed_in_z = []

    packing_mode = ""
    for data_layer_to_pack in data_layers_to_pack:
        if packing_mode == "":
                packing_mode = data_layer_to_pack.packing_mode
        elif packing_mode != data_layer_to_pack.packing_mode:
            return (False, "divergent packing mode", "", None)

        if packing_mode == "FRACTION" or ((packing_mode == "XY_BIT" or packing_mode == "XY_NUM") and data_layer_to_pack.pack_xy == "X") or ((packing_mode == "XYZ_BIT" or packing_mode == "XYZ_NUM") and data_layer_to_pack.pack_xyz == "X"):
            if len(layers_packed_in_y) > 0:
                return (False, "multiple layers targeting component X", "", None)
            else:
                layers_packed_in_y.append(data_layer_to_pack)
        elif ((packing_mode == "XY_BIT" or packing_mode == "XY_NUM") and data_layer_to_pack.pack_xy == "Y") or ((packing_mode == "XYZ_BIT" or packing_mode == "XYZ_NUM") and data_layer_to_pack.pack_xyz == "Y"):
            if len(layers_packed_in_y) > 0:
                return (False, "multiple layers targeting component Y", "", None)
            else:
                layers_packed_in_y.append(data_layer_to_pack)
        elif ((packing_mode == "XYZ_BIT" or packing_mode == "XYZ_NUM") and data_layer_to_pack.pack_xyz == "Z"):
            if len(layers_packed_in_z) > 0:
                return (False, "multiple layers targeting component Z", "", None)
            else:
                layers_packed_in_z.append(data_layer_to_pack)
        else:
            pass

    if packing_mode == "":
        packing_mode = data_layer_target.packing_mode

    # make sure to include targeted data_layer itself
    if len(layers_packed_in_x) == 0:
        layers_packed_in_x.append(data_layer_target)
    elif len(layers_packed_in_y) == 0:
        layers_packed_in_y.append(data_layer_target)
    elif len(layers_packed_in_z) == 0:
        layers_packed_in_z.append(data_layer_target)
    else:
        return (False, "layer is asked to pack too many layers and can't contain itself anymore", "", None)

    # fill empty list(s) with None
    if len(layers_packed_in_x) == 0:
        layers_packed_in_x.append(None)
    if len(layers_packed_in_y) == 0:
        layers_packed_in_y.append(None)
    if len(layers_packed_in_z) == 0:
        layers_packed_in_z.append(None)

    return (True, "", packing_mode, (layers_packed_in_x[0], layers_packed_in_y[0], layers_packed_in_z[0]))

def get_data_layer_name(data_layer: object) -> str:
    """
    Compute a friendly name for a data layer based on its various settings

    :param data_layer: data layer to generate a friendly name for
    :return: data layer's friendly name
    :rtype: str
    """
    if data_layer:
        if data_layer.data == "POSITION":
            if data_layer.obj_mode == "PARENT":
                prefix = "Parent "
            elif data_layer.obj_mode == "CUSTOM":
                prefix = "Custom "
            elif data_layer.obj_mode == "PROPERTY":
                prefix = "Prop "
            else:
                prefix = ""
            return prefix + "Position (" + data_layer.component + ")"
        elif data_layer.data == "QUATERNION":
            if data_layer.obj_mode == "PARENT":
                prefix = "Parent "
            elif data_layer.obj_mode == "CUSTOM":
                prefix = "Custom "
            elif data_layer.obj_mode == "PROPERTY":
                prefix = "Prop "
            else:
                prefix = ""
            return prefix + "Quaternion (" + data_layer.quat + ")"
        elif data_layer.data == "AXIS":
            if data_layer.obj_mode == "PARENT":
                prefix = "Parent "
            elif data_layer.obj_mode == "CUSTOM":
                prefix = "Custom "
            elif data_layer.obj_mode == "PROPERTY":
                prefix = "Prop "
            else:
                prefix = ""
            return prefix + "Axis " + data_layer.axis + " (" + data_layer.component + ")"
        elif data_layer.data == "SHAPEKEY":
            if data_layer.obj_mode == "PARENT":
                prefix = "Parent "
            elif data_layer.obj_mode == "CUSTOM":
                prefix = "Custom "
            elif data_layer.obj_mode == "PROPERTY":
                prefix = "Prop "
            else:
                prefix = ""

            if data_layer.vertex_mode == "OFFSET":
                return prefix + "Shapekey Offset (" + data_layer.component + ")"
            elif data_layer.vertex_mode == "NORMAL":
                return prefix + "Shapekey Normal (" + data_layer.component + ")"
            else:
                pass
        elif data_layer.data == "MASK":
            if data_layer.mask_mode == "SPHERE":
                return "Mask Sphere" + " (" + data_layer.origin_mode + ")"
            elif data_layer.mask_mode == "LINEAR":
                return "Mask Linear " + data_layer.axis + " (" + data_layer.origin_mode + ")"
            else:
                pass
        elif data_layer.data == "RANDOM":
            prefix = "Parent Axis " if data_layer.obj_mode == "PARENT" else "Axis "
            if data_layer.rand_mode == "COLLECTION":
                return "Random Per Col" + " (" + data_layer.component + ")"
            elif data_layer.rand_mode == "OBJECT":
                return "Random Per Obj" + " (" + data_layer.component + ")"
            elif data_layer.rand_mode == "FACE":
                return "Random Per Face" + " (" + data_layer.component + ")"
            else:
                pass
        elif data_layer.data == "VALUE":
            return "Value" + " (" + str(data_layer.x) + ")"
        elif data_layer.data == "CUSTOM_PROP":
            if data_layer.obj_mode == "PARENT":
                prefix = "Parent "
            elif data_layer.obj_mode == "CUSTOM":
                prefix = "Custom "
            elif data_layer.obj_mode == "PROPERTY":
                prefix = "Prop "
            else:
                prefix = ""

            if data_layer.name == "":
                return prefix + "Property (Invalid)"
            else:
                return prefix + "Property (" + data_layer.name + ")"
        elif data_layer.data == "FRAME":
            if data_layer.obj_mode == "PARENT":
                prefix = "Parent "
            elif data_layer.obj_mode == "CUSTOM":
                prefix = "Custom "
            elif data_layer.obj_mode == "PROPERTY":
                prefix = "Prop "
            else:
                prefix = ""

            if data_layer.vertex_mode == "OFFSET":
                return prefix + "Frame " + str(data_layer.index) + " Offset" + " (" + data_layer.component + ")"
            elif data_layer.vertex_mode == "NORMAL":
                return prefix + "Frame " + str(data_layer.index) + " Normal" + " (" + data_layer.component + ")"
            else:
                pass
        elif data_layer.data == "HIERARCHY":
            return "Hierarchy"
        else:
            pass

    return "Unknown"

def get_data_layer_icon(data_layer: object, details: bool = False) -> str:
    """
    Compute the icon to display for a data layer based on its various settings

    :param data_layer: data layer to generate an icon for
    :param details: True to generate an icon for packed layers
    :return: True if the data layer isn't packed into another layer, and the layer's icon name
    :rtype: tuple
    """
    if data_layer:
        if data_layer.packing_mode == "UV":
            return (True, "UV")
        elif data_layer.packing_mode == "VCOL":
            return (True, "GROUP_VCOL")
        elif data_layer.packing_mode == "NORMAL":
            return (True, "NORMALS_FACE")
        else:
            if details:
                # if data_layer.ptr < 0:
                #     return (False, "QUESTION")

                if data_layer.packing_mode == "XY_BIT" or data_layer.packing_mode == "XY_NUM":
                    return (False, "OVERLAY")
                elif data_layer.packing_mode == "XYZ_BIT" or data_layer.packing_mode == "XYZ_NUM":
                    return (False, "THREE_DOTS")
                elif data_layer.packing_mode == "FRACTION":
                    return (False, "PIVOT_ACTIVE")
                else:
                    pass

            return (False, "COPYDOWN")

    return (False, "X")

def get_data_layer_pre_bake_function(data_layer: object) -> callable:
    """
    Return the bake function associated with the given data layer

    :param data_layer: data layer to get bake function for
    :return: the bake function to call for the given data layer
    :rtype: callable function
    """
    if data_layer:
        if data_layer.data == "POSITION" :
            return pre_bake_position
        elif data_layer.data == "QUATERNION":
            return pre_bake_quaternion
        elif data_layer.data == "AXIS":
            return pre_bake_axis
        elif data_layer.data == "SHAPEKEY":
            return pre_bake_shapekey
        elif data_layer.data == "MASK":
            return pre_bake_mask
        elif data_layer.data == "RANDOM":
            return pre_bake_random
        elif data_layer.data == "VALUE":
            return pre_bake_value
        elif data_layer.data == "CUSTOM_PROP":
            return pre_bake_custom_prop
        elif data_layer.data == "FRAME":
            return pre_bake_frame
        elif data_layer.data == "HIERARCHY":
            return pre_bake_hierarchy
        else:
            pass
    
    return pre_bake_zeros

def get_data_layer_range(values: list, precision: float = 0.0001) -> tuple[bool, float, float]:
    """
    """
    if not values:
        return (False, 0.0, 1.0)

    if len(values) <= 0:
        return (False, 0.0, 1.0)

    if len(values) == 1:
        bake_range_offset = values[0]
        bake_range = 1.0
        bake_range_valid = False
    else:
        bake_range_offset = min(values)
        bake_range = max(values) - bake_range_offset
        if bake_range > abs(precision):
            bake_range_valid = True
        else:
            bake_range = 1.0
            bake_range_valid = False

    return bake_range_valid, bake_range_offset, bake_range

def get_data_layer_obj_source_obj(data_layer: object, obj: bpy.types.Object) -> bool:
    """
    Returns the source mesh to process for the given data layer's mesh.  
    The source can be:
    - itself, as the original un-evaluated object, retrieved via a custom property object pointer stored
      in the evaluated object,
    - the user-specified mesh defined in the data layer,
    - or the parent mesh.

    :param data_layer: The data layer currently being processed.  
    :param obj: The duplicated mesh currently being processed.
    """

    # user-specified object override
    if data_layer.obj_mode == "CUSTOM" and data_layer.obj:
        return data_layer.obj
    # parent object
    elif data_layer.obj_mode == "PARENT" and obj.parent:
        # walk up hierarchy
        parent = obj.get("BakedSource", obj)
        for depth in range(max(1, data_layer.index)):
            if parent.parent:
                parent = parent.parent
            else:
                return obj.get("BakedSource", obj) # fall back to self?

        return parent
    # source object
    elif data_layer.obj_mode == "PROPERTY":
        if data_layer.obj_prop != "" and data_layer.obj_prop in obj:
            source_obj = obj[data_layer.obj_prop]
            if source_obj:
                return source_obj
            else:
                return obj.get("BakedSource", obj) 
    else:
        return obj.get("BakedSource", obj)

######################
### BAKE FUNCTIONS ###
def bake_data_layers(context, layers_info, eval_objs_to_bake) -> tuple[bool, str]:
    """
    Responsible for actually baking data into meshes.

    For each layer:
    1. We check if it is contained in another layer and if so, we skip it
    2. For each other layer this layer may need to pack, we call this layer's bake function and gather the bake data
    in the following format: (mesh, [data_per_loop_id]). While doing so, we also keep track of the min/max values
    to bake for eventual bitpacking operations, in which case values need to be remapped to the range [0:1].
    3. For each mesh, get its data per layer, bitpack multiple data if needing to pack multiple layers. The value is
    finally stored in the mesh's UV, Vertex Color or Normal according to the data layer settings.

    :param context: Blender current execution context
    :param layers_info: list of data_layer, data_layer_info pairings
    :param eval_objs_to_bake: list of duplicated mesh objects to include in the bake
    :return: the function's success and potential error message
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    data_layers_uvs = []
    data_layers_vcols = []
    data_layers_normals = []

    dgraph = bpy.context.evaluated_depsgraph_get()

    # pre bake
    for data_layer, layer_info in layers_info:
        if not layer_info:
            continue

        to_bake, packing_mode, packing = layer_info
        if not to_bake:
            continue

        data_layer_range_offset = [0.0, 0.0, 0.0]
        data_layer_range = [0.0, 0.0, 0.0]
        safe_remap_range = False

        # numerically packed values must be within (0:1) range within a safety limit and the layer that is targeted by the other layer(s)
        # isn't itself using such packing_mode (UV instead) so we must iterate all ahead of time to see if the layer being targeted need
        # to report a modify range/offset to account for the safety precision offset as well
        for layer_packed_index, layer_packed in enumerate(packing):
            if layer_packed:
                if layer_packed.packing_mode == "XY_NUM" or layer_packed.packing_mode == "XYZ_NUM":
                    safe_remap_range = True

        for layer_packed_index, layer_packed in enumerate(packing):
            if layer_packed:
                pre_bake_func = get_data_layer_pre_bake_function(layer_packed)
                bake_success, bake_msg, bake_range_info = pre_bake_func(context, dgraph, layer_packed, eval_objs_to_bake)
                if not bake_success:
                    return (False, bake_msg)
                bake_range_valid, bake_offset, bake_range = bake_range_info
                data_layer_range_offset[layer_packed_index] = bake_offset
                if layer_packed.packing_mode == "FRACTION":
                    data_layer_range[layer_packed_index] = bake_range / min(0.99999, max(0.00001, settings.packing_precision))
                elif safe_remap_range:
                    # XY_NUM, XYZ_NUM can't have values equal to 0 or 1 once remapped to the range [0:1]
                    margin = 1.0 / 256.0
                    scale = 1.0 / (1.0 - 2.0 * margin)
                    adjusted_range = bake_range * scale
                    adjusted_offset = bake_offset - bake_range * (scale - 1.0) / 2.0

                    data_layer_range_offset[layer_packed_index] = adjusted_offset
                    data_layer_range[layer_packed_index] = adjusted_range
                else:
                    data_layer_range[layer_packed_index] = bake_range

        if data_layer.packing_mode == "UV":
            data_layers_uvs.append((data_layer, layer_info))
        elif data_layer.packing_mode == "VCOL":
            data_layers_vcols.append((data_layer, layer_info))
        elif data_layer.packing_mode == "NORMAL":
            data_layers_normals.append((data_layer, layer_info))
        else:
            pass

        add_bake_layer_report(data_layer, packing, (bake_range_valid, mathutils.Vector((data_layer_range_offset)), mathutils.Vector((data_layer_range))))

    # bake
    bake_data_layer_uv(context, eval_objs_to_bake, data_layers_uvs)
    bake_data_layer_vcol(context, eval_objs_to_bake, data_layers_vcols)
    bake_data_layer_normal(context, eval_objs_to_bake, data_layers_normals)

    return (True, "")

def bake_data_layer_uv(context, eval_objs_to_bake, data_layers_uvs):
    """

    """
    settings = context.scene.DataBakerSettings

    if not data_layers_uvs or len(data_layers_uvs) <= 0:
        return

    # for each mesh
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        progress = eval_obj_to_bake_index / max(1, (len(eval_objs_to_bake) - 1))
        context.window_manager.progress_update((progress * 26) + 10)

        eval_mesh = eval_obj_to_bake.data
        # for each uv layer
        for data_layer_uv, layer_info in data_layers_uvs:
            to_bake, packing_mode, packing = layer_info

            """ 1. prepare UV channel(s) """
            uv_index = 0 if data_layer_uv.uv_channel == "U" else 1
            one_minus = False if data_layer_uv.uv_channel == "U" else settings.unit_invert_v

            while (data_layer_uv.uv_index > (len(eval_mesh.uv_layers) - 1)):
                eval_mesh.uv_layers.new()

                zero_uv = (0.0, 1.0 if settings.unit_invert_v else 0.0)
                for loop_id in eval_mesh.loops:
                    eval_mesh.uv_layers[data_layer_uv.uv_index].data[loop_id.index].uv = zero_uv

            uv_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData"
            uv_name += "." + str(data_layer_uv.uv_index)
            eval_mesh.uv_layers[data_layer_uv.uv_index].name = uv_name

            """ 2. gather data from mesh attributes, and get layer range """
            layers_range = [None, None, None]
            datas = [None, None, None]
            for layer_packed_index, layer_packed in enumerate(packing):
                if layer_packed and (layer_packed.ID in eval_mesh.attributes):
                    data = np.zeros(len(eval_mesh.loops), dtype=np.float32)

                    attr = eval_mesh.attributes[layer_packed.ID]
                    attr.data.foreach_get('value', data)

                    datas[layer_packed_index] = data

                    layers_range[layer_packed_index] = (
                        get_bake_layer_report_range_valid(layer_packed),
                        get_bake_layer_report_range_offset(layer_packed),
                        get_bake_layer_report_range(layer_packed))
                    
            for layer_range_index, layer_range in enumerate(layers_range):
                if layer_range is None:
                    layers_range[layer_range_index] = (False, 0, 1)
                    
            """ 3. bake """
            for loop_id in eval_mesh.loops:
                index = loop_id.index

                data_to_pack = mathutils.Vector((
                    datas[0][index] if datas[0] is not None else 0.0,
                    datas[1][index] if datas[1] is not None else 0.0,
                    datas[2][index] if datas[2] is not None else 0.0))

                if packing_mode == "XYZ_BIT":
                    data_to_bake = get_packed_11_10_10_xyz(data_to_pack.x, layers_range[0][1], layers_range[0][2],
                                                            data_to_pack.y, layers_range[1][1], layers_range[1][2],
                                                            data_to_pack.z, layers_range[2][1], layers_range[2][2])
                elif packing_mode == "XYZ_NUM":
                    data_to_bake = get_pack_3(data_to_pack.x, layers_range[0][1], layers_range[0][2],
                                                            data_to_pack.y, layers_range[1][1], layers_range[1][2],
                                                            data_to_pack.z, layers_range[2][1], layers_range[2][2])
                elif packing_mode == "XY_BIT":
                    data_to_bake = get_packed_16_15_xy(data_to_pack.x, layers_range[0][1], layers_range[0][2],
                                                        data_to_pack.y, layers_range[1][1], layers_range[1][2])
                elif packing_mode == "XY_NUM":
                    data_to_bake = get_pack_2(data_to_pack.x, layers_range[0][1], layers_range[0][2],
                                                data_to_pack.y, layers_range[1][1], layers_range[1][2])
                elif packing_mode == "FRACTION":
                    data_to_bake = get_packed_frac(data_to_pack.x, data_to_pack.y, layers_range[1][1], layers_range[1][2])
                else:
                    data_to_bake = data_to_pack.x

                if one_minus:
                    data_to_bake = 1.0 - data_to_bake # @NOTE this screws up bit-packed data but is required for UE because of the hardcoded (1-x) upon mesh import

                eval_mesh.uv_layers[data_layer_uv.uv_index].data[loop_id.index].uv[uv_index] = data_to_bake

def bake_data_layer_vcol(context, eval_objs_to_bake, data_layers_vcols):
    """
    
    """
    settings = context.scene.DataBakerSettings
    
    if not data_layers_vcols or len(data_layers_vcols) <= 0:
        return

    # for each mesh
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        progress = eval_obj_to_bake_index / max(1, (len(eval_objs_to_bake) - 1))
        context.window_manager.progress_update((progress * 26) + 36)

        eval_mesh = eval_obj_to_bake.data
        # for each vcol layer
        for data_layer_vcol, layer_info in data_layers_vcols:
            to_bake, packing_mode, packing = layer_info

            """ 1. prepare Vertex Colors """
            vcol_index = 0 if data_layer_vcol.vcol_rgba == "R" else 1 if data_layer_vcol.vcol_rgba == "G" else 2 if data_layer_vcol.vcol_rgba == "B" else 3

            if eval_mesh.vertex_colors:
                vcol = eval_mesh.vertex_colors.active
            else:
                vcol = eval_mesh.vertex_colors.new()

                for loop_id in eval_mesh.loops:
                    vcol.data[loop_id.index].color = [0.0, 0.0, 0.0, 0.0]

            """ 2. gather data from mesh attributes """
            if data_layer_vcol.ID in eval_mesh.attributes:
                data = np.zeros(len(eval_mesh.loops), dtype=np.float32)

                attr = eval_mesh.attributes[data_layer_vcol.ID]
                attr.data.foreach_get('value', data)
            else:
                data = None

            """ 3. get min/max """
            data_to_bake_min = get_bake_layer_report_range_offset(data_layer_vcol)
            data_to_bake_max = get_bake_layer_report_range(data_layer_vcol) + data_to_bake_min

            is_unit = True if data_to_bake_min == 0 and data_to_bake_max == 1 else False
            edit_bake_layer_report_range_prop(data_layer_vcol, is_unit, "range_unit_vector")

            """ 4. bake """
            for loop_id in eval_mesh.loops:
                index = loop_id.index

                data_to_bake = data[index] if data is not None else 0.0
                data_to_bake = get_normalized(data_to_bake, data_to_bake_min, data_to_bake_max)

                vcol.data[index].color[vcol_index] = data_to_bake

def bake_data_layer_normal(context, eval_objs_to_bake, data_layers_normals):
    """

    """
    settings = context.scene.DataBakerSettings
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))

    if not data_layers_normals or len(data_layers_normals) <= 0:
        return

    layers_range = [None, None, None]
    layers_used = []

    """
    1. for each layer (aka, individual data to bake in the normal X, Y and Z components), gather min/max range
    and keep track of used X/Y/Z components (as 1/2/3 indices)
    """
    for data_layer_normal, layer_info in data_layers_normals:
        index = 0 if data_layer_normal.normal_xyz == "X" else 1 if data_layer_normal.normal_xyz == "Y" else 2            

        # get & cache layer min/max range
        layers_range[index] = (
            get_bake_layer_report_range_valid(data_layer_normal),
            get_bake_layer_report_range_offset(data_layer_normal),
            get_bake_layer_report_range(data_layer_normal))

        # keep track of used X/Y/Z components
        layers_used.append(index)

    """
    2. for each mesh, gather data to bake from its attributes and for each normal, compute the XYZ vector to
    store in the normal to check if said vector is of unit length. We sadly need to know this ahead of time
    before actually iterating meshes, and it's far from ideal...
    """
    unit_normal = True
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        eval_mesh = eval_obj_to_bake.data

        datas = [None, None, None]
        for data_layer_normal, layer_info in data_layers_normals:
            if data_layer_normal.ID in eval_mesh.attributes:
                data = np.zeros(len(eval_mesh.loops), dtype=np.float32)
                attr = eval_mesh.attributes[data_layer_normal.ID]
                attr.data.foreach_get('value', data)

                if data_layer_normal.normal_xyz == "X":
                    datas[0] = data
                elif data_layer_normal.normal_xyz == "Y":
                    datas[1] = data
                else:
                    datas[2] = data

        # for each normal to bake
        for index in range(len(eval_mesh.loops)):
            normal = mathutils.Vector((
                datas[0][index] if datas[0] is not None else 0.0,
                datas[1][index] if datas[1] is not None else 0.0,
                datas[2][index] if datas[2] is not None else 0.0))

            # check if its of unit length
            if abs(normal.length - 1.0) > 0.001:
                unit_normal = False
                break

    for data_layer_normal, layer_info in data_layers_normals:
        edit_bake_layer_report_range_prop(data_layer_normal, unit_normal, "range_unit_vector")

    """
    3. If any XYZ normal is not a unit vector, spherical reprojection becomes necessary. However, this prevents us from directly packing three
    independent values into the XYZ normal.

    Let's assume we want to bake a simple linear mask into the X component of the normal—and nothing else. Since the normal must be normalized,
    we cannot simply store values in the [0:1] range in the X component alone. Doing so would alter the X component upon normalization, unless
    we adjust another component (Y or Z) to maintain the unit length. This can be achieved with the following:

    y = sqrt(1.0 - saturation(dot(normal.xz, normal.xz)))
    or
    z = sqrt(1.0 - saturation(dot(normal.xy, normal.xy)))

    In this approach, one of the three components must be reserved to ensure that the resulting normal remains normalized, allowing the other
    two to carry the data. However, before doing this, the 2D vector formed by the other two components must be at most unit-length. To ensure
    this, we first find the value that deviates most from the mean and remap the values to the [-1:1] range.

    This entire step is unnecessary if all input normals are guaranteed to be of unit length. In that case, all three components of the normal
    can be used directly to store arbitrary values in a unit XYZ vector.
    """
    if unit_normal:
        layer_z_available = True
    else:
        layer_z_available = True if len(layers_used) < 3 else False

        global_min_x = layers_range[0][1] if layers_range[0] else 0.0
        global_min_y = layers_range[1][1] if layers_range[1] else 0.0
        global_min_z = layers_range[2][1] if layers_range[2] and layer_z_available else 0.0
        global_min = mathutils.Vector((global_min_x, global_min_y, global_min_z)) * signed_axis

        global_max_x = layers_range[0][2] if layers_range[0] else 0.0
        global_max_y = layers_range[1][2] if layers_range[1] else 0.0
        global_max_z = layers_range[2][2] if layers_range[2] and layer_z_available else 0.0
        global_max = mathutils.Vector((global_max_x, global_max_y, global_max_z)) * signed_axis

        global_average = (global_max + global_min) * 0.5
        global_radius = max((global_max - global_average).length, (global_average - global_min).length)
        global_radius_inv = (1.0 / global_radius) if global_radius > 0.0 else 1.0

        if not layer_z_available:
            layers_used.remove(2) # put Z layer back into the pool of available layers

    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        progress = eval_obj_to_bake_index / max(1, (len(eval_objs_to_bake) - 1))
        context.window_manager.progress_update((progress * 26) + 62)

        eval_mesh = eval_obj_to_bake.data
        """
        4. for each mesh, gather normal X/Y/Z data from its attributes
        """
        datas = [None, None, None]
        for data_layer_normal, layer_info in data_layers_normals:
            if data_layer_normal.normal_xyz == "Z" and not layer_z_available:
                continue

            if data_layer_normal.ID in eval_mesh.attributes:
                data = np.zeros(len(eval_mesh.loops), dtype=np.float32)
                attr = eval_mesh.attributes[data_layer_normal.ID]
                attr.data.foreach_get('value', data)

                if data_layer_normal.normal_xyz == "X":
                    datas[0] = data
                elif data_layer_normal.normal_xyz == "Y":
                    datas[1] = data
                else:
                    datas[2] = data

        """
        5. build normal buffer
        """
        num_normals = len(eval_mesh.loops)
        normals = [None] * num_normals
        for index in range(num_normals):
            normal = mathutils.Vector((
                datas[0][index] if datas[0] is not None else 0.0,
                datas[1][index] if datas[1] is not None else 0.0,
                datas[2][index] if datas[2] is not None else 0.0))

            normals[index] = normal * signed_axis

        """
        6. remap necessary X/Y/Z components IF packing a non-unit vector
        """
        if not unit_normal:
            indices_all = [0, 1, 2]

            if not layer_z_available:
                indices_to_remap = [0, 1]
            else:
                indices_to_remap = [index for index in indices_all if index in layers_used] # indices to remap are 'used' layers

            for normal in normals:
                for index in indices_to_remap:
                    normal[index] = (normal[index] - global_average[index]) * global_radius_inv

            """
            7. derive the first remaining component based on the other two: z = sqrt(1.0 - saturation(dot(normal.xz, normal.xz)))
            """
            index_to_derive = [index for index in indices_all if index not in layers_used][0] # indices to derive are 'unused' layers but we only really need the first one
            indices_all.remove(index_to_derive)
            for normal in normals:
                flat_normal = mathutils.Vector((normal[indices_all[0]], normal[indices_all[1]], 0.0))
                normal[index_to_derive] = math.sqrt(1.0 - min(1.0, max(0.0, flat_normal.dot(flat_normal))))

        """
        7.1. it's critical to account for mesh orientation! normals are set in local space and thus are rotated based on
        the mesh's orientation so normal has to be oriented by the inverse of the upcoming rotation change
        """
        for i, _ in enumerate(normals):
            normals[i] = eval_obj_to_bake.matrix_world.inverted().to_quaternion() @ normals[i]

        """
        8. bake!
        """
        eval_mesh.normals_split_custom_set(normals)

    """
    9. modify report
    """
    if unit_normal:
        for data_layer_normal, layer_info in data_layers_normals:
            edit_bake_layer_report_range_offset(data_layer_normal, mathutils.Vector((0.0, 0.0, 0.0)))
            edit_bake_layer_report_range(data_layer_normal, mathutils.Vector((1.0, 1.0, 1.0)))
            edit_bake_layer_report_range_valid(data_layer_normal, True)
    else:
        i = 0
        for data_layer_normal, layer_info in data_layers_normals:
            if i == 0:
                shared_offset = global_average.x * signed_axis[0] # sign_axis has to be cancelled here
                shared_radius = global_radius
                edit_range_offset = mathutils.Vector((shared_offset, shared_offset, shared_offset))
                edit_range =  mathutils.Vector((shared_radius, shared_radius, shared_radius))
            elif i == 1:
                shared_offset = global_average.y * signed_axis[1]
                shared_radius = global_radius
                edit_range_offset = mathutils.Vector((shared_offset, shared_offset, shared_offset))
                edit_range =  mathutils.Vector((shared_radius, shared_radius, shared_radius))
            else:
                shared_offset = global_average.z * signed_axis[2] if layer_z_available else 0.0
                shared_radius = global_radius if layer_z_available else 1.0
                edit_range_offset = mathutils.Vector((shared_offset, shared_offset, shared_offset))
                edit_range =  mathutils.Vector((shared_radius, shared_radius, shared_radius))
            edit_range_valid = abs(global_average.x - global_radius) > 0.0001 and abs(global_average.y - global_radius) > 0.0001 and abs(global_average.z - global_radius) > 0.0001

            edit_bake_layer_report_range_offset(data_layer_normal, edit_range_offset)
            edit_bake_layer_report_range(data_layer_normal, edit_range)
            edit_bake_layer_report_range_valid(data_layer_normal, edit_range_valid)

            if not layer_z_available and data_layer_normal.normal_xyz == "Z":
                clear_bake_layer_report(data_layer_normal)

            i += 1

##########################
### PRE-BAKE FUNCTIONS ###
def pre_bake_position(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        uneval_obj_source = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat
        eval_obj_source_loc = eval_obj_source_mat.to_translation()

        vector_to_bake = eval_obj_source_loc * signed_scale
        if settings.unit_axis_order != "XYZ":
                vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

        if data_layer.component == "X":
            data_to_bake = vector_to_bake.x
        elif data_layer.component == "Y":
            data_to_bake = vector_to_bake.y
        elif data_layer.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0
        
        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(data_to_bake)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_quaternion(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        uneval_obj_source = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat

        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                     (-1 if settings.unit_invert_y else 1),
                                                     (-1 if settings.unit_invert_z else 1), 1))
        rot_matrix = sign_matrix @ eval_obj_source_mat @ sign_matrix

        xyz_order = data_layer.quat_xyz_order if data_layer.override_xyz_order else settings.unit_axis_order
        euler = rot_matrix.to_euler(xyz_order)

        eval_obj_source_quat = euler.to_quaternion()

        if data_layer.quat == "X":
            data_to_bake = eval_obj_source_quat.x
        elif data_layer.quat == "Y":
            data_to_bake = eval_obj_source_quat.y
        elif data_layer.quat == "Z":
            data_to_bake = eval_obj_source_quat.z
        elif data_layer.quat == "W":
            data_to_bake = eval_obj_source_quat.w
        elif data_layer.quat == "XYZW":
            data_to_bake = get_compressed_quat(eval_obj_source_quat)
        else:
            data_to_bake = 0.0

        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        if data_layer.quat != "XYZW":
            bake_range_values.append(data_to_bake)
        else:
            bake_range_values.append(0)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_axis(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        uneval_obj_source = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat

        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                    (-1 if settings.unit_invert_y else 1),
                                                    (-1 if settings.unit_invert_z else 1), 1))
        eval_obj_source_mat = sign_matrix @ eval_obj_source_mat @ sign_matrix
        eval_obj_source_mat = eval_obj_source_mat.to_3x3()

        if data_layer.axis == "X":
            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((1.0, 0.0, 0.0))
        elif data_layer.axis == "Y":
            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((0.0, 1.0, 0.0))
        else: # Z
            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((0.0, 0.0, 1.0))
        vector_to_bake.normalize()

        if settings.unit_axis_order != "XYZ":
            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

        if data_layer.component == "X":
            data_to_bake = vector_to_bake.x
        elif data_layer.component == "Y":
            data_to_bake = vector_to_bake.y
        elif data_layer.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(data_to_bake)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_shapekey(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    dgraph = bpy.context.evaluated_depsgraph_get()

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        data_loop_ids = [0.0] * len(eval_mesh.loops)

        target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
        if not target:
            return (False, "Shapekey: No source object found", None)
        if target.type != "MESH":
            return (False, "Shapekey: Source object isn't a mesh", None)

        target_mesh = target.data
        if target_mesh.shape_keys and (data_layer.name in target_mesh.shape_keys.key_blocks):
            # duplicate mesh data and apply the shapekey offset to it
            bm = bmesh.new()
            bm.from_mesh(target_mesh)
            bm.verts.ensure_lookup_table()

            ref_pos = [target.matrix_world @ vertex.co for vertex in bm.verts]

            for vertex_index, vertex in enumerate(bm.verts):
                vertex.co = target.matrix_world @ target_mesh.shape_keys.key_blocks[data_layer.name].data[vertex_index].co

            bm.normal_update()
            bm.verts.ensure_lookup_table()

            # mesh_name = "MyDebugMesh"
            # object_name = "MyDebugObject"
            # mesh = bpy.data.meshes.new(mesh_name)
            # bm.to_mesh(mesh)
            # obj = bpy.data.objects.new(object_name, mesh)
            # bpy.context.collection.objects.link(obj)

            """
            if topology between duplicated, evaluated mesh and original or target mesh differs, we fall back
            to using nearest search. This is unlikely to result in a desirable offset or normal, except for
            rare cases, but it at least allows for the bake to continue
            """
            topology_mismatch  = len(eval_mesh.vertices) != len(target_mesh.vertices)
            topology_mismatch |= len(eval_mesh.loops) != len(target_mesh.loops)
            #topology_mismatch |= eval_mesh != target_mesh
            if topology_mismatch:
                BVH = BVHTree.FromBMesh(bm) # fall back to nearest search method

                for loop_id in eval_mesh.loops:
                    vert_pos = eval_mesh.vertices[loop_id.vertex_index].co
                    closest_face_pos, closest_face_nor, closest_face_index, closest_face_dist = BVH.find_nearest(vert_pos)

                    if data_layer.vertex_mode == "OFFSET":
                        vector_to_bake = (closest_face_pos - vert_pos) * signed_scale
                    else:
                        vector_to_bake = closest_face_nor.normalized() * signed_axis

                    if settings.unit_axis_order != "XYZ":
                        vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                    if data_layer.component == "X":
                        data_to_bake = vector_to_bake.x
                    elif data_layer.component == "Y":
                        data_to_bake = vector_to_bake.y
                    else:
                        data_to_bake = vector_to_bake.z

                    data_loop_ids[loop_id.index] = data_to_bake
            else:
                for loop_id in eval_mesh.loops:
                    if data_layer.vertex_mode == "OFFSET":
                        vert_pos = ref_pos[loop_id.vertex_index]
                        target_vert_pos = bm.verts[loop_id.vertex_index].co
                        vector_to_bake = (target_vert_pos - vert_pos) * signed_scale
                    else:
                        vector_to_bake = bm.verts[loop_id.vertex_index].normal.normalized() * signed_axis

                    if settings.unit_axis_order != "XYZ":
                        vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                    if data_layer.component == "X":
                        data_to_bake = vector_to_bake.x
                    elif data_layer.component == "Y":
                        data_to_bake = vector_to_bake.y
                    elif data_layer.component == "Z":
                        data_to_bake = vector_to_bake.z
                    else:
                        pass

                    data_loop_ids[loop_id.index] = data_to_bake

            bm.free()
        else:
            return (False, "No shapekey named " + data_layer.name + " found in object " + target.name, None)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(min(data_loop_ids))
        bake_range_values.append(max(data_loop_ids))

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_mask(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    origin_mode = "WORLD"
    if data_layer.origin_mode == origin_mode:
        pass # WORLD
    elif data_layer.origin_mode == "ORIGIN":
        if data_layer.obj:
            origin_mode = "ORIGIN"
        else:
            pass # WORLD
    elif data_layer.origin_mode == "SELECTION":
        origin_mode = data_layer.origin_mode
    elif data_layer.origin_mode == "OBJECT":
        origin_mode = data_layer.origin_mode
    elif data_layer.origin_mode == "PARENT":
        origin_mode = data_layer.origin_mode

    if data_layer.mask_mode == "SPHERE":
        return pre_bake_mask_sphere(dgraph, data_layer, eval_objs_to_bake, "BakedSource", origin_mode, signed_scale)
    elif data_layer.mask_mode == "LINEAR":
        if data_layer.axis == "X":
            world_axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif data_layer.axis == "Y":
            world_axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif data_layer.axis == "Z":
            world_axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            world_axis = mathutils.Vector((0.0, 0.0, 0.0))

        if settings.origin_obj:
            world_axis = settings.origin_obj.matrix_world.inverted().to_quaternion() @ world_axis

        return pre_bake_mask_linear(dgraph, data_layer, eval_objs_to_bake, "BakedSource", origin_mode, signed_scale, world_axis)
    else:
        return (False, "Unknown mask mode", None)

def pre_bake_mask_sphere(dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list, custom_prop: str, origin_mode: str="WORLD", signed_scale: mathutils.Vector=mathutils.Vector((1.0, 1.0, 1.0))) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    # sphere mask origin may be 'global' (shared across all objects)
    mask_global = False
    if origin_mode == "WORLD":
        mask_origin_pos = mathutils.Vector((0.0, 0.0, 0.0))
        mask_global = True
    elif origin_mode == "ORIGIN":
        mask_origin_pos = data_layer.obj.matrix_world.to_translation()
        mask_global = True
    elif origin_mode == "SELECTION":
        averaged_pos = mathutils.Vector((0.0, 0.0, 0.0))
        for eval_obj_to_bake in eval_objs_to_bake:
            averaged_pos += eval_obj_to_bake.matrix_world.to_translation()
        mask_origin_pos = averaged_pos / max(len(eval_objs_to_bake), 1)
        mask_global = True

    # if 'global', iterate all meshes to get max distance relative to sphere mask origin
    if mask_global:
        verts = []
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data

            uneval_obj_source = eval_obj_to_bake.get(custom_prop, eval_obj_to_bake)
            eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
            eval_obj_source_mat = eval_obj_source.matrix_world

            for loop_id in eval_mesh.loops:
                vertex_offset = (eval_obj_source_mat @ eval_mesh.vertices[loop_id.vertex_index].co) - mask_origin_pos
                verts.append(vertex_offset.length)

        min_dist = min(verts)
        max_dist = max(verts)
        length = max_dist - min_dist
        inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
        min_dist = min_dist if length > 0.0001 else 0.0

    dgraph = bpy.context.evaluated_depsgraph_get()

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data
        data_loop_ids = [0.0] * len(eval_mesh.loops)

        uneval_obj_source = eval_obj_to_bake.get(custom_prop, eval_obj_to_bake)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world

        eval_obj_source_mesh = eval_obj_source.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        eval_obj_source_mesh.transform(eval_obj_source_mat)

        # if 'local', get sphere mask origin per object
        if not mask_global:
            verts = [] # reset per mesh

            if origin_mode == "OBJECT":
                origin_obj = eval_obj_source
            elif origin_mode == "PARENT":
                if eval_obj_source.parent:
                    origin_obj = eval_obj_source.parent
                else:
                    origin_obj = eval_obj_source
            else:
                origin_obj = None

            if origin_obj:
                mask_origin_pos = origin_obj.matrix_world.to_translation()

                # iterate all meshes to get max distance relative to 'local' sphere mask origin
                for loop_id in eval_obj_source_mesh.loops:
                    vertex_offset = eval_obj_source_mesh.vertices[loop_id.vertex_index].co - mask_origin_pos
                    verts.append(vertex_offset.length)

            min_dist = min(verts)
            max_dist = max(verts)
            length = max_dist - min_dist
            inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
            min_dist = min_dist if length > 0.0001 else 0.0

        # compute sphere mask
        for loop_id in eval_obj_source_mesh.loops:
            vertex_offset = eval_obj_source_mesh.vertices[loop_id.vertex_index].co - mask_origin_pos

            data_to_bake = vertex_offset.length

            if data_layer.normalize:
                data_to_bake -= min_dist
                data_to_bake *= inv_length

            if data_layer.clamp:
                data_to_bake = max(0.0, min(1.0, data_to_bake))

            if data_layer.normalize or data_layer.clamp:
                data_to_bake = math.pow(data_to_bake, data_layer.falloff)

            data_loop_ids[loop_id.index] = data_to_bake

        eval_obj_source.to_mesh_clear()

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(min(data_loop_ids))
        bake_range_values.append(max(data_loop_ids))

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_mask_linear(dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list, custom_prop: str, origin_mode: str="WORLD", signed_scale: mathutils.Vector=mathutils.Vector((1.0, 1.0, 1.0)), world_axis: mathutils.Vector=mathutils.Vector((0.0, 0.0, 1.0))) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    # linear mask origin may be 'global' (shared across all objects)
    mask_global = False
    if origin_mode == "WORLD":
        mask_origin_pos = mathutils.Vector((0.0, 0.0, 0.0))
        mask_origin_axis = world_axis
        mask_global = True
    elif origin_mode == "ORIGIN":
        mask_origin_pos = data_layer.obj.matrix_world.to_translation()
        mask_origin_axis = world_axis
        mask_global = True

        if data_layer.axis_mode == "OBJECT" and data_layer.axis_obj:
            mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
        elif data_layer.axis_mode == "LOCAL":
            mask_origin_axis = data_layer.obj.matrix_world.to_quaternion() @ world_axis
        else:
            pass # WORLD
    elif origin_mode == "SELECTION":
        averaged_pos = mathutils.Vector((0.0, 0.0, 0.0))
        for eval_obj_to_bake in eval_objs_to_bake:
            uneval_obj_source = eval_obj_to_bake.get(custom_prop, eval_obj_to_bake)
            eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
            eval_obj_source_mat = eval_obj_source.matrix_world
            averaged_pos += eval_obj_source_mat.to_translation()
        mask_origin_pos = averaged_pos / max(len(eval_objs_to_bake), 1)
        mask_origin_axis = world_axis
        mask_global = True

    # if 'global', iterate all meshes to get max distance relative to linear mask origin
    if mask_global:
        verts = []
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data

            for loop_id in eval_mesh.loops:
                vertex_offset = (eval_obj_to_bake.matrix_world @ eval_mesh.vertices[loop_id.vertex_index].co) - mask_origin_pos
                verts.append(vertex_offset.dot(mask_origin_axis))

        min_dist = min(verts)
        max_dist = max(verts)
        length = max_dist - min_dist
        inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
        min_dist = min_dist if length > 0.0001 else 0.0

    dgraph = bpy.context.evaluated_depsgraph_get()

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data
        data_loop_ids = [0.0] * len(eval_mesh.loops)

        uneval_obj_source = eval_obj_to_bake.get(custom_prop, eval_obj_to_bake)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        eval_obj_source_mesh = eval_obj_source.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        eval_obj_source_mesh.transform(eval_obj_source_mat)

        # if 'local', get linear mask origin per object
        if not mask_global:
            verts = [] # reset per mesh

            if origin_mode == "OBJECT":
                origin_obj = eval_obj_source
            elif origin_mode == "PARENT":
                if eval_obj_source.parent:
                    origin_obj = eval_obj_source.parent
                else:
                    origin_obj = eval_obj_source
            else:
                origin_obj = None

            if origin_obj:
                mask_origin_pos = origin_obj.matrix_world.to_translation()
                if data_layer.axis_mode == "OBJECT" and data_layer.axis_obj:
                    mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
                elif data_layer.axis_mode == "LOCAL":
                    mask_origin_axis = origin_obj.matrix_world.to_quaternion() @ world_axis
                else:
                    mask_origin_axis = world_axis

                # iterate all meshes to get max distance relative to 'local' linear mask origin
                for loop_id in eval_obj_source_mesh.loops:
                    vertex_offset = eval_obj_source_mesh.vertices[loop_id.vertex_index].co - mask_origin_pos
                    verts.append(vertex_offset.dot(mask_origin_axis))
            else:
                if data_layer.axis_mode == "OBJECT" and data_layer.axis_obj:
                    mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
                elif data_layer.axis_mode == "LOCAL":
                    mask_origin_axis = eval_obj_source_mat.to_quaternion() @ world_axis
                else:
                    mask_origin_axis = world_axis

            min_dist = min(verts)
            max_dist = max(verts)
            length = max_dist - min_dist
            inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
            min_dist = min_dist if length > 0.0001 else 0.0

        # compute linear mask
        for loop_id in eval_obj_source_mesh.loops:
            vertex_offset = eval_obj_source_mesh.vertices[loop_id.vertex_index].co - mask_origin_pos

            data_to_bake = (vertex_offset).dot(mask_origin_axis)

            if data_layer.normalize:
                data_to_bake -= min_dist
                data_to_bake *= inv_length

            if data_layer.clamp:
                data_to_bake = max(0.0, min(1.0, data_to_bake))

            if data_layer.normalize or data_layer.clamp:
                data_to_bake = math.pow(data_to_bake, data_layer.falloff)

            data_loop_ids[loop_id.index] = data_to_bake

        eval_obj_source.to_mesh_clear()

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(min(data_loop_ids))
        bake_range_values.append(max(data_loop_ids))

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_random(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    if data_layer.rand_float_mode == "FLOAT":
        return pre_bake_random_float(context, dgraph, data_layer, eval_objs_to_bake)
    elif data_layer.rand_float_mode == "FLOAT2":
        return pre_bake_random_float2(context, dgraph, data_layer, eval_objs_to_bake)
    elif data_layer.rand_float_mode == "FLOAT3":
        return pre_bake_random_float3(context, dgraph, data_layer, eval_objs_to_bake)
    else:
        return (False, "Unknown random mode", None)

def pre_bake_random_float(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    uniform_values = []
    uniform_length = 0

    bake_range_values = []

    if data_layer.rand_mode == "COLLECTION":
        # pre pass
        cols = []
        for eval_obj_to_bake in eval_objs_to_bake:
            target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
            for col in target.users_collection:
                if col not in cols:
                    cols.append(col)

        uniform_length = len(cols)
        uniform_length = max(1, uniform_length - 1)

        for col_index, col in enumerate(cols):
            uniform_values.append(col_index / uniform_length)

        if uniform_length > 0:
            random.seed(data_layer.rand_seed)
            random.shuffle(uniform_values)

        # main pass
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data

            target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
            if target.users_collection:
                col_index = -1
                try:
                    col_index = cols.index(target.users_collection[0])
                except:
                    pass
                
                if col_index >= 0:
                    data_to_bake = (uniform_values[col_index] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random
                else:
                    data_to_bake = 0.0
            else:
                data_to_bake = 0.0

            data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(data_to_bake)
    elif data_layer.rand_mode == "OBJECT":
        uniform_length = len(eval_objs_to_bake)
        uniform_length = max(1, uniform_length - 1)

        # pre pass
        for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
            uniform_values.append(eval_obj_to_bake_index / uniform_length)

        if uniform_length > 0:
            random.seed(data_layer.rand_seed)
            random.shuffle(uniform_values)

        # main pass
        for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
            eval_mesh = eval_obj_to_bake.data

            data_to_bake = (uniform_values[eval_obj_to_bake_index] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

            data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(data_to_bake)
    elif data_layer.rand_mode == "FACE":
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data
            uniform_length += len(eval_mesh.polygons)
        uniform_length = max(1, uniform_length - 1)

        # pre pass
        face_offset = 0
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data
            for face_index, face in enumerate(eval_mesh.polygons):
                uniform_values.append((face_index + face_offset) / uniform_length)
            
            face_offset += len(eval_mesh.polygons)

        if uniform_length > 0:
            random.seed(data_layer.rand_seed)
            random.shuffle(uniform_values)

        # main pass
        face_offset = 0
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data
            data_loop_ids = [0.0] * len(eval_mesh.loops)

            for face_index, face in enumerate(eval_mesh.polygons):
                data_to_bake = (uniform_values[face_index + face_offset] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

                for loop_id in face.loop_indices:
                    data_loop_ids[loop_id] = data_to_bake

            face_offset += len(eval_mesh.polygons)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(min(data_loop_ids))
            bake_range_values.append(max(data_loop_ids))
    else:
        return (False, "Unknown rand mode", None)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_random_float2(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    bake_range_values = []

    if data_layer.rand_mode == "COLLECTION":
        # pre pass
        cols = []
        for eval_obj_to_bake in eval_objs_to_bake:
            target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
            for col in target.users_collection:
                if col not in cols:
                    cols.append(col)

        # main pass
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data

            target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
            if target.users_collection:
                col_index = cols.index(target.users_collection[0])
                if col_index >= 0:
                    np.random.seed(data_layer.rand_seed + col_index)
                    rand = np.random.uniform(-math.pi, math.pi)

                    if data_layer.component == "X":
                        data_to_bake = math.cos(rand)
                    elif data_layer.component == "Y":
                        data_to_bake = math.sin(rand)
                    elif data_layer.component == "Z":
                        data_to_bake = 0.0
                    else:
                        data_to_bake = 0.0
            else:
                data_to_bake = 0.0

            data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(data_to_bake)
    elif data_layer.rand_mode == "OBJECT":

        # main pass
        for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
            eval_mesh = eval_obj_to_bake.data

            np.random.seed(data_layer.rand_seed + eval_obj_to_bake_index)
            rand = np.random.uniform(-math.pi, math.pi)

            if data_layer.component == "X":
                data_to_bake = math.cos(rand)
            elif data_layer.component == "Y":
                data_to_bake = math.sin(rand)
            elif data_layer.component == "Z":
                data_to_bake = 0.0
            else:
                data_to_bake = 0.0

            data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(data_to_bake)
    elif data_layer.rand_mode == "FACE":
        # main pass
        face_offset = 0
        for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
            eval_mesh = eval_obj_to_bake.data

            data_loop_ids = [0.0] * len(eval_mesh.loops)

            for face_index, face in enumerate(eval_mesh.polygons):
                np.random.seed(data_layer.rand_seed + (face_index + face_offset))
                rand = np.random.uniform(-math.pi, math.pi)

                if data_layer.component == "X":
                    data_to_bake = math.cos(rand)
                elif data_layer.component == "Y":
                    data_to_bake = math.sin(rand)
                elif data_layer.component == "Z":
                    data_to_bake = 0.0
                else:
                    data_to_bake = 0.0

                for loop_id in face.loop_indices:
                    data_loop_ids[loop_id] = data_to_bake

            face_offset += len(eval_mesh.polygons)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(min(data_loop_ids))
            bake_range_values.append(max(data_loop_ids))
    else:
        return (False, "Unknown rand mode", None)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_random_float3(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    bake_range_values = []

    if data_layer.rand_mode == "COLLECTION":
        # pre pass
        cols = []
        for eval_obj_to_bake in eval_objs_to_bake:
            target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
            for col in target.users_collection:
                if col not in cols:
                    cols.append(col)

        # main pass
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_mesh = eval_obj_to_bake.data

            target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)
            if target.users_collection:
                col_index = cols.index(target.users_collection[0])
                if col_index >= 0:
                    # https://gist.github.com/andrewbolster/10274979
                    np.random.seed(data_layer.rand_seed + col_index)
                    phi = np.random.uniform(0,np.pi*2)
                    costheta = np.random.uniform(-1,1)
                    theta = np.arccos( costheta )

                    if data_layer.component == "X":
                        data_to_bake = np.sin( theta) * np.cos( phi )
                    elif data_layer.component == "Y":
                        data_to_bake = np.sin( theta) * np.sin( phi )
                    elif data_layer.component == "Z":
                        data_to_bake = np.cos( theta )
                    else:
                        data_to_bake = 0.0        
            else:
                data_to_bake = 0.0

            data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(data_to_bake)
    elif data_layer.rand_mode == "OBJECT":
        # main pass
        for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
            eval_mesh = eval_obj_to_bake.data

            # https://gist.github.com/andrewbolster/10274979
            np.random.seed(data_layer.rand_seed + eval_obj_to_bake_index)
            phi = np.random.uniform(0,np.pi*2)
            costheta = np.random.uniform(-1,1)
            theta = np.arccos( costheta )

            if data_layer.component == "X":
                data_to_bake = np.sin( theta) * np.cos( phi )
            elif data_layer.component == "Y":
                data_to_bake = np.sin( theta) * np.sin( phi )
            elif data_layer.component == "Z":
                data_to_bake = np.cos( theta )
            else:
                data_to_bake = 0.0

            data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(data_to_bake)
    elif data_layer.rand_mode == "FACE":
        # main pass
        face_offset = 0
        for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
            eval_mesh = eval_obj_to_bake.data

            data_loop_ids = [0.0] * len(eval_mesh.loops)

            for face_index, face in enumerate(eval_mesh.polygons):
                # https://gist.github.com/andrewbolster/10274979
                np.random.seed(data_layer.rand_seed + (face_index + face_offset))
                phi = np.random.uniform(0,np.pi*2)
                costheta = np.random.uniform(-1,1)
                theta = np.arccos( costheta )

                if data_layer.component == "X":
                    data_to_bake = np.sin( theta) * np.cos( phi )
                elif data_layer.component == "Y":
                    data_to_bake = np.sin( theta) * np.sin( phi )
                elif data_layer.component == "Z":
                    data_to_bake = np.cos( theta )
                else:
                    data_to_bake = 0.0

                for loop_id in face.loop_indices:
                    data_loop_ids[loop_id] = data_to_bake

            face_offset += len(eval_mesh.polygons)

            if data_layer.ID not in eval_mesh.attributes:
                eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

            attr = eval_mesh.attributes[data_layer.ID]
            attr.data.foreach_set('value', data_loop_ids)

            bake_range_values.append(min(data_loop_ids))
            bake_range_values.append(max(data_loop_ids))
    else:
        return (False, "Unknown rand mode", None)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_value(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        data_to_bake = data_layer.x

        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)
    
    bake_range_values = [data_layer.x]
    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_custom_prop(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        if data_layer.obj:
            target = data_layer.obj
        else:
            target = eval_obj_to_bake.get("BakedSource", eval_obj_to_bake)

        prop = target.get(data_layer.name, None)
        if prop and ((type(prop) is int) or (type(prop) is float)):
            data_to_bake = prop
        else:
            data_to_bake = 0.0

        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(data_to_bake)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_frame(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    bake_ref_frame = context.scene.frame_current

    dgraph = context.evaluated_depsgraph_get()

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        data_loop_ids = [0.0] * len(eval_mesh.loops)
        target = get_data_layer_obj_source_obj(data_layer, eval_obj_to_bake)

        context.scene.frame_set(data_layer.index)
        #context.view_layer.update()

        eval_obj = target.evaluated_get(dgraph)
        eval_mesh_source = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        eval_mesh_source.transform(eval_obj.matrix_world)

        topology_mismatch  = len(eval_mesh.vertices) != len(eval_mesh_source.vertices)
        topology_mismatch |= len(eval_mesh.loops) != len(eval_mesh_source.loops)

        # fall back to nearest search method
        if topology_mismatch:
            bm = bmesh.new()
            bm.from_mesh(eval_mesh_source)

            BVH = BVHTree.FromBMesh(bm)

            for loop_id in eval_mesh.loops:
                vert_pos = eval_mesh.vertices[loop_id.vertex_index].co
                closest_face_pos, closest_face_nor, closest_face_index, closest_face_dist = BVH.find_nearest(vert_pos)

                if data_layer.vertex_mode == "OFFSET":
                    vector_to_bake = (vert_pos - closest_face_pos) * signed_scale
                else:
                    vector_to_bake = closest_face_nor.normalized() * signed_axis
                
                if settings.unit_axis_order != "XYZ":
                    vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                if data_layer.component == "X":
                    data_to_bake = vector_to_bake.x
                elif data_layer.component == "Y":
                    data_to_bake = vector_to_bake.y
                else:
                    data_to_bake = vector_to_bake.z

                data_loop_ids[loop_id.index] = data_to_bake

            bm.free()
        else:
            for loop_id in eval_mesh.loops:
                if data_layer.vertex_mode == "OFFSET":
                    vert_pos = eval_mesh.vertices[loop_id.vertex_index].co
                    ref_vert_pos = eval_mesh_source.vertices[loop_id.vertex_index].co
                    vector_to_bake = (ref_vert_pos - vert_pos) * signed_scale
                else:
                    vector_to_bake = eval_mesh_source.vertices[loop_id.vertex_index].normal.normalized() * signed_axis

                if settings.unit_axis_order != "XYZ":
                    vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

                if data_layer.component == "X":
                    data_to_bake = vector_to_bake.x
                elif data_layer.component == "Y":
                    data_to_bake = vector_to_bake.y
                else:
                    data_to_bake = vector_to_bake.z

                data_loop_ids[loop_id.index] = data_to_bake

        eval_obj.to_mesh_clear()

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(min(data_loop_ids))
        bake_range_values.append(max(data_loop_ids))

    # restore initial frame
    context.scene.frame_set(bake_ref_frame)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_hierarchy(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    bake_range_values = []

    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        depth = 0
        parent = eval_obj_to_bake.parent
        while parent:
            parent = parent.parent
            depth += 1

        data_to_bake = depth
        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        bake_range_values.append(data_to_bake)

    return (True, "", get_data_layer_range(bake_range_values))

def pre_bake_zeros(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, data_layer: object, eval_objs_to_bake: list) -> tuple[bool, str, float, float]:
    """
    Intermediate bake function to store the value in the meshes' face corner attributes

    This function bakes zeros and has two purpose
    1. fallback function in case get_data_layer_pre_bake_function() couldn't find the appropriate bake function for a given data layer
    2. template function to serve as an example to build your own

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param data_layer: data layer to bake
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :return: success, potential error message, range info
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    # mesh was evaluated & stored in a new object that has no animation. That object however has an object custom
    # property that points to the initial source mesh to still access the object's position etc.

    # to apply to unit vectors
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    # to apply to non-unit vectors such as positions etc.
    signed_scale = signed_axis * settings.unit_scale

    # for source mesh evaluation
    dgraph = bpy.context.evaluated_depsgraph_get()

    bake_range_values = []

    # iterate all duplicated meshes
    for eval_obj_to_bake in eval_objs_to_bake:
        eval_mesh = eval_obj_to_bake.data

        # get user-specified mesh override, else get source mesh
        if data_layer.obj:
            target = data_layer.obj
        else:
            target = eval_obj_to_bake.get("BakedSource", eval_obj_to_bake)

        # you might want to evaluate the source mesh as the duplicated mesh was itself evaluated. This ensures vertex count/order are similar
        #obj_eval = target.evaluated_get(dgraph)
        #mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        #mesh_eval.transform(obj_eval.matrix_world)

        # pre-allocate buffer
        #data_loop_ids = [0.0] * len(eval_mesh.loops)

        # you might want to iterate mesh loops, and access the corresponding vertices to bake values per loop indices
        #for loop_id in mesh_eval.loops:
            # example: get vertex position's X component
            #data_to_bake = mesh_eval.vertices[loop_id.vertex_index].co.x

            #data_loop_ids[loop_id.index] = data_to_bake

        # you might also want to bake the same value for all vertices, like the object's position
        #data_to_bake = some_value

        # which could instead be used to initialize the buffer
        #data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        # important to clear once you're done accessing the evaluated source mesh's data
        #obj_eval.to_mesh_clear()

        # bunch of zeros!
        data_to_bake = 0.0
        data_loop_ids = [data_to_bake] * len(eval_mesh.loops)

        # create face corner attributes for this layer, if needed
        if data_layer.ID not in eval_mesh.attributes:
            eval_mesh.attributes.new(name=data_layer.ID, type='FLOAT', domain='CORNER')

        # use buffer to set face corner attributes
        attr = eval_mesh.attributes[data_layer.ID]
        attr.data.foreach_set('value', data_loop_ids)

        # keep track of min/max
        #bake_range_values.append(min(data_loop_ids))
        #bake_range_values.append(max(data_loop_ids))

    return (False, "Unknown data layer mode", get_data_layer_range(bake_range_values))

##############
### MESHES ###
def export_mesh_selection(context: bpy.types.Context, bake_name: str) -> tuple[bool, str, str]:
    """
    Export the current selection to FBX

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        # export selection and assume selection was properly handled outside of this function
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

def generate_mesh_material_indices(eval_objs_to_bake: list) -> tuple[bool, str, list]:
    """
    Presume meshes are going to be merged to build a set of materials and update face material indices if required
    
    :param eval_objs_to_bake: 
    :return: the function's success, potential error message, list of materials once objects are merged
    :rtype: tuple
    """
    
    """
    build unique list of materials as if objects were merged
    """
    materials = []
    for eval_obj_to_bake in eval_objs_to_bake:
        for material in eval_obj_to_bake.data.materials:
            if material not in materials:
                materials.append(material)

    if len(materials) <= 0:
        return (True, "", None)

    """
    evaluate each object vertices' face material index and see if it points to the same index
    in list of materials built pre-processed above. If not, it needs to be updated. Reason may
    be simple:

    Mesh_A has one material named Mat_A, face material index is 0
    Mesh_B has one material named Mat_B, face material index is 1

    Once merged, Mesh_C, containing Mesh_A and Mesh_B, have two materials, yet all face material
    indices are 0, so some must be updated
    """
    for eval_obj_to_bake in eval_objs_to_bake:
        for poly in eval_obj_to_bake.data.polygons:
            try:
                material_source = eval_obj_to_bake.data.materials[poly.material_index]
            except:
                poly.material_index = 0
            
            try:
                material_index_source = poly.material_index
                material_index_merged = materials.index(material_source)
                if material_index_source != material_index_merged:
                    poly.material_index = material_index_merged
            except:
                poly.material_index = 0

    return (True, "", materials)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    report = context.scene.DataBakerReport

    root = ET.Element("BakedData",
                      type="Data",
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

    # data layers info
    if report.data_layers:
        data_layers_el = ET.SubElement(root, "Layers")
        for data_layer in report.data_layers:
            active_data_layers = [packed_data_layer for packed_data_layer in data_layer.packed_layers if packed_data_layer.ID == data_layer.active_layer_ID]
            if active_data_layers and len(active_data_layers) > 0:
                active_data_layer = active_data_layers[0]
                data_layer_el = ET.SubElement(data_layers_el, "Layer",
                                              name=get_data_layer_name(active_data_layer),
                                              range_offset=str(data_layer.range_offset),
                                              range=str(data_layer.range),
                                              range_valid=str(data_layer.range_valid),
                                              packing=active_data_layer.packing_mode,
                                              uv_index=str(active_data_layer.uv_index) if active_data_layer.packing_mode == "UV" else "",
                                              uv_channel=str(active_data_layer.uv_channel) if active_data_layer.packing_mode == "UV" else "",
                                              vcol_rgba=str(active_data_layer.vcol_rgba) if active_data_layer.packing_mode == "VCOL" else "",
                                              normal_xyz=str(active_data_layer.normal_xyz) if active_data_layer.packing_mode == "NORMAL" else "")

                for packed_data_layer_index, packed_data_layer in enumerate(data_layer.packed_layers):
                    packing_component = "X" if packed_data_layer_index == 0 else "Y" if packed_data_layer_index == "1" else "Z"
                    
                    if (packed_data_layer == active_data_layer):
                        packed_data_layer_el = ET.SubElement(data_layer_el, "Packed", component=packing_component, name="self")
                    else:
                        packed_data_layer_el = ET.SubElement(data_layer_el, "Packed", component=packing_component, name=get_data_layer_name(packed_data_layer))

    # mesh info
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""

    mesh_el = ET.SubElement(root, "Mesh", path=mesh_export_path)

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