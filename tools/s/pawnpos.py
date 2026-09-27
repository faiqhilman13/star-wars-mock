def run():
    for n in range(0, 4):
        p = "/Game/Jedi/Maps/UEDPIE_0_Lvl_HordeArena.Lvl_HordeArena:PersistentLevel.BP_Jedi_C_%d" % n
        return {"xf": T("actor.get_actor_transform", actor=ref(p))["location"]}
