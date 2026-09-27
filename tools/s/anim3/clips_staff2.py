# ================= SABERSTAFF combos 1-3, v2: every blow drives FORWARD into the target =================
# (replaces the frontal-propeller / in-place spin / overhead-windmill openers; combo 4, the 360 finisher, stays)
# Conventions (see clips_staff.py / eng3.py): char space (forward, right, up) in cm from the actor at the floor.
# rP = right-hand position, rD = blade-1 direction (blade 2 = -rD). lg = left hand on the staff (0..1),
# lgo = where along rD the left hand grips (+ toward blade 1, - toward blade 2).
def B2(*v): return mulv(nrm(v), -1.0)          # key the staff by where BLADE 2 points
def lhand(keys, T):
    """left-hand finger curl on every frame (overwrites keys left by the old clips): grips when lg is on."""
    return [(f, keys(f)) for f in range(0, T + 1)]

# ---- combo 1: step-in diagonal cleave (blade 2, high right -> low left) + horizontal sweep (blade 1, right -> left) ----
def staff_c1(S=2300):
    K_ = [(0, P2(SR, lgo=20.0)),
          # chamber: blade 2 cocked high over the right shoulder, weight loading onto the back foot
          (3, dict(rP=(14, 32, 126), rD=B2(-0.45, 0.35, 0.82), lg=1.0, lgo=20.0, yaw=34, syaw=2, dz=-10, bend=4,
                   lf=LFs(2, 0, 3), lfp=6, lR=(24, 4, 0))),
          (5, dict(rP=(30, 24, 138), rD=B2(0.2, 0.2, 0.96), yaw=24, dz=-11, dfwd=4, lf=LFs(14, -1, 3), lfp=4)),
          # cut: step in with the lead foot and drive the blade down through the target
          (6, dict(rP=(45, 14, 128), rD=B2(0.7, 0.05, 0.7), yaw=14, dz=-13, dfwd=8, bend=10, lf=LFs(21, -1.5, 1), lfp=0)),
          (7, dict(rP=(54, 2, 112), rD=B2(0.95, -0.2, 0.1), yaw=5, syaw=-3, dz=-15, dfwd=11, bend=14, lf=LFs(24, -2, 0))),
          (8, dict(rP=(50, -8, 100), rD=B2(0.6, -0.5, -0.6), yaw=-1, syaw=-4, dz=-16, dfwd=12, bend=15)),
          (9, dict(rP=(44, -10, 98), rD=B2(0.3, -0.65, -0.7), lg=1.0, yaw=-3, dz=-16, dfwd=12)),
          # re-chamber blade 1 low on the right (left hand lets go to swap sides of the grip)
          (10, dict(lg=0.2)),
          (11, dict(rP=(28, 30, 118), rD=nrm((-0.35, 0.93, 0.12)), lg=0.4, lgo=-22.0, yaw=30, syaw=2, dz=-13, dfwd=10, bend=9,
                    rf=RFs(4, 0, 3), rfp=6)),
          # sweep: blade 1 flat across the front, right foot stepping through
          (12, dict(rP=(42, 22, 116), rD=nrm((0.35, 0.93, 0.08)), lg=1.0, yaw=17, dz=-14, dfwd=12, rf=RFs(12, -1, 3))),
          (13, dict(rP=(56, 6, 116), rD=nrm((0.97, 0.2, 0.05)), yaw=0, syaw=-2, dz=-15, dfwd=14, bend=12, rf=RFs(20, -2, 0), rfp=0)),
          (14, dict(rP=(48, -14, 116), rD=nrm((0.55, -0.83, 0.05)), yaw=-22, syaw=-4, dz=-15, dfwd=14, rf=RFs(24, -3, 0))),
          (15, dict(rP=(34, -24, 118), rD=nrm((-0.1, -0.99, 0.1)), yaw=-34, syaw=-5, dz=-14)),
          (16, dict(rP=(26, -26, 120), rD=nrm((-0.45, -0.85, 0.25)), lg=1.0, yaw=-38, dz=-13, dfwd=13)),
          # recover to the ready guard
          (19, dict(rP=(28, 5, 108), rD=nrm((0.2, -0.8, -0.55)), lg=0.5, yaw=-10, syaw=-3, dz=-12, dfwd=8, bend=10, rf=RFs(14, -1, 2), rfp=4)),
          (22, dict(rP=(22, 22, 100), rD=nrm((0.6, -0.4, -0.7)), lg=0.0, yaw=14, syaw=-4, dz=-11.5, dfwd=3, bend=8,
                    rf=RFs(3, 0, 1), rfp=0, lf=LFs(6, 0, 0), lR=(28, 8, -12))),
          (26, P2(SR, lgo=-22.0))]
    curl = Tr([(0, 0.25), (2, 0.6), (3, 1.0), (9, 1.0), (10, 0.35), (11, 0.6), (12, 1.0), (19, 0.8), (22, 0.25), (26, 0.25)])
    return Clip("AS_Staff_Combo1", S, 26, mk(K_), extra={"fing": {"r": 1.0, "l": lhand(curl, 26)}, "weapon": "staff"})

