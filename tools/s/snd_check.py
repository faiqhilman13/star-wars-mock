def run():
    L = "/Game/Jedi/Audio/Licensed/"
    T("asset.save_assets", asset_paths=[L + "SW_Blaster_Fire", L + "SW_Blaster_Deflect", L + "SW_Remote_Explode"])
    rc = T("bp.get_default_object", blueprint=ref("/Game/Jedi/Blueprints/BP_TrainingRemote.BP_TrainingRemote"))
    return {"l": T("logs.GetLogEntries", category="", pattern="jedi.ImportSounds: SW_(Blaster|Remote)", maxEntries=3),
            "dur": T("obj.get_properties", instance=ref(L + "SW_Blaster_Fire.SW_Blaster_Fire"), properties=["duration"]),
            "remote": T("obj.get_properties", instance=rc, properties=["FireSound", "ExplodeSound"])}
