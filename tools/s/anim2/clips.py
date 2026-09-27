
# ================= clip definitions =================
class Fl:
    def __init__(self,v): self.v=v
def mk(keys, period=None):
    ch={}
    for f,d in keys:
        for k,v in d.items():
            if isinstance(v,Fl): ch.setdefault(k,[]).append((f,v.v,'f'))
            else: ch.setdefault(k,[]).append((f,v))
    return {k:Tr(v, period) for k,v in ch.items()}
class Fn:
    def __init__(self,f): self.f=f
    def __call__(self,t): return self.f(t)
def U3(*a): return nrm(a)
FLOW=dict(yaw=10.0, bend=6.0, lean=-1.0, dz=-9.0, dfwd=2.0, dside=0.0, syaw=-2.0, sbend=1.0, slean=0.0,
          hyaw=0.0, hpitch=0.0, hroll=0.0, th=0.0,
          lf=(6.0,-1.0,0.0), lfy=-14.0, lfp=0.0, rf=(-6.0,2.0,0.0), rfy=-8.0, rfp=0.0,
          rP=(26.0,20.0,106.0), rD=U3(0.5,0.15,0.85), rpv=(-0.3,0.6,-0.75), rtw=0.0,
          lR=(12.0,-12.0,-36.0), lg=0.0)
def FL(**kw):
    d=dict(FLOW); d.update(kw); return d
def LF(a,b,c): return add(FLOW["lf"],(a,b,c))
def RF(a,b,c): return add(FLOW["rf"],(a,b,c))
def pivotQ():
    c=calib(); fb=c["W_foot_l_ik_ctrl"][0]
    return (fb[0]+FLOW["lf"][0], fb[1]+FLOW["lf"][1], 0.0)
# ---------- arcs
def arcP(C,R,U,V,phi): return add(C, mulv(arcv(phi,U,V),R))
# ---------------- COMBO 1: forehand diagonal high-right -> low-left, left foot steps in
def combo1(S=500):
    U=(1,0,0); V=U3(0,0.55,0.83); Cc=(16,8,122); R=31
    P=lambda ph: arcP(Cc,R,U,V,ph); D=lambda ph: arcv(ph,U,V)
    K=[(0,FL()),
       (2,dict(rP=(14,26,128), rD=U3(-0.1,0.35,0.93), yaw=24, syaw=5, dz=-7.5, bend=3, dside=2, dfwd=0, rpv=(-0.3,0.8,-0.5))),
       (4,dict(rP=P(126), rD=D(138), yaw=32, syaw=8, dz=-6.5, bend=1, lean=1, dside=3, dfwd=-3, rpv=(-0.2,0.9,-0.4))),
       (5,dict(rP=P(132), rD=D(150), yaw=34, syaw=8.5, dz=-6.5, bend=0, dfwd=-3, lf=LF(0,0,0), lfp=0)),
       (6,dict(rP=P(102), rD=D(122), yaw=16, syaw=6, dz=-8, bend=4, dfwd=1, lf=LF(9,-1,6), lfp=-8)),
       (7,dict(rP=P(38), rD=D(52))),
       (8,dict(rP=P(-38), rD=D(-30), yaw=-24, syaw=-6, dz=-15, bend=14, lean=-2, dside=-3, dfwd=10, lf=LF(21,-3,0), lfp=0, rfp=12, rfy=-21, rpv=(0.2,0.8,-0.5))),
       (9,dict(rP=P(-94), rD=D(-100), yaw=-33, syaw=-9, dz=-17, bend=17, dfwd=13, dside=-4)),
       (11,dict(rP=P(-116), rD=D(-128), yaw=-41, syaw=-11, dz=-18.5, bend=18.5, dfwd=13.5, lf=LF(21,-3,0), rfp=20, rfy=-28, rpv=(0.1,0.7,-0.7))),
       (13,dict(rP=P(-106), rD=D(-114), yaw=-32, syaw=-8, dz=-16, bend=15, dfwd=11, lf=LF(21,-3,0), rfp=14)),
       (14.5,dict(rP=(9,-8,99), rD=U3(0.45,-0.62,-0.64), yaw=-20, syaw=-6, dz=-14, bend=12, dfwd=9, lf=LF(16,-2,3))),
       (16,dict(rP=(16,0,104), rD=U3(0.88,-0.42,0.22), yaw=-6, syaw=-4, dz=-11.5, bend=9, dfwd=6, dside=-1, lf=LF(8,-1,3), rfp=4, rfy=-14)),
       (17,dict(rP=(23,12,106), rD=U3(0.62,-0.02,0.78))),
       (18,FL())]
    K+=[(4,dict(lR=(36,-4,-14), lback=(0,-0.3,1), lpv=(-0.2,-0.3,-1))),
        (8,dict(lR=(-10,-16,-35), lback=(-0.2,-1,0.1), lpv=(-0.6,-0.6,-0.5))),
        (11,dict(lR=(-18,-18,-32))),
        (16,dict(lR=(6,-14,-36), lback=(-0.2,-1,0.1), lpv=(-0.4,-0.6,-0.7)))]
    return Clip("AS_Saber_Combo1_V2", S, 18, mk(K))
