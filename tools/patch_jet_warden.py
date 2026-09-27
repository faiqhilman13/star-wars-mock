"""Jet Ghost flight/sound overhaul and aggressive Magna Wardens (staff combos, leaps, ripostes)."""
import sys

SRC = sys.argv[1]
H = SRC + "/Public/HordeEnemy.h"
C = SRC + "/Private/HordeEnemy.cpp"


def patch(p, pairs):
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:120])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


# ------------------------------------------------------------------ header
patch(H, [
    ("class AHordePickup;\n", "class AHordePickup;\nclass UAnimMontage;\nclass UAudioComponent;\n"),
    ("	UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> DeathSounds;\n",
     "	UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> DeathSounds;\n"
     "	/** Magna Warden: the Jedi saberstaff combo set (same grip, so the electrostaff moves like a saberstaff). */\n"
     "	UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequenceBase>> StaffComboAnims;\n"
     "	/** Jet Ghost: full-body loop while flying (stops the ground locomotion from jogging in mid-air). */\n"
     "	UPROPERTY(Transient) TObjectPtr<UAnimSequenceBase> HoverAnim;\n"
     "	UPROPERTY(Transient) TObjectPtr<USoundBase> JetLoopSound;\n"
     "	UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> RocketSounds;\n"
     "	UPROPERTY(Transient) TObjectPtr<UAudioComponent> EngineAudio;\n"),
    ("	enum class EState : uint8 { Approach, Aim, Melee, Stagger, Airborne, Rolling, Deploying, Deployed, Hover, Stunned, Dead };\n",
     "	enum class EState : uint8 { Approach, Aim, Melee, Stagger, Airborne, Rolling, Deploying, Deployed, Hover, Stunned, Dead };\n"
     "	enum class EJetMode : uint8 { Cruise, SwoopIn, SwoopOut, HoverShot };\n"),
    ("	void TickJet(float Dt, ACharacter* Player);\n",
     "	void TickJet(float Dt, ACharacter* Player);\n"
     "	void TickWarden(float Dt, ACharacter* Player);\n"
     "	void StartWardenSwing(int32 Index, bool bFast, bool bChained);\n"
     "	void UpdateJetVisuals(float Dt);\n"
     "	void FireBolt(ACharacter* Player, float Damage, float Speed, float Scale, float Spread, USoundBase* Sound, float Volume, float Pitch);\n"),
    ("	TWeakObjectPtr<AActor> LastHitter;\n",
     "	TWeakObjectPtr<AActor> LastHitter;\n"
     "\n"
     "	// Jet Ghost flight\n"
     "	EJetMode JetMode = EJetMode::Cruise;\n"
     "	float JetModeUntil = 0.f;\n"
     "	FVector SwoopTarget = FVector::ZeroVector;\n"
     "	FVector SwoopExit = FVector::ZeroVector;\n"
     "	int32 SwoopShots = 0;\n"
     "	float NextSwoopShot = 0.f;\n"
     "	bool bRocketFired = false;\n"
     "	float OrbitRadius = 1100.f;\n"
     "	float LeanPitch = 0.f;\n"
     "	float LeanRoll = 0.f;\n"
     "	FVector MeshBaseLoc = FVector::ZeroVector;\n"
     "	FQuat MeshBaseRot = FQuat::Identity;\n"
     "	float SputterUntil = 0.f;\n"
     "\n"
     "	// Magna Warden melee\n"
     "	TWeakObjectPtr<UAnimMontage> SwingMontage;\n"
     "	TArray<float> SwingHits;   // anim-time (s) of each strike in the current swing\n"
     "	int32 NextSwingHit = 0;\n"
     "	int32 ComboStep = 0;\n"
     "	int32 CombosLeft = 0;\n"
     "	float SwingRate = 1.f;\n"
     "	float SwingChainPos = 0.f;\n"
     "	float SwingStart = 0.f;\n"
     "	float SwingTellUntil = 0.f;\n"
     "	bool bSwingCommitted = false;\n"
     "	bool bLeapPending = false;\n"
     "	bool bRiposte = false;\n"
     "	float NextLeapTime = 0.f;\n"),
])

# ------------------------------------------------------------------ cpp
s = open(C, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:140])
    s = s.replace(a, b)


rep('#include "Animation/AnimInstance.h"\n', '#include "Animation/AnimInstance.h"\n#include "Animation/AnimMontage.h"\n#include "Components/AudioComponent.h"\n#include "Sound/SoundAttenuation.h"\n')

