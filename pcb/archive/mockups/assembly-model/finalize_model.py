"""Set convenient units and initial camera view in the saved editable model."""
import bpy
from pathlib import Path
path=Path(__file__).resolve().parent/'trueskate-assembly.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
scene.unit_settings.length_unit='MILLIMETERS'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('Model saved with millimetre units and camera viewport')
