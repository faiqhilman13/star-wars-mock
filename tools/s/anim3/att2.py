SAL="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Lightsaber_C_UAID_D8BBC102E1FDCD0503_1718477206"
ASEC=LS+":MovieScene_0.MovieScene3DAttachTrack_1.MovieScene3DAttachSection_0"
def run():
    guard()
    out={}
    T("actor.set_actor_transform", actor=ref(SAL), xform=xf((7,-2,0),(35,0,0)), worldspace=True)
    T("obj.set_properties", instance=ref(ASEC), values=json.dumps({"constraintBindingId":{"guid":"9FA787AC-44A7-EBA8-9DB0-CD9BBC973698"},
        "attachComponentName":"Body","attachSocketName":"hand_l","attachmentLocationRule":"KeepRelative","attachmentRotationRule":"KeepRelative","attachmentScaleRule":"KeepRelative"}))
    X(SQ+"set_section_range", section=ref(ASEC), start_frame=0, end_frame=6000)
    out["p"]=T("obj.get_properties", instance=ref(ASEC), properties=["constraintBindingId","attachComponentName","attachSocketName","attachmentLocationRule"])
    show(BASEF)
    out["salw"]=T("actor.get_actor_transform", actor=ref(SAL))
    out["hl"]=getw("hand_l_ik_ctrl",BASEF)
    sab=json.loads(T("obj.get_properties", instance=ref(ACTOR+".Saber"), properties=["childActor"]))["childActor"]
    out["sr"]=T("actor.get_actor_transform", actor=sab)
    out["hr"]=getw("hand_r_ik_ctrl",BASEF)
    return out
