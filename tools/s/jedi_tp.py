def run():
    p = "/Game/Jedi/Maps/UEDPIE_0_Lvl_HordeArena.Lvl_HordeArena:PersistentLevel.BP_Jedi_C_0"
    T("actor.set_actor_transform", actor=ref(p), xform=xf((-2500, 0, 160), (0, 0, 0)))
    return {"ok": True}
