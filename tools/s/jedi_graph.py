BP = "/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter"

EG = r'''
(event Custom|JediInit
  (Utilities|FlowControl|Delay 0.1)
  (bind s (Game|SpawnActorfromClass "/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber_C" (Math|Transform|MakeTransform (Transformation|GetActorLocation self)) "AlwaysSpawn" "MultiplyWithRoot" self))
  (Variables|Jedi|SetSaber s)
  (Transformation|AttachActorToComponent s (Variables|Character|GetMesh) "hand_r" "SnapToTarget" "SnapToTarget" "KeepWorld" false)
  (Transformation|SetActorRelativeLocation (Variables|Jedi|GetSaber) (Variables|Jedi|GetGripLoc) false false)
  (Transformation|SetActorRelativeRotation (Variables|Jedi|GetSaber) (Variables|Jedi|GetGripRot) false false)
  (Variables|Jedi|SetForcePower (Variables|Jedi|GetMaxForce))
  (Variables|Jedi|SetSaberOn true)
  (Variables|MeleeAttack|Damage|SetMeleeDamage (Variables|Jedi|GetSaberDamage))
  (Class|CharacterMovementComponent|SetJumpZVelocity :JumpZVelocity 820.0 :self (Variables|Character|GetCharacterMovement))
  (Class|CharacterMovementComponent|SetMaxWalkSpeed :MaxWalkSpeed (Variables|Jedi|GetBaseWalkSpeed) :self (Variables|Character|GetCharacterMovement))
  (bind w (Utilities|Casting|CastToUI_LifeBar (UserInterface|GetUserWidgetObject (Variables|Default|GetForceBar))))
  (Variables|Jedi|SetForceBarWidget w)
  (Class|UILifeBar|SetBarColor (Variables|Jedi|GetForceBarWidget) "(R=0.080000,G=0.400000,B=1.000000,A=1.000000)")
  (Class|UILifeBar|SetLifePercentage (Variables|Jedi|GetForceBarWidget) 1.0)
  (Variables|Jedi|SetJediReady true))

(event EventTick (DeltaSeconds)
  (if (Variables|Jedi|GetJediReady)
    (if (Variables|Jedi|GetIsChanneling)
      (if (> (Variables|Jedi|GetForcePower) 0.0)
        (Variables|Jedi|SetForcePower (Math|Float|Max(Float) 0.0 (- (Variables|Jedi|GetForcePower) (* (Variables|Jedi|GetLightningCost) DeltaSeconds))))
        (Variables|Jedi|SetLightningAccum (+ (Variables|Jedi|GetLightningAccum) DeltaSeconds))
        (if (>= (Variables|Jedi|GetLightningAccum) (Variables|Jedi|GetLightningInterval))
          (Variables|Jedi|SetLightningAccum 0.0)
          (CallFunction|LightningZap))
        (else
          (CallFunction|LightningStop)))
      (else
        (Variables|Jedi|SetForcePower (Math|Float|Min(Float) (Variables|Jedi|GetMaxForce) (+ (Variables|Jedi|GetForcePower) (* (Variables|Jedi|GetForceRegen) DeltaSeconds))))))
    (Class|UILifeBar|SetLifePercentage (Variables|Jedi|GetForceBarWidget) (/ (Variables|Jedi|GetForcePower) (Variables|Jedi|GetMaxForce)))))

(event Custom|ForcePush
  (if (and (Variables|Jedi|GetJediReady) (and (>= (Variables|Jedi|GetForcePower) (Variables|Jedi|GetPushCost)) (> (- (Utilities|Time|GetTimeSeconds) (Variables|Jedi|GetLastForceTime)) (Variables|Jedi|GetForceCooldown))))
    (Variables|Jedi|SetForcePower (- (Variables|Jedi|GetForcePower) (Variables|Jedi|GetPushCost)))
    (Variables|Jedi|SetLastForceTime (Utilities|Time|GetTimeSeconds))
    (bind loc (Transformation|GetActorLocation self))
    (bind cf (Math|Vector|GetForwardVector (Pawn|GetControlRotation (Pawn|GetController self))))
    (bind fwd (Math|Vector|Normalize (Math|Vector|MakeVector (.x cf) (.y cf) 0.0)))
    (Transformation|SetActorRotation self (Math|Rotator|MakeRotfromX fwd) false)
    (Animation|Montage|PlaySlotAnimationasDynamicMontage (Components|SkeletalMesh|GetAnimInstance (Variables|Character|GetMesh)) "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02.MM_Attack_02" "DefaultSlot" 0.08 0.25 1.5)
    (Game|SpawnActorfromClass "/Game/Jedi/Blueprints/BP_ForceWave.BP_ForceWave_C" (Math|Transform|MakeTransform (+ loc (* fwd 90.0)) (Math|Rotator|MakeRotfromX fwd)) "AlwaysSpawn" "MultiplyWithRoot" self)
    (Camera|PlayWorldCameraShake "/Game/Variant_Combat/Blueprints/BP_CameraShake_Hit_Enemy.BP_CameraShake_Hit_Enemy_C" loc 500.0 1500.0)
    (bind hits (Actor|GetAllActorsOfClass "/Script/Engine.Character"))
    (for a hits
      (bind aloc (Transformation|GetActorLocation a))
      (bind d (- aloc loc))
      (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector (.x d) (.y d) 0.0)))
      (if (and (!= a self) (and (< (Math|Vector|VectorLength d) (Variables|Jedi|GetPushRange)) (> (Math|Vector|DotProduct dir fwd) 0.3)))
        (Class|Damageable|ApplyDamage(Message) a (Variables|Jedi|GetPushDamage) self aloc (+ (* dir (Variables|Jedi|GetPushImpulse)) (Math|Vector|MakeVector 0.0 0.0 (Variables|Jedi|GetPushLift))))))
    (Utilities|Time|SetGlobalTimeDilation 0.3)
    (Utilities|FlowControl|Delay 0.07)
    (Utilities|Time|SetGlobalTimeDilation 1.0)))

(event Custom|ForcePull
  (if (and (Variables|Jedi|GetJediReady) (and (>= (Variables|Jedi|GetForcePower) (Variables|Jedi|GetPullCost)) (> (- (Utilities|Time|GetTimeSeconds) (Variables|Jedi|GetLastForceTime)) (Variables|Jedi|GetForceCooldown))))
    (bind eye (+ (Transformation|GetActorLocation self) (Math|Vector|MakeVector 0.0 0.0 60.0)))
    (bind cf (Math|Vector|GetForwardVector (Pawn|GetControlRotation (Pawn|GetController self))))
    (Variables|Jedi|SetBestScore 0.9)
    (bind all (Actor|GetAllActorsOfClass "/Script/Engine.Character"))
    (for c all
      (bind to (- (Transformation|GetActorLocation c) eye))
      (bind sc (Math|Vector|DotProduct (Math|Vector|Normalize to) cf))
      (if (and (!= c self) (and (< (Math|Vector|VectorLength to) (Variables|Jedi|GetPullRange)) (> sc (Variables|Jedi|GetBestScore))))
        (Variables|Jedi|SetBestScore sc)
        (Variables|Jedi|SetPullTarget c)))
    (if (> (Variables|Jedi|GetBestScore) 0.9)
      (bind ha (Variables|Jedi|GetPullTarget))
      (Variables|Jedi|SetForcePower (- (Variables|Jedi|GetForcePower) (Variables|Jedi|GetPullCost)))
      (Variables|Jedi|SetLastForceTime (Utilities|Time|GetTimeSeconds))
      (bind aloc (Transformation|GetActorLocation ha))
      (bind d (- (Transformation|GetActorLocation self) aloc))
      (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector (.x d) (.y d) 0.0)))
      (Transformation|SetActorRotation self (Math|Rotator|MakeRotfromX (- (Math|Vector|MakeVector 0.0 0.0 0.0) dir)) false)
      (Animation|Montage|PlaySlotAnimationasDynamicMontage (Components|SkeletalMesh|GetAnimInstance (Variables|Character|GetMesh)) "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_03.MM_Attack_03" "DefaultSlot" 0.08 0.25 1.4)
      (Game|SpawnActorfromClass "/Game/Jedi/Blueprints/BP_ForceWave.BP_ForceWave_C" (Math|Transform|MakeTransform aloc (Math|Rotator|MakeRotfromX dir) (Math|Vector|MakeVector 0.5 0.5 0.5)) "AlwaysSpawn" "MultiplyWithRoot" self)
      (Class|Damageable|ApplyDamage(Message) ha (Variables|Jedi|GetPullDamage) self aloc (+ (* dir (Variables|Jedi|GetPullImpulse)) (Math|Vector|MakeVector 0.0 0.0 (Variables|Jedi|GetPullLift)))))))

(event Custom|LightningStart
  (if (and (Variables|Jedi|GetJediReady) (> (Variables|Jedi|GetForcePower) 10.0))
    (Variables|Jedi|SetIsChanneling true)
    (Variables|Jedi|SetLightningAccum 1.0)
    (Class|CharacterMovementComponent|SetMaxWalkSpeed :MaxWalkSpeed 170.0 :self (Variables|Character|GetCharacterMovement))
    (Animation|Montage|PlaySlotAnimationasDynamicMontage (Components|SkeletalMesh|GetAnimInstance (Variables|Character|GetMesh)) "/Game/Characters/Mannequins/Anims/Pistol/MF_Pistol_Idle_ADS.MF_Pistol_Idle_ADS" "DefaultSlot" 0.15 0.2 1.0 100)))

(event Custom|LightningStop
  (if (Variables|Jedi|GetIsChanneling)
    (Variables|Jedi|SetIsChanneling false)
    (Class|CharacterMovementComponent|SetMaxWalkSpeed :MaxWalkSpeed (Variables|Jedi|GetBaseWalkSpeed) :self (Variables|Character|GetCharacterMovement))
    (Animation|Montage|StopSlotAnimation (Components|SkeletalMesh|GetAnimInstance (Variables|Character|GetMesh)) 0.2 "DefaultSlot")))

(event Custom|LightningZap
  (bind hand (Transformation|GetSocketLocation (Variables|Character|GetMesh) "hand_l"))
  (bind loc (Transformation|GetActorLocation self))
  (bind cf (Math|Vector|GetForwardVector (Pawn|GetControlRotation (Pawn|GetController self))))
  (bind fwd (Math|Vector|Normalize (Math|Vector|MakeVector (.x cf) (.y cf) 0.0)))
  (Transformation|SetActorRotation self (Math|Rotator|MakeRotfromX fwd) false)
  (Variables|Jedi|SetZapHits 0)
  (bind hits (Actor|GetAllActorsOfClass "/Script/Engine.Character"))
  (for a hits
    (bind aloc (Transformation|GetActorLocation a))
    (bind d (- aloc loc))
    (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector (.x d) (.y d) 0.0)))
    (if (and (!= a self) (and (< (Math|Vector|VectorLength d) (Variables|Jedi|GetLightningRange)) (> (Math|Vector|DotProduct dir fwd) 0.55)))
      (Variables|Jedi|SetZapHits (+ (Variables|Jedi|GetZapHits) 1))
      (bind b (Game|SpawnActorfromClass "/Game/Jedi/Blueprints/BP_LightningBolt.BP_LightningBolt_C" (Math|Transform|MakeTransform hand) "AlwaysSpawn" "MultiplyWithRoot" self))
      (Class|BPLightningBolt|Setup b hand (+ aloc (Math|Vector|MakeVector 0.0 0.0 (Math|Random|RandomFloatinRange -30.0 40.0))))
      (Class|Damageable|ApplyDamage(Message) a (Variables|Jedi|GetLightningDamage) self aloc (+ (* dir 140.0) (Math|Vector|MakeVector 0.0 0.0 60.0)))))
  (if (== (Variables|Jedi|GetZapHits) 0)
    (for i (range 2)
      (bind b2 (Game|SpawnActorfromClass "/Game/Jedi/Blueprints/BP_LightningBolt.BP_LightningBolt_C" (Math|Transform|MakeTransform hand) "AlwaysSpawn" "MultiplyWithRoot" self))
      (Class|BPLightningBolt|Setup b2 hand (+ hand (+ (* fwd 450.0) (* (Math|Random|RandomUnitVector) 160.0)))))))

(event Custom|SaberToggle
  (if (Variables|Jedi|GetSaberOn)
    (Class|BPLightsaber|Retract (Variables|Jedi|GetSaber))
    (Variables|Jedi|SetSaberOn false)
    (Variables|MeleeAttack|Damage|SetMeleeDamage (Variables|Jedi|GetFistDamage))
    (else
      (Class|BPLightsaber|Ignite (Variables|Jedi|GetSaber))
      (Variables|Jedi|SetSaberOn true)
      (Variables|MeleeAttack|Damage|SetMeleeDamage (Variables|Jedi|GetSaberDamage)))))

(event EventDestroyed
  (if (Variables|Jedi|GetJediReady)
    (Actor|DestroyActor (Variables|Jedi|GetSaber))))
'''


def run():
    out = {}
    bp = ref(BP)
    have = T("bp.list_variables", blueprint=bp)
    if "BestScore" not in have:
        T("bp.add_variable", blueprint=bp, name="BestScore", type_name="float")
        T("bp.set_variable_category", blueprint=bp, variable_name="BestScore", category="Jedi")
    if "PullTarget" not in have:
        T("bp.add_object_variable", blueprint=bp, name="PullTarget", object_class=ref("/Script/Engine.Actor"))
        T("bp.set_variable_category", blueprint=bp, variable_name="PullTarget", category="Jedi")
        T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    out["write"] = T("bp.write_graph_dsl", graph=ref(BP + ":EventGraph"), code=EG)
    out["compile"] = T("bp.compile_blueprint", blueprint=ref(BP), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_JediCharacter"])
    return out
