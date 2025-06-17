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
class OATBAKER_MT_MainPanel_Presets(bpy.types.Menu):
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
    bl_idname = "OATBAKER_PT_oatpanel"
    bl_label = "OAT Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

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
        OATBAKER_PT_ObjectAnimation_Preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

########
# DATA #
########
class OATBAKER_PT_DataPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_datapanel"
    bl_parent_id = "OATBAKER_PT_oatpanel"
    bl_label = "Data"		
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

class OATBAKER_PT_FirstTexPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_firsttexpanel"
    bl_parent_id = "OATBAKER_PT_datapanel"
    bl_label = "First Texture"		
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    #bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        layout.active = settings.FirstTexture
        layout.prop(settings, "FirstTexture", text="")

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        bEnabled = settings.FirstTexture

        row = layout.row()
        row.prop(settings, "FirstTextureR")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "FirstTextureG")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "FirstTextureB")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "FirstTextureA")
        row.enabled = bEnabled

        row = layout.separator(factor=2)

        if bEnabled:
            bPosition = settings.FirstTextureR == "PosX" or \
                        settings.FirstTextureG == "PosY" or \
                        settings.FirstTextureB == "PosZ"

            if bPosition:
                row = layout.row()
                row.prop(settings, "NormalizePosition")

            bRotation = settings.FirstTextureR == "QuatX" or \
                        settings.FirstTextureG == "QuatY" or \
                        settings.FirstTextureB == "QuatZ" or \
                        settings.FirstTextureA == "QuatW"

            if bRotation:    
                row = layout.row()
                row.prop(settings, "NormalizeQuaternion")

            bScale =    settings.FirstTextureR == "ScaleX" or \
                        settings.FirstTextureG == "ScaleY" or \
                        settings.FirstTextureB == "ScaleZ" or \
                        settings.FirstTextureA == "Scale"

            if settings.FirstTextureA == "Scale":
                row = layout.row()
                row.prop(settings, "ScaleUniformAxis")

            if bScale:    
                row = layout.row()
                row.prop(settings, "NormalizeScale")

            row = layout.separator(factor=2)

            bR8bits  = settings.FirstTextureR == "PosX" and settings.NormalizePosition
            bR8bits |= settings.FirstTextureR == "QuatX" and settings.NormalizeQuaternion
            bR8bits |= settings.FirstTextureR == "ScaleX" and settings.NormalizeScale

            bG8bits  = settings.FirstTextureG == "PosY" and settings.NormalizePosition
            bG8bits |= settings.FirstTextureG == "QuatY" and settings.NormalizeQuaternion
            bG8bits |= settings.FirstTextureG == "ScaleY" and settings.NormalizeScale

            bB8bits  = settings.FirstTextureB == "PosZ" and settings.NormalizePosition
            bB8bits |= settings.FirstTextureB == "QuatZ" and settings.NormalizeQuaternion
            bB8bits |= settings.FirstTextureB == "ScaleZ" and settings.NormalizeScale

            bA8bits  = settings.FirstTextureA == "Scale" and settings.NormalizeScale
            bA8bits |= settings.FirstTextureA == "ObjRand"
            bA8bits |= settings.FirstTextureA == "None"

            b8bits = bR8bits and bG8bits and bB8bits and bA8bits

            b32bits = settings.FirstTextureA == "Quat"

            if b8bits:
                row = layout.row()
                row.label(text="First texture *CAN* be RGBA 8 bits", icon="CHECKMARK")
            elif b32bits:
                row = layout.row()
                row.label(text="First texture *MUST* be HDR 32 bits", icon="ERROR")
            else:
                row = layout.row()
                row.label(text="First texture *MUST* at least be 16 bits", icon="ERROR")

            if (settings.FirstTextureA == "Scale" or \
               settings.SecondTextureA == "Scale" or \
               settings.FirstTextureA == "Scale") and \
               (settings.FirstTextureR == "ScaleX" or \
                settings.FirstTextureG == "ScaleY" or \
                settings.FirstTextureB == "ScaleZ"):
                row = layout.row()
                row.label(text="Uniform scale is already packed in the position texture", icon="ERROR")

