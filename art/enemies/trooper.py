"""Armoured troopers on the mannequin body (black undersuit + rigid armour shells sized from the body).
Usage: blender -b -P trooper.py -- <Bulwark|JetGhost|Warden>
Slots: 0 armour, 1 undersuit, 2 visor (glows at runtime), 3 trim/accent."""
import sys
sys.path.insert(0, r"C:\Users\User\PROJECTS\jedi-arena\art\enemies")
from enemy_lib import Kit, V
from mathutils import Euler
import math

VARIANT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "Bulwark"
STYLE = {
    "Bulwark": dict(slots=[("Armor", (0.86, 0.86, 0.88), 0.05, 0.28), ("Suit", (0.03, 0.03, 0.035), 0.0, 0.7),
                           ("Visor", (0.02, 0.03, 0.05), 0.2, 0.15), ("Trim", (0.35, 0.36, 0.4), 0.6, 0.4)],
                    bulk=1.0, margin=0.014),
    "JetGhost": dict(slots=[("Armor", (0.16, 0.17, 0.19), 0.7, 0.35), ("Suit", (0.04, 0.035, 0.03), 0.0, 0.7),
                            ("Visor", (0.3, 0.03, 0.02), 0.2, 0.15), ("Trim", (0.7, 0.45, 0.08), 0.8, 0.35)],
                     bulk=0.92, margin=0.012),
    "Warden": dict(slots=[("Armor", (0.05, 0.05, 0.055), 0.75, 0.3), ("Suit", (0.25, 0.02, 0.02), 0.0, 0.8),
                          ("Visor", (0.4, 0.02, 0.02), 0.2, 0.15), ("Trim", (0.75, 0.55, 0.15), 0.9, 0.3)],
                   bulk=1.12, margin=0.018),
}[VARIANT]

k = Kit(VARIANT, STYLE["slots"], keep_body=True, body_slot=1)
M = STYLE["margin"]
B = STYLE["bulk"]


def seg_shell(a, b, t0, t1, bone, slot=0, flatten=1.0, grow=1.0, bones=None, segs=16, steps=3, name="shell"):
    """An elliptical shell hugging the body's actual cross-section along bone a->b between t0..t1
    (twist bones count as part of the limb)."""
    if bones is None:
        side = a[-2:]
        stem = a[:-2]
        bones = [a] + [n for n in (stem + "_twist_01" + side, stem + "_twist_02" + side) if n in k.rig.data.bones]
    rings = []
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps
        c, u, v, ru, rv = k.section(a, b, t, bones)
        rings.append((c, u, v, (ru + M) * grow, (rv + M) * grow * flatten))
    return k.tube(rings, bone, slot, segs=segs, name=name)


# ---------------------------------------------------------------- torso cuirass
torso = ['spine_03', 'spine_04', 'spine_05', 'clavicle_l', 'clavicle_r']
x0, x1, y0, y1 = k.extent(1.2, 1.46, torso)
cz = 1.33
k.box(V(0, (y0 + y1) / 2 - 0.004, cz), ((x1 - x0) * B + 2 * M + 0.02, (y1 - y0) + 2 * M + 0.02, 0.3 * B), 'spine_05', slot=0,
      taper=(0.86, 0.92), bevel=0.05, seg=3, name="cuirass")
k.box(V(0, y0 - M - 0.01, cz + 0.02), (0.17 * B, 0.03, 0.14), 'spine_05', slot=3, bevel=0.012, name="chest_emblem")
ax0, ax1, ay0, ay1 = k.extent(1.08, 1.2, ['spine_02', 'spine_03'])
for i, z in enumerate((1.15, 1.09)):
    k.box(V(0, (ay0 + ay1) / 2, z), ((ax1 - ax0) + 2 * M + 0.01 - i * 0.02, (ay1 - ay0) + 2 * M + 0.01, 0.055), 'spine_03' if i == 0 else 'spine_02',
          slot=0, bevel=0.02, name="abdomen")
# belt with pouches
px0, px1, py0, py1 = k.extent(0.92, 1.02, ['pelvis', 'spine_01'])
k.box(V(0, (py0 + py1) / 2, 0.985), ((px1 - px0) + 2 * M + 0.01, (py1 - py0) + 2 * M + 0.01, 0.06), 'pelvis', slot=3, bevel=0.02, name="belt")
for sx in (1, -1):
    k.box(V(sx * 0.1, py0 - M, 0.975), (0.055, 0.035, 0.05), 'pelvis', slot=0, bevel=0.01, name="pouch")
    k.box(V(sx * 0.155, (py0 + py1) / 2, 0.975), (0.035, 0.07, 0.055), 'pelvis', slot=0, bevel=0.01, name="side_pouch")

