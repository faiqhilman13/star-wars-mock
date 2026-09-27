# Grey Warden quality status

Latest adopted review asset: collab/incoming/grey_warden_v4. It has 59,749 triangles, four material slots and twelve 2K PNGs. Claude confirmed default-import height of 180.24 cm and combat regression passes for idle, swings, two-handed guard, flip, dash and saber grip. V4 has the same visual asset as v3 and omits the redundant Pose record while retaining all 103 skin-cluster rest matrices. Claude confirmed the relative-matrix warning is gone and adopted v4; UE still emits an expected message before successfully reconstructing its bind pose. Its engine import reports 58,434 split vertices and 104 bones including the root node. Local diagnostic poses and supplied idle are under 07_candidate.

Final art acceptance has not passed. The latest measured forms silhouette IoU is 0.8691 front and 0.8571 back, below the skill's 0.90 forms target; small shoulder-attachment edits followed that measurement. These comparisons use the relaxed modeling pose, while the export uses Quinn's A-pose. The deliberately straightened lower legs override the reference's splayed stance at the user's request, so that part must remain straight rather than chasing the old silhouette. These metrics are not percentages of overall visual fidelity.

The analytical reference masks now fill enclosed bright-metal highlight holes, retaining the background connected to the panel boundary. Original reference artwork is unchanged. Old masks incorrectly treated bright armor highlights as empty silhouette regions.

Remaining visible differences include the exact collar fold arrangement, cape edge wear and drape, armor faceting, pouch construction and surface weathering. The rebuilt broad rear hood and shortened pointed hem tails improve the prior version but do not make it 1:1. Lower-hem band measurements remain outside tolerance. Generated front/back hem shapes also disagree, and side views contain yaw; unseen depth is inferred.

Do not promote this package to final because its rig, dimensions or triangle count pass. Exact combat grip/clearance, runtime cape collision, material appearance under arena lighting and final visual acceptance are separate outstanding checks.

Saved source checkpoints:
- CH_GreyWarden_forms.blend: latest relaxed modeling forms.
- CH_GreyWarden_skinned.blend: A-pose/UV/skin checkpoint.
- CH_GreyWarden_candidate.blend: latest textured candidate with shoulder/knee weight refinements.
- CH_GreyWarden_rigcheck_v1.blend: frozen original technical handoff.

The shader bakes logged an unused EnvSamplerTex path from the supplied reference FBX. It is not a character texture or a delivery dependency. All twelve delivery PNGs were created locally, checked for 2048x2048 size, and copied with SHA-256 verification.
