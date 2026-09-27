AN = "/Game/Jedi/Anims/"
def a(n): return AN + n + "." + n
# (clip, HitStart, HitEnd, ChainTime, DamageMultiplier, Lunge) from tools/s/anim3/STAFF_READY
# (windows span every blade contact in the clip; a victim is only hit once per swing).
COMBO = [("AS_Dual_Combo1", 0.09, 0.41, 0.50, 0.9, 360),   # alternating right-left slashes
         ("AS_Dual_Combo2", 0.19, 0.31, 0.42, 1.1, 300),   # X cross-cut (wind-up flick excluded)
         ("AS_Dual_Combo3", 0.03, 0.74, 0.80, 1.3, 250),   # 720 whirlwind
         ("AS_Dual_Combo4", 0.19, 0.32, 0.42, 1.6, 460)]   # scissor finisher
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
    st = styles[1]
    st["combo"] = [{"anim": a(c), "hitStart": hs, "hitEnd": he, "chainTime": ct, "damageMultiplier": dm, "playRate": 1.0, "lunge": lu}
                   for c, hs, he, ct, dm, lu in COMBO]
    st["idleAnim"] = a("AS_Dual_Idle"); st["runAnim"] = a("AS_Dual_Run"); st["blockAnim"] = a("AS_Dual_Block")
    st["damageMultiplier"] = 1.0
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": []}))
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": styles}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    got = fix(json.loads(T("obj.get_properties", instance=cdo, properties=["Styles"]))["Styles"])
    return {"names": [s["displayName"] for s in got], "dual": [(c["anim"].split(".")[-1], c["hitStart"], c["chainTime"]) for c in got[1]["combo"]],
            "dual_anims": [got[1]["idleAnim"], got[1]["runAnim"], got[1]["blockAnim"]], "single_combo": len(got[0]["combo"])}
