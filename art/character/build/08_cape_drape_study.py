"""Non-destructive local cloth study; does not alter delivered asset or rig."""
import bpy,pathlib,sys,json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CH_GreyWarden_forms.blend'))
cape=bpy.data.objects['CH_GreyWarden_Cape']
# Surface sim acts before shell thickness. Pin the shoulder attachment, grade below.
for modifier in list(cape.modifiers):cape.modifiers.remove(modifier)
pin=cape.vertex_groups.new(name='DrapePin')
for v in cape.data.vertices:
    w=max(0,min(1,(v.co.z-1.32)/.12))
    if w:pin.add([v.index],w,'REPLACE')
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'ref/SKM_Quinn_Simple_reference.fbx'),automatic_bone_orientation=False,use_anim=False)
refs=set(bpy.data.objects)-before
body=next(o for o in refs if o.type=='MESH')
# Bake just the imported reference's object transform for a stable collision proxy.
mw=body.matrix_world.copy()
for v in body.data.vertices:v.co=mw@v.co
body.parent=None;body.matrix_world.identity()
for mod in list(body.modifiers):body.modifiers.remove(mod)
body.modifiers.new('Body clearance','COLLISION');body.collision.thickness_outer=.012
body.hide_render=True
cloth=cape.modifiers.new('Drape study','CLOTH');settings=cloth.settings
settings.quality=6;settings.mass=.35;settings.air_damping=3
settings.tension_stiffness=20;settings.compression_stiffness=20;settings.shear_stiffness=12;settings.bending_stiffness=.7
settings.vertex_group_mass=pin.name;settings.pin_stiffness=1
cloth.collision_settings.use_collision=True;cloth.collision_settings.distance_min=.006
cloth.collision_settings.use_self_collision=True;cloth.collision_settings.self_distance_min=.006
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=55;scene.render.fps=30
cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=55
for frame in range(1,56):
    scene.frame_set(frame);bpy.context.view_layer.update()
    cape.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    if frame%10==0:print('DRAPE_FRAME',frame,flush=True)
bpy.ops.object.select_all(action='DESELECT');cape.select_set(True);bpy.context.view_layer.objects.active=cape
bpy.ops.object.modifier_apply(modifier=cloth.name)
solid=cape.modifiers.new('Cloth thickness','SOLIDIFY');solid.thickness=.003;solid.offset=0
# The old analytical edge ribbon no longer follows the simulated hem; omit in study.
hem=bpy.data.objects.get('CH_GreyWarden_CapeHemSeam')
if hem:bpy.data.objects.remove(hem,do_unlink=True)
for ob in refs:bpy.data.objects.remove(ob,do_unlink=True)
scene.frame_set(1)
bounds=[cape.matrix_world@v.co for v in cape.data.vertices]
(ROOT/'review/08_drape_bounds.json').write_text(json.dumps({'min':[min(p[i] for p in bounds) for i in range(3)],'max':[max(p[i] for p in bounds) for i in range(3)],'status':'STUDY ONLY, not promoted'},indent=2))
out=ROOT/'review/08_drape_study.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
sys.path.insert(0,r'C:/Users/User/.agents/skills/blender-image-to-3d/scripts')
import review_render as R
old=R.setup_engine
def engine(scene,a,eng,scope,center,extent):
    old(scene,a,eng,scope,center,extent);scene.render.engine='BLENDER_EEVEE'
R.setup_engine=engine
R.main(R.parse(['--blend',str(out),'--out',str(ROOT/'review/08_drape'),'--collections','LOW','--views','front,back,threequarter','--mode','material','--res','1000','--samples','32']))
print('DRAPE_STUDY_COMPLETE',flush=True)
