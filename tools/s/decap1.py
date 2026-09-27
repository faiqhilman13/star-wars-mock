def run():
    cdo = T("bp.get_default_object", blueprint=ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi"))
    T("obj.set_properties", instance=cdo, values=json.dumps({"DecapChance": 1.0}))
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    return {"v": T("obj.get_properties", instance=cdo, properties=["DecapChance"])}
