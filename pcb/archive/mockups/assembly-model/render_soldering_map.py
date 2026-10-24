"""Export precise callout projections and render the soldered carrier alone."""
import bpy,json,re,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'trueskate-assembly.blend'))
scene=bpy.context.scene
fps={f['ref']:f for f in json.loads((ROOT/'board-geometry.json').read_text())['footprints']}
def centre(ref,numbers=None):
    pads=[p for p in fps[ref]['pads'] if numbers is None or p['number'] in numbers]
    return [sum(p['xy'][i] for p in pads)/len(pads) for i in (0,1)]
def project(p):
    q=world_to_camera_view(scene,scene.camera,Vector((p[0],120-p[1],p[2])))
    return [q.x*scene.render.resolution_x,(1-q.y)*scene.render.resolution_y]
targets={
 'teensy':[(*centre('J1'),6),(*centre('J2'),6)],
 'mini_control':[(*centre('J14',[str(n) for n in range(1,11)]),6)],
 'mini_phase':[(*centre('J14',['P1','P2','P3']),6)],
 'motor_header':[(*centre('J24'),6.3)],
 'encoder':[(*centre('J36'),6)],
 'bulk':[(*centre('C13'),21.8)],
 'ceramic':[(*centre('C23'),6.25)],
 'resistor':[(*centre('R26'),3.5)],
 'power':[(*centre('J43'),9.7)],
 'input':[(*centre('J5'),9.7)],
 'fuse':[(*centre('F1'),6)],
}
bpy.context.view_layer.update()
(ROOT/'callout-projections.json').write_text(json.dumps({k:[project(p) for p in points] for k,points in targets.items()},indent=2))
# Hide the removable assembly, but keep all carrier-mounted parts and sockets.
for o in bpy.data.objects:
    n=o.name
    hidden=(n.startswith(('Teensy','Micro USB','USB to host','GM3506','Motor shaft','Motor vent','Motor encoder','Motor marking','Encoder bracket','Encoder sensor','Encoder plug','Six conductor','Phase plug','Supply cable'))
      or re.match(r'A[1-6] (SimpleFOC|male pin|driver chip|module|power [01])',n)
      or re.match(r'ENC[1-6] (JST adapter|white JST)',n)
      or re.match(r'Phase [123](\.|$)',n))
    if hidden:o.hide_render=True
if '--perspective-only' in sys.argv:
    cam=scene.camera;cam.location=(175,-120,255)
    cam.rotation_euler=(Vector((80,60,7))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=225
    bpy.context.view_layer.update()
    (ROOT/'callout-projections.json').write_text(json.dumps({k:[project(p) for p in points] for k,points in targets.items()},indent=2))
    scene.cycles.samples=32
    scene.render.filepath=str(ROOT/'carrier-soldered-perspective.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)
cam=scene.camera;cam.location=(80,60,400)
cam.rotation_euler=(Vector((80,60,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=180
scene.render.resolution_x=2400;scene.render.resolution_y=1800
scene.cycles.samples=32
scene.render.filepath=str(ROOT/'carrier-soldered-top.png')
bpy.context.view_layer.update()
(ROOT/'carrier-projections.json').write_text(json.dumps({ref:project((*centre(ref),2)) for ref in fps},indent=2))
bpy.ops.render.render(write_still=True)
