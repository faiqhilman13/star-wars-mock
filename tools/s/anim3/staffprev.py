def run():
    guard()
    sab = ref(ACTOR + ".Saber")
    T("obj.set_properties", instance=sab, values=json.dumps({"childActorClass": "/Game/Jedi/Blueprints/BP_Saberstaff.BP_Saberstaff_C"}))
    show(2000)
    return {"saber": T("obj.get_properties", instance=sab, properties=["childActorClass", "childActor"])}
