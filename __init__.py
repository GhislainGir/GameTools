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

bl_info = {
    "name": "Data Baker",
    "author": "Ghislain GIRARDOT, Joshua BOGART, George VOGIATZIS (Gvgeo)",
    "version": (0, 3, 1),
    "blender": (4, 3, 2),
    "location": "View 3D -> Game Tools",
    "description": "Toolset for baking animations and mesh data into textures using customizable layouts, UV maps, vertex colors, and normals",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "3D View",
}

import bpy
import os

from . import auto_load

auto_load.init()

def register():
    auto_load.register()

    if register_preset_path := getattr(bpy.utils, "register_preset_path", None): # @TODO check
        register_preset_path(os.path.join(os.path.dirname(__file__)))

def unregister():
    auto_load.unregister()

    if unregister_preset_path := getattr(bpy.utils, "unregister_preset_path", None):
        unregister_preset_path(os.path.join(os.path.dirname(__file__)))
