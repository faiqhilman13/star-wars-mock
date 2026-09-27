U=(1,0,0); V=(0,0.6,0.8)
def P1(phi, C=(20,6,130), R=34):
    return add(C, mulv(arcv(phi,U,V), R))
def run():
    setb("arm_l_fk_ik_switch", 250, True); setb("arm_l_stretch_switch", 250, False)
    S=300
    L=dict(lback=(-0.3,-1,0.2))
    poses=[
     (0, dict(), dict(READY)),
     (5, dict(yaw=30, bend=-4, lean=-3, syaw=7, dz=1, head_yaw=-15), dict(rP=P1(112), rD=arcv(115,U,V), lP=(24,-6,122), rpv=(0,1,-0.3), **L)),
     (6, dict(yaw=32, bend=-5, lean=-3, syaw=8, dz=1, head_yaw=-16), dict(rP=P1(118), rD=arcv(122,U,V), lP=(25,-5,123), rpv=(0,1,-0.3), **L)),
     (7, dict(yaw=15, bend=0, syaw=3, dz=-1, head_yaw=-8), dict(rP=P1(65), rD=arcv(62,U,V), lP=(18,-14,118), rpv=(-0.2,0.8,-0.5), **L)),
     (8, dict(yaw=-10, bend=8, syaw=-4, dz=-4, lean=2), dict(rP=P1(0), rD=arcv(0,U,V), lP=(8,-24,110), **L)),
     (10, dict(yaw=-24, bend=12, syaw=-7, dz=-6, lean=4, head_yaw=8), dict(rP=P1(-70), rD=arcv(-72,U,V), lP=(-2,-28,104), rpv=(-0.5,0.5,-0.7), **L)),
     (12, dict(yaw=-30, bend=13, syaw=-8, dz=-7, lean=4, head_yaw=10), dict(rP=P1(-100), rD=arcv(-102,U,V), lP=(-6,-29,100), rpv=(-0.5,0.5,-0.7), **L)),
     (14, dict(yaw=-28, bend=12, syaw=-7, dz=-6, lean=3, head_yaw=9), dict(rP=P1(-98), rD=arcv(-98,U,V), lP=(-4,-28,101), rpv=(-0.5,0.5,-0.7), **L)),
     (20, dict(), dict(READY)),
    ]
    return {"r":clip(S,poses)}
