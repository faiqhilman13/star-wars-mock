# ================= SABERSTAFF set =================
STAFF_READY=dict(yaw=25.0, bend=7.0, lean=0.0, dz=-11.0, dfwd=0.0, dside=0.0, syaw=-4.0, sbend=1.5, slean=0.0,
    hyaw=0.0, hpitch=-3.0, hroll=0.0, hc=0.9, th=0.0,
    lf=(8.0,6.0,0.0), lfy=2.4, lfp=0.0, rf=(-3.0,6.0,0.0), rfy=9.2, rfp=0.0,
    rP=(18.0,30.0,98.0), rD=U3(0.75,-0.15,-0.64), rpv=(-0.3,0.8,-0.5), rtw=0.0,
    lR=(30.0,8.0,-12.0), lback=(-0.3,-0.6,0.75), lpv=(-0.3,-0.7,-0.7), lg=0.0)
SR=STAFF_READY
def staff_Q():
    fb=foot_base("l"); return (fb[0]+SR["lf"][0], fb[1]+SR["lf"][1], 0.0)
def RFs(a,b,c): return add(SR["rf"],(a,b,c))
def LFs(a,b,c): return add(SR["lf"],(a,b,c))
# wheel planes (forward wheels at the sides, tilted so the low end swings outward)
NR=U3(0.0,0.819,0.574)     # right wheel: alpha 0=up/in, -90=forward, 90=back
NL=U3(0.0,-0.906,0.423)    # left wheel : alpha 0=up/in, +90=forward
def WR(a): return loopD(a,NR)
def WL(b): return mulv(loopD(b,NL),-1.0)   # blade-2 angle b in the left wheel -> blade-1 dir
# ---- idle (60f loop) ----
def staff_idle(S=2100):
    T=60.0; w=2*math.pi/T
    tr={k:K(v) for k,v in SR.items()}
    tr["dside"]=Fn(lambda t: 1.4*(math.sin(w*t)))
    tr["lean"]=Fn(lambda t: SR["lean"]+1.0*(math.sin(w*t+0.4)-math.sin(0.4)))
    tr["dz"]=Fn(lambda t: SR["dz"]-0.6*(1-math.cos(2*w*t))/2.0)
    tr["sbend"]=Fn(lambda t: SR["sbend"]-0.8*(math.sin(w*t+1.2)-math.sin(1.2)))
    tr["yaw"]=Fn(lambda t: SR["yaw"]+2.2*(math.sin(w*t+1.0)-math.sin(1.0)))
    tr["syaw"]=Fn(lambda t: SR["syaw"]+0.8*(math.sin(w*t+1.7)-math.sin(1.7)))
    tr["hyaw"]=Fn(lambda t: 3.0*(math.sin(w*t+2.2)-math.sin(2.2)))
    tr["hpitch"]=Fn(lambda t: SR["hpitch"]+1.2*(math.sin(w*t+0.6)-math.sin(0.6)))
    A0=nrm((0.35,0.1,-1.0))
    def rD(t):
        a1=16.0*math.sin(w*t)                        # slow twirl-sway about the forearm
        a2=5.0*(math.sin(2*w*t+0.5)-math.sin(0.5))   # pitch bob
        d=rodr(SR["rD"], A0, a1)
        return nrm(rodr(d, (0,1,0), a2))
    tr["rD"]=Fn(rD)
    tr["rP"]=Fn(lambda t: add(SR["rP"], (1.5*(math.sin(w*t+0.3)-math.sin(0.3)), 1.2*(math.cos(w*t+0.3)-math.cos(0.3)), 2.0*(math.sin(2*w*t+1.4)-math.sin(1.4)))))
    tr["lR"]=Fn(lambda t: add(SR["lR"], (1.5*(math.sin(w*t+2.0)-math.sin(2.0)), 1.0*(math.cos(w*t+2.0)-math.cos(2.0)), 1.6*(math.sin(w*t+0.9)-math.sin(0.9)))))
    return Clip("AS_Staff_Idle", S, 60, tr, loop=True, extra={"fing":{"r":1.0,"l":0.25},"weapon":"staff"})
