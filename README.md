# Jedi Arena (UE 5.8 prototype)

Third-person lightsaber + Force combat: a Dynasty-Warriors-style horde arena where one Jedi takes on hundreds of droids, plus the original training arena. It was built through the Unreal MCP inside the editor; the hilt and the Grey Warden character were modelled in Blender.

**Unreal project:** `C:\Users\User\Documents\Unreal Projects\JediArena\JediArena.uproject`
**Maps:** `/Game/Jedi/Maps/Lvl_HordeArena` (the horde mode) is the startup and default map. `/Game/Jedi/Maps/Lvl_JediArena` is the original training arena. Both use `BP_JediGameMode`, whose HUD is `AJediHUD`.

## Repository layout

| Path | What's in it |
|---|---|
| `unreal/JediArena/` | The Unreal project: `Source/`, `Config/`, `Content/`, `ArtSource/` and the `.uproject` |
| `tools/` | The MCP client (`ue.py`), helper shell scripts, and the editor build scripts in `tools/s/` |
| `audio/` | Sound build scripts (`audio/tools/`), the synthesized placeholder WAVs, and licence and source notes |
| `art/` | Blender sources: the hilt, the Grey Warden character and the horde enemies (`art/enemies/`) |
| `collab/` | The Codex ↔ Claude mailbox and Codex's asset deliveries |

**Syncing the Unreal project:**
- The live Unreal project sits outside this repo. `unreal/JediArena` is a mirror of it.
- Run `tools/sync_unreal.sh` before committing to refresh the mirror.
- Build and cache folders are never copied: `Binaries`, `Intermediate`, `Saved` and `DerivedDataCache`.
- To open the project from a fresh clone, copy `unreal/JediArena` somewhere and open `JediArena.uproject` with UE 5.8. Unreal will offer to compile the C++ module (Visual Studio 2022+ is required).

**Git LFS:** Unreal assets and art binaries (`.uasset`, `.umap`, `.fbx`, `.blend`, images, audio) are stored with Git LFS. Run `git lfs install` before cloning.

**Sound licences:** the downloaded Pixabay and Mixkit clips are not in the repo. Their licences allow using them in the game, but not redistributing the audio files on their own.
- `audio/licensed/sources.txt` lists every source URL.
- `audio/tools/*.py` rebuilds the game sounds from those downloads.
- The imported sound assets are already inside `Content/Jedi/Audio`.

## Controls

