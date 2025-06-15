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

from bpy.props import StringProperty
from bl_operators.presets import AddPresetBase

from . import Functions
from .Functions import bake, reset_bake_report, export_bake_report

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################

############
### MAIN ###
class VATBAKER_OT_Bake(bpy.types.Operator):
    """ Bakes object & skeletal animations of the active mesh into textures, storing positional & normal data per vertex. """
    bl_idname = "gametools.vatbaker_bakevat"
    bl_label = "Bake"
    bl_category = "Game Tools"
    bl_description = "Bake animations into vertex animation textures"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.VATBakerSettings

        Object = context.active_object
        if Object:
            if settings.bake_mode == "ANIMATION":
                return True
            elif Object.type == "MESH":
                return len(context.selected_objects) > 1
        
        return False

    def execute(self, context):
        success, verbose, msg = bake(context)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

##############
### PRESET ###
class VATBAKER_OT_VertexAnimation_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.vatbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'VATBAKER_MT_VertexAnimation_Presets'

    preset_defines = [ 'settings = bpy.context.scene.VATBakerSettings' ]

    preset_values = [
        'settings.bake_mode',
        'settings.unit_scale',
        'settings.unit_invert_x',
        'settings.unit_invert_y',
        'settings.unit_invert_z',
        'settings.unit_invert_v',
        'settings.unit_axis_order',
        'settings.mesh_uvmap_name',
        'settings.mesh_name',
        'settings.mesh_target_prop',
        'settings.mesh_materials',
        'settings.export_mesh',
        'settings.export_mesh_file_name',
        'settings.export_mesh_file_path',
        'settings.export_mesh_file_override',
        'settings.require_triangulation',
        'settings.previz_result',
        'settings.previz_bounds',
        'settings.export_xml',
        'settings.export_xml_mode',
        'settings.export_xml_file_name',
        'settings.export_xml_file_path',
        'settings.export_xml_override',
        'settings.frame_range_mode',
        'settings.frame_range_nla_exclusion',
        'settings.frame_range_nla_exclusion_selected_index',
        'settings.frame_range_nla_exclusion_selected',
        'settings.frame_range_custom_start',
        'settings.frame_range_custom_end',
        'settings.frame_range_custom_step',
        'settings.frame_range_custom_step_mode',
        'settings.frame_padding_mode',
        'settings.frame_padding',
        'settings.frame_ref_mode',
        'settings.frame_ref_custom',
        'settings.offset_tex',
        'settings.offset_tex_remap',
        'settings.offset_tex_file_name',
        'settings.normal_tex',
        'settings.normal_tex_remap',
        'settings.normal_tex_remap_biasscale',
        'settings.normal_tex_file_name',
        'settings.export_tex',
        'settings.export_tex_file_path',
        'settings.export_tex_override',
        'settings.export_tex_max_width',
        'settings.export_tex_max_height',
        'settings.tex_force_power_of_two',
        'settings.tex_force_power_of_two_square',
        'settings.tex_packing_mode'
    ]

    preset_subdir = 'operator/gametools_vatbaker'

#####################
### NLA EXCLUSION ###
class VATBAKER_OT_NLAExclusion_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "frame_range_nla_exclusion.new_item"
    bl_label = "Add a new item"
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.VATBakerSettings
        return settings.frame_range_nla_exclusion_selected != "" and settings.frame_range_nla_exclusion_selected not in [nla.name for nla in settings.frame_range_nla_exclusion]
    
    def execute(self, context):
        settings = context.scene.VATBakerSettings
        settings.frame_range_nla_exclusion.add()
        last_index = len(settings.frame_range_nla_exclusion) - 1
        if last_index >= 0:
            settings.frame_range_nla_exclusion_selected_index = last_index
            settings.frame_range_nla_exclusion[last_index].name = settings.frame_range_nla_exclusion_selected

        return{'FINISHED'}

class VATBAKER_OT_NLAExclusion_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "frame_range_nla_exclusion.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.VATBakerSettings.frame_range_nla_exclusion

    def execute(self, context):
        settings = context.scene.VATBakerSettings
        settings.frame_range_nla_exclusion.remove(settings.frame_range_nla_exclusion_selected_index)
        settings.frame_range_nla_exclusion_selected_index = min(max(0, settings.frame_range_nla_exclusion_selected_index), len(settings.frame_range_nla_exclusion) - 1)
        return{'FINISHED'}

class VATBAKER_OT_NLAExclusion_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "frame_range_nla_exclusion.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.VATBakerSettings.frame_range_nla_exclusion
    
    def execute(self, context):
        settings = context.scene.VATBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.frame_range_nla_exclusion.move(settings.frame_range_nla_exclusion_selected_index + index_offset, settings.frame_range_nla_exclusion_selected_index)
        settings.frame_range_nla_exclusion_selected_index = max(0, min(settings.frame_range_nla_exclusion_selected_index + index_offset, len(settings.frame_range_nla_exclusion) - 1))

        return{'FINISHED'}

##############
### REPORT ###
class VATBAKER_OT_ExportReport(bpy.types.Operator):
    """ """
    bl_idname = "gametools.vatbaker_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.VATBakerReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class VATBAKER_OT_ClearReport(bpy.types.Operator):
    """ """
    bl_idname = "gametools.vatbaker_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.VATBakerReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}