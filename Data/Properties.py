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

from . import Functions
from .Functions import get_data_layer_name

#############################################################################################
###################################### PROPERTY GROUPS ######################################
#############################################################################################

################
### SETTINGS ###
class DATABAKER_PG_SettingsDataLayer(PropertyGroup):
    """ """
    ID: StringProperty(name="ID", default="", description="")
    ptr: IntProperty(name="Ptr", default=0, description="")

    datas = [
        ("POSITION", "Position", "X/Y/Z component of the object's position"),
        ("AXIS", "Axis", "X/Y/Z component of the object's forward/right/up vector"),
        ("SHAPEKEY", "Shape key", "X/Y/Z offset/normal of the object's shapekey"),
        ("MASK", "Mask", "Linear/Spherical mask"),
        ("RANDOM", "Random", "Seeded random value per collection/object/face"),
        ("VALUE", "Value", "Fixed value"),
        ("CUSTOM_PROP", "Custom Property", "Object's Float/Integer custom property"),
        ("FRAME", "Frame", "Vertex offset/normal of the object's vertices at a given frame based on the current frame (vertex count/order must be maintained)"),
        ("HIERARCHY", "Depth", "Hierarchy depth index (0 for root object, 1 for children, 2 for grandchildren etc.)"),
        ("QUATERNION", "Quaternion", "X/Y/Z/W component of the object's quaternion"),
    ]
    data: EnumProperty(name="Data", items=datas, default="POSITION", description="Type of data to bake")

    component_x_y_z = [
        ("X", "X", "The vector's X component"),
        ("Y", "Y", "The vector's Y component"),
        ("Z", "Z", "The vector's Z component")
    ]
    component: EnumProperty(name="Component", items=component_x_y_z, default="X", description="Component to bake")

    packing_modes = [
        ("UV", "UV", "Bake the data into a UV map"),
        ("XY_BIT", "Bitwise XY", "Bake the data preferably into the U channel of a UV map, along with the target data layer using 16- and 15-bit precision. Expect some precision loss. !!PACKING IN THE V CHANNEL IS DANGEROUS!!"),
        ("XY_NUM", "Numeric XY", "Bake the data into the U or V channel of a UV map, along with the target data layer using numeric packing. Expect moderate precision loss. Packing in the V channel is safe"),
        ("XYZ_BIT", "Bitwise XYZ", "Bake the data preferably into the U channel of a UV map, along with another layer and the target data layer using 11-, 10- and 10-bit precision. Expect moderate precision loss. !!PACKING IN THE V CHANNEL IS DANGEROUS!!"),
        ("XYZ_NUM", "Numeric XYZ", "Bake the data into the V channel of a UV map, along with the target data layer using numeric packing. Expect high precision loss. Packing in the V channel is safe"),
        ("FRACTION", "UV - Fraction", "Bake the data into the fractional part of a UV map, along with the target data which will be floored"),
        ("VCOL", "Vertex Color", "Bake data into vertex colors"),
        ("NORMAL", "Normal", "Bake data in mesh normals"),
    ]
    packing_mode: EnumProperty(name="Mode", items=packing_modes, description="How to store the value")

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

    quat_x_y_z_w = [
        ("X", "X", "The quaternion's X component"),
        ("Y", "Y", "The quaternion's Y component"),
        ("Z", "Z", "The quaternion's Z component"),
        ("W", "W", "The quaternion's W component"),
        ("XYZW", "XYZW", "The quaternion's XYZW components bit-packed into a single float using the smallest-three method. This requires a 32-bit UVs! !!PACKING IN THE V CHANNEL IS DANGEROUS!!"),
    ]
    quat: EnumProperty(name="Component", items=quat_x_y_z_w, default="XYZW", description="Component to bake")

    quat_xyz_orders = [
         ("XYZ", "XYZ", "XYZ"),
         ("XZY", "XZY", "XZY"),
         ("YXZ", "YXZ", "YXZ"),
         ("YZX", "YZX", "YZX"),
         ("ZXY", "ZXY", "ZXY"),
         ("ZYX", "ZYX", "ZYX")
    ]
    quat_xyz_order: EnumProperty(name="Order", items=quat_xyz_orders, default="XYZ", description="Basis for the quaternion")
    override_xyz_order: BoolProperty(name="Override", default=False, description="Override the global mesh axis order setting")

    normal_xyz: EnumProperty(name="Component", items=component_x_y_z, default="X", description="Normal component to store the data in")

    pack_x_y = [
        ("X", "X", "Pack the data in the 'X' component"),
        ("Y", "Y", "Pack the data in the 'Y' component"),
    ]
    pack_xy: EnumProperty(name="XY Mode", items=pack_x_y, default="Y", description="Target packed component")
    pack_x_y_z = [
        ("X", "X", "Pack the data in the 'X' component"),
        ("Y", "Y", "Pack the data in the 'Y' component"),
        ("Z", "Z", "Pack the data in the 'Z' component"),
    ]
    pack_xyz: EnumProperty(name="XYZ Mode", items=pack_x_y_z, default="Y", description="Target packed component")

    axis_x_y_z = [
        ("X", "Forward (X)", "X-axis"),
        ("Y", "Right (Y)", "Y-axis"),
        ("Z", "Up (Z)", "Z-axis")
    ]
    axis: EnumProperty(name="Axis", items=axis_x_y_z, default="X", description="Axis to bake")
    axis_modes = [
        ("LOCAL", "Local", ""),
        ("WORLD", "World", ""),
        ("OBJECT", "Object", ""),
    ]
    axis_mode: EnumProperty(name="Axis Mode", items=axis_modes, default="WORLD", description="Coordinate system for the axis to bake")
    axis_obj: PointerProperty(type=bpy.types.Object, name="Object", description="")

    name: StringProperty(name="Name", default="", description="")

    obj_modes = [
        ("SELF", "Self", "Data is fetched from the object itself"),
        ("PARENT", "Parent", "Data is fetched from the object's parent, if it has at least one, at the specified depth, if possible: 1 is the immediate parent, 2 grandparent, etc. It stops at the last valid parent and falls back to itself if no parent at all"),
        ("CUSTOM", "Custom", "Data is fetched from the a shared, user-specified object. Falls back to itself if none is set"),
        ("PROPERTY", "Property", "Data is fetched from the object targeted by a custom object property stored in the object itself. Falls back to itself if no property name is set, or if said property isn't itself set to point to a valid object")
    ]
    obj_mode: EnumProperty(name="Source", items=obj_modes, default="SELF", description="Source object to use")
    obj: PointerProperty(type=bpy.types.Object, name="Object", description="")
    obj_prop: StringProperty(name="Property", default="SourceObject", description="Name of the custom property stored in the objects to bake, to point to the desired targets")

    vertex_modes = [
        ("OFFSET", "Offset", ""),
        ("NORMAL", "Normal", "")
    ]
    vertex_mode: EnumProperty(name="Type", items=vertex_modes, default="OFFSET", description="Vertex data to bake")

    mask_modes = [
        ("SPHERE", "Sphere", ""),
        ("LINEAR", "Linear", ""),
    ]
    mask_mode: EnumProperty(name="Type", items=mask_modes, default="SPHERE", description="Mask mode")

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
    origin_mode: EnumProperty(name="Origin", items=origin_modes, default="OBJECT", description="Origin mode")

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
    index: IntProperty(name="Depth", default=1, min=1, description="")

