#include "SandGobbler.h"

#include "ColosseumArena.h"
#include "FizzBarrel.h"
#include "HordeDirector.h"
#include "JediCharacter.h"
#include "JediDamageable.h"

#include "Components/CapsuleComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/MeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/OverlapResult.h"
#include "Engine/Scene.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Math/RotationMatrix.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

namespace GobblerKit
{
	constexpr int32 NumTeeth = 14;
	constexpr int32 NumGums = 22;
	constexpr float RestTilt = 14.f;   // degrees the teeth lean into the mouth at rest
	constexpr float BiteTilt = 66.f;   // ...and when they snap shut
	constexpr float ChompDuration = 0.34f;

	const FLinearColor GumColor(0.75f, 0.2f, 0.38f);
	const FLinearColor ToothColor(0.95f, 0.9f, 0.75f);

	int32 AddBox(UInstancedStaticMeshComponent* ISM, const FVector& Center, const FVector& Size, const FQuat& Rot = FQuat::Identity)
	{
		return ISM ? ISM->AddInstance(FArenaKit::FitBox(ISM->GetStaticMesh(), Center, Size, Rot), false) : INDEX_NONE;
	}

	UStaticMeshComponent* MakeDisc(UStaticMeshComponent* Disc, USceneComponent* Parent, UStaticMesh* Mesh, UMaterialInterface* Material)
	{
		Disc->SetupAttachment(Parent);
		Disc->SetStaticMesh(Mesh);
		if (Material)
		{
			Disc->SetMaterial(0, Material);
		}
		Disc->SetCastShadow(false);
		FArenaKit::NoCollision(Disc);
		return Disc;
	}

	void SetupISM(UInstancedStaticMeshComponent* ISM, USceneComponent* Parent, UStaticMesh* Mesh, UMaterialInterface* Material, bool bShadows)
	{
		ISM->SetupAttachment(Parent);
		ISM->SetStaticMesh(Mesh);
		if (Material)
		{
			ISM->SetMaterial(0, Material);
		}
		ISM->SetCastShadow(bShadows);
		FArenaKit::NoCollision(ISM);
	}
}

