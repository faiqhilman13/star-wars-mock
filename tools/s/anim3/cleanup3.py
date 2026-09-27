VA="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCF0503_1482041564"
SAL="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Lightsaber_C_UAID_D8BBC102E1FDCD0503_1718477206"
def run():
    guard()
    out={}
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=6000)
    p="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V3"
    out["save"]=T("asset.save_assets", asset_paths=[p])
    out["dirty"]=T("asset.is_dirty", asset_path=p)
    out["close"]=X(SQ+"close_sequence")
    for a in [ACTOR, VA, SAL]:
        try: out["rm_"+a[-10:]]=T("scene.remove_from_scene", actor=ref(a))
        except Exception as e: out["rm_"+a[-10:]]=str(e)[:150]
    out["left_rig"]=T("scene.find_actors", name="GripTest", tag="", collision_channels=[])
    out["left_sab"]=[x for x in T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])]
    out["map_dirty"]=T("asset.is_dirty", asset_path="/Game/Jedi/Maps/Lvl_JediArena")
    anims=T("asset.find_assets", folder_path="/Game/Jedi/Anims", name="", recursive=False)
    out["new_assets"]=[a for a in anims if ("V3" in a or "Staff_" in a or "Dual_" in a)]
    out["new_dirty"]={a:T("asset.is_dirty", asset_path=a) for a in out["new_assets"]}
    return out
