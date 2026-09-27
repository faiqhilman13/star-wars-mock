def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    run_anim = "/Game/Jedi/Anims/AS_Saber_Run_V3.AS_Saber_Run_V3"
    assert T("asset.exists", path="/Game/Jedi/Anims/AS_Saber_Run_V3")
    styles = json.loads(T("obj.get_properties", instance=cdo, properties=["Styles"]))["Styles"]
    def fix(v):
        if isinstance(v, dict) and "refPath" in v: return v["refPath"]
        if isinstance(v, dict): return {k: fix(x) for k, x in v.items()}
        if isinstance(v, list): return [fix(x) for x in v]
        return v
    styles = fix(styles)
    for s in styles:
        s["runAnim"] = run_anim
    T("obj.set_properties", instance=cdo, values=json.dumps({"Styles": styles, "StanceRunAnim": run_anim, "StanceRunReferenceSpeed": 680.0}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    got = json.loads(T("obj.get_properties", instance=cdo, properties=["Styles", "StanceRunAnim", "StanceRunReferenceSpeed"]))
    return {"runs": [s["runAnim"] for s in got["Styles"]], "stance": got["StanceRunAnim"], "ref": got["StanceRunReferenceSpeed"],
            "combo_ok": [len(s["combo"]) for s in got["Styles"]], "off": [s["offhandSaberClass"] for s in got["Styles"]]}
