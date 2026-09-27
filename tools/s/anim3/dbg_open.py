def run():
    acts = T("scene.find_actors", name="", tag="", collision_channels=[])
    names = [(a["refPath"] if isinstance(a, dict) else str(a)).split(".")[-1] for a in acts]
    return {"n": len(names), "some": [x for x in names if "StaticMesh" not in x and "PointLight" not in x]}
