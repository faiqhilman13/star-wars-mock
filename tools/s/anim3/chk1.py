def run():
    guard()
    out={}
    out["cr"]=X(CR+"get_control_rigs", sequence=ref(LS))
    trk=LS+":MovieScene_0.MovieSceneControlRigParameterTrack_0"
    out["secs"]=X(SQ+"get_sections", track=ref(trk))
    show(BASEF)
    c={}
    for n in ["body_ctrl","spine_01_ctrl","spine_02_ctrl","spine_03_ctrl","head_ctrl","neck_01_ctrl"]:
        e=geteul(n,BASEF); c["L_"+n]=[round(x,3) for x in tup(e["location"])+tup(e["rotation"])]
    for n in ["body_ctrl","foot_l_ik_ctrl","foot_r_ik_ctrl","leg_l_pv_ik_ctrl","leg_r_pv_ik_ctrl","upperarm_r_fk_ctrl","upperarm_l_fk_ctrl","hand_r_ik_ctrl","hand_l_ik_ctrl"]:
        w=getw(n,BASEF); c["W_"+n]=[round(x,2) for x in Cp(tup(w["location"]))+tup(w["rotation"])]
    out["cal"]=c
    out["sw"]=[X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=2000), X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_l_fk_ik_switch", frame=2000)]
    out["pr"]=X(SQ+"get_playback_range", sequence=ref(LS))
    return out
