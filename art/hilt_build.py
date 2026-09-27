import bpy, bmesh, math, os, json, sys
from mathutils import Matrix, Vector

SIDES = int(os.environ.get("HILT_SIDES", "24"))
ART = r"C:\Users\User\PROJECTS\jedi-arena\art"
os.makedirs(ART, exist_ok=True)
CM = 0.01

orig_scene = bpy.context.window.scene if bpy.context.window else bpy.context.scene
scn = bpy.data.scenes.new("SaberHilt")
if bpy.context.window:
    bpy.context.window.scene = scn
scn.unit_settings.system = 'METRIC'
scn.unit_settings.scale_length = 1.0
created_meshes, created_mats, created_objs = [], [], []

# ---------- materials ----------
def make_mat(name, col, metal, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*col, 1)
    created_mats.append(m)
    return m

M_METAL = make_mat("M_Hilt_Metal", (0.72, 0.73, 0.75), 1.0, 0.35)
M_DARK = make_mat("M_Hilt_Dark", (0.025, 0.025, 0.028), 0.0, 0.6)
M_ACC = make_mat("M_Hilt_Accent", (0.55, 0.02, 0.015), 0.0, 0.4)
MATS = [M_METAL, M_DARK, M_ACC]
METAL, DARK, ACC = 0, 1, 2

def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in MATS:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    scn.collection.objects.link(ob)
    created_meshes.append(me); created_objs.append(ob)
    return ob

# ---------- lathe body ----------
P = []  # (r_cm, z_cm, mat of segment to next point)
def add(r, z, m=METAL):
    P.append((r, z, m))

# pommel
add(0.0, 0.0, DARK)
add(1.2, 0.0, METAL)
add(1.6, 0.4, METAL)
add(1.6, 1.2, DARK)
add(1.45, 1.2, DARK)
add(1.45, 1.6, METAL)
add(1.8, 1.6, METAL)
add(1.88, 1.85, METAL)
add(1.8, 2.1, METAL)
add(1.62, 2.1, METAL)
# grip ridges
g0, g1, n = 2.8, 13.0, 7
ridge = 0.85
gap = (g1 - g0 - n * ridge) / (n + 1)
z = g0
add(1.62, z, METAL)
for i in range(n):
    z += gap
    add(1.62, z, DARK)
    add(1.86, z + 0.1, DARK)
    add(1.86, z + ridge - 0.1, DARK)
    add(1.62, z + ridge, METAL)
    z += ridge
# activation section
add(1.62, 13.0, METAL)
add(1.76, 13.12, METAL)
add(1.76, 13.6, DARK)
add(1.6, 13.6, DARK)
add(1.6, 13.85, METAL)
add(1.76, 13.85, METAL)
add(1.76, 19.15, DARK)
add(1.6, 19.15, DARK)
add(1.6, 19.4, METAL)
add(1.76, 19.4, METAL)
add(1.76, 19.88, METAL)
add(1.62, 20.0, METAL)
# emitter
add(1.62, 21.0, DARK)
add(1.72, 21.0, DARK)
add(1.72, 21.8, METAL)
add(1.62, 21.8, METAL)
add(1.72, 22.4, METAL)
add(1.96, 27.2, METAL)
add(2.06, 27.55, METAL)
add(2.06, 28.0, METAL)
add(1.68, 28.0, DARK)
add(1.68, 26.4, DARK)
add(0.55, 26.4, DARK)
add(0.55, 26.7, DARK)
add(0.0, 26.7, DARK)

bm = bmesh.new()
rings = []
for (r, zc, m) in P:
    if r < 1e-6:
        rings.append([bm.verts.new((0, 0, zc * CM))])
    else:
        ring = []
        for k in range(SIDES):
            a = 2 * math.pi * k / SIDES
            ring.append(bm.verts.new((r * CM * math.cos(a), r * CM * math.sin(a), zc * CM)))
        rings.append(ring)
for i in range(len(P) - 1):
    A, B, m = rings[i], rings[i + 1], P[i][2]
    for k in range(SIDES):
        k2 = (k + 1) % SIDES
        if len(A) == 1:
            f = bm.faces.new((A[0], B[k], B[k2]))
        elif len(B) == 1:
            f = bm.faces.new((A[k], A[k2], B[0]))
        else:
            f = bm.faces.new((A[k], A[k2], B[k2], B[k]))
        f.material_index = m
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
body = new_obj("Body", bm)

