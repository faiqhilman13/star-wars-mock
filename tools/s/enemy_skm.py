def run():
    out = {}
    paths = []
    for m in ["Clanker", "Bulwark", "JetGhost", "Warden"]:
        p = "/Game/Jedi/Enemies/%s/SKM_%s" % (m, m)
        sk = ref(p + ".SKM_" + m)
        info = {}
        try:
            info["bounds"] = "skip"
        except Exception as e:
            info["bounds_err"] = str(e)[:120]
        try:
            T("obj.set_properties", instance=sk, values=json.dumps({"PhysicsAsset": "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"}))
            info["pa"] = T("obj.get_properties", instance=sk, properties=["PhysicsAsset"])
        except Exception as e:
            info["pa_err"] = str(e)[:160]
        out[m] = info
        paths.append(p)
    # anything else the importer created (materials / auto physics assets) in those folders
    extra = []
    for m in ["Clanker", "Bulwark", "JetGhost", "Warden"]:
        extra += T("asset.find_assets", folder_path="/Game/Jedi/Enemies/" + m, name="", recursive=True)
    out["assets"] = extra
    T("asset.save_assets", asset_paths=[a.split(".")[0] for a in extra])
    return out
