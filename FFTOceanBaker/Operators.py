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

    preset_defines = [ 'settings = bpy.context.scene.FFTOCEANBAKERSettings' ]

    preset_values = [
    ] # @TODO

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