VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
SAL="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Lightsaber_C_UAID_D8BBC102E1FDCD0503_1718477206"
def run():
    out={}
    acts=[ACTOR, VA]
    tgts=[ACTOR+".BillboardComponent_13"]
    for a in acts:
        try:
            ch=json.loads(T("obj.get_properties", instance=ref(a+".Saber"), properties=["childActor"]))["childActor"]["refPath"]
            for c in T("actor.get_components", actor=ref(ch), component_type=None):
                if "Billboard" in c["refPath"]: tgts.append(c["refPath"])
        except Exception as e: out["err_"+a[-6:]]=str(e)[:100]
        for c in T("actor.get_components", actor=ref(a), component_type=None):
            if "Billboard" in c["refPath"]: tgts.append(c["refPath"])
    for c in T("actor.get_components", actor=ref(SAL), component_type=None):
        if "Billboard" in c["refPath"]: tgts.append(c["refPath"])
    n=0
    for c in tgts:
        try: T("obj.set_properties", instance=ref(c), values=json.dumps({"bVisible":False})); n+=1
        except Exception: pass
    out["hidden"]=n
    return out