class OATBAKER_PT_SecondTexPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_secondtexpanel"
    bl_parent_id = "OATBAKER_PT_datapanel"
    bl_label = "Second Texture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    #bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        layout.active = settings.SecondTexture
        layout.prop(settings, "SecondTexture", text="")

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        bEnabled = settings.SecondTexture

        row = layout.row()
        row.prop(settings, "SecondTextureR")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "SecondTextureG")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "SecondTextureB")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "SecondTextureA")
        row.enabled = bEnabled

        row = layout.separator(factor=2)

        if bEnabled:
            bPosition = settings.SecondTextureR == "PosX" or \
                        settings.SecondTextureG == "PosY" or \
                        settings.SecondTextureB == "PosZ"

            if bPosition:
                row = layout.row()
                row.prop(settings, "NormalizePosition")

            bRotation = settings.SecondTextureR == "QuatX" or \
                        settings.SecondTextureG == "QuatY" or \
                        settings.SecondTextureB == "QuatZ" or \
                        settings.SecondTextureA == "QuatW"

            if bRotation:    
                row = layout.row()
                row.prop(settings, "NormalizeQuaternion")

            bScale =    settings.SecondTextureR == "ScaleX" or \
                        settings.SecondTextureG == "ScaleY" or \
                        settings.SecondTextureB == "ScaleZ" or \
                        settings.SecondTextureA == "Scale"

            if settings.SecondTextureA == "Scale":
                row = layout.row()
                row.prop(settings, "ScaleUniformAxis")

            if bScale:    
                row = layout.row()
                row.prop(settings, "NormalizeScale")

            row = layout.separator(factor=2)
            
            bR8bits  = settings.SecondTextureR == "PosX" and settings.NormalizePosition
            bR8bits |= settings.SecondTextureR == "QuatX" and settings.NormalizeQuaternion
            bR8bits |= settings.SecondTextureR == "ScaleX" and settings.NormalizeScale

            bG8bits  = settings.SecondTextureG == "PosY" and settings.NormalizePosition
            bG8bits |= settings.SecondTextureG == "QuatY" and settings.NormalizeQuaternion
            bG8bits |= settings.SecondTextureG == "ScaleY" and settings.NormalizeScale

            bB8bits  = settings.SecondTextureB == "PosZ" and settings.NormalizePosition
            bB8bits |= settings.SecondTextureB == "QuatZ" and settings.NormalizeQuaternion
            bB8bits |= settings.SecondTextureB == "ScaleZ" and settings.NormalizeScale

            bA8bits  = settings.SecondTextureA == "Scale" and settings.NormalizeScale
            bA8bits |= settings.SecondTextureA == "ObjRand"
            bA8bits |= settings.SecondTextureA == "None"

            b8bits = bR8bits and bG8bits and bB8bits and bA8bits

            b32bits = settings.SecondTextureA == "Quat"

            if b8bits:
                row = layout.row()
                row.label(text="Second texture *CAN* be RGBA 8 bits", icon="CHECKMARK")
            elif b32bits:
                row = layout.row()
                row.label(text="Second texture *MUST* be HDR 32 bits", icon="ERROR")
            else:
                row = layout.row()
                row.label(text="Second texture *MUST* at least be 16 bits", icon="ERROR")

            if (settings.FirstTextureA == "Scale" or \
               settings.SecondTextureA == "Scale" or \
               settings.ThirdTextureA == "Scale") and \
               (settings.SecondTextureR == "ScaleX" or \
                settings.SecondTextureG == "ScaleY" or \
                settings.SecondTextureB == "ScaleZ"):
                row = layout.row()
                row.label(text="Uniform scale is already packed in the position texture", icon="ERROR")