class DATABAKER_PG_Settings(PropertyGroup):
    """ """

    data_layers: CollectionProperty(type=DATABAKER_PG_SettingsDataLayer, description="List of data layers")
    data_layers_selected_index: IntProperty(name="", default=0, description="Selected data layer")

    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData", description="UVMap to get or create for setting up the mesh UVs")
    mesh_materials: BoolProperty(name="Materials", default=True, description="Enable to copy materials")
    mesh_merge: BoolProperty(name="Merge", default=True, description="Enable merging of the duplicated selection once baking is complete. Otherwise, keep them separated to allow for additional bakes on the individual objects")
    mesh_duplicate: BoolProperty(name="Duplicate", default=True, description="Enable this option to preserve the original selection and bake data on the duplicated mesh. Disable it at your own risk—doing so will modify the selection, which may lead to unwanted changes to the source data and unpredictable bake results if data blocks are shared or have modifiers.")
    mesh_single_user: BoolProperty(name="Single User", default=True, description="If the selection isn't duplicated, the bake may not work as expected when data blocks are shared. This ensures that meshes are made 'single user' to prevent conflicts during the baking process. Issues may still arise on objects with modifiers.")
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert UVMap's V axis (typically True for exporting to UE or DirectX apps in general, False for Unity or OpenGL apps in general)")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied after inversion)")
    
    origin_obj: PointerProperty(type=bpy.types.Object, name="Origin", description="Optional object to use as the baking origin instead of the world origin. It takes into account the object's location, rotation, and unit_scale, which may lead to unexpected results. For this reason, it's considered experimental, but it might be useful in rare cases")
    clear_attributes: BoolProperty(name="Clear Attributes", default=True, description="Enable this option to remove face corner attributes that store the raw vertex data for each layer. These attributes are named using each layer's unique ID, created and used internally during baking, and are unlikely to be useful after the bake is complete")
    packing_precision: FloatProperty(name="Precision", min=0.001, max=0.999, default=0.99, description="Primiraly used to remap values ranging from [0:1] to [0:<1] for packing when using the 'fraction' mode")

    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")

    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended). Only available if the Blender file is saved")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the XML file name and path are generated")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported XML file (without the .xml extension)")
    export_xml_file_path: StringProperty(name="Path", default="//", description="Path for the exported XML file, excluding the file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .xml file")

