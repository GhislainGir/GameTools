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
from ctypes import POINTER, pointer, c_int, c_uint, cast, c_float
import uuid
import bmesh
import xml.etree.ElementTree as ET

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################

##############
### REPORT ###
def new_bake_report(context: bpy.types.Context):
    """
    Clear the previous bake report, if any exists, and create a new one

    :param context: Blender current execution context
    :return: None
    :rtype: None
    """
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
    add_bake_report("unit_axis_order", settings.unit_axis_order)
    add_bake_report("origin_obj", settings.origin_obj)
    
    add_bake_report("depth_limit_use", settings.depth_limit_use)
    add_bake_report("depth_limit", settings.depth_limit)
    add_bake_report("use_pivot_painter_packing", settings.use_pivot_painter_packing)
    add_bake_report("use_8bit_packing", settings.use_8bit_packing)

def reset_bake_report():
    """
    Reset all properties stored in the bake report to their default values

    :return: None
    :rtype: None
    """
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
    report.unit_axis_order = "XYZ"
    report.origin_obj = None

    report.depth_limit_use = False
    report.depth_limit = 0
    report.use_pivot_painter_packing = False
    report.use_8bit_packing = False

    report.tex_width = 0
    report.tex_height = 0
    report.textures.clear()
    report.textures_selected_index = 0

    report.mesh = None
    report.mesh_uvmap_index = 0
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_num_indices = 0

    report.xml = False
    report.xml_path = ""

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """
    Assign a value to the property of the given name in the bake report

    :param prop_name: name of the property to set in the ObjectAttributesReport PropertyGroup
    :param prov_value: value to set
    :return: None
    :rtype: None
    """
    setattr(bpy.context.scene.ObjectAttributesReport, prop_name, prop_value)

def add_bake_texture_report(texture: object, img: bpy.types.Image, buffer_ranges_offsets: list, buffer_ranges: list, buffer_ranges_valid: list) -> object:
    """
    Create a new texture in the bake report

    :param texture: texture to generate report for
    :param img: image generated for baking
    :param buffer_ranges_offsets: min value. One value per RGBA channel
    :param buffer_ranges: range is describe as (max value - min value). One value per RGBA channel
    :param buffer_ranges_valid: true if range is valid, aka (max - min) is not null. One value per RGBA channel
    :return: the report texture object created
    :rtype: object
    """
    report = bpy.context.scene.ObjectAttributesReport

    report_texture = report.textures.add()
    report_texture.name = texture.name
    report_texture.exported = False
    report_texture.path = ""
    report_texture.img = img

    report_texture.R_range_offset = buffer_ranges_offsets[0]
    report_texture.R_range = buffer_ranges[0]
    report_texture.R_range_valid = buffer_ranges_valid[0]
    report_texture.G_range_offset = buffer_ranges_offsets[1]
    report_texture.G_range = buffer_ranges[1]
    report_texture.G_range_valid = buffer_ranges_valid[0]
    report_texture.B_range_offset = buffer_ranges_offsets[2]
    report_texture.B_range = buffer_ranges[2]
    report_texture.B_range_valid = buffer_ranges_valid[0]
    report_texture.A_range_offset = buffer_ranges_offsets[3]
    report_texture.A_range = buffer_ranges[3]
    report_texture.A_range_valid = buffer_ranges_valid[0]

    # copy all attributes
    if hasattr(texture, "__annotations__"):
        for prop_name in texture.__annotations__.keys():
            try:
                setattr(report_texture, prop_name, getattr(texture, prop_name))
            except (AttributeError, TypeError):
                pass

        channels = [texture.R, texture.G, texture.B, texture.A]
        report_channels = [report_texture.R, report_texture.G, report_texture.B, report_texture.A]
        for channel_index, channel in enumerate(channels):
            for prop_name in channel.__annotations__.keys():
                try:
                    setattr(report_channels[channel_index], prop_name, getattr(channels[channel_index], prop_name))
                except (AttributeError, TypeError):
                    pass

    return report_texture

def edit_bake_texture_report_prop(texture: object, value, prop_name: str) -> bool:
    """
    Edit a texture in the report to modify the value stored in a property of a given name

    :param texture: texture to edit in the report
    :param value: value to tweak
    :param prop_name: property to tweak in the report texture PropertyGroup
    :return: True if edited
    :rtype: bool
    """
    report = bpy.context.scene.ObjectAttributesReport
    
    for report_texture in report.textures:
        if report_texture == texture:
            setattr(report_texture, prop_name, value)
            return True

    return False

