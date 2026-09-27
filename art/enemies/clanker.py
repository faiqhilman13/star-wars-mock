"""Clanker battle droid: a gangly, skinny, all-mechanical droid with a long snout head.
Slots: 0 tan plating, 1 dark joints/rods, 2 eyes (glow at runtime), 3 rust stripes."""
import sys
sys.path.insert(0, r"C:\Users\User\PROJECTS\jedi-arena\art\enemies")
from enemy_lib import Kit, V, FWD, LEFT, UP

k = Kit("Clanker", [("Plating", (0.62, 0.47, 0.27), 0.45, 0.5),
                    ("Joints", (0.07, 0.065, 0.06), 0.85, 0.4),
                    ("Eyes", (0.9, 0.7, 0.2), 0.0, 0.4),
                    ("Rust", (0.55, 0.22, 0.07), 0.3, 0.6)])

# ---------------------------------------------------------------- pelvis & spine
k.box(k.head('pelvis') + V(0, 0.005, -0.03), (0.2, 0.11, 0.09), 'pelvis', slot=0, taper=(1.1, 1.0), name="pelvis")
k.box(k.head('pelvis') + V(0, -0.058, -0.03), (0.08, 0.02, 0.06), 'pelvis', slot=3, name="codpiece")
k.limb('spine_01', 'spine_04', 0.026, 0.026, 'spine_02', slot=1, name="spine_rod")
for i, b in enumerate(['spine_02', 'spine_03']):
    k.torus(k.head(b) + V(0, 0, 0.02), 0.042, 0.012, b, slot=1, name="vertebra")

# ---------------------------------------------------------------- chest (narrow, sloped, with a back pack)
chest = k.mid('spine_04', 'neck_01', 0.45) + V(0, -0.005, 0)
k.box(chest, (0.24, 0.13, 0.25), 'spine_05', slot=0, taper=(1.15, 0.95), bevel=0.02, name="chest")
k.box(chest + V(0, -0.07, 0.01), (0.16, 0.03, 0.17), 'spine_05', slot=3, taper=(1.1, 1.0), name="chest_plate")
k.box(chest + V(0, 0.105, 0.0), (0.18, 0.08, 0.2), 'spine_05', slot=0, bevel=0.015, name="backpack")
k.box(chest + V(0, 0.15, -0.03), (0.1, 0.02, 0.08), 'spine_05', slot=1, name="backpack_vent")
k.cyl(chest + V(0.06, 0.12, 0.09), chest + V(0.06, 0.12, 0.42), 0.006, 'spine_05', slot=1, segs=6, name="antenna")
k.sphere(chest + V(0.06, 0.12, 0.425), 0.012, 'spine_05', slot=3, name="antenna_tip")
k.box(chest + V(0, 0, 0.14), (0.3, 0.1, 0.03), 'spine_05', slot=1, name="shoulder_bar")

# ---------------------------------------------------------------- neck & head (long snout)
k.limb('neck_01', 'head', 0.018, 0.016, 'neck_01', slot=1, pad=0.02, name="neck")
cranium = k.head('head') + V(0, 0.005, 0.055)
k.sphere(cranium, (0.062, 0.075, 0.07), 'head', slot=0, name="cranium")
snout0 = cranium + V(0, -0.05, -0.005)
snout1 = cranium + V(0, -0.245, -0.035)
k.cyl(snout0, snout1, 0.045, 'head', slot=0, r1=0.03, segs=14, flatten=0.9, name="snout")
k.sphere(snout1, (0.03, 0.02, 0.027), 'head', slot=0, name="snout_tip")
k.box(cranium + V(0, -0.1, 0.035), (0.03, 0.2, 0.015), 'head', slot=3, name="head_stripe")
for sx in (1, -1):
    k.sphere(cranium + V(0.045 * sx, -0.055, 0.02), 0.018, 'head', slot=2, name="eye")
    k.cyl(cranium + V(0.058 * sx, 0.0, 0.0), cranium + V(0.075 * sx, 0.0, 0.0), 0.022, 'head', slot=1, segs=10, name="ear")

