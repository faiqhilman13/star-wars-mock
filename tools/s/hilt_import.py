def run():
    out = {}
    for n in ["SM_SaberHilt", "M_Hilt_Metal", "M_Hilt_Dark", "M_Hilt_Accent"]:
        if T("asset.exists", path="/Game/Jedi/Meshes/" + n): T("asset.delete", path="/Game/Jedi/Meshes/" + n)
    T("sm.import_file", folder_path="/Game/Jedi/Meshes", asset_name="SM_SaberHilt",
        source_file="C:/Users/User/PROJECTS/jedi-arena/art/SM_SaberHilt.fbx", import_materials=True, import_textures=False, combine_meshes=True)
    mesh = ref("/Game/Jedi/Meshes/SM_SaberHilt.SM_SaberHilt")
    out["bounds"] = T("sm.get_bounds", mesh=mesh)
    out["tris"] = T("sm.get_triangle_count", mesh=mesh, lod_index=0)
    out["slots"] = T("sm.get_material_slots", mesh=mesh)
    T("sm.set_nanite_enabled", mesh=mesh, enabled=False)
    hilt = ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C:Hilt_GEN_VARIABLE")
    T("obj.set_properties", instance=hilt, values=json.dumps({"staticMesh": "/Game/Jedi/Meshes/SM_SaberHilt.SM_SaberHilt",
        "relativeLocation": {"x": 0, "y": 0, "z": 0}, "relativeScale3D": {"x": 1, "y": 1, "z": 1}, "overrideMaterials": []}))
    T("bp.compile_blueprint", blueprint=ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber"), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Meshes/SM_SaberHilt", "/Game/Jedi/Meshes/M_Hilt_Metal", "/Game/Jedi/Meshes/M_Hilt_Dark", "/Game/Jedi/Meshes/M_Hilt_Accent", "/Game/Jedi/Blueprints/BP_Lightsaber"])
    return out