def edit_bake_texture_report_path(texture: object, path: str) -> bool:
    """
    Edit a texture in the report to modify its path
    
    :param texture: texture to edit in the report
    :param path: new path to set
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_texture_report_prop(texture, path, "path")

def edit_bake_texture_report_exported(texture: object, exported: bool):
    """
    Edit a texture in the report to modify its 'exported' status
    
    :param texture: texture to edit in the report
    :param exported: new 'exported' status
    :return: True if edited
    :rtype: bool
    """
    return edit_bake_texture_report_prop(texture, exported, "exported")

def clear_bake_texture_report(texture: object) -> bool:
    """
    Remove a texture from the report
    
    :param texture: texture to remove from the report
    :return: True if cleared/removed
    :rtype: bool
    """
    report = bpy.context.scene.ObjectAttributesReport
    
    for report_texture in report.textures:
        if report_texture == texture:
            report.textures.remove(report_texture)

    return True

def export_bake_report(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Manually export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """
    return(export_xml(context))

###############
### PACKING ###
def get_bitpacked_integer(index: int) -> float:
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
def get_bake_textures(context: bpy.types.Context) -> tuple[bool, str, list]:
    """
    Scan the textures the user wants to generate, ensuring each has a unique name and contains data in at least one of the RGBA channels.

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
    Filter out non-mesh objects from the active selection and ensure the selection leads to a valid bake, then return the list of objects to include in the bake and the active object, or root object of the first hierarchy if no active selection.

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
    Selected meshes may be duplicated, in which case the function generates and returns a list of all depsgraph-evaluated meshes to be included in the bake, while preserving parents & creating pointers to the original meshes.
    Selected meshes may be made single user if not duplicated, in which case their data blocks are simply copied.
    The resulting selection's hierarchy is then scanned to compute depth and create unique indices for each mesh, accounting for a hierarchy depth limitation that may have been set.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: the function's success, potential error message, list of duplicated depsgraph-evaluated mesh objects to include in the bake, num of unique indices to account for
    :rtype: tuple
    """

    settings = context.scene.ObjectAttributesSettings

    dgraph = bpy.context.evaluated_depsgraph_get()

    if not settings.mesh_duplicate:
        # naming isn't the best... objs are not evaluated here.
        eval_objs_to_bake = objs_to_bake

        if settings.mesh_single_user:
            for eval_obj_to_bake in eval_objs_to_bake:
                mesh_copy = eval_obj_to_bake.data.copy()
                eval_obj_to_bake.data = mesh_copy
    else:
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

    if element_index > 256 and (settings.use_8bit_packing and not settings.use_pivot_painter_packing):
        return (False, "There are more than 256 elements to bake. Indices can't be packed using 8-bit packing", eval_objs_to_bake, element_index)

    return (True, "", eval_objs_to_bake, element_index)

def post_process_bake_selection(context: bpy.types.Context, eval_objs_to_bake: list, tex_width: int, tex_height: int) -> tuple[bool, str]:
    """
    Baked meshes UVs are generated.
    Baked meshes may then be merged into a single mesh, if desired. This process involves duplicating selection & handling materials to create a single data block and object.
    The relevant meshes are then selected for export and the rest is cleaned.

    :param context: Blender current execution context
    :param eval_objs_to_bake: list of duplicated mesh objects included in the bake
    :param tex_width: the hierarchy texture's width
    :param tex_height: the hierarchy texture's height
    :return: the function's success and potential error message
    :rtype: tuple
    """
    settings = context.scene.ObjectAttributesSettings

    success, msg, uvmap_name = generate_mesh_uvs(eval_objs_to_bake, tex_width, tex_height, settings.mesh_uvmap_name, settings.unit_invert_v)
    if not success:
        return (False, msg)

    """
    process of merging involves copying data blocks in a single bmesh
    """
    if settings.mesh_merge:
        # get materials to copy (face material indices might have to be modified because of merging process)
        success, msg, materials = generate_mesh_material_indices(eval_objs_to_bake)
        if not success:
            return (False, msg)

        bm = bmesh.new()

        # add each transformed data block to bmesh
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_obj_to_bake.data.transform(eval_obj_to_bake.matrix_world)
            bm.from_mesh(eval_obj_to_bake.data)
            
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        # create new single data block from bmesh
        name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.OA"
        merged_mesh = bpy.data.meshes.new(name)
        bm.to_mesh(merged_mesh)
        bm.free()

        # create single object that uses new data block
        obj = bpy.data.objects.new(name, merged_mesh)
        context.scene.collection.objects.link(obj)
        add_bake_report("mesh", obj)

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

        if settings.mesh_materials and materials:
            # copy materials
            for material in materials:
                obj.data.materials.append(material)

        # report uv map used
        for uvlayer_index, uvlayer in enumerate(merged_mesh.uv_layers):
            if uvlayer.name == uvmap_name:
                add_bake_report("mesh_uvmap_index", uvlayer_index)
                merged_mesh.uv_layers.active_index = uvlayer_index
                uvlayer.active_render = True
                break

        # select object (for export) & make it active for user-feedback
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # clear original selection (we don't care if it was duplicated or not)
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

        # report uv map used
        for uvlayer_index, uvlayer in enumerate(obj_to_highlight.data.uv_layers):
            if uvlayer.name == uvmap_name:
                add_bake_report("mesh_uvmap_index", uvlayer_index)
                obj_to_highlight.uv_layers.active_index = uvlayer_index
                uvlayer.active_render = True
                break
    else:
        # select objects (for export)
        for eval_obj_to_bake in eval_objs_to_bake:
            eval_obj_to_bake.select_set(True)
            context.view_layer.objects.active = eval_obj_to_bake

    return (True, "")

