def run():
    pa = ref("/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden_PhysicsAsset.SKM_GreyWarden_PhysicsAsset")
    setups = json.loads(T("obj.get_properties", instance=pa, properties=["SkeletalBodySetups"]))["SkeletalBodySetups"]
    out = {"n": len(setups)}
    first = True
    for s in setups:
        bs = ref(s["refPath"] if isinstance(s, dict) else s)
        name = json.loads(T("obj.get_properties", instance=bs, properties=["BoneName"]))["BoneName"]
        if first:
            out["props"] = [k for k in json.loads(T("obj.list_properties", instance=bs)).keys() if "ollision" in k or "physics" in k.lower()]
            first = False
        if str(name).startswith("cape_"):
            T("obj.set_properties", instance=bs, values=json.dumps({"CollisionReponse": "BodyCollision_Disabled"}))
            out.setdefault("set", []).append(name)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden_PhysicsAsset"])
    return out
