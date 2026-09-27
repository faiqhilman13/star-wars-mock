def _tips(kind, ctrl, F):
    w=getw(ctrl,F); P=Cp(tup(w["location"])); rot=tup(w["rotation"])
    D=blade_of(rot); O=saber_origin(P, rot)
    t={"b1":add(O,mulv(D,119.0))}
    if kind=="staff": t["b2"]=add(O,mulv(D,-137.0))
    return t
def run():
    guard()
    out={}
    for key in ONLY:
        c=ALL[key]()
        kind=c.extra.get("weapon","saber")
        rows=[]; prev={}
        for i in range(0,c.T+1):
            F=c.S+i; show(F)
            tips={("R"+k):v for k,v in _tips(kind,"hand_r_ik_ctrl",F).items()}
            if kind=="dual": tips.update({("L"+k):v for k,v in _tips("saber","hand_l_ik_ctrl",F).items()})
            r=[i]
            for k in sorted(tips):
                v=tips[k]; sp=0.0 if k not in prev else vlen(sub(v,prev[k]))*30.0
                prev[k]=v
                r.append([k,int(sp)]+[int(round(x)) for x in v])
            rows.append(r)
        out[key]=rows
    guard()
    return out
