def run():
    p = "/Game/Jedi/Maps/UEDPIE_0_Lvl_HordeArena.Lvl_HordeArena:PersistentLevel.BP_Jedi_C_0"
    return {"r": T("obj.get_properties", instance=ref(p), properties=["CurrentHP", "MaxHP", "HealthRegenDelay", "HealthRegenRate"])}