# ---------- helpers ----------
def box(name, size, loc, mat, rot=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size) * CM, verts=bm.verts)
    for f in bm.faces:
        f.material_index = mat
    ob = new_obj(name, bm)
    ob.location = Vector(loc) * CM
    if rot:
        ob.rotation_euler = rot
    if bevel > 0:
        md = ob.modifiers.new("Bevel", 'BEVEL')
        md.width = bevel * CM
        md.segments = 2
        md.limit_method = 'ANGLE'
        md.harden_normals = False
    return ob

def cyl(name, r, h, verts, loc, mat, axis='X', cap_mat=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=r * CM, radius2=r * CM, depth=h * CM)
    for f in bm.faces:
        f.material_index = mat
        if cap_mat is not None and abs(f.normal.z) > 0.9:
            f.material_index = cap_mat
    ob = new_obj(name, bm)
    ob.location = Vector(loc) * CM
    if axis == 'X':
        ob.rotation_euler = (0, math.radians(90), 0)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", 'BEVEL')
        md.width = bevel * CM
        md.segments = 1
        md.limit_method = 'ANGLE'
    return ob

# activation box (+X side), plus dark inset panel
box("ActBox", (1.4, 1.5, 4.4), (1.65, 0, 16.5), METAL, bevel=0.15)
box("ActPanel", (0.15, 1.1, 3.9), (2.39, 0, 16.5), DARK)
# red button
cyl("Button", 0.42, 0.5, 12, (2.55, 0, 17.5), ACC, bevel=0.06)
cyl("ButtonCollar", 0.55, 0.12, 12, (2.47, 0, 17.5), METAL)
# switch: dark base + tilted metal lever with red tip
box("SwitchBase", (0.2, 0.8, 1.0), (2.52, 0, 15.3), METAL, bevel=0.05)
lever = box("SwitchLever", (0.7, 0.28, 0.28), (2.85, 0, 15.45), METAL,
            rot=(0, math.radians(-25), 0), bevel=0.04)
box("SwitchTip", (0.18, 0.34, 0.34), (3.2, 0, 15.62), ACC, rot=(0, math.radians(-25), 0))
# emitter side detail: small dark window strip on -X (vent) and small accent jewel
box("EmitterVent", (0.3, 0.9, 2.6), (-1.85, 0, 24.3), DARK, rot=(0, math.radians(4.2), 0))
# grip clip (belt clip-ish) on -X at pommel side
box("PommelTab", (0.35, 0.8, 1.4), (-1.75, 0, 1.0), METAL, bevel=0.08)

# ---------- apply modifiers / transforms, join ----------
dg = bpy.context.evaluated_depsgraph_get()
for ob in created_objs:
    if ob.modifiers:
        ev = ob.evaluated_get(dg)
        me2 = bpy.data.meshes.new_from_object(ev)
        old = ob.data
        ob.modifiers.clear()
        ob.data = me2
        created_meshes.append(me2)
    ob.data.transform(ob.matrix_basis)
    ob.matrix_basis = Matrix.Identity(4)

bm = bmesh.new()
for ob in created_objs:
    tmp = ob.data.copy()
    # ensure material order same (all have MATS in same order)
    bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
final_me = bpy.data.meshes.new("SM_SaberHilt")
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
# origin at grip point z = 9cm
bmesh.ops.translate(bm, vec=(0, 0, -0.09), verts=bm.verts)
bm.to_mesh(final_me); bm.free()
for m in MATS:
    final_me.materials.append(m)
created_meshes.append(final_me)
for ob in list(created_objs):
    bpy.data.objects.remove(ob)
created_objs.clear()
hilt = bpy.data.objects.new("SM_SaberHilt", final_me)
scn.collection.objects.link(hilt)
created_objs.append(hilt)