# ---- run (20f loop) ----
def staff_run(S=2200):
    cfg=RunCfg()
    tr=run_tracks(cfg)
    run_left_pump(tr, cfg.lead)
    tr["rR"]=Fn(lambda t: (-14.0+2.5*cosp(t-cfg.lead-1.0,20.0), 17.0, -42.0+2.0*cosp(t-4.0,10.0)))
    tr["rD"]=Fn(lambda t: nrm((0.96, 0.12+0.02*cosp(t-cfg.lead-1.0,20.0), 0.18+0.04*cosp(t-4.5,10.0))))
    tr["rDt"]=K(0.6)
    tr["rpv"]=K((-0.5,0.8,0.1))
    return Clip("AS_Staff_Run", S, 20, tr, loop=True, extra={"fing":{"r":1.0,"l":0.65},"weapon":"staff"})
# ---- block (30f loop) : two-handed diagonal guard ----
STAFF_BLOCK=dict(yaw=14.0, syaw=-3.0, bend=6.0, dz=-12.0, dfwd=1.0, sbend=1.0, hpitch=-3.0, hc=0.9,
    rP=(38.0,16.0,121.0), rD=U3(0.2,0.6,0.77), rpv=(-0.3,0.8,-0.5), lg=1.0, lgo=-24.0, lgs=1.0, lgtw=0.0,
    lR=(26.0,10.0,-20.0), lpv=(-0.4,-0.6,-0.7))
def staff_block(S=2700):
    T=30.0; w=2*math.pi/T
    base=dict(SR); base.update(STAFF_BLOCK)
    tr={k:K(v) for k,v in base.items()}
    B=STAFF_BLOCK
    tr["yaw"]=Fn(lambda t: B["yaw"]+1.6*math.sin(w*t+0.5))
    tr["syaw"]=Fn(lambda t: B["syaw"]+0.6*math.sin(w*t+1.1))
    tr["dz"]=Fn(lambda t: B["dz"]-0.7*(1-math.cos(w*t))/2)
    tr["sbend"]=Fn(lambda t: B["sbend"]+0.8*math.sin(w*t+2.0))
    tr["dside"]=Fn(lambda t: 1.0*math.sin(w*t+2.4))
    tr["hyaw"]=Fn(lambda t: 2.0*math.sin(w*t+0.9))
    tr["rP"]=Fn(lambda t: add(B["rP"], (1.0*math.sin(w*t), 1.5*math.cos(w*t), 1.3*math.sin(w*t+0.7))))
    tr["rD"]=Fn(lambda t: nrm(add(B["rD"], (0.03*math.sin(w*t+1.0), 0.04*math.cos(w*t+0.4), 0.0))))
    return Clip("AS_Staff_Block", S, 30, tr, loop=True, extra={"fing":{"r":1.0,"l":1.0},"weapon":"staff"})