##############
### REPORT ###
class DATABAKER_PG_ReportDataLayer(PropertyGroup):
    """ """
    active_layer_ID: StringProperty(name="ID", default="", description="")

    packed_mode: StringProperty(name="Packing", default="", description="")
    packed_layers: CollectionProperty(type=DATABAKER_PG_SettingsDataLayer, description="")
    packed_layers_selected_index: IntProperty(name="", default=0, description="")

    range_offset: FloatVectorProperty(name="Offset")
    range: FloatVectorProperty(name="Range")
    range_valid: BoolProperty(name="Valid")
    range_unit_vector: BoolProperty(name="Unit")
    range_high_precision: BoolProperty(name="HighPrecision")

class DATABAKER_PG_Report(PropertyGroup):
    """"""

    data_layers: CollectionProperty(type=DATABAKER_PG_ReportDataLayer, description="")
    data_layers_selected_index: IntProperty(name="", default=0, description="")

    baked: BoolProperty(name="Baked", default=False, description="")
    success: BoolProperty(name="Success", default=False, description="")
    msg: StringProperty(name="Message", default="", description="")
    name: StringProperty(name="Name", default="", description="")
    ID: StringProperty(name="ID", default="", description="")

    unit_system: StringProperty(name="Unit System", default="", description="")
    unit_unit: StringProperty(name="Unit", default="", description="")
    unit_length: FloatProperty(name="Unit Length", default=0.0, description="")
    unit_scale: FloatProperty(name="Unit Scale", default=0.0, description="")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="")
    unit_invert_y: BoolProperty(name="Invert Y", default=False, description="")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="")
    unit_invert_v: BoolProperty(name="Invert V", default=False, description="")
    unit_axis_orders = [
        ("XYZ", "XYZ", "XYZ"),
        ("XZY", "XZY", "XZY"),
        ("YXZ", "YXZ", "YXZ"),
        ("YZX", "YZX", "YZX"),
        ("ZXY", "ZXY", "ZXY"),
        ("ZYX", "ZYX", "ZYX"),
    ]
    unit_axis_order: EnumProperty(name="Order", items=unit_axis_orders, default="XYZ", description="Swizzle world axis (applied after inversion)")

    packing_precision: FloatProperty(name="Precision", min=0.001, max=0.999, default=0.99, description="")

    mesh: PointerProperty(type=bpy.types.Object, description="")
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="")
    mesh_export: BoolProperty(name="Mesh Exported", default=False, description="")
    mesh_path: StringProperty(name="Mesh Filepath", default="//", description="", subtype='FILE_PATH')

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

    origin_obj: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="")

    export_mesh: BoolProperty(name="Export", default=True, description="")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="")
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="")

def register():
    bpy.types.Scene.DataBakerSettings = PointerProperty(type=DATABAKER_PG_Settings)
    bpy.types.Scene.DataBakerReport = PointerProperty(type=DATABAKER_PG_Report)

def unregister():
    del bpy.types.Scene.DataBakerSettings
    del bpy.types.Scene.DataBakerReport
