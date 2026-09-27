def run():
    out = {}
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        lab = T("actor.get_label", actor=a)
        if lab in ("Actor", "Actor2", "ArenaNavBounds", "PlayerStart", "DirectionalLight"):
            comps = T("actor.get_components", actor=a, component_type=ref("/Script/Engine.ActorComponent"))
            out[lab] = {"comps": [c["refPath"].split(".")[-1] for c in comps][:8], "xf": T("actor.get_actor_transform", actor=a)}
    return out
