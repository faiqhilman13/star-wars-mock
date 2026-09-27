def run():
    out={"p":T("obj.get_properties", instance=ref(ACTOR), properties=["TestLoc","TestRot"])}
    comps=T("actor.get_components", actor=ref(ACTOR), component_type=None)
    out["sab"]=T("obj.get_properties", instance=comps[3], properties=["RelativeLocation","RelativeRotation"])
    return out
