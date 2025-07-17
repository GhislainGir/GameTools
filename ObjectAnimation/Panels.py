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
from .Functions import get_texture_channel_allow_remap

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class OATBAKER_MT_ObjectAnimation_Presets(bpy.types.Menu):
    bl_label = 'OA Presets'
    preset_subdir = 'operator/gametools_oatbaker'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class OATBAKER_PT_ObjectAnimation_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'OA Presets'
    preset_subdir = 'operator/gametools_oatbaker'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.oatbaker_addpreset'

############
### MAIN ###
class OATBAKER_PT_MainPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_mainpanel"
    bl_label = "OAT Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.active.type == "MESH"

    def draw_header_preset(self, _context):
        OATBAKER_PT_ObjectAnimation_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        row = layout.row()
        row.operator("gametools.oatbaker_bakeoat")
        row.scale_y = 2.0

##############
### MESHES ###
class OATBAKER_PT_MeshMainPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_meshmainpanel"
    bl_parent_id = "OATBAKER_PT_mainpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

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
        row.prop(settings, "mesh_name")

        row = layout.row()
        row.prop(settings, "mesh_materials")

        row = layout.row()
        row.prop(settings, "mesh_target_prop")

        panel_header, panel_body = layout.panel("bat_mesh_previz")
        if panel_header:
            panel_header.label(text="Previz")
        if panel_body:
            row = panel_body.row()
            col = row.split()
            col.prop(settings, "previz_result", text="Anim")
            col.enabled = False
            col = row.split()
            col.prop(settings, "previz_bounds", text="Bounds")

class OATBAKER_PT_MeshUVPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_meshuvpanel"
    bl_parent_id = "OATBAKER_PT_meshmainpanel"
    bl_label = "UV"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        row = layout.row()
        row.prop(settings, "mesh_uvmap_name", text="Name")

        row = layout.row()
        row.prop(settings, "unit_invert_v")

# EXPORT #
class OATBAKER_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_meshexportpanel"
    bl_parent_id = "OATBAKER_PT_meshmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        layout.prop(settings, "export_mesh", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        layout.enabled = settings.export_mesh and bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class OATBAKER_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_meshadvexportpanel"
    bl_parent_id = "OATBAKER_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

################
### TEXTURES ###
class OATBAKER_UL_TextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                other_tex_names = [texture.name for texture in context.scene.OATBakerSettings.textures if texture != item]
                if item.name in other_tex_names:
                    layout.prop(item, "name", text="", emboss=False, icon="ERROR")
                else:
                    layout.prop(item, "name", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="", translate=False, icon="X")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", translate=False, icon="TEXTURE")

