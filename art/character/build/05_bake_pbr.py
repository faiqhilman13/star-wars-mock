"""Local 2K portable PBR textures; DirectX normals and linear packed ORM."""
import bpy,pathlib,sys,numpy as np,json
from types import SimpleNamespace
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,r'C:/Users/User/.agents/skills/blender-image-to-3d/scripts')
import bake_maps as B
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CH_GreyWarden_skinned.blend'))
out=ROOT/'textures';out.mkdir(exist_ok=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.threads_mode='FIXED';scene.render.threads=12
scene.render.bake.target='IMAGE_TEXTURES'
args=SimpleNamespace(extrusion=.004,ray_dist=.01,margin=12)

def material(role,mat):
    nt=mat.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
    output=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');l.new(p.outputs['BSDF'],output.inputs['Surface'])
    coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=43;noise.inputs['Detail'].default_value=4
    l.new(coord.outputs['Object'],noise.inputs['Vector'])
    base,metal,rough={'Armor':((.105,.098,.088),.90,.61),'Cloth':((.027,.025,.022),0,.92),'Leather':((.028,.017,.010),0,.70),'Visor':((.002,.003,.004),0,.40)}[role]
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[1].position=.77
    contrast=(.94,1.05) if role=='Armor' else (.78,1.15)
    ramp.color_ramp.elements[0].color=(*(c*contrast[0] for c in base),1);ramp.color_ramp.elements[1].color=(*(c*contrast[1] for c in base),1)
    l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if role=='Visor':p.inputs['Specular IOR Level'].default_value=.12;return
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=500 if role=='Cloth' else 280;fine.inputs['Detail'].default_value=2
    l.new(coord.outputs['Object'],fine.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.0005 if role=='Cloth' else .00006
    l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    remap=n.new('ShaderNodeMapRange');remap.inputs['From Min'].default_value=.25;remap.inputs['From Max'].default_value=.75
    spread=.045 if role=='Armor' else .10
    remap.inputs['To Min'].default_value=rough-spread;remap.inputs['To Max'].default_value=min(.98,rough+spread)
    l.new(noise.outputs['Fac'],remap.inputs['Value']);l.new(remap.outputs['Result'],p.inputs['Roughness'])
    if role=='Armor':
        # Sparse stretched noise gives shallow directional abrasions, no painted light.
        stretch=n.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(9,340,38)
        l.new(coord.outputs['Object'],stretch.inputs[0]);scratch=n.new('ShaderNodeTexNoise');scratch.inputs['Scale'].default_value=6
        l.new(stretch.outputs['Vector'],scratch.inputs['Vector']);threshold=n.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.76
        l.new(scratch.outputs['Fac'],threshold.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.23,.215,.19,1)
        l.new(threshold.outputs[0],mix.inputs[0]);l.new(ramp.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],p.inputs['Base Color'])

def save(img,path):img.filepath_raw=str(path);img.file_format='PNG';img.save()
def pixels(img):
    data=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(data);return data.reshape(-1,4)
def image_data(name,data):
    img=B.new_image(name,2048,True);img.pixels.foreach_set(data.ravel());img.update();return img
report=[]
for ob in list(bpy.data.collections['LOW'].objects):
    if ob.type!='MESH':continue
    role=ob.name.rsplit('_',1)[-1];mat=ob.data.materials[0];material(role,mat)
    images={}
    for kind in ['basecolor','roughness','metallic','normal','ao']:
        img=B.new_image('Bake_'+role+'_'+kind,2048,kind!='basecolor')
        print('BAKING',role,kind,flush=True)
        if kind=='metallic':
            restore=B.metallic_to_emission(ob);B.bake(scene,'EMIT',ob,None,img,args);B.restore_emission(restore)
        elif kind=='basecolor':
            nt=mat.node_tree;output=B.cycles_output(nt);p=B.principled_feeding(output)
            previous=output.inputs['Surface'].links[0].from_socket
            emit=nt.nodes.new('ShaderNodeEmission')
            nt.links.new(p.inputs['Base Color'].links[0].from_socket,emit.inputs['Color'])
            nt.links.new(emit.outputs[0],output.inputs['Surface'])
            B.bake(scene,'EMIT',ob,None,img,args)
            nt.nodes.remove(emit);nt.links.new(previous,output.inputs['Surface'])
        else:B.bake(scene,{'basecolor':'DIFFUSE','roughness':'ROUGHNESS','normal':'NORMAL','ao':'AO'}[kind],ob,None,img,args)
        images[kind]=img
    prefix='T_GreyWarden_'+role
    save(images['basecolor'],out/(prefix+'_BaseColor.png'))
    normal=pixels(images['normal']);normal[:,1]=1-normal[:,1]
    dx=image_data(prefix+'_Normal',normal);save(dx,out/(prefix+'_Normal.png'))
    orm=np.ones_like(normal);orm[:,0]=pixels(images['ao'])[:,0];orm[:,1]=pixels(images['roughness'])[:,0];orm[:,2]=pixels(images['metallic'])[:,0]
    packed=image_data(prefix+'_ORM',orm);save(packed,out/(prefix+'_ORM.png'))
    # Blender normal map nodes need +Y. Keep a packed internal GL image for previews;
    # only DirectX PNG is included in the Unreal handoff.
    images['normal'].pack()
    m=B.rebuild_material(ob,images);m.name='M_GreyWarden_'+role+'_Game'
    if role=='Visor':next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value=.12
    for key in ['roughness','metallic']:images[key].pack()
    report.append({'role':role,'size':2048,'files':[prefix+'_'+suffix+'.png' for suffix in ['BaseColor','Normal','ORM']],
                   'normal':'DirectX tangent Y-','ORM':'linear R=AO G=roughness B=metallic'})
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CH_GreyWarden_textured.blend'))
(ROOT/'review/05_texture_report.json').write_text(json.dumps(report,indent=2))
print('BAKING_COMPLETE',flush=True)
