def run():
    out = {}
    for p in ["/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface", "/Game/Jedi/Materials/M_ForceWave.M_ForceWave"]:
        m = ref(p)
        T("obj.set_properties", instance=m, values=json.dumps({"bUsedWithSkeletalMesh": True}))
        out[p] = T("obj.get_properties", instance=m, properties=["bUsedWithSkeletalMesh", "bUsedWithInstancedStaticMeshes"])
    T("asset.save_assets", asset_paths=["/Game/Jedi/Materials/M_ArenaSurface", "/Game/Jedi/Materials/M_ForceWave"])
    return out
