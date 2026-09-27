def comp_of(actor, cls):
    return T("actor.get_components", actor=actor, component_type=ref(cls))[0]
def run():
    out = {}
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.ExponentialHeightFog"), collision_channels=[]):
        c = comp_of(a, "/Script/Engine.ExponentialHeightFogComponent")
        T("obj.set_properties", instance=c, values=json.dumps({"fogDensity": 0.008, "fogHeightFalloff": 0.15, "fogInscatteringLuminance": {"r": 0.05, "g": 0.012, "b": 0.01, "a": 1}}))
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.PointLight"), collision_channels=[]):
        T("obj.set_properties", instance=comp_of(a, "/Script/Engine.PointLightComponent"), values=json.dumps({"intensity": 600.0}))
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.SkyLight"), collision_channels=[]):
        T("obj.set_properties", instance=comp_of(a, "/Script/Engine.SkyLightComponent"), values=json.dumps({"intensity": 0.6}))
    for a in T("scene.find_actors", name="", tag="", actor_type=ref("/Script/Engine.PostProcessVolume"), collision_channels=[]):
        out["pp"] = T("obj.get_properties", instance=a, properties=["bUnbound"])
        T("obj.set_properties", instance=a, values=json.dumps({"bUnbound": True, "settings": {"bOverride_AutoExposureBias": True, "autoExposureBias": -0.5, "bOverride_BloomIntensity": True, "bloomIntensity": 1.2, "bOverride_VignetteIntensity": True, "vignetteIntensity": 0.5}}))
        out["pp_after"] = T("obj.get_properties", instance=a, properties=["settings"])[:400]
    T("asset.save_assets", asset_paths=["/Game/Jedi/Maps/Lvl_JediArena"])
    return out
