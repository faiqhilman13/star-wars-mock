"""Local forms pass, based on approved phase-2 proportions.
Re-runnable: restores phase 2 from a checkpoint and creates secondary construction.
Metres; -Y forward. Frontal dimensions are reference-derived; surface depths inferred.
"""
import bpy,bmesh,math,pathlib,sys,random,json
from mathutils import Vector
from math import sin,cos,pi,sqrt
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build'))
import phase_helpers as H
H.PHASE='03_forms';H.OWNER_TAG='phase:03_forms'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CH_GreyWarden_blockout.blend'))
COL=H.col('LOW')
ARMOR=bpy.data.materials['M_GreyWarden_Armor'];CLOTH=bpy.data.materials['M_GreyWarden_Cloth']
LEATHER=bpy.data.materials['M_GreyWarden_Leather'];VISOR=bpy.data.materials['M_GreyWarden_Visor']
random.seed(18)

def mesh(name,vs,fs,mat=ARMOR,smooth=True,solid=0,bevel=0):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new('CH_GreyWarden_'+name,me);COL.objects.link(ob);H.own(ob)
    me.materials.append(mat)
    for p in me.polygons:p.use_smooth=smooth
    if solid:
        mod=ob.modifiers.new('Shell thickness','SOLIDIFY');mod.thickness=solid;mod.offset=0
    if bevel:
        mod=ob.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=3
    return ob

