import sys
import os
import bpy

addon_path = os.path.abspath('addon')
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

import waterfall_tool
waterfall_tool.register()

print("Waterfall tool loaded for preview.")
