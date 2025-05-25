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
import bmesh
import math
import os
import sys
import mathutils
from mathutils.bvhtree import BVHTree
import xml.etree.ElementTree as ET
import uuid
import time

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################

############
### BAKE ###
def bake(context: bpy.types.Context) -> tuple[bool, str, str]:
    """
    Main bake function

    :param context: Blender current execution context
    :return: success, message verbose, message
    :rtype: tuple
    """
    #bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

    #settings = context.scene.BATBakerSettings
    wm = bpy.context.window_manager
    wm.progress_begin(0, 99)

    #############
    # BAKE INFO #
    
    bake_start_time = time.time()

    settings = context.scene.BATBakerSettings

    if len(bpy.context.selected_objects) <= 0:
        return (False, 'ERROR', "no selection")
    
    obj_to_bake = bpy.context.selected_objects[0]
    if obj_to_bake.type != "MESH":
        return (False, 'ERROR', "no mesh selected")
    
    # @TODO normalize weights on mesh

    num_vertices = len(obj_to_bake.data.vertices)
    if num_vertices <= 0:
        return (False, 'ERROR', "mesh has no verts")
    
    if num_vertices > 4096: # @TODO fix
        tex_width = num_vertices
        rows_per_frame = math.ceil(num_vertices / tex_width)
    else:
        if False: # force square
            tex_width = 2
            while tex_width < num_vertices and tex_width < 4096:
                tex_width *= 2
            rows_per_frame = math.ceil(num_vertices / tex_width)
        else:
            tex_width = num_vertices
            rows_per_frame = 1
    
    tex_height = rows_per_frame * 2

    armature_mods = [mod for mod in obj_to_bake.modifiers if mod.type == "ARMATURE"]
    if len(armature_mods) <= 0:
        return (False, 'ERROR', "no armature")
    
    armature = None
    for armature_mod in armature_mods:
        if (armature_mod.object and armature_mod.object.animation_data and armature_mod.object.animation_data.nla_tracks):
            armature = armature_mod.object

    if armature == None:
        return (False, 'ERROR', "no armature with NLA track")
    
    success, msg, uvmap_index = generate_mesh_uvs(context, obj_to_bake.data, tex_width, tex_height)
    if not success:
        return (False, 'ERROR', msg)
    
    success, msg, buffer, bones = get_bones_indices_weights_buffer(obj_to_bake, armature, tex_width, tex_height, 4)
    if not success:
        return (False, 'ERROR', msg)

    if True: # invert_v
        buffer = get_inverted_buffers(buffer, tex_width, tex_height)

    success, msg, tex = generate_texture("Bake", "mytexture.Bones", buffer, tex_width, tex_height)
    if not success:
        return (False, 'ERROR', msg)

    export_texture(context, tex, "//", "hierarchy", "texture_name", "bake_name", True)
    
    frames_to_bake = list(range(21))

    num_bones = len(bones)
    
    if num_bones <= 0:
        return (False, 'ERROR', "mesh has no verts")
    
    num_frames = len(frames_to_bake)
    if num_frames <= 0:
        return (False, 'ERROR', "no frames to bake")

    if num_bones > 4096:
        bone_tex_width = num_bones
        bone_rows_per_frame = math.ceil(num_bones / bone_tex_width)
    else:
        if False: # force square
            bone_tex_width = 2
            while bone_tex_width < num_bones and bone_tex_width < 4096:
                bone_tex_width *= 2
            bone_rows_per_frame = math.ceil(num_bones / bone_tex_width)
        else:
            bone_tex_width = num_bones
            bone_rows_per_frame = 1
    
    bone_tex_height = num_frames * rows_per_frame
    if bone_tex_height > 4096:
        return (False, 'ERROR', "too many frames to bake")

    success, msg, pos_buffer, rot_buffer, x_axis_buffer, y_axis_buffer, z_axis_buffer = get_bone_transform_buffer(context, armature, bones, frames_to_bake, bone_tex_width, bone_tex_height)
    if not success:
        return (False, 'ERROR', msg)

    if settings.unit_invert_v:
        pos_buffer = get_inverted_buffers(pos_buffer, bone_tex_width, bone_tex_height)

        if settings.rot_mode == "AXES":
            x_axis_buffer = get_inverted_buffers(x_axis_buffer, bone_tex_width, bone_tex_height)
            y_axis_buffer = get_inverted_buffers(y_axis_buffer, bone_tex_width, bone_tex_height)
            z_axis_buffer = get_inverted_buffers(z_axis_buffer, bone_tex_width, bone_tex_height)
        else:
            rot_buffer = get_inverted_buffers(rot_buffer, bone_tex_width, bone_tex_height)

    success, msg, tex = generate_texture("Bake", "mytexture.Bones.Pos", pos_buffer, bone_tex_width, bone_tex_height)
    if not success:
        return (False, 'ERROR', msg)
    
    export_texture(context, tex, "//", "pos", "texture_name", "bake_name", True)

    if settings.rot_mode == "AXES":
        success, msg, tex = generate_texture("Bake", "mytexture.Bones.AxesX", x_axis_buffer, bone_tex_width, bone_tex_height)
        if not success:
            return (False, 'ERROR', msg)
        
        export_texture(context, tex, "//", "x_axis", "texture_name", "bake_name", True)
        
        success, msg, tex = generate_texture("Bake", "mytexture.Bones.AxesY", y_axis_buffer, bone_tex_width, bone_tex_height)
        if not success:
            return (False, 'ERROR', msg)
        
        export_texture(context, tex, "//", "y_axis", "texture_name", "bake_name", True)

        success, msg, tex = generate_texture("Bake", "mytexture.Bones.AxesZ", z_axis_buffer, bone_tex_width, bone_tex_height)
        if not success:
            return (False, 'ERROR', msg)
        
        export_texture(context, tex, "//", "z_axis", "texture_name", "bake_name", True)
    else:
        success, msg, tex = generate_texture("Bake", "mytexture.Bones.Quat", rot_buffer, bone_tex_width, bone_tex_height)
        if not success:
            return (False, 'ERROR', msg)

        export_texture(context, tex, "//", "quat", "texture_name", "bake_name", True)

    return (True, 'INFO', "Baked operation completed in %0.1fs" % (time.time() - bake_start_time))