class OATBAKER_PT_ThirdTexPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_thirdtexpanel"
    bl_parent_id = "OATBAKER_PT_datapanel"
    bl_label = "Third Texture"		
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        layout.active = settings.ThirdTexture
        layout.prop(settings, "ThirdTexture", text="")

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        bEnabled = settings.ThirdTexture

        row = layout.row()
        row.prop(settings, "ThirdTextureR")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "ThirdTextureG")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "ThirdTextureB")
        row.enabled = bEnabled

        row = layout.row()
        row.prop(settings, "ThirdTextureA")
        row.enabled = bEnabled

        row = layout.separator(factor=2)

        if bEnabled:
            bPosition = settings.ThirdTextureR == "PosX" or \
                        settings.ThirdTextureG == "PosY" or \
                        settings.ThirdTextureB == "PosZ"

            if bPosition:
                row = layout.row()
                row.prop(settings, "NormalizePosition")

            bRotation = settings.ThirdTextureR == "QuatX" or \
                        settings.ThirdTextureG == "QuatY" or \
                        settings.ThirdTextureB == "QuatZ" or \
                        settings.ThirdTextureA == "QuatW"

            if bRotation:    
                row = layout.row()
                row.prop(settings, "NormalizeQuaternion")

            bScale =    settings.ThirdTextureR == "ScaleX" or \
                        settings.ThirdTextureG == "ScaleY" or \
                        settings.ThirdTextureB == "ScaleZ" or \
                        settings.ThirdTextureA == "Scale"
            
            if settings.ThirdTextureA == "Scale":
                row = layout.row()
                row.prop(settings, "ScaleUniformAxis")

            if bScale:    
                row = layout.row()
                row.prop(settings, "NormalizeScale")
                
            row = layout.separator(factor=2)
            
            bR8bits  = settings.ThirdTextureR == "PosX" and settings.NormalizePosition
            bR8bits |= settings.ThirdTextureR == "QuatX" and settings.NormalizeQuaternion
            bR8bits |= settings.ThirdTextureR == "ScaleX" and settings.NormalizeScale

            bG8bits  = settings.ThirdTextureG == "PosY" and settings.NormalizePosition
            bG8bits |= settings.ThirdTextureG == "QuatY" and settings.NormalizeQuaternion
            bG8bits |= settings.ThirdTextureG == "ScaleY" and settings.NormalizeScale

            bB8bits  = settings.ThirdTextureB == "PosZ" and settings.NormalizePosition
            bB8bits |= settings.ThirdTextureB == "QuatZ" and settings.NormalizeQuaternion
            bB8bits |= settings.ThirdTextureB == "ScaleZ" and settings.NormalizeScale

            bA8bits  = settings.ThirdTextureA == "Scale" and settings.NormalizeScale
            bA8bits |= settings.ThirdTextureA == "ObjRand"
            bA8bits |= settings.ThirdTextureA == "None"

            b8bits = bR8bits and bG8bits and bB8bits and bA8bits

            b32bits = settings.ThirdTextureA == "Quat"

            if b8bits:
                row = layout.row()
                row.label(text="Third texture *CAN* be RGBA 8 bits", icon="CHECKMARK")
            elif b32bits:
                row = layout.row()
                row.label(text="Third texture *MUST* be HDR 32 bits", icon="ERROR")
            else:
                row = layout.row()
                row.label(text="Third texture *MUST* at least be 16 bits", icon="ERROR")

            if (settings.FirstTextureA == "Scale" or \
               settings.SecondTextureA == "Scale" or \
               settings.ThirdTextureA == "Scale") and \
               (settings.ThirdTextureR == "ScaleX" or \
                settings.ThirdTextureG == "ScaleY" or \
                settings.ThirdTextureB == "ScaleZ"):
                row = layout.row()
                row.label(text="Uniform scale is already packed in the position texture", icon="ERROR")

