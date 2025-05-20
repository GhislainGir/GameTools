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

from bpy.props import StringProperty
from bl_operators.presets import AddPresetBase

from . import Functions
from .Functions import bake

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################

############
### MAIN ###
class BATBAKER_OT_Bake(bpy.types.Operator):
    """ Bakes skeletal animations of the active mesh into textures, storing positional & normal data per bone. """
    bl_idname = "gametools.batbaker_bake"
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

##############
### PRESET ###
class BATBAKER_OT_BoneAnimation_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.batbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'BATBAKER_MT_BoneAnimation_Presets'

    preset_defines = [ 'settings = bpy.context.scene.BATBakerSettings' ]

    preset_values = [
    ]

    preset_subdir = 'operator/gametools_batbaker'
