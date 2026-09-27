def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber")
    cdo = T("bp.get_default_object", blueprint=bp)
    core = [c for c in T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.StaticMeshComponent")) if "BladeCore" in c["refPath"]][0]
    return {"body": T("obj.get_properties", instance=core, properties=["bodyInstance"])[:600],
            "ignite": T("obj.get_properties", instance=cdo, properties=["IgniteOnBeginPlay", "IgniteSpeed"])}
