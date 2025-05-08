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

import time, math, mathutils, bpy, os
from ctypes import POINTER, pointer, c_int, cast, c_float
import uuid
import bmesh
import xml.etree.ElementTree as ET

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################

##############
### REPORT ###
def new_bake_report(context: bpy.types.Context):
    """ """
    settings = context.scene.ObjectAttributesSettings

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
    add_bake_report("origin_obj", settings.origin_obj)
    
    add_bake_report("depth_limit_use", settings.depth_limit_use)
    add_bake_report("depth_limit", settings.depth_limit)
    add_bake_report("use_pivot_painter_packing", settings.use_pivot_painter_packing)
    
def reset_bake_report():
    """ """
    report = bpy.context.scene.ObjectAttributesReport

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
    report.origin_obj = None

    report.depth_limit_use = False
    report.depth_limit = 0
    report.use_pivot_painter_packing = False

    report.tex_width = 0
    report.tex_height = 0
    report.textures.clear()
    report.textures_selected_index = 0

    report.mesh = None
    report.mesh_uvmap = 0
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_num_indices = 0

    report.xml = False
    report.xml_path = ""

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """ """
    setattr(bpy.context.scene.ObjectAttributesReport, prop_name, prop_value)

def add_bake_texture_report(texture: object):
    """
    Set values in the bake report to describe a texture

    :param texture: 
    :return:
    :rtype:
    """
    report = bpy.context.scene.ObjectAttributesReport

    report_texture = report.textures.add()

    # copy all attributes
    if hasattr(texture, "__annotations__"):
        for prop_name in texture.__annotations__.keys():
            try:
                setattr(report_texture, prop_name, getattr(texture, prop_name))
            except (AttributeError, TypeError):
                pass

    return report_texture

def edit_bake_texture_report_name(texture: object, name: str):
    """ """
    report = bpy.context.scene.ObjectAttributesReport
    
    for report_texture in report.textures:
        if report_texture == texture:
            report_texture.name = name
            return True

    return False

def clear_bake_texture_report(texture) -> bool:
    """
    """
    report = bpy.context.scene.ObjectAttributesReport
    
    for report_texture in report.textures:
        if report_texture == texture:
            report.textures.remove(report_texture)

    return True

def export_bake_report(context: bpy.types.Context):
    """ """
    return(export_xml(context))

###############
### PACKING ###
def get_bitpacked_integer(index):
	"""
    https://github.com/Gvgeo/Pivot-Painter-for-Blender, original algorithm by Jonathan Lindquist.
    
    Pivot Painter algorithm for packing a 16-bit integer into a 32-bit float, in a way that preserves the value during 32-bit to 16-bit float conversion.
    
    :param index: integer index to bitpack
    :return: bit-packed float
    :rtype: float
    """
	index = int(index)
	index = index + 1024
	sigh = index & 0x8000
	sigh = sigh << 16
	
	exptest = index & 0x7fff

	if exptest == 0:
		exp = 0
	else:
		exp = index >> 10
		exp = exp & 0x1f
		exp = exp - 15
		exp = exp + 127
		exp = exp << 23
	
	mant = index & 0x3ff
	mant = mant << 13
	
	index = sigh|exp|mant
	
	cp = pointer(c_int(index))
	fp = cast(cp, POINTER(c_float))
	return fp.contents.value

############
### BAKE ###
def get_bake_textures(context: bpy.types.Context) -> tuple[bool, str, list]:
    """
    Scan the textures to generate, ensuring each has a unique name and contains data in at least one of the RGBA channels.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of textures to generate and bake
    :rtype: tuple
    """

    settings = context.scene.ObjectAttributesSettings

    textures = []
    for texture in settings.textures:
        other_tex_names = [other_texture.name for other_texture in settings.textures if other_texture != texture]
        if texture.name in other_tex_names: # texture must be uniquely named
            return (False, "Multiple textures share the same name", None)
        
        if texture.R.channel_mode == "NONE" and texture.G.channel_mode == "NONE" and texture.B.channel_mode == "NONE" and texture.A.channel_mode == "NONE":
            continue
    
        textures.append(texture)

    if len(textures) <= 0:
        return (False, "No data to bake in texture(s)", None)
    
    return (True, "", textures)

