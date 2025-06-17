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
import mathutils
import copy
import os
import random
import struct
import numpy as np

#from . import Properties
from .Properties import ProcessedTransform

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################
def get_bake_selection(context):
    """
    Modify & ensure the active & selected objects can lead to a valid bake and return the list of objects to include in the bake.

    :param context: Blender current execution context
    :return: success, additional message, list of objects to bake (filtered selection), active object
    :rtype: tuple
    """

    settings = context.scene.VATBakerSettings
    
    # proceed only if we have an active object
    if context.view_layer.objects.active == None:
        return (False, "No active object", None, None)

    # deselect all non-mesh
    for selected_obj in context.selected_objects:
        if selected_obj.type != "MESH":
            selected_obj.select_set(False)

    # double check selection after filter
    if not context.selected_objects:
        return (False, "No object selected once filtered out", None, None)
    
    # cache selection
    objs_to_bake = []
    if settings.bake_mode == 'ANIMATION':
        objs_to_bake = context.selected_objects
    else: # settings.bake_mode == 'MESHSEQUENCE'
        # sort by name to deduce 'frame order'
        names_of_objects_to_bake = [Object.name for Object in context.selected_objects]
        names_of_objects_to_bake.sort()

        for Name in names_of_objects_to_bake:
            objs_to_bake.append(context.scene.objects[Name])

    # check UVMap can be edited/created
    mesh_uvmap_name = settings.mesh_uvmap_name if settings.mesh_uvmap_name != "" else "UVMap.BakedData.VAT"
    if settings.bake_mode == 'ANIMATION':
        uvmaps = []
        # ensure objects can safely be merged without creating UVMap conflicts
        for obj_to_bake in objs_to_bake:
            # if we can NOT find target UVMap name in existing uvmaps, we'll need to create one
            if mesh_uvmap_name not in [uvlayer.name for uvlayer in obj_to_bake.data.uv_layers]:
                if len(obj_to_bake.data.uv_layers) >= 8:
                    return (False, obj_to_bake.name + " has the maximum amount of uvmaps already", None, None)

            # gather uvmaps as if objects were joined
            for uvlayer in obj_to_bake.data.uv_layers:
                if uvlayer.name not in uvmaps:
                    uvmaps.append(uvlayer.name)

        # if we can NOT find target UVMap name in all existing uvmaps, we'll need to create one
        if mesh_uvmap_name not in uvmaps and len(uvmaps) >= 8:
            return (False, "Joined mesh is projected to have more than the maximum amount of uvmaps", None, None)
    else: # settings.bake_mode == 'MESHSEQUENCE'
        ref_eval_obj = objs_to_bake[0]
        # if we can NOT find target UVMap name in existing uvmaps, we'll need to create one
        if mesh_uvmap_name not in [uvlayer.name for uvlayer in ref_eval_obj.data.uv_layers]:
            if len(ref_eval_obj.data.uv_layers) >= 8:
                return (False, ref_eval_obj.name + " has the maximum amount of uvmaps already", None, None)

    # deselect objects for now
    for obj_to_bake in objs_to_bake:
        obj_to_bake.select_set(False)

    active_object = context.view_layer.objects.active
    if settings.bake_mode == 'MESHSEQUENCE':
        active_object = objs_to_bake[0]

    context.view_layer.objects.active = None # blank canvas

    return (True, "", objs_to_bake, active_object)

def get_bake_frames(context, objs_to_bake):
    """
    Return the list of frames to bake and the resulting frame time.

    :param context: Blender current execution context
    :param objs_to_bake: list of objects to bake
    :return: success, additional message, list of frames in order, frame time
    :rtype: tuple
    """

    scene = context.scene
    settings = scene.OATBakerSettings

    Frames = []

    if settings.bake_mode == 'ANIMATION':
        # nla mode
        if (settings.frame_range_mode == "NLA"):
            Start = -1
            End = -1
            
            for Object in objs_to_bake:
                Tracks = []
                # check if object itself has an nla track
                if (Object and Object.animation_data and Object.animation_data.nla_tracks):
                    Tracks = Object.animation_data.nla_tracks
                # else, check if object is parented to an armature that has an nla track
                elif (Object.parent and Object.parent.type == "ARMATURE"):
                    if (Object.parent.animation_data and Object.parent.animation_data.nla_tracks):
                        Tracks = Object.parent.animation_data.nla_tracks
            
                for Track in Tracks:
                    for Strip in Track.strips:
                        nla_strip_frame_start = int(Strip.frame_start)
                        nla_strip_frame_end = int(Strip.frame_end)

                        Start = nla_strip_frame_start if Start < 0 else min(Start, nla_strip_frame_start)
                        End = nla_strip_frame_end if End < 0 else max(End, nla_strip_frame_end)
                    
                        for Frame in range(nla_strip_frame_start, nla_strip_frame_end + 1, settings.frame_range_custom_step):
                            if Frame not in Frames:
                                print(Frame)
                                Frames.append(Frame)
            
            Frames.sort()
        # custom mode
        elif (settings.frame_range_mode == "CUSTOM"):
            Start = settings.frame_range_custom_start
            End = settings.frame_range_custom_end
            Frames.extend(range(Start, End + 1, settings.frame_range_custom_step))
        # scene mode
        else:
            Start = scene.frame_start
            End = scene.frame_end
            Frames.extend(range(Start, End + 1, scene.frame_step))
    else: # settings.bake_mode == 'MESHSEQUENCE'
        # naïve object count, one frame per object @NOTE pythonify
        Frames = list(range(len(objs_to_bake)))

    # range checks
    num_frames = len(Frames)
    if num_frames < 2:
        return (False, str(num_frames) + " frames detected: too small of a range or no animation data found from NLA track", Frames, 1.0)
    
    # don't include optional rest pose frame
    if settings.SkipFirstFrame:
        Frames.pop()
        num_frames = len(Frames)

    # deduce how much 'one second' needs to be scaled down to equal 'one frame' (to be exported in XML & used in shader)
    FrameTime = (1/float(num_frames)) * scene.render.fps

    return (True, "", Frames, FrameTime)

