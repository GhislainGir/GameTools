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
from .Functions import *

from bl_operators.presets import AddPresetBase

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################

##############
### PRESET ###
class OBJECTATTRIBUTES_OT_ObjectAttributes_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.objectsattributes_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'OBJECTATTRIBUTES_MT_MainPanel_Presets'

    preset_defines = [ 'settings = bpy.context.scene.ObjectAttributesSettings' ]
    preset_values = [
        'settings.textures',
        'settings.textures_selected_index',
        'settings.depth_limit_use',
        'settings.depth_limit',
        'settings.use_pivot_painter_packing',
        'settings.use_8bit_packing',
        'settings.mesh_name',
        'settings.mesh_materials',
        'settings.mesh_uvmap_name',
        'settings.mesh_count_limit',
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
        'settings.export_mesh',
        'settings.export_mesh_file_name',
        'settings.export_mesh_file_path',
        'settings.export_mesh_file_override',
        'settings.export_xml',
        'settings.export_xml_modes',
        'settings.export_xml_mode',
        'settings.export_xml_file_name',
        'settings.export_xml_file_path',
        'settings.export_xml_override',
        'settings.export_tex',
        'settings.export_tex_file_name',
        'settings.export_tex_file_path',
        'settings.export_tex_override',
        'settings.export_tex_max_width',
        'settings.export_tex_max_height',
        'settings.tex_force_power_of_two',
        'settings.tex_force_power_of_two_square'
    ]

    preset_subdir = 'operator/gametools_objectattributes'

############
### MAIN ###
class OBJECTATTRIBUTES_OT_BakeData(bpy.types.Operator):
    """Bakes various object attributes, such as position, axis, hierarchy, into texture(s)."""
    bl_idname = "gametools.oabaker_bakeoa"
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

class OBJECTATTRIBUTES_OT_SelectDepth(bpy.types.Operator):
    """Configure the depth limit, select all objects to bake and press Filter to deselect all objects that do *not* exceed the depth limit.\n\nThese objects will be treated as if part of their last valid parent. This operator helps identify what will happen during the bake."""
    bl_idname = "gametools.databaker_selectdepth"
    bl_label = "Filter Selection"
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
        success, verbose, msg = filter_selection_depth(context)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

################
### TEXTURES ###
class OBJECTATTRIBUTES_OT_NewSettings_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "objectattributes_item.new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.ObjectAttributesSettings
        last_item = None
        current_index = settings.textures_selected_index
        if settings.textures and (current_index < len(settings.textures)):
            last_item = settings.textures[current_index]

        settings.textures.add()
        last_index = len(settings.textures) - 1
        if last_index >= 0:
            settings.textures_selected_index = last_index

            item = settings.textures[last_index]
            item.ID = uuid.uuid4().hex

            name = "Attributes"
            name_suffix = 0
            names = [skinning_texture.name for skinning_texture in settings.textures]
            while name in names:
                name_suffix += 1
                name_suffix_str = str(name_suffix).zfill(3)
                name = "Attributes." + name_suffix_str
            item.name = name

            if last_item:
                pass

        return{'FINISHED'}

class OBJECTATTRIBUTES_OT_NewSettings_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "objectattributes_item.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.ObjectAttributesSettings.textures

    def execute(self, context):
        if context.scene.ObjectAttributesSettings.textures and (context.scene.ObjectAttributesSettings.textures_selected_index < len(context.scene.ObjectAttributesSettings.textures)):
            context.scene.ObjectAttributesSettings.textures.remove(context.scene.ObjectAttributesSettings.textures_selected_index)
            context.scene.ObjectAttributesSettings.textures_selected_index = min(max(0, context.scene.ObjectAttributesSettings.textures_selected_index), len(context.scene.ObjectAttributesSettings.textures) - 1)        

        return{'FINISHED'}

class OBJECTATTRIBUTES_OT_NewSettings_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "objectattributes_item.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.ObjectAttributesSettings.textures

    def execute(self, context):
        settings = context.scene.ObjectAttributesSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.textures.move(settings.textures_selected_index + index_offset, settings.textures_selected_index)
        settings.textures_selected_index = max(0, min(settings.textures_selected_index + index_offset, len(settings.textures) - 1))

        return{'FINISHED'}

##############
### REPORT ###
class OBJECTATTRIBUTES_OT_ExportReport(bpy.types.Operator):
    """Export the bake report to an XML file, according to the XML export settings."""
    bl_idname = "gametools.objectattributes_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.ObjectAttributesReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class OBJECTATTRIBUTES_OT_ClearReport(bpy.types.Operator):
    """Clear the bake report."""
    bl_idname = "gametools.objectattributes_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.ObjectAttributesReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}
