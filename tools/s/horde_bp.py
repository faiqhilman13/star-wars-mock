J = "/Game/Jedi/Blueprints/"
def run():
    out = {}
    gm = ref(J + "BP_JediGameMode.BP_JediGameMode")
    gcdo = T("bp.get_default_object", blueprint=gm)
    T("obj.set_properties", instance=gcdo, values=json.dumps({"HUDClass": "/Script/JediArena.JediHUD"}))
    T("bp.compile_blueprint", blueprint=gm, warnings_as_errors=False)
    out["gm"] = T("obj.get_properties", instance=gcdo, properties=["HUDClass", "DefaultPawnClass"])
    bp = ref(J + "BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    T("obj.set_properties", instance=cdo, values=json.dumps({
        "StormAction": "/Game/Jedi/Input/IA_ForceStorm.IA_ForceStorm",
        "StormAnim": "/Game/Jedi/Anims/AS_Saber_Combo5_V2.AS_Saber_Combo5_V2",
        "MaxHP": 20.0}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    out["jedi"] = T("obj.get_properties", instance=cdo, properties=["StormAction", "StormAnim", "MaxHP"])
    T("asset.save_assets", asset_paths=[J + "BP_JediGameMode", J + "BP_Jedi", "/Game/Jedi/Materials/M_ArenaSurface", "/Game/Jedi/Input/IA_ForceStorm", "/Game/Variant_Combat/Input/IMC_Combat"])
    out["level_dirty"] = T("asset.is_dirty", asset_path="/Game/Jedi/Maps/Lvl_HordeArena")
    return out
