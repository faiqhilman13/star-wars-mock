def run():
    a = T("asset.find_assets", folder_path="/Game/Jedi/Enemies/Roller", name="", recursive=True)
    T("asset.save_assets", asset_paths=[x.split(".")[0] for x in a])
    info = {}
    for x in a:
        m = ref(x.split(".")[0] + "." + x.split(".")[0].split("/")[-1]) if False else None
    return {"n": len(a), "assets": a}
