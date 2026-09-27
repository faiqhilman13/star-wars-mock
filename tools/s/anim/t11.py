def run():
    out={"cur":X(SQ+"get_current_sequence"),"range":X(SQ+"get_playback_range", sequence=ref(LS))}
    show(308); out["ph"]=X(SQ+"get_playhead_frame")
    out["hw308"]=getw("hand_r_ik_ctrl",308)["location"]
    out["sw"]=X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=308)
    return out
