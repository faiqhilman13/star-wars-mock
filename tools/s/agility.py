def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi")
    cdo = T("bp.get_default_object", blueprint=bp)
    mv = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.CharacterMovementComponent"))[0]
    before = T("obj.get_properties", instance=mv, properties=["maxAcceleration", "brakingDecelerationWalking", "groundFriction"])
    T("obj.set_properties", instance=mv, values=json.dumps({"maxAcceleration": 4200.0, "brakingDecelerationWalking": 3400.0, "groundFriction": 10.0}))
    T("obj.set_properties", instance=cdo, values=json.dumps({"WalkSpeed": 680.0, "TurnRate": 1080.0}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    return {"before": before, "after": T("obj.get_properties", instance=mv, properties=["maxAcceleration", "brakingDecelerationWalking", "groundFriction"]),
            "cdo": T("obj.get_properties", instance=cdo, properties=["WalkSpeed", "TurnRate", "MaxLeanDegrees"])}
