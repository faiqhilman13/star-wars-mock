def run():
    out={}
    for F in [227,400,403,405,410,415]:
        show(F)
        r={}
        for n in ["body_ctrl","spine_03_ctrl","neck_01_ctrl","head_ctrl","thigh_l_fk_ctrl","thigh_r_fk_ctrl","foot_l_ik_ctrl","foot_r_ik_ctrl","upperarm_r_fk_ctrl","upperarm_l_fk_ctrl","hand_r_ik_ctrl","hand_l_ik_ctrl","calf_l_fk_ctrl","calf_r_fk_ctrl"]:
            w=getw(n,F); r[n]=[round(x,1) for x in Cp(tup(w["location"]))]
        b=r["body_ctrl"]; nk=r["neck_01_ctrl"]
        d=sub(nk,b); r["torso_deg"]=round(math.degrees(math.atan2(d[0],d[2])),1)
        h=getw("head_ctrl",F); r["head_rot"]=tup(h["rotation"])
        out[str(F)]=r
    return out
