def run():
    out={}
    T("obj.set_properties", instance=ref("/Game/Jedi/Anims/AS_Saber_Block.AS_Saber_Block"), values=json.dumps({"bLoop":True}))
    for n in ["AS_Saber_Swing1","AS_Saber_Swing2","AS_Saber_Swing3","AS_Saber_Block","AS_Saber_Parry","AS_Force_Dash","AS_Jump_Flip"]:
        p="/Game/Jedi/Anims/%s.%s"%(n,n)
        out[n]=T("obj.get_properties", instance=ref(p), properties=["sequenceLength","numberOfSampledKeys","numberOfSampledFrames","bLoop","rateScale"])
    return out
