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
from .Functions import get_bake_subdivisions

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
### FRAME ###
class FFTOCEANBAKER_PT_FramePanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_framepanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Frame"
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

#############
### OCEAN ###
class FFTOCEANBAKER_PT_OceanPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_oceanpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_mainpanel"
    bl_label = "Ocean"
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
        row.prop(settings, "subd")

        if settings.subd == "CUSTOM":
            row = layout.row()
            row.prop(settings, "subd_custom_subd")

        subd = get_bake_subdivisions(context)
        faces = pow(subd, 4)

        row = layout.row()
        row.label(text="Faces: " + str(faces))

        row = layout.row()
        row.prop(settings, "anim_speed")

        row = layout.row()
        col = row.split()
        col.prop(settings, "ocean_size")
        col = row.split()
        col.prop(settings, "ocean_spatial_size")

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
        row.prop(settings, "unit_scale")

        row = layout.row()
        row.label(text="Invert")
        row.prop(settings, "unit_invert_x", text="X")
        row.prop(settings, "unit_invert_y", text="Y")
        row.prop(settings, "unit_invert_z", text="Z")

        row = layout.row()
        row.prop(settings, "mesh_name")

class FFTOCEANBAKER_PT_MeshUVPanel(bpy.types.Panel):
    bl_idname = "FFTOCEANBAKER_PT_meshuvpanel"
    bl_parent_id = "FFTOCEANBAKER_PT_meshpanel"
    bl_label = "UV"
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
        row.prop(settings, "unit_invert_v")

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

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.FFTOCEANBAKERReport