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
class DATABAKER_PG_DataLayerPropertyGroup(PropertyGroup):
    """ """

    display_name: StringProperty(name="Name", default="Layer", description="")
    ID: StringProperty(name="ID", default="", description="")
    ptr_ID: StringProperty(name="Ptr", default="", description="")

    datas = [
        ("POSITION", "Position", "X/Y/Z component of the object's position"),
        ("AXIS", "Axis", "X/Y/Z component of the object's forward/right/up vector"),
        ("SHAPEKEY", "Shape key", "X/Y/Z offset/normal of the object's shapekey"),
        ("MASK", "Mask", "Linear/Spherical mask"),
        ("RANDOM", "Random", "Seeded random value per collection/object/face"),
        ("VALUE", "Value", "Fixed value"),
        ("CUSTOM_PROP", "Custom Property", "Object's Float/Integer custom property"),
        ("FRAME", "Frame", "Vertex offset/normal of the object's vertices at a given frame based on the current frame (vertex count/order must be maintained)"),
        ("HIERARCHY", "Hierarchy", "Object's parent index")
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
        ("XY", "UV - XY", "Bake the data into a UV map, along with the target data layer using 16- and 15-bit precision. Expect moderate precision loss"),
        ("XYZ", "UV - XYZ", "Bake the data into a UV map, along with another layer and the target data layer using 11-, 10- and 10-bit precision. Expect high precision loss"),
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
        ("SELF", "Self", "Itself"),
        ("PARENT", "Parent", "Parent, if it has any"),
        ("CUSTOM", "Custom", "Target Object"),
    ]
    obj_mode: EnumProperty(name="Source", items=obj_modes, default="SELF", description="Source object to use")
    obj: PointerProperty(type=bpy.types.Object, name="Object", description="")

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

class DATABAKER_PG_SettingsPropertyGroup(PropertyGroup):
    """ """

    # generate enum on demand to omit the selected layer, as it cannot be picked to prevent targeting self
    def get_data_layers_ptr_items(self, context):
        items = []
        for data_layer in self.data_layers:
            include_layer = True

            if self.data_layers_selected_index < len(self.data_layers):
                data_layer_selected = self.data_layers[self.data_layers_selected_index]
                if (data_layer_selected == data_layer):
                    include_layer = False

            if include_layer and (data_layer.packing_mode == "XY" or data_layer.packing_mode == "XYZ" or data_layer.packing_mode == "FRACTION"):
                include_layer = False

            if include_layer:
                items.append((data_layer.ID, data_layer.ID, ""))

        return items

    # getting the enum value is based on the selected layer's ptr_id matching any of the available enum items, else 0
    def get_data_layers_ptr(self):
        if self.data_layers and (self.data_layers_selected_index < len(self.data_layers)):
            data_layer_selected = self.data_layers[self.data_layers_selected_index]

            items = self.get_data_layers_ptr_items(bpy.context)
            for item_index, item in enumerate(items):
                if item[0] == data_layer_selected.ptr_ID: # ID match
                    return item_index

        return 0

    # setting the enum value sets the selected layer's ptr_id
    def set_data_layers_ptr(self, value):
        if self.data_layers and self.data_layers_selected_index < len(self.data_layers):
            data_layer_selected = self.data_layers[self.data_layers_selected_index]
            data_layer_selected.ptr_ID = self.get_data_layers_ptr_items(bpy.context)[value][0]
        return

    # used to expose a picker for data_layers to target all other data_layers but themselves
    data_layers_ptr: EnumProperty(items=get_data_layers_ptr_items, name="Target", get=get_data_layers_ptr, set=set_data_layers_ptr, description="Pick a target data layer for packing")

    data_layers: CollectionProperty(type=DATABAKER_PG_DataLayerPropertyGroup, description="List of data layers")
    data_layers_selected_index: IntProperty(name="", default=0, description="Selected data layer")

    # mesh
    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale applied during baking (e.g. meters to centimeters)")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    origin_obj: PointerProperty(type=bpy.types.Object, name="Origin", description="Optional object to use as the baking origin instead of the world origin. It takes into account the object's location, rotation, and unit_scale, which may lead to unexpected results. For this reason, it's considered experimental, but it might be useful in rare cases")
    clear_attributes: BoolProperty(name="Clear Attributes", default=True, description="Enable this option to remove face corner attributes that store the raw vertex data for each layer. These attributes are named using each layer's unique ID, created and used internally during baking, and are unlikely to be useful after the bake is complete")
    packing_precision: FloatProperty(name="Precision", min=0.001, max=0.999, default=0.99, description="Primiraly used to remap values ranging from [0:1] to [0:<1] for packing when using the 'fraction' mode")

    export_mesh: BoolProperty(name="Export", default=True, description="Enable to export the generated mesh to an FBX file upon bake completion. Only available if the Blender file is saved")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported FBX file (without the .fbx extension). <BakeName> is a placeholder tag that can be used to be replaced with the object's name")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="File path for the exported FBX, excluding the file name. The path is relative to the Blender file if saved", subtype='FILE_PATH')
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .fbx file")

    # uv
    mesh_uvmap_name: StringProperty(name="UVMap Name", default="UVMap.BakedData", description="UVMap to get or create for setting up the mesh UVs")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert UVMap's V axis & flip VAT texture(s) upside down (typically True for exporting to UE or DirectX apps in general, False for Unity or OpenGL apps in general)")

    # xml
    export_xml: BoolProperty(name="Export", default=True, description="True to export an XML file containing informations relative to the bake (recommended). Only available if the Blender file is saved")
    export_xml_modes = [
        ("MESHPATH", "Mesh Path", "Use the same mesh fbx file name & path. Defaults to 'Custom' if mesh is *not* exported"),
        ("CUSTOMPATH", "Custom Path", "Specify a custom xml file name & path")
    ]
    export_xml_mode: EnumProperty(name="Mode", items=export_xml_modes, default=0, description="Select how the XML file name and path are generated")
    export_xml_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="Name for the exported XML file (without the .xml extension)")
    export_xml_file_path: StringProperty(name="Path", default="//", description="Path for the exported XML file, excluding the file name", subtype='FILE_PATH')
    export_xml_override: BoolProperty(name="Override", default=True, description="Enable to override any existing .xml file")

