def run():
    guard()
    out={}
    trk=LS+":MovieScene_0.MovieSceneSkeletalAnimationTrack_1"
    out["rmtrk"]=X(SQ+"remove_track", binding=BODY, track=ref(trk))
    X(SQ+"set_section_start_bounded", section=ref(SEC), bounded=False)
    X(SQ+"set_section_end_bounded", section=ref(SEC), bounded=False)
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=1100)
    out["tracks"]=X(SQ+"get_tracks_on_binding", binding=BODY)
    names=["AS_Saber_Idle_V2","AS_Saber_Run_V2","AS_Saber_Combo1_V2","AS_Saber_Combo2_V2","AS_Saber_Combo3_V2","AS_Saber_Combo4_V2","AS_Saber_Combo5_V2","AS_Saber_Block_V2"]
    paths=["/Game/Jedi/Anims/"+n for n in names]+["/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2"]
    out["save"]=T("asset.save_assets", asset_paths=paths)
    out["dirty"]={p:T("asset.is_dirty", asset_path=p) for p in paths}
    out["close"]=X(SQ+"close_sequence")
    out["rm"]=T("scene.remove_from_scene", actor=ref(ACTOR))
    out["left"]=T("scene.find_actors", name="GripTest", tag="", collision_channels=[])
    out["animrig"]=T("scene.find_actors", name="AnimRig", tag="", collision_channels=[])
    out["sab"]=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    out["map_dirty"]=T("asset.is_dirty", asset_path="/Game/Jedi/Maps/Lvl_JediArena")
    return out