rep('''	const TArray<const TCHAR*> WardenParriedLines = { TEXT("Impossible!"), TEXT("Lucky block!") };
''', '''	const TArray<const TCHAR*> WardenParriedLines = { TEXT("Impossible!"), TEXT("Lucky block!") };
	const TArray<const TCHAR*> WardenLeapLines = { TEXT("Hyaaah!"), TEXT("Kneel!"), TEXT("You cannot run!") };
	const TArray<const TCHAR*> JetSwoopLines = { TEXT("Strafing run!"), TEXT("Coming in hot!"), TEXT("Buzzing the Jedi!") };

	/** Strike moments (anim time, s) of AS_Staff_Combo1..4 and when the Warden may chain the next swing. */
	struct FWardenSwing { float Hits[3]; int32 NumHits; float Chain; };
	const FWardenSwing WardenSwings[4] = {
		{ { 0.23f, 0.43f, 0.f }, 2, 0.6f },
		{ { 0.2f, 0.5f, 0.f }, 2, 0.62f },
		{ { 0.27f, 0.5f, 0.f }, 2, 0.66f },
		{ { 0.2f, 0.37f, 0.f }, 2, 0.6f } };
''')

rep('''	FireIntervalMin = 3.0f; FireIntervalMax = 4.6f; BoltDamage = 1.5f; BoltSpeed = 1500.f; BoltScale = 2.2f; Inaccuracy = 3.f;
	LaunchScale = 1.f; KOValue = 4; PickupChance = 0.3f;
}''', '''	FireIntervalMin = 2.6f; FireIntervalMax = 4.2f; BoltDamage = 1.5f; BoltSpeed = 1500.f; BoltScale = 2.2f; Inaccuracy = 3.f;
	LaunchScale = 1.f; KOValue = 4; PickupChance = 0.3f;
	// Some inertia: they bank and drift through turns instead of snapping around.
	GetCharacterMovement()->MaxAcceleration = 1500.f;
	GetCharacterMovement()->BrakingDecelerationFlying = 450.f;
}''')

rep('''	MaxHP = 10.f; MoveSpeed = 420.f; AttackRange = 240.f;''', '''	MaxHP = 10.f; MoveSpeed = 520.f; AttackRange = 270.f;''')

# Warden electrostaff in the Jedi's saber grip
rep('''		// Electrostaff held like a spear, crackling violet at both ends.
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(10.f, 0.f, 0.f), Forward, FVector(0.045f, 0.045f, 1.9f), Staff);
		AddPart(SphereMesh, M, TEXT("hand_r"), FVector(100.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.13f), Arc);
		AddPart(SphereMesh, M, TEXT("hand_r"), FVector(-80.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.13f), Arc);
''', '''		// Electrostaff in the Jedi's saber grip (hand_r, (-7,2,0), (35,0,180); staff along the grip's Z), so the
		// saberstaff combo set swings it exactly like the Jedi's blades. Crackles violet at both ends.
		USceneComponent* Grip = NewObject<USceneComponent>(this);
		Grip->RegisterComponent();
		Grip->AttachToComponent(M, FAttachmentTransformRules::SnapToTargetNotIncludingScale, TEXT("hand_r"));
		Grip->SetRelativeTransform(FTransform(FRotator(35.f, 0.f, 180.f), FVector(-7.f, 2.f, 0.f)));
		auto StaffPart = [&](UStaticMesh* PartMesh, const FVector& Loc, const FVector& Scale, UMaterialInterface* Mat)
		{
			UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
			C->SetStaticMesh(PartMesh);
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->SetGenerateOverlapEvents(false);
			C->RegisterComponent();
			C->AttachToComponent(Grip, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
			C->SetRelativeLocation(Loc);
			C->SetRelativeScale3D(Scale);
			C->SetMaterial(0, Mat);
			Parts.Add(C);
			return C;
		};
		Muzzle = StaffPart(CylinderMesh, FVector(0.f, 0.f, -5.f), FVector(0.045f, 0.045f, 2.1f), Staff);
		StaffPart(SphereMesh, FVector(0.f, 0.f, 100.f), FVector(0.13f), Arc);
		StaffPart(SphereMesh, FVector(0.f, 0.f, -110.f), FVector(0.13f), Arc);
''')

