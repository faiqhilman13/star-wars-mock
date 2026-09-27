def run():
    out={}
    for c in ["upperarm_r_fk_ctrl","lowerarm_r_fk_ctrl","upperarm_l_fk_ctrl","clavicle_r_ctrl","spine_01_ctrl","spine_02_ctrl","spine_03_ctrl","chest_ctrl","body_ctrl","hips_ctrl","neck_01_ctrl","head_ctrl","foot_r_ik_ctrl","foot_l_ik_ctrl","arm_r_pv_ik_ctrl","root_ctrl","index_01_r_ctrl"]:
        try:
            w=json.loads(X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=0))
            l=json.loads(X(CR+"get_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=0))
            f=lambda v:[round(x,1) for x in v]
            out[c]="W "+str(f([-1000-w["location"]["x"],400-w["location"]["y"],w["location"]["z"]-100]))+" R"+str(f(list(w["rotation"].values())))+" | L "+str(f(list(l["location"].values())))+str(f(list(l["rotation"].values())))
        except Exception as e: out[c]=str(e)[:150]
    out["range"]=X(SQ+"get_playback_range", sequence=ref(LS))
    return out
