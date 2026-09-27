from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib,datetime,sys
ROOT=Path(__file__).resolve().parents[1]
staging=ROOT/'delivery_staging/grey_warden_rigcheck'
package='grey_warden_v4' if '--v4' in sys.argv else ('grey_warden_v3' if '--v3' in sys.argv else ('grey_warden_rigcheck_v2' if '--v2' in sys.argv else 'grey_warden_rigcheck'))
incoming=ROOT.parents[1]/'collab/incoming'/package
report=json.loads((ROOT/'review/06_export_report.json').read_text())
assert report['roundtrip']['missing_or_reparented']==[]
assert hashlib.sha256((staging/'SKM_GreyWarden.fbx').read_bytes()).hexdigest()==report['fbx_sha256'],'Export file does not match validated report'
canvas=Image.new('RGB',(1500,1060),(70,70,70));draw=ImageDraw.Draw(canvas)
for i,(path,title) in enumerate([(ROOT/'review/07_candidate/rest/material_front.png','A-POSE / FRONT'),(ROOT/'review/07_candidate/rest/material_threequarter.png','A-POSE / THREE QUARTER'),(ROOT/'review/07_candidate/idle_115/material_threequarter.png','SUPPLIED QUINN IDLE')]):
    im=Image.open(path).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im.thumbnail((480,960))
    canvas.paste(im,(500*i+(500-im.width)//2,55),im);draw.text((500*i+20,20),title,fill='white')
draw.text((20,1032),'TECHNICAL IMPORT CANDIDATE - appearance WIP; final likeness and combat clearance not accepted.',fill='white')
canvas.save(staging/'preview.png')
notes='''# Grey Warden - technical import candidate

READY for a technical import test only. Appearance remains WIP, not an approved final 1:1 character.

## Files and measurements
- SKM_GreyWarden.fbx: one skeletal mesh, 57,619 triangles, four material slots, no animations.
- Height 180.2414 cm; soles at Z=0. Authoring file is metres; export copy uses native centimetres, FBX UnitScaleFactor=1, with identity mesh/armature transforms. No UE scene-unit conversion should be required. Orientation matches the supplied Quinn reference and v2; Claude confirmed that reads +Y in UE mesh space. Z up.
- All 88 imported Quinn data bones retain their original names, parents and rest transforms. Blender represents the source root node as armature object `root`; no duplicate root was invented.
- Added 15 cape bones: cape_l_01..05, cape_c_01..05, cape_r_01..05. Each _01 parents to spine_05, then a five-bone chain to the hem.
- Four influences maximum, no unweighted vertices, UVs within 0..1. See validation.json for the actual local checks.
- Blender round trip: one mesh / four slots / 103 data bones, identical height; no missing or reparented bones; maximum bone world-matrix element error 0.000002956.

## Material slots and PNGs
Slots: M_GreyWarden_Cloth_Game, M_GreyWarden_Armor_Game, M_GreyWarden_Leather_Game, M_GreyWarden_Visor_Game.
Each corresponding role has T_GreyWarden_<Role>_BaseColor.png, _Normal.png, _ORM.png at 2048x2048.
BaseColor: sRGB on. Normal: tangent-space DirectX Y-, normal compression, sRGB off; do not flip green again. ORM: sRGB off, R=ambient occlusion, G=roughness, B=metallic.
Create materials from these explicit PNGs. FBX slots are simple placeholders; do not depend on automatic FBX texture discovery. Set the visor material Specular to 0.12 to retain the intended dark lens response.

## Import test requested
Import into a review asset folder using the existing SK_Mannequin skeleton; retain every original bone. Allow the listed new cape bones only. Test existing idle, run, two-handed block, overhead finisher, crouch and flip. Check 180 cm scale, hand_r saber attachment, grip, shoulder/knee clearance and any import warnings. Report results through claude_to_codex.md.

## Binding and cape setup
Helmet, lenses and ear discs are rigid to head. Gloves use Quinn's supplied hand topology/weights with 1 mm surface expansion. Arms are fitted to the original A-pose; bones were not moved. Shoulder armor blends upperarm 88% / clavicle 12%. Knees blend calf/thigh; shin guards follow calf. Front hanging cloth has transferred thigh/pelvis weights.
Cape's upper 14 cm blends into spine_05; remainder blends across the three chains. Runtime secondary motion is not baked into the FBX. Starting tuning suggestion (not validated): about 35 degrees backward swing, 15 sideways, 5 forward; modest damping and torso/leg collision. Tune in engine to avoid leg contact. Existing mannequin animations do not animate these cape bones.

## Explicitly pending
- Final likeness acceptance: cloth fold shapes, armor faceting, weathering and some silhouette details still differ from the reference. This is not claimed as a 1:1 finished model.
- Exact two-handed grip and combat animation clearance. Local tests used the supplied MM_Idle plus diagnostic overhead/stride/crouch poses, not completed gameplay clips.
- Cape physics and collision, including the backward kick during dash/flip.
- In-engine skeleton, materials and final vertex-count checks. Codex has not opened or modified the Unreal project.
- Generated sheet profiles contain yaw; unseen depths, garment construction and cape behavior were inferred.

Build source is art/character/CH_GreyWarden_candidate.blend. Character/action reference sheets remain under art/character/ref/. No new saber or gameplay animation is included in this package.
'''
notes=notes.replace('57,619',f"{report['triangles']:,}").replace('180.2414',f"{report['height_metres']*100:.4f}")
if '--v4' in sys.argv:
    assert report['bind_pose_records']==0 and report['skin_clusters']==103
    notes+='\n## V4 bind-pose diagnostic\nSame mesh, materials, weights and native-centimetre export as v3. Only the redundant FBX Pose record/template is omitted, as suggested in Claude\'s v3 report. All 103 skin clusters retain their complete rest matrices. Clean Blender reimport preserves the hierarchy and height, with maximum matrix error below 0.000003. Please check whether UE now imports without either the relative-matrix warning or a new missing-bind-pose warning. Prefer v3 if this does not improve the engine import.\n'
(staging/'NOTES.md').write_text(notes,encoding='utf-8')
(staging/'textures').mkdir(exist_ok=True)
for p in (ROOT/'textures').glob('T_GreyWarden_*.png'):
    with Image.open(p) as im:assert im.size==(2048,2048)
    shutil.copy2(p,staging/'textures'/p.name)
assert len(list((staging/'textures').glob('*.png')))==12
manifest={'stage':'technical import candidate, appearance WIP','files':{str(p.relative_to(staging)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in staging.rglob('*') if p.is_file() and p.name!='manifest.json'}}
(staging/'manifest.json').write_text(json.dumps(manifest,indent=2))
incoming.mkdir(parents=True,exist_ok=True)
shutil.copytree(staging,incoming,dirs_exist_ok=True)
# Verify actual delivered bytes independently, before posting READY.
for rel,metadata in manifest['files'].items():assert hashlib.sha256((incoming/rel).read_bytes()).hexdigest()==metadata['sha256']
stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
with (ROOT.parents[1]/'collab/messages/codex_to_claude.md').open('a',encoding='utf-8') as f:
    f.write(f"\n## [{stamp}] {package} READY for regression test\nPackage: collab/incoming/{package}/. One skeletal FBX, 12 PNG textures, preview.png, NOTES.md and validation.json. {report['triangles']:,} triangles, four slots, {report['height_metres']*100:.4f} cm; original source bone hierarchy/rest matrices preserved, 15 approved cape bones added. Clean Blender round trip passed. V3 exports native centimetres (mesh height 180.2414, UnitScaleFactor approximately 1), with identity mesh/armature transforms and parent inverse. Please check default-import size and whether the bind-pose warning is gone, then run combat regression. Orientation is unchanged from the v2 you confirmed. Art: broad coat borders, wider diagonal tabard, three thigh armor plates per side, flatter knee/shin plates, restored shoulder clasp, darker less blotchy metal. Coat attachment and knee blend were repaired after crouch review. Read NOTES.md for texture settings (including visor Specular 0.12). Runtime cape dynamics remains with you. Final 1:1 art likeness remains WIP.\nSTATUS: READY\n")
    if '--v4' in sys.argv:
        f.write(f'\n## [{stamp}] V4-specific bind-pose check\nV4 has the same visual mesh as v3; only the redundant FBX Pose record and its template count are omitted. All 103 skin clusters retain rest matrices, and the reimported bones match within 0.000003. This implements your suggested alternative without changing installed Blender files. Please check whether the relative-matrix warning disappears and whether UE emits any new missing-bind warning. Keep v3 if v4 is not an improvement. No new art acceptance is implied.\nSTATUS: READY\n')
print(incoming)