def tube(name,pts,r,mat=ARMOR,n=8):
    vs=[];fs=[]
    for i,p in enumerate(pts):
        p=Vector(p);d=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);d.normalize()
        u=d.cross(Vector((0,1,0)))
        if u.length<.01:u=d.cross(Vector((1,0,0)))
        u.normalize();v=d.cross(u)
        rad=r[i] if isinstance(r,list) else r
        for j in range(n):vs.append(tuple(p+rad*(cos(2*pi*j/n)*u+sin(2*pi*j/n)*v)))
    for i in range(len(pts)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs.extend([tuple(reversed(range(n))),tuple((len(pts)-1)*n+j for j in range(n))])
    return mesh(name,vs,fs,mat)

def panel(name,outline,mat=ARMOR,depth=.004,thick=.005):
    # Concentric support rings retain the tailored outline with a shallow, smooth dome.
    pts=[Vector(p) for p in outline];c=sum(pts,Vector())/len(pts);n=len(pts);vs=[];fs=[]
    for scale,dy in [(1,0),(.965,-.001),(.78,-depth*.75),(.35,-depth)]:
        for p in pts:
            q=c+(p-c)*scale;q.y+=dy;vs.append(tuple(q))
    for k in range(3):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    vs.append(tuple(c+Vector((0,-depth,0))))
    for j in range(n):fs.append((3*n+j,3*n+(j+1)%n,4*n))
    return mesh(name,vs,fs,mat,True,thick,.0012)

def sphere(name,p,scale,mat=ARMOR,seg=12,rings=6):
    vs=[];fs=[]
    for i in range(rings+1):
        a=pi*i/rings
        for j in range(seg):
            b=2*pi*j/seg;vs.append((p[0]+scale[0]*sin(a)*cos(b),p[1]+scale[1]*sin(a)*sin(b),p[2]+scale[2]*cos(a)))
    for i in range(rings):
        for j in range(seg):k=i*seg+j;l=i*seg+(j+1)%seg;fs.append((k,l,l+seg,k+seg))
    return mesh(name,vs,fs,mat)

def rivet(name,p):return sphere(name,p,(.0032,.0018,.0032),ARMOR,8,4)

def remove(ob):bpy.data.objects.remove(ob,do_unlink=True)

# Correct the exaggerated ankle splay in the frozen blockout before deriving rims.
# These are the actual Quinn joint heads in world metres; no skeleton is changed.
def leg_axis(z):
    t=max(0,min(1,(.4976965-z)/(.4976965-.0812862)))
    return (.1306266+(.1468445-.1306266)*t,
            -.0169720+(-.0004134+.0169720)*t)

def interp(z,rows):
    if z<=rows[0][0]:return rows[0][1]
    for (a,x),(b,y) in zip(rows,rows[1:]):
        if z<=b:return x+(y-x)*(z-a)/(b-a)
    return rows[-1][1]

for ob in COL.objects:
    name=ob.name.removeprefix('CH_GreyWarden_')
    if not name.startswith(('BootShaft_','BootFoot_','BootSole_','Shin_','Knee_','Trouser_')):continue
    s=1 if name.endswith('_L') else -1
    for v in ob.data.vertices:
        z=v.co.z;nx,ny=leg_axis(z)
        if name.startswith('BootShaft_'):
            ox=interp(z,[(.10,.16),(.22,.16),(.34,.145),(.48,.128)])
            oy=interp(z,[(.10,0),(.22,.005),(.34,.005),(.48,.004)])
            v.co.y+=ny-oy
        elif name.startswith('BootFoot_'):
            ox=interp(z,[(.025,.161),(.055,.161),(.10,.160),(.16,.155)])
            nx=.1468445
        elif name.startswith('BootSole_'):ox=.161;nx=.1468445
        elif name.startswith('Shin_'):
            ox=interp(z,[(.195,.16),(.468,.128)])
            v.co.y+=ny-.004
        elif name.startswith('Knee_'):
            v.co.x+=s*(.1306266-.115);v.co.y-=.016972
            continue
        else:
            blend=max(0,min(1,(.75-z)/.26))
            v.co.x+=s*(.1306266-.115)*blend
            v.co.y-=.026972*blend
            continue
        old_splay=.042*max(0,min(1,(.50-z)/.36))
        v.co.x+=s*(nx-ox-old_splay)

# Refine all broad plate surfaces and give them real rolled rims.
prefixes=['Pectoral','Rib_','Abdominal','LowerAb','Vambrace','Knee_','Shin_','Thigh_','Jaw_','Cheek_','MaskLower','Nose_']
for ob in list(COL.objects):
    short=ob.name.removeprefix('CH_GreyWarden_')
    if any(short.startswith(p) for p in prefixes):
        # Phase2 fans store the perimeter first and centre last.
        pts=[tuple(v.co) for v in ob.data.vertices[:-1]]
        if short.startswith('Shin_'):
            s=1 if short.endswith('_L') else -1
            pts=[]
            for offset,z in [(-.047,.475),(.043,.475),(.061,.451),(.033,.206),(-.032,.202),(-.057,.447)]:
                ax,ay=leg_axis(z);pts.append((s*ax+offset,ay-.077,z))
        mat=ob.data.materials[0];remove(ob)
        panel(short,pts,mat,.004 if short.startswith(('Pectoral','Shin')) else .0025,.006)
        if short.startswith(('Vambrace','Knee','Shin','Pectoral','Thigh')):
            c=sum((Vector(p) for p in pts),Vector())/len(pts)
            edge=[tuple(c+(Vector(p)-c)*.95+Vector((0,-.003,0))) for p in pts]
            tube(short+'_RaisedRim',edge+[edge[0]],.0018,ARMOR,6)
            for j in range(0,len(edge),2):rivet(short+'_Rivet'+str(j),edge[j])

# Helmet crown longitudinal ribs, seam lines and structured band.
for s in [-1,1]:
    pts=[]
    for j in range(25):
        t=j/24;z=1.66+.14*t
        rx=.109*sqrt(max(.01,1-t*t));ry=.114*sqrt(max(.01,1-t*t))
        pts.append((s*.028*sqrt(max(.01,1-t*t)),-ry+.012,z))
    tube('CrownRidge_'+str(s),pts,.0025,ARMOR,8)
    # Multiple bands read clearly at close camera range.
    for z in [1.667,1.679]:
        pts=[(.113*cos(a),.013+.114*sin(a),z) for a in [2*pi*j/64 for j in range(65)]]
        tube('BrowEdge_'+str(s)+'_'+str(z),pts,.0017,ARMOR,6)
    for a in [-pi/2-.65,-pi/2+.65,0,pi]:
        rivet('BrowStud_'+str(s)+'_'+str(a),(.114*cos(a),.013+.116*sin(a),1.673))
    # Circular temple fittings face outward along X.
    for rad,x in [(.020,.126),(.015,.128)]:
        pts=[(s*x,rad*cos(2*pi*j/32),1.663+rad*sin(2*pi*j/32)) for j in range(33)]
        tube('TempleRing_'+str(s)+str(rad),pts,.0022,ARMOR,8)
    panel('TempleLens_'+str(s),[(s*.128,-.007,1.654),(s*.128,-.007,1.672),(s*.128,.007,1.672),(s*.128,.007,1.654)],VISOR,0,.003)
# Central tapered crown strip, clear shape from helmet detail sheet.
panel('CrownForehead',[(-.011,-.108,1.727),(.011,-.108,1.727),(.014,-.126,1.674),(0,-.144,1.654),(-.014,-.126,1.674)],ARMOR,.002,.004)

# Remove cylindrical collar proxies and replace them with broad asymmetric draped fabric.
for ob in list(COL.objects):
    if any(x in ob.name for x in ['CollarFold','ShoulderMantle','HoodFold']):remove(ob)
for layer in range(3):
    vs=[];fs=[];nu=80;nv=12
    for i in range(nv+1):
        t=i/nv
        for j in range(nu+1):
            a=2*pi*j/nu
            r=.081+.035*layer+.037*t
            # Face front at a=-pi/2; fold sags over sternum and crosses right shoulder.
            front=max(0,-sin(a));sag=.026*front+.015*cos(a)
            z=1.535-.035*layer-.049*t-sag+.004*sin(5*a+2*t)
            x=r*cos(a);y=(.061+.020*layer+.033*t)*sin(a)+.006
            y+=.013*sin(2*pi*t+.6*a)*front
            vs.append((x,y,z))
    for i in range(nv):
        for j in range(nu):k=i*(nu+1)+j;fs.append((k,k+1,k+nu+2,k+nu+1))
    mesh('ScarfDrape_'+str(layer),vs,fs,CLOTH,True,.003)
# Outer mantle hangs lower over character's left shoulder, as in original.
vs=[];fs=[];nu=64;nv=14
for i in range(nv+1):
    t=i/nv
    for j in range(nu+1):
        a=2*pi*j/nu;r=.125+.145*t
        z=1.49-.112*t+.023*cos(a)+.014*sin(3*a+2*t)
        rr=.008*sin(6*pi*t+1.5*a)*sin(pi*t)
        vs.append(((r+rr)*cos(a),(.092+.096*t+rr)*sin(a)+.003,z))
for i in range(nv):
    for j in range(nu):k=i*(nu+1)+j;fs.append((k,k+1,k+nu+2,k+nu+1))
mesh('MantleCloth',vs,fs,CLOTH,True,.003)
# Broad folded hood follows the visible U-shaped drape on the rear sheet.
vs=[];fs=[];nu=40;nv=20
for i in range(nv+1):
    t=i/nv
    for j in range(nu+1):
        u=2*j/nu-1;x=u*.210*(1-.18*t)
        sag=sqrt(max(0,1-u*u))
        z=1.495-.231*t*sag-.020*abs(u)
        y=.115+.092*t*sag+.009*sin(6*pi*t+.5*u)*sin(pi*t)
        vs.append((x,y,z))
for i in range(nv):
    for j in range(nu):k=i*(nu+1)+j;fs.append((k,k+1,k+nu+2,k+nu+1))
mesh('FoldedHood',vs,fs,CLOTH,True,.006)
for layer in range(3):
    pts=[]
    for j in range(49):
        u=2*j/48-1;sag=sqrt(max(0,1-u*u));t=.42+.28*layer
        pts.append((u*.210*(1-.18*t),.12+.095*t*sag,1.495-.231*t*sag-.02*abs(u)))
    tube('HoodRolledEdge_'+str(layer),pts,[.003+.009*sin(pi*j/48)**.5 for j in range(49)],CLOTH,10)

# Cape: irregular gravity-aligned folds and modest crumpling near shoulder attachment.
cape=bpy.data.objects['CH_GreyWarden_Cape']
for vertex in cape.data.vertices:
    row,col=divmod(vertex.index,73);t=row/44;u=col/72;a=-.48+(pi+.96)*u
    rx=.218+.140*t-.015*sin(pi*t);ry=.098+.137*t
    phase=15*pi*u+.8*sin(3*pi*u)+.7*t*sin(5*pi*u)
    ripple=(.004+.020*t)*(sin(phase)+.30*sin(27*pi*u+1.8*t))
    hem=-.023*(.5+.5*sin(13*pi*u+.4))-.008*(.5+.5*sin(103*u))
    z=1.468-1.14*t+hem*t**14
    vertex.co=((rx+ripple)*cos(a),.034+(ry+ripple)*sin(a)+.003*sin(34*t+12*u)*math.exp(-4*t),z)
cape.data.update()
# Tattered hem retained in geometry without noisy/random displacement over entire cape.
nu=72;nv=44
hem=[tuple(cape.data.vertices[nv*(nu+1)+j].co) for j in range(nu+1)]
tube('CapeHemSeam',hem,.0015,CLOTH,6)
for ob in list(COL.objects):
    if 'Tabard' in ob.name or 'TassetCloth' in ob.name:
        for v in ob.data.vertices:
            t=max(0,(1.05-v.co.z)/.45);v.co.y+=.004*sin(26*v.co.z+18*v.co.x)*t

# Garment wrinkles aligned around elbows and knees, not random global noise.
for ob in COL.objects:
    if any(p in ob.name for p in ['Sleeve_','ForearmSuit_','Trouser_']):
        for v in ob.data.vertices:
            x,y,z=v.co;sg=1 if x>0 else -1
            a=math.atan2(y,x-sg*(.26 if z>1 else .115))
            amp=.0035*sin(z*110+2*a)*(.4+.6*sin(z*18)**2)
            v.co.y+=amp*sin(a);v.co.x+=amp*cos(a)
        # Keep limb-end positions; subdivision of the capped proxy had shrunk elbows.

# Forearm rails and fastening straps, armor has credible attachment to underlying suit.
for s in [-1,1]:
    side='L' if s>0 else 'R'
    for z,w in [(1.145,.052),(.996,.044)]:
        cx=s*(.287+(1.18-z)*.25)
        pts=[(cx+s*w*cos(2*pi*j/32),-.004+.061*sin(2*pi*j/32),z) for j in range(33)]
        tube('ForearmStrap_'+side+str(z),pts,.008,LEATHER,8)
    for off in [-.012,.012]:
        tube('VambraceRail_'+side+str(off),[(s*(.306+off),-.094,1.133),(s*(.345+off),-.096,.990)],.0025,ARMOR,6)
    # Layered lower pauldron plate under top shell.
    panel('ShoulderLame_'+side,[(s*.247,-.074,1.378),(s*.291,-.048,1.368),(s*.294,-.049,1.306),(s*.249,-.079,1.318)],ARMOR,.006,.006)
    for z in [.527,.452,.228]:
        ax,ay=leg_axis(z);cx=s*ax
        pts=[(cx+.066*cos(2*pi*j/32),ay+.077*sin(2*pi*j/32),z) for j in range(33)]
        tube('LegStrap_'+side+str(z),pts,.009,LEATHER,8)
        panel('LegBuckle_'+side+str(z),[(cx+s*.056,-.045,z+.012),(cx+s*.082,-.045,z+.012),(cx+s*.082,-.045,z-.012),(cx+s*.056,-.045,z-.012)],ARMOR,.001,.003)
    # Boot layered ankle protection and toe cap.
    cx=s*.1468445
    # Tailored cap follows the curved toe-box, so it cannot float as a flat rectangle.
    vs=[];fs=[]
    for i in range(6):
        t=i/5;z=.037+.07*t
        for j in range(17):
            a=-pi*.82+pi*.64*j/16
            vs.append((cx+(.081-.005*t)*cos(a),-.067+(.153-.021*t)*sin(a),z))
    for i in range(5):
        for j in range(16):k=i*17+j;fs.append((k,k+1,k+18,k+17))
    mesh('BootToeCap_'+side,vs,fs,ARMOR,True,.004,.001)
    panel('AnklePlate_'+side,[(cx-.048,-.072,.219),(cx+.048,-.072,.219),(cx+.050,-.099,.174),(cx-.05,-.099,.174)],ARMOR,.003,.004)
    for z,y in [(.164,-.086),(.129,-.117)]:
        tube('BootStrap_'+side+str(z),[(cx-.06,y+.034,z),(cx-.035,y-.010,z),(cx+.035,y-.010,z),(cx+.061,y+.034,z)],.008,LEATHER,8)
    # Tunic leather edge harnesses and waist dangling straps.
    for dx in [-.018,.018]:
        tube('TorsoStrap_'+side+str(dx),[(s*.157+dx,-.105,1.395),(s*.151+dx,-.121,1.245),(s*.132+dx,-.125,1.116)],.006,LEATHER,6)
    # Pouch flap and keeper, preserving four total materials.
    xx=s*.103
    panel('PouchFlap_'+side,[(xx-.026,-.155,1.110),(xx+.026,-.155,1.110),(xx+.025,-.161,1.076),(xx,-.166,1.06),(xx-.025,-.161,1.076)],LEATHER,.002,.004)
    rivet('PouchSnap_'+side,(xx,-.17,1.073))
    tube('BeltTail_'+side,[(s*.145,-.117,1.086),(s*.171,-.121,.982),(s*.176,-.125,.892)],.008,LEATHER,6)

# Purpose-built relaxed gloves with five articulated fingers. Measurements inferred pending Quinn fit.
for ob in list(COL.objects):
    if any(k in ob.name for k in ['Glove_','Thumb_','FingerMass_']):remove(ob)
for s in [-1,1]:
    side='L' if s>0 else 'R';cx=s*.351
    sphere('GlovePalm_'+side,(cx,-.026,.903),(.037,.026,.053),LEATHER,24,12)
    panel('GloveBack_'+side,[(cx-.03,-.049,.94),(cx+.03,-.049,.94),(cx+.036,-.052,.90),(cx+.023,-.054,.869),(cx-.022,-.054,.873)],ARMOR,.001,.003)
    # Fingers fan gently; thumb on medial side, reference open hand.
    lengths=[.053,.063,.06,.047]
    for f in range(4):
        xx=cx+s*(-.025+f*.0165);ln=lengths[f]
        pts=[(xx,-.027,.871),(xx+s*.003,-.035,.871-ln*.45),(xx+s*.006,-.026,.871-ln*.85),(xx+s*.005,-.018,.871-ln)]
        tube('Finger_'+side+str(f),pts,[.010,.009,.008,.0065],LEATHER,10)
        sphere('Knuckle_'+side+str(f),(xx,-.048,.87),(.011,.006,.01),LEATHER,10,6)
    tube('Thumb_'+side,[(cx-s*.024,-.018,.925),(cx-s*.047,-.024,.902),(cx-s*.052,-.016,.879),(cx-s*.045,-.004,.862)],[.015,.014,.012,.008],LEATHER,12)

# Replace segmented face proxies with a continuous curved mask, with true openings.
for ob in list(COL.objects):
    short=ob.name.removeprefix('CH_GreyWarden_')
    if short.startswith(('EyeRim','Lens_','Cheek_','Jaw_','MaskLower','Nose_','Vent_','HelmetCrown')):remove(ob)
vs=[];fs=[];nz=28;nx=32
stations=[(1.521,.028,-.124),(1.55,.068,-.131),(1.59,.090,-.140),(1.63,.106,-.132),(1.671,.108,-.114),(1.690,.081,-.109)]
for i in range(nz+1):
    z=stations[0][0]+(stations[-1][0]-stations[0][0])*i/nz
    k=next((k for k in range(len(stations)-1) if stations[k][0]<=z<=stations[k+1][0]),len(stations)-2)
    a,b=stations[k],stations[k+1];t=(z-a[0])/(b[0]-a[0]);w=a[1]*(1-t)+b[1]*t;y=a[2]*(1-t)+b[2]*t
    for j in range(nx+1):
        u=2*j/nx-1
        cheek=.010*math.exp(-((z-1.611)/.019)**2)*sin(pi*abs(u))
        vs.append((w*u,y+.05*abs(u)**1.35-cheek,z))
for i in range(nz):
    for j in range(nx):k=i*(nx+1)+j;fs.append((k,k+1,k+nx+2,k+nx+1))
mask=mesh('Faceplate',vs,fs,ARMOR,True,.008)
bpy.context.view_layer.objects.active=mask
bpy.ops.object.modifier_apply(modifier=mask.modifiers[0].name)

def cut_profile(name,xz):
    vs=[(x,y,z) for y in [-.23,.02] for x,z in xz];n=len(xz)
    fs=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    cutter=mesh('CUT_'+name,vs,fs,VISOR,False)
    mod=mask.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.context.view_layer.objects.active=mask
    bpy.ops.object.modifier_apply(modifier=mod.name);remove(cutter)
for s in [-1,1]:
    shape=[(s*.015,1.655),(s*.083,1.674),(s*.09,1.661),(s*.075,1.637),(s*.048,1.629),(s*.02,1.637)]
    cut_profile('Eye'+str(s),shape)
    panel('Lens_'+str(s),[(x,-.119+.05*(abs(x)/.10)**1.9,z) for x,z in shape],VISOR,0,.003)
cut_profile('NoseOpening',[(-.004,1.620),(.015,1.587),(.006,1.580),(0,1.591),(-.008,1.580),(-.014,1.587)])
for j in range(-2,3):
    x=j*.010;top=1.575-abs(j)*.003;bottom=1.535+abs(j)*.002
    cut_profile('MouthVent'+str(j),[(x-.0022,top),(x+.0022,top),(x+.0022,bottom),(x-.0022,bottom)])
mod=mask.modifiers.new('Machined opening edges','BEVEL');mod.width=.0012;mod.segments=2
vs=[];fs=[]
for i in range(25):
    t=i/24;z=1.66+.14*t;r=max(.025,sqrt(max(0,1-t*t)))
    for j in range(64):a=2*pi*j/64;vs.append((.109*r*cos(a),.016+.113*r*sin(a),z))
for i in range(24):
    for j in range(64):k=i*64+j;l=i*64+(j+1)%64;fs.append((k,l,l+64,k+64))
fs.append(tuple(24*64+j for j in range(64)))
mesh('HelmetCrown',vs,fs,ARMOR)
# Continuous helmet side/rear shell closes the gap between crown, cheeks and nape.
vs=[];fs=[];steps=48
for z,rx,ry in [(1.536,.067,.079),(1.574,.091,.102),(1.622,.105,.112),(1.674,.108,.113)]:
    for j in range(steps+1):
        a=-.65+(pi+1.30)*j/steps
        vs.append((rx*cos(a),.012+ry*sin(a),z))
for i in range(3):
    for j in range(steps):k=i*(steps+1)+j;fs.append((k,k+1,k+steps+2,k+steps+1))
mesh('HelmetSideShell',vs,fs,ARMOR,True,.004)
# Dark backing behind the nose/vent openings, wholly inside helmet.
panel('RespiratorBacking',[(-.040,-.11,1.622),(.040,-.11,1.622),(.025,-.105,1.525),(-.025,-.105,1.525)],VISOR,0,.004)

# Refined fabric tubes, continuous across elbow and knee; support samples preserve end location.
for s in [-1,1]:
    side='L' if s>0 else 'R'
    for part,start,end,r0,r1 in [('Sleeve',(s*.215,.008,1.426),(s*.292,-.004,1.159),.066,.057),('ForearmSuit',(s*.284,-.004,1.194),(s*.343,-.029,.941),.058,.041)]:
        ob=bpy.data.objects.get('CH_GreyWarden_'+part+'_'+side)
        if ob:remove(ob)
        a,b=Vector(start),Vector(end);d=(b-a).normalized();u=Vector((0,1,0));v=d.cross(u).normalized();vs=[];fs=[]
        for i in range(29):
            t=i/28;c=a.lerp(b,t)
            for j in range(32):
                ang=2*pi*j/32
                wrinkle=.0045*sin(7*pi*t+1.8*sin(ang)+.6*cos(3*ang))*sin(pi*t)**.6
                radius=r0*(1-t)+r1*t+.002*sin(pi*t)+wrinkle
                vs.append(tuple(c+radius*(u*sin(ang)+v*cos(ang))))
        for i in range(28):
            for j in range(32):k=i*32+j;l=i*32+(j+1)%32;fs.append((k,l,l+32,k+32))
        mesh(part+'_'+side,vs,fs,CLOTH,True,.002)

# Reconstruct visible chest panel layout from the actual front reference pixels.
# Coordinates below are measured on review/reference-torso-detail.png, a 3x crop
# of turnaround-v1.png with crop origin (70,130). Y depths are inferred.
for ob in list(COL.objects):
    short=ob.name.removeprefix('CH_GreyWarden_')
    if short.startswith(('Pectoral','Rib_','Abdominal','LowerAb','TorsoStrap','ScarfDrape')):remove(ob)
def chestpoint(u,v):
    x=(u/3+70-248)*.00209546;z=(897-(v/3+130))*.00209546
    y=-.135+.19*x*x
    return (x,y,z)
traced={
 'Sternum':[(491,330),(598,336),(582,445),(498,445)],
 'Pectoral_R':[(379,291),(483,329),(491,443),(425,471),(352,398)],
 'Pectoral_L':[(606,334),(697,298),(727,400),(658,473),(590,444)],
 'RibUpper_R':[(350,409),(418,479),(397,511),(337,471)],
 'RibLower_R':[(333,478),(395,518),(415,557),(378,581),(328,540)],
 'RibUpper_L':[(733,410),(667,480),(687,514),(746,472)],
 'RibLower_L':[(750,480),(690,522),(667,558),(706,582),(753,541)],
 'Abdominal_R':[(504,462),(535,464),(535,571),(461,568),(439,499)],
 'Abdominal_L':[(545,464),(576,462),(634,499),(617,568),(545,571)],
 'LowerAb_R':[(464,581),(535,580),(535,643),(465,640),(450,602)],
 'LowerAb_L':[(545,580),(613,581),(625,603),(612,640),(545,643)]}
for name,outline in traced.items():
    pts=[chestpoint(u,v) for u,v in outline];panel(name,pts,ARMOR,.008 if name.startswith('Pectoral') else .003,.008)
    c=sum((Vector(p) for p in pts),Vector())/len(pts)
    edge=[tuple(c+(Vector(p)-c)*.93+Vector((0,-.004,0))) for p in pts]
    tube(name+'_Rim',edge+[edge[0]],.0012,ARMOR,6)
    for j in [0,len(pts)-2]:rivet(name+'_Stud'+str(j),edge[j])
# Broad soft scarf folds span the chest with asymmetric gravity sag.
for layer in range(4):
    vs=[];fs=[];nu=48;nv=10
    starts=[(-.215,-.026,1.477),(-.17,-.039,1.515),(-.23,-.025,1.439),(-.133,-.041,1.519)]
    mids=[(-.035,-.335,1.304),(.055,-.283,1.361),(.008,-.346,1.300),(-.052,-.240,1.391)]
    ends=[(.240,.003,1.489),(.195,-.006,1.456),(.259,.023,1.474),(.128,.024,1.506)]
    p0,p1,p2=map(Vector,(starts[layer],mids[layer],ends[layer]))
    for j in range(nu+1):
        t=j/nu;c=(1-t)**2*p0+2*t*(1-t)*p1+t*t*p2
        tuck=max(0,1-t/.20)**2+max(0,1-(1-t)/.20)**2
        c.y+=.075*tuck;c.z-=.065*tuck
        width=(.002+.024*sin(pi*t)**.5)*(1-.08*layer)
        for k in range(nv+1):
            a=-pi/2+pi*k/nv
            vs.append((c.x,c.y-(.010+.003*sin(7*t+layer))*cos(a)*sin(pi*t),c.z+width*sin(a)+.003*sin(11*t+2*a+layer)*sin(pi*t)))
    for j in range(nu):
        for k in range(nv):a=j*(nv+1)+k;fs.append((a,a+1,a+nv+2,a+nv+1))
    mesh('ScarfFrontFold_'+str(layer),vs,fs,CLOTH,True,.003)
for s in [-1,1]:
    # Wide flat leather-edged hanging front bands; curve sampled in garment space.
    pts=[Vector((s*.188,-.115,1.434)),Vector((s*.149,-.160,1.20)),Vector((s*.13,-.154,1.07)),Vector((s*.19,-.144,.735))]
    vs=[];fs=[]
    for i in range(33):
        t=i/32*3;k=min(2,int(t));f=t-k;c=pts[k].lerp(pts[k+1],f)
        for u in [-1,-.8,.8,1]:vs.append((c.x+.019*u,c.y-.003*(1-u*u),c.z))
    for i in range(32):
        for j in range(3):a=i*4+j;fs.append((a,a+1,a+5,a+4))
    mesh('FrontCapeBand_'+str(s),vs,fs,LEATHER,True,.003)
    for u in [-.016,.016]:tube('BandSeam_'+str(s)+str(u),[(p.x+u,p.y-.004,p.z) for p in pts],.0007,CLOTH,5)

# Pauldrons rebuilt as closed domed plates with rolled borders, avoiding open top rims.
for ob in list(COL.objects):
    if ob.name.startswith('CH_GreyWarden_Pauldron'):remove(ob)
for s in [-1,1]:
    side='L' if s>0 else 'R';vs=[];fs=[];nu=32;nv=18
    for i in range(nv+1):
        t=i/nv;theta=.10+1.68*t;z=1.390+.077*cos(theta);cx=s*.214
        rr=.076*sin(theta)
        for j in range(nu+1):
            a=-2.03+4.06*j/nu
            vs.append((cx+s*rr*cos(a),.004+.089*sin(theta)*sin(a),z-.005*cos(a)))
    for i in range(nv):
        for j in range(nu):k=i*(nu+1)+j;fs.append((k,k+1,k+nu+2,k+nu+1))
    mesh('Pauldron_'+side,vs,fs,ARMOR,True,.007,.001)
    rim=[vs[i*(nu+1)] for i in range(nv+1)]+[vs[nv*(nu+1)+j] for j in range(1,nu+1)]+[vs[i*(nu+1)+nu] for i in reversed(range(nv))]
    tube('PauldronRim_'+side,rim,.0017,ARMOR,6)
    # Raised cheek ridges give the mask the approved angular skull structure.
    panel('SkullCheek_'+side,[(s*.093,-.093,1.628),(s*.069,-.122,1.611),(s*.031,-.145,1.590),(s*.059,-.117,1.55),(s*.087,-.083,1.581)],ARMOR,.003,.003)
    tube('BrowRidge_'+side,[(s*.012,-.135,1.656),(s*.047,-.126,1.668),(s*.088,-.09,1.678)],.0025,ARMOR,6)
# Actual buckle construction and small fasteners.
for a,b in [((-.032,-.142,1.102),(.032,-.142,1.075)),((.032,-.142,1.102),(-.032,-.142,1.075))]:tube('BuckleDiagonal_'+str(a[0]),[a,b],.001,ARMOR,6)
for x in [-.031,.031]:
    for z in [1.076,1.102]:rivet('BuckleCorner_'+str(x)+str(z),(x,-.143,z))
for x in [-.078,-.058,.058,.078]:rivet('BeltRivet_'+str(x),(x,-.127,1.087))
for s in [-1,1]:
    side='L' if s>0 else 'R';cx=s*.103
    panel('PouchFlap_'+side,[(cx-.027,-.157,1.109),(cx+.027,-.157,1.109),(cx+.025,-.163,1.071),(cx,-.168,1.061),(cx-.025,-.163,1.071)],LEATHER,.003,.004)
    panel('PouchStrap_'+side,[(cx-.006,-.171,1.115),(cx+.006,-.171,1.115),(cx+.006,-.174,1.038),(cx-.006,-.174,1.038)],LEATHER,.001,.003)
    rivet('PouchStud_'+side,(cx,-.180,1.071))
# Brow band lies on top of the faceplate, rather than buried in the crown.
vs=[];fs=[]
for j in range(65):
    a=2*pi*j/64
    for z in [1.678,1.692]:vs.append((.111*cos(a),.011+.130*sin(a),z))
for j in range(64):fs.append((2*j,2*j+1,2*j+3,2*j+2))
mesh('HelmetBrowOverlay',vs,fs,ARMOR,True,.003,.001)
# Armor and inner garment fitting: preserve shoulders but reduce empty ribcage cloth.
torso=bpy.data.objects['CH_GreyWarden_Torso']
for v in torso.data.vertices:
    t=max(0,min(1,(v.co.z-1.12)/.22));v.co.x*=1-.16*t
for ob in COL.objects:
    short=ob.name.removeprefix('CH_GreyWarden_')
    if short.startswith(tuple(traced)):
        for v in ob.data.vertices:
            v.co.x*=1.10;v.co.z=1.25+(v.co.z-1.25)*1.10-.012
# Close-in stitch rows on front tabard and cloth borders.
for s in [-1,1]:
    for j in range(38):
        t=j/37;z=1.045-.35*t;x=s*(.070+.014*t)
        tube('TabardStitch_'+str(s)+'_'+str(j),[(x,-.165,z),(x,-.165,z-.0022)],.00042,LEATHER,4)

exec(compile((ROOT/'build/03b_reference_details.py').read_text(),str(ROOT/'build/03b_reference_details.py'),'exec'))

# Procedural material roles for look-development only; must be baked before game export.
for mat,base,metal,rough in [(ARMOR,(.11,.102,.092),1,.58),(CLOTH,(.038,.034,.032),0,.91),(LEATHER,(.023,.016,.012),0,.72),(VISOR,(.003,.005,.007),0,.30)]:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*base,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=650 if mat==CLOTH else 450;tex.inputs['Detail'].default_value=2
    coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Object'],tex.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[1].position=.8
    ramp.color_ramp.elements[0].color=(*(c*.70 for c in base),1);ramp.color_ramp.elements[1].color=(*(c*1.2 for c in base),1)
    links.new(tex.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    if mat!=VISOR:
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0006 if mat==CLOTH else .00025
        links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
    mat.diffuse_color=(*base,1)

for ob in COL.objects:ob['stage']='FORMS_WIP_UNAPPROVED'
bpy.context.scene['art_status']='FORMS WIP; Quinn reference available; no final export'
H.save_master(str(ROOT/'CH_GreyWarden_master.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_forms.blend'),copy=True)
print('FORMS_SAVED',len(COL.objects))