def clear_bake_selection(eval_objs_to_bake: list) -> bool:
    """
    Clear the Blender file of the provided list of objects

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
    #bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

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
        if settings.mesh_duplicate:
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
        buffer, buffer_ranges_offsets, buffer_ranges, buffer_ranges_valid = get_texture_buffer(context, dgraph, texture, eval_objs_to_bake, tex_width, tex_height, num_indices)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.unit_invert_v:
            buffer = get_inverted_buffer(buffer, tex_width, tex_height)

        success, msg, tex = generate_texture(texture.name, bake_name, settings.export_tex_file_name, buffer, tex_width, tex_height)
        if not success:
            if settings.mesh_duplicate:
                clear_bake_selection(eval_objs_to_bake)

            add_bake_report("success", False)
            add_bake_report("msg", msg)
            return (False, 'ERROR', msg)
        report_texture = add_bake_texture_report(texture, tex, buffer_ranges_offsets, buffer_ranges, buffer_ranges_valid)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

        if settings.export_tex and bpy.data.is_saved:
            success, msg, tex_path = export_texture(context, tex, settings.export_tex_file_path, settings.export_tex_file_name, texture.name, bake_name, settings.export_tex_override)
            if not success:
                if settings.mesh_duplicate:
                    clear_bake_selection(eval_objs_to_bake)

                add_bake_report("success", False)
                add_bake_report("msg", msg)
                return (False, 'ERROR', msg)
            edit_bake_texture_report_path(report_texture, tex_path)
            edit_bake_texture_report_exported(report_texture, True)
        bake_progress += bake_progress_step
        wm.progress_update(bake_progress)

    ########
    # MESH #

    success, msg = post_process_bake_selection(context, eval_objs_to_bake, tex_width, tex_height)
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

##############
### BUFFER ###
def get_texture_buffer_function(texture_channel: object) -> callable:
    """
    Return the buffer function associated with the given texture channel's mode: position, axis, scale, etc.

    :param texture_channel: texture channel to get bake function for
    :return: the buffer function to call for the given texture channel
    :rtype: callable function
    """
    if texture_channel.channel_mode == "POSITION":
        return texture_buffer_position
    elif texture_channel.channel_mode == "AXIS":
        return texture_buffer_axis
    elif texture_channel.channel_mode == "SCALE":
        return texture_buffer_scale
    elif texture_channel.channel_mode == "EXTENTS":
        return texture_buffer_extents
    elif texture_channel.channel_mode == "HIERARCHY":
        return texture_buffer_hierarchy
    elif texture_channel.channel_mode == "CUSTOM_PROP":
        return texture_buffer_custom_prop
    elif texture_channel.channel_mode == "QUATERNION":
        return texture_buffer_quaternion
    else:
        pass

    return texture_buffer_zeros

def get_texture_buffer(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture: object, eval_objs_to_bake: list, tex_width: int, tex_height: int, attr_buffer_length: int) -> tuple[list, list, list, list]:
    """
    Intermediate buffer function to return the values to store in the texture RGBA channels

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
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

    buffer_ranges_offsets = [0.0] * 4
    buffer_ranges = [1.0] * 4
    buffer_ranges_valid = [False] * 4

    for texture_channel_index, texture_channel in enumerate(texture_channels):
        if texture_channel is None:
            continue

        pre_bake_func = get_texture_buffer_function(texture_channel)
        obj_attr_buffer = pre_bake_func(context, dgraph, texture_channel, eval_objs_to_bake, attr_buffer_length)
        if obj_attr_buffer:
            if get_texture_channel_allow_remap(texture_channel):
                buffer_min = min(obj_attr_buffer)
                buffer_max = max(obj_attr_buffer)
                if abs(buffer_max - buffer_min) < 0.0001:
                    buffer_range = 1.0
                else:
                    buffer_range = buffer_max - buffer_min
                    buffer_ranges_valid[texture_channel_index] = True
                buffer_offset = buffer_min

                buffer_ranges_offsets[texture_channel_index] = buffer_offset
                buffer_ranges[texture_channel_index] = buffer_range

                if texture_channel.remapping:
                    obj_attr_buffer = [((data - buffer_min) / buffer_range) for data in obj_attr_buffer]

            for attr_index in range(len(obj_attr_buffer)):
                try:
                    buffer[(attr_index * 4) + texture_channel_index] = obj_attr_buffer[attr_index]
                except:
                    break

    return (buffer, buffer_ranges_offsets, buffer_ranges, buffer_ranges_valid)

