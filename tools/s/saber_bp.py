BP = "/Game/Jedi/Blueprints/BP_Lightsaber"
def run():
    if T("asset.exists", path=BP): T("asset.delete", path=BP)
    bp = T("bp.create", folder_path="/Game/Jedi/Blueprints", asset_name="BP_Lightsaber", asset_type=ref("/Script/Engine.Actor"))
    out = {"bp": bp}
    def add(cls, name):
        return T("actor.add_component", owner=bp, component_type=ref("/Script/Engine."+cls), name=name)
    root = add("SceneComponent", "SaberRoot")
    hilt = add("StaticMeshComponent", "Hilt")
    blade_root = add("SceneComponent", "BladeRoot")
    core = add("StaticMeshComponent", "BladeCore")
    glow = add("StaticMeshComponent", "BladeGlow")
    light = add("PointLightComponent", "BladeLight")
    tip = add("SceneComponent", "BladeTip")
    out["comps"] = [root, hilt, blade_root, core, glow, light, tip]
    out["core_props_sample"] = [k for k in json.loads(T("obj.list_properties", instance=core)).keys() if k.lower().startswith(("relative","static","override","cast","collision","body","mobility"))]
    return out