ASandGobbler::ASandGobbler()
{
	PrimaryActorTick.bCanEverTick = true;

	PitRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PitRoot"));
	PitRoot->SetMobility(EComponentMobility::Movable);
	RootComponent = PitRoot;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ChamferFinder(TEXT("/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> SurfaceFinder(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> LavaFinder(TEXT("/Game/Jedi/Materials/MI_Lava.MI_Lava"));
	static ConstructorHelpers::FObjectFinder<USoundBase> ChompFinder(TEXT("/Game/Jedi/Audio/Licensed/SW_Saber_Hit_Rec1.SW_Saber_Hit_Rec1"));
	static ConstructorHelpers::FObjectFinder<USoundBase> BurpFinder(TEXT("/Game/Jedi/Audio/Licensed/SW_Remote_Explode.SW_Remote_Explode"));
	static ConstructorHelpers::FObjectFinder<USoundBase> SpitFinder(TEXT("/Game/Jedi/Audio/SW_Force_Push.SW_Force_Push"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> SparkFinder(TEXT("/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"));

	ConeMesh = ConeFinder.Object;
	CylinderMesh = CylinderFinder.Object;
	SphereMesh = SphereFinder.Object;
	ChamferCubeMesh = ChamferFinder.Object;
	SurfaceMaterial = SurfaceFinder.Object;
	BellyMaterial = LavaFinder.Object;
	ChompSound = ChompFinder.Object;
	BurpSound = BurpFinder.Object;
	SpitSound = SpitFinder.Object;
	SpitFX = SparkFinder.Object;

	UStaticMesh* GumMesh = ChamferCubeMesh ? ChamferCubeMesh.Get() : CylinderMesh.Get();

	Throat = GobblerKit::MakeDisc(CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Throat")), PitRoot, CylinderMesh, SurfaceMaterial);
	Gullet = GobblerKit::MakeDisc(CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Gullet")), PitRoot, CylinderMesh, SurfaceMaterial);
	Belly = GobblerKit::MakeDisc(CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Belly")), PitRoot, CylinderMesh, BellyMaterial ? BellyMaterial.Get() : SurfaceMaterial.Get());

	Gums = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Gums"));
	GobblerKit::SetupISM(Gums, PitRoot, GumMesh, SurfaceMaterial, true);
	Teeth = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Teeth"));
	GobblerKit::SetupISM(Teeth, PitRoot, ConeMesh, SurfaceMaterial, true);
	EyeStalks = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("EyeStalks"));
	GobblerKit::SetupISM(EyeStalks, PitRoot, CylinderMesh, SurfaceMaterial, true);
	Eyeballs = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Eyeballs"));
	GobblerKit::SetupISM(Eyeballs, PitRoot, SphereMesh, SurfaceMaterial, true);
	Pupils = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Pupils"));
	GobblerKit::SetupISM(Pupils, PitRoot, SphereMesh, SurfaceMaterial, false);

	BellyLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("BellyLight"));
	BellyLight->SetupAttachment(PitRoot);
	BellyLight->SetRelativeLocation(FVector(0.f, 0.f, 60.f));
	BellyLight->IntensityUnits = ELightUnits::Candelas;
	BellyLight->SetIntensity(BellyLightIntensity);
	BellyLight->SetLightColor(FLinearColor(1.f, 0.35f, 0.1f));
	BellyLight->SetAttenuationRadius(900.f);
	BellyLight->SetCastShadows(false);
}

float ASandGobbler::TimeNow() const
{
	const UWorld* World = GetWorld();
	return World ? static_cast<float>(World->GetTimeSeconds()) : 0.f;
}

void ASandGobbler::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	BuildLayout();
}

void ASandGobbler::BeginPlay()
{
	Super::BeginPlay();
	BuildLayout();
	ApplyRuntimeMaterials();
	const float Now = TimeNow();
	NextIdleChomp = Now + FMath::FRandRange(IdleChompMin, IdleChompMax);
	NextBlink = Now + 1.5f;
}

// ============================================================================ layout

void ASandGobbler::BuildLayout()
{
	const float Mouth = FMath::Max(PitRadius, 100.f);

	// Stacked discs a few cm above the floor: brown rim -> black gullet -> glowing belly. The floor itself stays solid.
	if (Throat)
	{
		Throat->SetRelativeTransform(FArenaKit::FitBox(Throat->GetStaticMesh(), FVector(0.f, 0.f, 1.f), FVector(2.f * (Mouth + 20.f), 2.f * (Mouth + 20.f), 2.f)));
	}
	if (Gullet)
	{
		Gullet->SetRelativeTransform(FArenaKit::FitBox(Gullet->GetStaticMesh(), FVector(0.f, 0.f, 1.6f), FVector(1.4f * Mouth, 1.4f * Mouth, 2.f)));
	}
	if (Belly)
	{
		Belly->SetRelativeTransform(FArenaKit::FitBox(Belly->GetStaticMesh(), FVector(0.f, 0.f, 2.2f), FVector(0.6f * Mouth, 0.6f * Mouth, 2.f)));
		BellyBaseScale = Belly->GetRelativeScale3D();
	}

	if (Gums)
	{
		Gums->ClearInstances();
		const float GumChord = 2.f * (Mouth + 45.f) * FMath::Sin(PI / GobblerKit::NumGums) * 1.18f;
		for (int32 i = 0; i < GobblerKit::NumGums; ++i)
		{
			const float A = (i + 0.5f) * 360.f / GobblerKit::NumGums;
			float SinA = 0.f;
			float CosA = 1.f;
			FMath::SinCos(&SinA, &CosA, FMath::DegreesToRadians(A));
			const FVector At(CosA * (Mouth + 45.f), SinA * (Mouth + 45.f), 16.f + ((i % 2) ? 3.f : 0.f));
			GobblerKit::AddBox(Gums, At, FVector(110.f, GumChord, 38.f), FRotator(8.f, A, 0.f).Quaternion());
		}
	}

	ToothLayout.Reset();
	for (int32 i = 0; i < GobblerKit::NumTeeth; ++i)
	{
		FTooth& Tooth = ToothLayout.AddDefaulted_GetRef();
		const bool bBig = (i % 2) == 0;
		Tooth.Angle = i * 360.f / GobblerKit::NumTeeth + (bBig ? 0.f : 4.f);
		Tooth.Height = (bBig ? 175.f : 120.f) * FMath::Clamp(Mouth / 420.f, 0.6f, 1.6f);
		Tooth.Diameter = (bBig ? 85.f : 62.f) * FMath::Clamp(Mouth / 420.f, 0.6f, 1.6f);
	}
	if (Teeth)
	{
		Teeth->ClearInstances();
		for (int32 i = 0; i < ToothLayout.Num(); ++i)
		{
			Teeth->AddInstance(ToothTransform(i, GobblerKit::RestTilt), false);
		}
	}
	bTeethAtRest = true;

	// Two eye stalks poking out of the sand on the far side of the mouth.
	EyeLocal[0] = FVector(-(Mouth + 150.f), -115.f, 200.f);
	EyeLocal[1] = FVector(-(Mouth + 150.f), 115.f, 200.f);
	if (EyeStalks && Eyeballs && Pupils)
	{
		EyeStalks->ClearInstances();
		Eyeballs->ClearInstances();
		Pupils->ClearInstances();
		for (int32 e = 0; e < 2; ++e)
		{
			const FVector Eye = EyeLocal[e];
			GobblerKit::AddBox(EyeStalks, FVector(Eye.X, Eye.Y, Eye.Z * 0.5f), FVector(34.f, 34.f, Eye.Z));
			GobblerKit::AddBox(Eyeballs, Eye, FVector(80.f, 80.f, 80.f));
			GobblerKit::AddBox(Pupils, Eye + FVector(30.f, 0.f, 0.f), FVector(30.f, 30.f, 30.f));
		}
	}
	if (BellyLight)
	{
		BellyLight->SetAttenuationRadius(Mouth * 2.2f);
	}
}

void ASandGobbler::ApplyRuntimeMaterials()
{
	UMaterialInterface* Surf = SurfaceMaterial;
	auto Paint = [Surf](UMeshComponent* Target, const FLinearColor& Base, const FLinearColor& Emissive, float Rough, float Metal)
	{
		if (Target && Surf)
		{
			if (UMaterialInstanceDynamic* MID = FArenaKit::SharedSurfaceMID(Surf, Base, Emissive, Rough, Metal))
			{
				Target->SetMaterial(0, MID);
			}
		}
	};
	Paint(Throat, FLinearColor(0.05f, 0.025f, 0.012f), FLinearColor::Black, 1.f, 0.f);
	Paint(Gullet, FLinearColor(0.004f, 0.002f, 0.003f), FLinearColor::Black, 1.f, 0.f);
	if (!BellyMaterial)
	{
		Paint(Belly, FLinearColor(0.5f, 0.05f, 0.02f), FLinearColor(3.f, 0.4f, 0.1f), 0.6f, 0.f);
	}
	Paint(Gums, GobblerKit::GumColor, FLinearColor(0.05f, 0.f, 0.02f), 0.3f, 0.f);
	Paint(Teeth, GobblerKit::ToothColor, FLinearColor::Black, 0.35f, 0.f);
	Paint(EyeStalks, GobblerKit::GumColor, FLinearColor::Black, 0.4f, 0.f);
	Paint(Eyeballs, FLinearColor(0.95f, 0.95f, 0.9f), FLinearColor(0.05f, 0.05f, 0.05f), 0.2f, 0.f);
	Paint(Pupils, FLinearColor(0.01f, 0.01f, 0.01f), FLinearColor(0.25f, 0.03f, 0.f), 0.1f, 0.f);
}

FTransform ASandGobbler::ToothTransform(int32 Index, float TiltDegrees) const
{
	const FTooth& Tooth = ToothLayout[Index];
	float SinA = 0.f;
	float CosA = 1.f;
	FMath::SinCos(&SinA, &CosA, FMath::DegreesToRadians(Tooth.Angle));
	const FVector Radial(CosA, SinA, 0.f);
	const float Tilt = FMath::DegreesToRadians(TiltDegrees);
	// Lean the tooth axis from vertical toward the middle of the mouth.
	const FVector Axis = (FVector::UpVector * FMath::Cos(Tilt) - Radial * FMath::Sin(Tilt)).GetSafeNormal();
	const FVector Foot = Radial * (FMath::Max(PitRadius, 100.f) - 12.f) + FVector(0.f, 0.f, 26.f);
	const FQuat Q = FRotationMatrix::MakeFromZX(Axis, Radial).ToQuat();
	return FArenaKit::FitBox(Teeth ? Teeth->GetStaticMesh() : nullptr, Foot + Axis * (Tooth.Height * 0.5f), FVector(Tooth.Diameter, Tooth.Diameter, Tooth.Height), Q);
}

void ASandGobbler::UpdateTeeth(float Bite01)
{
	if (!Teeth)
	{
		return;
	}
	const int32 Count = FMath::Min(ToothLayout.Num(), Teeth->GetInstanceCount());
	for (int32 i = 0; i < Count; ++i)
	{
		// Big teeth bite a touch harder than the small ones.
		const float Tilt = FMath::Lerp(GobblerKit::RestTilt, GobblerKit::BiteTilt - ((i % 2) ? 8.f : 0.f), Bite01);
		Teeth->UpdateInstanceTransform(i, ToothTransform(i, Tilt), false, false, false);
	}
}

// ============================================================================ tick

void ASandGobbler::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float Now = TimeNow();

	ScanAccum += DeltaSeconds;
	if (ScanAccum >= ScanInterval)
	{
		ScanAccum = 0.f;
		Scan();
	}
	UpdateSwallows(Now);

	// Teeth: snap shut fast, open lazily.
	const float ChompAge = Now - ChompStart;
	if (ChompAge >= 0.f && ChompAge < GobblerKit::ChompDuration)
	{
		const float Tn = ChompAge / GobblerKit::ChompDuration;
		const float Bite = Tn < 0.3f ? FMath::Sin(Tn / 0.3f * HALF_PI) : 1.f - FMath::SmoothStep(0.3f, 1.f, Tn);
		UpdateTeeth(Bite);
		bTeethAtRest = false;
	}
	else if (!bTeethAtRest)
	{
		UpdateTeeth(0.f);
		bTeethAtRest = true;
	}
	if (Now >= NextIdleChomp)
	{
		Chomp(false);
		NextIdleChomp = Now + FMath::FRandRange(IdleChompMin, FMath::Max(IdleChompMin, IdleChompMax));
	}

	UpdateEyes(Now);

	// The belly breathes (and flares after a meal).
	const float Flare = Now < BellyFlareUntil ? 0.35f : 0.f;
	const float Pulse = 1.f + 0.08f * FMath::Sin(Now * 2.6f) + Flare;
	if (Belly)
	{
		Belly->SetRelativeScale3D(FVector(BellyBaseScale.X * Pulse, BellyBaseScale.Y * Pulse, BellyBaseScale.Z));
	}
	if (BellyLight)
	{
		BellyLight->SetIntensity(BellyLightIntensity * (0.8f + 0.2f * FMath::Sin(Now * 2.6f) + Flare * 6.f));
	}
}

void ASandGobbler::UpdateEyes(float Now)
{
	if (!EyeStalks || !Eyeballs || !Pupils || Eyeballs->GetInstanceCount() < 2 || Pupils->GetInstanceCount() < 2 || EyeStalks->GetInstanceCount() < 2)
	{
		return;
	}
	if (Now >= NextBlink)
	{
		BlinkUntil = Now + 0.12f;
		NextBlink = Now + FMath::FRandRange(2.f, 5.f);
	}
	const bool bBlink = Now < BlinkUntil;
	const bool bHappy = Now < HappyUntil;
	const ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const FTransform ActorXf = GetActorTransform();
	for (int32 e = 0; e < 2; ++e)
	{
		const FVector Eye = EyeLocal[e] + FVector(0.f, FMath::Sin(Now * 1.3f + e * 2.1f) * 10.f, FMath::Sin(Now * 2.f + e) * 6.f);
		const FVector StalkFoot(EyeLocal[e].X, EyeLocal[e].Y, 0.f);
		const FVector StalkSpan = Eye - StalkFoot;
		EyeStalks->UpdateInstanceTransform(e, FArenaKit::FitBox(EyeStalks->GetStaticMesh(), (StalkFoot + Eye) * 0.5f, FVector(34.f, 34.f, StalkSpan.Size()),
			FRotationMatrix::MakeFromZ(StalkSpan.GetSafeNormal()).ToQuat()), false, false, false);

		// Squint happily after a meal, blink now and then.
		const float Lid = bBlink ? 0.12f : (bHappy ? 0.45f : 1.f);
		Eyeballs->UpdateInstanceTransform(e, FArenaKit::FitBox(Eyeballs->GetStaticMesh(), Eye, FVector(80.f, 80.f, 80.f * Lid)), false, false, false);

		FVector Look = FVector::ForwardVector;
		if (Player)
		{
			Look = ActorXf.InverseTransformVectorNoScale(Player->GetActorLocation() - ActorXf.TransformPosition(Eye)).GetSafeNormal();
		}
		const float PupilSize = bBlink ? 1.f : 30.f;
		Pupils->UpdateInstanceTransform(e, FArenaKit::FitBox(Pupils->GetStaticMesh(), Eye + Look * 30.f, FVector(PupilSize, PupilSize, PupilSize * (bHappy ? 0.5f : 1.f))), false, false, false);
	}
}

// ============================================================================ eating

bool ASandGobbler::IsSwallowing(const AActor* Actor) const
{
	for (const FSwallow& Swallow : Swallows)
	{
		if (Swallow.Actor.Get() == Actor)
		{
			return true;
		}
	}
	return false;
}

void ASandGobbler::Scan()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	const FVector Center = GetActorLocation();
	TArray<FOverlapResult> Overlaps;
	FCollisionObjectQueryParams ObjectParams;
	ObjectParams.AddObjectTypesToQuery(ECC_Pawn);
	ObjectParams.AddObjectTypesToQuery(ECC_PhysicsBody);
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(SandGobblerScan), false, this);
	World->OverlapMultiByObjectType(Overlaps, Center + FVector(0.f, 0.f, 150.f), FQuat::Identity, ObjectParams,
		FCollisionShape::MakeCapsule(PitRadius + 60.f, 260.f), QueryParams);

	TArray<AActor*, TInlineAllocator<16>> Seen;
	for (const FOverlapResult& Overlap : Overlaps)
	{
		AActor* Victim = Overlap.GetActor();
		if (!IsValid(Victim) || Victim == this || Seen.Contains(Victim))
		{
			continue;
		}
		Seen.Add(Victim);
		const FVector P = Victim->GetActorLocation();
		if (FVector::DistSquared2D(P, Center) > FMath::Square(PitRadius) || P.Z - Center.Z > MaxBiteHeight || P.Z < Center.Z - 400.f)
		{
			continue;
		}
		HandleVictim(Victim);
	}

	if (SpitCooldown.Num() > 32)
	{
		const float Now = TimeNow();
		for (auto It = SpitCooldown.CreateIterator(); It; ++It)
		{
			if (!It.Key().IsValid() || It.Value() < Now)
			{
				It.RemoveCurrent();
			}
		}
	}
}

void ASandGobbler::HandleVictim(AActor* Victim)
{
	if (!IsValid(Victim) || IsSwallowing(Victim))
	{
		return;
	}
	ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	ACharacter* AsCharacter = Cast<ACharacter>(Victim);

	// The Jedi is not on the menu.
	if (Victim == Player || Victim->IsA(AJediCharacter::StaticClass()))
	{
		if (AsCharacter)
		{
			SpitOut(AsCharacter, true);
		}
		return;
	}
	if (AFizzBarrel* Barrel = Cast<AFizzBarrel>(Victim))
	{
		if (Barrel->IsJediTargetAlive())
		{
			FizzyBurp(Barrel);
		}
		return;
	}

	IJediDamageable* Damageable = Cast<IJediDamageable>(Victim);
	if (!AsCharacter && !Damageable)
	{
		return; // loose physics junk is not food
	}
	if (Damageable && !Damageable->IsJediTargetAlive())
	{
		return;
	}
	if (!Damageable && AsCharacter->GetCharacterMovement() && AsCharacter->GetCharacterMovement()->MovementMode == MOVE_None)
	{
		return; // already dead / disabled template enemy
	}

	AHordeDirector* Director = AHordeDirector::Get(this);
	const bool bBoss = Director && Director->GetBoss() == Victim;
	const float VictimRadius = (AsCharacter && AsCharacter->GetCapsuleComponent()) ? AsCharacter->GetCapsuleComponent()->GetScaledCapsuleRadius() : 50.f;
	if (bBoss || VictimRadius > MaxSwallowRadius)
	{
		// Too big to swallow: gag, spit it back out with a nip.
		if (AsCharacter)
		{
			SpitOut(AsCharacter, false);
		}
		if (Damageable)
		{
			Damageable->ReceiveJediHit(2.f, Player, Victim->GetActorLocation(), FVector::ZeroVector, EJediHitKind::Environment);
		}
		return;
	}

	const float Now = TimeNow();
	const FVector Loc = Victim->GetActorLocation();
	if (Damageable)
	{
		// The enemy handles its own death and KO report.
		Damageable->ReceiveJediHit(99999.f, Player, Loc, FVector::ZeroVector, EJediHitKind::Environment);
		// Shields can shrug off even this; it's going down the hatch anyway, so make sure it still counts.
		if (IsValid(Victim) && Damageable->IsJediTargetAlive() && Director)
		{
			Director->NotifyKO(Victim, Player, 1);
		}
	}
	else
	{
		AJediCharacter::DamageActor(Victim, 99999.f, Player, Loc, FVector::ZeroVector, EJediHitKind::Environment);
	}
	if (IsValid(Victim) && !Victim->IsActorBeingDestroyed())
	{
		BeginSwallow(Victim, Now);
	}

	Chomp(true);
	GetWorldTimerManager().SetTimer(BurpTimer, this, &ASandGobbler::Burp, 0.55f, false);
	HappyUntil = Now + 1.3f;
	BellyFlareUntil = Now + 0.8f;
	if (Director)
	{
		Director->AddHype(HypePerGobble);
	}
	if (AColosseumArena* Arena = Cast<AColosseumArena>(GetOwner()))
	{
		Arena->CrowdCheer(0.5f);
	}
	RecentGobbles.Add(Now);
	RecentGobbles.RemoveAll([Now](float Stamp) { return Now - Stamp > 2.5f; });
	if (RecentGobbles.Num() >= 3)
	{
		Say(TEXT("ALL YOU CAN EAT!"), LastStreakAnnounce, FLinearColor(1.f, 0.5f, 0.15f));
	}
	else
	{
		Say(TEXT("GOBBLED!"), LastGobbleAnnounce, FLinearColor(1.f, 0.7f, 0.2f));
	}
}

void ASandGobbler::BeginSwallow(AActor* Victim, float Now)
{
	FSwallow& Swallow = Swallows.AddDefaulted_GetRef();
	Swallow.Actor = Victim;
	Swallow.StartLocation = Victim->GetActorLocation();
	Swallow.StartScale = Victim->GetActorScale3D();
	Swallow.StartYaw = static_cast<float>(Victim->GetActorRotation().Yaw);
	Swallow.Start = Now;
	Swallow.Spin = FMath::FRandRange(-540.f, 540.f);

	Victim->SetActorEnableCollision(false);
	if (ACharacter* AsCharacter = Cast<ACharacter>(Victim))
	{
		if (UCharacterMovementComponent* Move = AsCharacter->GetCharacterMovement())
		{
			Move->StopMovementImmediately();
			Move->DisableMovement();
		}
	}
}

void ASandGobbler::UpdateSwallows(float Now)
{
	const FVector Center = GetActorLocation();
	for (int32 i = Swallows.Num() - 1; i >= 0; --i)
	{
		const FSwallow& Swallow = Swallows[i];
		AActor* Victim = Swallow.Actor.Get();
		if (!IsValid(Victim) || Victim->IsActorBeingDestroyed())
		{
			Swallows.RemoveAtSwap(i, EAllowShrinking::No);
			continue;
		}
		const float Tn = (Now - Swallow.Start) / FMath::Max(SwallowTime, 0.1f);
		if (Tn >= 1.f)
		{
			Swallows.RemoveAtSwap(i, EAllowShrinking::No);
			Victim->Destroy();
			continue;
		}
		// Slurp toward the middle of the mouth, then down through the sand, shrinking and spinning.
		const float Pull = FMath::SmoothStep(0.f, 0.6f, Tn) * 0.85f;
		const float Sink = Tn * Tn;
		FVector NewLoc = FMath::Lerp(Swallow.StartLocation, FVector(Center.X, Center.Y, Swallow.StartLocation.Z), Pull);
		NewLoc.Z = FMath::Lerp(Swallow.StartLocation.Z, Center.Z - 260.0, static_cast<double>(Sink));
		Victim->SetActorLocationAndRotation(NewLoc, FRotator(0.f, Swallow.StartYaw + Swallow.Spin * Tn, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
		Victim->SetActorScale3D(Swallow.StartScale * FMath::Lerp(1.f, 0.3f, Sink));
	}
}

void ASandGobbler::SpitOut(ACharacter* Spat, bool bIsPlayer)
{
	if (!IsValid(Spat))
	{
		return;
	}
	const float Now = TimeNow();
	if (const float* Until = SpitCooldown.Find(Spat))
	{
		if (Now < *Until)
		{
			return;
		}
	}
	SpitCooldown.Add(Spat, Now + 0.8f);

	// Away from the mouth, biased toward the arena centre (the Gobbler faces it) so nobody gets spat into the wall.
	FVector Away = Spat->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.GetSafeNormal() + GetActorForwardVector() * 1.2f;
	Away.Z = 0.f;
	if (!Away.Normalize())
	{
		Away = GetActorForwardVector();
	}
	Spat->LaunchCharacter(Away * SpitOutSpeed + FVector(0.f, 0.f, SpitUpSpeed), true, true);

	Chomp(true);
	const FVector Feet = Spat->GetActorLocation() - FVector(0.f, 0.f, 60.f);
	if (SpitSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, SpitSound, Feet, 0.7f, FMath::FRandRange(1.6f, 1.9f));
	}
	if (BurpSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, BurpSound, GetActorLocation(), 0.3f, FMath::FRandRange(0.45f, 0.55f));
	}
	if (SpitFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SpitFX, Feet, FRotator(90.f, 0.f, 0.f), FVector(1.5f));
	}
	if (bIsPlayer)
	{
		UGameplayStatics::ApplyDamage(Spat, PlayerSpitDamage, nullptr, this, nullptr);
		Say(TEXT("BLEGH!"), LastBleghAnnounce, FLinearColor(0.6f, 1.f, 0.3f));
	}
}

