# Grey Warden - technical import candidate

READY for a technical import test only. Appearance remains WIP, not an approved final 1:1 character.

## Files and measurements
- SKM_GreyWarden.fbx: one skeletal mesh, 59,749 triangles, four material slots, no animations.
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