# smoothing: smooth + sharp by angle, then weighted normals
final_me.shade_smooth()
final_me.set_sharp_from_angle(angle=math.radians(40))
wn = hilt.modifiers.new("WN", 'WEIGHTED_NORMAL')
wn.keep_sharp = True
wn.mode = 'FACE_AREA'
dg = bpy.context.evaluated_depsgraph_get()
ev = hilt.evaluated_get(dg)
me3 = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
hilt.modifiers.clear()
hilt.data = me3
bpy.data.meshes.remove(final_me)
me3.name = "SM_SaberHilt"
created_meshes = [m for m in created_meshes if m.name in bpy.data.meshes and m is not final_me] if False else []
created_meshes.append(me3)
for m in list(bpy.data.meshes):
    if m.users == 0 and m.name.startswith(("Body", "ActBox", "ActPanel", "Button", "Switch", "Emitter", "Pommel")):
        bpy.data.meshes.remove(m)

me = hilt.data
me.calc_loop_triangles()
tris = len(me.loop_triangles)
zs = [v.co.z for v in me.vertices]
xs = [v.co.x for v in me.vertices]
ys = [v.co.y for v in me.vertices]
info = {
    "sides": SIDES, "tris": tris, "verts": len(me.vertices),
    "dims_cm": [round(d * 100, 2) for d in hilt.dimensions],
    "zmin_cm": round(min(zs) * 100, 2), "zmax_cm": round(max(zs) * 100, 2),
    "xrange_cm": [round(min(xs) * 100, 2), round(max(xs) * 100, 2)],
    "yrange_cm": [round(min(ys) * 100, 2), round(max(ys) * 100, 2)],
    "slots": [s.material.name for s in hilt.material_slots],
    "mat_face_counts": [sum(1 for p in me.polygons if p.material_index == i) for i in range(3)],
    "loc": list(hilt.location), "rot": list(hilt.rotation_euler), "scale": list(hilt.scale),
}

# ---------- preview render ----------
if os.environ.get("HILT_RENDER", "1") == "1":
    cam_d = bpy.data.cameras.new("PrevCam"); cam_d.lens = 60
    cam = bpy.data.objects.new("PrevCam", cam_d); scn.collection.objects.link(cam)
    cam.location = (0.42, -0.42, 0.22)
    target = Vector((0, 0, 0.05))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scn.camera = cam
    def light(name, typ, loc, energy, size=0.3, col=(1, 1, 1)):
        ld = bpy.data.lights.new(name, typ); ld.energy = energy; ld.color = col
        if typ == 'AREA': ld.size = size
        lo = bpy.data.objects.new(name, ld); scn.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0.05)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return lo
    light("Key", 'AREA', (0.5, -0.2, 0.5), 8, 0.4)
    light("Fill", 'AREA', (-0.4, -0.5, 0.2), 3, 0.6, (0.85, 0.9, 1.0))
    light("Rim", 'AREA', (-0.2, 0.5, 0.4), 8, 0.3)
    w = bpy.data.worlds.new("PrevWorld"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.13, 0.15, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    scn.world = w
    r = scn.render
    r.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 48
    scn.cycles.use_denoising = True
    r.resolution_x, r.resolution_y, r.resolution_percentage = 700, 1000, 100
    r.image_settings.file_format = 'PNG'
    r.filepath = os.path.join(ART, os.environ.get("HILT_PNG", "hilt_preview.png"))
    bpy.ops.render.render(write_still=True, scene=scn.name)
    info["preview"] = r.filepath

# ---------- export ----------
if os.environ.get("HILT_EXPORT", "0") == "1":
    for o in scn.objects:
        o.select_set(False)
    hilt.select_set(True)
    bpy.context.view_layer.objects.active = hilt
    hilt.data.transform(__import__("mathutils").Matrix.Scale(100.0, 4))  # bake metres->centimetres for UE
    fbx = os.path.join(ART, "SM_SaberHilt.fbx")
    with bpy.context.temp_override(scene=scn, view_layer=scn.view_layers[0]):
        bpy.ops.export_scene.fbx(
            filepath=fbx, use_selection=True, object_types={'MESH'},
            apply_unit_scale=False, apply_scale_options="FBX_SCALE_NONE", global_scale=1.0,
            axis_forward='X', axis_up='Z', mesh_smooth_type='FACE',
            use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False,
            use_tspace=False, embed_textures=False)
    info["fbx"] = fbx
    info["fbx_bytes"] = os.path.getsize(fbx)

print("HILTINFO " + json.dumps(info))
# no save; background process exits without writing any .blend