def get_bake_name(context: bpy.types.Context, active_object: bpy.types.Object) -> str:
    """
    Return the name to give to the bake operation.

    :param context: Blender current execution context
    :param active_object: active object
    :return: the name
    :rtype: string
    """

    settings = context.scene.VATBakerSettings

    Name = settings.mesh_name if settings.mesh_name != "" else "BakedMesh.OAT"
    Tags = { "BakeName":active_object.name if active_object is not None else ""}
    return replace_tags(Name, Tags)

def bake(context):
    """ Main bake function """

    settings = context.scene.OATBakerSettings

    # we need to be in object mode
    bpy.ops.object.mode_set(mode="OBJECT") # @NOTE necessary? it fails when there's no active selection anyway

    #############
    # BAKE INFO #

    success, msg, objs_to_bake, active_object = get_bake_selection(context)
    if not success:
        return (False, 'ERROR', msg)
    
    success, msg, Frames, FrameTime = get_bake_frames(context, objs_to_bake)
    if not success:
        return (False, 'ERROR', msg)

    num_frames = len(Frames)
    num_objs = len(objs_to_bake)

    success, msg, tex_width, tex_height = get_best_texture_resolution(num_frames, num_objs, settings.export_tex_max_width, settings.export_tex_max_height, settings.tex_force_power_of_two, settings.tex_force_power_of_two_square)
    if not success:
        return (False, 'ERROR', msg)

    Name = get_bake_name(context, active_object)

    ##############
    ##############
    ##############
    ##############
    # get sanitized animation settings
    FrameStart = max(0, context.scene.frame_start)
    FrameEnd   = max(0, context.scene.frame_end + (1 if settings.bIncludeLastFrame else 0))
    FrameStep  = max(1, context.scene.frame_step)

    # cache animation's original frame rate
    settings.AnimFrameRate = context.scene.render.fps / context.scene.render.fps_base

    # cache number of frames to 'sample' from the animation
    settings.AnimFrames = max(1, math.ceil((FrameEnd - FrameStart) / FrameStep))
    if settings.AnimFrames > 4096:
        return (False, "Too many frames")

    # cache number of frames to bake into the texture (may differ from the number of samples to result in a power-of-two sized texture)
    settings.AnimFramesTex = 1
    while (settings.AnimFramesTex < settings.AnimFrames and settings.AnimFramesTex < 4096):
        settings.AnimFramesTex *= 2

    # cache animation duration in seconds
    settings.AnimDuration = settings.AnimFrames / settings.AnimFrameRate

    # cache ratio between sampled frames & baked frames (we likely have fewer sampled frames than baked frames, unless sample count is a power of two to begin with)
    settings.AnimDurationRatio = settings.AnimFrames / settings.AnimFramesTex

    # cache anim speed multiplier (that's how much Time in UE need to be multiplied to result in the same animation speed as seen in Blender)
    settings.AnimSpeed = 1.0 / (settings.AnimDuration * settings.AnimDurationRatio)
    ##############
    ##############
    ##############
    ##############


    ###########
    # BUFFERS #

    Buffer = GetInterpolatedWorldMatrixBuffer(context, Frames)

    success, msg = PostProcessSelection(context)
    if not success:
        return (False, 'ERROR', msg)
    
    if settings.FirstTexture:
        Pixels = GetPixelBuffer(context, 0, Buffer)
        Image, ImageName = CreateTexture(context, 0, Pixels)
        if settings.TexAutoExport:
            export_texture(context, Image, ImageName)

    if settings.SecondTexture:
        Pixels = GetPixelBuffer(context, 1, Buffer)
        Image, ImageName = CreateTexture(context, 1, Pixels)
        if settings.TexAutoExport:
            export_texture(context, Image, ImageName)

    if settings.ThirdTexture:
        Pixels = GetPixelBuffer(context, 2, Buffer)
        Image, ImageName = CreateTexture(context, 2, Pixels)
        if settings.TexAutoExport:
            export_texture(context, Image, ImageName)

    return (True, 'SUCCESS', "")

##########
# BUFFER #
##########
def GetObjectMatrixBuffer(context, Object, Frames):
    """ """

    dgraph = context.evaluated_depsgraph_get()

    Matrices = [] # @NOTE preallocate?

    for FrameIndex, Frame in enumerate(Frames):
        context.scene.frame_set(Frame)
        #context.view_layer.update()
        
        eval_obj = Object.evaluated_get(dgraph)
        Matrices.append(eval_obj.matrix_world.copy())
        # Matrices.append(copy.deepcopy(eval_obj.matrix_world)) # @NOTE is deepcopy required?

    return Matrices


def GetWorldMatrixBuffer(context, Frames, objs_to_bake):
    ''' Loop through frames & selected mesh objects to create a buffer of 4x4 transform matrix to bake '''

    settings = context.scene.OATBakerSettings

    signed_scale = mathutils.Vector((-1.0 if settings.unit_invert_x else 1.0,
                                    -1.0 if settings.unit_invert_y else 1.0,
                                    -1.0 if settings.unit_invert_z else 1.0)) * settings.unit_scale

    # buffer in the following order: obj1 frame1, obj1 frame2, obj1 frame3, obj2 frame1, obj2 frame 2, obj3, frame3...
    #MatrixBuffer = [mathutils.Matrix()] * settings.AnimObjects * settings.AnimFrames
    MatrixBuffer = [] # @NOTE preallocate?

    # get user-set origin, if any
    Origin = mathutils.Vector((0.0, 0.0, 0.0))
    OriginMatrix = mathutils.Matrix()
    if settings.origin is not None:
        Origin = settings.origin.matrix_world.to_translation() * -1.0 # inverted position
        OriginMatrix = mathutils.Matrix.Translation(Origin)

    for FrameIndex, Frame in enumerate(Frames):
        context.scene.frame_set(Frame)
        #context.view_layer.update()

        for obj_index, Object in enumerate(objs_to_bake): # @TODO evaluate object?! cache dimensions/bounds to avoid later expensive per-vertex bounds computation
            ObjectMatrix = copy.deepcopy(Object.matrix_world) # @NOTE is deepcopy required?

            BufferIndex = (obj_index * settings.AnimFrames) + FrameIndex
            MatrixBuffer[BufferIndex] = OriginMatrix @ ObjectMatrix

    return MatrixBuffer

