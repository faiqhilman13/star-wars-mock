CL=[("S1",300,320),("S2",400,420),("S3",500,527),("Parry",700,711),("Block",600,601)]
def run():
    out={}
    for n,a,b in CL:
        rows=[]
        for f in range(a,b+1):
            show(f); w=getw("hand_r_ik_ctrl",f); l=w["location"]; P=Cp((l["x"],l["y"],l["z"]))
            D=blade_of(w["rotation"]); tip=add(P,mulv(D,105)); mid=add(P,mulv(D,55))
            rows.append([f-a]+[round(x,1) for x in P]+[round(x,2) for x in D]+[round(x,1) for x in tip])
        out[n]=rows
    return out
