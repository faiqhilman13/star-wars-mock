import math

CYL = "/Engine/BasicShapes/Cylinder"
CUBE = "/Engine/BasicShapes/Cube"
M = "/Game/Jedi/Materials/"
VC = "/Game/Variant_Combat/Blueprints/"


def mat(actor, mi):
    for c in T("actor.get_components", actor=actor, component_type=ref("/Script/Engine.StaticMeshComponent")):
        T("obj.set_properties", instance=c, values=json.dumps({"overrideMaterials": [M + mi + "." + mi]}))


def place(asset, label, loc, rot=(0, 0, 0), scale=(1, 1, 1), mi=None, folder="Arena"):
    a = T("scene.add_to_scene_from_asset", asset_path=asset, name=label, xform=xf(loc, rot, scale))
    T("actor.set_label", actor=a, label=label)
    T("scene.set_actor_folder", actor=a, folder_path=folder)
    if mi:
        mat(a, mi)
    return a


def place_cls(cls, label, loc, rot=(0, 0, 0), scale=(1, 1, 1), folder="Arena"):
    a = T("scene.add_to_scene_from_class", actor_type=ref(cls), name=label, xform=xf(loc, rot, scale))
    T("actor.set_label", actor=a, label=label)
    T("scene.set_actor_folder", actor=a, folder_path=folder)
    return a


def comp_of(actor, cls):
    return T("actor.get_components", actor=actor, component_type=ref(cls))[0]