def GetInterpolatedWorldMatrixBuffer(context, Frames, objs_to_bake):
    ''' Loop through frames & selected mesh objects to first get their world matrix transform. Then convert each matrix into a position/rotation/scale that is linearly interpolated to support in-between frames. That may be necessary when baking a 100 frames-long animation into a 128px texture '''
    
    settings = context.scene.OATBakerSettings

    # initiate buffer
    BufferIndex = 0
    BufferLength = settings.AnimObjectsTex * settings.AnimFramesTex
    MatrixBuffer = [mathutils.Matrix()] * BufferLength
    
    # clear bounds & normalization values #
    settings.bPositionNormalized = False
    settings.MaxPosition = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    settings.bScaleNormalized = False
    settings.MaxScale = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    settings.bMinBounds = False
    settings.MinBounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    settings.MinBaseBounds = mathutils.Vector((float('inf'), float('inf'), float('inf')))

    settings.bMaxBounds = False
    settings.MaxBounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
    settings.MaxBaseBounds = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    BoundsOffset = (
                    mathutils.Vector((1.0, 1.0, 1.0)),
                    mathutils.Vector((1.0, 1.0, -1.0)),
                    mathutils.Vector((1.0, -1.0, 1.0)),
                    mathutils.Vector((1.0, -1.0, -1.0)),
                    mathutils.Vector((-1.0, 1.0, 1.0)),
                    mathutils.Vector((-1.0, 1.0, -1.0)),
                    mathutils.Vector((-1.0, -1.0, 1.0)),
                    mathutils.Vector((-1.0, -1.0, -1.0)),
                )

    # get per-frame per-object matrix buffer
    WorldMatrixBuffer = GetWorldMatrixBuffer(context, Frames, objs_to_bake)

    # for each object
    obj_index = 0
    for Object in context.selected_objects:
        if Object.type != "MESH": continue

        ################
        # LOCAL BOUNDS #
        ObjectBounds = Object.dimensions * 0.5
        ObjectScale = Object.matrix_world.to_scale()
        
        ObjectLocalBounds = copy.deepcopy(ObjectBounds)
        ObjectLocalBounds.x = ObjectBounds.x if ObjectScale.x == 0 else ObjectBounds.x / ObjectScale.x
        ObjectLocalBounds.y = ObjectBounds.y if ObjectScale.y == 0 else ObjectBounds.x / ObjectScale.y
        ObjectLocalBounds.z = ObjectBounds.z if ObjectScale.z == 0 else ObjectBounds.x / ObjectScale.z
    
        settings.MinBaseBounds.x = min(settings.MinBaseBounds.x, ObjectLocalBounds.x)
        settings.MinBaseBounds.y = min(settings.MinBaseBounds.y, ObjectLocalBounds.y)
        settings.MinBaseBounds.z = min(settings.MinBaseBounds.z, ObjectLocalBounds.z)

        settings.MaxBaseBounds.x = max(settings.MaxBaseBounds.x, ObjectLocalBounds.x)
        settings.MaxBaseBounds.y = max(settings.MaxBaseBounds.y, ObjectLocalBounds.y)
        settings.MaxBaseBounds.z = max(settings.MaxBaseBounds.z, ObjectLocalBounds.z)
        # LOCAL BOUNDS #
        ################

        # for each frame to bake in the texture (likely differs from amount of frames in the original animation)
        for FrameIndex in range(settings.AnimFramesTex):
            # compute frame A, B, T for interpolation
            Time = FrameIndex * settings.AnimDurationRatio
            FrameA = min(settings.AnimFrames - 1, math.floor(Time))
            FrameB = min(settings.AnimFrames - 1, math.ceil(Time))
            FrameTime = math.modf(Time)[0] # fractional part

            # get matrix A & B
            BufferOffset = obj_index * settings.AnimFrames
            ObjectMatrixA = WorldMatrixBuffer[BufferOffset + FrameA]
            ObjectMatrixB = WorldMatrixBuffer[BufferOffset + FrameB]

            # interpolate matrices
            InterpolatedObjectMatrix = mathutils.Matrix.lerp(ObjectMatrixA, ObjectMatrixB, FrameTime)
            MatrixBuffer[BufferIndex] = ObjectMatrixA # @todo revert this
            BufferIndex += 1

            ##########
            # BOUNDS #
            if settings.bAccurateBounds: # @slow
                for Vertex in Object.data.vertices:
                    VertexPosition = InterpolatedObjectMatrix @ Vertex.co

                    settings.MinBounds.x = min(settings.MinBounds.x, VertexPosition.x)
                    settings.MinBounds.y = min(settings.MinBounds.y, VertexPosition.y)
                    settings.MinBounds.z = min(settings.MinBounds.z, VertexPosition.z)

                    settings.MaxBounds.x = max(settings.MaxBounds.x, VertexPosition.x)
                    settings.MaxBounds.y = max(settings.MaxBounds.y, VertexPosition.y)
                    settings.MaxBounds.z = max(settings.MaxBounds.z, VertexPosition.z)
            # only loop through bounding box's 8 vertices to compute cheaper conservative transformed bounding box
            else:
                for BoundOffset in BoundsOffset:
                    VertexPosition = InterpolatedObjectMatrix @ (Object.dimensions * 0.5 * BoundOffset)

                    settings.MinBounds.x = min(settings.MinBounds.x, VertexPosition.x)
                    settings.MinBounds.y = min(settings.MinBounds.y, VertexPosition.y)
                    settings.MinBounds.z = min(settings.MinBounds.z, VertexPosition.z)

                    settings.MaxBounds.x = max(settings.MaxBounds.x, VertexPosition.x)
                    settings.MaxBounds.y = max(settings.MaxBounds.y, VertexPosition.y)
                    settings.MaxBounds.z = max(settings.MaxBounds.z, VertexPosition.z)
            # BOUNDS #
            ##########

            ###############
            # NORMALIZATION
            ObjectLocation = InterpolatedObjectMatrix.to_translation()
            settings.MaxPosition.x = max(settings.MaxPosition.x, abs(ObjectLocation.x))
            settings.MaxPosition.y = max(settings.MaxPosition.y, abs(ObjectLocation.y))
            settings.MaxPosition.z = max(settings.MaxPosition.z, abs(ObjectLocation.z))

            ObjectScale = InterpolatedObjectMatrix.to_scale()
            settings.MaxScale.x = max(settings.MaxScale.x, abs(ObjectScale.x))
            settings.MaxScale.y = max(settings.MaxScale.y, abs(ObjectScale.y))
            settings.MaxScale.z = max(settings.MaxScale.z, abs(ObjectScale.z))
            # NORMALIZATION
            ###############

        obj_index += 1

    #####################################
    # set bounds & normalization values #
    settings.bPositionNormalized = settings.NormalizePosition
    settings.bScaleNormalized = settings.NormalizeScale

    settings.bMinBounds = True
    settings.bMaxBounds = True
    # set bounds & normalization values #
    #####################################

    ##########
    # BOUNDS #
    ##########
    # display bounds?
    if settings.bPrevizBounds:
        display_bounds("ObjAnimBounds", settings.MinBounds, settings.MaxBounds)

    # compute bounds offset (that needs to be added in UE)
    settings.MinOffsetBounds = settings.MinBounds - settings.MinBaseBounds
    settings.MaxOffsetBounds = settings.MaxBounds - settings.MaxBaseBounds

    if True: # @todo expose absolute setting? but likely always true for UE... (min bounds are positive)
        settings.MinOffsetBounds.x = abs(settings.MinOffsetBounds.x)
        settings.MinOffsetBounds.y = abs(settings.MinOffsetBounds.y)
        settings.MinOffsetBounds.z = abs(settings.MinOffsetBounds.z)

        settings.MaxOffsetBounds.x = abs(settings.MaxOffsetBounds.x)
        settings.MaxOffsetBounds.y = abs(settings.MaxOffsetBounds.y)
        settings.MaxOffsetBounds.z = abs(settings.MaxOffsetBounds.z)

    # apply scale (m to cm by default)
    settings.MinOffsetBounds *= settings.unit_scale
    settings.MaxOffsetBounds *= settings.unit_scale

    return MatrixBuffer

