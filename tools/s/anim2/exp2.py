CL={"idle":("AS_Saber_Idle_V2",300,60,True), "run":("AS_Saber_Run_V2",400,20,True), "c1":("AS_Saber_Combo1_V2",500,18,False),
    "c2":("AS_Saber_Combo2_V2",600,16,False), "c3":("AS_Saber_Combo3_V2",700,18,False), "c4":("AS_Saber_Combo4_V2",800,17,False),
    "c5":("AS_Saber_Combo5_V2",900,28,False), "block":("AS_Saber_Block_V2",1000,30,True)}
def run():
    guard()
    out={}
    for key in ONLY:
        name,a,n,loop=CL[key]
        p="/Game/Jedi/Anims/"+name
        if not T("asset.exists", path=p):
            T("asset.duplicate", path="/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle", new_path=p)
        X(SQ+"set_playback_range", sequence=ref(LS), start_frame=a, end_frame=a+n+ENDADD)
        ok=X(IE+"export_anim_sequence", world=ref(WORLD), sequence=ref(LS), anim_sequence=ref(p+"."+name), binding=BODY, create_link=False)
        T("obj.set_properties", instance=ref(p+"."+name), values=json.dumps({"bLoop":loop}))
        out[name]=[ok, T("obj.get_properties", instance=ref(p+"."+name), properties=["sequenceLength","numberOfSampledFrames","numberOfSampledKeys","bLoop","Skeleton","bEnableRootMotion"])]
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=2000)
    guard()
    return out
