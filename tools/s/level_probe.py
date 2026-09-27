def run():
    lvl = T("scene.get_current_level")
    acts = T("scene.find_actors", name="", tag="", collision_channels=[])
    res = []
    for a in acts:
        try: lab = T("actor.get_label", actor=a)
        except Exception: lab = "?"
        res.append((lab, T("obj.get_class", instance=a)["refPath"].split(".")[-1], a["refPath"]))
    return {"lvl": lvl, "n": len(acts), "actors": res}
