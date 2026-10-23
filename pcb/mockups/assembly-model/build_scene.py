"""Deterministic simplified assembly, built in Blender from KiCad pad coordinates.
Run with Blender --background --python /absolute/path/build_scene.py.
Units in geometry are mm. Plug-in module bodies and motor are representative.
"""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'board-geometry.json').read_text())
FP = {f['ref']: f for f in DATA['footprints']}
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, metallic=0, roughness=.45):
    m = bpy.data.materials.new(name); m.diffuse_color=(*color,1)
    m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Roughness'].default_value=roughness
    return m

green=material('Carrier green',(.035,.19,.12))
module=material('Mini PCB blue',(.025,.12,.24))
teensy=material('Teensy PCB',(.035,.29,.18))
black=material('Header plastic',(.018,.023,.028))
metal=material('Tin and aluminium',(.65,.70,.74),.7,.28)
gold=material('Contacts',(.65,.44,.13),.7)
blue=material('Capacitor sleeves',(.025,.12,.31),.15)
terminal_green=material('Terminal blocks',(.10,.40,.22))
white=material('White markings',(.86,.90,.88))
red=material('12V positive',(.65,.035,.025))
orange=material('Motor phases',(.93,.29,.035))
cyan=material('Encoder harness',(.02,.43,.58))
beige=material('Resistor bodies',(.62,.49,.28))
copper=material('Copper under mask',(.07,.25,.16),.25)
ground=material('Backdrop',(.82,.85,.87))

def v(p): return Vector((p[0],120-p[1],p[2]))
def finish(o,name,mat):
    o.name=name; o.data.materials.append(mat); return o
def box(name,p,size,mat,bevel=.25):
    bpy.ops.mesh.primitive_cube_add(size=1,location=v(p)); o=bpy.context.object
    o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,mat)
    if bevel:
        m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=2
        o.modifiers.new('Normals','WEIGHTED_NORMAL')
    return o
def cylinder(name,p,r,depth,mat,vertices=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=v(p))
    o=finish(bpy.context.object,name,mat)
    m=o.modifiers.new('Edge bevel','BEVEL');m.width=.15;m.segments=2
    o.modifiers.new('Normals','WEIGHTED_NORMAL'); return o
def segment(name,a,b,r,mat):
    mid=(Vector(a)+Vector(b))/2
    o=cylinder(name,mid,r,(v(b)-v(a)).length,mat,16)
    o.rotation_euler=(v(b)-v(a)).to_track_quat('Z','Y').to_euler(); return o
def cable(name,points,r,mat):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=24
    c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):
        p.co=v(co);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);finish(o,name,mat)
    return o
def text(name,body,p,size=2,mat=white):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.align_x='CENTER';c.extrude=.008
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.location=v(p)
    c.materials.append(mat);return o
def pad(ref,num): return next(a['xy'] for a in FP[ref]['pads'] if a['number']==str(num))
def sockets(ref):
    for a in FP[ref]['pads']:
        x,y=a['xy'];box(ref+' socket',(x,y,5.7),(2.5,2.5,8.2),black,.12)
        box(ref+' recess',(x,y,9.82),(1.05,1.05,.08),gold,.06)
        box(ref+' aperture',(x,y,9.89),(.65,.65,.08),black,.03)
def terminal(name,x,y,z=1.6,pitch=3.81):
    box(name,(x+pitch/2,y,z+4),(pitch+4,7,8),terminal_green,.5)
    for dx in (0,pitch):
        cylinder(name+' screw',(x+dx,y,z+8.03),1.1,.3,metal,24)
        box(name+' screw slot',(x+dx,y,z+8.22),(1.55,.22,.12),black,.02)
        box(name+' wire entry',(x+dx,y+3.55,z+2.8),(2, .13,2.3),black,.1)

# Carrier and the actual surface copper centre-lines.
board=box('Carrier 160 x 120 x 1.6 mm',(80,60,.8),(160,120,1.6),green,.35)
for t in DATA['tracks']:
    o=segment('Top copper',(*t['start'],1.62),(*t['end'],1.62),t['width']/2,copper)
    o.matrix_world=Matrix.Translation((0,0,1.64)) @ Matrix.Diagonal((1,1,.01,1)) @ o.matrix_world
for f in DATA['footprints']:
    for a in f['pads']:
        x,y=a['xy']; d=max(a['size'])
        if a['drill'][0] and not f['ref'].startswith('H'):
            cylinder(f['ref']+' land',(x,y,1.68),d/2,.12,gold,16)
            cylinder('Drill indication',(x,y,1.76),a['drill'][0]/2,.03,black,16)
