"""Render an exact saved-raster diagram using Pillow; no simulation or inference."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/output_access_m31'
assert not (OUT/'witness.png').exists();data=json.loads((OUT/'witness_render.json').read_text())
fontpath=Path('/System/Library/Fonts/Supplemental/Arial.ttf')
def font(n):return ImageFont.truetype(str(fontpath),n) if fontpath.exists() else ImageFont.load_default()
im=Image.new('RGB',(1000,680),'#f7f7f4');draw=ImageDraw.Draw(im)
draw.text((35,20),'One unselected C6 mutant: a west-arm specialist',font=font(25),fill='#172c38')
draw.text((35,56),'M31 development data — same genome, same endpoints, two distant gates swapped',font=font(17),fill='#445660')
for index,panel in enumerate(data['panels']):
    m=panel['maze'];r=panel['row'];w=m['w'];cells=bytes.fromhex(m['cells_hex']);raw=bytes.fromhex(r['mask']);path=set(panel['path']);x0=45+index*490;y0=135;size=19
    title='West arm connected: correct 34-edge path' if index==0 else 'East arm connected: incorrect output'
    draw.text((x0,98),title,font=font(19),fill='#172c38')
    for p,opened in enumerate(cells):
        x=x0+(p%w)*size;y=y0+(p//w)*size;lit=(raw[p//8]>>(p%8))&1
        color='#203442' if not opened else '#e7e9e7'
        if lit:color='#29936c' if p in path else '#e59643'
        draw.rectangle((x,y,x+size-1,y+size-1),fill=color)
        if opened and p in path and not lit:draw.rectangle((x+3,y+3,x+size-4,y+size-4),outline='#4b82c3',width=2)
    for p,label in ((m['start'],'S'),(m['goal'],'G')):
        x=x0+(p%w)*size;y=y0+(p//w)*size;draw.rectangle((x+1,y+1,x+size-2,y+size-2),fill='#fbfbf7');draw.text((x+3,y),label,font=font(16),fill='#172c38')
    detail='Optimal, independently checked saved raster' if index==0 else 'Saved failure: '+r['failure'].replace('_',' ')
    draw.text((x0,548),detail,font=font(16),fill='#445660')
legend=[('#29936c','Correct illuminated pixel'),('#e59643','Illuminated off the shortest path'),('#4b82c3','Required path pixel left dark')]
for i,(color,text) in enumerate(legend):
    x=35+i*320;draw.rectangle((x,590,x+15,605),fill=color);draw.text((x+22,586),text,font=font(15),fill='#172c38')
draw.text((35,635),'Illustration of a retained research lead; zero complete matched alternative pairs and no fresh confirmation.',font=font(16),fill='#445660')
im.save(OUT/'witness.png')
