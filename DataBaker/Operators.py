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
from .Functions import bake, reset_bake_report, export_bake_report

from bl_operators.presets import AddPresetBase

import uuid

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################
class DATABAKER_OT_BakeData(Operator):
    """Bakes various data such as pivots and axis into UVs or VCols."""
    bl_idname = "gametools.databaker_bakedata"
    bl_label = "Bake"
    bl_category = "Game Tools"
    bl_options = {'REGISTER', 'UNDO'}

    # tooltip: bpy.props.StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")

    # @classmethod
    # def description(cls, context, operator):
    #     return operator.tooltip

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
    'settings.data_layers',
    'settings.data_layers_selected_index',
    'settings.world_obj',
    'settings.mesh_name',
    'settings.scale',
    'settings.invert_x',
    'settings.invert_y',
    'settings.invert_z',
    'settings.origin',
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

###################
### DATA LAYERS ###
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
                to_data_layer = item
                from_data_layer = last_item

                to_data_layer.data = from_data_layer.data

                # automatically wrap XYZ component
                to_data_layer.component = "X" if from_data_layer.component == "Z" else "Y" if from_data_layer.component == "X" else "Z"

                # automatically wrap uv/vcol rgba/normal xyz
                to_data_layer.packing_mode = from_data_layer.packing_mode
                if from_data_layer.packing_mode == "UV":
                    to_data_layer.uv_channel = "U" if from_data_layer.uv_channel == "V" else "V"
                    to_data_layer.uv_index = from_data_layer.uv_index + 1 if from_data_layer.uv_channel == "V" else from_data_layer.uv_index
                elif from_data_layer.packing_mode == "VCOL":
                    to_data_layer.vcol_rgba = "A" if from_data_layer.vcol_rgba == "B" else "B" if from_data_layer.vcol_rgba == "G" else "G" if from_data_layer.vcol_rgba == "R" else "R"
                elif from_data_layer.packing_mode == "NORMAL":
                    to_data_layer.normal_xyz = "Z" if from_data_layer.normal_xyz == "Y" else "Y" if from_data_layer.normal_xyz == "X" else "X"
                else:
                    pass

                to_data_layer.pack_x_y = from_data_layer.pack_x_y
                to_data_layer.pack_x_y_z = from_data_layer.pack_x_y_z
                to_data_layer.pack_only_if_non_null = from_data_layer.pack_only_if_non_null

                to_data_layer.axis = from_data_layer.axis
                to_data_layer.axis_mode = from_data_layer.axis_mode
                to_data_layer.axis_obj = from_data_layer.obj

                to_data_layer.name = from_data_layer.name

                to_data_layer.obj = from_data_layer.obj

                to_data_layer.vertex_mode = from_data_layer.vertex_mode
                
                to_data_layer.mask_mode = from_data_layer.mask_mode

                to_data_layer.normalize = from_data_layer.normalize
                to_data_layer.clamp = from_data_layer.clamp
                to_data_layer.falloff = from_data_layer.falloff
                to_data_layer.uniform = from_data_layer.uniform

                to_data_layer.origin_mode = from_data_layer.origin_mode

                to_data_layer.rand_mode = from_data_layer.rand_mode
                to_data_layer.rand_seed = from_data_layer.rand_seed
                to_data_layer.rand_float_mode = from_data_layer.rand_float_mode

                to_data_layer.x = from_data_layer.x
                to_data_layer.y = from_data_layer.y
                to_data_layer.z = from_data_layer.z
                to_data_layer.index = from_data_layer.index

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
    """Export the bake report to an XML file, according to the XML export settings."""
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
    """Clear the bake report."""
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
