def run():
    out={}
    for n in ["AS_Saber_Swing1","AS_Saber_Block"]:
        p="/Game/Jedi/Anims/%s.%s"%(n,n)
        out[n]=T("obj.get_properties", instance=ref(p), properties=["sequenceLength","numberOfSampledFrames","numberOfSampledKeys","bLoop","rateScale"])
    out["list"]=T("asset.find_assets", path="/Game/Jedi/Anims", class_name="", recursive=False) if False else None
    return out