# ---------------- COMBO 2: rising backhand low-left -> high-right
def combo2(S=600):
    U=(1,0,0); V=U3(0,-0.8,-0.6); Cc=(22,6,112); R=30
    P=lambda ph: arcP(Cc,R,U,V,ph); D=lambda ph: arcv(ph,U,V)
    K=[(0,FL()),
       (1,dict(rP=(27,14,105), rD=U3(0.38,0.07,0.92))),
       (2,dict(rP=(24,4,101), rD=U3(0.16,-0.2,0.97), yaw=-14, syaw=-4, dz=-11, bend=7, dside=-1, rpv=(-0.2,0.7,-0.7))),
       (3,dict(rP=(16,-5,99), rD=U3(-0.18,-0.66,0.73))),
       (4,dict(rP=(6,-12,97), rD=U3(-0.62,-0.78,0.1), yaw=-33, syaw=-9, dz=-13.5, bend=9, lean=2, dside=-3, lfy=-26, rpv=(0.3,0.6,-0.7))),
       (5,dict(rP=P(136), rD=D(152), yaw=-38, syaw=-10, dz=-14, bend=9, lean=3, rf=RF(0,0,0), rfp=10)),
       (6,dict(rP=P(110), rD=D(128), yaw=-24, syaw=-7, dz=-13, rf=RF(5,4,5), rfp=0)),
       (7,dict(rP=P(46), rD=D(62))),
       (8,dict(rP=P(-32), rD=D(-20), yaw=18, syaw=5, dz=-9, bend=5, lean=-2, dside=2, rf=RF(10,9,0), lfy=-10, lfp=10, rpv=(-0.2,0.8,-0.6))),
       (9,dict(rP=P(-90), rD=D(-96), yaw=30, syaw=8, dz=-7, bend=3, lean=-3, dside=3)),
       (11,dict(rP=P(-124), rD=D(-140), yaw=40, syaw=10, dz=-6, bend=1, rf=RF(10,9,0), lfp=14, rpv=(-0.4,0.8,-0.4))),
       (13,dict(rP=P(-114), rD=D(-126), yaw=32, syaw=7, dz=-7, bend=3, rf=RF(10,9,0), lfp=8)),
       (15,dict(rP=(25,23,112), rD=U3(0.38,0.22,0.9), yaw=16, syaw=0, dz=-8.5, bend=5, rf=RF(4,3,3), lfp=0, lfy=-14)),
       (16,FL())]
    K+=[(4,dict(lR=(-16,-20,-28), lback=(-0.3,-1,0.2), lpv=(-0.6,-0.5,-0.6))),
        (9,dict(lR=(24,-24,-22), lback=(0,-0.6,0.8), lpv=(-0.3,-0.5,-0.8))),
        (11,dict(lR=(26,-26,-18))),
        (15,dict(lR=(14,-14,-34), lback=(-0.2,-1,0.1), lpv=(-0.4,-0.6,-0.7)))]
    return Clip("AS_Saber_Combo2_V2", S, 16, mk(K))
