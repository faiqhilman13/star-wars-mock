def run():
    out={}
    out["hasend"]=X(SQ+"has_section_end_frame", section=ref(SEC))
    out["hasstart"]=X(SQ+"has_section_start_frame", section=ref(SEC))
    for f in [1050,1099,1100,1101]:
        out[str(f)]=[X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=f) for c in ["arm_r_fk_ik_switch","arm_l_fk_ik_switch"]]
    k=json.loads(X(KF+"get_keys", section=ref(SEC), channel_name="arm_r_fk_ik_switch"))
    out["nk"]=len(k); out["tail"]=k[-4:]
    k=json.loads(X(KF+"get_keys", section=ref(SEC), channel_name="body_ctrl.Location.X")) if False else None
    ch=X(KF+"get_channel_names", section=ref(SEC))
    out["bodych"]=[c for c in ch if c.startswith("body_ctrl")]
    return out
