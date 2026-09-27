from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
out=ROOT.parents[1]/'collab/wip/grey_warden'
out.mkdir(parents=True,exist_ok=True)
canvas=Image.new('RGB',(1500,960),(205,202,197));d=ImageDraw.Draw(canvas)
for i,(path,title) in enumerate([(ROOT/'ref/front.png','REFERENCE'),(ROOT/'review/03_forms/material_front.png','BLENDER WIP — FRONT'),(ROOT/'review/03_forms/material_threequarter.png','BLENDER WIP — 3/4')]):
    im=Image.open(path).convert('RGBA')
    if i==0:
        im.thumbnail((470,880))
    else:
        box=im.getchannel('A').getbbox();im=im.crop(box);im.thumbnail((460,875))
    canvas.paste(im,(i*500+(500-im.width)//2,50+(875-im.height)//2),im)
    d.text((i*500+20,20),title,fill=(25,25,25))
d.text((20,935),'WORK IN PROGRESS — appearance not accepted; unrigged; not an import-ready asset.',fill=(30,30,30))
canvas.save(out/'preview.png')
print(out/'preview.png')
