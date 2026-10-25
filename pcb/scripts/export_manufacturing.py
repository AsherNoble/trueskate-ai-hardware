#!/usr/bin/env python3
"""Export the explicitly requested current-board Gerber ZIP; never uploads/orders.

Run with ordinary Python 3.11. KiCad 10 CLI and bundled Python must be installed.
Fresh ERC/strict DRC and exact native-vs-Excellon hole checks gate the ZIP.
"""
import argparse,collections,datetime,hashlib,json,math,os,re,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KPY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
PCB=ROOT/'design/trueskate-main-v1.kicad_pcb';SCH=ROOT/'design/trueskate-main-v1.kicad_sch'
OUT=ROOT/'manufacturing';GERBERS=OUT/'gerbers';CHECKS=OUT/'validation'
STEM='trueskate-main-v1';ZIP=OUT/(STEM+'-2layer-1oz-JLCPCB.zip')
LAYERS='F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
EXPECTED_EXTENSIONS={'.gtl','.gbl','.gtp','.gbp','.gto','.gbo','.gts','.gbs','.gm1'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect_geometry():
 import pcbnew as k
 b=k.LoadBoard(str(PCB));holes=[];vias=[];edges=[]
 def xy(p):return [k.ToMM(p.x),k.ToMM(p.y)]
 for f in b.GetFootprints():
  for p in f.Pads():
   size=xy(p.GetDrillSize())
   if max(size)<=0:continue
   assert abs(size[0]-size[1])<1e-9,'Add slot validation before exporting noncircular holes'
   holes.append(dict(xy=xy(p.GetPosition()),diameter=size[0],plated=p.GetAttribute()==k.PAD_ATTRIB_PTH))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):
   holes.append(dict(xy=xy(t.GetPosition()),diameter=k.ToMM(t.GetDrillValue()),plated=True))
   vias.append(dict(xy=xy(t.GetPosition()),front_tented=t.IsTented(k.F_Cu),back_tented=t.IsTented(k.B_Cu)))
 for d in b.GetDrawings():
  if d.GetLayer()==k.Edge_Cuts:
   assert d.GetShape()==k.SHAPE_T_SEGMENT
   edges.append([xy(d.GetStart()),xy(d.GetEnd())])
 degrees=collections.Counter(tuple(p)for e in edges for p in e)
 assert len(edges)==4 and all(n==2 for n in degrees.values()),'Outline must be a closed rectangle'
 xs=[p[0]for p in degrees];ys=[p[1]for p in degrees]
 print(json.dumps(dict(layers=b.GetCopperLayerCount(),board_mm=[max(xs)-min(xs),max(ys)-min(ys)],holes=holes,vias=vias,outline=edges)))
