# Shape checkpoint — not a finished asset

Status: FRONT/BACK SILHOUETTE TOLERANCE MET; visual approval pending. No rig, UVs, baked textures or delivery FBX. Do not import into gameplay.

Measured using shared scale (1.8m/859 reference pixels), fixed axis and floor:

| View | Registered silhouette IoU | Largest absolute band-width difference / character height |
|---|---:|---:|
| Front | 0.8883 | 0.0420 |
| Back | 0.8722 | 0.0350 |

Blockout thresholds from requested skill: IoU >=0.85, band differences <=0.05. This is not a percentage of total visual fidelity. Bounding-box-aligned comparison is also available: front 0.890, back 0.876. Front chin, belt and knee heights are constructed within 5% of measured normalized landmarks. Full rig/posed clearance checks await the exact source skeleton and are not passed.

Visible deviations and omissions: polygonal faceplate/chest surfaces, rough glove/finger masses, undeveloped boots and belt/pouches, regular placeholder cape folds, cylindrical collar folds. These require forms work, not a texture painted over the blockout. Main cape hem differs between generated front and back references; current model is a compromise inside width tolerance. Side views have yaw, so a strict side silhouette score would be misleading; profile depth remains inferred pending source rig fit.

Source remains editable in ../../CH_GreyWarden_master.blend, rebuilt by ../../build/02_blockout.py. Front, side, back, three-quarter and reference-camera clay renders are in this directory. These are actual Blender renders, not generated images.

Next after approval: detailed forms and overlap construction; exact Quinn A-pose fitting; deformation topology; four material UV/bake sets; original skeleton binding plus 15 agreed cape bones; stress poses and idle test; FBX round trip; handoff to Claude for engine verification. No claim of 1:1 likeness or game readiness is made at this checkpoint.
