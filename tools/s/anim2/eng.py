
# ================= pose engine =================
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
def C(v): return Tr([(0,v)])
# ---- calibration (filled by calib()) ----
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
# body_ctrl local location axes -> char delta (set from axis test)
BLOC=((0,-1,0),(1,0,0),(0,0,1))   # local x -> char (f,r,u) ; local y ; local z
def bl_to_c(d): return add(add(mulv(BLOC[0],d[0]),mulv(BLOC[1],d[1])),mulv(BLOC[2],d[2]))
def c_to_bl(v): return (dot(BLOC[0],v),dot(BLOC[1],v),dot(BLOC[2],v))
REACH=50.0
FOOTAZ={"l":12.6,"r":40.8}
def clampP(P, S, reach):
    d=sub(P,S); L=vlen(d)
    return P if L<=reach else add(S, mulv(d, reach/L))
def pole(S, P, hint, dist=40.0):
    A=nrm(sub(P,S)); h=nrm(hint); h=sub(h, mulv(A, dot(h,A)))
    if vlen(h)<1e-3: h=(0,0,-1)
    return add(add(S, mulv(sub(P,S),0.5)), mulv(nrm(h), dist))
def env(t, T, a=2.0, b=3.0):
    return max(0.0, min(1.0, t/a, (T-t)/b))
class Clip:
    """tr: dict of Tracks. leads: per-group time leads (frames)."""
    def __init__(self, name, start, T, tr, leads=None, Q=(0,0,0), loop=False, lgrip=False, extra=None):
        self.name=name; self.S=start; self.T=T; self.tr=tr; self.Q=Q; self.loop=loop
        self.L=dict(pel=1.2, sp=0.6, hd=0.4, ft=0.8, arm=0.0, bl=-0.6, la=0.3)
        if leads: self.L.update(leads)
    def g(self, name, t, grp, default=0.0):
        tr=self.tr.get(name)
        if tr is None: return default
        if self.loop: return tr(t)
        e=env(t,self.T)
        return tr(min(self.T, max(0.0, t+self.L[grp]*e)))
    def pose(self, t):
        g=self.g; p={}
        for n in ["yaw","bend","lean","dz","dfwd","dside"]: p[n]=g(n,t,"pel")
        for n in ["syaw","sbend","slean"]: p[n]=g(n,t,"sp")
        for n in ["hyaw","hpitch","hroll"]: p[n]=g(n,t,"hd")
        p["th"]=g("th",t,"pel")
        for s in "lr":
            p[s+"f"]=g(s+"f",t,"ft",(0,0,0)); p[s+"fy"]=g(s+"fy",t,"ft"); p[s+"fp"]=g(s+"fp",t,"ft")
        p["rP"]=g("rP",t,"arm"); p["rD"]=nrm(g("rD",t,"bl")); p["rpv"]=g("rpv",t,"arm",(-0.3,0.6,-0.75)); p["rtw"]=g("rtw",t,"bl")
        p["lR"]=g("lR",t,"la",None); p["lback"]=g("lback",t,"la",(-0.2,-1,0.1)); p["lpv"]=g("lpv",t,"la",(-0.4,-0.6,-0.7)); p["lg"]=g("lg",t,"arm")
        p["hc"]=g("hc",t,"hd",0.6)
        return p
def spinp(p, th, Q):
    return add(Q, Rz(sub(p,Q), th))
