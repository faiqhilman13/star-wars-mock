def run():
    a = T("asset.find_assets", folder_path="/Game/Jedi/Audio/Deaths", name="", recursive=True)
    T("asset.save_assets", asset_paths=[x.split(".")[0] for x in a])
    return {"n": len(a), "first": a[:3]}
