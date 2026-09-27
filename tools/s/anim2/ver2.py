def run():
    guard()
    out={}
    trk=LS+":MovieScene_0.MovieSceneControlRigParameterTrack_0"
    X(SQ+"set_section_range", section=ref(SEC), start_frame=0, end_frame=1100)
    t=X(SQ+"add_track_to_binding", binding=BODY, track_type=ref("/Script/MovieSceneTracks.MovieSceneSkeletalAnimationTrack"))
    out["trk"]=t
    for a,st,n in [("AS_Saber_Combo3_V2",1200,18),("AS_Saber_Combo5_V2",1300,28),("AS_Saber_Run_V2",1400,20)]:
        s=X(SQ+"add_section", track=t)
        X(SQ+"set_section_animation", section=s, anim_sequence_path="/Game/Jedi/Anims/"+a)
        X(SQ+"set_section_range", section=s, start_frame=st, end_frame=st+n)
        out[a]=s
    return out
