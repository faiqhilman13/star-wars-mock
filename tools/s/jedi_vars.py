BP = "/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter"
FLOATS = {"ForcePower": 100, "MaxForce": 100, "ForceRegen": 14, "PushCost": 30, "PullCost": 20, "LightningCost": 28,
          "PushRange": 850, "PushImpulse": 1900, "PushLift": 550, "PushDamage": 1,
          "PullRange": 2200, "PullImpulse": 1500, "PullLift": 450, "PullDamage": 0.5,
          "LightningRange": 1100, "LightningDamage": 0.25, "LightningInterval": 0.12, "LightningAccum": 0,
          "LastForceTime": -10, "ForceCooldown": 0.45, "SaberDamage": 2, "FistDamage": 1, "BaseWalkSpeed": 500}
def run():
    bp = ref(BP); out = {}
    have = T("bp.list_variables", blueprint=bp)
    for n in FLOATS:
        if n not in have: T("bp.add_variable", blueprint=bp, name=n, type_name="float")
    for n in ["IsChanneling", "SaberOn"]:
        if n not in have: T("bp.add_variable", blueprint=bp, name=n, type_name="bool")
    if "GripLoc" not in have: T("bp.add_variable", blueprint=bp, name="GripLoc", type_name="Vector")
    if "GripRot" not in have: T("bp.add_variable", blueprint=bp, name="GripRot", type_name="Rotator")
    if "Saber" not in have: T("bp.add_object_variable", blueprint=bp, name="Saber", object_class=ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C"))
    if "ForceBarWidget" not in have: T("bp.add_object_variable", blueprint=bp, name="ForceBarWidget", object_class=ref("/Game/Variant_Combat/UI/UI_LifeBar.UI_LifeBar_C"))
    for n in list(FLOATS) + ["IsChanneling", "SaberOn", "GripLoc", "GripRot", "Saber", "ForceBarWidget"]:
        T("bp.set_variable_category", blueprint=bp, variable_name=n, category="Jedi")
    # Force bar widget component (copy of the inherited LifeBar setup)
    parent_cdo = T("bp.get_default_object", blueprint=ref("/Game/Variant_Combat/Blueprints/BP_CombatCharacter.BP_CombatCharacter"))
    comps = T("actor.get_components", actor=parent_cdo, component_type=ref("/Script/UMG.WidgetComponent"))
    out["lifebar"] = comps
    if comps:
        out["lifebar_props"] = T("obj.get_properties", instance=comps[0], properties=["widgetClass", "relativeLocation", "drawSize", "space", "bDrawAtDesiredSize"])
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    out["vars"] = T("bp.list_variables", blueprint=bp)
    return out
