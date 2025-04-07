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

import time, sys, math, ctypes, random, mathutils, bpy, os
import numpy as np
from ctypes import POINTER, pointer, c_int, cast, c_float
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import BoolProperty, PointerProperty, IntProperty, StringProperty
from math import floor, ceil, sqrt
from time import sleep
import uuid
import xml.etree.ElementTree as ET

#######################################################################################
###################################### FUNCTIONS ######################################
#######################################################################################
def setpixels(rgbfunction, alphafunction, texturealpha, tex_id, PivotPainterSettings, width, height, pixels, hdr):
	""" Calculate the pixels values """
	counter = 0
	tt = time.time()
	for obj in bpy.context.selected_objects:							# The 
		rgbvalues = rgbfunction(PivotPainterSettings, obj, counter, width, height, pixels, hdr)			# Does sending unused values affect performance(even if minimal)?  There must be a better way. (with the function selection)
		alphavalue = alphafunction(PivotPainterSettings, obj, counter, width, height, pixels, hdr)
		pixelindex=((width*height)-((floor(counter/width)+1)*width)+(counter%width))
		pixels[pixelindex*4] = rgbvalues[0]		
		pixels[pixelindex*4+1] = rgbvalues[1]
		pixels[pixelindex*4+2] = rgbvalues[2]		
		pixels[pixelindex*4+3] = alphavalue
		counter = counter + 1

	foundthem = False											# Only a couple pixels should be empty near the start.
	for i in range(len(pixels)):								# Fill Empty pixels
		if pixels[i] == None:
			pixels[i] = 1
			foundthem =True
		elif foundthem ==True:									# if have found empty pixels, but not anymore empty, stop.
			break
	if texturealpha == 'Hierarchy':	# second part of the function to create the hierarchy
		pixels = hierarchy(PivotPainterSettings, obj, counter, width, height, pixels, hdr)
	return pixels

def hierarchy(context, obj, counter, width, height, pixels, hdr):
	""" Hierarchy, current level of the object / highest possible level """
	maxlevel = 1
	for i in range(3,len(pixels),4):
		currentlevel = pixels[i]
		if currentlevel > maxlevel:
			maxlevel = currentlevel
	print ('Max level is ', maxlevel)
	for i in range(3,len(pixels),4):
		currentlevel = pixels[i]
		normalizedlevel = currentlevel / maxlevel
		pixels[i] = normalizedlevel
	return pixels

def boundboxAxis(context, obj, counter, size, pixels, hdr):
	""" Estimates the X vector from the origin point and boundbox vertices. Works only when object has zero rotation """
	settings = context.scene.PivotPainterSettings

	bbvv=[None for x in range(8)]
	bbLength=[None for x in range(8)]	
	ws=obj.matrix_world.to_scale()
	for i in range(8):
		bbvv[i] = mathutils.Vector((obj.bound_box[i][0] * ws[0], obj.bound_box[i][1] * ws[1], obj.bound_box[i][2] * ws[2] ))	# Create a vector list for each vert of the bounding box (from origin point)
		bbLength[i] = bbvv[i].length						# Create list with the lengths
		
	# Find the furthest points from origin (Hopefully they are near the main direction of the object, to use as a xaxis)
	highestVertexId = 0
	for i in range(1,8):										# find the furthest point
		if bbLength[highestVertexId] < bbLength[i]:
			highestVertexId = i
	
	fvidlist = []
	for i in range(8):																						# Check if other vertex have roughly the same distance
		if bbLength[i] >= ( bbLength[highestVertexId] * settings.percentagefreedom / 100 ): # Give a small range to include points with similar distances from the origin point, Blender inconsistencies(from floating values?) and users input
			fvidlist.append(i)

	# Get an average position
	axisdir = mathutils.Vector((0.0, 0.0, 0.0))
	for i in range(len(fvidlist)):
		axisdir = bbvv[fvidlist[i]] + axisdir
	axisdir = axisdir /len(fvidlist)
	
	vecout=axisdir.normalized()
	axisextent = axisdir.length
	return vecout, axisextent

