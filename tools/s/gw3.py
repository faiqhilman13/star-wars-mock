D = "/Game/Jedi/Review/GreyWarden_v3"
def tex(role, p): return "%s/Textures/T_GreyWarden_%s_%s.T_GreyWarden_%s_%s" % (D, role, p, role, p)
def run():
    out = {}
    T("asset.save_assets", asset_paths=T("asset.find_assets", folder_path=D + "/Textures", name="", recursive=True))
    if not T("asset.exists", path=D + "/SKM_GreyWarden"):
        T("skm.import_file", folder_path=D, asset_name="SKM_GreyWarden",
          source_file="C:/Users/User/PROJECTS/jedi-arena/collab/incoming/grey_warden_v3/SKM_GreyWarden.fbx",
          skeleton=ref("/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin"),
          import_materials=False, import_textures=False, import_animations=False, create_physics_asset=False)
    mesh = ref(D + "/SKM_GreyWarden.SKM_GreyWarden")
    out["bounds"] = T("skm.get_bounds", mesh=mesh)
    out["verts"] = T("skm.get_vertex_count", mesh=mesh, lod_index=0)
    out["slots"] = T("skm.get_material_slots", mesh=mesh)
    parent = ref("/Game/Jedi/Review/GreyWarden/M_GreyWarden.M_GreyWarden")
    for role in ["Cloth", "Armor", "Leather", "Visor"]:
        n = "MI_GreyWardenV3_" + role
        if not T("asset.exists", path=D + "/" + n):
            mi = T("mi.create", folder_path=D, asset_name=n, parent=parent)
        else:
            mi = ref(D + "/" + n + "." + n)
        for p in ["BaseColor", "Normal", "ORM"]:
            T("mi.set_texture_parameter", instance=mi, name=p, value=ref(tex(role, p)))
        T("skm.set_material", mesh=mesh, slot_name="M_GreyWarden_%s_Game" % role, material=mi)
    T("skm.assign_physics_asset", mesh=mesh, physics_asset=ref("/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"))
    T("asset.save_assets", asset_paths=[D + "/SKM_GreyWarden"] + [D + "/MI_GreyWardenV3_" + r for r in ["Cloth", "Armor", "Leather", "Visor"]])
    # review pawn -> v3
    cdo = T("bp.get_default_object", blueprint=ref("/Game/Jedi/Review/BP_JediReview.BP_JediReview"))
    mc = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.SkeletalMeshComponent"))[0]
    T("obj.set_properties", instance=mc, values=json.dumps({"skeletalMeshAsset": D + "/SKM_GreyWarden.SKM_GreyWarden"}))
    T("bp.compile_blueprint", blueprint=ref("/Game/Jedi/Review/BP_JediReview.BP_JediReview"), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Review/BP_JediReview"])
    return out
