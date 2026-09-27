BP = "/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter"
def run():
    bp = ref(BP); out = {}
    lb = ref("/Game/Variant_Combat/Blueprints/BP_CombatCharacter.BP_CombatCharacter_C:Life Bar_GEN_VARIABLE")
    out["lb_parent"] = T("actor.get_parent_component", component=lb)
    fb = T("actor.add_component", owner=bp, component_type=ref("/Script/UMG.WidgetComponent"), name="ForceBar")
    out["fb"] = fb
    out["fb_parent"] = T("actor.get_parent_component", component=fb)
    T("obj.set_properties", instance=fb, values=json.dumps({"widgetClass": "/Game/Variant_Combat/UI/UI_LifeBar.UI_LifeBar_C",
        "space": "Screen", "drawSize": {"x": 300, "y": 50}, "relativeLocation": {"x": 0, "y": 0, "z": 30}}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    cdo = T("bp.get_default_object", blueprint=bp)
    vals = {"ForcePower": 100, "MaxForce": 100, "ForceRegen": 14, "PushCost": 30, "PullCost": 20, "LightningCost": 28,
          "PushRange": 850, "PushImpulse": 1900, "PushLift": 550, "PushDamage": 1,
          "PullRange": 2200, "PullImpulse": 1500, "PullLift": 450, "PullDamage": 0.5,
          "LightningRange": 1100, "LightningDamage": 0.25, "LightningInterval": 0.12,
          "LastForceTime": -10, "ForceCooldown": 0.45, "SaberDamage": 2, "FistDamage": 1, "BaseWalkSpeed": 500,
          "SaberOn": True, "GripLoc": {"x": 0, "y": 0, "z": 0}, "GripRot": {"pitch": 0, "yaw": 0, "roll": 0},
          "Melee Damage": 2, "Melee Trace Distance": 110, "Melee Trace Radius": 90, "Melee Knockback Impulse": 380, "Melee Launch Impulse": 320,
          "JumpMaxCount": 2, "Max HP": 12}
    out["set"] = T("obj.set_properties", instance=cdo, values=json.dumps(vals))
    out["check"] = T("obj.get_properties", instance=cdo, properties=["PushImpulse", "Melee Damage", "JumpMaxCount", "Tags", "Max HP"])
    return out