########
# BAKE #
########
class OATBAKER_PT_BakePanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_bakepanel"
    bl_parent_id = "OATBAKER_PT_oatpanel"
    bl_label = "Bake"		
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings
        
        row = layout.row()
        row.prop(settings, "Scale")

        row = layout.row()
        row.prop(settings, "ORIGIN")
        
        # bake button
        row = layout.row()
        row.operator("gametools.objectanimbaker_bake")
        row.scale_y = 2.0 # bigger button

class OATBAKER_PT_ObjPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_objpanel"
    bl_parent_id = "OATBAKER_PT_bakepanel"
    bl_label = "Mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        row = layout.row()
        row.prop(settings, "MergeBakedMesh")

        row = layout.row()
        row.prop(settings, "MergedBakedMeshName")
        row.enabled = settings.MergeBakedMesh

        row = layout.row()
        row.prop(settings, "ObjAutoExport")
        row.enabled = settings.MergeBakedMesh
        if settings.ObjAutoExport:
            row = layout.row()
            row.prop(settings, "ObjPath")

class OATBAKER_PT_UVPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_uvpanel"
    bl_parent_id = "OATBAKER_PT_objpanel"
    bl_label = "UVs"		
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 0

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        # uv settings
        row = layout.row()
        row.prop(settings, "uv_index")

        row = layout.row()
        row.prop(settings, "uv_channelMode")
        if settings.uv_channelMode == "Value":
            row = layout.row()
            row.prop(settings, "uv_channelValue")

class OATBAKER_PT_TexPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_texpanel"
    bl_parent_id = "OATBAKER_PT_bakepanel"
    bl_label = "Textures"		
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 1

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        # texture settings
        row = layout.row()
        row.prop(settings, "TexName")

        row = layout.row()
        row.prop(settings, "TexAutoExport")
        if settings.TexAutoExport:
            row = layout.row()
            row.prop(settings, "TexPath")

class OATBAKER_PT_FramesPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_framespanel"
    bl_parent_id = "OATBAKER_PT_bakepanel"
    bl_label = "Frames"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 2

    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        # frame range
        row = layout.row()
        row.label(text="Frame Range:")

        row = layout.row()
        row.prop(context.scene, "frame_start", text="")
        row.prop(context.scene, "frame_end", text="")
        
        # frame step
        row = layout.row()
        row.prop(context.scene, "frame_step", text="Frame Step:")

        # last frame?
        row = layout.row()
        row.prop(settings, "bIncludeLastFrame")

class OATBAKER_PT_BakeInfoPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_bakeinfopanel"
    bl_parent_id = "OATBAKER_PT_bakepanel"
    bl_label = "Bake Info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 3

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings
'''
        Frames = GetFramesToBake(context)
        Icon = "CHECKMARK" if Frames > 0 else "ERROR"
        
        row = layout.row()
        row.label(text="Frames: " + str(Frames), icon=Icon)

        TextureResolution = GetTextureResolution(context)
        if TextureResolution[0]:
            row = layout.row()
            row.label(text="Texture size: " + str(TextureResolution[2]) + "x" + str(TextureResolution[3]), icon="CHECKMARK")

            row = layout.separator(factor=1)

            MemoryFootprintPerTexture = TextureResolution[2] * TextureResolution[3] * 32 * 4
            Textures = 0
            if settings.FirstTexture:
                Textures += 1
            if settings.SecondTexture:
                Textures += 1
            if settings.ThirdTexture:
                Textures += 1

            MemoryFootprintPerTexture *= Textures
            MemoryFootprintPerTexture = MemoryFootprintPerTexture / 1024.0

            row = layout.row()
            row.label(text="HDR Textures MemSize: " + str(MemoryFootprintPerTexture) + "KB")
        else:
            row = layout.row()
            row.label(text="Texture size: INVALID!", icon="ERROR")'''