# ---------------------------------------------------------------- limbs (mirrored)
for s, sx in (('l', 1), ('r', -1)):
    # arms
    k.limb('clavicle_' + s, 'upperarm_' + s, 0.016, 0.016, 'clavicle_' + s, slot=1, name="clav")
    k.sphere(k.head('upperarm_' + s), 0.045, 'upperarm_' + s, slot=0, name="shoulder")
    k.limb('upperarm_' + s, 'lowerarm_' + s, 0.018, 0.016, 'upperarm_' + s, slot=1, name="upperarm_rod")
    k.cyl(k.mid('upperarm_' + s, 'lowerarm_' + s, 0.2), k.mid('upperarm_' + s, 'lowerarm_' + s, 0.75), 0.03, 'upperarm_' + s,
          slot=0, r1=0.026, flatten=0.75, name="upperarm_plate")
    k.sphere(k.head('lowerarm_' + s), 0.028, 'lowerarm_' + s, slot=1, name="elbow")
    k.limb('lowerarm_' + s, 'hand_' + s, 0.016, 0.014, 'lowerarm_' + s, slot=1, name="forearm_rod")
    k.cyl(k.mid('lowerarm_' + s, 'hand_' + s, 0.15), k.mid('lowerarm_' + s, 'hand_' + s, 0.8), 0.029, 'lowerarm_' + s,
          slot=0, r1=0.024, flatten=0.7, name="forearm_plate")
    hand = k.head('hand_' + s)
    fingers = k.head('middle_01_' + s)
    d = (fingers - hand).normalized()
    k.cyl(hand - d * 0.01, hand + d * 0.06, 0.026, 'hand_' + s, slot=1, r1=0.022, flatten=0.55, segs=10, name="palm")
    for off in (-0.018, 0.018):
        side = d.cross(V(0, 0, 1)).normalized() * off
        k.cyl(hand + d * 0.05 + side, hand + d * 0.12 + side + V(0, 0, -0.02), 0.007, 'hand_' + s, slot=1, segs=6, name="finger")
    k.cyl(hand + d * 0.02 + V(0, -0.02, 0.01), hand + d * 0.07 + V(0, -0.04, 0.0), 0.007, 'hand_' + s, slot=1, segs=6, name="thumb")

    # legs
    k.sphere(k.head('thigh_' + s), 0.035, 'thigh_' + s, slot=1, name="hip")
    k.limb('thigh_' + s, 'calf_' + s, 0.02, 0.018, 'thigh_' + s, slot=1, name="thigh_rod")
    k.cyl(k.mid('thigh_' + s, 'calf_' + s, 0.1), k.mid('thigh_' + s, 'calf_' + s, 0.7), 0.042, 'thigh_' + s,
          slot=0, r1=0.032, flatten=0.8, name="thigh_plate")
    k.sphere(k.head('calf_' + s), 0.032, 'calf_' + s, slot=1, name="knee")
    k.box(k.head('calf_' + s) + V(0, -0.035, 0.0), (0.05, 0.02, 0.06), 'calf_' + s, slot=3, name="kneecap")
    k.limb('calf_' + s, 'foot_' + s, 0.018, 0.016, 'calf_' + s, slot=1, name="shin_rod")
    k.cyl(k.mid('calf_' + s, 'foot_' + s, 0.1), k.mid('calf_' + s, 'foot_' + s, 0.75), 0.035, 'calf_' + s,
          slot=0, r1=0.026, flatten=0.8, name="shin_plate")
    k.sphere(k.head('foot_' + s), 0.028, 'foot_' + s, slot=1, name="ankle")
    foot = k.head('foot_' + s)
    ball = k.head('ball_' + s)
    fc = (foot + ball) / 2
    fc.z = 0.034
    k.box(fc + V(0, 0.01, 0), (0.08, 0.2, 0.058), 'foot_' + s, slot=0, taper=(0.85, 0.85), bevel=0.015, name="foot")
    k.cyl(foot, V(foot.x, foot.y, 0.05), 0.02, 'foot_' + s, slot=1, segs=10, name="ankle_post")
    k.box(V(ball.x, ball.y - 0.045, 0.02), (0.075, 0.07, 0.035), 'ball_' + s, slot=3, name="toe")

k.render("preview")
k.export()
