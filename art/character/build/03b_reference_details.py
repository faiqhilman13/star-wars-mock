"""Reference construction corrections; executed in the forms builder namespace."""
# Replace the thin straight suspenders with broad, curved front coat edges.
for ob in list(COL.objects):
    short=ob.name.removeprefix('CH_GreyWarden_')
    if short.startswith(('FrontCapeBand','BandSeam','Tabard','Thigh_','CapeClasp','Knee_','Shin_')):remove(ob)

def ribbon(name,points,widths,mat,nu=48,nv=8):
    points=list(map(Vector,points));vs=[];fs=[]
    for i in range(nu+1):
        t=i/nu*(len(points)-1);k=min(len(points)-2,int(t));f=t-k
        c=points[k].lerp(points[k+1],f);w=widths[k]*(1-f)+widths[k+1]*f
        for j in range(nv+1):
            u=2*j/nv-1
            vs.append((c.x+u*w,c.y-.006*(1-u*u)+.002*sin(11*i/nu+3*u),c.z))
    for i in range(nu):
        for j in range(nv):a=i*(nv+1)+j;fs.append((a,a+1,a+nv+2,a+nv+1))
    return mesh(name,vs,fs,mat,True,.003)

def tailored_plate(name,pts,depth=.006):
    # A broad planar face and one sloping border, not concentric gemstone facets.
    pts=list(map(Vector,pts));c=sum(pts,Vector())/len(pts);n=len(pts)
    inner=[]
    for p in pts:
        q=c+(p-c)*.80;q.y=min(p.y for p in pts)-depth;inner.append(q)
    faces=[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]+[tuple(n+j for j in range(n))]
    return mesh(name,[tuple(p) for p in pts+inner],faces,ARMOR,False,.005,.001)

for s in [-1,1]:
    side='L' if s>0 else 'R'
    points=[(s*.170,-.125,1.454),(s*.145,-.171,1.269),(s*.126,-.167,1.087),(s*.154,-.158,.93),(s*.210,-.127,.755)]
    ribbon('FrontCapeBand_'+side,points,[.029,.026,.027,.040,.045],CLOTH)
    edge=[(x-s*w,y-.003,z) for (x,y,z),w in zip(points,[.029,.026,.027,.040,.045])]
    ribbon('BandSeam_'+side,edge,[.006]*5,LEATHER,nv=4)
    for k in range(14):
        t=k/13*3;j=min(2,int(t));f=t-j;a=Vector(edge[j]).lerp(Vector(edge[j+1]),f)
        rivet('BandSeamStud_'+side+str(k),(a.x,a.y-.005,a.z))

# The source tabard is wider, with a long diagonal hem rather than a skinny strip.
vs=[];fs=[];nu=24;nv=36
for i in range(nv+1):
    t=i/nv
    for j in range(nu+1):
        u=j/nu;x=(-.094-.018*t)*(1-u)+(.093-.005*t)*u
        bottom=.615+.133*u;z=1.065*(1-t)+bottom*t
        y=-.174-.009*sin(pi*u)+.004*sin(6*pi*u+.7*t)*sin(pi*t)
        vs.append((x,y,z))
for i in range(nv):
    for j in range(nu):a=i*(nu+1)+j;fs.append((a,a+1,a+nu+2,a+nu+1))
mesh('Tabard',vs,fs,CLOTH,True,.003)
for row in [0,nv]:
    tube('TabardHem_'+str(row),[vs[row*(nu+1)+j] for j in range(nu+1)],.0013,LEATHER,5)

