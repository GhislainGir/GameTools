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
from pathlib import Path

from bl_ui.utils import PresetPanel

from . import Functions
from .Functions import get_texture_channel_allow_remap

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class OBJECTATTRIBUTES_MT_MainPanel_Presets(bpy.types.Menu):
    bl_label = 'Object Attributes Presets'
    preset_subdir = 'operator/gametools_objectattributes'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class OBJECTATTRIBUTES_PT_ObjectAttributes_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'Object Attributes Presets'
    preset_subdir = 'operator/gametools_objectattributes'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.objectsattributes_addpreset'

############
### MAIN ###
class OBJECTATTRIBUTES_UL_TextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                other_tex_names = [texture.name for texture in context.scene.ObjectAttributesSettings.textures if texture != item]
                if item.name in other_tex_names:
                    layout.prop(item, "name", text="", emboss=False, icon="ERROR")
                else:
                    layout.prop(item, "name", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False, icon="TEXTURE")

class OBJECTATTRIBUTES_PT_MainPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Object Attributes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # prevent parent panel to show in any mode but the object mode
        if bpy.context.object is None:
            return False

        return True

    def draw_header_preset(self, _context):
        OBJECTATTRIBUTES_PT_ObjectAttributes_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        row = layout.row()
        row.scale_y = 2.0 # bigger button
        row.operator("gametools.oabaker_bakeoa")
        row.enabled = len(settings.textures) > 0

        row = layout.row()
        row.template_list("OBJECTATTRIBUTES_UL_TextureList", "", settings, "textures", settings, "textures_selected_index", rows=5)

        col = row.column(align=True)
        col.operator("objectattributes_item.new_item", text="", icon="ADD")
        col.operator("objectattributes_item.delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("objectattributes_item.move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("objectattributes_item.move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        if settings.textures:
            try:
                texture = settings.textures[settings.textures_selected_index]
            except:
                texture = None

            if texture:
                row = layout.row()
                row.prop(texture, "name", text="Name")

class OBJECTATTRIBUTES_PT_ChannelsPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_channelspanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Channels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0
    
    #bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.ObjectAttributesSettings
        return settings.textures
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        if settings.textures:
            texture = settings.textures[settings.textures_selected_index]

            if texture:
                channels = [
                    (texture.R, "R"),
                    (texture.G, "G"),
                    (texture.B, "B"),
                    (texture.A, "A"),
                    ]

                for texture_channel, texture_channel_name in channels:
                    if texture_channel.channel_mode == "NONE":
                        row = layout.row()
                        row.prop(texture_channel, "channel_mode", text=texture_channel_name)
                    else:
                        panel_header, panel_body = layout.panel(texture_channel_name)
                        if panel_header:
                            panel_header.prop(texture_channel, "channel_mode", text=texture_channel_name)
                        if panel_body:
                            if texture_channel.channel_mode == "POSITION":
                                row = panel_body.row()
                                row.prop(texture_channel, "reference_mode")

                                row = panel_body.row()
                                row.prop(texture_channel, "component")

                                row = panel_body.row()
                                row.prop(texture_channel, "obj_mode")
                            elif texture_channel.channel_mode == "AXIS":
                                row = panel_body.row()
                                row.prop(texture_channel, "reference_mode")

                                row = panel_body.row()
                                row.prop(texture_channel, "component")

                                row = panel_body.row()
                                row.prop(texture_channel, "axis")

                                row = panel_body.row()
                                row.prop(texture_channel, "obj_mode")
                            elif texture_channel.channel_mode == "SCALE":
                                row = panel_body.row()
                                row.prop(texture_channel, "reference_mode")

                                row = panel_body.row()
                                row.prop(texture_channel, "component")

                                row = panel_body.row()
                                row.prop(texture_channel, "obj_mode")
                            elif texture_channel.channel_mode == "EXTENTS":
                                row = panel_body.row()
                                row.prop(texture_channel, "axis")

                                row = panel_body.row()
                                row.prop(texture_channel, "obj_mode")
                            elif texture_channel.channel_mode == "HIERARCHY":
                                row = panel_body.row()
                                row.prop(texture_channel, "depth")
                            elif texture_channel.channel_mode == "CUSTOM_PROP":
                                row = panel_body.row()
                                row.prop(texture_channel, "name")

                                row = panel_body.row()
                                row.prop(texture_channel, "custom_prop_mode")

                                row = panel_body.row()
                                row.prop(texture_channel, "obj_mode")
                            elif texture_channel.channel_mode == "QUATERNION":
                                row = panel_body.row()
                                row.prop(texture_channel, "reference_mode")

                                row = panel_body.row()
                                row.prop(texture_channel, "quat")

                                row = panel_body.row()
                                col = row.split()
                                col.prop(texture_channel, "override_xyz_order")
                                col = row.split()
                                col.prop(texture_channel, "quat_xyz_order")
                                col.enabled = texture_channel.override_xyz_order

                                row = panel_body.row()
                                row.prop(texture_channel, "obj_mode")
                            else:
                                pass
                            
                            if texture_channel.channel_mode != "HIERARCHY":
                                if texture_channel.obj_mode == "SELF":
                                    pass
                                elif texture_channel.obj_mode == "PARENT":
                                    row = panel_body.row()
                                    row.prop(texture_channel, "depth")
                                elif texture_channel.obj_mode == "PROPERTY":
                                    row = panel_body.row()
                                    row.prop(texture_channel, "obj_prop")
                                else: # CUSTOM
                                    row = panel_body.row()
                                    row.prop(texture_channel, "obj")

                            if get_texture_channel_allow_remap(texture_channel):
                                row = panel_body.row()
                                row.prop(texture_channel, "remapping")

class OBJECTATTRIBUTES_PT_HierarchyPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_hierarchypanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Hierarchy"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        row = layout.row()
        col = row.split()
        col.prop(settings, "use_pivot_painter_packing")
        col = row.split()
        col.prop(settings, "use_8bit_packing")
        col.enabled = not settings.use_pivot_painter_packing

        layout.separator()

        row = layout.row()
        row.prop(settings, "depth_limit_use")
        
        row = layout.row()
        row.prop(settings, "depth_limit")
        row.enabled = settings.depth_limit_use

        row = layout.row()
        row.operator("gametools.databaker_selectdepth")
        row.scale_y = 2

##############
### MESHES ###
class OBJECTATTRIBUTES_PT_MeshMainPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_meshmainpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

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
        row.prop(settings, "mesh_merge")
        row = layout.row()
        col = row.split()
        col.prop(settings, "mesh_duplicate")
        col = row.split()
        col.prop(settings, "mesh_single_user")
        if settings.mesh_duplicate:
            col.enabled = False

class OBJECTATTRIBUTES_PT_MeshUVPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_meshuvpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_meshmainpanel"
    bl_label = "UV"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        row = layout.row()
        row.prop(settings, "mesh_uvmap_name", text="Name")

        row = layout.row()
        row.prop(settings, "unit_invert_v")

class OBJECTATTRIBUTES_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_meshexportpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_meshmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 50
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        layout.prop(settings, "export_mesh", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        layout.enabled = settings.export_mesh and bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class OBJECTATTRIBUTES_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_meshadvexportpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

################
### TEXTURES ###
class OBJECTATTRIBUTES_PT_TexMainPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_texmainpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

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

class OBJECTATTRIBUTES_PT_TexExportPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_texexportpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_texmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        layout.prop(settings, "export_tex", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings
        
        layout.enabled = settings.export_tex and bpy.data.is_saved
    
        row = layout.row()
        row.prop(settings, "export_tex_file_name")

        row = layout.row()
        row.prop(settings, "export_tex_file_path")

class OBJECTATTRIBUTES_PT_TexAdvExportPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_texadvexportpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_texexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings
    
        row = layout.row()
        row.prop(settings, "export_tex_override")

###########
### XML ###
class OBJECTATTRIBUTES_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_xmlpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

class OBJECTATTRIBUTES_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_xmlexportpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_xmlpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        layout.prop(settings, "export_xml", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

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
class OBJECTATTRIBUTES_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_reportpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.ObjectAttributesReport.baked

    # def draw_header(self, context):
    #     report = context.ObjectAttributesReport
    #     row = self.layout.row(align=True)
    #     if report.success:
    #         row.label(text="", icon="CHECKMARK")
    #     else:
    #         row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.ObjectAttributesReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.objectattributes_export_report")
            col = row.split()
            col.operator("gametools.objectattributes_clear_report")

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

class OBJECTATTRIBUTES_UL_ReportTexturesList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.label(text=item.name, translate=False, icon="ANIM_DATA")
            else:
                layout.label(text="", translate=False, icon="ANIM_DATA")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class OBJECTATTRIBUTES_PT_ReportTexPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_reporttexpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_reportpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.ObjectAttributesReport

        layout.template_list("OBJECTATTRIBUTES_UL_ReportTexturesList", "", report, "textures", report, "textures_selected_index", rows=3)
        if report.textures:
            texture = report.textures[report.textures_selected_index]
            if texture:
                row = layout.row()
                row.prop(texture, "ID", text="")
                row.enabled = False

                row = layout.row()
                col = row.split()
                col.label(text="Width: " + str(report.tex_width))
                col.label(text="Height: " + str(report.tex_height))

                if texture.exported:
                    row = layout.row()
                    row.label(text="File: " + texture.path, icon="FILE")

                texture_channels = [
                    ("texture_channel_R", "R", texture.R, texture.R_range_offset, texture.R_range, texture.R_range_valid),
                    ("texture_channel_G", "G", texture.G, texture.G_range_offset, texture.G_range, texture.G_range_valid),
                    ("texture_channel_B", "B", texture.B, texture.B_range_offset, texture.B_range, texture.B_range_valid),
                    ("texture_channel_A", "A", texture.A, texture.A_range_offset, texture.A_range, texture.A_range_valid)
                ]
                for texture_channel_name, texture_channel_prefix, texture_channel, texture_channel_range_offset, texture_channel_range, texture_channel_range_valid in texture_channels:
                    panel_header, panel_body = layout.panel(texture_channel_name)
                    if panel_header:
                        panel_header.prop(texture_channel, "channel_mode", text=texture_channel_prefix)
                        panel_header.enabled = False
                    if panel_body:
                        panel_body.enabled = False
                        if texture_channel.channel_mode == "POSITION":
                            row = panel_body.row()
                            row.prop(texture_channel, "reference_mode")

                            row = panel_body.row()
                            row.prop(texture_channel, "component")

                            row = panel_body.row()
                            row.prop(texture_channel, "obj_mode")
                        elif texture_channel.channel_mode == "AXIS":
                            row = panel_body.row()
                            row.prop(texture_channel, "reference_mode")

                            row = panel_body.row()
                            row.prop(texture_channel, "component")

                            row = panel_body.row()
                            row.prop(texture_channel, "axis")

                            row = panel_body.row()
                            row.prop(texture_channel, "obj_mode")
                        elif texture_channel.channel_mode == "SCALE":
                            row = panel_body.row()
                            row.prop(texture_channel, "reference_mode")

                            row = panel_body.row()
                            row.prop(texture_channel, "component")

                            row = panel_body.row()
                            row.prop(texture_channel, "obj_mode")
                        elif texture_channel.channel_mode == "EXTENTS":
                            row = panel_body.row()
                            row.prop(texture_channel, "axis")

                            row = panel_body.row()
                            row.prop(texture_channel, "obj_mode")
                        elif texture_channel.channel_mode == "HIERARCHY":
                            row = panel_body.row()
                            row.prop(texture_channel, "depth")
                        elif texture_channel.channel_mode == "CUSTOM_PROP":
                            row = panel_body.row()
                            row.prop(texture_channel, "name")

                            row = panel_body.row()
                            row.prop(texture_channel, "custom_prop_mode")

                            row = panel_body.row()
                            row.prop(texture_channel, "obj_mode")
                        elif texture_channel.channel_mode == "QUATERNION":
                            row = panel_body.row()
                            row.prop(texture_channel, "reference_mode")

                            row = panel_body.row()
                            row.prop(texture_channel, "quat")

                            row = panel_body.row()
                            col = row.split()
                            col.prop(texture_channel, "override_xyz_order")
                            col = row.split()
                            col.prop(texture_channel, "quat_xyz_order")
                            col.enabled = texture_channel.override_xyz_order

                            row = panel_body.row()
                            row.prop(texture_channel, "obj_mode")
                        else:
                            pass
                        
                        if texture_channel.channel_mode != "HIERARCHY":
                            if texture_channel.obj_mode == "SELF":
                                pass
                            elif texture_channel.obj_mode == "PARENT":
                                row = panel_body.row()
                                row.prop(texture_channel, "depth")
                            elif texture_channel.obj_mode == "PROPERTY":
                                row = panel_body.row()
                                row.prop(texture_channel, "obj_prop")
                            else: # CUSTOM
                                row = panel_body.row()
                                row.prop(texture_channel, "obj")

                        icon = "CHECKMARK" if texture_channel_range_valid else "ERROR"
                        row = layout.row()
                        row.label(text="Offset: %.5f" % texture_channel_range_offset, icon="DOT")
                        row.enabled = texture_channel.remapping and get_texture_channel_allow_remap(texture_channel)
                        row = layout.row()
                        row.label(text="Range: %.5f" % texture_channel_range, icon=icon)
                        row.enabled = texture_channel.remapping and get_texture_channel_allow_remap(texture_channel)

class OBJECTATTRIBUTES_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_reportmeshpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.ObjectAttributesReport
        row = self.layout.row(align=True)
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.ObjectAttributesReport

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
            row.label(text="Objects: " + str(report.mesh_num_indices))

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

        else:
            row = layout.row()
            row.label(text="None generated")

class OBJECTATTRIBUTES_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_reportxmlpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_reportpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.ObjectAttributesReport
        row = self.layout.row(align=True)
        if report.xml:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.ObjectAttributesReport

        row = layout.row()
        if report.xml:
            row.label(text="File: " + report.xml_path, icon="FILE")
        else:
            row.label(text="Not exported", icon="X")

class OBJECTATTRIBUTES_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_reportunitpanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.ObjectAttributesReport

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