# ---- combo 1: figure-8 twirl strikes (frontal propeller: CW half-turn right, CCW half-turn left) ----
NP1=U3(1.0,-0.2,0.15); NP2=U3(1.0,0.22,0.08)
def A1(a): return loopD(a,NP1)
def A2(a): return loopD(a,NP2)
def staff_c1(S=2300):
    K_=[(0,P2(SR, rR=(20,10,-32), rRw=0.0, rDt=0.0)),
        (1,dict(rRw=0.45, rR=(32,10,-8), rD=U3(0.6,-0.05,-0.8), rDt=0.3, yaw=22, syaw=-3, dz=-10.5)),
        (2,dict(rRw=1.0, rR=(44,9,14), rD=A1(160), rDt=1.0, yaw=16, syaw=-2, dz=-10, bend=5, lR=(24,0,-8), rpv=(-0.2,0.6,-0.8))),
        (3,dict(rR=(45,9,16), rD=A1(95), yaw=12, syaw=-1)),
        (4,dict(rR=(46,9,18), rD=A1(35), yaw=10, syaw=0, dz=-9, bend=4, lR=(14,-24,-4), lpv=(-0.5,-0.6,-0.6))),
        (5,dict(rD=A1(3))),
        (6,dict(rD=A1(65), yaw=6, dz=-10, lf=LFs(4,0,4), lfp=5)),
        (7,dict(rR=(46,8,17), rD=A1(135), yaw=0, syaw=-1, dz=-12, bend=8, dfwd=3, lf=LFs(9,0,1))),
        (8,dict(rD=A1(185), yaw=-4, dz=-13, bend=9, dfwd=5, lf=LFs(11,-0.5,0), lfp=0, lR=(10,-28,0))),
        (9,dict(rD=A1(193), rR=(46,-8,18), yaw=-7)),
        (10,dict(rD=A2(172), rR=(46,-24,21), yaw=-12, syaw=-3, rpv=(-0.3,0.3,-0.9))),
        (11,dict(rD=A2(120), yaw=-18, syaw=-4, dz=-11.5)),
        (12,dict(rD=A2(55), yaw=-22, dz=-12, bend=9, lR=(0,-30,-8))),
        (13,dict(rD=A2(5), yaw=-25, dz=-11.5, rR=(47,-22,24))),
        (14,dict(rD=A2(-8), yaw=-26, dz=-11, rR=(47,-18,28))),
        (16,dict(rD=A2(45), rR=(47,0,27), yaw=-16, syaw=-3, dz=-10.5, rpv=(-0.2,0.6,-0.8))),
        (18,dict(rD=A2(115), rR=(46,12,20), yaw=-6, syaw=-3, dz=-12.5, bend=8, lf=LFs(6,0,3), lR=(16,-16,-10))),
        (19,dict(rD=A2(160), yaw=0)),
        (20,dict(rD=A2(178), rR=(42,12,14), yaw=6, dz=-12, dfwd=2, lf=LFs(2,0,1))),
        (22,dict(rRw=0.55, rR=(34,10,-10), rDt=0.5, rD=U3(0.6,-0.1,-0.8), yaw=16, dz=-11.5, dfwd=0.5, lf=SR["lf"], lR=(26,6,-12))),
        (24,dict(rRw=0.15, rDt=0.1, rD=U3(0.7,-0.15,-0.7))),
        (26,P2(SR, rR=(20,10,-32), rRw=0.0, rDt=0.0))]
    return Clip("AS_Staff_Combo1", S, 26, mk(K_), extra={"fing":{"r":1.0,"l":0.25},"weapon":"staff"})