# ---------------- COMBO 3: spinning horizontal slash (CCW 360, pivot on left foot)
def combo3(S=700):
    K=[(0,FL()),
       (1.5,dict(rP=(14,28,106), rD=U3(0.1,0.75,0.65))),
       (3,dict(th=8, yaw=28, syaw=7.5, dz=-12, bend=8, rP=(4,34,104), rD=U3(-0.6,0.8,-0.05), rpv=(-0.1,0.8,-0.6), rfp=8)),
       (5,dict(th=2, yaw=34, syaw=9, dz=-13, bend=9, rP=(0,35,103), rD=U3(-0.76,0.65,-0.05), rfp=22, lfp=6)),
       (7,dict(th=-68, yaw=2, syaw=0, dz=-10, bend=10, lean=-6, rP=(24,38,104), rD=U3(0.2,0.98,0.0), rf=RF(4,3,9), rfp=5, lfp=16, rpv=(-0.2,0.7,-0.7), hyaw=-25)),
       (9,dict(th=-168, yaw=-18, syaw=-4, dz=-8, bend=10, lean=-8, rP=(30,36,106), rD=U3(0.55,0.83,0.02), rf=RF(5,4,14), hyaw=-38)),
       (11,dict(th=-265, yaw=-20, syaw=-6, dz=-8.5, lean=-8, rP=(30,34,106), rD=U3(0.6,0.8,0.02), rf=RF(3,3,10), hyaw=-35)),
       (13,dict(th=-332, yaw=-12, syaw=-5, dz=-11, lean=-4, rP=(30,30,104), rD=U3(0.75,0.6,0.0), rf=RF(0,1,2), rfp=-4, lfp=10, hyaw=-12)),
       (14,dict(rf=RF(0,0,0), rfp=0)),
       (15,dict(th=-357, yaw=2, syaw=-2, dz=-12.5, bend=9, lean=-1, rP=(28,22,104), rD=U3(0.7,0.3,0.65), lfp=3, hyaw=0)),
       (16.5,dict(th=-361.5)),
       (18,FL(th=-360.0))]
    K+=[(3,dict(lR=(30,-10,-20), lback=(0,-0.4,0.9), lpv=(-0.2,-0.4,-0.9))),
        (7,dict(lR=(6,-40,-12), lback=(0,-0.2,1), lpv=(-0.6,0,-0.8))),
        (11,dict(lR=(2,-40,-14))),
        (13,dict(lR=(4,-36,-20))),
        (15,dict(lR=(10,-18,-32), lback=(-0.2,-1,0.1), lpv=(-0.4,-0.6,-0.7)))]
    return Clip("AS_Saber_Combo3_V2", S, 18, mk(K), Q=pivotQ())
# ---------------- COMBO 4: overhead vertical cleave, hop-step, deep crouch (two-handed)
def combo4(S=800):
    K=[(0,FL()),
       (2,dict(rP=(16,12,140), rD=U3(0.1,0.05,1), lg=0.75, dz=-4, bend=-2, yaw=3, syaw=0, lfp=10, rfp=12, rpv=(-0.3,0.8,-0.4))),
       (4,dict(rP=(4,8,166), rD=U3(-0.6,0,0.8), lg=1.0, dz=2, bend=-8, sbend=-3, yaw=0, dfwd=4, lf=LF(2,0,2), lfp=28, rf=RF(2,0,3), rfp=32)),
       (5,dict(rP=(0,7,170), rD=U3(-0.85,0,0.52), dz=4, bend=-9, sbend=-4, dfwd=8, lf=LF(10,-1,9), lfp=10, rf=RF(8,1,10), rfp=20)),
       (6,dict(rP=(6,6,172), rD=U3(-0.55,0,0.84), dz=2, bend=-6, dfwd=12)),
       (7,dict(rP=(24,5,162), rD=U3(0.35,0,0.94), dz=-6, bend=4, sbend=1, dfwd=16, lf=LF(22,-2,3), lfp=-6, rf=RF(16,1,5), rfp=10)),
       (8,dict(rP=(40,4,132), rD=U3(0.93,0,0.36), dz=-18, bend=16, sbend=4, dfwd=19, lf=LF(24,-2,0), lfp=0, rf=RF(18,1,0), rfp=18)),
       (9,dict(rP=(44,3,100), rD=U3(0.85,0,-0.52), dz=-28, bend=24, sbend=6, dfwd=21, yaw=-4, rfp=26, rfy=-18)),
       (10,dict(rP=(42,3,92), rD=U3(0.75,0,-0.66), dz=-32, bend=26, sbend=7, dfwd=22)),
       (12,dict(rP=(42,3,95), rD=U3(0.8,0,-0.6), dz=-29, bend=24, sbend=6, dfwd=21, lg=1.0, lf=LF(24,-2,0), rf=RF(18,1,0), rfp=24)),
       (14,dict(rP=(34,10,100), rD=U3(0.85,0.1,-0.15), dz=-20, bend=16, sbend=3, dfwd=15, lg=0.8, lf=LF(18,-1,3), rf=RF(12,1,3), rfp=10)),
       (15,dict(rP=(30,16,102), rD=U3(0.7,0.15,0.5), dz=-14, bend=10, dfwd=9, lg=0.35, lf=LF(10,-1,4), rf=RF(6,1,3), rfp=4)),
       (17,FL())]
    return Clip("AS_Saber_Combo4_V2", S, 17, mk(K), leads=dict(bl=-0.4))
