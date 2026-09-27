def Rt(v, th):
    c,s=math.cos(math.radians(th)),math.sin(math.radians(th))
    return (v[0]*c+v[2]*s, v[1], -v[0]*s+v[2]*c)
def lerp(a,b,k): return tuple(x+(y-x)*k for x,y in zip(a,b))
def rotw(rot, th):
    m=Mr(*rot); rows=[Wd(Rt(Wd(r),th)) for r in m]
    return m2r(*rows)
TH=[0,6,25,55,90,130,170,210,250,290,322,345,360,360,360,360,360]
K =[0,0.3,0.7,0.95,1,1,1,1,1,1,1,1,0.9,0.7,0.45,0.2,0]
DZ=[0,-4,2,8,12,14,15,15,14,12,10,6,3,1,0,0,0]
def run():
    S=900
    pw=getw("body_ctrl",227)["location"]; pel=Cp((pw["x"],pw["y"],pw["z"]))
    feet={}
    for c in ["foot_l_ik_ctrl","foot_r_ik_ctrl"]:
        w=getw(c,227); feet[c]=(sub(Cp((w["location"]["x"],w["location"]["y"],w["location"]["z"])),pel), (w["rotation"]["pitch"],w["rotation"]["yaw"],w["rotation"]["roll"]))
    tuck={"foot_l_ik_ctrl":(14,-13,-42),"foot_r_ik_ctrl":(12,13,-44)}
    pvs={"leg_l_pv_ik_ctrl":(45,-14,-30),"leg_r_pv_ik_ctrl":(45,14,-30)}
    rs=sub(READY["rP"],pel); ls=sub(READY["lP"],pel)
    rt=(20,26,5); lt=(22,-14,-18)
    Ds=READY["rD"]; Dt=(-0.45,0.6,0.66)
    for i in range(17):
        k=K[i]; th=TH[i]
        body(S+i, yaw=-22.5*min(1,k*1.5), bend=th, dz=DZ[i], sbend=16*k, head_pitch=12*k)
    out=[]
    for i in range(17):
        k=K[i]; th=TH[i]; F=S+i
        piv=add(pel,(0,0,DZ[i]))
        for c in feet:
            rel=lerp(feet[c][0], tuck[c], k)
            setw(c, F, add(piv, Rt(rel,th)), rotw(feet[c][1], th))
        for c,v in pvs.items():
            setw(c, F, add(piv, Rt(v,th)))
        show(F)
        rP=add(piv, Rt(lerp(rs,rt,k),th)); lP=add(piv, Rt(lerp(ls,lt,k),th))
        D=Rt(nrm(lerp(Ds,Dt,k)),th)
        r=arms(F, rP=rP, rD=D, lP=lP, lback=Rt((-0.3,-1,0.2),th), rpv=Rt((-0.3,0.6,-0.75),th), lpv=Rt((-0.3,-0.6,-0.75),th))
        out.append([round(x) for x in r["rP"]])
    return {"r":out}
