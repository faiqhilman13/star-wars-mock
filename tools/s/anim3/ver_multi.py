import time
VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
VO=(-1000.0,1650.0,100.0)
def sabxf(actor):
    s=json.loads(T("obj.get_properties", instance=ref(actor+".Saber"), properties=["childActor"]))["childActor"]
    t=T("actor.get_actor_transform", actor=s)
    return tup(t["location"]), tup(t["rotation"])
def run():
    guard()
    out={}
    for key in VKEYS:
        c=ALL[key]()
        worst=0.0; worsta=0.0; n=0
        step=max(1,c.T//8)
        fr=sorted(set(list(range(0,c.T+1,step))+[c.T]))
        for i in fr:
            show(c.S+i); getw("hand_r_ik_ctrl",c.S+i); time.sleep(0.25)
            rl,rr=sabxf(ACTOR); vl,vr=sabxf(VA)
            d=vlen(sub(sub(vl,VO),sub(rl,O)))
            bz_r=Mr(*rr)[2]; bz_v=Mr(*vr)[2]
            ang=math.degrees(math.acos(max(-1,min(1,dot(bz_r,bz_v)))))
            worst=max(worst,d); worsta=max(worsta,ang); n+=1
        out[c.name]={"frames_checked":n,"worst_cm":round(worst,2),"worst_deg":round(worsta,2)}
    guard()
    return out
