def run():
    return {"v2": [a for a in T("asset.find_assets", folder_path="/Game/Jedi/Anims", name="", recursive=True) if "V2" in a]}
