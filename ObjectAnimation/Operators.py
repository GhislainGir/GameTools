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
class OATBAKER_OT_ObjectAnimation_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.oatbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'OATBAKER_MT_ObjectAnimation_Presets'

    preset_defines = [ 'settings = bpy.context.scene.OATBakerSettings' ]
    preset_values = [
        "settings.textures",
        "settings.textures_selected_index",
        "settings.unit_scale",
        "settings.unit_invert_x",
        "settings.unit_invert_y",
        "settings.unit_invert_z",
        "settings.unit_invert_v",
        "settings.unit_axis_order",
        "settings.origin_obj",
        "settings.mesh_name",
        "settings.mesh_uvmap_name",
        "settings.mesh_target_prop",
        "settings.mesh_materials",
        "settings.export_mesh",
        "settings.export_mesh_file_name",
        "settings.export_mesh_file_path",
        "settings.export_mesh_file_override",
        "settings.require_triangulation",
        "settings.previz_result",
        "settings.previz_bounds",
        "settings.export_xml",
        "settings.export_xml_mode",
        "settings.export_xml_file_name",
        "settings.export_xml_file_path",
        "settings.export_xml_override",
        "settings.frame_range_mode",
        "settings.frame_range_nla_exclusion",
        "settings.frame_range_nla_exclusion_selected_index",
        "settings.frame_range_nla_exclusion_selected",
        "settings.frame_range_custom_start",
        "settings.frame_range_custom_end",
        "settings.frame_range_custom_step",
        "settings.frame_range_custom_step_mode",
        "settings.frame_padding_mode",
        "settings.frame_padding",
        "settings.frame_ref_padding",
        "settings.frame_ref_mode",
        "settings.frame_ref_custom",
        "settings.export_tex",
        "settings.export_tex_file_name",
        "settings.export_tex_file_path",
        "settings.export_tex_override",
        "settings.export_tex_max_width",
        "settings.export_tex_max_height",
        "settings.tex_force_power_of_two",
        "settings.tex_force_power_of_two_square",
        "settings.tex_packing_mode",
    ]

    preset_subdir = 'operator/gametools_oatbaker'

############
### MAIN ###
class OATBAKER_OT_Bake(bpy.types.Operator):
    """ Bake the objects animation into texture(s) """
    bl_label = "Bake"
    bl_idname = "gametools.oatbaker_bakeoat"
    bl_category = "Game Tools"
    bl_options = {'REGISTER', 'UNDO'}

    # tooltip: bpy.props.StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")

    # @classmethod
    # def poll(cls, context):
    # 	settings = context.scene.OATBakerSettings
    # 	return True

    def execute(self, context):
        success, verbose, msg = bake(context)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

################
### TEXTURES ###
class OATBAKER_OT_NewSettings_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "oat_textures_item.new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.OATBakerSettings
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

            name = "Transform"
            name_suffix = 0
            names = [skinning_texture.name for skinning_texture in settings.textures]
            while name in names:
                name_suffix += 1
                name_suffix_str = str(name_suffix).zfill(3)
                name = "Transform." + name_suffix_str
            item.name = name

            if last_item:
                pass

        return{'FINISHED'}

class OATBAKER_OT_NewSettings_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "oat_textures_item.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.OATBakerSettings.textures

    def execute(self, context):
        if context.scene.OATBakerSettings.textures and (context.scene.OATBakerSettings.textures_selected_index < len(context.scene.OATBakerSettings.textures)):
            context.scene.OATBakerSettings.textures.remove(context.scene.OATBakerSettings.textures_selected_index)
            context.scene.OATBakerSettings.textures_selected_index = min(max(0, context.scene.OATBakerSettings.textures_selected_index), len(context.scene.OATBakerSettings.textures) - 1)        

        return{'FINISHED'}

class OATBAKER_OT_NewSettings_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "oat_textures_item.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.OATBakerSettings.textures

    def execute(self, context):
        settings = context.scene.OATBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.textures.move(settings.textures_selected_index + index_offset, settings.textures_selected_index)
        settings.textures_selected_index = max(0, min(settings.textures_selected_index + index_offset, len(settings.textures) - 1))

        return{'FINISHED'}

##############
### REPORT ###
class OATBAKER_OT_ExportReport(bpy.types.Operator):
    """Export the bake report to an XML file, according to the XML export settings."""
    bl_idname = "gametools.oatbaker_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.OATBakerReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class OATBAKER_OT_ClearReport(bpy.types.Operator):
    """Clear the bake report."""
    bl_idname = "gametools.oatbaker_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.OATBakerReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}
