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
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "View 3D -> Bake Data",
    "description": "Enables you to bake all kind of data (pivots, axis, shapekey offset/normals, linear mask, spherical mask and more, into UVs or Vertex Color",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "3D View",
}

import bpy
from bpy.props import PointerProperty
from bpy.types import PropertyGroup
import os
import shutil

from . import auto_load

def get_writable_preset_path(subdir: str) -> str:
    """
    Return the first preset folder we have permission to write to, given a preset subdir, excluding the vscode_development

    :param subdir: preset sub directory to look for
    :return: folder path
    :rtype: str
    """
    for path in bpy.utils.preset_paths("operator"):
        target_dir = os.path.join(path, subdir)

        if 'vscode_development' in path:
            continue

        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except PermissionError:
                continue

        try:
            test_file = os.path.join(target_dir, "temp_test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return target_dir
        except (PermissionError, OSError):
            continue

    return None

def install_default_presets():
    """
    Copy .py preset files bundled with the extension to the user preset folder, if not already in there
    """

    preset_subdirs = [
        "gametools_databaker",
        "gametools_oatbaker",
        "gametools_objectattributes",
        "gametools_sdfbaker",
        "gametools_vatbaker",
        "gametools_batbaker",
    ]

    for preset_subdir in preset_subdirs:
        writable_path = get_writable_preset_path(preset_subdir)
        if writable_path is None:
            print("Warning: No writable preset path found.")
            return

        addon_preset_path = os.path.join(os.path.dirname(__file__), "presets", preset_subdir)
        if not os.path.exists(addon_preset_path):
            os.makedirs(addon_preset_path)

        for file in os.listdir(addon_preset_path):
            src = os.path.join(addon_preset_path, file)
            dst = os.path.join(writable_path, file)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)

auto_load.init()

def register():
    install_default_presets()
    
    auto_load.register()

def unregister():
    auto_load.unregister()