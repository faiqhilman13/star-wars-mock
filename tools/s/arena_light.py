def run():
    for a in T("scene.find_actors", name="", tag="", collision_channels=[]):
        if T("actor.get_label", actor=a) == "Colosseum":
            T("obj.set_properties", instance=a, values=json.dumps({"PylonIntensity": 60.0, "BrazierIntensity": 160.0}))
            return {"now": T("obj.get_properties", instance=a, properties=["PylonIntensity", "BrazierIntensity"])}
    return {}
