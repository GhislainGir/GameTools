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

from . import Functions
from .Functions import bake, reset_bake_report, export_bake_report, get_data_layer_name

from bl_operators.presets import AddPresetBase

import uuid

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################

##############
### PRESET ###
class DATABAKER_OT_DataBaker_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.databaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'DATABAKER_MT_MainPanel_Presets'

    preset_defines = [ 'settings = bpy.context.scene.DataBakerSettings' ]
    preset_values = [
    'settings.data_layers',
    'settings.data_layers_selected_index',
    'settings.mesh_name',
    'settings.mesh_uvmap_name',
    'settings.mesh_materials',
    'settings.mesh_merge',
    'settings.mesh_duplicate',
    'settings.mesh_single_user',
    'settings.unit_scale',
    'settings.unit_invert_x',
    'settings.unit_invert_y',
    'settings.unit_invert_z',
    'settings.unit_invert_v',
    'settings.unit_axis_order',
    'settings.origin_obj',
    'settings.clear_attributes',
    'settings.packing_precision',
    'settings.export_mesh',
    'settings.export_mesh_file_name',
    'settings.export_mesh_file_path',
    'settings.export_mesh_file_override',
    'settings.export_xml',
    'settings.export_xml_mode',
    'settings.export_xml_file_name',
    'settings.export_xml_file_path',
    'settings.export_xml_override'
    ]

    preset_subdir = 'operator/gametools_databaker'

############
### MAIN ###
class DATABAKER_OT_BakeData(bpy.types.Operator):
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

###################
### DATA LAYERS ###
class DATABAKER_OT_NewSettings_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "databaker_item.new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.DataBakerSettings
        last_item = None
        current_index = settings.data_layers_selected_index
        if settings.data_layers and (current_index < len(settings.data_layers)):
            last_item = settings.data_layers[current_index]

        settings.data_layers.add()
        last_index = len(settings.data_layers) - 1
        if last_index >= 0:
            settings.data_layers_selected_index = last_index

            item = settings.data_layers[last_index]
            item.ID = uuid.uuid4().hex
            item.ptr = 0

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

                #to_data_layer.ptr = from_data_layer.ptr

                to_data_layer.pack_x_y = from_data_layer.pack_x_y
                to_data_layer.pack_x_y_z = from_data_layer.pack_x_y_z

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

class DATABAKER_OT_NewSettings_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "databaker_item.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerSettings.data_layers

    def execute(self, context):
        settings = context.scene.DataBakerSettings
        if settings.data_layers and (settings.data_layers_selected_index < len(settings.data_layers)):
            """
            1. cache (layer, target_layer_ID) pairs
            """
            layer_mappings = []
            for data_layer in settings.data_layers:
                try:
                    target_data_layer = settings.data_layers[data_layer.ptr]
                except:
                    target_data_layer = None

                if target_data_layer:
                    target_ID = target_data_layer.ID
                else:
                    target_ID = ""

                layer_mappings.append((data_layer, target_ID))

            """
            2. remove entry from list
            """
            settings.data_layers.remove(settings.data_layers_selected_index)
            settings.data_layers_selected_index = min(max(0, settings.data_layers_selected_index), len(settings.data_layers) - 1)

            """
            3. update ptrs
            """
            # for each (layer, target_layer_ID) pair
            for layer_mapping in layer_mappings:
                mapped_data_layer, mapped_target_ID = layer_mapping
                # for each layer
                for data_layer in settings.data_layers:
                    # find pair in layers list
                    if data_layer.ID == mapped_data_layer.ID:
                        # for each layer
                        for other_data_layer_index, other_data_layer in enumerate(settings.data_layers):
                            # find layer originally targeted
                            if other_data_layer.ID == mapped_target_ID:
                                # update int ptr with new index
                                data_layer.ptr = other_data_layer_index
                                break
                        break

        return{'FINISHED'}

class DATABAKER_OT_NewSettings_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "databaker_item.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerSettings.data_layers and len(context.scene.DataBakerSettings.data_layers) > 1

    def execute(self, context):
        settings = context.scene.DataBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1

        if (settings.data_layers_selected_index + index_offset) >= 0 and (settings.data_layers_selected_index + index_offset) < len(settings.data_layers):
            """
            1. cache (layer, target_layer_ID) pairs
            """
            layer_mappings = []
            for data_layer in settings.data_layers:
                try:
                    target_data_layer = settings.data_layers[data_layer.ptr]
                except:
                    target_data_layer = None

                if target_data_layer:
                    target_ID = target_data_layer.ID
                else:
                    target_ID = ""

                layer_mappings.append((data_layer, target_ID))

            """
            2. reorder list
            """
            settings.data_layers.move(settings.data_layers_selected_index + index_offset, settings.data_layers_selected_index)
            settings.data_layers_selected_index = max(0, min(settings.data_layers_selected_index + index_offset, len(settings.data_layers) - 1))

            """
            3. update ptrs
            """
            # for each (layer, target_layer_ID) pair
            for layer_mapping in layer_mappings:
                mapped_data_layer, mapped_target_ID = layer_mapping
                # for each layer
                for data_layer in settings.data_layers:
                    # find pair in layers list
                    if data_layer.ID == mapped_data_layer.ID:
                        # for each layer
                        for other_data_layer_index, other_data_layer in enumerate(settings.data_layers):
                            # find layer originally targeted
                            if other_data_layer.ID == mapped_target_ID:
                                # update int ptr with new index
                                data_layer.ptr = other_data_layer_index
                                break
                        break

        return{'FINISHED'}

class DATABAKER_OT_DataLayerTarget_ChangePtr(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "databaker_target.change_ptr"
    bl_label = "Select another layer to target for packing"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        settings = context.scene.DataBakerSettings

        try:
            data_layer = settings.data_layers[settings.data_layers_selected_index]
        except:
            return False

        return True

    def execute(self, context):
        settings = context.scene.DataBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        try:
            data_layer = settings.data_layers[settings.data_layers_selected_index]

            prev_ptr = data_layer.ptr
            
            data_layer.ptr += index_offset
            if data_layer.ptr == settings.data_layers_selected_index:
                if self.direction == 'UP':
                    data_layer.ptr -= 1
                else:
                    data_layer.ptr += 1

            data_layer.ptr = max(0, min(len(settings.data_layers) - 1, data_layer.ptr))

            if data_layer.ptr == settings.data_layers_selected_index:
                data_layer.ptr = max(0, min(len(settings.data_layers) - 1, prev_ptr))

            return{'FINISHED'}
        except:
            return {'CANCELLED'}

##############
### REPORT ###
class DATABAKER_OT_ExportReport(bpy.types.Operator):
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

class DATABAKER_OT_ClearReport(bpy.types.Operator):
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
