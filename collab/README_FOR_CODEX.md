# Codex ↔ Claude collaboration (Jedi Arena, UE 5.8)

Claude is building the gameplay: a C++ Jedi character, saber combat, Force powers, and the arena. You (Codex) are building the character assets. We talk through files in this folder. Claude's live session watches it.

## How to talk to Claude
- **Send a message:** append to `messages/codex_to_claude.md`. Use a new entry each time:
  ```
  ## [YYYY-MM-DD HH:MM] <short subject>
  <message: what you delivered or need, file paths, questions>
  STATUS: READY | WIP | QUESTION
  ```
  Only append; never rewrite earlier entries. Claude picks up new entries within a few minutes.
- **Read replies:** read `messages/claude_to_codex.md`. Claude appends there in the same format.
- Don't message Claude with `claude --resume` or `claude -p`. Those start a separate copy of the conversation that the live session never sees.

## Where to put assets
`incoming/<asset_name>/`, for example `incoming/hero_jedi/`:
- `<asset_name>.fbx`: the mesh, rigged and skinned
- `textures/`: PNG files named `T_<asset>_<part>_{BaseColor|Normal|ORM|Emissive}.png`. ORM means R=AO, G=Roughness, B=Metallic, and the normal map is DirectX style (Y−).
- `preview.png`: front and 3/4 renders
- `NOTES.md`: height, material slots, rig or bone notes, anything unusual

Write to a temp name and rename when done, or post a message with `STATUS: READY`. Claude only imports once there's a READY message.

## Asset requirements (so it works with the existing animations)
**Units, axes and scale**
- Z-up, 1 unit = 1 cm in Unreal. From Blender: metric units with scale 1.0. Either apply scale ×100 before export, or export with "FBX Units Scale", then check the height in the FBX.
- Height about 175–185 cm, feet at Z=0, pivot at the ground between the feet.
- Match Quinn's actual orientation in the exported reference (the UE5 mannequin faces +Y in mesh space; Unreal rotates the mesh −90° yaw in the character). Your v2 already matches.

**Skeleton (most important)**
- Best: skin directly to the UE5 Mannequin skeleton. Use the same bone names and hierarchy (`root > pelvis > spine_01..05 > neck_01 > head`, `clavicle_l/r > upperarm > lowerarm > hand`, finger bones `thumb/index/middle/ring/pinky_01..03_l/r`, `thigh > calf > foot > ball`).
- A-pose like the UE5 mannequin. `root` sits at the origin.
- That way every existing animation works as-is: locomotion, the saber combo, block/parry, dash, flip and Force poses.
- **Right hand:** the saber attaches to bone `hand_r`. Keep the hand orientation mannequin-like.
- Any other humanoid rig (Mixamo, Rigify, custom) also works, but tell Claude the bone names in `NOTES.md` so it can set up retargeting (IK Retargeter). Expect some extra iteration.
- No extra root motion or scale on the armature object, and leave out leaf/end bones.

**Mesh and materials**
- Game-ready: under about 60k triangles for the hero character, and at most 4 material slots, e.g. `M_Body`, `M_Robe`, `M_Head`, `M_Hair`.
- Loose robe or cape parts should be weighted to the nearest bones. There's no cloth sim for now.
- Optional extras, as separate FBX files: a custom lightsaber hilt (static mesh, 28 cm long along +Z, pivot at the grip centre, emitter at the top) and props.

## Current project state (for context)
- Unreal project: `C:\Users\User\Documents\Unreal Projects\JediArena` (UE 5.8). Don't open or edit it while Claude is working in it. Hand everything over through `incoming/`.
- The existing player uses `SKM_Quinn_Simple` on the `SK_Mannequin` skeleton, and your character will replace it.
- Existing hilt reference: `../art/SM_SaberHilt.fbx` and `../art/hilt_build.py`, a Blender script showing the export settings that work with Unreal.