##############
### REPORT ###
def new_bake_report(context: bpy.types.Context):
    """ """
    settings = context.scene.PivotPainterSettings

    reset_bake_report()

    add_bake_report("baked", True)
    add_bake_report("ID", uuid.uuid4().hex)
    add_bake_report("unit_system", context.scene.unit_settings.system)
    add_bake_report("unit_unit", context.scene.unit_settings.length_unit)
    add_bake_report("unit_length", context.scene.unit_settings.scale_length)
    add_bake_report("unit_scale", settings.scale)
    add_bake_report("unit_invert_x", settings.invert_x)
    add_bake_report("unit_invert_y", settings.invert_y)
    add_bake_report("unit_invert_z", settings.invert_z)
    
def reset_bake_report():
    """ """
    report = bpy.context.scene.PivotPainterReport
    report.baked = False
    report.success = False
    report.msg = ""
    report.name = ""
    report.ID = ""

    report.unit_system = ""
    report.unit_unit = ""
    report.unit_length = 0.0
    report.unit_scale = 0.0
    report.unit_invert_x = False
    report.unit_invert_y = False
    report.unit_invert_z = False

    report.mesh = None
    report.mesh_export = False
    report.mesh_path = ""
    report.mesh_uvmaps.clear()
    report.select_mesh_uvmap = 0
    report.mesh_uvmap_invert_v = False

    report.xml = False
    report.xml_path = ""

    # mesh
    report.duplicate_mesh = False
    report.make_single_user = False
    report.merge_mesh = False
    report.clean_bake = False
    report.mesh_name = ""
    report.scale = 0.0
    report.invert_x = False
    report.invert_y = False
    report.invert_z = False
    report.origin = None
    report.precision_offset = 0.0

    report.export_mesh = False
    report.export_mesh_file_name = ""
    report.export_mesh_file_path = ""
    report.export_mesh_file_override = False

def add_bake_report(prop_name: str, prop_value: float|int|str):
    """ """
    setattr(bpy.context.scene.PivotPainterReport, prop_name, prop_value)

def export_bake_report(context: bpy.types.Context):
    """ """
    return(export_xml(context))

###############
### PACKING ###
def get_bitpacked_integer(index):
	""" Store Int to float """
	index = int(index)
	index = index + 1024
	sigh=index & 0x8000
	sigh=sigh << 16
	
	exptest=index & 0x7fff
	if exptest == 0:
		exp = 0
	else:
		exp = index >> 10
		exp = exp & 0x1f
		exp = exp - 15
		exp = exp + 127
		exp = exp << 23
	
	mant = index & 0x3ff
	mant = mant << 13
	
	index = sigh|exp|mant
	
	cp = pointer(c_int(index))
	fp = cast(cp, POINTER(c_float))
	return fp.contents.value

############
### BAKE ###

##############
### MESHES ###
def generate_mesh_uvs(size, props):
	""" Create uvmap with point coordinates per object """
	tt = time.time()
	for idx, obj in enumerate(bpy.context.selected_objects):
		if props.automaticindexselect == True:
			obj.data.uv_layers.new(name = "PivotPainterMap")
			layernumber = len(obj.data.uv_layers) - 1
		else:
			layernumber = props.uvindex
			while len(obj.data.uv_layers) <= layernumber:
				obj.data.uv_layers.new(name = "PivotPainterMap") 
	
		x = idx%size[0]/size[0]+1/size[0] /2
		y = 1 - (floor(idx/size[0])/size[1]+1/size[1]/2)
		for poly in obj.data.polygons:
			for loopId in poly.loop_indices:							
				obj.data.uv_layers[layernumber].data[loopId].uv = (x, y)

