KEYS = ("Enemy", "Clanker", "Bulwark", "Roller", "Jet", "Warden", "Horde")
def run():
    out = {}
    acts = T("scene.find_actors", name="", tag="", collision_channels=[])
    names = [(a["refPath"] if isinstance(a, dict) else str(a)) for a in acts]
    hits = [p for p in names if any(k in p.split(".")[-1] for k in KEYS)]
    out["hits"] = [h.split(".")[-1] for h in hits][:20]
    for p in hits[:10]:
        try:
            out[p.split(".")[-1]] = T("obj.get_properties", instance=ref(p), properties=["Type", "DeathSounds"])[:300]
        except Exception as e:
            out[p.split(".")[-1]] = str(e)[:120]
    return out
