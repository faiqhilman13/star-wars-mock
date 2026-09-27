DST = "/Game/Jedi/Maps/Lvl_HordeArena"
def run():
    out = {}
    T("asset.save_assets", asset_paths=[DST])
    out["dirty_after"] = T("asset.is_dirty", asset_path=DST)
    T("scene.load_level", level_path=DST)
    out["current"] = T("scene.get_current_level")
    rows = []
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        cls = T("obj.get_class", instance=a)
        cn = cls["refPath"].split(".")[-1] if isinstance(cls, dict) else str(cls)
        rows.append(T("actor.get_label", actor=a) + " | " + cn)
    out["actors"] = rows
    return out
