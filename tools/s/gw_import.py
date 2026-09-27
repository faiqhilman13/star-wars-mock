D = "/Game/Jedi/Review/GreyWarden"
def run():
    out = {}
    tex = T("asset.find_assets", folder_path=D + "/Textures", name="", recursive=True)
    T("asset.save_assets", asset_paths=tex)
    out["tex"] = len(tex)
    out["normal_srgb"] = T("obj.get_properties", instance=ref(D + "/Textures/T_GreyWarden_Armor_Normal.T_GreyWarden_Armor_Normal"), properties=["SRGB", "CompressionSettings"])
    if not T("asset.exists", path=D + "/SKM_GreyWarden"):
        out["imp"] = T("skm.import_file", folder_path=D, asset_name="SKM_GreyWarden",
            source_file="C:/Users/User/PROJECTS/jedi-arena/collab/incoming/grey_warden_rigcheck_v2/SKM_GreyWarden.fbx",
            skeleton=ref("/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin"),
            import_materials=False, import_textures=False, import_animations=False, create_physics_asset=False)
    mesh = ref(D + "/SKM_GreyWarden.SKM_GreyWarden")
    out["skeleton"] = T("skm.get_skeleton", mesh=mesh)
    out["bounds"] = T("skm.get_bounds", mesh=mesh)
    bones = T("skm.get_bone_names", mesh=mesh)
    out["bones"] = len(bones)
    out["cape"] = [b for b in bones if b.startswith("cape")]
    out["slots"] = T("skm.get_material_slots", mesh=mesh)
    out["verts"] = T("skm.get_vertex_count", mesh=mesh, lod_index=0)
    quinn = T("skm.get_bone_names", mesh=ref("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple"))
    out["missing_quinn_bones"] = [b for b in quinn if b not in bones]
    out["pa_quinn"] = T("skm.get_physics_asset", mesh=ref("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple"))
    return out
