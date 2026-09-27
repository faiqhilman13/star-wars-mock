def run():
    out = {}
    for p in ["/Game/Jedi/Maps/Lvl_JediArena", "/Game/Jedi/Maps/Lvl_HordeArena", "/Game/Jedi/Blueprints/BP_Jedi"]:
        try:
            out[p] = {"exists": T("asset.exists", path=p), "dirty": T("asset.is_dirty", asset_path=p)}
        except Exception as e:
            out[p] = str(e)[:120]
    out["current"] = T("scene.get_current_level")
    return out
