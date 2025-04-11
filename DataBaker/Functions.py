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
from ctypes import POINTER, pointer, c_int, cast, c_float

from . import Properties
from .Properties import DATABAKER_PG_DataLayerPropertyGroup

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################

##############
### REPORT ###
def new_bake_report(context: bpy.types.Context):
    """ """
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
    """ """
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
    report.mesh_uvmap_count = 0

    report.meshes_count = 0
    report.empties_count = 0

    report.xml = False
    report.xml_path = ""

    report.world_obj = None

    report.duplicate_mesh = False
    report.make_single_user = False
    report.merge_mesh = False
    report.clean_bake = False
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
    """ """
    setattr(bpy.context.scene.DataBakerReport, prop_name, prop_value)

def add_bake_layer_report(data_layer, packing, pack_range):
    """ """
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

def export_bake_report(context: bpy.types.Context):
    """ """
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
    
      XXXXXXXXXXXXYYYYYYYYYYZZZZZZZZZZ
    > XXXXXXX0XXXXYYYYYYYYYYZZZZZZZZZZ

    range_max - range_min is assumed to be non-zero
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

def get_packed_15_16_xy(x: float, y: float, range_min: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0)), range_max: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0))) -> float:
    """ 
    Algorithm to pack two floats into one, using 15 and 16 bits of precision while preventing NaNs.

    32bit float NaNs are encoded with the exponent field filled with ones (like infinity values).
      SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
    > S11111111MMMMMMMMMMMMMMMMMMMMMMM = NAN

    We'd like to pack too 16 bits value (x,y) into the 32 bits of the float but we may only pack a
    15-bit and 16-bit values and split the first 15 bits into two groups of bits, as to ensure the
    exponent field isn't filled with ones.
    
      XXXXXXXXXXXXXXXXYYYYYYYYYYYYYYYY
    > XXXXXXX0XXXXXXXXYYYYYYYYYYYYYYYY

    range_max - range_min is assumed to be non-zero
    """
    a = min(1.0, max(0.0, (x - range_min.x) / (range_max.x - range_min.x)))
    bitstring_a = str(bin(math.floor(a * ((1 << 15) - 1))))
    bitstring_a = bitstring_a[2:] # get rid of '0b'
    bitstring_a = bitstring_a.zfill(15) # ensure it's 15 char long

    bitstring_a_a = bitstring_a[:8] # get first 8 characters
    bitstring_a_b = bitstring_a[-7:] # get last 7 characters
    bitstring_a = bitstring_a_a + "0" + bitstring_a_b # reconstruct 16 bits integer with last exponent bit as 0 to prevent NaNs

    b = min(1.0, max(0.0, (y - range_min.y) / (range_max.y - range_min.y)))
    bitstring_b = str(bin(math.floor(b * ((1 << 16) - 1))))
    bitstring_b = bitstring_b[2:] # get rid of '0b'
    bitstring_b = bitstring_b.zfill(16) # ensure it's 16 char long

    bits_string = "0b" + bitstring_a + bitstring_b

    cp = pointer(c_int(int(bits_string, 0)))
    fp = cast(cp, POINTER(c_float))
    return fp.contents.value

def get_packed_frac(x: float, y: float, y_range_min: float = 0.0, y_range_max: float = 1.0, precision: float = 0.99) -> float:
    """ """

    y = (y - y_range_min) / (y_range_max - y_range_min)
    y = min(1.0, max(0.0, y * precision)) # remap frac to [0:<1]
    return  math.floor(x) + y

def get_normalized(x: float, range_min: float, range_max: float):
    """ """
    return ((x - range_min)/ (range_max - range_min) if abs(range_max - range_min) > 0.0001 else 1.0)

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
    """ Algorithm to pack three normalized floats into one. Results in *severe* precision loss and probably isn't practical to encode data like positions """

    return (math.ceil(unit_vector.x * 100) * 10) + (math.ceil(unit_vector.y * 100) * 0.1) + (math.ceil(unit_vector.z * 100) * 0.001)

def get_packed_ab_vector_legacy(unit_vector: mathutils.Vector, a_component: float, b_component: float) -> float:
    """ Algorithm to pack two normalized floats into one. Gives acceptable precision loss unless numbers are large-ish """

    a = unit_vector.x if a_component == "X" else unit_vector.y if a_component == "Y" else unit_vector.z
    a = math.floor(a * (4096 - 1)) * 4096    

    b = unit_vector.x if b_component == "X" else unit_vector.y if b_component == "Y" else unit_vector.z
    b = math.floor(b * (4096 - 1))

    return (a + b)

