from PIL import Image,ImageDraw
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
im=Image.open(root/'ref/turnaround-v1.png').convert('RGB')
# Shared vertical window. Generated profiles contain slight three-quarter drift.
boxes={'front':(35,20,449,913),'left':(451,20,752,913),'back':(754,20,1131,913),'right':(1162,20,1472,913)}
out={}
for name,box in boxes.items():
    panel=im.crop(box)
    panel.save(root/f'ref/{name}.png')
    # Measurement-only matte; source art is never overwritten.
    mask=panel.convert('L').point(lambda p:255 if p<180 else 0)
    # Bright metal highlights are still inside the subject silhouette. Fill only
    # enclosed threshold holes; retain background connected to panel boundaries.
    flood=mask.copy()
    for x,y in [(x,0) for x in range(mask.width)]+[(x,mask.height-1) for x in range(mask.width)]+[(0,y) for y in range(mask.height)]+[(mask.width-1,y) for y in range(mask.height)]:
        if flood.getpixel((x,y))==0:ImageDraw.floodfill(flood,(x,y),128)
    mask=flood.point(lambda p:0 if p==128 else 255)
    bbox=mask.getbbox()
    panel.putalpha(mask)
    panel.save(root/f'ref/{name}-matte.png')
    out[name]={'sheet_box':box,'matte_bbox':bbox,'threshold':180,'interior_highlight_holes_filled':True,'orthographic_claim':'generated reference; side views contain yaw and are not exact orthographic measurements'}
(root/'review/reference-panels.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