# ---- combo 2: rising spin with both blades (CCW 360, pivot left foot) ----
def staff_c2(S=2400):
    K_=[(0,SR),
        (2,dict(th=18, yaw=28, syaw=0, dz=-13, bend=8, rP=(14,37,132), rD=U3(0.2,0.05,-0.98), lR=(20,-10,-6), rpv=(-0.3,0.8,-0.5))),
        (3,dict(th=34, rP=(10,38,118), rD=U3(-0.6,0.1,-0.8))),
        (4,dict(th=46, yaw=30, syaw=4, dz=-17, bend=12, rP=(6,37,94), rD=U3(-0.97,0.1,0.2), rf=RFs(0,0,0), rpv=(-0.2,0.9,-0.3), lR=(18,-24,-4))),
        (6,dict(th=16, yaw=20, syaw=2, dz=-15, rP=(7,37,97), rD=U3(-0.97,0.1,-0.1), rf=RFs(1,1,6), rfp=10, lfp=0)),
        (8,dict(th=-42, yaw=8, syaw=0, dz=-12, bend=10, rP=(8,36,104), rD=U3(-0.85,0.1,-0.52), rf=RFs(2,2,12), lean=-4, hyaw=-20)),
        (9,dict(rD=U3(-0.76,0.1,-0.64))),
        (10,dict(th=-112, yaw=4, dz=-10, rP=(8,35,116), rD=U3(-0.86,0.1,-0.5), lean=-6)),
        (11,dict(rD=U3(-0.97,0.1,-0.1))),
        (12,dict(th=-192, yaw=2, dz=-8, bend=8, rP=(9,34,128), rD=U3(-0.95,0.1,0.28), rf=RFs(2,2,14), hyaw=-30)),
        (13,dict(rD=U3(-0.8,0.1,0.58))),
        (14,dict(th=-272, yaw=2, dz=-6, bend=6, rP=(11,32,140), rD=U3(-0.62,0.1,0.78), rf=RFs(1,2,10), lean=-5)),
        (16,dict(th=-332, yaw=8, dz=-5, bend=5, rP=(13,30,148), rD=U3(-0.4,0.15,0.9), rf=RFs(0,1,4), rfp=6, lean=-2, hyaw=-10)),
        (18,dict(th=-357, yaw=12, syaw=-2, dz=-6, rP=(14,30,152), rD=U3(-0.3,0.2,0.93), rf=RFs(0,0,0), rfp=0, lean=0, hyaw=0, lR=(20,-18,4))),
        (19,dict(th=-362)),
        (20,dict(th=-361.5, rP=(19,36,146), rD=U3(0.46,-0.12,0.88), dz=-8, yaw=16)),
        (22,dict(th=-360.0, rP=(21,35,126), rD=U3(0.96,-0.1,0.26), dz=-11, bend=8, yaw=22)),
        (24,dict(rP=(19,31,106), rD=U3(0.98,-0.07,-0.21), dz=-11.5, lR=(28,4,-10))),
        (27,P2(SR, th=-360.0))]
    return Clip("AS_Staff_Combo2", S, 27, mk(K_), Q=staff_Q(), extra={"fing":{"r":1.0,"l":0.25},"weapon":"staff"})
# ---- combo 3: two-handed lift, overhead windmill (helicopter), side-wheel chop into two-handed lunge ----
def staff_c3(S=2500):
    def Dy(a): return nrm(Rz((0.02,1.0,0.03), -a))   # lateral staff rotated CCW (seen from above) by a deg
    K_=[(0,SR),
        (2,dict(rP=(28,34,140), rD=U3(0.5,-0.25,0.83), dz=-10, yaw=20, syaw=-2, bend=5, rpv=(-0.3,0.8,-0.4), lR=(26,-4,6))),
        (4,dict(rP=(26,22,164), rD=U3(-0.3,0.65,0.7), lg=0.0, dz=-8, yaw=14, syaw=-3, bend=3, lR=(24,6,26), lpv=(-0.3,-0.8,-0.4))),
        (5,dict(lg=0.6)),
        (6,dict(rP=(22,12,176), rD=Dy(0), lg=1.0, dz=-7, bend=2, sbend=0, hpitch=-6)),
        (7,dict(rD=Dy(30), lg=1.0)),
        (8,dict(rP=(21,11,178), rD=Dy(75), lg=0.5, yaw=10)),
        (9,dict(rD=Dy(125), lg=0.0, lR=(10,-25,10))),
        (10,dict(rP=(20,10,178), rD=Dy(175), yaw=6, dz=-6)),
        (11,dict(rD=Dy(225))),
        (12,dict(rP=(20,11,178), rD=Dy(275), yaw=8)),
        (13,dict(rD=Dy(320), lR=(20,-5,20))),
        (14,dict(rP=(24,16,174), rD=Dy(358), yaw=12, dz=-6)),
        (15,dict(rP=(36,40,164), rD=U3(-0.5,0.5,0.7), yaw=16, syaw=1, dz=-8, bend=4, lR=(26,-10,0))),
        (16,dict(rP=(34,42,152), rD=U3(0.45,-0.25,0.86), yaw=18, syaw=2, dz=-11, bend=8, dfwd=3, lf=LFs(6,-0.5,4))),
        (17,dict(rP=(42,44,130), rD=U3(0.9,-0.3,0.1), yaw=20, syaw=3, dz=-16, bend=14, dfwd=7, lf=LFs(13,-1,0), lR=(34,14,-14))),
        (18,dict(rP=(40,32,110), rD=U3(0.62,-0.35,-0.7), yaw=24, syaw=4, lg=0.6, dz=-20, bend=19, dfwd=10)),
        (19,dict(rP=(40,32,106), rD=U3(0.58,-0.35,-0.74), lg=1.0, dz=-21, bend=20)),
        (21,dict(rP=(38,32,107), rD=U3(0.6,-0.33,-0.73), lg=1.0, dz=-19, bend=17, dfwd=8, yaw=27)),
        (23,dict(rP=(30,31,103), rD=U3(0.68,-0.25,-0.69), lg=0.3, dz=-15, bend=12, dfwd=4, lf=LFs(6,-0.5,2), lR=(26,4,-14), yaw=26)),
        (25,dict(rP=(22,30,100), lg=0.0, dz=-12, bend=8, dfwd=1, lf=SR["lf"])),
        (28,SR)]
    return Clip("AS_Staff_Combo3", S, 28, mk(K_), extra={"fing":{"r":1.0,"l":[(0,0.25),(4,0.4),(6,1.0),(8,1.0),(9,0.3),(17,0.3),(19,1.0),(22,1.0),(25,0.25),(28,0.25)]},"weapon":"staff"})
