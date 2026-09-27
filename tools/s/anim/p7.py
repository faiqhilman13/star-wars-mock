def run():
    out={}
    out["load"]=X(CR+"load_anim_into_rig", cr_section=ref(SEC), anim_sequence_path="/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle", start_frame=0, reset_controls=True, key_reduce=False, tolerance=0.001)
    X(SQ+"set_playhead_frame", frame=0); X(SQ+"force_evaluate")
    for c in ["arm_r_fk_ik_switch","arm_l_fk_ik_switch","spine_fk_ik_switch","leg_r_fk_ik_switch"]:
        out[c]=X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=0)
    for c in ["upperarm_r_fk_ctrl","hand_r_fk_ctrl","body_ctrl","chest_ctrl","spine_01_ctrl"]:
        out[c]=X(CR+"get_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=0)
    return out