for x,y in [(5,5),(155,5),(155,115),(5,115)]:
    cylinder('Nylon spacer',(x,y,-3.5),3,7,white)
    cylinder('Nylon screw',(x,y,2.5),2.8,1.8,white)
    box('Screw slot',(x,y,3.43),(3.5,.6,.1),black,.1)

# Socketed Teensy; real two 24-contact rows, body dimensions simplified.
for ref in ['J1','J2']: sockets(ref)
box('Teensy 4.1',(73.2,67.62,11.4),(61,18,1.6),teensy)
for ref in ['J1','J2']:
    for a in FP[ref]['pads']:
        x,y=a['xy'];box('Teensy pin',(x,y,10.4),(.64,.64,3.3),gold,.03)
        cylinder('Teensy pin solder',(x,y,12.3),.8,.18,metal,16)
box('Teensy processor',(73,67.6,13.2),(9,9,1.9),black)
box('Teensy SD socket',(99,67.6,13.2),(8,11,2.1),metal)
box('Micro USB socket',(44,67.6,13.2),(5,7.5,2.7),metal)
box('Micro USB inserted plug',(38.2,67.6,13.2),(7,6,3.2),black)
cable('USB to host',[(35,67.6,13.2),(24,67.6,13.2),(-2,61,10),(-35,64,0)],1.5,black)
text('Teensy label','TEENSY 4.1',(69,71.5,12.35),1.8)

# Six modules, real socket positions, conceptual module bodies.
for i in range(1,7):
    ref=f'J{10+i}'; sockets(ref)
    col=(i-1)%3;top=i<=3;x=35+43*col;y=30 if top else 92
    cx=x+5 if top else x-5; cy=y-8.8 if top else y+8.8
    box(f'A{i} SimpleFOC Mini',(cx,cy,11.4),(24,24,1.6),module)
    for a in FP[ref]['pads']:
        px,py=a['xy'];box(f'A{i} male pin',(px,py,10.5),(.64,.64,3.4),gold,.03)
    box(f'A{i} driver chip',(cx-3,cy,13.2),(7,7,2),black)
    cylinder(f'A{i} module capacitor',(cx+6,cy-5 if top else cy+5,16),3.2,7.6,metal)
    text(f'A{i} module label',f'MINI {i}',(cx-2,cy+7,12.3),2)
    tx=cx+7;ty=cy+4 if top else cy-5
    terminal(f'A{i} module power',tx,ty,12.2,2.54)
    power=FP[f'J{40+i}']['xy'];terminal(f'A{i} carrier power',*power)
    for j,mat in enumerate([red,black]):
        sx=power[0]+j*3.81;sy=power[1]+3.6;ex=tx+j*2.54;ey=ty+3.6
        cable(f'A{i} power {j}',[(sx,sy,4.4),(sx,sy+3,12),(ex+2,ey+4,20),(ex,ey,15)],.55,mat)
    # Large local capacitor, measured package.
    a,b=FP[f'C{10+i}']['pads'];px=(a['xy'][0]+b['xy'][0])/2;py=a['xy'][1]
    cylinder(f'C{10+i} 1000uF',(px,py,11.6),6.25,20,blue)
    cylinder('Capacitor top',(px,py,21.65),5.7,.2,metal)
    box('Capacitor vent',(px,py,21.8),(7,.15,.05),black,.02)
    box('Capacitor vent',(px,py,21.8),(.15,7,.05),black,.02)
    # Through-hole resistor and ceramic, at extracted pad positions.
    ra,rb=FP[f'R{20+i}']['pads'];p=ra['xy'];q=rb['xy']
    segment('Resistor lead',(*p,2.7),(*q,2.7),.25,metal)
    segment('10k resistor',(p[0]+1,p[1],2.7),(q[0]-1,q[1],2.7),1,beige)
    p=FP[f'C{20+i}']['xy'];box('100nF ceramic',(p[0]+2.5,p[1],4),(5,2,4.5),beige)
    # Motor phase header.
    for a in FP[f'J{20+i}']['pads']:
        px,py=a['xy'];box('Phase header',(px,py,2.85),(2.5,2.5,2.5),black,.1)
        box('Phase pin',(px,py,6.3),(.64,.64,5),gold,.02)
    # Six-pin encoder adapter seated horizontally above its female socket.
    sockets(f'J{30+i}')
    points=FP[f'J{30+i}']['pads'];ex=sum(a['xy'][0] for a in points)/6;ey=points[0]['xy'][1]
    box(f'ENC{i} JST adapter',(ex,ey,11.1),(16,7,1.2),module)
    box(f'ENC{i} white JST',(ex,ey,13.7),(10,5,4),white)
    text(f'Encoder label',f'ENC {i}',(ex,ey+6,1.9),1.7)
    text(f'Axis label',f'AXIS {i}',(cx,cy+16 if top else cy-15,1.9),2.3)