def get_bones_indices_weights_buffer(obj_to_bake: bpy.types.Object, armature: bpy.types.Armature, tex_width: int, tex_height: int, max_weights: int = 4):
    """ 
    """

    """
    1. output list of [vertex_index, [bone_index, bone_weight]]. Each vertex may list up to max_weights number of bone data
    """
    bones = []
    vertices_bones_indices_weights = []
    for vertex_index, vertex in enumerate(obj_to_bake.data.vertices):
        # sort vertex groups by weight, the one with the most weight one first
        vertex_groups = sorted(vertex.groups, key=lambda x: x.weight, reverse=True)

        # filter out least participating vertex groups
        vertex_groups = vertex_groups[0:max_weights]
        if vertex_index == 1500:
            for v in vertex_groups:
                print(obj_to_bake.vertex_groups[v.group].name)
                vertex.select = True

        # compute value to normalize the remaining vertex groups
        normalization_sum = sum([vertex_group.weight for vertex_group in vertex_groups])
        if normalization_sum > 0.0:
            normalization_factor = 1.0 / normalization_sum
        else:
            normalization_factor = 1.0

        # each vertex may have multiple bone indices & weights because of skinning
        bone_indices_weights = []
        for vertex_group in vertex_groups:
            # get name from vertex_groups stored at the object level, not the vertices ones!
            vertex_group_index = vertex_group.group
            vertex_group_name = obj_to_bake.vertex_groups[vertex_group_index].name

            # some bones might not deform etc. so make sure they are part of bones present in weight groups
            if vertex_group_name in armature.data.bones:
                # get bone
                bone = armature.data.bones[vertex_group_name]
                if not bone.use_deform: # skip non deforming bones
                    continue

                # get bone index
                if bone.name not in bones:
                    bones.append(bone.name)
                    bone_index = len(bones) - 1
                else:
                    bone_index = bones.index(bone.name)

                # get normalized bone weight
                bone_weight = vertex_group.weight * normalization_factor

                # create bone data buffer per vertex
                bone_indices_weights.append((bone_index, bone_weight))
        # append bone data buffer per vertex
        vertices_bones_indices_weights.append((vertex.index, bone_indices_weights))

    if len(bones) <= 0:
        return (False, "No bones", None, None)

    buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height
    buffer_half_size = (tex_width * tex_height * 4) // 2

    for vertex_bone_index_weight in vertices_bones_indices_weights:
        vertex_index, bone_info = vertex_bone_index_weight
        for bone_channel, bone_index_weight in enumerate(bone_info):
            bone_index, bone_weight = bone_index_weight

            buffer_index = (vertex_index * 4) + bone_channel
            buffer[buffer_index] = bone_index
            buffer[buffer_index + buffer_half_size] = bone_weight

    return (True, "", buffer, bones)

