def run():
    out = {}
    for name in ["BP_Saberstaff", "BP_Lightsaber"]:
        bp = ref("/Game/Jedi/Blueprints/%s.%s" % (name, name))
        cdo = T("bp.get_default_object", blueprint=bp)
        d = {}
        for c in T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.PrimitiveComponent")):
            n = c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")
            b = json.loads(T("obj.get_properties", instance=c, properties=["bodyInstance"]))["bodyInstance"]
            d[n] = (b.get("collisionEnabled"), b.get("collisionProfileName"), b.get("objectType"))
        out[name] = d
    return out