# ---------------- COMBO 5: whirlwind finisher (2x CCW 360) -> low flourish -> flow
def combo5(S=900):
    Dh=U3(0.35,0.85,0.4); Dl=U3(0.45,0.85,-0.25)
    K=[(0,FL()),
       (2,dict(th=8, yaw=26, syaw=7, dz=-11, bend=7, rP=(6,33,108), rD=U3(-0.55,0.8,0.2), rfp=10)),
       (3,dict(th=6, yaw=30, syaw=8, rP=(2,34,110), rD=U3(-0.7,0.7,0.15), rfp=22, lfp=6)),
       (5,dict(th=-62, yaw=5, syaw=0, lean=-7, dz=-8, bend=8, rP=(20,37,122), rD=U3(0.15,0.95,0.3), rf=RF(4,3,8), rfp=4, lfp=16, hyaw=-25)),
       (7,dict(th=-180, yaw=-15, syaw=-4, lean=-9, dz=-6, rP=(22,36,124), rD=Dh, rf=RF(6,5,14), hyaw=-35)),
       (9,dict(th=-300, yaw=-18, syaw=-5, lean=-9, dz=-6.5, rP=(22,36,122), rD=Dh, rf=RF(4,3,8))),
       (10,dict(rf=RF(1,1,2))),
       (11,dict(th=-405, yaw=-15, syaw=-4, lean=-8, dz=-10, rP=(24,36,112), rD=U3(0.4,0.87,0.08), rf=RF(2,2,6))),
       (13,dict(th=-522, yaw=-18, syaw=-5, lean=-9, dz=-13, bend=10, rP=(26,36,102), rD=Dl, rf=RF(6,5,12))),
       (15,dict(th=-632, yaw=-18, syaw=-5, lean=-8, dz=-16, bend=12, rP=(26,35,98), rD=U3(0.5,0.8,-0.3), rf=RF(4,4,8), hyaw=-30)),
       (17,dict(th=-701, yaw=-8, syaw=-2, lean=-5, dz=-20, bend=14, rP=(24,32,94), rD=U3(0.4,0.7,-0.55), rf=RF(0,3,1), rfp=-3, lfp=12, hyaw=-15)),
       (18,dict(rf=RF(-3,4,0), rfp=0)),
       (19,dict(th=-724, yaw=8, syaw=2, lean=0, dz=-25, bend=18, dside=3, rP=(16,31,86), rD=U3(-0.2,0.7,-0.6), rf=RF(-6,5,0), lfp=4, hyaw=0)),
       (21,dict(th=-721, yaw=18, syaw=5, dz=-27, bend=20, rP=(8,31,84), rD=U3(-0.6,0.5,-0.55))),
       (22.5,dict(th=-720, yaw=17, syaw=4.5, dz=-26, bend=19, dside=2.5, rP=(8,31,85), rD=U3(-0.55,0.55,-0.55), rf=RF(-6,5,0))),
       (24.5,dict(yaw=14, syaw=3, dz=-20, bend=14, dside=1.5, rP=(13,30,89), rD=U3(0.15,0.6,-0.78), rf=RF(-4,3,2))),
       (26,dict(yaw=12, syaw=0, dz=-14, bend=10, dside=0.5, rP=(19,26,97), rD=U3(0.62,0.45,-0.1), rf=RF(-2,1,2))),
       (27,dict(rP=(23,23,102), rD=U3(0.58,0.3,0.72))),
       (28,FL(th=-720.0))]
    K+=[(2,dict(lR=(30,-10,-20), lback=(0,-0.4,0.9), lpv=(-0.2,-0.4,-0.9))),
        (5,dict(lR=(4,-40,-10), lback=(0,-0.2,1), lpv=(-0.6,0,-0.8))),
        (9,dict(lR=(2,-41,-8))),
        (13,dict(lR=(2,-40,-14))),
        (17,dict(lR=(6,-38,-18))),
        (21,dict(lR=(30,-24,-4), lback=(0,-0.5,0.85), lpv=(-0.3,-0.3,-0.9))),
        (23,dict(lR=(26,-22,-10))),
        (25.5,dict(lR=(14,-14,-30), lback=(-0.2,-1,0.1), lpv=(-0.4,-0.6,-0.7)))]
    return Clip("AS_Saber_Combo5_V2", S, 28, mk(K), Q=pivotQ())
