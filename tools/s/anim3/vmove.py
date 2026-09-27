VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
def run():
    T("actor.set_actor_transform", actor=ref(VA), xform=xf((-1000,VY,100),(0,90,0)), worldspace=True)
    return {"va":T("actor.get_actor_transform", actor=ref(VA))["location"]}
