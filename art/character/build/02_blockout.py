"""Measured local Blender construction. Phase 2 only, not a final game mesh.
Coordinates in metres, Z up, -Y forward. Front-sheet landmarks in asset-brief.md.
Depths and hidden geometry are inferred. Rebuild owns only phase:02_blockout.
"""
import bpy, math, pathlib, sys, json
from mathutils import Vector
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import phase_helpers as H
from math import sin,cos,pi,sqrt
ROOT=pathlib.Path(__file__).resolve().parents[1]
H.open_master(str(ROOT/'CH_GreyWarden_master.blend'))
H.PHASE='02_blockout';H.OWNER_TAG='phase:02_blockout';H.clear_owned()
COL=H.col('LOW')
for ob in H.col('REF').objects: ob.hide_render=True;ob.hide_set(True)

def material(name,color,metal=0,rough=.65):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
ARMOR=material('M_GreyWarden_Armor',(.13,.12,.108),.8,.42)
CLOTH=material('M_GreyWarden_Cloth',(.038,.035,.032),0,.92)
LEATHER=material('M_GreyWarden_Leather',(.07,.046,.030),0,.68)
VISOR=material('M_GreyWarden_Visor',(.004,.006,.009),.3,.2)

def mesh(name,vs,fs,mat=CLOTH,smooth=True,solid=0,bevel=0):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new('CH_GreyWarden_'+name,me);COL.objects.link(ob);H.own(ob)
    me.materials.append(mat)
    for p in me.polygons:p.use_smooth=smooth
    if solid:
        m=ob.modifiers.new('Shell thickness','SOLIDIFY');m.thickness=solid;m.offset=0
    if bevel:
        m=ob.modifiers.new('Edge radius','BEVEL');m.width=bevel;m.segments=3
    return ob

def loft(name,rings,mat=CLOTH,n=32,caps=True,fold=0):
    # (z, centre-x, centre-y, halfwidth, halfdepth), sheet front widths; depths inferred.
    vs=[];fs=[]
    for z,x,y,rx,ry in rings:
        for j in range(n):
            a=2*pi*j/n;dr=fold*sin(7*a+23*z)
            vs.append((x+(rx+dr)*cos(a),y+(ry+dr)*sin(a),z))
    for i in range(len(rings)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    if caps:fs.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+j for j in range(n))])
    return mesh(name,vs,fs,mat)

def panel(name,outline,mat=ARMOR,bulge=.018,thick=.008):
    # Outline is clockwise viewed from camera; fan centre curves forward.
    vs=[tuple(v) for v in outline]
    c=Vector((0,0,0))
    for v in vs:c+=Vector(v)
    c/=len(vs);c.y-=bulge;vs.append(tuple(c));i=len(vs)-1
    fs=[(j,(j+1)%i,i) for j in range(i)]
    return mesh(name,vs,fs,mat,False,thick,.002)