# ---------------- IDLE loop (60f)
def idle(S=300):
    T=60.0; w=2*math.pi/T
    s=lambda a,ph=0.0,n=1: Fn(lambda t: a*math.sin(n*w*t+ph))
    def cons(k, f):
        return Fn(lambda t: add(FLOW[k], f(t)) if isinstance(FLOW[k],tuple) else FLOW[k]+f(t))
    tr={}
    for k,v in FLOW.items(): tr[k]=Fn((lambda vv: (lambda t: vv))(v))
    tr["dside"]=Fn(lambda t: 1.6*(math.sin(w*t)-math.sin(0.0)))
    tr["lean"]=Fn(lambda t: FLOW["lean"]+1.2*(math.sin(w*t+0.4)-math.sin(0.4)))
    tr["dz"]=Fn(lambda t: FLOW["dz"]-0.5*(1-math.cos(2*w*t)))
    tr["sbend"]=Fn(lambda t: FLOW["sbend"]-0.9*(math.sin(w*t+1.2)-math.sin(1.2)))
    tr["yaw"]=Fn(lambda t: FLOW["yaw"]+1.8*(math.sin(w*t+1.0)-math.sin(1.0)))
    tr["syaw"]=Fn(lambda t: FLOW["syaw"]+0.7*(math.sin(w*t+1.7)-math.sin(1.7)))
    tr["hyaw"]=Fn(lambda t: 3.0*(math.sin(w*t+2.2)-math.sin(2.2)))
    tr["hpitch"]=Fn(lambda t: 1.2*(math.sin(w*t+0.6)-math.sin(0.6)))
    tr["rP"]=Fn(lambda t: add(FLOW["rP"], (1.3*(math.sin(w*t+0.3)-math.sin(0.3)), 1.1*(math.cos(w*t+0.3)-math.cos(0.3)), 1.6*(math.sin(w*t+1.4)-math.sin(1.4)))))
    tr["rD"]=Fn(lambda t: nrm(add(FLOW["rD"], (0.045*(math.sin(w*t+1.1)-math.sin(1.1)), 0.035*(math.cos(w*t+1.1)-math.cos(1.1)), 0.0))))
    tr["lR"]=Fn(lambda t: add(FLOW["lR"], (1.2*(math.sin(w*t+2.0)-math.sin(2.0)), 0.8*(math.cos(w*t+2.0)-math.cos(2.0)), 1.3*(math.sin(w*t+0.9)-math.sin(0.9)))))
    tr["rfp"]=Fn(lambda t: 0.0)
    return Clip("AS_Saber_Idle_V2", S, 60, tr, loop=True)
# ---------------- BLOCK loop (30f)
BLKB=dict(yaw=-10.0, syaw=-3.0, bend=6.0, dz=-11.0, lean=0.0, dfwd=1.0, sbend=1.0, hpitch=-2.0,
          rP=(30.0,8.0,118.0), rD=U3(0.2,-0.45,0.87), rpv=(-0.3,0.75,-0.6), lg=1.0)
def block(S=1000):
    T=30.0; w=2*math.pi/T
    tr={}
    base=dict(FLOW); base.update(BLKB)
    for k,v in base.items(): tr[k]=Fn((lambda vv: (lambda t: vv))(v))
    tr["yaw"]=Fn(lambda t: BLKB["yaw"]+1.6*math.sin(w*t+0.5))
    tr["syaw"]=Fn(lambda t: BLKB["syaw"]+0.6*math.sin(w*t+1.1))
    tr["dz"]=Fn(lambda t: BLKB["dz"]-0.7*(1-math.cos(w*t))/2)
    tr["sbend"]=Fn(lambda t: BLKB["sbend"]+0.8*math.sin(w*t+2.0))
    tr["dside"]=Fn(lambda t: 1.0*math.sin(w*t+2.4))
    tr["hyaw"]=Fn(lambda t: 2.0*math.sin(w*t+0.9))
    tr["rP"]=Fn(lambda t: add(BLKB["rP"], (0.9*math.sin(w*t), 1.4*math.cos(w*t), 1.2*math.sin(w*t+0.7))))
    tr["rD"]=Fn(lambda t: nrm(add(BLKB["rD"], (0.03*math.sin(w*t+1.0), 0.045*math.cos(w*t+0.4), 0.0))))
    return Clip("AS_Saber_Block_V2", S, 30, tr, loop=True)
