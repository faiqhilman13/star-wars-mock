VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
def run():
    guard()
    out={}
    body=ref(VA+".Body")
    T("obj.set_properties", instance=body, values=json.dumps({"skeletalMeshAsset":"/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden.SKM_GreyWarden","animationMode":"AnimationBlueprint"}))
    b=X(SQ+"add_actors", actors=[ref(VA)])
    out["b"]=b
    kids=X(SQ+"get_child_possessables", binding=b[0])
    out["kids"]=kids
    return out