############
### BAKE ###
def get_bake_data_layers_info(context: bpy.types.Context) -> tuple[bool, str, DATABAKER_PG_DataLayerPropertyGroup]:
    """

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
                return (False, msg)

            layers_info.append((data_layer, layer_info))

    return (True, "", layers_info)

def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object]:
    """
    Modify & ensure the active & selected objects can lead to a valid bake and return the list of objects to include in the bake.

    :param context: Blender current execution context
    :return: success, additional message, list of objects to bake (filtered selection), active object
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

    if not context.selected_objects:
        return (False, "No object selected once filtered out", None, None)

    objs_to_bake = context.selected_objects # cache selection
    active_obj = context.view_layer.objects.active

    """
    Bake will probably need to do a lot of UV processing so ensure the required UVMaps can be accessed or else, created
    """
    uv_layers, uv_maps = get_data_layers_uv_maps(context) # @TODO check

    add_bake_report("mesh_uvmap_count", 0) # @TODO

    if settings.invert_v:
        add_bake_report("mesh_uvmap_invert_v", True)

    obj_uvmaps = []
    for obj in objs_to_bake:
        if obj.type == "MESH":
            if any(uvmap_name in obj.data.uv_layers for uvmap_name in uv_maps): # UVMap exists?
                pass
            elif len(obj.data.uv_layers) >= 8: # ensure UVMap can be created
                return (False, obj.name + " has the maximum amount of uvmaps already", None, None)

            for uvlayer in obj.data.uv_layers: # gather uvmaps as if objects were joined
                if uvlayer.name not in obj_uvmaps:
                    obj_uvmaps.append(uvlayer.name)

    if not any(uvmap_name in obj_uvmaps for uvmap_name in uv_maps) and settings.merge_mesh and len(obj_uvmaps) >= 8:
        return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None)

    context.view_layer.objects.active = None # blank canvas

    return (True, "", objs_to_bake, active_obj)

def get_bake_name(context: bpy.types.Context, active_object:bpy.types.Object) -> str:
    """
    Return the name to give to the mesh & images to generate.

    :param context: Blender current execution context
    :param active_object: object to derive name from
    :return: the bake operation's 'name'
    :rtype: string
    """

    settings = context.scene.DataBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh"
    tags = { "ObjectName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def pre_process_bake_selection(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, list, list]:
    """ """

    settings = context.scene.DataBakerSettings

    if settings.duplicate_mesh or settings.make_single_user:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs_to_bake:
            obj.select_set(True)
            context.view_layer.objects.active = obj

        if settings.duplicate_mesh:
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

        bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False, obdata_animation=False)

    if (len(context.selected_objects) <= 0):
        return (False, "No mesh or empty selected", None)

    context.view_layer.objects.active = context.selected_objects[0]

    # loop through all *newly* selected objects that we may have duplicated and build list of all meshes and empties for later cleaning process
    meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
    add_bake_report("meshes_count", len(meshes))
    empties = [obj for obj in context.selected_objects if obj.type == "EMPTY"]
    add_bake_report("empties_count", len(empties))

    return (True, "", meshes, empties)

def post_process_bake_selection(context: bpy.types.Context, meshes: list, empties: list) -> tuple[bool, str, list]:
    """ """
    bpy.ops.object.select_all(action='DESELECT')

    settings = context.scene.DataBakerSettings
    if settings.clean_bake:
        for empty in empties:
            empty.select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)

    if settings.merge_mesh:
        for mesh in meshes:
            mesh.select_set(True)
            context.view_layer.objects.active = mesh

        name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.Data"
        context.view_layer.objects.active.name      = name
        context.view_layer.objects.active.data.name = name

        if len(meshes) > 1:
            bpy.ops.object.join()
        
        # only report mesh if it has been merged
        add_bake_report("mesh", context.view_layer.objects.active)

        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    else:
        for mesh in meshes:
            mesh.select_set(True)
            context.view_layer.objects.active = mesh

    return (True, "", context.selected_objects)

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function.

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    bpy.ops.object.mode_set(mode="OBJECT")

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

    success, msg, objs_to_export = post_process_bake_selection(context, meshes, empties)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(93)

    if settings.export_mesh and bpy.data.is_saved:
        success, msg, mesh_path = export_mesh(context, bake_name, objs_to_export)
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

