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

#############################################################################################
###################################### PROPERTY GROUPS ######################################
#############################################################################################
def data_layer_ptr_id_updated(self, context):
    """
    we use an UIList to target a layer but a UIList requires an integer index for the 'active selection'. User might re-order, add or remove
    layers though so we instead prefer to target a layer using its ID. This function converts the integer to the corresponding ID. This is
    automatically called when the data_layer's ptr_id property is updated in any way
    """
    settings = context.scene.DataBakerSettings
    if self.ptr_index < len(settings.data_layers):
        data_layer = settings.data_layers[self.ptr_index]
        # only pick target if not self
        if data_layer.ID != self.ID:
            self.ptr_ID = data_layer.ID
            return
        else:
            # else, attempt to find target
            for data_layer_index, data_layer in enumerate(settings.data_layers):
                # target found!
                if data_layer.ID == self.ptr_ID:
                    # re-assign ptr_index to the previous target based on ID
                    self.ptr_index = data_layer_index
                    return

    # else, invalidate
    self.ptr_ID = ""
    self.ptr_index = -1

class DATABAKER_PG_DataLayerPropertyGroup(PropertyGroup):
    """ """

    ID: StringProperty(name="ID", default="", description="")
    ptr_ID: StringProperty(name="Ptr", default="", description="")
    ptr_index: IntProperty(name="Ptr", default=-1, description="", update=data_layer_ptr_id_updated)

    datas = [
        ("POSITION", "Position", ""),
        ("AXIS", "Axis", ""),
        ("SHAPEKEY", "Shape key", ""),
        ("MASK", "Mask", ""),
        ("RANDOM", "Random", ""),
        ("PARENT_POS", "Parent Position", ""),
        ("PARENT_AXIS", "Parent Axis", ""),
        ("VALUE", "Value", ""),
        ("CUSTOM_PROP", "Custom Property", ""),
    ]
    data: EnumProperty(name="Data", items=datas, default="POSITION", description="Value to bake")

    component_x_y_z = [
        ("X", "X", "X-axis"),
        ("Y", "Y", "Y-axis"),
        ("Z", "Z", "Z-axis")
    ]
    component: EnumProperty(name="Component", items=component_x_y_z, default="X", description="Component to bake")

    storage_modes = [
        ("UV", "UV Map", "Bake data into a UV map"),
        ("VCOL", "Vertex Color", "Bake data into vertex colors"),
        ("NORMAL", "Normal", "Bake data in mesh normals"),
        ("AB", "AB", "Pack the value with another value with moderate precision loss"),
        ("XYZ", "XYZ", "Pack the value with two other values with high precision loss"),
        ("FRACTION", "Fraction", "Pack the value in the fractional part of another value"),
    ]
    storage_mode: EnumProperty(name="Mode", items=storage_modes, default="UV", description="How to bake the value")

    uv_u_v = [
        ("U", "U", "U channel of UV map"),
        ("V", "V", "V channel of UV map")
    ]
    uv_index: IntProperty(name="UV Map", min=0, max=7, default=1, description="Target UV map index")
    uv_channel: EnumProperty(name="Channel", items=uv_u_v, default="U", description="Target UV channel")

    vcol_r_g_b_a = [
        ("R", "R", "Red channel"),
        ("G", "G", "Green channel"),
        ("B", "B", "Blue channel"),
        ("A", "A", "Alpha channel")
    ]
    vcol_rgba: EnumProperty(name="Channel", items=vcol_r_g_b_a, default="R", description="Target RGBA channel")

    normal_xyz: EnumProperty(name="Component", items=component_x_y_z, default="X", description="Normal component to store value in")

    pack_a_b = [
        ("A", "A", "Pack the data in the 'A' component"),
        ("B", "B", "Pack the data in the 'B' component"),
    ]
    pack_ab: EnumProperty(name="AB Mode", items=pack_a_b, default="A", description="Method for baking data")
    pack_x_y_z = [
        ("X", "X", "Pack the data in the 'X' component"),
        ("Y", "Y", "Pack the data in the 'Y' component"),
        ("Z", "Z", "Pack the data in the 'Z' component"),
    ]
    pack_xyz: EnumProperty(name="XYZ Mode", items=pack_x_y_z, default="X", description="Method for baking data")
    pack_only_if_non_null: BoolProperty(name="Pack Only If Non-Zero", default=True, description="Pack only if not (0,0,0), as it involves bit-packing and further 0-testing of the unpacked value in shaders could prove to be an unreliable operation. This is recommended, although it may lead to a false positive if the position to pack happens to be close enough to (0,0,0)")

    axis_x_y_z = [
        ("X", "X", "X-axis"),
        ("Y", "Y", "Y-axis"),
        ("Z", "Z", "Z-axis")
    ]
    axis: EnumProperty(name="Axis", items=axis_x_y_z, default="X", description="Axis to bake")
    axis_modes = [
        ("LOCAL", "Local", ""),
        ("WORLD", "World", ""),
        ("OBJECT", "Object", ""),
    ]
    axis_mode: EnumProperty(name="Axis Mode", items=axis_modes, default="WORLD", description="")
    axis_obj: PointerProperty(type=bpy.types.Object, name="Object", description="")

    name: StringProperty(name="Name", default="", description="")

    obj: PointerProperty(type=bpy.types.Object, name="Object", description="")

    shapekey_modes = [
        ("OFFSET", "Offset", ""),
        ("NORMAL", "Normal", "")
    ]
    shapekey_mode: EnumProperty(name="Type", items=shapekey_modes, default="OFFSET", description="Shape key data to bake")

    mask_modes = [
        ("SPHERE", "Sphere", ""),
        ("LINEAR", "Linear", ""),
    ]
    mask_mode: EnumProperty(name="Type", items=mask_modes, default="SPHERE", description="")

    normalize: BoolProperty(name="Normalize", default=True, description="Normalize value to [0:1] range based on max value")
    clamp: BoolProperty(name="Clamp", default=False, description="Clamp value to [0:1] range")
    falloff: FloatProperty(name="Falloff", min=0.0, default=1.0, description="Power curve. 1 - linear falloff, 2 - cubic falloff...")
    uniform: FloatProperty(name="Uniform", min=0.0, max=1.0, default=1.0, description="1.0 for evenly distributed values, 0.0 for full randomness")

    origin_modes = [
        ("WORLD", "World", "Compute gradient from the world origin"),
        ("OBJECT", "Object", "Compute gradient from each object's origin"),
        ("ORIGIN", "Origin", "Compute gradient from a specified object's origin"),
        ("SELECTION", "Selection", "Compute gradient from the center of selected objects"),
        ("PARENT", "Parent", "Compute gradient from each object's parent origin, if any, else from each object's own origin")
    ]
    origin_mode: EnumProperty(name="Origin", items=origin_modes, default="OBJECT", description="Origin")

    rand_modes = [
        ("COLLECTION", "Per Collection", "Random value per collection"),
        ("OBJECT", "Per Object", "Random value per object"),
        ("FACE", "Per Face (!)", "Random value per face (duplicates all vertices!)"),
    ]
    rand_mode: EnumProperty(name="Mode", items=rand_modes, default="OBJECT", description="Basis for the random values")
    rand_seed: IntProperty(name="Seed", default=0, description="")
    rand_float_modes = [
        ("FLOAT", "Float", "Generate a single value, to be shuffled or uniformly distributed"),
        ("FLOAT2", "Float2", "Generate a 2D unit vector"),
        ("FLOAT3", "Float3", "Generate a 3D unit vector"),
    ]
    rand_float_mode: EnumProperty(name="SubMode", items=rand_float_modes, default="FLOAT", description="")

    x: FloatProperty(name="X Value", default=1.0, description="")
    y: FloatProperty(name="Y Value", default=1.0, description="")
    z: FloatProperty(name="Z Value", default=1.0, description="")
    index: IntProperty(name="Depth", default=1, min=1, description="Hierarchy depth to bake")

