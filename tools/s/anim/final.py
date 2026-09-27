def run():
    out={}
    for n in ["AS_Saber_Swing1","AS_Saber_Swing2","AS_Saber_Swing3","AS_Saber_Block","AS_Saber_Parry","AS_Force_Dash","AS_Jump_Flip"]:
        p="/Game/Jedi/Anims/"+n
        out[n]=[T("asset.exists", path=p), T("asset.is_dirty", asset_path=p)]
    out["map_dirty"]=T("asset.is_dirty", asset_path="/Game/Jedi/Maps/Lvl_JediArena")
    return out
