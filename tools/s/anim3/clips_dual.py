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
