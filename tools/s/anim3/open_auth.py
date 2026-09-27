def run():
    out = {}
    if T("app.IsPIERunning"): return {"err": "PIE"}
    out["load"] = T("scene.load_level", level_path="/Game/Jedi/Maps/Lvl_JediArena")
    out["open"] = X(SQ + "open_sequence", sequence=ref(LS))
    return out
