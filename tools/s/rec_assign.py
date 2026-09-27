L = "/Game/Jedi/Audio/Licensed/"
J = "/Game/Jedi/Blueprints/"
def s(n): return L + n + "." + n
def run():
    jedi = ref(J + "BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=jedi)
    T("obj.set_properties", instance=cdo, values=json.dumps({"HitSound": s("SW_Saber_Hit_Rec1"), "ClashSound": s("SW_Saber_Clash_Rec1"),
        "DeflectSound": s("SW_Blaster_Deflect_Rec")}))
    T("bp.compile_blueprint", blueprint=jedi, warnings_as_errors=False)
    names = ["SW_Saber_Clash_Rec%d" % i for i in range(1, 5)] + ["SW_Saber_Hit_Rec%d" % i for i in range(1, 4)] + ["SW_Blaster_Deflect_Rec"]
    T("asset.save_assets", asset_paths=[L + n for n in names] + [J + "BP_Jedi"])
    return {"jedi": T("obj.get_properties", instance=cdo, properties=["HitSound", "ClashSound", "DeflectSound"])}
