def run():
    out = {}
    names = ["Jet_1", "Jet_2", "Jet_3", "Roller_1", "Roller_2", "Roller_3", "Warden_1", "Warden_2"]
    paths = ["/Game/Jedi/Audio/Deaths/SW_Death_" + n for n in names]
    out["dirty_before"] = [T("asset.is_dirty", asset_path=p) for p in paths]
    for p in paths:
        o = ref(p + "." + p.split("/")[-1])
        v = json.loads(T("obj.get_properties", instance=o, properties=["Volume"]))["Volume"]
        T("obj.set_properties", instance=o, values=json.dumps({"Volume": v}))
    out["dirty_mid"] = [T("asset.is_dirty", asset_path=p) for p in paths]
    out["save"] = T("asset.save_assets", asset_paths=paths)
    out["dur"] = [json.loads(T("obj.get_properties", instance=ref(p + "." + p.split("/")[-1]), properties=["Duration"]))["Duration"] for p in paths]
    return out
