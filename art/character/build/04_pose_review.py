import bpy,pathlib,sys,json,math
from mathutils import Vector,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/('CH_GreyWarden_candidate.blend' if '--candidate' in sys.argv else 'CH_GreyWarden_skinned.blend')
REVIEW=ROOT/('review/07_candidate' if '--candidate' in sys.argv else 'review/04_rig')
REVIEW.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,r'C:/Users/User/.agents/skills/blender-image-to-3d/scripts')
import review_render as R
original=R.setup_engine
def setup(scene,a,engine,scope,center,extent):
    original(scene,a,engine,scope,center,extent);scene.render.engine='BLENDER_EEVEE'
R.setup_engine=setup
R.main(R.parse(['--blend',str(BASE),'--out',str(REVIEW/'rest'),'--collections','LOW','--views','front,side,threequarter,back','--mode','material','--res','1100','--samples','32']))
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rig=next(o for o in bpy.data.collections['RIG_DEF'].objects if o.type=='ARMATURE')
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'ref/MM_Idle.fbx'),automatic_bone_orientation=False,use_anim=True)
added=set(bpy.data.objects)-before
animrig=next(o for o in added if o.type=='ARMATURE')
action=animrig.animation_data.action
if not action:raise RuntimeError('Supplied idle has no action')
action=action.copy()
# FBX animation's object-scale tracks include the unit conversion already held
# by the mesh reference parent. Keep bone tracks; do not apply .01 a second time.
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in list(bag.fcurves):
                if not curve.data_path.startswith('pose.bones['):bag.fcurves.remove(curve)
action.name='Review_Quinn_Idle'
rig.animation_data_create();rig.animation_data.action=action
if action.slots:rig.animation_data.action_slot=action.slots[0]
for o in added:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.scene.frame_set(int(action.frame_range[0]));bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_pose_review.blend'))
for frame in [int(action.frame_range[0]),int(sum(action.frame_range)/2)]:
    R.main(R.parse(['--blend',str(ROOT/'CH_GreyWarden_pose_review.blend'),'--out',str(REVIEW/f'idle_{frame}'),'--collections','LOW','--views','front,threequarter','--action','Review_Quinn_Idle','--frame',str(frame),'--mode','material','--res','1100','--samples','32']))
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rig=next(o for o in bpy.data.collections['RIG_DEF'].objects if o.type=='ARMATURE')
def rotate_world(name,axis,degrees):
    p=rig.pose.bones[name];local=(rig.matrix_world@p.bone.matrix_local).to_3x3().inverted()@Vector(axis)
    p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(local.normalized(),math.radians(degrees))
for pose in ['overhead','stride','crouch']:
    for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion()
    if pose=='overhead':
        rotate_world('upperarm_l',(0,1,0),-115);rotate_world('upperarm_r',(0,1,0),115)
        rotate_world('lowerarm_l',(1,0,0),-40);rotate_world('lowerarm_r',(1,0,0),-40)
    elif pose=='stride':
        rotate_world('thigh_l',(1,0,0),-38);rotate_world('thigh_r',(1,0,0),28)
        rotate_world('calf_l',(1,0,0),25);rotate_world('calf_r',(1,0,0),45)
    else:
        for side in ['l','r']:
            rotate_world('thigh_'+side,(1,0,0),-65);rotate_world('calf_'+side,(1,0,0),95)
            rotate_world('foot_'+side,(1,0,0),-30)
        rotate_world('spine_03',(1,0,0),-20)
    bpy.context.view_layer.update()
    file=REVIEW/f'{pose}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file))
    R.main(R.parse(['--blend',str(file),'--out',str(REVIEW/pose),'--collections','LOW','--views','threequarter','--mode','material','--res','1100','--samples','32']))
    bpy.ops.wm.open_mainfile(filepath=str(BASE))
    rig=next(o for o in bpy.data.collections['RIG_DEF'].objects if o.type=='ARMATURE')
print('POSE_REVIEW_COMPLETE')
