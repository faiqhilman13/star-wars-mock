def run():
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=1000)
    show(308)
    return {"w":getw("hand_r_ik_ctrl",308),"e":geteul("hand_r_ik_ctrl",308)}