# BeginPlay: new assets + per-type setup
rep('''	switch (Type)
	{
	case EHordeType::Roller:
		State = EState::Rolling;
		break;
	case EHordeType::JetGhost:
		State = EState::Hover;
		HoverAltitude = FMath::FRandRange(420.f, 640.f);
		OrbitAngle = FMath::FRandRange(0.f, 2.f * PI);
		GetCharacterMovement()->SetMovementMode(MOVE_Flying);
		Say(JetLines, 0.3f);
		break;
	case EHordeType::Warden:
		Say(WardenLines, 0.4f);
		break;''', '''	switch (Type)
	{
	case EHordeType::Roller:
		State = EState::Rolling;
		break;
	case EHordeType::JetGhost:
	{
		State = EState::Hover;
		HoverAltitude = FMath::FRandRange(420.f, 640.f);
		OrbitAngle = FMath::FRandRange(0.f, 2.f * PI);
		OrbitRadius = FMath::FRandRange(950.f, 1350.f);
		GetCharacterMovement()->SetMovementMode(MOVE_Flying);
		MeshBaseLoc = GetMesh()->GetRelativeLocation();
		MeshBaseRot = GetMesh()->GetRelativeRotation().Quaternion();
		HoverAnim = LoadObject<UAnimSequenceBase>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle"));
		JetLoopSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Jedi/Audio/Jet/SW_Jetpack_Loop.SW_Jetpack_Loop"));
		for (int32 i = 1; i <= 3; ++i)
		{
			const FString Path = FString::Printf(TEXT("/Game/Jedi/Audio/Jet/SW_Rocket_Launch_%d.SW_Rocket_Launch_%d"), i, i);
			if (USoundBase* Snd = LoadObject<USoundBase>(nullptr, *Path))
			{
				RocketSounds.Add(Snd);
			}
		}
		if (JetLoopSound)
		{
			USoundAttenuation* Att = NewObject<USoundAttenuation>(this);
			Att->Attenuation.bAttenuate = true;
			Att->Attenuation.bSpatialize = true;
			Att->Attenuation.AttenuationShape = EAttenuationShape::Sphere;
			Att->Attenuation.AttenuationShapeExtents = FVector(300.f, 0.f, 0.f);
			Att->Attenuation.FalloffDistance = 2800.f;
			EngineAudio = UGameplayStatics::SpawnSoundAttached(JetLoopSound, GetRootComponent(), NAME_None, FVector::ZeroVector,
				EAttachLocation::KeepRelativeOffset, true, 0.35f, 1.f, FMath::FRandRange(0.f, 1.8f), Att, nullptr, true);
		}
		Say(JetLines, 0.3f);
		break;
	}
	case EHordeType::Warden:
		for (int32 i = 1; i <= 4; ++i)
		{
			const FString Path = FString::Printf(TEXT("/Game/Jedi/Anims/AS_Staff_Combo%d.AS_Staff_Combo%d"), i, i);
			if (UAnimSequenceBase* A = LoadObject<UAnimSequenceBase>(nullptr, *Path))
			{
				StaffComboAnims.Add(A);
			}
		}
		NextLeapTime = T + FMath::FRandRange(1.f, 3.f);
		Say(WardenLines, 0.4f);
		break;''')

# Tick: jets sputter on death, lean/flames/engine while alive, Warden dispatch
rep('''	Super::Tick(DeltaSeconds);
	if (bDead)
	{
		return;
	}''', '''	Super::Tick(DeltaSeconds);
	if (bDead)
	{
		// A dead Jet Ghost's pack coughs a few last flames on the way down.
		for (UStaticMeshComponent* F : JetFlames)
		{
			if (F)
			{
				const bool bOn = Now() < SputterUntil && FMath::FRand() < 0.4f;
				F->SetVisibility(bOn);
				if (bOn)
				{
					FVector S = F->GetRelativeScale3D();
					S.Z = S.X * FMath::FRandRange(0.8f, 2.6f);
					F->SetRelativeScale3D(S);
				}
			}
		}
		return;
	}''')
rep('''	for (UStaticMeshComponent* F : JetFlames)
	{
		if (F)
		{
			FVector S = F->GetRelativeScale3D();
			S.Z = S.X * FMath::FRandRange(2.1f, 3.3f); // flicker the flame length, keep its width
			F->SetRelativeScale3D(S);
		}
	}
''', '''	if (Type == EHordeType::JetGhost)
	{
		UpdateJetVisuals(DeltaSeconds);
	}
''')
rep('''	case EHordeType::JetGhost: TickJet(DeltaSeconds, Player); break;
	default: TickGround(DeltaSeconds, Player); break;''', '''	case EHordeType::JetGhost: TickJet(DeltaSeconds, Player); break;
	case EHordeType::Warden: TickWarden(DeltaSeconds, Player); break;
	default: TickGround(DeltaSeconds, Player); break;''')

