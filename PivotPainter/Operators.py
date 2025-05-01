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

############
### MAIN ###
class PIVOTPAINTER_OT_CreateSelectOrder(bpy.types.Operator):
	bl_label = "Start selection order"
	bl_idname = "gametools.pivotpainter_create_select_order"
	bl_category = "Game Tools"
	bl_description = "Press button, then start selecting objects with preferred order.\nPress again to store order number in 'SelectionOrder' custom property.\n\nYou can select more than 1 object each time.\nPress ESC to cancel. "

	@classmethod
	def poll(self, context):
		return bpy.context.mode == 'OBJECT'

	orderarray = []											# Array with selected objects in order of selection
	prevlen = 0
	def update(self, context):								# Create the orderarray
		curlen = len(context.selected_objects)
		if curlen > self.prevlen:							# Selected more objects
			for obj in context.selected_objects:
				if obj not in self.orderarray:				# if obj are missing add to orderarray
					self.orderarray.append(obj)
		elif curlen < self.prevlen:							# Deselect objects
			for i, obj in enumerate(self.orderarray):
				if obj not in context.selected_objects:		# if obj are deselected  remove from  orderarray
					del self.orderarray[i]
		self.prevlen = len(self.orderarray)					# Store len to avoid calculation every update

	def execute(self, context):								# Used for panel draw. When button is pressed will hide operator from panel and in place will show selectingobjects bool
		PivotPainterSettings = bpy.context.scene.PivotPainterSettings 
		PivotPainterSettings.selectingobjects = True

	def modal(self, context, event):
		PivotPainterSettings = bpy.context.scene.PivotPainterSettings 
		if PivotPainterSettings.selectingobjects == False:					# Used to store order to objects when flip the boolean
			counter = PivotPainterSettings.orderstart
			for obj in self.orderarray:
				obj["SelectionOrder"] = counter				# (order starts from 1 UE shader)
				if PivotPainterSettings.dontcount==False:
					counter = counter +1
			return {'FINISHED'}			
		elif event.type == 'ESC':							# Cancel operation
			PivotPainterSettings.selectingobjects = False
			context.area.tag_redraw()						# panel is lazy
			return {'CANCELLED'}
		self.update(context)
		return {'PASS_THROUGH'}

	def invoke(self, context, event):
		self.update(context)
		self.execute(context)
		context.window_manager.modal_handler_add(self)
		return {'RUNNING_MODAL'}

class PIVOTPAINTER_OT_CreateTextures(bpy.types.Operator):
	bl_label = "Bake"
	bl_idname = "gametools.pivotpainter_create_textures"
	bl_category = "Game Tools"
	bl_description = "Save before use is advised.\n\nProgress report in system console."

	@classmethod
	def poll(cls, context):
			return context.mode == 'OBJECT' # len(context.selected_objects) > 1  and  # and context.active_object.type == 'MESH'		# Check that you are ready to rumble.

	def execute(self, context):
		PivotPainterSettings = context.scene.PivotPainterSettings
		units = context.scene.unit_settings
		grandparentscount = 0
		objwithoutorder = []
		t1 = time.time()

		for obj in bpy.context.selected_objects:
			if obj.parent == None :								# Check that there is at least one object with parent 
				grandparentscount= grandparentscount +1			# Only 1 object should have no parent (the base)
				break

		if PivotPainterSettings.savetextures == True:														#Check that save is possible
			pathok = os.path.exists(bpy.path.abspath(PivotPainterSettings.folderpath))
			if pathok == False:
				self.report({'ERROR'}, 'Incorrect Save location ' +str(PivotPainterSettings.folderpath))
				return {'CANCELLED'}	

		warned = False
		hdrmismatch = 0
		testSelectionOrder = False
		testBoundBoxCenter = False
		rgb = (PivotPainterSettings.rgb, PivotPainterSettings.rgb2, PivotPainterSettings.rgb3, PivotPainterSettings.rgb4)
		alpha = (PivotPainterSettings.alpha, PivotPainterSettings.alpha2, PivotPainterSettings.alpha3, PivotPainterSettings.alpha4)
		for i in range(PivotPainterSettings.totaltextures):
			if rgb[i] != 'None' or alpha[i] != 'None' :
				_, _, texturergb, texturealpha, hdr, hdra = texturefunction(context, False, False, i)						# Find if rgb and alpha use Hdr and what the alpha channel is set to store
				if not ( rgb[i] == 'None' or alpha[i] == 'None' ) :														# In case the rbg or alpha is selected none hdr will stay false and the next test might fail
					if hdr != hdra : hdrmismatch = i +1 																# If HDR for rgb and alpha selection dont match save the texture number
				if texturealpha == "SelectionOrder": testSelectionOrder = True											# If alpha is set to selection order will need to check objects
				if (texturergb == "XAXIS" or texturealpha == "Xextent" or texturealpha == "Xwidth" ) and ( ( PivotPainterSettings.firstlevel == True ) or ( PivotPainterSettings.secondlevel == True ) or ( PivotPainterSettings.thirdlevel == True ) or ( PivotPainterSettings.fourthlevel == True ) ):
					testBoundBoxCenter = True																			# check if boundbox need testing

		if testSelectionOrder == True:
			for obj in bpy.context.selected_objects:															# Check that all objects have 'SelectionOrder' property. If not create a list for the user and cancel.
				try: obj["SelectionOrder"]
				except Exception:
					objwithoutorder.append(obj.name)
			if len(objwithoutorder) > 0:
				if len(objwithoutorder) < 4:	
					self.report({'ERROR'}, "Object " + str(objwithoutorder)+ " missing 'SelectionOrder' property")
				else:
					self.report({'INFO'}, " Objects missing 'SelectionOrder' property : " +  str(objwithoutorder))
					self.report({'ERROR'}, str(len(objwithoutorder)) + " Objects missing 'SelectionOrder' property\nList of the objects in the console. ")
				return {'CANCELLED'}

		if testBoundBoxCenter == True:
			for obj in bpy.context.selected_objects:
				vec1= mathutils.Vector ((obj.bound_box[0][0], obj.bound_box[0][1], obj.bound_box[0][2] ))				# Vector from the origin point to the min vertex position of the boundbox
				vec2= mathutils.Vector ((obj.bound_box[6][0], obj.bound_box[6][1], obj.bound_box[6][2] ))				# Max vertex is 6
				diagonalvector = vec1 -vec2																				# Vectors point to the opposite direction (if origin is in boundbox center)
				diagonallength = diagonalvector.length																	# The diagonal of bound box to get a base for comparison
				originvector = (vec1 + vec2) /2																			# Vector from origin to bound box center. if origin in the bound box center will give 0 vector
				originlength = originvector.length																		# size of vector from origin point to the 
				if originlength < diagonallength * 0.1:																	# The origin needs to be off-center. This is still too close, but should catch problems without bring headaches from couple bad objects.
