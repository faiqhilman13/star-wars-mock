def run():
    out={}
    for n in ["AS_Saber_Swing1","AS_Jump_Flip"]:
        p="/Game/Jedi/Anims/%s.%s"%(n,n)
        out[n]=T("obj.get_properties", instance=ref(p), properties=["bEnableRootMotion","bForceRootLock","interpolation","additiveAnimType"])
    idl="/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle"
    out["idle"]=T("obj.get_properties", instance=ref(idl), properties=["bEnableRootMotion"])
    return out
