# backhand horizontal: left -> right at chest height
U=(1,0,0); V=(0,-1,0.12)   # phi+ = toward left
def P2(phi, C=(18,4,124), R=32):
    return add(C, mulv(arcv(phi,U,V), R))
def run():
    S=400
    L=dict(lback=(-0.3,-1,0.2))
    poses=[
     (0, dict(), dict(READY)),
     (5, dict(yaw=-38, bend=3, lean=2, syaw=-9, dz=-2, head_yaw=15), dict(rP=P2(95,R=26), rD=arcv(120,U,V), lP=(-4,-26,112), rpv=(-0.6,0.4,-0.7), **L)),
     (6, dict(yaw=-40, bend=3, lean=2, syaw=-10, dz=-2, head_yaw=16), dict(rP=P2(100,R=26), rD=arcv(126,U,V), lP=(-6,-27,110), rpv=(-0.6,0.4,-0.7), **L)),
     (7, dict(yaw=-20, bend=4, syaw=-5, dz=-3, head_yaw=8), dict(rP=P2(50), rD=arcv(62,U,V), lP=(4,-26,112), rpv=(-0.3,0.5,-0.8), **L)),
     (8, dict(yaw=5, bend=5, syaw=2, dz=-4), dict(rP=P2(0), rD=arcv(0,U,V), lP=(12,-24,114), rpv=(-0.2,0.5,-0.8), **L)),
     (10, dict(yaw=25, bend=5, syaw=7, dz=-5, lean=-2, head_yaw=-8), dict(rP=P2(-60), rD=arcv(-72,U,V), lP=(22,-12,118), rpv=(-0.2,0.8,-0.5), **L)),
     (12, dict(yaw=32, bend=4, syaw=9, dz=-5, lean=-3, head_yaw=-10), dict(rP=P2(-85), rD=arcv(-105,U,V), lP=(24,-8,118), rpv=(-0.2,0.8,-0.5), **L)),
     (14, dict(yaw=30, bend=4, syaw=8, dz=-4, lean=-3, head_yaw=-9), dict(rP=P2(-82), rD=arcv(-100,U,V), lP=(23,-9,117), rpv=(-0.2,0.8,-0.5), **L)),
     (20, dict(), dict(READY)),
    ]
    return {"r":clip(S,poses)}
