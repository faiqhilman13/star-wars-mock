def run():
    p = "/Game/Jedi/Maps/UEDPIE_0_Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Jedi_C_0"
    return {"xf": T("actor.get_actor_transform", actor=ref(p))}