# ---- combo 2: rising diagonal (blade 1, low right -> high left) into a lunging two-handed spear thrust ----
def staff_c2(S=2400):
    K_ = [(0, P2(SR, lgo=-22.0)),
          (3, dict(rP=(10, 30, 95), rD=nrm((-0.1, 0.6, -0.8)), lg=1.0, lgo=-22.0, yaw=34, syaw=2, dz=-14, bend=6,
                   lf=LFs(2, 0, 3), lfp=6, lR=(24, 4, -10))),
          (5, dict(rP=(30, 24, 100), rD=nrm((0.6, 0.45, -0.65)), yaw=22, dz=-14, dfwd=5, bend=8, lf=LFs(12, -1, 3), lfp=3)),
          (6, dict(rP=(46, 10, 115), rD=nrm((0.95, 0.05, -0.1)), yaw=8, syaw=-2, dz=-12, dfwd=10, bend=9, lf=LFs(22, -2, 0), lfp=0)),
          (7, dict(rP=(48, -2, 132), rD=nrm((0.7, -0.35, 0.62)), yaw=-4, syaw=-4, dz=-8, dfwd=11, bend=7)),
          (8, dict(rP=(40, -6, 142), rD=nrm((0.2, -0.5, 0.85)), lg=1.0, yaw=-8, dz=-7, dfwd=11)),
          # chamber the thrust: staff levelled at the target, left (lead) hand forward, right hand drawn back
          (9, dict(lg=0.3)),
          (10, dict(rP=(8, 24, 122), rD=nrm((0.75, -0.1, 0.2)), lg=0.6, lgo=26.0, yaw=26, syaw=0, dz=-12, dfwd=6, bend=5, lf=LFs(12, -1, 0))),
          (12, dict(rP=(0, 22, 118), rD=nrm((1.0, 0.0, 0.05)), lg=1.0, lgo=26.0, yaw=32, syaw=1, dz=-14, dfwd=3, bend=5, lean=-2,
                    lf=LFs(10, -1, 2), lfp=5)),
          # thrust: long lunge step, hips turn square into it
          (13, dict(rP=(26, 14, 119), rD=nrm((1.0, -0.02, 0.03)), yaw=16, dz=-16, dfwd=10, bend=10, lean=0, lf=LFs(22, -2, 2), lfp=2)),
          (14, dict(rP=(48, 6, 120), rD=nrm((1.0, -0.03, 0.02)), yaw=2, syaw=-2, dz=-18, dfwd=15, bend=15, lf=LFs(30, -2, 0), lfp=0)),
          (15, dict(rP=(58, 2, 120), rD=nrm((1.0, -0.04, 0.01)), yaw=-4, dz=-19, dfwd=17, bend=17)),
          (17, dict(rP=(56, 3, 119), rD=nrm((0.99, -0.05, -0.05)), lg=1.0, yaw=-3, dz=-19, dfwd=16, bend=16)),
          # recover to the ready guard
          (20, dict(rP=(34, 16, 108), rD=nrm((0.85, -0.1, -0.5)), lg=0.5, yaw=8, dz=-15, dfwd=10, bend=12, lf=LFs(20, -1.5, 0))),
          (23, dict(rP=(22, 26, 100), rD=nrm((0.78, -0.15, -0.6)), lg=0.0, yaw=20, dz=-12, dfwd=3, bend=8, lf=LFs(10, 0, 0), lR=(28, 8, -12))),
          (27, P2(SR, lgo=26.0))]
    curl = Tr([(0, 0.25), (2, 0.6), (3, 1.0), (8, 1.0), (9, 0.4), (10, 0.7), (12, 1.0), (19, 1.0), (21, 0.5), (23, 0.25), (27, 0.25)])
    return Clip("AS_Staff_Combo2", S, 27, mk(K_), extra={"fing": {"r": 1.0, "l": lhand(curl, 27)}, "weapon": "staff"})

