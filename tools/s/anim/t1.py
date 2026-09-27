def run():
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=1000)
    setb("arm_r_fk_ik_switch", 250, True)
    setb("arm_r_stretch_switch", 250, False)
    hand(250, (30,15,115), (0.3,0,0.95), pv=(-20,50,100))
    show(250)
    return {"hw":getw("hand_r_ik_ctrl",250)}
