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

from bpy.types import Operator, StringProperty

from . import Functions
from .Functions import bake, get_data_layer_name, copy_data_layer, reset_bake_report, export_bake_report

from bl_operators.presets import AddPresetBase

import uuid

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################
class DATABAKER_OT_BakeData(Operator):
    """ Bakes various data such as pivots and axis into UVs or VCols. """
    bl_idname = "gametools.databaker_bakedata"
    bl_label = "Bake"
    bl_category = "Game Tools"
    bl_options = {'REGISTER', 'UNDO'}
    
    # @classmethod
    # def poll(cls, context):
    #     Object = context.active_object
    #     return Object and Object.type == 'MESH' and Object.mode == 'OBJECT'

    def execute(self, context):
        success, verbose, msg = bake(context)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

##############
### Preset ###
class DATABAKER_OT_DataBaker_AddPreset(AddPresetBase, Operator):
    bl_idname = 'databaker_databakerpanel.addpreset'
    bl_label = 'Add preset'
    preset_menu = 'DATABAKER_MT_DataBaker_Presets'

    preset_defines = [ 'settings = bpy.context.scene.DataBakerSettings' ]

    preset_values = [  
    'settings.world_obj',
    'settings.position',
    'settings.position_channel_mode',
    'settings.position_x',
    'settings.position_x_mode',
    'settings.position_x_uv_index',
    'settings.position_x_uv_channel',
    'settings.position_x_rgba',
    'settings.position_y',
    'settings.position_y_mode',
    'settings.position_y_uv_index',
    'settings.position_y_uv_channel',
    'settings.position_y_rgba',
    'settings.position_z',
    'settings.position_z_mode',
    'settings.position_z_uv_index',
    'settings.position_z_uv_channel',
    'settings.position_z_rgba',
    'settings.position_packed_uv_index',
    'settings.position_packed_uv_channel',
    'settings.position_pack_only_if_non_null',
    'settings.position_ab_packed_a_comp',
    'settings.position_ab_packed_b_comp',
    'settings.axis',
    'settings.axis_component',
    'settings.axis_channel_mode',
    'settings.axis_x',
    'settings.axis_x_mode',
    'settings.axis_x_uv_index',
    'settings.axis_x_uv_channel',
    'settings.axis_x_rgba',
    'settings.axis_y',
    'settings.axis_y_mode',
    'settings.axis_y_uv_index',
    'settings.axis_y_uv_channel',
    'settings.axis_y_rgba',
    'settings.axis_z',
    'settings.axis_z_mode',
    'settings.axis_z_uv_index',
    'settings.axis_z_uv_channel',
    'settings.axis_z_rgba',
    'settings.axis_packed_uv_index',
    'settings.axis_packed_uv_channel',
    'settings.axis_ab_packed_a_comp',
    'settings.axis_ab_packed_b_comp',
    'settings.shapekey_name',
    'settings.shapekey_rest_name',
    'settings.shapekey_offset',
    'settings.shapekey_offset_channel_mode',
    'settings.shapekey_offset_x',
    'settings.shapekey_offset_x_mode',
    'settings.shapekey_offset_x_uv_index',
    'settings.shapekey_offset_x_uv_channel',
    'settings.shapekey_offset_x_rgba',
    'settings.shapekey_offset_y',
    'settings.shapekey_offset_y_mode',
    'settings.shapekey_offset_y_uv_index',
    'settings.shapekey_offset_y_uv_channel',
    'settings.shapekey_offset_y_rgba',
    'settings.shapekey_offset_z',
    'settings.shapekey_offset_z_mode',
    'settings.shapekey_offset_z_uv_index',
    'settings.shapekey_offset_z_uv_channel',
    'settings.shapekey_offset_z_rgba',
    'settings.shapekey_offset_packed_uv_index',
    'settings.shapekey_offset_packed_uv_channel',
    'settings.shapekey_offset_pack_only_if_non_null',
    'settings.shapekey_offset_ab_packed_a_comp',
    'settings.shapekey_offset_ab_packed_b_comp',
    'settings.shapekey_normal',
    'settings.shapekey_normal_channel_mode',
    'settings.shapekey_normal_x',
    'settings.shapekey_normal_x_mode',
    'settings.shapekey_normal_x_uv_index',
    'settings.shapekey_normal_x_uv_channel',
    'settings.shapekey_normal_x_rgba',
    'settings.shapekey_normal_y',
    'settings.shapekey_normal_y_mode',
    'settings.shapekey_normal_y_uv_index',
    'settings.shapekey_normal_y_uv_channel',
    'settings.shapekey_normal_y_rgba',
    'settings.shapekey_normal_z',
    'settings.shapekey_normal_z_mode',
    'settings.shapekey_normal_z_uv_index',
    'settings.shapekey_normal_z_uv_channel',
    'settings.shapekey_normal_z_rgba',
    'settings.shapekey_normal_xyz_uv_index',
    'settings.shapekey_normal_xyz_uv_channel',
    'settings.shapekey_normal_ab_packed_a_comp',
    'settings.shapekey_normal_ab_packed_b_comp',
    'settings.sphere_mask',
    'settings.sphere_mask_normalize',
    'settings.sphere_mask_clamp',
    'settings.sphere_mask_origin_mode',
    'settings.sphere_mask_origin',
    'settings.sphere_mask_mode',
    'settings.sphere_mask_uv_index',
    'settings.sphere_mask_uv_channel',
    'settings.sphere_mask_rgba',
    'settings.sphere_mask_falloff',
    'settings.linear_mask',
    'settings.linear_mask_normalize',
    'settings.linear_mask_clamp',
    'settings.linear_mask_obj_mode',
    'settings.linear_mask_obj',
    'settings.linear_mask_mode',
    'settings.linear_mask_axis',
    'settings.linear_mask_uv_index',
    'settings.linear_mask_uv_channel',
    'settings.linear_mask_rgba',
    'settings.linear_mask_falloff',
    'settings.random_per_collection',
    'settings.random_per_collection_mode',
    'settings.random_per_collection_uv_index',
    'settings.random_per_collection_uv_channel',
    'settings.random_per_collection_rgba',
    'settings.random_per_collection_uniform',
    'settings.random_per_object',
    'settings.random_per_object_mode',
    'settings.random_per_object_uv_index',
    'settings.random_per_object_uv_channel',
    'settings.random_per_object_rgba',
    'settings.random_per_object_uniform',
    'settings.random_per_poly',
    'settings.random_per_poly_mode',
    'settings.random_per_poly_uv_index',
    'settings.random_per_poly_uv_channel',
    'settings.random_per_poly_rgba',
    'settings.random_per_poly_uniform',
    'settings.parent_mode',
    'settings.parent_depth',
    'settings.parent_max_depth',
    'settings.parent_automatic_uv_index',
    'settings.parent_automatic_uv_channel',
    'settings.parent_position',
    'settings.parent_position_channel_mode',
    'settings.parent_position_x',
    'settings.parent_position_x_mode',
    'settings.parent_position_x_uv_index',
    'settings.parent_position_x_uv_channel',
    'settings.parent_position_x_rgba',
    'settings.parent_position_y',
    'settings.parent_position_y_mode',
    'settings.parent_position_y_uv_index',
    'settings.parent_position_y_uv_channel',
    'settings.parent_position_y_rgba',
    'settings.parent_position_z',
    'settings.parent_position_z_mode',
    'settings.parent_position_z_uv_index',
    'settings.parent_position_z_uv_channel',
    'settings.parent_position_z_rgba',
    'settings.parent_position_packed_uv_index',
    'settings.parent_position_packed_uv_channel',
    'settings.parent_position_ab_packed_a_comp',
    'settings.parent_position_ab_packed_b_comp',
    'settings.parent_axis',
    'settings.parent_axis_component',
    'settings.parent_axis_channel_mode',
    'settings.parent_axis_x',
    'settings.parent_axis_x_mode',
    'settings.parent_axis_x_uv_index',
    'settings.parent_axis_x_uv_channel',
    'settings.parent_axis_x_rgba',
    'settings.parent_axis_y',
    'settings.parent_axis_y_mode',
    'settings.parent_axis_y_uv_index',
    'settings.parent_axis_y_uv_channel',
    'settings.parent_axis_y_rgba',
    'settings.parent_axis_z',
    'settings.parent_axis_z_mode',
    'settings.parent_axis_z_uv_index',
    'settings.parent_axis_z_uv_channel',
    'settings.parent_axis_z_rgba',
    'settings.parent_axis_packed_uv_index',
    'settings.parent_axis_packed_uv_channel',
    'settings.parent_axis_ab_packed_a_comp',
    'settings.parent_axis_ab_packed_b_comp',
    'settings.fixed_value',
    'settings.fixed_value_data',
    'settings.fixed_value_mode',
    'settings.fixed_value_uv_index',
    'settings.fixed_value_uv_channel',
    'settings.fixed_value_rgba',
    'settings.direction',
    'settings.direction_mode',
    'settings.direction_vector_x',
    'settings.direction_vector_y',
    'settings.direction_vector_z',
    'settings.direction_pack_mode',
    'settings.custom_prop',
    'settings.custom_prop_name',
    'settings.duplicate_mesh',
    'settings.make_single_user',
    'settings.merge_mesh',
    'settings.clean_bake',
    'settings.mesh_name',
    'settings.scale',
    'settings.invert_x',
    'settings.invert_y',
    'settings.invert_z',
    'settings.origin',
    'settings.precision_offset',
    'settings.export_mesh',
    'settings.export_mesh_file_name',
    'settings.export_mesh_file_path',
    'settings.export_mesh_file_override',
    'settings.uvmap_name',
    'settings.invert_v',
    'settings.export_xml',
    'settings.export_xml_mode',
    'settings.export_xml_file_name',
    'settings.export_xml_file_path',
    'settings.export_xml_override'
    ]

    preset_subdir = 'operator/databaker_data'

