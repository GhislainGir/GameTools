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

    report.position_multiplier = 1.0
    report.parent_position_multiplier = 1.0
    report.shapekey_offset_multiplier = 1.0

    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_uvmaps.clear()
    report.select_mesh_uvmap = 0
    report.mesh_uvmap_invert_v = False

    report.meshes_count = 0
    report.empties_count = 0

    report.xml = False
    report.xml_path = ""

    report.world_obj = None

    # position
    report.position = False
    report.position_channel_mode = ""
    report.position_x = False
    report.position_x_mode = ""
    report.position_x_uv_index = 0
    report.position_x_uv_channel = ""
    report.position_x_rgba = ""
    report.position_y = False
    report.position_y_mode = ""
    report.position_y_uv_index = 0
    report.position_y_uv_channel = ""
    report.position_y_rgba = ""
    report.position_z = False
    report.position_z_mode = ""
    report.position_z_uv_index = 0
    report.position_z_uv_channel = ""
    report.position_z_rgba = ""
    report.position_packed_uv_index = 0
    report.position_packed_uv_channel = ""
    report.position_pack_only_if_non_null = False
    report.position_ab_packed_a_comp = ""
    report.position_ab_packed_b_comp = ""

    # axis
    report.axis = False
    report.axis_component = ""
    report.axis_channel_mode = ""
    report.axis_x = False
    report.axis_x_mode = ""
    report.axis_x_uv_index = 0
    report.axis_x_uv_channel = ""
    report.axis_x_rgba = ""
    report.axis_y = False
    report.axis_y_mode = ""
    report.axis_y_uv_index = 0
    report.axis_y_uv_channel = ""
    report.axis_y_rgba = ""
    report.axis_z = False
    report.axis_z_mode = ""
    report.axis_z_uv_index = 0
    report.axis_z_uv_channel = ""
    report.axis_z_rgba = ""
    report.axis_packed_uv_index = 0
    report.axis_packed_uv_channel = ""
    report.axis_ab_packed_a_comp = ""
    report.axis_ab_packed_b_comp = ""
    
    # shapekey
    report.shapekey_name = ""
    report.shapekey_rest_name = ""
    
    # shapekey offset
    report.shapekey_offset = False
    report.shapekey_offset_channel_mode = ""
    report.shapekey_offset_x = False
    report.shapekey_offset_x_mode = ""
    report.shapekey_offset_x_uv_index = 0
    report.shapekey_offset_x_uv_channel = ""
    report.shapekey_offset_x_rgba = ""
    report.shapekey_offset_y = False
    report.shapekey_offset_y_mode = ""
    report.shapekey_offset_y_uv_index = 0
    report.shapekey_offset_y_uv_channel = ""
    report.shapekey_offset_y_rgba = ""
    report.shapekey_offset_z = False
    report.shapekey_offset_z_mode = ""
    report.shapekey_offset_z_uv_index = 0
    report.shapekey_offset_z_uv_channel = ""
    report.shapekey_offset_z_rgba = ""
    report.shapekey_offset_packed_uv_index = 0
    report.shapekey_offset_packed_uv_channel = ""
    report.shapekey_offset_pack_only_if_non_null = False
    report.shapekey_offset_ab_packed_a_comp = ""
    report.shapekey_offset_ab_packed_b_comp = ""

    # shapekey normal
    report.shapekey_normal = False
    report.shapekey_normal_channel_mode = ""
    report.shapekey_normal_x = False
    report.shapekey_normal_x_mode = ""
    report.shapekey_normal_x_uv_index = 0
    report.shapekey_normal_x_uv_channel = ""
    report.shapekey_normal_x_rgba = ""
    report.shapekey_normal_y = False
    report.shapekey_normal_y_mode = ""
    report.shapekey_normal_y_uv_index = 0
    report.shapekey_normal_y_uv_channel = ""
    report.shapekey_normal_y_rgba = ""
    report.shapekey_normal_z = False
    report.shapekey_normal_z_mode = ""
    report.shapekey_normal_z_uv_index = 0
    report.shapekey_normal_z_uv_channel = ""
    report.shapekey_normal_z_rgba = ""
    report.shapekey_normal_xyz_uv_index = 0
    report.shapekey_normal_xyz_uv_channel = ""
    report.shapekey_normal_ab_packed_a_comp = ""
    report.shapekey_normal_ab_packed_b_comp = ""

    # sphere mask
    report.sphere_mask = False
    report.sphere_mask_normalize = False
    report.sphere_mask_clamp = False
    report.sphere_mask_origin_mode = ""
    report.sphere_mask_origin = None
    report.sphere_mask_mode = ""
    report.sphere_mask_uv_index = 0
    report.sphere_mask_uv_channel = ""
    report.sphere_mask_rgba = ""
    report.sphere_mask_falloff = 0.0

    # linear mask
    report.linear_mask = False
    report.linear_mask_normalize = False
    report.linear_mask_clamp = False
    report.linear_mask_obj_mode = ""
    report.linear_mask_obj = None
    report.linear_mask_mode = ""
    report.linear_mask_axis = ""
    report.linear_mask_uv_index = 0
    report.linear_mask_uv_channel = ""
    report.linear_mask_rgba = ""
    report.linear_mask_falloff = 0.0
    
    # random per collection
    report.random_per_collection = False
    report.random_per_collection_mode = ""
    report.random_per_collection_uv_index = 0
    report.random_per_collection_uv_channel = ""
    report.random_per_collection_rgba = ""
    report.random_per_collection_uniform = 0.0
    
    # random per object
    report.random_per_object = False
    report.random_per_object_mode = ""
    report.random_per_object_uv_index = 0
    report.random_per_object_uv_channel = ""
    report.random_per_object_rgba = ""
    report.random_per_object_uniform = 0.0
    
    # random per poly
    report.random_per_poly = False
    report.random_per_poly_mode = ""
    report.random_per_poly_uv_index = 0
    report.random_per_poly_uv_channel = ""
    report.random_per_poly_rgba = ""
    report.random_per_poly_uniform = 0.0

    # parent
    report.parent_mode = ""
    report.parent_depth = 0
    report.parent_max_depth = 0
    report.parent_automatic_uv_index = 0
    report.parent_automatic_uv_channel = ""

    # parent position
    report.parent_position = False
    report.parent_position_channel_mode = ""
    report.parent_position_x = False
    report.parent_position_x_mode = ""
    report.parent_position_x_uv_index = 0
    report.parent_position_x_uv_channel = ""
    report.parent_position_x_rgba = ""
    report.parent_position_y = False
    report.parent_position_y_mode = ""
    report.parent_position_y_uv_index = 0
    report.parent_position_y_uv_channel = ""
    report.parent_position_y_rgba = ""
    report.parent_position_z = False
    report.parent_position_z_mode = ""
    report.parent_position_z_uv_index = 0
    report.parent_position_z_uv_channel = ""
    report.parent_position_z_rgba = ""
    report.parent_position_packed_uv_index = 0
    report.parent_position_packed_uv_channel = ""
    report.parent_position_ab_packed_a_comp = ""
    report.parent_position_ab_packed_b_comp = ""
    
    # parent axis
    report.parent_axis = False
    report.parent_axis_component = ""
    report.parent_axis_channel_mode = ""
    report.parent_axis_x = False
    report.parent_axis_x_mode = ""
    report.parent_axis_x_uv_index = 0
    report.parent_axis_x_uv_channel = ""
    report.parent_axis_x_rgba = ""
    report.parent_axis_y = False
    report.parent_axis_y_mode = ""
    report.parent_axis_y_uv_index = 0
    report.parent_axis_y_uv_channel = ""
    report.parent_axis_y_rgba = ""
    report.parent_axis_z = False
    report.parent_axis_z_mode = ""
    report.parent_axis_z_uv_index = 0
    report.parent_axis_z_uv_channel = ""
    report.parent_axis_z_rgba = ""
    report.parent_axis_packed_uv_index = 0
    report.parent_axis_packed_uv_channel = ""
    report.parent_axis_ab_packed_a_comp = ""
    report.parent_axis_ab_packed_b_comp = ""

    # fixed value
    report.fixed_value = False
    report.fixed_value_data = 0.0
    report.fixed_value_mode = ""
    report.fixed_value_uv_index = 0
    report.fixed_value_uv_channel = ""
    report.fixed_value_rgba = ""

    # direction
    report.direction = False
    report.direction_mode = ""
    report.direction_vector_x = 0.0
    report.direction_vector_y = 0.0
    report.direction_vector_z = 0.0
    report.direction_pack_mode = ""

    # custom prop
    report.custom_prop = False
    report.custom_prop_name = ""
    report.custom_prop_mode = ""
    report.custom_prop_uv_index = 0
    report.custom_prop_uv_channel = ""
    report.custom_prop_rgba = ""

    # mesh
    report.duplicate_mesh = False
    report.make_single_user = False
    report.merge_mesh = False
    report.clean_bake = False
    report.mesh_name = ""
    report.scale = 0.0
    report.invert_x = False
    report.invert_y = False
    report.invert_z = False
    report.origin = None
    report.precision_offset = 0.0

    report.export_mesh = False
    report.export_mesh_file_name = ""
    report.export_mesh_file_path = ""
    report.export_mesh_file_override = False

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """ """
    setattr(bpy.context.scene.DataBakerReport, prop_name, prop_value)

