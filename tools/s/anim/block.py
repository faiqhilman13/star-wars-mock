BLK=dict(rP=(30,6,120), rD=(0.2,-0.4,0.9), lP="grip", rpv=(-0.3,0.7,-0.6), lpv=(-0.3,-0.7,-0.6))
BLKB=dict(yaw=-12, bend=5, dz=-6, syaw=-3, sbend=1, head_pitch=-3)
def run():
    S=600
    poses=[(0,BLKB,BLK),
           (15,dict(BLKB, dz=-7, sbend=2), dict(BLK, rP=(30,6,119))),
           (30,BLKB,BLK)]
    return {"r":clip(S,poses)}
