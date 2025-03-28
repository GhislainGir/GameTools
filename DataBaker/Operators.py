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

from . import Functions
from .Functions import bake, get_position_data_multiplier, get_parent_position_data_multiplier, get_shapekey_offset_data_multiplier, reset_bake_report, export_bake_report

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

class DATABAKER_OT_GetPositionDataMultiplier(Operator):
    """ """
    bl_idname = "gametools.databaker_getpositionmultiplier"
    bl_label = "Compute Multiplier"
    bl_category = "Game Tools"
    bl_description = "Compute Multiplier the position multiplier to use in your UE materials in case you store said position in vertex color OR pack its XYZ components in a single float"
    
    def execute(self, context):
        report = context.scene.DataBakerReport
        report.position_multiplier = get_position_data_multiplier(context)

        return {'FINISHED'}

class DATABAKER_OT_GetParentPositionDataMultiplier(Operator):
    """ """
    bl_idname = "gametools.databaker_getparentoffsetmultipler"
    bl_label = "Compute Multiplier"
    bl_category = "Game Tools"
    bl_description = "Compute Multiplier the parent position multiplier to use in your UE materials in case you store said position in vertex color OR pack its XYZ components in a single float"
    
    def execute(self, context):
        report = context.scene.DataBakerReport
        report.parent_position_multiplier = get_parent_position_data_multiplier(context)

        return {'FINISHED'}

class DATABAKER_OT_GetShapekeyOffsetDataMultiplier(Operator):
    """ """
    bl_idname = "gametools.databaker_getshapekeyoffsetmultiplier"
    bl_label = "Compute Multiplier"
    bl_category = "Game Tools"
    bl_description = "Compute Multiplier the shapekey offset multiplier to use in your UE materials in case you store said offset in vertex color OR pack its XYZ components in a single float"

    def execute(self, context):
        report = context.scene.DataBakerReport
        report.shapekey_offset_multiplier = get_shapekey_offset_data_multiplier(context)

        return {'FINISHED'}
