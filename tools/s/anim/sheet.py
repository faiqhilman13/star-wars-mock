import sys
from PIL import Image, ImageDraw
out=sys.argv[1]; items=sys.argv[2:]  # label=path
ims=[]
for it in items:
    lab,p=it.split("=",1); im=Image.open(p).convert("RGB")
    w,h=im.size; im=im.crop((int(w*0.2),0,int(w*0.8),h)).resize((int(w*0.6*0.5),int(h*0.5)))
    ImageDraw.Draw(im).text((8,8),lab,fill=(255,255,0))
    ims.append(im)
cols=min(len(ims),4); rows=(len(ims)+cols-1)//cols
W,H=ims[0].size; S=Image.new("RGB",(W*cols,H*rows))
for i,im in enumerate(ims): S.paste(im,((i%cols)*W,(i//cols)*H))
S.save(out); print(out)
