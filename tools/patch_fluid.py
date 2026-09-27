root = r"C:\Users\User\Documents\Unreal Projects\JediArena"
src = root + r"\Source\JediArena"

# ---------------------------------------------------------------- Build.cs + uproject (procedural mesh for the saber trail)
p = src + r"\JediArena.Build.cs"
s = open(p).read()
if "ProceduralMeshComponent" not in s:
    s = s.replace('"UMG", "Niagara"', '"UMG", "Niagara", "ProceduralMeshComponent"')
    open(p, "w").write(s)
import json
p = root + r"\JediArena.uproject"
d = json.load(open(p))
if not any(x["Name"] == "ProceduralMeshComponent" for x in d["Plugins"]):
    d["Plugins"].append({"Name": "ProceduralMeshComponent", "Enabled": True})
    json.dump(d, open(p, "w"), indent="\t")

# ---------------------------------------------------------------- header
p = src + r"\Public\JediCharacter.h"
h = open(p, encoding="utf-8").read()


def hrep(a, b):
    global h
    assert a in h, "header anchor: " + a[:60]
    h = h.replace(a, b, 1)


if "SaberTrail" not in h:
    hrep("class ABlasterBolt;", "class ABlasterBolt;\nclass UProceduralMeshComponent;\nclass UAnimMontage;")
    hrep('''	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float PlayRate = 1.f;''', '''	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float PlayRate = 1.f;

	/** Forward burst at the start of the swing (cm/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float Lunge = 380.f;''')
    hrep('''	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UWidgetComponent> ForceBar;''', '''	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UWidgetComponent> ForceBar;

	/** World-space ribbon following the blade. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UProceduralMeshComponent> SaberTrail;''')
    hrep('''	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> FlipAnim;''', '''	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> FlipAnim;
	/** Optional full-body stance loops layered over the locomotion blueprint (saber-in-hand idle/run). */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> StanceIdleAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> StanceRunAnim;
	/** Ground speed at which the run loop plays at 1x. */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") float StanceRunReferenceSpeed = 650.f;

	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") TObjectPtr<UMaterialInterface> TrailMaterial;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") float TrailLifetime = 0.14f;
	/** Tip speed (cm/s) where the trail starts to appear / reaches full strength. */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") float TrailMinSpeed = 350.f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") float TrailFullSpeed = 1600.f;

	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Movement") float TurnRate = 720.f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Movement") float MaxLeanDegrees = 14.f;''')
    hrep('''	void EnableCapePhysics();''', '''	void EnableCapePhysics();

	// fluid movement
	void FaceDirection(const FVector& Dir);
	void TickLean(float DeltaSeconds);
	void TickStance();
	void TickTrail();

	struct FTrailSample { float Time; FVector Base; FVector Tip; float Strength; };
	TArray<FTrailSample> TrailSamples;
	FQuat BaseMeshRotation = FQuat::Identity;
	FRotator CurrentLean = FRotator::ZeroRotator;
	float LastYaw = 0.f;
	int32 StanceState = 0; // 0 none, 1 idle, 2 run
	UPROPERTY(Transient) TObjectPtr<UAnimMontage> StanceMontage;''')
    open(p, "w", encoding="utf-8").write(h)

# ---------------------------------------------------------------- cpp
p = src + r"\Private\JediCharacter.cpp"
s = open(p, encoding="utf-8").read()


def rep(a, b, count=1):
    global s
    assert a in s, "cpp anchor: " + a[:70]
    s = s.replace(a, b, count)


