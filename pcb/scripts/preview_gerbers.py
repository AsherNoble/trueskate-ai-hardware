from pathlib import Path
import json,warnings,xml.etree.ElementTree as ET
from gerbonara import LayerStack
import cairosvg
root=Path(__file__).resolve().parents[1]/'manufacturing'
out=root/'preview';out.mkdir(exist_ok=True)
with warnings.catch_warnings(record=True)as records:
 warnings.simplefilter('always');stack=LayerStack.open(root/'gerbers')
expected={('top','copper'),('bottom','copper'),('top','mask'),('bottom','mask'),('top','silk'),('bottom','silk'),('top','paste'),('bottom','paste'),('mechanical','outline')}
assert set(stack.graphic_layers)==expected
for side in ['top','bottom']:
 colors={side+' copper':'#28644e',side+' silk':'#2967c9','mechanical outline':'#111111','drill pth':'#ffffff','drill npth':'#dc2626'}
 svg=str(stack.to_svg(side_re=side+'|mechanical',margin=2,colors=colors))
 tree=ET.fromstring(svg)
 groups=[e for e in tree if e.tag.endswith('g')and e.get('id','').startswith('l-')]
 for e in groups:tree.remove(e)
 def priority(e):
  n=e.get('id','')
  return 0 if n.endswith('-copper')else 1 if n.endswith('-silk')else 2 if n.endswith('-outline')else 3
 for e in sorted(groups,key=priority):tree.append(e)
 svg=ET.tostring(tree,encoding='unicode')
 (out/(side+'.svg')).write_text(svg)
 cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out/(side+'.png')),output_width=2000)
bounds=stack.graphic_layers[('mechanical','outline')].bounding_box()
assert abs(bounds[0][0]+.025)<1e-6 and abs(bounds[0][1]+140.025)<1e-6
assert abs(bounds[1][0]-150.025)<1e-6 and abs(bounds[1][1]-.025)<1e-6
report=dict(parser='Gerbonara',layers=[list(k)for k in sorted(stack.graphic_layers)],plated_drill_hits=len(stack.drill_pth.objects),nonplated_drill_hits=len(stack.drill_npth.objects),outline_bounds_mm_including_0_05mm_plot_stroke=bounds,previews_from='exported copper, silkscreen, outline and Excellon; both copper sides viewed from top. Solder mask not shown in these unmasked-copper checks',parser_warnings=[str(w.message)for w in records],note='The G90-after-header warnings concern KiCad command placement; parser successfully reads the absolute-coordinate drill files.')
(root/'validation/gerber-viewer-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('Rendered exported top/bottom layers, all 9 expected Gerber layers and both drill files parsed.')