def add_bake_report_uv(ID: str, name: str):
    """ """
    settings = bpy.context.scene.DataBakerSettings
    report = bpy.context.scene.DataBakerReport

    report_uvmap = report.mesh_uvmaps.add()
    report_uvmap.ID = ID
    report_uvmap.name = name

def export_bake_report(context: bpy.types.Context):
    """ """
    return(export_xml(context))

###############
### PACKING ###
def get_packed_11_11_10_xyz(xyz: mathutils.Vector, multiplier: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0))) -> tuple[bool, str, float]:  
    """ """

    if multiplier <= 0:
        return (False, "Invalid multiplier", 0.0)

    bitstring_a = str(bin(math.floor((((min(1.0, max(0.0, xyz.x / multiplier))) + 1) * 0.5) * (1<<10))))
    bitstring_a = bitstring_a[2:] # get rid of 0b
    bitstring_a = bitstring_a.zfill(11) # ensure it's 11 char long

    bitstring_b = str(bin(math.floor((((min(1.0, max(0.0, xyz.y / multiplier))) + 1) * 0.5) * (1<<10))))
    bitstring_b = bitstring_b[2:] # get rid of 0b
    bitstring_b = bitstring_b.zfill(11) # ensure it's 11 char long

    bitstring_c = str(bin(math.floor((((min(1.0, max(0.0, xyz.z / multiplier))) + 1) * 0.5) * (1<<9))))
    bitstring_c = bitstring_c[2:] # get rid of 0b
    bitstring_c = bitstring_c.zfill(10) # ensure it's 10 char long

    bits = int((bitstring_a + bitstring_b + bitstring_c), 2)

    cp = pointer(c_int(bits))
    fp = cast(cp, POINTER(c_float))
    return (True, "", fp.contents.value)

