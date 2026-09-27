PT = "PhysicsToolsets.PhysicsAssetToolset."
def P(t, **k):
    r = execute_tool(PT + t, json.dumps(k))
    try: return r["returnValue"]
    except Exception: return r
def run():
    pa = ref("/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden_PhysicsAsset.SKM_GreyWarden_PhysicsAsset")
    cons = P("GetConstraints", physicsAsset=pa)
    return {"cape": [c for c in cons if c["bone1Name"] in ("cape_c_01", "cape_c_02")],
            "ref": [c for c in cons if c["bone1Name"] in ("head", "lowerarm_l")]}
