PT = "PhysicsToolsets.PhysicsAssetToolset."
D = "/Game/Jedi/Review/GreyWarden_v4"
def P(t, **k):
    r = execute_tool(PT + t, json.dumps(k))
    try: return r["returnValue"]
    except Exception: return r
def run():
    out = {}
    pa = ref(D + "/SKM_GreyWarden_PhysicsAsset.SKM_GreyWarden_PhysicsAsset")
    for b in P("GetBodyNames", physicsAsset=pa):
        if b.startswith("cape_"):
            P("RemoveBody", physicsAsset=pa, boneName=b)
    mesh = ref(D + "/SKM_GreyWarden.SKM_GreyWarden")
    have = P("GetBodyNames", physicsAsset=pa)
    radii = [11.0, 10.0, 9.0, 8.0, 7.0]
    for side in ["l", "c", "r"]:
        for i in range(1, 6):
            b = "cape_%s_%02d" % (side, i)
            if b not in have:
                P("AddBody", physicsAsset=pa, boneName=b)
            P("SetSphere", physicsAsset=pa, boneName=b, shapeName="S", center={"x": 0, "y": 0, "z": 0}, radius=radii[i - 1])
            P("SetBodyPhysicsMode", physicsAsset=pa, boneName=b, mode="Simulated")
            P("SetBodyMassScale", physicsAsset=pa, boneName=b, massScale=0.25)
            parent = "spine_05" if i == 1 else "cape_%s_%02d" % (side, i - 1)
            try:
                P("AddConstraint", physicsAsset=pa, bone1Name=b, bone2Name=parent)
            except Exception as e:
                out.setdefault("c_err", []).append(b + ":" + str(e)[:80])
            first = i == 1
            P("SetConstraintLimits", physicsAsset=pa, info={"bone1Name": b, "bone2Name": parent,
                "swing1Motion": "Limited", "swing1LimitDegrees": 20.0 if first else 35.0,
                "swing2Motion": "Limited", "swing2LimitDegrees": 10.0 if first else 15.0,
                "twistMotion": "Limited", "twistLimitDegrees": 5.0})
    out["bodies"] = len(P("GetBodyNames", physicsAsset=pa))
    out["cape_c"] = [c for c in P("GetConstraints", physicsAsset=pa) if "cape_c" in c["bone1Name"]][:2]
    T("skm.assign_physics_asset", mesh=mesh, physics_asset=pa)
    # Grey Warden becomes the default player mesh
    cdo = T("bp.get_default_object", blueprint=ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi"))
    mc = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.SkeletalMeshComponent"))[0]
    T("obj.set_properties", instance=mc, values=json.dumps({"skeletalMeshAsset": D + "/SKM_GreyWarden.SKM_GreyWarden"}))
    T("bp.compile_blueprint", blueprint=ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi"), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[D + "/SKM_GreyWarden_PhysicsAsset", D + "/SKM_GreyWarden", "/Game/Jedi/Blueprints/BP_Jedi"])
    out["mesh"] = T("obj.get_properties", instance=mc, properties=["skeletalMeshAsset"])
    return out
