PROPS = {
    "StaticMeshComponent": ["staticMesh", "overrideMaterials", "castShadow"],
    "PointLightComponent": ["intensity", "lightColor", "attenuationRadius", "sourceRadius", "sourceLength", "castShadows"],
    "AudioComponent": ["sound"],
}
def run():
    out = {}
    for name in ["BP_Lightsaber", "BP_LightsaberRed"]:
        bp = ref("/Game/Jedi/Blueprints/%s.%s" % (name, name))
        cdo = T("bp.get_default_object", blueprint=bp)
        comps = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.ActorComponent"))
        d = {}
        for c in comps:
            n = c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")
            cls = T("obj.get_class", instance=c)
            cn = cls["refPath"].split(".")[-1] if isinstance(cls, dict) else str(cls).split(".")[-1]
            ps = PROPS.get(cn, []) + ["relativeLocation", "relativeRotation", "relativeScale3D"]
            props = json.loads(T("obj.get_properties", instance=c, properties=ps))
            par = T("actor.get_parent_component", component=c)
            props["parent"] = par["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "") if isinstance(par, dict) else par
            d[n] = {"cls": cn, "p": props}
        out[name] = d
    return out
