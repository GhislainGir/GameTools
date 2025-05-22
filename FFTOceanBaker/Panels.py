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
import math

from bl_ui.utils import PresetPanel

from . import Functions
from .Functions import get_bake_frame_padding

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class FFTOCEANBAKER_MT_FFTOceanBaker_Presets(bpy.types.Menu):
    bl_label = 'FFT Ocean Baker Presets'
    preset_subdir = 'operator/gametools_fftoceanbaker'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class FFTOCEANBAKER_PT_FFTOceanBaker_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'FFT Ocean Baker Presets'
    preset_subdir = 'operator/gametools_fftoceanbaker'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.fftoceanbaker_addpreset'

############
### MAIN ###
class FFTOCEANBAKER_PT_FFTOceanBaker(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "FFT Ocean Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header_preset(self, _context):
        FFTOCEANBAKER_PT_FFTOceanBaker_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings
        report = scene.FFTOCEANBAKERReport

        row = layout.row()
        row.operator("gametools.fftoceanbaker_bakefftocean")
        row.scale_y = 2.0

#############
### OCEAN ###
class FFTOCEANBAKER_PT_OceanPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_oceanpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Ocean"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        row = layout.row()
        row.prop(settings, "subd")

        subd = max(2, settings.subd)
        res = subd * subd
        faces = res * res

        row = layout.row()
        row.label(text="Faces: " + str(faces))
        row.label(text="Res: " + str(res) + "x" + str(res))

        box = layout.box()
        box.enabled = not settings.ocean_from_active
    
        row = box.row()
        row.prop(settings, "ocean_time")

        row = box.row()
        col = row.split()
        col.prop(settings, "ocean_size")
        col = row.split()
        col.prop(settings, "ocean_spatial_size")

        row = box.row()
        row.prop(settings, "ocean_depth")

        row = box.row()
        row.prop(settings, "ocean_seed")

        row = box.row()
        row.prop(settings, "ocean_scale")

        row = box.row()
        row.prop(settings, "ocean_smallest_wave")

        row = box.row()
        row.prop(settings, "ocean_choppiness")

        row = box.row()
        row.prop(settings, "ocean_wind_vel")

        row = box.row()
        row.prop(settings, "ocean_alignment")

        row = box.row()
        row.prop(settings, "ocean_direction")
        row.enabled = settings.ocean_alignment > 0

        row = box.row()
        row.prop(settings, "ocean_damping")
        row.enabled = settings.ocean_alignment > 0

        row = layout.row()
        row.prop(settings, "ocean_from_active")
        row.prop(settings, "ocean_clear")

##############
### FRAMES ###
class FFTOCEANBAKER_PT_FramesPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_framespanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        row = layout.row()
        row.prop(settings, "frame_range_mode")

        if settings.frame_range_mode == "CUSTOM":
            row = layout.row()
            col = row.split()
            col.prop(settings, "frame_range_custom_start")
            col = row.split()
            col.prop(settings, "frame_range_custom_end")

            row = layout.row()
            row.prop(settings, "frame_range_custom_step")

############
### MESH ###
class FFTOCEANBAKER_PT_MeshPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_meshpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        row = layout.row()
        row.prop(settings, "mesh_name")

        row = layout.row()
        row.prop(settings, "generate_mesh")

class FFTOCEANBAKER_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_meshexportpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_meshpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.prop(settings, "export_mesh", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.enabled = settings.export_mesh and bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class FFTOCEANBAKER_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_meshadvexportpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

################
### TEXTURES ###
class FFTOCEANBAKER_PT_TexMainPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_texmainpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        row = layout.row()
        row.prop(settings, "tex_mode")

        row = layout.row()
        row.prop(settings, "flipbook_max_size")
        if settings.tex_mode != "FLIPBOOK":
            row.enabled = False
        row = layout.row()
        row.prop(settings, "frames_per_row")
        if settings.tex_mode != "FLIPBOOK":
            row.enabled = False
        row = layout.row()
        row.prop(settings, "frame_sort_mode")
        if settings.tex_mode != "FLIPBOOK":
            row.enabled = False

        row = layout.row()
        row.prop(settings, "unit_invert_u")
        row.prop(settings, "unit_invert_v")

        layout.separator()

        row = layout.row()
        row.prop(settings, "frame_size_mode")
        row = layout.row()
        row.prop(settings, "frame_size_custom")
        if settings.frame_size_mode != "CUSTOM":
            row.enabled = False

        layout.separator()

        row = layout.row()
        row.prop(settings, "frame_padding_mode")
        if settings.frame_padding_mode == "MIPLEVEL":
            row = layout.row()
            row.prop(settings, "frame_padding_mips")
        elif settings.frame_padding_mode == "PIXELS":
            row = layout.row()
            row.prop(settings, "frame_padding_pixels")
        else: # NONE
            pass

        padding = get_bake_frame_padding(context, clamp=True)
        row = layout.row()
        row.label(text="Padding: " + str(padding))

class FFTOCEANBAKER_PT_TexOffsetPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_texnoffsetpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_texmainpanel"
    bl_label = "Offsets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.prop(settings, "offset_tex", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings
        
        layout.enabled = settings.offset_tex
        
        row = layout.row()
        row.prop(settings, "unit_scale")

        row = layout.row()
        row.prop(settings, "offset_tex_mode")    

        row = layout.row()
        row.prop(settings, "offset_tex_file_name")

        row = layout.row()
        row.prop(settings, "offset_tex_remap")

class FFTOCEANBAKER_PT_TexNormalPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_texnormalpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_texmainpanel"
    bl_label = "Normals"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.prop(settings, "normal_tex", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.enabled = settings.normal_tex
    
        row = layout.row()
        row.prop(settings, "normal_tex_file_name")

        row = layout.row()
        row.prop(settings, "normal_tex_remap")

class FFTOCEANBAKER_PT_TexExportPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_texexportpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_texmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.prop(settings, "export_tex", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings
        
        layout.enabled = settings.export_tex and bpy.data.is_saved
    
        row = layout.row()
        row.prop(settings, "export_tex_file_path")

class FFTOCEANBAKER_PT_TexAdvExportPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_texadvexportpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_texexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings
    
        row = layout.row()
        row.prop(settings, "export_tex_override")

###########
### XML ###
class FFTOCEANBAKER_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_xmlpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

class FFTOCEANBAKER_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_xmlexportpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_xmlpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

        layout.prop(settings, "export_xml", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.FFTOCEANBAKERSettings

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
class FFTOCEANBAKER_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_reportpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.FFTOCEANBAKERReport.baked

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.FFTOCEANBAKERReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.fftoceanbaker_export_report")
            col = row.split()
            col.operator("gametools.fftoceanbaker_clear_report")

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

class FFTOCEANBAKER_PT_ReportTexPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_reporttexpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_reportpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.FFTOCEANBAKERReport
        row = self.layout.row(align=True)
        if report.tex_offset or report.tex_normal:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.FFTOCEANBAKERReport

        row = layout.row()
        col = row.split()
        col.label(text="Width: " + str(report.tex_width))
        col.label(text="Height: " + str(report.tex_height))

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
                layout.separator()

                row = layout.row()
                row.label(text="Offset")

                row = layout.row()
                row.label(text="X: " + str(report.tex_offset_range_offset[0]), icon="DOT")
                row = layout.row()
                row.label(text="Y: " + str(report.tex_offset_range_offset[1]), icon="DOT")
                row = layout.row()
                row.label(text="Z: " + str(report.tex_offset_range_offset[2]), icon="DOT")

                layout.separator()

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
        else:
            row.label(text="None generated", icon="X")

class FFTOCEANBAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_reportmeshpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.FFTOCEANBAKERReport
        row = self.layout.row(align=True)
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.FFTOCEANBAKERReport

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
            row.label(text="None generated")

class FFTOCEANBAKER_PT_ReportOceanPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_reportoceanpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_reportpanel"
    bl_label = "Ocean"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 13

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.FFTOCEANBAKERReport
    
        row = layout.row()
        row.label(text="Subdivisions: " + str(report.subd))

        row = layout.row()
        row.label(text="Time: " + str(report.ocean_time))

        row = layout.row()
        row.label(text="Size: " + str(report.ocean_size))
        row.label(text="Spatial Size: " +str( report.ocean_spatial_size))

        row = layout.row()
        row.label(text="Depth: " + str(report.ocean_depth))

        row = layout.row()
        row.label(text="Seed: " + str(report.ocean_seed))

        row = layout.row()
        row.label(text="Scale: " + str(report.ocean_scale))

        row = layout.row()
        row.label(text="Smallest Wave: %.3f" % report.ocean_smallest_wave)

        row = layout.row()
        row.label(text="Chopiness: " + str(report.ocean_choppiness))

        row = layout.row()
        row.label(text="Wind Vel: " + str(report.ocean_wind_vel))

        row = layout.row()
        row.label(text="Alignment: " + str(report.ocean_alignment))

        row = layout.row()
        row.label(text="Direction: " + str(report.ocean_direction))

        row = layout.row()
        row.label(text="Damping: " + str(report.ocean_damping))

class FFTOCEANBAKER_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_reportunitpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.FFTOCEANBAKERReport

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

        icon = "CHECKMARK" if report.unit_invert_u else "X"
        row = layout.row()
        row.label(text="X: " + str(report.unit_invert_u), icon=icon)
        row.enabled = report.unit_invert_u

        icon = "CHECKMARK" if report.unit_invert_v else "X"
        row = layout.row()
        row.label(text="Y: " + str(report.unit_invert_v), icon=icon)
        row.enabled = report.unit_invert_v