# ---------------------------------------------------------------- limbs
for s, sx in (('l', 1), ('r', -1)):
    ua, la, hd = 'upperarm_' + s, 'lowerarm_' + s, 'hand_' + s
    th, cf, ft, bl = 'thigh_' + s, 'calf_' + s, 'foot_' + s, 'ball_' + s
    # pauldron: a domed cap over the shoulder
    sh = k.head(ua) + V(sx * 0.01, 0, 0.03)
    k.sphere(sh, (0.1 * B, 0.1 * B, 0.075 * B), {ua: 0.8, 'clavicle_' + s: 0.2}, slot=0, name="pauldron")
    k.sphere(sh + V(sx * 0.012, 0, -0.035), (0.106 * B, 0.104 * B, 0.03), {ua: 0.8, 'clavicle_' + s: 0.2}, slot=3, name="pauldron_rim")
    seg_shell(ua, la, 0.35, 0.75, ua, slot=0, grow=1.08, name="biceps_plate")
    seg_shell(la, hd, 0.25, 0.85, la, slot=0, grow=1.1, name="bracer")
    k.sphere(k.mid(la, hd, 0.95), (0.045, 0.045, 0.045), hd, slot=1, name="cuff")
    # legs
    seg_shell(th, cf, 0.2, 0.74, th, slot=0, grow=1.06, name="thigh_plate")
    kn = k.head(cf) + V(0, -0.02, 0.01)
    k.sphere(kn + V(0, -k.radius(cf, ft, 0.05) * 0.7, 0), (0.06, 0.04, 0.07), {cf: 0.84, th: 0.16}, slot=3, name="knee_pad")
    seg_shell(cf, ft, 0.12, 0.72, cf, slot=0, grow=1.06, name="shin_guard")
    # boots
    foot, ball = k.head(ft), k.head(bl)
    k.box(V(foot.x, (foot.y + ball.y) / 2 - 0.01, 0.055), (0.11, 0.27, 0.11), ft, slot=0 if VARIANT != "JetGhost" else 3,
          taper=(0.92, 0.9), bevel=0.03, name="boot")
    k.box(V(ball.x, ball.y - 0.04, 0.03), (0.1, 0.09, 0.06), bl, slot=0, bevel=0.02, name="toe_cap")
    seg_shell(cf, ft, 0.78, 0.98, cf, slot=0, grow=1.12, name="boot_cuff")

# ---------------------------------------------------------------- helmet
hc = k.head('head') + V(0, -0.012, 0.075)
if VARIANT == "Bulwark":
    k.sphere(hc, (0.125, 0.14, 0.14), 'head', slot=0, segs=20, rings=12, name="helmet")
    k.box(hc + V(0, -0.125, 0.015), (0.16, 0.05, 0.045), 'head', slot=2, bevel=0.01, name="visor_brow")
    k.box(hc + V(0, -0.132, -0.03), (0.045, 0.04, 0.09), 'head', slot=2, bevel=0.01, name="visor_stem")
    k.box(hc + V(0, -0.12, -0.095), (0.1, 0.05, 0.05), 'head', slot=3, bevel=0.012, name="mouth_grille")
    for sx in (1, -1):
        k.cyl(hc + V(0.11 * sx, 0, -0.02), hc + V(0.135 * sx, 0, -0.02), 0.035, 'head', slot=3, segs=12, name="ear_disc")
    k.box(hc + V(0, 0.02, 0.125), (0.035, 0.2, 0.02), 'head', slot=3, name="helmet_ridge")
elif VARIANT == "JetGhost":
    k.sphere(hc + V(0, 0.005, 0.0), (0.12, 0.135, 0.135), 'head', slot=0, segs=20, rings=12, name="helmet")
    k.box(hc + V(0, -0.118, 0.0), (0.2, 0.04, 0.06), 'head', slot=2, taper=(1.0, 1.0), bevel=0.015, name="visor")
    k.cone(hc + V(0, -0.1, -0.08), hc + V(0, -0.16, -0.12), 0.05, 'head', slot=0, name="jaw")
    k.cyl(hc + V(0.1, 0.0, 0.05), hc + V(0.13, 0.0, 0.2), 0.008, 'head', slot=3, segs=6, name="rangefinder")
    k.box(hc + V(0.13, -0.02, 0.2), (0.02, 0.05, 0.02), 'head', slot=2, name="rangefinder_eye")
    k.box(hc + V(0, 0.01, 0.13), (0.04, 0.22, 0.03), 'head', slot=3, name="fin")
