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
from .Functions import get_data_layer_name, get_data_layer_icon, get_data_layer_info

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class DATABAKER_MT_MainPanel_Presets(bpy.types.Menu):
    bl_label = 'DATA Baker Presets'
    preset_subdir = 'operator/gametools_databaker'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class DATABAKER_PT_DataBaker_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'DATA Baker Presets'
    preset_subdir = 'operator/gametools_databaker'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.databaker_addpreset'

############
### MAIN ###
class DATABAKER_UL_DataList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                settings = context.scene.DataBakerSettings
                emphasis = False
                try:
                    selected_data_layer = settings.data_layers[settings.data_layers_selected_index]
                    if selected_data_layer.packing_mode == "XY_BIT" or selected_data_layer.packing_mode == "XY_NUM" or selected_data_layer.packing_mode == "XYZ_BIT" or selected_data_layer.packing_mode == "XYZ_NUM" or selected_data_layer.packing_mode == "FRACTION":
                        for data_layer_index, data_layer in enumerate(settings.data_layers):
                            if data_layer == item:
                                if selected_data_layer.ptr == data_layer_index:
                                    emphasis = True
                                    break
                except:
                    pass

                icon_base, icon_name = get_data_layer_icon(item, False)
                if emphasis:
                    icon_name = "TRIA_RIGHT_BAR"

                if icon_base:
                    row = layout.row()
                    row.label(text=get_data_layer_name(item), translate=False, icon=icon_name)
                    row = layout.row(align=True)
                    row.alignment = "RIGHT"
                else:
                    row = layout.row()
                    #col = row.split(align=True)
                    #col.alignment = "LEFT"
                    #col.label(text="")
                    col = row.split(align=True)
                    col.label(text=get_data_layer_name(item), translate=False, icon=icon_name)
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

                icon_base, icon_name = get_data_layer_icon(item, True)
                if not icon_base:
                    row.label(text="", translate=False, icon=icon_name)
                success, msg, _ = get_data_layer_info(item, data.data_layers)
                row.label(text="", translate=False, icon="CHECKMARK" if success else "ERROR")
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            icon_base, icon_name = get_data_layer_icon(item, False)
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False, icon=icon_name)

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
        row.template_list("DATABAKER_UL_DataList", "", settings, "data_layers", settings, "data_layers_selected_index", rows=8)

        col = row.column(align=True)
        col.operator("databaker_item.new_item", text="", icon="ADD")
        col.operator("databaker_item.delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("databaker_item.move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("databaker_item.move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        try:
            selected_data_layer = settings.data_layers[settings.data_layers_selected_index]
            if selected_data_layer.packing_mode == "XY_BIT" or selected_data_layer.packing_mode == "XY_NUM" or selected_data_layer.packing_mode == "XYZ_BIT" or selected_data_layer.packing_mode == "XYZ_NUM" or selected_data_layer.packing_mode == "FRACTION":
                col.separator()

                ope = col.operator("databaker_target.change_ptr", icon="AREA_JOIN_UP", text="")
                ope.direction = "UP"
                ope = col.operator("databaker_target.change_ptr", icon="AREA_JOIN_DOWN", text="")
                ope.direction = "DOWN"
        except:
            pass

class DATABAKER_PT_LayerPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_layerpanel"
    bl_parent_id = "DATABAKER_PT_databakerpanel"
    bl_label = "Layer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    #bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.DataBakerSettings
        return settings.data_layers

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

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
                    elif data.data == "QUATERNION":
                        row = panel_body.row()
                        row.prop(data, "quat")

                        row = panel_body.row()
                        col = row.split()
                        col.prop(data, "override_xyz_order")
                        col = row.split()
                        col.prop(data, "quat_xyz_order")
                        col.enabled = data.override_xyz_order
                    elif data.data == "AXIS":
                        row = panel_body.row()
                        row.prop(data, "axis", text="")

                        row = panel_body.row()
                        row.prop(data, "component")
                    elif data.data == "SHAPEKEY":
                        row = panel_body.row()
                        row.prop(data, "name", text="Shapekey")

                        row = panel_body.row()
                        row.prop(data, "vertex_mode")

                        row = panel_body.row()
                        row.prop(data, "component")
                    elif data.data == "MASK":
                        row = panel_body.row()
                        row.prop(data, "mask_mode")

                        row = panel_body.row()
                        row.prop(data, "origin_mode")

                        if data.origin_mode == "ORIGIN":
                            row = panel_body.row()
                            row.prop(data, "obj")

                        if data.mask_mode == "SPHERE":
                            pass
                        elif data.mask_mode == "LINEAR":
                            row = panel_body.row()
                            row.prop(data, "axis")
                            if data.origin_mode != "WORLD":
                                row = panel_body.row()
                                row.prop(data, "axis_mode")
                                
                                if data.axis_mode == "OBJECT":
                                    row = panel_body.row()
                                    row.prop(data, "axis_obj")
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

                        if data.rand_float_mode != "FLOAT":
                            row = panel_body.row()
                            row.prop(data, "component")
                        else:
                            row = panel_body.row()
                            row.prop(data, "uniform")
                    elif data.data == "VALUE":
                        row = panel_body.row()
                        row.prop(data, "x", text="")
                    elif data.data == "CUSTOM_PROP":
                        row = panel_body.row()
                        row.prop(data, "name", text="Name")
                    elif data.data == "FRAME":
                        row = panel_body.row()
                        row.prop(data, "vertex_mode", text="Mode")

                        row = panel_body.row()
                        row.prop(data, "index", text="Frame")

                        row = panel_body.row()
                        row.prop(data, "component")
                    elif data.data == "HIERARCHY":
                        pass
                    else:
                        pass

                    if data.data == "POSITION" or data.data == "QUATERNION" or data.data == "AXIS" or data.data == "SHAPEKEY" or data.data == "CUSTOM_PROP" or data.data == "FRAME":
                        row = panel_body.row()
                        row.prop(data, "obj_mode")
                        
                        if data.obj_mode == "CUSTOM":
                            row = panel_body.row()
                            row.prop(data, "obj")
                        elif data.obj_mode == "PARENT":
                            row = panel_body.row()
                            row.prop(data, "index", text="Depth")
                        elif data.obj_mode == "PROPERTY":
                                row = panel_body.row()
                                row.prop(data, "obj_prop")

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
                        if data.packing_mode == "XY_BIT" or data.packing_mode == "XY_NUM":
                            row = panel_body.row()
                            row.prop(data, "pack_xy", text="")
                        elif data.packing_mode == "XYZ_BIT" or data.packing_mode == "XYZ_NUM":
                            row = panel_body.row()
                            row.prop(data, "pack_xyz", text="")
                        elif data.packing_mode == "FRACTION":
                            row = panel_body.row()
                            row.prop(settings, "packing_precision")
                        else:
                            pass

##############
### MESHES ###
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
        row.prop(settings, "origin_obj")

        row = layout.row()
        row.prop(settings, "unit_scale")

        row = layout.row()
        row.label(text="Invert")
        row.prop(settings, "unit_invert_x", text="X")
        row.prop(settings, "unit_invert_y", text="Y")
        row.prop(settings, "unit_invert_z", text="Z")

        row = layout.row()
        row.prop(settings, "unit_axis_order")

        row = layout.row()
        row.prop(settings, "mesh_name")

        row = layout.row()
        row.prop(settings, "mesh_materials")

        row = layout.row()
        col = row.split()
        col.prop(settings, "mesh_merge")
        col = row.split()
        col.prop(settings, "clear_attributes")

        row = layout.row()
        col = row.split()
        col.prop(settings, "mesh_duplicate")
        col = row.split()
        col.prop(settings, "mesh_single_user")
        if settings.mesh_duplicate:
            col.enabled = False

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
        row.prop(settings, "mesh_uvmap_name", text="Name")

        row = layout.row()
        row.prop(settings, "unit_invert_v")

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
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.DataBakerSettings

        layout.enabled = settings.export_mesh and bpy.data.is_saved

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
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.enabled = bpy.data.is_saved

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
class DATABAKER_UL_ReportDataSubList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = context.scene.DataBakerSettings
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                row = layout.row()
                row.label(text=get_data_layer_name(item), translate=False, icon="COPYDOWN")
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False)

class DATABAKER_UL_ReportDataList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item and item.packed_layers:
                data_layer = [data_layer for data_layer in item.packed_layers if data_layer.ID == item.active_layer_ID][0]

                icon_base, icon_name = get_data_layer_icon(data_layer, False)
                if icon_base:
                    row = layout.row()
                    row.label(text=get_data_layer_name(data_layer), translate=False, icon=icon_name)
                    row = layout.row(align=True)
                    row.alignment = "RIGHT"
                else:
                    row = layout.row()
                    col = row.split(align=True)
                    col.alignment = "LEFT"
                    col.label(text="")
                    col = row.split(align=True)
                    col.label(text=get_data_layer_name(data_layer), translate=False, icon=icon_name)
                    row = layout.row(align=True)
                    row.alignment = "RIGHT"
                if data_layer.packing_mode == "UV":    
                    row.label(text=str(data_layer.uv_index))
                    row.label(text=data_layer.uv_channel)
                elif data_layer.packing_mode == "VCOL":
                    row.label(text=data_layer.vcol_rgba)
                elif data_layer.packing_mode == "NORMAL":
                    row.label(text=data_layer.normal_xyz)
                else:
                    pass
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            icon_base, icon_name = get_data_layer_icon(data_layer, False)
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False, icon=icon_name)

            layout.alignment = 'CENTER'
            layout.label(text="", icon="UV")

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
            row.label(text=report.name + " : Success", icon="CHECKMARK")
        else:
            row.label(text=report.name + " : Fail", icon="ERROR")
            row = layout.row()
            row.label(text=report.msg)

        row = layout.row()
        row.prop(report, "ID", text="")
        row.enabled = False

        layout.template_list("DATABAKER_UL_ReportDataList", "", report, "data_layers", report, "data_layers_selected_index", rows=6)