# ---- combo 4: 360 spin finisher, staff horizontal across the front (both blades sweep both sides) ----
def staff_c4(S=2600):
    Dl=U3(0.02,-0.99,0.1)     # blade 1 left, blade 2 right
    K_=[(0,SR),
        (2,dict(rP=(30,22,108), rD=U3(0.7,-0.6,-0.2), th=10, yaw=26, dz=-13, bend=8, rpv=(-0.3,0.8,-0.5))),
        (4,dict(rP=(36,8,112), rD=Dl, th=32, yaw=30, syaw=4, dz=-16, bend=10, lR=(10,-30,4), lpv=(-0.3,-0.8,-0.5))),
        (5,dict(th=30)),
        (7,dict(th=-20, yaw=20, syaw=1, dz=-14, rD=U3(0.02,-0.98,0.18), rf=RFs(1,1,6), rfp=8, lean=-3, hyaw=-15)),
        (9,dict(th=-95, yaw=12, dz=-11, bend=8, rD=U3(0.02,-0.99,0.08), rf=RFs(2,2,12), lean=-5, hyaw=-25)),
        (11,dict(th=-175, yaw=10, dz=-9, rD=U3(0.02,-0.99,-0.05), rP=(36,8,116))),
        (13,dict(th=-255, yaw=10, dz=-10, rD=U3(0.02,-0.99,0.12), rf=RFs(2,2,10))),
        (15,dict(th=-315, yaw=14, dz=-12, rD=U3(0.02,-0.99,0.04), rf=RFs(1,1,5), lean=-3, hyaw=-10)),
        (17,dict(th=-352, yaw=18, dz=-15, bend=11, rf=RFs(0,0,0), rfp=0, lean=0, hyaw=0)),
        (18,dict(th=-363)),
        (19,dict(th=-364, rP=(36,12,110), rD=U3(0.3,-0.93,-0.2), dz=-17, bend=12)),
        (21,dict(th=-361, rP=(30,22,104), rD=U3(0.65,-0.55,-0.52), dz=-14, lR=(24,-6,-8))),
        (23,dict(th=-360.0, rP=(22,28,100), rD=U3(0.75,-0.2,-0.63), dz=-12, bend=8)),
        (26,P2(SR, th=-360.0))]
    return Clip("AS_Staff_Combo4", S, 26, mk(K_), Q=staff_Q(), extra={"fing":{"r":1.0,"l":0.25},"weapon":"staff"})
ALL.update({"s_idle":staff_idle,"s_run":staff_run,"s_block":staff_block,"s_c1":staff_c1,"s_c2":staff_c2,"s_c3":staff_c3,"s_c4":staff_c4})
