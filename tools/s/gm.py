def run():
    gm = T("bp.get_default_object", blueprint=ref("/Game/Jedi/Blueprints/BP_JediGameMode.BP_JediGameMode"))
    T("obj.set_properties", instance=gm, values=json.dumps({"DefaultPawnClass": "/Game/Jedi/Blueprints/PAWN.PAWN_C"}))
    return {"gm": T("obj.get_properties", instance=gm, properties=["DefaultPawnClass"])}
