def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Saberstaff.BP_Saberstaff")
    cdo = T("bp.get_default_object", blueprint=bp)
    comps = {c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", ""): c for c in T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.PrimitiveComponent"))}
    good = json.loads(T("obj.get_properties", instance=comps["BladeCore2"], properties=["bodyInstance"]))["bodyInstance"]
    T("obj.set_properties", instance=comps["Hilt2"], values=json.dumps({"bodyInstance": good, "castShadow": True}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Saberstaff"])
    b = json.loads(T("obj.get_properties", instance=comps["Hilt2"], properties=["bodyInstance"]))["bodyInstance"]
    return {"hilt2": (b.get("collisionEnabled"), b.get("collisionProfileName"))}
