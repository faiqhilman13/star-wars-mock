CLIPS=[("AS_Saber_Swing1",300,320),("AS_Saber_Swing2",400,420),("AS_Saber_Swing3",500,527),("AS_Saber_Block",600,630),("AS_Saber_Parry",700,711),("AS_Force_Dash",800,812),("AS_Jump_Flip",900,916)]
import_only=None
def run():
    out={}
    for name,a,b in CLIPS:
        if import_only and name not in import_only: continue
        p="/Game/Jedi/Anims/"+name
        if not T("asset.exists", path=p):
            T("asset.duplicate", path="/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle", new_path=p)
        X(SQ+"set_playback_range", sequence=ref(LS), start_frame=a, end_frame=b)
        ok=X(IE+"export_anim_sequence", world=ref("/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena"), sequence=ref(LS), anim_sequence=ref(p+"."+name), binding=BODY, create_link=False)
        props=T("obj.get_properties", instance=ref(p+"."+name), properties=["SequenceLength","Skeleton"])
        out[name]=[ok, props]
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=1000)
    return out
