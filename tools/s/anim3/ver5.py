import time
VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
VO=(-1000.0,650.0,100.0)
def sabxf(actor):
    s=json.loads(T("obj.get_properties", instance=ref(actor+".Saber"), properties=["childActor"]))["childActor"]
    t=T("actor.get_actor_transform", actor=s)
    return tup(t["location"]), tup(t["rotation"])
def run():
    c=ALL[VNAME]()
    out={}
    for i in [16,18]:
        show(c.S+i)
        seq=[]
        for k in range(4):
            time.sleep(0.6)
            rl,_=sabxf(ACTOR); vl,_=sabxf(VA)
            seq.append([[round(x,1) for x in sub(rl,O)],[round(x,1) for x in sub(vl,VO)]])
        out[str(i)]=seq
    out["ph"]=X(SQ+"get_playhead_frame")
    return out
