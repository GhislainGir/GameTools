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
import uuid
import time

XYZUNITVECTOR = mathutils.Vector((1.0, 1.0, 1.0))
HALFXYZVECTOR = mathutils.Vector((0.5, 0.5, 0.5))
XYZLIST = ["X", "Y", "Z"]
XYZVECTORS = {
    "X": mathutils.Vector((1.0, 0.0, 0.0)),
    "Y": mathutils.Vector((0.0, 1.0, 0.0)),
    "Z": mathutils.Vector((0.0, 0.0, 1.0)),
}

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################

##############
### REPORT ###
def new_bake_report(context):
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

    add_bake_report("transform_obj", settings.transform_obj)
    
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

    report.transform_obj = None

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

def add_bake_report(prop_name, prop_value):
    """ """
    setattr(bpy.context.scene.DataBakerReport, prop_name, prop_value)

def add_bake_report_uv(ID, name):
    """ """
    settings = bpy.context.scene.DataBakerSettings
    report = bpy.context.scene.DataBakerReport

    report_uvmap = report.mesh_uvmaps.add()
    report_uvmap.ID = ID
    report_uvmap.name = name

def export_bake_report(context):
    """ """
    return(export_xml(context))

###################
### MULTIPLIERS ###
def get_position_data_needs_multiplier(context):
    """ """
    
    settings = context.scene.DataBakerSettings
    return settings.position and (settings.position_channel_mode == "AB_PACKED" or settings.position_channel_mode == "XYZ_PACKED" or settings.position_x_mode == "VCOL" or settings.position_y_mode == "VCOL" or settings.position_z_mode == "VCOL")

def get_position_data_multiplier(context):
    """ Loop through all selected objects (or just the specified transform object) and return the largest absolute X, Y or Z position """
    
    settings = context.scene.DataBakerSettings

    objs = [settings.transform_obj] if settings.transform_obj else context.selected_objects # baking a specified object's location or each object's location?

    largest_component = 0.0
        
    for obj in objs:
        # only allow selected objects of types MESH or EMPTY to be processed, but allow all types for the specified object, if any
        if obj.type == 'MESH' or obj.type == 'EMPTY' or settings.transform_obj != None:
            obj_location = obj.matrix_world.to_translation()
            if settings.origin:
                obj_location -= settings.origin.matrix_world.to_translation() # make position relative to a specified origin, if any
            
            largest_component = max(largest_component, max(math.fabs(obj_location.x), max(math.fabs(obj_location.y), math.fabs(obj_location.z))))
   
    if largest_component > 0.0:
        largest_component += settings.precision_offset
        largest_component *= settings.scale
    
    # round to the nearest integer. No point in annoying the user with a more precise float value which might be annoying to copy & paste into the engine
    return max(math.ceil(largest_component), 1)

def get_shapekey_offset_data_needs_multiplier(context):
    """ """
    
    settings = context.scene.DataBakerSettings
    return settings.shapekey_offset and (settings.shapekey_offset_channel_mode == "AB_PACKED" or settings.shapekey_offset_channel_mode == "XYZ_PACKED" or settings.shapekey_offset_x_mode == "VCOL" or settings.shapekey_offset_y_mode == "VCOL" or settings.shapekey_offset_z_mode == "VCOL")

def get_shapekey_offset_data_multiplier(context):
    """ Loop through all selected objects to return the largest absolute X, Y or Z shapekey offset """
    
    settings = context.scene.DataBakerSettings

    largest_component = 0.0
    
    for obj in context.selected_objects:
        if obj.data.shape_keys and (settings.shapekey_name in obj.data.shape_keys.key_blocks) and (settings.shapekey_rest_name in obj.data.shape_keys.key_blocks):
            """
            initial_shape_keys = []
            for shape_key in obj.data.shape_keys.key_blocks:
                initial_shape_keys.append((shape_key.name, shape_key.value)) # cache shapekeys
                if shape_key.name == settings.shapekey_name:
                    shape_key.value = 1.0
                else:
                    shape_key.value = 0.0
            """
            for face in obj.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = obj.data.loops[loop_id].vertex_index

                    shapekey_vertex_pos = obj.data.shape_keys.key_blocks[settings.shapekey_name].data[vertex_index].co
                    shapekey_rest_vertex_pos = obj.data.shape_keys.key_blocks[settings.shapekey_rest_name].data[vertex_index].co

                    offset = shapekey_vertex_pos - shapekey_rest_vertex_pos

                    largest_component = max(largest_component, max(math.fabs(offset.x), max(math.fabs(offset.y), math.fabs(offset.z))))
            """
            for shape_key_name, shape_key_value in initial_shape_keys:
                obj.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value # restore shapekeys
            """

    if largest_component > 0.0:
        largest_component += settings.precision_offset
        largest_component *= settings.scale

    # round to the nearest integer. No point in annoying the user with a more precise float value which might be annoying to copy & paste into the engine
    return max(math.ceil(largest_component), 1.0)

def get_parent_position_data_needs_multiplier(context):
    """ """

    settings = context.scene.DataBakerSettings
    return settings.parent_position and (settings.parent_position_channel_mode == "AB_PACKED" or settings.parent_position_channel_mode == "XYZ_PACKED" or settings.parent_position_x_mode == "VCOL" or settings.parent_position_y_mode == "VCOL" or settings.parent_position_z_mode == "VCOL")

def get_parent_position_data_multiplier(context):
    """ """

    settings = context.scene.DataBakerSettings

    # make sure user specified valid depth
    if settings.parent_max_depth <= 0:
        return 0.0

    manual_max_depth = max(min(settings.parent_depth, settings.parent_max_depth), 1.0)

    objs = [settings.transform_obj] if settings.transform_obj else context.selected_object # baking a specified object's parent's location or all selected object's parent's location?
    
    # if we pack parent's position using ABPacking OR XYZPacking OR Individual + Vertex Color, we need to normalize the baked positions to [0:1] and thus first need to find the most distant position's X/Y/Z component as a global divisor
    largest_component = 0.0
    
    for obj in objs:
        parent_obj = obj

        # walk up the hierarchy until we can't find a parent but no more than the specified max hierarchy depth
        for depth_index in range(settings.parent_max_depth):
            # if object is valid AND so is its parent AND that parent is either a MESH or an EMPTY
            if parent_obj and parent_obj.parent and (parent_obj.parent.type == 'MESH' or parent_obj.parent.type == 'EMPTY'):
                # only process the desired depth if in manual mode
                if settings.parent_mode == "MANUAL":
                    if depth_index != (manual_max_depth + 1):
                        continue
                
                # have we found a new parent?
                parent_obj = parent_obj.parent
                if parent_obj == None:
                    break
                
                parent_obj_location = parent_obj.matrix_world.to_translation()
                if settings.origin:
                    parent_obj_location -= settings.origin.matrix_world.to_translation()

                # cache the largest absolute position X/Y/Z component
                largest_component = max(largest_component, max(math.fabs(parent_obj_location.x), max(math.fabs(parent_obj_location.y), math.fabs(parent_obj_location.z))))
            else:
                break

    if largest_component > 0:
        largest_component += settings.precision_offset
        largest_component *= settings.scale
    
    # round to the nearest integer. No point in annoying the user with a more precise float value which might be annoying to copy & paste into the engine
    return max(math.ceil(largest_component), 1)

###############
### PACKING ###
def get_packed_xyz_vector(unit_vector):
    """ Algorithm to pack three normalized floats into one. Results in *severe* precision loss and probably isn't practical to encode data like positions """

    return (math.ceil(unit_vector.x * 100) * 10) + (math.ceil(unit_vector.y * 100) * 0.1) + (math.ceil(unit_vector.z * 100) * 0.001)

def get_packed_ab_vector(unit_vector, a_component, b_component):
    """ Algorithm to pack two normalized floats into one. Gives acceptable precision loss unless numbers are large-ish """

    a = unit_vector.x if a_component == "X" else unit_vector.y if a_component == "Y" else unit_vector.z
    a = math.floor(a * (4096 - 1)) * 4096    

    b = unit_vector.x if b_component == "X" else unit_vector.y if b_component == "Y" else unit_vector.z
    b = math.floor(b * (4096 - 1))

    return (a + b)

############
### BAKE ###
def get_bake_axis(quat, component, sign, remap, default = "Z"):
    """ """

    axis_to_bake = (quat @ XYZVECTORS["X"]) if component == "X" else (quat @ XYZVECTORS["Y"]) if component == "Y" else (quat @ XYZVECTORS["Z"]) * sign
    
    if (axis_to_bake.length < 0.001): # safe to normalize?
        axis_to_bake = XYZVECTORS[default]

    if remap:
        axis_to_bake = (axis_to_bake + XYZUNITVECTOR) * 0.5 # remap vector from [-1:1] to [0:1]

    return axis_to_bake

def get_bake_selection(context):
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
    uvmap_name = settings.uvmap_name if settings.uvmap_name != "" else "UVMap.BakedData"
    bake_uvmaps = []

    # get list of expected uvmaps
    info_uv, info_vcol, info_normal = get_bake_info(context)
    for uvmap_info in info_uv:
        ID, uv_index, uv_channel, is_packed, is_32_bits, has_multiplier, channel_mode = uvmap_info
        name_to_find = uvmap_name + "." + str(uv_index)
        if name_to_find not in bake_uvmaps:
            bake_uvmaps.append(name_to_find)
            add_bake_report_uv(ID, name_to_find)

    add_bake_report("mesh_uvmap_count", len(bake_uvmaps))

    if settings.invert_v:
        add_bake_report("mesh_uvmap_invert_v", True)

    obj_uvmaps = []
    for obj in objs_to_bake:
        if any(uvmap_name in obj.data.uv_layers for uvmap_name in bake_uvmaps): # UVMap exists?
            pass
        elif len(obj.data.uv_layers) >= 8: # ensure UVMap can be created
            return (False, obj.name + " has the maximum amount of uvmaps already", None, None)

        for uvlayer in obj.data.uv_layers: # gather uvmaps as if objects were joined
            if uvlayer.name not in obj_uvmaps:
                obj_uvmaps.append(uvlayer.name)

    if not any(uvmap_name in obj_uvmaps for uvmap_name in bake_uvmaps) and settings.merge_mesh and len(obj_uvmaps) >= 8:
        return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None)

    context.view_layer.objects.active = None # blank canvas

    return (True, "", objs_to_bake, active_obj)

def get_bake_name(context, active_object):
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

def pre_process_bake_selection(context, objs_to_bake):
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

def post_process_bake_selection(context, meshes, empties):
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

def bake(context):
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

    for bake_function in get_bake_functions():
        bake_function(context, meshes, empties)

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

def bake_data(obj, bake_data, bake_mode, uv_index, uv_channel, uv_name, rgba, invert_v = True, bake_loop_id = -1):
    """ Writes a float (data) to a specific UVMap at a specific channel of a given object, or to its vertex color at a specific color channel """

    if uv_index < 0 or uv_index > 7:
        return False

    if bake_mode == "UV":
        # create & zero uvmap(s) if needed
        while (uv_index > (len(obj.data.uv_layers) - 1)):
            obj.data.uv_layers.new()
            uvmap_index = len(obj.data.uv_layers) - 1
            
            for face in obj.data.polygons:
                for loop_id in face.loop_indices:
                    obj.data.uv_layers[uvmap_index].data[loop_id].uv = (0.0, 1.0 if invert_v else 0.0)
        
        uv_name = uv_name if uv_name != "" else "UVMap.BakedData"
        uv_name += "." + str(uv_index)
        obj.data.uv_layers[uv_index].name = uv_name
    elif rgba == "R" or rgba == "G" or rgba == "B" or rgba == "A" or rgba == "RGB" or rgba == "RG":
        if obj.data.vertex_colors:
            vcol = obj.data.vertex_colors.active
        else:
            vcol = obj.data.vertex_colors.new()
            
            for face in obj.data.polygons:
                for loop_id in face.loop_indices:
                    vcol.data[loop_id].color = [0.0, 0.0, 0.0, 0.0]

    elif bake_mode == "NORMALS":
        #obj.data.use_auto_smooth = True # @DEPRECATED in 4.1, used to be required to use custom normals

        for face in obj.data.polygons:
            face.use_smooth = True

        # create and assign normal buffer
        normals = []
        for vertex in obj.data.vertices:
            normals.append(bake_data)

        obj.data.normals_split_custom_set_from_vertices(normals)
        return True

    for face in obj.data.polygons:
        for loop_id in face.loop_indices:
            # override loop ID if one was specified. We might call this function *while* we loop through loop indices already to compute data to bake, based on polys or vertices, and so we wouldn't want to do that twice.
            # we're going to exit early those for loops if that's the case and write data just that once on the specified loop index @NOTE fix hack
            if (bake_loop_id >= 0):
                loop_id = bake_loop_id
            
            if bake_mode == "UV":
                # only set data on the specified UV channel (U or V) and preserve the other data
                if (uv_channel == "U"):
                    obj.data.uv_layers[uv_index].data[loop_id].uv[0] = bake_data
                else:
                    # need to flip UV's Y axis for Unreal!
                    obj.data.uv_layers[uv_index].data[loop_id].uv[1] = (1.0 - bake_data) if invert_v else bake_data
                
            else:
                # only set data on the specified rgba channel and preserve data on other channels
                col = vcol.data[loop_id].color
                if rgba == "R":
                    col[0] = bake_data
                elif rgba == "G":
                    col[1] = bake_data
                elif rgba == "B":
                    col[2] = bake_data
                elif rgba == "A":
                    col[3] = bake_data
                elif rgba == "RGB":
                    col[0] = bake_data.x
                    col[1] = bake_data.y
                    col[2] = bake_data.z
                elif rgba == "RG":
                    col[0] = bake_data.x
                    col[1] = bake_data.y
    
                vcol.data[loop_id].color = col
            
            # exit early if loop ID was specified and data written there just that once. We don't want to loop through loop indices here
            if (bake_loop_id >= 0):
                break
        # exit early if loop ID was specified and data written there just that once. We don't want to loop through polygons here
        if (bake_loop_id >= 0):
            break
        
    return True

