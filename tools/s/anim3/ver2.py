VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
VO=(-1000.0,650.0,100.0)
def sabxf(actor):
    s=json.loads(T("obj.get_properties", instance=ref(actor+".Saber"), properties=["childActor"]))["childActor"]
    t=T("actor.get_actor_transform", actor=s)
    return tup(t["location"]), tup(t["rotation"])
def run():
    guard()
    c=ALL[VNAME]()
    R={}; V={}
    for i in range(0,21):
        show(c.S+i)
        rl,rr=sabxf(ACTOR); vl,vr=sabxf(VA)
        R[i]=Cp(rl); V[i]=Cp((vl[0],vl[1]-250,vl[2]))
    out={}
    for i in [4,6,8,10,12]:
        out[str(i)]={"rig":[round(x,1) for x in R[i]],"ver":[round(x,1) for x in V[i]],
          "d-1":round(vlen(sub(V[i],R[i-1])),1),"d0":round(vlen(sub(V[i],R[i])),1),"d+1":round(vlen(sub(V[i],R[i+1])),1)}
    return out
