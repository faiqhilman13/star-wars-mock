AN = "/Game/Jedi/Anims/"
def a(n): return AN + n + "." + n
# (clip, HitStart, HitEnd, ChainTime, DamageMultiplier, Lunge) from tools/s/anim3/STAFF_READY
# (windows span every blade contact in the clip; a victim is only hit once per swing).
COMBO = [("AS_Staff_Combo1", 0.12, 0.54, 0.62, 1.0, 300),   # figure-8 twirl strikes
         ("AS_Staff_Combo2", 0.09, 0.74, 0.80, 1.1, 280),   # rising 360 spin
         ("AS_Staff_Combo3", 0.03, 0.64, 0.72, 1.3, 420),   # overhead windmill -> chop -> lunge
         ("AS_Staff_Combo4", 0.09, 0.44, 0.60, 1.6, 380)]   # horizontal 360 finisher
def fix(v):
    if isinstance(v, dict) and "refPath" in v: return v["refPath"]
    if isinstance(v, dict): return {k: fix(x) for k, x in v.items()}
    if isinstance(v, list): return [fix(x) for x in v]
    return v
def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    for c, *_ in COMBO:
        assert T("asset.exists", path=AN + c), c
    styles = fix(json.loads(T("obj.get_properties", instance=cdo, properties=["Styles"]))["Styles"])
    st = styles[2]
    st["combo"] = [{"anim": a(c), "hitStart": hs, "hitEnd": he, "chainTime": ct, "damageMultiplier": dm, "playRate": 1.0, "lunge": lu}
                   for c, hs, he, ct, dm, lu in COMBO]
    st["idleAnim"] = a("AS_Staff_Idle"); st["runAnim"] = a("AS_Staff_Run"); st["blockAnim"] = a("AS_Staff_Block")
    st["damageMultiplier"] = 1.0
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": []}))
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": styles}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    got = fix(json.loads(T("obj.get_properties", instance=cdo, properties=["Styles"]))["Styles"])
    return {"names": [s["displayName"] for s in got], "staff": [(c["anim"].split(".")[-1], c["hitStart"], c["chainTime"]) for c in got[2]["combo"]],
            "staff_anims": [got[2]["idleAnim"], got[2]["runAnim"], got[2]["blockAnim"]], "single_combo": len(got[0]["combo"])}
