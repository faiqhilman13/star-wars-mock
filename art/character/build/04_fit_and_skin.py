"""Reproducible local Quinn fitting/skin checkpoint. Source rest bones stay untouched."""
import bpy, bmesh, pathlib, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CH_GreyWarden_forms.blend'))
low=bpy.data.collections['LOW']
for o in list(low.objects):
    if any(k in o.name for k in ['Glove','Finger','Knuckle','Thumb']):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'ref/SKM_Quinn_Simple_reference.fbx'),automatic_bone_orientation=False,use_anim=False)
imported=list(bpy.context.selected_objects)
rig=next(o for o in imported if o.type=='ARMATURE')
source=next(o for o in imported if o.type=='MESH')
original={b.name:{'parent':b.parent.name if b.parent else None,'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones}
def joint(name):return rig.matrix_world@rig.data.bones[name].head_local
def choose(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
def move_collection(ob,col):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob)
for ob in imported:
    move_collection(ob,bpy.data.collections['RIG_DEF'] if ob==rig else bpy.data.collections['REF'])
    if ob!=rig:ob.hide_render=True

# Keep the original mesh and all source bone data in REF for later audit.
srcverts=[source.matrix_world@v.co for v in source.data.vertices]
source.data.calc_loop_triangles()
triangles=[tuple(t.vertices) for t in source.data.loop_triangles]
bvh=BVHTree.FromPolygons(srcverts,triangles,all_triangles=True)
groupnames={g.index:g.name for g in source.vertex_groups}
srcweights=[{groupnames[g.group]:g.weight for g in v.groups if g.weight>.00001 and groupnames[g.group] in original} for v in source.data.vertices]
def sample_weights(point):
    hit,normal,index,distance=bvh.find_nearest(point)
    if index is None:raise RuntimeError('No source surface for skin transfer')
    ids=triangles[index];a,b,c=[srcverts[i] for i in ids]
    w=barycentric_transform(hit,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    result={}
    for vi,fac in zip(ids,w):
        for name,value in srcweights[vi].items():result[name]=result.get(name,0)+max(0,fac)*value
    return result
def normalise(weights):
    items=sorted(((k,v) for k,v in weights.items() if v>.0001),key=lambda t:-t[1])[:4]
    total=sum(v for k,v in items)
    if total<=0:raise RuntimeError('Unweighted vertex')
    return {k:v/total for k,v in items}
def skin(ob,weights):
    for vi,ws in enumerate(weights):
        for name,value in normalise(ws).items():
            g=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name);g.add([vi],value,'REPLACE')
    mod=ob.modifiers.new('Quinn deformation','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
    mw=ob.matrix_world.copy();ob.parent=rig;ob.matrix_world=mw

# Concept sleeves are lower than Quinn's A-pose. Fit vertices, never source bones.
def fit_segment(p,a,b,A,B):
    d=b-a;D=B-A;t=(p-a).dot(d)/d.length_squared
    offset=p-a-d*t
    return A+D*t+d.rotation_difference(D)@offset
arm_prefix=('Sleeve','ForearmSuit','Vambrace','ForearmStrap','Pauldron','ShoulderLame')
for ob in low.objects:
    short=ob.name.removeprefix('CH_GreyWarden_')
    if not short.startswith(arm_prefix):continue
    side='l' if '_L' in short else 'r';s=1 if side=='l' else -1
    a=Vector((s*.215,.008,1.426));b=Vector((s*.287,-.004,1.177));c=Vector((s*.343,-.029,.948))
    A=joint('upperarm_'+side);B=joint('lowerarm_'+side);C=joint('hand_'+side)
    upper=short.startswith(('Sleeve','Pauldron','ShoulderLame'))
    for v in ob.data.vertices:v.co=fit_segment(v.co,a,b,A,B) if upper else fit_segment(v.co,b,c,B,C)

# Gloves use the supplied Quinn hand topology and weights, expanded 1 mm for leather.
for side in ['l','r']:
    names=[n for n in original if n=='hand_'+side or (n.endswith('_'+side) and any(n.startswith(f) for f in ['thumb_','index_','middle_','ring_','pinky_']))]
    keep={i for i,ws in enumerate(srcweights) if sum(ws.get(n,0) for n in names)>.45}
    faces=[tuple(p.vertices) for p in source.data.polygons if all(i in keep for i in p.vertices)]
    used=sorted({i for f in faces for i in f});remap={vi:i for i,vi in enumerate(used)}
    verts=[srcverts[i]+(source.matrix_world.to_3x3()@source.data.vertices[i].normal).normalized()*.001 for i in used]
    me=bpy.data.meshes.new('QuinnFittedGlove_'+side);me.from_pydata(verts,[],[tuple(remap[i] for i in f) for f in faces]);me.update()
    ob=bpy.data.objects.new('CH_GreyWarden_FittedGlove_'+side,me);low.objects.link(ob)
    me.materials.append(bpy.data.materials['M_GreyWarden_Leather'])
    for p in me.polygons:p.use_smooth=True
    skin(ob,[srcweights[i] for i in used])

# Three five-bone cape chains in addition to the unchanged mannequin hierarchy.
choose(rig);bpy.ops.object.mode_set(mode='EDIT')
inverse=rig.matrix_world.inverted();chains={}
for label,x in [('l',.235),('c',0),('r',-.235)]:
    positions=[]
    for k in range(6):
        t=k/5;positions.append(Vector((x*(.75+.80*t),.155+.13*t,1.43-1.12*t)))
    for k in range(5):
        name=f'cape_{label}_{k+1:02d}';bone=rig.data.edit_bones.new(name)
        bone.head=inverse@positions[k];bone.tail=inverse@positions[k+1]
        bone.parent=rig.data.edit_bones['spine_05' if k==0 else f'cape_{label}_{k:02d}']
        bone.use_connect=False
    chains[label]=positions
bpy.ops.object.mode_set(mode='OBJECT')

def cape_weights(p):
    vertical=max(0,min(4,(1.43-p.z)/1.12*5))
    k=min(3,int(vertical));v=vertical-k
    side='l' if p.x>=0 else 'r';lateral=min(1,abs(p.x)/(.235*(.75+.80*max(0,(1.43-p.z)/1.12))))
    ws={f'cape_c_{k+1:02d}':(1-lateral)*(1-v),f'cape_c_{k+2:02d}':(1-lateral)*v,
        f'cape_{side}_{k+1:02d}':lateral*(1-v),f'cape_{side}_{k+2:02d}':lateral*v}
    anchor=max(0,min(1,(p.z-1.29)/.14))
    ws={n:w*(1-anchor) for n,w in ws.items()};ws['spine_05']=anchor
    return ws
helmet_prefix=('Helmet','Crown','Temple','Nape','Faceplate','Lens','Respirator','SkullCheek','Brow')
rigid_prefix=('Pectoral','Sternum','RibUpper','RibLower','Abdominal','LowerAb','Buckle','Belt','Pouch','Knee','Shin','Boot','Ankle','Thigh','Vambrace','Pauldron','ShoulderLame')

# Collapse only construction modifiers now, preserving deliberate joint loops.
stats=[]
for ob in list(low.objects):
    if ob.type!='MESH' or ob.name.startswith('CH_GreyWarden_FittedGlove'):continue
    choose(ob)
    for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    short=ob.name.removeprefix('CH_GreyWarden_');side='l' if '_L' in short else 'r'
    # Remove zero-area construction caps and weld coincident pole vertices.
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    rigid=short.startswith(rigid_prefix+helmet_prefix)
    ob['rigid_component']=rigid
    ws=[]
    for vert in ob.data.vertices:
        p=ob.matrix_world@vert.co
        if short in ['Cape','CapeHemSeam']:w=cape_weights(p)
        elif short.startswith(helmet_prefix):w={'head':1}
        elif short.startswith(('Pauldron','ShoulderLame')):w={'upperarm_'+side:1}
        elif short.startswith('Vambrace'):w={'lowerarm_'+side:1}
        elif short.startswith('Knee'):w={'calf_'+side:.84,'thigh_'+side:.16}
        elif short.startswith(('Shin','Ankle')):w={'calf_'+side:1}
        elif short.startswith(('BootFoot','BootSole','BootToeCap','BootStrap')):w={'foot_'+side:1}
        elif short.startswith('BootShaft'):w={'calf_'+side:1}
        elif short.startswith('Thigh'):w={'thigh_'+side:1}
        elif short.startswith(('Pectoral','Sternum','RibUpper')):w={'spine_05':1}
        elif short.startswith(('RibLower','Abdominal','LowerAb')):w={'spine_03':1}
        elif short.startswith(('Belt','Buckle','Pouch')):w={'pelvis':1}
        elif short.startswith(('Mantle','Scarf','FoldedHood','Hood','CapeClasp')):w={'spine_05':1}
        elif short.startswith(('FrontCapeBand','BandSeam')):
            side='l' if p.x>0 else 'r'
            if p.z>=1.30:w={'spine_05':1}
            elif p.z>=1.16:
                t=(p.z-1.16)/.14;w={'spine_05':t,'spine_03':1-t}
            elif p.z>=1.05:
                t=(p.z-1.05)/.11;w={'spine_03':t,'pelvis':1-t}
            else:
                t=max(0,min(1,(1.05-p.z)/.25));w={'pelvis':1-t,'thigh_'+side:t}
        else:w=sample_weights(p)
        ws.append(w)
    skin(ob,ws)
    ob.data.calc_loop_triangles();stats.append((ob,len(ob.data.loop_triangles)))

# Keep a high resolution skinned checkpoint; reduce only the delivery copy.
bpy.context.scene['art_status']='RIG FIT WIP - appearance and deformation require review'
for ob in imported:
    if ob!=rig:ob.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_skinned_high.blend'))
total=sum(n for o,n in stats)+sum(len(o.data.polygons)*2 for o in low.objects if 'FittedGlove' in o.name)
ratio=min(1,53500/max(1,total))
for ob,n in stats:
    if n<100:continue
    choose(ob)
    dec=ob.modifiers.new('Delivery density','DECIMATE');dec.ratio=ratio
    # Decimation acts in rest space, before the armature.
    bpy.ops.object.modifier_move_up(modifier=dec.name)
    bpy.ops.object.modifier_apply(modifier=dec.name)

# Join by material, leaving four portable material groups and preserving weights.
parts=[]
for role in ['Armor','Cloth','Leather','Visor']:
    obs=[o for o in low.objects if o.type=='MESH' and o.data.materials and o.data.materials[0].name=='M_GreyWarden_'+role]
    if not obs:continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object
    ob.name='SKM_GreyWarden_'+role;ob.data.name=ob.name+'_Mesh';parts.append(ob)
    choose(ob)
    trim=ob.modifiers.new('Budget trim','DECIMATE');trim.ratio=.875
    bpy.ops.object.modifier_move_up(modifier=trim.name);bpy.ops.object.modifier_apply(modifier=trim.name)
    # Decimation interpolates groups, so limit and normalise again after topology edits.
    for v in ob.data.vertices:
        ws=normalise({ob.vertex_groups[g.group].name:g.weight for g in v.groups})
        for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
        for name,w in ws.items():ob.vertex_groups[name].add([v.index],w,'REPLACE')
    # Unique UVs per 2K material set, 16px-ish padding, stable triangulation for bake.
    choose(ob);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.008,area_weight=.3,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    tri=ob.modifiers.new('Locked triangles','TRIANGULATE');bpy.ops.object.modifier_move_up(modifier=tri.name);bpy.ops.object.modifier_apply(modifier=tri.name)
    ob.data.calc_loop_triangles()

errors=[]
for name,old in original.items():
    b=rig.data.bones[name]
    if (b.parent.name if b.parent else None)!=old['parent']:errors.append(name+' parent changed')
    if max(abs(b.matrix_local[i][j]-old['matrix'][i][j]) for i in range(4) for j in range(4))>1e-5:errors.append(name+' rest matrix changed')
report={'status':'WIP; engine and visual acceptance pending','original_bone_count':len(original),'original_bone_errors':errors,'extra_bones':[b.name for b in rig.data.bones if b.name not in original],
 'triangles':sum(len(o.data.loop_triangles) for o in parts),'parts':[{ 'name':o.name,'triangles':len(o.data.loop_triangles),'vertices':len(o.data.vertices),'uv_layers':len(o.data.uv_layers),'unweighted':sum(not v.groups for v in o.data.vertices),'max_influences':max(len(v.groups) for v in o.data.vertices)} for o in parts],
 'source_hand_topology':'Gloves derived from user-provided Quinn reference; preserve mannequin hand/finger weights.',
 'scale':'metres in Blender; source armature retains original parent 0.01 transform; export FBX_SCALE_UNITS',
 'inferred':'Cape bone locations and costume thickness inferred. No claim of 1:1 reference acceptance.'}
(ROOT/'review/04_skin_report.json').write_text(json.dumps(report,indent=2))
if errors:raise RuntimeError(errors)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_skinned.blend'))
print('SKIN_REPORT',json.dumps(report))
