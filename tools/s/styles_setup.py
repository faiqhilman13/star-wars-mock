J = "/Game/Jedi/Blueprints/"
AN = "/Game/Jedi/Anims/"
def a(n): return AN + n + "." + n
def run():
    bp = ref(J + "BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    combo = json.loads(T("obj.get_properties", instance=cdo, properties=["Combo"]))["Combo"]
    for c in combo:  # refs come back as {"refPath": ...}
        if isinstance(c.get("Anim"), dict):
            c["Anim"] = c["Anim"]["refPath"]
    base = {"Combo": combo, "IdleAnim": a("AS_Saber_Idle_V2"), "RunAnim": a("AS_Saber_Run_V2"), "BlockAnim": a("AS_Saber_Block_V2")}
    styles = [
        dict(base, DisplayName="Single Blade", MainSaberClass=J + "BP_Lightsaber.BP_Lightsaber_C", DamageMultiplier=1.0),
        dict(base, DisplayName="Dual Wield (Jar'Kai)", MainSaberClass=J + "BP_Lightsaber.BP_Lightsaber_C",
             OffhandSaberClass=J + "BP_Lightsaber.BP_Lightsaber_C", OffhandSocket="hand_l", DamageMultiplier=0.9),
        dict(base, DisplayName="Saberstaff (Double-Bladed)", MainSaberClass=J + "BP_Saberstaff.BP_Saberstaff_C", DamageMultiplier=1.1),
    ]
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": []}))
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": styles,
        "SaberStyleAction": "/Game/Jedi/Input/IA_SaberStyle.IA_SaberStyle", "MaxLeanDegrees": 22.0}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[J + "BP_Jedi"])
    got = json.loads(T("obj.get_properties", instance=cdo, properties=["Styles", "SaberStyleAction", "MaxLeanDegrees"]))
    return {"first": json.dumps(got["Styles"][1])[:900], "n": len(got["Styles"]), "action": got["SaberStyleAction"], "lean": got["MaxLeanDegrees"]}
