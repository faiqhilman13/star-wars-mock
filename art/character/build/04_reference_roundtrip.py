"""Isolated source-reference FBX roundtrip, not a character delivery."""
import bpy,pathlib,json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.ops.import_scene.fbx(filepath=str(ROOT/'ref/SKM_Quinn_Simple_reference.fbx'),automatic_bone_orientation=False,use_anim=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
def snapshot(rig):
    return {'object_name':rig.name,'object_world':[list(r) for r in rig.matrix_world],
    'bones':{b.name:{'parent':b.parent.name if b.parent else None,'matrix':[list(r) for r in rig.matrix_world@b.matrix_local]} for b in rig.data.bones}}
before=snapshot(rig)
for ob in bpy.data.objects:ob.select_set(ob.type in ['MESH','ARMATURE'])
bpy.context.view_layer.objects.active=rig
out=ROOT/'review/Quinn_reference_roundtrip.fbx'
bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(out),automatic_bone_orientation=False,use_anim=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');after=snapshot(rig)
errors=[];maxerr=0
for name,b in before['bones'].items():
    if name not in after['bones']:errors.append('missing '+name);continue
    a=after['bones'][name]
    if a['parent']!=b['parent']:errors.append('parent '+name)
    maxerr=max(maxerr,max(abs(a['matrix'][i][j]-b['matrix'][i][j]) for i in range(4) for j in range(4)))
report={'before':before,'after':after,'missing_or_reparented':errors,'max_world_matrix_element_error':maxerr,'mesh_heights':[o.dimensions.z for o in bpy.data.objects if o.type=='MESH'],'note':'Blender represents the UE root node as armature object root, with pelvis as first data bone. No artificial root bone has been inserted. Engine acceptance still required.'}
(ROOT/'review/source-rig-roundtrip.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['before','after']}))