terminal('12 V input',*FP['J5']['xy'],pitch=5.08)
for j,mat in enumerate([red,black]):
    sx=7+j*5.08
    cable('Supply cable',[(sx,72.6,4.4),(sx,84,7),(-9,93+j*3,2),(-36,94+j*3,0)],.9,mat)
# Fuse positioned along its actual two contact centres.
f=FP['F1']['pads'];a=f[0]['xy'];b=f[1]['xy']
box('Fuse holder',(8,(a[1]+b[1])/2,3),(8,29,3),black)
segment('Fuse body',(*a,6),(*b,6),2.5,white)
for q in [a,b]: cylinder('Fuse clip',(*q,6),3,1,metal)
text('Input label','12 V',(11,81,1.9),2.3)
text('Board title','TRUESKATE / SIX-AXIS CARRIER',(89,2.8,1.9),2.4)

# Representative low-profile GM3506; encoder concentric with motor shaft.
mx,my=-34,-13
cylinder('GM3506 stator',(mx,my,6),20.5,12,black,64)
cylinder('GM3506 rotor',(mx,my,15),21,7,metal,64)
cylinder('GM3506 top',(mx,my,19),20,1.3,black,64)
cylinder('Motor shaft',(mx,my,24),3,9,metal)
for n in range(12):
    a=n*math.tau/12
    cylinder('Motor vent',(mx+14*math.cos(a),my+14*math.sin(a),19.8),2.2,.2,copper,16)
for dx in [-9,9]:cylinder('Encoder bracket post',(mx+dx,my,26),1.2,12,white)
box('Encoder bracket',(mx,my,32),(23,12,1.5),black)
box('Motor encoder PCB',(mx,my,33.3),(17,10,1),module)
box('Encoder sensor',(mx,my,34.5),(5,5,1.2),black)
box('Motor encoder JST',(mx+6,my,35),(4,8,3),white)
text('Motor marking','GM3506',(mx,my+9,20),2.6,white)

# One motor only: three individually modelled phase wires and separate encoder loom.
for j,a in enumerate(FP['J21']['pads']):
    px,py=a['xy'];box('Phase plug',(px,py,8.5),(2.5,2.5,5),black,.2)
    cable(f'Phase {j+1}',[(px,py,11),(px,py-10,21),(14,-29-j*2,17),(-12,-28-j*2,9),(mx+15,my-5+j*2,6)],.65,orange)
ex=sum(a['xy'][0] for a in FP['J31']['pads'])/6;ey=FP['J31']['pads'][0]['xy'][1]
box('Encoder plug',(ex,ey-3,13.7),(10,4,3.5),white)
cable('Six conductor encoder harness',[(ex,ey-5,14),(24,39,16),(20,10,25),(-9,0,34),(mx+9,my,35)],1,cyan)

# Stage, camera and light. CPU Cycles works without a GUI/GPU session.
box('Ground',(48,52,-8),(600,500,1),ground,0)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
scene.unit_settings.length_unit='MILLIMETERS'
scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
scene.world.color=(.6,.6,.6)
scene.view_settings.view_transform='AgX'
for name,p,power,size in [('Key',(-80,-70,260),1900000,170),('Fill',(220,60,170),1100000,130)]:
    bpy.ops.object.light_add(type='AREA',location=v(p));o=bpy.context.object;o.name=name
    o.data.energy=power;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(v((65,55,0))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
def view(p,target,scale,path):
    cam.location=v(p);cam.rotation_euler=(v(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale;cam.data.clip_end=2000
    scene.render.filepath=str(ROOT/path)
view((175,240,255),(53,48,7),285,'assembly-perspective.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'trueskate-assembly.blend'))
bpy.ops.render.render(write_still=True)
view((53,48,400),(53,48,0),252,'assembly-top.png')
bpy.ops.render.render(write_still=True)
print('Saved Blender model and two renders in',ROOT)
