import time
def run():
    out={}
    t0=time.time()
    for i in range(5): X(SQ+"get_display_rate", sequence=ref(LS))
    out["t_trivial"]=(time.time()-t0)/5
    t0=time.time()
    for i in range(5): X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=100)
    out["t_getbool"]=(time.time()-t0)/5
    out["cur"]=X(SQ+"get_current_sequence")
    return out