def get_inverted_buffer(buffer: list, tex_width: int, tex_height: int) -> list:
    """ 
    Re-order pixel buffer so that it is flipped in V (aka invert image). Append line of pixels after line in reverse order.
    Method can likely be pythonified and improved

    :param buffer: object attributes buffer
    :param tex_width: hierarchy texture's width
    :param tex_height: hierarchy texture's height
    :return: processed buffer
    :rtype: list
    """

    buffer_inv = []
    for i in reversed(range(tex_height)):
        row = tex_width * 4
        row_offset = i * row
        buffer_inv.extend(buffer[row_offset:row_offset + row])

    return buffer_inv

def get_texture_buffer_obj_source_obj(texture_channel: object, eval_obj_to_bake: int, depth_limit_use: bool, depth_limit: int, return_source: bool = True) -> bpy.types.Object:
    """
    Returns the object to get attributes from depending the texture channel's settings. This accounts for a hierarchy depth limit that may have been set (last valid parent will be used).
    Function returns the input object if unable to compute the source object, which may in various cases, for instance if the texture channel's object mode is set to 'Custom' and no custom object is specified

    :param texture_channel: The texture channel currently being processed.
    :param eval_obj_to_bake: object to get source for
    :param depth_limit_use: enable to filter by hierarchy depth
    :param depth_limit: allowed maximum hierarchy depth
    :param return_source: set to true to return the original object, if the computed source object do happen to point to one via its custom properties
    :return: the source object to use for retrieving its attributes (position, axis, scale, etc.)
    :rtype: bpy.types.Object
    """

    source_obj = None

    if texture_channel.obj_mode == "CUSTOM":
        if texture_channel.obj:
            source_obj = texture_channel.obj
    elif texture_channel.obj_mode == "PARENT":
        depth = 0
        source_obj = eval_obj_to_bake
        while source_obj and (depth < max(1, texture_channel.depth)):
            depth += 1
            if source_obj.parent:
                source_obj = source_obj.parent
            else:
                break
    elif texture_channel.obj_mode == "PROPERTY":
        if texture_channel.obj_prop != "" and texture_channel.obj_prop in eval_obj_to_bake:
            source_obj = eval_obj_to_bake[texture_channel.obj_prop]
    else:
        pass

    # fall back to itself
    if source_obj == None or not isinstance(source_obj, bpy.types.Object):
        source_obj = eval_obj_to_bake

    # if limiting depth, go up in the hierarchy to find first valid parent
    if depth_limit_use and "ObjectAttributesHierarchyDepth" in source_obj:
        depth = eval_obj_to_bake["ObjectAttributesHierarchyDepth"]
        source_obj = eval_obj_to_bake
        while source_obj and (depth > (depth_limit + 1)):
            depth -= 1
            if source_obj.parent:
                source_obj = source_obj.parent
            else:
                break

    # return original object if desired, or self
    if "BakedSource" in source_obj and return_source:
        return source_obj["BakedSource"]
    else:
        return source_obj

