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
from .Functions import bake, reset_bake_report, export_bake_report, generate_geonodes_sdf_3d

from bl_operators.presets import AddPresetBase

import uuid

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################
class SDFBAKER_OT_BakeData(Operator):
    """ """
    bl_idname = "gametools.sdfbaker_bakedata"
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

class SDFBAKER_OT_GenerateGeoNodes(Operator):
    """Legacy way of baking SDF using geometry nodes. This was kept around in case you find the geometry nodes graph useful and for educational purposes"""
    bl_idname = "gametools.sdfbaker_generategeonodes"
    bl_label = "GeoNodes (Legacy)"
    bl_category = "Game Tools"
    bl_options = {'REGISTER', 'UNDO'}

    # tooltip: bpy.props.StringProperty(name="Name", default="BakedMesh.DATA", description="Name of the resulting baked mesh")

    # @classmethod
    # def description(cls, context, operator):
    #     return operator.tooltip

    @classmethod
    def poll(cls, context):
        Object = context.active_object
        return Object and Object.type == 'MESH' and Object.mode == 'OBJECT'

    def execute(self, context):
        success, verbose, msg = generate_geonodes_sdf_3d(context, bpy.context.active_object)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

##############
### Preset ###
class SDFBAKER_OT_DataBaker_AddPreset(AddPresetBase, Operator):
    bl_idname = 'sdfbaker_sdfbakerpanel.addpreset'
    bl_label = 'Add preset'
    preset_menu = 'SDFBAKER_MT_DataBaker_Presets'

    preset_defines = [ 'settings = bpy.context.scene.DataBakerSettings' ]
    preset_values = [
    'settings.scale',
    'settings.export_xml',
    'settings.export_xml_mode',
    'settings.export_xml_file_name',
    'settings.export_xml_file_path',
    'settings.export_xml_override'
    ] # @TODO

    preset_subdir = 'operator/sdfbaker_data'

##############
### Report ###
class SDFBAKER_OT_ExportReport(Operator):
    """ """
    bl_idname = "gametools.sdfbaker_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.SDFBakerReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class SDFBAKER_OT_ClearReport(Operator):
    """ Bakes object & skeletal animations of the active mesh into textures, storing positional & normal data per vertex. """
    bl_idname = "gametools.sdfbaker_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.SDFBakerReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}