def GetPixelBuffer(context, Index, WorldMatrixBuffer):
    ''' '''
    # get settings
    settings = context.scene.OATBakerSettings

    # get texture channel settings
    if Index == 0:
        R = settings.FirstTextureR
        G = settings.FirstTextureG
        B = settings.FirstTextureB
        A = settings.FirstTextureA
    elif Index == 1:
        R = settings.SecondTextureR
        G = settings.SecondTextureG
        B = settings.SecondTextureB
        A = settings.SecondTextureA
    else: # >1
        R = settings.ThirdTextureR
        G = settings.ThirdTextureG
        B = settings.ThirdTextureB
        A = settings.ThirdTextureA

    # see what kind of transform we need to convert to pixels
    bPosition = R == "PosX" or G == "PosY" or B == "PosZ"
    bRotation = R == "QuatX" or G == "QuatY" or B == "QuatZ" or A == "QuatA" or A == "Quat"
    bScale = R == "ScaleX" or G == "ScaleY" or B == "ScaleZ" or A == "Scale"

    tex_width = settings.AnimObjectsTex
    tex_height = settings.AnimFramesTex

    # pre allocate RGBA pixel buffer
    buffer_size = tex_width * tex_height
    Pixels = [0.0, 0.0, 0.0, 1.0] * buffer_size
    PixelIndex = 0

    # loop through pixels (row per row!)
    for Y in range(tex_height):
        for X in range(tex_width):
            # need to re-order index @todo
            BufferIndex = (tex_height - 1 - Y) + (X * tex_height)
            if BufferIndex < len(WorldMatrixBuffer):
                if bPosition:
                    Position = WorldMatrixBuffer[BufferIndex].to_translation()
                    Position.y *= -1.0 # flip y axis!
                    
                    if settings.NormalizePosition:
                        if settings.MaxPosition.x > 0:
                            Position.x = ((Position.x / settings.MaxPosition.x) * 0.5) + 0.5
                        else:
                            Position.x = 0.0
                        if settings.MaxPosition.y > 0:
                            Position.y = ((Position.y / settings.MaxPosition.y) * 0.5) + 0.5 # flip Y axis
                        else:
                            Position.y = 0.0
                        if settings.MaxPosition.z > 0:
                            Position.z = ((Position.z / settings.MaxPosition.z) * 0.5) + 0.5
                        else:
                            Position.z = 0.0
                    else: # 16 or 32bits can use real values!
                        Position = Position * settings.unit_scale

                if bRotation:
                    Quaternion = WorldMatrixBuffer[BufferIndex].to_quaternion()

                    QuaternionAxis = Quaternion.axis
                    QuaternionAxis.y *= -1.0 # flip Y axis

                    QuaternionAngle = Quaternion.angle
                    #Quaternion = mathutils.Quaternion(QuaternionAxis, QuaternionAngle)
                    QuaternionAngle *= -0.15915494309 # div by TWO PIs

                    if settings.NormalizeQuaternion:
                        QuaternionAxis.x = (QuaternionAxis.x * 0.5) + 0.5
                        QuaternionAxis.y = (QuaternionAxis.y * 0.5) + 0.5
                        QuaternionAxis.z = (QuaternionAxis.z * 0.5) + 0.5

                        QuaternionAngle  = (QuaternionAngle * 0.5) + 0.5

                if bScale:
                    Scale = WorldMatrixBuffer[BufferIndex].to_scale()
                
                    if settings.NormalizeScale:
                        if settings.MaxScale.x > 0.0:
                            Scale.x = ((Scale.x / settings.MaxScale.x) * 0.5) + 0.5
                        else:
                            Scale.x = 0.0
                        if settings.MaxScale.y > 0.0:
                            Scale.y = ((Scale.y / settings.MaxScale.y) * 0.5) + 0.5
                        else:
                            Scale.y = 0.0
                        if settings.MaxScale.z > 0.0:
                            Scale.z = ((Scale.z / settings.MaxScale.z) * 0.5) + 0.5
                        else:
                            Scale.z = 0.0

                # red channel
                if R == "PosX":
                    Pixels[PixelIndex] = Position.x
                elif R == "QuatX":
                    Pixels[PixelIndex] = QuaternionAxis.x
                else: #ScaleX
                    Pixels[PixelIndex] = Scale.x

                # green channel
                if G == "PosY":
                    Pixels[PixelIndex + 1] = Position.y
                elif G == "QuatY":
                    Pixels[PixelIndex + 1] = QuaternionAxis.y
                else: #ScaleY
                    Pixels[PixelIndex + 1] = Scale.y

                # blue channel
                if B == "PosZ":
                    Pixels[PixelIndex + 2] = Position.z
                elif B == "QuatZ":
                    Pixels[PixelIndex + 2] = QuaternionAxis.z
                else: #ScaleZ
                    Pixels[PixelIndex + 2] = Scale.z

                # alpha channel
                if A == "Scale":
                    if settings.scaleUniformAxis == "X":
                        UniformScale = Scale.x
                    elif settings.scaleUniformAxis == "Y":
                        UniformScale = Scale.y
                    else: #Z
                        UniformScale = Scale.z

                    Pixels[PixelIndex + 3] = UniformScale
                elif A == "Quat":
                    original_quaternion = np.array([Quaternion.x, Quaternion.y, Quaternion.z, Quaternion.w])
                    CompressedQuaternion = PackQuaternion(original_quaternion)
                    Bits = struct.unpack('I', struct.pack('f', CompressedQuaternion))[0]
                    print(str(BufferIndex) + "| Quat: " + str(CompressedQuaternion) + " | Bits: " + str(bin(Bits)))
            
                    Pixels[PixelIndex + 3] = CompressedQuaternion

                    CompressedQuaternion = CompressQuaternion(Quaternion)
                    Bits = struct.unpack('I', struct.pack('f', CompressedQuaternion))[0]
                    print(str(BufferIndex) + "| Quat: " + str(CompressedQuaternion) + " | Bits: " + str(bin(Bits)))
                    
                elif A == "QuatW":
                    Pixels[PixelIndex + 3] = QuaternionAngle
                else: #None
                    Pixels[PixelIndex + 3] = 1.0
            else: # out of buffer
                Pixels[PixelIndex + 0] = 0.0
                Pixels[PixelIndex + 1] = 1.0
                Pixels[PixelIndex + 2] = 0.0
                Pixels[PixelIndex + 3] = 1.0
                print("Pixel Buffer Error!")

            PixelIndex += 4

    return Pixels