def run(args):
 env=os.environ.copy();share='/Applications/KiCad/KiCad.app/Contents/SharedSupport'
 env.setdefault('KICAD10_FOOTPRINT_DIR',share+'/footprints');env.setdefault('KICAD10_3DMODEL_DIR',share+'/3dmodels')
 r=subprocess.run([str(a)for a in args],cwd=PCB.parent,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 print(r.stdout,flush=True);r.check_returncode()
def parse_drill(path,plated):
 tools={};tool=None;hits=[];text=path.read_text()
 assert 'METRIC' in text and ('FMAT,2'in text or 'M48'in text)
 for line in text.splitlines():
  line=line.strip()
  m=re.fullmatch(r'T(\d+)C([\d.]+)',line)
  if m:tools[m[1]]=float(m[2]);continue
  m=re.fullmatch(r'T(\d+)',line)
  if m:tool=m[1];continue
  m=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
  if m:
   assert tool in tools
   hits.append(dict(xy=[float(m[1]),-float(m[2])],diameter=tools[tool],plated=plated))
  elif line.startswith(('X','G85','G00','G01')):raise AssertionError('Unexpected slot/coordinate format: '+line)
 return hits
def main():
 source_hash=digest(PCB)
 for folder in [OUT,GERBERS,CHECKS]:folder.mkdir(exist_ok=True)
 if ZIP.exists():ZIP.unlink() # Do not leave an old upload package if checks fail.
 run([CLI,'sch','erc','--severity-all','--exit-code-violations','--format','json','--output',CHECKS/'erc.json',SCH])
 run([CLI,'pcb','drc','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','--exit-code-violations','--format','json','--output',CHECKS/'drc.json',PCB])
 erc=json.loads((CHECKS/'erc.json').read_text());drc=json.loads((CHECKS/'drc.json').read_text())
 assert not drc['ignored_checks'] and not any(drc[k]for k in ['violations','unconnected_items','schematic_parity'])
 assert not any(sheet['violations']for sheet in erc['sheets'])
 reviewed_erc=json.loads((ROOT/'review/checks/erc-review.json').read_text())
 assert erc['ignored_checks']==reviewed_erc['ignored_checks'],'ERC configuration changed since review'
 geometry=json.loads(subprocess.check_output([KPY,str(Path(__file__).resolve()),'--collect-geometry'],text=True))
 assert geometry['layers']==2 and geometry['board_mm']==[150.,140.]
 assert all(v['front_tented']and v['back_tented']for v in geometry['vias'])
 run([CLI,'pcb','export','gerbers','--layers',LAYERS,'--subtract-soldermask','--check-zones','--precision','6','--output',GERBERS,PCB])
 run([CLI,'pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-oval-format','alternate','--excellon-separate-th','--generate-report','--report-path',CHECKS/'drill-report.txt','--output',GERBERS,PCB])
 run([CLI,'pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-map','--map-format','svg','--output',CHECKS,PCB])
 drill_paths=[GERBERS/(STEM+'-PTH.drl'),GERBERS/(STEM+'-NPTH.drl')]
 actual=parse_drill(drill_paths[0],True)+parse_drill(drill_paths[1],False)
 pending=geometry['holes'][:];errors=[]
 for hit in actual:
  candidates=[(math.dist(hit['xy'],h['xy']),i)for i,h in enumerate(pending)if h['plated']==hit['plated']and abs(h['diameter']-hit['diameter'])<1e-6]
  assert candidates,'Unexpected drill tool/plating in exported file'
  error,index=min(candidates);assert error<=.00071,'Exported drill hit differs from native PCB'
  errors.append(error);pending.pop(index)
 assert not pending,'Native holes missing from export'
 files=[p for p in GERBERS.iterdir()if p.is_file()]
 assert {p.suffix for p in files}==EXPECTED_EXTENSIONS|{'.drl','.gbrjob'}
 assert len(files)==12 and all(p.stat().st_size>0 for p in files)
 for p in files:
  if p.suffix in EXPECTED_EXTENSIONS:assert '%MOMM*%'in p.read_text() and p.read_text().rstrip().endswith('M02*')
 assert digest(PCB)==source_hash,'Export must not modify native PCB'
 with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED)as z:
  for p in sorted(files):z.write(p,p.name)
 with zipfile.ZipFile(ZIP)as z:
  assert z.testzip()is None and len(z.namelist())==12 and all('/'not in n for n in z.namelist())
 revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 report=dict(exported_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=revision,source_worktree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),source_pcb=str(PCB.relative_to(ROOT)),source_pcb_sha256=source_hash,kicad_version=drc['kicad_version'],board_mm=geometry['board_mm'],layers=2,copper_oz=1,nominal_thickness_mm=1.6,erc='PASS (existing reviewed configuration)',erc_ignored_checks=erc['ignored_checks'],strict_drc='PASS (no ignored checks)',plated_holes=sum(h['plated']for h in actual),nonplated_holes=sum(not h['plated']for h in actual),native_hole_match='All hits matched; metric decimal coordinates rounded to 0.001mm by KiCad',max_drill_position_error_mm=max(errors),drill_coordinate_resolution_mm=.001,vias=len(geometry['vias']),via_tenting='front and back',drill_origin='absolute, shared with Gerbers; no mirroring',layers_exported=LAYERS.split(','),files_sha256={p.name:digest(p)for p in sorted(files)},zip_filename=ZIP.name,zip_sha256=digest(ZIP),zip_crc='PASS',uploaded=False,order_placed=False)
 (CHECKS/'native-geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 run([sys.executable,ROOT/'scripts/export_assembly.py'])
 print('Created',ZIP,flush=True);print('Drills:',report['plated_holes'],'plated,',report['nonplated_holes'],'non-plated. Source PCB unchanged.',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--collect-geometry',action='store_true');args=parser.parse_args()
 if args.collect_geometry:collect_geometry()
 else:main()