| Action | Keyboard / Mouse | Gamepad |
|---|---|---|
| Move / look | WASD / mouse | Left / right stick |
| Jump (press again in the air for the **Force flip double jump**) | Space | A |
| Saber combo: forehand, backhand, overhead finisher | LMB (tap to chain) | RB |
| **Block** (hold). Pressing it just before a hit (0.28 s) **parries**: the attacker staggers, you get slow-mo, +15 Force, and 2.5× damage on your next hit | Hold RMB | LT |
| **Force Dash** (works in the air; dodges melee while dashing) | Left Shift | B |
| **Force Push** (cone knockback) | Q | LB |
| **Force Pull** (enemy nearest the crosshair) | E | Y |
| **Force Lightning** (hold to channel) | Hold F | RT |
| Ignite / retract saber | T | X |
| Swap camera shoulder | R | D-pad down |
| **Cycle saber style**: single blade, dual wield (Jar'Kai), saberstaff | V | D-pad up |
| **Force Storm** (when the Force Surge meter is full) | C | Left stick click |

- The blue bar under your health is your Force.
- **Health regenerates** at 2.5 HP/s once you go 3 s without taking a hit (`HealthRegenDelay` / `HealthRegenRate` in BP_Jedi).
- Blocking costs 8 Force per hit and stops regeneration. If you run out, your guard breaks.
- While blocking, the Jedi turns to face the nearest attacker. Each swing snaps toward the nearest enemy in front of you.
- Push enemies off the platform into the lava.
- **Blaster deflection:** two training remotes circle the arena and fire bolts.
  - A held block deflects bolts toward your crosshair and costs a little Force.
  - A parry-timed block, or a bolt that meets your swinging blade, goes straight back at the shooter.
  - Remotes take 3 hits and respawn.
- **Decapitation:** a killing saber blow takes the head on combo swings 2 and 3 and on high cuts. On other killing blows it's a 60% chance (`DecapChance` in BP_Jedi).
- **Sound:** all sounds are synthesized by `audio/gen_sounds.py`. They cover the saber hum (its pitch and volume follow blade speed), ignite/retract, swings, hits, clashes, Force push, the lightning loop, and remote blaster fire, deflect and explosion. The editor command `jedi.ImportSounds <folder> /Game/Jedi/Audio` reimports them.

## Horde mode: the Duneglass Colosseum

**How it plays**
- You fight six escalating waves, alone. Enemies come through the colosseum's four gates, and drop pods fall from the sky.
- **KOs and combo hits fill the Force Surge meter.** When it's full, **Force Storm** (C) blasts everything around you with shockwaves and lightning.
- The HUD shows the KO count, combo hits, wave, crowd hype, Force Surge, the boss bar and announcer banners.
- Enemies sometimes drop orbs: green heals, blue restores Force.

**The arena**
- **The Gobbler:** a sand-pit monster that eats any enemy knocked into it. It spits the Jedi back out.
- **Fizz barrels:** they explode in chains.
- **Jump pads:** they launch you across the arena.
- **Crowd:** the stands are packed with spectators who get more excited as hype rises.

**Enemies** (all `AHordeEnemy`, in `Source/.../HordeEnemy.*`)

| Enemy | What it does |
|---|---|
| **Clanker droids** | Fodder with terrible aim and a lot of chatter |
| **Bulwark Troopers** | Carry a frontal energy shield. Break it with the Force, or hit them from the side |
| **Buzz-Rollers** | Roll in and unfold into shielded turrets. Lightning fries the shield |
| **Jet Ghosts** | Hover and fire rockets. Force Pull brings them down |
| **Magna Wardens** | Guard with electrostaffs. Parry their strikes |
| **Sith Acolytes** | Officers |
| **Scrap Colossus** (`ABossWalker`) | The boss: a junk chicken-walker. Its glowing knees are the weak points; it collapses at every 25% of health and rages below 50% |

**Models and sounds**
- Every enemy model is built in Blender by a script in `art/enemies/` on top of `enemy_lib.py`:
  - `clanker.py` and `trooper.py` (Bulwark, Jet Ghost, Warden) make skinned meshes on the mannequin skeleton, imported with `jedi.ImportSkeletal`.
  - `roller.py` makes three static meshes for the Buzz-Roller (armoured ball, turret head, spider leg), imported with `jedi.ImportStatic <fbx> <folder> <name>`.
- Each enemy type has its own death sounds (`/Game/Jedi/Audio/Deaths`):
  - Droids squawk, troopers cut out over their comms, Jet Ghosts sputter and fall, Wardens groan, and Rollers beep and pop.
  - They're built by `audio/tools/death_sounds.py` from Windows text-to-speech takes (`tts_lines.ps1`) plus synthesized layers.
  - Playback is throttled, so a Force Storm that drops thirty droids plays a handful of voices, never the same clip twice in a row.

**Code**
- `AHordeDirector`: waves, attack tokens (only a few enemies shoot or swing at once), KOs, hype and banners.
- `AColosseumArena`: the procedural arena, plus `ASandGobbler`, `AFizzBarrel` and `AJumpPad`.
- `ADropPod` and `AJediHUD`.
- Hits reach enemies through `IJediDamageable` (`JediDamageable.h`), with a hit kind: saber, push, pull, lightning, bolt, storm or explosion.
- Debug: `jedi.HordeDebug` lists the live enemies. `ke * AddSurge 100` fills the meter.

## Architecture

- **C++ module `JediArena`** (`Source/JediArena`): `AJediCharacter` holds all of the player's gameplay:
  - saber combo with blade-sweep traces and hit-stop
  - block, parry and riposte
  - Force Push, Pull, Lightning and Dash, plus the flip double jump
  - health, death and respawn

  Tuning values live in the class defaults of `/Game/Jedi/Blueprints/BP_Jedi` (a Blueprint on top of the C++ class), under the **Jedi|…** categories.
- **Enemies** are the Combat template's Blueprint enemies (`BP_SithEnemy`, StateTree AI). `BP_Jedi` implements the template's `BPI_Damageable` interface and forwards **Apply Damage** into C++ (`ReceiveTemplateDamage`).
- **Animations** (`/Game/Jedi/Anims`) were authored in-editor with Control Rig and Sequencer.
  - **V2 moveset (the one in use):**
    - Combo: `AS_Saber_Combo1..5_V2`. The hits are a forehand, a rising backhand, a 360° spin, a hop-and-cleave, and a double-spin whirlwind finisher.
    - Stance: `AS_Saber_Idle_V2` and `AS_Saber_Run_V2`, looped by C++ (`TickStance`).
    - Block: `AS_Saber_Block_V2`.
    - The authoring scripts are in `tools/s/anim2/`.
  - **Fluidity in C++:**
    - The character turns to face its movement.
    - Each swing lunges toward the nearest target.
    - The body leans into acceleration and turns.
    - A procedural saber trail is drawn (`M_SaberTrail`).
  - **Older clips:** `AS_Saber_Swing1/2/3`, `AS_Saber_Parry`, `AS_Force_Dash`, `AS_Jump_Flip`.
- **Cape:** the Grey Warden's cape has three physics chains (`cape_l/c/r_01..05`) in `SKM_GreyWarden_PhysicsAsset`. If you rebuild that physics asset, run `jedi.FixCape <PhysicsAsset> <SkeletalMesh>`. It snaps the constraint frames to the skeleton; constraints created without a preview mesh collapse the cape. It also sets the swing limits and turns off the cape's self-collision. Run `jedi.CapeDebug` in PIE to print where the cape bones are.
- **Sounds:** the files are in `/Game/Jedi/Audio/Licensed`, and sources and licences are listed in `audio/licensed/sources.txt`.
  - Most are free-licensed Pixabay and Mixkit clips, processed by `audio/tools/build_licensed.py`.
  - The blaster is an original physically modelled "guy-wire" synthesis (`audio/tools/synth_blaster.py`).
  - Hum levels and hit ducking are set with `HumIdleVolume`, `HumSwingVolume`, `HitVolume` and `HitDuckTime` on `BP_Jedi`.
- **Building:** close the editor, then run
  `UnrealBuildTool.exe JediArenaEditor Win64 Development -Project=<uproject>`.
  For `.cpp`-only edits, `LiveCoding.Compile` works while the editor is running.
- **Editor helper:** the console command `jedi.ImplementInterface <BlueprintPath> <InterfaceClassPath>` adds a Blueprint interface to a Blueprint.

## What's in `/Game/Jedi`

- `BP_Jedi`: the player, on top of the C++ `AJediCharacter`. `BP_JediCharacter` is the older all-Blueprint prototype and is no longer used.
- `BP_SithEnemy`: child of the Combat template enemy, using the template's StateTree AI, with a red saber.
- `BP_Lightsaber` / `BP_LightsaberRed`: hilt (Blender mesh), core and glow blade, light, and an ignite/retract animation.
- `BP_ForceWave`, `BP_LightningBolt`: VFX actors for the Force powers.
- `Input/IA_Force*`, `IA_SaberToggle`: bound in `/Game/Variant_Combat/Input/IMC_Combat`.
- `Dev/BP_GripTest`: editor rig for tuning how the saber sits in the hand.

## Tooling

- `tools/ue.py`: CLI client for the editor's MCP server (`127.0.0.1:8000/mcp`).
- `tools/s/*.py`: the build scripts; most are idempotent and can be rerun.
- The editor needs `ModelContextProtocol.StartServer` (or Auto Start in Editor Preferences) before the tools can connect.
- `art/hilt_build.py`: headless Blender script that rebuilds `SM_SaberHilt.fbx`.

## Known limitations and next steps

- The sword animations are hand-keyed in-editor, so they read well but are simpler than mocap.
- In the unarmed idle and locomotion, the saber trails down and back.
- Force push and lightning still use the synthesized placeholder sounds.
- In the training arena the enemies are basic melee AI (the horde arena has its own six enemy types).
