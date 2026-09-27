def run():
    T("obj.set_properties", instance=ref("/Game/Jedi/Audio/Jet/SW_Jetpack_Loop.SW_Jetpack_Loop"), values=json.dumps({"bLooping": True}))
    paths = []
    for f in ("/Game/Jedi/Audio/Jet", "/Game/Jedi/Audio/Deaths"):
        paths += [x.split(".")[0] for x in T("asset.find_assets", folder_path=f, name="", recursive=True)]
    T("asset.save_assets", asset_paths=paths)
    return {"n": len(paths), "loop": T("obj.get_properties", instance=ref("/Game/Jedi/Audio/Jet/SW_Jetpack_Loop.SW_Jetpack_Loop"), properties=["bLooping"])}
