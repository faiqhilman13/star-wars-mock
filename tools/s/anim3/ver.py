import time
VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
VO=(-1000.0,VYV,100.0)
def sabxf(actor):
    s=json.loads(T("obj.get_properties", instance=ref(actor+".Saber"), properties=["childActor"]))["childActor"]
    t=T("actor.get_actor_transform", actor=s)
    return tup(t["location"]), tup(t["rotation"])
def run():
    guard()
    out={}
    c=ALL[VNAME]()
    worst=0.0; worsta=0.0; rows=[]
    for i in VFR:
        show(c.S+i); getw("hand_r_ik_ctrl",c.S+i); time.sleep(0.3)
        rl,rr=sabxf(ACTOR); vl,vr=sabxf(VA)
        rrel=sub(rl,O); vrel=sub(vl,VO)
        dv=sub(vrel,rrel); d=vlen(dv)
        bz_r=Mr(*rr)[2]; bz_v=Mr(*vr)[2]
        ang=math.degrees(math.acos(max(-1,min(1,dot(bz_r,bz_v)))))
        worst=max(worst,d); worsta=max(worsta,ang)
        rows.append([i, round(d,2), round(ang,2), [round(x,1) for x in Wd(dv)]])
    out["rows"]=rows; out["worst_cm"]=round(worst,2); out["worst_deg"]=round(worsta,2)
    guard()
    return out
