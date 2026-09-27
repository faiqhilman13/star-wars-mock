def run():
    out={}
    c=ALL[MNAME]()
    for i in MFR:
        F=c.S+i; show(F)
        r={}
        for n in ["body_ctrl","neck_01_ctrl","head_ctrl","thigh_r_fk_ctrl","calf_r_fk_ctrl","foot_r_fk_ctrl","ball_r_fk_ctrl","thigh_l_fk_ctrl","calf_l_fk_ctrl","foot_l_fk_ctrl","upperarm_r_fk_ctrl","hand_r_fk_ctrl","upperarm_l_fk_ctrl","lowerarm_l_fk_ctrl","hand_l_fk_ctrl"]:
            w=getw(n,F); r[n[:-5]]=[round(x,1) for x in Cp(tup(w["location"]))]
        d=sub(r["neck_01"],r["body"]); r["torso"]=round(math.degrees(math.atan2(d[0],d[2])),1)
        r["head_rot"]=[round(x,1) for x in tup(getw("head_ctrl",F)["rotation"])]
        p=c.pose(float(i))
        if p.get("rA") is not None: r["rA_tgt"]=[round(x,1) for x in p["rA"]]; r["lA_tgt"]=[round(x,1) for x in p["lA"]]
        out[str(i)]=r
    return out