def tube(name,points,r,mat=CLOTH,n=12):
    vs=[];fs=[]
    for i,p in enumerate(points):
        p=Vector(p);d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        d.normalize();u=d.cross(Vector((0,1,0)))
        if u.length<.01:u=d.cross(Vector((1,0,0)))
        u.normalize();v=d.cross(u)
        rad=r[i] if isinstance(r,list) else r
        for j in range(n):vs.append(tuple(p+rad*(cos(2*pi*j/n)*u+sin(2*pi*j/n)*v)))
    for i in range(len(points)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs += [tuple(reversed(range(n))),tuple((len(points)-1)*n+j for j in range(n))]
    return mesh(name,vs,fs,mat)

def limb(name,a,b,radii,mat=CLOTH,n=24):
    a,b=Vector(a),Vector(b);d=(b-a).normalized();u=Vector((0,1,0));v=d.cross(u).normalized()
    vs=[];fs=[]
    for i,(rx,ry) in enumerate(radii):
        t=i/(len(radii)-1);c=a.lerp(b,t)
        for j in range(n):ang=j*2*pi/n;vs.append(tuple(c+v*(rx*cos(ang))+u*(ry*sin(ang))))
    for i in range(len(radii)-1):
        for j in range(n):k=i*n+j;l=i*n+(j+1)%n;fs.append((k,l,l+n,k+n))
    fs.extend([tuple(reversed(range(n))),tuple((len(radii)-1)*n+j for j in range(n))])
    return mesh(name,vs,fs,mat)

# Primary garment cage, measured frontal outline, depth inferred from profile.
loft('Torso',[ (1.00,0,0,.165,.100),(1.08,0,0,.158,.10),(1.17,0,0,.158,.102),
 (1.29,0,0,.195,.112),(1.40,0,.005,.221,.115),(1.46,0,.012,.18,.095),
 (1.51,0,.008,.07,.066)],fold=.002)
loft('Pelvis',[(.84,0,0,.146,.105),(.93,0,0,.167,.107),(1.075,0,0,.162,.10)])
loft('Neck',[(1.45,0,0,.065,.066),(1.60,0,0,.062,.065)])

# Crown and mask: helmet height/width measured from sheet. Face depth inferred.
loft('HelmetCrown',[(1.60,0,.014,.100,.096),(1.65,0,.013,.110,.109),
 (1.70,0,.015,.107,.112),(1.75,0,.016,.08,.085),(1.787,0,.017,.033,.039),(1.80,0,.017,.009,.015)],ARMOR,n=48)
loft('HelmetBrowBand',[(1.665,0,.013,.113,.114),(1.68,0,.013,.111,.114)],ARMOR,n=48)
# Sculptural face built around actual ocular openings rather than painted eyes.
for s in [-1,1]:
    side='L' if s>0 else 'R'
    def P(x,y,z):return (s*x,y,z)
    eye=[P(.009,-.106,1.658),P(.084,-.077,1.675),P(.095,-.072,1.658),P(.081,-.091,1.630),P(.047,-.115,1.627),P(.015,-.118,1.638)]
    panel('Lens_'+side,eye,VISOR,bulge=-.003,thick=.004)
    outer=[P(.003,-.123,1.675),P(.087,-.083,1.689),P(.106,-.07,1.67),P(.094,-.099,1.617),P(.045,-.137,1.610),P(.005,-.142,1.633)]
    vs=outer+eye;fs=[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    mesh('EyeRim_'+side,vs,fs,ARMOR,False,.006,.0015)
    panel('Cheek_'+side,[P(.096,-.080,1.634),P(.050,-.139,1.610),P(.032,-.142,1.55),P(.082,-.087,1.56),P(.105,-.059,1.60)],ARMOR,.004)
    panel('Jaw_'+side,[P(.031,-.142,1.596),P(.058,-.123,1.58),P(.068,-.103,1.548),P(.026,-.120,1.524),P(.010,-.135,1.535)],ARMOR,.002)
    panel('Nose_'+side,[P(.004,-.138,1.659),P(.022,-.137,1.611),P(.004,-.153,1.597)],ARMOR,.001)
    # Ear disc is primary silhouette, no micro-detail at this gate.
    limb('Temple_'+side,(s*.109,.0,1.663),(s*.125,.0,1.663),[(.023,.024)]*2,ARMOR)
panel('MaskLower', [(-.026,-.128,1.591),(.026,-.128,1.591),(.025,-.12,1.53),(0,-.125,1.520),(-.025,-.12,1.53)],ARMOR,.002)
for x in [-.018,-.009,0,.009,.018]:
    panel('Vent_'+str(x),[(x-.002,-.136,1.578),(x+.002,-.136,1.578),(x+.002,-.134,1.540),(x-.002,-.134,1.540)],VISOR,0,.001)
# Nape plates leave front face open, repeat broad structural lames.
for k in range(3):
    vs=[];fs=[]
    for j in range(25):
        a=-.15+(pi+.30)*j/24
        for z,r in [(1.61-k*.027,.105+k*.004),(1.576-k*.027,.111+k*.007)]:vs.append((r*cos(a),.012+r*sin(a),z))
    for j in range(24):fs.append((j*2,j*2+1,j*2+3,j*2+2))
    mesh('Nape_'+str(k),vs,fs,ARMOR,True,.006,.002)

# Chest plate construction follows visible segment breaks.
for s in [-1,1]:
    side='L' if s>0 else 'R'
    panel('Pectoral_'+side,[(s*.012,-.130,1.39),(s*.130,-.107,1.414),(s*.192,-.085,1.342),(s*.116,-.135,1.279),(s*.009,-.152,1.302)],ARMOR,.012)
    panel('Rib_'+side,[(s*.186,-.086,1.33),(s*.202,-.072,1.285),(s*.167,-.092,1.204),(s*.104,-.137,1.226),(s*.12,-.139,1.27)],ARMOR,.007)
    panel('Abdominal_'+side,[(s*.008,-.144,1.29),(s*.101,-.129,1.27),(s*.113,-.122,1.216),(s*.077,-.128,1.180),(s*.007,-.143,1.186)],ARMOR,.005)
    panel('LowerAb_'+side,[(s*.008,-.142,1.176),(s*.078,-.130,1.17),(s*.104,-.111,1.116),(s*.008,-.129,1.11)],ARMOR,.002)

loft('Belt',[(1.062,0,-.002,.174,.121),(1.115,0,-.002,.171,.120)],LEATHER,n=48)
panel('Buckle',[(-.036,-.13,1.105),(.036,-.13,1.105),(.036,-.13,1.071),(-.036,-.13,1.071)],ARMOR,0,.010)
for s in [-1,1]:
    side='L' if s>0 else 'R'
    # Hands/boots are separate rough masses from the outset, no fake finished hands.
    limb('Sleeve_'+side,(s*.215,.008,1.418),(s*.287,-.004,1.17),[(.068,.072),(.064,.069),(.059,.062),(.052,.055)],CLOTH)
    limb('ForearmSuit_'+side,(s*.285,-.004,1.18),(s*.343,-.029,.948),[(.055,.057),(.063,.064),(.048,.051),(.041,.041)],CLOTH)
    limb('Glove_'+side,(s*.345,-.028,.960),(s*.366,-.035,.84),[(.04,.037),(.045,.037),(.040,.035),(.030,.028)],LEATHER)
    limb('Thumb_'+side,(s*.322,-.055,.91),(s*.322,-.062,.865),[(.016,.016),(.012,.013)],LEATHER,n=12)
    for f in range(4):
        xx=s*(.342+.012*f)
        limb('FingerMass_'+side+str(f),(xx,-.036,.854),(xx+s*.007,-.043,.797+abs(f-1)*.009),[(.009,.012),(.008,.010),(.006,.008)],LEATHER,n=10)
    # Pauldron curved cap, not spheres.
    vs=[];fs=[]
    for i in range(8):
        t=i/7;z=1.456-.145*t;cx=s*(.223+.020*t)
        for j in range(13):
            a=-pi*.95+pi*1.90*j/12
            vs.append((cx+s*(.037+.037*sin(pi*t*.8))*cos(a),.010+(.055+.025*sin(pi*t))*sin(a),z-.017*cos(a)))
    for i in range(7):
        for j in range(12):k=i*13+j;fs.append((k,k+1,k+14,k+13))
    mesh('Pauldron_'+side,vs,fs,ARMOR,True,.009,.003)
    panel('Vambrace_'+side,[(s*.292,-.070,1.162),(s*.336,-.066,1.141),(s*.375,-.064,.970),(s*.322,-.075,.962),(s*.282,-.078,1.104)],ARMOR,.011)
    x=s*.115
    loft('Trouser_'+side,[(.49,x,.01,.064,.071),(.62,x,.005,.075,.080),(.75,x,0,.090,.091),(.9,s*.102,.005,.091,.10)],fold=.0025)
    loft('BootShaft_'+side,[(.10,s*.16,0,.060,.068),(.22,s*.16,.005,.061,.071),(.34,s*.145,.005,.065,.072),(.48,s*.128,.004,.068,.071)],LEATHER)
    # Boot last, section shape in horizontal planes, toe projects forward.
    loft('BootFoot_'+side,[(.025,s*.161,-.067,.077,.146),(.055,s*.161,-.068,.077,.147),(.10,s*.160,-.062,.073,.132),(.16,s*.155,-.015,.058,.072)],LEATHER)
    loft('BootSole_'+side,[(0,s*.161,-.067,.078,.148),(.025,s*.161,-.067,.078,.148)],LEATHER)
    panel('Knee_'+side,[(x-.055,-.065,.578),(x+.054,-.065,.578),(x+.063,-.081,.520),(x+.022,-.101,.470),(x-.03,-.099,.482),(x-.067,-.08,.527)],ARMOR,.008)
    panel('Shin_'+side,[(s*.128-s*.058,-.083,.468),(s*.128+s*.058,-.081,.468),(s*.16+s*.048,-.078,.205),(s*.16-s*.045,-.082,.195)],ARMOR,.021)
    panel('Thigh_'+side,[(x-.073,-.083,.893),(x+.071,-.08,.892),(x+.063,-.097,.675),(x+.026,-.11,.632),(x-.058,-.1,.674)],ARMOR,.008)
    panel('Pouch_'+side,[(s*.103-s*.025,-.126,1.113),(s*.103+s*.025,-.126,1.113),(s*.103+s*.027,-.139,1.02),(s*.103-s*.027,-.139,1.02)],LEATHER,.013,.026)

# Split tunic skirt and asymmetric front tabard: grid cloth instead of a cone.
def cloth_panel(name,topL,topR,botL,botR,fold=.008,nx=16,ny=20):
    vs=[];fs=[]
    for i in range(ny+1):
        t=i/ny;l=Vector(topL).lerp(Vector(botL),t);r=Vector(topR).lerp(Vector(botR),t)
        for j in range(nx+1):
            u=j/nx;p=l.lerp(r,u);p.y+=fold*sin(5*pi*u+.7*t)*sin(pi*t*.85)
            vs.append(tuple(p))
    for i in range(ny):
        for j in range(nx):k=i*(nx+1)+j;fs.append((k,k+1,k+nx+2,k+nx+1))
    return mesh(name,vs,fs,CLOTH,True,.003)
cloth_panel('Tabard',(-.078,-.152,1.054),(.073,-.153,1.054),(-.09,-.158,.634),(.060,-.161,.698))
for s in [-1,1]:
    cloth_panel('TassetCloth_'+str(s),(s*.080,-.138,1.058),(s*.157,-.086,1.06),(s*.120,-.143,.718),(s*.228,-.065,.699))

# Cape spans shoulders to calves. Cross-section inferred from front/back silhouette.
vs=[];fs=[];nu=72;nv=44
for i in range(nv+1):
    t=i/nv;rx=.218+.173*t-.025*sin(pi*t);ry=.098+.137*t
    for j in range(nu+1):
        u=j/nu;a=-.48+(pi+.96)*u
        ripple=(.004+.015*t)*sin(18*pi*u+.6*t)+.005*t*sin(30*pi*u)
        tails=.095*(math.exp(-((u-.30)/.030)**2)+math.exp(-((u-.70)/.030)**2))
        z=1.468-1.125*t + (.010*sin(13*pi*u)-tails)*t**12
        x=(rx+ripple)*cos(a);y=.034+(ry+ripple)*sin(a)
        vs.append((x,y,z))
for i in range(nv):
    for j in range(nu):k=i*(nu+1)+j;fs.append((k,k+1,k+nu+2,k+nu+1))
mesh('Cape',vs,fs,CLOTH,True,.004)
# Broad draped collar folds, inferred depth, reference-derived vertical placement.
for k in range(3):
    pts=[]
    for j in range(49):
        a=2*pi*j/48
        pts.append(((.104+.034*k)*cos(a),(.073+.024*k)*sin(a),1.508-.037*k+.020*sin(a)+.009*cos(2*a+k)))
    tube('CollarFold_'+str(k),pts,.026-k*.003,CLOTH,12)
# Folded hood at back.
loft('HoodFold',[(1.30,0,.137,.03,.022),(1.36,0,.160,.084,.048),(1.43,0,.120,.108,.060),(1.48,0,.080,.090,.064)],CLOTH,n=32)
limb('CapeClasp',(-.175,-.095,1.438),(-.175,-.114,1.438),[(.026,.026)]*2,ARMOR,n=32)

# Wider boot stance read from sheet. Shift lower legs progressively, retaining knee location.
for ob in COL.objects:
    if any(k in ob.name for k in ['BootShaft','BootFoot','BootSole','Shin']):
        for v in ob.data.vertices:
            s=1 if v.co.x>0 else -1
            v.co.x+=s*.042*max(0,min(1,(.50-v.co.z)/.36))
# Shoulder mantle is a broad cloth layer, primary silhouette visible in approved concept.
vs=[];fs=[]
for i in range(11):
    t=i/10
    for j in range(49):
        a=2*pi*j/48
        rx=.085+.18*t;ry=.066+.060*t
        z=1.493-.135*t + .022*cos(a)*t+.010*sin(3*a+t)
        vs.append((rx*cos(a),.006+ry*sin(a),z))
for i in range(10):
    for j in range(48):k=i*49+j;fs.append((k,k+1,k+50,k+49))
mesh('ShoulderMantle',vs,fs,CLOTH,True,.004)

for ob in COL.objects:
    ob['stage']='BLOCKOUT_UNAPPROVED'
    ob['dimensions_source']='front turnaround; depth and hidden surfaces inferred'
H.save_master(str(ROOT/'CH_GreyWarden_master.blend'))
print('BLOCKOUT_SAVED',len(COL.objects))
