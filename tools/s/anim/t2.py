def run():
    s=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    comps=T("actor.get_components", actor=ref(ACTOR), component_type=None)
    return {"s":s,"t":T("actor.get_actor_transform", actor=s[0]), "hw":getw("hand_r_ik_ctrl",250),"fk":getw("hand_r_fk_ctrl",250)}
