def run():
    out={}
    sab=json.loads(T("obj.get_properties", instance=ref(ACTOR+".Saber"), properties=["childActor"]))["childActor"]
    out["sab"]=[c["refPath"].split(".")[-1] for c in T("actor.get_components", actor=sab, component_type=None)]
    out["rig"]=[c["refPath"].split(".")[-1] for c in T("actor.get_components", actor=ref(ACTOR), component_type=None)]
    vis=T("scene.find_actors", name="", tag="", collision_channels=[], bounds={"min":{"x":-1200,"y":200,"z":80},"max":{"x":-800,"y":600,"z":400}}) if False else None
    return out