if "TickStance" not in s:
    rep('#include "JediCharacter.h"\n', '#include "JediCharacter.h"\n\n#include "ProceduralMeshComponent.h"\n#include "Animation/AnimMontage.h"\n')

    # constructor: orient to movement, trail component
    rep('''	bUseControllerRotationYaw = true;''', '''	bUseControllerRotationYaw = false;''')
    rep('''	Move->bOrientRotationToMovement = false;''', '''	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, TurnRate, 0.f);''')
    rep('''	Tags.Add(TEXT("Player"));''', '''	SaberTrail = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("SaberTrail"));
	SaberTrail->SetupAttachment(RootComponent);
	SaberTrail->SetUsingAbsoluteLocation(true);
	SaberTrail->SetUsingAbsoluteRotation(true);
	SaberTrail->SetUsingAbsoluteScale(true);
	SaberTrail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SaberTrail->SetCastShadow(false);
	SaberTrail->bUseAsyncCooking = true;

	Tags.Add(TEXT("Player"));''')

    # BeginPlay: movement tuning + remember mesh rotation
    rep('''	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	SavedFriction''', '''	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.f, TurnRate, 0.f);
	bUseControllerRotationYaw = false;
	BaseMeshRotation = GetMesh()->GetRelativeRotation().Quaternion();
	LastYaw = GetActorRotation().Yaw;
	if (TrailMaterial)
	{
		SaberTrail->SetMaterial(0, TrailMaterial);
	}
	SavedFriction''')

    # cape: no self-collision (bodies overlapping the torso exploded the chain) + damping
    rep('''			M->SetAllBodiesBelowSimulatePhysics(Root, true, true);
			M->SetAllBodiesBelowPhysicsBlendWeight(Root, 1.f, false, true);''', '''			M->SetAllBodiesBelowSimulatePhysics(Root, true, true);
			M->SetAllBodiesBelowPhysicsBlendWeight(Root, 1.f, false, true);
			const int32 RootIndex = M->GetBoneIndex(Root);
			for (int32 B = 0; B < M->GetNumBones(); ++B)
			{
				if (B != RootIndex && !M->BoneIsChildOf(M->GetBoneName(B), Root))
				{
					continue;
				}
				if (FBodyInstance* BI = M->GetBodyInstance(M->GetBoneName(B)))
				{
					BI->SetResponseToAllChannels(ECR_Ignore);
					BI->LinearDamping = 1.0f;
					BI->AngularDamping = 2.5f;
					BI->UpdateDampingProperties();
				}
			}''')

    # any non-stance animation cancels the stance loop
    rep('''	if (UAnimInstance* AI = Anim(); AI && Seq)
	{
		AI->PlaySlotAnimationAsDynamicMontage(Seq, TEXT("DefaultSlot"), BlendIn, BlendOut, Rate, Loops);
	}''', '''	if (UAnimInstance* AI = Anim(); AI && Seq)
	{
		AI->PlaySlotAnimationAsDynamicMontage(Seq, TEXT("DefaultSlot"), BlendIn, BlendOut, Rate, Loops);
		StanceState = 0;
		StanceMontage = nullptr;
	}''')

    # swing: per-swing lunge, snap facing to target or camera
    rep('''	GetCharacterMovement()->MaxWalkSpeed = AttackMoveSpeed;
	FVector LungeDir = AimForwardFlat();''', '''	GetCharacterMovement()->MaxWalkSpeed = AttackMoveSpeed;
	GetCharacterMovement()->bOrientRotationToMovement = false;
	// No target: swing where the player is steering, else where the camera looks.
	FVector LungeDir = GetLastMovementInputVector().IsNearlyZero() ? AimForwardFlat() : GetLastMovementInputVector().GetSafeNormal2D();''')
    rep('''		LungeDir = (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		if (Controller)
		{
			FRotator ControlRot = Controller->GetControlRotation();
			ControlRot.Yaw = LungeDir.Rotation().Yaw;
			Controller->SetControlRotation(ControlRot);
		}
	}
	if (!GetCharacterMovement()->IsFalling())
	{
		LaunchCharacter(LungeDir * AttackLunge, true, false);
	}''', '''		LungeDir = (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
	}
	FaceDirection(LungeDir);
	if (!GetCharacterMovement()->IsFalling())
	{
		LaunchCharacter(LungeDir * Swing.Lunge, true, false);
	}''')
    rep('''	bAttacking = false;
	bQueuedAttack = false;
	bHaveLastBlade = false;
	if (!bBlocking && !bChanneling)''', '''	bAttacking = false;
	bQueuedAttack = false;
	bHaveLastBlade = false;
	if (!bBlocking)
	{
		GetCharacterMovement()->bOrientRotationToMovement = true;
	}
	if (!bBlocking && !bChanneling)''')

    # block keeps its own facing (soft lock), release restores orient-to-movement
    rep('''	bUseControllerRotationYaw = true;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	StopAnims(0.15f);''', '''	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	StopAnims(0.15f);''')
    rep('''	bBlocking = true;
	BlockStartTime = Now();
	bUseControllerRotationYaw = false;''', '''	bBlocking = true;
	BlockStartTime = Now();
	GetCharacterMovement()->bOrientRotationToMovement = false;
	FaceDirection(AimForwardFlat());''')

    # tick hooks
    rep('''	// FOV kick recovery (dash)''', '''	TickLean(DeltaSeconds);
	TickStance();
	TickTrail();

	// FOV kick recovery (dash)''')

    # force powers aim with the camera: face aim direction first
    rep('''	const FVector Loc = GetActorLocation();
	const FVector Fwd = AimForwardFlat();
	PlayAnim(PushAnim''', '''	FaceDirection(AimForwardFlat());
	const FVector Loc = GetActorLocation();
	const FVector Fwd = AimForwardFlat();
	PlayAnim(PushAnim''')

    s += r'''
// ---------------------------------------------------------------- fluid movement

void AJediCharacter::FaceDirection(const FVector& Dir)
{
	const FVector Flat = Dir.GetSafeNormal2D();
	if (!Flat.IsNearlyZero())
	{
		SetActorRotation(Flat.Rotation());
	}
}

void AJediCharacter::TickLean(float DeltaSeconds)
{
	USkeletalMeshComponent* M = GetMesh();
	if (!M || bDead || DeltaSeconds <= 0.f)
	{
		return;
	}
	// Bank into turns and lean forward with speed, like a sprinting duelist.
	const float Yaw = GetActorRotation().Yaw;
	const float YawRate = FMath::FindDeltaAngleDegrees(LastYaw, Yaw) / DeltaSeconds;
	LastYaw = Yaw;
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const float Speed01 = Move->IsMovingOnGround() ? FMath::Clamp(GetVelocity().Size2D() / FMath::Max(WalkSpeed, 1.f), 0.f, 1.3f) : 0.f;

	FRotator Want;
	Want.Pitch = -Speed01 * MaxLeanDegrees * 0.55f;
	Want.Roll = FMath::Clamp(YawRate * 0.02f * Speed01, -MaxLeanDegrees, MaxLeanDegrees);
	Want.Yaw = 0.f;
	if (bAttacking || bBlocking || bDashing)
	{
		Want = FRotator::ZeroRotator;
	}
	CurrentLean = FMath::RInterpTo(CurrentLean, Want, DeltaSeconds, 7.f);
	// Lean is applied in actor space around the feet (mesh origin).
	M->SetRelativeRotation(FQuat(CurrentLean) * BaseMeshRotation);
}

void AJediCharacter::TickStance()
{
	UAnimInstance* AI = Anim();
	if (!AI || bDead || !StanceIdleAnim)
	{
		return;
	}
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const bool bBusy = bAttacking || bBlocking || bChanneling || bDashing;
	int32 Want = 0;
	float Rate = 1.f;
	if (!bBusy && Move->IsMovingOnGround())
	{
		const float Speed = GetVelocity().Size2D();
		if (StanceRunAnim && Speed > WalkSpeed * 0.45f)
		{
			Want = 2;
			Rate = FMath::Clamp(Speed / FMath::Max(StanceRunReferenceSpeed, 1.f), 0.6f, 1.5f);
		}
		else if (Speed < 60.f)
		{
			Want = 1;
		}
		else
		{
			Want = 0; // slow walking: let the locomotion blueprint handle foot placement
		}
	}

	// Another montage took the slot (attack, parry, flip...)? Wait until it's done.
	if (StanceState == 0 && AI->IsAnyMontagePlaying() && !bBusy && Want != 0)
	{
		UAnimMontage* Active = AI->GetCurrentActiveMontage();
		if (Active && Active != StanceMontage && AI->Montage_GetPosition(Active) < Active->GetPlayLength() - 0.2f)
		{
			return;
		}
	}

	if (Want != StanceState)
	{
		if (Want == 0)
		{
			if (StanceMontage && AI->Montage_IsPlaying(StanceMontage))
			{
				AI->Montage_Stop(0.2f, StanceMontage);
			}
			StanceMontage = nullptr;
		}
		else
		{
			UAnimSequenceBase* Seq = Want == 2 ? StanceRunAnim.Get() : StanceIdleAnim.Get();
			StanceMontage = AI->PlaySlotAnimationAsDynamicMontage(Seq, TEXT("DefaultSlot"), 0.22f, 0.22f, Rate, 100000);
		}
		StanceState = Want;
	}
	else if (StanceState == 2 && StanceMontage)
	{
		AI->Montage_SetPlayRate(StanceMontage, Rate);
	}
}

void AJediCharacter::TickTrail()
{
	if (!SaberTrail)
	{
		return;
	}
	const float T = Now();
	FVector Base, Tip;
	if (bSaberOn && !bDead && GetBlade(Base, Tip))
	{
		float Strength = 0.f;
		if (TrailSamples.Num() > 0)
		{
			const FTrailSample& Prev = TrailSamples.Last();
			const float Dt = FMath::Max(T - Prev.Time, 1e-3f);
			const float Speed = FVector::Dist(Tip, Prev.Tip) / Dt;
			Strength = FMath::Clamp((Speed - TrailMinSpeed) / FMath::Max(TrailFullSpeed - TrailMinSpeed, 1.f), 0.f, 1.f);
		}
		TrailSamples.Add({ T, Base, Tip, Strength });
	}
	TrailSamples.RemoveAll([&](const FTrailSample& S) { return T - S.Time > TrailLifetime; });

	float MaxStrength = 0.f;
	for (const FTrailSample& S : TrailSamples)
	{
		MaxStrength = FMath::Max(MaxStrength, S.Strength);
	}
	if (TrailSamples.Num() < 2 || MaxStrength <= 0.01f)
	{
		SaberTrail->ClearAllMeshSections();
		return;
	}

	// Two rows (blade base -> tip) per sample; alpha fades with age and toward the hilt.
	TArray<FVector> Verts;
	TArray<int32> Tris;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FLinearColor> Colors;
	TArray<FProcMeshTangent> Tangents;
	const int32 N = TrailSamples.Num();
	for (int32 i = 0; i < N; ++i)
	{
		const FTrailSample& S = TrailSamples[i];
		const float Age = FMath::Clamp((T - S.Time) / TrailLifetime, 0.f, 1.f);
		const float A = (1.f - Age) * S.Strength;
		const FVector Mid = FMath::Lerp(S.Base, S.Tip, 0.25f); // start a little up the blade
		Verts.Add(Mid);
		Verts.Add(S.Tip);
		Colors.Add(FLinearColor(1.f, 1.f, 1.f, A * 0.35f));
		Colors.Add(FLinearColor(1.f, 1.f, 1.f, A));
		UVs.Add(FVector2D(Age, 0.f));
		UVs.Add(FVector2D(Age, 1.f));
		Normals.Add(FVector::UpVector);
		Normals.Add(FVector::UpVector);
		if (i > 0)
		{
			const int32 P0 = (i - 1) * 2, P1 = P0 + 1, C0 = i * 2, C1 = C0 + 1;
			Tris.Append({ P0, C0, P1, P1, C0, C1 });
		}
	}
	SaberTrail->CreateMeshSection_LinearColor(0, Verts, Tris, Normals, UVs, Colors, Tangents, false);
}
'''
    open(p, "w", encoding="utf-8").write(s)
print("fluid patch applied")
