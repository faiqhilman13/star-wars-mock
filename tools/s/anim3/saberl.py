SAL="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Lightsaber_C_UAID_D8BBC102E1FDCD0503_1718477206"
ASEC=LS+":MovieScene_0.MovieScene3DAttachTrack_1.MovieScene3DAttachSection_0"
def run():
    guard()
    out={}
    on=bool(SL_ON)
    T("obj.set_properties", instance=ref(ASEC), values=json.dumps({"bIsActive":on}))
    if not on:
        T("actor.set_actor_transform", actor=ref(SAL), xform=xf((-1000,400,-600),(0,0,0)), worldspace=True)
    else:
        T("actor.set_actor_transform", actor=ref(SAL), xform=xf((7,-2,0),(35,0,0)), worldspace=True)
    sab=ref(ACTOR+".Saber")
    if STAFF is not None:
        cls="/Game/Jedi/Blueprints/BP_Saberstaff.BP_Saberstaff_C" if STAFF else "/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C"
        T("obj.set_properties", instance=sab, values=json.dumps({"childActorClass":cls}))
    out["saber"]=T("obj.get_properties", instance=sab, properties=["childActorClass","childActor"])
    show(2000)
    out["sal"]=T("actor.get_actor_transform", actor=ref(SAL))
    return out
