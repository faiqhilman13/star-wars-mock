def run():
    hand(250, (30,15,115), (0.3,0,0.95), pv=(-20,50,100))
    show(250)
    s=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    t=T("actor.get_actor_transform", actor=s[0])
    return {"t":t}