def run():
    out = {}
    # clear previous build + template leftovers
    if "Arena" in (T("scene.get_folders") or []):
        for a in T("scene.get_actors_in_folder", folder_path="Arena", recursive=True) or []:
            T("scene.remove_from_scene", actor=a)
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        if T("actor.get_label", actor=a) in ("Floor", "SM_SkySphere", "PreviewSaber"):
            T("scene.remove_from_scene", actor=a)

    # --- platform (top surface at z=100, radius 1500) + trim ring
    place(CYL, "ArenaPlatform", (0, 0, 0), scale=(30, 30, 2), mi="MI_ArenaStone")
    place(CYL, "ArenaTrim", (0, 0, -8), scale=(30.6, 30.6, 2), mi="MI_GlowRed")
    place(CYL, "CenterSeal", (0, 0, 101), scale=(6, 6, 0.04), mi="MI_ArenaMetal")
    place(CYL, "CenterSealGlow", (0, 0, 100.5), scale=(6.3, 6.3, 0.04), mi="MI_GlowBlue")

    # --- lava far below the edge
    lava = place(VC + "Interactables/BP_Combat_LavaFloor", "Lava", (-4000, -4000, -300), scale=(80, 80, 1))
    out["lava_bounds"] = T("actor.get_actor_bounds", actor=lava)

    # --- ring of pillars with glowing caps
    for i in range(8):
        ang = math.radians(i * 45 + 22.5)
        x, y = 1300 * math.cos(ang), 1300 * math.sin(ang)
        broken = i in (2, 5)
        h = 3.5 if broken else 8.0
        place(CYL, "Pillar%d" % i, (x, y, 100 + h * 50), scale=(1.3, 1.3, h), mi="MI_ArenaPillar", folder="Arena/Pillars")
        place(CYL, "PillarBase%d" % i, (x, y, 125), scale=(1.8, 1.8, 0.5), mi="MI_ArenaStone", folder="Arena/Pillars")
        if not broken:
            place(CYL, "PillarCap%d" % i, (x, y, 100 + h * 100 + 10), scale=(1.6, 1.6, 0.2), mi="MI_ArenaStone", folder="Arena/Pillars")
            place(CYL, "PillarGlow%d" % i, (x, y, 100 + h * 100 - 30), scale=(1.35, 1.35, 0.12), mi="MI_GlowRed", folder="Arena/Pillars")

    # --- cover blocks / ruins
    for n, (loc, rot, sc) in {"Cover0": ((350, 650, 160), (0, 20, 0), (2.2, 0.8, 1.2)),
                              "Cover1": ((200, -700, 160), (0, -35, 0), (2.0, 0.8, 1.2)),
                              "Cover2": ((-500, 450, 140), (0, 60, 0), (1.2, 1.2, 0.8)),
                              "Rubble0": ((850, 150, 130), (8, 30, 12), (1.0, 0.9, 0.6))}.items():
        place(CUBE, n, loc, rot, sc, mi="MI_ArenaPillar", folder="Arena/Props")

    # --- pushable props + training dummies
    for i, (x, y) in enumerate([(-300, -350), (-250, -470), (450, 300), (500, -250)]):
        place(VC + "Interactables/BP_Combat_DamageableBox", "Crate%d" % i, (x, y, 160), folder="Arena/Props")
    for i, (x, y) in enumerate([(-450, -150), (-450, 180)]):
        place(VC + "Interactables/BP_Combat_Dummy", "TrainingDummy%d" % i, (x, y, 100), rot=(0, 180, 0), folder="Arena/Gameplay")

    # --- Sith spawners
    for i, (x, y, yaw) in enumerate([(950, 500, 200), (950, -500, 160)]):
        s = place(VC + "AI/BP_Combat_EnemySpawner", "SithSpawner%d" % i, (x, y, 100), rot=(0, yaw, 0), folder="Arena/Gameplay")
        T("obj.set_properties", instance=s, values=json.dumps({"Enemy Class": "/Game/Jedi/Blueprints/BP_SithEnemy.BP_SithEnemy_C",
                                                               "Initial Spawn Delay": 4.0, "Spawn Count": 3, "Respawn Delay": 6.0}))

    # --- player start
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.PlayerStart"), collision_channels=[]):
        T("actor.set_actor_transform", actor=a, xform=xf((-1000, 0, 200), (0, 0, 0)), worldspace=True)

    # --- navmesh
    nav = place_cls("/Script/NavigationSystem.NavMeshBoundsVolume", "ArenaNavBounds", (0, 0, 150), scale=(17, 17, 3), folder="Arena/Gameplay")

    # --- mood lighting: low red sunset sun, dim sky, pillar lights
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.DirectionalLight"), collision_channels=[]):
        T("actor.set_actor_transform", actor=a, xform={"rotation": {"pitch": -9, "yaw": 150, "roll": 0}}, worldspace=True)
        T("obj.set_properties", instance=comp_of(a, "/Script/Engine.DirectionalLightComponent"),
          values=json.dumps({"intensity": 6.0, "lightColor": {"r": 1.0, "g": 0.55, "b": 0.35, "a": 1.0}}))
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.ExponentialHeightFog"), collision_channels=[]):
        T("obj.set_properties", instance=comp_of(a, "/Script/Engine.ExponentialHeightFogComponent"),
          values=json.dumps({"fogDensity": 0.035, "fogInscatteringLuminance": {"r": 0.25, "g": 0.06, "b": 0.04, "a": 1}}))
    for i in range(8):
        if i in (2, 5):
            continue
        ang = math.radians(i * 45 + 22.5)
        x, y = 1150 * math.cos(ang), 1150 * math.sin(ang)
        l = place_cls("/Script/Engine.PointLight", "PillarLight%d" % i, (x, y, 700), folder="Arena/Lights")
        T("obj.set_properties", instance=comp_of(l, "/Script/Engine.PointLightComponent"),
          values=json.dumps({"intensity": 5000.0, "attenuationRadius": 1400.0, "lightColor": {"r": 1.0, "g": 0.12, "b": 0.05, "a": 1.0}, "castShadows": False}))

    # --- level uses the Jedi game mode
    ws = T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.WorldSettings"), collision_channels=[])[0]
    T("obj.set_properties", instance=ws, values=json.dumps({"DefaultGameMode": "/Game/Jedi/Blueprints/BP_JediGameMode.BP_JediGameMode_C"}))
    out["gm"] = T("obj.get_properties", instance=ws, properties=["DefaultGameMode"])
    T("asset.save_assets", asset_paths=["/Game/Jedi/Maps/Lvl_JediArena"])
    return out
