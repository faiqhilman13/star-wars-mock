def run():
    names = ["Jet_1", "Jet_2", "Jet_3", "Roller_1", "Roller_2", "Roller_3", "Warden_1", "Warden_2"]
    paths = ["/Game/Jedi/Audio/Deaths/SW_Death_" + n for n in names]
    out = {"save": T("asset.save_assets", asset_paths=paths)}
    out["dur"] = [round(json.loads(T("obj.get_properties", instance=ref(p + "." + p.split("/")[-1]), properties=["Duration"]))["Duration"], 2) for p in paths]
    return out
