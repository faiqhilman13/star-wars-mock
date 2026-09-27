def run():
    out={}
    F=260
    b=geteul("body_ctrl",227); r=b["rotation"]
    def sh():
        show(F); w=getw("upperarm_r_fk_ctrl",F)["location"]; return [round(-1000-w["x"],1), round(400-w["y"],1), round(w["z"]-100,1)]
    setl("body_ctrl",F,tuple(b["location"].values()),(r["pitch"],r["yaw"],r["roll"])); out["base"]=sh()
    setl("body_ctrl",F,tuple(b["location"].values()),(r["pitch"],r["yaw"]+30,r["roll"])); out["yaw+30"]=sh()
    setl("body_ctrl",F,tuple(b["location"].values()),(r["pitch"],r["yaw"],r["roll"]))
    out["pelvis"]=getw("body_ctrl",F)
    return out
