L = "/Game/Jedi/Audio/Licensed/"
J = "/Game/Jedi/Blueprints/"
def s(n): return L + n + "." + n
def run():
    jedi = ref(J + "BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=jedi)
    T("obj.set_properties", instance=cdo, values=json.dumps({"HitSound": s("SW_Saber_HitBody_V2"), "ClashSound": s("SW_Saber_Clash_V2")}))
    T("bp.compile_blueprint", blueprint=jedi, warnings_as_errors=False)
    bolt = ref(J + "BP_BlasterBolt.BP_BlasterBolt")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=bolt), values=json.dumps({"ImpactSound": s("SW_Saber_HitBody_V2")}))
    T("bp.compile_blueprint", blueprint=bolt, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[L + "SW_Saber_HitBody_V2", L + "SW_Saber_Clash_V2", J + "BP_Jedi", J + "BP_BlasterBolt"])
    return {"jedi": T("obj.get_properties", instance=cdo, properties=["HitSound", "ClashSound"])}
