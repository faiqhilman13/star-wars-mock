"""Material WIP inspection using standard skill cameras, no alteration to master."""
import sys,pathlib,bpy
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,r'C:/Users/User/.agents/skills/blender-image-to-3d/scripts')
import review_render as R
original=R.setup_engine
def setup(scene,a,engine,scope,center,extent):
    original(scene,a,engine,scope,center,extent)
    scene.render.engine='BLENDER_EEVEE'
    scene.render.image_settings.color_mode='RGBA'
R.setup_engine=setup
args=R.parse(['--blend',str(ROOT/'CH_GreyWarden_master.blend'),'--out',str(ROOT/'review/03_forms'),'--collections','LOW','--views','front,side,threequarter,back','--mode','material','--res','1000','--samples','32'])
R.main(args)
