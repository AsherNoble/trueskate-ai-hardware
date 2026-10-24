"""Apply the final surface/camera refinement to the first saved scene."""
import bpy
from pathlib import Path
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'trueskate-assembly.blend'))
for o in bpy.data.objects:
    if o.name.startswith('Top copper'):
        o.matrix_world=Matrix.Translation((0,0,1.64)) @ Matrix.Diagonal((1,1,.01,1)) @ o.matrix_world
scene=bpy.context.scene
scene.camera.data.ortho_scale=285
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'trueskate-assembly.blend'))
scene.render.filepath=str(ROOT/'assembly-perspective.png')
bpy.ops.render.render(write_still=True)
cam=scene.camera;cam.location=(53,72,400)
cam.rotation_euler=(Vector((53,72,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=252
scene.render.filepath=str(ROOT/'assembly-top.png')
bpy.ops.render.render(write_still=True)
