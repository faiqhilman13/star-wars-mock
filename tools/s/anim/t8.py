def cp(c, fr):
    return geteul(c, fr)
def run():
    out={}
    F=260
    ctrls=["body_ctrl","spine_01_ctrl","spine_02_ctrl","spine_03_ctrl"]
    base={c:geteul(c,227) for c in ctrls}
    def put(c, d):
        b=base[c]; r=b["rotation"]
        setl(c, F, tuple(b["location"].values()), (r["pitch"]+d[0], r["yaw"]+d[1], r["roll"]+d[2]))
    def hp():
        show(F)
        w=getw("head_ctrl",F)["location"]; 
        return [round(-1000-w["x"],1), round(400-w["y"],1), round(w["z"]-100,1)]
    for c in ctrls: put(c,(0,0,0))
    out["base"]=hp()
    for c in ["body_ctrl","spine_02_ctrl"]:
        for i,nm in enumerate(["pitch","yaw","roll"]):
            d=[0,0,0]; d[i]=20; put(c,d); out[c+"+"+nm]=hp(); put(c,(0,0,0))
    return out