def key_body(F, p, Q):
    c=calib()
    th=p["th"]
    bl,br=c["L_body_ctrl"]; pw,_=c["W_body_ctrl"]
    d=(p["dside"], p["dfwd"], p["dz"])   # char-ish: side(+right), fwd, up
    pc=add(pw, (d[1], d[0], d[2]))
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
def key_feet(F, p, Q):
    c=calib()
    th=p["th"]
    pel=add(c["W_body_ctrl"][0], (p["dfwd"], p["dside"], p["dz"]))
    for s in "lr":
        fb,frot=c["W_foot_%s_ik_ctrl"%s]; pb,_=c["W_leg_%s_pv_ik_ctrl"%s]
        off=p[s+"f"]; fy=p[s+"fy"]; fp=p[s+"fp"]
        pos=add(fb, off)
        rot=rotz_rot(frot, fy)
        if abs(fp)>0.01:
            lat=Rz((0,1,0),fy)
            rot=rot_about(rot, lat, fp)
            if fp>0:
                fwd=Rz((1,0,0),fy+FOOTAZ[s]); ball=add(pos, add(mulv(fwd,14.0),(0,0,-8.0)))
                pos=add(ball, rodr(sub(pos,ball), lat, fp))
        pos_w=spinp(pos, th, Q); rot_w=rotz_rot(rot, th)
        setw("foot_%s_ik_ctrl"%s, F, pos_w, rot_w)
        # knee pole: in front of knee, following foot yaw
        rel=sub(pb, fb)
        pv=add(pos, Rz(rel, fy))
        pv=add(pv, (0,0,(p["dz"])*0.5))
        setw("leg_%s_pv_ik_ctrl"%s, F, spinp(pv, th, Q))
def key_arms(F, p, Q):
    th=p["th"]
    show(F)
    S=wpos("upperarm_r_fk_ctrl", F)
    if abs(S[2])>400 or S[2]<40: raise RuntimeError("bad shoulder read %s at %d"%(str(S),F))
    rP=spinp(p["rP"], th, Q); rD=nrm(Rz(p["rD"], th))
    P=clampP(rP, S, REACH); A=nrm(sub(P,S))
    rr=hand_rot(rD, A, p["rtw"])
    setw("hand_r_ik_ctrl", F, P, rr)
    setw("arm_r_pv_ik_ctrl", F, pole(S,P,Rz(p["rpv"],th)))
    out={"P":P,"D":rD,"S":S}
    if p["lR"] is not None:
        SL=wpos("upperarm_l_fk_ctrl", F)
        psi=p["yaw"]+3*p["syaw"]+th
        lP=add(SL, Rz(p["lR"], psi)); lback=Rz(p["lback"], psi); lpvh=Rz(p["lpv"], psi)
        lg=max(0.0,min(1.0,p["lg"]))
        if lg>0.001:
            m=Mr(*rr); cz=Wd(m[2])
            gP=add(P, mulv(rD, 8.5)); gb=mulv(cz,-1.0)
            lP=add(mulv(lP,1-lg), mulv(gP,lg)); lback=add(mulv(lback,1-lg), mulv(gb,lg))
            lpvh=add(mulv(lpvh,1-lg), mulv(Rz((-0.3,-0.75,-0.6),th),lg))
        Pl=clampP(lP, SL, REACH); Al=nrm(sub(Pl,SL))
        setw("hand_l_ik_ctrl", F, Pl, lhand_rot(Al, lback))
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
def analyze(clip, blade=100.0):
    rows=[]; prev=None
    for i in range(0, clip.T+1):
        F=clip.S+i; show(F)
        w=getw("hand_r_ik_ctrl",F); P=Cp(tup(w["location"])); D=blade_of(tup(w["rotation"]))
        tip=add(P, mulv(D,blade)); mid=add(P, mulv(D,blade*0.6))
        sp=0.0 if prev is None else vlen(sub(tip,prev))*30.0
        prev=tip
        rows.append([i, round(sp), [round(x) for x in tip], [round(x,2) for x in D]])
    return rows
FING=[("index",-65),("middle",-72),("ring",-78),("pinky",-82)]
FCACHE={}
def fingers(side, F, curl):
    """side 'l'/'r'; curl True -> saber grip; False -> MM_Idle relaxed values (BASEF)"""
    for f,base in FING:
        for j in ["01","02","03"]:
            c="%s_%s_%s_ctrl"%(f,j,side)
            if c not in FCACHE:
                e=geteul(c,BASEF); FCACHE[c]=(tup(e["location"]),tup(e["rotation"]))
            l,r=FCACHE[c]
            if curl:
                if j=="01": rr=(r[0],base,r[2])
                elif j=="02": rr=(0,-85,0)
                else: rr=(0,-55,0)
                setl(c,F,(0,0,0),rr)
            else:
                setl(c,F,l,r)
