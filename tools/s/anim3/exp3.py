def run():
    guard()
    out={}
    for key in ONLY:
        c=ALL[key]()
        name=c.name; a=c.S; n=c.T
        p="/Game/Jedi/Anims/"+name
        if not T("asset.exists", path=p):
            T("asset.duplicate", path="/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle", new_path=p)
        X(SQ+"set_playback_range", sequence=ref(LS), start_frame=a, end_frame=a+n)
        ok=X(IE+"export_anim_sequence", world=ref(WORLD), sequence=ref(LS), anim_sequence=ref(p+"."+name), binding=BODY, create_link=False)
        T("obj.set_properties", instance=ref(p+"."+name), values=json.dumps({"bLoop":bool(c.loop)}))
        out[name]=[ok, T("obj.get_properties", instance=ref(p+"."+name), properties=["sequenceLength","numberOfSampledFrames","numberOfSampledKeys","bLoop","Skeleton","bEnableRootMotion"])]
        out["save_"+name]=T("asset.save_assets", asset_paths=[p])
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=6000)
    guard()
    return out