class DATABAKER_PG_DataLayerReportPropertyGroup(PropertyGroup):
    """ """
    active_layer_ID: StringProperty(name="ID", default="", description="")

    packed_mode: StringProperty(name="Packing", default="", description="")
    packed_layers: CollectionProperty(type=DATABAKER_PG_DataLayerPropertyGroup, description="")
    packed_layers_selected_index: IntProperty(name="", default=0, description="")

    range_offset: FloatVectorProperty(name="Offset")
    range: FloatVectorProperty(name="Range")
    range_valid: BoolProperty(name="Valid")
    range_unit_vector: BoolProperty(name="Unit")
    range_high_precision: BoolProperty(name="HighPrecision")

class DATABAKER_PG_ReportPropertyGroup(PropertyGroup):
    """"""

    data_layers: CollectionProperty(type=DATABAKER_PG_DataLayerReportPropertyGroup, description="")
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
    packing_precision: FloatProperty(name="Precision", min=0.001, max=0.999, default=0.99, description="")

    mesh: PointerProperty(type=bpy.types.Object, description="")
    mesh_export: BoolProperty(name="Mesh Exported", default=False, description="")
    mesh_path: StringProperty(name="Mesh Filepath", default="//", description="", subtype='FILE_PATH')
    unit_invert_v: BoolProperty(name="Invert V", default=False, description="")

    xml: BoolProperty(name="XML Exported", default=False, description="")
    xml_path: StringProperty(name="XML Filepath", default="//", description="", subtype='FILE_PATH')

    mesh_name: StringProperty(name="Name", default="BakedMesh.DATA", description="") # @TODO duplicate?!
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="") # @TODO duplicate?!
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="") # @TODO duplicate?!
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="") # @TODO duplicate?!
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="") # @TODO duplicate?!
    origin_obj: PointerProperty(type=bpy.types.Object, name="Custom Origin", description="")

    export_mesh: BoolProperty(name="Export", default=True, description="")
    export_mesh_file_name: StringProperty(name="Name", default="SM_<BakeName>", description="")
    export_mesh_file_path: StringProperty(name="Path", default="//", description="")
    export_mesh_file_override: BoolProperty(name="Override", default=True, description="")

def register():
    bpy.types.Scene.DataBakerSettings = PointerProperty(type=DATABAKER_PG_SettingsPropertyGroup)
    bpy.types.Scene.DataBakerReport = PointerProperty(type=DATABAKER_PG_ReportPropertyGroup)

def unregister():
    del bpy.types.Scene.DataBakerSettings
    del bpy.types.Scene.DataBakerReport
