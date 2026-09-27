import bpy
from pathlib import Path
REF = Path(r"C:\Users\User\PROJECTS\jedi-arena\art\character\ref\SKM_Quinn_Simple_reference.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(REF), automatic_bone_orientation=False, use_anim=False)
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, "parent=", o.parent.name if o.parent else None, "scale=", tuple(round(x,4) for x in o.matrix_world.to_scale()))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
b = rig.data.bones['head']
print("HEADLOCAL", tuple(round(x,3) for x in b.head_local))
m = next(o for o in bpy.data.objects if o.type == 'MESH')
print("MESHVERT", tuple(round(x,3) for x in m.data.vertices[0].co), "mods", [md.type for md in m.modifiers], "vgroups", len(m.vertex_groups))
