L = "/Game/Jedi/Audio/Licensed/"
J = "/Game/Jedi/Blueprints/"
def s(n): return L + n + "." + n
def run():
    out = {"l": T("logs.GetLogEntries", category="", pattern="jedi.ImportSounds: SW_", maxEntries=4)}
    T("obj.set_properties", instance=ref(s("SW_Saber_Hum_Loop")), values=json.dumps({"volume": 0.4}))
    jedi = ref(J + "BP_Jedi.BP_Jedi")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=jedi), values=json.dumps({
        "HitSound": s("SW_Saber_HitBody"), "DeflectSound": s("SW_Blaster_Deflect_Wire")}))
    T("bp.compile_blueprint", blueprint=jedi, warnings_as_errors=False)
    bolt = ref(J + "BP_BlasterBolt.BP_BlasterBolt")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=bolt), values=json.dumps({"ImpactSound": s("SW_Saber_HitBody")}))
    T("bp.compile_blueprint", blueprint=bolt, warnings_as_errors=False)
    remote = ref(J + "BP_TrainingRemote.BP_TrainingRemote")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=remote), values=json.dumps({"FireSound": s("SW_Blaster_Fire_Wire")}))
    T("bp.compile_blueprint", blueprint=remote, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[L + n for n in ["SW_Saber_Hum_Loop", "SW_Saber_HitBody", "SW_Blaster_Fire_Wire", "SW_Blaster_Deflect_Wire",
        "SW_Blaster_Fire", "SW_Blaster_Deflect", "SW_Remote_Explode"]] + [J + "BP_Jedi", J + "BP_BlasterBolt", J + "BP_TrainingRemote"])
    out["jedi"] = T("obj.get_properties", instance=T("bp.get_default_object", blueprint=jedi), properties=["HitSound", "DeflectSound"])
    out["remote"] = T("obj.get_properties", instance=T("bp.get_default_object", blueprint=remote), properties=["FireSound", "ExplodeSound"])
    out["hum"] = T("obj.get_properties", instance=ref(s("SW_Saber_Hum_Loop")), properties=["volume", "bLooping"])
    return out