def get_bake_selection(context: bpy.types.Context) -> tuple[bool, str, list, bpy.types.Object]:
    """
    Filter out non-mesh objects from the active selection and ensure the selection leads to a valid bake, then return the list of objects to include in the bake and the active object, or root object of the hierarchy if no active selection.

    :param context: Blender current execution context
    :return: the function's success, potential error message, list of objects to bake (filtered selection), active/root object
    :rtype: tuple
    """

    settings = context.scene.ObjectAttributesSettings

    active_obj = context.view_layer.objects.active # cache active object

    for selected_obj in context.selected_objects:
        if selected_obj.type != "MESH":
            selected_obj.select_set(False)
        elif len(selected_obj.data.vertices) <= 0: # mesh could have no vertices
            selected_obj.select_set(False)

    if not context.selected_objects:
        return (False, "No object selected once filtered out", None, None)

    objs_to_bake = context.selected_objects

    if len(objs_to_bake) > settings.mesh_count_limit:
         return (False, "Too many objects to bake", None, None)

    """
    we'll need to create a UVMap to assign a texel per unique element so we need to ensure objects can be safely merged without creating UVMap conflicts.
    This involves gathering uvmaps of all selected objects to build a list of maps as if objects were joined and checking if the amount of uvmaps exceed
    the maximum amount in case we need to create one.
    """
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.OA"
    uvmaps = []

    for obj_to_bake in objs_to_bake:
        if mesh_uvmap_name not in [uvlayer.name for uvlayer in obj_to_bake.data.uv_layers]: # can't find target UVMap?
            if len(obj_to_bake.data.uv_layers) >= 8: # ensure UVMap can be created
                return (False, obj_to_bake.name + " has the maximum amount of uvmaps already", None, None)

        for uvlayer in obj_to_bake.data.uv_layers: # gather uvmaps as if objects were joined
            if uvlayer.name not in uvmaps:
                uvmaps.append(uvlayer.name)

    if mesh_uvmap_name not in uvmaps: # can't find target UVMap?
        if len(uvmaps) >= 8: # ensure UVMap can be created
            return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None)

    """ """
    for obj_to_bake in objs_to_bake: # deselect objects for now
        obj_to_bake.select_set(False)

    context.view_layer.objects.active = None # blank canvas

    if active_obj is None:
        roots = [object for object in objs_to_bake if object.parent is None]
        active_obj = roots[0] if len(roots) > 0 else objs_to_bake[0]

    return (True, "", objs_to_bake, active_obj)

def get_bake_name(context: bpy.types.Context, active_object: bpy.types.Object) -> str:
    """
    Return the name to give to the bake operation.

    :param context: Blender current execution context
    :param active_object: object to derive name from
    :return: the bake operation's 'name'
    :rtype: string
    """

    settings = context.scene.ObjectAttributesSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.OT"
    tags = { "BakeName" : active_object.name if active_object is not None else ""}
    name = replace_tags(name, tags)
    return name

