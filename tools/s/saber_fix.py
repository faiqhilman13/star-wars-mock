B = "/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C:"
def c(n): return ref(B + n + "_GEN_VARIABLE")
def run():
    out = {}
    T("actor.remove_component", component=c("SaberRoot"))
    bi = json.loads(T("obj.get_properties", instance=c("BladeCore"), properties=["bodyInstance"]))["bodyInstance"]
    out["bi_keys"] = list(bi.keys())
    for n in ["Hilt", "BladeCore", "BladeGlow"]:
        b = json.loads(T("obj.get_properties", instance=c(n), properties=["bodyInstance"]))["bodyInstance"]
        b["collisionEnabled"] = "NoCollision"
        for k in b:
            if "profile" in k.lower(): b[k] = "NoCollision"
        T("obj.set_properties", instance=c(n), values=json.dumps({"bodyInstance": b}))
    out["after"] = json.loads(T("obj.get_properties", instance=c("BladeCore"), properties=["bodyInstance"]))["bodyInstance"].get("collisionEnabled")
    out["try1"] = T("obj.set_properties", instance=c("BladeLight"), values=json.dumps({"lightColor": "(R=40,G=110,B=255,A=255)"}))
    out["light"] = T("obj.get_properties", instance=c("BladeLight"), properties=["lightColor"])
    return out
