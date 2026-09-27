def run():
    out={}
    info=X(CR+"get_controls_info", sequence=ref(LS), control_rig_asset_path=RIG) if False else None
    show(BASEF)
    for n in ["thigh_l_fk_ctrl","thigh_r_fk_ctrl","calf_l_fk_ctrl","calf_r_fk_ctrl","foot_l_fk_ctrl","foot_r_fk_ctrl","ball_l_fk_ctrl","ball_r_fk_ctrl","ball_l_ik_ctrl","ball_r_ik_ctrl","foot_l_ik_ctrl","foot_r_ik_ctrl","pelvis_ctrl","body_ctrl","neck_01_ctrl","head_ctrl","spine_03_ctrl","upperarm_r_fk_ctrl","lowerarm_r_fk_ctrl","hand_r_fk_ctrl","upperarm_l_fk_ctrl","lowerarm_l_fk_ctrl","hand_l_fk_ctrl","clavicle_l_ctrl"]:
        try:
            w=getw(n,BASEF); out[n]=[round(x,2) for x in Cp(tup(w["location"]))]+[round(x,2) for x in tup(w["rotation"])]
        except Exception as e: out[n]=str(e)[:80]
    return out
