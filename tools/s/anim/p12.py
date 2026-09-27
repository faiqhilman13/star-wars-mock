SAB="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.Saber_GEN_VARIABLE_BP_Lightsaber_C_CAT_UAID_D8BBC102E1FDB60503_2062309264"
def run():
    return {"b":T("actor.get_actor_bounds", actor=ref(SAB)),"t":T("actor.get_actor_transform", actor=ref(SAB))["location"]}
