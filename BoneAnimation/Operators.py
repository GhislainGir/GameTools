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
import uuid

from bpy.props import StringProperty, EnumProperty
from bl_operators.presets import AddPresetBase

from . import Functions
from .Functions import bake, export_bake_report, reset_bake_report

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################

##############
### PRESET ###
class BATBAKER_OT_BoneAnimation_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.batbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'BATBAKER_MT_BoneAnimation_Presets'

    preset_defines = [ 'settings = bpy.context.scene.BATBakerSettings' ]

    preset_values = [
        'settings.skinning_textures',
        'settings.skinning_textures_selected_index',
        'settings.animation_textures',
        'settings.animation_textures_selected_index',
        'settings.unit_scale',
        'settings.unit_invert_x',
        'settings.unit_invert_y',
        'settings.unit_invert_z',
        'settings.unit_invert_v',
        'settings.mesh_name',
        'settings.mesh_uvmap_name',
        'settings.mesh_target_prop',
        'settings.mesh_materials',
        'settings.export_mesh',
        'settings.export_mesh_file_name',
        'settings.export_mesh_file_path',
        'settings.export_mesh_file_override',
        'settings.require_triangulation',
        'settings.previz_result',
        'settings.previz_bounds',
        'settings.export_xml',
        'settings.export_xml_mode',
        'settings.export_xml_file_name',
        'settings.export_xml_file_path',
        'settings.export_xml_override',
        'settings.frame_range_mode',
        'settings.frame_range_nla_exclusion',
        'settings.frame_range_nla_exclusion_selected_index',
        'settings.frame_range_nla_exclusion_selected',
        'settings.frame_range_custom_start',
        'settings.frame_range_custom_end',
        'settings.frame_range_custom_step',
        'settings.frame_range_custom_step_mode',
        'settings.frame_ref_padding',
        'settings.frame_padding_mode',
        'settings.frame_padding',
        'settings.frame_ref_mode',
        'settings.frame_ref_custom',
        'settings.export_tex',
        'settings.export_tex_file_name',
        'settings.export_tex_file_path',
        'settings.export_tex_override',
        'settings.skinning_tex_max_width',
        'settings.skinning_tex_max_height',
        'settings.skinning_tex_res_mode',
        'settings.animation_tex_max_width',
        'settings.animation_tex_max_height',
        'settings.animation_tex_force_power_of_two',
        'settings.animation_tex_force_power_of_two_square',
        'settings.animation_tex_packing_mode',
    ]

    preset_subdir = 'operator/gametools_batbaker'

############
### MAIN ###
class BATBAKER_OT_Bake(bpy.types.Operator):
    """ Bakes skeletal animations of the active mesh into textures, storing positional & normal data per bone. """
    bl_idname = "gametools.batbaker_bakebat"
    bl_label = "Bake"
    bl_category = "Game Tools"
    bl_description = "Bake animations into bone animation textures"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BATBakerSettings

        return True

    def execute(self, context):
        success, verbose, msg = bake(context)
        if success:
            self.report({verbose}, msg)
            return {'FINISHED'}
        else:
            self.report({verbose}, msg)
            return {'CANCELLED'}

#####################
### NLA EXCLUSION ###
class BATBAKER_OT_NLAExclusion_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "gametools.batbaker_frame_range_nla_exclusion_new_item"
    bl_label = "Add a new item"
    
    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.frame_range_nla_exclusion_selected != "" and context.scene.BATBakerSettings.frame_range_nla_exclusion_selected not in [nla.name for nla in context.scene.BATBakerSettings.frame_range_nla_exclusion]
    
    def execute(self, context):
        context.scene.BATBakerSettings.frame_range_nla_exclusion.add()
        last_index = len(context.scene.BATBakerSettings.frame_range_nla_exclusion) - 1
        if last_index >= 0:
            context.scene.BATBakerSettings.frame_range_nla_exclusion_selected_index = last_index
            context.scene.BATBakerSettings.frame_range_nla_exclusion[last_index].name = context.scene.BATBakerSettings.frame_range_nla_exclusion_selected

        return{'FINISHED'}

class BATBAKER_OT_NLAExclusion_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "gametools.batbaker_frame_range_nla_exclusion_delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.frame_range_nla_exclusion

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        settings.frame_range_nla_exclusion.remove(settings.frame_range_nla_exclusion_selected_index)
        settings.frame_range_nla_exclusion_selected_index = min(max(0, settings.frame_range_nla_exclusion_selected_index), len(settings.frame_range_nla_exclusion) - 1)
        return{'FINISHED'}