##########
# BOUNDS #
##########
def display_bounds(Name, MinBounds, MaxBounds):
    ''' Create a wireframe mesh to display the given bounds '''
    if Name is not None:
        # build bounds vertices
        Vertices = [
            mathutils.Vector((MinBounds.x, MinBounds.y, MinBounds.z)),
            mathutils.Vector((MinBounds.x, MinBounds.y, MaxBounds.z)),
            mathutils.Vector((MinBounds.x, MaxBounds.y, MaxBounds.z)),
            mathutils.Vector((MinBounds.x, MaxBounds.y, MinBounds.z)),
            mathutils.Vector((MaxBounds.x, MaxBounds.y, MaxBounds.z)),
            mathutils.Vector((MaxBounds.x, MaxBounds.y, MinBounds.z)),
            mathutils.Vector((MaxBounds.x, MinBounds.y, MinBounds.z)),
            mathutils.Vector((MaxBounds.x, MinBounds.y, MaxBounds.z))
        ]

        # try get existing bounds?
        BoundsObject = bpy.context.scene.objects.get(Name, None)
        if BoundsObject is not None:
            if BoundsObject.type == "MESH":
                # does it look like our mesh?z
                if len(BoundsObject.data.vertices) == 8:
                    # update our mesh!
                    for VertexIndex, Vertex in enumerate(BoundsObject.data.vertices):
                        Vertex.co = Vertices[VertexIndex]
                # existing mesh does not have 8 vertices, strange! Maybe it's not ours after all? Best not delete it
                else:
                    return (False, "An object named " + Name + " already exists but it doesn't look like it's from a previous bake. Unsafe to modify")
            else:
                return (False, "An object named " + Name + " already exists but isn't a mesh. Can't modify it")
        # create new bounds
        else:
            # create mesh
            BoundsMesh = bpy.data.meshes.new(Name)

            # create object to contain mesh
            BoundsObject = bpy.data.objects.new(BoundsMesh.name, BoundsMesh)

            # see if collection exists
            Collection = bpy.data.collections.get("ObjAnim", None)
            # create collection if needed
            if Collection is None:
                Collection = bpy.data.collections.new("ObjAnim")
                bpy.context.scene.collection.children.link(Collection)

            # assign bounds object to collection
            Collection.objects.link(BoundsObject)

            # we only need to construct faces for new bounds mesh
            Faces = [
                [0, 1, 2, 3],
                [4, 5, 6, 7],
                [0, 1, 7, 6],
                [4, 5, 3, 2],
                [7, 4, 2, 1],
                [6, 5, 3, 0]
            ]

            # create bounds mesh
            BoundsMesh.from_pydata(Vertices, [], Faces)

            # display wire in viewport
            BoundsObject.display_type = 'WIRE'

    return (True, "")

