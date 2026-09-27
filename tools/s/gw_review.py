J = "/Game/Jedi/Blueprints/"
def run():
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        try:
            if T("actor.get_label", actor=a) == "GWReview":
                T("scene.remove_from_scene", actor=a)
        except Exception:
            pass
    if not T("asset.exists", path="/Game/Jedi/Review/BP_JediReview"):
        T("bp.create", folder_path="/Game/Jedi/Review", asset_name="BP_JediReview", asset_type=ref(J + "BP_Jedi.BP_Jedi_C"))
    bp = ref("/Game/Jedi/Review/BP_JediReview.BP_JediReview")
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    cdo = T("bp.get_default_object", blueprint=bp)
    mesh = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.SkeletalMeshComponent"))[0]
    T("obj.set_properties", instance=mesh, values=json.dumps({"skeletalMeshAsset": "/Game/Jedi/Review/GreyWarden/SKM_GreyWarden.SKM_GreyWarden"}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Review/BP_JediReview"])
    gm = T("bp.get_default_object", blueprint=ref(J + "BP_JediGameMode.BP_JediGameMode"))
    T("obj.set_properties", instance=gm, values=json.dumps({"DefaultPawnClass": "/Game/Jedi/Review/BP_JediReview.BP_JediReview_C"}))
    return {"mesh": T("obj.get_properties", instance=mesh, properties=["skeletalMeshAsset", "animClass"])}
