def run():
    guard()
    X(SQ + "set_playback_range", sequence=ref(LS), start_frame=0, end_frame=6000)
    return {"save": T("asset.save_assets", asset_paths=["/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V3"])}
