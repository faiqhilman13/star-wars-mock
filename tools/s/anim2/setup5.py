def run():
    guard()
    out={}
    for s in ["r","l"]:
        setb("arm_%s_fk_ik_switch"%s, 250, True); setb("arm_%s_stretch_switch"%s, 250, False)
    fingers("r",250,True)
    fingers("l",250,False)
    e=geteul("neck_02_ctrl",BASEF); l=tup(e["location"]); r=tup(e["rotation"])
    for f in range(1500,1520): setl("neck_02_ctrl", f, l, r)
    out["neck02"]=[l,r]
    out["sw"]=[X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=600)]
    return out
