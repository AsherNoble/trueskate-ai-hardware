#!/usr/bin/env python3
"""Independent native-footprint/drill overlay and all-six-instance fit check.

Run with Python 3.11 (matplotlib). KiCad's Python reads actual library/board pads.
No manufacturing files are generated.
"""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from extract_mini import drills, outline, schematic_pins

ROOT=Path(__file__).resolve().parents[1]
KPY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'

def collect():
    import pcbnew as k
    fp=k.FootprintLoad(str(ROOT/'design/TrueSkate.pretty'),'SimpleFOC_Mini_v1.0')
    b=k.LoadBoard(str(ROOT/'design/trueskate-main-v1.kicad_pcb'))
    def pads(f):
        return [dict(pin=p.GetNumber(),x_mm=k.ToMM(p.GetPosition().x),y_mm=k.ToMM(p.GetPosition().y),drill_mm=k.ToMM(p.GetDrillSize().x),net=p.GetNetname()) for p in f.Pads()]
    result={'library':pads(fp),'instances':{f.GetReference():dict(flipped=f.IsFlipped(),angle=f.GetOrientationDegrees(),x=k.ToMM(f.GetPosition().x),y=k.ToMM(f.GetPosition().y),pads=pads(f)) for f in b.GetFootprints() if f.GetReference() in {f'J{i}' for i in range(11,17)}}}
    print(json.dumps(result))

def main():
    result=subprocess.run([KPY,str(Path(__file__).resolve()),'--collect'],check=True,text=True,capture_output=True)
    actual=json.loads(result.stdout)
    hits=drills();contacts=[h for h in hits if h['tool'] in ('T03','T04')]
    assert len(actual['library'])==len(contacts)==15
    # Pin labels are independently fixed by the upstream H1/P1 pad/net audit.
    pin_at={(0,0):'9',(0,2.54):'10',(2.54,0):'7',(2.54,2.54):'8',(5.08,0):'5',(5.08,2.54):'6',(7.62,0):'3',(7.62,2.54):'4',(10.16,0):'1',(10.16,2.54):'2',(3.556,17.653):'P3',(6.096,17.653):'P2',(8.636,17.653):'P1',(17.399,3.810):'GND',(17.399,8.763):'VIN'}
    reference={pin_at[(p['x_mm'],p['y_mm'])]:p for p in contacts}
    errors=[]
    def check(ref,p,x,y):
        q=reference[p['pin']];e=math.hypot(x-q['x_mm'],y-q['y_mm'])
        assert abs(p['drill_mm']-q['drill_mm'])<.00001,(ref,p)
        assert e<.05,(ref,p['pin'],e)
        errors.append(dict(reference=ref,pad=p['pin'],position_error_mm=round(e,9)))
    assert {p['pin'] for p in actual['library']}==set(reference)
    mismatches=[]
    for p in actual['library']:check('library',p,p['x_mm'],p['y_mm'])
    assert set(actual['instances'])=={f'J{i}' for i in range(11,17)}
    for ref,f in actual['instances'].items():
        assert len(f['pads'])==15 and {p['pin'] for p in f['pads']}==set(reference)
        assert not f['flipped'],ref
        i=int(ref[1:])-10
        expected={'1':'GND','2':None,'3':f'A{i}_PWM1','4':'GND',
                  '5':f'A{i}_PWM2','6':None,'7':f'A{i}_PWM3','8':None,
                  '9':f'A{i}_EN','10':None,'P1':f'A{i}_PH3','P2':f'A{i}_PH2',
                  'P3':f'A{i}_PH1','VIN':'12V_FUSED','GND':'GND'}
        for p in f['pads']:
            net=None if p['net'].startswith('unconnected-') else p['net']
            if net!=expected[p['pin']]:mismatches.append(dict(reference=ref,pad=p['pin'],expected=expected[p['pin']],actual=net))
        theta=math.radians(f['angle']);c,s=math.cos(theta),math.sin(theta)
        for p in f['pads']:
            dx,dy=p['x_mm']-f['x'],p['y_mm']-f['y']
            check(ref,p,c*dx-s*dy,s*dx+c*dy)
    schematic_pins()
    maxerror=max(p['position_error_mm'] for p in errors)
    report=dict(source_tag='v1.0',source_commit='848e8ece46d045ac24283e2d6ee9ea4ba8ef95d5',contacts_per_footprint=15,instances_checked=6,max_position_error_mm=maxerror,tolerance_mm=.05,drill_diameters_mm=[1.101,1.021],control_net_mismatches=[m for m in mismatches if m["pad"].isdigit()],all_net_mismatches=mismatches,measurements=errors)
    (ROOT/'review/checks/mini-fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not mismatches,mismatches
    if '--checks-only' in sys.argv:
        print(f'PASS: 105 Mini contacts; max drill position error {maxerror:.6f} mm')
        return
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/trueskate-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    fig,ax=plt.subplots(figsize=(11,9))
    for path in outline():ax.plot([p[0] for p in path],[p[1] for p in path],color='#777777',lw=1)
    for p in hits:ax.add_patch(Circle((p['x_mm'],p['y_mm']),p['drill_mm']/2,facecolor='none',edgecolor='#b8b8b8',lw=.8))
    ax.scatter([p['x_mm'] for p in contacts],[p['y_mm'] for p in contacts],s=95,facecolors='none',edgecolors='#0072B2',linewidths=1.7,label='Upstream drill centres (15 contacts)')
    ax.scatter([p['x_mm'] for p in actual['library']],[p['y_mm'] for p in actual['library']],s=60,marker='+',color='#D55E00',linewidths=1.4,label='KiCad footprint centres')
    for p in actual['library']:
        name=('H1.'+p['pin']) if p['pin'].isdigit() else p['pin']
        ax.annotate(name,(p['x_mm'],p['y_mm']),xytext=(0,-15),textcoords='offset points',ha='center',fontsize=9)
    ax.set_aspect('equal');ax.set_xlim(-7,24);ax.set_ylim(21,-4)
    ax.set_xlabel('X (mm), right from H1.9');ax.set_ylabel('Y (mm), toward phase header')
    ax.set_title(f'SimpleFOC Mini v1.0 — 15/15 drill centres match\nMaximum position error: {maxerror:.6f} mm (< 0.05 mm)',fontsize=15,pad=15)
    ax.grid(alpha=.18);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.10),ncol=2,frameon=False)
    fig.text(.5,.025,'Top view • component side up, pins down • NOT mirrored • grey: full upstream drills and GKO outline',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.06,1,1))
    fig.savefig(ROOT/'review/drawings/mini-drill-overlay.png',dpi=180)
    fig.savefig(ROOT/'review/drawings/mini-drill-overlay.svg')
    print(f'PASS: library + 6 placed footprints, 105 contacts checked, max position error {maxerror:.6f} mm')

if __name__=='__main__':
    collect() if '--collect' in sys.argv else main()
