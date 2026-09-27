SAL="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Lightsaber_C_UAID_D8BBC102E1FDCD0503_1718477206"
SB={"bindingId":"2F4B2D92-4716-4D0A-C169-2580C45D5A4C","sequence":ref(LS)}
def run():
    out={}
    trks=X(SQ+"find_tracks_by_type", binding=SB, track_type=ref("/Script/MovieSceneTracks.MovieScene3DTransformTrack"))
    t=trks[0] if trks else X(SQ+"add_track_to_binding", binding=SB, track_type=ref("/Script/MovieSceneTracks.MovieScene3DTransformTrack"))
    secs=X(SQ+"get_sections", track=t)
    s=secs[0] if secs else X(SQ+"add_section", track=t)
    X(SQ+"set_section_range", section=s, start_frame=0, end_frame=6000)
    ch=X(KF+"get_channel_names", section=s)
    out["ch"]=ch
    vals={"Location.X":7.0,"Location.Y":-2.0,"Location.Z":0.0,"Rotation.X":0.0,"Rotation.Y":35.0,"Rotation.Z":0.0,"Scale.X":1.0,"Scale.Y":1.0,"Scale.Z":1.0}
    for c in ch:
        for k,v in vals.items():
            if c.endswith(k):
                X(KF+"set_default_value", section=s, channel_name=c, value=v)
    F=2905; show(F); getw("hand_l_ik_ctrl",F); time.sleep(0.4); show(F); w=getw("hand_l_ik_ctrl",F); time.sleep(0.3)
    st=T("actor.get_actor_transform", actor=ref(SAL))
    m=Mr(*tup(w["rotation"])); o=Mr(*tup(st["rotation"])); d=sub(tup(st["location"]),tup(w["location"]))
    out["rel"]=[round(dot(d,m[k]),2) for k in range(3)]; out["Z"]=[round(dot(o[2],m[k]),3) for k in range(3)]
    return out
