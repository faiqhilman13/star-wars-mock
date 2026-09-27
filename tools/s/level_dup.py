def run():
    out = {}
    if not T("asset.exists", path="/Game/Jedi/Maps/Lvl_JediArena"):
        out["dup"] = T("asset.duplicate", path="/Game/ThirdPerson/Lvl_ThirdPerson", new_path="/Game/Jedi/Maps/Lvl_JediArena")
    T("asset.save_assets", asset_paths=["/Game/Jedi/Maps/Lvl_JediArena"])
    out["load"] = T("scene.load_level", level_path="/Game/Jedi/Maps/Lvl_JediArena")
    out["cur"] = T("scene.get_current_level")
    acts = T("scene.find_actors", name="", tag="", collision_channels=[])
    out["n"] = len(acts)
    removed = 0
    for a in acts:
        cls = T("obj.get_class", instance=a)["refPath"].split(".")[-1]
        lab = T("actor.get_label", actor=a)
        if cls == "StaticMeshActor" and lab not in ("Floor", "SM_SkySphere"):
            T("scene.remove_from_scene", actor=a); removed += 1
    out["removed"] = removed
    return out