def get_bone_transform_buffer(context: bpy.types.Context, armature: bpy.types.Armature, bones: list, frames_to_bake: list, tex_width: int, tex_height: int):
    """ """
    settings = context.scene.BATBakerSettings
    
    signed_axis = mathutils.Vector((
        -1.0 if settings.unit_invert_x else 1.0,
        -1.0 if settings.unit_invert_y else 1.0,
        -1.0 if settings.unit_invert_z else 1.0
    ))
    signed_scale = settings.unit_scale * signed_axis

    """
    0. pre-allocate buffers
    """
    pos_buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height
    
    if settings.rot_mode == "AXES":
        x_axis_buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height
        y_axis_buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height
        z_axis_buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height

        rot_buffer = []
    else:
        x_axis_buffer = []
        y_axis_buffer = []
        z_axis_buffer = []

        rot_buffer = [0.0, 0.0, 0.0, 0.0] * tex_width * tex_height

    """
    1. cache bone matrices in reference pose
    """    
    ref_frame = min(frames_to_bake)
    ref_pose_bones = []

    bpy.context.scene.frame_set(ref_frame)
    dgraph = bpy.context.evaluated_depsgraph_get()
    eval_arm = armature.evaluated_get(dgraph)

    #bone_names = [bone.name for bone in bones]
    for bone in eval_arm.pose.bones:
        try:
            bone_index = bones.index(bone.name)
        except:
            continue

        ref_mat = eval_arm.matrix_world @ bone.matrix
        # if settings.unit_invert_x:
        #     flip_x = mathutils.Matrix.Scale(-1, 4, (1,0,0))
        #     ref_mat = flip_x @ ref_mat @ flip_x

        # if settings.unit_invert_y:
        #     flip_y = mathutils.Matrix.Scale(-1, 4, (0,1,0))
        #     ref_mat = flip_y @ ref_mat @ flip_y

        # if settings.unit_invert_z:
        #     flip_z = mathutils.Matrix.Scale(-1, 4, (0,0,1))
        #     ref_mat = flip_z @ ref_mat @ flip_z
        ref_pose_bones.append(ref_mat.copy())

    """
    2. iterate frames. Frame 0 is the ref pos and contains data in local space, subsequent frames are relative to ref pose
    """    
    rows_per_frame = math.ceil(len(bones) / tex_width)

    for frame_index, frame in enumerate(frames_to_bake):
        bpy.context.scene.frame_set(frame)
        dgraph = bpy.context.evaluated_depsgraph_get()
        eval_arm = armature.evaluated_get(dgraph)
        ref_pose = frame_index == 0

        for bone in eval_arm.pose.bones:
            try:
                bone_index = bones.index(bone.name)
            except:
                continue

            world_matrix = eval_arm.matrix_world @ bone.matrix
            # if settings.unit_invert_x:
            #     flip_x = mathutils.Matrix.Scale(-1, 4, (1,0,0))
            #     world_matrix = flip_x @ world_matrix @ flip_x

            # if settings.unit_invert_y:
            #     flip_y = mathutils.Matrix.Scale(-1, 4, (0,1,0))
            #     world_matrix = flip_y @ world_matrix @ flip_y

            # if settings.unit_invert_z:
            #     flip_z = mathutils.Matrix.Scale(-1, 4, (0,0,1))
            #     world_matrix = flip_z @ world_matrix @ flip_z

            if ref_pose:
                pos = world_matrix.to_translation() * signed_scale

                
                world_matrix = world_matrix.to_3x3()
                if settings.unit_invert_x:
                    flip_x = mathutils.Matrix.Scale(-1, 3, (1,0,0))
                    world_matrix = flip_x @ world_matrix @ flip_x

                if settings.unit_invert_y:
                    flip_y = mathutils.Matrix.Scale(-1, 3, (0,1,0))
                    world_matrix = flip_y @ world_matrix @ flip_y

                if settings.unit_invert_z:
                    flip_z = mathutils.Matrix.Scale(-1, 3, (0,0,1))
                    world_matrix = flip_z @ world_matrix @ flip_z

                quat = world_matrix.to_quaternion()
            else:
                #world_matrix = (world_matrix @ ref_pose_bones[bone_index].inverted()).to_translation # @TODO test
                pos = (world_matrix.to_translation() - ref_pose_bones[bone_index].to_translation()) * signed_scale
                #pos = (ref_pose_bones[bone_index].inverted() @ world_matrix).to_translation() * signed_scale
                

                #world_matrix = world_matrix.to_3x3()
                # if settings.unit_invert_x:
                #     flip_x = mathutils.Matrix.Scale(-1, 3, (1,0,0))
                #     world_matrix = flip_x @ world_matrix @ flip_x

                # if settings.unit_invert_y:
                #     flip_y = mathutils.Matrix.Scale(-1, 3, (0,1,0))
                #     world_matrix = flip_y @ world_matrix @ flip_y

                # if settings.unit_invert_z:
                #     flip_z = mathutils.Matrix.Scale(-1, 3, (0,0,1))
                #     world_matrix = flip_z @ world_matrix @ flip_z

                # ref_world_matrix = ref_pose_bones[bone_index].to_3x3()
                # if settings.unit_invert_x:
                #     flip_x = mathutils.Matrix.Scale(-1, 3, (1,0,0))
                #     ref_world_matrix = flip_x @ ref_world_matrix @ flip_x

                # if settings.unit_invert_y:
                #     flip_y = mathutils.Matrix.Scale(-1, 3, (0,1,0))
                #     ref_world_matrix = flip_y @ ref_world_matrix @ flip_y

                # if settings.unit_invert_z:
                #     flip_z = mathutils.Matrix.Scale(-1, 3, (0,0,1))
                #     ref_world_matrix = flip_z @ ref_world_matrix @ flip_z
                
                world_matrix = world_matrix.to_3x3() @ref_pose_bones[bone_index].to_3x3().inverted()

                
                #world_matrix = world_matrix.to_3x3()
                if settings.unit_invert_x:
                    flip_x = mathutils.Matrix.Scale(-1, 3, (1,0,0))
                    world_matrix = flip_x @ world_matrix @ flip_x

                if settings.unit_invert_y:
                    flip_y = mathutils.Matrix.Scale(-1, 3, (0,-1,0))
                    world_matrix = flip_y @ world_matrix @ flip_y

                if settings.unit_invert_z:
                    flip_z = mathutils.Matrix.Scale(-1, 3, (0,0,1))
                    world_matrix = flip_z @ world_matrix @ flip_z

                quat = world_matrix.to_quaternion()
                #quat = world_matrix.to_quaternion().rotation_difference(ref_world_matrix.to_quaternion())

            u = bone_index % tex_width
            v = math.floor(bone_index / tex_width)
            v += frame_index * rows_per_frame
            i = (u * 4) + (v * tex_width * 4)

            pos_buffer[i:i+3] = pos

            if settings.rot_mode == "QUAT":
                quat = quat.xyzw # @TODO test @TODO bitpack
                rot_buffer[i+4] = quat
            elif settings.rot_mode == "AXES": # @TODO this works
                world_matrix = world_matrix @ ref_pose_bones[bone_index].inverted() # @TODO test
                if settings.unit_invert_x:
                    flip_x = mathutils.Matrix.Scale(-1, 4, (1,0,0))
                    world_matrix = flip_x @ world_matrix @ flip_x

                if settings.unit_invert_y:
                    flip_y = mathutils.Matrix.Scale(-1, 4, (0,1,0))
                    world_matrix = flip_y @ world_matrix @ flip_y

                if settings.unit_invert_z:
                    flip_z = mathutils.Matrix.Scale(-1, 4, (0,0,1))
                    world_matrix = flip_z @ world_matrix @ flip_z

                euler = world_matrix.to_euler()

                x_axis = mathutils.Vector((1.0, 0.0, 0.0))
                x_axis.rotate(euler)
                x_axis_buffer[i:i+3] = x_axis

                y_axis = mathutils.Vector((0.0, -1.0, 0.0)) # @TODO inverted sign!
                y_axis.rotate(euler)
                y_axis_buffer[i:i+3] = y_axis

                z_axis = mathutils.Vector((0.0, 0.0, 1.0))
                z_axis.rotate(euler)
                z_axis_buffer[i:i+3] = z_axis
            else: # ANGLE_AXIS
                axis, angle = quat.to_axis_angle()
                rot_buffer[i:i+3] = axis

                if settings.quat_angle_unit_mode == "DEGREES":
                    angle *= (180/math.pi)
                elif settings.quat_angle_unit_mode == "UNIT":
                    angle *= (180/math.pi)
                    angle /= 360
                else: # RADIANS
                    pass

                rot_buffer[i+3] = angle

    return (True, "", pos_buffer, rot_buffer, x_axis_buffer, y_axis_buffer, z_axis_buffer)

