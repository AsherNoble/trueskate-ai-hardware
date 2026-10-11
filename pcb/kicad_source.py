"""Native schematic/project emitter for the passive carrier."""
import json
import math
def q(s): return json.dumps(str(s))
def eff(size=1,extra=""): return f'(effects (font (size {size} {size})) {extra})'
def symbol(p):
    rows=math.ceil(len(p["pins"])/2);height=max(5.08,(rows+1)*2.54);name=p["ref"]
    s=f'(symbol "TrueSkate:{name}" (pin_names (offset .508)) (in_bom yes) (on_board yes) '
    for key,val,y in [("Reference",name,-height/2-2.54),("Value",p["value"],height/2+2.54),("Footprint",p["fp"],0)]:
        s+=f'(property {q(key)} {q(val)} (at 0 {y} 0) {eff(1.27,"(hide yes)" if key=="Footprint" else "")}) '
    s+=f'(symbol "{name}_0_1" (rectangle (start -10.16 {height/2}) (end 10.16 {-height/2}) (stroke (width .254) (type default)) (fill (type background)))) (symbol "{name}_1_1" '
    for i,num in enumerate(p["pins"]):
        right=i>=rows;idx=i-rows if right else i;y=(rows-1)*1.27-idx*2.54;x=15.24 if right else -15.24
        pname=p["note"].split("Physical pin legend: ")[-1].split(",")[i] if name in ("J1","J2") else num
        s+=f'(pin passive line (at {x} {y} {180 if right else 0}) (length 5.08) (name {q(pname)} {eff(1.27)}) (number {q(num)} {eff(1.27)})) '
    return s+'))',height