# ---------------- RUN loop (20f)
def _foot_path():
    # psi 0 = contact. (f rel pelvis, du, pitch)
    k=[(0.00,(30.0,0.0,0.0)),(0.10,(4.0,0.0,0.0)),(0.20,(-24.0,0.0,8.0)),(0.27,(-42.0,1.0,26.0)),(0.32,(-52.0,5.0,40.0)),
       (0.42,(-50.0,20.0,45.0)),(0.52,(-36.0,33.0,30.0)),(0.63,(-8.0,38.0,12.0)),(0.74,(20.0,30.0,-2.0)),(0.84,(34.0,15.0,-8.0)),(0.93,(34.0,4.0,-5.0)),(1.00,(30.0,0.0,0.0))]
    return Tr([(a*20.0,b) for a,b in k], period=20.0)
def run_clip(S=400):
    T=20.0; w=2*math.pi/T
    FP=_foot_path()
    tr={}
    base=dict(FLOW)
    for k,v in base.items(): tr[k]=Fn((lambda vv: (lambda t: vv))(v))
    c=calib(); fl=c["W_foot_l_ik_ctrl"][0]; fr=c["W_foot_r_ik_ctrl"][0]
    # lateral targets: feet near midline
    lr_l=-8.0-fl[1]; lr_r=8.0-fr[1]; pf=c["W_body_ctrl"][0][0]+5.0
    tr["rf"]=Fn(lambda t: (pf+FP(t)[0]-fr[0], lr_r, FP(t)[1]))
    tr["lf"]=Fn(lambda t: (pf+FP(t+10.0)[0]-fl[0], lr_l, FP(t+10.0)[1]))
    tr["rfp"]=Fn(lambda t: FP(t)[2]); tr["lfp"]=Fn(lambda t: FP(t+10.0)[2])
    tr["rfy"]=Fn(lambda t: -36.0); tr["lfy"]=Fn(lambda t: -10.0)
    tr["dz"]=Fn(lambda t: -7.0-3.0*math.cos(2*w*t-2*math.pi*0.24))
    tr["yaw"]=Fn(lambda t: -9.0*math.cos(w*t))
    tr["syaw"]=Fn(lambda t: 5.5*math.cos(w*t))
    tr["bend"]=Fn(lambda t: 13.0+1.5*math.cos(2*w*t-2*math.pi*0.3))
    tr["sbend"]=Fn(lambda t: 1.5)
    tr["lean"]=Fn(lambda t: 2.0*math.cos(w*t-2*math.pi*0.12))
    tr["dside"]=Fn(lambda t: 1.5*math.cos(w*t-2*math.pi*0.12))
    tr["dfwd"]=Fn(lambda t: 5.0)
    tr["hpitch"]=Fn(lambda t: 0.0)
    tr["hc"]=Fn(lambda t: 0.8)
    tr["lR"]=Fn(lambda t: (24.0*math.cos(w*t), -2.0+7.0*math.cos(w*t), -26.0+5.0*math.cos(w*t)+4.0*math.sin(w*t)))
    tr["lback"]=Fn(lambda t: (-0.2,-1.0,0.1))
    tr["lpv"]=Fn(lambda t: (-1.0,-0.35,-0.3))
    tr["rP"]=Fn(lambda t: (-3.0-7.0*math.cos(w*t), 26.0, 88.0+2.5*math.cos(w*t)))
    tr["rD"]=Fn(lambda t: nrm((-0.85, 0.38+0.04*math.sin(w*t), -0.3+0.05*math.cos(w*t))))
    tr["rpv"]=Fn(lambda t: (-1.0,0.35,0.0))
    return Clip("AS_Saber_Run_V2", S, 20, tr, loop=True)
ALL={"idle":idle,"run":run_clip,"c1":combo1,"c2":combo2,"c3":combo3,"c4":combo4,"c5":combo5,"block":block}
