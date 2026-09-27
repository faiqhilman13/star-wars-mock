REMOVE_PREFIX = ("Pillar", "CenterSeal", "ArenaPlatform", "ArenaTrim", "Cover", "Crate", "Rubble", "Lava", "SithSpawner", "TrainingRemote", "TrainingDummy")
def run():
    out = {"removed": [], "added": []}
    assert T("scene.get_current_level") == "/Game/Jedi/Maps/Lvl_HordeArena"
    acts = T("scene.find_actors", name="", tag="", collision_channels=[])
    labels = {}
    for a in acts:
        lab = T("actor.get_label", actor=a)
        labels[lab] = a
        if lab.startswith(REMOVE_PREFIX):
            T("scene.remove_from_scene", actor=a)
            out["removed"].append(lab)
    if "Colosseum" not in labels:
        arena = T("scene.add_to_scene_from_class", actor_type=ref("/Script/JediArena.ColosseumArena"), name="Colosseum", xform=xf((0, 0, 0)))
        T("actor.set_label", actor=arena, label="Colosseum")
        out["added"].append("Colosseum")
    if "HordeDirector" not in labels:
        d = T("scene.add_to_scene_from_class", actor_type=ref("/Script/JediArena.HordeDirector"), name="HordeDirector", xform=xf((0, 0, 600)))
        T("actor.set_label", actor=d, label="HordeDirector")
        out["added"].append("HordeDirector")
    ps = labels.get("PlayerStart")
    if ps:
        T("actor.set_actor_transform", actor=ps, xform=xf((-390, 0, 170), (0, 0, 0)))
    nav = labels.get("ArenaNavBounds")
    if nav:
        T("actor.set_actor_transform", actor=nav, xform=xf((0, 0, 200), (0, 0, 0), (46, 46, 6)))
    return out
