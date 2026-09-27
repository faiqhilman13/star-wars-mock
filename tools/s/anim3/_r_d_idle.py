import math
SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
KF="animation_toolset.toolsets.keyframing.SequencerKeyframingTools."
IE="animation_toolset.toolsets.import_export.SequencerImportExportTools."
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V3.LS_SaberAuthoring_V3"
BODY={"bindingId":"BF895B52-4243-5DF0-29DD-768D103845A0","sequence":ref(LS)}
RIG="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body"
SEC=LS+":MovieScene_0.MovieSceneControlRigParameterTrack_0.MovieSceneControlRigParameterSection_0"
ACTOR="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCD0503_1297333191"
WORLD="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena"
BASEF=227
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
# ---------------- vector math (char space: f=forward, r=right, u=up; origin = actor at floor) ----
O=(-1000.0,400.0,100.0)
def Wd(v): return (-v[0],-v[1],v[2])
def Wp(p): return (O[0]-p[0],O[1]-p[1],O[2]+p[2])
def Cp(w): return (O[0]-w[0], O[1]-w[1], w[2]-O[2])
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mulv(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vlen(a): return math.sqrt(dot(a,a))
def nrm(a):
    l=vlen(a); return tuple(x/l for x in a)
def m2r(X_,Y_,Z_):
    p=math.degrees(math.atan2(X_[2], math.sqrt(X_[0]**2+X_[1]**2)))
    y=math.degrees(math.atan2(X_[1],X_[0]))
    sy=(-math.sin(math.radians(y)), math.cos(math.radians(y)), 0.0)
    r=math.degrees(math.atan2(dot(Z_,sy), dot(Y_,sy)))
    return (p,y,r)
def Mr(p,y,r):
    p,y,r=[math.radians(v) for v in (p,y,r)]
    SP,CP,SY,CY,SR,CR_=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    return [(CP*CY,CP*SY,SP),(SR*SP*CY-CR_*SY,SR*SP*SY+CR_*CY,-SR*CP),(-(CR_*SP*CY+SR*SY),CY*SR-CR_*SP*SY,CR_*CP)]
def Rz(v, th):
    """rotate char-space vector about up axis; th+ = turn right (forward->right)"""
    c,s=math.cos(math.radians(th)),math.sin(math.radians(th))
    return (v[0]*c - v[1]*s, v[0]*s + v[1]*c, v[2])
def rodr(v, a, ang):
    a=nrm(a); c,s=math.cos(math.radians(ang)),math.sin(math.radians(ang))
    return add(add(mulv(v,c), mulv(cross(a,v),s)), mulv(a, dot(a,v)*(1-c)))
def rot_about(rot, axis_c, ang):
    """rotate world rotator by ang about char-space axis"""
    m=Mr(*rot); rows=[Wd(rodr(Wd(r), axis_c, ang)) for r in m]
    return m2r(*rows)
def rotz_rot(rot, th):
    m=Mr(*rot); rows=[Wd(Rz(Wd(r),th)) for r in m]
    return m2r(*rows)
BA, BB = -math.sin(math.radians(35)), -math.cos(math.radians(35))   # blade = BA*cX + BB*cY
def hand_rot(Dc, Ac, twist=0.0):
    D=nrm(Wd(Dc)); A=nrm(Wd(Ac))
    t=mulv(A,-1.0); E=sub(t, mulv(D, dot(t,D)))
    if vlen(E)<1e-4: E=(0,0,1)
    E=nrm(E)
    if twist:
        c,s=math.cos(math.radians(twist)),math.sin(math.radians(twist))
        E=add(mulv(E,c), mulv(cross(D,E),s))
    cX=add(mulv(D,BA), mulv(E,-BB)); cY=add(mulv(D,BB), mulv(E,BA)); cZ=cross(cX,cY)
    return m2r(cX,cY,cZ)
def blade_of(rot):
    m=Mr(rot[0],rot[1],rot[2])
    return Wd(add(mulv(m[0],BA), mulv(m[1],BB)))
def lhand_rot(Ac, backc):
    cX=nrm(Wd(Ac)); bk=Wd(backc); cZ=nrm(sub(bk, mulv(cX, dot(bk,cX)))); cY=cross(cZ,cX)
    return m2r(cX,cY,cZ)
def arcv(phi, u, v):
    c,s=math.cos(math.radians(phi)),math.sin(math.radians(phi))
    return nrm(add(mulv(nrm(u),c), mulv(nrm(v),s)))
# ---------------- rig io ----------------
def setw(ctrl, frame, pos_c, rot=(0,0,0)):
    w=Wp(pos_c)
    return X(CR+"set_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame,
             location_x=w[0], location_y=w[1], location_z=w[2], rotation_pitch=rot[0], rotation_yaw=rot[1], rotation_roll=rot[2], set_key=True)
def setl(ctrl, frame, loc=(0,0,0), rot=(0,0,0)):
    return X(CR+"set_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame,
             location_x=loc[0], location_y=loc[1], location_z=loc[2], rotation_pitch=rot[0], rotation_yaw=rot[1], rotation_roll=rot[2], scale_x=1, scale_y=1, scale_z=1, set_key=True)
def setb(ctrl, frame, v):
    return X(CR+"set_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame, value=v, set_key=True)
def geteul(ctrl, frame):
    return json.loads(X(CR+"get_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame))
def getw(ctrl, frame):
    return json.loads(X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame))
def wpos(ctrl, frame):
    l=getw(ctrl, frame)["location"]; return Cp((l["x"],l["y"],l["z"]))
def show(frame):
    X(SQ+"set_playhead_frame", frame=frame+1); X(SQ+"force_evaluate")
    X(SQ+"set_playhead_frame", frame=frame); X(SQ+"force_evaluate")
def tup(d): return (d["x"],d["y"],d["z"]) if "x" in d else (d["pitch"],d["yaw"],d["roll"])
def guard():
    if T("app.IsPIERunning"): raise RuntimeError("PIE_RUNNING")

# ================= pose engine V3 (extends anim2/eng.py) =================
def _comb(terms):
    v0=terms[0][1]
    if isinstance(v0,(tuple,list)):
        n=len(v0); return tuple(sum(c*v[i] for c,v in terms) for i in range(n))
    return sum(c*v for c,v in terms)
class Tr:
    """cubic hermite (catmull-rom) track. keys: (t, v[, 'f' flat]). period -> looping (last key == first)."""
    def __init__(self, keys, period=None):
        self.k=[(float(k[0]), k[1], (k[2] if len(k)>2 else None)) for k in sorted(keys,key=lambda k:k[0])]
        self.P=period
    def _nb(self,i):
        n=len(self.k)
        if self.P is None:
            return self.k[max(0,min(n-1,i))]
        m=n-1; q,r=divmod(i,m); t,v,f=self.k[r]; return (t+q*self.P, v, f)
    def _m(self,i):
        n=len(self.k); t,v,f=self._nb(i)
        if f=='f' or (self.P is None and (i<=0 or i>=n-1)): return _comb([(0.0,v)])
        t0,v0,_=self._nb(i-1); t1,v1,_=self._nb(i+1)
        return _comb([(1.0/(t1-t0),v1),(-1.0/(t1-t0),v0)])
    def __call__(self,t):
        if self.P is not None: t=t%self.P
        if len(self.k)==1: return self.k[0][1]
        if t<=self.k[0][0]: return self.k[0][1]
        if t>=self.k[-1][0]: return self.k[-1][1]
        i=0
        while self.k[i+1][0]<t: i+=1
        t0,v0,_=self.k[i]; t1,v1,_=self.k[i+1]; h=t1-t0; s=(t-t0)/h
        m0=self._m(i); m1=self._m(i+1)
        h00=2*s**3-3*s**2+1; h10=s**3-2*s**2+s; h01=-2*s**3+3*s**2; h11=s**3-s**2
        return _comb([(h00,v0),(h10*h,m0),(h01,v1),(h11*h,m1)])
class Fn:
    def __init__(self,f): self.f=f
    def __call__(self,t): return self.f(t)
def K(v): return Fn((lambda vv: (lambda t: vv))(v))
# ---- calibration ----
CAL=None
def calib():
    global CAL
    if CAL is not None: return CAL
    c={}
    for n in ["body_ctrl","spine_01_ctrl","spine_02_ctrl","spine_03_ctrl","head_ctrl","neck_01_ctrl"]:
        e=geteul(n,BASEF); c["L_"+n]=(tup(e["location"]),tup(e["rotation"]))
    for n in ["body_ctrl","foot_l_ik_ctrl","foot_r_ik_ctrl","leg_l_pv_ik_ctrl","leg_r_pv_ik_ctrl"]:
        w=getw(n,BASEF); c["W_"+n]=(Cp(tup(w["location"])),tup(w["rotation"]))
    CAL=c; return c
CAL_OFF={"L_body_ctrl":((1.491,-3.499,-3.75),(-2.46,22.492,4.338)),
     "L_spine_01_ctrl":((0,0.426,1.757),(1.034,0.013,4.723)),"L_spine_02_ctrl":((0,-0.046,-0.385),(0.683,-0.025,1.276)),
     "L_spine_03_ctrl":((0,0.02,-0.327),(0.68,-0.054,3.411)),"L_head_ctrl":((0.021,-0.303,-0.789),(2.579,-15.149,7.168)),
     "L_neck_01_ctrl":((-0.048,-0.482,1.853),(0.727,-2.08,-1.424)),
     "W_body_ctrl":((-0.69,-1.49,99.83),(-2.46,112.49,4.34)),"W_foot_l_ik_ctrl":((11.03,-20.55,8.48),(-2.05,101.58,1.94)),
     "W_foot_r_ik_ctrl":((-19.86,10.36,8.14),(-1.06,129.82,2.05)),"W_leg_l_pv_ik_ctrl":((57.98,-14.64,57.96),(0,0,0)),"W_leg_r_pv_ik_ctrl":((29.41,37.19,45.0),(0,0,0))}
BLOC=((0,-1,0),(1,0,0),(0,0,1))   # body_ctrl parent-local x,y,z -> char (f,r,u)
def bl_to_c(d): return add(add(mulv(BLOC[0],d[0]),mulv(BLOC[1],d[1])),mulv(BLOC[2],d[2]))
def c_to_bl(v): return (dot(BLOC[0],v),dot(BLOC[1],v),dot(BLOC[2],v))
REACH=51.0
FOOTAZ={"l":12.6,"r":40.8}
BALL=(14.6,-9.0)     # ankle->ball: forward, up (char cm)
ANKZ=8.48            # base ankle height
def clampP(P, S, reach):
    d=sub(P,S); L=vlen(d)
    return P if L<=reach else add(S, mulv(d, reach/L))
def pole(S, P, hint, dist=40.0):
    A=nrm(sub(P,S)); h=nrm(hint); h=sub(h, mulv(A, dot(h,A)))
    if vlen(h)<1e-3: h=(0,0,-1)
    return add(add(S, mulv(sub(P,S),0.5)), mulv(nrm(h), dist))
def env(t, T, a=2.0, b=3.0):
    return max(0.0, min(1.0, t/a, (T-t)/b))
# ---------- quaternion helpers (rows = world axes X,Y,Z) ----------
def m2q(m):
    X_,Y_,Z_=m
    R=[[X_[0],Y_[0],Z_[0]],[X_[1],Y_[1],Z_[1]],[X_[2],Y_[2],Z_[2]]]
    tr=R[0][0]+R[1][1]+R[2][2]
    if tr>0:
        s=math.sqrt(tr+1.0)*2; w=0.25*s; x=(R[2][1]-R[1][2])/s; y=(R[0][2]-R[2][0])/s; z=(R[1][0]-R[0][1])/s
    elif R[0][0]>R[1][1] and R[0][0]>R[2][2]:
        s=math.sqrt(1.0+R[0][0]-R[1][1]-R[2][2])*2; w=(R[2][1]-R[1][2])/s; x=0.25*s; y=(R[0][1]+R[1][0])/s; z=(R[0][2]+R[2][0])/s
    elif R[1][1]>R[2][2]:
        s=math.sqrt(1.0+R[1][1]-R[0][0]-R[2][2])*2; w=(R[0][2]-R[2][0])/s; x=(R[0][1]+R[1][0])/s; y=0.25*s; z=(R[1][2]+R[2][1])/s
    else:
        s=math.sqrt(1.0+R[2][2]-R[0][0]-R[1][1])*2; w=(R[1][0]-R[0][1])/s; x=(R[0][2]+R[2][0])/s; y=(R[1][2]+R[2][1])/s; z=0.25*s
    return (w,x,y,z)
def q2m(q):
    w,x,y,z=q
    R=[[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],[2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],[2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    return [(R[0][0],R[1][0],R[2][0]),(R[0][1],R[1][1],R[2][1]),(R[0][2],R[1][2],R[2][2])]
def slerp_rot(r0, r1, a):
    if a<=0.0001: return r0
    if a>=0.9999: return r1
    q0=m2q(Mr(*r0)); q1=m2q(Mr(*r1))
    d=sum(x*y for x,y in zip(q0,q1))
    if d<0: q1=tuple(-x for x in q1); d=-d
    if d>0.9995:
        q=tuple(x+(y-x)*a for x,y in zip(q0,q1))
    else:
        th=math.acos(d); s0=math.sin((1-a)*th)/math.sin(th); s1=math.sin(a*th)/math.sin(th)
        q=tuple(s0*x+s1*y for x,y in zip(q0,q1))
    n=math.sqrt(sum(x*x for x in q)); q=tuple(x/n for x in q)
    m=q2m(q)
    return m2r(*m)
def ctrl_axes_c(rot):
    m=Mr(*rot); return (Wd(m[0]),Wd(m[1]),Wd(m[2]))
SABOFF=(7.0,0.0,-2.0)   # saber origin in hand-ik-ctrl local axes (measured, both hands)
def saber_origin(P, rot):
    cx,cy,cz=ctrl_axes_c(rot)
    return add(P, add(mulv(cx,SABOFF[0]), mulv(cz,SABOFF[2])))
def lsaber_rot(D, A, tw=0.0):
    """left-hand ctrl rotation that points the left saber (mirror grip) along D; A = shoulder->hand"""
    return hand_rot(D, mulv(A,-1.0), -tw)
# ---------- clip ----------
GRP={"yaw":"pel","bend":"pel","lean":"pel","dz":"pel","dfwd":"pel","dside":"pel","th":"pel",
     "syaw":"sp","sbend":"sp","slean":"sp","hyaw":"hd","hpitch":"hd","hroll":"hd","hc":"hd",
     "lf":"ft","rf":"ft","lfy":"ft","rfy":"ft","lfp":"ft","rfp":"ft","lA":"ft","rA":"ft","lK":"ft","rK":"ft",
     "rD":"bl","rtw":"bl","lD":"lbl","ltw":"lbl",
     "lR":"la","lback":"la","lpv":"la","lP":"la","lRs":"la"}
DEF={"yaw":0.0,"bend":0.0,"lean":0.0,"dz":0.0,"dfwd":0.0,"dside":0.0,"th":0.0,"syaw":0.0,"sbend":0.0,"slean":0.0,
     "hyaw":0.0,"hpitch":0.0,"hroll":0.0,"hc":0.6,"lf":(0,0,0),"rf":(0,0,0),"lfy":0.0,"rfy":0.0,"lfp":0.0,"rfp":0.0,
     "rpv":(-0.3,0.6,-0.75),"rtw":0.0,"lback":(-0.2,-1,0.1),"lpv":(-0.4,-0.6,-0.7),"lg":0.0,"lgo":-24.0,"lgs":1.0,"lgtw":0.0,
     "ltw":0.0,"rDt":0.0,"lDt":0.0}
class Clip:
    def __init__(self, name, start, T, tr, leads=None, Q=(0,0,0), loop=False, extra=None):
        self.name=name; self.S=start; self.T=T; self.tr=tr; self.Q=Q; self.loop=loop
        self.L=dict(pel=1.0, sp=0.5, hd=0.3, ft=0.8, arm=0.0, bl=-0.5, la=0.3, lbl=-0.5)
        if leads: self.L.update(leads)
        self.extra=extra or {}
    def g(self, name, t):
        tr=self.tr.get(name)
        if tr is None: return DEF.get(name)
        if self.loop: return tr(t)
        e=env(t,self.T)
        return tr(min(self.T, max(0.0, t+self.L[GRP.get(name,"arm")]*e)))
    def pose(self, t):
        p={}
        for n in set(list(DEF.keys())+list(self.tr.keys())): p[n]=self.g(n,t)
        return p
def spinp(p, th, Q):
    return add(Q, Rz(sub(p,Q), th))
def key_body(F, p, Q):
    c=calib()
    th=p["th"]
    bl,br=c["L_body_ctrl"]; pw,_=c["W_body_ctrl"]
    pc=add(pw, (p["dfwd"], p["dside"], p["dz"]))
    pc2=spinp(pc, th, Q)
    loc=add(bl, c_to_bl(sub(pc2,pw)))
    setl("body_ctrl", F, loc, (br[0]+p["lean"], p["yaw"]+th, br[2]+p["bend"]))
    for n in ["spine_01_ctrl","spine_02_ctrl","spine_03_ctrl"]:
        l,r=c["L_"+n]
        setl(n, F, l, (r[0]+p["slean"], r[1]+p["syaw"], r[2]+p["sbend"]))
    l,r=c["L_head_ctrl"]
    hy=p["hyaw"]-p["hc"]*(p["yaw"]+3*p["syaw"])
    hy=max(-65,min(65,hy))
    setl("head_ctrl", F, l, (r[0]+p["hroll"], hy, r[2]+p["hpitch"]))
def foot_target(s, p, c):
    """returns (pos_c, rot_world, pole_c) before spin"""
    fb,frot=c["W_foot_%s_ik_ctrl"%s]; pb,_=c["W_leg_%s_pv_ik_ctrl"%s]
    fy=p[s+"fy"]; fp=p[s+"fp"]
    A=p.get(s+"A")
    pos=A if A is not None else add(fb, p[s+"f"])
    rot=rotz_rot(frot, fy)
    az=fy+FOOTAZ[s]; lat=Rz((0,1,0),az)
    if abs(fp)>0.01:
        rot=rot_about(rot, lat, fp)
        if fp>0 and A is None:
            fwd=Rz((1,0,0),az); ball=add(pos, add(mulv(fwd,BALL[0]),(0,0,BALL[1])))
            pos=add(ball, rodr(sub(pos,ball), lat, fp))
    Kp=p.get(s+"K")
    if Kp is not None: pv=Kp
    else:
        rel=sub(pb, fb); pv=add(add(pos, Rz(rel, fy)), (0,0,p["dz"]*0.5))
    return pos, rot, pv
def key_feet(F, p, Q):
    c=calib(); th=p["th"]
    for s in "lr":
        pos,rot,pv=foot_target(s,p,c)
        setw("foot_%s_ik_ctrl"%s, F, spinp(pos, th, Q), rotz_rot(rot, th))
        setw("leg_%s_pv_ik_ctrl"%s, F, spinp(pv, th, Q))
def right_target(p, S, Q):
    th=p["th"]; psi=p["yaw"]+3*p["syaw"]+th
    w=p.get("rRw")
    if p.get("rR") is not None and w is None: rP=add(S, Rz(p["rR"], psi))
    elif p.get("rR") is not None and p.get("rP") is not None:
        w=max(0.0,min(1.0,w)); rP=add(mulv(spinp(p["rP"], th, Q),1-w), mulv(add(S, Rz(p["rR"], psi)),w))
    else: rP=spinp(p["rP"], th, Q)
    rD=nrm(Rz(p["rD"], th+p["rDt"]*(psi-th)))
    P=clampP(rP, S, REACH); A=nrm(sub(P,S))
    rr=hand_rot(rD, A, p["rtw"])
    return P, rD, rr, A, psi
def left_target(p, SL, P, rD, rr, Q):
    """returns (Pl, rot, pole_hint) for the left hand"""
    th=p["th"]; psi=p["yaw"]+3*p["syaw"]+th
    lpvh=Rz(p["lpv"], psi)
    if p.get("lD") is not None:
        # left saber (dual wield)
        if p.get("lRs") is not None: lP=add(SL, Rz(p["lRs"], psi))
        else: lP=spinp(p["lP"], th, Q)
        lD=nrm(Rz(p["lD"], th+p["lDt"]*(psi-th)))
        Pl=clampP(lP, SL, REACH); Al=nrm(sub(Pl,SL))
        return Pl, lsaber_rot(lD, Al, p["ltw"]), lpvh
    lP=add(SL, Rz(p["lR"], psi)); lback=Rz(p["lback"], psi)
    Pl=clampP(lP, SL, REACH); Al=nrm(sub(Pl,SL))
    lrot=lhand_rot(Al, lback)
    lg=max(0.0,min(1.0,p["lg"]))
    if lg>0.001:
        O=saber_origin(P, rr)
        Dg=mulv(rD, p["lgs"])
        Qg=add(O, mulv(rD, p["lgo"]))
        Ag=nrm(sub(Qg,SL))
        for it in range(3):
            gr=lsaber_rot(Dg, Ag, p["lgtw"])
            cx,cy,cz=ctrl_axes_c(gr)
            gP=sub(Qg, add(mulv(cx,SABOFF[0]), mulv(cz,SABOFF[2])))
            Ag=nrm(sub(gP,SL))
        gpv=Rz(p.get("lgpv") or (-0.3,-0.75,-0.6), psi)
        Pl=add(mulv(Pl,1-lg), mulv(gP,lg)); Pl=clampP(Pl, SL, REACH+2.0)
        lrot=slerp_rot(lrot, gr, lg)
        lpvh=add(mulv(nrm(lpvh),1-lg), mulv(nrm(gpv),lg))
    return Pl, lrot, lpvh
def key_arms(F, p, Q):
    show(F)
    S=wpos("upperarm_r_fk_ctrl", F)
    if abs(S[2])>400 or S[2]<30: raise RuntimeError("bad shoulder read %s at %d"%(str(S),F))
    P,rD,rr,A,psi=right_target(p,S,Q)
    setw("hand_r_ik_ctrl", F, P, rr)
    setw("arm_r_pv_ik_ctrl", F, pole(S,P,Rz(p["rpv"],psi if (p.get("rR") is not None and p.get("rRw") is None) else p["th"]+p["rDt"]*(psi-p["th"]))))
    out={"P":P,"D":rD,"S":S}
    if p.get("lR") is not None or p.get("lD") is not None:
        SL=wpos("upperarm_l_fk_ctrl", F)
        Pl,lrot,lpvh=left_target(p,SL,P,rD,rr,Q)
        setw("hand_l_ik_ctrl", F, Pl, lrot)
        setw("arm_l_pv_ik_ctrl", F, pole(SL,Pl,lpvh))
        out["lP"]=Pl
    return out
def bake(clip, frames=None, parts="bfa"):
    fr = frames if frames is not None else list(range(0, clip.T+1))
    done=[]; res=[]
    try:
        calib()
        for i in fr:
            guard()
            p=clip.pose(float(i)); F=clip.S+i
            if "b" in parts: key_body(F, p, clip.Q)
            if "f" in parts: key_feet(F, p, clip.Q)
            if "a" in parts:
                o=key_arms(F, p, clip.Q); res.append([i]+[round(x,1) for x in o["P"]])
            guard()
            done.append(i)
    except RuntimeError as e:
        return {"done":done, "err":str(e)[:200], "res":res}
    return {"done":done, "err":None, "res":res}
FING=[("index",-65),("middle",-72),("ring",-78),("pinky",-82)]
FCACHE={}
def fingers(side, F, curl):
    """curl: True/1.0 = saber grip; False/0 = MM_Idle relaxed; 0<x<1 = partial fist"""
    k=1.0 if curl is True else (0.0 if curl is False else float(curl))
    for f,base in FING:
        for j in ["01","02","03"]:
            c="%s_%s_%s_ctrl"%(f,j,side)
            if c not in FCACHE:
                e=geteul(c,BASEF); FCACHE[c]=(tup(e["location"]),tup(e["rotation"]))
            l,r=FCACHE[c]
            if j=="01": g=(r[0],base,r[2])
            elif j=="02": g=(0,-85,0)
            else: g=(0,-55,0)
            if k>=0.999: setl(c,F,(0,0,0),g)
            elif k<=0.001: setl(c,F,l,r)
            else: setl(c,F,mulv(l,1-k),add(mulv(r,1-k),mulv(g,k)))

# ================= V3 clip definitions =================
def U3(*a): return nrm(a)
def cosp(ph, per): return math.cos(2*math.pi*ph/per)
def sinp(ph, per): return math.sin(2*math.pi*ph/per)
def periodic(tab, per):
    """tab: list of (t, value) -> periodic catmull-rom track (adds closing key)"""
    k=list(tab)+[(per, tab[0][1])]
    return Tr(k, period=per)
def lerp(a,b,s):
    if isinstance(a,tuple): return tuple(x+(y-x)*s for x,y in zip(a,b))
    return a+(b-a)*s
def smooth(s): s=max(0.0,min(1.0,s)); return s*s*(3-2*s)
# ---------------- body helpers ----------------
THIGH_L=45.8; SHIN_L=41.7
IDLE_J={"body":(-0.69,-1.49,99.83),"thigh_l":(3.23,-11.97,90.78),"thigh_r":(-5.35,8.62,90.35),
      "ua_r":(-4.76,16.99,142.19),"ua_l":(9.14,-18.52,141.83),"neck":(4.24,0.07,150.66),"head":(8.21,1.67,159.72)}
def body_rows_p(lean,yaw,bend):
    br=CAL_OFF["L_body_ctrl"][1]
    return [bl_to_c(r) for r in Mr(br[0]+lean, yaw, br[2]+bend)]
_RB0=body_rows_p(0.0,22.492,0.0)
JLOC={k:tuple(dot(sub(v,IDLE_J["body"]),r) for r in _RB0) for k,v in IDLE_J.items()}
def hip_approx(s, dfwd, dside, dz, lean, yaw, bend):
    b=add(CAL_OFF["W_body_ctrl"][0],(dfwd,dside,dz)); rb=body_rows_p(lean,yaw,bend); L=JLOC["thigh_"+s]
    return add(b, add(add(mulv(rb[0],L[0]),mulv(rb[1],L[1])),mulv(rb[2],L[2])))
def leg_from_angles(th, kap):
    sh=th-kap
    x=THIGH_L*math.sin(math.radians(th))+SHIN_L*math.sin(math.radians(sh))
    z=-THIGH_L*math.cos(math.radians(th))-SHIN_L*math.cos(math.radians(sh))
    return x,z,sh
# ---------------- ninja run (shared by saber / staff / dual) ----------------
RUN_V=680.0/30.0            # ground speed cm/frame (680 cm/s)
BALL_R=math.sqrt(BALL[0]**2+BALL[1]**2); BALL_B=math.degrees(math.atan2(-BALL[1],BALL[0]))
BALLZ=ANKZ+BALL[1]
def _ankle_from_ball(bx, a):
    ang=math.radians(BALL_B+a)
    return (bx-BALL_R*math.cos(ang), BALLZ+BALL_R*math.sin(ang))
RUN_B0=60.0
RUN_STANCE_A=[8.0, 0.0, 2.0, 12.0, 30.0, 52.0]
# swing: phase -> (thigh angle from vertical (+fwd), knee flexion, extra plantarflexion)
RUN_SWING=[(6,(-32.0,40.0,12.0)),(7,(-27.0,68.0,8.0)),(8,(-20.0,95.0,3.0)),(9,(-11.0,115.0,0.0)),(10,(0.0,126.0,-4.0)),
           (11,(13.0,128.0,-6.0)),(12,(27.0,122.0,-8.0)),(13,(41.0,110.0,-10.0)),(14,(53.0,94.0,-10.0)),(15,(61.0,74.0,-8.0)),
           (16,(63.0,52.0,0.0)),(17,(58.0,33.0,12.0)),(18,(51.0,23.0,20.0)),(19,(44.0,18.0,22.0))]
class RunCfg:
    def __init__(self, **kw):
        self.dfwd=1.0; self.dz0=-7.5; self.dza=2.75; self.yawa=11.0; self.syawa=6.3; self.bend=14.5; self.sbend=3.3
        self.hpitch=-22.5; self.flat=9.0; self.lead=-3.0
        self.__dict__.update(kw)
def run_tracks(cfg):
    tr={}
    tr["dz"]=Fn(lambda t: cfg.dz0-cfg.dza*cosp(t-2.5,10.0))
    tr["dfwd"]=K(cfg.dfwd)
    tr["dside"]=Fn(lambda t: 1.3*cosp(t-2.5,20.0))
    tr["yaw"]=Fn(lambda t: -cfg.yawa*cosp(t-cfg.lead,20.0))
    tr["bend"]=Fn(lambda t: cfg.bend+1.0*cosp(t-2.5,10.0))
    tr["lean"]=Fn(lambda t: -2.0*cosp(t-3.5,20.0))
    tr["syaw"]=Fn(lambda t: cfg.syawa*cosp(t-cfg.lead-1.0,20.0))
    tr["sbend"]=Fn(lambda t: cfg.sbend+0.5*cosp(t-3.5,10.0))
    tr["slean"]=Fn(lambda t: 0.8*cosp(t-4.5,20.0))
    tr["hpitch"]=Fn(lambda t: cfg.hpitch+1.2*cosp(t-3.0,10.0))
    tr["hroll"]=Fn(lambda t: 1.5*cosp(t-3.5,20.0))
    tr["hyaw"]=K(0.0); tr["hc"]=K(0.95)
    xref=CAL_OFF["W_body_ctrl"][0][0]+cfg.dfwd-2.5
    def hip(s, t):
        return hip_approx(s, tr["dfwd"](t), tr["dside"](t), tr["dz"](t), tr["lean"](t), tr["yaw"](t), tr["bend"](t))
    def foot_int(s, i):
        """integer phase i (0..19): absolute ankle (x,z) and pitch"""
        i=i%20
        if i<=5:
            a=RUN_STANCE_A[i]; bx=RUN_B0-RUN_V*i
            x,z=_ankle_from_ball(bx,a)
            return (xref+x, z), a
        th,kap,pf=dict(RUN_SWING)[i]
        h=hip(s, float(i if s=="r" else i-10))
        x,z,sh=leg_from_angles(th,kap)
        return (h[0]+x, h[2]+z), -sh+pf
    cache={}
    def foot(s, t):
        off=0.0 if s=="r" else 10.0
        ph=(t+off)%20.0
        i0=int(math.floor(ph+1e-6)); fr=ph-i0
        key=(s,i0)
        if key not in cache: cache[key]=foot_int(s,i0)
        (x,z),a=cache[key]
        if fr>1e-6:
            if (s,i0+1) not in cache: cache[(s,i0+1)]=foot_int(s,i0+1)
            (x1,z1),a1=cache[(s,i0+1)]
            if i0+1==20: x1+=0.0
            x,z,a=lerp(x,x1,fr),lerp(z,z1,fr),lerp(a,a1,fr)
        lat=cfg.flat if s=="r" else -cfg.flat
        return (x, lat, z), a
    tr["rA"]=Fn(lambda t: foot("r",t)[0]); tr["lA"]=Fn(lambda t: foot("l",t)[0])
    tr["rfp"]=Fn(lambda t: foot("r",t)[1]); tr["lfp"]=Fn(lambda t: foot("l",t)[1])
    tr["rfy"]=K(4.0-FOOTAZ["r"]); tr["lfy"]=K(-4.0-FOOTAZ["l"])
    tr["rK"]=K((xref+75.0, 16.0, 95.0)); tr["lK"]=K((xref+75.0, -16.0, 95.0))
    return tr
def run_left_pump(tr, lead=-3.0):
    """free left arm: big sprint pump, elbow ~90deg, from behind hip to chin"""
    def lR(t):
        c=cosp(t-lead+0.5,20.0)
        th=math.radians(33.0+70.0*c); R=39.5-3.5*c
        lat=2.0+8.0*c
        return (R*math.sin(th), lat, -R*math.cos(th))
    tr["lR"]=Fn(lR)
    tr["lpv"]=Fn(lambda t: nrm((-0.75+0.25*cosp(t-lead+0.5,20.0), -0.42, -0.33-0.67*cosp(t-lead+0.5,20.0))))
    tr["lback"]=K((-0.15,-1.0,0.2))
def saber_run(S=2000):
    cfg=RunCfg()
    tr=run_tracks(cfg)
    run_left_pump(tr, cfg.lead)
    tr["rR"]=Fn(lambda t: (-30.0+2.5*cosp(t-cfg.lead-1.0,20.0), 14.0, -36.0+2.2*cosp(t-4.0,10.0)))
    tr["rD"]=Fn(lambda t: nrm((-0.86, 0.32+0.03*cosp(t-cfg.lead-1.0,20.0), -0.40+0.05*cosp(t-4.5,10.0))))
    tr["rDt"]=K(0.5)
    tr["rpv"]=K((-0.35,0.9,0.25))
    return Clip("AS_Saber_Run_V3", S, 20, tr, loop=True, extra={"fing":{"r":1.0,"l":0.65}})
ALL={"run":saber_run}
# ---------------- keyframe helpers ----------------
def mk(keys):
    """keys: list of (frame, dict). every channel -> Catmull-Rom track over the frames where it is given"""
    ch={}
    for f,d in keys:
        for k,v in d.items(): ch.setdefault(k,{})[float(f)]=v
    return {k:Tr(sorted(v.items())) for k,v in ch.items()}
def loopD(alpha, n):
    n=nrm(n); up=(0.0,0.0,1.0)
    u=nrm(sub(up, mulv(n, dot(n,up)))); r=nrm(cross(u,n))
    return arcv(alpha, u, r)
def P2(base, **kw):
    d=dict(base); d.update(kw); return d
def foot_base(s):
    return CAL_OFF["W_foot_%s_ik_ctrl"%s][0]

# ================= DUAL WIELD (Jar'Kai) set =================
DUAL_READY=dict(yaw=12.0, bend=7.0, lean=0.0, dz=-12.0, dfwd=0.0, dside=0.0, syaw=-2.0, sbend=1.5, slean=0.0,
    hyaw=0.0, hpitch=-3.0, hroll=0.0, hc=0.9, th=0.0,
    lf=(9.0,4.0,0.0), lfy=-2.0, lfp=0.0, rf=(-2.0,4.0,0.0), rfy=4.0, rfp=0.0,
    rP=(30.0,30.0,130.0), rD=U3(0.3,0.05,0.95), rpv=(-0.3,0.8,-0.5), rtw=0.0,
    lP=(28.0,-24.0,100.0), lD=U3(0.8,0.25,-0.55), lpv=(-0.4,-0.7,-0.6), ltw=0.0)
DR=DUAL_READY
def dual_Q():
    fb=foot_base("l"); return (fb[0]+DR["lf"][0], fb[1]+DR["lf"][1], 0.0)
def RFd(a,b,c): return add(DR["rf"],(a,b,c))
def LFd(a,b,c): return add(DR["lf"],(a,b,c))
DUALX={"fing":{"r":1.0,"l":1.0},"weapon":"dual"}
# ---- idle (60f loop) ----
def dual_idle(S=2800):
    T=60.0; w=2*math.pi/T
    tr={k:K(v) for k,v in DR.items()}
    tr["dside"]=Fn(lambda t: 1.3*(math.sin(w*t)))
    tr["lean"]=Fn(lambda t: DR["lean"]+1.0*(math.sin(w*t+0.4)-math.sin(0.4)))
    tr["dz"]=Fn(lambda t: DR["dz"]-0.6*(1-math.cos(2*w*t))/2.0)
    tr["sbend"]=Fn(lambda t: DR["sbend"]-0.8*(math.sin(w*t+1.2)-math.sin(1.2)))
    tr["yaw"]=Fn(lambda t: DR["yaw"]+2.0*(math.sin(w*t+1.0)-math.sin(1.0)))
    tr["syaw"]=Fn(lambda t: DR["syaw"]+0.8*(math.sin(w*t+1.7)-math.sin(1.7)))
    tr["hyaw"]=Fn(lambda t: 3.0*(math.sin(w*t+2.2)-math.sin(2.2)))
    tr["hpitch"]=Fn(lambda t: DR["hpitch"]+1.2*(math.sin(w*t+0.6)-math.sin(0.6)))
    tr["rP"]=Fn(lambda t: add(DR["rP"], (1.4*(math.sin(w*t+0.3)-math.sin(0.3)), 1.2*(math.cos(w*t+0.3)-math.cos(0.3)), 1.8*(math.sin(2*w*t+1.4)-math.sin(1.4)))))
    tr["rD"]=Fn(lambda t: nrm(add(DR["rD"], (0.06*(math.sin(w*t+1.1)-math.sin(1.1)), 0.05*(math.cos(w*t+1.1)-math.cos(1.1)), 0.0))))
    tr["lP"]=Fn(lambda t: add(DR["lP"], (1.4*(math.sin(w*t+2.0)-math.sin(2.0)), 1.1*(math.cos(w*t+2.0)-math.cos(2.0)), 1.6*(math.sin(2*w*t+0.9)-math.sin(0.9)))))
    tr["lD"]=Fn(lambda t: nrm(add(DR["lD"], (0.05*(math.sin(w*t+2.4)-math.sin(2.4)), 0.06*(math.cos(w*t+2.4)-math.cos(2.4)), 0.04*(math.sin(w*t+0.2)-math.sin(0.2))))))
    return Clip("AS_Dual_Idle", S, 60, tr, loop=True, extra=DUALX)
# ---- run (20f loop): both arms swept back, both blades trailing ----
def dual_run(S=2900):
    cfg=RunCfg()
    tr=run_tracks(cfg)
    tr["rR"]=Fn(lambda t: (-30.0+3.0*cosp(t-cfg.lead-1.0,20.0), 14.0, -36.0+2.2*cosp(t-4.0,10.0)))
    tr["rD"]=Fn(lambda t: nrm((-0.86, 0.32+0.03*cosp(t-cfg.lead-1.0,20.0), -0.40+0.05*cosp(t-4.5,10.0))))
    tr["rDt"]=K(0.5); tr["rpv"]=K((-0.35,0.9,0.25))
    tr["lRs"]=Fn(lambda t: (-30.0-3.0*cosp(t-cfg.lead-1.0,20.0), -14.0, -36.0+2.2*cosp(t-4.5,10.0)))
    tr["lD"]=Fn(lambda t: nrm((-0.86, -0.32+0.03*cosp(t-cfg.lead-1.0,20.0), -0.40+0.05*cosp(t-5.0,10.0))))
    tr["lDt"]=K(0.5); tr["lpv"]=K((-0.35,-0.9,0.25))
    return Clip("AS_Dual_Run", S, 20, tr, loop=True, extra=DUALX)
# ---- block (30f loop): crossed-blades X guard ----
DUAL_BLOCK=dict(yaw=4.0, syaw=-1.0, bend=6.0, dz=-13.0, dfwd=1.0, sbend=0.5, hpitch=-2.0, hc=0.9,
    rP=(30.0,18.0,120.0), rD=U3(0.35,-0.45,0.82), rpv=(-0.3,0.8,-0.5),
    lP=(30.0,-18.0,120.0), lD=U3(0.35,0.45,0.82), lpv=(-0.3,-0.8,-0.5))
def dual_block(S=3400):
    T=30.0; w=2*math.pi/T
    base=dict(DR); base.update(DUAL_BLOCK)
    tr={k:K(v) for k,v in base.items()}
    B=DUAL_BLOCK
    tr["yaw"]=Fn(lambda t: B["yaw"]+1.5*math.sin(w*t+0.5))
    tr["syaw"]=Fn(lambda t: B["syaw"]+0.6*math.sin(w*t+1.1))
    tr["dz"]=Fn(lambda t: B["dz"]-0.7*(1-math.cos(w*t))/2)
    tr["sbend"]=Fn(lambda t: B["sbend"]+0.8*math.sin(w*t+2.0))
    tr["dside"]=Fn(lambda t: 1.0*math.sin(w*t+2.4))
    tr["hyaw"]=Fn(lambda t: 2.0*math.sin(w*t+0.9))
    tr["rP"]=Fn(lambda t: add(B["rP"], (1.0*math.sin(w*t), 1.2*math.cos(w*t), 1.3*math.sin(w*t+0.7))))
    tr["lP"]=Fn(lambda t: add(B["lP"], (1.0*math.sin(w*t+0.4), -1.2*math.cos(w*t+0.4), 1.3*math.sin(w*t+1.1))))
    tr["rD"]=Fn(lambda t: nrm(add(B["rD"], (0.03*math.sin(w*t+1.0), 0.035*math.cos(w*t+0.4), 0.0))))
    tr["lD"]=Fn(lambda t: nrm(add(B["lD"], (0.03*math.sin(w*t+1.4), -0.035*math.cos(w*t+0.8), 0.0))))
    return Clip("AS_Dual_Block", S, 30, tr, loop=True, extra=DUALX)
# ---- combo 1: alternating right / left diagonal slashes ----
def dual_c1(S=3000):
    K_=[(0,DR),
        (2,dict(rP=(10,32,142), rD=U3(-0.45,0.35,0.82), yaw=20, syaw=2, dz=-11, bend=5, lP=(26,-22,104), lD=U3(0.75,0.3,-0.6), rpv=(-0.2,0.8,-0.5))),
        (3,dict(rP=(8,33,144), rD=U3(-0.5,0.35,0.8), yaw=22, syaw=3)),
        (4,dict(rP=(22,26,140), rD=U3(0.35,0.35,0.87), yaw=14, syaw=1, dz=-12, lf=LFd(4,0,3), lfp=5)),
        (5,dict(rP=(38,14,122), rD=U3(0.96,0.1,0.25), yaw=2, syaw=-2, dz=-14, bend=9, dfwd=3, lf=LFd(9,0,0), lfp=0, lP=(18,-26,112), lD=U3(0.2,-0.2,0.96))),
        (6,dict(rP=(38,0,104), rD=U3(0.6,-0.6,-0.52), yaw=-8, syaw=-4, dz=-16, bend=12, dfwd=6)),
        (7,dict(rP=(36,-2,99), rD=U3(0.42,-0.64,-0.64), yaw=-14, syaw=-5, dz=-17, bend=13, lP=(16,-34,140), lD=U3(-0.35,-0.25,0.9), lpv=(-0.3,-0.8,-0.5))),
        (8,dict(rP=(34,0,101), rD=U3(0.4,-0.65,-0.64), yaw=-16, lP=(14,-35,143), lD=U3(-0.38,-0.25,0.89))),
        (9,dict(yaw=-12, syaw=-4, lP=(20,-26,140), lD=U3(0.35,-0.35,0.87), rP=(24,8,106), rD=U3(0.3,-0.3,-0.9), rf=RFd(3,0,3), rfp=6)),
        (10,dict(lP=(36,-14,122), lD=U3(0.96,-0.1,0.25), yaw=-2, syaw=1, dz=-15, rP=(18,22,116), rD=U3(0.1,0.3,0.95), rf=RFd(7,1,0), rfp=0)),
        (11,dict(lP=(38,0,104), lD=U3(0.6,0.6,-0.52), yaw=10, syaw=4, dz=-17, bend=13, dfwd=8, rP=(14,30,130), rD=U3(-0.1,0.3,0.95))),
        (12,dict(lP=(36,2,99), lD=U3(0.42,0.64,-0.64), yaw=16, syaw=5, dz=-18, bend=14)),
        (13,dict(lP=(34,1,100), lD=U3(0.4,0.65,-0.64), yaw=18)),
        (15,dict(lP=(31,-8,99), lD=U3(0.55,0.55,-0.63), yaw=16, syaw=2, dz=-16, bend=11, dfwd=5, rP=(28,31,131), rD=U3(0.25,0.1,0.96), lf=LFd(6,0,2), rf=RFd(4,1,0))),
        (18,dict(lP=(29,-20,100), lD=U3(0.78,0.3,-0.55), yaw=13, syaw=-1, dz=-13, bend=8, dfwd=1.5, lf=LFd(1,0,0), rf=RFd(1,0,0))),
        (22,DR)]
    return Clip("AS_Dual_Combo1", S, 22, mk(K_), extra=DUALX)
# ---- combo 2: X cross-cut (both blades from high to low, crossing) ----
def dual_c2(S=3100):
    K_=[(0,DR),
        (2,dict(rP=(14,32,142), rD=U3(-0.2,0.35,0.92), lP=(18,-30,128), lD=U3(0.1,-0.4,0.91), dz=-10, bend=4, yaw=8, syaw=-1, lpv=(-0.3,-0.8,-0.5))),
        (4,dict(rP=(8,34,150), rD=U3(-0.45,0.4,0.8), lP=(8,-34,150), lD=U3(-0.45,-0.4,0.8), dz=-8, bend=1, sbend=-1, hpitch=-5, lf=LFd(4,0,3), lfp=5)),
        (5,dict(rP=(12,33,152), rD=U3(-0.5,0.4,0.77), lP=(12,-33,152), lD=U3(-0.5,-0.4,0.77))),
        (6,dict(rP=(30,22,138), rD=U3(0.55,0.45,0.7), lP=(28,-22,136), lD=U3(0.55,-0.45,0.7), dz=-12, bend=8, dfwd=4, lf=LFd(12,0,1), lfp=0, sbend=1.5)),
        (7,dict(rP=(42,6,118), rD=U3(0.95,-0.05,-0.3), lP=(38,-6,114), lD=U3(0.95,0.05,-0.3), dz=-17, bend=14, dfwd=9, lf=LFd(16,-0.5,0))),
        (8,dict(rP=(40,-4,106), rD=U3(0.55,-0.52,-0.65), lP=(34,4,100), lD=U3(0.55,0.52,-0.65), dz=-20, bend=17, dfwd=11)),
        (9,dict(rP=(38,-6,104), rD=U3(0.5,-0.52,-0.69), lP=(32,6,98), lD=U3(0.5,0.52,-0.69), dz=-21, bend=18)),
        (11,dict(rP=(38,-5,105), rD=U3(0.52,-0.5,-0.69), lP=(32,5,99), lD=U3(0.52,0.5,-0.69), dz=-20, bend=17)),
        (13,dict(rP=(38,18,112), rD=U3(0.95,0.15,0.1), lP=(36,-14,102), lD=U3(0.85,-0.1,-0.5))),
        (15,dict(rP=(33,26,122), rD=U3(0.55,0.05,0.83), lP=(33,-20,101), lD=U3(0.8,0.1,-0.58), dz=-16, bend=12, dfwd=6, lf=LFd(9,0,2))),
        (17,dict(rP=(31,29,129), rD=U3(0.33,0.05,0.94), lP=(30,-23,100), lD=U3(0.8,0.2,-0.56), dz=-13, bend=8, dfwd=2, lf=LFd(2,0,0))),
        (20,DR)]
    return Clip("AS_Dual_Combo2", S, 20, mk(K_), extra=DUALX)
# ---- combo 3: double-spin whirlwind (CCW 720, arms out) ----
def dual_c3(S=3200):
    rOut=U3(0.6,0.78,-0.1); lOut=U3(-0.7,-0.7,-0.05)
    K_=[(0,DR),
        (2,dict(th=14, yaw=18, syaw=2, dz=-15, bend=10, rP=(14,36,124), rD=U3(0.2,0.7,0.68), lP=(22,-28,108), lD=U3(0.4,-0.6,-0.1))),
        (4,dict(th=32, yaw=22, syaw=4, dz=-17, bend=12, rP=(6,58,124), rD=rOut, lP=(8,-56,120), lD=lOut, rpv=(-0.3,0.6,-0.75), lpv=(-0.3,-0.6,-0.75))),
        (6,dict(th=-10, yaw=14, dz=-14, rf=RFd(1,1,6), rfp=8, lean=-4, hyaw=-18)),
        (8,dict(th=-95, yaw=10, dz=-11, bend=9, rf=RFd(2,2,12), lean=-6, hyaw=-28, rD=U3(0.6,0.78,-0.02), lD=U3(-0.7,-0.7,-0.12))),
        (10,dict(th=-185, dz=-9, rf=RFd(2,2,14))),
        (12,dict(th=-275, dz=-10, rf=RFd(1,1,6), rD=U3(0.6,0.78,-0.15), lD=U3(-0.7,-0.7,0.02))),
        (13,dict(th=-320, dz=-12, rf=RFd(1,1,2))),
        (14,dict(th=-365, dz=-10, rf=RFd(1,1,6))),
        (16,dict(th=-455, dz=-9, rf=RFd(2,2,12), rD=U3(0.6,0.78,0.0), lD=U3(-0.7,-0.7,-0.14))),
        (18,dict(th=-545, dz=-10, rf=RFd(2,2,12))),
        (20,dict(th=-635, yaw=12, dz=-13, rf=RFd(1,1,6), lean=-4, hyaw=-20, rD=U3(0.6,0.78,-0.1))),
        (22,dict(th=-705, yaw=14, dz=-16, bend=11, rf=RFd(0,0,0), rfp=0, lean=0, hyaw=0)),
        (23,dict(th=-724)),
        (24,dict(th=-722, rP=(20,42,124), rD=U3(0.45,0.5,0.74), lP=(18,-34,108), lD=U3(0.5,-0.55,-0.4), dz=-15)),
        (26,dict(th=-720.0, rP=(27,32,129), rD=U3(0.32,0.12,0.94), lP=(25,-26,102), lD=U3(0.75,0.15,-0.62), dz=-13, bend=8)),
        (28,P2(DR, th=-720.0))]
    return Clip("AS_Dual_Combo3", S, 28, mk(K_), Q=dual_Q(), extra=DUALX)
# ---- combo 4: scissor-cut finisher (wide wind, lunge, blades snap together crossing in front) ----
def dual_c4(S=3300):
    K_=[(0,DR),
        (2,dict(rP=(10,40,132), rD=U3(0.2,0.8,0.56), lP=(12,-38,118), lD=U3(0.2,-0.85,0.45), dz=-11, bend=5, yaw=10, lpv=(-0.3,-0.8,-0.5))),
        (4,dict(rP=(-2,46,128), rD=U3(-0.15,0.92,0.35), lP=(-2,-46,126), lD=U3(-0.15,-0.92,0.35), dz=-9, bend=2, sbend=-1.5, hpitch=-5, yaw=6, syaw=0, lf=LFd(3,0,4), lfp=6)),
        (5,dict(rP=(-4,47,128), rD=U3(-0.2,0.92,0.33), lP=(-4,-47,126), lD=U3(-0.2,-0.92,0.33))),
        (6,dict(rP=(14,44,126), rD=U3(0.35,0.9,0.25), lP=(14,-44,124), lD=U3(0.35,-0.9,0.25), dz=-13, bend=9, dfwd=5, lf=LFd(12,0,3), sbend=1.5)),
        (7,dict(rP=(34,28,122), rD=U3(0.9,0.4,0.12), lP=(34,-28,120), lD=U3(0.9,-0.4,0.12), dz=-17, bend=14, dfwd=10, lf=LFd(20,-1,0), lfp=0)),
        (8,dict(rP=(54,22,122), rD=U3(0.72,-0.69,0.08), lP=(52,-22,118), lD=U3(0.72,0.69,0.08), dz=-19, bend=13, dfwd=13)),
        (9,dict(rP=(56,16,121), rD=U3(0.5,-0.86,0.05), lP=(54,-16,117), lD=U3(0.5,0.86,0.05), dz=-20, bend=13, dfwd=14)),
        (11,dict(rP=(55,17,121), rD=U3(0.53,-0.84,0.1), lP=(53,-17,117), lD=U3(0.53,0.84,0.1), dz=-19, bend=12)),
        (13,dict(rP=(46,22,120), rD=U3(0.92,0.25,0.3), lP=(44,-20,108), lD=U3(0.9,-0.2,-0.38), bend=12)),
        (15,dict(rP=(34,26,124), rD=U3(0.62,0.1,0.78), lP=(34,-20,104), lD=U3(0.85,0.05,-0.52), dz=-17, bend=13, dfwd=10, lf=LFd(14,-0.5,2))),
        (18,dict(rP=(31,29,130), rD=U3(0.35,0.06,0.93), lP=(30,-23,101), lD=U3(0.8,0.22,-0.56), dz=-13.5, bend=8, dfwd=3, lf=LFd(4,0,1))),
        (22,DR)]
    return Clip("AS_Dual_Combo4", S, 22, mk(K_), extra=DUALX)
ALL.update({"d_idle":dual_idle,"d_run":dual_run,"d_block":dual_block,"d_c1":dual_c1,"d_c2":dual_c2,"d_c3":dual_c3,"d_c4":dual_c4})

NAME='d_idle'
FRAMES=[60]
FIRST=False
PARTS='bfa'

def run():
    c=ALL[NAME]()
    if FIRST:
        guard()
        fg=c.extra.get("fing",{})
        for s in "lr":
            v=fg.get(s, 1.0 if s=="r" else 0.0)
            if isinstance(v, list):
                for f,val in v: fingers(s, c.S+f, val)
            else:
                for f in (c.S, c.S+c.T): fingers(s, f, v)
        for s in "rl": setb("arm_%s_fk_ik_switch"%s, c.S-1, True)
    return bake(c, frames=FRAMES, parts=PARTS)

