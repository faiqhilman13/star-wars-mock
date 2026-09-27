def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber")
    cdo = T("bp.get_default_object", blueprint=bp)
    comps = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.SceneComponent"))
    out = {"comps": []}
    for c in comps:
        info = {"c": c}
        try:
            info["p"] = T("obj.get_properties", instance=c, properties=["relativeLocation", "relativeRotation", "relativeScale3D"])
        except Exception as e:
            pass
        out["comps"].append(info)
    out["graphs"] = T("bp.list_graphs", blueprint=bp) if True else None
    return out
