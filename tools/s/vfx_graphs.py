WAVE = r'''
(event EventBeginPlay
  (Variables|Default|SetAge 0.0))

(event EventTick (DeltaSeconds)
  (Variables|Default|SetAge (+ (Variables|Default|GetAge) DeltaSeconds))
  (bind a (/ (Variables|Default|GetAge) (Variables|Default|GetLifetime)))
  (if (>= a 1.0)
    (Actor|DestroyActor self)
    (else
      (bind s (Math|Float|Lerp (Variables|Default|GetStartScale) (Variables|Default|GetEndScale) (Math|Float|Sqrt a)))
      (Transformation|SetRelativeScale3D (Variables|Default|GetWave) (Math|Vector|MakeVector s s (* s 0.75)))
      (Transformation|AddActorWorldOffset :DeltaLocation (* (Transformation|GetActorForwardVector self) (* (Variables|Default|GetSpeed) DeltaSeconds)))
      (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetWave) "Fade" (- 1.0 a)))))
'''
BOLT = r'''
(fn Setup (Start End)
  (Variables|Default|SetPrev Start)
  (bind segs (Actor|GetComponentsByClass self "/Script/Engine.StaticMeshComponent"))
  (for i (range 8)
    (bind base (Math|Vector|Lerp(Vector) Start End (/ (+ i 1) 8.0)))
    (Variables|Default|SetCur (select (< i 7) (+ base (* (Math|Random|RandomUnitVector) (Math|Random|RandomFloatinRange 10.0 45.0))) End))
    (bind prev (Variables|Default|GetPrev))
    (bind cur (Variables|Default|GetCur))
    (bind seg (Utilities|Array|Get(acopy) segs i))
    (Transformation|SetWorldLocationAndRotation seg (* (+ prev cur) 0.5) (Math|Rotator|FindLookatRotation prev cur) false true)
    (Transformation|SetWorldScale3D seg (Math|Vector|MakeVector (/ (Math|Vector|VectorLength (- cur prev)) 100.0) 0.045 0.045))
    (Variables|Default|SetPrev cur))
  (Transformation|SetWorldLocation (Variables|Default|GetFlash) End false true)
  (Actor|SetLifeSpan self 0.08))
'''
def run():
    out = {}
    wb = "/Game/Jedi/Blueprints/BP_ForceWave.BP_ForceWave"
    pass  # out["wave"] = T("bp.write_graph_dsl", graph=ref(wb + ":EventGraph"), code=WAVE)
    bb = "/Game/Jedi/Blueprints/BP_LightningBolt.BP_LightningBolt"
    if "Cur" not in T("bp.list_variables", blueprint=ref(bb)):
        T("bp.add_variable", blueprint=ref(bb), name="Cur", type_name="Vector")
        T("bp.compile_blueprint", blueprint=ref(bb), warnings_as_errors=False)
    out["bolt"] = T("bp.write_graph_dsl", graph=ref(bb + ":Setup"), code=BOLT)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_ForceWave", "/Game/Jedi/Blueprints/BP_LightningBolt"])
    out["read"] = T("bp.read_graph_dsl", graph=ref(bb + ":Setup"))
    return out
