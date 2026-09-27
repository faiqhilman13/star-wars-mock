def run():
    J = "/Game/Jedi/Blueprints/"
    j = T("bp.get_default_object", blueprint=ref(J + "BP_Jedi.BP_Jedi"))
    r = T("bp.get_default_object", blueprint=ref(J + "BP_TrainingRemote.BP_TrainingRemote"))
    b = T("bp.get_default_object", blueprint=ref(J + "BP_BlasterBolt.BP_BlasterBolt"))
    return {"jedi": T("obj.get_properties", instance=j, properties=["HitSound", "DeflectSound", "HumSound"]),
            "remote": T("obj.get_properties", instance=r, properties=["FireSound"]),
            "bolt": T("obj.get_properties", instance=b, properties=["ImpactSound"]),
            "hum": T("obj.get_properties", instance=ref("/Game/Jedi/Audio/Licensed/SW_Saber_Hum_Loop.SW_Saber_Hum_Loop"), properties=["volume"])}