def bake_data(context, layers_info, meshes, empties):
    """ """
    settings = context.scene.DataBakerSettings
    
    for data_layer, layer_info in layers_info:
        """
        First, we unpack layer_info and see if we should continue.

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
        Second, the goal is to call the appropriate bake function for each valid layer and gather the list values to
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
                    print(get_data_layer_name(layer_packed))
                    layer_data, layer_data_range = layer_func(context, layer_packed, meshes, empties) # @NOTE performance bottleneck

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
        We ensured that each layer processed the same amount of meshes, so we simply iterate meshes by index. For each, we gather
        the values to bake per layer. While doing so, we also double check that the number of values to bake is similar for all
        layers, as well as the object to bake at that index.

        There might only be one layer, thus one single list of values to bake, but layers might be asked to pack other layers so we may need to stack lists.
        """
        for mesh_index, mesh_info in enumerate(meshes_to_bake):
            progress = mesh_index / (len(meshes_to_bake) - 1)
            bpy.context.window_manager.progress_update((progress * 80) + 10)

            mesh, num_values = mesh_info
            print("----")
            print(mesh)
            values_to_pack = np.stack((
                np.array(np.zeros(num_values, dtype=float) if layers_data[0] is None else layers_data[0][mesh_index][1]),
                np.array(np.zeros(num_values, dtype=float) if layers_data[1] is None else layers_data[1][mesh_index][1]),
                np.array(np.zeros(num_values, dtype=float) if layers_data[2] is None else layers_data[2][mesh_index][1])),
                axis=-1)

            print(values_to_pack)

            if data_layer.packing_mode == "UV":
                if data_layer.uv_channel == "U":
                    index = 0
                    invert_v = False
                else:
                    index = 1
                    invert_v = settings.invert_v

                while (data_layer.uv_index > (len(mesh.data.uv_layers) - 1)):
                    mesh.data.uv_layers.new()

                    zero_uv = (0.0, 1.0 if invert_v else 0.0)
                    for face in mesh.data.polygons:
                        for loop_id in face.loop_indices:
                            mesh.data.uv_layers[data_layer.uv_index].data[loop_id].uv = zero_uv

                uv_name = settings.uvmap_name if settings.uvmap_name != "" else "UVMap.BakedData"
                uv_name += "." + str(data_layer.uv_index)
                mesh.data.uv_layers[data_layer.uv_index].name = uv_name

                for face in mesh.data.polygons: # @NOTE performance bottleneck
                    for loop_id in face.loop_indices:
                        x = 0.0
                        if packing_mode == "XYZ":
                            x = get_packed_11_10_10_xyz(values_to_pack[loop_id][0], values_to_pack[loop_id][1], values_to_pack[loop_id][2], pack_min, pack_max)
                        elif packing_mode == "XY":
                            x = get_packed_15_16_xy(values_to_pack[loop_id][0], values_to_pack[loop_id][1], pack_min, pack_max)
                        elif packing_mode == "FRACTION":
                            x = get_packed_frac(values_to_pack[loop_id][0], values_to_pack[loop_id][1], pack_min.x, pack_max.x, settings.packing_precision)
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

                for face in mesh.data.polygons: # @NOTE performance bottleneck
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
                continue
                # @TODO need to convert loop_id to vertex index :(
                for face in mesh.data.polygons:
                    face.use_smooth = True

                normals = []
                for vertex in obj.data.vertices: # @TODO we might need to duplicate verts? (rand per face)
                    normals.append(data_array)

                mesh.data.normals_split_custom_set_from_vertices(normals)
            else:
                pass

        add_bake_layer_report(data_layer, packing, (pack_min, pack_max))

    return (True, "")

##################
### DATA LAYER ###
def get_data_layer_info(data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list):
    """ """
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
        success, msg, layer_info = get_data_layer_non_targeting_info(data_layer, data_layers)
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

