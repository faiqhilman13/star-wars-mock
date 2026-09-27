from pathlib import Path
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[1]
canvas=Image.new('RGB',(1200,1000),(65,65,65))
draw=ImageDraw.Draw(canvas)
for i,view in enumerate(['front','side']):
    im=Image.open(root/f'review/03_forms/material_{view}.png').convert('RGBA')
    im=im.crop(im.getchannel('A').getbbox())
    im.thumbnail((560,880))
    canvas.paste(im,(i*600+(600-im.width)//2,55),im)
    draw.text((i*600+25,20),f'CORRECTED LOWER LEGS / {view.upper()}',fill='white')
draw.text((25,960),'Blender geometry preview - character remains WIP.',fill='white')
canvas.save(root/'review/03_forms/leg_alignment_fix.png')
