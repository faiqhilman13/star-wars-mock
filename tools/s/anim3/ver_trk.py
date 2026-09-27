VB={"bindingId":"B9B46C94-4DCD-E389-2C7D-F5B1D0978FB2","sequence":ref(LS)}
def run():
    guard()
    out={}
    trks=X(SQ+"find_tracks_by_type", binding=VB, track_type=ref("/Script/MovieSceneTracks.MovieSceneSkeletalAnimationTrack"))
    if trks: t=trks[0]
    else: t=X(SQ+"add_track_to_binding", binding=VB, track_type=ref("/Script/MovieSceneTracks.MovieSceneSkeletalAnimationTrack"))
    out["t"]=t
    for key in VKEYS:
        c=ALL[key]()
        s=X(SQ+"add_section", track=t)
        X(SQ+"set_section_animation", section=s, anim_sequence_path="/Game/Jedi/Anims/"+c.name)
        X(SQ+"set_section_range", section=s, start_frame=c.S, end_frame=c.S+c.T+1)
        out[key]=s
    return out