class BATBAKER_OT_NLAExclusion_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "gametools.batbaker_frame_range_nla_exclusion_move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.frame_range_nla_exclusion
    
    def execute(self, context):
        settings = context.scene.BATBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.frame_range_nla_exclusion.move(settings.frame_range_nla_exclusion_selected_index + index_offset, settings.frame_range_nla_exclusion_selected_index)
        settings.frame_range_nla_exclusion_selected_index = max(0, min(settings.frame_range_nla_exclusion_selected_index + index_offset, len(settings.frame_range_nla_exclusion) - 1))

        return{'FINISHED'}

############################
### INDEX/WEIGHT TEXTURE ###
class BATBAKER_OT_SkinningTextureList_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "gametools.batbaker_skinning_texturelist_new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        last_item = None
        current_index = settings.skinning_textures_selected_index
        if settings.skinning_textures and (current_index < len(settings.skinning_textures)):
            last_item = settings.skinning_textures[current_index]

        settings.skinning_textures.add()
        last_index = len(settings.skinning_textures) - 1
        if last_index >= 0:
            settings.skinning_textures_selected_index = last_index

            item = settings.skinning_textures[last_index]
            item.ID = uuid.uuid4().hex

            name = "Skinning"
            name_suffix = 0
            names = [skinning_texture.name for skinning_texture in settings.skinning_textures if skinning_texture != item]
            while name in names:
                name_suffix += 1
                name_suffix_str = str(name_suffix).zfill(3)
                name = "Skinning." + name_suffix_str
            item.name = name

            if last_item:
                pass

            texture_row = item.rows.add()
            texture_row.name = "Indices"
            texture_row.R.channel_mode = "INDEX"
            texture_row.R.index = 1
            texture_row.G.channel_mode = "INDEX"
            texture_row.G.index = 2
            texture_row.B.channel_mode = "INDEX"
            texture_row.B.index = 3
            texture_row.A.channel_mode = "INDEX"
            texture_row.A.index = 4

            texture_row = item.rows.add()
            texture_row.name = "Weights"
            texture_row.R.channel_mode = "WEIGHT"
            texture_row.R.index = 1
            texture_row.G.channel_mode = "WEIGHT"
            texture_row.G.index = 2
            texture_row.B.channel_mode = "WEIGHT"
            texture_row.B.index = 3
            texture_row.A.channel_mode = "WEIGHT"
            texture_row.A.index = 4

        return{'FINISHED'}

class BATBAKER_OT_SkinningTextureList_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "gametools.batbaker_skinning_texturelist_delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.skinning_textures

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        if settings.skinning_textures and (settings.skinning_textures_selected_index < len(settings.skinning_textures)):
            settings.skinning_textures.remove(settings.skinning_textures_selected_index)
            settings.skinning_textures_selected_index = min(max(0, settings.skinning_textures_selected_index), len(settings.skinning_textures) - 1)        

        return{'FINISHED'}

class BATBAKER_OT_SkinningTextureList_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "gametools.batbaker_skinning_texturelist_move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.skinning_textures

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.skinning_textures.move(settings.skinning_textures_selected_index + index_offset, settings.skinning_textures_selected_index)
        settings.skinning_textures_selected_index = max(0, min(settings.skinning_textures_selected_index + index_offset, len(settings.skinning_textures) - 1))

        return{'FINISHED'}

########################
### INDEX/WEIGHT ROW ###
class BATBAKER_OT_SkinningRowList_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "gametools.batbaker_skinning_rowlist_new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        settings = context.scene.BATBakerSettings
        try:
            skinning_texture = settings.skinning_textures[settings.skinning_textures_selected_index]
        except:
            skinning_texture = None

        if skinning_texture:
            if skinning_texture.storage_mode == "VCOL":
                return len(skinning_texture.rows) <= 0
            else:
                return True
        else:
            return True

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        try:
            texture = settings.skinning_textures[settings.skinning_textures_selected_index]

            last_item = None
            current_index = texture.rows_selected_index
            if texture.rows and (current_index < len(texture.rows)):
                last_item = texture.rows[current_index]

            texture.rows.add()
            last_index = len(texture.rows) - 1
            if last_index >= 0:
                texture.rows_selected_index = last_index

                item = texture.rows[last_index]
                item.ID = uuid.uuid4().hex

                name = "Row"
                name_suffix = 0
                names = [skinning_texture_row.name for skinning_texture_row in texture.rows if skinning_texture_row != item]
                while name in names:
                    name_suffix += 1
                    name_suffix_str = str(name_suffix).zfill(3)
                    name = "Row." + name_suffix_str
                item.name = name

                if last_item:
                    pass

            return{'FINISHED'}
        except:
            return {'CANCELLED'}