else:  # Warden: tall crested helm with a slit visor and a gold-trimmed bevor
    k.cyl(hc + V(0, 0, -0.12), hc + V(0, 0, 0.12), 0.13, 'head', slot=0, r1=0.12, segs=18, name="helm")
    k.sphere(hc + V(0, 0, 0.12), (0.12, 0.12, 0.06), 'head', slot=0, name="helm_top")
    k.box(hc + V(0, -0.128, 0.02), (0.15, 0.02, 0.022), 'head', slot=2, name="visor_slit")
    k.box(hc + V(0, -0.1, -0.1), (0.22, 0.1, 0.07), 'head', slot=3, taper=(0.8, 1.0), bevel=0.015, name="bevor")
    k.box(hc + V(0, 0.02, 0.26), (0.035, 0.3, 0.17), 'head', slot=1, taper=(0.6, 0.6), bevel=0.012, name="crest")

# ---------------------------------------------------------------- variant extras
back = V(0, y1 + M, cz)
if VARIANT == "Bulwark":
    k.box(back + V(0, 0.05, 0.0), (0.26, 0.09, 0.26), 'spine_05', slot=0, bevel=0.025, name="backpack")
    k.cyl(back + V(0, 0.1, -0.06), back + V(0, 0.1, 0.1), 0.035, 'spine_05', slot=3, name="power_cell")
    k.box(back + V(0, 0.1, 0.1), (0.08, 0.03, 0.03), 'spine_05', slot=2, name="cell_light")
elif VARIANT == "JetGhost":
    k.box(back + V(0, 0.06, 0.0), (0.24, 0.1, 0.24), 'spine_05', slot=0, bevel=0.025, name="jet_core")
    for sx in (1, -1):
        k.cyl(back + V(0.11 * sx, 0.1, 0.1), back + V(0.11 * sx, 0.1, -0.2), 0.065, 'spine_05', slot=3, r1=0.055, segs=16, name="thruster")
        k.cyl(back + V(0.11 * sx, 0.1, -0.2), back + V(0.11 * sx, 0.1, -0.26), 0.055, 'spine_05', slot=1, r1=0.07, segs=16, name="nozzle")
    # shoulder rocket launcher on the right
    base = k.head('upperarm_r') + V(-0.02, 0.02, 0.1)
    k.cyl(base + V(0, 0.18, 0), base + V(0, -0.34, 0), 0.055, 'spine_05', slot=0, segs=14, name="launcher")
    k.cyl(base + V(0, -0.34, 0), base + V(0, -0.37, 0), 0.062, 'spine_05', slot=3, segs=14, name="launcher_mouth")
else:
    # Warden: heavy spiked pauldrons, tabard plates and a short cape-like back plate
    for s, sx in (('l', 1), ('r', -1)):
        sh = k.head('upperarm_' + s) + V(sx * 0.01, 0, 0.03)
        k.box(sh + V(sx * 0.02, 0, 0.02), (0.2, 0.2, 0.05), {'upperarm_' + s: 0.7, 'clavicle_' + s: 0.3}, slot=0,
              rot=Euler((0, math.radians(-20 * sx), 0)), bevel=0.02, name="pauldron_slab")
        k.cone(sh + V(sx * 0.03, 0, 0.05), sh + V(sx * 0.06, 0, 0.16), 0.03, {'upperarm_' + s: 0.7, 'clavicle_' + s: 0.3}, slot=3, name="spike")
        k.box(V(sx * 0.09, py0 - M - 0.01, 0.84), (0.11, 0.025, 0.2), 'thigh_' + s, slot=1, taper=(0.8, 1.0), bevel=0.01, name="tabard")
    k.box(V(0, y1 + M + 0.02, 1.2), (0.36, 0.03, 0.5), 'spine_05', slot=1, taper=(1.2, 1.0), bevel=0.012, name="back_cloth")
    k.box(V(0, py0 - M - 0.012, 0.87), (0.12, 0.02, 0.26), 'pelvis', slot=1, taper=(0.9, 1.0), bevel=0.01, name="front_tabard")

k.render("preview")
k.export()
