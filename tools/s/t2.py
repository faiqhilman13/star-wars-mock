def run():
    out = {}
    cdo = T("bp.get_default_object", blueprint=ref("/Game/Variant_Combat/Blueprints/BP_CombatCharacter.BP_CombatCharacter"))
    out["vars"] = T("obj.get_properties", instance=cdo, properties=["Default Camera Distance", "Death Camera Distance", "Respawn Time", "Shoulder Offset", "Camera Height", "Pelvis Bone Name", "Danger Trace Distance", "Danger Trace Radius"])
    cap = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.CapsuleComponent"))[0]
    out["cap"] = T("obj.get_properties", instance=cap, properties=["capsuleHalfHeight", "capsuleRadius"])
    out["lava"] = T("bp.read_graph_dsl", graph=ref("/Game/Variant_Combat/Blueprints/Interactables/BP_Combat_LavaFloor.BP_Combat_LavaFloor:EventGraph"))[:1500]
    out["enemy_notify"] = T("bp.read_graph_dsl", graph=ref("/Game/Variant_Combat/Blueprints/AI/BP_CombatEnemy.BP_CombatEnemy:EventGraph"))[5000:9000]
    return out
