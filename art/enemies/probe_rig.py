import bpy, json
from pathlib import Path
REF = Path(r"C:\Users\User\PROJECTS\jedi-arena\art\character\ref\SKM_Quinn_Simple_reference.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(REF), automatic_bone_orientation=False, use_anim=False)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
names = ['root','pelvis','spine_01','spine_02','spine_03','spine_04','spine_05','neck_01','neck_02','head','clavicle_l','upperarm_l','lowerarm_l','hand_l','thigh_l','calf_l','foot_l','ball_l','middle_01_l','thumb_01_l']
out = {"rig_scale": list(rig.scale), "meshes": [(m.name, len(m.data.vertices), [s.name for s in m.material_slots], list(m.dimensions)) for m in meshes], "nbones": len(rig.data.bones)}
for n in names:
    b = rig.data.bones.get(n)
    if b:
        out[n] = [round(x, 3) for x in (rig.matrix_world @ b.head_local)] + [round(x, 3) for x in (rig.matrix_world @ b.tail_local)]
print("RIGJSON", json.dumps(out))
