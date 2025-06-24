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
from mathutils import geometry
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
    settings = context.scene.SDFBakerSettings

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

def reset_bake_report():
    """
    Set all report properties to their default values

    :return: None
    :rtype: None
    """
    report = bpy.context.scene.SDFBakerReport

    report.baked = False
    report.success = False
    report.msg = ""
    report.name = ""
    report.ID = ""

    report.unit_system = ""
    report.unit_unit = ""
    report.unit_length = 0.0
    report.unit_scale = 0.0

    report.distance_mode = ""
    report.sdf_mode = ""
    report.sdf_bounds = None

    report.xml = False
    report.xml_path = ""

    report.unit_scale = 0.0
    report.unit_invert_x = False
    report.unit_invert_y = False
    report.unit_invert_z = False
    
    report.frames = 0
    report.x = 0
    report.y = 0
    report.z = 0
    report.max_dist = 0.0

    report.offset = mathutils.Vector((0.0, 0.0, 0.0))

    report.tile_sort_mode = ""
    report.unit_invert_v = False
    report.invert_sign = False
    report.two_sided = False

    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_min_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    report.mesh_max_bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))

    report.tex = None
    report.tex_width = 0
    report.tex_height = 0
    report.tex_slices = 0
    report.tex_export = False
    report.tex_path = ""

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """
    Set a value in the bake report

    :param prop_name: report property to set
    :param prop_value: value to assign to the property
    :return: None
    :rtype: None
    """
    setattr(bpy.context.scene.SDFBakerReport, prop_name, prop_value)

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
def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object]:
    """
    Return the filtered list of objects to bake, as well as the active object

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of objects to bake and active object
    :rtype: tuple
    """

    settings = context.scene.SDFBakerSettings

    active_obj = context.view_layer.objects.active # cache active object

    for selected_object in context.selected_objects:
        if selected_object.type != "MESH":
            selected_object.select_set(False)

        if settings.sdf_mode == "CUSTOM":
            if selected_object == settings.sdf_bounds:
                selected_object.select_set(False) # deselect custom bounds!

    objs_to_bake = context.selected_objects
    if len(objs_to_bake) <= 0:
        return (False, "No mesh selected", None, None)

    for selected_object in context.selected_objects:
        selected_object.select_set(False)

    if active_obj is None:
        active_obj = objs_to_bake[0]
        #context.view_layer.objects.active = active_obj
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

    settings = context.scene.SDFBakerSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.SDF"
    tags = { "BakeName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def get_bake_obj(context: bpy.types.Context, objs_to_bake: list, bake_name: str) -> tuple[bool, str, bpy.types.Object]:
    """
    Return the objects to bake, duplicated and merged as a single object

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :param bake_name: the bake operation's 'name'
    :return: the function's success, potential error message, merged object
    :rtype: tuple
    """

    settings = context.scene.SDFBakerSettings

    #scene = bpy.data.scenes.get("SDFBaker", None)
    #if scene is None:
        #scene = bpy.data.scenes.new("SDFBaker")
    scene = bpy.context.scene

    dgraph = bpy.context.evaluated_depsgraph_get()

    name = bake_name + ".source" if bake_name != "" else "BakedMesh.SDF.source"
    mesh = bpy.data.meshes.new(name)

    bm = bmesh.new()
    for obj_to_bake in objs_to_bake:
        obj_eval = obj_to_bake.evaluated_get(dgraph)
        mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
        mesh_eval.transform(obj_eval.matrix_world)

        bm.from_mesh(mesh_eval)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        obj_eval.to_mesh_clear()

    bm.to_mesh(mesh)
    bm.free()

    if mesh.vertices and (len(mesh.vertices) <= 0 or len(mesh.polygons) <= 0):
        bpy.data.meshes.remove(mesh) # clean
        return (False, "Mesh has no faces or vertices", None)

    if settings.unit_invert_x or settings.unit_invert_y or settings.unit_invert_z:    
        custom_bounds = False
        if settings.sdf_mode == "CUSTOM" and settings.sdf_bounds:
            if settings.sdf_bounds.type == "MESH" or settings.sdf_bounds.type == "EMPTY":
                custom_bounds = True
        
        if custom_bounds:
            mirror_pos = settings.sdf_bounds.matrix_world.to_translation()
            mirror_pos.x = mirror_pos.x if settings.unit_invert_x else 0
            mirror_pos.y = mirror_pos.y if settings.unit_invert_y else 0
            mirror_pos.z = mirror_pos.z if settings.unit_invert_z else 0
            mesh.transform(mathutils.Matrix.Translation(-mirror_pos))

        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                (-1 if settings.unit_invert_y else 1),
                                                (-1 if settings.unit_invert_z else 1), 1))
        mesh.transform(sign_matrix)

        if custom_bounds:
            mesh.transform(mathutils.Matrix.Translation(mirror_pos))

        bm = bmesh.new()
        bm.from_mesh(mesh)

        # only reverse face if only doing one or three mirror operations. Mirroring twice will reverse faces twice already, which has no effect
        mirror_operations = (1 if settings.unit_invert_x else 0) + (1 if settings.unit_invert_y else 0) + (1 if settings.unit_invert_z else 0)
        if mirror_operations == 1 or mirror_operations == 3:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(mesh)

    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)

    #bpy.context.window.scene = scene

    return (True, "", obj)

def clear_bake_obj(context: bpy.types.Context, obj: bpy.types.Object) -> bool:
    """
    Destroy the merged object generated by the bake process (and its data), assuming user doesn't want to keep it around

    :param context: Blender current execution context
    :param obj: object to delete
    :return: the function's success
    :rtype: bool
    """
    settings = context.scene.SDFBakerSettings

    if obj and not settings.gen_selection_mesh:
        bpy.data.meshes.remove(obj.data)
        return True
    
    return False

def bake_sdf(context, bake_name: str, obj: bpy.types.Object, tex_width: int, tex_height: int) -> tuple[bool, str, list, tuple[mathutils.Vector, mathutils.Vector]]:
    """
    Generate a BVH tree for the merged object to bake and generate a signed distance field by sampling the nearest surface point for each voxel

    :param context: Blender current execution context
    :param obj: merged object to bake
    :param tex_width: sdf texture's width
    :param tex_height: sdf texture's height
    :return: the function's success, potential error message, list of distances, tuple containing the sdf volume 'zero' and 'one' corners
    :rtype: tuple
    """
    settings = context.scene.SDFBakerSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    BVH = mathutils.bvhtree.BVHTree.FromBMesh(bm)

    if not BVH:
        return (False, "Couldn't create BVH", None, (None, None))

    add_bake_report("tile_sort_mode", settings.tile_sort_mode)
    add_bake_report("unit_invert_v", settings.unit_invert_v)
    add_bake_report("invert_sign", settings.invert_sign)
    add_bake_report("two_sided", settings.two_sided)

    custom_bounds = False
    if settings.sdf_mode == "CUSTOM" and settings.sdf_bounds:
        if settings.sdf_bounds.type == "MESH" or settings.sdf_bounds.type == "EMPTY":
            custom_bounds = True

    if custom_bounds:
        add_bake_report("sdf_mode", "CUSTOM")
        add_bake_report("sdf_bounds", obj)
        bounds_obj = settings.sdf_bounds
        bounds_offset = mathutils.Vector((0.0, 0.0, 0.0))
    else:
        add_bake_report("sdf_mode", "BOUNDS")
        bounds_obj = obj # fallback to merged selection
        bounds_offset = mathutils.Vector(settings.offset) * 2.0

    if custom_bounds:
        center_local = mathutils.Vector((0.0, 0.0, 0.0))

        if bounds_obj.type == "EMPTY":
            uniform_size = bounds_obj.empty_display_size
            bounds_local = mathutils.Vector((uniform_size, uniform_size, uniform_size)) * bounds_obj.matrix_world.to_scale() * 2.0 # derive bounds from empty size
        else: # MESH
            bounds_local = bounds_obj.dimensions
    else:
        center_local = 0.125 * sum((mathutils.Vector(b) for b in bounds_obj.bound_box), mathutils.Vector())
        bounds_local = bounds_obj.dimensions

    center = (bounds_obj.matrix_world @ center_local)
    bounds = (bounds_local) + bounds_offset

    zero_corner = center - (bounds * 0.5)
    one_corner = center + (bounds * 0.5)
    step = mathutils.Vector((bounds.x / settings.x, bounds.y / settings.y, bounds.z / settings.z))

    if settings.gen_debug_mesh:
        samples = []

    max_dist = 0.0
    sdf = [0.0, 0.0, 0.0, 1.0] * (tex_width * tex_height)
    for z in range(settings.z):
        progress_z = z / max(1.0, (settings.z - 1))
        bpy.context.window_manager.progress_update((progress_z * 80) + 10)

        flip_tile_x = settings.tile_sort_mode == "TB_RL" or settings.tile_sort_mode == "BT_RL"
        sdf_index_z_tile_x_offset = (z % settings.frames) * settings.x
        sdf_index_z_tile_x_offset = ((settings.frames - 1) * settings.x) - sdf_index_z_tile_x_offset if flip_tile_x else sdf_index_z_tile_x_offset

        flip_tile_y = settings.tile_sort_mode == "BT_LR" or settings.tile_sort_mode == "BT_RL"
        sdf_index_z_tile_y_offset = math.floor(z / settings.frames) * settings.y * tex_width
        sdf_index_z_tile_y_offset = (math.floor((settings.z - 1) / settings.frames) * settings.y * tex_width) - sdf_index_z_tile_y_offset if flip_tile_y else sdf_index_z_tile_y_offset

        sdf_index_z_offset = (sdf_index_z_tile_x_offset + sdf_index_z_tile_y_offset) * 4

        for y in range(settings.y):
            #progress_y = y / max(1.0, (settings.y - 1))
            sdf_index_y_offset = ((settings.y - 1 - y) if settings.unit_invert_v else y) * tex_width * 4
            for x in range(settings.x):
                #progress_x = x / max(1.0, (settings.x - 1))
                sdf_index_x_offset = x * 4

                sample_pos = zero_corner + (step * mathutils.Vector((x, y, z))) + (step * 0.5)

                if settings.gen_debug_mesh:
                    samples.append(sample_pos)

                nearest_pos, nearest_nor, nearest_index, nearest_dist = BVH.find_nearest(sample_pos)
                if nearest_dist:
                    nearest_dist *= abs(settings.unit_scale)
                    max_dist = max(max_dist, nearest_dist)

                    # tracing any ray from within the geometry will result in a hit, allowing us to figure out if voxel
                    # is inside mesh and thus if distance should be negative to create a signed distance field
                    hit_pos, hit_nor, hit_index, hit_dist = BVH.ray_cast(sample_pos, mathutils.Vector((0.0, 0.0, 1.0)))
                    if not settings.two_sided and hit_dist and hit_nor.dot(mathutils.Vector((0.0, 0.0, 1.0))) > 0.0:
                        nearest_dist *= -1.0

                    if settings.invert_sign:
                        nearest_dist *= -1.0

                    sdf_index = sdf_index_x_offset + sdf_index_y_offset + sdf_index_z_offset
                    sdf[sdf_index] = nearest_dist

                #sdf[sdf_index+0] = progress_x
                #sdf[sdf_index+1] = progress_y
                #sdf[sdf_index+2] = progress_z

    if settings.gen_debug_mesh:
        bake_name = bake_name + ".debug" if bake_name != "" else "BakedMesh.SDF.debug"
        mesh = bpy.data.meshes.new(bake_name)
        mesh.from_pydata(samples, [], [])
        mesh.update()
        
        obj = bpy.data.objects.new(bake_name, mesh)
        bpy.context.scene.collection.objects.link(obj)

    add_bake_report("max_dist", max_dist)

    return (True, "", sdf, max_dist, (zero_corner, one_corner))

def get_remapped_sdf(context: bpy.types.Context, sdf: list, max_dist: float):
    """
    Normalize and or remap the list of distances

    :param context: Blender current execution context
    :param sdf: list of distances
    :param max_dist: maximum absolute distance reported during the bake
    :return: the function's success, potential error message, list of distances
    :rtype: tuple
    """
    settings = context.scene.SDFBakerSettings

    if abs(max_dist) < 0.00001:
        return (False, "Invalid maximum distance", sdf)
    
    if settings.distance_mode == "REAL":
        return (False, "Not asked to normalize or remap", sdf)

    if not sdf or len(sdf) < 4:
        return (False, "Invalid buffer", sdf)

    max_range = max_dist
    min_range = -max_dist if settings.distance_mode == "REMAPPED" else 0.0

    max_voxel = len(sdf) // 4
    for voxel_index in range(max_voxel):
        voxel_index *= 4
        sdf[voxel_index] = (sdf[voxel_index] - min_range) / (max_range - min_range)

    return (True, "", sdf)

def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

    settings = context.scene.SDFBakerSettings
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

    bake_name = get_bake_name(context, active_object)
    add_bake_report("name", bake_name)

    wm.progress_update(3)

    success, msg, tex_width, tex_height = get_best_texture_resolution(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(7)

    success, msg, obj = get_bake_obj(context, objs_to_bake, bake_name)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    wm.progress_update(10)

    ########
    # BAKE #

    success, msg, sdf, max_dist, corners = bake_sdf(context, bake_name, obj, tex_width, tex_height)
    if not success:
        clear_bake_obj(context, obj)
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)

    success, msg, obj_to_export = generate_sdf_mesh_bounds(bake_name, corners, settings.unit_scale)
    if not success:
        clear_bake_obj(context, obj)
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, "ERROR", msg)
    add_bake_report("mesh", obj_to_export)

    if settings.distance_mode != "REAL":
        success, msg, sdf = get_remapped_sdf(context, sdf, max_dist)
    add_bake_report("distance_mode", settings.distance_mode)

    wm.progress_update(90)

    ############
    # TEXTURES #

    success, msg, img_offset = generate_texture(bake_name, settings.tex_file_name, sdf, tex_width, tex_height)
    if not success:
        if obj and not settings.gen_selection_mesh:
            bpy.data.meshes.remove(obj.data)
            bpy.data.objects.remove(obj)
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)
    add_bake_report("tex", img_offset)

    wm.progress_update(92)

    if settings.export_tex and bpy.data.is_saved:
        success, msg, img_path = export_texture(context, img_offset, settings.export_tex_file_path, settings.tex_file_name, bake_name, settings.export_tex_override)
        if not success:
            clear_bake_obj(context, obj)
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("tex_export", True)
        add_bake_report("tex_path", img_path)

    wm.progress_update(94)

    ########
    # MESH #

    if settings.export_mesh and bpy.data.is_saved:
        success, msg, mesh_path = export_mesh_selection(context, bake_name)
        if not success:
            clear_bake_obj(context, obj)
            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        add_bake_report("mesh_export", True)
        add_bake_report("mesh_path", mesh_path)

    wm.progress_update(96)

    #######
    # XML #

    if settings.export_xml and bpy.data.is_saved:
        success, msg, path = export_xml(context)
        add_bake_report("xml", True)
        add_bake_report("xml_path", path)
    
    clear_bake_obj(context, obj)

    add_bake_report("success", True)
    wm.progress_update(99)
    wm.progress_end()

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

