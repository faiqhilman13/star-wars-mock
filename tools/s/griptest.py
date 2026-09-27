P = "/Game/Jedi/Dev/BP_GripTest"
CS = r'''
(fn ConstructionScript ()
  (Transformation|AttachComponentToComponent (Variables|Default|GetSaber) (Variables|Default|GetBody) "hand_r" "SnapToTarget" "SnapToTarget" "KeepWorld" false)
  (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetSaber) (Variables|Default|GetTestLoc) (Variables|Default|GetTestRot) false false))
'''
def run():
    out = {}
    if T("asset.exists", path=P): T("asset.delete", path=P)
    bp = T("bp.create", folder_path="/Game/Jedi/Dev", asset_name="BP_GripTest", asset_type=ref("/Script/Engine.Actor"))
    sk = T("actor.add_component", owner=bp, component_type=ref("/Script/Engine.SkeletalMeshComponent"), name="Body")
    ca = T("actor.add_component", owner=bp, component_type=ref("/Script/Engine.ChildActorComponent"), name="Saber")
    T("actor.set_parent_component", component=ca, parent=sk)
    props = json.loads(T("obj.list_properties", instance=ca)).keys()
    out["ca_props"] = [p for p in props if "ttach" in p or "child" in p.lower()]
    T("obj.set_properties", instance=sk, values=json.dumps({"skeletalMeshAsset": "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple",
        "animationMode": "AnimationSingleNode", "animationData": {"animToPlay": "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle", "bSavedLooping": True, "bSavedPlaying": False, "savedPosition": 0.5, "savedPlayRate": 1.0}}))
    T("obj.set_properties", instance=ca, values=json.dumps({"childActorClass": "/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C",
        "relativeLocation": {"x": -7, "y": 2, "z": 0}, "relativeRotation": {"pitch": 0, "yaw": 0, "roll": 180}}))
    T("bp.add_variable", blueprint=bp, name="TestLoc", type_name="Vector")
    T("bp.add_variable", blueprint=bp, name="TestRot", type_name="Rotator")
    T("bp.set_variable_instance_editable", blueprint=bp, variable_name="TestLoc", instance_editable=True)
    T("bp.set_variable_instance_editable", blueprint=bp, variable_name="TestRot", instance_editable=True)
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("bp.write_graph_dsl", graph=ref(P + ".BP_GripTest:UserConstructionScript"), code=CS)
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=bp), values=json.dumps({"TestLoc": {"x": -7, "y": 2, "z": 0}, "TestRot": {"pitch": 0, "yaw": 0, "roll": 180}}))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    out["ca"] = T("obj.get_properties", instance=ca, properties=["childActorClass"])
    a = T("scene.add_to_scene_from_asset", asset_path=P, name="GripTest", xform=xf((-1000, 400, 100), (0, 90, 0)))
    T("actor.set_label", actor=a, label="GripTest")
    return out
