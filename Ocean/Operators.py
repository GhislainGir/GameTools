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
class FFTOCEANBAKER_OT_Bake(bpy.types.Operator):
    """ Bakes object & skeletal animations of the active mesh into textures, storing positional & normal data per vertex. """
    bl_idname = "gametools.fftoceanbaker_bakefftocean"
    bl_label = "Bake"
    bl_category = "Game Tools"
    bl_description = "Bake animations into vertex animation textures"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

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
class FFTOCEANBAKER_OT_FFTOceanBaker_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.fftoceanbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'FFTOCEANBAKER_MT_FFTOceanBaker_Presets'

    preset_defines = [ 'settings = bpy.context.scene.FFTOceanBakerSettings' ]

    preset_values = [
        'settings.unit_scale',
        'settings.unit_invert_u',
        'settings.unit_invert_v',
        'settings.unit_axis_order',
        'settings.frame_sort_mode',
        'settings.subd',
        'settings.frames_per_row',
        'settings.frame_padding_mode',
        'settings.frame_padding_mips',
        'settings.frame_padding_pixels',
        'settings.ocean_time',
        'settings.ocean_size',
        'settings.ocean_spatial_size',
        'settings.ocean_depth',
        'settings.ocean_seed',
        'settings.ocean_scale',
        'settings.ocean_smallest_wave',
        'settings.ocean_choppiness',
        'settings.ocean_wind_vel',
        'settings.ocean_alignment',
        'settings.ocean_direction',
        'settings.ocean_damping',
        'settings.ocean_clear',
        'settings.ocean_from_active',
        'settings.mesh_name',
        'settings.generate_mesh',
        'settings.export_mesh',
        'settings.export_mesh_file_name',
        'settings.export_mesh_file_path',
        'settings.export_mesh_file_override',
        'settings.export_xml',
        'settings.export_xml_mode',
        'settings.export_xml_file_name',
        'settings.export_xml_file_path',
        'settings.export_xml_override',
        'settings.frame_range_mode',
        'settings.frame_range_custom_start',
        'settings.frame_range_custom_end',
        'settings.frame_range_custom_step',
        'settings.frame_size_mode',
        'settings.frame_size_custom',
        'settings.flipbook_max_size',
        'settings.tex_mode',
        'settings.offset_tex',
        'settings.offset_tex_remap',
        'settings.offset_tex_file_name',
        'settings.normal_tex',
        'settings.normal_tex_remap',
        'settings.normal_tex_file_name',
        'settings.crest_tex',
        'settings.crest_tex_file_name',
        'settings.crest_threshold',
        'settings.export_tex',
        'settings.export_tex_file_path',
        'settings.export_tex_override'
    ]

    preset_subdir = 'operator/gametools_fftoceanbaker'

##############
### REPORT ###
class FFTOCEANBAKER_OT_ExportReport(bpy.types.Operator):
    """ """
    bl_idname = "gametools.fftoceanbaker_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.FFTOCEANBAKERReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class FFTOCEANBAKER_OT_ClearReport(bpy.types.Operator):
    """ """
    bl_idname = "gametools.fftoceanbaker_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.FFTOCEANBAKERReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}