# TickGround: the Warden has its own brain now
rep('''	Move->bOrientRotationToMovement = true;
	FVector Want = FVector::ZeroVector;
	if (Type == EHordeType::Warden)
	{
		Want = D > 190.f ? Dir : FVector::CrossProduct(Dir, FVector::UpVector) * StrafeSign * 0.3f;
		if (D < AttackRange && T >= NextMeleeTime && MeleeAnims.Num() > 0)
		{
			AHordeDirector* Director = AHordeDirector::Get(this);
			if (!Director || Director->RequestAttackToken(this, true, 1.8f))
			{
				UAnimSequenceBase* Swing = MeleeAnims[FMath::RandRange(0, MeleeAnims.Num() - 1)];
				if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
				{
					AI->PlaySlotAnimationAsDynamicMontage(Swing, TEXT("DefaultSlot"), 0.1f, 0.2f, 1.1f);
				}
				State = EState::Melee;
				StateUntil = T + Swing->GetPlayLength() / 1.1f;
				MeleeHitTime = T + 0.38f;
				NextMeleeTime = T + FMath::FRandRange(1.5f, 2.6f);
				Move->StopMovementImmediately();
				Move->bOrientRotationToMovement = false;
				return;
			}
			NextMeleeTime = T + 0.5f;
		}
	}
	else
	{
		if (D > PreferredMaxRange)''', '''	Move->bOrientRotationToMovement = true;
	FVector Want = FVector::ZeroVector;
	{
		if (D > PreferredMaxRange)''')

# FireAt -> FireBolt
rep('''void AHordeEnemy::FireAt(ACharacter* Player)
{
	if (!BoltClass || !Player)
	{
		return;
	}''', '''void AHordeEnemy::FireAt(ACharacter* Player)
{
	const float Pitch = Type == EHordeType::Clanker ? 1.18f : Type == EHordeType::Roller ? 1.35f : 1.f;
	FireBolt(Player, BoltDamage, BoltSpeed, BoltScale, Inaccuracy, FireSound, 0.45f, Pitch);
	if (FireAnim && Type != EHordeType::Roller && Type != EHordeType::JetGhost)
	{
		if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
		{
			AI->PlaySlotAnimationAsDynamicMontage(FireAnim, TEXT("DefaultSlot"), 0.05f, 0.15f, 1.2f);
		}
	}
}

void AHordeEnemy::FireBolt(ACharacter* Player, float Damage, float Speed, float Scale, float Spread, USoundBase* Sound, float Volume, float Pitch)
{
	if (!BoltClass || !Player)
	{
		return;
	}''')
rep('''	const FVector Target = Player->GetActorLocation() + FVector(0.f, 0.f, 20.f)
		+ Player->GetVelocity() * (FVector::Dist(From, Player->GetActorLocation()) / FMath::Max(BoltSpeed, 1.f)) * 0.5f;
	FRotator Aim = (Target - From).Rotation();
	Aim.Pitch += FMath::FRandRange(-Inaccuracy, Inaccuracy) * 0.5f;
	Aim.Yaw += FMath::FRandRange(-Inaccuracy, Inaccuracy);
	const FTransform SpawnXf(Aim, From, FVector(BoltScale));
	if (ABlasterBolt* Bolt = GetWorld()->SpawnActorDeferred<ABlasterBolt>(BoltClass, SpawnXf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
	{
		Bolt->Shooter = this;
		Bolt->Damage = BoltDamage;
		Bolt->Speed = BoltSpeed;
		Bolt->ImpactFX = SparkFX;
		UGameplayStatics::FinishSpawningActor(Bolt, SpawnXf);
	}
	if (FireSound)
	{
		const float Pitch = Type == EHordeType::Clanker ? 1.18f : Type == EHordeType::Roller ? 1.35f : Type == EHordeType::JetGhost ? 0.62f : 1.f;
		UGameplayStatics::PlaySoundAtLocation(this, FireSound, From, 0.45f, Pitch * FMath::FRandRange(0.95f, 1.05f));
	}
	if (FireAnim && Type != EHordeType::Roller && Type != EHordeType::JetGhost)
	{
		if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
		{
			AI->PlaySlotAnimationAsDynamicMontage(FireAnim, TEXT("DefaultSlot"), 0.05f, 0.15f, 1.2f);
		}
	}
}''', '''	const FVector Target = Player->GetActorLocation() + FVector(0.f, 0.f, 20.f)
		+ Player->GetVelocity() * (FVector::Dist(From, Player->GetActorLocation()) / FMath::Max(Speed, 1.f)) * 0.5f;
	FRotator Aim = (Target - From).Rotation();
	Aim.Pitch += FMath::FRandRange(-Spread, Spread) * 0.5f;
	Aim.Yaw += FMath::FRandRange(-Spread, Spread);
	const FTransform SpawnXf(Aim, From, FVector(Scale));
	if (ABlasterBolt* Bolt = GetWorld()->SpawnActorDeferred<ABlasterBolt>(BoltClass, SpawnXf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
	{
		Bolt->Shooter = this;
		Bolt->Damage = Damage;
		Bolt->Speed = Speed;
		Bolt->ImpactFX = SparkFX;
		UGameplayStatics::FinishSpawningActor(Bolt, SpawnXf);
	}
	if (Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, From, Volume, Pitch * FMath::FRandRange(0.95f, 1.05f));
	}
}''')

