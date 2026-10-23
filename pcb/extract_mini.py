#!/usr/bin/env python3
"""Verify Mini v1.0 drills, EasyEDA connectivity and outline; no grid snapping."""
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'sources/simplefoc-mini-v1.0'
ORIGIN = (-1.143, -3.937)  # H1.9, not H1.1

def local(x, y):
    return round(x-ORIGIN[0], 6), round(ORIGIN[1]-y, 6)

def drills():
    source = (SOURCE/'Drill_PTH_Through.DRL').read_text()
    assert 'METRIC,LZ,000.000' in source and ';FILE_FORMAT=3:3' in source
    tools = {}; hits = []; tool = None
    for line in source.splitlines():
        if m := re.fullmatch(r'(T\d+)C([\d.]+)', line):
            tools[m[1]] = float(m[2])
        elif re.fullmatch(r'T\d+', line): tool = line
        elif m := re.fullmatch(r'X(-?\d+)Y(-?\d+)', line):
            x,y = int(m[1])/1000, int(m[2])/1000
            hits.append(dict(x_mm=local(x,y)[0],y_mm=local(x,y)[1],drill_mm=tools[tool],tool=tool))
    return hits

def outline():
    """Read this tag's Gerber 4:5 line/CCW-arc outline, including scalloped ears."""
    text = (SOURCE/'Gerber_BoardOutlineLayer.GKO').read_text()
    assert '%FSLAX45Y45*%' in text and '%MOMM*%' in text
    mode = 'G01'; start = None; paths = []
    for line in text.splitlines():
        if line in ('G01*','G03*'): mode=line[:3]
        m=re.fullmatch(r'X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D(0[12])\*',line)
        if not m: continue
        end=(int(m[1])/1e5,int(m[2])/1e5)
        if m[5]=='01':
            if mode=='G03':
                cx,cy=start[0]+int(m[3])/1e5,start[1]+int(m[4])/1e5
                r=math.hypot(start[0]-cx,start[1]-cy)
                a=math.atan2(start[1]-cy,start[0]-cx)
                sweep=(math.atan2(end[1]-cy,end[0]-cx)-a)%(2*math.pi)
                path=[local(cx+r*math.cos(a+sweep*i/256),cy+r*math.sin(a+sweep*i/256)) for i in range(257)]
                path[0]=local(*start);path[-1]=local(*end)
            else:path=[local(*start),local(*end)]
            paths.append(path)
        start=end
    assert len(paths)==12
    return paths

def schematic_pins():
    shapes=json.loads((SOURCE/'SCH_simplefocmini_2022-04-20.json').read_text())['schematics'][0]['dataStr']['shape']
    pins={};wires=[];labels=[]
    for shape in shapes:
        if shape.startswith('LIB~'):
            chunks=shape.split('#@$')
            ref=next(x.split('~')[12] for x in chunks if x.startswith('T~P~'))
            for p in chunks:
                if not p.startswith('P~'):continue
                f=p.split('^^')[0].split('~')
                pins[ref+'.'+f[3]]=(float(f[4]),float(f[5]))
        elif shape.startswith('W~'):
            f=list(map(float,shape.split('~')[1].split()));pts=list(zip(f[::2],f[1::2]));wires.extend(zip(pts,pts[1:]))
        elif shape.startswith('F~'):
            f=shape.split('^^');xy=f[1].split('~');labels.append(((float(xy[0]),float(xy[1])),f[2].split('~')[0]))
    points=set(pins.values())|{p for w in wires for p in w}|{p for p,_ in labels}
    parent={p:p for p in points}
    def find(p):
        if parent[p]!=p:parent[p]=find(parent[p])
        return parent[p]
    def union(a,b):parent[find(a)]=find(b)
    for a,b in wires:
        for p in points:
            cross=(p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0])
            if abs(cross)<1e-8 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]):union(a,p)
    named={}
    for p,name in labels:
        if name in named:union(p,named[name])
        named[name]=p
    def connected(a,b):return find(pins[a])==find(pins[b] if b in pins else named[b])
    expected={'1':'GND','2':'3.3V','3':'U1.27','4':'GND','5':'U1.25','6':'nRes','7':'U1.23','8':'nSlp','9':'R4.2','10':'nFlt'}
    for pin,target in expected.items():assert connected('H1.'+pin,target),(pin,target)
    for pin in ('22','24','26'):assert connected('R4.1','U1.'+pin)
    for pin,target in {'1':'U1.9','2':'U1.8','3':'U1.5'}.items():assert connected('P1.'+pin,target)
    return expected

def extract():
    manifest=json.loads((SOURCE/'provenance.json').read_text())
    for name,digest in manifest['sha256'].items():assert hashlib.sha256((SOURCE/Path(name).name).read_bytes()).hexdigest()==digest
    schematic_pins()
    hits=drills();selected=[h for h in hits if h['tool'] in ('T03','T04')]
    assert len(selected)==15
    expected={(round(x,3),y) for x in (0,2.54,5.08,7.62,10.16) for y in (0,2.54)}
    expected|={(x,17.653) for x in (3.556,6.096,8.636)}|{(17.399,3.810),(17.399,8.763)}
    assert {(p['x_mm'],p['y_mm']) for p in selected}==expected
    pcb=json.loads((SOURCE/'PCB_simplefocmini_2022-04-20.json').read_text())
    connectors={'control':[],'phase':[],'power':[]}
    for shape in pcb['shape']:
        if shape.startswith('LIB~'):
            chunks=shape.split('#@$')
            group='control' if 'package`HDR-TH_10P' in chunks[0] else 'phase' if 'package`HDR-TH_3P' in chunks[0] else None
            if not group:continue
            pads=[p for p in chunks if p.startswith('PAD~')]
        elif shape.startswith('PAD~') and shape.split('~')[8] in ('2','3'):
            group='power';pads=[shape]
        else:continue
        for pad in pads:
            f=pad.split('~');x=round((float(f[2])-4089.5)*.254,6);y=round((float(f[3])-3046)*.254,6)
            hit=next(h for h in selected if math.hypot(h['x_mm']-x,h['y_mm']-y)<.002)
            pin=f[8] if group!='power' else {'GND':'GND','VCC':'VIN'}[f[7]]
            connectors[group].append(dict(pin=pin,upstream_net=f[7],x_mm=hit['x_mm'],y_mm=hit['y_mm'],drill_mm=hit['drill_mm']))
    for group in ('control','phase'):connectors[group].sort(key=lambda p:int(p['pin']))
    paths=outline();points=[p for path in paths for p in path]
    bounds=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
    result=dict(units='mm',view='top/component side; +X right, +Y toward phases; NOT mirrored',origin='H1 pin 9 / drill (-1.143, -3.937)',connectors=connectors,power_pitch_mm=4.953,outline_paths=paths,outline_bounds_mm=bounds,courtyard_bounds_mm=[round(bounds[0]-.25,3),round(bounds[1]-.25,3),round(bounds[2]+.25,3),round(bounds[3]+.25,3)],control_net_mismatches=[])
    (ROOT/'sources/mini-geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='outline_paths'},indent=2))
    return result

if __name__=='__main__':extract()