def write_schematic(root,project,parts,pages,uid):
    lib=['(kicad_symbol_lib (version 20250114) (generator "trueskate")']
    lib += [symbol(p)[0].replace('"TrueSkate:'+p["ref"]+'"','"'+p["ref"]+'"',1) for p in parts]
    (root/"TrueSkate.kicad_sym").write_text("\n".join(lib)+")\n")
    for pg,data in pages.items():
        s=f'(kicad_sch (version 20250114) (generator "trueskate") (uuid {uid(pg)}) (paper "A4" portrait) (title_block (title {q(data["title"])}) (rev "v1 REVIEW")) (lib_symbols '
        s+=" ".join(symbol(p)[0] for p in data["parts"])+')\n'
        for p in data["parts"]:
            sx,sy=p['sch'];sx=sx-45 if sx>=150 else sx
            x,y=[round(v/1.27)*1.27 for v in (sx,sy)];rows=math.ceil(len(p["pins"])/2);height=symbol(p)[1]
            s+=f'(symbol (lib_id "TrueSkate:{p["ref"]}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(p["ref"])}) '
            for key,val,py,hide in [("Reference",p["ref"],y-height/2-2.54,False),("Value",p["value"],y+height/2+2.54,False),("Footprint",p["fp"],y,True)]:
                s+=f'(property {q(key)} {q(val)} (at {x} {py} 0) {eff(1.27,"(hide yes)" if hide else "")}) '
            for pin in p["pins"]: s+=f'(pin {q(pin)} (uuid {uid(p["ref"]+"-"+pin)})) '
            s+=f'(instances (project "{project}" (path "/{uid("root")}/{uid("sheet-"+pg)}" (reference {q(p["ref"])}) (unit 1)))))\n'
            for i,net in enumerate(p["nets"]):
                right=i>=rows;idx=i-rows if right else i;px=x+(15.24 if right else -15.24);py=y-((rows-1)*1.27-idx*2.54)
                if net:
                    end=px+(3.81 if right else -3.81)
                    s+=f'(wire (pts (xy {px} {py}) (xy {end} {py})) (stroke (width 0) (type default)) (uuid {uid(p["ref"]+"w"+str(i))})) '
                    s+=f'(global_label {q(net)} (shape bidirectional) (at {end} {py} {0 if right else 180}) {eff(1.27,"(justify left)" if right else "(justify right)")} (uuid {uid(p["ref"]+"l"+str(i))}))\n'
                else: s+=f'(no_connect (at {px} {py}) (uuid {uid(p["ref"]+"nc"+str(i))}))\n'
        for n,note in enumerate(data["notes"]): s+=f'(text {q(note)} (at 15 {15+n*3.5} 0) {eff(1.27,"(justify left)")} (uuid {uid(pg+"note"+str(n))})) '
        (root/(pg+".kicad_sch")).write_text(s+")\n")
    s=f'(kicad_sch (version 20250114) (generator "trueskate") (uuid {uid("root")}) (paper "A3") (title_block (title "TrueSkate USB-powered six-axis carrier") (rev "v1 REVIEW")) (lib_symbols) '
    for i,(pg,data) in enumerate(pages.items()):
        x=15+(i%3)*130;y=50+(i//3)*55
        s+=f'(sheet (at {x} {y}) (size 115 35) (stroke (width .254) (type default)) (fill (color 0 0 0 0)) (uuid {uid("sheet-"+pg)}) '
        s+=f'(property "Sheetname" {q(data["title"])} (at {x} {y-1.27} 0) {eff(1,"(justify left bottom)")}) '
        s+=f'(property "Sheetfile" "{pg}.kicad_sch" (at {x} {y+36.27} 0) {eff(1,"(justify left top)")}) '
        s+=f'(instances (project "{project}" (path "/{uid("root")}" (page "{i+2}"))))) '
    notes=["REVIEW PACKAGE - STOP BEFORE MANUFACTURING EXPORTS","USB-powered Teensy / six socketed Minis / through-hole assembly / fused 12V motor power","Identical global labels are the same connection. All components are passive carrier connections.","User confirmed Mini fit, encoder contact 1 and 160 x 120 mm base fit. Human review before ordering."]
    for n,note in enumerate(notes): s+=f'(text {q(note)} (at 15 {15+n*5} 0) {eff(1.2,"(justify left)")} (uuid {uid("root-note"+str(n))})) '
    (root/(project+".kicad_sch")).write_text(s+f'(sheet_instances (path "/" (page "1"))))\n')
def write_project(root,project,parts):
    rules=dict(min_clearance=.2,min_track_width=.2,min_via_diameter=.7,min_through_hole_diameter=.3,
               min_via_annular_width=.2,min_copper_edge_clearance=.5,min_hole_clearance=.45,
               min_hole_to_hole=.45,min_silk_clearance=.15,
               min_text_height=1,min_text_thickness=.15)
    nc=dict(name="Default",clearance=.2,track_width=.25,via_diameter=.7,via_drill=.3,
            microvia_diameter=.3,microvia_drill=.1,diff_pair_width=.25,diff_pair_gap=.25,diff_pair_via_gap=.25)
    # Explicit current schema versions prevent KiCad's legacy migrations from
    # replacing these conservative rules with application defaults.
    severities={name:'warning' for name in ['missing_courtyard','track_not_centered_on_via',
        'tuning_profile_track_geometries','footprint_filters_mismatch','footprint_type_mismatch']}
    data=dict(meta=dict(filename=project+".kicad_pro",version=3),
              board=dict(design_settings=dict(meta=dict(version=2),rules=rules,
                  rule_severities=severities,drc_exclusions=[])),
              net_settings=dict(meta=dict(version=5),classes=[nc]))
    (root/(project+".kicad_pro")).write_text(json.dumps(data,indent=2)+"\n")
    (root/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "TrueSkate") (type "KiCad") (uri "${KIPRJMOD}/TrueSkate.kicad_sym") (options "") (descr "Passive carrier symbols")))\n')
    libs=sorted({p["fp"].split(":")[0] for p in parts}|{"MountingHole"});s='(fp_lib_table (version 7) '
    for name in libs:
        uri="${KIPRJMOD}/TrueSkate.pretty" if name=="TrueSkate" else "${KICAD10_FOOTPRINT_DIR}/"+name+".pretty"
        s+=f'(lib (name {q(name)}) (type "KiCad") (uri {q(uri)}) (options "") (descr "")) '
    (root/"fp-lib-table").write_text(s+")\n")