def get_packed_16_16_ab(xyz: mathutils.Vector, a_component: float, b_component: float, multiplier: mathutils.Vector = mathutils.Vector((1.0, 1.0, 1.0))) -> tuple[bool, str, float]:
    """ """ 

    if multiplier <= 0:
        return (False, "Invalid multiplier", 0.0)

    a = xyz.x if a_component == "X" else xyz.y if a_component == "Y" else xyz.z
    bitstring_a = str(bin(math.floor((((min(1.0, max(0.0, a / multiplier))) + 1) * 0.5) * (1<<15))))
    bitstring_a = bitstring_a[2:] # get rid of 0b
    bitstring_a = bitstring_a.zfill(16) # ensure it's 11 char long

    b = xyz.x if b_component == "X" else xyz.y if b_component == "Y" else xyz.z
    bitstring_b = str(bin(math.floor((((min(1.0, max(0.0, b / multiplier))) + 1) * 0.5) * (1<<15))))
    bitstring_b = bitstring_b[2:] # get rid of 0b
    bitstring_b = bitstring_b.zfill(16) # ensure it's 11 char long

    bits = int((bitstring_a + bitstring_b), 2)

    cp = pointer(c_int(bits))
    fp = cast(cp, POINTER(c_float))
    return (True, "", fp.contents.value)

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
        for obj in reversed(objs_to_bake): # @NOTE why reversed?
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

    #############
    # BAKE INFO #

    bake_start_time = time.time()

    success, msg = get_data_layers_sanity(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    success, msg, objs_to_bake, active_object = get_bake_selection(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    success, msg, meshes, empties = pre_process_bake_selection(context, objs_to_bake)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)


    bake_name = get_bake_name(context, active_object)
    add_bake_report("name", bake_name)

    ########
    # BAKE #

    for data_layer_index, data_layer in enumerate(settings.data_layers):
        if not get_data_layer_sanity_ask_for_packing(data_layer):
            success, msg, packing = get_data_layer_sanity_packing(data_layer, settings.data_layers)
            if not success:
                return (False, msg, packing)

            data_to_bake = 0.0
            if packing:
                layers_to_bake = []
                if len(packing[0]) == 0:
                    layers_to_bake.append(data_layer)
                    if len(packing[1]) != 0:
                        layers_to_bake.append(packing[1][0])
                    if len(packing[2]) != 0:
                        layers_to_bake.append(packing[2][0])
                elif len(packing[1]) == 0:
                    if len(packing[0]) != 0:
                        layers_to_bake.append(packing[0][0])
                    layers_to_bake.append(data_layer)
                    if len(packing[2]) != 0:
                        layers_to_bake.append(packing[2][0])
                elif len(packing[2]) == 0:
                    if len(packing[0]) != 0:
                        layers_to_bake.append(packing[0][0])
                    if len(packing[1]) != 0:
                        layers_to_bake.append(packing[1][0])
                    layers_to_bake.append(data_layer)
                print("=====")
                print(layers_to_bake)
                print("=====")

                t = []
                for l in layers_to_bake:
                    t.append(get_data_layer_bake_function(l)(context, data_layer, meshes, empties))

                u = {}
                for i in t:
                    for m, d in i:
                        if m not in u:
                            u[m] = [d]
                        else:
                            i = u[m]
                            i.append(d)

                print(u)

                if data_layer.storage_mode == "UV":
                    for mesh_to_bake, data_array in u.items():
                        bake_data_uv(mesh_to_bake, data_array, data_layer.uv_index, data_layer.uv_channel, settings.uvmap_name, settings.invert_v)
                elif data_layer.storage_mode == "VCOL":
                    for mesh_to_bake, data_array in u.items():
                        bake_data_vcol(mesh_to_bake, data_array, data_layer.vcol_rgba)
                elif data_layer.storage_mode == "NORMAL":
                    for mesh_to_bake, data_array in u.items():
                        bake_data_normal(mesh_to_bake, data_array)
                else:
                    pass

    # handle packing...

    ########
    # MESH #

    success, msg, objs_to_export = post_process_bake_selection(context, meshes, empties)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    if settings.export_mesh:
        success, msg, mesh_path = export_mesh(context, bake_name, objs_to_export)
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

    add_bake_report("success", True)

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

def bake_data_uv(obj: bpy.types.Object, data_array: float, uv_index: int, uv_channel: str, uv_name: str, invert_v: bool = True) -> bool:
    """ Writes a float (data) to a specific UVMap at a specific channel of a given object, or to its vertex color at a specific color channel """

    if uv_index < 0 or uv_index > 7:
        return False

    if not data_array:
        return False

    # create & zero uvmap(s) if needed @TODO ensure this works correctly
    while (uv_index > (len(obj.data.uv_layers) - 1)):
        obj.data.uv_layers.new()
        uvmap_index = len(obj.data.uv_layers) - 1

        for face in obj.data.polygons:
            for loop_id in face.loop_indices:
                obj.data.uv_layers[uvmap_index].data[loop_id].uv = (0.0, 1.0 if invert_v else 0.0)

    uv_name = uv_name if uv_name != "" else "UVMap.BakedData"
    uv_name += "." + str(uv_index)
    obj.data.uv_layers[uv_index].name = uv_name

    if uv_channel == "U":
        index = 0
        invert_v = False
    else:
        index = 1

    for loop_id in data_array:
        print(loop_id)
        if len(data_array) == 1:
            data_to_bake = data_array[0]
        elif len(data_array) == 2:
            data_to_bake = get_packed_16_16_ab(data_array[0], data_array[1])
        else:
            data_to_bake = get_packed_16_16_ab(data_array[0], data_array[1], data_array[2])
        
        obj.data.uv_layers[uv_index].data[loop_id].uv[index] = (1.0 - data_to_bake) if invert_v else data_to_bake
    
    return True

def bake_data_vcol(obj: bpy.types.Object, data_array: float, rgba: str) -> bool:
    """ Writes a float (data) to a specific UVMap at a specific channel of a given object, or to its vertex color at a specific color channel """

    if not data_to_bake:
        return False

    if obj.data.vertex_colors:
        vcol = obj.data.vertex_colors.active
    else:
        vcol = obj.data.vertex_colors.new()
    
        for face in obj.data.polygons:
            for loop_id in face.loop_indices:
                vcol.data[loop_id].color = [0.0, 0.0, 0.0, 0.0]

    for loop_id, data in data_to_bake:
        if rgba == "R":
            vcol.data[loop_id].color[0] = data # @TODO need to remap
        elif rgba == "G":
            vcol.data[loop_id].color[1] = data
        elif rgba == "B":
            vcol.data[loop_id].color[2] = data
        elif rgba == "A":
            vcol.data[loop_id].color[3] = data

    return True

def bake_data_normal(obj: bpy.types.Object, data_array: float) -> bool:
    """ Writes a float (data) to a specific UVMap at a specific channel of a given object, or to its vertex color at a specific color channel """

    #obj.data.use_auto_smooth = True # @DEPRECATED in 4.1, used to be required to use custom normals

    for face in obj.data.polygons:
        face.use_smooth = True

    # create and assign normal buffer
    normals = []
    for vertex in obj.data.vertices: # @TODO we might need to duplicate verts? (rand per face)
        normals.append(data_to_bake)

    obj.data.normals_split_custom_set_from_vertices(normals)
    return True

##################
### DATA LAYER ###
def get_data_layer_sanity_disallow_packing(data_layer: DATABAKER_PG_DataLayerPropertyGroup) -> bool:
    """
    Return true if the data_layer's storage_mode doesn't allow other layers to be bit-packed into it, false else
    """
    if get_data_layer_sanity_ask_for_packing(data_layer):
        return False

    return data_layer.storage_mode == "VCOL"

def get_data_layer_sanity_ask_for_packing(data_layer: DATABAKER_PG_DataLayerPropertyGroup) -> bool:
    """
    Return true if the data_layer's storage_mode indicates that the layer should be packed into another layer,  false else
    """
    return data_layer.storage_mode == "FRACTION" or data_layer.storage_mode == "AB" or data_layer.storage_mode == "XYZ"

def get_data_layer_sanity_empty_ptr_id(data_layer: DATABAKER_PG_DataLayerPropertyGroup) -> bool:
    """
    Return true if the data_layer's ptr_ID is empty, false else
    """
    return data_layer.ptr_ID == ""

def get_data_layer_sanity_self_ptr_id(data_layer: DATABAKER_PG_DataLayerPropertyGroup) -> bool:
    """
    Return true if the data_layer's ptr_ID is the same as it's ID, false else
    """
    return data_layer.ptr_ID == data_layer.ID

def get_data_layer_sanity_packing_target(data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list) -> DATABAKER_PG_DataLayerPropertyGroup:
    """
    Return the first data_layer in the data_layers list which ID matches the given data_layer's ptr_ID
    """
    return next(target_data_layer for target_data_layer in data_layers if target_data_layer.ID == data_layer.ptr_ID)

def get_data_layer_sanity_is_self(data_layer: DATABAKER_PG_DataLayerPropertyGroup, other_data_layer: DATABAKER_PG_DataLayerPropertyGroup) -> bool:
    """ 
    Return true if the data_layer ptr and other_data_layer ptr point to the same object
    """
    return data_layer == other_data_layer

def get_data_layer_sanity_packing(target_data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list) -> tuple[bool, str, list]:
    """
    Find all layers targeting the given data_layer and see if all use the same packing mode and that all ask to be bit-packed in different components
    """
    layers_sharing_target = [layer for layer in data_layers if layer.ptr_ID == target_data_layer.ID]

    if not layers_sharing_target:
        (True, get_data_layer_name(target_data_layer) + " isn't asked to pack other layers", None)

    layers_packed_in_a = []
    layers_packed_in_b = []
    layers_packed_in_c = []

    # ignore potential packing errors and just build lists first
    for sibling_data_layer in layers_sharing_target:
        if sibling_data_layer.storage_mode == "FRACTION" or (sibling_data_layer.storage_mode == "AB" and sibling_data_layer.pack_ab == "A") or (sibling_data_layer.storage_mode == "XYZ" and sibling_data_layer.pack_xyz == "X"):
            layers_packed_in_a.append(sibling_data_layer)
        elif (sibling_data_layer.storage_mode == "AB" and sibling_data_layer.pack_ab == "B") or (sibling_data_layer.storage_mode == "XYZ" and sibling_data_layer.pack_xyz == "Y"):
            layers_packed_in_b.append(sibling_data_layer)
        elif (sibling_data_layer.storage_mode == "XYZ" and sibling_data_layer.pack_xyz == "Z"):
            layers_packed_in_c.append(sibling_data_layer)
        else:
            pass

    packing = [layers_packed_in_a, layers_packed_in_b, layers_packed_in_c]

    # check for potential packing errors
    for packed_layers_component, packed_layers in enumerate([layers_packed_in_a, layers_packed_in_b, layers_packed_in_c]):
        packed_layers_names = [layer.ID for layer in packed_layers]
        packed_layers_component_name = "A" if packed_layers_component == 0 else "B" if packed_layers_component == 1 else "C"

        # can't pack more than one layer per component
        if len(packed_layers) > 1:
            return (False, "Packing error with " + get_data_layer_name(target_data_layer) + ": multiple layers packed in component " + packed_layers_component_name + ": " + ','.join(packed_layers_names), packing)

        # ensure packing mode is consistent
        for packed_layer in packed_layers:
            if packed_layer.storage_mode != packed_layer.storage_mode:
                return (False, "Packing error with " + get_data_layer_name(target_data_layer) + ": target " + get_data_layer_name(packed_layer) + " don't share the packing mode", packing)

    packed_layers_names = [layer.ID for layer in packed_layers for packed_layers in packing]

    return (True, get_data_layer_name(target_data_layer) + "successfully packing other layers: " + ','.join(packed_layers_names), packing)

def get_data_layer_sanity_channel(data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list) -> tuple[bool, str]:
    """
    Check if the data_layer's storage_mode don't conflict with other layers: UV index & U/V channel, VCOL R/G/B/A channel, NORMAL X/Y/Z component
    """
    if data_layer.storage_mode == "UV":
        if data_layer.uv_index > 7:
            return (False, "Packing error with " + get_data_layer_name(data_layer) + ": can't have " + str(data_layer.uv_index + 1) + " UVMaps")

        uv_components = []
        for data_layer in data_layers:
            layer_index = data_layer.uv_index * 2 + (0 if data_layer.uv_channel == "U" else 1)
            if data_layer.storage_mode == "UV" and (layer_index in uv_components):
                return (False, "Packing error with " + get_data_layer_name(data_layer) + ": UVMap " + str(data_layer.uv_index) + " channel " + data_layer.uv_channel + " is already used")
            else:
                uv_components.append(layer_index)
    elif data_layer.storage_mode == "VCOL":
        vcol_components = []
        for data_layer in data_layers:
            if data_layer.storage_mode == "VCOL" and (data_layer.vcol_rgba in vcol_components):
                return (False, "Packing error with " + get_data_layer_name(data_layer) + ": " + data_layer.vcol_rgba + " already targeted")
            else:
                vcol_components.append(data_layer.vcol_rgba)
    elif data_layer.storage_mode == "NORMAL":
        normal_components = []
        for data_layer in data_layers:
            if data_layer.storage_mode == "NORMAL" and (data_layer.normal_xyz in normal_components):
                return (False, "Packing error with " + get_data_layer_name(data_layer) + ": Normal " + str(data_layer.normal_xyz) + " is already used")
            else:
                normal_components.append(data_layer.normal_xyz)
    else:
        return (True, "")

    return (True, "")

def get_data_layer_sanity(data_layer: DATABAKER_PG_DataLayerPropertyGroup, data_layers: list) -> tuple[bool, str, list]:
    """ 
    If layer is meant to be 'packed', the layer itself will be 'discarded', because included in the bake process
    when the targeted layer itself is baked. So we just need to check the validity of this data layer's target.
    """
    if not data_layer:
        return (False, "Invalid data layer", None)

    # data layer might "be packed into another layer"
    if get_data_layer_sanity_ask_for_packing(data_layer): # FRACTION, AB, XYZ?
        if get_data_layer_sanity_empty_ptr_id(data_layer): # null ptr_ID?
            return (False, "Packing error with " + get_data_layer_name(data_layer) + ": no target specified", None)
        if get_data_layer_sanity_self_ptr_id(data_layer): # ptr_ID == ID?
            return (False, "Packing error with " + get_data_layer_name(data_layer) + ": targeting itself (ID)", None)

        # get target!
        data_layer_target = get_data_layer_sanity_packing_target(data_layer, data_layers) # ptr_ID -> target
        if data_layer_target:
            if get_data_layer_sanity_is_self(data_layer, data_layer_target): # target == self?
                return (False, "Packing error with " + get_data_layer_name(data_layer_target) + ": targeting itself (Layer)", None)
            if get_data_layer_sanity_disallow_packing(data_layer_target): # target FRACTION, AB, XYZ or VCOL?
                return (False, "Packing error with " + get_data_layer_name(data_layer_target) + ": is targeted by " + get_data_layer_name(data_layer) + " but don't allow bit-packing", None)

            return get_data_layer_sanity_packing(data_layer_target, data_layers)
        else:
            return (False, "Packing error with " + get_data_layer_name(data_layer) + ": target specified couldn't be found", None)
    else: # data layer might "pack other layers"
        success, msg, packing = get_data_layer_sanity_packing(data_layer, data_layers)
        if not success:
            return (False, msg, packing)

        success, msg = get_data_layer_sanity_channel(data_layer, data_layers)
        if not success:
            return (False, msg, None)

        return (True, "", None)

def get_data_layers_sanity_ids_sane(data_layers: list) -> bool:
    """
    Return true if layers all have unique IDs, false else
    """
    ids = []
    for data_layer in data_layers:
        if data_layer.ID == "":
            return (False, "Empty ID")
        elif data_layer.ID not in ids:
            ids.append(data_layer.ID)
        else:
            return (False, "Duplicated IDs")
    
    return (True, "")

def get_data_layers_sanity(context: bpy.types.Context) -> tuple[bool, str, DATABAKER_PG_DataLayerPropertyGroup]:
    """

    """
    settings = context.scene.DataBakerSettings

    success, msg = get_data_layers_sanity_ids_sane(settings.data_layers)
    if not success:
        return (False, msg)

    for data_layer in settings.data_layers:
        success, msg, _ = get_data_layer_sanity(data_layer, settings.data_layers)
        if not success:
            return (False, msg)

    return (True, "")

def get_data_layers_uv_maps(context: bpy.types.Context) -> tuple[list, list]:
    """ """
    settings = context.scene.DataBakerSettings
    uvmap_name = settings.uvmap_name if settings.uvmap_name != "" else "UVMap.BakedData"

    data_layers_uv = [d for d in settings.data_layers if d.storage_mode == "UV"]
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

def get_data_layer_storage_mode_icon(item: DATABAKER_PG_DataLayerPropertyGroup) -> str:
    """ """
    if item:
        if item.storage_mode == "UV":
            return "UV"
        elif item.storage_mode == "VCOL":
            return "GROUP_VCOL"
        elif item.storage_mode == "NORMAL":
            return "NORMALS_FACE"
        else:
            return "DOT"

    return "X"

def get_data_layer_packing_mode_icon(data: list, item: DATABAKER_PG_DataLayerPropertyGroup) -> str:
    """ """
    if item:
        if item.storage_mode == "AB" or item.storage_mode == "XYZ" or item.storage_mode == "FRACTION":
            if item.ptr_ID == "":
                return "QUESTION"
            else: # packed in target data
                return "COPYDOWN"
        else:
            if item.storage_mode == "AB":
                return "OVERLAY"
            elif item.storage_mode == "XYZ":
                return "THREE_DOTS"
            elif item.storage_mode == "FRACTION":
                return "PIVOT_ACTIVE"
            else:
                pass

    return "DOT"

def copy_data_layer(to_data_layer: DATABAKER_PG_DataLayerPropertyGroup, from_data_layer: DATABAKER_PG_DataLayerPropertyGroup) -> bool:
    """ """
    if to_data_layer and from_data_layer:
        to_data_layer.data = from_data_layer.data
        
        # automatically wrap XYZ component
        to_data_layer.component = "X" if from_data_layer.component == "Z" else "Y" if from_data_layer.component == "X" else "Z"
        
        # automatically wrap uv/vcol rgba/normal xyz
        to_data_layer.storage_mode = from_data_layer.storage_mode
        if from_data_layer.storage_mode == "UV":
            to_data_layer.uv_channel = "U" if from_data_layer.uv_channel == "V" else "V"
            to_data_layer.uv_index = from_data_layer.uv_index + 1 if from_data_layer.uv_channel == "V" else from_data_layer.uv_index
        elif from_data_layer.storage_mode == "VCOL":
            to_data_layer.vcol_rgba = "A" if from_data_layer.vcol_rgba == "B" else "B" if from_data_layer.vcol_rgba == "G" else "G" if from_data_layer.vcol_rgba == "R" else "R"
        elif from_data_layer.storage_mode == "NORMAL":
            to_data_layer.normal_xyz = "Z" if from_data_layer.normal_xyz == "Y" else "Y" if from_data_layer.normal_xyz == "X" else "X"
        else:
            pass

        to_data_layer.pack_a_b = from_data_layer.pack_a_b
        to_data_layer.pack_x_y_z = from_data_layer.pack_x_y_z
        to_data_layer.pack_only_if_non_null = from_data_layer.pack_only_if_non_null

        to_data_layer.axis = from_data_layer.axis
        to_data_layer.axis_mode = from_data_layer.axis_mode
        to_data_layer.axis_obj = from_data_layer.obj

        to_data_layer.name = from_data_layer.name

        to_data_layer.obj = from_data_layer.obj

        to_data_layer.shapekey_mode = from_data_layer.shapekey_mode
        
        to_data_layer.mask_mode = from_data_layer.mask_mode

        to_data_layer.normalize = from_data_layer.normalize
        to_data_layer.clamp = from_data_layer.clamp
        to_data_layer.falloff = from_data_layer.falloff
        to_data_layer.uniform = from_data_layer.uniform

        to_data_layer.origin_mode = from_data_layer.origin_mode

        to_data_layer.rand_mode = from_data_layer.rand_mode
        to_data_layer.rand_seed = from_data_layer.rand_seed
        to_data_layer.rand_float_mode = from_data_layer.rand_float_mode

        to_data_layer.x = from_data_layer.x
        to_data_layer.y = from_data_layer.y
        to_data_layer.z = from_data_layer.z
        to_data_layer.index = from_data_layer.index

        return True
    return False

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

        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_loop_ids.append((loop_id, data_to_bake))
        bake_data.append((mesh, data_loop_ids))
    return bake_data

def get_bake_axis(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    
    bake_data = []

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

        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                data_loop_ids.append((loop_id, data_to_bake))
        bake_data.append((mesh, data_loop_ids))
    return bake_data

def get_bake_shapekey(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    # @TODO rework way shapekeys offset & normal are computed
    settings = context.scene.DataBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []

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
                    data_loop_ids.append((loop_id, vector_to_bake.x))
                elif data_layer.component == "Y":
                    data_loop_ids.append((loop_id, vector_to_bake.y))
                elif data_layer.component == "Z":
                    data_loop_ids.append((loop_id, vector_to_bake.z))
                else:
                    pass

        bake_data.append((mesh, data_loop_ids))
    return bake_data

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
        return (None, None)

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

                data_loop_ids.append((loop_id, data_to_bake))

        bake_data.append((mesh, data_loop_ids))
    return bake_data

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

                data_loop_ids.append((loop_id, data_to_bake))

        bake_data.append((mesh, data_loop_ids))
    return bake_data

def get_bake_random(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    if data_layer.rand_float_mode == "FLOAT":
        return get_bake_random_float(context, data_layer, meshes, empties)
    elif data_layer.rand_float_mode == "FLOAT2":
        return get_bake_random_float2(context, data_layer, meshes, empties)
    elif data_layer.rand_float_mode == "FLOAT3":
        return get_bake_random_float3(context, data_layer, meshes, empties)
    else:
        return (None, None)

def get_bake_random_float(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    settings = context.scene.DataBakerSettings

    bake_data = []

    uniform_values = []
    uniform_length = 0

    if data_layer.rand_mode == "COLLECTION":
        cols = []
        for mesh in meshes:
            print(mesh.users_collection)
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
                    data_loop_ids.append((loop_id, data_to_bake))
        elif data_layer.rand_mode == "OBJECT":
            data_to_bake = (uniform_values[mesh_index] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append((loop_id, data_to_bake))
        elif data_layer.rand_mode == "FACE":
            for face_index, face in enumerate(mesh.data.polygons):
                data_to_bake = (uniform_values[face_index +face_offset] * data_layer.uniform) + ((1 - data_layer.uniform) * random.uniform(0,1)) # blend between uniform random and completely random

                for loop_id in face.loop_indices:
                    data_loop_ids.append((loop_id, data_to_bake))

            face_offset += len(mesh.data.polygons)

        bake_data.append((mesh, data_loop_ids))
    return bake_data

def get_bake_random_float2(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    settings = context.scene.DataBakerSettings

    bake_data = []

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
                    data_loop_ids.append((loop_id, data_to_bake))

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
                    data_loop_ids.append((loop_id, data_to_bake))

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
                    data_loop_ids.append((loop_id, data_to_bake))
                
            face_offset += len(mesh.data.polygons)

            bake_data.append((mesh, data_loop_ids))
    else:
        pass

    return bake_data

def get_bake_random_float3(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """"""
    settings = context.scene.DataBakerSettings

    bake_data = []

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
                    data_loop_ids.append((loop_id, data_to_bake))

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
                    data_loop_ids.append((loop_id, data_to_bake))

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
                    value_to_bake = np.sin( theta) * np.cos( phi )
                elif data_layer.component == "Y":
                    value_to_bake = np.sin( theta) * np.sin( phi )
                elif data_layer.component == "Z":
                    value_to_bake = np.cos( theta )
                else:
                    value_to_bake = 0.0

                for loop_id in face.loop_indices:
                    data_loop_ids.append((loop_id, value_to_bake))

            face_offset += len(mesh.data.polygons)

            bake_data.append((mesh, data_loop_ids))
    else:
        pass

    return bake_data

def get_bake_parent_pos(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    bake_data = []

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

        if parent:
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
                    data_loop_ids.append((loop_id, data_to_bake))
            bake_data.append((mesh, data_loop_ids))
    return bake_data

def get_bake_parent_axis(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))

    bake_data = []

    target_depth = max(1, settings.index)
    for mesh in meshes:
        data_loop_ids = []

        parent = mesh                
        for depth in range(target_depth):
            if parent.parent and (parent.parent.type == 'MESH' or parent.parent.type == 'EMPTY'):
                parent = parent.parent
            else:
                parent = None
        
        if parent:
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
                    data_loop_ids.append((loop_id, data_to_bake))
            bake_data.append((mesh, data_loop_ids))
    return bake_data

def get_bake_value(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

    bake_data = []

    for mesh in meshes:
        data_loop_ids = []
        for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append((loop_id, data_layer.x))
        bake_data.append((mesh, data_loop_ids))

    return bake_data

def get_bake_custom_prop(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    settings = context.scene.DataBakerSettings

    bake_data = []

    for mesh in meshes:
        data_loop_ids = []

        prop = mesh.get(data_layer.custom_prop_name, None)
        if prop and ((type(prop) is int) or (type(prop) is float)):
            data_to_bake = prop
        else:
            data_to_bake = 0.0

        for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    data_loop_ids.append((loop_id, data_to_bake))
        bake_data.append((mesh, data_loop_ids))

    return bake_data

def get_bake_none(context: bpy.types.Context, data_layer: DATABAKER_PG_DataLayerPropertyGroup, meshes: list, empties: list) -> list:
    """ """
    return []

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
    
    for mesh_uvmap in report.mesh_uvmaps:
        uv_sub_el = ET.SubElement(uv_el, "UVMap", name=mesh_uvmap.name, id=mesh_uvmap.ID)

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