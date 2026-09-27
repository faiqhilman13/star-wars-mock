import time
VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
def sabxf(actor):
    s=json.loads(T("obj.get_properties", instance=ref(actor+".Saber"), properties=["childActor"]))["childActor"]
    t=T("actor.get_actor_transform", actor=s)
    return tup(t["location"]), tup(t["rotation"])
def run():
    guard()
    c=ALL[VNAME]()
    out={}
    for i in [4,8,12]:
        show(c.S+i)
        a=[round(x,1) for x in Cp(sabxf(ACTOR)[0])]
        h=[round(x,1) for x in wpos("hand_r_ik_ctrl",c.S+i)]
        time.sleep(0.5)
        b=[round(x,1) for x in Cp(sabxf(ACTOR)[0])]
        X(SQ+"force_evaluate")
        cc=[round(x,1) for x in Cp(sabxf(ACTOR)[0])]
        v=sabxf(VA)[0]; v=[round(x,1) for x in Cp((v[0],v[1]-250,v[2]))]
        out[str(i)]={"rig_now":a,"hand":h,"rig_later":b,"rig_eval":cc,"ver":v}
    return out
