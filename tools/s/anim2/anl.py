def run():
    guard()
    out={}
    for nm in ONLY:
        c=ALL[nm]()
        rows=[]; prev=None
        for i in range(0, c.T+1):
            F=c.S+i; show(F)
            w=getw("hand_r_ik_ctrl",F); P=Cp(tup(w["location"])); D=blade_of(tup(w["rotation"]))
            tip=add(P, mulv(D,100.0))
            sp=0.0 if prev is None else vlen(sub(tip,prev))*30.0
            prev=tip
            az=math.degrees(math.atan2(tip[1],tip[0]))
            rows.append([i, int(sp), [int(round(x)) for x in tip], int(az), [int(round(x)) for x in P]])
        out[nm]=rows
    guard()
    return out
