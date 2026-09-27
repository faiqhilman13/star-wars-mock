BLK=dict(rP=(30,6,120), rD=(0.2,-0.4,0.9), lP="grip", rpv=(-0.3,0.7,-0.6), lpv=(-0.3,-0.7,-0.6))
BLKB=dict(yaw=-12, bend=5, dz=-6, syaw=-3, sbend=1, head_pitch=-3)
def run():
    S=700
    poses=[(0,BLKB,BLK),
      (3,dict(yaw=8, bend=6, dz=-7, syaw=3, sbend=1, lean=-2, head_pitch=-3), dict(BLK, rP=(39,24,127), rD=(0.42,0.78,0.47))),
      (5,dict(yaw=10, bend=6, dz=-7, syaw=4, sbend=1, lean=-2, head_pitch=-3), dict(BLK, rP=(38,25,126), rD=(0.4,0.8,0.45))),
      (11,BLKB,BLK)]
    return {"r":clip(S,poses)}
