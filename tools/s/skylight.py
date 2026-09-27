def run():
    out = {}
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        lab = T("actor.get_label", actor=a)
        if lab in ("SkyLight", "DirectionalLight"):
            comps = T("actor.get_components", actor=a, component_type=ref("/Script/Engine.LightComponentBase"))
            for c in comps:
                out[lab] = T("obj.get_properties", instance=c, properties=["Intensity", "LightColor"])
                if lab == "SkyLight":
                    T("obj.set_properties", instance=c, values=json.dumps({"Intensity": 1.5}))
                    out["SkyLight_after"] = T("obj.get_properties", instance=c, properties=["Intensity"])
    return out
