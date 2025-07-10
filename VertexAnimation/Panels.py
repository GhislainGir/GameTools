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
import os

from bl_ui.utils import PresetPanel

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class VATBAKER_MT_VertexAnimation_Presets(bpy.types.Menu):
    bl_label = 'VAT Baker Presets'
    preset_subdir = 'operator/gametools_vatbaker'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class VATBAKER_PT_VertexAnimation_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'VAT Baker Presets'
    preset_subdir = 'operator/gametools_vatbaker'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.vatbaker_addpreset'

############
### MAIN ###
class VATBAKER_PT_VertexAnimation(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_mainpanel"
    bl_label = "VAT Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.active.type == "MESH"

    def draw_header_preset(self, _context):
        VATBAKER_PT_VertexAnimation_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings
        report = scene.VATBakerReport

        row = layout.row()
        row.prop(settings, "bake_mode")

        row = layout.row()
        row.operator("gametools.vatbaker_bakevat")
        row.scale_y = 2.0
        row.enabled = settings.offset_tex or settings.normal_tex

#############
### SCENE ###
class VATBAKER_PT_FramePanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_framepanel"
    bl_parent_id = "VATBAKER_PT_mainpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.VATBakerSettings
        return settings.bake_mode == 'ANIMATION'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        row = layout.row()
        row.prop(settings, "frame_range_mode", text="")

        if (settings.frame_range_mode == "NLA"):
            row = layout.row()
            row.prop(settings, "frame_range_custom_step", text="Step:")

            if settings.frame_range_custom_step > 1:
                row = layout.row()
                row.prop(settings, "frame_range_custom_step_mode")

            row = layout.row()
            row.prop(settings, "frame_padding")

            row = layout.row()
            row.prop(settings, "frame_padding_mode")
            row.enabled = settings.frame_padding > 0
 
        elif (settings.frame_range_mode == "SCENE"):
            row = layout.row()
            row.label(text="Frame Range:")

            row = layout.row()
            row.prop(scene, "frame_start", text="")
            row.prop(scene, "frame_end", text="")

            row = layout.row()
            row.prop(scene, "frame_step", text="Step:")
        elif (settings.frame_range_mode == "CUSTOM"):
            row = layout.row()
            row.label(text="Frame Range:")

            row = layout.row()
            row.prop(settings, "frame_range_custom_start", text="")
            row.prop(settings, "frame_range_custom_end", text="")

            row = layout.row()
            row.prop(settings, "frame_range_custom_step", text="Step:")

        row = layout.row()
        row.prop(settings, "frame_ref_mode", text="Ref")
        if settings.frame_ref_mode == "CUSTOM":
            row = layout.row()
            row.prop(settings, "frame_ref_custom", text="Frame")

class VATBAKER_PT_FrameAdvPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_frameadvpanel"
    bl_parent_id = "VATBAKER_PT_framepanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.VATBakerSettings.frame_range_mode == "NLA"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        row = layout.row()
        row.label(text="NLA clips to exclude:")

        row = layout.row()
        row.template_list("VATBAKER_UL_NLAExclusionList", "", settings, "frame_range_nla_exclusion", settings, "frame_range_nla_exclusion_selected_index", rows=4)

        col = row.column(align=True)
        col.operator("frame_range_nla_exclusion.new_item", text="", icon="ADD")
        col.operator("frame_range_nla_exclusion.delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("frame_range_nla_exclusion.move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("frame_range_nla_exclusion.move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        row = layout.row()
        row.prop(settings, "frame_range_nla_exclusion_selected")

class VATBAKER_UL_NLAExclusionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

##############
### MESHES ###
class VATBAKER_PT_MeshMainPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_meshmainpanel"
    bl_parent_id = "VATBAKER_PT_mainpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings
        
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

        if settings.bake_mode == "ANIMATION":
            row = layout.row()
            row.prop(settings, "mesh_target_prop")

        panel_header, panel_body = layout.panel("vat_mesh_previz")
        if panel_header:
            panel_header.label(text="Previz")
        if panel_body:
            row = panel_body.row()
            col = row.split()
            col.prop(settings, "previz_result", text="Anim")
            col.enabled = False
            col = row.split()
            col.prop(settings, "previz_bounds", text="Bounds")


class VATBAKER_PT_MeshUVPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_meshuvpanel"
    bl_parent_id = "VATBAKER_PT_meshmainpanel"
    bl_label = "UV"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        row = layout.row()
        row.prop(settings, "mesh_uvmap_name", text="Name")

        row = layout.row()
        row.prop(settings, "unit_invert_v")

class VATBAKER_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_meshexportpanel"
    bl_parent_id = "VATBAKER_PT_meshmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.prop(settings, "export_mesh", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.enabled = settings.export_mesh and bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class VATBAKER_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_meshadvexportpanel"
    bl_parent_id = "VATBAKER_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

################
### TEXTURES ###
class VATBAKER_PT_TexMainPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_texmainpanel"
    bl_parent_id = "VATBAKER_PT_mainpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        row = layout.row()
        row.prop(settings, "export_tex_max_width")
        
        row = layout.row()
        row.prop(settings, "export_tex_max_height")
        
        row = layout.row()
        col = row.split()
        col.prop(settings, "tex_force_power_of_two")
        col = row.split()
        col.prop(settings, "tex_force_power_of_two_square")
        col.enabled = settings.tex_force_power_of_two

        row = layout.row()
        row.prop(settings, "tex_packing_mode")

        row = layout.row()
        row.prop(settings, "tex_packing_stack_mode")
        row.enabled = settings.tex_packing_mode == "STACK"

class VATBAKER_PT_TexOffsetPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_texnoffsetpanel"
    bl_parent_id = "VATBAKER_PT_texmainpanel"
    bl_label = "Offsets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.prop(settings, "offset_tex", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings
        
        layout.enabled = settings.offset_tex

        row = layout.row()
        row.prop(settings, "offset_tex_mode")    

        row = layout.row()
        row.prop(settings, "offset_tex_file_name")

        row = layout.row()
        row.prop(settings, "offset_tex_remap")

class VATBAKER_PT_TexNormalPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_texnormalpanel"
    bl_parent_id = "VATBAKER_PT_texmainpanel"
    bl_label = "Normals"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.prop(settings, "normal_tex", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.enabled = settings.normal_tex
    
        row = layout.row()
        row.prop(settings, "normal_tex_file_name")

        row = layout.row()
        row.prop(settings, "normal_tex_remap")
        row.prop(settings, "normal_tex_remap_biasscale")
        row.enabled = settings.normal_tex_remap

class VATBAKER_PT_TexExportPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_texexportpanel"
    bl_parent_id = "VATBAKER_PT_texmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings

        layout.prop(settings, "export_tex", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings
        
        layout.enabled = settings.export_tex and bpy.data.is_saved
    
        row = layout.row()
        row.prop(settings, "export_tex_file_path")

class VATBAKER_PT_TexAdvExportPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_texadvexportpanel"
    bl_parent_id = "VATBAKER_PT_texexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.VATBakerSettings
    
        row = layout.row()
        row.prop(settings, "export_tex_override")

###########
### XML ###
class VATBAKER_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_xmlpanel"
    bl_parent_id = "VATBAKER_PT_mainpanel"
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

class VATBAKER_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_xmlexportpanel"
    bl_parent_id = "VATBAKER_PT_xmlpanel"
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

        row = layout.row()
        row.prop(settings, "export_xml_mode")
        row.enabled = settings.export_mesh and bpy.data.is_saved

        if (settings.export_xml_mode == "CUSTOMPATH" or not settings.export_mesh):
            row = layout.row()
            row.prop(settings, "export_xml_file_name")

            row = layout.row()
            row.prop(settings, "export_xml_file_path")

        row = layout.row()
        row.prop(settings, "export_xml_override")

##############
### REPORT ###
class VATBAKER_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reportpanel"
    bl_parent_id = "VATBAKER_PT_mainpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.VATBakerReport.baked

    # def draw_header(self, context):
    #     report = context.scene.VATBakerReport
    #     row = self.layout.row(align=True)
    #     if report.success:
    #         row.label(text="", icon="CHECKMARK")
    #     else:
    #         row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.vatbaker_export_report")
            col = row.split()
            col.operator("gametools.vatbaker_clear_report")

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

class VATBAKER_PT_ReportTexPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reporttexpanel"
    bl_parent_id = "VATBAKER_PT_reportpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.VATBakerReport.success
    
    def draw_header(self, context):
        report = context.scene.VATBakerReport
        row = self.layout.row(align=True)
        if report.tex_offset or report.tex_normal:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

        row = layout.row()
        col = row.split()
        col.label(text="Width: " + str(report.tex_width))
        col.label(text="Height: " + str(report.tex_height))

        # row = layout.row()
        # row.label(text="Underflow: " + str(report.tex_underflow))

        # row = layout.row()
        # row.label(text="Overflow: " + str(report.tex_overflow))

        layout.separator()

        row = layout.row()
        row.label(text="Offset")

        if report.tex_offset:
            row = layout.row()
            row.prop(report, "tex_offset", text="")
            row.enabled = False

            row = layout.row()
            if report.tex_offset_export:
                row.label(text="File: " + report.tex_offset_path, icon="FILE")
            else:
                row.label(text="Not exported", icon="X")

            icon = "CHECKMARK" if report.tex_offset_remapped else "X"
            row = layout.row()
            row.label(text="Remapped: " + str(report.tex_offset_remapped), icon=icon)
            row.enabled = report.tex_offset_remapped

            if report.tex_offset_remapped:
                row = layout.row()
                row.label(text="Offset")
                
                row = layout.row()
                row.label(text="X: " + str(report.tex_offset_range_offset[0]), icon="DOT")
                row = layout.row()
                row.label(text="Y: " + str(report.tex_offset_range_offset[1]), icon="DOT")
                row = layout.row()
                row.label(text="Z: " + str(report.tex_offset_range_offset[2]), icon="DOT")

                row.separator()

                row = layout.row()
                row.label(text="Range")
                
                row = layout.row()
                row.label(text="X: " + str(report.tex_offset_range[0]), icon="DOT")
                row = layout.row()
                row.label(text="Y: " + str(report.tex_offset_range[1]), icon="DOT")
                row = layout.row()
                row.label(text="Z: " + str(report.tex_offset_range[2]), icon="DOT")

            row = layout.row()
            if report.tex_offset_mode == "OFFSET":
                row.label(text="Mode: " + report.tex_offset_mode, icon="X")
                row.enabled = False
            else:
                row.label(text="Mode: " + report.tex_offset_mode, icon="INFO")
        else:
            row.label(text="None generated", icon="X")

        layout.separator()

        row = layout.row()
        row.label(text="Normal")

        if report.tex_normal:
            row = layout.row()
            row.prop(report, "tex_normal", text="")
            row.enabled = False

            row = layout.row()
            if report.tex_normal_export:
                row.label(text="File: " + report.tex_normal_path, icon="FILE")
            else:
                row.label(text="Not exported", icon="X")

            icon = "CHECKMARK" if report.tex_offset_remapped else "X"
            row = layout.row()
            row.label(text="Remapped: " + str(report.tex_normal_remapped), icon=icon)
            row.enabled = report.tex_normal_remapped

            if report.tex_normal_remapped:
                row = layout.row()
                row.label(text="Offset")
                
                row = layout.row()
                row.label(text="X: " + str(report.tex_normal_range_offset[0]), icon="DOT")
                row = layout.row()
                row.label(text="Y: " + str(report.tex_normal_range_offset[1]), icon="DOT")
                row = layout.row()
                row.label(text="Z: " + str(report.tex_normal_range_offset[2]), icon="DOT")

                row.separator()

                row = layout.row()
                row.label(text="Range")
                
                row = layout.row()
                row.label(text="X: " + str(report.tex_normal_range[0]), icon="DOT")
                row = layout.row()
                row.label(text="Y: " + str(report.tex_normal_range[1]), icon="DOT")
                row = layout.row()
                row.label(text="Z: " + str(report.tex_normal_range[2]), icon="DOT")

        else:
            row.label(text="None generated", icon="X")

class VATBAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reportmeshpanel"
    bl_parent_id = "VATBAKER_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.VATBakerReport
        row = self.layout.row(align=True)
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

        if report.mesh:
            row = layout.row()
            row.prop(report, "mesh", text="")
            row.enabled = False

            row = layout.row()
            if report.mesh_export:
                row.label(text="File: " + report.mesh_path, icon="FILE")
            else:
                row.label(text="Not exported", icon="X")
            
            row = layout.row()
            row.label(text="Verts: " + str(report.num_verts))

            layout.separator()
            
            row = layout.row()
            row.label(text="UVMap")
            icon = "QUESTION" if report.mesh_uvmap_index == 0 else "DOT"
            row = layout.row()
            row.label(text="Index: " + str(report.mesh_uvmap_index), icon=icon)

            icon = "CHECKMARK" if report.unit_invert_v else "X"
            row = layout.row()
            row.label(text="Invert V: " + str(report.unit_invert_v), icon=icon)
            row.enabled = report.unit_invert_v

            layout.separator()

            row = layout.row()
            row.label(text="Min Bounds Offset")

            row = layout.row()
            row.label(text="X: " + str(report.mesh_min_bounds_offset[0]), icon="DOT")
            row = layout.row()
            row.label(text="Y: " + str(report.mesh_min_bounds_offset[1]), icon="DOT")
            row = layout.row()
            row.label(text="Z: " + str(report.mesh_min_bounds_offset[2]), icon="DOT")

            layout.separator()

            row = layout.row()
            row.label(text="Max Bounds Offset")

            row = layout.row()
            row.label(text="X: " + str(report.mesh_max_bounds_offset[0]), icon="DOT")
            row = layout.row()
            row.label(text="Y: " + str(report.mesh_max_bounds_offset[1]), icon="DOT")
            row = layout.row()
            row.label(text="Z: " + str(report.mesh_max_bounds_offset[2]), icon="DOT")
        else:
            row = layout.row()
            row.label(text="Verts: " + str(report.num_verts))

            row = layout.row()
            row.label(text="None generated")

class VATBAKER_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reportxmlpanel"
    bl_parent_id = "VATBAKER_PT_reportpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.VATBakerReport
        row = self.layout.row(align=True)
        if report.xml:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

        row = layout.row()
        if report.xml:
            row.label(text="File: " + report.xml_path, icon="FILE")
        else:
            row.label(text="Not exported", icon="X")

class VATBAKER_PT_ReportAnimsPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reportanimspanel"
    bl_parent_id = "VATBAKER_PT_reportpanel"
    bl_label = "Anims"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10

    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.VATBakerReport.success

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

        layout.template_list("VATBAKER_UL_ReportAnimsList", "", report, "anims", report, "selected_anim", rows=3)
        if report.anims:
            anim = report.anims[report.selected_anim]
            if anim:
                row = layout.row()
                row.label(text="Length: " + str(anim.end_frame - (anim.start_frame - 1)))

                row = layout.row()
                row.label(text="Start")
                row = layout.row()
                row.label(text="Frame: " + str(anim.start_frame - 1), icon="KEYFRAME")
                row = layout.row()
                row.label(text="Time: " + str(anim.start_time), icon="TIME")

                layout.separator()

                row = layout.row()
                row.label(text="End")
                row = layout.row()
                row.label(text="Frame: " + str(anim.end_frame - 1), icon="KEYFRAME")
                row = layout.row()
                row.label(text="Time: " + str(anim.end_time), icon="TIME")

                layout.separator()

                row = layout.row()
                row.label(text="Associated Objects")

                if len(anim.objs) > 0:
                    layout.template_list("VATBAKER_UL_ReportAnimsObjsList", "", anim, "objs", anim, "selected_obj", rows=2)
                    if anim.objs:
                        anim_obj = anim.objs[anim.selected_obj]
                        if anim_obj:
                            if anim_obj.target_obj:
                                row = layout.row()
                                row.label(text="Target: ", icon="CHECKMARK")

                                row = layout.row()
                                row.prop(anim_obj, "target_obj", text="")
                                row.enabled = False
                            else:
                                row = layout.row()
                                row.label(text="No target", icon="X")
                                row.enabled = False

class VATBAKER_UL_ReportAnimsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.label(text=item.name, translate=False, icon="ANIM_DATA")
            else:
                layout.label(text="", translate=False, icon="ANIM_DATA")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class VATBAKER_UL_ReportAnimsObjsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.obj:
                layout.label(text=item.obj.name, translate=False, icon="OBJECT_DATA")
            else:
                layout.label(text="", translate=False, icon="OBJECT_DATA")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="OBJECT_DATA")

class VATBAKER_PT_ReportFramesPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reportframespanel"
    bl_parent_id = "VATBAKER_PT_reportpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 12

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

        row = layout.row()
        row.prop(report, "tex_sampling_mode")
        row.enabled = False

        if report.tex_sampling_mode == "STACK":
            row = layout.row()
            row.prop(report, "tex_packing_stack_mode")
            row.enabled = False

        layout.separator()

        icon = "CHECKMARK" if report.padded else "ERROR" if (scene.VATBakerSettings.frame_padding > 0 and not report.padded) else "X"
        row = layout.row()
        row.label(text="Padding: " + str(report.padding), icon=icon)

        if report.padded:
            row = layout.row()
            row.prop(report, "padding_mode", text="")
            row.enabled = False

        layout.separator()

        row = layout.row()
        col = row.split()
        col.label(text="Start: " + str(report.start_frame))
        col.label(text="End: " + str(report.end_frame))
        row.enabled = False

        row = layout.row()
        col = row.split()
        col.label(text="Frames: " + str(report.num_frames))
        col.enabled = False
        col.label(text="Step: " + str(report.frame_step))
        col.enabled = report.frame_step != 1
        col.label(text="FPS: " + str(report.frame_rate))
        col.enabled = report.frame_rate != 24.0

        row = layout.row()
        if report.tex_sampling_mode == 'CONTINUOUS':
            row.label(text="Width: " + str(report.frame_width))
            row.enabled = report.tex_underflow or report.tex_overflow
        else:
            row.label(text="Height: " + str(report.frame_height))
            row.enabled = report.tex_overflow

class VATBAKER_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "VATBAKER_PT_reportunitpanel"
    bl_parent_id = "VATBAKER_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.VATBakerReport

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