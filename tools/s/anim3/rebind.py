# Re-authoring setup. cleanup3.py removes the rig actors from Lvl_JediArena after a bake, so before baking again:
#   1. open_auth.py loads Lvl_JediArena and opens LS_SaberAuthoring_V3
#   2. this script adds a fresh BP_GripTest rig and rebinds the sequence's "AnimRig_V3" binding to it
#   3. put the new actor path it prints into ACTOR in lib3.py (staffprev.py swaps the preview prop to the saberstaff)
#   4. EXTRA="clips_staff.py clips_staff2.py" python driver3.py s_c1 ...  then exp3.py / anl3.py / contacts2.py
# Close the editor without saving the level afterwards (or remove the rig) so the training arena stays clean.
def run():
    out = {}
    guard()
    a = T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Dev/BP_GripTest", name="AnimRig_V3", xform=xf((-1000, 400, 100), (0, 90, 0)), parent=None, snap_to_ground=False)
    T("actor.set_label", actor=a, label="AnimRig_V3")
    T("obj.set_properties", instance=a, values=json.dumps({"TestLoc": {"x": -7, "y": 2, "z": 0}, "TestRot": {"pitch": 35, "yaw": 0, "roll": 180}}))
    ap = a["refPath"] if isinstance(a, dict) else str(a)
    out["actor"] = ap
    body = ref(ap + ".Body")
    T("obj.set_properties", instance=body, values=json.dumps({"skeletalMeshAsset": "/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden.SKM_GreyWarden"}))
    rig = {"bindingId": "9FA787AC-44A7-EBA8-9DB0-CD9BBC973698", "sequence": ref(LS)}
    out["replace"] = X(SQ + "replace_binding_with_actors", actors=[ref(ap)], binding=rig)
    out["bound"] = str(X(SQ + "get_bound_objects", binding=rig) if False else "")
    show(2300)
    out["w"] = getw("upperarm_r_fk_ctrl", 2300)["location"]
    return out
