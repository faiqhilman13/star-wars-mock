def run():
    out={}
    out["pr"]=X(SQ+"get_playback_range", sequence=ref(LS))
    out["wr"]=X(SQ+"get_work_range", sequence=ref(LS))
    out["vr"]=X(SQ+"get_view_range", sequence=ref(LS))
    setb("arm_r_fk_ik_switch", 1990, True)
    out["2000"]=X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=2000)
    out["1990"]=X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=1990)
    out["e1000"]=geteul("body_ctrl",1000)
    out["e2000"]=geteul("body_ctrl",2000)
    return out
