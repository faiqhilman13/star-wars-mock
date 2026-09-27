def run():
    out={}
    for n in ["AS_Saber_Run_V2","AS_Saber_Idle_V2","AS_Saber_Combo1_V2"]:
        p="/Game/Jedi/Anims/%s.%s"%(n,n)
        out[n]=T("obj.get_properties", instance=ref(p), properties=["sequenceLength","numberOfSampledFrames","numberOfSampledKeys","bLoop","bEnableRootMotion","rateScale","Skeleton"])
    return out
