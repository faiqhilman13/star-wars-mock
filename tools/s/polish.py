def run():
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=ref("/Game/Jedi/Blueprints/BP_ForceWave.BP_ForceWave")), values=json.dumps({"Lifetime": 0.35, "EndScale": 5.0}))
    T("bp.compile_blueprint", blueprint=ref("/Game/Jedi/Blueprints/BP_ForceWave.BP_ForceWave"), warnings_as_errors=False)
    for e in T("mat.get_expressions", material_or_function=ref("/Game/Jedi/Materials/M_ForceWave.M_ForceWave")):
        try:
            p = json.loads(T("obj.get_properties", instance=e, properties=["parameterName"]))
        except Exception:
            continue
        if p.get("parameterName") == "Intensity":
            T("obj.set_properties", instance=e, values=json.dumps({"defaultValue": 2.2}))
    T("mat.recompile", material_or_function=ref("/Game/Jedi/Materials/M_ForceWave.M_ForceWave"))
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_ForceWave", "/Game/Jedi/Materials/M_ForceWave", "/Game/Jedi/Blueprints/BP_LightningBolt", "/Game/Jedi/Maps/Lvl_JediArena"])
    return {"ok": True}
