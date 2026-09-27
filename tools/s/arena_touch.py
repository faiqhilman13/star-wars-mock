def run():
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        if T("actor.get_label", actor=a) == "Colosseum":
            r = json.loads(T("obj.get_properties", instance=a, properties=["ArenaRadius"]))
            T("obj.set_properties", instance=a, values=json.dumps({"ArenaRadius": r["ArenaRadius"] + 1.0}))
            T("obj.set_properties", instance=a, values=json.dumps({"ArenaRadius": r["ArenaRadius"]}))
            return {"radius": r}
    return {"err": "no colosseum"}