class OATBAKER_PT_UEInfoPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_ueinfopanel"
    bl_parent_id = "OATBAKER_PT_bakepanel"
    bl_label = "UE Material Multipliers"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 4

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        row = layout.row()
        row.label(text="Position Multiplier")
        if settings.bPositionNormalized:
            row = layout.row()
            row.label(text="X: " + str(settings.MaxPosition.x * settings.unit_scale), icon="CON_OBJECTSOLVER")

            row = layout.row()
            row.label(text="Y: " + str(settings.MaxPosition.y * settings.unit_scale), icon="CON_OBJECTSOLVER")

            row = layout.row()
            row.label(text="Z: " + str(settings.MaxPosition.z * settings.unit_scale), icon="CON_OBJECTSOLVER")
        else:
            row = layout.row()
            row.label(text="No multiplier", icon="CHECKMARK")

        row = layout.separator(factor=1)

        row = layout.row()
        row.label(text="Scale Multiplier")
        if settings.bScaleNormalized:
            if settings.FirstTextureA == "Scale" or \
               settings.SecondTextureA == "Scale" or \
               settings.ThirdTextureA == "Scale":
                if settings.scaleUniformAxis == "X":
                    row = layout.row()
                    row.label(text="Uniform Scale X: " + str(settings.MaxScale.x), icon="CON_OBJECTSOLVER")
                elif settings.scaleUniformAxis == "Y":
                    row = layout.row()
                    row.label(text="Uniform Scale Y: " + str(settings.MaxScale.y), icon="CON_OBJECTSOLVER")
                else: #Z
                    row = layout.row()
                    row.label(text="Uniform Scale Z: " + str(settings.MaxScale.z), icon="CON_OBJECTSOLVER")
            else:
                row = layout.row()
                row.label(text="X: " + str(settings.MaxScale.x), icon="CON_OBJECTSOLVER")

                row = layout.row()
                row.label(text="Y: " + str(settings.MaxScale.y), icon="CON_OBJECTSOLVER")

                row = layout.row()
                row.label(text="Z: " + str(settings.MaxScale.z), icon="CON_OBJECTSOLVER")
        else:
            row = layout.row()
            row.label(text="No multiplier", icon="CHECKMARK")

        row = layout.separator(factor=1)

        row = layout.row()
        row.label(text="Speed Multiplier: " + str(settings.AnimSpeed))
        

class OATBAKER_PT_UEBoundsInfoPanel(bpy.types.Panel):
    bl_idname = "OATBAKER_PT_ueboundsinfopanel"
    bl_parent_id = "OATBAKER_PT_bakepanel"
    bl_label = "UE Mesh vertices_bounds"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Tools"
    bl_order = 5

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # get settings
        settings = context.scene.OATBakerSettings

        row = layout.row()
        row.prop(settings, "bAccurateBounds")

        row = layout.row()
        row.prop(settings, "bPrevizBounds")

        row = layout.row()
        row.label(text="Max vertices_bounds")
        if settings.bMaxBounds:
            row = layout.row()
            row.label(text="X: " + str(settings.MaxBounds.x), icon="CON_OBJECTSOLVER")

            row = layout.row()
            row.label(text="Y: " + str(settings.MaxBounds.y), icon="CON_OBJECTSOLVER")

            row = layout.row()
            row.label(text="Z: " + str(settings.MaxBounds.z), icon="CON_OBJECTSOLVER")
        else:
            row = layout.row()
            row.label(text="No bounds computed", icon="CHECKMARK")

        row = layout.separator(factor=2)

        row = layout.row()
        row.label(text="Min vertices_bounds")
        if settings.bMinBounds:
            row = layout.row()
            row.label(text="X: " + str(settings.MinBounds.x), icon="CON_OBJECTSOLVER")

            row = layout.row()
            row.label(text="Y: " + str(settings.MinBounds.y), icon="CON_OBJECTSOLVER")

            row = layout.row()
            row.label(text="Z: " + str(settings.MinBounds.z), icon="CON_OBJECTSOLVER")
        else:
            row = layout.row()
            row.label(text="No bounds computed", icon="CHECKMARK")