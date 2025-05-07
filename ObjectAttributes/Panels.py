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

####################################################################################
###################################### PANELS ######################################
####################################################################################

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
        row.operator("gametools.databaker_bakeoa")
        row.enabled = len(settings.textures) > 0

        row = layout.row()
        row.template_list("OBJECTATTRIBUTES_UL_TextureList", "", settings, "textures", settings, "textures_selected_index", rows=5)

        col = row.column(align=True)
        col.operator("objectattributes_item.new_item", text="", icon="ADD")
        col.operator("objectattributes_item.delete_item", text="", icon="REMOVE")

        col.separator()

        col.operator("objectattributes_item.move_item", text="", icon="TRIA_UP").direction = "UP"
        col.operator("objectattributes_item.move_item", text="", icon="TRIA_DOWN").direction = "DOWN"

class OBJECTATTRIBUTES_PT_ChannelsPanel(bpy.types.Panel):
    bl_idname = "OBJECTATTRIBUTES_PT_channelspanel"
    bl_parent_id = "OBJECTATTRIBUTES_PT_mainpanel"
    bl_label = "Channels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0
    
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ObjectAttributesSettings

        if settings.textures:
            texture = settings.textures[settings.textures_selected_index]

            if texture:
                textures = [
                    (texture.R, "R"),
                    (texture.G, "G"),
                    (texture.B, "B"),
                    (texture.A, "A"),
                    ]

                for tex_data, tex_name in textures:
                    if tex_data.channel_mode == "NONE":
                        row = layout.row()
                        row.prop(tex_data, "channel_mode", text=tex_name)
                    else:
                        panel_header, panel_body = layout.panel(tex_name)
                        if panel_header:
                            panel_header.prop(tex_data, "channel_mode", text=tex_name)
                        if panel_body:
                            if tex_data.channel_mode == "POSITION":
                                row = panel_body.row()
                                row.prop(tex_data, "component")

                                row = panel_body.row()
                                row.prop(tex_data, "obj_mode")

                                if tex_data.obj_mode == "SELF":
                                    pass
                                elif tex_data.obj_mode == "PARENT":
                                    row = panel_body.row()
                                    row.prop(tex_data, "depth")
                                else:
                                    row = panel_body.row()
                                    row.prop(tex_data, "obj")
                            elif tex_data.channel_mode == "AXIS":
                                row = panel_body.row()
                                row.prop(tex_data, "component")

                                row = panel_body.row()
                                row.prop(tex_data, "axis")
                                row = panel_body.row()
                                row.prop(tex_data, "axis_mode", text="Mode")

                                row = panel_body.row()
                                row.prop(tex_data, "obj_mode")

                                if tex_data.obj_mode == "SELF":
                                    pass
                                elif tex_data.obj_mode == "PARENT":
                                    row = panel_body.row()
                                    row.prop(tex_data, "depth")
                                else:
                                    row = panel_body.row()
                                    row.prop(tex_data, "obj")
                            elif tex_data.channel_mode == "EXTENTS":
                                row = panel_body.row()
                                row.prop(tex_data, "component")

                                row = panel_body.row()
                                row.prop(tex_data, "axis")
                                row = panel_body.row()
                                row.prop(tex_data, "axis_mode", text="Mode")

                                row = panel_body.row()
                                row.prop(tex_data, "obj_mode")

                                if tex_data.obj_mode == "SELF":
                                    pass
                                elif tex_data.obj_mode == "PARENT":
                                    row = panel_body.row()
                                    row.prop(tex_data, "depth")
                                else:
                                    row = panel_body.row()
                                    row.prop(tex_data, "obj")
                            elif tex_data.channel_mode == "HIERARCHY":
                                row = panel_body.row()
                                row.prop(tex_data, "depth")
                            else:
                                pass

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
        row.prop(settings, "use_pivot_painter_packing")

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
        row.prop(settings, "mesh_name")

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

###############
### PRESETS ###
class OBJECTATTRIBUTES_MT_ObjectAttributes_Presets(bpy.types.Menu):
    bl_label = 'Object Attributes Presets'
    preset_subdir = 'operator/databaker_OA'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class OBJECTATTRIBUTES_PT_ObjectAttributes_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'Object Attributes Presets'
    preset_subdir = 'operator/databaker_OA'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'databaker_ObjectAttributespanel.addpreset'
