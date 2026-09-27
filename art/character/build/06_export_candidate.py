"""Verify and export a technical import candidate. Not final likeness approval."""
import bpy,pathlib,json,math,hashlib,sys
from mathutils import Vector,Matrix
ROOT=pathlib.Path(__file__).resolve().parents[1]
omit_bind_pose='--with-bind-pose' not in sys.argv  # Claude adopted this UE-tested recipe in v4.
OUT=ROOT/'delivery_staging/grey_warden_rigcheck';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CH_GreyWarden_textured.blend'))
rig=next(o for o in bpy.data.collections['RIG_DEF'].objects if o.type=='ARMATURE')
parts=[o for o in bpy.data.collections['LOW'].objects if o.type=='MESH']
def reset_weights(ob,v,weights):
    weights=sorted([(n,w) for n,w in weights.items() if w>1e-5],key=lambda x:-x[1])[:4];total=sum(w for n,w in weights)
    for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
    for n,w in weights:
        group=ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n);group.add([v.index],w/total,'REPLACE')
changes={'knee_vertices':0,'pauldron_vertices':0}
for ob in parts:
    if ob.name.endswith('Armor'):
        for v in ob.data.vertices:
            ws={ob.vertex_groups[g.group].name:g.weight for g in v.groups};p=ob.matrix_world@v.co
            for side in ['l','r']:
                if ws.get('calf_'+side,0)>.5 and ws.get('thigh_'+side,0)>.10 and .45<p.z<.60:
                    # Knee plates already have a uniform 84/16 blend in the part
                    # builder. A per-vertex gradient here would buckle their faces.
                    changes['knee_vertices']+=1
                if ws.get('upperarm_'+side,0)>.999 and p.z>1.30:
                    reset_weights(ob,v,{'upperarm_'+side:.88,'clavicle_'+side:.12});changes['pauldron_vertices']+=1

def snap(rig):
    return {b.name:{'parent':b.parent.name if b.parent else None,'world':[list(r) for r in rig.matrix_world@b.matrix_local]} for b in rig.data.bones}
before=snap(rig)
verts=[o.matrix_world@v.co for o in parts for v in o.data.vertices]
bounds={'min':[min(p[i] for p in verts) for i in range(3)],'max':[max(p[i] for p in verts) for i in range(3)]}
audit={'stage':'TECHNICAL IMPORT CANDIDATE; final appearance not accepted','weight_refinements':changes,'bounds_metres':bounds,
       'height_metres':bounds['max'][2]-bounds['min'][2],'materials':[m.name for o in parts for m in o.data.materials],
       'triangles':sum(len(o.data.polygons) for o in parts),'unweighted':sum(not v.groups for o in parts for v in o.data.vertices),
       'max_influences':max(len(v.groups) for o in parts for v in o.data.vertices),
       'max_weight_sum_error':max(abs(sum(g.weight for g in v.groups)-1) for o in parts for v in o.data.vertices),
       'uv_out_of_bounds':sum(not(-.00001<=loop.uv.x<=1.00001 and -.00001<=loop.uv.y<=1.00001) for o in parts for loop in o.data.uv_layers.active.data)}
assert audit['triangles']<=60000 and audit['unweighted']==0 and audit['max_influences']<=4 and audit['uv_out_of_bounds']==0,audit
# Pack preview textures, so the retained Blender asset is self-contained.
for ob in parts:
    for mat in ob.data.materials:
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image and not node.image.packed_file:node.image.pack()
bpy.context.scene['art_status']='Textured rigged import candidate; likeness and engine checks pending'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_candidate.blend'))

