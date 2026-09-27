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
