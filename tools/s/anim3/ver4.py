VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
def run():
    return {"va":T("actor.get_actor_transform", actor=ref(VA)),"rig":T("actor.get_actor_transform", actor=ref(ACTOR)),
            "vbody":T("obj.get_properties", instance=ref(VA+".Body"), properties=["relativeLocation","relativeRotation","skeletalMeshAsset"]),
            "rbody":T("obj.get_properties", instance=ref(ACTOR+".Body"), properties=["relativeLocation","relativeRotation","skeletalMeshAsset"])}
