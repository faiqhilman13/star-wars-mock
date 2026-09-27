def run():
    for n in range(0, 6):
        p = "/Game/Jedi/Maps/UEDPIE_0_Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Jedi_C_%d" % n
        try:
            return {str(n): T("obj.get_properties", instance=ref(p), properties=["CurrentHP", "ForcePower"])}
        except Exception:
            pass
    return {}
