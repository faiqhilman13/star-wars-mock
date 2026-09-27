# Grey Warden — reference and production brief

ASSET CH_GreyWarden / SKM_GreyWarden

CATEGORY Character, armored humanoid biped.

VIEWS Approved concept: front three-quarter and rear three-quarter, approximately 20-degree yaw and level long-lens camera. Helmet detail: three-quarter, front and rear. Turnaround: generated front, left, back and right; individual panel boxes recorded in review/reference-panels.json. Side panels have unintended yaw and must not be treated as exact metric orthographic views. Front crown y=38, floor y=897 (859px subject height). Back crown y=37, floor y=895. Action sheet is pose intent only; clipped blades in parry/dodge prohibit weapon measurement.

SCALE Preserve Quinn source armature scale and rest pose. Approximately 1.8m adult, final scale measured from source FBX. The concept has broader male armored shoulders than Quinn; armor silhouette can broaden without moving skeleton joints.

PROPORTIONS Front sheet pixel landmarks (y, measured visually): crown 38; chin 166; shoulder 199; chest base 285; belt 373; crotch under cloth inferred 470; knees 649; ankles 805; floor 897. Relative heights from floor / 859: chin .851; shoulder .813; chest base .712; belt .610; crotch .497; knee .289; ankle .107. Helmet width ~108px / height859=.126; shoulders ~274/859=.319; belt ~174/859=.203; cape hem width ~376/859=.438. These are reference ratios, not a claim that mannequin joints share them.

PARTS Undersuit and gloves deform; armor plates separate rigid shells fitted over garment; belt and pouches; layered front tabards deform; cape and hood separate, cape needs supplemental bones and later engine physics tuning. Helmet rigid to head, lenses separate shading region. Keep body source hidden in master as calibration reference, never ship Quinn mesh as part of the costume.

SILHOUETTE Tapered skull-mask helmet; folded collar/hood; layered shoulder armor; long calf-length triangular cape; segmented shin armor and substantial boots.

MATERIALS At most four export roles: M_GreyWarden_Armor (weathered graphite metal), M_GreyWarden_Cloth (charcoal weave), M_GreyWarden_Leather (dark brown belt/gloves/boots), M_GreyWarden_Visor (black optics). 2K BaseColor sRGB, DirectX tangent Normal linear, ORM linear = R occlusion G roughness B metallic. No baked directional light. Hidden skin/hair are not needed for the approved helmeted design.

ARTICULATION Original exported Quinn SK_Mannequin hierarchy and A-pose unchanged. All original bones retained. Saber remains separate using hand_r. Supplemental cape bones permitted; enumerate them in delivery report. Action sheet required, animation clips are separate future deliverables unless explicitly requested; do not replace partial gameplay clips.

INFERRED Armor under cape, back of torso, exact cloth seams, inner helmet, boot soles, body depth and unseen hand surfaces. No source image proves these. Generated views also vary in tiny rivet and scratch layouts. Approved concept takes priority for design, original Quinn takes priority for joint placement and rest pose. Surface scars are not guaranteed 1:1.

TARGET Unreal Engine 5.8 JediArena, SK_Mannequin, third-person over-shoulder. Authoring forward -Y, Z up, metres internally with FBX Units Scale, as required by collab/README_FOR_CODEX.md. 30–60k triangles one LOD, four materials maximum. FBX only mesh+armature, no leaf bones, bake_anim false, smoothing FACE. Verify scale and hierarchy after reimport. Handoff through C:/Users/User/PROJECTS/jedi-arena/collab/incoming/. Do not access the Unreal project.

ACCEPTANCE Status pending. Never label a procedural approximation 1:1. Require matched-camera evidence and list measured deviations. Skeleton/skin/cloth/material/export tests must pass separately from appearance.
