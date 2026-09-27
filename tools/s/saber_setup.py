B = "/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C:"
def c(n): return ref(B + n + "_GEN_VARIABLE")
def sp(n, **v): return T("obj.set_properties", instance=c(n), values=json.dumps(v))
def run():
    out = {}
    for ch in ["BladeCore", "BladeGlow", "BladeLight", "BladeTip"]:
        T("actor.set_parent_component", component=c(ch), parent=c("BladeRoot"))
    out["parents"] = {n: T("actor.get_parent_component", component=c(n)) for n in ["Hilt","BladeRoot","BladeCore","BladeLight"]}
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    nocol = {"collisionProfileName": "NoCollision"}
    out["hilt"] = sp("Hilt", staticMesh=cyl, relativeLocation={"x":0,"y":0,"z":5}, relativeScale3D={"x":0.034,"y":0.034,"z":0.28},
       overrideMaterials=["/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial"], bodyInstance=nocol)
    out["bladeroot"] = sp("BladeRoot", relativeLocation={"x":0,"y":0,"z":19})
    out["core"] = sp("BladeCore", staticMesh=cyl, relativeLocation={"x":0,"y":0,"z":50}, relativeScale3D={"x":0.026,"y":0.026,"z":1.0},
       overrideMaterials=["/Game/Jedi/Materials/MI_SaberCore_Blue.MI_SaberCore_Blue"], castShadow=False, bodyInstance=nocol)
    out["glow"] = sp("BladeGlow", staticMesh=cyl, relativeLocation={"x":0,"y":0,"z":50}, relativeScale3D={"x":0.075,"y":0.075,"z":1.03},
       overrideMaterials=["/Game/Jedi/Materials/MI_SaberGlow_Blue.MI_SaberGlow_Blue"], castShadow=False, bodyInstance=nocol)
    out["light"] = sp("BladeLight", relativeLocation={"x":0,"y":0,"z":50}, intensity=40.0, attenuationRadius=350.0,
       lightColor={"r":40,"g":110,"b":255,"a":255}, castShadows=False, sourceLength=90.0)
    out["tip"] = sp("BladeTip", relativeLocation={"x":0,"y":0,"z":100})
    out["check"] = T("obj.get_properties", instance=c("BladeCore"), properties=["staticMesh","relativeScale3D","overrideMaterials","bodyInstance"])[:600]
    out["light_check"] = T("obj.get_properties", instance=c("BladeLight"), properties=["intensity","lightColor","intensityUnits","sourceLength"])
    return out