##############
# QUATERNION #
##############
def CompressQuaternion(Quaternion):
    ''' Quaternion packing using the three smallest component method (from quat to 32bits float) '''
    EncodedQuatFloat = 0

    packed_quat = mathutils.Vector((0.0,0.0,0.0))

    abs_quat_component = 0.0
    max_abs_quat_component = -1000.0
    max_abs_quat_component_index = 0

    # re-order quat components... wth is the W component first in Blender??!!
    quat_components = [
        Quaternion.x,
        Quaternion.y,
        Quaternion.z,
        Quaternion.w
    ]

    # get quat's largest absolute component
    for quat_component_index in range(4):
        abs_quat_component = abs(quat_components[quat_component_index])

        if abs_quat_component > max_abs_quat_component:
            max_abs_quat_component = abs_quat_component

            max_abs_quat_component_index = quat_component_index

    # ensure quat's largest component is positive so we don't have to save sign
    quat_largest_component_sign = -1.0 if quat_components[max_abs_quat_component_index] < 0.0 else 1.0
    quat_components[0] = quat_components[0] * quat_largest_component_sign
    quat_components[1] = quat_components[1] * quat_largest_component_sign
    quat_components[2] = quat_components[2] * quat_largest_component_sign
    quat_components[3] = quat_components[3] * quat_largest_component_sign

    # pack the smallest 3 components - fourth can be later reconstructed due to quaternions' property
    if max_abs_quat_component_index == 0: # X component is largest!!
        packed_quat = mathutils.Vector((quat_components[1], quat_components[2], quat_components[3]))
    elif max_abs_quat_component_index == 1: # Y component is largest!!
        packed_quat = mathutils.Vector((quat_components[0], quat_components[2], quat_components[3]))
    elif max_abs_quat_component_index == 2: # Z component is largest!!
        packed_quat = mathutils.Vector((quat_components[0], quat_components[1], quat_components[3]))
    else: # W component is largest!!
        packed_quat = mathutils.Vector((quat_components[0], quat_components[1], quat_components[2]))

    # none of the 3 smallest components of a quat can be larger than 1/sqrt(2), so it can be remapped to increase accuracy
    quat_normalization_offset = 0.707106781
    quat_normalization_scale = quat_normalization_offset + quat_normalization_offset

    packed_quat.x = min(1.0, max(0.0, (packed_quat.x + quat_normalization_offset) / quat_normalization_scale))
    packed_quat.y = min(1.0, max(0.0, (packed_quat.y + quat_normalization_offset) / quat_normalization_scale))
    packed_quat.z = min(1.0, max(0.0, (packed_quat.z + quat_normalization_offset) / quat_normalization_scale))

    # 2 bits for the index to reconstruct, 10 each for the others
    compression_bits = 10
    compression_mask = 1023.0 # 1023, precision mask

    # XYZ component converted into [0:1023] integer range to be packed into 10 bits
    int_packed_quat_x = math.floor((packed_quat.x) * compression_mask)
    int_packed_quat_y = math.floor((packed_quat.y) * compression_mask)
    int_packed_quat_z = math.floor((packed_quat.z) * compression_mask)

    # create 32 bits float: 2 | 10 | 10 | 10
    encoded_quat  = max_abs_quat_component_index << 30
    encoded_quat |= int_packed_quat_x << (compression_bits * 2)
    encoded_quat |= int_packed_quat_y << (compression_bits * 1)
    encoded_quat |= int_packed_quat_z << (compression_bits * 0)
    EncodedQuatFloat = struct.unpack('@f', struct.pack('@I', encoded_quat))[0]

    return EncodedQuatFloat

def UnCompressQuaternion(CompressedQuaternion):
    ''' Quaternion unpacking using the three smallest component method (from 32bits float to quaternion) '''
    quat_components = [
        0.0,
        0.0,
        0.0,
        1.0
    ] # X, Y, Z, W

    encoded_quat = struct.unpack('@I', struct.pack('@f', CompressedQuaternion))[0]
    
    # 2 bits for the index to reconstruct, 10 each for the others
    max_abs_quat_component_index = encoded_quat >> (30)
    compression_bits = 10
    compression_mask = 1023 # 1023, precision mask

    # unpack the smallest 3 components - fourth is going to be reconstructed next due to quaternions' property
    quat_components[0] = float( (encoded_quat >> (compression_bits * 2) ) & compression_mask ) / compression_mask
    quat_components[1] = float( (encoded_quat >> (compression_bits * 1) ) & compression_mask ) / compression_mask
    quat_components[2] = float( (encoded_quat >> (compression_bits * 0) ) & compression_mask ) / compression_mask

    # none of the 3 smallest components of a quat can be larger than 1/sqrt(2), so it has been remapped to increase accuracy
    quat_normalization_offset = 0.707106781
    quat_normalization_scale = quat_normalization_offset + quat_normalization_offset

    quat_components[0] = (quat_components[0] * quat_normalization_scale) - quat_normalization_offset
    quat_components[1] = (quat_components[1] * quat_normalization_scale) - quat_normalization_offset
    quat_components[2] = (quat_components[2] * quat_normalization_scale) - quat_normalization_offset

    # reconstruct fourth component
    QuatVector = mathutils.Vector((quat_components[0], quat_components[1], quat_components[2]))
    quat_components[3] = math.sqrt(max(0.0, 1.0 + (QuatVector @ -QuatVector)))

    # reorder quaternion if needed, depending on first two bits that contains max component index
    if max_abs_quat_component_index == 0: # wxyz
        quat_components = (quat_components[3], quat_components[0], quat_components[1], quat_components[2])
    elif max_abs_quat_component_index == 1: # xwyz
        quat_components = (quat_components[0], quat_components[3], quat_components[1], quat_components[2])
    elif max_abs_quat_component_index == 2: # xywz
        quat_components = (quat_components[0], quat_components[1], quat_components[3], quat_components[2])

    # WXYZ order... -_-
    return mathutils.Quaternion((quat_components[3], quat_components[0], quat_components[1], quat_components[2]))