def get_texture_channel_allow_remap(texture_channel: object) -> bool:
    """
    Return true if texture channel may allow values to be remapped from range [-min:max] to [0:1] for potential storage in 8-bit RGBA texture(s)

    :param texture_channel: texture channel to validate statement for
    :return: true if channel can be safely remapped
    :rtype: bool
    """
    if texture_channel.channel_mode == "NONE":
        return False
    
    if texture_channel.channel_mode == "HIERARCHY": # indices must not be remapped!
        return False
    
    if texture_channel.channel_mode == "QUATERNION" and texture_channel.quat == "XYZW": # bit-packed quaternions don't allow remapping
        return False
    return True

########################
### BUFFER FUNCTIONS ###
def texture_buffer_position(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: list of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat
        eval_obj_source_loc = eval_obj_source_mat.to_translation()

        # output position relative to parent, if desired
        if texture_channel.reference_mode == "REL_PARENT" and uneval_obj_source.parent:
            eval_obj_source_parent = uneval_obj_source.parent.evaluated_get(dgraph)
            eval_obj_source_parent_mat = eval_obj_source_parent.matrix_world
            if settings.origin_obj:
                eval_obj_source_parent_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_parent_mat
            eval_obj_source_loc -= eval_obj_source_parent_mat.to_translation()

        vector_to_bake = eval_obj_source_loc * signed_scale
        if settings.unit_axis_order != "XYZ":
            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

        if texture_channel.component == "X":
            data_to_bake = vector_to_bake.x
        elif texture_channel.component == "Y":
            data_to_bake = vector_to_bake.y
        else: # Z
            data_to_bake = vector_to_bake.z

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass

    return obj_attr_buffer

def texture_buffer_axis(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: Number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat

        # output axis relative to parent, if desired
        if texture_channel.reference_mode == "REL_PARENT" and uneval_obj_source.parent:
            eval_obj_source_parent = uneval_obj_source.parent.evaluated_get(dgraph)
            eval_obj_source_parent_mat = eval_obj_source_parent.matrix_world
            if settings.origin_obj:
                eval_obj_source_parent_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_parent_mat
            eval_obj_source_mat = eval_obj_source_mat @ eval_obj_source_parent_mat.inverted()

        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                    (-1 if settings.unit_invert_y else 1),
                                                    (-1 if settings.unit_invert_z else 1), 1))
        eval_obj_source_mat = sign_matrix @ eval_obj_source_mat @ sign_matrix
        eval_obj_source_mat = eval_obj_source_mat.to_3x3()

        if texture_channel.axis == "X":
            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((1.0, 0.0, 0.0))
        elif texture_channel.axis == "Y":
            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((0.0, 1.0, 0.0))
        else: # Z
            vector_to_bake = eval_obj_source_mat @ mathutils.Vector((0.0, 0.0, 1.0))

        if settings.unit_axis_order != "XYZ":
            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

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

def texture_buffer_scale(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: List of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: Number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat
        eval_obj_source_scale = eval_obj_source_mat.to_scale()

        # output scale relative to parent, if desired
        if texture_channel.reference_mode == "REL_PARENT" and uneval_obj_source.parent:
            eval_obj_source_parent = uneval_obj_source.parent.evaluated_get(dgraph)
            eval_obj_source_parent_mat = eval_obj_source_parent.matrix_world
            if settings.origin_obj:
                eval_obj_source_parent_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_parent_mat
            eval_obj_source_parent_mat = eval_obj_source_parent_mat.to_scale()
            eval_obj_source_scale.x /= eval_obj_source_parent_mat.x
            eval_obj_source_scale.y /= eval_obj_source_parent_mat.y
            eval_obj_source_scale.z /= eval_obj_source_parent_mat.z

        # I think we want to skip inversion here. It doesn't make sense to output negative scale in Y by default for exporting to UE?
        vector_to_bake = eval_obj_source_scale # * signed_axis
        if settings.unit_axis_order != "XYZ":
            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

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

def texture_buffer_extents(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: list of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat

        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                     (-1 if settings.unit_invert_y else 1),
                                                     (-1 if settings.unit_invert_z else 1), 1))
        eval_obj_source_mat = sign_matrix @ eval_obj_source_mat @ sign_matrix

        if texture_channel.axis == "X":
            vector_to_bake = eval_obj_source_mat.to_3x3() @ mathutils.Vector((1.0, 0.0, 0.0))
        elif texture_channel.axis == "Y":
            vector_to_bake = eval_obj_source_mat.to_3x3() @ mathutils.Vector((0.0, 1.0, 0.0))
        else: # Z
            vector_to_bake = eval_obj_source_mat.to_3x3() @ mathutils.Vector((0.0, 0.0, 1.0))

        if settings.unit_axis_order != "XYZ":
            vector_to_bake = mathutils.Vector([getattr(vector_to_bake, axis.lower()) for axis in settings.unit_axis_order])

        eval_mesh_source = uneval_obj_source.to_mesh()
        eval_mesh_source.transform(eval_obj_source_mat)
        eval_obj_source_loc = eval_obj_source_mat.to_translation()
        vertices_delta = [((vertex.co - eval_obj_source_loc) * settings.unit_scale).dot(vector_to_bake) for vertex in eval_mesh_source.vertices]
        data_to_bake = abs(max(vertices_delta, key=abs))

        uneval_obj_source.to_mesh_clear()

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass

    return obj_attr_buffer

