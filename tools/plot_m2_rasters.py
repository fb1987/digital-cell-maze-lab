"""Render saved confirmation rasters, without inference or image editing."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/wave_accessibility'
x=json.loads((OUT/'raster_examples.json').read_text())
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f=lambda n,b=False:ImageFont.truetype(bold if b else font,n)
im=Image.new('RGB',(1260,660),'#f6f8fa');d=ImageDraw.Draw(im)
d.text((35,22),'A real improvement — and the boundary that remains',font=f(29,True),fill='#162d45')
d.text((35,66),'Native outputs on fresh confirmation mazes. Same first maze before and after mutation.',font=f(18),fill='#40546a')
for k,p in enumerate(x['panels']):
 ox=35+415*k;oy=160;size=17;m=p['maze'];r=p['response'];w=m['w'];cells=bytes.fromhex(m['cells_hex']);path=set(p['metadata']['path']);mask=int.from_bytes(bytes.fromhex(r['mask']),'little')
 d.text((ox,109),p['title'],font=f(22,True),fill='#162d45')
 d.text((ox,138),'Source '+str(p['metadata']['prefix'])+(' cell' if p['metadata']['prefix']==1 else ' cells')+' before the fork',font=f(16),fill='#40546a')
 for pos,v in enumerate(cells):
  px=ox+(pos%w)*size;py=oy+(pos//w)*size;on=bool(mask&(1<<pos))
  color='#25364a' if not v else '#e0e7ed'
  if on:color='#22a996' if pos in path else '#eb785e'
  d.rectangle((px,py,px+size-1,py+size-1),fill=color)
  if pos in path:d.rectangle((px+3,py+3,px+size-4,py+size-4),outline='#ffffff',width=1)
  if pos in (m['start'],m['goal']):d.text((px+3,py), 'S' if pos==m['start'] else 'G',font=f(13,True),fill='#132337')
 count=mask.bit_count();extras=sum(bool(mask&(1<<p)) for p in range(len(cells)) if p not in path)
 d.text((ox,500),('Correct shortest path' if r['optimal'] else 'Invalid: extra illuminated cells'),font=f(18,True),fill='#127966' if r['optimal'] else '#a94531')
 d.text((ox,530),f"{count} pixels emitted; {len(path)} needed; {extras} extra",font=f(16),fill='#40546a')
 d.text((ox,555),f"{r['steps']} ticks · {len(path)-1} route edges",font=f(16),fill='#40546a')
d.rectangle((35,608,51,624),fill='#22a996');d.text((61,605),'Emitted route pixels',font=f(17),fill='#40546a')
d.rectangle((285,608,301,624),fill='#eb785e');d.text((311,605),'Emitted extras',font=f(17),fill='#40546a')
d.text((505,605),'White inset: required route. S: source. G: goal.',font=f(17),fill='#40546a')
im.save(OUT/'raster_comparison.png')
