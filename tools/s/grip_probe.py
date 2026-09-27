def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    return {"g": T("obj.get_properties", instance=cdo, properties=["GripLoc", "GripRot", "SaberSocket"])}