def texture_buffer_hierarchy(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: list of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        # get source (possibly apply max depth limit to get it)
        eval_obj_source = eval_obj_to_bake
        if settings.depth_limit_use and "ObjectAttributesHierarchyDepth" in eval_obj_source:
            depth = eval_obj_source["ObjectAttributesHierarchyDepth"]
            while eval_obj_source and (depth > (settings.depth_limit + 1)):
                depth -= 1
                if eval_obj_source.parent:
                    eval_obj_source = eval_obj_source.parent
                else:
                    break

        # walk up hierarchy from source to get parent at desired depth
        for depth in range(texture_channel.depth):
            if eval_obj_source.parent:
                eval_obj_source = eval_obj_source.parent
            else:
                break

        if "ObjectAttributesHierarchyIndex" in eval_obj_source:
            parent_hierarchy_index = eval_obj_source["ObjectAttributesHierarchyIndex"]
        else:
            continue

        if settings.use_pivot_painter_packing:
            parent_hierarchy_index = get_bitpacked_integer(parent_hierarchy_index)
        elif settings.use_8bit_packing:
            parent_hierarchy_index /= 255

        try:
            obj_attr_buffer[index] = parent_hierarchy_index
        except:
            pass

    return obj_attr_buffer

def texture_buffer_custom_prop(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: list of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)

        if texture_channel.custom_prop_mode == "OBJECT":
            if texture_channel.name != "" and texture_channel.name in eval_obj_source:
                custom_prop = eval_obj_source[texture_channel.name]
                if not isinstance(custom_prop, float) and not isinstance(custom_prop, int):
                    continue
            else:
                continue
        else: # MESH
            eval_mesh_source = eval_obj_source.to_mesh()
            if texture_channel.name != "" and texture_channel.name in eval_mesh_source:
                custom_prop = eval_mesh_source[texture_channel.name]
                if not isinstance(custom_prop, float) and not isinstance(custom_prop, int):
                    eval_obj_source.to_mesh_clear()
                    continue
            else:
                eval_obj_source.to_mesh_clear()
                continue

            eval_obj_source.to_mesh_clear()

        data_to_bake = custom_prop

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass

    return obj_attr_buffer

def texture_buffer_quaternion(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: list of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """
    settings = context.scene.ObjectAttributesSettings

    obj_attr_buffer = [0.0] * attr_buffer_length
    for eval_obj_to_bake in eval_objs_to_bake:
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)
        eval_obj_source_mat = eval_obj_source.matrix_world
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat

        # output axis relative to parent, if desired
        if texture_channel.reference_mode == "REL_PARENT" and uneval_obj_source.parent:
            eval_obj_source_parent = uneval_obj_source.parent.evaluated_get(dgraph)
            eval_obj_source_parent_mat = eval_obj_source_parent.matrix_world
            if settings.origin_obj:
                eval_obj_source_parent_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_parent_mat
            eval_obj_source_mat = eval_obj_source_mat @ eval_obj_source_parent_mat.inverted()

        sign_matrix = mathutils.Matrix.Diagonal(((-1 if settings.unit_invert_x else 1),
                                                     (-1 if settings.unit_invert_y else 1),
                                                     (-1 if settings.unit_invert_z else 1), 1))
        rot_matrix = sign_matrix @ eval_obj_source_mat @ sign_matrix

        xyz_order = texture_channel.quat_xyz_order if texture_channel.override_xyz_order else settings.unit_axis_order
        euler = rot_matrix.to_euler(xyz_order)

        eval_obj_source_quat = euler.to_quaternion()

        if texture_channel.quat == "X":
            data_to_bake = eval_obj_source_quat.x
        elif texture_channel.quat == "Y":
            data_to_bake = eval_obj_source_quat.y
        elif texture_channel.quat == "Z":
            data_to_bake = eval_obj_source_quat.z
        elif texture_channel.quat == "W":
            data_to_bake = eval_obj_source_quat.w
        elif texture_channel.quat == "XYZW":
            data_to_bake = get_compressed_quat(eval_obj_source_quat)
        else:
            data_to_bake = 0.0

        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass

    return obj_attr_buffer

def texture_buffer_zeros(context: bpy.types.Context, dgraph: bpy.types.Depsgraph, texture_channel: object, eval_objs_to_bake: list, attr_buffer_length: int) -> list:
    """
    Intermediate buffer function to return the values to store in the texture channel

    :param context: Blender current execution context
    :param dgraph: evaluated depsgraph
    :param texture_channel: texture channel to generate buffer for
    :param eval_objs_to_bake: list of duplicated objects (evaluated). Length & order must match source_objs'
    :param attr_buffer_length: number of unique indices to bake
    :return: buffer, one value per object
    :rtype: list
    """

    """
    # get settings
    settings = context.scene.ObjectAttributesSettings

    # account for unit sign & scale
    signed_axis = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0))
    signed_scale = signed_axis * settings.unit_scale
    """ 
    obj_attr_buffer = [0.0] * attr_buffer_length
    """
    for eval_obj_to_bake in eval_objs_to_bake:
        # get element buffer index
        if "ObjectAttributesHierarchyIndex" in eval_obj_to_bake:
            index = eval_obj_to_bake["ObjectAttributesHierarchyIndex"]
        else:
            continue

        # get element to target. Element was duplicated earlier in the bake process and has a 'BakeSource' custom object property pointing to the
        # original object. The texture channel may be configured to target a specific object rather than the 'eval_obj_to_bake', or even its parent
        # at a specific depth. This may be what you want, it might not, it just depends.
        get_original_object = True
        uneval_obj_source = get_texture_buffer_obj_source_obj(texture_channel, eval_obj_to_bake, settings.depth_limit_use, settings.depth_limit, get_original_object)
        
        # evaluate object (account for constraints, hierarchy etc.)
        eval_obj_source = uneval_obj_source.evaluated_get(dgraph)

        # get evaluated world matrix
        eval_obj_source_mat = eval_obj_source.matrix_world

        # make it relative to custom world origin if needed
        if settings.origin_obj:
            eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat
        eval_obj_source_loc = eval_obj_source_mat.to_translation()

        # output position relative to parent, if desired
        if texture_channel.reference_mode == "REL_PARENT" and uneval_obj_source.parent:
            eval_obj_source = uneval_obj_source.parent.evaluated_get(dgraph) # eval parent
            eval_obj_source_mat = eval_obj_source.matrix_world # get evaluated parent's world matrix
            if settings.origin_obj: # make parent relative to custom world origin if needed
                eval_obj_source_mat = settings.origin_obj.matrix_world.inverted() @ eval_obj_source_mat
            eval_obj_source_loc -= eval_obj_source_mat.to_translation() # make pos relative to parent pos

        # get location to bake, account for scale & sign
        vector_to_bake = eval_obj_source_loc * signed_scale

        # isolate X/Y/Z component
        if texture_channel.component == "X":
            data_to_bake = vector_to_bake.x
        elif texture_channel.component == "Y":
            data_to_bake = vector_to_bake.y
        elif texture_channel.component == "Z":
            data_to_bake = vector_to_bake.z
        else:
            data_to_bake = 0.0

        # write to buffer
        try:
            obj_attr_buffer[index] = data_to_bake
        except:
            pass
    """

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

def filter_selection_depth(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Filters the active selection to highlight objects that'd be depth-limited according to the current settings. Depth-limited objects behave as if they were an integral part of their parent.

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
                if parent and parent.type == "MESH":
                    current_depth += 1
                else:
                    pass

            selected_obj.select_set(current_depth > settings.depth_limit)

    if len(context.selected_objects) <= 0:
        return (True, "INFO", "No mesh object exceed the depth limit")
    else:
        return (True, "INFO", str(len(context.selected_objects)) + " mesh object(s) exceed the depth limit")

def generate_mesh_uvs(eval_objs_to_bake: list, tex_width: int, tex_height: int, uvmap_name: str, invert_v: bool) -> tuple[bool, str, str]:
    """
    Generate the vertex-to-texel uvmap for meshes to bake, given the texture's width and height
    
    :param eval_objs_to_bake:
    :param tex_width: hierarchy texture's width
    :param tex_height: hierarchy texture's height
    :param uvmap_name: name of the uvmap to look for, for storing the vertex-to-texel coordinates, or to create if not existing
    :param invert_v: true to flip the v axis to account for difference in direct-x/opengl oriented applications
    :return: the function's success, potential error message, name of uvmap generated
    :rtype: tuple
    """
    mesh_uvmap_name = uvmap_name if uvmap_name != "" else "UVMap.BakedData.OA"

    texel_size_x = (1.0 / tex_width)
    half_texel_size_x = texel_size_x * 0.5

    texel_size_y = (1.0 / tex_height)
    half_texel_size_y = texel_size_y * 0.5

    for eval_obj_to_bake in eval_objs_to_bake:
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
        if invert_v:
            v = 1.0 - v

        for loop_id in eval_obj_to_bake.data.loops:
            eval_obj_to_bake.data.uv_layers[uvmap_index].data[loop_id.index].uv = (u,v)

    return (True, "", mesh_uvmap_name)

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
                    
                material_index_source = poly.material_index
                material_index_merged = materials.index(material_source)
                if material_index_source != material_index_merged:
                    poly.material_index = material_index_merged
            except:
                poly.material_index = 0

    return (True, "", materials)

################
### TEXTURES ###
def generate_texture(texture_name: str, bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate the attributes image of given width and height to contain the provided buffer.

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

    image_name = filename
    tags = { "TextureName": texture_name, "BakeName": bake_name}
    image_name = replace_tags(image_name, tags)
    if image_name == "":
        return (True, "Invalid image name", None)

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

def export_texture(context: bpy.types.Context, image: bpy.types.Image, file_path: str, file_name: str, texture_name: str, bake_name: str, override_file: bool) -> tuple[bool, str, str]:
    """
    Export the attributes image

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
    
    This implementation differs from the original's Pivot Painter 2 function, as it was originally way too
    complicated. This simpler method seem to work but it has to be battle-tested.

    :param context: Blender current execution context
    :param num_indices: number of indices to bake
    :return: the function's success, potential error message, texture width, height
    :rtype: tuple
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
        while (tex_height < math.ceil(num_indices / tex_width)):
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
    """
    Export the bake report to XML

    :param context: Blender current execution context
    :return: the function's success, potential error message, export path
    :rtype: tuple
    """

    settings = context.scene.ObjectAttributesSettings
    report = context.scene.ObjectAttributesReport

    root = ET.Element("BakedData",
                      type="ObjectAttributes",
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

    # textures
    tex_el = ET.SubElement(root, "Textures",
                           width=str(report.tex_width),
                           height=str(report.tex_height))
    if report.textures:
        for texture in report.textures:
            tex_subel = ET.SubElement(tex_el, "Texture",
                                      name=texture.name,
                                      path=texture.path)

            channels = [
                (texture.R, "R", texture.R_range_offset, texture.R_range, texture.R_range_valid),
                (texture.G, "G", texture.G_range_offset, texture.G_range, texture.G_range_valid),
                (texture.B, "B", texture.B_range_offset, texture.B_range, texture.B_range_valid),
                (texture.A, "A", texture.A_range_offset, texture.A_range, texture.A_range_valid)
            ]
            for channel, channel_name, channel_range_offset, channel_range, channel_range_valid in channels:
                channel_remapped = channel.remapping and get_texture_channel_allow_remap(channel)
                channel_depth = channel.depth if channel.channel_mode == "HIERARCHY" or channel.obj_mode == "PARENT" else 1
                channel_el = ET.SubElement(tex_subel, channel_name,
                                           mode=channel.channel_mode,
                                           reference_mode=channel.reference_mode,
                                           component=channel.component,
                                           axis=channel.axis,
                                           quat=channel.quat,
                                           quat_axis_order=channel.quat_xyz_order if channel.override_xyz_order else report.unit_axis_order,
                                           depth=str(channel_depth),
                                           remapped=str(channel_remapped),
                                           range_offset=str(channel_range_offset),
                                           range=str(channel_range),
                                           range_valid=str(channel_range_valid))

    # depth
    depth_el = ET.SubElement(root, "Depth",
                             depth_limit_use=str(report.depth_limit_use),
                             depth_limit=str(report.depth_limit),
                             use_pivot_painter_packing=str(report.use_pivot_painter_packing),
                             use_8bit_packing=str(report.use_8bit_packing)
                             )

    # mesh info
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""

    mesh_el = ET.SubElement(root, "Mesh", path=mesh_export_path,
                            uv_index=str(report.mesh_uvmap_index),
                            num_elements=str(report.mesh_num_indices),
                            )

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