D = "/Game/Jedi/Blueprints/"
def mk(name):
    if T("asset.exists", path=D + name): T("asset.delete", path=D + name)
    return T("bp.create", folder_path="/Game/Jedi/Blueprints", asset_name=name, asset_type=ref("/Script/Engine.Actor"))
def comp(bp, cls, name):
    return T("actor.add_component", owner=bp, component_type=ref("/Script/Engine." + cls), name=name)
def nocol(c):
    b = json.loads(T("obj.get_properties", instance=c, properties=["bodyInstance"]))["bodyInstance"]
    b["collisionEnabled"] = "NoCollision"; b["collisionProfileName"] = "NoCollision"
    T("obj.set_properties", instance=c, values=json.dumps({"bodyInstance": b}))
def run():
    out = {}
    # --- Force wave
    w = mk("BP_ForceWave")
    s = comp(w, "StaticMeshComponent", "Wave")
    T("obj.set_properties", instance=s, values=json.dumps({"staticMesh": "/Engine/BasicShapes/Sphere.Sphere",
        "overrideMaterials": ["/Game/Jedi/Materials/M_ForceWave.M_ForceWave"], "castShadow": False, "relativeScale3D": {"x": 0.3, "y": 0.3, "z": 0.3}}))
    nocol(s)
    for n, t in [("Age", "float"), ("Lifetime", "float"), ("StartScale", "float"), ("EndScale", "float"), ("Speed", "float")]:
        T("bp.add_variable", blueprint=w, name=n, type_name=t)
    T("bp.add_object_variable", blueprint=w, name="MID", object_class=ref("/Script/Engine.MaterialInstanceDynamic"))
    T("bp.compile_blueprint", blueprint=w, warnings_as_errors=False)
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=w), values=json.dumps({"Lifetime": 0.4, "StartScale": 0.4, "EndScale": 5.5, "Speed": 900.0}))
    out["wave"] = w
    # --- Lightning bolt: 8 thin cube segments + a flash light
    b = mk("BP_LightningBolt")
    root = comp(b, "SceneComponent", "BoltRoot")
    for i in range(8):
        c = comp(b, "StaticMeshComponent", "Seg%d" % i)
        T("obj.set_properties", instance=c, values=json.dumps({"staticMesh": "/Engine/BasicShapes/Cube.Cube",
            "overrideMaterials": ["/Game/Jedi/Materials/M_ForceLightning.M_ForceLightning"], "castShadow": False,
            "relativeScale3D": {"x": 0.1, "y": 0.025, "z": 0.025}}))
        nocol(c)
    l = comp(b, "PointLightComponent", "Flash")
    T("obj.set_properties", instance=l, values=json.dumps({"intensity": 60.0, "attenuationRadius": 600.0, "lightColor": {"r": 0.55, "g": 0.6, "b": 1.0, "a": 1.0}, "castShadows": False}))
    T("bp.add_variable", blueprint=b, name="Prev", type_name="Vector")
    fg = T("bp.add_function_graph", blueprint=b, graph_name="Setup")
    T("bp.add_function_param", graph=fg, param_name="Start", param_type="Vector", input_param=True)
    T("bp.add_function_param", graph=fg, param_name="End", param_type="Vector", input_param=True)
    T("bp.compile_blueprint", blueprint=b, warnings_as_errors=False)
    out["bolt"] = b
    out["bolt_graphs"] = T("bp.list_graphs", blueprint=b)
    return out