def pre_process_bake_selection(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, list, int]:
    """
    Generate and return copies of all depsgraph-evaluated meshes to be included in the bake.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: the function's success, potential error message, list of duplicated depsgraph-evaluated mesh objects to include in the bake, num of unique indices to account for
    :rtype: tuple
    """
    
    settings = context.scene.ObjectAttributesSettings

    dgraph = bpy.context.evaluated_depsgraph_get()

    """
    duplicate depsgraph-evaluated filtered selection & forward initial transform
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
        eval_obj_to_bake.matrix_world = eval_obj.matrix_world # forward initial transform

        for key in obj_to_bake.keys():
            if key != "_RNA_UI":
                eval_obj_to_bake[key] = obj_to_bake[key]

        eval_obj.to_mesh_clear()

        col.objects.link(eval_obj_to_bake)
        eval_objs_to_bake.append(eval_obj_to_bake)

        eval_obj_to_bake["BakedSource"] = obj_to_bake
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
    evaluate hierarchy just this once
    """
    hierarchy = []
    for eval_obj_to_bake in eval_objs_to_bake:
        """
        1. get the depth the object is at in the hierarchy
        """
        depth = 0
        eval_obj_to_bake_parent = eval_obj_to_bake
        while eval_obj_to_bake_parent:
            eval_obj_to_bake_parent = eval_obj_to_bake_parent.parent
            depth += 1
        eval_obj_to_bake["ObjectAttributesHierarchyDepth"] = depth

        """
        2. populate unique list of objects per depth: [[all root objects], [all children], [all grand children], ...]
        """
        while (depth - 1) >= len(hierarchy):
            hierarchy.append(None)

        if hierarchy[(depth - 1)] is None:
            hierarchy[(depth - 1)] = [eval_obj_to_bake]
        else:
            hierarchy[(depth - 1)].append(eval_obj_to_bake)

    """
    3. assign a unique element index to each object but depth-limit has to be accounted for
       let's assume the following hierarchy, with the associated unique element index:
    
        trunk (0) -> branch (1) -> twig (2) -> leaf (3)
                                            -> leaf (4)

       setting a depth limit of 1 requires the following change in assigning element index:

        trunk (0) -> branch (1) -> twig (1) -> leaf (1)
                                            -> leaf (1)

       this element index will be used to generate the UV map and center UV on the necessary
       texel corresponding to the element's index. Depth limit essentially makes the algorithm
       see leaves and twig as if they were part of the branch object. This simply involves
       assigning a unique element index per depth:
        - first all root objects
        - second all children...
       for each depth, check if max depth is reached, and if so, unique element index to assign
       is simply the parent element's index
    """
    element_index = 0
    for depth_index, depth_objs in enumerate(hierarchy):
        if settings.depth_limit_use and depth_index > settings.depth_limit:
            for obj in depth_objs:
                obj["ObjectAttributesHierarchyIndex"] = obj.parent["ObjectAttributesHierarchyIndex"]
        else:
            for obj in depth_objs:
                obj["ObjectAttributesHierarchyIndex"] = element_index
                element_index += 1

    return (True, "", eval_objs_to_bake, element_index)

