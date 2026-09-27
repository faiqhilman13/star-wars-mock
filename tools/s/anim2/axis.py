def run():
    out={}
    F=1100
    ctr=["body_ctrl","foot_l_ik_ctrl","foot_r_ik_ctrl","leg_l_pv_ik_ctrl","leg_r_pv_ik_ctrl","upperarm_r_fk_ctrl","upperarm_l_fk_ctrl","hand_r_ik_ctrl","hand_l_ik_ctrl","arm_r_pv_ik_ctrl","head_ctrl","spine_03_ctrl","ball_l_ik_ctrl","clavicle_r_ctrl"]
    guard(); show(BASEF)
    base={}
    for c in ctr:
        w=getw(c,BASEF); base[c]=w
        out["W_"+c]=[round(x,2) for x in Cp(tup(w["location"]))]+[round(x,2) for x in tup(w["rotation"])]
    for c in ["body_ctrl","spine_01_ctrl","spine_02_ctrl","spine_03_ctrl","head_ctrl","neck_01_ctrl","foot_l_ik_ctrl","hand_r_ik_ctrl"]:
        e=geteul(c,BASEF); out["L_"+c]=[round(x,3) for x in tup(e["location"])+tup(e["rotation"])]
    b=geteul("body_ctrl",BASEF); bl=tup(b["location"]); br=tup(b["rotation"])
    p0=Cp(tup(base["body_ctrl"]["location"]))
    for i,nm in enumerate(["x","y","z"]):
        d=[0,0,0]; d[i]=10
        setl("body_ctrl",F,add(bl,tuple(d)),br); show(F)
        out["dloc_"+nm]=[round(x,2) for x in sub(wpos("body_ctrl",F),p0)]
    setl("body_ctrl",F,bl,(br[0],br[1]+30,br[2])); show(F)
    out["yaw30_uarm_r"]=[round(x,2) for x in wpos("upperarm_r_fk_ctrl",F)]
    out["yaw30_body_rot"]=tup(getw("body_ctrl",F)["rotation"])
    setl("body_ctrl",F,bl,(br[0],br[1]+200,br[2]))
    out["yaw200_read"]=geteul("body_ctrl",F)["rotation"]
    setl("body_ctrl",F,bl,br)
    return out
