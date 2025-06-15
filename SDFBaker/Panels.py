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

###############
### PRESETS ###
class SDFBAKER_MT_MainPanel_Presets(bpy.types.Menu):
    bl_label = 'SDF Baker Presets'
    preset_subdir = 'operator/gametools_sdfbaker'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset

class SDFBAKER_PT_SDF_Preset(PresetPanel, bpy.types.Panel):
    bl_label = 'SDF Baker Presets'
    preset_subdir = 'operator/gametools_sdfbaker'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'gametools.sdfbaker_addpreset'

############
### MAIN ###
class SDFBAKER_PT_SDFBAKER(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "SDF Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

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
        SDFBAKER_PT_SDF_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        row = layout.row()
        row.scale_y = 2.0 # bigger button
        row.operator("gametools.sdfbaker_bakesdf")

class SDFBAKER_PT_VoxelsPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_voxelspanel"
    bl_parent_id = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "Voxels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings
        
        row = layout.row()
        row.prop(settings, "sdf_mode")

        if settings.sdf_mode == "BOUNDS":
            row = layout.row()
            row.prop(settings, "offset")
        else: # CUSTOM
            row = layout.row()
            row.prop(settings, "sdf_bounds")

        row = layout.row()
        row.prop(settings, "x")
        row.prop(settings, "y")

        row = layout.row()
        row.prop(settings, "z")

############
### MESH ###
class SDFBAKER_PT_MeshPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_meshpanel"
    bl_parent_id = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings
        
        row = layout.row()
        row.prop(settings, "unit_scale")

        row = layout.row()
        row.label(text="Invert")
        row.prop(settings, "unit_invert_x", text="X")
        row.prop(settings, "unit_invert_y", text="Y")
        row.prop(settings, "unit_invert_z", text="Z")

        row = layout.row()
        row.prop(settings, "mesh_name")

        layout.separator()

        row = layout.row()
        row.prop(settings, "gen_selection_mesh", text="Merged")
        row.prop(settings, "gen_debug_mesh", text="Debug")

class SDFBAKER_PT_MeshExportPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_meshexportpanel"
    bl_parent_id = "SDFBAKER_PT_meshpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        layout.prop(settings, "export_mesh", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings
    
        layout.enabled = bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_mesh_file_name")

        row = layout.row()
        row.prop(settings, "export_mesh_file_path")

class SDFBAKER_PT_MeshAdvExportPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_meshadvexportpanel"
    bl_parent_id = "SDFBAKER_PT_meshexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        layout.enabled = bpy.data.is_saved
    
        row = layout.row()
        row.prop(settings, "export_mesh_file_override")

################
### TEXTURES ###
class SDFBAKER_PT_TexPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_texpanel"
    bl_parent_id = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "Texture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings
        
        row = layout.row()
        row.prop(settings, "distance_mode")

        row = layout.row()
        row.prop(settings, "tex_file_name")

        row = layout.row()
        row.prop(settings, "tile_sort_mode")
        
        row = layout.row()
        row.prop(settings, "frames")

        row = layout.row()
        col = row.split()
        col.prop(settings, "unit_invert_v")
        col = row.split()
        col.prop(settings, "invert_sign")
        col = row.split()
        col.prop(settings, "two_sided")

class SDFBAKER_PT_TexExportPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_texexportpanel"
    bl_parent_id = "SDFBAKER_PT_texpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        layout.prop(settings, "export_tex", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings
    
        layout.enabled = bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_tex_file_path")

class SDFBAKER_PT_TexAdvExportPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_texadvexportpanel"
    bl_parent_id = "SDFBAKER_PT_texexportpanel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        layout.enabled = bpy.data.is_saved
    
        row = layout.row()
        row.prop(settings, "export_tex_override")

###########
### XML ###
class SDFBAKER_PT_XMLPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_xmlpanel"
    bl_parent_id = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

class SDFBAKER_PT_XMLExportPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_xmlexportpanel"
    bl_parent_id = "SDFBAKER_PT_xmlpanel"
    bl_label = "Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        layout.prop(settings, "export_xml", text="")
        layout.enabled = bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        layout.enabled = bpy.data.is_saved

        row = layout.row()
        row.prop(settings, "export_xml_mode")
        row.enabled = settings.export_tex

        if (settings.export_xml_mode == "CUSTOMPATH" or not settings.export_tex):
            row = layout.row()
            row.prop(settings, "export_xml_file_name")

            row = layout.row()
            row.prop(settings, "export_xml_file_path")

        row = layout.row()
        row.prop(settings, "export_xml_override")

##############
### REPORT ###
class SDFBAKER_PT_ReportPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_reportpanel"
    bl_parent_id = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "Report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 500
    
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.SDFBakerReport.baked
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.SDFBakerReport

        if report.baked:
            row = layout.row()
            row.scale_y = 2.0
            col = row.split()
            col.operator("gametools.sdfbaker_export_report")
            col = row.split()
            col.operator("gametools.sdfbaker_clear_report")

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

class SDFBAKER_PT_ReportTexPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_reporttexpanel"
    bl_parent_id = "SDFBAKER_PT_reportpanel"
    bl_label = "Texture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.SDFBakerReport.success
    
    def draw_header(self, context):
        report = context.scene.SDFBakerReport
        row = self.layout.row(align=True)
        if report.tex:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.SDFBakerReport

        row = layout.row()
        col = row.split()
        col.label(text="Width: " + str(report.tex_width))
        col.label(text="Height: " + str(report.tex_height))

        row = layout.row()
        row.label(text="Slices Per Row: " + str(report.tex_slices))

        layout.separator()

        row = layout.row()
        row.label(text="Voxels")
        row = layout.row()
        row.label(text="X " + str(report.x))
        row.label(text="Y " + str(report.y))
        row.label(text="Z " + str(report.z))

        layout.separator()

        if report.tex:
            row = layout.row()
            row.prop(report, "tex", text="")
            row.enabled = False

            row = layout.row()
            if report.tex_export:
                row.label(text="File: " + report.tex_path, icon="FILE")
            else:
                row.label(text="Not exported", icon="X")

            layout.separator()

            row = layout.row()
            row.label(text="Distance: " + report.distance_mode)
            if report.distance_mode != "REAL":
                row = layout.row()
                row.label(text="Max: " + str(report.max_dist))
        else:
            row.label(text="None generated", icon="X")
    
        layout.separator()

        row = layout.row()
        col = row.split()
        col.label(text="Invert V: " + str(report.unit_invert_v))
        col.label(text="Invert Sign: " + str(report.invert_sign))

        row = layout.row()
        row.label(text="Tiles Sort: " + str(report.tile_sort_mode))

class SDFBAKER_PT_ReportMeshPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_reportmeshpanel"
    bl_parent_id = "SDFBAKER_PT_reportpanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.SDFBakerReport
        row = self.layout.row(align=True)
        if report.mesh:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.SDFBakerReport

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

class SDFBAKER_PT_ReportXMLPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_reportxmlpanel"
    bl_parent_id = "SDFBAKER_PT_reportpanel"
    bl_label = "XML"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        report = context.scene.SDFBakerReport
        row = self.layout.row(align=True)
        if report.xml:
            row.label(text="", icon="CHECKMARK")
        else:
            row.label(text="", icon="X")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.SDFBakerReport

        row = layout.row()
        if report.xml:
            row.label(text="File: " + report.xml_path, icon="FILE")
        else:
            row.label(text="Not exported", icon="X")

class SDFBAKER_PT_ReportUnitPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_reportunitpanel"
    bl_parent_id = "SDFBAKER_PT_reportpanel"
    bl_label = "Unit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 14

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        report = scene.SDFBakerReport

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

##############
### LEGACY ###
class SDFBAKER_PT_LegacyPanel(bpy.types.Panel):
    bl_idname = "SDFBAKER_PT_legacypanel"
    bl_parent_id = "SDFBAKER_PT_sdfbakerpanel"
    bl_label = "Legacy"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 10000

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.SDFBakerSettings

        row = layout.row()
        row.scale_y = 2.0
        row.operator("gametools.sdfbaker_generategeonodes")
