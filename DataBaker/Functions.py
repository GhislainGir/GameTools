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
from ctypes import POINTER, pointer, c_int, cast, c_float

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
    add_bake_report("unit_scale", settings.scale)
    add_bake_report("unit_invert_x", settings.invert_x)
    add_bake_report("unit_invert_y", settings.invert_y)
    add_bake_report("unit_invert_z", settings.invert_z)

    add_bake_report("world_obj", settings.world_obj)
    
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

    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_uvmap_invert_v = False

    report.meshes_count = 0
    report.empties_count = 0

    report.xml = False
    report.xml_path = ""

    report.world_obj = None

    report.mesh_name = ""
    report.scale = 0.0
    report.invert_x = False
    report.invert_y = False
    report.invert_z = False

    report.export_mesh = False
    report.export_mesh_file_name = ""
    report.export_mesh_file_path = ""
    report.export_mesh_file_override = False

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """
    Set a value in the bake report

    :param prop_name: report property to set
    :param prop_value: value to assign to the property
    :return: None
    :rtype: None
    """
    setattr(bpy.context.scene.DataBakerReport, prop_name, prop_value)

def add_bake_layer_report(data_layer, packing, pack_range):
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

    pack_min, pack_max = pack_range

    for layer_packed_index, layer_packed in enumerate(packing):
        if layer_packed:
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

    report_data_layer.range_min = pack_min
    report_data_layer.range_max = pack_max

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
def get_packed_11_10_10_xyz(x: float, y: float, z:float, range_min: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0)), range_max: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0))) -> float:  
    """ 
    Algorithm to pack three floats into one, using 11, 10 and 10 bits of precision while preventing NaNs.

    32bit float NaNs are encoded with the exponent field filled with ones (like infinity values).
      SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
    > S11111111MMMMMMMMMMMMMMMMMMMMMMM = NAN

    We'd like to pack the three floats ideally using 11, 11 and 10 bits of precision, totalling 32 bits.
    We may however only use 31 bits and split the bits of the first float into two groups of bits, as to
    ensure the exponent field isn't filled with ones, thus using 11, 10 and 10 bits of precision.
    
    > XXXXXXX0XXXXYYYYYYYYYYZZZZZZZZZZ

    :param x: first float to pack
    :param y: second float to pack
    :param z: third float to pack
    :param range_min: XYZ vector to remap the 'x', 'y' and 'z' floats to the range [0:1]. range_max - range_min is assumed to be non-zero!
    :param range_max: XYZ vector to remap the 'x', 'y' and 'z' floats to the range [0:1]. range_max - range_min is assumed to be non-zero!
    :return: bit-packed float
    :rtype: float
    """

    bitstring_a = str(bin(math.floor((((min(1.0, max(0.0, (x-range_min.x) / (range_max.x - range_min.x)))) + 1) * 0.5) * (1<<10))))
    bitstring_a = bitstring_a[2:] # get rid of 0b
    bitstring_a = bitstring_a.zfill(11) # ensure it's 11 char long

    bitstring_a_a = bitstring_a[:8] # get first 8 characters
    bitstring_a_b = bitstring_a[-3:] # get last 3 characters
    bitstring_a = bitstring_a_a + "0" + bitstring_a_b # reconstruct 10 bits integer with last exponent bit as 0 to prevent NaNs

    bitstring_b = str(bin(math.floor((((min(1.0, max(0.0, (y-range_min.y) / (range_max.y - range_min.y)))) + 1) * 0.5) * (1<<10))))
    bitstring_b = bitstring_b[2:] # get rid of 0b
    bitstring_b = bitstring_b.zfill(10) # ensure it's 11 char long

    bitstring_c = str(bin(math.floor((((min(1.0, max(0.0, (z-range_min.z) / (range_max.z - range_min.z)))) + 1) * 0.5) * (1<<9))))
    bitstring_c = bitstring_c[2:] # get rid of 0b
    bitstring_c = bitstring_c.zfill(10) # ensure it's 10 char long

    bits_string = "0b" + bitstring_a + bitstring_b + bitstring_c

    cp = pointer(c_int(int(bits_string, 0)))
    fp = cast(cp, POINTER(c_float))
    return fp.contents.value

def get_packed_16_15_xy(x: float, y: float, range_min: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0)), range_max: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0))) -> float:
    """ 
    Algorithm to pack two floats into one, using 15 and 16 bits of precision while preventing NaNs.

    32bit float NaNs are encoded with the exponent field filled with ones (like infinity values).
      SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
    > S11111111MMMMMMMMMMMMMMMMMMMMMMM = NAN

    We'd like to pack two 16 bits value (x,y) into the 32 bits of the float but we may only pack a
    16-bit and 15-bit values and split the first 16 bits into two groups of bits, as to ensure the
    exponent field isn't filled with ones.

    > XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY

    range_max - range_min is assumed to be non-zero

    :param x: first float to pack
    :param y: second float to pack
    :param range_min: XY0 vector to remap the 'x' and 'y' floats to the range [0:1]. range_max - range_min is assumed to be non-zero!
    :param range_max: XY0 vector to remap the 'x' and 'y' floats to the range [0:1]. range_max - range_min is assumed to be non-zero!
    :return: bit-packed float
    :rtype: float
    """
    a = min(1.0, max(0.0, (x - range_min.x) / (range_max.x - range_min.x)))
    bitstring_a = str(bin(math.floor(a * ((1 << 16) - 1))))
    bitstring_a = bitstring_a[2:] # get rid of '0b'
    bitstring_a = bitstring_a.zfill(16) # ensure it's 15 char long

    bitstring_a_a = bitstring_a[:8] # get first 8 characters
    bitstring_a_b = bitstring_a[-8:] # get last 7 characters
    bitstring_a = bitstring_a_a + "0" + bitstring_a_b # use 17 bits integer with last exponent bit as 0 to prevent NaNs

    b = min(1.0, max(0.0, (y - range_min.y) / (range_max.y - range_min.y)))
    bitstring_b = str(bin(math.floor(b * ((1 << 15) - 1))))
    bitstring_b = bitstring_b[2:] # get rid of '0b'
    bitstring_b = bitstring_b.zfill(15) # ensure it's 16 char long

    bits_string = "0b" + bitstring_a + bitstring_b

    cp = pointer(c_int(int(bits_string, 0)))
    fp = cast(cp, POINTER(c_float))
    return fp.contents.value

