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

from bl_operators.presets import AddPresetBase
from bl_ui.utils import PresetPanel

from . import Functions
from .Functions import get_bake_info, get_position_data_needs_multiplier, get_parent_position_data_needs_multiplier, get_shapekey_offset_data_needs_multiplier

####################################################################################
###################################### PANELS ######################################
####################################################################################
class DATABAKER_MT_DataBaker_Presets(bpy.types.Menu):
    bl_label = 'DATA Baker Presets'
    preset_subdir = 'operator/databaker_data'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class DATABAKER_OT_DataBaker_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'databaker_databakerpanel.addpreset'
    bl_label = 'Add preset'
    preset_menu = 'DATABAKER_MT_DataBaker_Presets'

    preset_defines = [ 'settings = bpy.context.scene.DataBakerSettings' ]

    preset_values = [  
    'settings.transform_obj',
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

class DATABAKER_PT_DataBaker_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'DATA Baker Presets'
    preset_subdir = 'operator/databaker_data'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'databaker_databakerpanel.addpreset'

class DATABAKER_PT_DataBaker(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_databakerpanel"
    bl_label = "Data Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as we have an active object
        if context.view_layer.objects.active == None:
            return False

        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True

        return False

    def draw_header_preset(self, _context):
        DATABAKER_PT_DataBaker_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        row = layout.row()
        row.scale_y = 2.0 # bigger button
        row.operator("gametools.databaker_bakedata")
        
        row.enabled = (
        settings.position and (settings.position_x or settings.position_y or settings.position_z or settings.position_channel_mode == "AB_PACKED" or settings.position_channel_mode == "XYZ_PACKED") or
        settings.axis and (settings.axis_x or settings.axis_y or settings.axis_z or settings.axis_channel_mode == "AB_PACKED" or settings.axis_channel_mode == "XYZ_PACKED") or
        settings.shapekey_offset and (settings.shapekey_offset_x or settings.shapekey_offset_y or settings.shapekey_offset_z or settings.shapekey_offset_channel_mode == "AB_PACKED" or settings.shapekey_offset_channel_mode == "XYZ_PACKED") or
        settings.shapekey_normal and (settings.shapekey_normal_x or settings.shapekey_normal_y or settings.shapekey_normal_z or settings.shapekey_normal_channel_mode == "AB_PACKED" or settings.shapekey_normal_channel_mode == "XYZ_PACKED") or
        settings.sphere_mask or
        settings.linear_mask or
        settings.random_per_collection or
        settings.random_per_object or
        settings.random_per_poly or
        settings.parent_position and (settings.parent_position_x or settings.parent_position_y or settings.parent_position_z or settings.parent_position_channel_mode == "AB_PACKED" or settings.parent_position_channel_mode == "XYZ_PACKED") or
        settings.parent_axis and (settings.parent_axis_x or settings.parent_axis_y or settings.parent_axis_z or settings.parent_axis_channel_mode == "AB_PACKED" or settings.parent_axis_channel_mode == "XYZ_PACKED") or
        settings.fixed_value or
        settings.direction)

############
### DATA ###
class DATABAKER_PT_Data(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_datapanel"
    bl_parent_id = "DATABAKER_PT_databakerpanel"
    bl_label = "Data"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

# TRANSFORM #
class DATABAKER_PT_TransformPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_transformpanel"
    bl_parent_id = "DATABAKER_PT_datapanel"
    bl_label = "Transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 0
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "transform_obj")

# POSITION #
class DATABAKER_PT_PositionPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_positionpanel"
    bl_parent_id = "DATABAKER_PT_transformpanel"
    bl_label = "Position"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 0
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.position
        layout.prop(settings, "position", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        position_bake_option_enabled = settings.position
        
        row = layout.row()
        row.prop(settings, "position_channel_mode")
        row.enabled = position_bake_option_enabled
        
        if settings.position_channel_mode == "INDIVIDUAL":
            position_bake_option_enabled = position_bake_option_enabled and (settings.position_x or settings.position_y or settings.position_z)

class DATABAKER_PT_PositionXPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_positionxpanel"
    bl_parent_id = "DATABAKER_PT_positionpanel"
    bl_label = "X"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.position_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.position_x
        layout.prop(settings, "position_x", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        bake_option_enabled = settings.position_x
        
        row = layout.row()
        row.prop(settings, "position_x_mode")
        row.enabled = bake_option_enabled

        if settings.position_x_mode == "UV":
            row = layout.row()
            row.prop(settings, "position_x_uv_index")
            row.enabled = bake_option_enabled
        
            row = layout.row()
            row.prop(settings, "position_x_uv_channel")
            row.enabled = bake_option_enabled

        else:
            row = layout.row()
            row.prop(settings, "position_x_rgba")
            row.enabled = bake_option_enabled

class DATABAKER_PT_PositionYPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_positionypanel"
    bl_parent_id = "DATABAKER_PT_positionpanel"
    bl_label = "Y"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.position_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.position_y
        layout.prop(settings, "position_y", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        bake_option_enabled = settings.position_y
        
        row = layout.row()
        row.prop(settings, "position_y_mode")
        row.enabled = settings.position_y

        if settings.position_y_mode == "UV":
            row = layout.row()
            row.prop(settings, "position_y_uv_index")
            row.enabled = bake_option_enabled
        
            row = layout.row()
            row.prop(settings, "position_y_uv_channel")
            row.enabled = bake_option_enabled

        else:
            row = layout.row()
            row.prop(settings, "position_y_rgba")
            row.enabled = bake_option_enabled

class DATABAKER_PT_PositionZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_positionzpanel"
    bl_parent_id = "DATABAKER_PT_positionpanel"
    bl_label = "Z"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.position_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.position_z
        layout.prop(settings, "position_z", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        bake_option_enabled = settings.position_z
        
        row = layout.row()
        row.prop(settings, "position_z_mode")
        row.enabled = bake_option_enabled

        if settings.position_z_mode == "UV":
            row = layout.row()
            row.prop(settings, "position_z_uv_index")
            row.enabled = bake_option_enabled
        
            row = layout.row()
            row.prop(settings, "position_z_uv_channel")
            row.enabled = bake_option_enabled

        else:
            row = layout.row()
            row.prop(settings, "position_z_rgba")
            row.enabled = bake_option_enabled

class DATABAKER_PT_PositionXYZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_positionxyzpanel"
    bl_parent_id = "DATABAKER_PT_positionpanel"
    bl_label = "XYZ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.position_channel_mode == "XYZ_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "position_packed_uv_index")
    
        row = layout.row()
        row.prop(settings, "position_packed_uv_channel")
        
        row = layout.row()
        row.prop(settings, "position_pack_only_if_non_null")

class DATABAKER_PT_PositionABPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_positionabpanel"
    bl_parent_id = "DATABAKER_PT_positionpanel"
    bl_label = "AB"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.position_channel_mode == "AB_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "position_packed_uv_index")
    
        row = layout.row()
        row.prop(settings, "position_packed_uv_channel")
        
        row = layout.row()
        row.prop(settings, "position_pack_only_if_non_null")
        
        row = layout.row()
        row.prop(settings, "position_ab_packed_a_comp")
        
        row = layout.row()
        row.prop(settings, "position_ab_packed_b_comp")

# AXIS #
class DATABAKER_PT_AxisPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_axispanel"
    bl_parent_id = "DATABAKER_PT_transformpanel"
    bl_label = "Axis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.axis
        layout.prop(settings, "axis", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        axis_bake_option_enabled = settings.axis
        
        row = layout.row()
        row.prop(settings, "axis_channel_mode")
        row.enabled = axis_bake_option_enabled
        
        if settings.axis_channel_mode == "INDIVIDUAL":
            axis_bake_option_enabled = axis_bake_option_enabled and (settings.axis_x or settings.axis_y or settings.axis_z)
        elif settings.axis_channel_mode == "POSITION_PACKED":
            Icon = "INFO" if settings.position_channel_mode != "INDIVIDUAL" else "CHECKMARK"
            row = layout.row()
            row.label(text="Position mode must be INDIVIDUAL!", icon=Icon)
        
        row = layout.row()
        row.prop(settings, "axis_component")
        row.enabled = axis_bake_option_enabled

class DATABAKER_PT_AxisXPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_axisxpanel"
    bl_parent_id = "DATABAKER_PT_axispanel"
    bl_label = "X Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.axis_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.axis_x
        layout.prop(settings, "AxisX", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "axis_x_mode")
        row.enabled = settings.axis_x

        if settings.axis_x_mode == "UV":
            row = layout.row()
            row.prop(settings, "axis_x_uv_index")
            row.enabled = settings.axis_x

            row = layout.row()
            row.prop(settings, "axis_x_uv_channel")
            row.enabled = settings.axis_x

        else:
            row = layout.row()
            row.prop(settings, "axis_x_rgba")
            row.enabled = settings.axis_x

class DATABAKER_PT_AxisYPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_axisypanel"
    bl_parent_id = "DATABAKER_PT_axispanel"
    bl_label = "Y Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.axis_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.axis_y
        layout.prop(settings, "axis_y", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "axis_y_mode")
        row.enabled = settings.axis_y

        if settings.axis_y_mode == "UV":
            row = layout.row()
            row.prop(settings, "axis_y_uv_index")
            row.enabled = settings.axis_y

            row = layout.row()
            row.prop(settings, "axis_y_uv_channel")
            row.enabled = settings.axis_y

        else:
            row = layout.row()
            row.prop(settings, "axis_y_RGBA")
            row.enabled = settings.axis_y

class DATABAKER_PT_AxisZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_axiszpanel"
    bl_parent_id = "DATABAKER_PT_axispanel"
    bl_label = "Z Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.axis_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.axis_z
        layout.prop(settings, "axis_z", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "axis_z_mode")
        row.enabled = settings.axis_z

        if settings.axis_z_mode == "UV":
            row = layout.row()
            row.prop(settings, "axis_z_uv_index")
            row.enabled = settings.axis_z
        
            row = layout.row()
            row.prop(settings, "axis_z_uv_channel")
            row.enabled = settings.axis_z

        else:        
            row = layout.row()
            row.prop(settings, "axis_z_rgba")
            row.enabled = settings.axis_z

class DATABAKER_PT_AxisXYZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_axisxyzpanel"
    bl_parent_id = "DATABAKER_PT_axispanel"
    bl_label = "XYZ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.axis_channel_mode == "XYZ_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "axis_packed_uv_index")
    
        row = layout.row()
        row.prop(settings, "axis_packed_uv_channel")

class DATABAKER_PT_AxisABPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_axisabpanel"
    bl_parent_id = "DATABAKER_PT_axispanel"
    bl_label = "AB"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.axis_channel_mode == "AB_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "axis_packed_uv_index")
    
        row = layout.row()
        row.prop(settings, "axis_packed_uv_channel")
        
        row = layout.row()
        row.prop(settings, "axis_ab_packed_a_comp")
        
        row = layout.row()
        row.prop(settings, "axis_ab_packed_b_comp")

# SHAPEKEY #
class DATABAKER_PT_ShapekeyPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeypanel"
    bl_parent_id = "DATABAKER_PT_datapanel"
    bl_label = "Shapekey"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 50
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True

        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "shapekey_name")
        
        row = layout.row()
        row.prop(settings, "shapekey_rest_name")

# SHAPEKEY OFFSET #
class DATABAKER_PT_ShapekeyOffsetPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeyoffsetpanel"
    bl_parent_id = "DATABAKER_PT_shapekeypanel"
    bl_label = "Offset"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_offset
        layout.prop(settings, "shapekey_offset", text="")


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        shapekey_offset_bake_option_enabled = settings.shapekey_offset
        
        row = layout.row()
        row.prop(settings, "shapekey_offset_channel_mode")
        row.enabled = shapekey_offset_bake_option_enabled
        
        if settings.shapekey_offset_channel_mode == "INDIVIDUAL":
            shapekey_offset_bake_option_enabled = shapekey_offset_bake_option_enabled and (settings.shapekey_offset_x or settings.shapekey_offset_y or settings.shapekey_offset_z)

class DATABAKER_PT_ShapekeyOffsetXPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeyoffsetxpanel"
    bl_parent_id = "DATABAKER_PT_shapekeyoffsetpanel"
    bl_label = "X"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_offset_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_offset_x
        layout.prop(settings, "shapekey_offset_x", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
    
        row = layout.row()
        row.prop(settings, "shapekey_offset_x_mode")
        row.enabled = settings.shapekey_offset_x

        if settings.shapekey_offset_x_mode == "UV":
            row = layout.row()
            row.prop(settings, "shapekey_offset_x_uv_index")
            row.enabled = settings.shapekey_offset_x
        
            row = layout.row()
            row.prop(settings, "shapekey_offset_x_uv_channel")
            row.enabled = settings.shapekey_offset_x

        else:
            row = layout.row()
            row.prop(settings, "shapekey_offset_x_rgba")
            row.enabled = settings.shapekey_offset_x

class DATABAKER_PT_ShapekeyOffsetYPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeyoffsetypanel"
    bl_parent_id = "DATABAKER_PT_shapekeyoffsetpanel"
    bl_label = "Y"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_offset_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_offset_y
        layout.prop(settings, "shapekey_offset_y", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "shapekey_offset_y_mode")
        row.enabled = settings.shapekey_offset_y

        if settings.shapekey_offset_y_mode == "UV":
            row = layout.row()
            row.prop(settings, "shapekey_offset_y_uv_index")
            row.enabled = settings.shapekey_offset_y
        
            row = layout.row()
            row.prop(settings, "shapekey_offset_y_uv_channel")
            row.enabled = settings.shapekey_offset_y

        else:        
            row = layout.row()
            row.prop(settings, "shapekey_offset_y_rgba")
            row.enabled = settings.shapekey_offset_y

class DATABAKER_PT_ShapekeyOffsetZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeyoffsetzpanel"
    bl_parent_id = "DATABAKER_PT_shapekeyoffsetpanel"
    bl_label = "Z"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_offset_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_offset_z
        layout.prop(settings, "shapekey_offset_z", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
    
        row = layout.row()
        row.prop(settings, "shapekey_offset_z_mode")
        row.enabled = settings.shapekey_offset_z

        if settings.shapekey_offset_z_mode == "UV":
            row = layout.row()
            row.prop(settings, "shapekey_offset_z_uv_index")
            row.enabled = settings.shapekey_offset_z
        
            row = layout.row()
            row.prop(settings, "shapekey_offset_z_uv_channel")
            row.enabled = settings.shapekey_offset_z

        else:
            row = layout.row()
            row.prop(settings, "shapekey_offset_z_rgba")
            row.enabled = settings.shapekey_offset_z

class DATABAKER_PT_ShapekeyOffsetXYZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeyoffsetxyzpanel"
    bl_parent_id = "DATABAKER_PT_shapekeyoffsetpanel"
    bl_label = "XYZ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_offset_channel_mode == "XYZ_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
    
        row = layout.row()
        row.prop(settings, "shapekey_offset_packed_uv_index")

        row = layout.row()
        row.prop(settings, "shapekey_offset_packed_uv_channel")
        
        row = layout.row()
        row.prop(settings, "shapekey_offset_pack_only_if_non_null")

class DATABAKER_PT_ShapekeyOffsetABPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeyoffsetabpanel"
    bl_parent_id = "DATABAKER_PT_shapekeyoffsetpanel"
    bl_label = "AB"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_offset_channel_mode == "AB_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
    
        row = layout.row()
        row.prop(settings, "shapekey_offset_packed_uv_index")

        row = layout.row()
        row.prop(settings, "shapekey_offset_packed_uv_channel")
        
        row = layout.row()
        row.prop(settings, "shapekey_offset_pack_only_if_non_null")
        
        row = layout.row()
        row.prop(settings, "shapekey_offset_ab_packed_a_comp")
        
        row = layout.row()
        row.prop(settings, "shapekey_offset_ab_packed_b_comp")

# SHAPEKEY NORMAL #
class DATABAKER_PT_ShapekeyNormalPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeynormalpanel"
    bl_parent_id = "DATABAKER_PT_shapekeypanel"
    bl_label = "Normal"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_normal
        layout.prop(settings, "shapekey_normal", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        bake_option_enabled = settings.shapekey_normal

        row = layout.row()
        row.prop(settings, "shapekey_normal_channel_mode")
        row.enabled = bake_option_enabled
        
        if settings.shapekey_normal_channel_mode == "INDIVIDUAL":
            bake_option_enabled = bake_option_enabled and (settings.shapekey_normal_x or settings.shapekey_normal_y or settings.shapekey_normal_z)
        elif settings.shapekey_normal_channel_mode == "OFFSET_PACKED":
            Icon = "INFO" if settings.shapekey_offset_channel_mode != "INDIVIDUAL" else "CHECKMARK"
            row = layout.row()
            row.label(text="Offset mode must be INDIVIDUAL!", icon="INFO")

class DATABAKER_PT_ShapekeyNormalXPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeynormalxpanel"
    bl_parent_id = "DATABAKER_PT_shapekeynormalpanel"
    bl_label = "X Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_normal_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_normal_x
        layout.prop(settings, "shapekey_normal_x", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "ShapekeyNormalXMode")
        row.enabled = settings.shapekey_normal_x

        if settings.shapekey_normal_x_mode == "UV":
            row = layout.row()
            row.prop(settings, "shapekey_normal_x_uv_index")
            row.enabled = settings.shapekey_normal_x
        
            row = layout.row()
            row.prop(settings, "shapekey_normal_x_uv_channel")
            row.enabled = settings.shapekey_normal_x

        else:
            row = layout.row()
            row.prop(settings, "shapekey_normal_x_rgba")
            row.enabled = settings.shapekey_normal_x

class DATABAKER_PT_ShapekeyNormalYPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeynormalypanel"
    bl_parent_id = "DATABAKER_PT_shapekeynormalpanel"
    bl_label = "Y Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_normal_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_normal_y
        layout.prop(settings, "shapekey_normal_y", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "shapekey_normal_y_mode")
        row.enabled = settings.shapekey_normal_y

        if settings.shapekey_normal_y_mode == "UV":
            row = layout.row()
            row.prop(settings, "shapekey_normal_y_uv_index")
            row.enabled = settings.shapekey_normal_y
        
            row = layout.row()
            row.prop(settings, "shapekey_normal_y_uv_channel")
            row.enabled = settings.shapekey_normal_y

        else:
            row = layout.row()
            row.prop(settings, "shapekey_normal_y_rgba")
            row.enabled = settings.shapekey_normal_y

class DATABAKER_PT_ShapekeyNormalZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeynormalzpanel"
    bl_parent_id = "DATABAKER_PT_shapekeynormalpanel"
    bl_label = "Z Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_normal_channel_mode == "INDIVIDUAL":
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.shapekey_normal_z
        layout.prop(settings, "shapekey_normal_z", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "shapekey_normal_z_mode")
        row.enabled = settings.shapekey_normal_z

        if settings.shapekey_normal_z_mode == "UV":
            row = layout.row()
            row.prop(settings, "shapekey_normal_z_uv_index")
            row.enabled = settings.shapekey_normal_z
        
            row = layout.row()
            row.prop(settings, "shapekey_normal_z_uv_channel")
            row.enabled = settings.shapekey_normal_z

        else:
            row = layout.row()
            row.prop(settings, "shapekey_normal_z_rgba")
            row.enabled = settings.shapekey_normal_z

class DATABAKER_PT_ShapekeyNormalXYZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeynormalxyzpanel"
    bl_parent_id = "DATABAKER_PT_shapekeynormalpanel"
    bl_label = "XYZ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_normal_channel_mode == "XYZ_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "shapekey_normal_xyz_uv_index")
    
        row = layout.row()
        row.prop(settings, "shapekey_normal_xyz_uv_channel")

class DATABAKER_PT_ShapekeyNormalABPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_shapekeynormalabpanel"
    bl_parent_id = "DATABAKER_PT_shapekeynormalpanel"
    bl_label = "AB"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.shapekey_normal_channel_mode == "AB_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "shapekey_normal_xyz_uv_index")
    
        row = layout.row()
        row.prop(settings, "shapekey_normal_xyz_uv_channel")
        
        row = layout.row()
        row.prop(settings, "shapekey_normal_ab_packed_a_comp")
        
        row = layout.row()
        row.prop(settings, "shapekey_normal_ab_packed_b_comp")

# MASK #
class DATABAKER_PT_MaskPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_maskpanel"
    bl_parent_id = "DATABAKER_PT_datapanel"
    bl_label = "Masks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 80
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

# SPHERE MASK #
class DATABAKER_PT_SphereMaskPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_spheremaskpanel"
    bl_parent_id = "DATABAKER_PT_maskpanel"
    bl_label = "Sphere Mask"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.sphere_mask
        layout.prop(settings, "sphere_mask", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        
        row = layout.row()
        row.prop(settings, "sphere_mask_origin_mode")
        row.enabled = settings.sphere_mask
        
        if settings.sphere_mask_origin_mode == "OBJECT":
            row = layout.row()
            row.prop(settings, "sphere_mask_origin")
            row.enabled = settings.sphere_mask
        
        row = layout.row()
        row.prop(settings, "sphere_mask_mode")
        row.enabled = settings.sphere_mask

        if settings.sphere_mask_mode == "UV":
            row = layout.row()
            row.prop(settings, "sphere_mask_normalize")
            row.enabled = settings.sphere_mask

            row = layout.row()
            row.prop(settings, "sphere_mask_clamp")
            row.enabled = settings.sphere_mask


            row = layout.row()
            row.prop(settings, "sphere_mask_uv_index")
            row.enabled = settings.sphere_mask

            row = layout.row()
            row.prop(settings, "sphere_mask_uv_channel")
            row.enabled = settings.sphere_mask

        else:
            row = layout.row()
            row.prop(settings, "sphere_mask_rgba")
            row.enabled = settings.sphere_mask
            
        row = layout.row()
        row.prop(settings, "sphere_mask_falloff")
        row.enabled = settings.sphere_mask and (settings.sphere_mask_normalize or settings.sphere_mask_mode == "VCOL")

# LINEAR MASK #
class DATABAKER_PT_LinearMaskPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_linearmaskpanel"
    bl_parent_id = "DATABAKER_PT_maskpanel"
    bl_label = "Linear Mask"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.linear_mask
        layout.prop(settings, "linear_mask", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "linear_mask_obj_mode")
        row.enabled = settings.linear_mask
        
        if settings.linear_mask_obj_mode == "OBJECT":
            row = layout.row()
            row.prop(settings, "linear_mask_obj")
            row.enabled = settings.linear_mask
        
        row = layout.row()
        row.prop(settings, "linear_mask_mode")
        row.enabled = settings.linear_mask

        if settings.linear_mask_mode == "UV":
            row = layout.row()
            row.prop(settings, "linear_mask_normalize")
            row.enabled = settings.linear_mask
            
            row = layout.row()
            row.prop(settings, "linear_mask_clamp")
            row.enabled = settings.linear_mask

            row = layout.row()
            row.prop(settings, "linear_mask_uv_index")
            row.enabled = settings.linear_mask
        
            row = layout.row()
            row.prop(settings, "linear_mask_uv_channel")
            row.enabled = settings.linear_mask

        else:
            row = layout.row()
            row.prop(settings, "linear_mask_rgba")
            row.enabled = settings.linear_mask
            
        row = layout.row()
        row.prop(settings, "linear_mask_axis")
        row.enabled = settings.linear_mask
            
        row = layout.row()
        row.prop(settings, "linear_mask_falloff")
        row.enabled = settings.linear_mask and (settings.linear_mask_normalize or settings.linear_mask_mode == "VCOL")

# RANDOM #
class DATABAKER_PT_RandomPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_randompanel"
    bl_parent_id = "DATABAKER_PT_datapanel"
    bl_label = "Random"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 90

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

# RANDOM PER COLLECTION #
class DATABAKER_PT_RandomPerCollectionPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_randompercollectionpanel"
    bl_parent_id = "DATABAKER_PT_randompanel"
    bl_label = "Random Per Collection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.random_per_collection
        layout.prop(settings, "random_per_collection", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "random_per_collection_mode")
        row.enabled = settings.random_per_collection

        if settings.random_per_collection_mode == "UV":
            row = layout.row()
            row.prop(settings, "random_per_collection_uv_index")
            row.enabled = settings.random_per_collection
        
            row = layout.row()
            row.prop(settings, "random_per_collection_uv_channel")
            row.enabled = settings.random_per_collection

        else:        
            row = layout.row()
            row.prop(settings, "random_per_collection_rgba")
            row.enabled = settings.random_per_collection
            
        row = layout.row()
        row.prop(settings, "random_per_collection_uniform")
        row.enabled = settings.random_per_collection

# RANDOM PER OBJECT #
class DATABAKER_PT_RandomPerObjectPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_randomperobjectpanel"
    bl_parent_id = "DATABAKER_PT_randompanel"
    bl_label = "Random Per Object"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.random_per_object
        layout.prop(settings, "random_per_object", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "random_per_object_mode")
        row.enabled = settings.random_per_object

        if settings.random_per_object_mode == "UV":
            row = layout.row()
            row.prop(settings, "random_per_object_uv_index")
            row.enabled = settings.random_per_object
        
            row = layout.row()
            row.prop(settings, "random_per_object_uv_channel")
            row.enabled = settings.random_per_object

        else:        
            row = layout.row()
            row.prop(settings, "random_per_object_rgba")
            row.enabled = settings.random_per_object
            
        row = layout.row()
        row.prop(settings, "random_per_object_uniform")
        row.enabled = settings.random_per_object

# RANDOM PER POLY #
class DATABAKER_PT_RandomPerPolyPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_randomperpolypanel"
    bl_parent_id = "DATABAKER_PT_randompanel"
    bl_label = "Random Per Poly"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.random_per_poly
        layout.prop(settings, "random_per_poly", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "random_per_poly_mode")
        row.enabled = settings.random_per_poly

        if settings.random_per_poly_mode == "UV":
            row = layout.row()
            row.prop(settings, "random_per_poly_uv_index")
            row.enabled = settings.random_per_poly
        
            row = layout.row()
            row.prop(settings, "random_per_poly_uv_channel")
            row.enabled = settings.random_per_poly

        else:
            row = layout.row()
            row.prop(settings, "random_per_poly_rgba")
            row.enabled = settings.random_per_poly
            
        row = layout.row()
        row.prop(settings, "random_per_poly_uniform")
        row.enabled = settings.random_per_poly

# PARENT #
class DATABAKER_PT_ParentPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpanel"
    bl_parent_id = "DATABAKER_PT_datapanel"
    bl_label = "Parent"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
         
        row = layout.row()
        row.prop(settings, "parent_mode")
                
        row = layout.row()
        row.prop(settings, "parent_max_depth")

        if settings.parent_mode == "AUTOMATIC":
            
            layout.separator(factor=2)
            
            row = layout.row()
            row.prop(settings, "parent_automatic_uv_index")
        
            row = layout.row()
            row.prop(settings, "parent_automatic_uv_channel")
            
        else:
            row = layout.row()
            row.prop(settings, "parent_depth")

# PARENT POSITION #
class DATABAKER_PT_ParentPositionPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpositionpanel"
    bl_parent_id = "DATABAKER_PT_parentpanel"
    bl_label = "Parent Position"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_position
        layout.prop(settings, "parent_position", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        position_bake_option_enabled = settings.parent_position
        
        row = layout.row()
        row.prop(settings, "parent_position_channel_mode")
        row.enabled = position_bake_option_enabled
        
        if settings.parent_mode == "AUTOMATIC" and settings.parent_position_channel_mode == "INDIVIDUAL":
            row = layout.row()
            row.prop(settings, "parent_position_x")
            
            row = layout.row()
            row.prop(settings, "parent_position_y")
            
            row = layout.row()
            row.prop(settings, "parent_position_z")
        
class DATABAKER_PT_ParentPositionXPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpositionxpanel"
    bl_parent_id = "DATABAKER_PT_parentpositionpanel"
    bl_label = "X"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_position_channel_mode == "INDIVIDUAL":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_position_x
        layout.prop(settings, "parent_position_x", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        bake_option_enabled = settings.parent_position_x
        
        row = layout.row()
        row.prop(settings, "parent_position_x_mode")
        row.enabled = bake_option_enabled

        if settings.parent_position_x_mode == "UV":
            row = layout.row()
            row.prop(settings, "parent_position_x_uv_index")
            row.enabled = bake_option_enabled
        
            row = layout.row()
            row.prop(settings, "parent_position_x_uv_channel")
            row.enabled = bake_option_enabled

        else:        
            row = layout.row()
            row.prop(settings, "parent_position_x_rgba")
            row.enabled = bake_option_enabled

class DATABAKER_PT_ParentPositionYPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpositionypanel"
    bl_parent_id = "DATABAKER_PT_parentpositionpanel"
    bl_label = "Y"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_position_channel_mode == "INDIVIDUAL":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_position_y
        layout.prop(settings, "parent_position_y", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        bake_option_enabled = settings.parent_position_y
        
        row = layout.row()
        row.prop(settings, "parent_position_y_mode")
        row.enabled = bake_option_enabled

        if settings.parent_mode != "AUTOMATIC":
            if settings.parent_position_y_mode == "UV":
                row = layout.row()
                row.prop(settings, "parent_position_y_uv_index")
                row.enabled = bake_option_enabled
            
                row = layout.row()
                row.prop(settings, "parent_position_y_uv_channel")
                row.enabled = bake_option_enabled

            else:        
                row = layout.row()
                row.prop(settings, "parent_position_y_rgba")
                row.enabled = bake_option_enabled
            
class DATABAKER_PT_ParentPositionZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpositionzpanel"
    bl_parent_id = "DATABAKER_PT_parentpositionpanel"
    bl_label = "Z"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_position_channel_mode == "INDIVIDUAL":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_position_z
        layout.prop(settings, "parent_position_z", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        bake_option_enabled = settings.parent_position_z
        
        row = layout.row()
        row.prop(settings, "parent_position_z_mode")
        row.enabled = bake_option_enabled

        if settings.parent_mode != "AUTOMATIC":
            if settings.parent_position_z_mode == "UV":
                row = layout.row()
                row.prop(settings, "parent_position_z_uv_index")
                row.enabled = bake_option_enabled
            
                row = layout.row()
                row.prop(settings, "parent_position_z_uv_channel")
                row.enabled = bake_option_enabled

            else:        
                row = layout.row()
                row.prop(settings, "parent_position_z_rgba")
                row.enabled = bake_option_enabled

class DATABAKER_PT_ParentPositionXYZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpositionxyzpanel"
    bl_parent_id = "DATABAKER_PT_parentpositionpanel"
    bl_label = "XYZ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_position_channel_mode == "XYZ_PACKED":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "parent_position_packed_uv_index")
    
        row = layout.row()
        row.prop(settings, "parent_position_packed_uv_channel")

class DATABAKER_PT_ParentPositionABPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentpositionabpanel"
    bl_parent_id = "DATABAKER_PT_parentpositionpanel"
    bl_label = "AB"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_position_channel_mode == "AB_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        if settings.parent_mode != "AUTOMATIC":
            row = layout.row()
            row.prop(settings, "parent_position_packed_uv_index")
        
            row = layout.row()
            row.prop(settings, "parent_position_packed_uv_channel")
            
        row = layout.row()
        row.prop(settings, "parent_position_ab_packed_a_comp")
        
        row = layout.row()
        row.prop(settings, "parent_position_ab_packed_b_comp")

# PARENT AXIS #
class DATABAKER_PT_ParentAxisPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentaxispanel"
    bl_parent_id = "DATABAKER_PT_parentpanel"
    bl_label = "Parent Axis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        # show panel as long as there's at least one mesh selected
        for Object in context.selected_objects:
            if (Object.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_axis
        layout.prop(settings, "parent_axis", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        axis_bake_option_enabled = settings.parent_axis
        
        row = layout.row()
        row.prop(settings, "parent_axis_channel_mode")
        row.enabled = axis_bake_option_enabled
        
        if settings.parent_axis_channel_mode == "INDIVIDUAL":
            axis_bake_option_enabled = axis_bake_option_enabled and (settings.parent_axis_x or settings.parent_axis_y or settings.parent_axis_z)
        elif settings.parent_axis_channel_mode == "POSITION_PACKED":
            Icon = "INFO" if settings.parent_position_channel_mode != "INDIVIDUAL" else "CHECKMARK"
            row = layout.row()
            row.label(text="Parent Position mode must be INDIVIDUAL!", icon="INFO")
        
        row = layout.row()
        row.prop(settings, "parent_axis_component")
        row.enabled = axis_bake_option_enabled
        
        if settings.parent_mode == "AUTOMATIC" and settings.parent_axis_channel_mode == "INDIVIDUAL":
            row = layout.row()
            row.prop(settings, "parent_axis_x")
            
            row = layout.row()
            row.prop(settings, "parent_axis_y")
            
            row = layout.row()
            row.prop(settings, "parent_axis_z")

class DATABAKER_PT_ParentAxisXPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentaxisxpanel"
    bl_parent_id = "DATABAKER_PT_parentaxispanel"
    bl_label = "X Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_axis_channel_mode == "INDIVIDUAL":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_axis_x
        layout.prop(settings, "parent_axis_x", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        DataOptionEnabled = settings.parent_axis_x
        
        row = layout.row()
        row.prop(settings, "parent_axis_x_mode")
        row.enabled = DataOptionEnabled

        if settings.parent_mode != "AUTOMATIC":
            if settings.parent_axis_x_mode == "UV":
                row = layout.row()
                row.prop(settings, "parent_axis_x_uv_index")
                row.enabled = DataOptionEnabled
            
                row = layout.row()
                row.prop(settings, "parent_axis_x_uv_channel")
                row.enabled = DataOptionEnabled

            else:        
                row = layout.row()
                row.prop(settings, "parent_axis_x_rgba")
                row.enabled = DataOptionEnabled

class DATABAKER_PT_ParentAxisYPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentaxisypanel"
    bl_parent_id = "DATABAKER_PT_parentaxispanel"
    bl_label = "Y Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_axis_channel_mode == "INDIVIDUAL":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_axis_y
        layout.prop(settings, "parent_axis_y", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        DataOptionEnabled = settings.parent_axis_y
        
        row = layout.row()
        row.prop(settings, "parent_axis_y_mode")
        row.enabled = DataOptionEnabled

        if settings.parent_mode != "AUTOMATIC":
            if settings.parent_axis_y_mode == "UV":
                row = layout.row()
                row.prop(settings, "parent_axis_y_uv_index")
                row.enabled = DataOptionEnabled
            
                row = layout.row()
                row.prop(settings, "parent_axis_y_uv_channel")
                row.enabled = DataOptionEnabled

            else:        
                row = layout.row()
                row.prop(settings, "parent_axis_y_rgba")
                row.enabled = DataOptionEnabled
            
class DATABAKER_PT_ParentAxisZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentaxiszpanel"
    bl_parent_id = "DATABAKER_PT_parentaxispanel"
    bl_label = "Z Component"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_axis_channel_mode == "INDIVIDUAL":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.parent_axis_z
        layout.prop(settings, "parent_axis_z", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        DataOptionEnabled = settings.parent_axis_z
        
        row = layout.row()
        row.prop(settings, "parent_axis_z_mode")
        row.enabled = DataOptionEnabled

        if settings.parent_mode != "AUTOMATIC":
            if settings.parent_axis_z_mode == "UV":
                row = layout.row()
                row.prop(settings, "parent_axis_z_uv_index")
                row.enabled = DataOptionEnabled
            
                row = layout.row()
                row.prop(settings, "parent_axis_z_uv_channel")
                row.enabled = DataOptionEnabled

            else:        
                row = layout.row()
                row.prop(settings, "parent_axis_z_rgba")
                row.enabled = DataOptionEnabled

class DATABAKER_PT_ParentAxisXYZPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentaxisxyzpanel"
    bl_parent_id = "DATABAKER_PT_parentaxispanel"
    bl_label = "XYZ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_axis_channel_mode == "XYZ_PACKED":
            return context.scene.DataBakerSettings.parent_mode != "AUTOMATIC"
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        if settings.parent_mode != "AUTOMATIC":
            row = layout.row()
            row.prop(settings, "parent_axis_packed_uv_index")
        
            row = layout.row()
            row.prop(settings, "parent_axis_packed_uv_channel")
        
class DATABAKER_PT_ParentAxisABPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_parentaxisabpanel"
    bl_parent_id = "DATABAKER_PT_parentaxispanel"
    bl_label = "AB"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.DataBakerSettings.parent_axis_channel_mode == "AB_PACKED":
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings

        if settings.parent_mode != "AUTOMATIC":
            row = layout.row()
            row.prop(settings, "parent_axis_packed_uv_index")
    
            row = layout.row()
            row.prop(settings, "parent_axis_packed_uv_channel")
        
        row = layout.row()
        row.prop(settings, "parent_axis_ab_packed_a_comp")
        
        row = layout.row()
        row.prop(settings, "parent_axis_ab_packed_b_comp")

# MISC #
class DATABAKER_PT_MiscPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_miscpanel"
    bl_parent_id = "DATABAKER_PT_datapanel"
    bl_label = "Misc"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 100
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

# FIXED VALUE #
class DATABAKER_PT_FixedValuePanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_fixedvaluepanel"
    bl_parent_id = "DATABAKER_PT_miscpanel"
    bl_label = "Fixed Value"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.fixed_value
        layout.prop(settings, "fixed_value", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "fixed_value_data")
        row.enabled = settings.fixed_value

        if settings.fixed_value_mode == "UV":
            row = layout.row()
            row.prop(settings, "fixed_value_uv_index")
            row.enabled = settings.fixed_value
        
            row = layout.row()
            row.prop(settings, "fixed_value_uv_channel")
            row.enabled = settings.fixed_value

        else:
            row = layout.row()
            row.prop(settings, "fixed_value_rgba")
            row.enabled = settings.fixed_value

# DIRECTION #
class DATABAKER_PT_DirectionPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_directionpanel"
    bl_parent_id = "DATABAKER_PT_miscpanel"
    bl_label = "Direction"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # show panel as long as there's at least one mesh selected
        for obj in context.selected_objects:
            if (obj.type == "MESH"):
                return True
        
        return False

    def draw_header(self, context):
        layout = self.layout
        settings = context.scene.DataBakerSettings

        layout.active = settings.direction
        layout.prop(settings, "direction", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "direction_mode")
        row.enabled = settings.direction

        row = layout.row()
        row.prop(settings, "direction_pack_mode")
        row.enabled = settings.direction

        if settings.direction_mode == "2DVECTOR" or settings.direction_mode == "3DVECTOR":
            row = layout.row()
            row.prop(settings, "direction_vector_x")
            row = layout.row()
            row.prop(settings, "direction_vector_y")
            if settings.direction_mode == "3DVECTOR":
                row = layout.row()
                row.prop(settings, "direction_vector_z")

############
### INFO ###
def draw_info_panel_uvs(context, layout, info_uv):
    """ """

    box = layout.box()
    
    # label
    used_uv_channels = []
    uv_channel_override = False
    uv_channel_overflow = False
    warning_32_bits = False
    warning_multiplier = False
    for uvmap_info in info_uv:
        ID, uv_index, uv_channel, is_packed, is_32_bits, has_multiplier, channel_mode = uvmap_info
        if is_32_bits and not warning_32_bits:
            warning_32_bits = True

        if has_multiplier and not warning_multiplier:
            warning_multiplier = True

        uv_channel_index = (uv_index * 2) + (0 if uv_channel == "U" else 1)
        if uv_channel_index in used_uv_channels:
            uv_channel_override = True

        if uv_channel_index > 15:
            uv_channel_overflow = True

        used_uv_channels.append(uv_channel_index)

    box_text = "UV"
    box_icon = "CHECKMARK"
    if warning_32_bits or warning_multiplier:
        box_icon = "INFO"
        if warning_32_bits and warning_multiplier:
            box_text = "UV - 32bits (full precision) & multiplier(s) required!"
        elif warning_32_bits:
            box_text = "UV - 32bits (full precision) required!"
        else:
            box_text = "UV - Multiplier(s) required!"
        
    if uv_channel_override:
        box_text = "UV - Override detected!"
        box_icon = "ERROR"

    if len(info_uv) > 15:
        box_text = "UV - Can't store that many data in UVs!"
        box_icon = "X"
    elif uv_channel_overflow:
        box_text = "UV - UV index exceeding max limit!"
        box_icon = "X"
    elif len(info_uv) == 0:
        box_text = "UV - No data"
        box_icon = "X"

    box.label(text=box_text, icon=box_icon)

    # list UVs
    for uvmap_info in info_uv:
        ID, uv_index, uv_channel, is_packed, is_32_bits, has_multiplier, channel_mode = uvmap_info
        
        uv_channel_index = (uv_index * 2) + (0 if uv_channel == "U" else 1)
        uv_channel_override = len([index for index in used_uv_channels if index == uv_channel_index]) > 1
        
        icon = "RADIOBUT_ON"
        if channel_mode == "AB_PACKED":
            icon = "CON_TRANSLIKE"
        elif channel_mode == "XYZ_PACKED":
            icon = "PRESET_NEW"
        elif channel_mode == "OFFSET_PACKED" or channel_mode == "POSITION_PACKED":
            icon = "ORIENTATION_LOCAL"
        else:
            if is_packed:
                icon = "OBJECT_ORIGIN"
        if uv_channel_override:
            icon = "ERROR"

        if uv_channel_index < 16:
            row = box.row()
            row.label(text=ID + ": UV " + str(uv_index) + " - " + str(uv_channel), icon=icon)
        else:
            row = box.row()
            row.label(text=ID + ": UV " + str(uv_index) + " - Not available", icon="X")

        if has_multiplier:
            if "Parent" in ID:
                row.label(text="", icon="PIVOT_BOUNDBOX")
            elif "Position" in ID:
                row.label(text="", icon="CON_OBJECTSOLVER")
            elif "Offset" in ID:
                row.label(text="", icon="MOD_BEVEL")

def draw_info_panel_vcols(context, layout, info_vcol):
    """ """
    box = layout.box()

    # label
    used_vcols = []
    rgba_channel_override = False
    rgba_packed = False
    for vcol_info in info_vcol:
        ID, vcol_channel, packed = vcol_info
        if vcol_channel in used_vcols:
            rgba_channel_override = True

        if packed:
            rgba_packed = True

        used_vcols.append(vcol_channel)

    box_text = "VCOL"
    box_icon = "CHECKMARK"

    if rgba_packed:
        box_text = "VCOL - Multiplier(s) required!"
        box_icon = "CHECKMARK"

    if rgba_channel_override:
        box_text = "VCOL - Override detected!"
        box_icon = "ERROR"

    if len(info_vcol) == 0:
        box_text = "VCOL - No data"
        box_icon = "X"

    box.label(text=box_text, icon=box_icon)

    # list vcols
    for vcol_info in info_vcol:
        ID, vcol_channel, packed = vcol_info
        
        rgba_channel_override = len([channel for channel in used_vcols if channel == vcol_channel]) > 1

        icon = "COLOR"
        if rgba_channel_override:
            icon = "ERROR"

        row = box.row()
        row.label(text=ID + ": " + vcol_channel, icon=icon)

        if packed:
            if "Parent" in ID:
                row.label(text="", icon="PIVOT_BOUNDBOX")
            elif "Position" in ID:
                row.label(text="", icon="CON_OBJECTSOLVER")
            elif "Offset" in ID:
                row.label(text="", icon="MOD_BEVEL")

def draw_info_panel_normals(context, layout, info_normal):
    """ """
    box = layout.box()

    # label
    normal_overrides = False
    normal_components = []
    for normal_info in info_normal:
        if normal_info in normal_components:
            normal_overrides = True
        
        normal_components.append(normal_info)

    box_text = "NORMAL"
    box_icon = "CHECKMARK"

    if normal_overrides:
        box_text = "NORMAL - Override detected!"
        box_icon = "ERROR"

    if len(info_normal) == 0:
        box_text = "NORMAL - No data"
        box_icon = "X"

    box.label(text=box_text, icon=box_icon)

    # list normals
    for normal_info in info_normal:
        row = box.row()
        row.label(text=normal_info, icon="CHECKMARK")

def draw_info_panel_multipliers(context, layout):
    """ """
    report = context.scene.DataBakerReport

    box = layout.box()

    pos_multiplier = get_position_data_needs_multiplier(context)
    parent_pos_multiplier = get_parent_position_data_needs_multiplier(context)
    shapekey_offset_multiplier = get_shapekey_offset_data_needs_multiplier(context)

    if pos_multiplier or parent_pos_multiplier or shapekey_offset_multiplier:
        box.label(text="MULTIPLIERS", icon="INFO")
    else:
        box.label(text="MULTIPLIERS - None", icon="X")

    if pos_multiplier:
        row = box.row()
        col = row.split()
        col.label(text="Position: ")
        col.label(text=str(report.position_multiplier), icon="CON_OBJECTSOLVER")

        row = box.row()
        row.operator("gametools.databaker_getpositionmultiplier")

    if parent_pos_multiplier:
        row = box.row()
        col = row.split()
        col.label(text="Parent Position: ")
        col.label(text=str(report.parent_position_multiplier), icon="PIVOT_BOUNDBOX")

        row = box.row()
        row.operator("gametools.databaker_getparentoffsetmultipler")

    if shapekey_offset_multiplier:
        row = box.row()
        col = row.split()
        col.label(text="Shakekey Offset: ")
        col.label(text=str(report.shapekey_offset_multiplier), icon="MOD_BEVEL")

        row = box.row()
        row.operator("gametools.databaker_getshapekeyoffsetmultiplier")

class DATABAKER_PT_InfoPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_infopanel"
    bl_parent_id = "DATABAKER_PT_databakerpanel"
    bl_label = "Info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake Data"
    bl_order = 150
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        info_uv, info_vcol, info_normal = get_bake_info(context)
        
        draw_info_panel_uvs(context, layout, info_uv)
        draw_info_panel_vcols(context, layout, info_vcol)
        draw_info_panel_normals(context, layout, info_normal)
        draw_info_panel_multipliers(context, layout)

##########
# MESHES #
class DATABAKER_PT_MeshMainPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_meshmainpanel"
    bl_parent_id = "DATABAKER_PT_databakerpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "origin")

        row = layout.row()
        row.prop(settings, "scale")
        
        row = layout.row()
        row.label(text="Invert")
        row.prop(settings, "invert_x", text="X")
        row.prop(settings, "invert_y", text="Y")
        row.prop(settings, "invert_z", text="Z")
        
        row = layout.row()
        row.prop(settings, "mesh_name")
        row.enabled = settings.merge_mesh

class DATABAKER_PT_MeshUVPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_meshuvpanel"
    bl_parent_id = "DATABAKER_PT_meshmainpanel"
    bl_label = "UV"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "uvmap_name", text="Name")

        row = layout.row()
        row.prop(settings, "invert_v")

class DATABAKER_PT_MeshAdvPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_meshadvpanel"
    bl_parent_id = "DATABAKER_PT_meshmainpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 100
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings
        
        row = layout.row()
        row.prop(settings, "duplicate_mesh")
        
        row = layout.row()
        row.prop(settings, "make_single_user")
        row.enabled = settings.duplicate_mesh == False
        
        row = layout.row()
        row.prop(settings, "merge_mesh")

        row = layout.row()
        row.prop(settings, "clean_bake")
        row.enabled = settings.duplicate_mesh

class DATABAKER_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_meshexportpanel"
    bl_parent_id = "DATABAKER_PT_meshmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 50
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        layout.prop(settings, "export_mesh", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        layout.enabled = settings.export_mesh

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class DATABAKER_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_meshadvexportpanel"
    bl_parent_id = "DATABAKER_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

        row = layout.row()
        row.prop(settings, "precision_offset")
        row.enabled = False

###########
### XML ###
class DATABAKER_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_xmlpanel"
    bl_parent_id = "DATABAKER_PT_databakerpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

class DATABAKER_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_xmlexportpanel"
    bl_parent_id = "DATABAKER_PT_xmlpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.prop(settings, "export_xml", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        row = layout.row()
        row.prop(settings, "export_xml_mode")
        row.enabled = settings.export_mesh

        if (settings.export_xml_mode == "CUSTOMPATH" or not settings.export_mesh):
            row = layout.row()
            row.prop(settings, "export_xml_file_name")

            row = layout.row()
            row.prop(settings, "export_xml_file_path")

            row = layout.row()
            row.prop(settings, "export_xml_override")

##############
### REPORT ###
class DATABAKER_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_reportpanel"
    bl_parent_id = "DATABAKER_PT_databakerpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.DataBakerReport.baked
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.DataBakerReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.databaker_export_report")
            col = row.split()
            col.operator("gametools.databaker_clear_report")

        row = layout.row()
        if report.success:
            row.label(text="Success", icon="CHECKMARK")
        else:
            row.label(text="Fail", icon="ERROR")

        row = layout.row()
        row.prop(report, "ID")

        if not report.success:
            row = layout.row()
            row.label(text=report.msg)

        row = layout.row()
        row.label(text=report.name)

class DATABAKER_UL_ReportUVMapList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.label(text=item.name, translate=False, icon="ANIM_DATA")
            else:
                layout.label(text="", translate=False, icon="ANIM_DATA")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class DATABAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_infomeshpanel"
    bl_parent_id = "DATABAKER_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.DataBakerReport
        row = self.layout.row(align=True)
        if report.mesh or report.meshes_count > 0:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.DataBakerReport

        if report.mesh or report.meshes_count > 0:
            row = layout.row()
            row.prop(report, "mesh", text="")
            row.enabled = False

            row = layout.row()
            if report.mesh_export:
                row.label(text="File: " + report.mesh_path, icon="FILE")
            else:
                row.label(text="Not exported", icon="X")

            layout.separator()

            icon = "CHECKMARK" if report.mesh_uvmap_invert_v else "X"
            row = layout.row()
            row.label(text="Invert V: " + str(report.mesh_uvmap_invert_v), icon=icon)
            row.enabled = report.mesh_uvmap_invert_v

            layout.template_list("DATABAKER_UL_ReportUVMapList", "", report, "mesh_uvmaps", report, "select_mesh_uvmap", rows=6)
            if report.mesh_uvmaps:
                uvmap = report.mesh_uvmaps[report.select_mesh_uvmap]
                if uvmap:
                    row = layout.row()
                    row.label(text=str(uvmap.ID))

        else:
            row = layout.row()
            row.label(text="None generated")

class DATABAKER_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_infoxmlpanel"
    bl_parent_id = "DATABAKER_PT_reportpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.DataBakerReport
        row = self.layout.row(align=True)
        if report.xml:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.DataBakerReport

        row = layout.row()
        if report.xml:
            row.label(text="File: " + report.xml_path, icon="FILE")
        else:
            row.label(text="Not exported", icon="X")

class DATABAKER_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_infounitpanel"
    bl_parent_id = "DATABAKER_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.DataBakerReport

        row = layout.row()
        row.label(text="System: " + report.unit_system)
        row.enabled = report.unit_system != "METRIC"

        row = layout.row()
        row.label(text="Unit: " + report.unit_unit)
        row.enabled = report.unit_unit != "METERS"

        row = layout.row()
        row.label(text="Length: " + str(report.unit_length))
        row.enabled = report.unit_length != 1.0

        row = layout.row()
        row.label(text="Scale: " + str(report.unit_scale))

        layout.separator()
        row = layout.row()
        row.label(text="Invert")

        icon = "CHECKMARK" if report.unit_invert_x else "X"
        row = layout.row()
        row.label(text="X: " + str(report.unit_invert_x), icon=icon)
        row.enabled = report.unit_invert_x

        icon = "CHECKMARK" if report.unit_invert_y else "X"
        row = layout.row()
        row.label(text="Y: " + str(report.unit_invert_y), icon=icon)
        row.enabled = report.unit_invert_y

        icon = "CHECKMARK" if report.unit_invert_z else "X"
        row = layout.row()
        row.label(text="Z: " + str(report.unit_invert_z), icon=icon)
        row.enabled = report.unit_invert_z