################
### TEXTURES ###
def get_best_texture_dimensions ():
	""" Try to find efficient texture dimensions for the total number of object	 """
	ObjectToProcessCount = len(bpy.context.selected_objects)
	# 1600 had problems, problems. 256 is enough as it gives 64k pixel image.
	DecrementerTotal = 256
	HalfEvenNumber = ((ObjectToProcessCount/2) % 2)
	HalfNumber = ceil(ObjectToProcessCount/2)
	modResult = 1
	# highest possible x dimension
	if HalfNumber < DecrementerTotal :
		newDecrementerTotal = HalfNumber
	else:
		newDecrementerTotal = DecrementerTotal
	
	if HalfEvenNumber==0:
		decrementAmount = 2
	else:
		decrementAmount = 1
	
	complete = False
	# tries to find y dimension by checking the mod=0 
	while complete == False:
		modResult = ObjectToProcessCount % newDecrementerTotal
		if modResult==0 or newDecrementerTotal < 1:
			complete = True
		if complete == False:
			newDecrementerTotal -= decrementAmount
		if newDecrementerTotal < 1:
			newDecrementerTotal=1
	
	if newDecrementerTotal == 1 or ((ObjectToProcessCount/newDecrementerTotal)>DecrementerTotal):
		Y = floor(sqrt(ObjectToProcessCount))
		X = ceil(ObjectToProcessCount/floor(Y))
		size=[X,Y]
	else:
		size=[newDecrementerTotal,(ObjectToProcessCount//newDecrementerTotal)]
		
	return size

def texturefunction(context, hdr, hdra, tex_id):
	settings = context.scene.PivotPainterSettings

	if tex_id < len(settings.textures):
		tex = settings.textures[tex_id]

		texturergb = tex.rgb_mode
		texturealpha = tex.alpha_mode

	rgbfunction, hdr = get_pivot_painter_bake_rgb_function(texturergb, hdr)
	alphafunction, hdra = get_pivot_painter_bake_alpha_function(texturealpha, hdra)

	if texturealpha == 'Randomhdr' :
		texturealpha = 'Random'
	elif texturealpha == 'Hierarchyhdr' :
		texturealpha = 'Hierarchy'
	elif texturealpha == 'Diameterscaledhdr' :
		texturealpha = 'DiameterScaled'
	return rgbfunction, alphafunction, texturergb, texturealpha, hdr, hdra

def createtexture(context, width, height, tex_id):
	""" Create and save the textures """

	settings = context.scene.PivotPainterSettings

	pixels = [None] * width * height *4 # RGB pixel list
	hdr = False # Bool for texture creation
	rgbfunction, alphafunction, texturergb, texturealpha, hdr, _ = texturefunction(context, hdr, False,tex_id)	# Select variables between the textures in the UIPanel
	
	texturename = bpy.context.selected_objects[0].name + '_' + texturergb + '_' + texturealpha
	if hdr == True:
		texturename = texturename + '_HDR'
	if settings.createnew == False:																		#check if there is already the texture, else create new.
		for img in bpy.data.images:
			if img.name == texturename:
				image = img
				bpy.data.images.remove(image)														# there is no way to change dimensions
	image = bpy.data.images.new(name=texturename, width=width, height=height, float_buffer=hdr)
	
	pixels = setpixels(rgbfunction, alphafunction, texturealpha, tex_id, settings, width, height, pixels, hdr)	# Calculate the pixels values
	image.pixels = pixels																			# assign pixels

	if settings.savetextures == True:	
		image_settings = bpy.context.scene.render.image_settings
		image_settings.color_mode = 'RGBA'
		if hdr == True:
			imagepath = bpy.path.abspath(settings.folderpath) + image.name +'.exr'			
			image_settings.file_format = 'OPEN_EXR'
			image_settings.color_depth = '16'
		else:
			imagepath = bpy.path.abspath(settings.folderpath) + image.name +'.png'
			image_settings.file_format = 'PNG'
			image_settings.color_depth = '8'
		image.save_render(imagepath)

###########
### XML ###
def export_xml(context: bpy.types.Context) -> tuple[bool, str, str]:
    """ """

    settings = context.scene.DataBakerSettings
    report = context.scene.DataBakerReport

    root = ET.Element("BakedData",
                      type="Pivot Painter",
                      ID=report.ID,
                      version="1.0")

    # unit
    unit_el = ET.SubElement(root, "Unit",
                            system=report.unit_system,
                            unit=str(report.unit_unit),
                            length=str(report.unit_length),
                            scale=str(report.unit_scale),
                            invert_x=str(report.unit_invert_x),
                            invert_y=str(report.unit_invert_y),
                            invert_z=str(report.unit_invert_z))

    # mesh info
    mesh_export_path = os.path.abspath(report.mesh_path) if report.mesh_path != "" else ""

    mesh_el = ET.SubElement(root, "Mesh", path=mesh_export_path)

    # write xml
    tree = ET.ElementTree(root)
    if settings.export_xml_mode == "MESHPATH" and report.mesh_path != "":
        export_path = os.path.join(os.path.dirname(report.mesh_path), report.name + ".xml")
        tree.write(export_path)
        return (True, "", export_path)
    else:
        success, msg, export_path = get_path(settings.export_xml_file_path, settings.export_xml_file_name if settings.export_xml_file_name != "" else report.name, ".xml", [], settings.export_xml_override)
        if success:
            tree.write(export_path)
            return (True, "", export_path)
        else:
            return (False, msg, "")

######################
### BAKE FUNCTIONS ###
def get_pivot_painter_bake_rgb_function(rgb_mode, hdr): 
	""" """
	
	hdr = False
	if rgb_mode == "PIVOT":
		rgbfunction = get_pivot_painter_bake_pivot
		hdr = True
	elif rgb_mode == "XAXIS":
		rgbfunction = get_pivot_painter_bake_x_axis
	elif rgb_mode == "YAXIS":
		rgbfunction = get_pivot_painter_bake_y_axis
	elif rgb_mode == "ZAXIS":
		rgbfunction = get_pivot_painter_bake_z_axis		
	elif rgb_mode == "ORIGINPOS":
		rgbfunction = get_pivot_painter_bake_origin
		hdr = True
	elif rgb_mode == "ORIGINEXTENTS":
		rgbfunction = get_pivot_painter_bake_extents
		hdr = True
	else:
		rgbfunction = get_pivot_painter_bake_none
	
	return rgbfunction, hdr

def get_pivot_painter_bake_alpha_function(alpha_mode, hdr):
	""" """

	hdr = False
	if alpha_mode == 'Index' :		
		alphafunction = get_pivot_painter_bake_index
		hdr = True
	elif alpha_mode == 'Steps' or alpha_mode == 'Hierarchyhdr': #hierarchy is based on level function (later has a second process)
		alphafunction = get_pivot_painter_bake_level
		hdr = True
	elif alpha_mode == 'Hierarchy' :
		alphafunction = get_pivot_painter_bake_level
	elif alpha_mode == 'Randomhdr' :
		alphafunction = get_pivot_painter_bake_rand_float
		hdr = True
	elif alpha_mode == 'Diameter' :
		alphafunction = get_pivot_painter_bake_diagonal
		hdr = True
	elif alpha_mode == 'Xextent' :
		alphafunction = get_pivot_painter_bake_rand_x_extent
	elif alpha_mode == 'Yextent' :
		alphafunction = get_pivot_painter_bake_rand_y_extent
	elif alpha_mode == 'Zextent' :
		alphafunction = get_pivot_painter_bake_rand_z_extent
	elif alpha_mode == 'Random' :
		alphafunction = get_pivot_painter_bake_rand_float
	elif alpha_mode == 'Diameterscaledhdr' :
		alphafunction = get_pivot_painter_bake_diag_scaled_hdr
		hdr = True
	elif alpha_mode == 'Diameterscaled' :
		alphafunction = get_pivot_painter_bake_diag_scaled
	elif alpha_mode == 'SelectionOrder' :
		alphafunction = get_pivot_painter_bake_custom_order
		hdr = True
	elif alpha_mode == 'Xwidth' :
		alphafunction = get_pivot_painter_bake_rand_x_extent
		hdr = True
	elif alpha_mode == 'Ydepth' :
		alphafunction = get_pivot_painter_bake_rand_y_extent
		hdr = True
	elif alpha_mode == 'Zheight' :
		alphafunction = get_pivot_painter_bake_rand_z_extent
		hdr = True
	else:
		alphafunction = get_pivot_painter_bake_alpha_one

	return alphafunction, hdr

def get_pivot_painter_bake_extents(context, obj, counter, size, pixels, hdr):
	""" Extents(Dimensions) in local coordinates """
	settings = context.scene.PivotPainterSettings

	r = obj.dimensions[0]
	g = obj.dimensions[1]
	b = obj.dimensions[2]
	rgbvalues = [ r, g, b, ]
	return rgbvalues

def get_pivot_painter_bake_alpha_one(context, obj, counter, size, pixels, hdr):
	""" 0 as alpha, to avoid Null problems (used at the end to fill empty pixels) """
	settings = context.scene.PivotPainterSettings

	a = 0
	return a

def get_pivot_painter_bake_diag_scaled_hdr(context, obj, counter, size, pixels, hdr):
	""" Diagonal length of the bound box scaled """
	settings = context.scene.PivotPainterSettings

	ws=obj.matrix_world.to_scale()																							# The scale of the object
	vec1= mathutils.Vector ((obj.bound_box[0][0] * ws[0], obj.bound_box[0][1] * ws[1], obj.bound_box[0][2] * ws[2] ))       # Vector from the origin point to the min vertex position of the boundbox, scaled
	vec2= mathutils.Vector ((obj.bound_box[6][0] * ws[0], obj.bound_box[6][1] * ws[1], obj.bound_box[6][2] * ws[2] ))		# Max vertex is 6
	diagonalvector = vec1 - vec2
	length = diagonalvector.length
	return length

def get_pivot_painter_bake_custom_order(context, obj, counter, size, pixels, hdr):
	""" Selection order using custom property """
	settings = context.scene.PivotPainterSettings

	a = obj["SelectionOrder"]
	a = get_bitpacked_integer(a)
	return a

def get_pivot_painter_bake_diag_scaled(context, obj, counter, size, pixels, hdr):
	""" Diagonal length of the bound box scaled """
	settings = context.scene.PivotPainterSettings

	ws=obj.matrix_world.to_scale()																							# The scale of the object
	vec1= mathutils.Vector ((obj.bound_box[0][0] * ws[0], obj.bound_box[0][1] * ws[1], obj.bound_box[0][2] * ws[2] ))       # Vector from the origin point to the min vertex position of the boundbox, scaled
	vec2= mathutils.Vector ((obj.bound_box[6][0] * ws[0], obj.bound_box[6][1] * ws[1], obj.bound_box[6][2] * ws[2] ))		# Max vertex is 6
	diagonalvector = vec1 - vec2
	length = diagonalvector.length
	length = length /8 			
	length = np.clip(length,1,256)
	length = length /256
	return length

def get_pivot_painter_bake_diagonal(context, obj, counter, size, pixels, hdr):
	""" Diagonal length of the bound box """
	settings = context.scene.PivotPainterSettings

	vec1= mathutils.Vector ((obj.bound_box[0][0], obj.bound_box[0][1], obj.bound_box[0][2] ))				# Vector from the origin point to the min vertex position of the boundbox, unscaled
	vec2= mathutils.Vector ((obj.bound_box[6][0], obj.bound_box[6][1], obj.bound_box[6][2] ))				# Max vertex is 6 (lists start from zero, six is the seventh item in a list)
	diagonalvector = vec1 - vec2																			# Vectors point to the opposite direction
	length = diagonalvector.length
	return length

def get_pivot_painter_bake_origin(context, obj, counter, size, pixels, hdr):
	""" Find the center of the boundbox. Origin Position (not Pivot Point) """
	settings = context.scene.PivotPainterSettings

	ws=obj.matrix_world.to_scale()																							# The scale of the object
	vec1= mathutils.Vector ((obj.bound_box[0][0] * ws[0], obj.bound_box[0][1] * ws[1], obj.bound_box[0][2] * ws[2] ))       # Vector from the origin point to the min vertex position of the boundbox, scaled
	vec2= mathutils.Vector ((obj.bound_box[6][0] * ws[0], obj.bound_box[6][1] * ws[1], obj.bound_box[6][2] * ws[2] ))		# Max vertex is 6
	center = vec1 + vec2
	center = center /2							# Vector point to Center of the boundbox from origin point in local coordinates

	wr=obj.matrix_world.to_euler('XYZ')			# Rotation of the obj
	center.rotate(wr)
	wl=obj.matrix_world.to_translation()		# Origin position in global coordinates
	center = center + wl						# The boundbox center in global coordinates
	r = center[0]
	g = center[1]
	b = center[2]
	rgbvalues = [ r, g, b, ]
	return rgbvalues																		# TO DO(Canceled, it cannot be used with the current shaders): use 3cursor move technic so I can set center type, mass or bb or surface center.

def get_pivot_painter_bake_rand_float(context, obj, counter, size, pixels, hdr):
	""" Random float """
	settings = context.scene.PivotPainterSettings

	a = random.random()
	return a

def get_pivot_painter_bake_level(context, obj, counter, size, pixels, hdr):
	""" Level, number of parents of every object """
	settings = context.scene.PivotPainterSettings

	par=[] 											# Create a list with the parents of the obj
	j = 0
	if obj.parent:
		par.append(obj.parent) 						# First input for while loop. without the first it fails.
		while par[j].parent: 						# IF the parent has a parent    (can it be simplified?)
			par.append(par[j].parent)				# add it to the list
			j=j+1
	level = len(par)
	return level

def get_pivot_painter_bake_index(context, obj, counter, size, pixels, hdr):
	""" Index of the parent. (Used to inherit properties, like rotation position.) """
	settings = context.scene.PivotPainterSettings

	if obj.parent:
		index=int(bpy.context.selected_objects.index(obj.parent)) 	# index nubmer of the parent. # do I need remove .5 ? In find object parents it removes from arrayIndex (Line1113 at PivotPainter2.ms)# YES SEE "2dArrayLookupByIndex" material function in the unreal engine. it adds .5 # NO. TESTED. the index wont work.
	else:
		index=int(bpy.context.selected_objects.index(obj))
	# index = index - 0.5																					# NO FAILURE # Testing # For compatibility function to be the same as the maxscript. (I have no Idea why this operation ) 
	a = get_bitpacked_integer(index)										# packs int to float
	return a

def get_pivot_painter_bake_pivot(context, obj, counter, size, pixels, hdr):
	""" Pivot point, in practice the origin position """
	settings = context.scene.PivotPainterSettings

	wl=obj.matrix_world.to_translation()		# Gives world location
	r=wl[0]
	g=-wl[1]
	b=wl[2]
	rgbvalues = [ r, g, b, ]
	return rgbvalues

def get_pivot_painter_bake_x_axis(context, obj, counter, size, pixels, hdr):
	""" X Axis, the direction of the local x axis """
	settings = context.scene.PivotPainterSettings

	#if PivotPainterSettings.firstlevel == True or PivotPainterSettings.secondlevel == True or PivotPainterSettings.thirdlevel == True or PivotPainterSettings.fourthlevel == True :				# Avoid unnecessary calculations. Probably wont use BoundBox method
	if True:
		localevel = 0
		localevel = level (PivotPainterSettings, obj, counter, size, pixels, hdr)
		if (localevel == 0 and PivotPainterSettings.firstlevel == True) or (localevel == 1 and PivotPainterSettings.secondlevel == True) or (localevel == 2 and PivotPainterSettings.thirdlevel == True) or (localevel == 3 and PivotPainterSettings.fourthlevel == True) :		# Choosing BoundBox method 
			vec, _ = boundboxAxis(PivotPainterSettings, obj, counter, size, pixels, hdr)
		else:
			vec = mathutils.Vector((1.0, 0.0, 0.0))
			wr=obj.matrix_world.to_euler('XYZ')
			vec.rotate(wr)	
	else:
		vec = mathutils.Vector((1.0, 0.0, 0.0))
		wr=obj.matrix_world.to_euler('XYZ')
		vec.rotate(wr)
	r = ( vec[0] +1 ) /2
	g = ( (-vec[1]) +1 ) /2
	b = ( vec[2] +1 ) /2
	rgbvalues = [r, g, b]
	return rgbvalues

def get_pivot_painter_bake_y_axis(context, obj, counter, size, pixels, hdr):
	""" Y Axis, the direction of the local Y axis """
	settings = context.scene.PivotPainterSettings

	vec = mathutils.Vector((0.0, 1.0, 0.0))
	wr=obj.matrix_world.to_euler('XYZ')
	vec.rotate(wr)
	r = ( vec[0] +1 ) /2
	g = ( (-vec[1]) +1 ) /2
	b = ( vec[2] +1 ) /2
	rgbvalues = [r, g, b]
	return rgbvalues

def get_pivot_painter_bake_z_axis(context, obj, counter, size, pixels, hdr):
	""" Z Axis, the direction of the local z axis """
	settings = context.scene.PivotPainterSettings

	vec = mathutils.Vector((0.0, 0.0, 1.0))
	wr=obj.matrix_world.to_euler('XYZ')
	vec.rotate(wr)
	r = ( vec[0] +1 ) /2
	g = ( (-vec[1]) +1 ) /2
	b = ( vec[2] +1 ) /2
	rgbvalues = [r, g, b]
	return rgbvalues

def get_pivot_painter_bake_rand_x_extent(context, obj, counter, size, pixels, hdr):
	""" X Extent, the length of the object on the local x axis """
	settings = context.scene.PivotPainterSettings
	
	#if PivotPainterSettings.firstlevel == True or PivotPainterSettings.secondlevel == True or PivotPainterSettings.thirdlevel == True or PivotPainterSettings.fourthlevel == True :				# Avoid unnecessary calculations. Probably wont use BoundBox method
	if True:
		localevel = 0
		localevel = level (PivotPainterSettings, obj, counter, size, pixels, hdr)
		if (localevel == 0 and PivotPainterSettings.firstlevel == True) or (localevel == 1 and PivotPainterSettings.secondlevel == True) or (localevel == 2 and PivotPainterSettings.thirdlevel == True) or (localevel == 3 and PivotPainterSettings.fourthlevel == True) :		# Choosing BoundBox method 
			_, a = boundboxAxis(PivotPainterSettings, obj, counter, size, pixels, hdr)
			a = a/8
		else:
			a = obj.dimensions[0]/8 
	else:
		a = obj.dimensions[0]/8 			# "Dimensions" property, change with the scale -> There is no need to apply scale, nor does it effect it.
	if hdr == False :
		a = np.clip(a,1,256)
		a = a /256
	return a

def get_pivot_painter_bake_rand_y_extent(context, obj, counter, size, pixels, hdr):
	""" Y Extent, the length of the object on the local y axis """
	settings = context.scene.PivotPainterSettings

	a = obj.dimensions[1]/8 			# "Dimensions" property, change with the scale -> There is no need to apply scale, nor does it effect it.
	if hdr == False :
		a = np.clip(a,1,256)
		a = a /256
	return a

def get_pivot_painter_bake_rand_z_extent(context, obj, counter, size, pixels, hdr):
	""" Z Extent, the length of the object on the local z axis """
	settings = context.scene.PivotPainterSettings

	a = obj.dimensions[2]/8 			# "Dimensions" property, change with the scale -> There is no need to apply scale, nor does it effect it.
	if hdr == False :
		a = np.clip(a,1,256)
		a = a /256
	return a

def get_pivot_painter_bake_none(context, obj, counter, size, pixels, hdr):
	""" 0 as rgb values , to avoid Null problems (used at the end to fill empty pixels) """
	settings = context.scene.PivotPainterSettings

	rgb = ( 0, 0, 0)
	return rgb # @TODO weird

#########################
### PATHS & FILENAMES ###
def get_path(path: str, file_name: str, file_ext: str, tags: list, override_file: bool) -> tuple[bool, str, str]:
    """ Compiles file path/name/extension into a path and performs a couples of safety checks """
    
    file_exts = [".png", ".exr", ".fbx"]
    if file_ext not in file_exts:
        return (False, "Invalid File Extension", "")

    file_name = replace_tags(file_name, tags)
    export_path = os.path.abspath(os.path.join(bpy.path.abspath(path), file_name + file_ext))
    success, msg = check_path(export_path, override_file)
    
    return (success, msg, export_path)

def replace_tags(name: str, tags: list) -> str:
    # check tags
    for tag_key, tag_value in tags.items():
        tag = "<"+tag_key+">"
        if (tag in name):
            name = name.replace(tag, tag_value)

    return name

def check_path(path: str, override_file: str) -> tuple[bool, str]:
    """ """
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        return (False, f"Directory does not exist: {dir}")
    
    if not os.access(dir, os.W_OK):
        return (False, f"Directory is not writable: {dir}")

    if os.path.isfile(path) and not override_file:
        return (False, f"File already exists: {path}")

    return (True, "")