def settings_data_layers_selected_index_updated(self, context):
    """
    we use an UIList to target a layer but a UIList requires an integer index for the 'active selection'. User might re-order, add or remove
    layers though so we instead prefer to target a layer using its ID. This function converts the ID to the corresponding integer index. This
    is automatically called when the settings's data_layers_selected_index property is updated in any way
    """
    # get data layer selected in main UI list
    settings = context.scene.DataBakerSettings
    if settings.data_layers_selected_index < len(settings.data_layers):
        data_layer_selected = settings.data_layers[settings.data_layers_selected_index]

        # is the selected data layer supposed to target another layer?
        if data_layer_selected.storage_mode == "FRACTION" or data_layer_selected.storage_mode == "AB" or data_layer_selected.storage_mode == "XYZ":
            # attempt to find target
            for data_layer_index, data_layer in enumerate(settings.data_layers):
                # target found!
                if data_layer.ID == data_layer_selected.ptr_ID:
                    # validate target only if not pointing to self
                    if data_layer.ID != data_layer_selected.ID:
                        data_layer_selected.ptr_index = data_layer_index
                        return

        # else, invalidate
        data_layer_selected.ptr_ID = ""
        data_layer_selected.ptr_index = -1

class DATABAKER_PG_SettingsPropertyGroup(PropertyGroup):
    """ """
    data_layers: CollectionProperty(type=DATABAKER_PG_DataLayerPropertyGroup, description="")
    data_layers_selected_index: IntProperty(name="", default=0, description="", update=settings_data_layers_selected_index_updated)

    # transform
    world_obj: PointerProperty(type=bpy.types.Object, name="Object", description="Defaults to 'self'. Use this in the rare occasion that you want to bake the position/axis of a specific object into another object. Usually using 'self' is what you want (meaning, leave this empty)")

    # mesh
    duplicate_mesh: BoolProperty(name="Duplicate Mesh", default=True, description="Duplicate mesh before baking to preserve original. Disable at your own risk")
    make_single_user: BoolProperty(name="Make Single-User", default=True, description="Ensure mesh data is unique to avoid conflicts. Ensured if duplicated, else, disable at your own risk")
    merge_mesh: BoolProperty(name="Merge Meshes", default=True, description="Merge all baked meshes into one. Safe to enable if duplicated, else, use at your own risk")
    clean_bake: BoolProperty(name="Clean Up", default=True, description="Remove temporary objects after baking")
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")
    scale: FloatProperty(name="Scale Factor", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")
    invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    origin: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="Optional object to use as baking origin")
    precision_offset: FloatProperty(name="Precision Offset", min=1.0, default=1.0, description="Offset to improve packing precision")

    export_mesh: BoolProperty(name="Export", default=True, description="True to export the mesh to FBX upon bake completion")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="FBX file name, without extension")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="FBX file path, not including file name", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="True to override any existing .fbx file")

    # uv
    uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData", description="UVMap to get or create for setting up the mesh UVs")
    invert_v: BoolProperty(name="Invert V", default=True, description="Invert UVMap's V axis & flip VAT texture(s) upside down (typically True for exporting to UE or DirectX apps in general, False for Unity or OpenGL apps in general)")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended)")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the xml file name & path is computed")
    export_xml_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="XML file name, without extension")
    export_xml_file_path: StringProperty(name="Path", default="//", description="XML file path, not including file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="True to override any existing .xml file")

class DATABAKER_PG_ReportUVMapPropertyGroup(PropertyGroup):
    """Properties for reporting animation-related bake data."""

    ID: StringProperty(name="ID", default="", description="Unique identifier for the animation data")
    name: StringProperty(name="Name", default="", description="Name of the animation data")

class DATABAKER_PG_ReportPropertyGroup(PropertyGroup):
    """Enhanced reporting properties for DataBaker with detailed feedback."""

    baked: BoolProperty(name="Baked", default=False, description="")
    success: BoolProperty(name="Success", default=False, description="")
    msg: StringProperty(name="Message", default="", description="")
    name: StringProperty(name="Name", default="", description="")
    ID: StringProperty(name="ID", default="", description="")

    unit_system: StringProperty(name="Unit System", default="", description="")
    unit_unit: StringProperty(name="Unit", default="", description="")
    unit_length: FloatProperty(name="Unit Length", default=0.0, description="")
    unit_scale: FloatProperty(name="Scale Factor", default=0.0, description="")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="")
    unit_invert_y: BoolProperty(name="Invert Y", default=False, description="")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="")

    position_multiplier: FloatProperty(name="Position Multiplier", default=0.0, description="")
    parent_position_multiplier: FloatProperty(name="Parent Position Multiplier", default=0.0, description="")
    shapekey_offset_multiplier: FloatProperty(name="Shape Key Offset Multiplier", default=0.0, description="")

    mesh: PointerProperty(type=bpy.types.Object, description="")
    mesh_export: BoolProperty(name="Mesh Exported", default=False, description="")
    mesh_path: StringProperty(name="Mesh Filepath", default="//", description="", subtype='FILE_PATH')
    mesh_uvmaps: CollectionProperty(type=DATABAKER_PG_ReportUVMapPropertyGroup, description="")
    select_mesh_uvmap: IntProperty(name="Selected UV Map", default=0, description="")
    mesh_uvmap_invert_v: BoolProperty(name="Invert V", default=False, description="")
    mesh_uvmap_count: IntProperty(name="UV Map Count", default=0, description="")

    meshes_count: IntProperty(name="Mesh Count", default=0, description="")
    empties_count: IntProperty(name="Empty Count", default=0, description="")

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

    world_obj: PointerProperty(type=bpy.types.Object, name="World", description="")

    # mesh
    duplicate_mesh: BoolProperty(name="Duplicate Mesh", default=True, description="")
    make_single_user: BoolProperty(name="Make Single-User", default=True, description="")
    merge_mesh: BoolProperty(name="Merge Meshes", default=True, description="")
    clean_bake: BoolProperty(name="Clean Up", default=True, description="")
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="")
    scale: FloatProperty(name="Scale Factor", min=0.001, default=100.0, description="")
    invert_x: BoolProperty(name="Invert X", default=False, description="")
    invert_y: BoolProperty(name="Invert Y", default=True, description="")
    invert_z: BoolProperty(name="Invert Z", default=False, description="")
    origin: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="")
    precision_offset: FloatProperty(name="Precision Offset", min=1.0, default=1.0, description="")

    export_mesh: BoolProperty(name="Export", default=True, description="")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<ObjectName>", description="")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="")
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="")

def register():
    bpy.types.Scene.DataBakerSettings = PointerProperty(type=DATABAKER_PG_SettingsPropertyGroup)
    bpy.types.Scene.DataBakerReport = PointerProperty(type=DATABAKER_PG_ReportPropertyGroup)

def unregister():
    del bpy.types.Scene.DataBakerSettings
    del bpy.types.Scene.DataBakerReport