void ASandGobbler::FizzyBurp(AFizzBarrel* Barrel)
{
	const float Now = TimeNow();
	const FVector Where = Barrel->GetActorLocation();
	Barrel->Gobble();
	Chomp(true);
	HappyUntil = Now + 1.5f;
	BellyFlareUntil = Now + 1.2f;
	if (BurpSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, BurpSound, GetActorLocation(), 0.8f, 0.6f, 0.f);
	}
	if (SpitFX)
	{
		for (int32 i = 0; i < 3; ++i)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SpitFX, Where + FMath::VRand() * 40.f, FRotator(90.f, 0.f, 0.f), FVector(2.f));
		}
	}
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->AddHype(2.f);
	}
	if (AColosseumArena* Arena = Cast<AColosseumArena>(GetOwner()))
	{
		Arena->CrowdCheer(0.35f);
	}
	Say(TEXT("FIZZY BURP!"), LastFizzAnnounce, FLinearColor(0.3f, 0.9f, 1.f));
}

void ASandGobbler::Burp()
{
	const FVector Mouth = GetActorLocation() + FVector(0.f, 0.f, 40.f);
	if (BurpSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, BurpSound, Mouth, 0.6f, FMath::FRandRange(0.27f, 0.33f));
	}
	if (SpitFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SpitFX, Mouth, FRotator(90.f, 0.f, 0.f), FVector(1.2f));
	}
	BellyFlareUntil = TimeNow() + 0.5f;
}

void ASandGobbler::Chomp(bool bLoud)
{
	ChompStart = TimeNow();
	if (ChompSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ChompSound, GetActorLocation() + FVector(0.f, 0.f, 60.f), bLoud ? 0.8f : 0.22f, FMath::FRandRange(0.42f, 0.55f));
	}
}

void ASandGobbler::Say(const FString& Text, float& LastTime, const FLinearColor& Color)
{
	const float Now = TimeNow();
	if (Now - LastTime < AnnounceCooldown)
	{
		return;
	}
	LastTime = Now;
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->Announce(Text, 1.8f, Color);
	}
}
