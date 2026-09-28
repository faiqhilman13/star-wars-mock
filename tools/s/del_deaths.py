def run():
    names = ["Jet_1", "Jet_2", "Jet_3", "Roller_1", "Roller_2", "Roller_3", "Warden_1", "Warden_2"]
    out = {}
    for n in names:
        p = "/Game/Jedi/Audio/Deaths/SW_Death_" + n
        try: out[n] = T("asset.delete", path=p)
        except Exception as e: out[n] = str(e)[:120]
    return out