#####################
### NLA Exclusion ###
class DATABAKER_OT_NewSettings_NewItem(Operator):
    """Add a new item to the list."""
    bl_idname = "databaker_item.new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        last_item = None
        current_index = context.scene.DataBakerSettings.data_layers_selected_index
        if context.scene.DataBakerSettings.data_layers and (current_index < len(context.scene.DataBakerSettings.data_layers)):
            last_item = context.scene.DataBakerSettings.data_layers[current_index]

        context.scene.DataBakerSettings.data_layers.add()
        last_index = len(context.scene.DataBakerSettings.data_layers) - 1
        if last_index >= 0:
            context.scene.DataBakerSettings.data_layers_selected_index = last_index

            item = context.scene.DataBakerSettings.data_layers[last_index]
            item.ID = uuid.uuid4().hex
            item.ptr_ID = ""

            if last_item:
                copy_data_layer(item, last_item)

        return{'FINISHED'}

class DATABAKER_OT_NewSettings_DeleteItem(Operator):
    """Delete the selected item from the list."""
    bl_idname = "databaker_item.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerSettings.data_layers

    def execute(self, context):
        if context.scene.DataBakerSettings.data_layers and (context.scene.DataBakerSettings.data_layers_selected_index < len(context.scene.DataBakerSettings.data_layers)):
            for data in context.scene.DataBakerSettings.data_layers:
                if data.ptr_ID == context.scene.DataBakerSettings.data_layers[context.scene.DataBakerSettings.data_layers_selected_index].ID:
                    data.ptr_ID = "" # invalidate all ptrs pointing to the data to be removed

            context.scene.DataBakerSettings.data_layers.remove(context.scene.DataBakerSettings.data_layers_selected_index)
            context.scene.DataBakerSettings.data_layers_selected_index = min(max(0, context.scene.DataBakerSettings.data_layers_selected_index), len(context.scene.DataBakerSettings.data_layers) - 1)        

        return{'FINISHED'}

class DATABAKER_OT_NewSettings_MoveItem(Operator):
    """Move an item in the list."""
    bl_idname = "databaker_item.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerSettings.data_layers

    def execute(self, context):
        settings = context.scene.DataBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.data_layers.move(settings.data_layers_selected_index + index_offset, settings.data_layers_selected_index)
        settings.data_layers_selected_index = max(0, min(settings.data_layers_selected_index + index_offset, len(settings.data_layers) - 1))

        return{'FINISHED'}

##############
### Report ###
class DATABAKER_OT_ExportReport(Operator):
    """ """
    bl_idname = "gametools.databaker_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class DATABAKER_OT_ClearReport(Operator):
    """ Bakes object & skeletal animations of the active mesh into textures, storing positional & normal data per vertex. """
    bl_idname = "gametools.databaker_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}
