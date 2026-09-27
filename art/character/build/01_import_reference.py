import bpy,json,pathlib,math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CH_GreyWarden_master.blend'))
for o in list(bpy.data.objects):
    if o.get('source_quinn'): bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'ref/SKM_Quinn_Simple_reference.fbx'),automatic_bone_orientation=False,use_anim=False)
obs=list(bpy.context.selected_objects)
rig=next(o for o in obs if o.type=='ARMATURE')
report={'objects':[],'bones':[]}
for o in obs:
    o['source_quinn']=True
    report['objects'].append({'name':o.name,'type':o.type,'dimensions':list(o.dimensions),'scale':list(o.scale),'rotation':list(o.rotation_euler)})
    for c in list(o.users_collection):c.objects.unlink(o)
    bpy.data.collections['REF'].objects.link(o)
    o.hide_render=True
    o.hide_set(True)
for b in rig.data.bones:
    report['bones'].append({'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local),'matrix_local':[list(r) for r in b.matrix_local]})
(ROOT/'review/quinn-blender-reference.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_master.blend'))
print(json.dumps({'objects':report['objects'],'landmarks':[b for b in report['bones'] if b['name'] in ['root','pelvis','head','hand_r','foot_r','upperarm_r','lowerarm_r','thigh_r','calf_r','spine_05']]}))