######################
### BAKE FUNCTIONS ###
def get_bake_functions():
    """ """
    return [
        bake_position,
        bake_axis,
        bake_shapekey_offset,
        bake_shapekey_normal,
        bake_linear_mask,
        bake_sphere_mask,
        bake_random_value_per_collection,
        bake_random_value_per_object,
        bake_random_value_per_polygon,
        bake_parent,
        bake_fixed_value,
        bake_direction
    ]

def bake_position(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.position:
        add_bake_report("position", True)
        add_bake_report("position_channel_mode", settings.position_channel_mode)
        add_bake_report("position_x", settings.position_x)
        add_bake_report("position_x_mode", settings.position_x_mode)
        add_bake_report("position_x_uv_index", settings.position_x_uv_index)
        add_bake_report("position_x_uv_channel", settings.position_x_uv_channel)
        add_bake_report("position_x_rgba", settings.position_x_rgba)
        add_bake_report("position_y", settings.position_y)
        add_bake_report("position_y_mode", settings.position_y_mode)
        add_bake_report("position_y_uv_index", settings.position_y_uv_index)
        add_bake_report("position_y_uv_channel", settings.position_y_uv_channel)
        add_bake_report("position_y_rgba", settings.position_y_rgba)
        add_bake_report("position_z", settings.position_z)
        add_bake_report("position_z_mode", settings.position_z_mode)
        add_bake_report("position_z_uv_index", settings.position_z_uv_index)
        add_bake_report("position_z_uv_channel", settings.position_z_uv_channel)
        add_bake_report("position_z_rgba", settings.position_z_rgba)
        add_bake_report("position_packed_uv_index", settings.position_packed_uv_index)
        add_bake_report("position_packed_uv_channel", settings.position_packed_uv_channel)
        add_bake_report("position_pack_only_if_non_null", settings.position_pack_only_if_non_null)
        add_bake_report("position_ab_packed_a_comp", settings.position_ab_packed_a_comp)
        add_bake_report("position_ab_packed_b_comp", settings.position_ab_packed_b_comp)
    else:
        return False

    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    # data might need a 'multiplier' to be normalized and packed/unpacked
    packing_multiplier = get_position_data_multiplier(context) if get_position_data_needs_multiplier(context) else 1.0
    packing_divisor = 1.0 / packing_multiplier
    add_bake_report("position_multiplier", packing_multiplier)

    for mesh in meshes:
        ref_obj = settings.transform_obj if settings.transform_obj else mesh # use specified object if any, else use self
        loc = ref_obj.matrix_world.to_translation() # get object's location and make it relative to specified origin, if any
        if settings.origin:
            loc -= settings.origin.matrix_world.to_translation()
        loc_to_bake = loc * signed_scale

        if settings.position_channel_mode == "INDIVIDUAL":
            # packing axis is only available if we pack X/Y/Z components individually
            if settings.axis and settings.axis_channel_mode == "POSITION_PACKED":
                quat = ref_obj.matrix_world.to_quaternion()

                axis_to_bake = get_bake_axis(quat, settings.axis_component, signed_axis, True)

                # round position & pack axis in fractional part
                loc_to_bake.x = math.floor(loc_to_bake.x) + axis_to_bake.x
                loc_to_bake.y = math.floor(loc_to_bake.y) + axis_to_bake.y
                loc_to_bake.z = math.floor(loc_to_bake.z) + axis_to_bake.z

            # X POSITION
            if settings.position_x:
                data_to_bake = loc_to_bake.x

                if settings.position_x_mode == "VCOL":
                    data_to_bake = data_to_bake * packing_divisor
                    data_to_bake = (data_to_bake + 1) * 0.5

                bake_data(mesh, data_to_bake, settings.position_x_mode, settings.position_x_uv_index, settings.position_x_uv_channel, settings.uvmap_name, settings.position_x_rgba, settings.invert_v)

            # Y POSITION
            if settings.position_y:
                data_to_bake = loc_to_bake.y

                if settings.position_y_mode == "VCOL":
                    data_to_bake = data_to_bake * packing_divisor
                    data_to_bake = (data_to_bake + 1) * 0.5

                bake_data(mesh, data_to_bake, settings.position_y_mode, settings.position_y_uv_index, settings.position_y_uv_channel, settings.uvmap_name, settings.position_y_rgba, settings.invert_v)

            # Z POSITION
            if settings.position_z:
                data_to_bake = loc_to_bake.z

                if settings.position_z_mode == "VCOL":
                    data_to_bake = data_to_bake * packing_divisor
                    data_to_bake = (data_to_bake + 1) * 0.5

                bake_data(mesh, data_to_bake, settings.position_z_mode, settings.position_z_uv_index, settings.position_z_uv_channel, settings.uvmap_name, settings.position_z_rgba, settings.invert_v)
        # PACKED
        else:
            remapped_loc = mathutils.Vector((
                max(min(loc_to_bake.x * packing_divisor, 1.0), -1.0),
                max(min(loc_to_bake.y * packing_divisor, 1.0), -1.0),
                max(min(loc_to_bake.z * packing_divisor, 1.0), -1.0))
                )

            normalized_loc = (remapped_loc + XYZUNITVECTOR) * 0.5

            data_to_bake = 0.0
            # X/Y or X/Z or Y/Z POSITION
            if settings.position_channel_mode == "AB_PACKED":
                data_to_bake = get_packed_ab_vector(normalized_loc, settings.position_ab_packed_a_comp, settings.position_ab_packed_b_comp)
            # XYZ POSITION
            elif settings.position_channel_mode == "XYZ_PACKED":
                data_to_bake = get_packed_xyz_vector(normalized_loc)

            if settings.position_pack_only_if_non_null:
                if loc_to_bake.length < 0.01:
                    data_to_bake = 0.0 # @NOTE might be interesting to report in case this behaves unexpectedly?

            bake_data(mesh, data_to_bake, "UV", settings.position_packed_uv_index, settings.position_packed_uv_channel, settings.uvmap_name, 0, settings.invert_v)

    return True   

def bake_axis(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.axis and settings.axis_channel_mode != "POSITION_PACKED":
        add_bake_report("axis", True)
        add_bake_report("axis_component", settings.axis_component)
        add_bake_report("axis_channel_mode", settings.axis_channel_mode)
        add_bake_report("axis_x", settings.axis_x)
        add_bake_report("axis_x_mode", settings.axis_x_mode)
        add_bake_report("axis_x_uv_index", settings.axis_x_uv_index)
        add_bake_report("axis_x_uv_channel", settings.axis_x_uv_channel)
        add_bake_report("axis_x_rgba", settings.axis_x_rgba)
        add_bake_report("axis_y", settings.axis_y)
        add_bake_report("axis_y_mode", settings.axis_y_mode)
        add_bake_report("axis_y_uv_index", settings.axis_y_uv_index)
        add_bake_report("axis_y_uv_channel", settings.axis_y_uv_channel)
        add_bake_report("axis_y_rgba", settings.axis_y_rgba)
        add_bake_report("axis_z", settings.axis_z)
        add_bake_report("axis_z_mode", settings.axis_z_mode)
        add_bake_report("axis_z_uv_index", settings.axis_z_uv_index)
        add_bake_report("axis_z_uv_channel", settings.axis_z_uv_channel)
        add_bake_report("axis_z_rgba", settings.axis_z_rgba)
        add_bake_report("axis_packed_uv_index", settings.axis_packed_uv_index)
        add_bake_report("axis_packed_uv_channel", settings.axis_packed_uv_channel)
        add_bake_report("axis_ab_packed_a_comp", settings.axis_ab_packed_a_comp)
        add_bake_report("axis_ab_packed_b_comp", settings.axis_ab_packed_b_comp)
    else:
        return False
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))

    for mesh in meshes:
        ref_obj = settings.transform_obj if settings.transform_obj else mesh
        
        ref_obj_quat = ref_obj.matrix_world.to_quaternion()
        
        axis_to_bake = get_bake_axis(ref_obj_quat, settings.axis_component, signed_axis, False)

        if settings.axis_channel_mode == "INDIVIDUAL":
            # AXIS X COMPONENT
            if settings.axis_x:
                data_to_bake = axis_to_bake.x
                
                if (settings.axis_x_mode == "VCOL"):
                    data_to_bake = (data_to_bake + 1) * 0.5

                bake_data(mesh, data_to_bake, settings.axis_x_mode, settings.axis_x_uv_index, settings.axis_x_uv_channel, settings.uvmap_name, settings.axis_x_rgba, settings.invert_v)

            # AXIS Y COMPONENT
            if settings.axis_y:
                data_to_bake = axis_to_bake.y

                if (settings.axis_y_mode == "VCOL"):
                    data_to_bake = (data_to_bake + 1) * 0.5

                bake_data(mesh, data_to_bake, settings.axis_y_mode, settings.axis_y_uv_index, settings.axis_y_uv_channel, settings.uvmap_name, settings.axis_y_rgba, settings.invert_v)

            # AXIS Z COMPONENT
            if settings.axis_z:
                data_to_bake = axis_to_bake.z

                if (settings.axis_z_mode == "VCOL"):
                    data_to_bake = (data_to_bake + 1) * 0.5

                bake_data(mesh, data_to_bake, settings.axis_z_mode, settings.axis_z_uv_index, settings.axis_z_uv_channel, settings.uvmap_name, settings.axis_z_rgba, settings.invert_v)
        # PACKED
        else:
            RemappedAxis = (axis_to_bake + XYZUNITVECTOR) * 0.5
            
            # X/Y or X/Z or Y/Z AXIS
            if settings.axis_channel_mode == "AB_PACKED":
                data_to_bake = get_packed_ab_vector(RemappedAxis, settings.axis_ab_packed_a_comp, settings.axis_ab_packed_b_comp)                
            # XYZ AXIS
            elif settings.axis_channel_mode == "XYZ_PACKED":
                data_to_bake = get_packed_xyz_vector(RemappedAxis)

            bake_data(mesh, data_to_bake, "UV", settings.axis_packed_uv_index, settings.axis_packed_uv_channel, settings.uvmap_name, 0, settings.invert_v)
    return True

