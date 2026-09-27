def run():
    out={}
    trk="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring.LS_SaberAuthoring:MovieScene_0.MovieSceneSkeletalAnimationTrack_1"
    out["rmtrk"]=X(SQ+"remove_track", binding=BODY, track=ref(trk))
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=1000)
    out["save"]=T("asset.save_assets", asset_paths=["/Game/Jedi/Anims/AS_Saber_Swing1","/Game/Jedi/Anims/AS_Saber_Swing2","/Game/Jedi/Anims/AS_Saber_Swing3","/Game/Jedi/Anims/AS_Saber_Block","/Game/Jedi/Anims/AS_Saber_Parry","/Game/Jedi/Anims/AS_Force_Dash","/Game/Jedi/Anims/AS_Jump_Flip","/Game/Jedi/Anims/Authoring/LS_SaberAuthoring"])
    out["close"]=X(SQ+"close_sequence")
    out["rm"]=T("scene.remove_from_scene", actor=ref(ACTOR))
    out["left"]=T("scene.find_actors", name="GripTest", tag="", collision_channels=[])
    out["sab"]=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    return out