def QuatToAxisAndAngleAtan(Quaternion):
    ''' One possible way to convert a quaternion into an axis & an angle, using Atan2 '''
    axis_and_angle = mathutils.Vector((0.0, 0.0, 0.0, 0.0))

    sin_half_angle = math.sqrt(Quaternion.x * Quaternion.x + Quaternion.y * Quaternion.y + Quaternion.z * Quaternion.z)

    if sin_half_angle > 0.0:
        axis_and_angle.x = Quaternion.x / sin_half_angle
        axis_and_angle.y = Quaternion.y / sin_half_angle
        axis_and_angle.z = Quaternion.z / sin_half_angle
    else:
        axis_and_angle.x = 0.0
        axis_and_angle.y = 0.0
        axis_and_angle.z = 1.0
    
    axis_and_angle.w = 2.0 * math.atan2(sin_half_angle, Quaternion.w)

    return axis_and_angle

def QuatToAxisAndAngleAcos(Quaternion):
    ''' One possible way to convert a quaternion into an axis & an angle, using ACos '''
    axis_and_angle = mathutils.Vector((0.0, 0.0, 0.0, 0.0))

    HalfAngle = math.acos(Quaternion.w)
    HalfSin = math.sin(HalfAngle)

    if HalfSin > 0.0:
        axis_and_angle.x = Quaternion.x / HalfSin
        axis_and_angle.y = Quaternion.y / HalfSin
        axis_and_angle.z = Quaternion.z / HalfSin
    else:
        axis_and_angle.x = 0.0
        axis_and_angle.y = 0.0
        axis_and_angle.z = 1.0
        
    axis_and_angle.w = HalfAngle * 2.0

    return axis_and_angle

############
# TEXTURES #
############
def CreateTexture(context, Index, PixelBuffer):
    ''' '''
    # get settings
    settings = context.scene.OATBakerSettings
    
    # get rid of existing image with that name, if any exists
    ImageName = settings.TexName + '_' + str(Index)
    Image = bpy.data.images.get(ImageName, None)
    if Image is not None:
        bpy.data.images.remove(Image)

    tex_width = settings.AnimObjectsTex
    tex_height = settings.AnimFramesTex

    # create texture
    Image = bpy.data.images.new(name=ImageName, width=tex_width, height=tex_height, alpha=True, float_buffer=True)
    Image.pixels = PixelBuffer

    return (Image, ImageName)

def export_texture(context, Image, ImageName):
    ''' '''
    # get settings
    settings = context.scene.OATBakerSettings

    SceneToRestore = context.scene
    NewScene = bpy.data.scenes.new("RenderSettingsScene")
    
    bpy.context.window.scene = NewScene

    NewScene.view_settings.view_transform = 'Raw'
    SceneSettings = NewScene.render.image_settings
    SceneSettings.file_format = 'OPEN_EXR'
    SceneSettings.color_mode = 'RGBA'
    SceneSettings.color_depth = '32'
    SceneSettings.compression = 0
    SceneSettings.exr_codec = 'NONE'

    FilePath = settings.TexPath + ImageName + '.exr'
    Image.save_render(bpy.path.abspath(FilePath), scene=NewScene)

    bpy.context.window.scene = SceneToRestore
    bpy.data.scenes.remove(NewScene)

    return True

def get_best_texture_resolution(num_frames, num_objs, MaxHeight, MaxWidth, ForcePowerOfTwo = False, ForceSquare = False):
    """ Returns the best texture resolution for a given amount of frames & vertices to bake """

    # first, simply check if data can theoritically fit into texture based on the maximum allowed image size
    if (num_frames * num_objs > MaxWidth * MaxHeight):
        return (False, "Buffer exceeding allowed size: " + str(num_frames * num_objs) + " instead of " + str(MaxWidth * MaxHeight), 0, 0)

    if (ForcePowerOfTwo):
        # compute the closest highest power of two that matches the number of vertices to bake
        tex_width = 2
        while (tex_width < num_objs and tex_width < MaxWidth):
            tex_width *= 2

        # however, if data can no longer fit into the texture based on that width
        # because there's more frames to bake than the allowed maximum height, we
        # revert to using maximum allowed width
        if (num_frames > MaxHeight):
            tex_width = MaxWidth

        TargetHeight = math.ceil(num_frames * (num_objs / float(tex_width)))
        tex_height = 2
        while (tex_height < TargetHeight):
            tex_height *= 2

        # kinda pointless imho, especially if power of two isn't enforced but implemented still only in that case
        if (ForceSquare):
            if tex_width < tex_height:
                tex_width = tex_height
            elif tex_height < tex_width:
                tex_height = tex_width
    else:
        if (num_objs <= MaxWidth):
            # one entire frame worth of vertex data can fit into one row of pixels
            tex_width = num_objs

            # however, if data can no longer fit into the texture based on that width
            # because there's more frames to bake than the allowed maximum height, we
            # revert to using maximum allowed width
            if (num_frames > MaxHeight):
                tex_width = MaxWidth
        else:
            # one entire frame worth of vertex data can NOT fit into one row of pixels and has to be split into multiple rows
            tex_width = MaxWidth

        tex_height = math.ceil(num_frames * (num_objs / float(tex_width)))

    # sanity check
    if (tex_width > MaxWidth):
        return (False, "Invalid tex_width", tex_width, tex_height)
    elif (tex_height > MaxHeight):
        return (False, "Invalid tex_height", tex_width, tex_height)
    else:
        return (True, "", tex_width, tex_height)

