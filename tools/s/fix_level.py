def comp_of(actor, cls):
    return T("actor.get_components", actor=actor, component_type=ref(cls))[0]
def run():
    out = {"saved": 0}
    F = "/Game/Jedi/Materials"
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        try:
            lab = T("actor.get_label", actor=a)
        except Exception:
            continue
        cls = T("obj.get_class", instance=a)["refPath"].split(".")[-1]
        if cls == "DirectionalLight":
            T("actor.set_actor_transform", actor=a, xform={"rotation": {"pitch": -9, "yaw": 150, "roll": 0}}, worldspace=True)
            T("obj.set_properties", instance=comp_of(a, "/Script/Engine.DirectionalLightComponent"), values=json.dumps({"intensity": 6.0, "lightColor": {"r": 1.0, "g": 0.55, "b": 0.35, "a": 1.0}}))
        elif cls == "ExponentialHeightFog":
            T("obj.set_properties", instance=comp_of(a, "/Script/Engine.ExponentialHeightFogComponent"), values=json.dumps({"fogDensity": 0.008, "fogHeightFalloff": 0.15, "fogInscatteringLuminance": {"r": 0.05, "g": 0.012, "b": 0.01, "a": 1}}))
        elif cls == "PointLight":
            T("obj.set_properties", instance=comp_of(a, "/Script/Engine.PointLightComponent"), values=json.dumps({"intensity": 600.0, "lightColor": {"r": 1.0, "g": 0.12, "b": 0.05, "a": 1.0}, "castShadows": False}))
        elif cls == "SkyLight":
            T("obj.set_properties", instance=comp_of(a, "/Script/Engine.SkyLightComponent"), values=json.dumps({"intensity": 0.6}))
        elif cls == "PostProcessVolume":
            T("obj.set_properties", instance=a, values=json.dumps({"bUnbound": True, "settings": {"bOverride_AutoExposureBias": True, "autoExposureBias": -0.5, "bOverride_BloomIntensity": True, "bloomIntensity": 1.2, "bOverride_VignetteIntensity": True, "vignetteIntensity": 0.5}}))
        elif lab == "Lava":
            T("obj.set_properties", instance=comp_of(a, "/Script/Engine.StaticMeshComponent"), values=json.dumps({"overrideMaterials": [F + "/MI_Lava.MI_Lava"]}))
        elif cls == "WorldSettings":
            T("obj.set_properties", instance=a, values=json.dumps({"DefaultGameMode": "/Game/Jedi/Blueprints/BP_JediGameMode.BP_JediGameMode_C"}))
        else:
            continue
        try:
            T("scene.save_actor", actor=a); out["saved"] += 1
        except Exception as e:
            out.setdefault("err", []).append(lab + ": " + str(e)[:120])
    T("asset.save_assets", asset_paths=["/Game/Jedi/Maps/Lvl_JediArena"])
    return out