#  %i of %i" % (idx, len(bpy.context.selected_objects)
					self.report({'WARNING'},"Found at least 1 object(%s) with origin point near the center of BoundBox. You can ignore this warning if the object/s is not set up to use Boundbox method. To calculate X axis from BoundBox, origin point needs to be off-center and rotation zero. To disable it, deselect all the boxes under 'Calculate X Axis from BoundBox' in the Extra Options" %(str(obj.name)))
					warned = True
					break
				if obj.rotation_euler[0]!=0 or obj.rotation_euler[1]!=0 or obj.rotation_euler[2]!=0 :
					self.report({'WARNING'}, "Found at least 1 object (" + str(obj.name) + ")  with non zero rotation ("+str(int(round(math.degrees(obj.rotation_euler[0])))) +", "+str(int(round(math.degrees(obj.rotation_euler[1]))))+", " +str(int(round(math.degrees(obj.rotation_euler[2])))) +"). To calculate X axis from BoundBox, origin point needs to be off-center and rotation zero. To disable it, uncheck all the boxes under 'Calculate X Axis from BoundBox' in the Extra Options")
					warned = True
					break
		
		if units.system != 'METRIC' or round(units.scale_length, 2) != 0.01:									# Numerous checks that everything is fine
			self.report({'ERROR'}, "Scene units must be Metric with a Unit Scale of 0.01!")
			return {'CANCELLED'}
		elif len(context.selected_objects) < 2:
			self.report({'ERROR'}, "Need more Objects!") 
			return {'CANCELLED'}
		elif len(context.selected_objects) == 1:
			self.report({'ERROR'}, "There is only 1 selected object")
			return {'CANCELLED'}
		elif grandparentscount == 0:
			self.report({'ERROR'}, "Objects have no base object!") 
			return {'CANCELLED'}
		elif PivotPainterSettings.savetextures == True and PivotPainterSettings.folderpath == '' :
			self.report({'ERROR'}, "No specified folder path") 
			return {'CANCELLED'}
		elif hdrmismatch > 0:
			self.report({'ERROR'}, "Texture " + str(hdrmismatch)+ " has mixed HDR and LDR texture selection") 
			return {'CANCELLED'}
		else:
			print('===================')
			print('Pivot Painter start')
			tt = time.time()
			PivotPainterSettings = context.scene.PivotPainterSettings 

			if PivotPainterSettings.totaltextures>=1 :	
				size = get_best_texture_dimensions()
				generate_mesh_uvs(size,PivotPainterSettings)
				if (PivotPainterSettings.rgb != 'None' or PivotPainterSettings.alpha != 'None' ) :
					createtexture(size, 0) # Start the texture creation for each one set
				if PivotPainterSettings.totaltextures>=2 and (PivotPainterSettings.rgb2 != 'None' or PivotPainterSettings.alpha2 != 'None') :
					createtexture(size, 1)
				if PivotPainterSettings.totaltextures>=3 and (PivotPainterSettings.rgb3 != 'None' or PivotPainterSettings.alpha3 != 'None') :
					createtexture(size, 2)
				if PivotPainterSettings.totaltextures==4 and (PivotPainterSettings.rgb4 != 'None' or PivotPainterSettings.alpha4 != 'None') :
					createtexture(size, 3)

			print('Blender GUI may take a moment to respond')
			if warned == False:
				self.report({'INFO'}, "Pivot Painter Done, total time: "+ str(time.time() - t1))
			else:
				self.report({'INFO'}, "Pivot Painter done with WARNING, total time: "+ str(time.time() - t1) + ". See info area or system console for more info")
			return {'FINISHED'}
		
##############
### PRESET ###
class PIVOTPAINTER_OT_Pivot_AddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'databaker_pivotpainterpanel.addpreset'
    bl_label = 'Add preset'
    preset_menu = 'PIVOTPAINTER_MT_Pivot_Presets'

    # preset_defines = [ 'settings = bpy.context.scene.PivotPainterSettings' ]
    # preset_values = [
    #     'settings.bake_mode',
    # ] @TODO presets

    preset_subdir = 'operator/databaker_pivotpainter'
