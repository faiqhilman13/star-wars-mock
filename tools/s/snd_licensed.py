L = "/Game/Jedi/Audio/Licensed/"
A = "/Game/Jedi/Audio/"
J = "/Game/Jedi/Blueprints/"
def s(n): return L + n + "." + n
def run():
    out = {}
    names = ["SW_Blaster_Deflect", "SW_Blaster_Fire", "SW_Remote_Explode", "SW_Saber_Clash", "SW_Saber_Hit", "SW_Saber_Hum_Loop",
             "SW_Saber_Ignite", "SW_Saber_Retract"] + ["SW_Saber_Swing%d" % i for i in range(1, 6)]
    # Keep saber layers from overpowering; the hum is modulated in code.
    for n in names:
        if "Swing" in n:
            T("obj.set_properties", instance=ref(s(n)), values=json.dumps({"volume": 0.8}))
    T("obj.set_properties", instance=ref(s("SW_Saber_Hum_Loop")), values=json.dumps({"volume": 0.7}))
    T("asset.save_assets", asset_paths=[L + n for n in names])

    jedi = ref(J + "BP_Jedi.BP_Jedi")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=jedi), values=json.dumps({"SwingSounds": []}))
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=jedi), values=json.dumps({
        "HumSound": s("SW_Saber_Hum_Loop"), "IgniteSound": s("SW_Saber_Ignite"), "RetractSound": s("SW_Saber_Retract"),
        "SwingSounds": [s("SW_Saber_Swing%d" % i) for i in range(1, 6)],
        "HitSound": s("SW_Saber_Hit"), "ClashSound": s("SW_Saber_Clash"), "DeflectSound": s("SW_Blaster_Deflect")}))
    T("bp.compile_blueprint", blueprint=jedi, warnings_as_errors=False)
    out["jedi"] = T("obj.get_properties", instance=T("bp.get_default_object", blueprint=jedi), properties=["HumSound", "SwingSounds", "DeflectSound"])

    bolt = ref(J + "BP_BlasterBolt.BP_BlasterBolt")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=bolt), values=json.dumps({"ImpactSound": s("SW_Saber_Hit")}))
    T("bp.compile_blueprint", blueprint=bolt, warnings_as_errors=False)

    remote = ref(J + "BP_TrainingRemote.BP_TrainingRemote")
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=remote), values=json.dumps({
        "FireSound": s("SW_Blaster_Fire"), "ExplodeSound": s("SW_Remote_Explode")}))
    T("bp.compile_blueprint", blueprint=remote, warnings_as_errors=False)

    red = ref(J + "BP_LightsaberRed.BP_LightsaberRed")
    comps = T("actor.get_components", actor=T("bp.get_default_object", blueprint=red), component_type=ref("/Script/Engine.AudioComponent"))
    for c in comps:
        T("obj.set_properties", instance=c, values=json.dumps({"sound": s("SW_Saber_Hum_Loop")}))
    out["red"] = [T("obj.get_properties", instance=c, properties=["sound"]) for c in comps]
    T("bp.compile_blueprint", blueprint=red, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[J + "BP_Jedi", J + "BP_BlasterBolt", J + "BP_TrainingRemote", J + "BP_LightsaberRed"])
    return out