def bake_shapekey_offset(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.shapekey_offset:
        add_bake_report("shapekey_name", settings.shapekey_name)
        add_bake_report("shapekey_rest_name", settings.shapekey_rest_name)

        add_bake_report("shapekey_offset", True)
        add_bake_report("shapekey_offset_channel_mode", settings.shapekey_offset_channel_mode)
        add_bake_report("shapekey_offset_x", settings.shapekey_offset_x)
        add_bake_report("shapekey_offset_x_mode", settings.shapekey_offset_x_mode)
        add_bake_report("shapekey_offset_x_uv_index", settings.shapekey_offset_x_uv_index)
        add_bake_report("shapekey_offset_x_uv_channel", settings.shapekey_offset_x_uv_channel)
        add_bake_report("shapekey_offset_x_rgba", settings.shapekey_offset_x_rgba)
        add_bake_report("shapekey_offset_y", settings.shapekey_offset_y)
        add_bake_report("shapekey_offset_y_mode", settings.shapekey_offset_y_mode)
        add_bake_report("shapekey_offset_y_uv_index", settings.shapekey_offset_y_uv_index)
        add_bake_report("shapekey_offset_y_uv_channel", settings.shapekey_offset_y_uv_channel)
        add_bake_report("shapekey_offset_y_rgba", settings.shapekey_offset_y_rgba)
        add_bake_report("shapekey_offset_z", settings.shapekey_offset_z)
        add_bake_report("shapekey_offset_z_mode", settings.shapekey_offset_z_mode)
        add_bake_report("shapekey_offset_z_uv_index", settings.shapekey_offset_z_uv_index)
        add_bake_report("shapekey_offset_z_uv_channel", settings.shapekey_offset_z_uv_channel)
        add_bake_report("shapekey_offset_z_rgba", settings.shapekey_offset_z_rgba)
        add_bake_report("shapekey_offset_packed_uv_index", settings.shapekey_offset_packed_uv_index)
        add_bake_report("shapekey_offset_packed_uv_channel", settings.shapekey_offset_packed_uv_channel)
        add_bake_report("shapekey_offset_ab_packed_a_comp", settings.shapekey_offset_ab_packed_a_comp)
        add_bake_report("shapekey_offset_ab_packed_b_comp", settings.shapekey_offset_ab_packed_b_comp)
    else:
        return False
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    # data might need a 'multiplier' to be normalized and packed/unpacked
    packing_multiplier = get_shapekey_offset_data_multiplier(context) if get_shapekey_offset_data_needs_multiplier(context) else 1.0
    packing_divisor = 1.0 / packing_multiplier
    add_bake_report("shapekey_offset_multiplier", packing_multiplier)

    for mesh in meshes:
        # make sure shapekey exists
        if mesh.data.shape_keys and (settings.shapekey_name in mesh.data.shape_keys.key_blocks) and (settings.shapekey_rest_name in mesh.data.shape_keys.key_blocks):
            initial_shape_keys = []
            for shape_key in mesh.data.shape_keys.key_blocks:
                initial_shape_keys.append((shape_key.name, shape_key.value)) # cache shapekeys
                if shape_key.name == settings.shapekey_name:
                    shape_key.value = 1.0
                else:
                    shape_key.value = 0.0
        
            dgraph = context.evaluated_depsgraph_get()
            obj_eval = mesh.evaluated_get(dgraph)
            mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            
            for face in mesh.data.polygons:
                for loop_id in face.loop_indices:
                    vertex_index = mesh.data.loops[loop_id].vertex_index
                    
                    shapekey_vertex_pos = mesh.data.shape_keys.key_blocks[settings.shapekey_name].data[vertex_index].co
                    shapekey_rest_vertex_pos = mesh.data.shape_keys.key_blocks[settings.shapekey_rest_name].data[vertex_index].co
                    
                    offset = (shapekey_vertex_pos - shapekey_rest_vertex_pos) * signed_scale
                                    
                    if settings.shapekey_offset_channel_mode == "INDIVIDUAL":
                        # packing normal is only available if we pack X/Y/Z components individually
                        if settings.shapekey_normal and settings.shapekey_normal_channel_mode == "OFFSET_PACKED":
                            normal = mesh_eval.vertices[vertex_index].normal * signed_axis
                            
                            # @hack prevent float from getting too close to 1 which causes issues with that packing method (fractional part of 1.0 is .0 which is incorrect)
                            fix_precision_issue = 0.025

                            xyz_packed_normal_conv_bias = (normal + XYZUNITVECTOR) * (0.5 - fix_precision_issue) # remap normal from [-1:1] to [0:1]

                            # round offset & pack normal into the fractional part
                            offset.x = math.floor(offset.x) + xyz_packed_normal_conv_bias.x
                            offset.y = math.floor(offset.y) + xyz_packed_normal_conv_bias.y
                            offset.z = math.floor(offset.z) + xyz_packed_normal_conv_bias.z
                        
                        # X OFFSET
                        if settings.shapekey_offset_x:
                            data_to_bake = offset.x
                            
                            if settings.shapekey_offset_x_mode == "VCOL":
                                data_to_bake = data_to_bake * packing_divisor
                                data_to_bake = (data_to_bake + 1) * 0.5

                            bake_data(mesh, data_to_bake, settings.shapekey_offset_x_mode, settings.shapekey_offset_x_uv_index, settings.shapekey_offset_x_uv_channel, settings.uvmap_name, settings.shapekey_offset_x_rgba, settings.invert_v, loop_id)
                            
                        # Y OFFSET
                        if settings.shapekey_offset_y:
                            data_to_bake = offset.y

                            if settings.shapekey_offset_y_mode == "VCOL":
                                data_to_bake = data_to_bake * packing_divisor
                                data_to_bake = (data_to_bake + 1) * 0.5

                            bake_data(mesh, data_to_bake, settings.shapekey_offset_y_mode, settings.shapekey_offset_y_uv_index, settings.shapekey_offset_y_uv_channel, settings.uvmap_name, settings.shapekey_offset_y_rgba, settings.invert_v, loop_id)

                        # Z OFFSET
                        if settings.shapekey_offset_z:
                            data_to_bake = offset.z

                            if settings.shapekey_offset_z_mode == "VCOL":
                                data_to_bake = data_to_bake * packing_divisor
                                data_to_bake = (data_to_bake + 1) * 0.5

                            bake_data(mesh, data_to_bake, settings.shapekey_offset_z_mode, settings.shapekey_offset_z_uv_index, settings.shapekey_offset_z_uv_channel, settings.uvmap_name, settings.shapekey_offset_z_rgba, settings.invert_v, loop_id)
                    
                    else:
                        remapped_offset = mathutils.Vector((
                                max(min(offset.x * packing_divisor, 1.0), -1.0),
                                max(min(offset.y * packing_divisor, 1.0), -1.0),
                                max(min(offset.z * packing_divisor, 1.0), -1.0))
                            )

                        normalized_offset = (remapped_offset + XYZUNITVECTOR) * 0.5
                        
                        data_to_bake = 0.0
                        # X/Y or X/Z or Y/Z OFFSET
                        if settings.shapekey_offset_channel_mode == "AB_PACKED":
                            data_to_bake = get_packed_ab_vector(normalized_offset, settings.shapekey_offset_ab_packed_a_comp, settings.shapekey_offset_ab_packed_b_comp)
                        # XYZ OFFSET
                        elif settings.shapekey_offset_channel_mode == "XYZ_PACKED":
                            data_to_bake = get_packed_xyz_vector(normalized_offset)
                            
                        if settings.shapekey_offsetPackOnlyIfNonNull:
                            if offset.length < 0.01:
                                data_to_bake = 0.0
                        
                        bake_data(mesh, data_to_bake, "UV", settings.shapekey_offset_packed_uv_index, settings.shapekey_offset_packed_uv_channel, settings.uvmap_name, 0, settings.invert_v, loop_id)
                        
            # clear converted mesh
            obj_eval.to_mesh_clear()

            for shape_key_name, shape_key_value in initial_shape_keys:
                mesh.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value # restore shapekeys
    
    return True

def bake_shapekey_normal(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.shapekey_normal and settings.shapekey_normal_channel_mode != "OFFSET_PACKED":
        add_bake_report("shapekey_name", settings.shapekey_name)
        add_bake_report("shapekey_rest_name", settings.shapekey_rest_name)

        add_bake_report("shapekey_normal", True)
        add_bake_report("shapekey_normal_channel_mode", settings.shapekey_normal_channel_mode)
        add_bake_report("shapekey_normal_x", settings.shapekey_normal_x)
        add_bake_report("shapekey_normal_x_mode", settings.shapekey_normal_x_mode)
        add_bake_report("shapekey_normal_x_uv_index", settings.shapekey_normal_x_uv_index)
        add_bake_report("shapekey_normal_x_uv_channel", settings.shapekey_normal_x_uv_channel)
        add_bake_report("shapekey_normal_x_rgba", settings.shapekey_normal_x_rgba)
        add_bake_report("shapekey_normal_y", settings.shapekey_normal_y)
        add_bake_report("shapekey_normal_y_mode", settings.shapekey_normal_y_mode)
        add_bake_report("shapekey_normal_y_uv_index", settings.shapekey_normal_y_uv_index)
        add_bake_report("shapekey_normal_y_uv_channel", settings.shapekey_normal_y_uv_channel)
        add_bake_report("shapekey_normal_y_rgba", settings.shapekey_normal_y_rgba)
        add_bake_report("shapekey_normal_z", settings.shapekey_normal_z)
        add_bake_report("shapekey_normal_z_mode", settings.shapekey_normal_z_mode)
        add_bake_report("shapekey_normal_z_uv_index", settings.shapekey_normal_z_uv_index)
        add_bake_report("shapekey_normal_z_uv_channel", settings.shapekey_normal_z_uv_channel)
        add_bake_report("shapekey_normal_z_rgba", settings.shapekey_normal_z_rgba)
        add_bake_report("shapekey_normal_xyz_uv_index", settings.shapekey_normal_xyz_uv_index)
        add_bake_report("shapekey_normal_xyz_uv_channel", settings.shapekey_normal_xyz_uv_channel)
        add_bake_report("shapekey_normal_ab_packed_a_comp", settings.shapekey_normal_ab_packed_a_comp)
        add_bake_report("shapekey_normal_ab_packed_b_comp", settings.shapekey_normal_ab_packed_b_comp)
    else:
        return False
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))

    for mesh in meshes:
        # make sure shapekey exists
        if not mesh.data.shape_keys or not (settings.shapekey_name in mesh.data.shape_keys.key_blocks) or not (settings.shapekey_rest_name in mesh.data.shape_keys.key_blocks):
            continue
        
        # enable shapekey
        shapekey_value_to_restore = mesh.data.shape_keys.key_blocks[settings.shapekey_name].value
        mesh.data.shape_keys.key_blocks[settings.shapekey_name].value = 1
        
        # create converted mesh to read normals
        dgraph = context.evaluated_depsgraph_get()
        obj_eval = mesh.evaluated_get(dgraph)
        mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        
        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = mesh.data.loops[loop_id].vertex_index

                normal = mesh_eval.vertices[vertex_index].normal * signed_axis

                if settings.shapekey_normal_channel_mode == "INDIVIDUAL":
                    # NORMAL X COMPONENT
                    if settings.shapekey_normal_x:
                        data_to_bake = normal.x

                        if (settings.shapekey_normal_x_mode == "VCOL"):
                            data_to_bake = (data_to_bake + 1) * 0.5

                        bake_data(mesh, data_to_bake, settings.shapekey_normal_x_mode, settings.shapekey_normal_x_uv_index, settings.shapekey_normal_x_uv_channel, settings.uvmap_name, settings.shapekey_normal_x_rgba, settings.invert_v, loop_id)
                    # NORMAL Y COMPONENT
                    if settings.shapekey_normal_y:
                        data_to_bake = normal.y

                        if (settings.shapekey_normal_y_mode == "VCOL"):
                            data_to_bake = (data_to_bake + 1) * 0.5

                        bake_data(mesh, data_to_bake, settings.shapekey_normal_y_mode, settings.shapekey_normal_y_uv_index, settings.shapekey_normal_y_uv_channel, settings.uvmap_name, settings.shapekey_normal_y_rgba, settings.invert_v, loop_id)
                    # NORMAL Z COMPONENT
                    if settings.shapekey_normal_z:
                        data_to_bake = normal.z

                        if (settings.shapekey_normal_z_mode == "VCOL"):
                            data_to_bake = (data_to_bake + 1) * 0.5

                        bake_data(mesh, data_to_bake, settings.shapekey_normal_z_mode, settings.shapekey_normal_z_uv_index, settings.shapekey_normal_z_uv_channel, settings.uvmap_name, settings.shapekey_normal_z_rgba, settings.invert_v, loop_id)
                else:
                    clamped_normal = mathutils.Vector((
                        max(min(normal.x, 1.0), -1.0),
                        max(min(normal.y, 1.0), -1.0),
                        max(min(normal.z, 1.0), -1.0)))
                    
                    # @hack prevent float from getting too close to 1 which seems to cause issues. @NOTE investigate to fix hack
                    fix_precision_issue = 0.025

                    remapped_normal = mathutils.Vector((
                        (clamped_normal.x + 1) * (0.5 - fix_precision_issue),
                        (clamped_normal.y + 1) * (0.5 - fix_precision_issue),
                        (clamped_normal.z + 1) * (0.5 - fix_precision_issue)))
                    # X/Y or X/Z or Y/Z normal
                    if settings.shapekey_normal_channel_mode == "AB_PACKED":
                        data_to_bake = get_packed_ab_vector(remapped_normal, settings.shapekey_normal_ab_packed_a_comp, settings.shapekey_normal_ab_packed_b_comp)
                    # XYZ
                    elif settings.shapekey_normal_channel_mode == "XYZ_PACKED":
                        data_to_bake = get_packed_xyz_vector(remapped_normal)
                    
                    bake_data(mesh, data_to_bake, "UV", settings.shapekey_normal_xyz_uv_index, settings.shapekey_normal_xyz_uv_channel, settings.uvmap_name, 0, settings.invert_v, loop_id)
                    
        # clear converted mesh
        obj_eval.to_mesh_clear()
        
        # restore shapekey
        mesh.data.shape_keys.key_blocks[settings.shapekey_name].value = shapekey_value_to_restore
    return True

def get_sphere_mask_max_dist(meshes, origin):
    """ """

    vertex_max_dist = 0.0
    for mesh in meshes:
        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = mesh.data.loops[loop_id].vertex_index

                vertex_pos = mesh.matrix_world @ mesh.data.vertices[vertex_index].co
                offset = vertex_pos - origin
                vertex_dist = offset.length
                if (vertex_dist > vertex_max_dist):
                    vertex_max_dist = vertex_dist

    return vertex_max_dist

