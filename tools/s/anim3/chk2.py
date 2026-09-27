def run():
    out={}
    for f in [0,100,227,250,260,300,600,1000,1100,1500,2000]:
        out[str(f)]=[X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=f) for c in ["arm_r_fk_ik_switch","arm_l_fk_ik_switch","spine_fk_ik_switch","leg_r_fk_ik_switch","arm_r_stretch_switch"]]
    ch=X(KF+"get_channel_names", section=ref(SEC))
    out["n"]=len(ch)
    sw=[c for c in ch if "switch" in c.lower()]
    out["swch"]=sw
    for c in sw[:6]:
        try: out["k_"+c]=X(KF+"get_keys", section=ref(SEC), channel_name=c)
        except Exception as e: out["k_"+c]=str(e)[:200]
    return out
