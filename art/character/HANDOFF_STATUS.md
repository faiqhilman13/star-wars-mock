# Grey Warden — Codex / Claude handoff

Status: IN PROGRESS — technical import candidate delivered; final art likeness remains unapproved.

Codex owns character art, Blender source, skinning and export. Claude owns gameplay integration, animation state setup and in-engine validation. Authoritative communication is append-only at ../../collab/messages/codex_to_claude.md and claude_to_codex.md. Finished deliveries go to ../../collab/incoming/grey_warden/, only with a READY message. No direct Unreal access by Codex.

Approved design: original helmeted grey Jedi; dark charcoal cape and hood down; weathered gunmetal segmented armor; Kipchak-inspired skull-like faceplate. See ref/approved-concept.png and ref/helmet-detail.png. Generated turnaround and action sheet are design references, not a 3D result or animation clips.

Delivery contract: UE 5.8, original Quinn/Manny SK_Mannequin bone names, hierarchy and A-pose; existing hand_r saber attachment; 30–60k triangles, one LOD, at most four materials, 2K BaseColor/Normal/ORM maps. No new weapon is needed; existing blue saber remains separate. Preserve original bones and explicitly list cape additions. Validate scale with a clean export/import round trip.

No C++ files, gameplay blueprints, existing animation clips, or original skeleton assets are to be replaced by this art build. Feedback from Claude can go in CLAUDE_FEEDBACK.md.

3D method: fully local Blender, as requested. No Scenario upload or generation authorized.

Current milestone: collab/incoming/grey_warden_rigcheck contains a textured, skinned technical import candidate (57,619 triangles, four slots, 12 PNGs). Claude acknowledged receipt and is testing it in engine. CH_GreyWarden_rigcheck_v1.blend freezes that version. No claim of final art or 1:1 acceptance.

The user approved the shape checkpoint, then explicitly requested straight lower legs. That correction follows the exact Quinn knee/ankle positions, overriding the outward stance in the generated reference. The supplied original Quinn FBX and MM_Idle are under ref/. All 88 imported original bones retain their rest transforms; 15 cape bones were added. Local FBX round trip retained the hierarchy and 180.24 cm height. The idle review removes duplicated FBX object-scale tracks only; the source animation and bones are not changed.

Latest art delivery: collab/incoming/grey_warden_v3 (59,749 triangles), with broad coat borders, wider diagonal tabard, three thigh armor plates per side, flatter knee/shin plates, shoulder clasp, darker controlled metal, and repaired coat/knee weights. CH_GreyWarden_candidate.blend contains this textured/skinned version. Authoring remains metres; the export copy uses native centimetres and identity mesh/armature transforms, with FBX UnitScaleFactor approximately 1. Build scripts 03 through 07 reproduce the pipeline; 03b adds the reference construction pass.

Claude confirmed v3 default-import height is correct at 180.24 cm. Its original skeleton, materials, saber grip, idle, swings, two-handed guard, flip and dash passed in Unreal with no runtime errors. He then adopted grey_warden_v4: same art and weights, redundant FBX Pose record omitted, all 103 skin-cluster rest matrices retained. The relative-matrix warning is gone; UE emits an expected missing-pose message and successfully reconstructs FbxSDKBindPose. Engine import reports 58,434 vertices and 104 bones including the root node. This native-centimetre/cluster-only bind recipe is now the default in 06_export_candidate.py. Do not rotate the asset or change that recipe for later art revisions.

Runtime cape dynamics is owned by Claude. Orientation must stay as it is: the reference matches +Y in UE mesh space; the earlier README -Y statement was incorrect. The actual export orientation was already correct.

Final likeness remains WIP. review/07_candidate contains textured rest, idle and diagnostic poses. review/08_drape is a rejected cloth study: it narrowed the silhouette and intersected the outer outfit, so it was not promoted. Technical passes are not full visual acceptance.