def bake_sphere_mask(context, meshes, empties):
    """ """
    settings = context.scene.DataBakerSettings
    if settings.sphere_mask:
        add_bake_report("sphere_mask", True)
        add_bake_report("sphere_mask_normalize", settings.sphere_mask_normalize)
        add_bake_report("sphere_mask_clamp", settings.sphere_mask_clamp)
        add_bake_report("sphere_mask_origin_mode", settings.sphere_mask_origin_mode)
        add_bake_report("sphere_mask_origin", settings.sphere_mask_origin)
        add_bake_report("sphere_mask_mode", settings.sphere_mask_mode)
        add_bake_report("sphere_mask_uv_index", settings.sphere_mask_uv_index)
        add_bake_report("sphere_mask_uv_channel", settings.sphere_mask_uv_channel)
        add_bake_report("sphere_mask_rgba", settings.sphere_mask_rgba)
        add_bake_report("sphere_mask_falloff", settings.sphere_mask_falloff)
    else:
        return False
    
    origin_pos = mathutils.Vector((0.0, 0.0, 0.0))
    origin_pos_set = False

    if settings.sphere_mask_origin_mode == "ORIGIN" or settings.sphere_mask_origin_mode == "SELECTION" or settings.sphere_mask_origin_mode == "OBJECT":
        if settings.origin: # default origin
            origin_pos = settings.origin.matrix_world.to_translation()

        if settings.sphere_mask_origin_mode == "SELECTION": # selection origin
            averaged_pos = mathutils.Vector((0.0, 0.0, 0.0))
            averaged_div = 1.0 / max(len(meshes), 1)
            for mesh in meshes:
                averaged_pos += mesh.matrix_world.to_translation()

            origin_pos.x = averaged_pos.x * averaged_div
            origin_pos.y = averaged_pos.y * averaged_div
            origin_pos.z = averaged_pos.z * averaged_div
        elif settings.sphere_mask_origin_mode == "OBJECT": # object origin
            if settings.sphere_mask_origin:
                origin_pos = settings.sphere_mask_origin.matrix_world.to_translation()
            else:
                return False

        origin_pos_set = True

    # precompute greatest vertex distance if need to, else we'll do this on per-object basis
    max_dist = get_sphere_mask_max_dist(meshes, origin_pos) if origin_pos_set else 0.0

    for mesh in meshes:
        if origin_pos_set:
            pass
        else:
            origin_obj = mesh
            
            if settings.sphere_mask_origin_mode == "SELF":
                origin_pos = mesh.matrix_world.to_translation()
                
                origin_objs = [origin_obj]
                max_dist = get_sphere_mask_max_dist(origin_objs, origin_pos)
            elif settings.sphere_mask_origin_mode == "PARENT":
                if mesh.parent:
                    origin_obj = mesh.parent
                    origin_pos = mesh.parent.matrix_world.to_translation()

                    origin_objs = []
                    origin_objs = [child_obj for child_obj in origin_obj.children if child_obj in meshes] # make sure that child is part of our selected meshes

                    max_dist = get_sphere_mask_max_dist(origin_objs, origin_pos)
                else:
                    continue
        
        for face in mesh.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = mesh.data.loops[loop_id].vertex_index
                vertex_pos = mesh.matrix_world @ mesh.data.vertices[vertex_index].co
                offset = vertex_pos - origin_pos
                vertex_dist = offset.length

                if settings.sphere_mask_normalize or settings.sphere_mask_mode == "VCOL":
                    vertex_dist = math.pow((vertex_dist / max_dist), settings.sphere_mask_falloff)

                if settings.sphere_mask_clamp or settings.sphere_mask_mode == "VCOL":
                    vertex_dist = max(min(vertex_dist, 1.0), 0.0)

                data_to_bake = vertex_dist
                bake_data(mesh, data_to_bake, settings.sphere_mask_mode, settings.sphere_mask_uv_index, settings.sphere_mask_uv_channel, settings.uvmap_name, settings.sphere_mask_rgba, settings.invert_v, loop_id)
    
    return True

