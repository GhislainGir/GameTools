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

from . import Functions
from .Functions import *

from bl_operators.presets import AddPresetBase

#######################################################################################
###################################### OPERATORS ######################################
#######################################################################################
class OBJECTANIMBAKER_OT_Bake(bpy.types.Operator):
	'''  '''
	bl_label = "Bake"
	bl_idname = "gametools.objectanimbaker_bake"
	bl_category = "Game Tools"
	bl_description = "Bake the selected *mesh* objects animation into a texture using the specified settings"

	@classmethod
	def poll(cls, context):
		settings = context.scene.OATBakerSettings
		return settings.FirstTexture or settings.SecondTexture or settings.ThirdTexture

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
class OATBAKER_OT_ObjectAnimation_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'gametools.oatbaker_addpreset'
    bl_label = 'Add preset'
    preset_menu = 'OATBAKER_MT_MainPanel_Presets'

    # preset_defines = [ 'settings = bpy.context.scene.OATBakerSettings' ]
    # preset_values = [
    # 'settings.distance_mode',
    # ] # @TODO presets

    preset_subdir = 'operator/gametools_oatbaker'
