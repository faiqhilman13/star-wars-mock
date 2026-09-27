# Run after the C++ rebuild that adds HitSoundVariants / ClashSoundVariants.
L = "/Game/Jedi/Audio/Licensed/"
def s(n): return L + n + "." + n
def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    T("obj.set_properties", instance=cdo, values=json.dumps({
        "HitSoundVariants": [s("SW_Saber_Hit_Rec%d" % i) for i in range(1, 4)],
        "ClashSoundVariants": [s("SW_Saber_Clash_Rec%d" % i) for i in range(1, 5)]}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    return {"v": T("obj.get_properties", instance=cdo, properties=["HitSoundVariants", "ClashSoundVariants"])}