class BATBAKER_OT_SkinningRowList_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "gametools.batbaker_skinning_rowlist_delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        settings = context.scene.BATBakerSettings
        try:
            texture = settings.skinning_textures[settings.skinning_textures_selected_index]
            return texture.rows
        except:
            return False

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        try:
            texture = settings.skinning_textures[settings.skinning_textures_selected_index]

            if texture.rows and (texture.rows_selected_index < len(texture.rows)):
                texture.rows.remove(texture.rows_selected_index)
                texture.rows_selected_index = min(max(0, texture.rows_selected_index), len(texture.rows) - 1)        

            return{'FINISHED'}
        except:
            return {'CANCELLED'}

class BATBAKER_OT_SkinningRowList_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "gametools.batbaker_skinning_rowlist_move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        settings = context.scene.BATBakerSettings
        try:
            texture = settings.skinning_textures[settings.skinning_textures_selected_index]
            return texture.rows
        except:
            return False

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        try:
            texture = settings.skinning_textures[settings.skinning_textures_selected_index]

            index_offset = -1 if self.direction == 'UP' else 1
            texture.rows.move(texture.rows_selected_index + index_offset, texture.rows_selected_index)
            texture.rows_selected_index = max(0, min(texture.rows_selected_index + index_offset, len(texture.rows) - 1))
            return {'FINISHED'}
        except:
            return {'CANCELLED'}
        
#########################
### TRANSFORM TEXTURE ###
class BATBAKER_OT_AnimationTextureList_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "gametools.batbaker_animation_texturelist_new_item"
    bl_label = "Add a new item"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        last_item = None
        current_index = settings.animation_textures_selected_index
        if settings.animation_textures and (current_index < len(settings.animation_textures)):
            last_item = settings.animation_textures[current_index]

        settings.animation_textures.add()
        last_index = len(settings.animation_textures) - 1
        if last_index >= 0:
            settings.animation_textures_selected_index = last_index

            item = settings.animation_textures[last_index]
            item.ID = uuid.uuid4().hex

            name = "Texture"
            name_suffix = 0
            names = [animation_texture.name for animation_texture in settings.animation_textures if animation_texture != item]
            while name in names:
                name_suffix += 1
                name_suffix_str = str(name_suffix).zfill(3)
                name = "Texture." + name_suffix_str
            item.name = name

            if last_item:
                pass

        return {'FINISHED'}

class BATBAKER_OT_AnimationTextureList_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "gametools.batbaker_animation_texturelist_delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.animation_textures

    def execute(self, context):
        if context.scene.BATBakerSettings.animation_textures and (context.scene.BATBakerSettings.animation_textures_selected_index < len(context.scene.BATBakerSettings.animation_textures)):
            context.scene.BATBakerSettings.animation_textures.remove(context.scene.BATBakerSettings.animation_textures_selected_index)
            context.scene.BATBakerSettings.animation_textures_selected_index = min(max(0, context.scene.BATBakerSettings.animation_textures_selected_index), len(context.scene.BATBakerSettings.animation_textures) - 1)        

        return{'FINISHED'}

class BATBAKER_OT_AnimationTextureList_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "gametools.batbaker_animation_texturelist_move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(
        ('UP', 'Up', ""),
        ('DOWN', 'Down', ""),
        ))

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerSettings.animation_textures

    def execute(self, context):
        settings = context.scene.BATBakerSettings
        index_offset = -1 if self.direction == 'UP' else 1
        settings.animation_textures.move(settings.animation_textures_selected_index + index_offset, settings.animation_textures_selected_index)
        settings.animation_textures_selected_index = max(0, min(settings.animation_textures_selected_index + index_offset, len(settings.animation_textures) - 1))

        return{'FINISHED'}

##############
### REPORT ###
class BATBAKER_OT_ExportReport(bpy.types.Operator):
    """ """
    bl_idname = "gametools.batbaker_export_report"
    bl_label = "Export"
    bl_category = "Game Tools"
    bl_description = "Export last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerReport.baked

    def execute(self, context):
        success, msg, path = export_bake_report(context)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class BATBAKER_OT_ClearReport(bpy.types.Operator):
    """ """
    bl_idname = "gametools.batbaker_clear_report"
    bl_label = "Clear"
    bl_category = "Game Tools"
    bl_description = "Clear last report"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.scene.BATBakerReport.baked

    def execute(self, context):
        reset_bake_report()
        return {'FINISHED'}