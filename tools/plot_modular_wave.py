"""Raster diagram from saved M1 development outputs. No inference or output repair."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];out=root/'results/modular_pilot';x=json.loads((out/'development_032_examples.json').read_text())
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def f(size,strong=False):return ImageFont.truetype(bold if strong else font,size)
im=Image.new('RGB',(1440,740),'#fafaf7');d=ImageDraw.Draw(im)
d.text((48,30),'An evolved wave explores—but emits the explored region',font=f(32,True),fill='#152c38')
d.text((48,82),'One random-origin modular descendant at round 32. Saved development outputs; no repaired paths.',font=f(22),fill='#49545b')
for index,e in enumerate(e for e in x['examples'] if e['metadata']['prefix'] in (0,1,4)):
 m=e['maze'];meta=e['metadata'];r=e['response'];n=m['w'];cells=list(bytes.fromhex(m['cells_hex']));raw=bytes.fromhex(r['mask']);mask={p for p in range(len(cells)) if raw[p//8]>>(p%8)&1};path=set(meta['path']);left=48+index*466;top=180;size=22
 d.text((left,136),f'Prefix {meta["prefix"]}: '+('correct path' if r['optimal'] else 'extra branches'),font=f(25,True),fill='#152c38')
 for p,cell in enumerate(cells):
  color='#dce0df' if not cell else '#ffffff'
  if p in path and p in mask:color='#287c9a'
  elif p in mask:color='#df6b57'
  elif p in path:color='#aad9b5'
  xx=left+p%n*size;yy=top+p//n*size;d.rectangle((xx,yy,xx+size-1,yy+size-1),fill=color)
 for p,label in ((m['start'],'S'),(m['goal'],'G')):d.text((left+p%n*size+size/2,top+p//n*size+size/2),label,anchor='mm',font=f(16,True),fill='#0a141a')
 d.text((left,615),f'{r["steps"]} ticks · {len(mask)} lit cells · {len(path)} needed',font=f(21),fill='#49545b')
for xx,color,label in [(48,'#287c9a','Output on the route'),(425,'#df6b57','Extra output'),(725,'#ffffff','Unlit open cell')]:
 d.rectangle((xx,662,xx+20,682),fill=color,outline='#c0c7c7');d.text((xx+30,658),label,font=f(21),fill='#152c38')
d.text((48,704),'The wave advances from the goal by one edge every two ticks and stops when it reaches the source.',font=f(20),fill='#49545b')
im.save(out/'development_wave.png')