def post_process_bake_selection(context: bpy.types.Context, eval_objs_to_bake: list, tex_width: int, tex_height: int) -> tuple[bool, str]:
    """
    Merge duplicated meshes that were part of the bake and clean duplicated meshes, if any

    :param context: Blender current execution context
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :param tex_width: 
    :param tex_height: 
    :return: the function's success and potential error message
    :rtype: tuple
    """
    #return (True, "")
    settings = context.scene.ObjectAttributesSettings

    name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.OA"

    # create a new mesh to 'merge' all duplicated meshes
    merged_mesh = bpy.data.meshes.new(name)

    texel_size_x = (1.0 / tex_width)
    half_texel_size_x = texel_size_x * 0.5

    texel_size_y = (1.0 / tex_height)
    half_texel_size_y = texel_size_y * 0.5

    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.OA"

    bm = bmesh.new()
    for eval_obj_to_bake in eval_objs_to_bake:
        """
        configure UVs
        """
        uvmap = None
        uvmap_index = 0
        
        for uvlayer_index, uvlayer in enumerate(eval_obj_to_bake.data.uv_layers):
            if uvlayer.name == mesh_uvmap_name:
                uvmap = uvlayer
                uvmap_index = uvlayer_index
                break

        if uvmap is None:
            if len(eval_obj_to_bake.data.uv_layers) >= 8:
                return(False, "Too many existing uvmaps")

            eval_obj_to_bake.data.uv_layers.new()
            uvmap_index = len(eval_obj_to_bake.data.uv_layers) - 1
            uvmap = eval_obj_to_bake.data.uv_layers[uvmap_index]
            uvmap.name = mesh_uvmap_name

        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            return(False, "Hierarchy index")

        u = (index % tex_width) * texel_size_x
        u += half_texel_size_x
        v = (index // tex_width) * texel_size_y
        v += half_texel_size_y
        if settings.unit_invert_v:
            v = 1.0 - v

        for loop_id in eval_obj_to_bake.data.loops:
            eval_obj_to_bake.data.uv_layers[uvmap_index].data[loop_id.index].uv = (u,v)

        """
        duplicate mesh
        """
        eval_obj_to_bake.data.transform(eval_obj_to_bake.matrix_world)
        bm.from_mesh(eval_obj_to_bake.data)
        
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    bm.to_mesh(merged_mesh)
    bm.free()

    # create a new object from the new mesh
    obj = bpy.data.objects.new(name, merged_mesh)
    if settings.origin_obj:
        obj.matrix_world = settings.origin_obj.matrix_world
        merged_mesh.transform(settings.origin_obj.matrix_world.inverted())
    context.scene.collection.objects.link(obj)

    add_bake_report("mesh", obj)

    for uvlayer_index, uvlayer in enumerate(merged_mesh.uv_layers):
        if uvlayer.name == mesh_uvmap_name:
            add_bake_report("mesh_uvmap", uvlayer_index)
            break 

    obj.select_set(True)
    context.view_layer.objects.active = obj

    clear_bake_selection(eval_objs_to_bake)

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

def bake(context: bpy.types.Context):
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    #bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? @TODO fails when no active selection

    settings = context.scene.ObjectAttributesSettings
    new_bake_report(context)

    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #

    bake_start_time = time.time()

    success, msg, textures = get_bake_textures(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    success, msg, objs_to_bake, root_obj = get_bake_selection(context)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(3)

    success, msg, eval_objs_to_bake, num_indices = pre_process_bake_selection(context, objs_to_bake)
    if not success:
        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)
    add_bake_report("mesh_num_indices", num_indices)

    wm.progress_update(5)

    success, msg, tex_width, tex_height = get_best_texture_resolution(context, num_indices)
    if not success:
        clear_bake_selection(eval_objs_to_bake)

        add_bake_report("success", False)
        add_bake_report("msg", msg)
        return (False, 'ERROR', msg)

    wm.progress_update(7)

    bake_name = get_bake_name(context, root_obj)
    add_bake_report("name", bake_name)

    wm.progress_update(10)

    ############
    # TEXTURES #

    dgraph = bpy.context.evaluated_depsgraph_get()

    bake_progress = 10
    bake_progress_step = (1.0 / (len(textures) * 4 * 3)) * 80
    for texture in textures:
        buffer = get_texture_buffer(context, dgraph, texture, objs_to_bake, eval_objs_to_bake, tex_width, tex_height, num_indices)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.unit_invert_v:
            buffer = get_inverted_buffer(buffer, tex_width, tex_height)

        success, msg, tex = generate_texture(texture.name, bake_name, settings.export_tex_file_name, buffer, tex_width, tex_height)
        if not success:
            clear_bake_selection(eval_objs_to_bake)

            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        report_texture = add_bake_texture_report(texture)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.export_tex and bpy.data.is_saved:
            success, msg, tex_path = export_texture(context, tex, settings.export_tex_file_path, settings.export_tex_file_name, texture.name, bake_name, settings.export_tex_override)
            if not success:
                clear_bake_selection(eval_objs_to_bake)

                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            edit_bake_texture_report_name(report_texture, tex_path)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

    ########
    # MESH #

    success, msg = post_process_bake_selection(context, eval_objs_to_bake, tex_width, tex_height)
    if not success:
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

##############
### BUFFER ###
def get_texture_buffer_function(texture_channel: object) -> callable:
    """
    Return the buffer function associated with the given texture channel

    :param texture_channel: texture channel to get bake function for
    :return: the buffer function to call for the given texture channel
    :rtype: callable function
    """
    if texture_channel.channel_mode == "POSITION":
        return texture_buffer_position
    elif texture_channel.channel_mode == "AXIS":
        return texture_buffer_axis
    elif texture_channel.channel_mode == "EXTENTS":
        return texture_buffer_extents
    elif texture_channel.channel_mode == "HIERARCHY":
        return texture_buffer_hierarchy
    else:
        pass

    return texture_buffer_zeros

def get_texture_buffer(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture: object, objs_to_bake: list, eval_objs_to_bake: list, tex_width: int, tex_height: int, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture RGBA channels

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param objs_to_bake: List of source objects (un-evaluated). Length & order must match eval_objs'
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :param tex_width: OA's texture width
    :param tex_height: OA's texture height
    :param attr_buffer_length: length of attribute buffer to create
    :return: buffer (one set of RGBA values per object)
    :rtype: list
    """
    buffer = [0.0] * tex_width * tex_height * 4 # RGBA
    
    texture_channels = [
        (texture.R if texture.R.channel_mode != "NONE" else None),
        (texture.G if texture.G.channel_mode != "NONE" else None),
        (texture.B if texture.B.channel_mode != "NONE" else None),
        (texture.A if texture.A.channel_mode != "NONE" else None),
        ]

    for texture_channel_index, texture_channel in enumerate(texture_channels):
        if texture_channel is None:
            continue

        pre_bake_func = get_texture_buffer_function(texture_channel)
        obj_attr_buffer = pre_bake_func(context, dgraph, texture_channel, objs_to_bake, eval_objs_to_bake, attr_buffer_length)
        if obj_attr_buffer:
            for attr_index in range(len(obj_attr_buffer)):
                buffer[(attr_index * 4) + texture_channel_index] = obj_attr_buffer[attr_index]

    return buffer

def get_inverted_buffer(buffer: list, tex_width: int, tex_height: int) -> list:
    """ 
    Re-order pixel buffer so that it is flipped in V (aka invert image). Append line of pixels after line in reverse order

    :param buffer: object attributes buffer
    :param tex_width: OA texture(s) width
    :param tex_height: OA texture(s) height
    :return: processed buffer
    :rtype: list
    """

    buffer_inv = []
    for i in reversed(range(tex_height)): # @NOTE performance & pythonify
        row = tex_width * 4
        row_offset = i * row
        buffer_inv.extend(buffer[row_offset:row_offset + row])

    return buffer_inv

def get_texture_buffer_obj_source_obj(texture_channel: object, eval_obj_to_bake: int, depth_limit_use: bool, depth_limit: int) -> bpy.types.Object:
    """
    Returns the object to get attributes from:
    - a user-specified mesh, defined in the texture_channel
    - the parent of the mesh, found in the provided list at the given index
    - the mesh itself, found in the provided list at the given index

    :param texture_channel: The texture channel currently being processed.
    :param eval_obj_to_bake: depsgraph-evaluated object to bake
    :param depth_limit_use: Enable to filter by hierarchy depth
    :param depth_limit: Allowed maximum hierarchy depth
    :return: the source object to use for retrieving its attributes (position, axis, etc.)
    :rtype: bpy.types.Object
    """

    if texture_channel.obj_mode == "CUSTOM" and texture_channel.obj:
        eval_obj_to_bake = texture_channel.obj
    elif texture_channel.obj_mode == "PARENT":
        depth = 0
        while eval_obj_to_bake and (depth < max(1, texture_channel.depth)):
            depth += 1
            if eval_obj_to_bake.parent:
                eval_obj_to_bake = eval_obj_to_bake.parent
            else:
                break

    if depth_limit_use and "ObjectAttributesHierarchyDepth" in eval_obj_to_bake:
        depth = eval_obj_to_bake["ObjectAttributesHierarchyDepth"]
        while eval_obj_to_bake and (depth >= max(1, depth_limit)): # @TODO test
            depth -= 1
            if eval_obj_to_bake.parent:
                eval_obj_to_bake = eval_obj_to_bake.parent
            else:
                break

    if "BakedSource" in eval_obj_to_bake:
        return eval_obj_to_bake["BakedSource"]
    else:
        return eval_obj_to_bake

########################
### BUFFER FUNCTIONS ###
def texture_buffer_position(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, objs_to_bake: list, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param objs_to_bake: List of source objects (un-evaluated). Length & order must match eval_objs'
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = eval_obj_source_mat @ settings.origin_obj.matrix_world.inverted()
        eval_obj_source_loc = eval_obj_source_mat.to_translation()

        vector_to_bake = eval_obj_source_loc * signed_scale

        if texture_channel.component == "X":
            data_to_bake = vector_to_bake.x
        elif texture_channel.component == "Y":
            data_to_bake = vector_to_bake.y
        elif texture_channel.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass
    
    return obj_attr_buffer

def texture_buffer_axis(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, objs_to_bake: list, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param objs_to_bake: List of source objects (un-evaluated). Length & order must match eval_objs'
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = eval_obj_source_mat @ settings.origin_obj.matrix_world.inverted()
        eval_obj_source_euler = eval_obj_source_mat.to_euler()

        if texture_channel.axis == "X":
            axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif texture_channel.axis == "Y":
            axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif texture_channel.axis == "Z":
            axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            axis = mathutils.Vector((0.0, 0.0, 0.0))

        axis.rotate(eval_obj_source_euler)
        vector_to_bake = axis * signed_axis

        if texture_channel.component == "X":
            data_to_bake = vector_to_bake.x
        elif texture_channel.component == "Y":
            data_to_bake = vector_to_bake.y
        elif texture_channel.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass
    
    return obj_attr_buffer

def texture_buffer_extents(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, objs_to_bake: list, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param objs_to_bake: List of source objects (un-evaluated). Length & order must match eval_objs'
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = eval_obj_source_mat @ settings.origin_obj.matrix_world.inverted()
        eval_obj_source_loc = eval_obj_source_mat.to_translation()
        eval_obj_source_euler = eval_obj_source_mat.to_euler()

        if texture_channel.axis == "X":
            axis = mathutils.Vector((1.0, 0.0, 0.0))
        elif texture_channel.axis == "Y":
            axis = mathutils.Vector((0.0, 1.0, 0.0))
        elif texture_channel.axis == "Z":
            axis = mathutils.Vector((0.0, 0.0, 1.0))
        else:
            axis = mathutils.Vector((0.0, 0.0, 0.0))

        axis.rotate(eval_obj_source_euler)
        extent_axis = axis * signed_axis

        eval_mesh_source = uneval_obj_source.to_mesh()
        vertices_delta = [(vertex.co - eval_obj_source_loc).dot(extent_axis) for vertex in eval_mesh_source.vertices] # @TODO this is probably wrong
        data_to_bake = abs(max(vertices_delta, key=abs))

        uneval_obj_source.to_mesh_clear()

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass

    return obj_attr_buffer

def texture_buffer_hierarchy(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, objs_to_bake: list, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param objs_to_bake: List of source objects (un-evaluated). Length & order must match eval_objs'
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake_index, eval_obj_to_bake in enumerate(eval_objs_to_bake):
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        parent_hierarchy_index = 0

        # try to reach desired parent to get its index
        parent = eval_obj_to_bake
        target_depth = max(1, texture_channel.depth)
        for depth in range(target_depth):
            
            if parent.parent:
                parent = parent.parent
                if "ObjectAttributesHierarchyIndex" in parent:
                    parent_hierarchy_index = parent["ObjectAttributesHierarchyIndex"]
            else:
                break

        if settings.use_pivot_painter_packing:
            parent_hierarchy_index = get_bitpacked_integer(parent_hierarchy_index)

        try:
            obj_attr_buffer[index] = parent_hierarchy_index
        except:
            pass

    return obj_attr_buffer

def texture_buffer_zeros(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, objs_to_bake: list, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param objs_to_bake: List of source objects (un-evaluated). Length & order must match eval_objs'
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :return: buffer, one value per object
    :rtype: list
    """
    obj_attr_buffer = [0.0] * attr_buffer_length

    return obj_attr_buffer

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
    settings = context.scene.ObjectAttributesSettings

    tags = { "BakeName" : bake_name}
    success, msg, export_path = get_path(settings.export_mesh_file_path, settings.export_mesh_file_name, ".fbx", tags, settings.export_mesh_file_override)
    if success:
        # export selection and assume selection was properly handled outside of this function
        bpy.ops.export_scene.fbx(filepath=export_path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    else:
        return (False, msg, None)

    return (True, "", export_path)

def filter_selection_depth(context: bpy.types.Context):
    """
    Configure the depth limit, select all objects to bake and press to deselect all objects that do *not* exceed the depth limit.\n\n
    These objects will be treated as if part of their last valid parent. This operator helps identify what will happen during the bake.

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    settings = context.scene.ObjectAttributesSettings

    for selected_obj in context.selected_objects:
        current_depth = 0
        if selected_obj.type != "MESH":
            selected_obj.select_set(False)
        elif len(selected_obj.data.vertices) <= 0: # mesh could have no vertices
            selected_obj.select_set(False)
        else:
            parent = selected_obj
            while parent:
                parent = parent.parent

                # @TODO account for non mesh?! only increment for meshes?
                if parent and parent.type == "MESH":
                    current_depth += 1
                else:
                    pass

            selected_obj.select_set(current_depth > settings.depth_limit)

    if len(context.selected_objects) <= 0:
        return (True, "INFO", "No mesh object exceed the depth limit")
    else:
        return (True, "INFO", str(len(context.selected_objects)) + " mesh object(s) exceed the depth limit")

################
### TEXTURES ###
def generate_texture(texture_name:str, bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate the object attributes image

    :param texture_name: the texture's name
    :param bake_name: the bake operation's 'name'
    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: object attributes image's width
    :param tex_height: object attributes image's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Attribute Buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename if filename != "" else "T_Bake_ObjectAttributes"
    tags = { "TextureName": texture_name, "BakeName": bake_name}
    image_name = replace_tags(image_name, tags)
    image_name += ".exr"

    image = bpy.data.images.get(image_name, None)
    if image is not None:
        if image.packed_file:
            image.unpack()
        bpy.data.images.remove(image) # remove image if it exists

    image = bpy.data.images.new(name=image_name, width=tex_width, height=tex_height, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.file_format = 'OPEN_EXR'
    image.use_half_precision = False
    image.pixels = buffer
    image.use_fake_user = True
    image.pack()

    return (True, "", image)

def export_texture(context: bpy.types.Context, image: bpy.types.Image, file_path: str, file_name: str, texture_name: str, bake_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the object attributes image

    :param context: Blender current execution context
    :param image: the object attributes image to export
    :param file_path: export path
    :param file_name: file name
    :param texture_name: texture name
    :param bake_name: the bake operation's 'name'
    :param override_file: if an existing .exr file should be overriden
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    tags = { "TextureName": texture_name, "BakeName": bake_name}
    success, msg, tex_path = get_path(file_path, file_name, ".exr", tags, override_file)
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

def get_best_texture_resolution(context: bpy.types.Context, num_indices: int) -> tuple[bool, str, int, int]:
    """
    Generate the best texture width and height based on a number of element indices (texels) to contain.
    This should result in a low-resolution square NPOT texture, unless the 'tex_force_power_of_two' option
    is on, in which case this may generate a non-square POT texture, unless the 'tex_force_power_of_two_square'
    option is on. A 256*256 resolution is likely to be the best upper limit as it allows the baking of up to
    65k elements, which is more than the precision offered by Pivot Painter's algorithm and more than you'd
    ever likely need.

    :param context: Blender current execution context
    :param num_indices: number of indices to bake
    """

    settings = context.scene.ObjectAttributesSettings

    if num_indices > (settings.export_tex_max_width * settings.export_tex_max_height):
        return (False, "Too many indices", 0, 0)
    elif num_indices == 1:
        return (True, "", 1, 1)
    elif num_indices <= 0:
        return (False, "Zero indices", 0, 0)

    sqrt_num_indices = math.sqrt(num_indices)

    #########
    # WIDTH #

    if (settings.tex_force_power_of_two):
        tex_width = 2
        while (tex_width < math.ceil(sqrt_num_indices) and tex_width < settings.export_tex_max_width):
            tex_width *= 2
    else:
        tex_width = math.ceil(sqrt_num_indices)
        if (tex_width > settings.export_tex_max_width):
            tex_width = settings.export_tex_max_width

    ##########
    # HEIGHT #

    if (settings.tex_force_power_of_two):
        tex_height = 2
        while (tex_height < tex_width):
            tex_height *= 2
    else:
        tex_height = math.ceil(num_indices / (tex_width))

    if tex_height > settings.export_tex_max_height:
         return (False, "Invalid Height", 0, 0)

    ##########

    if (settings.tex_force_power_of_two and settings.tex_force_power_of_two_square):
        if tex_width < tex_height:
            tex_width = tex_height
        elif tex_height < tex_width:
            tex_height = tex_width

    add_bake_report("tex_width", tex_width)
    add_bake_report("tex_height", tex_height)

    return (True, "", tex_width, tex_height)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """ """

    settings = context.scene.ObjectAttributesSettings
    report = context.scene.ObjectAttributesReport

    root = ET.Element("BakedData",
                      type="OA",
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

######################
### BAKE FUNCTIONS ###

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