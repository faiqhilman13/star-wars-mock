D = "/Game/Jedi/Review/GreyWarden_v4"
def run():
    T("skm.import_file", folder_path=D, asset_name="SKM_GreyWarden",
      source_file="C:/Users/User/PROJECTS/jedi-arena/collab/incoming/grey_warden_v4/SKM_GreyWarden.fbx",
      skeleton=ref("/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin"),
      import_materials=False, import_textures=False, import_animations=False, create_physics_asset=False)
    mesh = ref(D + "/SKM_GreyWarden.SKM_GreyWarden")
    return {"bounds": T("skm.get_bounds", mesh=mesh)["boxExtent"], "verts": T("skm.get_vertex_count", mesh=mesh, lod_index=0),
            "v3verts": T("skm.get_vertex_count", mesh=ref("/Game/Jedi/Review/GreyWarden_v3/SKM_GreyWarden.SKM_GreyWarden"), lod_index=0)}