class DATABAKER_PT_ReportLayerPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_reportlayerpanel"
    bl_parent_id = "DATABAKER_PT_reportpanel"
    bl_label = "Layer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.DataBakerReport

        if report.data_layers and (report.data_layers_selected_index < len(report.data_layers)):
            data_layer = report.data_layers[report.data_layers_selected_index]

            if data_layer and data_layer.packed_layers:
                if data_layer.packed_layers_selected_index < len(data_layer.packed_layers):
                    packed_data_layer = data_layer.packed_layers[data_layer.packed_layers_selected_index]
                    if packed_data_layer:
                        row = layout.row()
                        row.prop(packed_data_layer, "ID", text="")
                        row.enabled = False

                if len(data_layer.packed_layers) > 1:
                    row = layout.row()
                    row.label(text="Packing: " + str(data_layer.packed_mode))
                else:
                    row = layout.row()
                    row.label(text="Packing: None")
                    row.enabled = False

                layout.template_list("DATABAKER_UL_ReportDataSubList", "", data_layer, "packed_layers", data_layer, "packed_layers_selected_index", rows=3)

                if data_layer.packed_layers_selected_index < len(data_layer.packed_layers):
                    packed_data_layer = data_layer.packed_layers[data_layer.packed_layers_selected_index]
                    if packed_data_layer:
                        icon = "CHECKMARK" if data_layer.range_valid else "ERROR"

                        layer_remapped = False

                        if packed_data_layer.packing_mode == "FRACTION" or packed_data_layer.packing_mode == "XY_NUM" or packed_data_layer.packing_mode == "XY_BIT" or packed_data_layer.packing_mode == "XYZ_NUM" or packed_data_layer.packing_mode == "XYZ_BIT":
                            layer_remapped = True
                        elif packed_data_layer.packing_mode == "NORMAL" or packed_data_layer.packing_mode == "VCOL": # @NOTE unsure about this. Should it be data_layer.packed_mode?!
                            layer_remapped = not data_layer.range_unit_vector
                        elif data_layer.packed_mode == "FRACTION" or data_layer.packed_mode == "XY_BIT" or data_layer.packed_mode == "XY_NUM" or data_layer.packed_mode == "XYZ_BIT" or data_layer.packed_mode == "XYZ_NUM":
                            layer_remapped = True

                        row = layout.row()
                        if data_layer.range_high_precision:
                            row.label(text="Requires 32 bit: Yes")
                        else:
                            row.label(text="Requires 32 bit: No")
                            row.enabled = False

                        row = layout.row()
                        if layer_remapped:
                            row.label(text="Requires remapping: Yes")
                        else:
                            row.label(text="Requires remapping: No")
                            row.enabled = False

                        row = layout.row()
                        row.label(text="Offset: %.5f" % data_layer.range_offset[data_layer.packed_layers_selected_index], icon="DOT")
                        row.enabled = layer_remapped
                        row = layout.row()
                        row.label(text="Range: %.5f" % data_layer.range[data_layer.packed_layers_selected_index], icon=icon)
                        row.enabled = layer_remapped

                        if packed_data_layer.packing_mode == "NORMAL":
                            row = layout.row()
                            row.label(text="Is Unit: " + str(data_layer.range_unit_vector))

class DATABAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_reportmeshpanel"
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
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.DataBakerReport

        if report.mesh:
            row = layout.row()
            row.prop(report, "mesh", text="")
            row.enabled = False

            row = layout.row()
            if report.mesh_export:
                row.label(text="File: " + report.mesh_path, icon="FILE")
            else:
                row.label(text="Not exported", icon="X")

            layout.separator()

            icon = "CHECKMARK" if report.unit_invert_v else "X"
            row = layout.row()
            row.label(text="Invert V: " + str(report.unit_invert_v), icon=icon)
            row.enabled = report.unit_invert_v

        else:
            row = layout.row()
            row.label(text="None generated")

class DATABAKER_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "DATABAKER_PT_reportxmlpanel"
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
    bl_idname = "DATABAKER_PT_reportunitpanel"
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

        row = layout.row()
        row.prop(report, "unit_axis_order")
        row.enabled = False
