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
