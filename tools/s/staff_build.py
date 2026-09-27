# BP_Saberstaff: a Darth Maul style double-bladed saber. Child of BP_Lightsaber (IsSith -> red), with a
# mirrored second hilt and a second blade (BladeRoot2/BladeTip2). AJediCharacter keeps BladeRoot2's
# ignition scale/visibility in step with BladeRoot.
J = "/Game/Jedi/Blueprints/"
RED_CORE = "/Game/Jedi/Materials/MI_SaberCore_Red.MI_SaberCore_Red"
RED_GLOW = "/Game/Jedi/Materials/MI_SaberGlow_Red.MI_SaberGlow_Red"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
def V(x, y, z): return {"x": x, "y": y, "z": z}
def R(p, y, r): return {"pitch": p, "yaw": y, "roll": r}
def run():
    out = {}
    parent_bp = ref(J + "BP_Lightsaber.BP_Lightsaber")
    pcdo = T("bp.get_default_object", blueprint=parent_bp)
    core = [c for c in T("actor.get_components", actor=pcdo, component_type=ref("/Script/Engine.StaticMeshComponent")) if "BladeCore" in c["refPath"]][0]
    body = json.loads(T("obj.get_properties", instance=core, properties=["bodyInstance"]))["bodyInstance"]

    if not T("asset.exists", path=J + "BP_Saberstaff"):
        T("bp.create", folder_path="/Game/Jedi/Blueprints", asset_name="BP_Saberstaff", asset_type=ref(J + "BP_Lightsaber.BP_Lightsaber_C"))
    bp = ref(J + "BP_Saberstaff.BP_Saberstaff")
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    cdo = T("bp.get_default_object", blueprint=bp)
    T("obj.set_properties", instance=cdo, values=json.dumps({"IsSith": True}))
    have = [c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "") for c in T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.ActorComponent"))]
    out["had"] = have

    def add(name, cls, props, parent=None):
        if name in have:
            c = [x for x in T("actor.get_components", actor=T("bp.get_default_object", blueprint=bp), component_type=ref("/Script/Engine.ActorComponent")) if x["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "") == name][0]
        else:
            c = T("actor.add_component", owner=bp, component_type=ref(cls), name=name)
        if parent is not None:
            T("actor.set_parent_component", component=c, parent=parent)
        T("obj.set_properties", instance=c, values=json.dumps(props))
        return c

    # Hilt (inherited) spans z -9..+19 around the grip pivot; the mirrored hilt joins it at z=-9.
    add("Hilt2", "/Script/Engine.StaticMeshComponent", {"staticMesh": "/Game/Jedi/Meshes/SM_SaberHilt.SM_SaberHilt",
        "relativeLocation": V(0, 0, -18), "relativeRotation": R(0, 0, 180), "relativeScale3D": V(0.01, 0.01, 0.01)})
    root2 = add("BladeRoot2", "/Script/Engine.SceneComponent", {"relativeLocation": V(0, 0, -37), "relativeRotation": R(0, 0, 180)})
    blade_props = {"staticMesh": CYL, "castShadow": False, "bodyInstance": body, "relativeLocation": V(0, 0, 50), "relativeRotation": R(0, 0, 0)}
    add("BladeCore2", "/Script/Engine.StaticMeshComponent", dict(blade_props, overrideMaterials=[RED_CORE], relativeScale3D=V(0.026, 0.026, 1.0)), root2)
    add("BladeGlow2", "/Script/Engine.StaticMeshComponent", dict(blade_props, overrideMaterials=[RED_GLOW], relativeScale3D=V(0.075, 0.075, 1.03)), root2)
    add("BladeLight2", "/Script/Engine.PointLightComponent", {"intensity": 40, "lightColor": {"r": 1.0, "g": 0.05, "b": 0.02, "a": 1.0},
        "attenuationRadius": 350, "sourceLength": 90, "castShadows": False, "relativeLocation": V(0, 0, 50), "relativeRotation": R(0, 0, 0)}, root2)
    add("BladeTip2", "/Script/Engine.SceneComponent", {"relativeLocation": V(0, 0, 100)}, root2)
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    T("asset.save_assets", asset_paths=[J + "BP_Saberstaff"])
    comps = T("actor.get_components", actor=T("bp.get_default_object", blueprint=bp), component_type=ref("/Script/Engine.SceneComponent"))
    out["comps"] = [c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "") for c in comps]
    return out
