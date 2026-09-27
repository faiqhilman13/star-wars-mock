def run():
    out={}
    out["gt"]=T("scene.find_actors", name="GripTest", tag="", collision_channels=[])
    out["sab"]=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    out["bound"]=X(SQ+"get_bound_objects", binding=BODY)
    out["p"]=T("obj.get_properties", instance=ref(ACTOR), properties=["TestLoc","TestRot"])
    return out
