def run():
    out = {}
    base = "/Game/Jedi/Maps/UEDPIE_0_Lvl_HordeArena.Lvl_HordeArena:PersistentLevel."
    for n in ["ClankerDroid_0", "ClankerDroid_1", "ClankerDroid_2", "ClankerDroid_5"]:
        try:
            comps = T("actor.get_components", actor=ref(base + n), component_type=ref("/Script/Engine.SkeletalMeshComponent"))
            out[n] = T("obj.get_properties", instance=comps[0], properties=["OverrideMaterials", "SkeletalMeshAsset"])[:700]
            break
        except Exception as e:
            out[n] = str(e)[:100]
    out["slots"] = T("obj.get_properties", instance=ref("/Game/Jedi/Enemies/Clanker/SKM_Clanker.SKM_Clanker"), properties=["Materials"])[:600]
    return out