# ---- combo 3: leaping overhead double chop (blade 1 then blade 2 come over the top and down in front) ----
def staff_c3(S=2500):
    K_ = [(0, P2(SR, lgo=-22.0)),
          (2, dict(rP=(20, 24, 130), rD=nrm((-0.2, 0.2, 0.96)), lg=0.6, lgo=-22.0, yaw=18, dz=-14, bend=5, lR=(24, 0, 4))),
          # rise onto the toes, staff raised two-handed overhead (blade 1 back, blade 2 forward)
          (4, dict(rP=(12, 14, 166), rD=nrm((-0.55, 0.1, 0.83)), lg=1.0, yaw=12, syaw=-1, dz=-5, bend=0, lean=-3, hpitch=-8,
                   lf=LFs(4, 0, 4), lfp=10, rfp=8)),
          (6, dict(rP=(28, 10, 170), rD=nrm((0.2, 0.05, 0.98)), yaw=8, dz=-4, dfwd=6, lean=-2, lf=LFs(16, -1, 6), lfp=6)),
          # chop 1 (blade 1) with the landing step
          (7, dict(rP=(46, 6, 152), rD=nrm((0.85, 0.0, 0.5)), yaw=5, dz=-10, dfwd=11, bend=10, lean=0, hpitch=-3, lf=LFs(24, -1, 2), lfp=2)),
          (8, dict(rP=(56, 4, 126), rD=nrm((0.95, 0.0, -0.3)), yaw=3, dz=-18, dfwd=14, bend=18, lf=LFs(28, -1, 0), lfp=0, rfp=0)),
          (9, dict(rP=(52, 4, 108), rD=nrm((0.6, 0.0, -0.8)), lg=1.0, yaw=3, dz=-22, dfwd=14, bend=22)),
          # the staff keeps rolling forward: blade 2 is now cocked high behind, the grip shifts
          (10, dict(lg=0.3)),
          (11, dict(rP=(40, 6, 150), rD=B2(0.1, 0.05, 0.99), lg=0.6, lgo=22.0, yaw=6, dz=-15, dfwd=12, bend=12, rf=RFs(8, 0, 4), rfp=6)),
          # chop 2 (blade 2) stepping through with the right foot
          (12, dict(rP=(55, 4, 140), rD=B2(0.85, 0.0, 0.5), lg=1.0, yaw=0, dz=-16, dfwd=15, bend=16, rf=RFs(18, -1, 2), rfp=2)),
          (13, dict(rP=(60, 3, 120), rD=B2(0.97, 0.0, -0.2), yaw=-2, dz=-21, dfwd=16, bend=22, rf=RFs(24, -2, 0), rfp=0)),
          (14, dict(rP=(56, 3, 105), rD=B2(0.65, 0.0, -0.75), lg=1.0, yaw=-2, dz=-23, dfwd=16, bend=24)),
          # recover to the ready guard
          (17, dict(rP=(42, 10, 106), rD=nrm((0.3, -0.2, 0.93)), lg=0.6, yaw=6, dz=-18, dfwd=12, bend=16, rf=RFs(16, -1, 2), rfp=4)),
          (21, dict(rP=(30, 22, 104), rD=nrm((0.7, -0.15, -0.7)), lg=0.0, yaw=18, dz=-13, dfwd=5, bend=9, rf=RFs(4, 0, 1), rfp=0,
                    lf=LFs(12, 0, 0), lR=(28, 8, -12))),
          (28, P2(SR, lgo=22.0))]
    curl = Tr([(0, 0.25), (2, 0.7), (4, 1.0), (9, 1.0), (10, 0.4), (11, 0.7), (12, 1.0), (17, 0.8), (21, 0.25), (28, 0.25)])
    return Clip("AS_Staff_Combo3", S, 28, mk(K_), extra={"fing": {"r": 1.0, "l": lhand(curl, 28)}, "weapon": "staff"})

ALL.update({"s_c1": staff_c1, "s_c2": staff_c2, "s_c3": staff_c3})