class OATBAKER_PT_TexturesPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_texturespanel"
    bl_parent_id = "OATBAKER_PT_mainpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

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

        row = layout.row()
        row.template_list("OATBAKER_UL_TextureList", "", settings, "textures", settings, "textures_selected_index", rows=5)

        col = row.column(align=True)
        col.operator("oat_textures_item.new_item", text="", icon="ADD")
        col.operator("oat_textures_item.delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("oat_textures_item.move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("oat_textures_item.move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        if settings.textures:
            try:
                texture = settings.textures[settings.textures_selected_index]
            except:
                texture = None

            if texture:
                row = layout.row()
                row.prop(texture, "name", text="Name")

class OATBAKER_PT_ChannelsPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_channelspanel"
    bl_parent_id = "OATBAKER_PT_texturespanel"
    bl_label = "Channels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    #bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.OATBakerSettings
        return settings.textures

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

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
                                row.prop(texture_channel, "unit_axis_order")

                                row = panel_body.row()
                                row.prop(texture_channel, "component")
                            elif texture_channel.channel_mode == "ROTATION":
                                row = panel_body.row()
                                row.prop(texture_channel, "unit_axis_order")

                                row = panel_body.row()
                                row.prop(texture_channel, "rot_mode")

                                if texture_channel.rot_mode == "QUAT":
                                    row = panel_body.row()
                                    row.prop(texture_channel, "quat")    
                                else: #AXIS_ANGLE
                                    row = panel_body.row()
                                    row.prop(texture_channel, "axis_angle_mode")

                                    if texture_channel.axis_angle_mode == "ANGLE":
                                        row = panel_body.row()
                                        row.prop(texture_channel, "quat_angle_unit_mode")
                            elif texture_channel.channel_mode == "SCALE":
                                row = panel_body.row()
                                row.prop(texture_channel, "unit_axis_order")

                                row = panel_body.row()
                                row.prop(texture_channel, "component")
                            elif texture_channel.channel_mode == "AXIS":
                                row = panel_body.row()
                                row.prop(texture_channel, "axis")

                                row = panel_body.row()
                                row.prop(texture_channel, "component")

                                row = panel_body.row()
                                row.prop(texture_channel, "axis_scaled")
                            elif texture_channel.channel_mode == "CUSTOM_PROP":
                                row = panel_body.row()
                                row.prop(texture_channel, "name")
                            else:
                                pass

                            if get_texture_channel_allow_remap(texture_channel):
                                row = panel_body.row()
                                row.prop(texture_channel, "remapping")

##########
# EXPORT #
class OATBAKER_PT_TexExportPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_texexportpanel"
    bl_parent_id = "OATBAKER_PT_channelspanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        layout.prop(settings, "export_tex", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        layout.enabled = settings.export_tex and bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_tex_file_path")

class OATBAKER_PT_TexAdvExportPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_texadvexportpanel"
    bl_parent_id = "OATBAKER_PT_texexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        row = layout.row()
        row.prop(settings, "export_tex_override")

#############
### SCENE ###
class OATBAKER_PT_FramePanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_framepanel"
    bl_parent_id = "OATBAKER_PT_mainpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

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

            row = layout.row()
            row.prop(settings, "frame_ref_padding", text="Ref Padding:")
        
        elif (settings.frame_range_mode == "SCENE"):
            row = layout.row()
            row.label(text="Frame Range:")

            row = layout.row()
            row.prop(scene, "frame_start", text="")
            row.prop(scene, "frame_end", text="")

            row = layout.row()
            row.prop(scene, "frame_step", text="Step:")

            row = layout.row()
            row.prop(settings, "frame_ref_padding", text="Ref Padding:")
        elif (settings.frame_range_mode == "CUSTOM"):
            row = layout.row()
            row.label(text="Frame Range:")

            row = layout.row()
            row.prop(settings, "frame_range_custom_start", text="")
            row.prop(settings, "frame_range_custom_end", text="")

            row = layout.row()
            row.prop(settings, "frame_range_custom_step", text="Step:")

            row = layout.row()
            row.prop(settings, "frame_ref_padding", text="Ref Padding:")

        row = layout.row()
        row.prop(settings, "frame_ref_mode", text="Ref")
        if settings.frame_ref_mode == "CUSTOM":
            row = layout.row()
            row.prop(settings, "frame_ref_custom", text="Frame")

class OATBAKER_PT_FrameAdvPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_frameadvpanel"
    bl_parent_id = "OATBAKER_PT_framepanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.OATBakerSettings.frame_range_mode == "NLA"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        row = layout.row()
        row.label(text="NLA clips to exclude:")

        row = layout.row()
        row.template_list("OATBAKER_UL_NLAExclusionList", "", settings, "frame_range_nla_exclusion", settings, "frame_range_nla_exclusion_selected_index", rows=4)

        col = row.column(align=True)
        col.operator("gametools.oatbaker_frame_range_nla_exclusion_new_item", text="", icon="ADD")
        col.operator("gametools.oatbaker_frame_range_nla_exclusion_delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("gametools.oatbaker_frame_range_nla_exclusion_move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("gametools.oatbaker_frame_range_nla_exclusion_move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        row = layout.row()
        row.prop(settings, "frame_range_nla_exclusion_selected")

class OATBAKER_UL_NLAExclusionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

###########
### XML ###
class OATBAKER_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_xmlpanel"
    bl_parent_id = "OATBAKER_PT_mainpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

class OATBAKER_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_xmlexportpanel"
    bl_parent_id = "OATBAKER_PT_xmlpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

        layout.prop(settings, "export_xml", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.OATBakerSettings

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
class OATBAKER_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reportpanel"
    bl_parent_id = "OATBAKER_PT_mainpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.OATBakerReport.baked

    # def draw_header(self, context):
    #     report = context.scene.OATBakerReport
    #     row = self.layout.row(align=True)
    #     if report.success:
    #         row.label(text="", icon="CHECKMARK")
    #     else:
    #         row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.oatbaker_export_report")
            col = row.split()
            col.operator("gametools.oatbaker_clear_report")

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

# TEXTURES #
class OATBAKER_PT_ReportTexPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reporttexpanel"
    bl_parent_id = "OATBAKER_PT_reportpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.OATBakerReport
        row = self.layout.row(align=True)
        if report.textures:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

        row = layout.row()
        col = row.split()
        col.label(text="Width: " + str(report.tex_width))
        col.label(text="Height: " + str(report.tex_height))

        row = layout.row()
        row.prop(report, "tex_sampling_mode")
        row.enabled = False

        row = layout.row()
        if report.tex_sampling_mode == 'CONTINUOUS':
            row.label(text="Width: " + str(report.tex_frame_width))
            row.enabled = report.tex_underflow or report.tex_overflow
        else:
            row.label(text="Height: " + str(report.tex_frame_height))
            row.enabled = report.tex_overflow

        row = layout.row()
        row.template_list("OATBAKER_UL_ReportTextureList", "", report, "textures", report, "textures_selected_index", rows=5)

        if report.textures:
            try:
                texture = report.textures[report.textures_selected_index]
            except:
                texture = None

            if texture:
                row = layout.row()
                row.prop(texture, "img", text="")
                row.enabled = False

                if texture.exported:
                    row = layout.row()
                    row.label(text=texture.path, icon="CHECKMARK")
                else:
                    row = layout.row()
                    row.label(text="Not exported", icon="ERROR")

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
                            row.prop(texture_channel, "unit_axis_order")

                            row = panel_body.row()
                            row.prop(texture_channel, "component")
                        elif texture_channel.channel_mode == "ROTATION":
                            row = panel_body.row()
                            row.prop(texture_channel, "unit_axis_order")

                            row = panel_body.row()
                            row.prop(texture_channel, "rot_mode")

                            if texture_channel.rot_mode == "QUAT":
                                row = panel_body.row()
                                row.prop(texture_channel, "quat")
                            else: #AXIS_ANGLE
                                row = panel_body.row()
                                row.prop(texture_channel, "axis_angle_mode")

                                if texture_channel.axis_angle_mode == "ANGLE":
                                    row = panel_body.row()
                                    row.prop(texture_channel, "quat_angle_unit_mode")
                        elif texture_channel.channel_mode == "SCALE":
                            row = panel_body.row()
                            row.prop(texture_channel, "unit_axis_order")

                            row = panel_body.row()
                            row.prop(texture_channel, "component")
                        elif texture_channel.channel_mode == "AXIS":
                            row = panel_body.row()
                            row.prop(texture_channel, "axis")

                            row = panel_body.row()
                            row.prop(texture_channel, "component")

                            row = panel_body.row()
                            row.prop(texture_channel, "axis_scaled")
                        elif texture_channel.channel_mode == "CUSTOM_PROP":
                            row = panel_body.row()
                            row.prop(texture_channel, "name")
                        else:
                            pass

                        icon = "CHECKMARK" if texture_channel_range_valid else "ERROR"
                        row = layout.row()
                        row.label(text="Offset: %.5f" % texture_channel_range_offset, icon="DOT")
                        row.enabled = texture_channel.remapping and get_texture_channel_allow_remap(texture_channel)
                        row = layout.row()
                        row.label(text="Range: %.5f" % texture_channel_range, icon=icon)
                        row.enabled = texture_channel.remapping and get_texture_channel_allow_remap(texture_channel)

class OATBAKER_UL_ReportTextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = context.scene.BATBakerSettings
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.prop(item, "name", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="", translate=False, icon="TEXTURE")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

# MESH #
class OATBAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reportmeshpanel"
    bl_parent_id = "OATBAKER_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.OATBakerReport
        row = self.layout.row(align=True)
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

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
            row.label(text="None generated")

# XML #
class OATBAKER_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reportxmlpanel"
    bl_parent_id = "OATBAKER_PT_reportpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.OATBakerReport
        row = self.layout.row(align=True)
        if report.xml:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

        row = layout.row()
        if report.xml:
            row.label(text="File: " + report.xml_path, icon="FILE")
        else:
            row.label(text="Not exported", icon="X")

# ANIMS #
class OATBAKER_PT_ReportAnimsPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reportanimspanel"
    bl_parent_id = "OATBAKER_PT_reportpanel"
    bl_label = "Anims"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10

    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.OATBakerReport.success

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

        layout.template_list("OATBAKER_UL_ReportAnimsList", "", report, "anims", report, "selected_anim", rows=3)
        if report.anims:
            anim = report.anims[report.selected_anim]
            if anim:
                row = layout.row()
                row.label(text="Length: " + str(anim.end_frame - (anim.start_frame - 1)))

                row = layout.row()
                row.label(text="Start: " + str(anim.start_frame))
                row = layout.row()
                row.label(text="End: " + str(anim.end_frame))

class OATBAKER_UL_ReportAnimsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.label(text=item.name, translate=False, icon="ANIM_DATA")
            else:
                layout.label(text="", translate=False, icon="ANIM_DATA")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

# FRAMES #
class OATBAKER_PT_ReportFramesPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reportframespanel"
    bl_parent_id = "OATBAKER_PT_reportpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 12

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

        row = layout.row()
        row.prop(report, "tex_sampling_mode")
        row.enabled = False

        if report.tex_sampling_mode == "STACK":
            row = layout.row()
            row.prop(report, "tex_packing_stack_mode")
            row.enabled = False

        layout.separator()

        icon = "CHECKMARK" if report.padded else "ERROR" if (scene.BATBakerSettings.frame_padding > 0 and not report.padded) else "X"
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

# UNIT #
class OATBAKER_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_reportunitpanel"
    bl_parent_id = "OATBAKER_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.OATBakerReport

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