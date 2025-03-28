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

from bpy.types import Operator
from bpy.props import StringProperty

from . import Functions
from .Functions import bake, reset_bake_report, export_bake_report

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################
class VATBAKER_OT_Bake(Operator):
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
        if Object and Object.type == 'MESH' and Object.mode == 'OBJECT':
            if settings.bake_mode == "ANIMATION":
                return True
            else: # settings.bake_mode == "Mesh Sequence"
                return len(context.selected_objects) > 1
        else:
            return False

    def execute(self, context):
        success, verbose, msg = bake(context)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

class VATBAKER_OT_ExportReport(Operator):
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

class VATBAKER_OT_ClearReport(Operator):
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