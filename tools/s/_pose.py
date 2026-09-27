def run():
    out = {}
    acts = [a for a in T("scene.find_actors", name="", tag="", collision_channels=[]) if T("actor.get_label", actor=a) == "GWReview"]
    if acts:
        a = acts[0]
    else:
        a = T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Dev/BP_GripTest", name="GWReview", xform=xf((-600, 900, 100), (0, 0, 0)))
        T("actor.set_label", actor=a, label="GWReview")
    body = [c for c in T("actor.get_components", actor=a, component_type=ref("/Script/Engine.SkeletalMeshComponent")) if "Body" in c["refPath"]][0]
    T("obj.set_properties", instance=body, values=json.dumps({"skeletalMeshAsset": "/Game/Jedi/Review/GreyWarden/SKM_GreyWarden.SKM_GreyWarden",
        "animationMode": "AnimationSingleNode", "animationData": {"animToPlay": "/Game/Characters/Mannequins/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd.MF_Unarmed_Jog_Fwd", "bSavedLooping": False, "bSavedPlaying": False, "savedPosition": 0.2, "savedPlayRate": 1.0}}))
    T("obj.set_properties", instance=a, values=json.dumps({"TestLoc": {"x": -7, "y": 2, "z": 0}, "TestRot": {"pitch": 35, "yaw": 0, "roll": 180}}))
    return {"a": a}
