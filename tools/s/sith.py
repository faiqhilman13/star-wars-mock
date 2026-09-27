J = "/Game/Jedi/Blueprints/"
def child(name, parent):
    if not T("asset.exists", path=J + name):
        T("bp.create", folder_path="/Game/Jedi/Blueprints", asset_name=name, asset_type=ref(parent))
    return ref(J + name + "." + name)
SITH = r'''
(event Custom|SithInit
  (Utilities|FlowControl|Delay 0.1)
  (bind s (Game|SpawnActorfromClass "/Game/Jedi/Blueprints/BP_LightsaberRed.BP_LightsaberRed_C" (Math|Transform|MakeTransform (Transformation|GetActorLocation self)) "AlwaysSpawn" "MultiplyWithRoot" self))
  (Variables|Sith|SetSaber s)
  (Transformation|AttachActorToComponent s (Variables|Character|GetMesh) "hand_r" "SnapToTarget" "SnapToTarget" "KeepWorld" false)
  (Transformation|SetActorRelativeLocation (Variables|Sith|GetSaber) (Variables|Sith|GetGripLoc) false false)
  (Transformation|SetActorRelativeRotation (Variables|Sith|GetSaber) (Variables|Sith|GetGripRot) false false)
  (Variables|Sith|SetSithReady true))

(event EventDestroyed
  (if (Variables|Sith|GetSithReady)
    (Actor|DestroyActor (Variables|Sith|GetSaber))))
'''
def run():
    out = {}
    # 1. respawn as Jedi
    pc = ref("/Game/Variant_Combat/Blueprints/BP_CombatPlayerController.BP_CombatPlayerController")
    node = ref("/Game/Variant_Combat/Blueprints/BP_CombatPlayerController.BP_CombatPlayerController:EventGraph.K2Node_SpawnActorFromClass_0")
    T("bp.set_pin_value", pin={"direction": "EGPD_Input", "index_id": 1, "node": node}, value="/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter_C")
    T("bp.compile_blueprint", blueprint=pc, warnings_as_errors=False)
    # 2. game mode
    gm = child("BP_JediGameMode", "/Game/Variant_Combat/Blueprints/BP_CombatGameMode.BP_CombatGameMode_C")
    T("bp.compile_blueprint", blueprint=gm, warnings_as_errors=False)
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=gm), values=json.dumps({"DefaultPawnClass": "/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter_C"}))
    # 3. red saber
    rs = child("BP_LightsaberRed", "/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C")
    T("bp.compile_blueprint", blueprint=rs, warnings_as_errors=False)
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=rs), values=json.dumps({"IsSith": True}))
    T("bp.compile_blueprint", blueprint=rs, warnings_as_errors=False)
    # 4. Sith enemy
    se = child("BP_SithEnemy", "/Game/Variant_Combat/Blueprints/AI/BP_CombatEnemy.BP_CombatEnemy_C")
    have = T("bp.list_variables", blueprint=se)
    if "Saber" not in have: T("bp.add_object_variable", blueprint=se, name="Saber", object_class=ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C"))
    if "SithReady" not in have: T("bp.add_variable", blueprint=se, name="SithReady", type_name="bool")
    if "GripLoc" not in have: T("bp.add_variable", blueprint=se, name="GripLoc", type_name="Vector")
    if "GripRot" not in have: T("bp.add_variable", blueprint=se, name="GripRot", type_name="Rotator")
    for n in ["Saber", "SithReady", "GripLoc", "GripRot"]:
        T("bp.set_variable_category", blueprint=se, variable_name=n, category="Sith")
    T("bp.add_event", blueprint=se, event_name="SithInit", position={"x": 0, "y": 0})
    T("bp.compile_blueprint", blueprint=se, warnings_as_errors=False)
    T("bp.write_graph_dsl", graph=ref(J + "BP_SithEnemy.BP_SithEnemy:EventGraph"), code=SITH)
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=se), values=json.dumps({"Melee Damage": 1, "Max HP": 5}))
    T("bp.compile_blueprint", blueprint=se, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Variant_Combat/Blueprints/BP_CombatPlayerController", J + "BP_JediGameMode", J + "BP_LightsaberRed", J + "BP_SithEnemy"])
    out["ok"] = True
    return out