def get_data_layer_targeting_info(data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list):
    """ """
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
        if mode == "FRACTION" or mode == "XY" or mode == "XYZ" or mode == "VCOL":
            return (False, "is targeted by " + get_data_layer_name(data_layer) + " but don't allow bit-packing", None)

        return (True, "", data_layer_target)
    else:
        return (False, "target specified couldn't be found", None)

def get_data_layer_non_targeting_info(data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list):
    """ """
    # check if targeted UV channel/index is free
    if data_layer.packing_mode == "UV":
        if data_layer.uv_index > 7:
            return (False, "can't have " + str(data_layer.uv_index + 1) + " UVMaps", None)

        uv_components = []
        for data_layer in data_layers:
            layer_index = data_layer.uv_index * 2 + (0 if data_layer.uv_channel == "U" else 1)
            if data_layer.packing_mode == "UV":
                if (layer_index in uv_components):
                    return (False, "UVMap " + str(data_layer.uv_index) + " channel " + data_layer.uv_channel + " is already targeted", None)
                else:
                    uv_components.append(layer_index)
    # check if targeted VCOL RGBA channel is free                    
    elif data_layer.packing_mode == "VCOL":
        vcol_components = []
        for data_layer in data_layers:
            if data_layer.packing_mode == "VCOL":
                if (data_layer.vcol_rgba in vcol_components):
                    return (False, data_layer.vcol_rgba + " already targeted", None)
                else:
                    vcol_components.append(data_layer.vcol_rgba)
    # check if targeted NORMAL XYZ component is free
    elif data_layer.packing_mode == "NORMAL":
        normal_components = []
        for data_layer in data_layers:
            if data_layer.packing_mode == "NORMAL":
                if (data_layer.normal_xyz in normal_components):
                    return (False, "Normal " + str(data_layer.normal_xyz) + " is already targeted", None)
                else:
                    normal_components.append(data_layer.normal_xyz)

    return (True, "", None)

def get_data_layer_packing_info(data_layer_target, data_layers_to_pack: list):
    """ """
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

def get_data_layers_uv_maps(context: bpy.types.Context) -> tuple[list, list]:
    """ """
    settings = context.scene.DataBakerSettings
    uvmap_name = settings.uvmap_name if settings.uvmap_name != "" else "UVMap.BakedData"

    data_layers_uv = [d for d in settings.data_layers if d.packing_mode == "UV"]
    uv_layers = []
    uv_maps = []
    for data_layer_uv in data_layers_uv:
        uv_layers.append(data_layer_uv.uv_index * 2 + (1 if data_layer_uv.uv_channel == "U" else 0))
        
        uv_index_str = str(data_layer_uv.uv_index)
        uv_index_str = uv_index_str.zfill(3)
        if (uvmap_name + uv_index_str) not in uv_maps:
            uv_maps.append(uvmap_name + uv_index_str)

    return (uv_layers, uv_maps)

def get_data_layer_name(item: DATABAKER_PG_DataLayerPropertyGroup) -> str:
    """ """
    if item:
        if item.data == "POSITION":
            return "Position " + item.component
        elif item.data == "AXIS":
            return "Axis " + item.component
        elif item.data == "SHAPEKEY":
            if item.shapekey_mode == "OFFSET":
                return "Shapekey Offset " + item.component
            elif item.shapekey_mode == "NORMAL":
                return "Shapekey Normal " + item.component
            else:
                pass
        elif item.data == "MASK":
            if item.mask_mode == "SPHERE":
                return "Mask Sphere"
            elif item.mask_mode == "LINEAR":
                return "Mask Linear " + item.axis
        elif item.data == "RANDOM":
            if item.rand_mode == "COLLECTION":
                return "Random Per Col"
            elif item.rand_mode == "OBJECT":
                return "Random Per Obj"
            elif item.rand_mode == "FACE":
                return "Random Per Face"
            else:
                pass
        elif item.data == "PARENT_POS":
            return "Parent " + str(item.index) + " Pos " + item.component
        elif item.data == "PARENT_AXIS":
            return "Parent " + str(item.index) + " Axis " + item.component
        elif item.data == "VALUE":
            return "Value"
        elif item.data == "CUSTOM_PROP":
            if item.name == "":
                return "Invalid Custom Prop"
            else:
                return item.name
        else:
            pass

    return "UNKNOWN"

