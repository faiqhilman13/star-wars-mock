A = "/Game/Jedi/Audio/"
J = "/Game/Jedi/Blueprints/"
def snd(n): return A + n + "." + n
def child(name, parent):
    if not T("asset.exists", path=J + name):
        T("bp.create", folder_path="/Game/Jedi/Blueprints", asset_name=name, asset_type=ref(parent))
    bp = ref(J + name + "." + name)
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    return bp
def run():
    out = {}
    names = ["SW_Blaster_Deflect", "SW_Blaster_Fire", "SW_Force_Lightning_Loop", "SW_Force_Push", "SW_Remote_Explode", "SW_Remote_Hum_Loop",
             "SW_Saber_Clash", "SW_Saber_Hit", "SW_Saber_Hum_Loop", "SW_Saber_Ignite", "SW_Saber_Retract", "SW_Saber_Swing1", "SW_Saber_Swing2", "SW_Saber_Swing3"]
    out["loops"] = {n: T("obj.get_properties", instance=ref(snd(n)), properties=["bLooping"]) for n in names if "Loop" in n}
    T("asset.save_assets", asset_paths=[A + n for n in names])

    # Jedi
    jedi = ref(J + "BP_Jedi.BP_Jedi")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=jedi), values=json.dumps({
        "HumSound": snd("SW_Saber_Hum_Loop"), "IgniteSound": snd("SW_Saber_Ignite"), "RetractSound": snd("SW_Saber_Retract"),
        "SwingSounds": [snd("SW_Saber_Swing1"), snd("SW_Saber_Swing2"), snd("SW_Saber_Swing3")],
        "HitSound": snd("SW_Saber_Hit"), "ClashSound": snd("SW_Saber_Clash"), "DeflectSound": snd("SW_Blaster_Deflect"),
        "PushSound": snd("SW_Force_Push"), "LightningLoopSound": snd("SW_Force_Lightning_Loop"),
        "StumpMaterial": "/Game/Jedi/Materials/MI_Lava.MI_Lava", "bDecapitation": True}))
    T("bp.compile_blueprint", blueprint=jedi, warnings_as_errors=False)

    # Bolt + remote
    bolt = child("BP_BlasterBolt", "/Script/JediArena.BlasterBolt")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=bolt), values=json.dumps({"ImpactSound": snd("SW_Saber_Hit")}))
    T("bp.compile_blueprint", blueprint=bolt, warnings_as_errors=False)
    remote = child("BP_TrainingRemote", "/Script/JediArena.TrainingRemote")
    rcdo = T("bp.get_default_object", blueprint=remote)
    T("obj.set_properties", instance=rcdo, values=json.dumps({"BoltClass": J + "BP_BlasterBolt.BP_BlasterBolt_C",
        "FireSound": snd("SW_Blaster_Fire"), "ExplodeSound": snd("SW_Remote_Explode"), "HitFX": "/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"}))
    hum = T("actor.get_components", actor=rcdo, component_type=ref("/Script/Engine.AudioComponent"))
    out["remote_hum_comp"] = hum
    if hum:
        T("obj.set_properties", instance=hum[0], values=json.dumps({"sound": snd("SW_Remote_Hum_Loop")}))
    T("bp.compile_blueprint", blueprint=remote, warnings_as_errors=False)

    # Sith saber hum (3D)
    red = ref(J + "BP_LightsaberRed.BP_LightsaberRed")
    existing = [c for c in T("actor.get_components", actor=T("bp.get_default_object", blueprint=red), component_type=ref("/Script/Engine.AudioComponent"))]
    if not existing:
        ac = T("actor.add_component", owner=red, component_type=ref("/Script/Engine.AudioComponent"), name="Hum")
        T("obj.set_properties", instance=ac, values=json.dumps({"sound": snd("SW_Saber_Hum_Loop"), "bAutoActivate": True,
            "relativeLocation": {"x": 0, "y": 0, "z": 60}, "volumeMultiplier": 0.5, "pitchMultiplier": 0.85, "bOverrideAttenuation": True}))
        att = json.loads(T("obj.get_properties", instance=ac, properties=["attenuationOverrides"]))["attenuationOverrides"]
        att["bAttenuate"] = True; att["bSpatialize"] = True; att["falloffDistance"] = 1100.0
        att["attenuationShapeExtents"] = {"x": 120.0, "y": 0.0, "z": 0.0}
        T("obj.set_properties", instance=ac, values=json.dumps({"attenuationOverrides": att}))
        out["red_hum"] = T("obj.get_properties", instance=ac, properties=["sound", "bOverrideAttenuation"])
    T("bp.compile_blueprint", blueprint=red, warnings_as_errors=False)

    # Place two remotes over the arena
    placed = [a for a in T("scene.find_actors", name="", tag="", collision_channels=[]) if T("actor.get_label", actor=a).startswith("TrainingRemote")]
    if not placed:
        for i, (x, y) in enumerate([(300, 700), (300, -700)]):
            a = T("scene.add_to_scene_from_asset", asset_path=J + "BP_TrainingRemote", name="TrainingRemote%d" % i, xform=xf((x, y, 300)))
            T("actor.set_label", actor=a, label="TrainingRemote%d" % i)
            T("scene.set_actor_folder", actor=a, folder_path="Arena/Gameplay")
    T("asset.save_assets", asset_paths=[J + "BP_Jedi", J + "BP_BlasterBolt", J + "BP_TrainingRemote", J + "BP_LightsaberRed"])
    return out
