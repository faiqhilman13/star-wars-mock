def run():
    grip = {"GripLoc": {"x": -7.0, "y": 2.0, "z": 0.0}, "GripRot": {"pitch": 0.0, "yaw": 0.0, "roll": 180.0}}
    for bpp in ["/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter", "/Game/Jedi/Blueprints/BP_SithEnemy.BP_SithEnemy"]:
        T("obj.set_properties", instance=T("bp.get_default_object", blueprint=ref(bpp)), values=json.dumps(grip))
    fb = ref("/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter_C:ForceBar_GEN_VARIABLE")
    T("obj.set_properties", instance=fb, values=json.dumps({"pivot": {"x": 0.5, "y": -0.35}, "drawSize": {"x": 300, "y": 40}}))
    for bpp in ["/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter", "/Game/Jedi/Blueprints/BP_SithEnemy.BP_SithEnemy"]:
        T("bp.compile_blueprint", blueprint=ref(bpp), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_JediCharacter", "/Game/Jedi/Blueprints/BP_SithEnemy"])
    return {"pivot": T("obj.get_properties", instance=fb, properties=["pivot"])}
