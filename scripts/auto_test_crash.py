import sys
import os
import bpy
import time

addon_path = os.path.abspath('addon')
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

import waterfall_tool
waterfall_tool.register()

print("Test start")

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 5))
emitter = bpy.context.active_object
emitter.name = "TestEmitter"
emitter.waterfall_emitter.enabled = True
emitter.waterfall_emitter.speed = 10.0
emitter.waterfall_emitter.direction_axis = 'NEG_Z'

bpy.ops.waterfall.simulate_curve()

def wait_for_timers():
    timeout = time.time() + 0.5
    while time.time() < timeout:
        bpy.context.view_layer.update()
wait_for_timers()

print("Move emitter")
emitter.location.x += 1.0
emitter.update_tag()
bpy.context.view_layer.update()

wait_for_timers()
print("Done")
