def run():
    out = {}
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        lab = T("actor.get_label", actor=a)
        if lab in ("Colosseum", "HordeDirector", "PlayerStart", "ArenaNavBounds"):
            out[lab] = T("actor.get_actor_transform", actor=a)["location"]
    out["n"] = len(T("scene.find_actors", name="", tag="", collision_channels=[]))
    return out