# DoMeleeHit: the staff reaches a little further
rep('''	if (To.Size2D() > 290.f || FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) < 0.25f)''',
    '''	const float Reach = Type == EHordeType::Warden ? 320.f : 290.f;
	if (To.Size2D() > Reach || FMath::Abs(To.Z) > 220.f || FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) < 0.25f)''')

# Jet brain: replace TickJet wholesale
a0 = s.index("void AHordeEnemy::TickJet(float Dt, ACharacter* Player)")
a1 = s.index("// ============================================================================ damage")
s = s[:a0] + r'''void AHordeEnemy::TickJet(float Dt, ACharacter* Player)
{
	const float T = Now();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const FVector Me = GetActorLocation();
	const FVector P = Player->GetActorLocation();

	switch (State)
	{
	case EState::Airborne:
		return;
	case EState::Stunned:
		if (T >= StateUntil)
		{
			State = EState::Hover;
			JetMode = EJetMode::Cruise;
			Move->SetMovementMode(MOVE_Flying);
			LaunchCharacter(FVector(0.f, 0.f, 450.f), false, true);
			Say(JetLines, 0.4f);
		}
		return;
	default:
		break;
	}

	if (Move->MovementMode != MOVE_Flying)
	{
		Move->SetMovementMode(MOVE_Flying);
	}
	State = EState::Hover;
	Move->bOrientRotationToMovement = false;
	if (HoverAnim)
	{
		UAnimInstance* AI = GetMesh()->GetAnimInstance();
		if (AI && !AI->IsAnyMontagePlaying())
		{
			AI->PlaySlotAnimationAsDynamicMontage(HoverAnim, TEXT("DefaultSlot"), 0.3f, 0.3f, 0.8f, 1000);
		}
	}

	const AColosseumArena* Arena = FindArena(this);
	auto Contain = [Arena](FVector G)
	{
		if (Arena)
		{
			const FVector C = Arena->GetArenaCenter();
			FVector Off = G - C;
			Off.Z = 0.f;
			const float MaxR = Arena->GetArenaRadius() - 450.f;
			if (Off.Size() > MaxR)
			{
				const FVector Clamped = C + Off.GetSafeNormal() * MaxR;
				G.X = Clamped.X;
				G.Y = Clamped.Y;
			}
		}
		return G;
	};
	const float CruiseZ = GroundZ + HoverAltitude;
	FVector Goal = Me;
	float Speed = 760.f;
	bool bFaceTravel = false;

	switch (JetMode)
	{
	case EJetMode::Cruise:
	{
		// Loose, weaving orbit: the circling speed, radius and height all drift so no two passes look alike.
		OrbitAngle += Dt * (0.42f + 0.18f * FMath::Sin(T * 0.3f + OrbitRadius)) * StrafeSign;
		const float R = OrbitRadius + 260.f * FMath::Sin(T * 0.45f + OrbitAngle);
		Goal = Contain(P + FVector(FMath::Cos(OrbitAngle), FMath::Sin(OrbitAngle), 0.f) * R);
		Goal.Z = CruiseZ + 90.f * FMath::Sin(T * 0.9f + OrbitAngle * 2.f);
		if (T >= NextStrafeFlip)
		{
			StrafeSign = -StrafeSign;
			NextStrafeFlip = T + FMath::FRandRange(5.f, 9.f);
		}
		if (T >= NextFireTime && FVector::Dist(Me, P) < AttackRange)
		{
			AHordeDirector* Director = AHordeDirector::Get(this);
			if (!Director || Director->RequestAttackToken(this, false, 3.f))
			{
				if (FMath::FRand() < 0.55f)
				{
					// Strafing run: dive past the Jedi on one side, blasting, and climb out the far side.
					const FVector Across = (P - Me).GetSafeNormal2D();
					const FVector Side = FVector::CrossProduct(FVector::UpVector, Across) * (FMath::RandBool() ? 1.f : -1.f);
					SwoopTarget = P + Side * 260.f - Across * 120.f;
					SwoopTarget.Z = GroundZ + 230.f;
					SwoopExit = Contain(P + Across * 1300.f + Side * 450.f);
					SwoopExit.Z = CruiseZ + 120.f;
					SwoopShots = 3;
					NextSwoopShot = T + 0.3f;
					JetMode = EJetMode::SwoopIn;
					JetModeUntil = T + 3.5f;
					Say(JetSwoopLines, 0.35f);
				}
				else
				{
					// Pull up, hang in the air and put a rocket on target.
					JetMode = EJetMode::HoverShot;
					JetModeUntil = T + 1.15f;
					bRocketFired = false;
				}
				NextFireTime = T + FMath::FRandRange(FireIntervalMin, FireIntervalMax);
			}
			else
			{
				NextFireTime = T + 0.7f;
			}
		}
		break;
	}
	case EJetMode::SwoopIn:
	{
		Goal = SwoopTarget;
		Speed = 1250.f;
		bFaceTravel = true;
		const FVector ToP = P - Me;
		if (SwoopShots > 0 && T >= NextSwoopShot && ToP.Size() < 1500.f
			&& FVector::DotProduct(GetVelocity().GetSafeNormal(), ToP.GetSafeNormal()) > 0.3f)
		{
			FireBolt(Player, 0.5f, 2600.f, 1.1f, 4.f, FireSound, 0.4f, 0.92f);
			--SwoopShots;
			NextSwoopShot = T + 0.16f;
		}
		if (FVector::Dist(Me, SwoopTarget) < 240.f || T > JetModeUntil)
		{
			JetMode = EJetMode::SwoopOut;
			JetModeUntil = T + 3.f;
		}
		break;
	}
	case EJetMode::SwoopOut:
		Goal = SwoopExit;
		Speed = 1100.f;
		bFaceTravel = true;
		if (FVector::Dist(Me, SwoopExit) < 320.f || T > JetModeUntil)
		{
			JetMode = EJetMode::Cruise;
			const FVector From = Me - P;
			OrbitAngle = FMath::Atan2(From.Y, From.X);
		}
		break;
	case EJetMode::HoverShot:
		Goal = FVector(Me.X, Me.Y, CruiseZ + 60.f);
		Speed = 220.f;
		if (!bRocketFired && T >= JetModeUntil - 0.55f)
		{
			USoundBase* Launch = RocketSounds.Num() > 0 ? RocketSounds[FMath::RandRange(0, RocketSounds.Num() - 1)].Get() : FireSound.Get();
			FireBolt(Player, BoltDamage, BoltSpeed, BoltScale, Inaccuracy, Launch, 0.7f, 1.f);
			bRocketFired = true;
			LaunchCharacter(-GetActorForwardVector() * 380.f + FVector(0.f, 0.f, 120.f), false, false); // recoil
		}
		if (T >= JetModeUntil)
		{
			JetMode = EJetMode::Cruise;
		}
		break;
	}

	// Keep clear of the other jets.
	FVector Sep = FVector::ZeroVector;
	for (const TWeakObjectPtr<AHordeEnemy>& W : AllEnemies)
	{
		const AHordeEnemy* O = W.Get();
		if (O && O != this && !O->bDead && O->Type == EHordeType::JetGhost)
		{
			const FVector Dl = Me - O->GetActorLocation();
			const float Dist = Dl.Size();
			if (Dist > 1.f && Dist < 380.f)
			{
				Sep += Dl / Dist * (380.f - Dist) / 380.f;
			}
		}
	}
	Move->MaxFlySpeed = Speed;
	const FVector Want = Goal - Me;
	if (Want.Size() > 30.f || !Sep.IsNearlyZero())
	{
		AddMovementInput((Want.GetSafeNormal() + Sep * 1.5f).GetSafeNormal(), FMath::Clamp(Want.Size() / 250.f, 0.25f, 1.f));
	}
	if (bFaceTravel && GetVelocity().Size2D() > 200.f)
	{
		FaceToward(Me + GetVelocity(), Dt, 420.f);
	}
	else
	{
		FaceToward(P, Dt, 300.f);
	}
}

void AHordeEnemy::UpdateJetVisuals(float Dt)
{
	// Lean into the flight: nose down when rushing forward, bank into sideways drift. The mesh pivots
	// around the jetpack (chest height) so the legs swing out behind like a real jetpack flyer.
	const bool bFlying = GetCharacterMovement()->MovementMode == MOVE_Flying;
	const FVector V = GetVelocity();
	const FVector LocalV = GetActorQuat().UnrotateVector(V);
	const float MaxV = 1250.f;
	const float WantPitch = bFlying ? FMath::Clamp(-LocalV.X / MaxV * 40.f, -40.f, 22.f) : 0.f;
	const float WantRoll = bFlying ? FMath::Clamp(LocalV.Y / MaxV * 36.f, -36.f, 36.f) : 0.f;
	LeanPitch = FMath::FInterpTo(LeanPitch, WantPitch, Dt, 3.5f);
	LeanRoll = FMath::FInterpTo(LeanRoll, WantRoll, Dt, 3.5f);
	const FQuat Lean = FRotator(LeanPitch, 0.f, LeanRoll).Quaternion();
	const FVector Pivot(0.f, 0.f, 35.f);
	GetMesh()->SetRelativeLocationAndRotation(Pivot + Lean.RotateVector(MeshBaseLoc - Pivot), Lean * MeshBaseRot);

	// Thrusters burn harder (and louder) with speed and climb.
	const float Thrust = bFlying ? FMath::Clamp(0.55f + V.Size() / MaxV * 0.6f + FMath::Max(V.Z, 0.f) / 600.f, 0.4f, 1.6f) : 0.f;
	for (UStaticMeshComponent* F : JetFlames)
	{
		if (F)
		{
			F->SetVisibility(Thrust > 0.05f);
			FVector S = F->GetRelativeScale3D();
			S.Z = S.X * FMath::FRandRange(2.1f, 3.3f) * Thrust; // flicker the flame length, keep its width
			F->SetRelativeScale3D(S);
		}
	}
	if (EngineAudio)
	{
		EngineAudio->SetVolumeMultiplier(bFlying ? 0.22f + 0.2f * Thrust : 0.08f);
		EngineAudio->SetPitchMultiplier(0.82f + 0.3f * Thrust);
	}
}

void AHordeEnemy::TickWarden(float Dt, ACharacter* Player)
{
	const float T = Now();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const FVector Me = GetActorLocation();
	const FVector P = Player->GetActorLocation();
	FVector To = P - Me;
	To.Z = 0.f;
	const float D = To.Size();
	const FVector Dir = To.GetSafeNormal();

	switch (State)
	{
	case EState::Stagger:
	case EState::Stunned:
		if (T >= StateUntil)
		{
			State = EState::Approach;
			CombosLeft = 0;
			bLeapPending = false;
		}
		return;
	case EState::Airborne:
		return;
	case EState::Melee:
	{
		Move->bOrientRotationToMovement = false;
		// Track the Jedi hard during the wind-up; once the blow is committed it can be sidestepped.
		FaceToward(P, Dt, T < SwingTellUntil ? 720.f : 240.f);
		UAnimInstance* AI = GetMesh()->GetAnimInstance();
		UAnimMontage* Mont = SwingMontage.Get();
		const bool bPlaying = AI && Mont && AI->Montage_IsPlaying(Mont);
		if (T >= SwingTellUntil && !bSwingCommitted)
		{
			bSwingCommitted = true;
			if (bPlaying)
			{
				AI->Montage_SetPlayRate(Mont, SwingRate);
			}
			if (bLeapPending)
			{
				// Leap in: land just in front of where the Jedi is heading, chop on arrival.
				bLeapPending = false;
				const float Flight = 0.42f;
				FVector Target = P + Player->GetVelocity() * 0.35f - Dir * 110.f;
				FVector V = (Target - Me) / Flight;
				V.Z = 0.f;
				V = V.GetClampedToMaxSize(2100.f);
				V.Z = 0.5f * FMath::Abs(GetWorld()->GetGravityZ()) * Move->GravityScale * Flight + 60.f;
				LaunchCharacter(V, true, true);
			}
			else if (D > 140.f && Move->IsMovingOnGround())
			{
				LaunchCharacter(Dir * FMath::Min(D * 1.8f, 620.f), true, false); // step into the blow
			}
		}
		const float Pos = bPlaying ? AI->Montage_GetPosition(Mont) : 99.f;
		while (NextSwingHit < SwingHits.Num() && Pos >= SwingHits[NextSwingHit])
		{
			DoMeleeHit();
			++NextSwingHit;
		}
		if (!bPlaying || Pos >= SwingChainPos || T >= StateUntil)
		{
			if (CombosLeft > 0 && D < 380.f && Move->IsMovingOnGround() && StaffComboAnims.Num() > 0)
			{
				--CombosLeft;
				StartWardenSwing((ComboStep + 1) % StaffComboAnims.Num(), false, true);
				return;
			}
			if (!bPlaying || T >= StateUntil)
			{
				State = EState::Approach;
				Move->bOrientRotationToMovement = true;
				NextMeleeTime = T + FMath::FRandRange(0.4f, 0.9f);
			}
		}
		return;
	}
	default:
		break;
	}

	Move->bOrientRotationToMovement = true;
	Move->MaxWalkSpeed = D > 600.f ? MoveSpeed * 1.5f : MoveSpeed; // sprint to close the gap
	if (T >= NextMeleeTime)
	{
		AHordeDirector* Director = AHordeDirector::Get(this);
		if (D > 420.f && D < 950.f && T >= NextLeapTime && StaffComboAnims.Num() >= 3 && Move->IsMovingOnGround())
		{
			if (!Director || Director->RequestAttackToken(this, true, 2.6f))
			{
				StartWardenSwing(2, false, false);
				bLeapPending = true;
				CombosLeft = FMath::RandRange(0, 1);
				NextLeapTime = T + FMath::FRandRange(4.f, 7.f);
				Say(WardenLeapLines, 0.5f);
				return;
			}
			NextMeleeTime = T + 0.35f;
		}
		else if (D < AttackRange)
		{
			if (!Director || Director->RequestAttackToken(this, true, 3.5f))
			{
				CombosLeft = FMath::RandRange(1, 2);
				StartWardenSwing(bRiposte ? 1 : FMath::RandRange(0, 1), bRiposte, false);
				bRiposte = false;
				return;
			}
			NextMeleeTime = T + 0.35f;
		}
	}
	const FVector Want = D > 160.f ? Dir : FVector::CrossProduct(Dir, FVector::UpVector) * StrafeSign * 0.35f;
	AddMovementInput(SteerAround(Want), 1.f);
}

void AHordeEnemy::StartWardenSwing(int32 Index, bool bFast, bool bChained)
{
	UAnimInstance* AI = GetMesh()->GetAnimInstance();
	UAnimSequenceBase* Anim = nullptr;
	SwingHits.Reset();
	if (StaffComboAnims.IsValidIndex(Index) && StaffComboAnims[Index] && Index < 4)
	{
		Anim = StaffComboAnims[Index];
		const FWardenSwing& W = WardenSwings[Index];
		for (int32 i = 0; i < W.NumHits; ++i)
		{
			SwingHits.Add(W.Hits[i]);
		}
		SwingChainPos = W.Chain;
	}
	else if (MeleeAnims.Num() > 0)
	{
		Anim = MeleeAnims[FMath::RandRange(0, MeleeAnims.Num() - 1)];
		SwingHits.Add(0.42f);
		SwingChainPos = Anim->GetPlayLength();
	}
	if (!Anim || !AI)
	{
		return;
	}
	const float T = Now();
	// A slowed wind-up ("tell") before each opening blow keeps the Warden parryable; chained blows barely pause.
	const float Tell = bChained ? 0.06f : (bFast ? 0.12f : 0.3f);
	const float TellRate = 0.3f;
	ComboStep = Index;
	SwingRate = bFast ? 1.15f : 0.95f;
	SwingMontage = AI->PlaySlotAnimationAsDynamicMontage(Anim, TEXT("DefaultSlot"), 0.1f, 0.25f, TellRate);
	bSwingCommitted = false;
	SwingStart = T;
	SwingTellUntil = T + Tell;
	NextSwingHit = 0;
	State = EState::Melee;
	StateUntil = T + Tell + (Anim->GetPlayLength() - Tell * TellRate) / SwingRate + 0.1f;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->StopMovementImmediately();
	Move->bOrientRotationToMovement = false;
}

''' + s[a1:]

# Warden guard -> riposte
rep('''		Clang();
		FaceToward(GetActorLocation() + FromDir * 100.f, 1.f, 720.f);
		return 0.f;''', '''		Clang();
		FaceToward(GetActorLocation() + FromDir * 100.f, 1.f, 720.f);
		// ...and answers straight back.
		bRiposte = true;
		NextMeleeTime = FMath::Min(NextMeleeTime, T + 0.15f);
		return 0.f;''')

# Death: jets sputter out instead of their flames just vanishing
rep('''	for (UStaticMeshComponent* F : JetFlames)
	{
		if (F)
		{
			F->SetVisibility(false);
		}
	}
	if (ShieldMesh)''', '''	if (Type == EHordeType::JetGhost)
	{
		SputterUntil = Now() + 1.2f;
		if (EngineAudio)
		{
			EngineAudio->FadeOut(0.4f, 0.f); // the death sound carries the pack's last coughs
		}
	}
	if (ShieldMesh)''')

open(C, "w", encoding="utf-8").write(s)
print("patched")