def bake_linear_mask(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.linear_mask:
        add_bake_report("linear_mask", True)
        add_bake_report("linear_mask_normalize", settings.linear_mask_normalize)
        add_bake_report("linear_mask_clamp", settings.linear_mask_clamp)
        add_bake_report("linear_mask_obj_mode", settings.linear_mask_obj_mode)
        add_bake_report("linear_mask_obj", settings.linear_mask_obj)
        add_bake_report("linear_mask_mode", settings.linear_mask_mode)
        add_bake_report("linear_mask_axis", settings.linear_mask_axis)
        add_bake_report("linear_mask_uv_index", settings.linear_mask_uv_index)
        add_bake_report("linear_mask_uv_channel", settings.linear_mask_uv_channel)
        add_bake_report("linear_mask_rgba", settings.linear_mask_rgba)
        add_bake_report("linear_mask_falloff", settings.linear_mask_falloff)
    else:
        return False

    local_mode = (settings.linear_mask_obj_mode == "PARENT_LOCAL") or (settings.linear_mask_obj_mode == "SELF_LOCAL")
    parent_mode = (settings.linear_mask_obj_mode == "PARENT_WORLD") or (settings.linear_mask_obj_mode == "PARENT_LOCAL")
    
    origin_pos = mathutils.Vector((0.0, 0.0, 0.0))
    origin_pos_set = False

    axis_min_bound = 0.0
    axis_min_bound_set = False

    axis_max_bound = 0.0
    axis_max_bound_set = False
    
    axis = XYZVECTORS["X"] if settings.linear_mask_axis == "X" else XYZVECTORS["Y"] if settings.linear_mask_axis == "Y" else XYZVECTORS["Z"]
    
    if settings.linear_mask_obj_mode == "SELECTION" or settings.linear_mask_obj_mode == "OBJECT":
        # first we need to loop through all selected mesh objects and find the vertex which has the greatest distance to the specified origin so we can build a normalized [0:1] gradient
        if settings.linear_mask_obj_mode == "SELECTION":
            for mesh in meshes:
                for face in mesh.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = obj.data.loops[loop_id].vertex_index

                        vertex_loc = obj.matrix_world @ obj.data.vertices[vertex_index].co
                        vertex_loc_projected = vertex_loc.dot(axis)

                        if (vertex_loc_projected < axis_min_bound) or not axis_min_bound_set:
                            axis_min_bound = vertex_loc_projected
                            axis_min_bound_set = True
                        
                        if (vertex_loc_projected > axis_max_bound) or not axis_max_bound_set:
                            axis_max_bound = vertex_loc_projected
                            axis_max_bound_set = True
        elif settings.linear_mask_obj_mode == "OBJECT":
            if settings.linear_mask_obj is None:
                return False

            obj = settings.linear_mask_obj
            obj_rot = obj.rotation_quaternion if obj.rotation_mode == "QUATERNION" else obj.rotation_euler
            obj_rot_mat = mathutils.Matrix.LocRotScale(None, obj_rot, None)

            if obj.type == "EMPTY":
                empty_loc = obj.matrix_world.to_translation()
                local_axis = obj_rot_mat @ axis # transform world axis to object's local space
                
                empty_loc_projected = empty_loc.dot(local_axis)
                
                if (empty_loc_projected < axis_min_bound) or not axis_min_bound_set:
                    axis_min_bound = empty_loc_projected
                    axis_min_bound_set = True
                
                if (empty_loc_projected > axis_max_bound) or not axis_max_bound_set:
                    axis_max_bound = empty_loc_projected
                    axis_max_bound_set = True
                
                empty_tip_offset = local_axis * obj.empty_display_size * obj.scale
                empty_loc = obj.matrix_world.to_translation() + empty_tip_offset # compute empty 'tip' location in world space
                empty_loc_projected = empty_loc.dot(local_axis) # project on local axis
                
                if (empty_loc_projected < axis_min_bound) or not axis_min_bound_set:
                    axis_min_bound = empty_loc_projected
                    axis_min_bound_set = True
                
                if (empty_loc_projected > axis_max_bound) or not axis_max_bound_set:
                    axis_max_bound = empty_loc_projected
                    axis_max_bound_set = True
            elif obj.type == "MESH":
                for face in obj.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = obj.data.loops[loop_id].vertex_index
                        vertex_loc = obj.matrix_world @ obj.data.vertices[vertex_index].co
                        local_axis = obj_rot_mat @ axis # transform world axis to object's local space
                        vertex_loc_projected = vertex_loc.dot(local_axis) # project on local axis

                        if (vertex_loc_projected < axis_min_bound) or not axis_min_bound_set:
                            axis_min_bound = vertex_loc_projected
                            axis_min_bound_set = True
                        
                        if (vertex_loc_projected > axis_max_bound) or not axis_max_bound_set:
                            axis_max_bound = vertex_loc_projected
                            axis_max_bound_set = True
            else:
                return False

        origin_pos_set = True

    for mesh in meshes:
        ref_obj = mesh # assume 'reference' object is self at first

        # self or parent mode
        if not origin_pos_set:
            if parent_mode and ref_obj.parent:
                ref_obj = ref_obj.parent
            else:
                continue

            # need to reset these per object
            axis_min_bound = 0.0
            axis_min_bound_set = False

            axis_max_bound = 0.0
            axis_max_bound_set = False

            if ref_obj.type == "EMPTY":
                empty_loc = ref_obj.matrix_world.to_translation()
                empty_loc_projected = empty_loc.dot(axis) # project on world axis at first
                empty_rot_mat = ref_obj.rotation_quaternion if ref_obj.rotation_mode == "QUATERNION" else ref_obj.rotation_euler
                
                # unless we're in local space
                if local_mode:
                    local_axis = mathutils.Matrix.LocRotScale(None, empty_rot_mat, None) @ axis
                    empty_loc_projected = empty_loc.dot(local_axis) # project on local axis
                
                if (empty_loc_projected < axis_min_bound) or not axis_min_bound_set:
                    axis_min_bound = empty_loc_projected
                    axis_min_bound_set = True
                
                if (empty_loc_projected > axis_max_bound) or not axis_max_bound_set:
                    axis_max_bound = empty_loc_projected
                    axis_max_bound_set = True
                
                empty_tip_offset = mathutils.Matrix.LocRotScale(None, empty_rot_mat, ref_obj.empty_display_size * ref_obj.scale) @ axis
                empty_loc = ref_obj.matrix_world.to_translation() + empty_tip_offset # compute empty 'tip' location in world space
                empty_loc_projected = empty_loc.dot(axis)  # project on world axis
                
                # unless we're in local space
                if local_mode:
                    local_axis = mathutils.Matrix.LocRotScale(None, empty_rot_mat, None) @ axis
                    empty_loc_projected = empty_loc.dot(local_axis) # project on local axis
                
                if (empty_loc_projected < axis_min_bound) or not axis_min_bound_set:
                    axis_min_bound = empty_loc_projected
                    axis_min_bound_set = True
                
                if (empty_loc_projected > axis_max_bound) or not axis_max_bound_set:
                    axis_max_bound = empty_loc_projected
                    axis_max_bound_set = True
            elif ref_obj.type == "MESH":
                for face in ref_obj.data.polygons:
                    for loop_id in face.loop_indices:
                        vertex_index = ref_obj.data.loops[loop_id].vertex_index
                        vertex_loc = ref_obj.matrix_world @ ref_obj.data.vertices[vertex_index].co
                        vertex_loc_projected = vertex_loc.dot(axis) # project on world axis at first
                        
                        # unless we're in local space
                        if local_mode:
                            ref_obj_rot = ref_obj.rotation_quaternion if ref_obj.rotation_mode == "QUATERNION" else ref_obj.rotation_euler
                            ref_obj_rot_mat = mathutils.Matrix.LocRotScale(None, ref_obj_rot, None)
                            local_axis = ref_obj_rot_mat @ axis
                            
                            vertex_loc_projected = vertex_loc.dot(local_axis) # project on local axis

                        if (vertex_loc_projected < axis_min_bound) or not axis_min_bound_set:
                            axis_min_bound = vertex_loc_projected
                            axis_min_bound_set = True
                        
                        if (vertex_loc_projected > axis_max_bound) or not axis_max_bound_set:
                            axis_max_bound = vertex_loc_projected
                            axis_max_bound_set = True
            else:
                continue

        elif settings.linear_mask_obj_mode == "OBJECT":
            ref_obj = settings.linear_mask_obj

        for face in obj.data.polygons:
            for loop_id in face.loop_indices:
                vertex_index = obj.data.loops[loop_id].vertex_index
                vertex_loc = obj.matrix_world @ obj.data.vertices[vertex_index].co
                vertex_loc_projected = vertex_loc.dot(axis) # project on world axis at first

                # local mode
                if local_mode or settings.linear_mask_obj_mode == "OBJECT":
                    ref_obj_rot = ref_obj.rotation_quaternion if ref_obj.rotation_mode == "QUATERNION" else ref_obj.rotation_euler
                    ref_obj_rot_mat = mathutils.Matrix.LocRotScale(None, ref_obj_rot, None)
                    local_axis = ref_obj_rot_mat @ axis

                    vertex_loc_projected = vertex_loc.dot(local_axis) # project on local axis

                data_to_bake = (vertex_loc_projected - axis_min_bound)
                if settings.linear_mask_normalize or settings.linear_mask_mode == "VCOL":
                    data_to_bake = math.pow(data_to_bake / (axis_max_bound - axis_min_bound), settings.linear_mask_falloff)

                if settings.linear_mask_clamp or settings.linear_mask_mode == "VCOL":
                    data_to_bake = max(min(data_to_bake, 1.0), 0.0)

                bake_data(mesh, data_to_bake, settings.linear_mask_mode, settings.linear_mask_uv_index, settings.linear_mask_uv_channel, settings.uvmap_name, settings.linear_mask_rgba, settings.invert_v, loop_id)

    return True

def bake_random_value_per_collection(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.random_per_collection:
        add_bake_report("random_per_collection", True)
        add_bake_report("random_per_collection_mode", settings.random_per_collection_mode)
        add_bake_report("random_per_collection_uv_index", settings.random_per_collection_uv_index)
        add_bake_report("random_per_collection_uv_channel", settings.random_per_collection_uv_channel)
        add_bake_report("random_per_collection_rgba", settings.random_per_collection_rgba)
        add_bake_report("random_per_collection_uniform", settings.random_per_collection_uniform)
    else:
        return False

    # initiate object ID/uniform value dictionary. Rather than generate a random value per object which may give poor randomization due to hazard, we can choose to output randomized uniform values (if 5 objects, then values would be 0.0, 0,25, 0.5, 0.75, 1.0 in a random order)
    per_col_random_uniform_values = []

    # gather list of collections objects are part of
    cols = []
    for mesh in meshes:
        for col in mesh.users_collection:
            if col not in cols:
                cols.append(col)

    unique_col = len(cols) == 1

    # offset object index & count if we only have one object so that uniform value is 0.5 (this is an arbitrary choice)
    col_index = 1 if unique_col else 0
    col_count = 2 if unique_col else (len(cols) - 1)

    for col in cols:
        # build uniform value
        per_col_random_uniform_values.append(col_index / col_count)

        col_index += 1

    if col_index == 0:
        return False

    random.shuffle(per_col_random_uniform_values)

    for mesh_index, mesh in enumerate(meshes):
        col = mesh.users_collection[0] if mesh.users_collection else None
        if col is None:
            continue

        col_index = cols.index(col, 0, len(cols))
        if col_index >= 0:
            # blend between uniform random and completely random
            data_to_bake = per_col_random_uniform_values[col_index]
            data_to_bake = (data_to_bake * settings.random_per_collection_uniform) + ((1 - settings.random_per_collection_uniform) * random.uniform(0,1))

            bake_data(mesh, data_to_bake, settings.random_per_collection_mode, settings.random_per_collection_uv_index, settings.random_per_collection_uv_channel, settings.uvmap_name, settings.random_per_collection_rgba, settings.invert_v)

    return True

def bake_random_value_per_object(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.random_per_object:
        add_bake_report("random_per_object", True)
        add_bake_report("random_per_object_mode", settings.random_per_object_mode)
        add_bake_report("random_per_object_uv_index", settings.random_per_object_uv_index)
        add_bake_report("random_per_object_uv_channel", settings.random_per_object_uv_channel)
        add_bake_report("random_per_object_rgba", settings.random_per_object_rgba)
        add_bake_report("random_per_object_uniform", settings.random_per_object_uniform)
    else:
        return False
    
    # initiate object ID/uniform value dictionary. Rather than generate a random value per object which may give poor randomization due to hazard, we can choose to output randomized uniform values (if 5 objects, then values would be 0.0, 0,25, 0.5, 0.75, 1.0 in a random order)
    per_obj_random_uniform_values = []
    
    mesh_count = len(meshes)
    
    # offset object index & count if we only have one object so that uniform value is 0.5 (this is an arbitrary choice)
    obj_index = 1 if mesh_count == 1 else 0
    obj_count = 2 if mesh_count == 1 else (mesh_count - 1)
    
    for mesh in meshes:
        # build uniform value
        per_obj_random_uniform_values.append(obj_index / obj_count)
    
        obj_index += 1
    
    if obj_index == 0:
        return False
    
    random.shuffle(per_obj_random_uniform_values)
    
    # reset object index
    obj_index = 0
    
    for mesh in meshes:
        # blend between uniform random and completely random
        data_to_bake = per_obj_random_uniform_values[obj_index]
        data_to_bake = (data_to_bake * settings.random_per_object_uniform) + ((1 - settings.random_per_object_uniform) * random.uniform(0,1))

        bake_data(mesh, data_to_bake, settings.random_per_object_mode, settings.random_per_object_uv_index, settings.random_per_object_uv_channel, settings.uvmap_name, settings.random_per_object_rgba, settings.invert_v)
        
        obj_index += 1
    
    return obj_index > 0

def bake_random_value_per_polygon(context, meshes, empties):
    """ """
    settings = context.scene.DataBakerSettings
    if settings.random_per_poly:
        add_bake_report("random_per_poly", True)
        add_bake_report("random_per_poly_mode", settings.random_per_poly_mode)
        add_bake_report("random_per_poly_uv_index", settings.random_per_poly_uv_index)
        add_bake_report("random_per_poly_uv_channel", settings.random_per_poly_uv_channel)
        add_bake_report("random_per_poly_rgba", settings.random_per_poly_rgba)
        add_bake_report("random_per_poly_uniform", settings.random_per_poly_uniform)
    else:
        return False

    # initiate vertex ID/uniform value dictionary. Rather than generate a random value per poly which may give poor randomization due to hazard, we can choose to output randomized uniform values (if 5 polys, then values would be 0.0, 0,25, 0.5, 0.75, 1.0 in a random order)
    per_poly_random_uniform_values = []

    poly_count = 0
    # first, gather the total amount of polygons across all selected mesh objects
    for mesh in meshes:
        poly_count += len(mesh.data.polygons)

    if poly_count == 0:
        return False

    # offset poly index & count if we only have one poly so that uniform value is 0.5 (this is an arbitrary choice)
    poly_index = 1 if poly_count == 1 else 0
    poly_count = 2 if poly_count == 1 else poly_count

    for mesh in meshes:
        for face in mesh.data.polygons:
            # build uniform value
            per_poly_random_uniform_values.append(poly_index / poly_count)

            # increment poly index
            poly_index += 1

    random.shuffle(per_poly_random_uniform_values)

    # reset poly index
    poly_index = 0

    for mesh in meshes:
        for face in mesh.data.polygons:
            # blend between uniform random and completely random
            data_to_bake = per_poly_random_uniform_values[poly_index]
            data_to_bake = (data_to_bake * settings.random_per_poly_uniform) + ((1 - settings.random_per_poly_uniform) * random.uniform(0,1))

            poly_index += 1

            for loop_id in face.loop_indices:
                bake_data(mesh, data_to_bake, settings.random_per_poly_mode, settings.random_per_poly_uv_index, settings.random_per_poly_uv_channel, settings.uvmap_name, settings.random_per_poly_rgba, settings.invert_v, loop_id)

    return poly_index > 0

def bake_parent(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings

    parent_auto_mode = settings.parent_mode == "AUTOMATIC"

    if (settings.parent_position or settings.parent_axis) and settings.parent_max_depth > 0:
        add_bake_report("parent_mode", settings.parent_mode)
        add_bake_report("parent_depth", settings.parent_depth)
        add_bake_report("parent_max_depth", settings.parent_max_depth)
        add_bake_report("parent_automatic_uv_index", settings.parent_automatic_uv_index)
        add_bake_report("parent_automatic_uv_channel", settings.parent_automatic_uv_channel)
        if settings.parent_position:
            add_bake_report("parent_position", True)
            add_bake_report("parent_axis_component", settings.parent_axis_component)
            add_bake_report("parent_position_channel_mode", settings.parent_position_channel_mode)
            add_bake_report("parent_position_x", settings.parent_position_x)
            add_bake_report("parent_position_x_mode", settings.parent_position_x_mode)
            add_bake_report("parent_position_x_uv_index", settings.parent_position_x_uv_index)
            add_bake_report("parent_position_x_uv_channel", settings.parent_position_x_uv_channel)
            add_bake_report("parent_position_x_rgba", settings.parent_position_x_rgba)
            add_bake_report("parent_position_y", settings.parent_position_y)
            add_bake_report("parent_position_y_mode", settings.parent_position_y_mode)
            add_bake_report("parent_position_y_uv_index", settings.parent_position_y_uv_index)
            add_bake_report("parent_position_y_uv_channel", settings.parent_position_y_uv_channel)
            add_bake_report("parent_position_y_rgba", settings.parent_position_y_rgba)
            add_bake_report("parent_position_z", settings.parent_position_z)
            add_bake_report("parent_position_z_mode", settings.parent_position_z_mode)
            add_bake_report("parent_position_z_uv_index", settings.parent_position_z_uv_index)
            add_bake_report("parent_position_z_uv_channel", settings.parent_position_z_uv_channel)
            add_bake_report("parent_position_z_rgba", settings.parent_position_z_rgba)
            add_bake_report("parent_position_packed_uv_index", settings.parent_position_packed_uv_index)
            add_bake_report("parent_position_packed_uv_channel", settings.parent_position_packed_uv_channel)
            add_bake_report("parent_position_ab_packed_a_comp", settings.parent_position_ab_packed_a_comp)
            add_bake_report("parent_position_ab_packed_b_comp", settings.parent_position_ab_packed_b_comp)
        if settings.parent_axis:
            add_bake_report("parent_axis", True)
            add_bake_report("parent_axis_component", settings.parent_axis_component)
            add_bake_report("parent_axis_channel_mode", settings.parent_axis_channel_mode)
            add_bake_report("parent_axis_x", settings.parent_axis_x)
            add_bake_report("parent_axis_x_mode", settings.parent_axis_x_mode)
            add_bake_report("parent_axis_x_uv_index", settings.parent_axis_x_uv_index)
            add_bake_report("parent_axis_x_uv_channel", settings.parent_axis_x_uv_channel)
            add_bake_report("parent_axis_x_rgba", settings.parent_axis_x_rgba)
            add_bake_report("parent_axis_y", settings.parent_axis_y)
            add_bake_report("parent_axis_y_mode", settings.parent_axis_y_mode)
            add_bake_report("parent_axis_y_uv_index", settings.parent_axis_y_uv_index)
            add_bake_report("parent_axis_y_uv_channel", settings.parent_axis_y_uv_channel)
            add_bake_report("parent_axis_y_rgba", settings.parent_axis_y_rgba)
            add_bake_report("parent_axis_z", settings.parent_axis_z)
            add_bake_report("parent_axis_z_mode", settings.parent_axis_z_mode)
            add_bake_report("parent_axis_z_uv_index", settings.parent_axis_z_uv_index)
            add_bake_report("parent_axis_z_uv_channel", settings.parent_axis_z_uv_channel)
            add_bake_report("parent_axis_z_rgba", settings.parent_axis_z_rgba)
            add_bake_report("parent_axis_packed_uv_index", settings.parent_axis_packed_uv_index)
            add_bake_report("parent_axis_packed_uv_channel", settings.parent_axis_packed_uv_channel)
            add_bake_report("parent_axis_ab_packed_a_comp", settings.parent_axis_ab_packed_a_comp)
            add_bake_report("parent_axis_ab_packed_b_comp", settings.parent_axis_ab_packed_b_comp)
    else:
        return False

    manual_max_depth = max(min(settings.parent_depth, settings.parent_max_depth), 1.0)

    # data might need a 'multiplier' to be normalized and packed/unpacked
    packing_multiplier = get_parent_position_data_multiplier(context) if get_parent_position_data_needs_multiplier(context) else 1.0
    packing_divisor = 1.0 / packing_multiplier
    add_bake_report("parent_position_multiplier", packing_multiplier)
    
    signed_axis = mathutils.Vector((-1.0 if settings.invert_x else 1.0,
                                    -1.0 if settings.invert_y else 1.0,
                                    -1.0 if settings.invert_z else 1.0))
    signed_scale = signed_axis * settings.scale

    for mesh in meshes:
        ref_obj = settings.transform_obj if settings.transform_obj else mesh

        # automatic processing will loop through all parents and build used_uv_channels as needed so we need a starting point
        uv_channel_index = (settings.parent_automatic_uv_index * 2) + (0 if settings.parent_automatic_uv_channel == "U" else 1)
        uv_index = uv_channel_index // 2
        uv_channel = settings.parent_automatic_uv_channel

        parent_obj = ref_obj
        parent_objs = []

        # walk up the hierarchy by X levels and build the list of all parents for that object
        for depth_index in range(settings.parent_max_depth):
            if (parent_obj != None) and (parent_obj.parent != None) and (parent_obj.parent.type == 'MESH' or parent_obj.parent.type == 'EMPTY'):
                parent_obj = parent_obj.parent
                parent_objs.append(parent_obj)
            else:
                break

        # reverse the hierarchy
        parent_objs.reverse()
        
        # complete the tree will nullptrs until max depth reached
        while(len(parent_objs) < settings.parent_max_depth):
            parent_objs.append(None)

        # loop through parents from root to child
        for depth, parent_obj in enumerate(parent_objs):
            # only process the desired depth if in manual mode
            if settings.parent_mode == "MANUAL":
                if depth != (manual_max_depth + 1):
                    continue
            
            # if this object has no parent at this depth, we still want to make sure to write 0 that will indicate that element has no parent at this hierarchy level
            if parent_obj == None:
                # NULL POSITION (no parent)
                if settings.parent_position:
                    # INDIVIDUAL POSITION
                    if settings.parent_position_channel_mode == "INDIVIDUAL":
                        for xyz_comp in XYZLIST:
                            uv_index = uv_channel_index // 2
                            uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                            
                            use_vcol = False
                            if xyz_comp == "X" and settings.parent_position_x:
                                use_vcol = settings.parent_position_x_mode == "VCOL"
                                if parent_auto_mode:
                                    bake_data(mesh, 0.0, settings.parent_position_x_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_position_x_rgba, settings.invert_v)
                                else:
                                    bake_data(mesh, 0.0, settings.parent_position_x_mode, settings.parent_position_x_uv_index, settings.parent_position_x_uv_channel, settings.uvmap_name, settings.parent_position_x_rgba, settings.invert_v)
                            elif xyz_comp == "Y" and settings.parent_position_y:
                                use_vcol = settings.parent_position_y_mode == "VCOL"
                                if parent_auto_mode:
                                    bake_data(mesh, 0.0, settings.parent_position_y_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_position_y_rgba, settings.invert_v)
                                else:
                                    bake_data(mesh, 0.0, settings.parent_position_y_mode, settings.parent_position_y_uv_index, settings.parent_position_y_uv_channel, settings.uvmap_name, settings.parent_position_y_rgba, settings.invert_v)
                            elif xyz_comp == "Z" and settings.parent_position_z:
                                use_vcol = settings.parent_position_z_mode == "VCOL"
                                if parent_auto_mode:
                                    bake_data(mesh, 0.0, settings.parent_position_z_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_position_z_rgba, settings.invert_v)
                                else:
                                    bake_data(mesh, 0.0, settings.parent_position_z_mode, settings.parent_position_z_uv_index, settings.parent_position_z_uv_channel, settings.uvmap_name, settings.parent_position_z_rgba, settings.invert_v)
                            else:
                                continue
                            
                            if parent_auto_mode and not use_vcol:
                                uv_channel_index += 1

                    # AB or XYZ PACKED POSITION
                    else:
                        uv_index = settings.parent_position_packed_uv_index
                        uv_channel = settings.parent_position_packed_uv_channel
                        if parent_auto_mode:
                            uv_index = uv_channel_index // 2
                            uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                            
                            uv_channel_index += 1
                        
                        bake_data(mesh, 0.0, "UV", uv_index, uv_channel, settings.uvmap_name, 0, settings.invert_v)
                
                # NULL AXIS (no parent)
                if settings.parent_axis:
                    # INDIVIDUAL AXIS
                    if settings.parent_axis_channel_mode == "INDIVIDUAL":
                        for xyz_comp in XYZLIST:
                            uv_index = uv_channel_index // 2
                            uv_channel = "U" if uv_channel_index % 2 == 0 else "V"

                            use_vcol = False
                            if xyz_comp == "X" and settings.parent_axis_x:
                                use_vcol = settings.parent_axis_x_mode == "VCOL"
                                if parent_auto_mode:
                                    bake_data(mesh, 0.0, settings.parent_axis_x_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_axis_x_rgba, settings.invert_v)
                                else:
                                    bake_data(mesh, 0.0, settings.parent_axis_x_mode, settings.parent_axis_x_uv_index, settings.uvmap_name, settings.parent_axis_x_uv_channel, settings.parent_axis_x_rgba, settings.invert_v)
                            elif xyz_comp == "Y" and settings.parent_axis_y:
                                use_vcol = settings.parent_axis_y_mode == "VCOL"
                                if parent_auto_mode:
                                    bake_data(mesh, 0.0, settings.parent_axis_y_mode, uv_index, settings.uvmap_name, uv_channel, settings.parent_axis_y_rgba, settings.invert_v)
                                else:
                                    bake_data(mesh, 0.0, settings.parent_axis_y_mode, settings.parent_axis_y_uv_index, settings.parent_axis_y_uv_channel, settings.uvmap_name, settings.parent_axis_y_rgba, settings.invert_v)
                            elif xyz_comp == "Z" and settings.parent_axis_z:
                                use_vcol = settings.parent_axis_z_mode == "VCOL"
                                if parent_auto_mode:
                                    bake_data(mesh, 0.0, settings.parent_axis_z_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_axis_z_rgba, settings.invert_v)
                                else:
                                    bake_data(mesh, 0.0, settings.parent_axis_z_mode, settings.parent_axis_z_uv_index, settings.parent_axis_z_uv_channel, settings.uvmap_name, settings.parent_axis_z_rgba, settings.invert_v)
                            else:
                                continue

                            if parent_auto_mode and not use_vcol:
                                uv_channel_index += 1

                    # AB or XYZ PACKED AXIS
                    elif settings.parent_axis_channel_mode != "POSITION_PACKED":
                        uv_index = settings.parent_position_packed_uv_index
                        uv_channel = settings.parent_position_packed_uv_channel
                        if parent_auto_mode:
                            uv_index = uv_channel_index // 2
                            uv_channel = "U" if uv_channel_index % 2 == 0 else "V"

                            uv_channel_index += 1

                        bake_data(mesh, 0.0, "UV", uv_index, uv_channel, settings.uvmap_name, 0, settings.invert_v)
                # no parent means we move onto the next object
                continue

            # parent object is valid here
            parent_obj = parent_objs[depth]
            if parent_obj == None:
                continue

            parent_obj_quat = parent_obj.matrix_world.to_quaternion()
            parent_axis_to_bake = get_bake_axis(parent_obj_quat, settings.parent_axis_component, signed_axis, False)

            # POSITION
            if settings.parent_position:
                # get parent's position in world space, to scale
                parent_location_to_bake = parent_obj.matrix_world.to_translation() * signed_scale

                if settings.parent_position_channel_mode == "INDIVIDUAL":
                    # prevent parent pivot to be exactly at 0,0,0 in case the parent is indeed at origin because then we couldn't mask it in-engine based on pivot's distance from origin so we need to shift it by at least some amount to indicate there's indeed a valid parent here
                    if parent_location_to_bake.length < 1:
                        parent_location_to_bake = mathutils.Vector((1.001,1.001,1.001))

                    # packing axis is only available if we pack X/Y/Z components individually
                    if settings.parent_axis_channel_mode == "POSITION_PACKED":
                        parent_axis_to_bake = (parent_axis_to_bake + XYZUNITVECTOR) * 0.5

                        # round position & pack axis in the fractional part
                        parent_location_to_bake.x = math.floor(parent_location_to_bake.x) + parent_axis_to_bake.x
                        parent_location_to_bake.y = math.floor(parent_location_to_bake.y) + parent_axis_to_bake.y
                        parent_location_to_bake.z = math.floor(parent_location_to_bake.z) + parent_axis_to_bake.z

                    for xyz_comp in XYZLIST:
                        uv_index = uv_channel_index // 2
                        uv_channel = "U" if uv_channel_index % 2 == 0 else "V"

                        use_vcol = False
                        if xyz_comp == "X" and settings.parent_position_x:
                            data_to_bake = parent_location_to_bake.x

                            use_vcol = settings.parent_position_x_mode == "VCOL"
                            if use_vcol:
                                data_to_bake = data_to_bake * packing_divisor
                                data_to_bake = (data_to_bake + 1) * 0.5
                            
                            if parent_auto_mode:
                                bake_data(mesh, data_to_bake, settings.parent_position_x_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_position_x_rgba, settings.invert_v)
                            else:
                                bake_data(mesh, data_to_bake, settings.parent_position_x_mode, settings.parent_position_x_uv_index, settings.parent_position_x_uv_channel, settings.uvmap_name, settings.parent_position_x_rgba, settings.invert_v)
                        elif xyz_comp == "Y" and settings.parent_position_y:
                            data_to_bake = parent_location_to_bake.y
                            
                            use_vcol = settings.parent_position_y_mode == "VCOL"
                            if use_vcol:
                                data_to_bake = data_to_bake * packing_divisor
                                data_to_bake = (data_to_bake + 1) * 0.5
                            
                            if parent_auto_mode:
                                bake_data(mesh, data_to_bake, settings.parent_position_y_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_position_y_rgba, settings.invert_v)
                            else:
                                bake_data(mesh, data_to_bake, settings.parent_position_y_mode, settings.parent_position_y_uv_index, settings.parent_position_y_uv_channel, settings.uvmap_name, settings.parent_position_y_rgba, settings.invert_v)
                        elif xyz_comp == "Z" and settings.parent_position_z:
                            data_to_bake = parent_location_to_bake.z

                            use_vcol = settings.parent_position_z_mode == "VCOL"
                            if use_vcol:
                                data_to_bake = data_to_bake * packing_divisor
                                data_to_bake = (data_to_bake + 1) * 0.5
                            
                            if parent_auto_mode:
                                bake_data(mesh, data_to_bake, settings.parent_position_z_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_position_z_rgba, settings.invert_v)
                            else:
                                bake_data(mesh, data_to_bake, settings.parent_position_z_mode, settings.parent_position_z_uv_index, settings.parent_position_z_uv_channel, settings.uvmap_name, settings.parent_position_z_rgba, settings.invert_v)
                        else:
                            continue
                          
                        if parent_auto_mode and not use_vcol:
                            uv_channel_index += 1
                        
                # PACKED
                else:
                    # prevent parent pivot to be exactly at 0,0,0 in case the parent is indeed at origin because then we couldn't mask it in-engine based on pivot's distance from origin so we need to shift it by at least some amount to indicate there's indeed a valid parent here
                    if parent_location_to_bake.length < 1:
                        precision_offset = (1.0 / 65536.0) * packing_multiplier # 16bits precision?
                        if settings.parent_position_channel_mode == "XYZ_PACKED":
                            precision_offset = (1.0 / 256.0) * packing_multiplier # 8bits precision?
                        parent_location_to_bake = mathutils.Vector((precision_offset, precision_offset, precision_offset))
                    
                    parent_location_to_bake = mathutils.Vector((
                        max(min(parent_location_to_bake.x * packing_divisor, 1.0), -1.0),
                        max(min(parent_location_to_bake.y * packing_divisor, 1.0), -1.0),
                        max(min(parent_location_to_bake.z * packing_divisor, 1.0), -1.0)
                        ))

                    parent_location_to_bake = (parent_location_to_bake + XYZUNITVECTOR) * 0.5
                    
                    # X/Y or X/Z or Y/Z POSITION
                    if settings.parent_position_channel_mode == "AB_PACKED":
                        data_to_bake = get_packed_ab_vector(parent_location_to_bake, settings.parent_position_ab_packed_a_comp, settings.parent_position_ab_packed_b_comp)
                    # XYZ POSITION
                    elif settings.parent_position_channel_mode == "XYZ_PACKED":
                        data_to_bake = get_packed_xyz_vector(parent_location_to_bake)
                    
                    uv_index = settings.parent_position_packed_uv_index
                    uv_channel = settings.parent_position_packed_uv_channel
                    if parent_auto_mode:
                        uv_index = uv_channel_index // 2
                        uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                        
                        uv_channel_index += 1
                    
                    bake_data(mesh, data_to_bake, "UV", uv_index, uv_channel, settings.uvmap_name, 0, settings.invert_v)

            # AXIS
            if settings.parent_axis and settings.parent_axis_channel_mode != "POSITION_PACKED":
                if settings.parent_axis_channel_mode == "INDIVIDUAL":
                    for xyz_comp in XYZLIST:
                        uv_index = uv_channel_index // 2
                        uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                        
                        use_vcol = False
                        if xyz_comp == "X" and settings.parent_axis_x:
                            data_to_bake = parent_axis_to_bake.x
                            
                            use_vcol = settings.parent_axis_x_mode == "VCOL"
                            if use_vcol:
                                data_to_bake = (data_to_bake + 1) * 0.5
                            
                            if parent_auto_mode:
                                bake_data(mesh, data_to_bake, settings.parent_axis_x_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_axis_x_rgba, settings.invert_v)
                            else:
                                bake_data(mesh, data_to_bake, settings.parent_axis_x_mode, settings.parent_axis_x_uv_index, settings.parent_axis_x_uv_channel, settings.uvmap_name, settings.parent_axis_x_rgba, settings.invert_v)
                        elif xyz_comp == "Y" and settings.parent_axis_y:
                            data_to_bake = parent_axis_to_bake.y
                            
                            use_vcol = settings.parent_axis_y_mode == "VCOL"
                            if use_vcol:
                                data_to_bake = (data_to_bake + 1) * 0.5
                            
                            if parent_auto_mode:
                                bake_data(mesh, data_to_bake, settings.parent_axis_y_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_axis_z_rgba, settings.invert_v)
                            else:
                                bake_data(mesh, data_to_bake, settings.parent_axis_y_mode, settings.parent_axis_y_uv_index, settings.parent_axis_y_uv_channel, settings.uvmap_name, settings.parent_axis_y_rgba, settings.invert_v)
                        elif xyz_comp == "Z" and settings.parent_axis_z:
                            data_to_bake = parent_axis_to_bake.z
                            
                            use_vcol = settings.parent_axis_z_mode == "VCOL"
                            if use_vcol:
                                data_to_bake = (data_to_bake + 1) * 0.5
                            
                            if parent_auto_mode:
                                bake_data(mesh, data_to_bake, settings.parent_axis_z_mode, uv_index, uv_channel, settings.uvmap_name, settings.parent_axis_z_rgba, settings.invert_v)
                            else:
                                bake_data(mesh, data_to_bake, settings.parent_axis_z_mode, settings.parent_axis_z_uv_index, settings.parent_axis_z_uv_channel, settings.parent_axis_z_rgba, settings.invert_v)
                        else:
                            continue
                        
                        if parent_auto_mode and not use_vcol:
                            uv_channel_index += 1
                # PACKED
                else:
                    parent_axis_to_bake = (parent_axis_to_bake + XYZUNITVECTOR) * 0.5
                
                    # X/Y or X/Z or Y/Z AXIS
                    if settings.parent_axis_channel_mode == "AB_PACKED":
                        data_to_bake = get_packed_ab_vector(parent_axis_to_bake, settings.parent_axis_ab_packed_a_comp, settings.parent_axis_ab_packed_b_comp)
                    # XYZ AXIS
                    else:
                        data_to_bake = get_packed_xyz_vector(parent_axis_to_bake)
                    
                    uv_index = settings.parent_axis_packed_uv_index
                    uv_channel = settings.parent_axis_packed_uv_channel
                    if parent_auto_mode:
                        uv_index = uv_channel_index // 2
                        uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                        
                        uv_channel_index += 1
                    
                    bake_data(mesh, data_to_bake, "UV", uv_index, uv_channel, settings.uvmap_name, 0, settings.invert_v)
            
    return True

def bake_fixed_value(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.fixed_value:
        add_bake_report("fixed_value", True)
        add_bake_report("fixed_value_data", settings.fixed_value_data)
        add_bake_report("fixed_value_mode", settings.fixed_value_mode)
        add_bake_report("fixed_value_uv_index", settings.fixed_value_uv_index)
        add_bake_report("fixed_value_uv_channel", settings.fixed_value_uv_channel)
        add_bake_report("fixed_value_rgba", settings.fixed_value_rgba)
    else:
        return False
    
    for mesh in meshes:
        bake_data(mesh, settings.fixed_value_data, settings.fixed_value_mode, settings.fixed_value_uv_index, settings.fixed_value_uv_channel, settings.uvmap_name, settings.fixed_value_rgba, settings.invert_v)
    
    return True

def bake_direction(context, meshes, empties):
    """ """

    settings = context.scene.DataBakerSettings
    if settings.direction:
        add_bake_report("direction", True)
        add_bake_report("direction_mode", settings.direction_mode)
        add_bake_report("direction_vector_x", settings.direction_vector_x)
        add_bake_report("direction_vector_y", settings.direction_vector_y)
        add_bake_report("direction_vector_z", settings.direction_vector_z)
        add_bake_report("direction_pack_mode", settings.direction_pack_mode)
    else:
        return False

    direction = mathutils.Vector((0.0, 0.0, 0.0))
    
    # shared for all meshes
    if settings.direction_mode == "3DVECTOR":
        normalized_direction = mathutils.Vector((settings.direction_vector_x, settings.direction_vector_y, settings.direction_vector_z)).normalized()

        Direction = normalized_direction
    elif settings.direction_mode == "2DVECTOR":
        normalized_direction = mathutils.Vector((settings.direction_vector_x, settings.direction_vector_y, 0.0)).normalized() # nullify Z

        direction = normalized_direction
    
    for mesh in meshes:
        if settings.direction_mode == "3DRAND":
            # https://gist.github.com/andrewbolster/10274979
            phi = np.random.uniform(0,np.pi*2)
            costheta = np.random.uniform(-1,1)

            theta = np.arccos( costheta )
            x = np.sin( theta) * np.cos( phi )
            y = np.sin( theta) * np.sin( phi )
            z = np.cos( theta )

            direction = mathutils.Vector((x,y,z))
        elif settings.direction_mode == "2DRAND":
            x = np.random.uniform(-math.pi, math.pi)
            cosx = math.cos(x)
            sinx = math.sin(x)

            direction = mathutils.Vector((cosx,sinx,0.0))

        if settings.direction_pack_mode == "VCOL":
            direction = (direction * HALFXYZVECTOR) + HALFXYZVECTOR

            if (settings.direction_mode == "3DVECTOR" or settings.direction_mode == "3DRAND"):
                bake_data(mesh, direction, settings.direction_pack_mode, 0, 0, settings.uvmap_name, 'RGB', settings.invert_v)
            else:
                bake_data(mesh, direction, settings.direction_pack_mode, 0, 0, settings.uvmap_name, 'RG', settings.invert_v)
        else:
            bake_data(mesh, direction, settings.direction_pack_mode, 0, 0, settings.uvmap_name, '', settings.invert_v)

    return True

#################
### BAKE INFO ###
def get_bake_info(context):
    """ """

    info_uv   = []
    info_vcol = []
    info_normal  = []

    for bake_info_function in get_bake_info_functions():
        bake_info, bake_info_uv, bake_info_vcol, bake_info_normal = bake_info_function(context)

        if bake_info:
            info_uv.extend(bake_info_uv)
            info_vcol.extend(bake_info_vcol)
            info_normal.extend(bake_info_normal)

    return (info_uv, info_vcol, info_normal)

def get_bake_info_functions():
    """ """
    return [
        get_bake_position_info,
        get_bake_axis_info,
        get_bake_shapekey_offset_info,
        get_bake_shapekey_normal_info,
        get_bake_linear_mask_info,
        get_bake_sphere_mask_info,
        get_bake_per_collection_random_info,
        get_bake_per_object_random_info,
        get_bake_per_poly_random_info,
        get_bake_parent_info,
        get_bake_fixed_value_info,
        get_bake_direction_info
    ]

def get_bake_position_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.position:
        if settings.position_channel_mode == "INDIVIDUAL":
            axis_packed = settings.axis and settings.axis_channel_mode == "POSITION_PACKED" # requires 32 bits if true

            if settings.position_x:
                ID = "Position X"
                if settings.position_x_mode == "UV":
                    if axis_packed:
                        ID = "Position And Axis X"

                    info_uv.append((ID, settings.position_x_uv_index, settings.position_x_uv_channel, axis_packed, axis_packed, False, settings.position_channel_mode))
                elif settings.position_x_mode == "VCOL":
                    info_vcol.append((ID, settings.position_x_rgba, True))

            if settings.position_y:
                ID = "Position Y"
                if settings.position_y_mode == "UV":
                    if axis_packed:
                        ID = "Position And Axis Y"

                    info_uv.append((ID, settings.position_y_uv_index, settings.position_y_uv_channel, axis_packed, axis_packed, False, settings.position_channel_mode))
                elif settings.position_y_mode == "VCOL":
                    info_vcol.append((ID, settings.position_y_rgba, True))

            if settings.position_z:
                ID = "Position Z"
                if settings.position_z_mode == "UV":
                    if axis_packed:
                        ID = "Position And Axis Z"

                    info_uv.append((ID, settings.position_z_uv_index, settings.position_z_uv_channel, axis_packed, axis_packed, False, settings.position_channel_mode))
                elif settings.position_z_mode == "VCOL":
                    info_vcol.append((ID, settings.position_z_rgba, True))
        else:
            if settings.position_channel_mode == "XYZ_PACKED":
                ID = "Position XYZ"
            elif settings.position_channel_mode == "AB_PACKED":
                ID = "Position " + settings.position_ab_packed_a_comp + settings.position_ab_packed_b_comp

            info_uv.append((ID, settings.position_packed_uv_index, settings.position_packed_uv_channel, False, True, True, settings.position_channel_mode))

    return (settings.position, info_uv, info_vcol, info_normal)

def get_bake_axis_info(context):
    """ """
    
    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.axis:
        if settings.axis_channel_mode == "INDIVIDUAL":
            if settings.axis_x:
                ID = "Axis X"
                if settings.axis_x_mode == "UV":
                    info_uv.append((ID, settings.axis_x_uv_index, settings.axis_x_uv_channel, False, False, False, settings.axis_channel_mode))
                elif settings.axis_x_mode == "VCOL":
                    info_vcol.append((ID, settings.axis_x_rgba, False))

            if settings.axis_y:
                ID = "Axis Y"
                if settings.axis_y_mode == "UV":
                    info_uv.append((ID, settings.axis_y_uv_index, settings.axis_y_uv_channel, False, False, False, settings.axis_channel_mode))
                elif settings.axis_y_mode == "VCOL":
                    info_vcol.append((ID, settings.axis_y_rgba, False)) 

            if settings.axis_z:
                ID = "Axis Z"
                if settings.axis_z_mode == "UV":
                    info_uv.append((ID, settings.axis_z_uv_index, settings.axis_z_uv_channel, False, False, False, settings.axis_channel_mode))
                elif settings.axis_z_mode == "VCOL":
                    info_vcol.append((ID, settings.axis_z_rgba, False)) 
        elif settings.axis_channel_mode != "POSITION_PACKED":
            if settings.axis_channel_mode == "XYZ_PACKED":
                ID = "Axis XYZ"
            elif settings.axis_channel_mode == "AB_PACKED":
                ID = "Axis " + settings.axis_ab_packed_a_comp + settings.axis_ab_packed_b_comp

            info_uv.append((ID, settings.axis_packed_uv_index, settings.axis_packed_uv_channel, False, True, False, settings.axis_channel_mode))
    
    return (settings.axis, info_uv, info_vcol, info_normal)

def get_bake_shapekey_offset_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.shapekey_offset:
        if settings.shapekey_offset_channel_mode == "INDIVIDUAL":
            normal_packed = settings.shapekey_normal and settings.shapekey_normal_channel_mode == "POSITION_PACKED" # requires 32 bits if True
            
            if settings.shapekey_offset_x:
                ID = "Shapekey Offset X"
                if settings.shapekey_offset_x_mode == "UV":
                    if normal_packed:
                        ID = "Shapekey Offset & Normal X"

                    info_uv.append((ID, settings.shapekey_offset_x_uv_index, settings.shapekey_offset_x_uv_channel, normal_packed, normal_packed, False, settings.shapekey_offset_channel_mode))
                elif settings.shapekey_offset_x_mode == "VCOL":
                    info_vcol.append((ID, settings.shapekey_offset_x_rgba, True)) 

            if settings.shapekey_offset_y:
                ID = "Shapekey Offset Y"
                if settings.shapekey_offset_y_mode == "UV":
                    if normal_packed:
                        ID = "Shapekey Offset & Normal Y"
                    
                    info_uv.append((ID, settings.shapekey_offset_y_uv_index, settings.shapekey_offset_y_uv_channel, normal_packed, normal_packed, False, settings.shapekey_offset_channel_mode))
                elif settings.shapekey_offset_y_mode == "VCOL":
                    info_vcol.append((ID, settings.shapekey_offset_y_rgba, True)) 

            if settings.shapekey_offset_z:
                ID = "Shapekey Offset Z"
                if settings.shapekey_offset_z_mode == "UV":
                    if normal_packed:
                        ID = "Shapekey Offset & Normal Z"

                    info_uv.append((ID, settings.shapekey_offset_z_uv_index, settings.shapekey_offset_z_uv_channel, normal_packed, normal_packed, False, settings.shapekey_offset_channel_mode))
                elif settings.shapekey_offset_z_mode == "VCOL":
                    info_vcol.append((ID, settings.shapekey_offset_z_rgba, True)) 
        else:
            if settings.shapekey_offset_channel_mode == "XYZ_PACKED":
                ID = "Shapekey Offset XYZ"
                
            elif settings.shapekey_offset_channel_mode == "AB_PACKED":
                ID = "Shapekey Offset " + settings.shapekey_offset_ab_packed_a_comp + settings.shapekey_offset_ab_packed_b_comp

            info_uv.append((ID, settings.shapekey_offset_packed_uv_index, settings.shapekey_offset_packed_uv_channel, False, True, True, settings.shapekey_offset_channel_mode))

    return (settings.shapekey_offset, info_uv, info_vcol, info_normal)
        
def get_bake_shapekey_normal_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.shapekey_normal:
        if settings.shapekey_normal_channel_mode == "INDIVIDUAL":
            if settings.shapekey_normal_x:
                ID = "Shapekey Normal X"
                if settings.shapekey_normal_x_mode == "UV":
                    info_uv.append((ID, settings.shapekey_normal_x_uv_index, settings.shapekey_normal_x_uv_channel, False, False, False, settings.shapekey_normal_channel_mode))
                elif settings.shapekey_normal_x_mode == "VCOL":
                    info_vcol.append((ID, settings.shapekey_normal_x_rgba, False))

            if settings.shapekey_normal_y:
                ID = "Shapekey Normal Y"
                if settings.shapekey_normal_y_mode == "UV":
                    info_uv.append((ID, settings.shapekey_normal_y_uv_index, settings.shapekey_normal_y_uv_channel, False, False, False, settings.shapekey_normal_channel_mode))
                elif settings.shapekey_normal_y_mode == "VCOL":
                    info_vcol.append((ID, settings.shapekey_normal_y_rgba, False))
                    
            if settings.shapekey_normal_z:
                ID = "Shapekey Normal Z"
                if settings.shapekey_normal_z_mode == "UV":
                    info_uv.append((ID, settings.shapekey_normal_z_uv_index, settings.shapekey_normal_z_uv_channel, False, False, False, settings.shapekey_normal_channel_mode))
                elif settings.shapekey_normal_z_mode == "VCOL":
                    info_vcol.append((ID, settings.shapekey_normal_z_rgba, False))
        elif settings.shapekey_normal_channel_mode != "OFFSET_PACKED":
            if settings.shapekey_normal_channel_mode == "XYZ_PACKED":
                ID = "Shapekey Normal XYZ"
            
            elif settings.shapekey_normal_channel_mode == "AB_PACKED":
                ID = "Shapekey Normal " + settings.shapekey_normal_ab_packed_a_comp + settings.shapekey_normal_ab_packed_b_comp

            info_uv.append((ID, settings.shapekey_normal_xyz_uv_index, settings.shapekey_normal_xyz_uv_channel, False, True, False, settings.shapekey_normal_channel_mode))

    return (settings.shapekey_normal, info_uv, info_vcol, info_normal)
           
def get_bake_linear_mask_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.linear_mask:
        ID = "Linear Mask"
        if settings.linear_mask_mode == "UV":
            info_uv.append((ID, settings.linear_mask_uv_index, settings.linear_mask_uv_channel, False, False, False, ""))
        elif settings.linear_mask_mode == "VCOL":
            info_vcol.append((ID, settings.linear_mask_rgba, False))

    return (settings.linear_mask, info_uv, info_vcol, info_normal)

def get_bake_sphere_mask_info(context):
    """ """
     
    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.sphere_mask:
        ID = "Sphere Mask"
        if settings.sphere_mask_mode == "UV":
            info_uv.append((ID, settings.sphere_mask_uv_index, settings.sphere_mask_uv_channel, False, False, False, ""))
        elif settings.sphere_mask_mode == "VCOL":
            info_vcol.append((ID, settings.sphere_mask_rgba, False))

    return (settings.sphere_mask, info_uv, info_vcol, info_normal)

def get_bake_per_collection_random_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.random_per_collection:
        ID = "Per Collection Random"
        if settings.random_per_collection_mode == "UV":
            info_uv.append((ID, settings.random_per_collection_uv_index, settings.random_per_collection_uv_channel, False, False, False, ""))
        elif settings.random_per_collection_mode == "VCOL":
            info_vcol.append((ID, settings.random_per_collection_rgba, False))

    return (settings.random_per_collection, info_uv, info_vcol, info_normal)

def get_bake_per_object_random_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.random_per_object:
        ID = "Per Object Random"
        if settings.random_per_object_mode == "UV":
            info_uv.append((ID, settings.random_per_object_uv_index, settings.random_per_object_uv_channel, False, False, False, ""))
        elif settings.random_per_object_mode == "VCOL":
            info_vcol.append((ID, settings.random_per_object_rgba, False))

    return (settings.random_per_object, info_uv, info_vcol, info_normal)

def get_bake_per_poly_random_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.random_per_poly:
        ID = "Per Poly Random"
        if settings.random_per_poly_mode == "UV":
            info_uv.append((ID, settings.random_per_poly_uv_index, settings.random_per_poly_uv_channel, False, False, False, ""))
        elif settings.random_per_poly_mode == "VCOL":
            info_vcol.append((ID, settings.random_per_poly_rgba, False))

    return (settings.random_per_poly, info_uv, info_vcol, info_normal)

def get_bake_parent_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.parent_position or settings.parent_axis:
        # AUTOMATIC
        parent_auto_mode = settings.parent_mode == "AUTOMATIC"

        uv_channel_index = (settings.parent_automatic_uv_index * 2) + (0 if settings.parent_automatic_uv_channel == "U" else 1)
        uv_index = uv_channel_index // 2
        uv_channel = 0 if uv_channel_index % 2 == 0 else 1

        manual_max_depth = max(min(settings.parent_depth, settings.parent_max_depth), 1.0)

        ID = ""

        for depth in range(settings.parent_max_depth):
            if parent_auto_mode:
                # only process the desired depth if in manual mode
                if settings.parent_mode == "MANUAL":
                    if depth != (manual_max_depth + 1):
                        continue
            
            hierarchy_index = settings.parent_max_depth - (depth + 1)
            
            # parent position
            if settings.parent_position:
                if settings.parent_position_channel_mode == "INDIVIDUAL":
                    axis_packed = settings.parent_axis and settings.parent_axis_channel_mode == "POSITION_PACKED" # requires 32 bits if True
                    
                    for xyz_comp in XYZLIST:
                        uv_index = uv_channel_index // 2
                        uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                        
                        # X position?
                        if xyz_comp == "X" and settings.parent_position_x:
                            ID = "Parent " + str(hierarchy_index) + " Position X"
                            if settings.parent_position_x_mode == "UV":
                                if axis_packed:
                                    ID = "Parent " + str(hierarchy_index) + " Position And Axis X"

                                uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_position_x_uv_index
                                uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_position_x_uv_channel

                                info_uv.append((ID, uv_channel_index_to_use, uv_channel_channel_to_use, axis_packed, axis_packed, False, settings.parent_position_channel_mode))
                            elif settings.parent_position_x_mode == "VCOL":
                                info_vcol.append((ID, settings.parent_position_x_rgba, True))
                        # Y position?
                        elif xyz_comp == "Y" and settings.parent_position_y:                    
                            ID = "Parent " + str(hierarchy_index) + " Position Y"
                            if settings.parent_position_y_mode == "UV":
                                if axis_packed:
                                    ID = "Parent " + str(hierarchy_index) + " Position And Axis Y"
                                
                                uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_position_y_uv_index
                                uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_position_y_uv_channel

                                info_uv.append((ID, uv_channel_index_to_use, uv_channel_channel_to_use, axis_packed, axis_packed, False, settings.parent_position_channel_mode))
                            elif settings.parent_position_y_mode == "VCOL":
                                info_vcol.append((ID, settings.parent_position_y_rgba, True))
                        # Z position?
                        elif xyz_comp == "Z" and settings.parent_position_z:
                            ID = "Parent " + str(hierarchy_index) + " Position Z"
                            if settings.parent_position_z_mode == "UV":
                                if axis_packed:
                                    ID = "Parent " + str(hierarchy_index) + " Position And Axis Z"
                                
                                uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_position_z_uv_index
                                uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_position_z_uv_channel

                                info_uv.append((ID, uv_channel_index_to_use, uv_channel_channel_to_use, axis_packed, axis_packed, False, settings.parent_position_channel_mode))
                            elif settings.parent_position_z_mode == "VCOL":
                                info_vcol.append((ID, settings.parent_position_z_rgba, True))
                        else:
                            continue
                        
                        uv_channel_index += 1
                else:
                    if settings.parent_position_channel_mode == "XYZ_PACKED":
                        ID = "Parent " + str(hierarchy_index) + " Position XYZ"
                    elif settings.parent_position_channel_mode == "AB_PACKED":
                        ID = "Parent " + str(hierarchy_index) + " Position " + settings.parent_position_ab_packed_a_comp + settings.parent_position_ab_packed_b_comp

                    uv_index = uv_channel_index // 2
                    uv_channel = "U" if uv_channel_index % 2 == 0 else "V"

                    uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_position_packed_uv_index
                    uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_position_packed_uv_channel

                    info_uv.append((ID, uv_channel_index_to_use, uv_channel_channel_to_use, False, True, True, settings.parent_position_channel_mode))

                    uv_channel_index += 1
            # parent axis
            if settings.parent_axis:
                if settings.parent_axis_channel_mode == "INDIVIDUAL":
                    for xyz_comp in XYZLIST:
                        uv_index = uv_channel_index // 2
                        uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                        
                        # X component?
                        if xyz_comp == "X" and settings.parent_axis_x:
                            ID = "Parent " + str(hierarchy_index) + " Axis X"
                            if settings.parent_axis_x_mode == "UV":
                                uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_axis_x_uv_index
                                uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_axis_x_uv_channel
                                
                                info_uv.append((ID, uv_index, uv_channel_index, False, False, False, settings.parent_axis_channel_mode))
                            elif settings.parent_axis_x_mode == "VCOL":
                                info_vcol.append((ID, settings.parent_axis_x_rgba, False))
                        # Y component?
                        elif xyz_comp == "Y" and settings.parent_axis_y:
                            ID = "Parent " + str(hierarchy_index) + " Axis Y"
                            if settings.parent_axis_y_mode == "UV":
                                uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_axis_y_uv_index
                                uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_axis_y_uv_channel
                                
                                info_uv.append((ID, uv_index, uv_channel_index, False, False, False, settings.parent_axis_channel_mode))
                            elif settings.parent_axis_y_mode == "VCOL":
                                info_vcol.append((ID, settings.parent_axis_y_rgba, False))
                        # Z component?
                        elif xyz_comp == "Z" and settings.parent_axis_z:
                            ID = "Parent " + str(hierarchy_index) + " Axis Z"
                            if settings.parent_axis_z_mode == "UV":
                                uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_axis_z_uv_index
                                uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_axis_z_uv_channel
                                
                                info_uv.append((ID, uv_index, uv_channel_index, False, False, False, settings.parent_axis_channel_mode))
                            elif settings.parent_axis_z_mode == "VCOL":
                                info_vcol.append((ID, settings.parent_axis_z_rgba, False))
                        else:
                            continue

                        uv_channel_index += 1
                elif settings.parent_axis_channel_mode != "POSITION_PACKED":
                    if settings.parent_axis_channel_mode == "XYZ_PACKED":
                        ID = "Parent " + str(hierarchy_index) + " Axis XYZ"
                    elif settings.parent_axis_channel_mode == "AB_PACKED":
                        ID = "Parent " + str(hierarchy_index) + " Axis " + settings.parent_axis_ab_packed_a_comp + settings.parent_axis_ab_packed_b_comp
                    else:
                        continue
                    
                    uv_index = uv_channel_index // 2
                    uv_channel = "U" if uv_channel_index % 2 == 0 else "V"
                    
                    uv_channel_index_to_use = uv_index if parent_auto_mode else settings.parent_axis_packed_uv_index
                    uv_channel_channel_to_use = uv_channel if parent_auto_mode else settings.parent_axis_packed_uv_channel

                    info_uv.append((ID, uv_index, uv_channel, False, True, False, settings.parent_axis_channel_mode))

                    uv_channel_index += 1

    return (settings.parent_position or settings.parent_axis, info_uv, info_vcol, info_normal)

def get_bake_fixed_value_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.fixed_value:
        ID = "Fixed Value"
        if settings.fixed_value_mode == "UV":
            info_uv.append((ID, settings.fixed_value_uv_index, settings.fixed_value_uv_channel, False, False, False, ""))
        elif settings.fixed_value_mode == "VCOL":
            info_vcol.append((ID, settings.fixed_value_rgba, False))

    return (settings.fixed_value, info_uv, info_vcol, info_normal)

def get_bake_direction_info(context):
    """ """

    settings = context.scene.DataBakerSettings

    info_uv   = [] # ID, uv_index, uv_channel, unit axis or normal packed in position?, requires 32 bits?, requires multiplier?, channel mode
    info_vcol = [] # ID, rgba_channel, requires multiplier?
    info_normal  = [] # normal_component

    if settings.direction:
        ID = "Direction"
        if settings.direction_pack_mode == "VCOL":
            info_vcol.append((ID + " X", 'R', False))
            info_vcol.append((ID + " Y", 'G', False))
            
            if settings.direction_mode == "3DVECTOR" or settings.direction_mode == "3DRAND":
                info_vcol.append((ID + " Z", 'B', False))
        elif settings.direction_pack_mode == "NORMALS":
            info_normal.append(ID + " X")
            info_normal.append(ID + " Y")

            if settings.direction_mode == "3DVECTOR" or settings.direction_mode == "3DRAND":
                info_normal.append(ID + " Z")

    return (settings.direction, info_uv, info_vcol, info_normal)

##############
### MESHES ###
def export_mesh(context, bake_name, objs_to_export):
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
        return (False, msg, None, -1)

    return (True, "", export_path)

###########
### XML ###
def export_xml(context):
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
def get_path(path, file_name, file_ext, tags, override_file):
    """ Compiles file path/name/extension into a path and performs a couples of safety checks """
    
    file_exts = [".png", ".exr", ".fbx"]
    if file_ext not in file_exts:
        return (False, "Invalid File Extension", "")

    file_name = replace_tags(file_name, tags)
    export_path = os.path.abspath(os.path.join(bpy.path.abspath(path), file_name + file_ext))
    success, msg = check_path(export_path, override_file)
    
    return (success, msg, export_path)

def replace_tags(name, tags):
    # check tags
    for tag_key, tag_value in tags.items():
        tag = "<"+tag_key+">"
        if (tag in name):
            name = name.replace(tag, tag_value)

    return name

def check_path(path, override_file):
    """ """
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        return (False, f"Directory does not exist: {dir}")
    
    if not os.access(dir, os.W_OK):
        return (False, f"Directory is not writable: {dir}")

    if os.path.isfile(path) and not override_file:
        return (False, f"File already exists: {path}")

    return (True, "")