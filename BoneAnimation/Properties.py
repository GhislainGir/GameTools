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

from bpy.props import PointerProperty, BoolProperty, FloatProperty, EnumProperty, StringProperty, IntProperty, CollectionProperty, FloatVectorProperty
from bpy.types import PropertyGroup

#############################################################################################
###################################### PROPERTY GROUPS ######################################
#############################################################################################
class BATBAKER_PG_SettingsPropertyGroup(PropertyGroup):
    """ """

    # scene 
    unit_scale: FloatProperty(name="Scale", min=0.001, default=100.0, description="Scale factor for the baked offsets/positions. This compensates for Blender's default unit (1 meter) and aligns with the target application's unit system. A default factor of 100 is used to convert from meters to centimeters, Unreal's default unit")
    unit_invert_x: BoolProperty(name="Invert X", default=False, description="Invert the world X axis (set to False for Unreal Engine compatibility)")
    unit_invert_y: BoolProperty(name="Invert Y", default=True, description="Invert the world Y axis (set to True for Unreal Engine compatibility)")
    unit_invert_z: BoolProperty(name="Invert Z", default=False, description="Invert the world Z axis (set to False for Unreal Engine compatibility)")
    unit_invert_v: BoolProperty(name="Invert V", default=True, description="Invert the V axis of the UVMap and flip the BAT texture(s) upside down. Typically True for exporting to Unreal Engine or DirectX apps, False for Unity or OpenGL apps")

    quat_angle_unit_modes = [
        ("UNIT", "Unit", "Angle is normalized in [0:1] range, 1.0 for 360 degrees"),
        ("DEGREES", "Degrees", "Angle is in degrees in [0:360] range"),
        ("RADIANS", "Radians", "Angle is in radians in [0:TwoPi] range")
    ]
    quat_angle_unit_mode: EnumProperty(name="Unit", items=quat_angle_unit_modes, default="UNIT", description="")

    rot_modes = [
        ("QUAT", "Quaternion", ""),
        ("AXES", "Axes", ""),
        ("ANGLE_AXIS", "Angle & Axis", ""),
    ]
    rot_mode: EnumProperty(name="Modes", items=rot_modes, default="ANGLE_AXIS", description="")

def register():
    bpy.types.Scene.BATBakerSettings = PointerProperty(type=BATBAKER_PG_SettingsPropertyGroup)

def unregister():
    del bpy.types.Scene.BATBakerSettings
