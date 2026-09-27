def run():
    guard()
    out={}
    acts=[a for a in T("scene.find_actors", name="", tag="", collision_channels=[]) if T("actor.get_label", actor=a)=="VerifyRig_V3"]
    if acts: a=acts[0]
    else:
        a=T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Dev/BP_GripTest", name="VerifyRig_V3", xform=xf((-1000,650,100),(0,90,0)), parent=None, snap_to_ground=False)
        T("actor.set_label", actor=a, label="VerifyRig_V3")
    T("obj.set_properties", instance=a, values=json.dumps({"TestLoc":{"x":-7,"y":2,"z":0},"TestRot":{"pitch":35,"yaw":0,"roll":180}}))
    out["a"]=a
    return out
