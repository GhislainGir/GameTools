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

from bl_ui.utils import PresetPanel

from . import Functions
from .Functions import get_data_layer_name, get_data_layer_storage_mode_icon, get_data_layer_packing_mode_icon, get_data_layer_info

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class DATABAKER_MT_DataBaker_Presets(bpy.types.Menu):
    bl_label = 'DATA Baker Presets'
    preset_subdir = 'operator/databaker_data'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class DATABAKER_PT_DataBaker_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'DATA Baker Presets'
    preset_subdir = 'operator/databaker_data'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'databaker_databakerpanel.addpreset'

############
### DATA ###
class DATABAKER_UL_DataTargetList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = context.scene.DataBakerSettings
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                row = layout.row()
                row.label(text=get_data_layer_name(item), translate=False)
                row.enabled = settings.data_layers[settings.data_layers_selected_index].ID != item.ID
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False)

class DATABAKER_UL_DataList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                row = layout.row()
                row.label(text=get_data_layer_name(item), translate=False, icon=get_data_layer_storage_mode_icon(item))
                row = layout.row(align=True)
                row.alignment = "RIGHT"
                if item.packing_mode == "UV":    
                    row.label(text=str(item.uv_index))
                    row.label(text=item.uv_channel)
                elif item.packing_mode == "VCOL":
                    row.label(text=item.vcol_rgba)
                elif item.packing_mode == "NORMAL":
                    row.label(text=item.normal_xyz)
                else:
                    pass

                row.label(text="", translate=False, icon=get_data_layer_packing_mode_icon(context.scene.DataBakerSettings.data_layers, item))
                success, msg, _ = get_data_layer_info(item, data.data_layers) # @TODO
                row.label(text="", translate=False, icon="CHECKMARK" if success else "ERROR")
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False, icon=get_data_layer_storage_mode_icon(item))

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
        row.enabled = len(settings.data_layers) > 0

        row = layout.row()
        row.prop(settings, "world_obj")

        row = layout.row()
        row.template_list("DATABAKER_UL_DataList", "", settings, "data_layers", settings, "data_layers_selected_index", rows=5)

        col = row.column(align=True)
        col.operator("databaker_item.new_item", text="", icon="ADD")
        col.operator("databaker_item.delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("databaker_item.move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("databaker_item.move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        if settings.data_layers:
            data = settings.data_layers[settings.data_layers_selected_index]
            if data:
                panel_header, panel_body = layout.panel("position")
                if panel_header:
                    panel_header.prop(data, "data")
                if panel_body:
                    if data.data == "POSITION":
                        row = panel_body.row()
                        row.prop(data, "component")

                    elif data.data == "AXIS":
                        row = panel_body.row()
                        row.prop(data, "axis", text="")

                        row = panel_body.row()
                        row.prop(data, "component")

                    elif data.data == "SHAPEKEY":
                        row = panel_body.row()
                        row.prop(data, "name", text="Shapekey")

                        row = panel_body.row()
                        row.prop(data, "shapekey_mode")

                        row = panel_body.row()
                        row.prop(data, "component")
                    elif data.data == "MASK":
                        row = panel_body.row()
                        row.prop(data, "mask_mode")

                        row = panel_body.row()
                        row.prop(data, "origin_mode")

                        if data.origin_mode == "ORIGIN":
                            row = panel_body.row()
                            row.prop(data, "obj", text="")

                        if data.mask_mode == "SPHERE":
                            pass
                        elif data.mask_mode == "LINEAR":
                            row = panel_body.row()
                            row.prop(data, "axis")
                            if data.origin_mode != "WORLD":
                                row = panel_body.row()
                                row.prop(data, "axis_mode")
                        else:
                            pass

                        row = panel_body.row()
                        row.prop(data, "clamp")

                        row = panel_body.row()
                        row.prop(data, "normalize")

                        row = panel_body.row()
                        row.prop(data, "falloff")
                        row.enabled = data.normalize or data.clamp

                    elif data.data == "RANDOM":
                        row = panel_body.row()
                        row.prop(data, "rand_mode")
                        row = panel_body.row()
                        row.prop(data, "rand_seed")
                        row = panel_body.row()
                        row.prop(data, "rand_float_mode")
                        row = panel_body.row()
                        row.prop(data, "uniform")
                    elif data.data == "PARENT_POS":
                        row = panel_body.row()
                        row.prop(data, "index", text="Depth")

                        row = panel_body.row()
                        row.prop(data, "component", text="")
                    elif data.data == "PARENT_AXIS":
                        row = panel_body.row()
                        row.prop(data, "index", text="Depth")

                        row = panel_body.row()
                        row.prop(data, "axis", text="")

                        row = panel_body.row()
                        row.prop(data, "component")
                    elif data.data == "VALUE":
                        row = panel_body.row()
                        row.prop(data, "x", text="")
                    elif data.data == "CUSTOM_PROP":
                        row = panel_body.row()
                        row.prop(data, "name", text="Name")
                    else:
                        pass

                panel_header, panel_body = layout.panel("packing_mode")
                if panel_header:
                    panel_header.prop(data, "packing_mode", text="Storage")
                if panel_body:
                    if data.packing_mode == "UV":
                        row = panel_body.row()
                        row.prop(data, "uv_index")
                        row = panel_body.row()
                        row.prop(data, "uv_channel")
                    elif data.packing_mode == "VCOL":
                        row = panel_body.row()
                        row.prop(data, "vcol_rgba")
                    elif data.packing_mode == "NORMAL":
                        row = panel_body.row()
                        row.prop(data, "normal_xyz")
                    else:
                        if data.packing_mode == "XY":
                            row = panel_body.row()
                            row.prop(data, "pack_xy", text="")
                        elif data.packing_mode == "XYZ":
                            row = panel_body.row()
                            row.prop(data, "pack_xyz", text="")
                        elif data.packing_mode == "FRACTION":
                            pass
                        else:
                            pass

                        row = panel_body.row()
                        row.template_list("DATABAKER_UL_DataTargetList", "", settings, "data_layers", data, "ptr_index", rows=3)

                        row = panel_body.row()
                        row.prop(data, "pack_only_if_non_null")

                # @TODO add error panel if any errors!

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
                layout.label(text=item.name, translate=False, icon="UV")
            else:
                layout.label(text="", translate=False, icon="UV")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="UV")

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