def generate_mesh_uvs(context: bpy.types.Context, mesh: bpy.types.Mesh, tex_width: int, tex_height: int) -> tuple[bool, str, int]:
    """
    Configure the mesh UVs so that one vertex is located on one unique texel in the VAT texture(s)

    :param context: Blender current execution context
    :param mesh: mesh to edit
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :return: the function's success, potential error message, index of UVMap used to map the VAT texture(s)
    :rtype: tuple
    """

    #settings = context.scene.VATBakerSettings

    uvmap = None
    uvmap_index = 0
    #mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.VAT"
    invert_v = True

    # attempt to find existing UVMap
    for uvlayer_index, uvlayer in enumerate(mesh.uv_layers):
        #if uvlayer.name == mesh_uvmap_name:
        if uvlayer.name == "UVMap.BakedData.VAT":
            uvmap = uvlayer
            uvmap_index = uvlayer_index
            break

    # else create one, if possible
    if uvmap is None:
        if len(mesh.uv_layers) >= 8:
            return(False, "Too many existing uvmaps", -1)

        mesh.uv_layers.new()
        uvmap_index = len(mesh.uv_layers) - 1
        uvmap = mesh.uv_layers[uvmap_index]
        #uvmap.name = mesh_uvmap_name
        uvmap.name = "UVMap.BakedData.VAT"

    # set UV
    for loop in mesh.loops:
        vertex_index = loop.vertex_index
        u = (0.5 / float(tex_width)) + (vertex_index % tex_width) / float(tex_width)
        v = (0.5 / float(tex_height)) + (vertex_index // float(tex_width)) / float(tex_height)
        #if settings.unit_invert_y:
        if invert_v:
            v = 1.0 - v

        uvmap.data[loop.index].uv = (u,v)

    return (True, "", uvmap_index)

def generate_texture(bake_name: str, filename: str, buffer: list, tex_width: int, tex_height: int) -> tuple[bool, str, bpy.types.Image]:
    """
    Generate the offset or normal image

    :param bake_name: the bake operation's 'name'
    :param filename: the image's name
    :param buffer: RGBA pixel buffer
    :param tex_width: VAT image's width
    :param tex_height: VAT image's height
    :return: the function's success, potential error message, image
    :rtype: tuple
    """

    buffer_size = tex_width * tex_height * 4 # RGBA
    if ((len(buffer)) != buffer_size):
        return (False, "Vertex buffer has unexpected length: " + str(len(buffer)) + " vs " + str(buffer_size), None)

    image_name = filename if filename != "" else "T_Bake_VertOffsets"
    tags = { "BakeName": bake_name}
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

def get_inverted_buffers(buffer: list, tex_width: int, tex_height: int) -> tuple[list, list]:
    """ 
    Re-order vert buffers so that pixel buffer is flipped in V (aka invert image). Append line of pixels after line in reverse order. Method can likely be pythonified and improved

    :param buffer: buffer
    :param tex_width: VAT texture(s) width
    :param tex_height: VAT texture(s) height
    :return: processed offset buffer, processed normal buffer
    :rtype: tuple
    """

    buffer_inv = []
    for i in reversed(range(tex_height)):
        row = tex_width * 4
        row_offset = i * row
        buffer_inv.extend(buffer[row_offset:row_offset + row])

    return buffer_inv

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

# success, verbose, msg = bake(bpy.context)
# if not success:
#     print(msg)