def get_data_layer_storage_mode_icon(item: DATABAKER_PG_DataLayerPropertyGroup, details: bool = False) -> str:
    """ """
    if item:
        if item.packing_mode == "UV":
            return (True, "UV")
        elif item.packing_mode == "VCOL":
            return (True, "GROUP_VCOL")
        elif item.packing_mode == "NORMAL":
            return (True, "NORMALS_FACE")
        else:
            if details:
                if item.ptr_ID == "":
                    return (False, "QUESTION")

                if item.packing_mode == "XY":
                    return (False, "OVERLAY")
                elif item.packing_mode == "XYZ":
                    return (False, "THREE_DOTS")
                elif item.packing_mode == "FRACTION":
                    return (False, "PIVOT_ACTIVE")
                else:
                    pass

            return (False, "COPYDOWN")

    return (False, "X")

def get_data_layer_bake_function(data_layer: DATABAKER_PG_DataLayerPropertyGroup):
    """ """
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
        else:
            return get_bake_none
    
    return get_bake_none

######################
### BAKE FUNCTIONS ###
def get_bake_position(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

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

        target_obj = data_layer.obj if data_layer.obj else mesh
        target_obj_mat = target_obj.matrix_world
        if settings.world_obj:
            target_obj_mat = target_obj_mat @ settings.world_obj.matrix_world.inverted # relative to world obj
        target_obj_loc = target_obj_mat.to_translation()

        vector_to_bake = target_obj_loc * signed_scale

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

def get_bake_axis(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

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
        
        target_obj = data_layer.obj if data_layer.obj else mesh
        target_obj_mat = target_obj.matrix_world
        if settings.world_obj:
            target_obj_mat = target_obj_mat @ settings.world_obj.matrix_world.inverted # relative to world obj

        target_obj_quat = target_obj_mat.to_quaternion()

        if data_layer.axis == "X":
            axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif data_layer.axis == "Y":
            axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif data_layer.axis == "Z":
            axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            axis = mathutils.Vector((0.0, 0.0, 0.0))

        vector_to_bake = (target_obj_quat @ (axis * signed_axis))

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

def get_bake_shapekey(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    # @TODO rework way shapekeys offset & normal are computed
    settings = context.scene.DataBakerSettings

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

        # cache & reset all shape keys
        initial_shape_keys = []
        for shape_key in mesh.data.shape_keys.key_blocks:
            initial_shape_keys.append((shape_key.name, shape_key.value))
            shape_key.value = 0.0

        # enable shape key to bake
        if data_layer.name in mesh.data.shape_keys.key_blocks:
            mesh.data.shape_keys.key_blocks[settings.name].value = 1.0

        # cache posed vertices
        dgraph = context.evaluated_depsgraph_get()
        obj_eval = mesh.evaluated_get(dgraph)
        mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        vertices_posed = [vertex.copy() for vertex in mesh_eval.vertices]
        obj_eval.to_mesh_clear()

        # disable shape key to bake
        if data_layer.name in mesh.data.shape_keys.key_blocks:
            mesh.data.shape_keys.key_blocks[settings.name].value = 0.0

        # cache rest vertices
        dgraph = context.evaluated_depsgraph_get()
        obj_eval = mesh.evaluated_get(dgraph)
        mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        vertices_rest = [vertex.copy() for vertex in mesh_eval.vertices]
        obj_eval.to_mesh_clear()

        # restore shapekeys
        for shape_key_name, shape_key_value in initial_shape_keys:
            mesh.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value 

        # compute shape key value to bake
        for face in mesh_eval.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = mesh_eval.data.loops[loop_id].vertex_index

                if data_layer.shapekey_mode == "OFFSET":
                    vector_to_bake = (vertices_posed[vertex_index].co - vertices_rest[vertex_index].co) * signed_scale
                elif data_layer.shapekey_mode == "NORMAL":
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

def get_bake_mask(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

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
        return get_bake_mask_sphere(data_layer, meshes, empties, origin_mode, signed_scale)
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

        return get_bake_mask_linear(data_layer, meshes, empties, origin_mode, signed_scale, world_axis)
    else:
        return (None, (0.0, 0.0))

def get_bake_mask_sphere(data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list, origin_mode: str="WORLD", signed_scale: mathutils.Vector=mathutils.Vector((1.0, 1.0, 1.0))) -> list:
    """ """
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
            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = mesh.data.loops[loop_id].vertex_index

                    vertex_offset = (mesh.matrix_world @ mesh.data.vertices[vertex_index].co) - mask_origin_pos
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

        # if 'local', get sphere mask origin per object
        if not mask_global:
            verts = [] # reset per mesh

            if origin_mode == "OBJECT":
                target = mesh
            elif origin_mode == "PARENT":
                if mesh.parent:
                    target = mesh.parent
                else:
                    target = mesh
            else:
                target = None

            if target:
                mask_origin_pos = target.matrix_world.to_translation()

                # iterate all meshes to get max distance relative to 'local' sphere mask origin 
                for face in mesh.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = mesh.data.loops[loop_id].vertex_index
                        vertex_offset = (mesh.matrix_world @ mesh.data.vertices[vertex_index].co) - mask_origin_pos

                        verts.append(vertex_offset.length)

            min_dist = min(verts)
            max_dist = max(verts)
            length = max_dist - min_dist
            inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
            min_dist = min_dist if length > 0.0001 else 0.0

        # compute sphere mask
        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = mesh.data.loops[loop_id].vertex_index
                vertex_offset = (mesh.matrix_world @ mesh.data.vertices[vertex_index].co) - mask_origin_pos

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

def get_bake_mask_linear(data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list, origin_mode: str="WORLD", signed_scale: mathutils.Vector=mathutils.Vector((1.0, 1.0, 1.0)), world_axis: mathutils.Vector=mathutils.Vector((0.0, 0.0, 1.0))) -> list:
    """ """
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
            averaged_pos += mesh.matrix_world.to_translation()
        mask_origin_pos = averaged_pos / max(len(meshes), 1)
        mask_origin_axis = world_axis
        mask_global = True

    # if 'global', iterate all meshes to get max distance relative to linear mask origin
    if mask_global:
        verts = []
        for mesh in meshes:
            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = mesh.data.loops[loop_id].vertex_index

                    vertex_offset = (mesh.matrix_world @ mesh.data.vertices[vertex_index].co) - mask_origin_pos
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

        # if 'local', get linear mask origin per object
        if not mask_global:
            verts = [] # reset per mesh

            if origin_mode == "OBJECT":
                target = mesh
            elif origin_mode == "PARENT":
                if mesh.parent:
                    target = mesh.parent
                else:
                    target = mesh
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
                for face in mesh.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = mesh.data.loops[loop_id].vertex_index
                        vertex_offset = (mesh.matrix_world @ mesh.data.vertices[vertex_index].co) - mask_origin_pos

                        verts.append(vertex_offset.dot(mask_origin_axis))
            else:
                if data_layer.axis_mode == "CUSTOM" and data_layer.axis_obj:
                    mask_origin_axis = data_layer.axis_obj.matrix_world.to_quaternion() @ world_axis
                elif data_layer.axis_mode == "LOCAL":
                    mask_origin_axis = mesh.matrix_world.to_quaternion() @ world_axis
                else:
                    mask_origin_axis = world_axis

            min_dist = min(verts)
            max_dist = max(verts)
            length = max_dist - min_dist
            inv_length = 1.0 / length if length > 0.0001 else 1.0 / max_dist if max_dist > 0.0001 else 1.0
            min_dist = min_dist if length > 0.0001 else 0.0

        # compute linear mask
        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = mesh.data.loops[loop_id].vertex_index
                vertex_offset = mesh.matrix_world @ mesh.data.vertices[vertex_index].co - mask_origin_pos

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

def get_bake_random(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    if data_layer.rand_float_mode == "FLOAT":
        return get_bake_random_float(context, data_layer, meshes, empties)
    elif data_layer.rand_float_mode == "FLOAT2":
        return get_bake_random_float2(context, data_layer, meshes, empties)
    elif data_layer.rand_float_mode == "FLOAT3":
        return get_bake_random_float3(context, data_layer, meshes, empties)
    else:
        return (None, (0.0, 0.0))

def get_bake_random_float(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    settings = context.scene.DataBakerSettings

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
            for col in mesh.users_collection:
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
            if mesh.users_collection:
                col_index = -1
                try:
                    col_index = cols.index(mesh.users_collection[0])
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
    return bake_data, (bake_data_min, bake_data_max)

def get_bake_random_float2(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    settings = context.scene.DataBakerSettings

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    if data_layer.rand_mode == "COLLECTION":
        cols = []
        for mesh in meshes:
            for col in mesh.users_collection:
                if col not in cols:
                    cols.append(col)

        for mesh in meshes:
            data_loop_ids = []

            if mesh.users_collection:
                col_index = cols.index(mesh.users_collection[0])
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
                data_to_bake = [math.cos(rand)]
            elif data_layer.component == "Y":
                data_to_bake = [math.sin(rand)]
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
                    data_to_bake = [math.cos(rand)]
                elif data_layer.component == "Y":
                    data_to_bake = [math.sin(rand)]
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

    return bake_data, (bake_data_min, bake_data_max)

def get_bake_random_float3(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    settings = context.scene.DataBakerSettings

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    if data_layer.rand_mode == "COLLECTION":
        cols = []
        for mesh in meshes:
            for col in mesh.users_collection:
                if col not in cols:
                    cols.append(col)

        for mesh in meshes:
            data_loop_ids = []

            if mesh.users_collection:
                col_index = cols.index(mesh.users_collection[0])
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

    return bake_data, (bake_data_min, bake_data_max)

def get_bake_parent_pos(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    target_depth = max(1, settings.index)
    for mesh in meshes:
        data_loop_ids = []

        parent = mesh                
        for depth in range(target_depth):
            if parent.parent and (parent.parent.type == 'MESH' or parent.parent.type == 'EMPTY'):
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

def get_bake_parent_axis(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    target_depth = max(1, settings.index)
    for mesh in meshes:
        data_loop_ids = []

        parent = mesh                
        for depth in range(target_depth):
            if parent.parent and (parent.parent.type == 'MESH' or parent.parent.type == 'EMPTY'):
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

def get_bake_value(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

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

def get_bake_custom_prop(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

    bake_data = []
    bake_data_min = 0.0
    bake_data_min_set = False
    bake_data_max = 0.0
    bake_data_max_set = False

    for mesh in meshes:
        data_loop_ids = []

        prop = mesh.get(data_layer.custom_prop_name, None)
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

def get_bake_none(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    return [], (0.0, 0.0)

##############
### MESHES ###
def export_mesh(context: bpy.types.Context, bake_name: str, objs_to_export: list) -> tuple[bool, str, str]:
    """
    Export the given object to FBX

    :param context: Blender current execution context
    :param Name: Bake operation's 'name'
    :param Object: Object to edit
    :return: success, message, path
    :rtype: tuple
    """

    settings = context.scene.DataBakerSettings

    tags = { "ObjectName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        bpy.ops.object.select_all(action='DESELECT')
        for obj_to_export in objs_to_export:
            obj_to_export.select_set(True)
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
        #bpy.ops.object.select_all(action='DESELECT') # keep selection for feedback
    else:
        return (False, msg, None)

    return (True, "", export_path)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """ """

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
                          invert_v=str(report.mesh_uvmap_invert_v),
                          count=str(report.mesh_uvmap_count))
    
    #for mesh_uvmap in report.mesh_uvmaps:
    #    uv_sub_el = ET.SubElement(uv_el, "UVMap", name=mesh_uvmap.name, id=mesh_uvmap.ID)

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
def get_path(path: str, file_name: str, file_ext: str, tags: list, override_file: bool) -> tuple[bool, str, str]:
    """ Compiles file path/name/extension into a path and performs a couples of safety checks """
    
    file_exts = [".png", ".exr", ".fbx"]
    if file_ext not in file_exts:
        return (False, "Invalid File Extension", "")

    file_name = replace_tags(file_name, tags)
    export_path = os.path.abspath(os.path.join(bpy.path.abspath(path), file_name + file_ext))
    success, msg = check_path(export_path, override_file)
    
    return (success, msg, export_path)

def replace_tags(name: str, tags: list) -> str:
    # check tags
    for tag_key, tag_value in tags.items():
        tag = "<"+tag_key+">"
        if (tag in name):
            name = name.replace(tag, tag_value)

    return name

def check_path(path: str, override_file: str) -> tuple[bool, str]:
    """ """
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        return (False, f"Directory does not exist: {dir}")
    
    if not os.access(dir, os.W_OK):
        return (False, f"Directory is not writable: {dir}")

    if os.path.isfile(path) and not override_file:
        return (False, f"File already exists: {path}")

    return (True, "")