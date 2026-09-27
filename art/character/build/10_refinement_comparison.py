from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]
collab=root.parents[1]/'collab'
canvas=Image.new('RGB',(1500,1100),(70,70,70));draw=ImageDraw.Draw(canvas)
ref=Image.open(root/'ref/front.png').convert('RGB').crop((16,18,403,877));ref.thumbnail((470,960))
canvas.paste(ref,((500-ref.width)//2,65+(960-ref.height)//2))
for i,folder in enumerate(['grey_warden_rigcheck_v2','grey_warden_v3'],start=1):
    panel=Image.open(collab/f'incoming/{folder}/preview.png').convert('RGB').crop((0,48,500,1020))
    canvas.paste(panel,(500*i,65))
for i,title in enumerate(['APPROVED REFERENCE / RELAXED POSE','PREVIOUS MODEL / A-POSE','REFINED MODEL / A-POSE']):draw.text((500*i+15,22),title,fill='white')
draw.text((20,1060),'Actual Blender renders. Art likeness remains WIP. Straight leg alignment is retained by user request.',fill='white')
canvas.save(root/'review/refinement_v2_to_v3.png')
