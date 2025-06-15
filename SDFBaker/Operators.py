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
from .Functions import bake, reset_bake_report, export_bake_report, generate_geonodes_sdf_3d

from bl_operators.presets import AddPresetBase

import uuid

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################

############
### MAIN ###
class SDFBAKER_OT_BakeSDF(bpy.types.Operator):
    """Bakes a 2D or 3D SDF from the selected meshes."""
    bl_idname = "gametools.sdfbaker_bakesdf"
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

class SDFBAKER_OT_GenerateGeoNodes(bpy.types.Operator):
    """Legacy way of baking SDF using geometry nodes (for educational purposes only)."""
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
### PRESET ###
class SDFBAKER_OT_SDFBaker_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.sdfbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'SDFBAKER_MT_MainPanel_Presets'

    preset_defines = [ 'settings = bpy.context.scene.SDFBakerSettings' ]
    preset_values = [
    'settings.distance_mode',
    'settings.sdf_mode',
    'settings.sdf_bounds',
    'settings.frames',
    'settings.x',
    'settings.y',
    'settings.z',
    'settings.offset',
    'settings.tile_sort_mode',
    'settings.unit_invert_v',
    'settings.invert_sign',
    'settings.two_sided',
    'settings.mesh_name',
    'settings.gen_selection_mesh',
    'settings.gen_debug_mesh',
    'settings.export_mesh',
    'settings.export_mesh_file_name',
    'settings.export_mesh_file_path',
    'settings.export_mesh_file_override',
    'settings.unit_scale',
    'settings.unit_invert_x',
    'settings.unit_invert_y',
    'settings.unit_invert_z',
    'settings.export_xml',
    'settings.export_xml_mode',
    'settings.export_xml_file_name',
    'settings.export_xml_file_path',
    'settings.export_xml_override',
    'settings.tex_file_name',
    'settings.export_tex',
    'settings.export_tex_file_path',
    'settings.export_tex_override',
    ]

    preset_subdir = 'operator/gametools_sdfbaker'

##############
### REPORT ###
class SDFBAKER_OT_ExportReport(bpy.types.Operator):
    """Export the bake report to an XML file, according to the XML export settings."""
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

class SDFBAKER_OT_ClearReport(bpy.types.Operator):
    """Clear the bake report."""
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
