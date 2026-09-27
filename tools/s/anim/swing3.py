U=(1,0,0); V=(0,0.06,1)
def D3(phi): return arcv(phi,U,V)
def P3(phi, C=(14,6,138), R=30): return add(C, mulv(arcv(phi,U,V), R))
G=dict(lP="grip", rpv=(-0.3,0.8,-0.5), lpv=(-0.3,-0.8,-0.5))
def run():
    S=500
    poses=[
     (0, dict(), dict(READY)),
     (8, dict(yaw=6, bend=-6, dz=2, sbend=-3, head_pitch=-4), dict(rP=P3(98), rD=D3(135), **G)),
     (10, dict(yaw=7, bend=-8, dz=3, sbend=-4, head_pitch=-5), dict(rP=P3(102), rD=D3(145), **G)),
     (12, dict(yaw=3, bend=2, dz=-3, dfwd=2, sbend=0), dict(rP=P3(70), rD=D3(95), **G)),
     (14, dict(yaw=-3, bend=12, dz=-10, dfwd=5, sbend=4), dict(rP=P3(15), rD=D3(25), **G)),
     (15, dict(yaw=-5, bend=16, dz=-13, dfwd=6, sbend=5), dict(rP=P3(-15), rD=D3(-8), **G)),
     (17, dict(yaw=-6, bend=20, dz=-16, dfwd=7, sbend=6, head_pitch=-6), dict(rP=P3(-45), rD=D3(-42), **G)),
     (20, dict(yaw=-6, bend=20, dz=-16, dfwd=7, sbend=6, head_pitch=-6), dict(rP=P3(-47), rD=D3(-45), **G)),
     (27, dict(), dict(READY)),
    ]
    r=clip(S,poses)
    for off,kw in [(0,{}),(10,{}),(12,dict(df=8,du=7)),(14,dict(df=17)),(21,dict(df=17)),(24,dict(df=8,du=6)),(27,{})]:
        foot("foot_l_ik_ctrl", S+off, **kw)
    return {"r":r}
