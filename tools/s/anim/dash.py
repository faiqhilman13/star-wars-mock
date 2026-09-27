def run():
    S=800
    trail=dict(rP=(-26,24,88), rD=(-0.75,0.25,-0.6), lP=(-22,-24,92), lback=(0,-1,0), rpv=(0.2,0.6,-0.8), lpv=(0.2,-0.6,-0.8))
    poses=[(0, dict(), dict(READY)),
      (3, dict(bend=30, dz=-9, dfwd=10, sbend=6, head_pitch=-22, yaw=-10), dict(trail)),
      (9, dict(bend=33, dz=-10, dfwd=11, sbend=7, head_pitch=-24, yaw=-10), dict(trail, rP=(-28,24,86))),
      (12, dict(bend=31, dz=-9, dfwd=10, sbend=6, head_pitch=-22, yaw=-10), dict(trail))]
    r=clip(S,poses)
    for off,kw in [(0,{}),(3,dict(df=-18,du=12)),(9,dict(df=-20,du=14)),(12,dict(df=-18,du=12))]:
        foot("foot_r_ik_ctrl", S+off, **kw)
    for off,kw in [(0,{}),(3,dict(df=6)),(12,dict(df=6))]:
        foot("foot_l_ik_ctrl", S+off, **kw)
    return {"r":r}