def get_packed_frac(x: float, y: float, y_range_min: float = 0.0, y_range_max: float = 1.0, precision: float = 0.99) -> float:
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
    :param y_range_min: float to remap the 'y' float to the range [0:1]. y_range_max - y_range_min is assumed to be non-zero!
    :param y_range_max: float to remap the 'y' float to the range [0:1]. y_range_max - y_range_min is assumed to be non-zero!
    :return: frac-packed float
    :rtype: float
    """
    prec = min(0.999, max(0.001, precision))

    y = (y - y_range_min) / (y_range_max - y_range_min)
    y = min(1.0, max(0.0, y * prec)) # remap frac to [0:<1]
    return  math.floor(x) + y

def get_normalized(x: float, range_min: float, range_max: float, default: float = 1.0, default_threshold: float = 0.0001):
    """
    Remap a float to the range [0:1].

    If (range_max - range_min) is too close to the 'default_threshold', the function returns the 'default' value instead

    :param x: float to remap
    :param range_min: float used to remap the given float to the range [0:1]
    :param range_max: float used to remap the given float to the range [0:1]
    :param default: default value to return if range_max - range_min is too close to zero
    :param default_threshold: how close range_max - range_min has to be for the function to return the default value instead
    """
    return ((x - range_min)/ (range_max - range_min) if abs(range_max - range_min) > default_threshold else default)

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
        if selected_obj.type != "MESH" and selected_obj.type != "EMPTY":
            selected_obj.select_set(False)
        elif selected_obj.type == "MESH" and len(selected_obj.data.vertices) <= 0: # mesh could have no vertices
            selected_obj.select_set(False)

    objs_to_bake = context.selected_objects # cache selection
    if objs_to_bake and len(objs_to_bake) <= 0:
        return (False, "No mesh or empty to bake once filtered out", None, None)

    active_obj = context.view_layer.objects.active

    if settings.invert_v:
        add_bake_report("mesh_uvmap_invert_v", True)

    # blank canvas
    for obj in objs_to_bake:
        obj.select_set(False)

    context.view_layer.objects.active = None

    return (True, "", objs_to_bake, active_obj)

def get_bake_name(context: bpy.types.Context, active_object:bpy.types.Object) -> str:
    """
    Return the name to give to the mesh to generate.

    :param context: Blender current execution context
    :param active_object: object to derive name from
    :return: the bake operation's 'name'
    :rtype: str
    """

    settings = context.scene.DataBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.Data"
    tags = { "ObjectName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def pre_process_bake_selection(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, list, list]:
    """
    Generate and return a copy of all depsgraph-evaluated meshes and empties to be included in the bake

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to generate duplicates from
    :return: the function's success, potential error message, list of duplicated mesh objects to include in the bake, list of duplicated empty objects to include in the bake
    :rtype: tuple
    """

    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    dgraph = bpy.context.evaluated_depsgraph_get()

    duped_objs = []
    for obj_to_bake in objs_to_bake:
        col = context.scene.collection
        if obj_to_bake.users_collection and len(obj_to_bake.users_collection) > 0:
            col = obj_to_bake.users_collection[0]

        if obj_to_bake.type == "MESH":
            eval_obj = obj_to_bake.evaluated_get(dgraph)
            eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

            if eval_obj.parent:
                eval_mesh.transform(eval_obj.parent.matrix_world.inverted() @ eval_obj.matrix_world)
            else:
                eval_mesh.transform(eval_obj.matrix_world)

            duped_obj = bpy.data.objects.new(obj_to_bake.name + ".baked", eval_mesh)
        elif obj_to_bake.type == "EMPTY": # @NOTE legacy method of including empties in the objects to duplicate. Probably need a refactor at some point
            duped_obj = bpy.data.objects.new(obj_to_bake.name + ".baked", object_data=None)

            if obj_to_bake.parent:
                duped_obj.matrix_world = obj_to_bake.parent.matrix_world.inverted() @ obj_to_bake.matrix_world.copy()
            else:
                duped_obj.matrix_world = obj_to_bake.matrix_world.copy()

            duped_obj.empty_display_type = obj_to_bake.empty_display_type
            duped_obj.empty_display_size = obj_to_bake.empty_display_size
        else: # shouldn't encounter any other object type at this point, thanks to the get_bake_selection call filtering out selected objects
            continue

        duped_obj.parent = obj_to_bake.parent

        for key in obj_to_bake.keys():
            if key != "_RNA_UI":
                duped_obj[key] = obj_to_bake[key]

        # create pairing with original obj
        duped_obj[custom_prop] = obj_to_bake
        duped_obj.id_properties_ensure()
        property_manager = duped_obj.id_properties_ui(custom_prop)
        property_manager.update(id_type="OBJECT") # @NOTE dirty hack to prevent weird UI bug

        col.objects.link(duped_obj)
        duped_objs.append(duped_obj)

    context.view_layer.objects.active = objs_to_bake[0]

    # loop through all *newly* selected objects that we may have duplicated and build list of all meshes and empties for later cleaning process
    meshes = [obj for obj in duped_objs if obj.type == "MESH"]
    add_bake_report("meshes_count", len(meshes))
    empties = [obj for obj in duped_objs if obj.type == "EMPTY"]
    add_bake_report("empties_count", len(empties))

    return (True, "", meshes, empties)

def post_process_bake_selection(context: bpy.types.Context, meshes: list, empties: list) -> tuple[bool, str]:
    """
    Merge duplicated meshes that were part of the bake and clean duplicated empties, if any

    :param context: Blender current execution context
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: the function's success and potential error message
    :rtype: tuple
    """

    settings = context.scene.DataBakerSettings
    
    dgraph = bpy.context.evaluated_depsgraph_get()

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.Data"
    
    # create a new mesh to 'merge' all duplicated meshes
    merged_mesh = bpy.data.meshes.new(name)
    
    bm = bmesh.new()
    for mesh in meshes:
        obj_eval = mesh.evaluated_get(dgraph)
        mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        mesh_eval.transform(obj_eval.matrix_world)

        bm.from_mesh(mesh_eval)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        obj_eval.to_mesh_clear()

    bm.to_mesh(merged_mesh)
    bm.free()

    # create a new object from the new mesh
    obj = bpy.data.objects.new(name, merged_mesh)
    context.scene.collection.objects.link(obj)

    add_bake_report("mesh", obj)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # delete duplicated empties
    for empty in empties:
        bpy.data.objects.remove(empty)

    # delete duplicated meshes
    for mesh in meshes:
        bpy.data.objects.remove(mesh)

    return (True, "")

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    bpy.ops.object.mode_set(mode="OBJECT") # @TODO is this necessary?

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

    success, msg, meshes, empties = pre_process_bake_selection(context, objs_to_bake)
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

    success, msg = bake_data(context, layers_info, meshes, empties)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    ########
    # MESH #

    success, msg = post_process_bake_selection(context, meshes, empties)
    if not success:
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

def bake_data(context, layers_info, meshes, empties) -> tuple[bool, str]:
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
    :param meshes: list of duplicated meshes to include in the bake
    :param empties: list of duplicated empties to include in the bake
    :return: the function's success and potential error message
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings

    for data_layer, layer_info in layers_info:
        """
        1. First, we unpack layer_info and see if we should continue.

        to_bake: layer might be packed into another layer. If so, we just skip and wait for said layer to be processed

        packing_mode: layer might be baked in say, UVs, but might be required to pack other layers using FRACTION, XY
        or XYZ packing mode which is what this value tells

        packing: layer tuple (a, b, c). These are the layers to be baked and packed within one of them three. We don't
        know which one to pack into and we don't care, at least in this function. At least one data_layer should be
        valid, the rest may be None and possibly not in order: b could be None whereas c could be valid.
        """
        to_bake, packing_mode, packing = layer_info
        if not to_bake:
            continue

        """ 
        Bit-packing might be used to pack multiple layers into one. This requires to remap values to the range [0:1]
        using the min & max values to bake, per component, need to be known. This is computed further below and has
        to be shared across all meshes.
        """
        pack_min = mathutils.Vector((0.0, 0.0, 0.0))
        pack_max = mathutils.Vector((0.0, 0.0, 0.0))

        """
        2. Second, the goal is to call the appropriate bake function for each valid layer and gather the list values to
        bake for each loop_id for each polygon for each mesh, as well as the min-max range of values. While doing so
        we double check that each layer processed the same amount of meshes. Order is *assumed* to be identical since
        there's no reason for it to be different except if a bake function was wrongly implemented. While iterating
        layers, we also gather the min & values values to bake, per component. A position's X component might be
        packed along with a linear gradient already in a [0:1] range, so each component may benefit from using their
        own min-max range to be brought back into a [0:1] range

        layer_data: tuple (mesh, [values])
        layer_data_range: tuple (min, max)
        """
        layers_data = [] # assuming packing is a tuple of three layers, this list *will* contain three tuples as well
        num_meshes = -1
        meshes_to_bake = []
        for layer_packed_index, layer_packed in enumerate(packing):
            if layer_packed:
                layer_func = get_data_layer_bake_function(layer_packed)
                if layer_func:
                    layer_data, layer_data_range = layer_func(context, layer_packed, meshes, empties)

                    if num_meshes < 0:
                        num_meshes = len(layer_data)
                    elif num_meshes != len(layer_data):
                        return (False, "Inconsistent amount of baked meshes for data layer '" + get_data_layer_name(layer_packed) + "'")

                    if layer_packed_index == 0: # x
                        pack_min.x = layer_data_range[0]
                        pack_max.x = layer_data_range[1]
                    elif layer_packed_index == 1: # y
                        pack_min.y = layer_data_range[0]
                        pack_max.y = layer_data_range[1]
                    else: # 2 or z
                        pack_min.z = layer_data_range[0]
                        pack_max.z = layer_data_range[1]

                    for data_index, data in enumerate(layer_data):
                        """ """
                        mesh, values = data
                        if data_index < len(meshes_to_bake):
                            if mesh != meshes_to_bake[data_index][0]:
                                return (False, "Mesh list differs for data layer '" + get_data_layer_name(layer_data) + "'")
                            elif len(values) != meshes_to_bake[data_index][1]:
                                return (False, "Inconsistent amount of loop indices registered for data layer '" + get_data_layer_name(layer_data) + "'")
                        else:
                            meshes_to_bake.append((mesh, len(values)))
                else:
                    return (False, "Function for data layer '" + get_data_layer_name(layer_packed) + "' couldn't be found")
            else:
                layer_data = None

            layers_data.append(layer_data)

        """
        We want to prevent a potential div by zero further below (we might bake a single object's position, making min == max)
        @NOTE find a more elegant solution that don't rely on arbitrary precision?
        """
        if abs(pack_max.x - pack_min.x) < 0.00001:
            pack_max.x = 1.0
            pack_min.x = 0.0
        if abs(pack_max.y - pack_min.y) < 0.00001:
            pack_max.y = 1.0
            pack_min.y = 0.0
        if abs(pack_max.z - pack_min.z) < 0.00001:
            pack_max.z = 1.0
            pack_min.z = 0.0

        """
        3. Third, we ensured that each layer processed the same amount of meshes, so we simply iterate meshes by index. For each
        we gather the values to bake per layer. While doing so, we also double check that the number of values to bake is similar
        for all layers, as well as the object to bake at that index.

        There might only be one layer, thus one single list of values to bake, but layers might be asked to pack other layers so we may need to stack lists.
        """
        for mesh_index, mesh_info in enumerate(meshes_to_bake):
            progress = mesh_index / max(1, (len(meshes_to_bake) - 1))
            bpy.context.window_manager.progress_update((progress * 80) + 10)

            mesh, num_values = mesh_info
            values_to_pack = np.stack((
                np.array(np.zeros(num_values, dtype=float) if layers_data[0] is None else layers_data[0][mesh_index][1]),
                np.array(np.zeros(num_values, dtype=float) if layers_data[1] is None else layers_data[1][mesh_index][1]),
                np.array(np.zeros(num_values, dtype=float) if layers_data[2] is None else layers_data[2][mesh_index][1])),
                axis=-1)

            if data_layer.packing_mode == "UV":
                while (data_layer.uv_index > (len(mesh.data.uv_layers) - 1)):
                    mesh.data.uv_layers.new()

                    zero_uv = (0.0, 1.0 if settings.invert_v else 0.0)
                    for face in mesh.data.polygons:
                        for loop_id in face.loop_indices:
                            mesh.data.uv_layers[data_layer.uv_index].data[loop_id].uv = zero_uv

                uv_name = settings.uvmap_name if settings.uvmap_name != "" else "UVMap.BakedData"
                uv_name += "." + str(data_layer.uv_index)
                mesh.data.uv_layers[data_layer.uv_index].name = uv_name

                if data_layer.uv_channel == "U":
                    index = 0
                    invert_v = False
                else:
                    index = 1
                    invert_v = settings.invert_v

                for face in mesh.data.polygons:
                    for loop_id in face.loop_indices:
                        x = 0.0
                        if packing_mode == "XYZ":
                            x = get_packed_11_10_10_xyz(values_to_pack[loop_id][0], values_to_pack[loop_id][1], values_to_pack[loop_id][2], pack_min, pack_max)
                        elif packing_mode == "XY":
                            x = get_packed_16_15_xy(values_to_pack[loop_id][0], values_to_pack[loop_id][1], pack_min, pack_max)
                        elif packing_mode == "FRACTION":
                            x = get_packed_frac(values_to_pack[loop_id][0], values_to_pack[loop_id][1], pack_min.x, pack_max.x, data_layer.packing_precision)
                        else:
                            x = values_to_pack[loop_id][0]

                        mesh.data.uv_layers[data_layer.uv_index].data[loop_id].uv[index] = (1.0 - x) if invert_v else x
            elif data_layer.packing_mode == "VCOL":
                if mesh.data.vertex_colors:
                    vcol = mesh.data.vertex_colors.active
                else:
                    vcol = mesh.data.vertex_colors.new()

                    for face in mesh.data.polygons:
                        for loop_id in face.loop_indices:
                            vcol.data[loop_id].color = [0.0, 0.0, 0.0, 0.0]

                for face in mesh.data.polygons:
                    for loop_id in face.loop_indices:
                        if data_layer.vcol_rgba == "R":
                            vcol.data[loop_id].color[0] = get_normalized(values_to_pack[loop_id][0], pack_min, pack_max)
                        elif data_layer.vcol_rgba == "G":
                            vcol.data[loop_id].color[1] = get_normalized(values_to_pack[loop_id][0], pack_min, pack_max)
                        elif data_layer.vcol_rgba == "B":
                            vcol.data[loop_id].color[2] = get_normalized(values_to_pack[loop_id][0], pack_min, pack_max)
                        elif data_layer.vcol_rgba == "A":
                            vcol.data[loop_id].color[3] = get_normalized(values_to_pack[loop_id][0], pack_min, pack_max)
            elif data_layer.packing_mode == "NORMAL":
                normals = [loop.normal.copy() for loop in mesh.data.loops]

                for face in mesh.data.polygons:
                    face.use_smooth = True
                    for loop_id in face.loop_indices:
                        x = values_to_pack[loop_id][0]

                        if data_layer.normal_xyz == "X":
                            normals[loop_id].x = x # @TODO remap to [-1:1] # @TODO fix needing smooth faces?
                        elif data_layer.normal_xyz == "Y":
                            normals[loop_id].y = x
                        else: #z
                            normals[loop_id].z = x

                mesh.data.normals_split_custom_set(normals)
            else:
                pass

        add_bake_layer_report(data_layer, packing, (pack_min, pack_max))

    return (True, "")

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
    targeting = data_layer.packing_mode == "FRACTION" or data_layer.packing_mode == "XY" or data_layer.packing_mode == "XYZ"
    if targeting:
        success, msg, data_layer_target = get_data_layer_targeting_info(data_layer, data_layers)
        if not success:
            return (False, err_base_msg + msg, None)

        # gather sibling(s) (aka, all layers that have the same target than us, including us)
        layers_sharing_target = [layer for layer in data_layers if layer.ptr_ID == data_layer_target.ID]
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

        # gather child(s) (aka, all layers that *may* target us)
        layers_targeting_self = [layer for layer in data_layers if layer.ptr_ID == data_layer.ID]
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
    # check that we're not asking to be packed into another layer while other layers are asking us to pack them
    layers_targeting_self = [layer for layer in data_layers if layer.ptr_ID == data_layer.ID]
    if len(layers_targeting_self) > 0:
        return (False, "layer is itself targeted by other layers", None)

    # check ptr ID isn't empty
    if data_layer.ptr_ID == "":
        return (False, "no target specified", None)
    # make sure ptr ID isn't self ID
    if data_layer.ptr_ID == data_layer.ID:
        return (False, "targeting itself (ID)", None)

    # gather target(s)
    data_layer_targets = [target_data_layer for target_data_layer in data_layers if target_data_layer.ID == data_layer.ptr_ID]
    if data_layer_targets:
        # finding multiple targets is wrong!
        if len(data_layer_targets) > 1:
            return (False, "multiple targets found", None)
        data_layer_target = data_layer_targets[0]
        # make sure we haven't found self
        if data_layer == data_layer_target:
            return (False, "targeting itself (Layer)", None)
        # make sure target's storage mode allow bit-packing
        mode = data_layer_target.packing_mode
        if mode == "FRACTION" or mode == "XY" or mode == "XYZ" or mode == "VCOL" or mode == "NORMAL":
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
        vcol_components = []
        for data_layer in data_layers:
            if data_layer.packing_mode == "VCOL":
                if (data_layer.vcol_rgba in vcol_components):
                    return (False, data_layer.vcol_rgba + " already targeted")
                else:
                    vcol_components.append(data_layer.vcol_rgba)
    # check if targeted NORMAL XYZ component is free
    elif data_layer.packing_mode == "NORMAL":
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

        if packing_mode == "FRACTION" or (packing_mode == "XY" and data_layer_to_pack.pack_xy == "X") or (packing_mode == "XYZ" and data_layer_to_pack.pack_xyz == "X"):
            if len(layers_packed_in_x) > 0:
                return (False, "multiple layers targeting component X", "", None)
            else:
                layers_packed_in_x.append(data_layer_to_pack)
        elif (packing_mode == "XY" and data_layer_to_pack.pack_xy == "Y") or (packing_mode == "XYZ" and data_layer_to_pack.pack_xyz == "Y"):
            if len(layers_packed_in_y) > 0:
                return (False, "multiple layers targeting component Y", "", None)
            else:
                layers_packed_in_y.append(data_layer_to_pack)
        elif (packing_mode == "XYZ" and data_layer_to_pack.pack_xyz == "Z"):
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
            return "Position " + data_layer.component
        elif data_layer.data == "AXIS":
            return "Axis " + data_layer.component
        elif data_layer.data == "SHAPEKEY":
            if data_layer.vertex_mode == "OFFSET":
                return "Shapekey Offset " + data_layer.component
            elif data_layer.vertex_mode == "NORMAL":
                return "Shapekey Normal " + data_layer.component
            else:
                pass
        elif data_layer.data == "MASK":
            if data_layer.mask_mode == "SPHERE":
                return "Mask Sphere"
            elif data_layer.mask_mode == "LINEAR":
                return "Mask Linear " + data_layer.axis
        elif data_layer.data == "RANDOM":
            if data_layer.rand_mode == "COLLECTION":
                return "Random Per Col " + data_layer.component
            elif data_layer.rand_mode == "OBJECT":
                return "Random Per Obj " + data_layer.component
            elif data_layer.rand_mode == "FACE":
                return "Random Per Face " + data_layer.component
            else:
                pass
        elif data_layer.data == "PARENT_POS":
            return "Parent " + str(data_layer.index) + " Pos " + data_layer.component
        elif data_layer.data == "PARENT_AXIS":
            return "Parent " + str(data_layer.index) + " Axis " + data_layer.component
        elif data_layer.data == "VALUE":
            return "Value"
        elif data_layer.data == "CUSTOM_PROP":
            if data_layer.name == "":
                return "Invalid Custom Prop"
            else:
                return data_layer.name
        elif data_layer.data == "FRAME":
            if data_layer.vertex_mode == "OFFSET":
                return "Frame " + str(data_layer.index) + " Offset " + data_layer.component
            else: #normal
                return "Frame " + str(data_layer.index) + " Normal " + data_layer.component
        else:
            pass

    return "UNKNOWN"

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
                if data_layer.ptr_ID == "":
                    return (False, "QUESTION")

                if data_layer.packing_mode == "XY":
                    return (False, "OVERLAY")
                elif data_layer.packing_mode == "XYZ":
                    return (False, "THREE_DOTS")
                elif data_layer.packing_mode == "FRACTION":
                    return (False, "PIVOT_ACTIVE")
                else:
                    pass

            return (False, "COPYDOWN")

    return (False, "X")

def get_data_layer_bake_function(data_layer: object):
    """
    Return the bake function associated with the given data layer

    :param data_layer: data layer to get bake function for
    :return: the bake function to call for the given data layer
    :rtype: callable function
    """
    if data_layer:
        if data_layer.data == "POSITION" :
            return get_bake_position
        elif data_layer.data == "AXIS":
            return get_bake_axis
        elif data_layer.data == "SHAPEKEY":
            return get_bake_shapekey
        elif data_layer.data == "MASK":
            return get_bake_mask
        elif data_layer.data == "RANDOM":
            return get_bake_random
        elif data_layer.data == "PARENT_POS":
            return get_bake_parent_pos
        elif data_layer.data == "PARENT_AXIS":
            return get_bake_parent_axis
        elif data_layer.data == "VALUE":
            return get_bake_value
        elif data_layer.data == "CUSTOM_PROP":
            return get_bake_custom_prop
        elif data_layer.data == "FRAME":
            return get_bake_frame
        else:
            return get_bake_none
    
    return get_bake_none

######################
### BAKE FUNCTIONS ###
def get_bake_position(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> tuple[list, tuple[float, float]]:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale
    
    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []

        obj = mesh.get(custom_prop, mesh)
        obj_mat = obj.matrix_world
        if settings.world_obj:
            obj_mat = obj_mat @ settings.world_obj.matrix_world.inverted # relative to world obj
        obj_loc = obj_mat.to_translation()

        vector_to_bake = obj_loc * signed_scale

        if data_layer.component == "X":
            data_to_bake = vector_to_bake.x
        elif data_layer.component == "Y":
            data_to_bake = vector_to_bake.y
        elif data_layer.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_loop_ids.append(data_to_bake)

        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_axis(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    
    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []
        
        obj = mesh.get(custom_prop, mesh)
        obj_mat = obj.matrix_world
        if settings.world_obj:
            obj_mat = obj_mat @ settings.world_obj.matrix_world.inverted # relative to world obj

        obj_quat = obj_mat.to_quaternion()

        if data_layer.axis == "X":
            axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif data_layer.axis == "Y":
            axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif data_layer.axis == "Z":
            axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            axis = mathutils.Vector((0.0, 0.0, 0.0))

        vector_to_bake = (obj_quat @ (axis * signed_axis))

        if data_layer.component == "X":
            data_to_bake = vector_to_bake.x
        elif data_layer.component == "Y":
            data_to_bake = vector_to_bake.y
        elif data_layer.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_loop_ids.append(data_to_bake)
        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_shapekey(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    # @TODO check that it is working & rework way shapekeys offset & normal are computed
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False
    
    for mesh in meshes:
        data_loop_ids = []

        obj = mesh.get(custom_prop, mesh)

        if obj.data.shape_keys:
            # cache & reset all shape keys
            initial_shape_keys = []
            for shape_key in obj.data.shape_keys.key_blocks:
                initial_shape_keys.append((shape_key.name, shape_key.value))
                shape_key.value = 0.0

            # enable shape key to bake
            if data_layer.name in obj.data.shape_keys.key_blocks:
                obj.data.shape_keys.key_blocks[settings.name].value = 1.0

            # cache posed vertices
            dgraph = context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(dgraph)
            mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            mesh_eval.transform(obj_eval.matrix_world)
            vertices_posed = [vertex.copy() for vertex in mesh_eval.vertices]
            obj_eval.to_mesh_clear()

            # disable shape key to bake
            if data_layer.name in obj.data.shape_keys.key_blocks:
                obj.data.shape_keys.key_blocks[settings.name].value = 0.0

            # cache rest vertices
            dgraph = context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(dgraph)
            mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            mesh_eval.transform(obj_eval.matrix_world)
            vertices_rest = [vertex.copy() for vertex in mesh_eval.vertices]
            obj_eval.to_mesh_clear()

            # restore shapekeys
            for shape_key_name, shape_key_value in initial_shape_keys:
                obj.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value 

            # compute shape key value to bake
            for face in mesh_eval.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = mesh_eval.data.loops[loop_id].vertex_index

                    if data_layer.vertex_mode == "OFFSET":
                        vector_to_bake = (vertices_posed[vertex_index].co - vertices_rest[vertex_index].co) * signed_scale
                    elif data_layer.vertex_mode == "NORMAL":
                        vector_to_bake = vertices_posed[vertex_index].normal * signed_axis
                    else:
                        vector_to_bake = mathutils.Vector((0.0, 0.0, 0.0))

                    if data_layer.component == "X":
                        data_to_bake = vector_to_bake.x
                    elif data_layer.component == "Y":
                        data_to_bake = vector_to_bake.y
                    elif data_layer.component == "Z":
                        data_to_bake = vector_to_bake.z
                    else:
                        pass

                    data_loop_ids.append(data_to_bake)
        else:
            for face in obj.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(0.0) # fallback to 0 if no shapekey

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, min(data_loop_ids))
        else:
            bake_data_min_set = True
            bake_data_min = min(data_loop_ids)

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, max(data_loop_ids))
        else:
            bake_data_max_set = True
            bake_data_max = max(data_loop_ids)
        
        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_mask(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

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
        return get_bake_mask_sphere(data_layer, meshes, empties, custom_prop, origin_mode, signed_scale)
    elif data_layer.mask_mode == "LINEAR":            
        if data_layer.axis == "X":
            world_axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif data_layer.axis == "Y":
            world_axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif data_layer.axis == "Z":
            world_axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            world_axis = mathutils.Vector((0.0, 0.0, 0.0))

        if settings.world_obj:
            world_axis = settings.world_obj.matrix_world.to_quaternion() @ world_axis # relative to world obj

        return get_bake_mask_linear(data_layer, meshes, empties, custom_prop, origin_mode, signed_scale, world_axis)
    else:
        return (None, (0.0, 0.0))

def get_bake_mask_sphere(data_layer: object, meshes: list, empties: list, custom_prop: str, origin_mode: str="WORLD", signed_scale: mathutils.Vector=mathutils.Vector((1.0, 1.0, 1.0))) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
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
        for mesh in meshes:
            averaged_pos += mesh.matrix_world.to_translation()
        mask_origin_pos = averaged_pos / max(len(meshes), 1)
        mask_global = True

    # if 'global', iterate all meshes to get max distance relative to sphere mask origin
    if mask_global:
        verts = []
        for mesh in meshes:
            obj = mesh.get(custom_prop, mesh)

            for face in obj.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = obj.data.loops[loop_id].vertex_index

                    vertex_offset = (obj.matrix_world @ obj.data.vertices[vertex_index].co) - mask_origin_pos
                    verts.append(vertex_offset.length)

        min_dist = min(verts)
        max_dist = max(verts)
        length = max_dist - min_dist
        inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
        min_dist = min_dist if length > 0.0001 else 0.0

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []

        obj = mesh.get(custom_prop, mesh)
        
        # if 'local', get sphere mask origin per object
        if not mask_global:
            verts = [] # reset per mesh

            if origin_mode == "OBJECT":
                target = obj
            elif origin_mode == "PARENT":
                if obj.parent:
                    target = obj.parent
                else:
                    target = obj
            else:
                target = None

            if target:
                mask_origin_pos = target.matrix_world.to_translation()

                # iterate all meshes to get max distance relative to 'local' sphere mask origin 
                for face in obj.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = obj.data.loops[loop_id].vertex_index
                        vertex_offset = (obj.matrix_world @ obj.data.vertices[vertex_index].co) - mask_origin_pos

                        verts.append(vertex_offset.length)

            min_dist = min(verts)
            max_dist = max(verts)
            length = max_dist - min_dist
            inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
            min_dist = min_dist if length > 0.0001 else 0.0

        # compute sphere mask
        for face in obj.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = obj.data.loops[loop_id].vertex_index
                vertex_offset = (obj.matrix_world @ obj.data.vertices[vertex_index].co) - mask_origin_pos

                data_to_bake = vertex_offset.length

                if data_layer.normalize:
                    data_to_bake -= min_dist
                    data_to_bake *= inv_length

                if data_layer.clamp:
                    data_to_bake = max(0.0, min(1.0, data_to_bake))

                if data_layer.normalize or data_layer.clamp:
                    data_to_bake = math.pow(data_to_bake, data_layer.falloff)

                data_loop_ids.append(data_to_bake)

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, min(data_loop_ids))
        else:
            bake_data_min_set = True
            bake_data_min = min(data_loop_ids)

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, max(data_loop_ids))
        else:
            bake_data_max_set = True
            bake_data_max = max(data_loop_ids)

        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_mask_linear(data_layer: object, meshes: list, empties: list, custom_prop: str, origin_mode: str="WORLD", signed_scale: mathutils.Vector=mathutils.Vector((1.0, 1.0, 1.0)), world_axis: mathutils.Vector=mathutils.Vector((0.0, 0.0, 1.0))) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
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

        if data_layer.axis_mode == "CUSTOM" and data_layer.axis_obj:
            mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
        elif data_layer.axis_mode == "LOCAL":
            mask_origin_axis = data_layer.obj.matrix_world.to_quaternion() @ world_axis
        else:
            pass # WORLD
    elif origin_mode == "SELECTION":
        averaged_pos = mathutils.Vector((0.0, 0.0, 0.0))
        for mesh in meshes:
            obj = mesh.get(custom_prop, mesh)

            averaged_pos += obj.matrix_world.to_translation()
        mask_origin_pos = averaged_pos / max(len(meshes), 1)
        mask_origin_axis = world_axis
        mask_global = True

    # if 'global', iterate all meshes to get max distance relative to linear mask origin
    if mask_global:
        verts = []
        for mesh in meshes:
            obj = mesh.get(custom_prop, mesh)

            for face in obj.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = obj.data.loops[loop_id].vertex_index

                    vertex_offset = (obj.matrix_world @ obj.data.vertices[vertex_index].co) - mask_origin_pos
                    verts.append(vertex_offset.dot(mask_origin_axis))

        min_dist = min(verts)
        max_dist = max(verts)
        length = max_dist - min_dist
        inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
        min_dist = min_dist if length > 0.0001 else 0.0

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []

        obj = mesh.get(custom_prop, mesh)

        # if 'local', get linear mask origin per object
        if not mask_global:
            verts = [] # reset per mesh

            if origin_mode == "OBJECT":
                target = obj
            elif origin_mode == "PARENT":
                if obj.parent:
                    target = obj.parent
                else:
                    target = obj
            else:
                target = None

            if target:
                mask_origin_pos = target.matrix_world.to_translation()
                if data_layer.axis_mode == "CUSTOM" and data_layer.axis_obj:
                    mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
                elif data_layer.axis_mode == "LOCAL":
                    mask_origin_axis = target.matrix_world.to_quaternion() @ world_axis
                else:
                    mask_origin_axis = world_axis

                # iterate all meshes to get max distance relative to 'local' linear mask origin
                for face in obj.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = obj.data.loops[loop_id].vertex_index
                        vertex_offset = (obj.matrix_world @ obj.data.vertices[vertex_index].co) - mask_origin_pos

                        verts.append(vertex_offset.dot(mask_origin_axis))
            else:
                if data_layer.axis_mode == "CUSTOM" and data_layer.axis_obj:
                    mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
                elif data_layer.axis_mode == "LOCAL":
                    mask_origin_axis = obj.matrix_world.to_quaternion() @ world_axis
                else:
                    mask_origin_axis = world_axis

            min_dist = min(verts)
            max_dist = max(verts)
            length = max_dist - min_dist
            inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
            min_dist = min_dist if length > 0.0001 else 0.0

        # compute linear mask
        for face in obj.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = obj.data.loops[loop_id].vertex_index
                vertex_offset = obj.matrix_world @ obj.data.vertices[vertex_index].co - mask_origin_pos

                data_to_bake = (vertex_offset).dot(mask_origin_axis)

                if data_layer.normalize:
                    data_to_bake -= min_dist
                    data_to_bake *= inv_length

                if data_layer.clamp:
                    data_to_bake = max(0.0, min(1.0, data_to_bake))

                if data_layer.normalize or data_layer.clamp:
                    data_to_bake = math.pow(data_to_bake, data_layer.falloff)

                data_loop_ids.append(data_to_bake)
    
        if bake_data_min_set:
            bake_data_min = min(bake_data_min, min(data_loop_ids))
        else:
            bake_data_min_set = True
            bake_data_min = min(data_loop_ids)

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, max(data_loop_ids))
        else:
            bake_data_max_set = True
            bake_data_max = max(data_loop_ids)

        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_random(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    if data_layer.rand_float_mode == "FLOAT":
        return get_bake_random_float(context, data_layer, meshes, empties)
    elif data_layer.rand_float_mode == "FLOAT2":
        return get_bake_random_float2(context, data_layer, meshes, empties)
    elif data_layer.rand_float_mode == "FLOAT3":
        return get_bake_random_float3(context, data_layer, meshes, empties)
    else:
        return (None, (0.0, 0.0))

def get_bake_random_float(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    uniform_values = []
    uniform_length = 0

    if data_layer.rand_mode == "COLLECTION":
        cols = []
        for mesh in meshes:
            obj = mesh.get(custom_prop, mesh)

            for col in obj.users_collection:
                if col not in cols:
                    cols.append(col)

        uniform_length = len(cols)
        uniform_length = max(1, uniform_length - 1)

        for col_index, col in enumerate(cols):
            uniform_values.append(col_index / uniform_length)
    elif data_layer.rand_mode == "OBJECT":
        uniform_length = len(meshes)
        uniform_length = max(1, uniform_length - 1)

        for mesh_index, mesh in enumerate(meshes):
            uniform_values.append(mesh_index / uniform_length)
    elif data_layer.rand_mode == "FACE":
        for mesh in meshes:
            uniform_length += len(mesh.data.polygons)
        uniform_length = max(1, uniform_length - 1)

        face_offset = 0
        for mesh in meshes:
            for face_index, face in enumerate(mesh.data.polygons):
                uniform_values.append((face_index + face_offset) / uniform_length)
            face_offset += len(mesh.data.polygons)
    else:
        pass

    if uniform_length > 0:
        random.seed(data_layer.rand_seed)
        random.shuffle(uniform_values)

    face_offset = 0
    for mesh_index, mesh in enumerate(meshes):
        data_loop_ids = []

        if data_layer.rand_mode == "COLLECTION":
            data_to_bake = 0.0

            obj = mesh.get(custom_prop, mesh)
            if obj.users_collection:
                col_index = -1
                try:
                    col_index = cols.index(obj.users_collection[0])
                except:
                    pass
                
                if col_index >= 0:
                    data_to_bake = (uniform_values[col_index] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, data_to_bake)
            else:
                bake_data_min_set = True
                bake_data_min = data_to_bake

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, data_to_bake)
            else:
                bake_data_max_set = True
                bake_data_max = data_to_bake
        elif data_layer.rand_mode == "OBJECT":
            data_to_bake = (uniform_values[mesh_index] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, data_to_bake)
            else:
                bake_data_min_set = True
                bake_data_min = data_to_bake

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, data_to_bake)
            else:
                bake_data_max_set = True
                bake_data_max = data_to_bake
        elif data_layer.rand_mode == "FACE":
            for face_index, face in enumerate(mesh.data.polygons):
                data_to_bake = (uniform_values[face_index +face_offset] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, min(data_loop_ids))
            else:
                bake_data_min_set = True
                bake_data_min = min(data_loop_ids)

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, max(data_loop_ids))
            else:
                bake_data_max_set = True
                bake_data_max = max(data_loop_ids)

            face_offset += len(mesh.data.polygons)

        bake_data.append((mesh, data_loop_ids))
    return (bake_data, (bake_data_min, bake_data_max))

def get_bake_random_float2(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    if data_layer.rand_mode == "COLLECTION":
        cols = []
        for mesh in meshes:
            obj = mesh.get(custom_prop, mesh)

            for col in obj.users_collection:
                if col not in cols:
                    cols.append(col)

        for mesh in meshes:
            data_loop_ids = []

            obj = mesh.get(custom_prop, mesh)

            if obj.users_collection:
                col_index = cols.index(obj.users_collection[0])
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
            
            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, data_to_bake)
            else:
                bake_data_min_set = True
                bake_data_min = data_to_bake

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, data_to_bake)
            else:
                bake_data_max_set = True
                bake_data_max = data_to_bake

            bake_data.append((mesh, data_loop_ids))
    elif data_layer.rand_mode == "OBJECT":
        for mesh_index, mesh in enumerate(meshes):
            data_loop_ids = []

            np.random.seed(data_layer.rand_seed + mesh_index)
            rand = np.random.uniform(-math.pi, math.pi)

            if data_layer.component == "X":
                data_to_bake = math.cos(rand)
            elif data_layer.component == "Y":
                data_to_bake = math.sin(rand)
            elif data_layer.component == "Z":
                data_to_bake = 0.0
            else:
                data_to_bake = 0.0

            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, data_to_bake)
            else:
                bake_data_min_set = True
                bake_data_min = data_to_bake

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, data_to_bake)
            else:
                bake_data_max_set = True
                bake_data_max = data_to_bake

            bake_data.append((mesh, data_loop_ids))
    elif data_layer.rand_mode == "FACE":
        face_offset = 0
        for mesh_index, mesh in enumerate(meshes):
            data_loop_ids = []

            for face_index, face in enumerate(mesh.data.polygons):
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
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, min(data_loop_ids))
            else:
                bake_data_min_set = True
                bake_data_min = min(data_loop_ids)

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, max(data_loop_ids))
            else:
                bake_data_max_set = True
                bake_data_max = max(data_loop_ids)
                
            face_offset += len(mesh.data.polygons)

            bake_data.append((mesh, data_loop_ids))
    else:
        pass

    return (bake_data, (bake_data_min, bake_data_max))

def get_bake_random_float3(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    if data_layer.rand_mode == "COLLECTION":
        cols = []
        for mesh in meshes:
            obj = mesh.get(custom_prop, mesh)

            for col in obj.users_collection:
                if col not in cols:
                    cols.append(col)

        for mesh in meshes:
            data_loop_ids = []

            obj = mesh.get(custom_prop, mesh)

            if obj.users_collection:
                col_index = cols.index(obj.users_collection[0])
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

            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, data_to_bake)
            else:
                bake_data_max_set = True
                bake_data_max = data_to_bake

            bake_data.append((mesh, data_loop_ids))
    elif data_layer.rand_mode == "OBJECT":
        for mesh_index, mesh in enumerate(meshes):
            data_loop_ids = []

            # https://gist.github.com/andrewbolster/10274979
            np.random.seed(data_layer.rand_seed + mesh_index)
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

            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, data_to_bake)
            else:
                bake_data_max_set = True
                bake_data_max = data_to_bake

            bake_data.append((mesh, data_loop_ids))
    elif data_layer.rand_mode == "FACE":
        face_offset = 0
        for mesh_index, mesh in enumerate(meshes):
            data_loop_ids = []

            for face_index, face in enumerate(mesh.data.polygons):
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
                    data_loop_ids.append(data_to_bake)

            if bake_data_min_set:
                bake_data_min = min(bake_data_min, min(data_loop_ids))
            else:
                bake_data_min_set = True
                bake_data_min = min(data_loop_ids)

            if bake_data_max_set:
                bake_data_max = max(bake_data_max, max(data_loop_ids))
            else:
                bake_data_max_set = True
                bake_data_max = max(data_loop_ids)

            face_offset += len(mesh.data.polygons)

            bake_data.append((mesh, data_loop_ids))
    else:
        pass

    return (bake_data, (bake_data_min, bake_data_max))

def get_bake_parent_pos(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    target_depth = max(1, data_layer.index)
    for mesh in meshes:
        data_loop_ids = []

        parent = mesh                
        for depth in range(target_depth):
            if parent and parent.parent and (parent.parent.type == 'MESH' or parent.parent.type == 'EMPTY'):
                parent = parent.parent
            else:
                parent = None
                break

        if not parent: # fallback to self @NOTE see if this is the best solution
            parent = mesh

        parent_loc = parent.matrix_world.to_translation()
        if data_layer.obj:
            parent_loc -= data_layer.obj.matrix_world.to_translation() # relative to origin?

        vector_to_bake = parent_loc * signed_scale

        if data_layer.component == "X":
            data_to_bake = vector_to_bake.x
        elif data_layer.component == "Y":
            data_to_bake = vector_to_bake.y
        elif data_layer.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_loop_ids.append(data_to_bake)

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_parent_axis(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    target_depth = max(1, data_layer.index)
    for mesh in meshes:
        data_loop_ids = []

        parent = mesh                
        for depth in range(target_depth):
            if parent and parent.parent and (parent.parent.type == 'MESH' or parent.parent.type == 'EMPTY'):
                parent = parent.parent
            else:
                parent = None
        
        if not parent: # fallback to self @NOTE see if this is the best solution
            parent = mesh

        parent_quat = parent.matrix_world.to_quaternion()

        if data_layer.axis == "X":
            axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif data_layer.axis == "Y":
            axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif data_layer.axis == "Z":
            axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            axis = mathutils.Vector((0.0, 0.0, 0.0))

        vector_to_bake = (parent_quat @ (axis * signed_axis))

        if data_layer.component == "X":
            data_to_bake = vector_to_bake.x
        elif data_layer.component == "Y":
            data_to_bake = vector_to_bake.y
        elif data_layer.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_loop_ids.append(data_to_bake)

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

        bake_data.append((mesh, data_loop_ids))
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_value(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []
        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_to_bake = data_layer.x
                data_loop_ids.append(data_to_bake)

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

        bake_data.append((mesh, data_loop_ids))

    return bake_data, (bake_data_min, bake_data_max)

def get_bake_custom_prop(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []

        prop = mesh.get(data_layer.name, None)
        if prop and ((type(prop) is int) or (type(prop) is float)):
            data_to_bake = prop
        else:
            data_to_bake = 0.0

        for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append(data_to_bake)
        bake_data.append((mesh, data_loop_ids))

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

    return bake_data, (bake_data_min, bake_data_max)

def get_bake_frame(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    bake_ref_frame = context.scene.frame_current

    dgraph = context.evaluated_depsgraph_get()

    for mesh in meshes:
        data_loop_ids = []

        obj = mesh.get(custom_prop, mesh)

        ############
        # REF POSE #

        context.scene.frame_set(bake_ref_frame)
        #context.view_layer.update()

        ref_eval_obj = obj.evaluated_get(dgraph)
        ref_eval_mesh = ref_eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        ref_eval_mesh.transform(ref_eval_obj.matrix_world)
        ref_eval_mesh_vertex_count = len(ref_eval_mesh.vertices)
        ref_eval_mesh_vertices_pos = [v.co.copy() for v in ref_eval_mesh.vertices] # cache SOURCE vertices pos @NOTE .copy() seems necessary here

        ref_eval_obj.to_mesh_clear()

        context.scene.frame_set(data_layer.index) # advance to frame
        #context.view_layer.update()

        eval_posed_obj = obj.evaluated_get(dgraph)
        eval_posed_mesh = eval_posed_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        eval_posed_mesh.transform(eval_posed_obj.matrix_world)
        eval_mesh_vertex_count = len(eval_posed_mesh.vertices)

        if eval_mesh_vertex_count != ref_eval_mesh_vertex_count:
            return (False, "Vertex count mismatch in frame " + str(data_layer.index) + " for object " + obj.name + ". It likely has a modifier that changes its topology during animation (i.e. a split edge modifier that suddenly splits an edge due to an increase angle).", [], [], None)

        if data_layer.vertex_mode == "OFFSET":
            for face in eval_posed_mesh.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = eval_posed_mesh.loops[loop_id].vertex_index

                    vert_pos = eval_posed_mesh.vertices[vertex_index].co
                    ref_vert_pos = ref_eval_mesh_vertices_pos[vertex_index]
                    offset = vert_pos - ref_vert_pos

                    if data_layer.component == "X":
                        data_to_bake = offset.x
                    elif data_layer.component == "Y":
                        data_to_bake = offset.y
                    else:
                        data_to_bake = offset.z

                    data_loop_ids.append(data_to_bake)
      
                    if bake_data_min_set:
                        bake_data_min = min(bake_data_min, data_to_bake)
                    else:
                        bake_data_min_set = True
                        bake_data_min = data_to_bake

                    if bake_data_max_set:
                        bake_data_max = max(bake_data_max, data_to_bake)
                    else:
                        bake_data_max_set = True
                        bake_data_max = data_to_bake
        else: # NORMAL
            for face in eval_posed_mesh.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = eval_posed_mesh.loops[loop_id].vertex_index

                    vert_nor = eval_posed_mesh.vertices[vertex_index].normal.normalized()

                    if data_layer.component == "X":
                        data_to_bake = vert_nor.x
                    elif data_layer.component == "Y":
                        data_to_bake = vert_nor.y
                    else:
                        data_to_bake = vert_nor.z

                    data_loop_ids.append(data_to_bake)

                    if bake_data_min_set:
                        bake_data_min = min(bake_data_min, data_to_bake)
                    else:
                        bake_data_min_set = True
                        bake_data_min = data_to_bake

                    if bake_data_max_set:
                        bake_data_max = max(bake_data_max, data_to_bake)
                    else:
                        bake_data_max_set = True
                        bake_data_max = data_to_bake

        eval_posed_obj.to_mesh_clear()

        bake_data.append((mesh, data_loop_ids))

    # restore initial frame
    context.scene.frame_set(bake_ref_frame)

    return bake_data, (bake_data_min, bake_data_max)

def get_bake_none(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Return an empty list of (mesh, [data_per_loop_id]) pairings for this bake function

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    return [], (0.0, 0.0)

def get_bake_template(context: bpy.types.Context, data_layer: object, meshes: list, empties: list) -> list:
    """
    Compute and return the list of (mesh, [data_per_loop_id]) pairings for this bake function

    This is a template function, to be used as an example to implement your own

    :param context: Blender current execution context
    :param data_layer: data layer to bake
    :param meshes: list of duplicated meshes included in the bake
    :param empties: list of duplicated empties included in the bake
    :return: list of (mesh, [data_per_loop_id]) pairings and the min/max values to bake
    :rtype: tuple
    """
    settings = context.scene.DataBakerSettings
    custom_prop = settings.mesh_target_prop if settings.mesh_target_prop != "" else "BakeSource"

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False
    
    for mesh in meshes:
        data_loop_ids = []

        obj = mesh.get(custom_prop, mesh)

        for face in obj.data.polygons:
            for loop_id in face.loop_indices:
                data_to_bake = 0.0 # example

                data_loop_ids.append(data_to_bake)
        bake_data.append((mesh, data_loop_ids))

        if bake_data_min_set:
            bake_data_min = min(bake_data_min, data_to_bake)
        else:
            bake_data_min_set = True
            bake_data_min = data_to_bake

        if bake_data_max_set:
            bake_data_max = max(bake_data_max, data_to_bake)
        else:
            bake_data_max_set = True
            bake_data_max = data_to_bake

    return bake_data, (bake_data_min, bake_data_max)

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

    tags = { "ObjectName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        # export selection and assume selection was properly handled outside of this function
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

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
                            scale=str(report.unit_scale),
                            invert_x=str(report.unit_invert_x),
                            invert_y=str(report.unit_invert_y),
                            invert_z=str(report.unit_invert_z))

    # uv info
    uv_el = ET.SubElement(root, "UV",
                          invert_v=str(report.mesh_uvmap_invert_v))

    # data layers info
    if report.data_layers:
        data_layers_el = ET.SubElement(root, "Layers")
        for data_layer in report.data_layers:
            active_data_layers = [packed_data_layer for packed_data_layer in data_layer.packed_layers if packed_data_layer.ID == data_layer.active_layer_ID]
            if active_data_layers and len(active_data_layers) > 0:
                active_data_layer = active_data_layers[0]
                data_layer_el = ET.SubElement(data_layers_el, "Layer",
                                              name=get_data_layer_name(active_data_layer),
                                              min=str(data_layer.range_min),
                                              max=str(data_layer.range_max),
                                              packing=active_data_layer.packing_mode,
                                              uv_index=str(active_data_layer.uv_index) if active_data_layer.packing_mode == "UV" else "",
                                              uv_channel=str(active_data_layer.uv_channel) if active_data_layer.packing_mode == "UV" else "",
                                              vcol_rgba=str(active_data_layer.vcol_rgba) if active_data_layer.packing_mode == "VCOL" else "",
                                              normal_xyz=str(active_data_layer.normal_xyz) if active_data_layer.packing_mode == "NORMAL" else "",
                                              packing_precision=str(active_data_layer.packing_precision))

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
def get_path(path: str, file_name: str, file_ext: str, tags: dict, override_file: bool) -> tuple[bool, str, str]:
    """
    Compile file path/name/extension into a path and perform a couples of safety checks

    :param path: export path
    :param file_name: file name
    :param file_ext: file extension
    :param tags: dict of tags to look for and what they should be replaced with
    :param override_file: if any existing file at the computed path should be overriden
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    
    file_exts = [".png", ".exr", ".fbx"]
    if file_ext not in file_exts:
        return (False, "Invalid File Extension", "")

    file_name = replace_tags(file_name, tags)
    export_path = os.path.abspath(os.path.join(bpy.path.abspath(path), file_name + file_ext))
    success, msg = check_path(export_path, override_file)
    
    return (success, msg, export_path)

def replace_tags(name: str, tags: dict) -> str:
    """
    Check for tags and replace them with their associated value

    :param name: string to search tags in
    :param tags: dict of tags to look for and what they should be replaced with
    :return: the modified name
    :rtype: str
    """
    # check tags
    for tag_key, tag_value in tags.items():
        tag = "<"+tag_key+">"
        if (tag in name):
            name = name.replace(tag, tag_value)

    return name

def check_path(path: str, override_file: str) -> tuple[bool, str]:
    """
    Check for tags and replace them with their associated value

    :param path: export path
    :param override_file: if any existing file at the given path should be overriden
    :return: the path's validity and potential error message
    :rtype: tuple
    """
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        return (False, f"Directory does not exist: {dir}")
    
    if not os.access(dir, os.W_OK):
        return (False, f"Directory is not writable: {dir}")

    if os.path.isfile(path) and not override_file:
        return (False, f"File already exists: {path}")

    return (True, "")