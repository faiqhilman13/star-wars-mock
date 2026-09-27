AN = "/Game/Jedi/Anims/"
J = "/Game/Jedi/Blueprints/"
def a(n): return AN + n + "." + n
# (clip, HitStart, HitEnd, ChainTime, DamageMultiplier, PlayRate, Lunge) -- from the V2 authoring report,
# contact windows widened by ~1 frame each side.
COMBO = [
    ("AS_Saber_Combo1_V2", 0.20, 0.33, 0.42, 1.0, 1.0, 380),   # forehand diagonal
    ("AS_Saber_Combo2_V2", 0.20, 0.33, 0.42, 1.0, 1.0, 320),   # rising backhand
    ("AS_Saber_Combo3_V2", 0.15, 0.40, 0.46, 1.2, 1.0, 260),   # 360 spin, flat
    ("AS_Saber_Combo4_V2", 0.20, 0.36, 0.42, 1.5, 1.0, 480),   # hop + overhead cleave
    ("AS_Saber_Combo5_V2", 0.10, 0.52, 0.76, 2.0, 1.0, 420),   # double-spin whirlwind finisher
]
def run():
    out = {}
    bp = ref(J + "BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    combo = [{"Anim": a(c), "HitStart": hs, "HitEnd": he, "ChainTime": ct, "DamageMultiplier": dm, "PlayRate": pr, "Lunge": lu}
             for c, hs, he, ct, dm, pr, lu in COMBO]
    T("obj.set_properties", instance=cdo, values=json.dumps({"Combo": []}))
    T("obj.set_properties", instance=cdo, values=json.dumps({
        "Combo": combo,
        "BlockAnim": a("AS_Saber_Block_V2"),
        "StanceIdleAnim": a("AS_Saber_Idle_V2"),
        "StanceRunAnim": a("AS_Saber_Run_V2"),
        "StanceRunReferenceSpeed": 410.0,
        "WalkSpeed": 600.0,
        "TrailMaterial": "/Game/Jedi/Materials/M_SaberTrail.M_SaberTrail"}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[J + "BP_Jedi"])
    out["check"] = T("obj.get_properties", instance=cdo, properties=["BlockAnim", "StanceIdleAnim", "StanceRunAnim", "WalkSpeed",
        "TrailMaterial", "HumIdleVolume", "HitVolume"])
    out["combo_n"] = len(json.loads(T("obj.get_properties", instance=cdo, properties=["Combo"]))["Combo"])
    return out
