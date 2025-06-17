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

from bpy.props import PointerProperty, BoolProperty, FloatProperty, EnumProperty, StringProperty, IntProperty, CollectionProperty, FloatVectorProperty
from bpy.types import PropertyGroup

import mathutils
from typing import NamedTuple

class ProcessedTransform(NamedTuple):
    loc: mathutils.Vector
    Quaternion: mathutils.Quaternion
    RotationAxis: mathutils.Vector
    RotationAngle: float
    Scale: mathutils.Vector

#############################################################################################
###################################### PROPERTY GROUPS ######################################
#############################################################################################
################
### SETTINGS ###
class OATBAKER_PG_Settings(PropertyGroup):
    """ """

    BakeModes = [
        ("ANIMATION", "Animation", "Bake vertex animation data based on the selected objects movement inherited from keyframed transforms"),
        ("MESHSEQUENCE", "Mesh Sequence", "Bake vertex animation data based on the selected mesh sequence. Frame order must be deducible from the objects names (.000, .001 etc)")
    ]
    bake_mode: EnumProperty(name="Mode", items=BakeModes, default=0, description="Select how the vertex animation data is baked")

    # scene
    Scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scaling factor. Defaults to 100 to go from 1 Blender unit (meter) to 1 UE unit (centimeter)")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert world X axis (must be False for UE)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert world Y axis (must be True for UE)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert world Z axis (must be False for UE)")

    # uv
    uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="UVMap to use to sample the generated textures. *Will* override existing UV data at that index, if any!")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData.VAT", description="UVMap to get or create for setting up the mesh UVs")
    uv_channelModes = [
        ("ObjRandom", "Object Random", 'Random value in the V channel, per object'),
        ("Value", "Value", 'Arbitrary in the V channel'),
    ]
    uv_channelMode: EnumProperty(name="V Axis", items=uv_channelModes, default=0, description="Select the data to store in the mesh's V axis, unused otherwise")
    uv_channelValue: FloatProperty(name="Value", min=0.0, default=0.0, description="Arbitrary value to store in the mesh's V axis")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended)")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the xml file name & path is computed")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="XML file name, without extension")
    export_xml_file_path: StringProperty(name="Path", default="//", description="XML file path, not including file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="True to override any existing .xml file")

    # frames
    SkipFirstFrame: BoolProperty(name="Skip First Frame", default=False, description="True to skip the first frame. Useful if this is used to provide a reference pose just for one frame in case animations are retargeted and mappings need to be performed in rest pose for more accurate results")
    frame_range_modes = [
            ("NLA", "NLA", "Derive frame range from the anims in the NLA track. This only works if the mesh to bake has an NLA track OR if it's parented to an armature that has one. Deriving frame range from NLA will also apply the frame step setting per animation, ensure that the first frame is always included"),
            ("Scene", "Scene", "Use the scene's frame range. Start & End are inclusives"),
            ("Custom", "Custom", "Use a custom frame range. Start & End are inclusives"),
        ]
    frame_range_mode: EnumProperty(name="Mode", items=frame_range_modes, default=0, description="Select how the frame range is derived")
    frame_range_custom_start: IntProperty(name="Start", min=1, default=1, description="Inclusive")
    frame_range_custom_end: IntProperty(name="End", min=2, default=25, description="Inclusive")
    frame_range_custom_step: IntProperty(name="Step", min=1, default=1, description="How many frames to skip 'each frame'. When using 'NLA' mode, this isn't a global skip but a per anim skip, as to ensure that the first frame of each animation clip is included")

    Axis = [
    ("X", "X", "X"),
    ("Y", "Y", "Y"),
    ("Z", "Z", "Z")
    ]

    RChannel = [
        ("PosX", "Position X", ""),
        ("QuatX", "Quaternion X", ""),
        ("ScaleX", "Scale X", "")
    ]

    GChannel = [
        ("PosY", "Position Y", ""),
        ("QuatY", "Quaternion Y", ""),
        ("ScaleY", "Scale Y", "")
    ]

    BChannel = [
        ("PosZ", "Position Z", ""),
        ("QuatZ", "Quaternion Z", ""),
        ("ScaleZ", "Scale Z", "")
    ]

    AChannel = [
        ("Scale", "Uniform Scale", ""),
        ("Quat", "Quat", ""),
        ("QuatW", "Quaternion W", ""),
        ("None", "None", "")
    ]
    
    # Global settings
    MergeBakedMesh: BoolProperty(name="Merge", default=True, description="Merge selected objects into one final mesh once bake is complete")
    MergedBakedMeshName: StringProperty(name="Name", default="Baked Mesh", description="Name to give the merged object if you do merge selected meshes into a single mesh")
    Origin: PointerProperty(type=bpy.types.Object, name="ORIGIN", description="")

    # texture 1
    FirstTexture: BoolProperty(name="First Texture", default=True, description="")
    FirstTextureR: EnumProperty(name="R", items=RChannel, default=0, description="")
    FirstTextureG: EnumProperty(name="G", items=GChannel, default=0, description="")
    FirstTextureB: EnumProperty(name="B", items=BChannel, default=0, description="")
    FirstTextureA: EnumProperty(name="A", items=AChannel, default=3, description="")

    # texture 2
    SecondTexture: BoolProperty(name="Second Texture", default=True, description="")
    SecondTextureR: EnumProperty(name="R", items=RChannel, default=1, description="")
    SecondTextureG: EnumProperty(name="G", items=GChannel, default=1, description="")
    SecondTextureB: EnumProperty(name="B", items=BChannel, default=1, description="")
    SecondTextureA: EnumProperty(name="A", items=AChannel, default=2, description="")

    # texture 3
    ThirdTexture: BoolProperty(name="Third Texture", default=False, description="")
    ThirdTextureR: EnumProperty(name="R", items=RChannel, default=2, description="")
    ThirdTextureG: EnumProperty(name="G", items=GChannel, default=2, description="")
    ThirdTextureB: EnumProperty(name="B", items=BChannel, default=2, description="")
    ThirdTextureA: EnumProperty(name="A", items=AChannel, default=3, description="")

    # texture path & name
    TexName: StringProperty(name="Name", default="T_BakedMesh_ObjAnim", description="Texture name")
    TexPath: StringProperty(name="Path", default="//", subtype='DIR_PATH', description="Export path")
    TexAutoExport: BoolProperty(name="Save To Disk", default=False, description="Export EXR file(s)")

    # mesh path & name
    ObjPath: StringProperty(name="Path", default="//", subtype='DIR_PATH', description="Export path")
    ObjAutoExport: BoolProperty(name="Save To Disk", default=False, description="Export FBX file")

    # pos
    NormalizePosition: BoolProperty(name="Normalize Position", default=False, description="Remap the offset to a [0:1] range to be exported to a 8 bits texture. This comes at a a loss of precision and requires a multiplier to be used in UE! There is no need to normalize the position if you intend to use a 16 or 32bits texture")
    bPositionNormalized: BoolProperty(name="MaxPosition", default=False, description="")
    MaxPosition: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")

    # rot
    NormalizeQuaternion: BoolProperty(name="Normalize Quaternion", default=False, description="Remap the quaternion to a [0:1] range to be exported to a 8 bits texture. This comes at a a loss of precision! There is no need to normalize the rotation if you intend to use a 16 or 32bits texture")

    # scale
    NormalizeScale: BoolProperty(name="Normalize Scale", default=False, description="Remap the scale to a [0:1] range to be exported to a 8 bits texture. This comes at a a loss of precision and requires a multiplier to be used in UE! There is no need to normalize the scale if you intend to use a 16 or 32bits texture")
    bScaleNormalized: BoolProperty(name="MaxScale", default=False, description="")
    MaxScale: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")
    ScaleUniformAxis: EnumProperty(name="Axis", items=Axis, default=0, description="Select the axis used to drive the uniform scale")

    # bounds
    bAccurateBounds: BoolProperty(name="Accurate vertices_bounds", default=False, description="If false, bounds will be conservative/overshot because based on rotated bounding boxes, but bake should be much faster. If true, bounds will be accurate because based on vertices")
    bPrevizBounds: BoolProperty(name="Previz vertices_bounds", default=False, description="If true, creates a wireframe mesh corresponding to the animation's bounds")
    bMaxBounds: BoolProperty(name="MaxScale", default=False, description="")
    MaxBounds: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")
    MaxOffsetBounds: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")
    MaxBaseBounds: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")
    bMinBounds: BoolProperty(name="MaxScale", default=False, description="")
    MinOffsetBounds: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")
    MinBounds: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")
    MinBaseBounds: FloatVectorProperty(name="Index", subtype='XYZ', default=(0,0,0), description="")

    # frames
    bIncludeLastFrame: BoolProperty(name="Include Last Frame", default=False, description="")

    # cached values
    AnimObjects: IntProperty(name="Objects", min=0, default=0, description="Number of meshes to bake")
    AnimObjectsTex: IntProperty(name="Objects", min=0, default=0, description="Number of rows to allocate in the texture, one per object")
    AnimFrames: IntProperty(name="Frames", min=0, default=0, description="Number of frames to play through and cache")
    AnimFramesTex: IntProperty(name="Frames Tex", min=0, default=0, description="Number of lines to allocate in the textre, one per frame (equals 'AnimFrames' rounded up to the nearest power of two)")
    
    AnimFrameRate: FloatProperty(name="Frame Rate", min=0.0, default=0.0, description="Animation's frame rate (based on the current scene's settings)")
    AnimDuration: FloatProperty(name="Duration", min=0.0, default=0.0, description="Animation's raw length (last frame - first frame)")
    AnimDurationRatio: FloatProperty(name="Duration", min=0.0, default=0.0, description="Ratio between animation's raw length and animation length once stretched to fit in a power of two texture")
    AnimSpeed: FloatProperty(name="Animation Speed", min=0.0, default=0.0, description="Multiplier to use so scrolling the animation texture using time, in seconds, result in the original animation speed (eg. 0.25 if the original animation is 4s long). Multiplier takes the duration ratio into account")

def register():
    bpy.types.Scene.OATBakerSettings = PointerProperty(type=OATBAKER_PG_Settings)

def unregister():
    del bpy.types.Scene.OATBakerSettings