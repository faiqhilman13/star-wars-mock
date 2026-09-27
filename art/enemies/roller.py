"""Buzz-Roller static meshes: the rolled-up armoured ball, the unfolded turret head and a spider leg.
Blender -Y becomes Unreal +X (forward). Slots: 0 bronze shell, 1 dark frame, 2 eye/lamps (glow), 3 trim."""
import sys, math
sys.path.insert(0, r"C:\Users\User\PROJECTS\jedi-arena\art\enemies")
from enemy_lib import StaticKit, V
from mathutils import Euler

SLOTS = [("Shell", (0.5, 0.3, 0.12), 0.9, 0.35), ("Frame", (0.05, 0.045, 0.04), 0.8, 0.4),
         ("Lamp", (0.9, 0.1, 0.05), 0.0, 0.4), ("Trim", (0.75, 0.6, 0.35), 0.9, 0.3)]
k = StaticKit("Roller", SLOTS)

# ---------------------------------------------------------------- ball (rolled up): 1.2 m armoured sphere
R = 0.6
k.sphere(V(0, 0, 0), R * 0.97, None, slot=1, segs=24, rings=14, name="core")
# curved armour petals: six scaled sphere caps around the ball
for i in range(6):
    yaw = i * 60.0
    rot = Euler((0, 0, math.radians(yaw)))
    d = V(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)
    k.sphere(d * 0.2, (0.46, 0.46, 0.56), None, slot=0, rot=rot, segs=20, rings=12, name="petal")
k.torus(V(0, 0, 0), R * 1.1, 0.04, None, slot=3, rot=Euler((math.radians(90), 0, 0)), name="band")
k.torus(V(0, 0, 0), R * 1.1, 0.035, None, slot=1, name="band_equator")
for sz in (1, -1):
    k.cyl(V(0, 0, sz * R * 1.0), V(0, 0, sz * R * 1.14), 0.13, None, slot=3, segs=16, name="axle_cap")
k.sphere(V(0, -R * 0.93, 0.18), 0.05, None, slot=2, name="lamp")
k.export_static("SM_RollerBall", render_tag="ball")

# ---------------------------------------------------------------- turret head (origin = turret pivot)
k.sphere(V(0, 0, 0.3), (0.38, 0.38, 0.26), None, slot=0, segs=24, rings=12, name="dome")
k.cyl(V(0, 0, 0.12), V(0, 0, 0.3), 0.36, None, slot=1, r1=0.38, segs=24, name="collar")
k.box(V(0, -0.33, 0.3), (0.34, 0.1, 0.2), None, slot=1, taper=(0.9, 1.0), bevel=0.03, name="face")
k.sphere(V(0, -0.39, 0.32), 0.07, None, slot=2, name="eye")
k.torus(V(0, -0.37, 0.32), 0.085, 0.015, None, slot=3, rot=Euler((math.radians(90), 0, 0)), name="eye_ring")
for sx in (1, -1):
    k.box(V(0.3 * sx, -0.12, 0.22), (0.16, 0.34, 0.16), None, slot=0, bevel=0.03, name="gun_housing")
    k.cyl(V(0.3 * sx, -0.25, 0.22), V(0.3 * sx, -0.72, 0.22), 0.045, None, slot=1, segs=12, name="barrel")
    k.cyl(V(0.3 * sx, -0.72, 0.22), V(0.3 * sx, -0.78, 0.22), 0.06, None, slot=3, segs=12, name="muzzle_brake")
    k.cyl(V(0.2 * sx, 0.1, 0.45), V(0.24 * sx, 0.2, 0.75), 0.012, None, slot=1, segs=6, name="antenna")
k.box(V(0, 0.3, 0.26), (0.26, 0.14, 0.16), None, slot=1, bevel=0.03, name="power_pack")
k.export_static("SM_RollerHead", render_tag="head")

# ---------------------------------------------------------------- leg (origin = hip, reaching out along -Y then down)
hip = V(0, 0, 0)
knee = V(0, -0.34, 0.2)
foot = V(0, -0.55, -0.42)
k.sphere(hip, 0.07, None, slot=3, name="hip_joint")
k.cyl(hip, knee, 0.05, None, slot=0, r1=0.04, segs=12, name="upper_leg")
k.sphere(knee, 0.055, None, slot=1, name="knee")
k.cyl(knee, foot, 0.04, None, slot=0, r1=0.022, segs=12, name="lower_leg")
k.cyl(foot, foot + V(0, -0.04, -0.06), 0.05, None, slot=1, r1=0.02, segs=10, name="foot_claw")
k.box(knee + V(0, -0.05, 0.05), (0.06, 0.12, 0.04), None, slot=3, bevel=0.01, name="knee_plate")
k.export_static("SM_RollerLeg", render_tag="leg")