##############
### MESHES ###
def generate_sdf_mesh_bounds(bake_name: str, corners: tuple[mathutils.Vector, mathutils.Vector], scale: float) -> tuple[bool, str]:
    """
    Generate a world aligned bounding box mesh matching the sdf bake's overall 'volume'

    :param bake_name: the bake operation's 'name'
    :param corners: tuple containing the 'zero' and 'one' corners
    :param scale: scale to apply to the corners
    :return: the function's success, potential error message, generated object
    :rtype: tuple
    """

    bake_name = bake_name if bake_name != "" else "BakedMesh.SDF"

    zero_corner, one_corner = corners

    add_bake_report("mesh_min_bounds_offset", zero_corner * scale)
    add_bake_report("mesh_max_bounds_offset", one_corner * scale)

    bounds_verts = [
        mathutils.Vector((zero_corner.x, zero_corner.y, zero_corner.z)),
        mathutils.Vector((zero_corner.x, zero_corner.y, one_corner.z)),
        mathutils.Vector((zero_corner.x, one_corner.y, one_corner.z)),
        mathutils.Vector((zero_corner.x, one_corner.y, zero_corner.z)),
        mathutils.Vector((one_corner.x, one_corner.y, one_corner.z)),
        mathutils.Vector((one_corner.x, one_corner.y, zero_corner.z)),
        mathutils.Vector((one_corner.x, zero_corner.y, zero_corner.z)),
        mathutils.Vector((one_corner.x, zero_corner.y, one_corner.z))
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

        #scene = bpy.data.scenes.get("SDFBaker", None)
        #if scene is None:
            #scene = bpy.data.scenes.new("SDFBaker")
        scene = bpy.context.scene
        scene.collection.objects.link(bounds_obj)
    else:
        if bounds_obj.type == "MESH":
            bounds_mesh = bounds_obj.data
            if len(bounds_mesh.vertices) == 8: # does it look like our mesh? update it!
                for bounds_vertex_index, bounds_vertex in enumerate(bounds_mesh.vertices):
                    bounds_vertex.co = bounds_verts[bounds_vertex_index]
            else:
                return (False, "An object named " + bake_name + " already exists but it doesn't look like it's from a previous bake. Unsafe to modify", None)
        else:
            return (False, "An object named " + bake_name + " already exists but isn't a mesh. Can't modify it", None)

    bounds_obj.select_set(True)
    bpy.context.view_layer.objects.active = bounds_obj

    return (True, "", bounds_obj)

def export_mesh_selection(context: bpy.types.Context, bake_name: str):
    """
    Export the current selection to FBX

    :param context: Blender current execution context
    :param bake_name: Bake operation's 'name'
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.SDFBakerSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        # export selection and assume selection was properly handled outside of this function
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

##############
### CURVES ###
def cubic_bezier(p0, p1, p2, p3, t):
    """
    """
    u = 1 - t
    return (
        u**3 * p0 +
        3 * u**2 * t * p1 +
        3 * u * t**2 * p2 +
        t**3 * p3
    )

def get_closest_point_on_curve(curve_obj, target_point, samples=100):
    """
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    eval_curve = eval_obj.data

    closest_point = None
    min_dist = float('inf')

    for spline in eval_curve.splines:
        for segment_index in range(len(spline.bezier_points) // 2):
            points_on_curve = geometry.interpolate_bezier(
                spline.bezier_points[(segment_index * 2)].co,
                spline.bezier_points[(segment_index * 2)].handle_right,
                spline.bezier_points[(segment_index * 2) + 1].handle_left,
                spline.bezier_points[(segment_index * 2) + 1].co,
                samples)

            for point_on_curve in points_on_curve:
                dist = (target_point - point_on_curve).length
                if dist < min_dist:
                    min_dist = dist
                    closest_point = point_on_curve

    return closest_point

################
### GEONODES ###
def generate_geonodes_sdf_3d(context: bpy.types.Context, obj: bpy.types.Object):
    """
    Create a new object with a geometry nodes modifier attached to it (creating the necessary geometry node graph along the way) to generate a SDF using geometry nodes @LEGACY

    :param context: Blender current execution context
    :param obj: object to use as a target for the geometry nodes modifier
    :return: success, message verbose, message
    :rtype: tuple
    """
    settings = context.scene.SDFBakerSettings

    geonodes_mesh = bpy.data.meshes.new("SDFBaker.NODES")
    geonodes_obj = bpy.data.objects.new("SDFBaker.NODES", geonodes_mesh)

    #scene = bpy.data.scenes.get("SDFBaker", None)
    #if scene is None:
        #scene = bpy.data.scenes.new("SDFBaker")
    scene = bpy.context.scene
    scene.collection.objects.link(geonodes_obj)

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "Nodes_SDF_3D":
            geonode_tree = node_group
            break

    if geonode_tree is None:
        geonode_tree = build_geonodes_sdf_3d()

    geonode_mod = geonodes_obj.modifiers.get("GeometryNodes", None)
    if geonode_mod is None:
        geonode_mod = geonodes_obj.modifiers.new(name="GeometryNodes", type='NODES')

    geonode_mod.node_group = geonode_tree

    geonode_mod[geonode_tree.nodes["Group Input"].outputs["X Frames"].identifier] = settings.frames
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["X"].identifier] = settings.x
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Y"].identifier] = settings.y
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Z"].identifier] = settings.z
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Object"].identifier] = obj
    geonode_mod[geonode_tree.nodes["Group Input"].outputs["Bounds Offset"].identifier] = settings.offset

    map = bpy.data.materials.get("SDF", None)
    if map is None:
        mat = bpy.data.materials.new(name = "SDF")
        buid_material_sdf_3d_node_group(mat)

    if geonodes_obj.data.materials:
        geonodes_obj.data.materials[0] = mat
    else:
        geonodes_obj.data.materials.append(mat)

    return (True, "INFO", "")

def build_geonodes_sdf_linearindextounitindex_node_group() -> bpy.types.NodeGroup:
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    sdf_linearindextounitindex = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "SDF_LinearIndexToUnitIndex")

    sdf_linearindextounitindex.color_tag = 'NONE'
    sdf_linearindextounitindex.description = ""
    sdf_linearindextounitindex.default_group_node_width = 140
    


    #sdf_linearindextounitindex interface
    #Socket Index
    index_socket = sdf_linearindextounitindex.interface.new_socket(name = "Index", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    index_socket.default_value = (0.0, 0.0, 0.0)
    index_socket.min_value = -3.4028234663852886e+38
    index_socket.max_value = 3.4028234663852886e+38
    index_socket.subtype = 'NONE'
    index_socket.attribute_domain = 'POINT'
    index_socket.description = "XYZ Voxel Index"

    #Socket UnitIndex
    unitindex_socket = sdf_linearindextounitindex.interface.new_socket(name = "UnitIndex", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    unitindex_socket.default_value = (0.0, 0.0, 0.0)
    unitindex_socket.min_value = -3.4028234663852886e+38
    unitindex_socket.max_value = 3.4028234663852886e+38
    unitindex_socket.subtype = 'NONE'
    unitindex_socket.attribute_domain = 'POINT'
    unitindex_socket.description = "XYZ Voxel Index in [0:1] unit space"

    #Socket Voxels
    voxels_socket = sdf_linearindextounitindex.interface.new_socket(name = "Voxels", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    voxels_socket.default_value = (0.0, 0.0, 0.0)
    voxels_socket.min_value = -3.4028234663852886e+38
    voxels_socket.max_value = 3.4028234663852886e+38
    voxels_socket.subtype = 'NONE'
    voxels_socket.attribute_domain = 'POINT'
    voxels_socket.description = "Amount of voxels in XYZ"

    #Socket VoxelCount
    voxelcount_socket = sdf_linearindextounitindex.interface.new_socket(name = "VoxelCount", in_out='OUTPUT', socket_type = 'NodeSocketFloat')
    voxelcount_socket.default_value = 0.0
    voxelcount_socket.min_value = -3.4028234663852886e+38
    voxelcount_socket.max_value = 3.4028234663852886e+38
    voxelcount_socket.subtype = 'NONE'
    voxelcount_socket.attribute_domain = 'POINT'
    voxelcount_socket.description = "Total amount of voxels"

    #Socket X
    x_socket = sdf_linearindextounitindex.interface.new_socket(name = "X", in_out='INPUT', socket_type = 'NodeSocketInt')
    x_socket.default_value = 0
    x_socket.min_value = -2147483648
    x_socket.max_value = 2147483647
    x_socket.subtype = 'NONE'
    x_socket.attribute_domain = 'POINT'
    x_socket.description = "X resolution"

    #Socket Y
    y_socket = sdf_linearindextounitindex.interface.new_socket(name = "Y", in_out='INPUT', socket_type = 'NodeSocketInt')
    y_socket.default_value = 0
    y_socket.min_value = -2147483648
    y_socket.max_value = 2147483647
    y_socket.subtype = 'NONE'
    y_socket.attribute_domain = 'POINT'
    y_socket.description = "Y resolution"

    #Socket Z
    z_socket = sdf_linearindextounitindex.interface.new_socket(name = "Z", in_out='INPUT', socket_type = 'NodeSocketInt')
    z_socket.default_value = 0
    z_socket.min_value = -2147483648
    z_socket.max_value = 2147483647
    z_socket.subtype = 'NONE'
    z_socket.attribute_domain = 'POINT'
    z_socket.description = "Z resolution"


    #initialize sdf_linearindextounitindex nodes
    #node Group Output
    group_output = sdf_linearindextounitindex.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    #node Group Input
    group_input = sdf_linearindextounitindex.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    #node Math.017
    math_017 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_017.name = "Math.017"
    math_017.operation = 'FLOORED_MODULO'
    math_017.use_clamp = False

    #node Combine XYZ.003
    combine_xyz_003 = sdf_linearindextounitindex.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_003.name = "Combine XYZ.003"

    #node Math.026
    math_026 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_026.name = "Math.026"
    math_026.operation = 'DIVIDE'
    math_026.use_clamp = False

    #node Math.027
    math_027 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_027.name = "Math.027"
    math_027.operation = 'FLOOR'
    math_027.use_clamp = False

    #node Math.028
    math_028 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_028.name = "Math.028"
    math_028.operation = 'FLOORED_MODULO'
    math_028.use_clamp = False

    #node Vector Math.012
    vector_math_012 = sdf_linearindextounitindex.nodes.new("ShaderNodeVectorMath")
    vector_math_012.name = "Vector Math.012"
    vector_math_012.operation = 'DIVIDE'

    #node Combine XYZ.004
    combine_xyz_004 = sdf_linearindextounitindex.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_004.name = "Combine XYZ.004"

    #node Math.029
    math_029 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_029.name = "Math.029"
    math_029.operation = 'MULTIPLY'
    math_029.use_clamp = False

    #node Index
    index = sdf_linearindextounitindex.nodes.new("GeometryNodeInputIndex")
    index.name = "Index"

    #node Reroute.001
    reroute_001 = sdf_linearindextounitindex.nodes.new("NodeReroute")
    reroute_001.name = "Reroute.001"
    reroute_001.socket_idname = "NodeSocketInt"
    #node Reroute.003
    reroute_003 = sdf_linearindextounitindex.nodes.new("NodeReroute")
    reroute_003.name = "Reroute.003"
    reroute_003.socket_idname = "NodeSocketVector"
    #node Math.009
    math_009 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_009.name = "Math.009"
    math_009.operation = 'MULTIPLY'
    math_009.use_clamp = False

    #node Math.010
    math_010 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_010.name = "Math.010"
    math_010.operation = 'MULTIPLY'
    math_010.use_clamp = False

    #node Reroute.004
    reroute_004 = sdf_linearindextounitindex.nodes.new("NodeReroute")
    reroute_004.name = "Reroute.004"
    reroute_004.socket_idname = "NodeSocketInt"
    #node Reroute.005
    reroute_005 = sdf_linearindextounitindex.nodes.new("NodeReroute")
    reroute_005.name = "Reroute.005"
    reroute_005.socket_idname = "NodeSocketInt"
    #node Reroute.006
    reroute_006 = sdf_linearindextounitindex.nodes.new("NodeReroute")
    reroute_006.name = "Reroute.006"
    reroute_006.socket_idname = "NodeSocketInt"
    #node Reroute.007
    reroute_007 = sdf_linearindextounitindex.nodes.new("NodeReroute")
    reroute_007.name = "Reroute.007"
    reroute_007.socket_idname = "NodeSocketInt"
    #node Frame
    frame = sdf_linearindextounitindex.nodes.new("NodeFrame")
    frame.label = "voxel count (XYZ & Total)"
    frame.name = "Frame"
    frame.label_size = 20
    frame.shrink = True

    #node Frame.001
    frame_001 = sdf_linearindextounitindex.nodes.new("NodeFrame")
    frame_001.label = "convert linear index to XYZ Index"
    frame_001.name = "Frame.001"
    frame_001.label_size = 20
    frame_001.shrink = True

    #node Math
    math = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math.name = "Math"
    math.operation = 'FLOORED_MODULO'
    math.use_clamp = False

    #node Math.001
    math_001 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_001.name = "Math.001"
    math_001.operation = 'DIVIDE'
    math_001.use_clamp = False

    #node Math.002
    math_002 = sdf_linearindextounitindex.nodes.new("ShaderNodeMath")
    math_002.name = "Math.002"
    math_002.operation = 'FLOOR'
    math_002.use_clamp = False




    #Set parents
    math_017.parent = frame_001
    combine_xyz_003.parent = frame_001
    math_026.parent = frame_001
    math_027.parent = frame_001
    math_028.parent = frame_001
    combine_xyz_004.parent = frame
    math_029.parent = frame_001
    index.parent = frame_001
    reroute_003.parent = frame
    math_009.parent = frame
    math_010.parent = frame
    reroute_007.parent = frame
    math.parent = frame_001
    math_001.parent = frame_001
    math_002.parent = frame_001

    #Set locations
    group_output.location = (642.9230346679688, 147.84527587890625)
    group_input.location = (-639.4849853515625, -233.99684143066406)
    math_017.location = (83.93328857421875, 267.2830810546875)
    combine_xyz_003.location = (254.6279296875, 146.80198669433594)
    math_026.location = (-238.690185546875, -58.8555908203125)
    math_027.location = (-79.803955078125, -58.76080322265625)
    math_028.location = (84.980712890625, 101.4500732421875)
    vector_math_012.location = (463.6160583496094, 89.04966735839844)
    combine_xyz_004.location = (247.88522338867188, -170.18246459960938)
    math_029.location = (-432.3706970214844, -51.88743591308594)
    index.location = (-431.6681213378906, 26.34064483642578)
    reroute_001.location = (-323.18060302734375, -292.4911804199219)
    reroute_003.location = (568.024169921875, -204.34884643554688)
    math_009.location = (246.67437744140625, -300.2756652832031)
    math_010.location = (418.43804931640625, -340.6806640625)
    reroute_004.location = (19.769548416137695, -313.3082275390625)
    reroute_005.location = (22.835954666137695, -269.43597412109375)
    reroute_006.location = (21.813859939575195, -291.3077697753906)
    reroute_007.location = (249.03323364257812, -471.3094482421875)
    frame.location = (9.299346923828125, -137.5657958984375)
    frame_001.location = (0.0, 0.0)
    math.location = (88.29673767089844, -55.58885955810547)
    math_001.location = (-237.75823974609375, 263.1468811035156)
    math_002.location = (-78.8228988647461, 263.1469421386719)

    #Set dimensions
    group_output.width, group_output.height = 140.0, 100.0
    group_input.width, group_input.height = 140.0, 100.0
    math_017.width, math_017.height = 140.0, 100.0
    combine_xyz_003.width, combine_xyz_003.height = 140.0, 100.0
    math_026.width, math_026.height = 140.0, 100.0
    math_027.width, math_027.height = 140.0, 100.0
    math_028.width, math_028.height = 140.0, 100.0
    vector_math_012.width, vector_math_012.height = 140.0, 100.0
    combine_xyz_004.width, combine_xyz_004.height = 140.0, 100.0
    math_029.width, math_029.height = 140.0, 100.0
    index.width, index.height = 140.0, 100.0
    reroute_001.width, reroute_001.height = 16.0, 100.0
    reroute_003.width, reroute_003.height = 16.0, 100.0
    math_009.width, math_009.height = 140.0, 100.0
    math_010.width, math_010.height = 140.0, 100.0
    reroute_004.width, reroute_004.height = 16.0, 100.0
    reroute_005.width, reroute_005.height = 16.0, 100.0
    reroute_006.width, reroute_006.height = 16.0, 100.0
    reroute_007.width, reroute_007.height = 16.0, 100.0
    frame.width, frame.height = 394.9909362792969, 388.0
    frame_001.width, frame_001.height = 887.0, 544.0
    math.width, math.height = 140.0, 100.0
    math_001.width, math_001.height = 140.0, 100.0
    math_002.width, math_002.height = 140.0, 100.0

    #initialize sdf_linearindextounitindex links
    #math_029.Value -> math_026.Value
    sdf_linearindextounitindex.links.new(math_029.outputs[0], math_026.inputs[1])
    #math_028.Value -> combine_xyz_003.Y
    sdf_linearindextounitindex.links.new(math_028.outputs[0], combine_xyz_003.inputs[1])
    #math_026.Value -> math_027.Value
    sdf_linearindextounitindex.links.new(math_026.outputs[0], math_027.inputs[0])
    #combine_xyz_004.Vector -> vector_math_012.Vector
    sdf_linearindextounitindex.links.new(combine_xyz_004.outputs[0], vector_math_012.inputs[1])
    #combine_xyz_003.Vector -> vector_math_012.Vector
    sdf_linearindextounitindex.links.new(combine_xyz_003.outputs[0], vector_math_012.inputs[0])
    #reroute_005.Output -> combine_xyz_004.X
    sdf_linearindextounitindex.links.new(reroute_005.outputs[0], combine_xyz_004.inputs[0])
    #reroute_006.Output -> combine_xyz_004.Y
    sdf_linearindextounitindex.links.new(reroute_006.outputs[0], combine_xyz_004.inputs[1])
    #reroute_004.Output -> combine_xyz_004.Z
    sdf_linearindextounitindex.links.new(reroute_004.outputs[0], combine_xyz_004.inputs[2])
    #group_input.X -> math_029.Value
    sdf_linearindextounitindex.links.new(group_input.outputs[0], math_029.inputs[0])
    #group_input.Y -> math_029.Value
    sdf_linearindextounitindex.links.new(group_input.outputs[1], math_029.inputs[1])
    #index.Index -> math_026.Value
    sdf_linearindextounitindex.links.new(index.outputs[0], math_026.inputs[0])
    #group_input.Y -> reroute_001.Input
    sdf_linearindextounitindex.links.new(group_input.outputs[1], reroute_001.inputs[0])
    #vector_math_012.Vector -> group_output.UnitIndex
    sdf_linearindextounitindex.links.new(vector_math_012.outputs[0], group_output.inputs[1])
    #combine_xyz_003.Vector -> group_output.Index
    sdf_linearindextounitindex.links.new(combine_xyz_003.outputs[0], group_output.inputs[0])
    #reroute_003.Output -> group_output.Voxels
    sdf_linearindextounitindex.links.new(reroute_003.outputs[0], group_output.inputs[2])
    #combine_xyz_004.Vector -> reroute_003.Input
    sdf_linearindextounitindex.links.new(combine_xyz_004.outputs[0], reroute_003.inputs[0])
    #math_009.Value -> math_010.Value
    sdf_linearindextounitindex.links.new(math_009.outputs[0], math_010.inputs[0])
    #group_input.Z -> reroute_004.Input
    sdf_linearindextounitindex.links.new(group_input.outputs[2], reroute_004.inputs[0])
    #reroute_005.Output -> math_009.Value
    sdf_linearindextounitindex.links.new(reroute_005.outputs[0], math_009.inputs[0])
    #reroute_006.Output -> math_009.Value
    sdf_linearindextounitindex.links.new(reroute_006.outputs[0], math_009.inputs[1])
    #reroute_007.Output -> math_010.Value
    sdf_linearindextounitindex.links.new(reroute_007.outputs[0], math_010.inputs[1])
    #reroute_004.Output -> reroute_007.Input
    sdf_linearindextounitindex.links.new(reroute_004.outputs[0], reroute_007.inputs[0])
    #math_010.Value -> group_output.VoxelCount
    sdf_linearindextounitindex.links.new(math_010.outputs[0], group_output.inputs[3])
    #math_027.Value -> math.Value
    sdf_linearindextounitindex.links.new(math_027.outputs[0], math.inputs[0])
    #math.Value -> combine_xyz_003.Z
    sdf_linearindextounitindex.links.new(math.outputs[0], combine_xyz_003.inputs[2])
    #reroute_004.Output -> math.Value
    sdf_linearindextounitindex.links.new(reroute_004.outputs[0], math.inputs[1])
    #reroute_006.Output -> math_028.Value
    sdf_linearindextounitindex.links.new(reroute_006.outputs[0], math_028.inputs[1])
    #reroute_001.Output -> reroute_006.Input
    sdf_linearindextounitindex.links.new(reroute_001.outputs[0], reroute_006.inputs[0])
    #index.Index -> math_001.Value
    sdf_linearindextounitindex.links.new(index.outputs[0], math_001.inputs[0])
    #reroute_001.Output -> math_001.Value
    sdf_linearindextounitindex.links.new(reroute_001.outputs[0], math_001.inputs[1])
    #math_001.Value -> math_002.Value
    sdf_linearindextounitindex.links.new(math_001.outputs[0], math_002.inputs[0])
    #math_002.Value -> math_017.Value
    sdf_linearindextounitindex.links.new(math_002.outputs[0], math_017.inputs[0])
    #reroute_005.Output -> math_017.Value
    sdf_linearindextounitindex.links.new(reroute_005.outputs[0], math_017.inputs[1])
    #index.Index -> math_028.Value
    sdf_linearindextounitindex.links.new(index.outputs[0], math_028.inputs[0])
    #math_017.Value -> combine_xyz_003.X
    sdf_linearindextounitindex.links.new(math_017.outputs[0], combine_xyz_003.inputs[0])
    #group_input.X -> reroute_005.Input
    sdf_linearindextounitindex.links.new(group_input.outputs[0], reroute_005.inputs[0])
    return sdf_linearindextounitindex

def build_geonodes_sdf_getvoxeldata_node_group() -> bpy.types.NodeGroup:
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    sdf_getvoxeldata = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "SDF_GetVoxelData")

    sdf_getvoxeldata.color_tag = 'NONE'
    sdf_getvoxeldata.description = ""
    sdf_getvoxeldata.default_group_node_width = 140
    


    #sdf_getvoxeldata interface
    #Socket Voxel Position
    voxel_position_socket = sdf_getvoxeldata.interface.new_socket(name = "Voxel Position", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    voxel_position_socket.default_value = (0.0, 0.0, 0.0)
    voxel_position_socket.min_value = -3.4028234663852886e+38
    voxel_position_socket.max_value = 3.4028234663852886e+38
    voxel_position_socket.subtype = 'NONE'
    voxel_position_socket.attribute_domain = 'POINT'

    #Socket Voxel Offset
    voxel_offset_socket = sdf_getvoxeldata.interface.new_socket(name = "Voxel Offset", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    voxel_offset_socket.default_value = (0.0, 0.0, 0.0)
    voxel_offset_socket.min_value = -3.4028234663852886e+38
    voxel_offset_socket.max_value = 3.4028234663852886e+38
    voxel_offset_socket.subtype = 'NONE'
    voxel_offset_socket.attribute_domain = 'POINT'

    #Socket Voxel Size
    voxel_size_socket = sdf_getvoxeldata.interface.new_socket(name = "Voxel Size", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    voxel_size_socket.default_value = (0.0, 0.0, 0.0)
    voxel_size_socket.min_value = -3.4028234663852886e+38
    voxel_size_socket.max_value = 3.4028234663852886e+38
    voxel_size_socket.subtype = 'NONE'
    voxel_size_socket.attribute_domain = 'POINT'

    #Socket Bounds Min
    bounds_min_socket = sdf_getvoxeldata.interface.new_socket(name = "Bounds Min", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    bounds_min_socket.default_value = (0.0, 0.0, 0.0)
    bounds_min_socket.min_value = -3.4028234663852886e+38
    bounds_min_socket.max_value = 3.4028234663852886e+38
    bounds_min_socket.subtype = 'NONE'
    bounds_min_socket.attribute_domain = 'POINT'

    #Socket Bounds Max
    bounds_max_socket = sdf_getvoxeldata.interface.new_socket(name = "Bounds Max", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    bounds_max_socket.default_value = (0.0, 0.0, 0.0)
    bounds_max_socket.min_value = -3.4028234663852886e+38
    bounds_max_socket.max_value = 3.4028234663852886e+38
    bounds_max_socket.subtype = 'NONE'
    bounds_max_socket.attribute_domain = 'POINT'

    #Socket Bounds Extent
    bounds_extent_socket = sdf_getvoxeldata.interface.new_socket(name = "Bounds Extent", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    bounds_extent_socket.default_value = (0.0, 0.0, 0.0)
    bounds_extent_socket.min_value = -3.4028234663852886e+38
    bounds_extent_socket.max_value = 3.4028234663852886e+38
    bounds_extent_socket.subtype = 'NONE'
    bounds_extent_socket.attribute_domain = 'POINT'

    #Socket Geometry
    geometry_socket = sdf_getvoxeldata.interface.new_socket(name = "Geometry", in_out='INPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'

    #Socket UnitIndex
    unitindex_socket_1 = sdf_getvoxeldata.interface.new_socket(name = "UnitIndex", in_out='INPUT', socket_type = 'NodeSocketVector')
    unitindex_socket_1.default_value = (0.0, 0.0, 0.0)
    unitindex_socket_1.min_value = -10000.0
    unitindex_socket_1.max_value = 10000.0
    unitindex_socket_1.subtype = 'NONE'
    unitindex_socket_1.attribute_domain = 'POINT'
    unitindex_socket_1.description = "XYZ Voxel Index in [0:1] unit space"

    #Socket Voxels
    voxels_socket_1 = sdf_getvoxeldata.interface.new_socket(name = "Voxels", in_out='INPUT', socket_type = 'NodeSocketVector')
    voxels_socket_1.default_value = (0.0, 0.0, 0.0)
    voxels_socket_1.min_value = -3.4028234663852886e+38
    voxels_socket_1.max_value = 3.4028234663852886e+38
    voxels_socket_1.subtype = 'NONE'
    voxels_socket_1.attribute_domain = 'POINT'
    voxels_socket_1.description = "Amount of voxels in XYZ"

    #Socket Bounds Offset
    bounds_offset_socket = sdf_getvoxeldata.interface.new_socket(name = "Bounds Offset", in_out='INPUT', socket_type = 'NodeSocketVector')
    bounds_offset_socket.default_value = (0.0, 0.0, 0.0)
    bounds_offset_socket.min_value = -3.4028234663852886e+38
    bounds_offset_socket.max_value = 3.4028234663852886e+38
    bounds_offset_socket.subtype = 'NONE'
    bounds_offset_socket.attribute_domain = 'POINT'
    bounds_offset_socket.description = "How much bounds are extended (user-controlled)"


    #initialize sdf_getvoxeldata nodes
    #node Group Output
    group_output_1 = sdf_getvoxeldata.nodes.new("NodeGroupOutput")
    group_output_1.name = "Group Output"
    group_output_1.is_active_output = True

    #node Group Input
    group_input_1 = sdf_getvoxeldata.nodes.new("NodeGroupInput")
    group_input_1.name = "Group Input"

    #node Bounding Box.002
    bounding_box_002 = sdf_getvoxeldata.nodes.new("GeometryNodeBoundBox")
    bounding_box_002.name = "Bounding Box.002"

    #node Vector Math.014
    vector_math_014 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_014.name = "Vector Math.014"
    vector_math_014.operation = 'ADD'

    #node Vector Math.015
    vector_math_015 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_015.name = "Vector Math.015"
    vector_math_015.operation = 'MULTIPLY'

    #node Vector Math.016
    vector_math_016 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_016.label = "Box Size"
    vector_math_016.name = "Vector Math.016"
    vector_math_016.operation = 'SUBTRACT'

    #node Vector Math.017
    vector_math_017 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_017.name = "Vector Math.017"
    vector_math_017.operation = 'DIVIDE'

    #node Vector Math.018
    vector_math_018 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_018.name = "Vector Math.018"
    vector_math_018.operation = 'DIVIDE'

    #node Vector Math.019
    vector_math_019 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_019.name = "Vector Math.019"
    vector_math_019.operation = 'MULTIPLY'
    #Vector_001
    vector_math_019.inputs[1].default_value = (2.0, 2.0, 2.0)

    #node Reroute.009
    reroute_009 = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute_009.name = "Reroute.009"
    reroute_009.socket_idname = "NodeSocketVector"
    #node Vector Math.020
    vector_math_020 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_020.label = "Box Min"
    vector_math_020.name = "Vector Math.020"
    vector_math_020.operation = 'SUBTRACT'

    #node Vector Math.021
    vector_math_021 = sdf_getvoxeldata.nodes.new("ShaderNodeVectorMath")
    vector_math_021.label = "Box Max"
    vector_math_021.name = "Vector Math.021"
    vector_math_021.operation = 'ADD'

    #node Reroute.028
    reroute_028 = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute_028.name = "Reroute.028"
    reroute_028.socket_idname = "NodeSocketVector"
    #node Reroute.034
    reroute_034 = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute_034.name = "Reroute.034"
    reroute_034.socket_idname = "NodeSocketVector"
    #node Reroute
    reroute = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute.name = "Reroute"
    reroute.socket_idname = "NodeSocketVector"
    #node Frame
    frame_1 = sdf_getvoxeldata.nodes.new("NodeFrame")
    frame_1.label = "voxel position"
    frame_1.name = "Frame"
    frame_1.label_size = 20
    frame_1.shrink = True

    #node Frame.001
    frame_001_1 = sdf_getvoxeldata.nodes.new("NodeFrame")
    frame_001_1.label = "voxel size"
    frame_001_1.name = "Frame.001"
    frame_001_1.label_size = 20
    frame_001_1.shrink = True

    #node Frame.002
    frame_002 = sdf_getvoxeldata.nodes.new("NodeFrame")
    frame_002.label = "voxel half unit offset"
    frame_002.name = "Frame.002"
    frame_002.label_size = 20
    frame_002.shrink = True

    #node Reroute.002
    reroute_002 = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute_002.name = "Reroute.002"
    reroute_002.socket_idname = "NodeSocketVector"
    #node Reroute.004
    reroute_004_1 = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute_004_1.name = "Reroute.004"
    reroute_004_1.socket_idname = "NodeSocketVector"
    #node Frame.003
    frame_003 = sdf_getvoxeldata.nodes.new("NodeFrame")
    frame_003.label = "expand bounding box if desired"
    frame_003.name = "Frame.003"
    frame_003.label_size = 20
    frame_003.shrink = True

    #node Reroute.005
    reroute_005_1 = sdf_getvoxeldata.nodes.new("NodeReroute")
    reroute_005_1.name = "Reroute.005"
    reroute_005_1.socket_idname = "NodeSocketVector"



    #Set parents
    bounding_box_002.parent = frame_003
    vector_math_014.parent = frame_1
    vector_math_015.parent = frame_1
    vector_math_016.parent = frame_003
    vector_math_017.parent = frame_001_1
    vector_math_018.parent = frame_002
    vector_math_019.parent = frame_002
    vector_math_020.parent = frame_003
    vector_math_021.parent = frame_003
    reroute_002.parent = frame_003

    #Set locations
    group_output_1.location = (532.5283203125, 21.964950561523438)
    group_input_1.location = (-730.1163940429688, -38.641239166259766)
    bounding_box_002.location = (-210.5875244140625, -30.791969299316406)
    vector_math_014.location = (268.38348388671875, 312.94683837890625)
    vector_math_015.location = (101.12797546386719, 309.2855224609375)
    vector_math_016.location = (145.31021118164062, -146.425537109375)
    vector_math_017.location = (99.88054656982422, -71.27569580078125)
    vector_math_018.location = (419.88983154296875, -313.7822265625)
    vector_math_019.location = (250.41970825195312, -418.44732666015625)
    reroute_009.location = (-56.14452362060547, -277.22784423828125)
    vector_math_020.location = (-41.695526123046875, 15.31451416015625)
    vector_math_021.location = (-40.14825439453125, -124.07410430908203)
    reroute_028.location = (-387.2210693359375, -140.1140594482422)
    reroute_034.location = (-504.29205322265625, -275.22479248046875)
    reroute.location = (-500.96221923828125, 149.61451721191406)
    frame_1.location = (34.282562255859375, -75.95541381835938)
    frame_001_1.location = (41.440940856933594, 49.79426956176758)
    frame_002.location = (-230.9459228515625, -6.404449462890625)
    reroute_002.location = (152.36843872070312, -135.56903076171875)
    reroute_004_1.location = (267.99578857421875, 43.53580093383789)
    frame_003.location = (-310.88800048828125, 60.21763610839844)
    reroute_005_1.location = (83.3830337524414, -120.92294311523438)

    #Set dimensions
    group_output_1.width, group_output_1.height = 140.0, 100.0
    group_input_1.width, group_input_1.height = 140.0, 100.0
    bounding_box_002.width, bounding_box_002.height = 140.0, 100.0
    vector_math_014.width, vector_math_014.height = 140.0, 100.0
    vector_math_015.width, vector_math_015.height = 140.0, 100.0
    vector_math_016.width, vector_math_016.height = 140.0, 100.0
    vector_math_017.width, vector_math_017.height = 140.0, 100.0
    vector_math_018.width, vector_math_018.height = 140.0, 100.0
    vector_math_019.width, vector_math_019.height = 140.0, 100.0
    reroute_009.width, reroute_009.height = 16.0, 100.0
    vector_math_020.width, vector_math_020.height = 140.0, 100.0
    vector_math_021.width, vector_math_021.height = 140.0, 100.0
    reroute_028.width, reroute_028.height = 16.0, 100.0
    reroute_034.width, reroute_034.height = 16.0, 100.0
    reroute.width, reroute.height = 16.0, 100.0
    frame_1.width, frame_1.height = 368.0, 199.0
    frame_001_1.width, frame_001_1.height = 200.0, 195.0
    frame_002.width, frame_002.height = 370.0, 360.0000305175781
    reroute_002.width, reroute_002.height = 16.0, 100.0
    reroute_004_1.width, reroute_004_1.height = 16.0, 100.0
    frame_003.width, frame_003.height = 555.0, 357.0
    reroute_005_1.width, reroute_005_1.height = 16.0, 100.0

    #initialize sdf_getvoxeldata links
    #bounding_box_002.Min -> vector_math_020.Vector
    sdf_getvoxeldata.links.new(bounding_box_002.outputs[1], vector_math_020.inputs[0])
    #vector_math_015.Vector -> vector_math_014.Vector
    sdf_getvoxeldata.links.new(vector_math_015.outputs[0], vector_math_014.inputs[0])
    #reroute_028.Output -> vector_math_020.Vector
    sdf_getvoxeldata.links.new(reroute_028.outputs[0], vector_math_020.inputs[1])
    #vector_math_021.Vector -> vector_math_016.Vector
    sdf_getvoxeldata.links.new(vector_math_021.outputs[0], vector_math_016.inputs[0])
    #reroute_009.Output -> vector_math_019.Vector
    sdf_getvoxeldata.links.new(reroute_009.outputs[0], vector_math_019.inputs[0])
    #reroute_028.Output -> vector_math_021.Vector
    sdf_getvoxeldata.links.new(reroute_028.outputs[0], vector_math_021.inputs[1])
    #vector_math_019.Vector -> vector_math_018.Vector
    sdf_getvoxeldata.links.new(vector_math_019.outputs[0], vector_math_018.inputs[1])
    #reroute_034.Output -> reroute_009.Input
    sdf_getvoxeldata.links.new(reroute_034.outputs[0], reroute_009.inputs[0])
    #bounding_box_002.Max -> vector_math_021.Vector
    sdf_getvoxeldata.links.new(bounding_box_002.outputs[2], vector_math_021.inputs[0])
    #group_input_1.Geometry -> bounding_box_002.Geometry
    sdf_getvoxeldata.links.new(group_input_1.outputs[0], bounding_box_002.inputs[0])
    #reroute.Output -> vector_math_015.Vector
    sdf_getvoxeldata.links.new(reroute.outputs[0], vector_math_015.inputs[0])
    #group_input_1.UnitIndex -> reroute.Input
    sdf_getvoxeldata.links.new(group_input_1.outputs[1], reroute.inputs[0])
    #group_input_1.Bounds Offset -> reroute_028.Input
    sdf_getvoxeldata.links.new(group_input_1.outputs[3], reroute_028.inputs[0])
    #group_input_1.Voxels -> reroute_034.Input
    sdf_getvoxeldata.links.new(group_input_1.outputs[2], reroute_034.inputs[0])
    #vector_math_014.Vector -> group_output_1.Voxel Position
    sdf_getvoxeldata.links.new(vector_math_014.outputs[0], group_output_1.inputs[0])
    #vector_math_018.Vector -> group_output_1.Voxel Offset
    sdf_getvoxeldata.links.new(vector_math_018.outputs[0], group_output_1.inputs[1])
    #reroute_004_1.Output -> vector_math_014.Vector
    sdf_getvoxeldata.links.new(reroute_004_1.outputs[0], vector_math_014.inputs[1])
    #reroute_009.Output -> vector_math_017.Vector
    sdf_getvoxeldata.links.new(reroute_009.outputs[0], vector_math_017.inputs[1])
    #reroute_002.Output -> group_output_1.Bounds Min
    sdf_getvoxeldata.links.new(reroute_002.outputs[0], group_output_1.inputs[3])
    #vector_math_021.Vector -> group_output_1.Bounds Max
    sdf_getvoxeldata.links.new(vector_math_021.outputs[0], group_output_1.inputs[4])
    #reroute_005_1.Output -> group_output_1.Bounds Extent
    sdf_getvoxeldata.links.new(reroute_005_1.outputs[0], group_output_1.inputs[5])
    #vector_math_020.Vector -> reroute_002.Input
    sdf_getvoxeldata.links.new(vector_math_020.outputs[0], reroute_002.inputs[0])
    #vector_math_020.Vector -> reroute_004_1.Input
    sdf_getvoxeldata.links.new(vector_math_020.outputs[0], reroute_004_1.inputs[0])
    #vector_math_020.Vector -> vector_math_016.Vector
    sdf_getvoxeldata.links.new(vector_math_020.outputs[0], vector_math_016.inputs[1])
    #vector_math_016.Vector -> reroute_005_1.Input
    sdf_getvoxeldata.links.new(vector_math_016.outputs[0], reroute_005_1.inputs[0])
    #reroute_005_1.Output -> vector_math_017.Vector
    sdf_getvoxeldata.links.new(reroute_005_1.outputs[0], vector_math_017.inputs[0])
    #reroute_005_1.Output -> vector_math_015.Vector
    sdf_getvoxeldata.links.new(reroute_005_1.outputs[0], vector_math_015.inputs[1])
    #reroute_005_1.Output -> vector_math_018.Vector
    sdf_getvoxeldata.links.new(reroute_005_1.outputs[0], vector_math_018.inputs[0])
    #vector_math_017.Vector -> group_output_1.Voxel Size
    sdf_getvoxeldata.links.new(vector_math_017.outputs[0], group_output_1.inputs[2])
    return sdf_getvoxeldata

def build_geonodes_sdf_indextounit2dposition_node_group() -> bpy.types.NodeGroup:
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    sdf_indextounit2dposition = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "SDF_IndexToUnit2DPosition")

    sdf_indextounit2dposition.color_tag = 'NONE'
    sdf_indextounit2dposition.description = ""
    sdf_indextounit2dposition.default_group_node_width = 140
    


    #sdf_indextounit2dposition interface
    #Socket Unit 2D Position
    unit_2d_position_socket = sdf_indextounit2dposition.interface.new_socket(name = "Unit 2D Position", in_out='OUTPUT', socket_type = 'NodeSocketVector')
    unit_2d_position_socket.default_value = (0.0, 0.0, 0.0)
    unit_2d_position_socket.min_value = -3.4028234663852886e+38
    unit_2d_position_socket.max_value = 3.4028234663852886e+38
    unit_2d_position_socket.subtype = 'NONE'
    unit_2d_position_socket.attribute_domain = 'POINT'

    #Socket X Frames
    x_frames_socket = sdf_indextounit2dposition.interface.new_socket(name = "X Frames", in_out='INPUT', socket_type = 'NodeSocketFloat')
    x_frames_socket.default_value = 0.0
    x_frames_socket.min_value = -3.4028234663852886e+38
    x_frames_socket.max_value = 3.4028234663852886e+38
    x_frames_socket.subtype = 'NONE'
    x_frames_socket.attribute_domain = 'POINT'

    #Socket Index
    index_socket_1 = sdf_indextounit2dposition.interface.new_socket(name = "Index", in_out='INPUT', socket_type = 'NodeSocketVector')
    index_socket_1.default_value = (0.0, 0.0, 0.0)
    index_socket_1.min_value = -10000.0
    index_socket_1.max_value = 10000.0
    index_socket_1.subtype = 'NONE'
    index_socket_1.attribute_domain = 'POINT'

    #Socket Unit Index
    unit_index_socket = sdf_indextounit2dposition.interface.new_socket(name = "Unit Index", in_out='INPUT', socket_type = 'NodeSocketVector')
    unit_index_socket.default_value = (0.0, 0.0, 0.0)
    unit_index_socket.min_value = -10000.0
    unit_index_socket.max_value = 10000.0
    unit_index_socket.subtype = 'NONE'
    unit_index_socket.attribute_domain = 'POINT'


    #initialize sdf_indextounit2dposition nodes
    #node Group Output
    group_output_2 = sdf_indextounit2dposition.nodes.new("NodeGroupOutput")
    group_output_2.name = "Group Output"
    group_output_2.is_active_output = True

    #node Group Input
    group_input_2 = sdf_indextounit2dposition.nodes.new("NodeGroupInput")
    group_input_2.name = "Group Input"

    #node Math.017
    math_017_1 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_017_1.name = "Math.017"
    math_017_1.operation = 'ADD'
    math_017_1.use_clamp = False

    #node Math.018
    math_018 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_018.name = "Math.018"
    math_018.operation = 'ADD'
    math_018.use_clamp = False

    #node Math.024
    math_024 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_024.name = "Math.024"
    math_024.operation = 'FLOORED_MODULO'
    math_024.use_clamp = False

    #node Math.025
    math_025 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_025.name = "Math.025"
    math_025.operation = 'DIVIDE'
    math_025.use_clamp = False

    #node Math.026
    math_026_1 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_026_1.name = "Math.026"
    math_026_1.operation = 'FLOOR'
    math_026_1.use_clamp = False

    #node Reroute.034
    reroute_034_1 = sdf_indextounit2dposition.nodes.new("NodeReroute")
    reroute_034_1.name = "Reroute.034"
    reroute_034_1.socket_idname = "NodeSocketFloat"
    #node Separate XYZ.004
    separate_xyz_004 = sdf_indextounit2dposition.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz_004.name = "Separate XYZ.004"

    #node Separate XYZ.001
    separate_xyz_001 = sdf_indextounit2dposition.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz_001.name = "Separate XYZ.001"

    #node Reroute.008
    reroute_008 = sdf_indextounit2dposition.nodes.new("NodeReroute")
    reroute_008.name = "Reroute.008"
    reroute_008.socket_idname = "NodeSocketFloat"
    #node Vector Math.014
    vector_math_014_1 = sdf_indextounit2dposition.nodes.new("ShaderNodeVectorMath")
    vector_math_014_1.name = "Vector Math.014"
    vector_math_014_1.operation = 'DIVIDE'

    #node Separate XYZ
    separate_xyz = sdf_indextounit2dposition.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.name = "Separate XYZ"

    #node Math.001
    math_001_1 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_001_1.name = "Math.001"
    math_001_1.operation = 'SUBTRACT'
    math_001_1.use_clamp = False
    #Value
    math_001_1.inputs[0].default_value = 1.0

    #node Combine XYZ
    combine_xyz = sdf_indextounit2dposition.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.name = "Combine XYZ"

    #node Frame
    frame_2 = sdf_indextounit2dposition.nodes.new("NodeFrame")
    frame_2.label = "flip x axis for UE"
    frame_2.name = "Frame"
    frame_2.label_size = 20
    frame_2.shrink = True

    #node Frame.001
    frame_001_2 = sdf_indextounit2dposition.nodes.new("NodeFrame")
    frame_001_2.label = "distribute Z slices in X & Y"
    frame_001_2.name = "Frame.001"
    frame_001_2.label_size = 20
    frame_001_2.shrink = True

    #node Combine XYZ.004
    combine_xyz_004_1 = sdf_indextounit2dposition.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_004_1.name = "Combine XYZ.004"
    #Z
    combine_xyz_004_1.inputs[2].default_value = 0.0

    #node Reroute
    reroute_1 = sdf_indextounit2dposition.nodes.new("NodeReroute")
    reroute_1.name = "Reroute"
    reroute_1.socket_idname = "NodeSocketVector"
    #node Reroute.001
    reroute_001_1 = sdf_indextounit2dposition.nodes.new("NodeReroute")
    reroute_001_1.name = "Reroute.001"
    reroute_001_1.socket_idname = "NodeSocketVector"
    #node Frame.002
    frame_002_1 = sdf_indextounit2dposition.nodes.new("NodeFrame")
    frame_002_1.label = " "
    frame_002_1.name = "Frame.002"
    frame_002_1.label_size = 20
    frame_002_1.shrink = True

    #node Math.005
    math_005 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_005.name = "Math.005"
    math_005.operation = 'MULTIPLY'
    math_005.use_clamp = False
    #Value_001
    math_005.inputs[1].default_value = 1.0

    #node Math.006
    math_006 = sdf_indextounit2dposition.nodes.new("ShaderNodeMath")
    math_006.name = "Math.006"
    math_006.operation = 'MULTIPLY'
    math_006.use_clamp = False
    #Value_001
    math_006.inputs[1].default_value = 1.0

    #node Reroute.002
    reroute_002_1 = sdf_indextounit2dposition.nodes.new("NodeReroute")
    reroute_002_1.name = "Reroute.002"
    reroute_002_1.socket_idname = "NodeSocketFloat"
    #node Reroute.003
    reroute_003_1 = sdf_indextounit2dposition.nodes.new("NodeReroute")
    reroute_003_1.name = "Reroute.003"
    reroute_003_1.socket_idname = "NodeSocketFloat"



    #Set parents
    math_017_1.parent = frame_002_1
    math_018.parent = frame_002_1
    math_024.parent = frame_001_2
    math_025.parent = frame_001_2
    math_026_1.parent = frame_001_2
    separate_xyz_004.parent = frame_002_1
    separate_xyz_001.parent = frame_001_2
    separate_xyz.parent = frame_2
    math_001_1.parent = frame_2
    combine_xyz.parent = frame_2
    combine_xyz_004_1.parent = frame_002_1
    math_005.parent = frame_002_1
    math_006.parent = frame_002_1
    reroute_002_1.parent = frame_002_1
    reroute_003_1.parent = frame_002_1

    #Set locations
    group_output_2.location = (1846.91748046875, 150.09571838378906)
    group_input_2.location = (-1094.9285888671875, 14.197369575500488)
    math_017_1.location = (-46.72430419921875, 273.8778991699219)
    math_018.location = (-47.34539031982422, 80.06221008300781)
    math_024.location = (-515.8817749023438, 317.2615966796875)
    math_025.location = (-517.4718627929688, 140.12762451171875)
    math_026_1.location = (-335.4490966796875, 140.72796630859375)
    reroute_034_1.location = (-754.212646484375, -250.936279296875)
    separate_xyz_004.location = (-411.0942687988281, 105.51486206054688)
    separate_xyz_001.location = (-694.9862060546875, 287.5432434082031)
    reroute_008.location = (420.6412048339844, -246.47781372070312)
    vector_math_014_1.location = (470.7908020019531, 55.973453521728516)
    separate_xyz.location = (659.7344360351562, 59.47777557373047)
    math_001_1.location = (831.3579711914062, 155.85037231445312)
    combine_xyz.location = (1004.4439697265625, 84.02913665771484)
    frame_2.location = (42.6824951171875, 64.11441040039062)
    frame_001_2.location = (-186.7396240234375, -152.22540283203125)
    combine_xyz_004_1.location = (122.66310119628906, 177.08615112304688)
    reroute_1.location = (-384.28411865234375, -276.9636535644531)
    reroute_001_1.location = (-754.91162109375, -274.36578369140625)
    frame_002_1.location = (127.4990234375, -105.19476318359375)
    math_005.location = (-223.47259521484375, 179.34512329101562)
    math_006.location = (-228.22030639648438, -15.56097412109375)
    reroute_002_1.location = (-88.29773712158203, 233.28045654296875)
    reroute_003_1.location = (-408.6700134277344, -29.568862915039062)

    #Set dimensions
    group_output_2.width, group_output_2.height = 140.0, 100.0
    group_input_2.width, group_input_2.height = 140.0, 100.0
    math_017_1.width, math_017_1.height = 140.0, 100.0
    math_018.width, math_018.height = 140.0, 100.0
    math_024.width, math_024.height = 140.0, 100.0
    math_025.width, math_025.height = 140.0, 100.0
    math_026_1.width, math_026_1.height = 140.0, 100.0
    reroute_034_1.width, reroute_034_1.height = 16.0, 100.0
    separate_xyz_004.width, separate_xyz_004.height = 140.0, 100.0
    separate_xyz_001.width, separate_xyz_001.height = 140.0, 100.0
    reroute_008.width, reroute_008.height = 16.0, 100.0
    vector_math_014_1.width, vector_math_014_1.height = 140.0, 100.0
    separate_xyz.width, separate_xyz.height = 140.0, 100.0
    math_001_1.width, math_001_1.height = 140.0, 100.0
    combine_xyz.width, combine_xyz.height = 140.0, 100.0
    frame_2.width, frame_2.height = 545.0, 285.0
    frame_001_2.width, frame_001_2.height = 560.0, 395.0
    combine_xyz_004_1.width, combine_xyz_004_1.height = 140.0, 100.0
    reroute_1.width, reroute_1.height = 16.0, 100.0
    reroute_001_1.width, reroute_001_1.height = 16.0, 100.0
    frame_002_1.width, frame_002_1.height = 739.1710205078125, 508.0
    math_005.width, math_005.height = 140.0, 100.0
    math_006.width, math_006.height = 140.0, 100.0
    reroute_002_1.width, reroute_002_1.height = 16.0, 100.0
    reroute_003_1.width, reroute_003_1.height = 16.0, 100.0

    #initialize sdf_indextounit2dposition links
    #math_025.Value -> math_026_1.Value
    sdf_indextounit2dposition.links.new(math_025.outputs[0], math_026_1.inputs[0])
    #reroute_034_1.Output -> math_025.Value
    sdf_indextounit2dposition.links.new(reroute_034_1.outputs[0], math_025.inputs[1])
    #math_006.Value -> math_018.Value
    sdf_indextounit2dposition.links.new(math_006.outputs[0], math_018.inputs[1])
    #group_input_2.Index -> separate_xyz_001.Vector
    sdf_indextounit2dposition.links.new(group_input_2.outputs[1], separate_xyz_001.inputs[0])
    #reroute_1.Output -> separate_xyz_004.Vector
    sdf_indextounit2dposition.links.new(reroute_1.outputs[0], separate_xyz_004.inputs[0])
    #separate_xyz_001.Z -> math_024.Value
    sdf_indextounit2dposition.links.new(separate_xyz_001.outputs[2], math_024.inputs[0])
    #separate_xyz_001.Z -> math_025.Value
    sdf_indextounit2dposition.links.new(separate_xyz_001.outputs[2], math_025.inputs[0])
    #vector_math_014_1.Vector -> separate_xyz.Vector
    sdf_indextounit2dposition.links.new(vector_math_014_1.outputs[0], separate_xyz.inputs[0])
    #separate_xyz.X -> math_001_1.Value
    sdf_indextounit2dposition.links.new(separate_xyz.outputs[0], math_001_1.inputs[1])
    #math_001_1.Value -> combine_xyz.X
    sdf_indextounit2dposition.links.new(math_001_1.outputs[0], combine_xyz.inputs[0])
    #separate_xyz.Y -> combine_xyz.Y
    sdf_indextounit2dposition.links.new(separate_xyz.outputs[1], combine_xyz.inputs[1])
    #separate_xyz.Z -> combine_xyz.Z
    sdf_indextounit2dposition.links.new(separate_xyz.outputs[2], combine_xyz.inputs[2])
    #group_input_2.X Frames -> reroute_034_1.Input
    sdf_indextounit2dposition.links.new(group_input_2.outputs[0], reroute_034_1.inputs[0])
    #reroute_034_1.Output -> math_024.Value
    sdf_indextounit2dposition.links.new(reroute_034_1.outputs[0], math_024.inputs[1])
    #reroute_008.Output -> vector_math_014_1.Vector
    sdf_indextounit2dposition.links.new(reroute_008.outputs[0], vector_math_014_1.inputs[1])
    #math_017_1.Value -> combine_xyz_004_1.X
    sdf_indextounit2dposition.links.new(math_017_1.outputs[0], combine_xyz_004_1.inputs[0])
    #math_018.Value -> combine_xyz_004_1.Y
    sdf_indextounit2dposition.links.new(math_018.outputs[0], combine_xyz_004_1.inputs[1])
    #reroute_001_1.Output -> reroute_1.Input
    sdf_indextounit2dposition.links.new(reroute_001_1.outputs[0], reroute_1.inputs[0])
    #group_input_2.Unit Index -> reroute_001_1.Input
    sdf_indextounit2dposition.links.new(group_input_2.outputs[2], reroute_001_1.inputs[0])
    #reroute_034_1.Output -> reroute_008.Input
    sdf_indextounit2dposition.links.new(reroute_034_1.outputs[0], reroute_008.inputs[0])
    #combine_xyz_004_1.Vector -> vector_math_014_1.Vector
    sdf_indextounit2dposition.links.new(combine_xyz_004_1.outputs[0], vector_math_014_1.inputs[0])
    #separate_xyz_004.X -> math_005.Value
    sdf_indextounit2dposition.links.new(separate_xyz_004.outputs[0], math_005.inputs[0])
    #math_005.Value -> math_017_1.Value
    sdf_indextounit2dposition.links.new(math_005.outputs[0], math_017_1.inputs[1])
    #separate_xyz_004.Y -> math_006.Value
    sdf_indextounit2dposition.links.new(separate_xyz_004.outputs[1], math_006.inputs[0])
    #math_024.Value -> reroute_002_1.Input
    sdf_indextounit2dposition.links.new(math_024.outputs[0], reroute_002_1.inputs[0])
    #reroute_003_1.Output -> math_018.Value
    sdf_indextounit2dposition.links.new(reroute_003_1.outputs[0], math_018.inputs[0])
    #reroute_002_1.Output -> math_017_1.Value
    sdf_indextounit2dposition.links.new(reroute_002_1.outputs[0], math_017_1.inputs[0])
    #combine_xyz.Vector -> group_output_2.Unit 2D Position
    sdf_indextounit2dposition.links.new(combine_xyz.outputs[0], group_output_2.inputs[0])
    #math_026_1.Value -> reroute_003_1.Input
    sdf_indextounit2dposition.links.new(math_026_1.outputs[0], reroute_003_1.inputs[0])
    return sdf_indextounit2dposition

def build_geonodes_sdf_3d_node_group() -> bpy.types.NodeGroup:
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    sdf_3d = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "SDF_3D")

    sdf_3d.color_tag = 'NONE'
    sdf_3d.description = ""
    sdf_3d.default_group_node_width = 140
    


    #sdf_3d interface
    #Socket Voxels
    voxels_socket_2 = sdf_3d.interface.new_socket(name = "Voxels", in_out='OUTPUT', socket_type = 'NodeSocketGeometry')
    voxels_socket_2.attribute_domain = 'POINT'

    #Socket Distance
    distance_socket = sdf_3d.interface.new_socket(name = "Distance", in_out='OUTPUT', socket_type = 'NodeSocketFloat')
    distance_socket.default_value = 0.0
    distance_socket.min_value = -3.4028234663852886e+38
    distance_socket.max_value = 3.4028234663852886e+38
    distance_socket.subtype = 'NONE'
    distance_socket.attribute_domain = 'POINT'

    #Socket Bounding Box
    bounding_box_socket = sdf_3d.interface.new_socket(name = "Bounding Box", in_out='OUTPUT', socket_type = 'NodeSocketGeometry')
    bounding_box_socket.attribute_domain = 'POINT'

    #Socket Debug
    debug_socket = sdf_3d.interface.new_socket(name = "Debug", in_out='INPUT', socket_type = 'NodeSocketBool')
    debug_socket.default_value = False
    debug_socket.attribute_domain = 'POINT'

    #Socket X Frames
    x_frames_socket_1 = sdf_3d.interface.new_socket(name = "X Frames", in_out='INPUT', socket_type = 'NodeSocketFloat')
    x_frames_socket_1.default_value = 4.0
    x_frames_socket_1.min_value = 1.0
    x_frames_socket_1.max_value = 10000.0
    x_frames_socket_1.subtype = 'NONE'
    x_frames_socket_1.attribute_domain = 'POINT'

    #Socket X
    x_socket_1 = sdf_3d.interface.new_socket(name = "X", in_out='INPUT', socket_type = 'NodeSocketInt')
    x_socket_1.default_value = 16
    x_socket_1.min_value = -2147483648
    x_socket_1.max_value = 2147483647
    x_socket_1.subtype = 'NONE'
    x_socket_1.attribute_domain = 'POINT'

    #Socket Y
    y_socket_1 = sdf_3d.interface.new_socket(name = "Y", in_out='INPUT', socket_type = 'NodeSocketInt')
    y_socket_1.default_value = 16
    y_socket_1.min_value = -2147483648
    y_socket_1.max_value = 2147483647
    y_socket_1.subtype = 'NONE'
    y_socket_1.attribute_domain = 'POINT'

    #Socket Z
    z_socket_1 = sdf_3d.interface.new_socket(name = "Z", in_out='INPUT', socket_type = 'NodeSocketInt')
    z_socket_1.default_value = 16
    z_socket_1.min_value = -2147483648
    z_socket_1.max_value = 2147483647
    z_socket_1.subtype = 'NONE'
    z_socket_1.attribute_domain = 'POINT'

    #Socket Object
    object_socket = sdf_3d.interface.new_socket(name = "Object", in_out='INPUT', socket_type = 'NodeSocketObject')
    object_socket.attribute_domain = 'POINT'

    #Socket Bounds Offset
    bounds_offset_socket_1 = sdf_3d.interface.new_socket(name = "Bounds Offset", in_out='INPUT', socket_type = 'NodeSocketVector')
    bounds_offset_socket_1.default_value = (0.0, 0.0, 0.0)
    bounds_offset_socket_1.min_value = -10000.0
    bounds_offset_socket_1.max_value = 10000.0
    bounds_offset_socket_1.subtype = 'NONE'
    bounds_offset_socket_1.attribute_domain = 'POINT'

    #Socket Threshold
    threshold_socket = sdf_3d.interface.new_socket(name = "Threshold", in_out='INPUT', socket_type = 'NodeSocketFloat')
    threshold_socket.default_value = 0.0
    threshold_socket.min_value = -10000.0
    threshold_socket.max_value = 10000.0
    threshold_socket.subtype = 'NONE'
    threshold_socket.attribute_domain = 'POINT'


    #initialize sdf_3d nodes
    #node Group Output
    group_output_3 = sdf_3d.nodes.new("NodeGroupOutput")
    group_output_3.name = "Group Output"
    group_output_3.is_active_output = True

    #node Group Input
    group_input_3 = sdf_3d.nodes.new("NodeGroupInput")
    group_input_3.name = "Group Input"

    #node Points
    points = sdf_3d.nodes.new("GeometryNodePoints")
    points.name = "Points"
    #Position
    points.inputs[1].default_value = (0.0, 0.0, 0.0)
    #Radius
    points.inputs[2].default_value = 0.10000000149011612

    #node Sample Nearest Surface
    sample_nearest_surface = sdf_3d.nodes.new("GeometryNodeSampleNearestSurface")
    sample_nearest_surface.name = "Sample Nearest Surface"
    sample_nearest_surface.data_type = 'FLOAT_VECTOR'
    #Group ID
    sample_nearest_surface.inputs[2].default_value = 0
    #Sample Group ID
    sample_nearest_surface.inputs[4].default_value = 0

    #node Position
    position = sdf_3d.nodes.new("GeometryNodeInputPosition")
    position.name = "Position"

    #node Instance on Points
    instance_on_points = sdf_3d.nodes.new("GeometryNodeInstanceOnPoints")
    instance_on_points.name = "Instance on Points"
    #Selection
    instance_on_points.inputs[1].default_value = True
    #Pick Instance
    instance_on_points.inputs[3].default_value = False
    #Instance Index
    instance_on_points.inputs[4].default_value = 0
    #Rotation
    instance_on_points.inputs[5].default_value = (0.0, 0.0, 0.0)

    #node Set Position.001
    set_position_001 = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position_001.name = "Set Position.001"
    #Selection
    set_position_001.inputs[1].default_value = True

    #node Delete Geometry
    delete_geometry = sdf_3d.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry.name = "Delete Geometry"
    delete_geometry.domain = 'POINT'
    delete_geometry.mode = 'ONLY_FACE'
    #Selection
    delete_geometry.inputs[1].default_value = True

    #node Realize Instances
    realize_instances = sdf_3d.nodes.new("GeometryNodeRealizeInstances")
    realize_instances.name = "Realize Instances"
    #Selection
    realize_instances.inputs[1].default_value = True
    #Realize All
    realize_instances.inputs[2].default_value = True
    #Depth
    realize_instances.inputs[3].default_value = 0

    #node Store Named Attribute
    store_named_attribute = sdf_3d.nodes.new("GeometryNodeStoreNamedAttribute")
    store_named_attribute.name = "Store Named Attribute"
    store_named_attribute.data_type = 'FLOAT'
    store_named_attribute.domain = 'POINT'
    #Selection
    store_named_attribute.inputs[1].default_value = True
    #Name
    store_named_attribute.inputs[2].default_value = "Distance"

    #node Switch
    switch = sdf_3d.nodes.new("GeometryNodeSwitch")
    switch.name = "Switch"
    switch.input_type = 'FLOAT'
    #False
    switch.inputs[1].default_value = 0.0

    #node Vector Math.007
    vector_math_007 = sdf_3d.nodes.new("ShaderNodeVectorMath")
    vector_math_007.name = "Vector Math.007"
    vector_math_007.operation = 'DISTANCE'

    #node Named Attribute
    named_attribute = sdf_3d.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute.name = "Named Attribute"
    named_attribute.data_type = 'FLOAT'
    #Name
    named_attribute.inputs[0].default_value = "Distance"

    #node Attribute Statistic
    attribute_statistic = sdf_3d.nodes.new("GeometryNodeAttributeStatistic")
    attribute_statistic.name = "Attribute Statistic"
    attribute_statistic.data_type = 'FLOAT'
    attribute_statistic.domain = 'POINT'
    #Selection
    attribute_statistic.inputs[1].default_value = True

    #node Reroute.002
    reroute_002_2 = sdf_3d.nodes.new("NodeReroute")
    reroute_002_2.name = "Reroute.002"
    reroute_002_2.socket_idname = "NodeSocketFloat"
    #node Store Named Attribute.001
    store_named_attribute_001 = sdf_3d.nodes.new("GeometryNodeStoreNamedAttribute")
    store_named_attribute_001.name = "Store Named Attribute.001"
    store_named_attribute_001.data_type = 'FLOAT'
    store_named_attribute_001.domain = 'POINT'
    #Selection
    store_named_attribute_001.inputs[1].default_value = True
    #Name
    store_named_attribute_001.inputs[2].default_value = "Distance"

    #node Math.008
    math_008 = sdf_3d.nodes.new("ShaderNodeMath")
    math_008.name = "Math.008"
    math_008.operation = 'DIVIDE'
    math_008.use_clamp = False

    #node Frame.001
    frame_001_3 = sdf_3d.nodes.new("NodeFrame")
    frame_001_3.label = "create & position voxels in geometry's bounding box volume"
    frame_001_3.name = "Frame.001"
    frame_001_3.label_size = 20
    frame_001_3.shrink = True

    #node Reroute.014
    reroute_014 = sdf_3d.nodes.new("NodeReroute")
    reroute_014.name = "Reroute.014"
    reroute_014.socket_idname = "NodeSocketGeometry"
    #node Frame.003
    frame_003_1 = sdf_3d.nodes.new("NodeFrame")
    frame_003_1.label = "write signed distance field to voxel"
    frame_003_1.name = "Frame.003"
    frame_003_1.label_size = 20
    frame_003_1.shrink = True

    #node Frame.004
    frame_004 = sdf_3d.nodes.new("NodeFrame")
    frame_004.label = "invert & normalize distance field"
    frame_004.name = "Frame.004"
    frame_004.label_size = 20
    frame_004.shrink = True

    #node Math.006
    math_006_1 = sdf_3d.nodes.new("ShaderNodeMath")
    math_006_1.name = "Math.006"
    math_006_1.operation = 'SUBTRACT'
    math_006_1.use_clamp = False

    #node Frame.005
    frame_005 = sdf_3d.nodes.new("NodeFrame")
    frame_005.label = "instanciate  & center voxels"
    frame_005.name = "Frame.005"
    frame_005.label_size = 20
    frame_005.shrink = True

    #node Reroute.018
    reroute_018 = sdf_3d.nodes.new("NodeReroute")
    reroute_018.name = "Reroute.018"
    reroute_018.socket_idname = "NodeSocketGeometry"
    #node Delete Geometry.001
    delete_geometry_001 = sdf_3d.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry_001.name = "Delete Geometry.001"
    delete_geometry_001.domain = 'POINT'
    delete_geometry_001.mode = 'ALL'

    #node Named Attribute.001
    named_attribute_001 = sdf_3d.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute_001.name = "Named Attribute.001"
    named_attribute_001.data_type = 'FLOAT'
    #Name
    named_attribute_001.inputs[0].default_value = "Distance"

    #node Compare
    compare = sdf_3d.nodes.new("FunctionNodeCompare")
    compare.name = "Compare"
    compare.data_type = 'FLOAT'
    compare.mode = 'ELEMENT'
    compare.operation = 'LESS_THAN'

    #node Math.012
    math_012 = sdf_3d.nodes.new("ShaderNodeMath")
    math_012.name = "Math.012"
    math_012.operation = 'ABSOLUTE'
    math_012.use_clamp = False

    #node Reroute.020
    reroute_020 = sdf_3d.nodes.new("NodeReroute")
    reroute_020.name = "Reroute.020"
    reroute_020.socket_idname = "NodeSocketGeometry"
    #node Raycast
    raycast = sdf_3d.nodes.new("GeometryNodeRaycast")
    raycast.name = "Raycast"
    raycast.data_type = 'FLOAT'
    raycast.mapping = 'INTERPOLATED'
    #Attribute
    raycast.inputs[1].default_value = 0.0
    #Ray Direction
    raycast.inputs[3].default_value = (0.0, 0.0, 1.0)
    #Ray Length
    raycast.inputs[4].default_value = 100.0

    #node Vector Math.009
    vector_math_009 = sdf_3d.nodes.new("ShaderNodeVectorMath")
    vector_math_009.name = "Vector Math.009"
    vector_math_009.operation = 'DOT_PRODUCT'
    #Vector_001
    vector_math_009.inputs[1].default_value = (0.0, 0.0, 1.0)

    #node Compare.001
    compare_001 = sdf_3d.nodes.new("FunctionNodeCompare")
    compare_001.name = "Compare.001"
    compare_001.data_type = 'FLOAT'
    compare_001.mode = 'ELEMENT'
    compare_001.operation = 'GREATER_THAN'
    #B
    compare_001.inputs[1].default_value = 0.0

    #node Switch.001
    switch_001 = sdf_3d.nodes.new("GeometryNodeSwitch")
    switch_001.name = "Switch.001"
    switch_001.input_type = 'FLOAT'
    #False
    switch_001.inputs[1].default_value = 1.0
    #True
    switch_001.inputs[2].default_value = -1.0

    #node Math.007
    math_007 = sdf_3d.nodes.new("ShaderNodeMath")
    math_007.name = "Math.007"
    math_007.operation = 'MULTIPLY'
    math_007.use_clamp = False

    #node Math.013
    math_013 = sdf_3d.nodes.new("ShaderNodeMath")
    math_013.name = "Math.013"
    math_013.operation = 'MULTIPLY'
    math_013.use_clamp = False
    #Value_001
    math_013.inputs[1].default_value = 2.0

    #node Cube.001
    cube_001 = sdf_3d.nodes.new("GeometryNodeMeshCube")
    cube_001.name = "Cube.001"
    #Size
    cube_001.inputs[0].default_value = (1.0, 1.0, 1.0)
    #Vertices X
    cube_001.inputs[1].default_value = 2
    #Vertices Y
    cube_001.inputs[2].default_value = 2
    #Vertices Z
    cube_001.inputs[3].default_value = 2

    #node Set Position
    set_position = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position.name = "Set Position"
    #Selection
    set_position.inputs[1].default_value = True
    #Offset
    set_position.inputs[3].default_value = (0.0, 0.0, 0.0)

    #node Points.001
    points_001 = sdf_3d.nodes.new("GeometryNodePoints")
    points_001.name = "Points.001"
    #Count
    points_001.inputs[0].default_value = 1
    #Position
    points_001.inputs[1].default_value = (0.0, 0.0, 0.0)
    #Radius
    points_001.inputs[2].default_value = 0.10000000149011612

    #node Instance on Points.001
    instance_on_points_001 = sdf_3d.nodes.new("GeometryNodeInstanceOnPoints")
    instance_on_points_001.name = "Instance on Points.001"
    #Selection
    instance_on_points_001.inputs[1].default_value = True
    #Pick Instance
    instance_on_points_001.inputs[3].default_value = False
    #Instance Index
    instance_on_points_001.inputs[4].default_value = 0
    #Rotation
    instance_on_points_001.inputs[5].default_value = (0.0, 0.0, 0.0)

    #node Realize Instances.001
    realize_instances_001 = sdf_3d.nodes.new("GeometryNodeRealizeInstances")
    realize_instances_001.name = "Realize Instances.001"
    #Selection
    realize_instances_001.inputs[1].default_value = True
    #Realize All
    realize_instances_001.inputs[2].default_value = True
    #Depth
    realize_instances_001.inputs[3].default_value = 0

    #node Set Position.002
    set_position_002 = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position_002.name = "Set Position.002"
    #Selection
    set_position_002.inputs[1].default_value = True
    #Position
    set_position_002.inputs[2].default_value = (0.0, 0.0, 0.0)
    #Offset
    set_position_002.inputs[3].default_value = (0.5, 0.5, 0.5)

    #node Frame.006
    frame_006 = sdf_3d.nodes.new("NodeFrame")
    frame_006.label = "construct custom bounds (accounting for user-specified offset)"
    frame_006.name = "Frame.006"
    frame_006.label_size = 20
    frame_006.shrink = True

    #node Reroute.023
    reroute_023 = sdf_3d.nodes.new("NodeReroute")
    reroute_023.name = "Reroute.023"
    reroute_023.socket_idname = "NodeSocketVector"
    #node Reroute.027
    reroute_027 = sdf_3d.nodes.new("NodeReroute")
    reroute_027.name = "Reroute.027"
    reroute_027.socket_idname = "NodeSocketVector"
    #node Set Position.003
    set_position_003 = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position_003.name = "Set Position.003"
    #Selection
    set_position_003.inputs[1].default_value = True
    #Offset
    set_position_003.inputs[3].default_value = (0.0, 0.0, 0.0)

    #node Frame.007
    frame_007 = sdf_3d.nodes.new("NodeFrame")
    frame_007.label = "lay voxels flat in 2D unit space "
    frame_007.name = "Frame.007"
    frame_007.label_size = 20
    frame_007.shrink = True

    #node Reroute.031
    reroute_031 = sdf_3d.nodes.new("NodeReroute")
    reroute_031.name = "Reroute.031"
    reroute_031.socket_idname = "NodeSocketFloat"
    #node Switch.002
    switch_002 = sdf_3d.nodes.new("GeometryNodeSwitch")
    switch_002.label = "Debug"
    switch_002.name = "Switch.002"
    switch_002.input_type = 'GEOMETRY'

    #node Reroute.032
    reroute_032 = sdf_3d.nodes.new("NodeReroute")
    reroute_032.name = "Reroute.032"
    reroute_032.socket_idname = "NodeSocketBool"
    #node Reroute.033
    reroute_033 = sdf_3d.nodes.new("NodeReroute")
    reroute_033.name = "Reroute.033"
    reroute_033.socket_idname = "NodeSocketBool"
    #node Capture Attribute
    capture_attribute = sdf_3d.nodes.new("GeometryNodeCaptureAttribute")
    capture_attribute.name = "Capture Attribute"
    capture_attribute.active_index = 0
    capture_attribute.capture_items.clear()
    capture_attribute.capture_items.new('FLOAT', "Attribute")
    capture_attribute.capture_items["Attribute"].data_type = 'FLOAT'
    capture_attribute.domain = 'POINT'

    #node Named Attribute.002
    named_attribute_002 = sdf_3d.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute_002.name = "Named Attribute.002"
    named_attribute_002.data_type = 'FLOAT'
    #Name
    named_attribute_002.inputs[0].default_value = "Distance"

    #node Group
    group = sdf_3d.nodes.new("GeometryNodeGroup")
    group.name = "Group"
    #group.node_tree = build_geonodes_sdf_linearindextounitindex_node_group()

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "SDF_LinearIndexToUnitIndex":
            geonode_tree = node_group
            break

    if geonode_tree is None:
        geonode_tree = build_geonodes_sdf_linearindextounitindex_node_group()
    group.node_tree = geonode_tree

    #node Reroute.001
    reroute_001_2 = sdf_3d.nodes.new("NodeReroute")
    reroute_001_2.name = "Reroute.001"
    reroute_001_2.socket_idname = "NodeSocketVector"
    #node Vector Math
    vector_math = sdf_3d.nodes.new("ShaderNodeVectorMath")
    vector_math.name = "Vector Math"
    vector_math.operation = 'DIVIDE'
    #Vector
    vector_math.inputs[0].default_value = (1.0, 1.0, 1.0)

    #node Reroute
    reroute_2 = sdf_3d.nodes.new("NodeReroute")
    reroute_2.name = "Reroute"
    reroute_2.socket_idname = "NodeSocketVector"
    #node Vector Math.012
    vector_math_012_1 = sdf_3d.nodes.new("ShaderNodeVectorMath")
    vector_math_012_1.name = "Vector Math.012"
    vector_math_012_1.operation = 'DIVIDE'

    #node Group.001
    group_001 = sdf_3d.nodes.new("GeometryNodeGroup")
    group_001.name = "Group.001"
    #group_001.node_tree = build_geonodes_sdf_getvoxeldata_node_group() 

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "SDF_GetVoxelData":
            geonode_tree = node_group
            break

    if geonode_tree is None:
        geonode_tree = build_geonodes_sdf_getvoxeldata_node_group()
    group_001.node_tree = geonode_tree

    #node Reroute.003
    reroute_003_2 = sdf_3d.nodes.new("NodeReroute")
    reroute_003_2.name = "Reroute.003"
    reroute_003_2.socket_idname = "NodeSocketGeometry"
    #node Group.002
    group_002 = sdf_3d.nodes.new("GeometryNodeGroup")
    group_002.name = "Group.002"
    #group_002.node_tree = build_geonodes_sdf_indextounit2dposition_node_group()

    geonode_tree = None
    for node_group in bpy.data.node_groups:
        if node_group.name == "SDF_IndexToUnit2DPosition":
            geonode_tree = node_group
            break

    if geonode_tree is None:
        geonode_tree = build_geonodes_sdf_indextounit2dposition_node_group()
    group_002.node_tree = geonode_tree

    #node Reroute.004
    reroute_004_2 = sdf_3d.nodes.new("NodeReroute")
    reroute_004_2.name = "Reroute.004"
    reroute_004_2.socket_idname = "NodeSocketFloat"
    #node Reroute.005
    reroute_005_2 = sdf_3d.nodes.new("NodeReroute")
    reroute_005_2.name = "Reroute.005"
    reroute_005_2.socket_idname = "NodeSocketVector"
    #node Reroute.006
    reroute_006_1 = sdf_3d.nodes.new("NodeReroute")
    reroute_006_1.name = "Reroute.006"
    reroute_006_1.socket_idname = "NodeSocketVector"
    #node Reroute.007
    reroute_007_1 = sdf_3d.nodes.new("NodeReroute")
    reroute_007_1.name = "Reroute.007"
    reroute_007_1.socket_idname = "NodeSocketFloat"
    #node Reroute.008
    reroute_008_1 = sdf_3d.nodes.new("NodeReroute")
    reroute_008_1.name = "Reroute.008"
    reroute_008_1.socket_idname = "NodeSocketVector"
    #node Reroute.009
    reroute_009_1 = sdf_3d.nodes.new("NodeReroute")
    reroute_009_1.name = "Reroute.009"
    reroute_009_1.socket_idname = "NodeSocketVector"
    #node Reroute.010
    reroute_010 = sdf_3d.nodes.new("NodeReroute")
    reroute_010.name = "Reroute.010"
    reroute_010.socket_idname = "NodeSocketVector"
    #node Reroute.011
    reroute_011 = sdf_3d.nodes.new("NodeReroute")
    reroute_011.name = "Reroute.011"
    reroute_011.socket_idname = "NodeSocketVector"
    #node Reroute.012
    reroute_012 = sdf_3d.nodes.new("NodeReroute")
    reroute_012.name = "Reroute.012"
    reroute_012.socket_idname = "NodeSocketVector"
    #node Reroute.013
    reroute_013 = sdf_3d.nodes.new("NodeReroute")
    reroute_013.name = "Reroute.013"
    reroute_013.socket_idname = "NodeSocketVector"
    #node Reroute.015
    reroute_015 = sdf_3d.nodes.new("NodeReroute")
    reroute_015.name = "Reroute.015"
    reroute_015.socket_idname = "NodeSocketVector"
    #node Reroute.019
    reroute_019 = sdf_3d.nodes.new("NodeReroute")
    reroute_019.name = "Reroute.019"
    reroute_019.socket_idname = "NodeSocketVector"
    #node Reroute.022
    reroute_022 = sdf_3d.nodes.new("NodeReroute")
    reroute_022.name = "Reroute.022"
    reroute_022.socket_idname = "NodeSocketVector"
    #node Reroute.024
    reroute_024 = sdf_3d.nodes.new("NodeReroute")
    reroute_024.name = "Reroute.024"
    reroute_024.socket_idname = "NodeSocketVector"
    #node Frame
    frame_3 = sdf_3d.nodes.new("NodeFrame")
    frame_3.label = "SDF voxel visualization"
    frame_3.name = "Frame"
    frame_3.label_size = 20
    frame_3.shrink = True

    #node Reroute.025
    reroute_025 = sdf_3d.nodes.new("NodeReroute")
    reroute_025.name = "Reroute.025"
    reroute_025.socket_idname = "NodeSocketFloat"
    #node Reroute.026
    reroute_026 = sdf_3d.nodes.new("NodeReroute")
    reroute_026.name = "Reroute.026"
    reroute_026.socket_idname = "NodeSocketFloat"
    #node Reroute.028
    reroute_028_1 = sdf_3d.nodes.new("NodeReroute")
    reroute_028_1.name = "Reroute.028"
    reroute_028_1.socket_idname = "NodeSocketGeometry"
    #node Frame.002
    frame_002_2 = sdf_3d.nodes.new("NodeFrame")
    frame_002_2.label = "output"
    frame_002_2.name = "Frame.002"
    frame_002_2.label_size = 20
    frame_002_2.shrink = True

    #node Grid
    grid = sdf_3d.nodes.new("GeometryNodeMeshGrid")
    grid.name = "Grid"
    #Size X
    grid.inputs[0].default_value = 1.0
    #Size Y
    grid.inputs[1].default_value = 1.0
    #Vertices X
    grid.inputs[2].default_value = 2
    #Vertices Y
    grid.inputs[3].default_value = 2

    #node Math
    math_1 = sdf_3d.nodes.new("ShaderNodeMath")
    math_1.name = "Math"
    math_1.operation = 'ABSOLUTE'
    math_1.use_clamp = False

    #node Math.001
    math_001_2 = sdf_3d.nodes.new("ShaderNodeMath")
    math_001_2.name = "Math.001"
    math_001_2.operation = 'MAXIMUM'
    math_001_2.use_clamp = False

    #node Set Position.004
    set_position_004 = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position_004.name = "Set Position.004"
    #Selection
    set_position_004.inputs[1].default_value = True
    #Position
    set_position_004.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Object Info
    object_info = sdf_3d.nodes.new("GeometryNodeObjectInfo")
    object_info.name = "Object Info"
    object_info.transform_space = 'ORIGINAL'
    #As Instance
    object_info.inputs[1].default_value = False

    #node Vector Math.001
    vector_math_001 = sdf_3d.nodes.new("ShaderNodeVectorMath")
    vector_math_001.name = "Vector Math.001"
    vector_math_001.operation = 'MULTIPLY'
    #Vector_001
    vector_math_001.inputs[1].default_value = (-0.5, 0.5, 0.0)

    #node Set Position.005
    set_position_005 = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position_005.name = "Set Position.005"
    #Selection
    set_position_005.inputs[1].default_value = True
    #Position
    set_position_005.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Vector Math.002
    vector_math_002 = sdf_3d.nodes.new("ShaderNodeVectorMath")
    vector_math_002.name = "Vector Math.002"
    vector_math_002.operation = 'ADD'
    #Vector_001
    vector_math_002.inputs[1].default_value = (-0.5, -0.5, 0.0)

    #node Set Position.006
    set_position_006 = sdf_3d.nodes.new("GeometryNodeSetPosition")
    set_position_006.name = "Set Position.006"
    #Selection
    set_position_006.inputs[1].default_value = True
    #Position
    set_position_006.inputs[2].default_value = (0.0, 0.0, 0.0)

    #node Reroute.016
    reroute_016 = sdf_3d.nodes.new("NodeReroute")
    reroute_016.name = "Reroute.016"
    reroute_016.socket_idname = "NodeSocketVector"
    #node Set Point Radius
    set_point_radius = sdf_3d.nodes.new("GeometryNodeSetPointRadius")
    set_point_radius.name = "Set Point Radius"
    #Selection
    set_point_radius.inputs[1].default_value = True
    #Radius
    set_point_radius.inputs[2].default_value = 0.009999999776482582

    #node Reroute.017
    reroute_017 = sdf_3d.nodes.new("NodeReroute")
    reroute_017.name = "Reroute.017"
    reroute_017.socket_idname = "NodeSocketGeometry"
    #node Boolean Math
    boolean_math = sdf_3d.nodes.new("FunctionNodeBooleanMath")
    boolean_math.name = "Boolean Math"
    boolean_math.operation = 'AND'

    #node Reroute.021
    reroute_021 = sdf_3d.nodes.new("NodeReroute")
    reroute_021.name = "Reroute.021"
    reroute_021.socket_idname = "NodeSocketBool"



    #Set parents
    group_output_3.parent = frame_002_2
    points.parent = frame_001_3
    sample_nearest_surface.parent = frame_003_1
    position.parent = frame_003_1
    instance_on_points.parent = frame_005
    set_position_001.parent = frame_001_3
    delete_geometry.parent = frame_006
    realize_instances.parent = frame_005
    store_named_attribute.parent = frame_003_1
    switch.parent = frame_003_1
    vector_math_007.parent = frame_003_1
    named_attribute.parent = frame_004
    attribute_statistic.parent = frame_004
    reroute_002_2.parent = frame_004
    store_named_attribute_001.parent = frame_004
    math_008.parent = frame_004
    reroute_014.parent = frame_003_1
    math_006_1.parent = frame_004
    reroute_018.parent = frame_004
    delete_geometry_001.parent = frame_3
    named_attribute_001.parent = frame_3
    compare.parent = frame_3
    math_012.parent = frame_3
    reroute_020.parent = frame_003_1
    raycast.parent = frame_003_1
    vector_math_009.parent = frame_003_1
    compare_001.parent = frame_003_1
    switch_001.parent = frame_003_1
    math_007.parent = frame_003_1
    math_013.parent = frame_004
    cube_001.parent = frame_006
    set_position.parent = frame_006
    points_001.parent = frame_006
    instance_on_points_001.parent = frame_006
    realize_instances_001.parent = frame_006
    set_position_002.parent = frame_006
    reroute_023.parent = frame_006
    reroute_027.parent = frame_006
    set_position_003.parent = frame_007
    capture_attribute.parent = frame_002_2
    named_attribute_002.parent = frame_002_2
    group.parent = frame_001_3
    vector_math.parent = frame_005
    vector_math_012_1.parent = frame_005
    group_001.parent = frame_001_3
    group_002.parent = frame_007
    reroute_010.parent = frame_001_3
    reroute_011.parent = frame_001_3
    reroute_012.parent = frame_001_3
    reroute_015.parent = frame_003_1
    reroute_019.parent = frame_003_1
    reroute_022.parent = frame_003_1
    reroute_024.parent = frame_006
    grid.parent = frame_005
    math_1.parent = frame_004
    math_001_2.parent = frame_004
    vector_math_001.parent = frame_005
    set_position_005.parent = frame_005
    vector_math_002.parent = frame_005
    boolean_math.parent = frame_003_1
    reroute_021.parent = frame_003_1

    #Set locations
    group_output_3.location = (3957.519287109375, 375.9239196777344)
    group_input_3.location = (-1696.15869140625, 813.2702026367188)
    points.location = (-1517.342529296875, 202.48370361328125)
    sample_nearest_surface.location = (596.9215698242188, 800.9130859375)
    position.location = (429.50921630859375, 662.265380859375)
    instance_on_points.location = (1441.125, 540.343017578125)
    set_position_001.location = (-1163.4888916015625, 227.159912109375)
    delete_geometry.location = (1272.497802734375, -187.59226989746094)
    realize_instances.location = (1771.272216796875, 568.461669921875)
    store_named_attribute.location = (1097.7738037109375, 949.698974609375)
    switch.location = (929.5620727539062, 824.99462890625)
    vector_math_007.location = (771.4120483398438, 731.608642578125)
    named_attribute.location = (1622.6610107421875, 200.71963500976562)
    attribute_statistic.location = (1804.3525390625, 509.71917724609375)
    reroute_002_2.location = (1944.6331787109375, 167.39602661132812)
    store_named_attribute_001.location = (2694.3974609375, 637.1520385742188)
    math_008.location = (2521.119140625, 497.45166015625)
    frame_001_3.location = (436.0032958984375, 799.7252197265625)
    reroute_014.location = (414.51336669921875, 837.497802734375)
    frame_003_1.location = (-887.6524658203125, -95.36004638671875)
    frame_004.location = (-1161.861572265625, 143.62548828125)
    math_006_1.location = (2335.3955078125, 508.7923583984375)
    frame_005.location = (959.482421875, 779.881103515625)
    reroute_018.location = (1722.509765625, 524.86962890625)
    delete_geometry_001.location = (3328.922119140625, 1299.44287109375)
    named_attribute_001.location = (2832.329345703125, 1159.6920166015625)
    compare.location = (3157.908447265625, 1162.9444580078125)
    math_012.location = (2994.941162109375, 1161.1392822265625)
    reroute_020.location = (400.744873046875, 691.7406005859375)
    raycast.location = (430.18951416015625, 544.519775390625)
    vector_math_009.location = (605.2916259765625, 536.384765625)
    compare_001.location = (767.8292846679688, 534.8316650390625)
    switch_001.location = (1087.6524658203125, 575.3600463867188)
    math_007.location = (1097.968994140625, 740.4876098632812)
    math_013.location = (2332.60009765625, 344.3539123535156)
    cube_001.location = (435.6810302734375, -403.1053771972656)
    set_position.location = (939.4271240234375, -286.5730895996094)
    points_001.location = (599.221435546875, -192.445068359375)
    instance_on_points_001.location = (774.1058349609375, -308.94439697265625)
    realize_instances_001.location = (1104.3260498046875, -260.80810546875)
    set_position_002.location = (605.8958740234375, -396.3113708496094)
    frame_006.location = (-937.4663696289062, 160.19229125976562)
    reroute_023.location = (441.7779235839844, -650.9663696289062)
    reroute_027.location = (441.9057312011719, -383.6954040527344)
    set_position_003.location = (2439.835693359375, 1605.6990966796875)
    frame_007.location = (-596.995361328125, -309.726318359375)
    reroute_031.location = (-1295.379150390625, 1206.04150390625)
    switch_002.location = (2962.495361328125, 907.4381103515625)
    reroute_032.location = (2867.60205078125, 1406.4434814453125)
    reroute_033.location = (-1302.7073974609375, 1397.864013671875)
    capture_attribute.location = (3784.21435546875, 402.77093505859375)
    named_attribute_002.location = (3603.680419921875, 355.1932373046875)
    group.location = (-1692.422607421875, 81.51385498046875)
    reroute_001_2.location = (-1059.4835205078125, 1159.9844970703125)
    vector_math.location = (1113.03173828125, 330.7069091796875)
    reroute_2.location = (-1069.37744140625, 1183.646484375)
    vector_math_012_1.location = (1278.16064453125, 225.162841796875)
    group_001.location = (-1338.654541015625, 158.0269775390625)
    reroute_003_2.location = (-950.6799926757812, 594.6954345703125)
    group_002.location = (2250.8603515625, 1596.3089599609375)
    reroute_004_2.location = (1520.1234130859375, 894.897216796875)
    reroute_005_2.location = (1359.446533203125, 1163.8924560546875)
    reroute_006_1.location = (1359.446533203125, 1185.938232421875)
    reroute_007_1.location = (1359.446533203125, 1207.9532470703125)
    reroute_008_1.location = (1360.4886474609375, 1136.3067626953125)
    reroute_009_1.location = (-1047.9840087890625, 1135.78076171875)
    reroute_010.location = (-1393.48974609375, -151.218505859375)
    reroute_011.location = (-1507.554443359375, -55.5220947265625)
    reroute_012.location = (-1506.90478515625, -77.3095703125)
    reroute_013.location = (1462.013671875, 940.0596313476562)
    reroute_015.location = (569.0888671875, 579.9088134765625)
    reroute_019.location = (395.4002990722656, 579.09814453125)
    reroute_022.location = (397.97967529296875, 304.9390869140625)
    reroute_024.location = (741.8193359375, -651.621826171875)
    frame_3.location = (359.47705078125, -318.0537109375)
    reroute_025.location = (3484.71435546875, 574.1519775390625)
    reroute_026.location = (-1322.665283203125, 557.6737060546875)
    reroute_028_1.location = (3955.082763671875, -44.88593292236328)
    frame_002_2.location = (75.56494140625, 0.778656005859375)
    grid.location = (1281.538330078125, 472.076171875)
    math_1.location = (1973.3074951171875, 517.5889282226562)
    math_001_2.location = (2144.3251953125, 518.5302124023438)
    set_position_004.location = (1840.206298828125, 804.8887939453125)
    object_info.location = (-1483.071533203125, 717.279052734375)
    vector_math_001.location = (1444.375244140625, 254.019775390625)
    set_position_005.location = (1602.692626953125, 542.7158203125)
    vector_math_002.location = (1599.74609375, 257.06787109375)
    set_position_006.location = (1828.827880859375, 1.3083686828613281)
    reroute_016.location = (1761.03125, 678.5283813476562)
    set_point_radius.location = (2034.6766357421875, 777.55029296875)
    reroute_017.location = (2882.342529296875, 746.4934692382812)
    boolean_math.location = (927.6524658203125, 632.7140502929688)
    reroute_021.location = (611.7842407226562, 550.0679931640625)

    #Set dimensions
    group_output_3.width, group_output_3.height = 140.0, 100.0
    group_input_3.width, group_input_3.height = 140.0, 100.0
    points.width, points.height = 140.0, 100.0
    sample_nearest_surface.width, sample_nearest_surface.height = 150.0, 100.0
    position.width, position.height = 140.0, 100.0
    instance_on_points.width, instance_on_points.height = 140.0, 100.0
    set_position_001.width, set_position_001.height = 140.0, 100.0
    delete_geometry.width, delete_geometry.height = 140.0, 100.0
    realize_instances.width, realize_instances.height = 140.0, 100.0
    store_named_attribute.width, store_named_attribute.height = 140.0, 100.0
    switch.width, switch.height = 140.0, 100.0
    vector_math_007.width, vector_math_007.height = 140.0, 100.0
    named_attribute.width, named_attribute.height = 140.0, 100.0
    attribute_statistic.width, attribute_statistic.height = 140.0, 100.0
    reroute_002_2.width, reroute_002_2.height = 16.0, 100.0
    store_named_attribute_001.width, store_named_attribute_001.height = 140.0, 100.0
    math_008.width, math_008.height = 140.0, 100.0
    frame_001_3.width, frame_001_3.height = 729.0, 456.4932861328125
    reroute_014.width, reroute_014.height = 16.0, 100.0
    frame_003_1.width, frame_003_1.height = 910.252197265625, 835.0
    frame_004.width, frame_004.height = 1272.0, 628.0
    math_006_1.width, math_006_1.height = 140.0, 100.0
    frame_005.width, frame_005.height = 858.0, 569.0
    reroute_018.width, reroute_018.height = 16.0, 100.0
    delete_geometry_001.width, delete_geometry_001.height = 140.0, 100.0
    named_attribute_001.width, named_attribute_001.height = 140.0, 100.0
    compare.width, compare.height = 140.0, 100.0
    math_012.width, math_012.height = 140.0, 100.0
    reroute_020.width, reroute_020.height = 16.0, 100.0
    raycast.width, raycast.height = 150.0, 100.0
    vector_math_009.width, vector_math_009.height = 140.0, 100.0
    compare_001.width, compare_001.height = 140.0, 100.0
    switch_001.width, switch_001.height = 140.0, 100.0
    math_007.width, math_007.height = 140.0, 100.0
    math_013.width, math_013.height = 140.0, 100.0
    cube_001.width, cube_001.height = 140.0, 100.0
    set_position.width, set_position.height = 140.0, 100.0
    points_001.width, points_001.height = 140.0, 100.0
    instance_on_points_001.width, instance_on_points_001.height = 140.0, 100.0
    realize_instances_001.width, realize_instances_001.height = 140.0, 100.0
    set_position_002.width, set_position_002.height = 140.0, 100.0
    frame_006.width, frame_006.height = 1038.6884765625, 542.4295654296875
    reroute_023.width, reroute_023.height = 16.0, 100.0
    reroute_027.width, reroute_027.height = 16.0, 100.0
    set_position_003.width, set_position_003.height = 140.0, 100.0
    frame_007.width, frame_007.height = 389.0, 271.0
    reroute_031.width, reroute_031.height = 16.0, 100.0
    switch_002.width, switch_002.height = 140.0, 100.0
    reroute_032.width, reroute_032.height = 16.0, 100.0
    reroute_033.width, reroute_033.height = 16.0, 100.0
    capture_attribute.width, capture_attribute.height = 140.0, 100.0
    named_attribute_002.width, named_attribute_002.height = 140.0, 100.0
    group.width, group.height = 140.0, 100.0
    reroute_001_2.width, reroute_001_2.height = 16.0, 100.0
    vector_math.width, vector_math.height = 140.0, 100.0
    reroute_2.width, reroute_2.height = 16.0, 100.0
    vector_math_012_1.width, vector_math_012_1.height = 140.0, 100.0
    group_001.width, group_001.height = 140.0, 100.0
    reroute_003_2.width, reroute_003_2.height = 16.0, 100.0
    group_002.width, group_002.height = 140.0, 100.0
    reroute_004_2.width, reroute_004_2.height = 16.0, 100.0
    reroute_005_2.width, reroute_005_2.height = 16.0, 100.0
    reroute_006_1.width, reroute_006_1.height = 16.0, 100.0
    reroute_007_1.width, reroute_007_1.height = 16.0, 100.0
    reroute_008_1.width, reroute_008_1.height = 16.0, 100.0
    reroute_009_1.width, reroute_009_1.height = 16.0, 100.0
    reroute_010.width, reroute_010.height = 16.0, 100.0
    reroute_011.width, reroute_011.height = 16.0, 100.0
    reroute_012.width, reroute_012.height = 16.0, 100.0
    reroute_013.width, reroute_013.height = 16.0, 100.0
    reroute_015.width, reroute_015.height = 16.0, 100.0
    reroute_019.width, reroute_019.height = 16.0, 100.0
    reroute_022.width, reroute_022.height = 16.0, 100.0
    reroute_024.width, reroute_024.height = 16.0, 100.0
    frame_3.width, frame_3.height = 696.0, 354.0
    reroute_025.width, reroute_025.height = 16.0, 100.0
    reroute_026.width, reroute_026.height = 16.0, 100.0
    reroute_028_1.width, reroute_028_1.height = 16.0, 100.0
    frame_002_2.width, frame_002_2.height = 554.0, 239.0
    grid.width, grid.height = 140.0, 100.0
    math_1.width, math_1.height = 140.0, 100.0
    math_001_2.width, math_001_2.height = 140.0, 100.0
    set_position_004.width, set_position_004.height = 140.0, 100.0
    object_info.width, object_info.height = 140.0, 100.0
    vector_math_001.width, vector_math_001.height = 140.0, 100.0
    set_position_005.width, set_position_005.height = 140.0, 100.0
    vector_math_002.width, vector_math_002.height = 140.0, 100.0
    set_position_006.width, set_position_006.height = 140.0, 100.0
    reroute_016.width, reroute_016.height = 16.0, 100.0
    set_point_radius.width, set_point_radius.height = 140.0, 100.0
    reroute_017.width, reroute_017.height = 16.0, 100.0
    boolean_math.width, boolean_math.height = 140.0, 100.0
    reroute_021.width, reroute_021.height = 16.0, 100.0

    #initialize sdf_3d links
    #sample_nearest_surface.Is Valid -> switch.Switch
    sdf_3d.links.new(sample_nearest_surface.outputs[1], switch.inputs[0])
    #position.Position -> vector_math_007.Vector
    sdf_3d.links.new(position.outputs[0], vector_math_007.inputs[1])
    #position.Position -> sample_nearest_surface.Sample Position
    sdf_3d.links.new(position.outputs[0], sample_nearest_surface.inputs[3])
    #named_attribute.Attribute -> attribute_statistic.Attribute
    sdf_3d.links.new(named_attribute.outputs[0], attribute_statistic.inputs[2])
    #position.Position -> sample_nearest_surface.Value
    sdf_3d.links.new(position.outputs[0], sample_nearest_surface.inputs[1])
    #sample_nearest_surface.Value -> vector_math_007.Vector
    sdf_3d.links.new(sample_nearest_surface.outputs[0], vector_math_007.inputs[0])
    #named_attribute.Attribute -> reroute_002_2.Input
    sdf_3d.links.new(named_attribute.outputs[0], reroute_002_2.inputs[0])
    #vector_math_007.Value -> switch.True
    sdf_3d.links.new(vector_math_007.outputs[1], switch.inputs[2])
    #reroute_014.Output -> store_named_attribute.Geometry
    sdf_3d.links.new(reroute_014.outputs[0], store_named_attribute.inputs[0])
    #reroute_028_1.Output -> group_output_3.Bounding Box
    sdf_3d.links.new(reroute_028_1.outputs[0], group_output_3.inputs[2])
    #set_position_001.Geometry -> reroute_014.Input
    sdf_3d.links.new(set_position_001.outputs[0], reroute_014.inputs[0])
    #reroute_020.Output -> sample_nearest_surface.Mesh
    sdf_3d.links.new(reroute_020.outputs[0], sample_nearest_surface.inputs[0])
    #reroute_002_2.Output -> math_006_1.Value
    sdf_3d.links.new(reroute_002_2.outputs[0], math_006_1.inputs[1])
    #reroute_018.Output -> store_named_attribute_001.Geometry
    sdf_3d.links.new(reroute_018.outputs[0], store_named_attribute_001.inputs[0])
    #store_named_attribute.Geometry -> reroute_018.Input
    sdf_3d.links.new(store_named_attribute.outputs[0], reroute_018.inputs[0])
    #reroute_018.Output -> attribute_statistic.Geometry
    sdf_3d.links.new(reroute_018.outputs[0], attribute_statistic.inputs[0])
    #math_006_1.Value -> math_008.Value
    sdf_3d.links.new(math_006_1.outputs[0], math_008.inputs[0])
    #compare.Result -> delete_geometry_001.Selection
    sdf_3d.links.new(compare.outputs[0], delete_geometry_001.inputs[1])
    #named_attribute_001.Attribute -> math_012.Value
    sdf_3d.links.new(named_attribute_001.outputs[0], math_012.inputs[0])
    #math_012.Value -> compare.A
    sdf_3d.links.new(math_012.outputs[0], compare.inputs[0])
    #reroute_003_2.Output -> reroute_020.Input
    sdf_3d.links.new(reroute_003_2.outputs[0], reroute_020.inputs[0])
    #reroute_020.Output -> raycast.Target Geometry
    sdf_3d.links.new(reroute_020.outputs[0], raycast.inputs[0])
    #reroute_022.Output -> raycast.Source Position
    sdf_3d.links.new(reroute_022.outputs[0], raycast.inputs[2])
    #raycast.Hit Normal -> vector_math_009.Vector
    sdf_3d.links.new(raycast.outputs[2], vector_math_009.inputs[0])
    #vector_math_009.Value -> compare_001.A
    sdf_3d.links.new(vector_math_009.outputs[1], compare_001.inputs[0])
    #switch.Output -> math_007.Value
    sdf_3d.links.new(switch.outputs[0], math_007.inputs[0])
    #switch_001.Output -> math_007.Value
    sdf_3d.links.new(switch_001.outputs[0], math_007.inputs[1])
    #math_007.Value -> store_named_attribute.Value
    sdf_3d.links.new(math_007.outputs[0], store_named_attribute.inputs[3])
    #math_013.Value -> math_008.Value
    sdf_3d.links.new(math_013.outputs[0], math_008.inputs[1])
    #points_001.Points -> instance_on_points_001.Points
    sdf_3d.links.new(points_001.outputs[0], instance_on_points_001.inputs[0])
    #instance_on_points_001.Instances -> set_position.Geometry
    sdf_3d.links.new(instance_on_points_001.outputs[0], set_position.inputs[0])
    #set_position.Geometry -> realize_instances_001.Geometry
    sdf_3d.links.new(set_position.outputs[0], realize_instances_001.inputs[0])
    #realize_instances_001.Geometry -> delete_geometry.Geometry
    sdf_3d.links.new(realize_instances_001.outputs[0], delete_geometry.inputs[0])
    #reroute_024.Output -> instance_on_points_001.Scale
    sdf_3d.links.new(reroute_024.outputs[0], instance_on_points_001.inputs[6])
    #cube_001.Mesh -> set_position_002.Geometry
    sdf_3d.links.new(cube_001.outputs[0], set_position_002.inputs[0])
    #set_position_002.Geometry -> instance_on_points_001.Instance
    sdf_3d.links.new(set_position_002.outputs[0], instance_on_points_001.inputs[2])
    #reroute_027.Output -> set_position.Position
    sdf_3d.links.new(reroute_027.outputs[0], set_position.inputs[2])
    #group_input_3.X Frames -> reroute_031.Input
    sdf_3d.links.new(group_input_3.outputs[1], reroute_031.inputs[0])
    #reroute_032.Output -> switch_002.Switch
    sdf_3d.links.new(reroute_032.outputs[0], switch_002.inputs[0])
    #reroute_033.Output -> reroute_032.Input
    sdf_3d.links.new(reroute_033.outputs[0], reroute_032.inputs[0])
    #group_input_3.Debug -> reroute_033.Input
    sdf_3d.links.new(group_input_3.outputs[0], reroute_033.inputs[0])
    #named_attribute_002.Attribute -> capture_attribute.Attribute
    sdf_3d.links.new(named_attribute_002.outputs[0], capture_attribute.inputs[1])
    #capture_attribute.Attribute -> group_output_3.Distance
    sdf_3d.links.new(capture_attribute.outputs[1], group_output_3.inputs[1])
    #capture_attribute.Geometry -> group_output_3.Voxels
    sdf_3d.links.new(capture_attribute.outputs[0], group_output_3.inputs[0])
    #group_input_3.X -> group.X
    sdf_3d.links.new(group_input_3.outputs[2], group.inputs[0])
    #group_input_3.Y -> group.Y
    sdf_3d.links.new(group_input_3.outputs[3], group.inputs[1])
    #group_input_3.Z -> group.Z
    sdf_3d.links.new(group_input_3.outputs[4], group.inputs[2])
    #group.UnitIndex -> reroute_001_2.Input
    sdf_3d.links.new(group.outputs[1], reroute_001_2.inputs[0])
    #reroute_013.Output -> vector_math.Vector
    sdf_3d.links.new(reroute_013.outputs[0], vector_math.inputs[1])
    #group.Index -> reroute_2.Input
    sdf_3d.links.new(group.outputs[0], reroute_2.inputs[0])
    #vector_math.Vector -> vector_math_012_1.Vector
    sdf_3d.links.new(vector_math.outputs[0], vector_math_012_1.inputs[0])
    #vector_math_012_1.Vector -> instance_on_points.Scale
    sdf_3d.links.new(vector_math_012_1.outputs[0], instance_on_points.inputs[6])
    #reroute_004_2.Output -> vector_math_012_1.Vector
    sdf_3d.links.new(reroute_004_2.outputs[0], vector_math_012_1.inputs[1])
    #points.Points -> set_position_001.Geometry
    sdf_3d.links.new(points.outputs[0], set_position_001.inputs[0])
    #reroute_011.Output -> group_001.UnitIndex
    sdf_3d.links.new(reroute_011.outputs[0], group_001.inputs[1])
    #reroute_010.Output -> group_001.Bounds Offset
    sdf_3d.links.new(reroute_010.outputs[0], group_001.inputs[3])
    #reroute_012.Output -> group_001.Voxels
    sdf_3d.links.new(reroute_012.outputs[0], group_001.inputs[2])
    #group_001.Voxel Position -> set_position_001.Position
    sdf_3d.links.new(group_001.outputs[0], set_position_001.inputs[2])
    #group_001.Voxel Offset -> set_position_001.Offset
    sdf_3d.links.new(group_001.outputs[1], set_position_001.inputs[3])
    #group_001.Bounds Extent -> reroute_023.Input
    sdf_3d.links.new(group_001.outputs[5], reroute_023.inputs[0])
    #group_001.Bounds Min -> reroute_027.Input
    sdf_3d.links.new(group_001.outputs[3], reroute_027.inputs[0])
    #reroute_003_2.Output -> group_001.Geometry
    sdf_3d.links.new(reroute_003_2.outputs[0], group_001.inputs[0])
    #reroute_006_1.Output -> group_002.Index
    sdf_3d.links.new(reroute_006_1.outputs[0], group_002.inputs[1])
    #reroute_005_2.Output -> group_002.Unit Index
    sdf_3d.links.new(reroute_005_2.outputs[0], group_002.inputs[2])
    #group_002.Unit 2D Position -> set_position_003.Position
    sdf_3d.links.new(group_002.outputs[0], set_position_003.inputs[2])
    #reroute_007_1.Output -> group_002.X Frames
    sdf_3d.links.new(reroute_007_1.outputs[0], group_002.inputs[0])
    #reroute_001_2.Output -> reroute_005_2.Input
    sdf_3d.links.new(reroute_001_2.outputs[0], reroute_005_2.inputs[0])
    #reroute_2.Output -> reroute_006_1.Input
    sdf_3d.links.new(reroute_2.outputs[0], reroute_006_1.inputs[0])
    #reroute_031.Output -> reroute_007_1.Input
    sdf_3d.links.new(reroute_031.outputs[0], reroute_007_1.inputs[0])
    #reroute_007_1.Output -> reroute_004_2.Input
    sdf_3d.links.new(reroute_007_1.outputs[0], reroute_004_2.inputs[0])
    #reroute_009_1.Output -> reroute_008_1.Input
    sdf_3d.links.new(reroute_009_1.outputs[0], reroute_008_1.inputs[0])
    #group.Voxels -> reroute_009_1.Input
    sdf_3d.links.new(group.outputs[2], reroute_009_1.inputs[0])
    #group_input_3.Bounds Offset -> reroute_010.Input
    sdf_3d.links.new(group_input_3.outputs[6], reroute_010.inputs[0])
    #group.UnitIndex -> reroute_011.Input
    sdf_3d.links.new(group.outputs[1], reroute_011.inputs[0])
    #group.Voxels -> reroute_012.Input
    sdf_3d.links.new(group.outputs[2], reroute_012.inputs[0])
    #reroute_008_1.Output -> reroute_013.Input
    sdf_3d.links.new(reroute_008_1.outputs[0], reroute_013.inputs[0])
    #position.Position -> reroute_015.Input
    sdf_3d.links.new(position.outputs[0], reroute_015.inputs[0])
    #reroute_015.Output -> reroute_019.Input
    sdf_3d.links.new(reroute_015.outputs[0], reroute_019.inputs[0])
    #reroute_019.Output -> reroute_022.Input
    sdf_3d.links.new(reroute_019.outputs[0], reroute_022.inputs[0])
    #reroute_023.Output -> reroute_024.Input
    sdf_3d.links.new(reroute_023.outputs[0], reroute_024.inputs[0])
    #reroute_025.Output -> compare.B
    sdf_3d.links.new(reroute_025.outputs[0], compare.inputs[1])
    #reroute_026.Output -> reroute_025.Input
    sdf_3d.links.new(reroute_026.outputs[0], reroute_025.inputs[0])
    #group_input_3.Threshold -> reroute_026.Input
    sdf_3d.links.new(group_input_3.outputs[7], reroute_026.inputs[0])
    #set_position_006.Geometry -> reroute_028_1.Input
    sdf_3d.links.new(set_position_006.outputs[0], reroute_028_1.inputs[0])
    #group.VoxelCount -> points.Count
    sdf_3d.links.new(group.outputs[3], points.inputs[0])
    #grid.Mesh -> instance_on_points.Instance
    sdf_3d.links.new(grid.outputs[0], instance_on_points.inputs[2])
    #set_position_003.Geometry -> instance_on_points.Points
    sdf_3d.links.new(set_position_003.outputs[0], instance_on_points.inputs[0])
    #attribute_statistic.Min -> math_1.Value
    sdf_3d.links.new(attribute_statistic.outputs[3], math_1.inputs[0])
    #math_1.Value -> math_001_2.Value
    sdf_3d.links.new(math_1.outputs[0], math_001_2.inputs[0])
    #attribute_statistic.Max -> math_001_2.Value
    sdf_3d.links.new(attribute_statistic.outputs[4], math_001_2.inputs[1])
    #math_001_2.Value -> math_006_1.Value
    sdf_3d.links.new(math_001_2.outputs[0], math_006_1.inputs[0])
    #math_001_2.Value -> math_013.Value
    sdf_3d.links.new(math_001_2.outputs[0], math_013.inputs[0])
    #group_input_3.Object -> object_info.Object
    sdf_3d.links.new(group_input_3.outputs[5], object_info.inputs[0])
    #object_info.Geometry -> reroute_003_2.Input
    sdf_3d.links.new(object_info.outputs[4], reroute_003_2.inputs[0])
    #vector_math_012_1.Vector -> vector_math_001.Vector
    sdf_3d.links.new(vector_math_012_1.outputs[0], vector_math_001.inputs[0])
    #instance_on_points.Instances -> set_position_005.Geometry
    sdf_3d.links.new(instance_on_points.outputs[0], set_position_005.inputs[0])
    #set_position_005.Geometry -> realize_instances.Geometry
    sdf_3d.links.new(set_position_005.outputs[0], realize_instances.inputs[0])
    #vector_math_001.Vector -> vector_math_002.Vector
    sdf_3d.links.new(vector_math_001.outputs[0], vector_math_002.inputs[0])
    #vector_math_002.Vector -> set_position_005.Offset
    sdf_3d.links.new(vector_math_002.outputs[0], set_position_005.inputs[3])
    #switch_002.Output -> delete_geometry_001.Geometry
    sdf_3d.links.new(switch_002.outputs[0], delete_geometry_001.inputs[0])
    #delete_geometry_001.Geometry -> capture_attribute.Geometry
    sdf_3d.links.new(delete_geometry_001.outputs[0], capture_attribute.inputs[0])
    #math_008.Value -> store_named_attribute_001.Value
    sdf_3d.links.new(math_008.outputs[0], store_named_attribute_001.inputs[3])
    #delete_geometry.Geometry -> set_position_006.Geometry
    sdf_3d.links.new(delete_geometry.outputs[0], set_position_006.inputs[0])
    #object_info.Location -> reroute_016.Input
    sdf_3d.links.new(object_info.outputs[1], reroute_016.inputs[0])
    #reroute_016.Output -> set_position_006.Offset
    sdf_3d.links.new(reroute_016.outputs[0], set_position_006.inputs[3])
    #set_position_004.Geometry -> set_point_radius.Points
    sdf_3d.links.new(set_position_004.outputs[0], set_point_radius.inputs[0])
    #reroute_016.Output -> set_position_004.Offset
    sdf_3d.links.new(reroute_016.outputs[0], set_position_004.inputs[3])
    #reroute_017.Output -> switch_002.True
    sdf_3d.links.new(reroute_017.outputs[0], switch_002.inputs[2])
    #set_point_radius.Points -> reroute_017.Input
    sdf_3d.links.new(set_point_radius.outputs[0], reroute_017.inputs[0])
    #realize_instances.Geometry -> switch_002.False
    sdf_3d.links.new(realize_instances.outputs[0], switch_002.inputs[1])
    #reroute_021.Output -> boolean_math.Boolean
    sdf_3d.links.new(reroute_021.outputs[0], boolean_math.inputs[0])
    #boolean_math.Boolean -> switch_001.Switch
    sdf_3d.links.new(boolean_math.outputs[0], switch_001.inputs[0])
    #compare_001.Result -> boolean_math.Boolean
    sdf_3d.links.new(compare_001.outputs[0], boolean_math.inputs[1])
    #raycast.Is Hit -> reroute_021.Input
    sdf_3d.links.new(raycast.outputs[0], reroute_021.inputs[0])
    #store_named_attribute_001.Geometry -> set_position_003.Geometry
    sdf_3d.links.new(store_named_attribute_001.outputs[0], set_position_003.inputs[0])
    #store_named_attribute_001.Geometry -> set_position_004.Geometry
    sdf_3d.links.new(store_named_attribute_001.outputs[0], set_position_004.inputs[0])
    return sdf_3d

def build_geonodes_sdf_3d() -> bpy.types.NodeGroup:
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    nodes_sdf_3d = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "Nodes_SDF_3D")

    nodes_sdf_3d.color_tag = 'NONE'
    nodes_sdf_3d.description = ""
    nodes_sdf_3d.default_group_node_width = 140
    

    nodes_sdf_3d.is_modifier = True

    #nodes_sdf_3d interface
    #Socket Geometry
    geometry_socket_1 = nodes_sdf_3d.interface.new_socket(name = "Geometry", in_out='OUTPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket_1.attribute_domain = 'POINT'

    #Socket SDF
    sdf_socket = nodes_sdf_3d.interface.new_socket(name = "SDF", in_out='OUTPUT', socket_type = 'NodeSocketColor')
    sdf_socket.default_value = (0.0, 0.0, 0.0, 1.0)
    sdf_socket.attribute_domain = 'CORNER'

    #Socket Debug
    debug_socket_1 = nodes_sdf_3d.interface.new_socket(name = "Debug", in_out='INPUT', socket_type = 'NodeSocketBool')
    debug_socket_1.default_value = False
    debug_socket_1.attribute_domain = 'POINT'

    #Socket X Frames
    x_frames_socket_2 = nodes_sdf_3d.interface.new_socket(name = "X Frames", in_out='INPUT', socket_type = 'NodeSocketFloat')
    x_frames_socket_2.default_value = 4.0
    x_frames_socket_2.min_value = 1.0
    x_frames_socket_2.max_value = 10000.0
    x_frames_socket_2.subtype = 'NONE'
    x_frames_socket_2.attribute_domain = 'POINT'

    #Socket X
    x_socket_2 = nodes_sdf_3d.interface.new_socket(name = "X", in_out='INPUT', socket_type = 'NodeSocketInt')
    x_socket_2.default_value = 16
    x_socket_2.min_value = -2147483648
    x_socket_2.max_value = 2147483647
    x_socket_2.subtype = 'NONE'
    x_socket_2.attribute_domain = 'POINT'

    #Socket Y
    y_socket_2 = nodes_sdf_3d.interface.new_socket(name = "Y", in_out='INPUT', socket_type = 'NodeSocketInt')
    y_socket_2.default_value = 16
    y_socket_2.min_value = -2147483648
    y_socket_2.max_value = 2147483647
    y_socket_2.subtype = 'NONE'
    y_socket_2.attribute_domain = 'POINT'

    #Socket Z
    z_socket_2 = nodes_sdf_3d.interface.new_socket(name = "Z", in_out='INPUT', socket_type = 'NodeSocketInt')
    z_socket_2.default_value = 16
    z_socket_2.min_value = -2147483648
    z_socket_2.max_value = 2147483647
    z_socket_2.subtype = 'NONE'
    z_socket_2.attribute_domain = 'POINT'

    #Socket Object
    object_socket_1 = nodes_sdf_3d.interface.new_socket(name = "Object", in_out='INPUT', socket_type = 'NodeSocketObject')
    object_socket_1.attribute_domain = 'POINT'

    #Socket Bounds Offset
    bounds_offset_socket_2 = nodes_sdf_3d.interface.new_socket(name = "Bounds Offset", in_out='INPUT', socket_type = 'NodeSocketVector')
    bounds_offset_socket_2.default_value = (0.5, 0.5, 0.5)
    bounds_offset_socket_2.min_value = -10000.0
    bounds_offset_socket_2.max_value = 10000.0
    bounds_offset_socket_2.subtype = 'NONE'
    bounds_offset_socket_2.attribute_domain = 'POINT'

    #Socket Threshold
    threshold_socket_1 = nodes_sdf_3d.interface.new_socket(name = "Threshold", in_out='INPUT', socket_type = 'NodeSocketFloat')
    threshold_socket_1.default_value = 0.5
    threshold_socket_1.min_value = -10000.0
    threshold_socket_1.max_value = 10000.0
    threshold_socket_1.subtype = 'NONE'
    threshold_socket_1.attribute_domain = 'POINT'


    #initialize nodes_sdf_3d nodes
    #node Group Input
    group_input_4 = nodes_sdf_3d.nodes.new("NodeGroupInput")
    group_input_4.name = "Group Input"

    #node Group Output
    group_output_4 = nodes_sdf_3d.nodes.new("NodeGroupOutput")
    group_output_4.name = "Group Output"
    group_output_4.is_active_output = True

    #node Group.003
    group_003 = nodes_sdf_3d.nodes.new("GeometryNodeGroup")
    group_003.name = "Group.003"
    group_003.node_tree = build_geonodes_sdf_3d_node_group()

    #node Set Material
    set_material = nodes_sdf_3d.nodes.new("GeometryNodeSetMaterial")
    set_material.name = "Set Material"
    #Selection
    set_material.inputs[1].default_value = True
    if "SDF" in bpy.data.materials:
        set_material.inputs[2].default_value = bpy.data.materials["SDF"]

    #node Join Geometry
    join_geometry = nodes_sdf_3d.nodes.new("GeometryNodeJoinGeometry")
    join_geometry.name = "Join Geometry"

    #node Reroute
    reroute_3 = nodes_sdf_3d.nodes.new("NodeReroute")
    reroute_3.name = "Reroute"
    reroute_3.socket_idname = "NodeSocketGeometry"




    #Set locations
    group_input_4.location = (-499.7200927734375, 57.794464111328125)
    group_output_4.location = (230.0159454345703, 150.42523193359375)
    group_003.location = (-289.5909423828125, 145.61419677734375)
    set_material.location = (-106.26431274414062, 228.70626831054688)
    join_geometry.location = (66.55682373046875, 189.17645263671875)
    reroute_3.location = (25.431991577148438, 69.00948333740234)

    #Set dimensions
    group_input_4.width, group_input_4.height = 140.0, 100.0
    group_output_4.width, group_output_4.height = 140.0, 100.0
    group_003.width, group_003.height = 140.0, 100.0
    set_material.width, set_material.height = 140.0, 100.0
    join_geometry.width, join_geometry.height = 140.0, 100.0
    reroute_3.width, reroute_3.height = 16.0, 100.0

    #initialize nodes_sdf_3d links
    #group_input_4.X -> group_003.X
    nodes_sdf_3d.links.new(group_input_4.outputs[2], group_003.inputs[2])
    #group_input_4.Y -> group_003.Y
    nodes_sdf_3d.links.new(group_input_4.outputs[3], group_003.inputs[3])
    #group_input_4.Z -> group_003.Z
    nodes_sdf_3d.links.new(group_input_4.outputs[4], group_003.inputs[4])
    #group_input_4.Bounds Offset -> group_003.Bounds Offset
    nodes_sdf_3d.links.new(group_input_4.outputs[6], group_003.inputs[6])
    #group_input_4.X Frames -> group_003.X Frames
    nodes_sdf_3d.links.new(group_input_4.outputs[1], group_003.inputs[1])
    #group_input_4.Debug -> group_003.Debug
    nodes_sdf_3d.links.new(group_input_4.outputs[0], group_003.inputs[0])
    #group_input_4.Threshold -> group_003.Threshold
    nodes_sdf_3d.links.new(group_input_4.outputs[7], group_003.inputs[7])
    #group_003.Distance -> group_output_4.SDF
    nodes_sdf_3d.links.new(group_003.outputs[1], group_output_4.inputs[1])
    #group_input_4.Object -> group_003.Object
    nodes_sdf_3d.links.new(group_input_4.outputs[5], group_003.inputs[5])
    #group_003.Voxels -> set_material.Geometry
    nodes_sdf_3d.links.new(group_003.outputs[0], set_material.inputs[0])
    #reroute_3.Output -> join_geometry.Geometry
    nodes_sdf_3d.links.new(reroute_3.outputs[0], join_geometry.inputs[0])
    #join_geometry.Geometry -> group_output_4.Geometry
    nodes_sdf_3d.links.new(join_geometry.outputs[0], group_output_4.inputs[0])
    #group_003.Bounding Box -> reroute_3.Input
    nodes_sdf_3d.links.new(group_003.outputs[2], reroute_3.inputs[0])
    #set_material.Geometry -> join_geometry.Geometry
    nodes_sdf_3d.links.new(set_material.outputs[0], join_geometry.inputs[0])
    return nodes_sdf_3d

def buid_material_sdf_3d_node_group(mat: bpy.types.Material) -> bpy.types.NodeGroup:
    """
    Create a new node group
    https://github.com/BrendanParmer/NodeToPython/

    :return: node group
    :rtype: bpy.types.NodeGroup
    """
    mat.use_nodes = True
    sdf = mat.node_tree
    #start with a clean node tree
    for node in sdf.nodes:
        sdf.nodes.remove(node)
    sdf.color_tag = 'NONE'
    sdf.description = ""
    sdf.default_group_node_width = 140
    

    #sdf interface

    #initialize sdf nodes
    #node Material Output
    material_output = sdf.nodes.new("ShaderNodeOutputMaterial")
    material_output.name = "Material Output"
    material_output.is_active_output = True
    material_output.target = 'ALL'
    #Displacement
    material_output.inputs[2].default_value = (0.0, 0.0, 0.0)
    #Thickness
    material_output.inputs[3].default_value = 0.0

    #node Attribute
    attribute = sdf.nodes.new("ShaderNodeAttribute")
    attribute.name = "Attribute"
    attribute.attribute_name = "Color"
    attribute.attribute_type = 'GEOMETRY'

    #node Emission
    emission = sdf.nodes.new("ShaderNodeEmission")
    emission.name = "Emission"
    #Strength
    emission.inputs[1].default_value = 1.0


    #Set locations
    material_output.location = (300.0, 300.0)
    attribute.location = (-50.5788459777832, 251.546630859375)
    emission.location = (122.99018096923828, 275.61212158203125)

    #Set dimensions
    material_output.width, material_output.height = 140.0, 100.0
    attribute.width, attribute.height = 140.0, 100.0
    emission.width, emission.height = 140.0, 100.0

    #initialize sdf links
    #emission.Emission -> material_output.Surface
    sdf.links.new(emission.outputs[0], material_output.inputs[0])
    #attribute.Color -> emission.Color
    sdf.links.new(attribute.outputs[0], emission.inputs[0])
    return sdf

################
### TEXTURES ###
def generate_texture(bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate the SDF image

    :param bake_name: the bake operation's 'name'
    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: SDF image's width
    :param tex_height: SDF image's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename if filename != "" else "T_Bake_VertOffsets"
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

def export_texture(context: bpy.types.Context, image: bpy.types.Image, path: str, name: str, bake_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the SDF image

    :param context: Blender current execution context
    :param image: the SDF image to export
    :param path: export path
    :param name: file name
    :param bake_name: the bake operation's 'name'
    :param override_file: if an existing .exr file should be overriden
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    tags = {"BakeName": bake_name}
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

def get_best_texture_resolution(context: bpy.types.Context) -> tuple[bool, str, int, int]:
    """
    Return the best texture resolution given the amount of voxels to bake in X & Y, the number of slices to bake in Z as well as the amount of slices to 'distribute' per row

    :param context: Blender current execution context
    :return: the function's success, potential error message, texture width, texture height
    :rtype: tuple
    """


    settings = context.scene.SDFBakerSettings

    add_bake_report("x", settings.x)
    add_bake_report("y", settings.y)
    add_bake_report("z", settings.z)

    NumVoxels = settings.x * settings.y * settings.z
    if NumVoxels <= 0:
        return (False, "Zero voxel to bake", 0, 0)

    if settings.frames <= 0:
        return (False, "Invalid frames setting", 0, 0)

    slices_per_row = settings.frames
    slices = 0
    row = 0
    while slices < settings.z:
        slices += slices_per_row
        row += 1

    add_bake_report("tex_slices", slices_per_row)

    tex_width = slices_per_row * settings.x
    if tex_width <= 0:
        return (False, "Invalid texture width", tex_width, 0)
    elif tex_width > 8192:
        return (False, "Width over 8K", tex_width, 0)

    add_bake_report("tex_width", tex_width)

    tex_height = row * settings.y
    if tex_height <= 0:
        return (False, "Invalid texture height", tex_width, tex_height)
    elif tex_height > 8192:
        return (False, "Height over 8K", tex_width, tex_height)

    add_bake_report("tex_height", tex_height)

    return (True, "", tex_width, tex_height)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    settings = context.scene.SDFBakerSettings
    report = context.scene.SDFBakerReport

    root = ET.Element("BakedData",
                      type="SDF",
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
                            unit_invert_z=str(report.unit_invert_z))
    
    # mesh info
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""

    mesh_el = ET.SubElement(root, "Mesh", path=mesh_export_path,
                             bounds_offset_min_x=str(abs(report.mesh_min_bounds_offset[0])),
                             bounds_offset_min_y=str(abs(report.mesh_min_bounds_offset[1])),
                             bounds_offset_min_z=str(abs(report.mesh_min_bounds_offset[2])),
                             bounds_offset_max_x=str(abs(report.mesh_max_bounds_offset[0])),
                             bounds_offset_max_y=str(abs(report.mesh_max_bounds_offset[1])),
                             bounds_offset_max_z=str(abs(report.mesh_max_bounds_offset[2])))

    # texture
    if report.tex:
        if report.tex_path != "":
            tex_path_el = ET.SubElement(root, "Texture",
                                        width=str(report.tex_width),
                                        height=str(report.tex_height),
                                        slices=str(report.tex_slices),
                                        path=report.tex_path,
                                        distance=report.distance_mode,
                                        max_dist=str(report.max_dist),
                                        tiles=report.tile_sort_mode,
                                        x=str(report.x),
                                        y=str(report.y),
                                        z=str(report.z))

    # write xml
    tree = ET.ElementTree(root)
    if settings.export_xml_mode == "TEXPATH" and report.tex_path != "":
        export_path = os.path.join(os.path.dirname(report.tex_path), report.name + ".xml")
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