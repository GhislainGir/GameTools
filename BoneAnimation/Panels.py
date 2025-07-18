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

from . import Functions
from .Functions import get_animation_texture_channel_allow_remap

####################################################################################
###################################### PANELS ######################################
####################################################################################

###############
### PRESETS ###
class BATBAKER_MT_BoneAnimation_Presets(bpy.types.Menu):
    bl_label = 'BAT Baker Presets'
    preset_subdir = 'operator/gametools_batbaker'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class BATBAKER_PT_BoneAnimation_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'BAT Baker Presets'
    preset_subdir = 'operator/gametools_batbaker'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.batbaker_addpreset'

############
### MAIN ###
class BATBAKER_PT_MainPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_mainpanel"
    bl_label = "BAT Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.active.type == "MESH"

    def draw_header_preset(self, _context):
        BATBAKER_PT_BoneAnimation_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        row = layout.row()
        row.operator("gametools.batbaker_bakebat")
        row.scale_y = 2.0

#############
### SCENE ###
class BATBAKER_PT_FramePanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_framepanel"
    bl_parent_id = "BATBAKER_PT_mainpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

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

class BATBAKER_PT_FrameAdvPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_frameadvpanel"
    bl_parent_id = "BATBAKER_PT_framepanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.frame_range_mode == "NLA"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        row = layout.row()
        row.label(text="NLA clips to exclude:")

        row = layout.row()
        row.template_list("BATBAKER_UL_NLAExclusionList", "", settings, "frame_range_nla_exclusion", settings, "frame_range_nla_exclusion_selected_index", rows=4)

        col = row.column(align=True)
        col.operator("gametools.batbaker_frame_range_nla_exclusion_new_item", text="", icon="ADD")
        col.operator("gametools.batbaker_frame_range_nla_exclusion_delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("gametools.batbaker_frame_range_nla_exclusion_move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("gametools.batbaker_frame_range_nla_exclusion_move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        row = layout.row()
        row.prop(settings, "frame_range_nla_exclusion_selected")

class BATBAKER_UL_NLAExclusionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

##############
### MESHES ###
class BATBAKER_PT_MeshMainPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_meshmainpanel"
    bl_parent_id = "BATBAKER_PT_mainpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

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

class BATBAKER_PT_MeshUVPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_meshuvpanel"
    bl_parent_id = "BATBAKER_PT_meshmainpanel"
    bl_label = "UV"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        row = layout.row()
        row.prop(settings, "mesh_uvmap_name", text="Name")

        row = layout.row()
        row.prop(settings, "unit_invert_v")

# EXPORT #
class BATBAKER_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_meshexportpanel"
    bl_parent_id = "BATBAKER_PT_meshmainpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        layout.prop(settings, "export_mesh", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        layout.enabled = settings.export_mesh and bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class BATBAKER_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_meshadvexportpanel"
    bl_parent_id = "BATBAKER_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

################
### TEXTURES ###
class BATBAKER_PT_TexturesPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_texturespanel"
    bl_parent_id = "BATBAKER_PT_mainpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

# SKINNING TEXTURES #
class BATBAKER_UL_SkinningTextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = context.scene.BATBakerSettings
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                other_tex_names = [texture.name for texture in settings.skinning_textures if texture != item]
                animation_tex_names = [texture.name for texture in settings.animation_textures]
                all_other_tex_names = other_tex_names + animation_tex_names
                if item.name in all_other_tex_names:
                    layout.prop(item, "name", text="", emboss=False, icon="ERROR")
                else:
                    if item.storage_mode == "VCOL":
                        if len(item.rows) > 1:
                            layout.prop(item, "name", text="", emboss=False, icon="ERROR")
                        else:
                            layout.prop(item, "name", text="", emboss=False, icon="COLOR")
                    else:
                        layout.prop(item, "name", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="", translate=False, icon="TEXTURE")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class BATBAKER_UL_SkinningRowList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.label(text=item.name, translate=False, icon="DOT")
            else:
                layout.label(text="", translate=False, icon="DOT")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class BATBAKER_PT_SkinningTexturesPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_skinningtexturespanel"
    bl_parent_id = "BATBAKER_PT_texturespanel"
    bl_label = "Skinning Data"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        row = layout.row()
        row.prop(settings, "skinning_tex_max_width")

        row = layout.row()
        row.prop(settings, "skinning_tex_max_height")

        row = layout.row()
        row.prop(settings, "skinning_tex_res_mode")

        row = layout.row()
        row.template_list("BATBAKER_UL_SkinningTextureList", "", settings, "skinning_textures", settings, "skinning_textures_selected_index", rows=5)

        col = row.column(align=True)
        col.operator("gametools.batbaker_skinning_texturelist_new_item", text="", icon="ADD")
        col.operator("gametools.batbaker_skinning_texturelist_delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("gametools.batbaker_skinning_texturelist_move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("gametools.batbaker_skinning_texturelist_move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        if settings.skinning_textures:
            try:
                texture = settings.skinning_textures[settings.skinning_textures_selected_index]
            except:
                texture = None

            if texture:
                row = layout.row()
                row.prop(texture, "name", text="Name")

                row = layout.row()
                row.prop(texture, "storage_mode")

                row = layout.row()
                row.template_list("BATBAKER_UL_SkinningRowList", "", texture, "rows", texture, "rows_selected_index", rows=3)

                col = row.column(align=True)
                col.operator("gametools.batbaker_skinning_rowlist_new_item", text="", icon="ADD")
                col.operator("gametools.batbaker_skinning_rowlist_delete_item", text="", icon="REMOVE")

                col.separator()

                col.operator("gametools.batbaker_skinning_rowlist_move_item", text="", icon="TRIA_UP").direction = "UP"
                col.operator("gametools.batbaker_skinning_rowlist_move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

                try:
                    texture_row = texture.rows[texture.rows_selected_index]
                except:
                    texture_row = None

                if texture_row:
                    row = layout.row()
                    row.prop(texture_row, "name", text="Name")

                    channels = [
                        (texture_row.R, "R"),
                        (texture_row.G, "G"),
                        (texture_row.B, "B"),
                        (texture_row.A, "A"),
                        ]

                    for texture_row, texture_row_name in channels:
                        if texture_row.channel_mode == "NONE":
                            row = layout.row()
                            row.prop(texture_row, "channel_mode", text=texture_row_name)
                        else:
                            panel_header, panel_body = layout.panel(texture_row_name)
                            if panel_header:
                                panel_header.prop(texture_row, "channel_mode", text=texture_row_name)
                            if panel_body:
                                if texture_row.channel_mode == "INDEX":
                                    row = panel_body.row()
                                    row.prop(texture_row, "index", text="Bone Index")

                                    row = panel_body.row()
                                    row.prop(texture_row, "remapping")
                                else: # WEIGHT
                                    row = panel_body.row()
                                    row.prop(texture_row, "index", text="Bone Index")

# ANIMATION TEXTURES #
class BATBAKER_UL_AnimationTextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = context.scene.BATBakerSettings
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                other_tex_names = [texture.name for texture in settings.animation_textures if texture != item]
                skinning_tex_names = [texture.name for texture in settings.skinning_textures]
                all_other_tex_names = other_tex_names + skinning_tex_names
                if item.name in all_other_tex_names:
                    layout.prop(item, "name", text="", emboss=False, icon="ERROR")
                else:
                    layout.prop(item, "name", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="", translate=False, icon="TEXTURE")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class BATBAKER_PT_AnimationTexturesPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_animationtexturespanel"
    bl_parent_id = "BATBAKER_PT_texturespanel"
    bl_label = "Animation Data"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        row = layout.row()
        row.prop(settings, "animation_tex_max_width")
        
        row = layout.row()
        row.prop(settings, "animation_tex_max_height")

        row = layout.row()
        col = row.split()
        col.prop(settings, "animation_tex_force_power_of_two")
        col = row.split()
        col.prop(settings, "animation_tex_force_power_of_two_square")
        col.enabled = settings.animation_tex_force_power_of_two

        row = layout.row()
        row.prop(settings, "animation_tex_packing_mode")

        row = layout.row()
        row.prop(settings, "animation_tex_packing_stack_mode")
        row.enabled = settings.animation_tex_packing_mode == "STACK"

        row = layout.row()
        row.template_list("BATBAKER_UL_AnimationTextureList", "", settings, "animation_textures", settings, "animation_textures_selected_index", rows=5)

        col = row.column(align=True)
        col.operator("gametools.batbaker_animation_texturelist_new_item", text="", icon="ADD")
        col.operator("gametools.batbaker_animation_texturelist_delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("gametools.batbaker_animation_texturelist_move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("gametools.batbaker_animation_texturelist_move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

        if settings.animation_textures:
            try:
                texture = settings.animation_textures[settings.animation_textures_selected_index]
            except:
                texture = None

            if texture:
                row = layout.row()
                row.prop(texture, "name", text="Name")

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

                            if get_animation_texture_channel_allow_remap(texture_channel):
                                row = panel_body.row()
                                row.prop(texture_channel, "remapping")

# EXPORT #
class BATBAKER_PT_TexExportPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_texexportpanel"
    bl_parent_id = "BATBAKER_PT_texturespanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        layout.prop(settings, "export_tex", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings
        
        layout.enabled = settings.export_tex and bpy.data.is_saved
    
        row = layout.row()
        row.prop(settings, "export_tex_file_path")

class BATBAKER_PT_TexAdvExportPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_texadvexportpanel"
    bl_parent_id = "BATBAKER_PT_texexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings
    
        row = layout.row()
        row.prop(settings, "export_tex_override")

###########
### XML ###
class BATBAKER_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_xmlpanel"
    bl_parent_id = "BATBAKER_PT_mainpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

class BATBAKER_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_xmlexportpanel"
    bl_parent_id = "BATBAKER_PT_xmlpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

        layout.prop(settings, "export_xml", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.BATBakerSettings

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
class BATBAKER_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportpanel"
    bl_parent_id = "BATBAKER_PT_mainpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerReport.baked

    # def draw_header(self, context):
    #     report = context.scene.BATBakerReport
    #     row = self.layout.row(align=True)
    #     if report.success:
    #         row.label(text="", icon="CHECKMARK")
    #     else:
    #         row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.batbaker_export_report")
            col = row.split()
            col.operator("gametools.batbaker_clear_report")

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
class BATBAKER_PT_ReportTexPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reporttexpanel"
    bl_parent_id = "BATBAKER_PT_reportpanel"
    bl_label = "Textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.BATBakerReport
        row = self.layout.row(align=True)
        if report.skinning_textures and report.animation_textures:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

# SKINNING TEXTURES #
class BATBAKER_UL_ReportSkinningTextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = context.scene.BATBakerSettings
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                if item.storage_mode == "VCOL":
                    layout.prop(item, "name", text="", emboss=False, icon="COLOR")
                else:
                    layout.prop(item, "name", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="", translate=False, icon="DOT")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class BATBAKER_UL_ReportSkinningRowList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.name:
                layout.label(text=item.name, translate=False, icon="DOT")
            else:
                layout.label(text="", translate=False, icon="DOT")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="ANIM_DATA")

class BATBAKER_PT_ReportSkinningTexPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportskinningtexpanel"
    bl_parent_id = "BATBAKER_PT_reporttexpanel"
    bl_label = "Skinning Data"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

        row = layout.row()
        col = row.split()
        col.label(text="Width: " + str(report.skinning_tex_width))
        col.label(text="Height: " + str(report.skinning_tex_height))

        row = layout.row()
        row.prop(report, "skinning_tex_res_mode")
        row.enabled = False

        row = layout.row()
        row.label(text="Rows: " + str(report.skinning_tex_rows))
        row.enabled = report.skinning_tex_rows > 1

        row = layout.row()
        row.template_list("BATBAKER_UL_ReportSkinningTextureList", "", report, "skinning_textures", report, "skinning_textures_selected_index", rows=5)

        if report.skinning_textures:
            try:
                texture = report.skinning_textures[report.skinning_textures_selected_index]
            except:
                texture = None

            if texture:
                row = layout.row()
                row.template_list("BATBAKER_UL_ReportSkinningRowList", "", texture, "rows", texture, "rows_selected_index", rows=3)

                row = layout.row()
                row.prop(texture, "storage_mode")
                row.enabled = False

                if texture.storage_mode == "TEXTURE":
                    row = layout.row()
                    row.prop(texture, "img", text="")
                    row.enabled = False

                    if texture.exported:
                        row = layout.row()
                        row.label(text=texture.path, icon="CHECKMARK")
                    else:
                        row = layout.row()
                        row.label(text="Not exported", icon="ERROR")

                try:
                    texture_row = texture.rows[texture.rows_selected_index]
                except:
                    texture_row = None

                if texture_row:
                    row = layout.row()
                    row.prop(texture_row, "name", text="Name")
                    row.enabled = False

                    channels = [
                        (texture_row.R, "R"),
                        (texture_row.G, "G"),
                        (texture_row.B, "B"),
                        (texture_row.A, "A"),
                        ]

                    for texture_row, texture_row_name in channels:
                        if texture_row.channel_mode == "NONE":
                            row = layout.row()
                            row.prop(texture_row, "channel_mode", text=texture_row_name)
                        else:
                            panel_header, panel_body = layout.panel(texture_row_name)
                            if panel_header:
                                panel_header.prop(texture_row, "channel_mode", text=texture_row_name)
                                panel_header.enabled = False
                            if panel_body:
                                panel_body.enabled = False
                                if texture_row.channel_mode == "INDEX":
                                    row = panel_body.row()
                                    row.prop(texture_row, "index", text="Bone Index")
                                else: # WEIGHT
                                    row = panel_body.row()
                                    row.prop(texture_row, "index", text="Bone Index")

# ANIMATION TEXTURES #
class BATBAKER_UL_ReportAnimationTextureList(bpy.types.UIList):
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

class BATBAKER_PT_ReportAnimationTexPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportanimationtexpanel"
    bl_parent_id = "BATBAKER_PT_reporttexpanel"
    bl_label = "Animation Data"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

        row = layout.row()
        col = row.split()
        col.label(text="Width: " + str(report.animation_tex_width))
        col.label(text="Height: " + str(report.animation_tex_height))

        row = layout.row()
        row.prop(report, "animation_tex_sampling_mode")
        row.enabled = False

        row = layout.row()
        if report.animation_tex_sampling_mode == 'CONTINUOUS':
            row.label(text="Width: " + str(report.animation_tex_frame_width))
            row.enabled = report.animation_tex_underflow or report.animation_tex_overflow
        else:
            row.label(text="Height: " + str(report.animation_tex_frame_height))
            row.enabled = report.animation_tex_overflow

        row = layout.row()
        row.template_list("BATBAKER_UL_ReportAnimationTextureList", "", report, "animation_textures", report, "animation_textures_selected_index", rows=5)

        if report.animation_textures:
            try:
                texture = report.animation_textures[report.animation_textures_selected_index]
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
                        row.enabled = texture_channel.remapping and get_animation_texture_channel_allow_remap(texture_channel)
                        row = layout.row()
                        row.label(text="Range: %.5f" % texture_channel_range, icon=icon)
                        row.enabled = texture_channel.remapping and get_animation_texture_channel_allow_remap(texture_channel)

# MESH #
class BATBAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportmeshpanel"
    bl_parent_id = "BATBAKER_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.BATBakerReport
        row = self.layout.row(align=True)
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

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

            row = layout.row()
            row.label(text="Bones: " + str(report.num_bones))

            row = layout.row()
            row.label(text="Max Weights: " + str(report.num_bones_max))

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

# XML #
class BATBAKER_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportxmlpanel"
    bl_parent_id = "BATBAKER_PT_reportpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.BATBakerReport
        row = self.layout.row(align=True)
        if report.xml:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

        row = layout.row()
        if report.xml:
            row.label(text="File: " + report.xml_path, icon="FILE")
        else:
            row.label(text="Not exported", icon="X")

# ANIMS #
class BATBAKER_PT_ReportAnimsPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportanimspanel"
    bl_parent_id = "BATBAKER_PT_reportpanel"
    bl_label = "Anims"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10

    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.BATBakerReport.success

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

        layout.template_list("BATBAKER_UL_ReportAnimsList", "", report, "anims", report, "selected_anim", rows=3)
        if report.anims:
            anim = report.anims[report.selected_anim]
            if anim:
                row = layout.row()
                row.label(text="Length: " + str(anim.end_frame - (anim.start_frame - 1)))

                row = layout.row()
                row.label(text="Start: " + str(anim.start_frame))
                row = layout.row()
                row.label(text="End: " + str(anim.end_frame))

class BATBAKER_UL_ReportAnimsList(bpy.types.UIList):
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
class BATBAKER_PT_ReportFramesPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportframespanel"
    bl_parent_id = "BATBAKER_PT_reportpanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 12

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

        row = layout.row()
        row.prop(report, "animation_tex_sampling_mode")
        row.enabled = False
        
        if report.animation_tex_sampling_mode == "STACK":
            row = layout.row()
            row.prop(report, "animation_tex_packing_stack_mode")
            row.enabled = False

        layout.separator()

        icon = "CHECKMARK" if report.padded else "ERROR" if (report.padding > 0 and not report.padded) else "X"
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
class BATBAKER_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "BATBAKER_PT_reportunitpanel"
    bl_parent_id = "BATBAKER_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.BATBakerReport

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