# Tailored articulated thigh plates seen either side of the hanging tabard.
for s in [-1,1]:
    side='L' if s>0 else 'R'
    for k in range(3):
        z=.91-.086*k;cx=s*(.128+.014*k)
        pts=[(cx-.060,-.123,z),(cx+.058,-.121,z+.006),(cx+.058,-.135,z-.079),(cx+.027,-.145,z-.096),(cx-.055,-.131,z-.075)]
        ob=tailored_plate('Thigh_'+side+'_'+str(k),pts,.003)
        for p in ob.data.polygons:p.use_smooth=False
        c=sum(map(Vector,pts),Vector())/len(pts)
        seam=[tuple(c+(Vector(p)-c)*.89+Vector((0,-.003,0))) for p in pts]
        tube('Thigh_'+side+'_'+str(k)+'_Edge',seam+[seam[0]],.0012,ARMOR,5)
        for j in [0,1,3]:rivet('Thigh_'+side+'_'+str(k)+'_Stud'+str(j),seam[j])
    # Faceted knee shell with a crest and bevel border.
    cx=s*.1306266
    pts=[(cx-.039,-.096,.582),(cx+.038,-.096,.582),(cx+.064,-.100,.543),(cx+.051,-.123,.489),(cx+.004,-.133,.463),(cx-.051,-.118,.496),(cx-.063,-.099,.543)]
    ob=tailored_plate('Knee_'+side,pts,.006)
    for p in ob.data.polygons:p.use_smooth=False
    c=sum(map(Vector,pts),Vector())/len(pts)
    seam=[tuple(c+(Vector(p)-c)*.87+Vector((0,-.003,0))) for p in pts]
    tube('Knee_'+side+'_Edge',seam+[seam[0]],.0014,ARMOR,5)
    for j in [1,3,5]:rivet('Knee_'+side+'_Stud'+str(j),seam[j])
    # Straight longitudinal center follows Quinn; plate taper does not bend the leg.
    pts=[]
    for dx,z in [(-.043,.468),(.041,.468),(.057,.447),(.031,.208),(-.030,.205),(-.052,.447)]:
        ax,ay=leg_axis(z);pts.append((s*ax+dx,ay-.078,z))
    ob=tailored_plate('Shin_'+side,pts,.005)
    for p in ob.data.polygons:p.use_smooth=False
    c=sum(map(Vector,pts),Vector())/len(pts)
    seam=[tuple(c+(Vector(p)-c)*.91+Vector((0,-.003,0))) for p in pts]
    tube('Shin_'+side+'_Edge',seam+[seam[0]],.0012,ARMOR,5)
    # Engraved panel divisions stop above the ankle articulation.
    ax,ay=leg_axis(.40)
    tube('Shin_'+side+'_Ridge',[(s*ax,ay-.092,.445),(s*leg_axis(.24)[0],leg_axis(.24)[1]-.092,.24)],.0013,ARMOR,5)

# Circular cloak clasp must sit in front of the cloth, as in the reference.
cx=-.158;cy=-.141;cz=1.457
sphere('CapeClasp',(cx,cy,cz),(.025,.006,.025),ARMOR,32,12)
for rad in [.020,.025]:
    tube('CapeClaspRing_'+str(rad),[(cx+rad*cos(2*pi*j/48),cy-.006,cz+rad*sin(2*pi*j/48)) for j in range(49)],.0015,ARMOR,6)

# Raised neck folds fill the gap beneath the helmet without changing the helmet.
vs=[];fs=[];nu=64;nv=12
for i in range(nv+1):
    t=i/nv;r=.072+.072*t
    for j in range(nu+1):
        a=2*pi*j/nu
        vs.append((r*cos(a),.010+(.063+.050*t)*sin(a),1.554-.069*t+.008*sin(3*a+5*t)))
for i in range(nv):
    for j in range(nu):a=i*(nu+1)+j;fs.append((a,a+1,a+nu+2,a+nu+1))
mesh('ScarfNeck',vs,fs,CLOTH,True,.003)

# Continuous cloth over each shoulder physically joins coat borders to the cape.
for s in [-1,1]:
    vs=[];fs=[];nu=24;nv=6
    for i in range(nu+1):
        t=i/nu;x=s*(.170+.024*t);y=-.126+.244*t
        z=1.454+.039*sin(pi*t)-.015*t
        for j in range(nv+1):
            u=2*j/nv-1;vs.append((x+.034*u,y,z+.004*(1-u*u)))
    for i in range(nu):
        for j in range(nv):a=i*(nv+1)+j;fs.append((a,a+1,a+nv+2,a+nv+1))
    mesh('ScarfShoulderBridge_'+str(s),vs,fs,CLOTH,True,.003)

# Slightly lower ragged hem retains the corrected straight legs beneath it.
cape=bpy.data.objects['CH_GreyWarden_Cape']
for v in cape.data.vertices:
    t=max(0,min(1,(1.468-v.co.z)/1.14));v.co.z-=.028*t**6
hem=bpy.data.objects.get('CH_GreyWarden_CapeHemSeam')
if hem:
    for v in hem.data.vertices:v.co.z-=.028
