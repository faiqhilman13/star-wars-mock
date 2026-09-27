def run():
    out={}
    X(SQ+"set_section_range", section=ref(SEC), start_frame=0, end_frame=1001)
    trk=X(SQ+"add_track_to_binding", binding=BODY, track_type=ref("/Script/MovieSceneTracks.MovieSceneSkeletalAnimationTrack"))
    out["trk"]=trk
    sec=X(SQ+"add_section", track=trk)
    out["sec"]=sec
    X(SQ+"set_section_animation", section=sec, anim_sequence_path="/Game/Jedi/Anims/AS_Saber_Swing3")
    X(SQ+"set_section_range", section=sec, start_frame=2000, end_frame=2027)
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=2100)
    return out