# Single skeletal mesh with four slots. Preserve all source bones, including IK helpers.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();mesh=bpy.context.object;mesh.name='SKM_GreyWarden'
# Engine feedback: write native centimetres with UnitScaleFactor=1, eliminating
# reliance on UE's optional scene-unit conversion. Keep the authoring file metres.
# Source bone data is already in centimetres under a .01 reference parent.
assert max(abs(rig.matrix_world[i][j]-(.01 if i==j and i<3 else (1 if i==j else 0))) for i in range(4) for j in range(4))<1e-6
mesh_world=mesh.matrix_world.copy()
for vertex in mesh.data.vertices:vertex.co=(mesh_world@vertex.co)*100
rig.parent=None;rig.matrix_world=Matrix.Identity(4);rig.animation_data_clear()
rig.data.pose_position='REST'
mesh.parent=rig;mesh.matrix_parent_inverse=Matrix.Identity(4);mesh.matrix_world=Matrix.Identity(4)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
bpy.context.view_layer.update()
audit['export_units']={'scene_unit_metres':.01,'mesh_height_in_scene_units':mesh.dimensions.z,'armature_scale':list(rig.scale),'mesh_scale':list(mesh.scale),'parent_inverse_identity':True}
# FBX material import is not the texture contract. Keep simple slots; maps are separate.
for mat in mesh.data.materials:
    for node in list(mat.node_tree.nodes):
        if node.type not in ['BSDF_PRINCIPLED','OUTPUT_MATERIAL']:mat.node_tree.nodes.remove(node)
rig.select_set(True);rig.hide_set(False)
file=OUT/'SKM_GreyWarden.fbx'
if omit_bind_pose:
    # UE can build its bind pose from the complete skin-cluster rest matrices.
    # Omit only the redundant Pose record for this requested diagnostic variant.
    # Patch this process, never the installed Blender exporter files.
    from io_scene_fbx import export_fbx_bin as exporter
    original_pose=exporter.fbx_data_bindpose_element
    original_scene=exporter.fbx_data_from_scene
    def cluster_matrices_only(root,*args,**kwargs):
        start=len(root.elems);result=original_pose(root,*args,**kwargs)
        root.elems[start:]=[e for e in root.elems[start:] if e.id!=b'Pose']
        return result
    def scene_without_pose_template(*args,**kwargs):
        data=original_scene(*args,**kwargs);data.templates.pop(b'BindPose',None)
        return data._replace(templates_users=sum(t.nbr_users for t in data.templates.values()))
    exporter.fbx_data_bindpose_element=cluster_matrices_only
    exporter.fbx_data_from_scene=scene_without_pose_template
bpy.ops.export_scene.fbx(filepath=str(file),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',path_mode='RELATIVE',embed_textures=False)

# Inspect the file's own unit metadata rather than trusting export settings.
from io_scene_fbx import parse_fbx
tree,version=parse_fbx.parse(str(file))
def walk(element):
    yield element
    for child in element.elems:yield from walk(child)
unit_values=[e.props[-1] for e in walk(tree) if e.id==b'P' and e.props and e.props[0]==b'UnitScaleFactor']
audit['export_units']['fbx_unit_scale_factor']=unit_values
assert len(unit_values)==1 and abs(unit_values[0]-1)<1e-6,unit_values
audit['bind_pose_records']=sum(e.id==b'Pose' for e in walk(tree))
audit['skin_clusters']=sum(e.id==b'Deformer' and len(e.props)>2 and e.props[2]==b'Cluster' for e in walk(tree))
if omit_bind_pose:assert audit['bind_pose_records']==0 and audit['skin_clusters']==103

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(file),automatic_bone_orientation=False,use_anim=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');after=snap(rig)
meshes=[o for o in bpy.data.objects if o.type=='MESH']
errors=[];maxerr=0
for n,b in before.items():
    if n not in after:errors.append('missing '+n);continue
    if b['parent']!=after[n]['parent']:errors.append('parent '+n)
    maxerr=max(maxerr,max(abs(b['world'][i][j]-after[n]['world'][i][j]) for i in range(4) for j in range(4)))
audit['roundtrip']={'missing_or_reparented':errors,'max_world_matrix_element_error':maxerr,'bones':len(after),'meshes':len(meshes),'material_slots':sum(len(o.material_slots) for o in meshes),'height_metres':max((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)-min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)}
assert not errors and maxerr<.0001,audit['roundtrip']
assert abs(audit['roundtrip']['height_metres']-audit['height_metres'])<.001,audit
audit['fbx_sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
(ROOT/'review/06_export_report.json').write_text(json.dumps(audit,indent=2))
(OUT/'validation.json').write_text(json.dumps(audit,indent=2))
print('EXPORT_VALIDATED',json.dumps(audit),flush=True)