########
# MESH #
########
def BatchProjectUVs(context, Meshes):
    ''' '''
    # get settings
    settings = context.scene.OATBakerSettings

    # compute texel size in X
    TexelWidth = 1 / float(settings.AnimObjectsTex)
    HalfTexelWidth = TexelWidth * 0.5

    # compute texel size in Y
    TexelHeight = 1 / float(settings.AnimFramesTex)
    HalfTexelHeight = TexelHeight * 0.5

    if settings.uv_channelMode == "ObjRandom":
        # preloop through all meshes
        NumMeshes = 0
        for Object in Meshes:
            # type should have been ensured at this point, but precheck still :shrug:
            if Object.type == "MESH":
                NumMeshes += 1

        # pre compute uniform random value
        Rand = []
        for Index in range(NumMeshes):
            Offset = (1 / float(NumMeshes)) * 0.5
            Rand.append((Index / float(NumMeshes)) + Offset)
        random.shuffle(Rand)

    obj_index = 0
    # loop through all meshes
    for Object in Meshes:
        # type should have been ensured at this point, but check still :shrug:
        if Object.type == "MESH":
            obj_index += 1

            # create uvmap(s) if needed
            while (settings.uv_index > (len(Object.data.uv_layers) - 1)):
                Object.data.uv_layers.new()
                NewUVLayerIndex = len(Object.data.uv_layers) - 1

                for Poly in Object.data.polygons:
                    for loop_id in Poly.loop_indices:
                        # U axis - index based, must correspond of the 'row of pixels' to sample to play this object's animation in UE
                        Object.data.uv_layers[NewUVLayerIndex].data[loop_id].uv[0] = (obj_index / float(settings.AnimObjectsTex))

                        # arbitrary value in V Axis
                        if settings.uv_channelMode == "ObjRandom":
                            Object.data.uv_layers[NewUVLayerIndex].data[loop_id].uv[1] = Rand[obj_index - 1]
                        elif settings.uv_channelMode == "Value":
                            Object.data.uv_layers[NewUVLayerIndex].data[loop_id].uv[1] = settings.uv_channelValue
                        else:
                            Object.data.uv_layers[NewUVLayerIndex].data[loop_id].uv[1] = 0.0

                        # offset by half a texel to center UV on pixel!
                        Object.data.uv_layers[NewUVLayerIndex].data[loop_id].uv[0] -= HalfTexelWidth
                        Object.data.uv_layers[NewUVLayerIndex].data[loop_id].uv[1] -= HalfTexelHeight

    return True

#############
# SELECTION #
#############
def PostProcessSelection(context):
    ''' '''
    # get settings
    settings = context.scene.OATBakerSettings

    # duplicate selection
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False}) # @TODO get rid of it

    # see if collection exists
    ObjAnimCollection = bpy.data.collections.get("ObjAnim", None)
    # create collection if needed
    if ObjAnimCollection is None:
        ObjAnimCollection = bpy.data.collections.new("ObjAnim")
        bpy.context.scene.collection.children.link(ObjAnimCollection)

    # loop through duplicated selection
    DuplicatedObjects = context.selected_objects
    if len(DuplicatedObjects) <= 0:
        return (False, "No duplicated objects")

    for DuplicatedObject in DuplicatedObjects:
        # clean actions for duplicated objects
        if DuplicatedObject.animation_data is not None and DuplicatedObject.animation_data.action is not None:
            bpy.data.actions.remove(DuplicatedObject.animation_data.action, do_unlink = True)

        # objects transform must be reinitialized for export! Transforms are now baked into textures.
        DuplicatedObject.location = (0.0, 0.0, 0.0)
        DuplicatedObject.rotation_euler = mathutils.Euler((0.0, 0.0, 0.0))
        DuplicatedObject.unit_scale = (1.0, 1.0, 1.0)
        DuplicatedObject.rotation_quaternion = mathutils.Quaternion((0.0, 0.0, 0.0, 1.0))

        # unlink object from existing collections
        Collections = DuplicatedObject.users_collection
        for Collection in Collections:
            Collection.objects.unlink(DuplicatedObject)

        # assign object to collection
        ObjAnimCollection.objects.link(DuplicatedObject)

    # make selection single user
    bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False, obdata_animation=False) # @TODO get rid of it

    # loop through meshes and create necessary UV maps & UV data
    BatchProjectUVs(context, DuplicatedObjects)

    # merge if we actually have multiple meshes to merge!
    if settings.MergeBakedMesh:
        # make sure active object is actually one of our duplicated mesh
        bpy.context.view_layer.objects.active = DuplicatedObjects[0]

        # name active object for merge
        bpy.context.view_layer.objects.active.name      = settings.MergedBakedMeshName
        bpy.context.view_layer.objects.active.data.name = settings.MergedBakedMeshName

        # merge
        if len(DuplicatedObjects) > 1:
            bpy.ops.object.join() # @TODO get rid of it

        # export only available if merged? @todo why?
        if settings.ObjAutoExport:
            bpy.ops.export_scene.fbx(filepath=Path, check_existing=False, filter_glob='*.fbx', use_selection=True, use_visible=False, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', colors_type='SRGB', prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False, use_custom_props=False, add_leaf_bones=True, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')

    return (True, "")

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