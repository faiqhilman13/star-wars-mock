#include "BossWalker.h"

#include "BlasterBolt.h"
#include "Camera/CameraShakeBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/DamageEvents.h"
#include "Engine/OverlapResult.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "HordeDirector.h"
#include "JediCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

namespace ScrapRig
{
	// Leg geometry (cm). These match the meshes built in the constructor.
	constexpr float HipSpread = 150.f;     // hips at +-Y from the pelvis centre
	constexpr float ThighLength = 230.f;
	constexpr float ShinLength = 200.f;
	constexpr float AnkleHeight = 50.f;    // ankle pivot above the sole
	constexpr float NeutralFootX = 15.f;   // resting foot, forward of the hip
	constexpr float SwingFraction = 0.4f;  // share of the walk cycle each foot spends in the air

	// Scrap palette (linear colour).
	const FLinearColor ColRust(0.42f, 0.13f, 0.04f);
	const FLinearColor ColRustDark(0.20f, 0.065f, 0.03f);
	const FLinearColor ColTeal(0.07f, 0.26f, 0.24f);
	const FLinearColor ColOlive(0.20f, 0.22f, 0.07f);
	const FLinearColor ColGrey(0.25f, 0.25f, 0.27f);
	const FLinearColor ColDarkMetal(0.05f, 0.05f, 0.055f);
	const FLinearColor ColFlag(0.55f, 0.03f, 0.02f);
	const FLinearColor ColHulaGreen(0.12f, 0.45f, 0.08f);
	const FLinearColor ColHulaSkin(0.55f, 0.32f, 0.2f);
	const FLinearColor ColKneeBase(0.4f, 0.12f, 0.02f);
	const FLinearColor ColKneeGlow(22.f, 6.f, 0.8f);
	const FLinearColor ColEyeLBase(0.5f, 0.45f, 0.2f);
	const FLinearColor ColEyeLGlow(14.f, 10.f, 2.5f);
	const FLinearColor ColEyeRBase(0.1f, 0.4f, 0.35f);
	const FLinearColor ColEyeRGlow(1.5f, 9.f, 7.f);
	const FLinearColor ColRageEyes(22.f, 1.2f, 0.3f);
	const FLinearColor ColWarning(1.f, 0.06f, 0.02f);
	const FLinearColor ColShock(1.f, 0.45f, 0.1f);

	/**
	 * Planar two-bone IK for a reverse ("chicken") knee. Dx/Dz = ankle target relative to the hip in the leg's X/Z plane.
	 * Returns absolute thigh / shin angles in degrees, measured from straight down toward +X (forward).
	 */
	void SolveTwoBone(float Dx, float Dz, float& OutThighDeg, float& OutShinDeg)
	{
		const float L1 = ThighLength;
		const float L2 = ShinLength;
		const float Phi = FMath::Atan2(Dx, -Dz);
		const float D = FMath::Clamp(FMath::Sqrt(Dx * Dx + Dz * Dz), FMath::Abs(L1 - L2) + 1.f, L1 + L2 - 0.5f);
		const float CosA = FMath::Clamp((L1 * L1 + D * D - L2 * L2) / (2.f * L1 * D), -1.f, 1.f);
		const float Thigh = Phi - FMath::Acos(CosA); // knee bends backward
		const float KneeX = L1 * FMath::Sin(Thigh);
		const float KneeZ = -L1 * FMath::Cos(Thigh);
		const float AnkleX = D * FMath::Sin(Phi);
		const float AnkleZ = -D * FMath::Cos(Phi);
		const float Shin = FMath::Atan2(AnkleX - KneeX, -(AnkleZ - KneeZ));
		OutThighDeg = FMath::RadiansToDegrees(Thigh);
		OutShinDeg = FMath::RadiansToDegrees(Shin);
	}
}


// ================================================================ construction

ABossWalker::ABossWalker()
{
	PrimaryActorTick.bCanEverTick = true;

	// No AI controller: the walker drives its own movement and rotation.
	AutoPossessAI = EAutoPossessAI::Disabled;
	AIControllerClass = nullptr;
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	GetCapsuleComponent()->InitCapsuleSize(160.f, 350.f);
	GetCapsuleComponent()->SetCanEverAffectNavigation(false);

	if (USkeletalMeshComponent* SkelMesh = GetMesh())
	{
		SkelMesh->SetVisibility(false);
		SkelMesh->SetHiddenInGame(true);
		SkelMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		SkelMesh->SetGenerateOverlapEvents(false);
		SkelMesh->SetCanEverAffectNavigation(false);
		SkelMesh->PrimaryComponentTick.bStartWithTickEnabled = false;
	}

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bRunPhysicsWithNoController = true;
	Move->bOrientRotationToMovement = false;
	Move->bUseControllerDesiredRotation = false;
	Move->MaxWalkSpeed = WalkSpeed;
	Move->MaxAcceleration = 700.f;
	Move->BrakingDecelerationWalking = 900.f;
	Move->GroundFriction = 6.f;
	Move->Mass = 8000.f;
	Move->MaxStepHeight = 80.f;

	// ---- assets
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeF(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereF(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderF(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeF(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> SurfaceF(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> WaveF(TEXT("/Game/Jedi/Materials/M_ForceWave.M_ForceWave"));
	static ConstructorHelpers::FObjectFinder<USoundBase> FireF(TEXT("/Game/Jedi/Audio/Licensed/SW_Blaster_Fire_Wire.SW_Blaster_Fire_Wire"));
	static ConstructorHelpers::FObjectFinder<USoundBase> ExplodeF(TEXT("/Game/Jedi/Audio/Licensed/SW_Remote_Explode.SW_Remote_Explode"));
	static ConstructorHelpers::FObjectFinder<USoundBase> PushF(TEXT("/Game/Jedi/Audio/SW_Force_Push.SW_Force_Push"));
	static ConstructorHelpers::FObjectFinder<USoundBase> ClangF(TEXT("/Game/Jedi/Audio/Licensed/SW_Saber_Clash_Rec1.SW_Saber_Clash_Rec1"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> HitFXF(TEXT("/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"));
	static ConstructorHelpers::FClassFinder<ABlasterBolt> BoltF(TEXT("/Game/Jedi/Blueprints/BP_BlasterBolt.BP_BlasterBolt_C"));

	UStaticMesh* Cube = CubeF.Object;
	UStaticMesh* Sphere = SphereF.Object;
	UStaticMesh* Cylinder = CylinderF.Object;
	UStaticMesh* Cone = ConeF.Object;
	SphereMesh = Sphere;
	SurfaceMaterial = SurfaceF.Object;
	WaveMaterial = WaveF.Object;
	FireSound = FireF.Object;
	ExplodeSound = ExplodeF.Object;
	StompSound = PushF.Object;
	ClangSound = ClangF.Object;
	HitFX = HitFXF.Object;
	if (BoltF.Succeeded())
	{
		BoltClass = BoltF.Class;
	}
	else
	{
		BoltClass = ABlasterBolt::StaticClass();
	}

	// ---- rig: floor-level origin -> pelvis (bobs) -> hull pivot (sways / pecks / looks)
	Rig = CreateDefaultSubobject<USceneComponent>(TEXT("Rig"));
	Rig->SetupAttachment(GetCapsuleComponent());
	Rig->SetRelativeLocation(FVector(0.f, 0.f, -350.f));

	Pelvis = MakePivot(TEXT("Pelvis"), Rig, FVector(0.f, 0.f, HipHeight));
	HullPivot = MakePivot(TEXT("HullPivot"), Pelvis, FVector(0.f, 0.f, 45.f));

	PelvisAxle = MakePart(TEXT("PelvisAxle"), Pelvis, Cylinder, FVector::ZeroVector, FRotator(0.f, 0.f, 90.f), FVector(0.9f, 0.9f, 2.9f));

	// ---- the cockpit: a rusty box with a goofy face
	const FVector HullScale(3.0f, 2.5f, 1.7f);
	HullBody = MakePart(TEXT("HullBody"), HullPivot, Cube, FVector(10.f, 0.f, 100.f), FRotator::ZeroRotator, HullScale);
	MakeHittable(HullBody);
	// Eye lamps ride on the hull box so they leave with the head; undo its non-uniform scale. Mismatched on purpose.
	EyeL = MakePart(TEXT("EyeL"), HullBody, Sphere, FVector(153.f, -68.f, 12.f) / HullScale, FRotator::ZeroRotator, FVector(0.78f) / HullScale);
	EyeR = MakePart(TEXT("EyeR"), HullBody, Sphere, FVector(150.f, 66.f, 30.f) / HullScale, FRotator::ZeroRotator, FVector(0.5f) / HullScale);
	for (UStaticMeshComponent* Eye : { EyeL.Get(), EyeR.Get() })
	{
		Eye->SetCastShadow(false);
	}
	HullRoof = MakePart(TEXT("HullRoof"), HullPivot, Cube, FVector(-20.f, 8.f, 205.f), FRotator(0.f, 4.f, 0.f), FVector(2.3f, 2.1f, 0.45f));
	SidePatch = MakePart(TEXT("SidePatch"), HullPivot, Cube, FVector(25.f, -129.f, 95.f), FRotator(8.f, 0.f, 0.f), FVector(1.3f, 0.08f, 0.95f));
	// Dented, slightly crooked beak with the twin cannons slung underneath.
	Beak = MakePart(TEXT("Beak"), HullPivot, Cone, FVector(222.f, 0.f, 42.f), FRotator(-102.f, 0.f, 7.f), FVector(1.0f, 1.3f, 1.5f));
	MakeHittable(Beak);
	CannonL = MakePart(TEXT("CannonL"), HullPivot, Cylinder, FVector(215.f, -48.f, -8.f), FRotator(90.f, 0.f, 0.f), FVector(0.34f, 0.34f, 1.9f));
	CannonR = MakePart(TEXT("CannonR"), HullPivot, Cylinder, FVector(205.f, 50.f, -4.f), FRotator(90.f, 0.f, 0.f), FVector(0.3f, 0.3f, 1.6f));
	// One grumpy eyebrow.
	Brow = MakePart(TEXT("Brow"), HullPivot, Cube, FVector(172.f, -68.f, 158.f), FRotator(0.f, 0.f, 16.f), FVector(0.25f, 0.95f, 0.13f));
	// Antenna with a tiny flag.
	Antenna = MakePart(TEXT("Antenna"), HullPivot, Cylinder, FVector(-95.f, 88.f, 285.f), FRotator(0.f, 0.f, -10.f), FVector(0.06f, 0.06f, 1.7f));
	FlagPivot = MakePivot(TEXT("FlagPivot"), HullPivot, FVector(-95.f, 74.f, 358.f));
	Flag = MakePart(TEXT("Flag"), FlagPivot, Cube, FVector(-28.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.55f, 0.04f, 0.34f));
	// Spinning radar dish.
	RadarPivot = MakePivot(TEXT("RadarPivot"), HullPivot, FVector(45.f, -55.f, 228.f));
	RadarDish = MakePart(TEXT("RadarDish"), RadarPivot, Cone, FVector(0.f, 0.f, 30.f), FRotator(125.f, 0.f, 0.f), FVector(0.9f, 0.9f, 0.3f));
	// Mismatched exhaust stacks.
	ExhaustL = MakePart(TEXT("ExhaustL"), HullPivot, Cylinder, FVector(-155.f, -60.f, 175.f), FRotator(18.f, 0.f, 0.f), FVector(0.28f, 0.28f, 1.6f));
	ExhaustR = MakePart(TEXT("ExhaustR"), HullPivot, Cylinder, FVector(-152.f, 55.f, 165.f), FRotator(24.f, 0.f, 0.f), FVector(0.24f, 0.24f, 1.4f));
	// Scrap-missile rack on the roof (pops open in rage).
	MissileRack = MakePart(TEXT("MissileRack"), HullPivot, Cube, FVector(-70.f, -5.f, 250.f), FRotator::ZeroRotator, FVector(1.2f, 1.4f, 0.55f));
	// Hula-dancer bobblehead on the "dashboard" (the top of the beak).
	HulaPivot = MakePivot(TEXT("HulaPivot"), HullPivot, FVector(190.f, 0.f, 84.f));
	HulaSkirt = MakePart(TEXT("HulaSkirt"), HulaPivot, Cone, FVector(0.f, 0.f, 12.f), FRotator::ZeroRotator, FVector(0.22f, 0.22f, 0.24f));
	HulaHead = MakePart(TEXT("HulaHead"), HulaPivot, Sphere, FVector(0.f, 0.f, 30.f), FRotator::ZeroRotator, FVector(0.14f));
	for (UStaticMeshComponent* Tiny : { Flag.Get(), HulaSkirt.Get(), HulaHead.Get(), Antenna.Get() })
	{
		Tiny->SetCastShadow(false);
	}

	// ---- legs: hip pivot -> thigh; knee pivot -> glowing knee + shin; ankle pivot -> foot + toe claw
	float RestThigh = 0.f;
	float RestShin = 0.f;
	ScrapRig::SolveTwoBone(ScrapRig::NeutralFootX, ScrapRig::AnkleHeight - HipHeight, RestThigh, RestShin);
	for (int32 i = 0; i < 2; ++i)
	{
		const bool bLeft = (i == 0);
		const float Side = bLeft ? -1.f : 1.f;
		USceneComponent* Hip = MakePivot(bLeft ? TEXT("HipPivotL") : TEXT("HipPivotR"), Pelvis, FVector(0.f, Side * ScrapRig::HipSpread, 0.f));
		Hip->SetRelativeRotation(FRotator(RestThigh, 0.f, 0.f));
		UStaticMeshComponent* Thigh = MakePart(bLeft ? TEXT("ThighL") : TEXT("ThighR"), Hip, Cube, FVector(0.f, 0.f, -ScrapRig::ThighLength * 0.5f), FRotator::ZeroRotator, FVector(0.75f, 0.55f, ScrapRig::ThighLength / 100.f));
		USceneComponent* Knee = MakePivot(bLeft ? TEXT("KneePivotL") : TEXT("KneePivotR"), Hip, FVector(0.f, 0.f, -ScrapRig::ThighLength));
		Knee->SetRelativeRotation(FRotator(RestShin - RestThigh, 0.f, 0.f));
		UStaticMeshComponent* Joint = MakePart(bLeft ? TEXT("KneeJointL") : TEXT("KneeJointR"), Knee, Sphere, FVector::ZeroVector, FRotator::ZeroRotator, FVector(0.85f));
		UStaticMeshComponent* Shin = MakePart(bLeft ? TEXT("ShinL") : TEXT("ShinR"), Knee, Cylinder, FVector(0.f, 0.f, -ScrapRig::ShinLength * 0.5f), FRotator::ZeroRotator, FVector(0.55f, 0.55f, ScrapRig::ShinLength / 100.f));
		USceneComponent* Ankle = MakePivot(bLeft ? TEXT("AnklePivotL") : TEXT("AnklePivotR"), Knee, FVector(0.f, 0.f, -ScrapRig::ShinLength));
		Ankle->SetRelativeRotation(FRotator(-RestShin, 0.f, 0.f));
		UStaticMeshComponent* Foot = MakePart(bLeft ? TEXT("FootL") : TEXT("FootR"), Ankle, Cube, FVector(22.f, 0.f, -33.f), FRotator::ZeroRotator, FVector(1.7f, 1.05f, 0.32f));
		UStaticMeshComponent* Toe = MakePart(bLeft ? TEXT("ToeL") : TEXT("ToeR"), Ankle, Cone, FVector(135.f, 0.f, -36.f), FRotator(-90.f, 0.f, 0.f), FVector(0.45f, 0.9f, 0.6f));
		MakeHittable(Thigh);
		MakeHittable(Joint);
		MakeHittable(Shin);
		MakeHittable(Foot);

		Legs[i].Side = Side;
		if (bLeft)
		{
			HipPivotL = Hip; KneePivotL = Knee; AnklePivotL = Ankle;
			ThighL = Thigh; KneeJointL = Joint; ShinL = Shin; FootL = Foot; ToeL = Toe;
		}
		else
		{
			HipPivotR = Hip; KneePivotR = Knee; AnklePivotR = Ankle;
			ThighR = Thigh; KneeJointR = Joint; ShinR = Shin; FootR = Foot; ToeR = Toe;
		}
	}
}

USceneComponent* ABossWalker::MakePivot(const TCHAR* Name, USceneComponent* Parent, const FVector& Loc)
{
	USceneComponent* Pivot = CreateDefaultSubobject<USceneComponent>(Name);
	Pivot->SetupAttachment(Parent);
	Pivot->SetRelativeLocation(Loc);
	return Pivot;
}

UStaticMeshComponent* ABossWalker::MakePart(const TCHAR* Name, USceneComponent* Parent, UStaticMesh* ShapeMesh, const FVector& Loc, const FRotator& Rot, const FVector& Scale)
{
	UStaticMeshComponent* Comp = CreateDefaultSubobject<UStaticMeshComponent>(Name);
	Comp->SetupAttachment(Parent);
	if (ShapeMesh)
	{
		Comp->SetStaticMesh(ShapeMesh);
	}
	Comp->SetRelativeLocation(Loc);
	Comp->SetRelativeRotation(Rot);
	Comp->SetRelativeScale3D(Scale);
	Comp->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
	Comp->SetGenerateOverlapEvents(false);
	Comp->SetCanEverAffectNavigation(false);
	Comp->bReceivesDecals = false;
	if (SurfaceMaterial)
	{
		Comp->SetMaterial(0, SurfaceMaterial);
	}
	return Comp;
}

void ABossWalker::MakeHittable(UStaticMeshComponent* Comp)
{
	// Query-only so saber sweeps (object queries) and blaster bolts (overlaps) register hits where they actually land,
	// while nothing gets blocked by it (the capsule does the blocking).
	Comp->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Comp->SetCollisionObjectType(ECC_WorldDynamic);
	Comp->SetCollisionResponseToAllChannels(ECR_Ignore);
	Comp->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Overlap);
	Comp->SetGenerateOverlapEvents(true);
}

// ================================================================ setup

void ABossWalker::BeginPlay()
{
	Super::BeginPlay();

	HP = MaxHP;
	if (bLeashToSpawnPoint)
	{
		LeashCenter = GetActorLocation();
	}
	if (!BoltClass)
	{
		BoltClass = LoadClass<ABlasterBolt>(nullptr, TEXT("/Game/Jedi/Blueprints/BP_BlasterBolt.BP_BlasterBolt_C"));
	}
	if (!BoltClass)
	{
		BoltClass = ABlasterBolt::StaticClass();
	}

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = WalkSpeed;
	SavedGravityScale = Move->GravityScale;

	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	Rig->SetRelativeLocation(FVector(0.f, 0.f, -HalfHeight));
	Pelvis->SetRelativeLocation(FVector(0.f, 0.f, HipHeight));

	Legs[0].Hip = HipPivotL; Legs[0].Knee = KneePivotL; Legs[0].Ankle = AnklePivotL; Legs[0].KneeJoint = KneeJointL; Legs[0].Side = -1.f;
	Legs[1].Hip = HipPivotR; Legs[1].Knee = KneePivotR; Legs[1].Ankle = AnklePivotR; Legs[1].KneeJoint = KneeJointR; Legs[1].Side = 1.f;
	for (int32 i = 0; i < 2; ++i)
	{
		Legs[i].FootPos = NeutralFoot(i);
		Legs[i].SwingFrom = Legs[i].FootPos;
		Legs[i].SwingTo = Legs[i].FootPos;
		Legs[i].Ankle3D = Legs[i].FootPos + FVector(0.f, 0.f, ScrapRig::AnkleHeight);
	}

	CannonBase[0] = CannonL->GetRelativeLocation();
	CannonBase[1] = CannonR->GetRelativeLocation();
	ExhaustBaseScale[0] = ExhaustL->GetRelativeScale3D();
	ExhaustBaseScale[1] = ExhaustR->GetRelativeScale3D();
	EyeLBaseScale = EyeL->GetRelativeScale3D();
	EyeRBaseScale = EyeR->GetRelativeScale3D();
	HulaHeadBase = HulaHead->GetRelativeLocation();
	RackBaseRot = MissileRack->GetRelativeRotation();

	BuildParts();
	CreatePuffs();

	const float T = Now();
	PrevYaw = static_cast<float>(GetActorRotation().Yaw);
	NextStumbleTime = T + FMath::FRandRange(StumbleInterval.X, StumbleInterval.Y);
	NextBlinkTime = T + 2.f;
	NextStrafeFlip = T + 4.f;
	NextPuffTime = T + 0.5f;
	NextAttackTime = T + 4.f;
	NextBarrageTime = T + 4.f;

	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->SetBoss(this, TEXT("SCRAP COLOSSUS"));
		Director->Announce(TEXT("THE SCRAP COLOSSUS HAS ENTERED THE ARENA!"), 3.5f, FLinearColor(1.f, 0.55f, 0.1f));
		Director->AddHype(10.f);
	}

	// Intro: drop in from the sky, unless something (a gate arch, a roof) is overhead.
	SetState(EBossWalkerState::Intro);
	bIntroFalling = false;
	bIntroImpactDone = false;
	if (bDropIn && DropHeight > 500.f)
	{
		const FVector Start = GetActorLocation();
		const float Margin = HalfHeight * 2.f + 100.f;
		float Height = DropHeight;
		FHitResult Hit;
		FCollisionQueryParams Query(SCENE_QUERY_STAT(BossWalkerDrop), false, this);
		FCollisionObjectQueryParams Objects;
		Objects.AddObjectTypesToQuery(ECC_WorldStatic);
		Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
		if (GetWorld()->LineTraceSingleByObjectType(Hit, Start, Start + FVector(0.f, 0.f, DropHeight + Margin), Objects, Query))
		{
			Height = Hit.Distance - Margin;
		}
		if (Height > 500.f)
		{
			SetActorLocation(Start + FVector(0.f, 0.f, Height), false, nullptr, ETeleportType::TeleportPhysics);
			Move->GravityScale = 2.f;
			Move->SetMovementMode(MOVE_Falling);
			Move->Velocity = FVector(0.f, 0.f, -600.f);
			bIntroFalling = true;
		}
	}
}

void ABossWalker::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (EndPlayReason == EEndPlayReason::Destroyed && bDead)
	{
		ReportKO();
	}
	Missiles.Reset();
	Super::EndPlay(EndPlayReason);
}

int32 ABossWalker::AddPart(UStaticMeshComponent* PartMesh, const FLinearColor& Base, float Roughness, float Metallic, const FLinearColor& Emissive, float DebrisDelay)
{
	if (!PartMesh)
	{
		return INDEX_NONE;
	}
	FScrapPart Part;
	Part.Mesh = PartMesh;
	Part.Emissive = Emissive;
	Part.DebrisDelay = DebrisDelay;
	if (SurfaceMaterial)
	{
		Part.MID = PartMesh->CreateDynamicMaterialInstance(0, SurfaceMaterial);
		if (Part.MID)
		{
			// Every panel came off a different wreck: nudge the tint a little.
			FLinearColor Tint = Base * FMath::FRandRange(0.85f, 1.15f);
			Tint.A = 1.f;
			Part.MID->SetVectorParameterValue(TEXT("BaseColor"), Tint);
			Part.MID->SetScalarParameterValue(TEXT("Roughness"), Roughness);
			Part.MID->SetScalarParameterValue(TEXT("Metallic"), Metallic);
			Part.MID->SetVectorParameterValue(TEXT("Emissive"), Emissive);
		}
	}
	return Parts.Add(Part);
}

void ABossWalker::BuildParts()
{
	Parts.Reset();
	const FLinearColor Off = FLinearColor::Black;

	// Debris delay: seconds into the death sequence a part pops off (0 = final blast, -1 = stays on its parent).
	HullPart = AddPart(HullBody, ScrapRig::ColRust, 0.8f, 0.35f, Off, 0.f);
	EyeLPart = AddPart(EyeL, ScrapRig::ColEyeLBase, 0.3f, 0.f, ScrapRig::ColEyeLGlow, -1.f);
	EyeRPart = AddPart(EyeR, ScrapRig::ColEyeRBase, 0.3f, 0.f, ScrapRig::ColEyeRGlow, -1.f);
	AddPart(HullRoof, ScrapRig::ColTeal, 0.7f, 0.25f, Off, 0.f);
	AddPart(SidePatch, ScrapRig::ColOlive, 0.75f, 0.2f, Off, 1.3f);
	AddPart(Beak, ScrapRig::ColGrey, 0.45f, 0.85f, Off, 0.f);
	CannonPart[0] = AddPart(CannonL, ScrapRig::ColDarkMetal, 0.4f, 1.f, Off, 1.8f);
	CannonPart[1] = AddPart(CannonR, ScrapRig::ColDarkMetal, 0.4f, 1.f, Off, 0.f);
	AddPart(Brow, ScrapRig::ColRustDark, 0.85f, 0.3f, Off, 0.f);
	AddPart(Antenna, ScrapRig::ColGrey, 0.4f, 0.9f, Off, 0.6f);
	AddPart(Flag, ScrapRig::ColFlag, 0.9f, 0.f, FLinearColor(0.35f, 0.01f, 0.f), 0.6f);
	AddPart(RadarDish, ScrapRig::ColGrey, 0.35f, 0.9f, Off, 1.0f);
	ExhaustPart[0] = AddPart(ExhaustL, ScrapRig::ColDarkMetal, 0.5f, 0.9f, Off, 2.1f);
	ExhaustPart[1] = AddPart(ExhaustR, ScrapRig::ColDarkMetal, 0.5f, 0.9f, Off, 0.f);
	RackPart = AddPart(MissileRack, ScrapRig::ColOlive, 0.7f, 0.3f, Off, 0.f);
	AddPart(HulaSkirt, ScrapRig::ColHulaGreen, 0.9f, 0.f, Off, 0.f);
	AddPart(HulaHead, ScrapRig::ColHulaSkin, 0.6f, 0.f, Off, 1.5f);
	AddPart(PelvisAxle, ScrapRig::ColDarkMetal, 0.45f, 1.f, Off, 0.f);

	// Legs: deliberately mismatched salvage.
	AddPart(ThighL, ScrapRig::ColRust, 0.8f, 0.35f, Off, 0.f);
	AddPart(ThighR, ScrapRig::ColOlive, 0.75f, 0.2f, Off, 0.f);
	KneePart[0] = AddPart(KneeJointL, ScrapRig::ColKneeBase, 0.3f, 0.f, ScrapRig::ColKneeGlow, 0.f);
	KneePart[1] = AddPart(KneeJointR, ScrapRig::ColKneeBase, 0.3f, 0.f, ScrapRig::ColKneeGlow, 0.f);
	AddPart(ShinL, ScrapRig::ColTeal, 0.7f, 0.25f, Off, 0.f);
	AddPart(ShinR, ScrapRig::ColGrey, 0.45f, 0.85f, Off, 0.f);
	AddPart(FootL, ScrapRig::ColGrey, 0.45f, 0.85f, Off, 0.f);
	AddPart(FootR, ScrapRig::ColRustDark, 0.85f, 0.3f, Off, 0.f);
	AddPart(ToeL, ScrapRig::ColDarkMetal, 0.4f, 1.f, Off, 0.f);
	AddPart(ToeR, ScrapRig::ColDarkMetal, 0.4f, 1.f, Off, 0.f);
}

void ABossWalker::CreatePuffs()
{
	if (!SphereMesh)
	{
		return;
	}
	for (int32 i = 0; i < 6; ++i)
	{
		UStaticMeshComponent* Puff = NewObject<UStaticMeshComponent>(this);
		Puff->SetStaticMesh(SphereMesh);
		Puff->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		Puff->SetGenerateOverlapEvents(false);
		Puff->SetCastShadow(false);
		Puff->SetCanEverAffectNavigation(false);
		Puff->SetUsingAbsoluteLocation(true);
		Puff->SetUsingAbsoluteRotation(true);
		Puff->SetUsingAbsoluteScale(true);
		Puff->SetupAttachment(GetRootComponent());
		Puff->RegisterComponent();
		Puff->SetVisibility(false);
		if (SurfaceMaterial)
		{
			if (UMaterialInstanceDynamic* MID = Puff->CreateDynamicMaterialInstance(0, SurfaceMaterial))
			{
				// Cartoon smoke: soft dark-grey balls.
				MID->SetVectorParameterValue(TEXT("BaseColor"), FLinearColor(0.09f, 0.085f, 0.08f));
				MID->SetScalarParameterValue(TEXT("Roughness"), 1.f);
				MID->SetScalarParameterValue(TEXT("Metallic"), 0.f);
				MID->SetVectorParameterValue(TEXT("Emissive"), FLinearColor::Black);
			}
		}
		Puffs.Add(Puff);
		PuffStart.Add(-100.f);
		PuffOrigin.Add(FVector::ZeroVector);
		PuffDrift.Add(FVector::ZeroVector);
		PuffSize.Add(1.f);
	}
}

// ================================================================ small helpers

float ABossWalker::Now() const
{
	const UWorld* World = GetWorld();
	return World ? static_cast<float>(World->GetTimeSeconds()) : 0.f;
}

ACharacter* ABossWalker::GetPlayer() const
{
	return UGameplayStatics::GetPlayerCharacter(this, 0);
}

bool ABossWalker::IsTargetable(const ACharacter* Player) const
{
	if (!IsValid(Player))
	{
		return false;
	}
	if (const AJediCharacter* Jedi = Cast<AJediCharacter>(Player))
	{
		return !Jedi->IsDead();
	}
	return true;
}

bool ABossWalker::IsLive(const UStaticMeshComponent* Comp) const
{
	return Comp && Comp->GetAttachParent() != nullptr;
}

float ABossWalker::GetJediHealthFraction() const
{
	return MaxHP > 0.f ? FMath::Clamp(HP / MaxHP, 0.f, 1.f) : 0.f;
}

FVector ABossWalker::GetKneeLocation(int32 LegIndex) const
{
	const UStaticMeshComponent* Joint = LegIndex <= 0 ? KneeJointL.Get() : KneeJointR.Get();
	return Joint ? Joint->GetComponentLocation() : GetActorLocation();
}

void ABossWalker::SetState(EBossWalkerState NewState)
{
	State = NewState;
	StateTime = 0.f;
	StepTime = 0.f;
	StateStep = 0;
}

void ABossWalker::NextStep()
{
	++StateStep;
	StepTime = 0.f;
}

void ABossWalker::FinishAttack(float ExtraCooldown)
{
	LastAttack = State;
	SetState(EBossWalkerState::Roam);
	NextAttackTime = Now() + (bRage ? RageAttackCooldown : AttackCooldown) * FMath::FRandRange(0.8f, 1.2f) + ExtraCooldown;
	PoseOffsetTarget = FVector::ZeroVector;
	PosePitchTarget = 0.f;
	PoseRollTarget = 0.f;
	PoseSpeed = 5.f;
	bGaitHold = false;
	Legs[0].bOverride = false;
	Legs[1].bOverride = false;
}

void ABossWalker::CancelAttack()
{
	ReleaseRing(StompRing, StompRingSerial);
	StompRing = INDEX_NONE;
	for (int32 i = 0; i < 2; ++i)
	{
		FLegState& Leg = Legs[i];
		if (Leg.bOverride)
		{
			// Drop a raised foot straight down; the gait re-centres it with the next step.
			Leg.bOverride = false;
			FVector Ground = Leg.OverrideAnkle;
			Ground.Z = NeutralFoot(i).Z;
			Leg.FootPos = Ground;
			Leg.bSwinging = false;
			Leg.FootPitch = 0.f;
		}
	}
	if (State == EBossWalkerState::Barrage)
	{
		NextBarrageTime = Now() + BarrageCooldown * 0.5f;
	}
	bGaitHold = false;
	ShotsLeft = 0;
	MissilesLeft = 0;
	bPeckStruck = false;
	bPeckStuck = false;
	bPeckParried = false;
	PoseOffsetTarget = FVector::ZeroVector;
	PosePitchTarget = 0.f;
	PoseRollTarget = 0.f;
	PoseSpeed = 5.f;
}

void ABossWalker::TurnToward(const FVector& Target, float Rate, float Dt)
{
	FVector To = Target - GetActorLocation();
	To.Z = 0.f;
	if (To.SizeSquared() < 1.f)
	{
		return;
	}
	const float Desired = static_cast<float>(To.Rotation().Yaw);
	const float Current = static_cast<float>(GetActorRotation().Yaw);
	SetActorRotation(FRotator(0.f, FMath::FixedTurn(Current, Desired, Rate * Dt), 0.f));
}

void ABossWalker::Sparks(const FVector& Location, int32 Count, float Scale)
{
	if (!HitFX)
	{
		return;
	}
	for (int32 i = 0; i < Count; ++i)
	{
		const FVector Offset = i == 0 ? FVector::ZeroVector : FMath::VRand() * (25.f * Scale);
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, Location + Offset, FMath::VRand().Rotation(), FVector(Scale));
	}
}

void ABossWalker::PlaySoundAt(USoundBase* Sound, const FVector& Location, float Volume, float Pitch)
{
	if (Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, Location, Volume, Pitch);
	}
}

void ABossWalker::Shake(const FVector& Where, float Inner, float Outer)
{
	if (StompShake)
	{
		UGameplayStatics::PlayWorldCameraShake(this, StompShake, Where, Inner, Outer);
	}
}

void ABossWalker::KickWobble(float PitchVel, float RollVel)
{
	WobbleVel.X += PitchVel;
	WobbleVel.Y += RollVel;
}

void ABossWalker::KickWobbleFrom(const FVector& WorldDir, float Strength)
{
	FVector Dir = WorldDir;
	Dir.Z = 0.f;
	if (!Dir.Normalize())
	{
		return;
	}
	// Lean the cockpit the way it was shoved: pushed backward = nose up (+pitch), pushed right = right side down (+roll).
	const FVector Local = GetActorRotation().UnrotateVector(Dir);
	KickWobble(static_cast<float>(-Local.X) * Strength, static_cast<float>(Local.Y) * Strength);
}

void ABossWalker::Flash(int32 PartIndex, const FLinearColor& Color, float Amount)
{
	if (Parts.IsValidIndex(PartIndex))
	{
		FScrapPart& Part = Parts[PartIndex];
		Part.Flash = FMath::Max(Part.Flash, Amount);
		Part.FlashColor = Color;
		Part.bDirty = true;
	}
}

FVector ABossWalker::GroundBelow(const FVector& Point) const
{
	FHitResult Hit;
	FCollisionQueryParams Query(SCENE_QUERY_STAT(BossWalkerGround), false, this);
	FCollisionObjectQueryParams Objects;
	Objects.AddObjectTypesToQuery(ECC_WorldStatic);
	const UWorld* World = GetWorld();
	if (World && World->LineTraceSingleByObjectType(Hit, Point + FVector(0.f, 0.f, 300.f), Point - FVector(0.f, 0.f, 3000.f), Objects, Query))
	{
		return Hit.ImpactPoint;
	}
	return FVector(Point.X, Point.Y, GetActorLocation().Z - GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
}

// ================================================================ tick

void ABossWalker::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Dt = FMath::Min(DeltaSeconds, 0.05f);
	StateTime += Dt;
	StepTime += Dt;

	if (bFinalBlast)
	{
		// Only debris now: keep the FX going and remember the head's velocity for its bounces.
		if (HullBody && HullBody->IsSimulatingPhysics())
		{
			HeadPrevVelocity = HullBody->GetPhysicsLinearVelocity();
		}
		UpdateFlashes(Dt);
		UpdateRings();
		UpdatePuffs();
		UpdateMissiles();
		return;
	}

	ACharacter* Player = GetPlayer();
	ACharacter* Target = IsTargetable(Player) ? Player : nullptr;

	switch (State)
	{
	case EBossWalkerState::Intro:     TickIntro(Dt); break;
	case EBossWalkerState::Roam:      TickRoam(Dt, Target); break;
	case EBossWalkerState::Volley:    TickVolley(Dt, Target); break;
	case EBossWalkerState::Stomp:     TickStomp(Dt, Target); break;
	case EBossWalkerState::Peck:      TickPeck(Dt, Target); break;
	case EBossWalkerState::Barrage:   TickBarrage(Dt, Target); break;
	case EBossWalkerState::Stagger:   TickStagger(Dt); break;
	case EBossWalkerState::Collapsed: TickCollapse(Dt); break;
	case EBossWalkerState::Dead:      TickDeath(Dt); break;
	default: break;
	}

	if (bFinalBlast)
	{
		return; // TickDeath just blew it apart
	}

	UpdateGait(Dt);
	UpdatePose(Dt);
	SolveLegs();
	UpdateDetails(Dt);
	UpdateFlashes(Dt);
	UpdateRings();
	UpdatePuffs();
	UpdateMissiles();
}

// ================================================================ brain

void ABossWalker::TickIntro(float Dt)
{
	if (bIntroFalling)
	{
		// Flail a little on the way down.
		PosePitchTarget = 8.f * FMath::Sin(StateTime * 9.f);
		PoseRollTarget = 10.f * FMath::Sin(StateTime * 7.f);
		PoseSpeed = 6.f;
		if (StateTime > 6.f)
		{
			bIntroFalling = false;
			GetCharacterMovement()->GravityScale = SavedGravityScale;
			IntroImpact();
		}
		return;
	}
	if (!bIntroImpactDone)
	{
		// Spawned on the ground (no drop): a power-on stomp instead.
		PosePitchTarget = 10.f;
		PoseSpeed = 3.f;
		if (StateTime >= 0.8f)
		{
			IntroImpact();
		}
		return;
	}

	// Rear back and show off for the crowd, then get to work.
	const bool bPose = StepTime < 1.2f;
	PosePitchTarget = bPose ? 14.f : 0.f;
	PoseRollTarget = bPose ? 4.f * FMath::Sin(StepTime * 10.f) : 0.f;
	PoseOffsetTarget = FVector(0.f, 0.f, bPose ? 25.f : 0.f);
	PoseSpeed = 4.f;
	EyeSquint = bPose ? 1.3f : 1.f;
	if (StepTime >= 1.8f)
	{
		LastAttack = EBossWalkerState::Intro;
		SetState(EBossWalkerState::Roam);
		NextAttackTime = Now() + 1.2f;
		NextBarrageTime = Now() + 4.f;
	}
}

void ABossWalker::IntroImpact()
{
	bIntroImpactDone = true;
	StepTime = 0.f;
	for (int32 i = 0; i < 2; ++i)
	{
		Legs[i].FootPos = NeutralFoot(i);
		Legs[i].bSwinging = false;
		Legs[i].bOverride = false;
		Legs[i].FootPitch = 0.f;
	}
	GaitPhase = 0.45f; // both feet planted
	DipVel -= 700.f;
	KickWobble(-60.f, FMath::FRandRange(-40.f, 40.f));
	const FVector Feet = GetActorLocation() - FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
	StompImpact(Feet, StompRadius * 1.3f, StompDamage, 1.f);
	Sparks(Feet + GetActorRightVector() * ScrapRig::HipSpread, 2, 1.5f);
	Sparks(Feet - GetActorRightVector() * ScrapRig::HipSpread, 2, 1.5f);
}

void ABossWalker::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);
	if (bIntroFalling)
	{
		bIntroFalling = false;
		GetCharacterMovement()->GravityScale = SavedGravityScale;
		IntroImpact();
	}
}

void ABossWalker::TickRoam(float Dt, ACharacter* Player)
{
	PoseOffsetTarget = FVector::ZeroVector;
	PosePitchTarget = 0.f;
	PoseRollTarget = 0.f;
	PoseSpeed = 5.f;
	CannonCharge = FMath::FInterpTo(CannonCharge, 0.f, Dt, 4.f);

	const FVector Loc = GetActorLocation();
	const float T = Now();
	FVector Move = FVector::ZeroVector;

	if (!Player)
	{
		// Nobody left to squash: a little victory jig on the spot.
		PoseRollTarget = 9.f * FMath::Sin(StateTime * 6.f);
		PosePitchTarget = 4.f * FMath::Sin(StateTime * 12.f);
		PoseSpeed = 10.f;
	}
	else
	{
		FVector ToPlayer = Player->GetActorLocation() - Loc;
		ToPlayer.Z = 0.f;
		const float Dist = static_cast<float>(ToPlayer.Size());
		const FVector Dir = ToPlayer.GetSafeNormal();
		TurnToward(Player->GetActorLocation(), CurrentTurnRate(), Dt);
		const float Facing = static_cast<float>(FVector::DotProduct(GetActorForwardVector(), Dir));

		if (Dist > ApproachRange)
		{
			Move = Dir * FMath::Clamp(Facing, 0.3f, 1.f);
		}
		else if (Dist < BackOffRange)
		{
			Move = -Dir * 0.45f;
		}
		else
		{
			if (T >= NextStrafeFlip)
			{
				StrafeSign = -StrafeSign;
				NextStrafeFlip = T + FMath::FRandRange(3.f, 6.f);
			}
			const FVector Side = FVector::CrossProduct(FVector::UpVector, Dir) * StrafeSign;
			Move = Side * 0.5f + Dir * 0.15f;
		}

		if (T >= NextAttackTime && CollapseAlpha < 0.05f)
		{
			ChooseAttack(Player, Dist);
			if (State != EBossWalkerState::Roam)
			{
				return;
			}
		}
	}

	// Leash: never wander out of the colosseum.
	FVector FromCenter = Loc - LeashCenter;
	FromCenter.Z = 0.f;
	const float R = static_cast<float>(FromCenter.Size());
	if (R > LeashRadius)
	{
		Move = -FromCenter.GetSafeNormal();
	}
	else if (R > LeashRadius - 400.f && R > 1.f)
	{
		const FVector Out = FromCenter / R;
		const float Outward = static_cast<float>(FVector::DotProduct(Move, Out));
		if (Outward > 0.f)
		{
			Move -= Out * Outward; // slide along the edge instead
		}
	}

	const float SpeedScale = T < StumbleUntil ? 0.15f : 1.f;
	GetCharacterMovement()->MaxWalkSpeed = (bRage ? RageWalkSpeed : WalkSpeed) * SpeedScale;
	if (!Move.IsNearlyZero())
	{
		AddMovementInput(Move.GetSafeNormal(), FMath::Min(static_cast<float>(Move.Size()), 1.f));
	}
}

void ABossWalker::ChooseAttack(ACharacter* Player, float Dist)
{
	FVector Dir = Player->GetActorLocation() - GetActorLocation();
	Dir.Z = 0.f;
	Dir.Normalize();
	const float Facing = static_cast<float>(FVector::DotProduct(GetActorForwardVector(), Dir));

	struct FOption
	{
		EBossWalkerState Attack;
		float Weight;
	};
	FOption Options[] = {
		{ EBossWalkerState::Peck, (Dist < PeckRange && Facing > 0.6f) ? 3.f : 0.f },
		{ EBossWalkerState::Stomp, Dist < StompTriggerRange ? 3.f : 0.f },
		{ EBossWalkerState::Volley, Dist > 450.f ? (Dist > 1200.f ? 3.f : 2.f) : 0.f },
		{ EBossWalkerState::Barrage, (bRage && Now() >= NextBarrageTime && Dist > 350.f) ? 3.5f : 0.f },
	};
	float Total = 0.f;
	for (FOption& Option : Options)
	{
		if (Option.Attack == LastAttack)
		{
			Option.Weight *= 0.4f; // variety
		}
		Total += Option.Weight;
	}
	EBossWalkerState Pick = Dist > 450.f ? EBossWalkerState::Volley : EBossWalkerState::Stomp;
	if (Total > 0.f)
	{
		float Roll = FMath::FRandRange(0.f, Total);
		for (const FOption& Option : Options)
		{
			if (Option.Weight <= 0.f)
			{
				continue;
			}
			if (Roll <= Option.Weight)
			{
				Pick = Option.Attack;
				break;
			}
			Roll -= Option.Weight;
		}
	}

	SetState(Pick);
	ShotsLeft = 0;
	MissilesLeft = 0;
	bPeckStruck = false;
	bPeckStuck = false;
	bPeckParried = false;
	// Audible "ka-chunk" so every attack has a sound cue as well as a visual one.
	PlaySoundAt(ClangSound, HullBody->GetComponentLocation(), 0.55f, 0.45f);
}

void ABossWalker::TickVolley(float Dt, ACharacter* Player)
{
	if (!Player)
	{
		CancelAttack();
		FinishAttack();
		return;
	}
	const float Telegraph = bRage ? VolleyTelegraph * 0.7f : VolleyTelegraph;
	switch (StateStep)
	{
	case 0: // charge up: cannons glow, eyes narrow, lean back a touch
		TurnToward(Player->GetActorLocation(), CurrentTurnRate() * 0.9f, Dt);
		CannonCharge = FMath::Clamp(StepTime / FMath::Max(Telegraph, 0.05f), 0.f, 1.f);
		EyeSquint = 0.55f;
		PosePitchTarget = 5.f;
		PoseOffsetTarget = FVector(-15.f, 0.f, 10.f);
		PoseSpeed = 4.f;
		if (StepTime >= Telegraph)
		{
			ShotsLeft = FMath::RandRange(VolleyShotsMin, FMath::Max(VolleyShotsMin, VolleyShotsMax)) + (bRage ? RageExtraShots : 0);
			ShotIndex = FMath::RandRange(0, 1);
			NextShotTime = Now();
			NextStep();
		}
		break;

	case 1: // pew pew pew
		TurnToward(Player->GetActorLocation(), CurrentTurnRate() * 0.5f, Dt);
		CannonCharge = 1.f;
		EyeSquint = 0.55f;
		PosePitchTarget = -3.f;
		PoseOffsetTarget = FVector::ZeroVector;
		PoseSpeed = 6.f;
		if (ShotsLeft > 0 && Now() >= NextShotTime)
		{
			FireCannon(ShotIndex % 2, Player);
			++ShotIndex;
			--ShotsLeft;
			NextShotTime += bRage ? VolleyInterval * 0.7f : VolleyInterval;
		}
		if (ShotsLeft <= 0)
		{
			NextStep();
		}
		break;

	default: // cool down
		CannonCharge = FMath::FInterpTo(CannonCharge, 0.f, Dt, 5.f);
		PosePitchTarget = 0.f;
		if (StepTime >= 0.5f)
		{
			FinishAttack();
		}
		break;
	}
}

void ABossWalker::FireCannon(int32 Side, ACharacter* Player)
{
	UStaticMeshComponent* Cannon = Side == 0 ? CannonL.Get() : CannonR.Get();
	if (!Cannon || !Player)
	{
		return;
	}
	// The cylinder lies along -X after its 90 degree pitch, so its local -Z end is the muzzle.
	const FVector Muzzle = Cannon->GetComponentTransform().TransformPosition(FVector(0.f, 0.f, -54.f));
	FVector Target = Player->GetActorLocation() + FVector(0.f, 0.f, 25.f);
	if (bRage)
	{
		Target += Player->GetVelocity() * FMath::FRandRange(0.f, 0.3f); // a little lead so strafing isn't free
	}
	FRotator Aim = (Target - Muzzle).Rotation();
	Aim.Pitch += FMath::FRandRange(-BoltSpread, BoltSpread);
	Aim.Yaw += FMath::FRandRange(-BoltSpread, BoltSpread);
	SpawnBolt(Muzzle, Aim, BoltDamage, BoltScale, BoltSpeed);

	Recoil[Side] = 30.f;
	Flash(CannonPart[Side], FLinearColor(3.f, 1.2f, 0.3f));
	KickWobble(18.f, Side == 0 ? -10.f : 10.f);
	PlaySoundAt(FireSound, Muzzle, 1.f, FMath::FRandRange(0.6f, 0.72f));
}

ABlasterBolt* ABossWalker::SpawnBolt(const FVector& From, const FRotator& Aim, float Damage, float Scale, float Speed)
{
	UWorld* World = GetWorld();
	if (!World || !BoltClass)
	{
		return nullptr;
	}
	const FTransform SpawnXf(Aim, From, FVector(Scale));
	ABlasterBolt* Bolt = World->SpawnActorDeferred<ABlasterBolt>(BoltClass, SpawnXf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
	if (!Bolt)
	{
		return nullptr;
	}
	Bolt->Shooter = this;
	Bolt->Damage = Damage;
	Bolt->Speed = Speed;
	if (!Bolt->ImpactFX && HitFX)
	{
		Bolt->ImpactFX = HitFX;
	}
	UGameplayStatics::FinishSpawningActor(Bolt, SpawnXf);
	return IsValid(Bolt) ? Bolt : nullptr;
}

void ABossWalker::TickStomp(float Dt, ACharacter* Player)
{
	const float Telegraph = bRage ? StompTelegraph * 0.75f : StompTelegraph;
	const float SlamTime = 0.1f;
	const float LiftHeight = 190.f;

	switch (StateStep)
	{
	case 0: // get both feet on the ground, pick the foot nearest the player
	{
		if (Player)
		{
			TurnToward(Player->GetActorLocation(), CurrentTurnRate() * 0.5f, Dt);
		}
		const bool bPlanted = !Legs[0].bSwinging && !Legs[1].bSwinging;
		if (bPlanted || StepTime > 0.7f)
		{
			const FVector Target = Player ? Player->GetActorLocation() : GetActorLocation() + GetActorForwardVector() * 300.f;
			const float SideDot = static_cast<float>(FVector::DotProduct(GetActorRightVector(), Target - GetActorLocation()));
			StompLeg = SideDot >= 0.f ? 1 : 0;
			FLegState& Leg = Legs[StompLeg];
			if (Leg.bSwinging)
			{
				Leg.bSwinging = false;
				Leg.FootPos = Leg.SwingTo;
			}
			StompFrom = Leg.FootPos;
			FVector Toward = Target - StompFrom;
			Toward.Z = 0.f;
			StompTo = StompFrom + Toward.GetClampedToMaxSize(90.f);
			StompTo.Z = StompFrom.Z;
			Leg.bOverride = true;
			Leg.OverrideAnkle = StompFrom + FVector(0.f, 0.f, ScrapRig::AnkleHeight);
			bGaitHold = true;
			StompRing = ShowWarningRing(StompTo, StompRadius, Telegraph + SlamTime + 0.05f, ScrapRig::ColWarning, StompRingSerial);
			NextStep();
		}
		break;
	}

	case 1: // raise the foot high, lean away from it
	{
		const float A = FMath::Clamp(StepTime / FMath::Max(Telegraph, 0.05f), 0.f, 1.f);
		const float Up = 1.f - FMath::Square(1.f - A);
		FLegState& Leg = Legs[StompLeg];
		Leg.OverrideAnkle = FMath::Lerp(StompFrom, StompTo, 0.5f * A) + FVector(0.f, 0.f, ScrapRig::AnkleHeight + LiftHeight * Up);
		Leg.FootPitch = 22.f * Up;
		PoseRollTarget = -Leg.Side * 9.f * Up;
		PosePitchTarget = 6.f * Up;
		PoseOffsetTarget = FVector(0.f, 0.f, 30.f * Up);
		PoseSpeed = 8.f;
		if (A >= 1.f)
		{
			NextStep();
		}
		break;
	}

	case 2: // SLAM
	{
		const float B = FMath::Clamp(StepTime / SlamTime, 0.f, 1.f);
		FLegState& Leg = Legs[StompLeg];
		const FVector Raised = FMath::Lerp(StompFrom, StompTo, 0.5f) + FVector(0.f, 0.f, ScrapRig::AnkleHeight + LiftHeight);
		Leg.OverrideAnkle = FMath::Lerp(Raised, StompTo + FVector(0.f, 0.f, ScrapRig::AnkleHeight), B * B);
		Leg.FootPitch = 22.f * (1.f - B);
		PoseRollTarget = Leg.Side * 5.f;
		PosePitchTarget = -6.f;
		PoseOffsetTarget = FVector(0.f, 0.f, -20.f);
		PoseSpeed = 20.f;
		if (B >= 1.f)
		{
			Leg.bOverride = false;
			Leg.bSwinging = false;
			Leg.FootPitch = 0.f;
			Leg.FootPos = StompTo;
			Leg.Ankle3D = StompTo + FVector(0.f, 0.f, ScrapRig::AnkleHeight);
			ReleaseRing(StompRing, StompRingSerial);
			StompRing = INDEX_NONE;
			StompImpact(StompTo, StompRadius, StompDamage, StompMinionDamage);
			NextStep();
		}
		break;
	}

	default: // settle
		PoseRollTarget = 0.f;
		PosePitchTarget = 0.f;
		PoseOffsetTarget = FVector::ZeroVector;
		PoseSpeed = 4.f;
		if (StepTime >= 0.65f)
		{
			FinishAttack();
		}
		break;
	}
}

void ABossWalker::StompImpact(const FVector& Center, float Radius, float PlayerDamage, float MinionDamage)
{
	SpawnShockRing(Center + FVector(0.f, 0.f, 8.f), 60.f, Radius, 0.45f, ScrapRig::ColShock);
	SpawnShockRing(Center + FVector(0.f, 0.f, 8.f), 30.f, Radius * 0.55f, 0.3f, FLinearColor(1.f, 0.85f, 0.5f));
	Sparks(Center + FVector(0.f, 0.f, 20.f), 3, 1.6f);
	PlaySoundAt(StompSound, Center, 1.3f, 0.55f);
	PlaySoundAt(ExplodeSound, Center, 0.8f, 0.45f);
	Shake(Center, Radius * 0.6f, Radius * 3.f);
	DipVel -= 350.f;
	KickWobble(-25.f, FMath::FRandRange(-30.f, 30.f));

	ShockPlayer(Center, Radius, PlayerDamage, StompLaunch, StompLift, true);

	// It is very funny when it flattens its own droids.
	const int32 Squashed = HurtMinions(Center, Radius, MinionDamage, 900.f, 550.f);
	if (Squashed > 0)
	{
		if (AHordeDirector* Director = AHordeDirector::Get(this))
		{
			Director->AddHype(1.5f * Squashed);
			if (Squashed >= 2 && Now() - LastFriendlyFireBanner > 30.f)
			{
				LastFriendlyFireBanner = Now();
				Director->Announce(TEXT("FRIENDLY FIRE! THE CROWD LOVES IT!"), 2.f, FLinearColor(1.f, 0.8f, 0.2f));
			}
		}
	}
}

bool ABossWalker::ShockPlayer(const FVector& Center, float Radius, float Damage, float Launch, float Lift, bool bAirborneImmune)
{
	ACharacter* Player = GetPlayer();
	if (!IsTargetable(Player))
	{
		return false;
	}
	const FVector Delta = Player->GetActorLocation() - Center;
	if (Delta.Size2D() > Radius || FMath::Abs(Delta.Z) > 450.f)
	{
		return false;
	}
	const UCharacterMovementComponent* PlayerMove = Player->GetCharacterMovement();
	if (bAirborneImmune && PlayerMove && PlayerMove->IsFalling())
	{
		return false; // jumped over it
	}
	float Dealt = 0.f;
	if (Damage > 0.f)
	{
		Dealt = UGameplayStatics::ApplyDamage(Player, Damage, nullptr, this, nullptr);
	}
	if (!IsTargetable(Player))
	{
		return true; // that one finished them
	}
	FVector Away = Delta;
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
	// A blocked shockwave still shoves, just less.
	const float Scale = (Damage <= 0.f || Dealt > 0.f) ? 1.f : 0.45f;
	Player->LaunchCharacter(Away * (Launch * Scale) + FVector(0.f, 0.f, Lift * Scale), true, true);
	return true;
}

int32 ABossWalker::HurtMinions(const FVector& Center, float Radius, float Damage, float Push, float Lift)
{
	UWorld* World = GetWorld();
	if (!World || Radius <= 0.f)
	{
		return 0;
	}
	TArray<FOverlapResult> Overlaps;
	FCollisionObjectQueryParams Objects;
	Objects.AddObjectTypesToQuery(ECC_Pawn);
	Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
	Objects.AddObjectTypesToQuery(ECC_PhysicsBody);
	FCollisionQueryParams Query(SCENE_QUERY_STAT(BossWalkerShock), false, this);
	World->OverlapMultiByObjectType(Overlaps, Center, FQuat::Identity, Objects, FCollisionShape::MakeSphere(Radius), Query);

	const ACharacter* Player = GetPlayer();
	TSet<AActor*> Seen;
	int32 Hits = 0;
	for (const FOverlapResult& Overlap : Overlaps)
	{
		AActor* Other = Overlap.GetActor();
		if (!IsValid(Other) || Other == this || Other == Player)
		{
			continue;
		}
		FVector Away = Other->GetActorLocation() - Center;
		Away.Z = 0.f;
		Away = Away.IsNearlyZero() ? FMath::VRand().GetSafeNormal2D() : Away.GetSafeNormal();
		const FVector Impulse = Away * Push + FVector(0.f, 0.f, Lift);

		if (IJediDamageable* Damageable = Cast<IJediDamageable>(Other))
		{
			if (Seen.Contains(Other))
			{
				continue;
			}
			Seen.Add(Other);
			if (Damageable->IsJediTargetAlive())
			{
				Damageable->ReceiveJediHit(Damage, this, Other->GetActorLocation(), Impulse, EJediHitKind::Explosion);
				++Hits;
			}
		}
		else if (UPrimitiveComponent* Prim = Overlap.GetComponent(); Prim && Prim->IsSimulatingPhysics())
		{
			Prim->AddImpulse(Impulse * 0.6f, NAME_None, true);
		}
	}
	return Hits;
}

void ABossWalker::TickPeck(float Dt, ACharacter* Player)
{
	const FVector BeakTip = Beak ? Beak->GetComponentTransform().TransformPosition(FVector(0.f, 0.f, 50.f)) : GetActorLocation();

	if (bPeckParried)
	{
		// The Jedi swatted the beak away: BONK.
		bPeckParried = false;
		PlaySoundAt(ClangSound, BeakTip, 1.2f, 1.35f);
		Sparks(BeakTip, 3, 1.3f);
		TryStagger(-GetActorForwardVector() * 600.f, true);
		return;
	}

	switch (StateStep)
	{
	case 0: // rear back, eyes wide
		if (Player)
		{
			TurnToward(Player->GetActorLocation(), CurrentTurnRate() * 1.5f, Dt);
		}
		PosePitchTarget = 20.f;
		PoseOffsetTarget = FVector(-35.f, 0.f, 25.f);
		PoseSpeed = 6.f;
		EyeSquint = 1.3f;
		if (StepTime >= (bRage ? PeckTelegraph * 0.75f : PeckTelegraph))
		{
			bPeckStruck = false;
			bPeckStuck = FMath::FRand() < PeckStuckChance;
			GetCharacterMovement()->AddImpulse(GetActorForwardVector() * 380.f, true);
			PlaySoundAt(StompSound, BeakTip, 0.8f, 1.6f);
			NextStep();
		}
		break;

	case 1: // PECK
		PosePitchTarget = -55.f;
		PoseOffsetTarget = FVector(80.f, 0.f, -120.f);
		PoseSpeed = 22.f;
		if (!bPeckStruck && StepTime >= 0.09f)
		{
			bPeckStruck = true;
			Sparks(BeakTip, 2, 1.f);
			PlaySoundAt(ClangSound, BeakTip, 0.9f, 0.7f);
			if (Player)
			{
				const FVector ToPlayer = Player->GetActorLocation() - GetActorLocation();
				const FVector HullForward = HullPivot->GetForwardVector().GetSafeNormal2D();
				const bool bInFront = FVector::DotProduct(ToPlayer.GetSafeNormal2D(), HullForward) > 0.45f;
				const bool bClose = ToPlayer.Size2D() < PeckRange + 20.f || FVector::Dist(BeakTip, Player->GetActorLocation()) < 220.f;
				if (bInFront && bClose && FMath::Abs(ToPlayer.Z) < 500.f)
				{
					// Note: a parry calls back into ReceiveJediHit (zero damage) from inside ApplyDamage.
					const float Dealt = UGameplayStatics::ApplyDamage(Player, PeckDamage, nullptr, this, nullptr);
					if (Dealt > 0.f && IsTargetable(Player))
					{
						Player->LaunchCharacter(HullForward * PeckKnockback + FVector(0.f, 0.f, 420.f), true, true);
					}
				}
			}
		}
		if (StepTime >= 0.16f)
		{
			NextStep();
		}
		break;

	case 2: // hold... sometimes the beak gets stuck in the floor
	{
		const float Hold = bPeckStuck ? 1.5f : 0.25f;
		PosePitchTarget = -53.f + (bPeckStuck ? 3.f * FMath::Sin(StepTime * 25.f) : 0.f);
		PoseRollTarget = bPeckStuck ? 9.f * FMath::Sin(StepTime * 13.f) : 0.f;
		PoseOffsetTarget = FVector(80.f, 0.f, -120.f);
		PoseSpeed = bPeckStuck ? 14.f : 10.f;
		EyeSquint = bPeckStuck ? 0.4f + 0.6f * FMath::Abs(FMath::Sin(StepTime * 6.f)) : 1.f;
		if (bPeckStuck && FMath::FRand() < Dt * 5.f)
		{
			Sparks(BeakTip, 1, 0.8f);
		}
		if (StepTime >= Hold)
		{
			if (bPeckStuck)
			{
				// Yanks itself free.
				PlaySoundAt(ClangSound, BeakTip, 1.f, 0.5f);
				KickWobble(80.f, 0.f);
			}
			NextStep();
		}
		break;
	}

	default: // recover
		PosePitchTarget = 0.f;
		PoseRollTarget = 0.f;
		PoseOffsetTarget = FVector::ZeroVector;
		PoseSpeed = 4.f;
		if (StepTime >= 0.55f)
		{
			FinishAttack();
		}
		break;
	}
}

void ABossWalker::TickBarrage(float Dt, ACharacter* Player)
{
	switch (StateStep)
	{
	case 0: // rack pops open and blinks red
		if (Player)
		{
			TurnToward(Player->GetActorLocation(), CurrentTurnRate() * 0.5f, Dt);
		}
		RackOpen = FMath::Clamp(StepTime / 0.5f, 0.f, 1.f);
		RackCharge = FMath::Frac(StepTime * 4.f) < 0.5f ? 1.f : 0.25f;
		PosePitchTarget = 7.f;
		PoseOffsetTarget = FVector(-20.f, 0.f, 15.f);
		PoseSpeed = 4.f;
		if (StepTime >= 0.9f)
		{
			MissilesLeft = FMath::RandRange(MissilesMin, FMath::Max(MissilesMin, MissilesMax));
			MissileIndex = 0;
			NextMissileTime = Now();
			NextStep();
		}
		break;

	case 1: // fire everything
		RackOpen = 1.f;
		RackCharge = 1.f;
		if (!Player)
		{
			MissilesLeft = 0;
		}
		else if (MissilesLeft > 0 && Now() >= NextMissileTime)
		{
			LaunchMissile(Player, MissileIndex++);
			--MissilesLeft;
			NextMissileTime += 0.13f;
		}
		if (MissilesLeft <= 0)
		{
			NextStep();
		}
		break;

	default:
		PosePitchTarget = 0.f;
		PoseOffsetTarget = FVector::ZeroVector;
		if (StepTime >= 0.6f)
		{
			NextBarrageTime = Now() + BarrageCooldown;
			FinishAttack();
		}
		break;
	}
}

void ABossWalker::LaunchMissile(ACharacter* Player, int32 Index)
{
	if (!Player || !MissileRack)
	{
		return;
	}
	// First one goes where the player is headed, the rest rain around them.
	FVector Aim = Player->GetActorLocation();
	if (Index == 0)
	{
		Aim += Player->GetVelocity() * (MissileFlightTime * 0.5f);
	}
	else
	{
		const FVector2D Offset = FMath::RandPointInCircle(MissileSpread);
		Aim += FVector(Offset.X, Offset.Y, 0.f) + Player->GetVelocity() * (MissileFlightTime * 0.3f);
	}
	// Keep the rain inside the arena.
	FVector FromCenter = Aim - LeashCenter;
	FromCenter.Z = 0.f;
	const float MaxR = LeashRadius + 400.f;
	if (FromCenter.Size() > MaxR)
	{
		const FVector Clamped = FromCenter.GetSafeNormal() * MaxR;
		Aim.X = LeashCenter.X + Clamped.X;
		Aim.Y = LeashCenter.Y + Clamped.Y;
	}
	const FVector Ground = GroundBelow(Aim);
	const FVector Start = MissileRack->GetComponentTransform().TransformPosition(FVector(FMath::FRandRange(-25.f, 25.f), FMath::FRandRange(-35.f, 35.f), 60.f));

	// Ballistic launch that lands exactly on the warning ring after FlightTime.
	const float FlightTime = FMath::Max(MissileFlightTime * FMath::FRandRange(0.92f, 1.1f), 0.3f);
	const float GravityZ = GetWorld()->GetGravityZ() * MissileGravityScale;
	const FVector Launch = (Ground - Start) / FlightTime - FVector(0.f, 0.f, 0.5f * GravityZ * FlightTime);

	ABlasterBolt* Bolt = SpawnBolt(Start, Launch.Rotation(), MissileDamage, 2.1f, static_cast<float>(Launch.Size()));
	if (!Bolt)
	{
		return;
	}
	if (UProjectileMovementComponent* ProjMove = Bolt->FindComponentByClass<UProjectileMovementComponent>())
	{
		ProjMove->ProjectileGravityScale = MissileGravityScale;
		ProjMove->MaxSpeed = 0.f; // unlimited: it speeds up on the way down
		ProjMove->Velocity = Launch;
	}

	FScrapMissile Missile;
	Missile.Bolt = Bolt;
	Missile.Target = Ground;
	Missile.LastPos = Start;
	Missile.ImpactTime = Now() + FlightTime;
	Missile.Ring = ShowWarningRing(Ground, MissileSplashRadius, FlightTime + 0.1f, ScrapRig::ColWarning, Missile.RingSerial);
	Missiles.Add(Missile);

	PlaySoundAt(FireSound, Start, 0.7f, FMath::FRandRange(0.38f, 0.5f));
	EmitPuff(Start, 0.6f);
	KickWobble(10.f, FMath::FRandRange(-8.f, 8.f));
}

void ABossWalker::UpdateMissiles()
{
	for (int32 i = Missiles.Num() - 1; i >= 0; --i)
	{
		FScrapMissile& Missile = Missiles[i];
		ABlasterBolt* Bolt = Missile.Bolt.Get();
		bool bExplode = false;
		bool bRemove = false;
		if (IsValid(Bolt))
		{
			if (Bolt->bDeflected)
			{
				bRemove = true; // the Jedi sent it back: it is their bolt now, no splash here
			}
			else
			{
				Missile.LastPos = Bolt->GetActorLocation();
				if (Now() > Missile.ImpactTime + 0.6f)
				{
					bExplode = true;
					bRemove = true;
					Bolt->Destroy();
				}
			}
		}
		else
		{
			// It hit something. Splash only if it came down near its mark (not on a pillar halfway there).
			bExplode = FVector::DistSquared(Missile.LastPos, Missile.Target) < FMath::Square(450.f);
			bRemove = true;
		}
		if (bRemove)
		{
			const FVector Where = Missile.LastPos;
			ReleaseRing(Missile.Ring, Missile.RingSerial);
			Missiles.RemoveAtSwap(i);
			if (bExplode)
			{
				ExplodeMissile(Where);
			}
		}
	}
}

void ABossWalker::ExplodeMissile(const FVector& Where)
{
	Sparks(Where, 2, 1.3f);
	PlaySoundAt(ExplodeSound, Where, 0.8f, FMath::FRandRange(0.85f, 1.2f));
	SpawnShockRing(Where + FVector(0.f, 0.f, 6.f), 40.f, MissileSplashRadius, 0.3f, FLinearColor(1.f, 0.3f, 0.05f));
	ShockPlayer(Where, MissileSplashRadius, MissileSplashDamage, 500.f, 380.f, false);
	HurtMinions(Where, MissileSplashRadius, 0.5f, 500.f, 350.f);
}

void ABossWalker::TickStagger(float Dt)
{
	const float A = FMath::Clamp(StateTime / 0.8f, 0.f, 1.f);
	PosePitchTarget = 16.f * (1.f - A);
	PoseOffsetTarget = FVector(-40.f * (1.f - A), 0.f, -30.f * FMath::Sin(A * UE_PI));
	PoseSpeed = 9.f;
	EyeSquint = 1.35f;
	if (StateTime >= 0.85f)
	{
		FinishAttack(0.3f);
	}
}

// ================================================================ damage

float ABossWalker::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bDead)
	{
		return 0.f;
	}
	const float Amount = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	if (Amount <= 0.f)
	{
		return 0.f;
	}

	FVector Location = FVector::ZeroVector;
	FVector Impulse = FVector::ZeroVector;
	bool bHaveLocation = false;
	EJediHitKind Kind = EJediHitKind::Generic;
	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		const FPointDamageEvent& Point = static_cast<const FPointDamageEvent&>(DamageEvent);
		Location = Point.HitInfo.ImpactPoint;
		bHaveLocation = !Location.IsNearlyZero();
		Impulse = Point.ShotDirection * 300.f;
	}
	else if (DamageEvent.IsOfType(FRadialDamageEvent::ClassID))
	{
		const FRadialDamageEvent& Radial = static_cast<const FRadialDamageEvent&>(DamageEvent);
		Location = Radial.Origin;
		bHaveLocation = true;
		Kind = EJediHitKind::Explosion;
	}
	if (!bHaveLocation)
	{
		Location = EstimateHitLocation(DamageCauser);
	}
	if (Impulse.IsNearlyZero() && IsValid(DamageCauser))
	{
		Impulse = (GetActorLocation() - DamageCauser->GetActorLocation()).GetSafeNormal2D() * 300.f;
	}
	return ReceiveJediHit(Amount, DamageCauser, Location, Impulse, Kind);
}

FVector ABossWalker::EstimateHitLocation(AActor* Causer) const
{
	const FVector Center = GetActorLocation();
	if (!IsValid(Causer))
	{
		return Center;
	}
	if (Causer->IsA(ABlasterBolt::StaticClass()))
	{
		return Causer->GetActorLocation();
	}
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const float Radius = GetCapsuleComponent()->GetScaledCapsuleRadius();

	// A deflected bolt reports its deflector as the causer: find the bolt that just reached us.
	if (FVector::Dist2D(Causer->GetActorLocation(), Center) > Radius + 400.f)
	{
		for (TActorIterator<ABlasterBolt> It(GetWorld()); It; ++It)
		{
			if (It->Shooter.Get() == Causer && FVector::Dist2D(It->GetActorLocation(), Center) < Radius + 250.f)
			{
				return It->GetActorLocation();
			}
		}
	}

	// Melee: the point of our capsule facing the attacker, at blade height.
	const FVector Probe = Causer->GetActorLocation() + FVector(0.f, 0.f, 40.f);
	FVector Flat = Probe - Center;
	Flat.Z = 0.f;
	Flat = Flat.GetSafeNormal();
	const double Z = FMath::Clamp(Probe.Z, Center.Z - HalfHeight, Center.Z + HalfHeight);
	return FVector(Center.X, Center.Y, Z) + Flat * Radius;
}

bool ABossWalker::IsFriendlyFire(const AActor* Causer) const
{
	if (!IsValid(Causer) || Causer == this)
	{
		return false;
	}
	const ACharacter* Player = GetPlayer();
	if (Causer == Player)
	{
		return false;
	}
	if (const ABlasterBolt* Bolt = Cast<ABlasterBolt>(Causer))
	{
		const AActor* Shooter = Bolt->Shooter.Get();
		return Shooter && Shooter != Player;
	}
	if (Player && (Causer->GetOwner() == Player || Causer->GetInstigator() == Player))
	{
		return false; // the player's own props / projectiles
	}
	return Causer->IsA(APawn::StaticClass());
}

bool ABossWalker::IsWeakPointHit(const FVector& Location, int32* OutLeg) const
{
	const float Stretch = FMath::Max(WeakPointVerticalStretch, 0.01f);
	for (int32 i = 0; i < 2; ++i)
	{
		FVector Delta = Location - GetKneeLocation(i);
		Delta.Z /= Stretch;
		if (Delta.Size() <= WeakPointRadius)
		{
			if (OutLeg)
			{
				*OutLeg = i;
			}
			return true;
		}
	}
	return false;
}

float ABossWalker::ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
{
	if (bDead)
	{
		return 0.f;
	}
	if (bIgnoreFriendlyFire && IsFriendlyFire(Causer))
	{
		KickWobbleFrom(Impulse, 10.f); // droid bolts just go "tink"
		return 0.f;
	}

	if (Kind == EJediHitKind::ForcePull)
	{
		// Several tonnes of junk do not get yanked. It does wobble in a slightly embarrassed way.
		KickWobbleFrom(Impulse, 130.f);
		PlaySoundAt(ClangSound, HullBody ? HullBody->GetComponentLocation() : GetActorLocation(), 0.5f, 0.45f);
		EyeFlickerUntil = FMath::Max(EyeFlickerUntil, Now() + 0.3f);
		return 0.f;
	}

	if (Damage <= 0.f)
	{
		// Zero-damage shove: a parry knocking the peck aside, or a harmless push.
		if (State == EBossWalkerState::Peck && bPeckStruck)
		{
			bPeckParried = true;
		}
		else if (Kind == EJediHitKind::ForcePush || Impulse.SizeSquared() > FMath::Square(500.f))
		{
			TryStagger(Impulse, false);
		}
		else
		{
			KickWobbleFrom(Impulse, 25.f);
		}
		return 0.f;
	}

	int32 WeakLeg = INDEX_NONE;
	float Mult = HullMultiplier;
	if (State == EBossWalkerState::Collapsed)
	{
		Mult = CollapsedMultiplier;
	}
	else if (Kind == EJediHitKind::Lightning || Kind == EJediHitKind::Storm)
	{
		Mult = 1.f; // fries the electronics, armour or not
	}
	else if (IsWeakPointHit(Location, &WeakLeg))
	{
		Mult = WeakPointMultiplier;
	}

	const float Final = Damage * Mult;
	HP = FMath::Max(0.f, HP - Final);
	if (IsValid(Causer))
	{
		LastDamageCauser = Causer;
	}

	HitFeedback(Location, Kind, WeakLeg, Final);
	if (Kind == EJediHitKind::ForcePush)
	{
		TryStagger(Impulse, false);
	}

	if (HP <= 0.f)
	{
		Die(Causer);
		return Final;
	}

	// Every CollapseStep of health lost: down on its knees.
	const int32 Crossed = FMath::FloorToInt((1.f - HP / FMath::Max(MaxHP, 1.f)) / FMath::Max(CollapseStep, 0.01f) + UE_KINDA_SMALL_NUMBER);
	if (Crossed > CollapsesDone)
	{
		CollapsesDone = Crossed;
		if (State != EBossWalkerState::Collapsed && State != EBossWalkerState::Intro)
		{
			StartCollapse();
		}
	}
	if (!bRage && HP <= MaxHP * RageThreshold)
	{
		if (State == EBossWalkerState::Collapsed)
		{
			bRagePending = true; // gets angry when it stands back up
		}
		else
		{
			EnterRage();
		}
	}
	return Final;
}

void ABossWalker::HitFeedback(const FVector& Location, EJediHitKind Kind, int32 WeakLeg, float Damage)
{
	const bool bWeak = WeakLeg != INDEX_NONE;
	const bool bZap = Kind == EJediHitKind::Lightning || Kind == EJediHitKind::Storm;
	const bool bDown = State == EBossWalkerState::Collapsed;
	const float T = Now();

	const int32 PartIndex = bWeak ? KneePart[FMath::Clamp(WeakLeg, 0, 1)] : FindNearestPart(Location);
	const FLinearColor FlashColor = bWeak ? FLinearColor(4.f, 3.4f, 2.6f)
		: bDown ? FLinearColor(3.f, 1.8f, 0.8f)
		: bZap ? FLinearColor(0.8f, 1.2f, 4.f)
		: FLinearColor(1.4f, 0.55f, 0.15f);
	Flash(PartIndex, FlashColor, 1.f);

	if (bZap)
	{
		EyeFlickerUntil = FMath::Max(EyeFlickerUntil, T + 0.25f);
		if (T - LastSparkTime > 0.15f)
		{
			LastSparkTime = T;
			Sparks(Location, 1, 0.8f);
		}
	}
	else
	{
		Sparks(Location, bWeak ? 2 : 1, bWeak ? 1.4f : 0.9f);
		if (T - LastClangTime > 0.06f)
		{
			LastClangTime = T;
			// Knees ring high and bright; armour goes "tonk".
			const float Pitch = bWeak ? FMath::FRandRange(1.15f, 1.3f) : bDown ? FMath::FRandRange(0.85f, 1.f) : FMath::FRandRange(0.55f, 0.7f);
			PlaySoundAt(ClangSound, Location, bWeak ? 1.f : 0.75f, Pitch);
		}
	}

	KickWobbleFrom(GetActorLocation() - Location, bWeak ? 60.f : 20.f);
	if (bWeak)
	{
		DipVel -= 140.f; // the knee buckles a little
	}

	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		if (bWeak)
		{
			Director->AddHype(1.5f);
		}
		else if (Damage >= 3.f)
		{
			Director->AddHype(Damage * 0.5f);
		}
	}
}

int32 ABossWalker::FindNearestPart(const FVector& Location) const
{
	int32 Best = INDEX_NONE;
	double BestDist = TNumericLimits<double>::Max();
	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		const FScrapPart& Part = Parts[i];
		if (!Part.Mesh || Part.bDetached)
		{
			continue;
		}
		const double Dist = FVector::Dist(Part.Mesh->Bounds.Origin, Location) - Part.Mesh->Bounds.SphereRadius * 0.5;
		if (Dist < BestDist)
		{
			BestDist = Dist;
			Best = i;
		}
	}
	return Best;
}

void ABossWalker::TryStagger(const FVector& Impulse, bool bForce)
{
	KickWobbleFrom(Impulse, 140.f);
	if (bDead || State == EBossWalkerState::Collapsed || State == EBossWalkerState::Intro || State == EBossWalkerState::Dead)
	{
		return;
	}
	if (!bForce && Now() < StaggerImmuneUntil)
	{
		return;
	}
	StaggerImmuneUntil = Now() + 3.5f;
	CancelAttack();
	SetState(EBossWalkerState::Stagger);
	FVector Shove = Impulse;
	Shove.Z = 0.f;
	if (!Shove.IsNearlyZero())
	{
		GetCharacterMovement()->AddImpulse(Shove.GetSafeNormal() * 280.f, true);
	}
	PlaySoundAt(ClangSound, HullBody ? HullBody->GetComponentLocation() : GetActorLocation(), 0.8f, 0.5f);
	EyeFlickerUntil = FMath::Max(EyeFlickerUntil, Now() + 0.6f);
}

void ABossWalker::StartCollapse()
{
	CancelAttack();
	SetState(EBossWalkerState::Collapsed);
	const FVector Core = HullBody ? HullBody->GetComponentLocation() : GetActorLocation();
	KickWobble(-50.f, FMath::FRandRange(-40.f, 40.f));
	PlaySoundAt(ExplodeSound, Core, 0.9f, 0.6f);
	PlaySoundAt(ClangSound, Core, 1.f, 0.4f);
	Sparks(Core, 3, 1.5f);
	EyeFlickerUntil = Now() + CollapseDuration;
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->Announce(TEXT("IT'S DOWN! HIT IT WHILE IT'S DOWN!"), 2.2f, FLinearColor(1.f, 0.6f, 0.15f));
		Director->AddHype(8.f);
	}
}

void ABossWalker::TickCollapse(float Dt)
{
	PosePitchTarget = 0.f;
	PoseRollTarget = 0.f;
	PoseOffsetTarget = FVector::ZeroVector;
	PoseSpeed = 4.f;

	if (StateStep == 0)
	{
		const float Before = CollapseAlpha;
		CollapseAlpha = FMath::Min(1.f, CollapseAlpha + Dt / 0.45f);
		if (Before < 1.f && CollapseAlpha >= 1.f)
		{
			// Knees hit the floor.
			DipVel -= 500.f;
			KickWobble(-40.f, 20.f);
			for (int32 i = 0; i < 2; ++i)
			{
				const FVector Knee = GetKneeLocation(i);
				Sparks(Knee, 2, 1.2f);
				PlaySoundAt(ExplodeSound, Knee, 0.7f, 0.4f);
			}
			Shake(GetActorLocation(), 400.f, 2500.f);
		}
		// Sparks and smoke while it is down.
		if (Parts.Num() > 0 && FMath::FRand() < Dt * 3.f)
		{
			const int32 Index = FMath::RandRange(0, Parts.Num() - 1);
			if (Parts[Index].Mesh && !Parts[Index].bDetached)
			{
				Sparks(Parts[Index].Mesh->Bounds.Origin, 1, 1.f);
			}
		}
		if (StepTime >= CollapseDuration)
		{
			NextStep();
			PlaySoundAt(ClangSound, HullBody->GetComponentLocation(), 0.8f, 0.35f);
		}
		return;
	}

	// Stand back up.
	CollapseAlpha = FMath::Max(0.f, CollapseAlpha - Dt / 0.9f);
	if (CollapseAlpha <= 0.f)
	{
		// Shrug-off pulse so it can't be juggled forever.
		const FVector Feet = GetActorLocation() - FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
		SpawnShockRing(Feet + FVector(0.f, 0.f, 8.f), 60.f, 480.f, 0.35f, FLinearColor(1.f, 0.7f, 0.3f));
		ShockPlayer(Feet, 480.f, 0.f, 900.f, 350.f, true);
		HurtMinions(Feet, 480.f, 0.25f, 600.f, 300.f);
		PlaySoundAt(StompSound, Feet, 1.f, 0.8f);
		KickWobble(40.f, 0.f);
		StaggerImmuneUntil = Now() + 2.f;
		if (bRagePending)
		{
			EnterRage();
		}
		LastAttack = EBossWalkerState::Collapsed;
		SetState(EBossWalkerState::Roam);
		NextAttackTime = Now() + 1.f;
	}
}

void ABossWalker::EnterRage()
{
	if (bRage)
	{
		return;
	}
	bRage = true;
	bRagePending = false;
	if (Parts.IsValidIndex(EyeLPart))
	{
		Parts[EyeLPart].Emissive = ScrapRig::ColRageEyes;
		Parts[EyeLPart].bDirty = true;
	}
	if (Parts.IsValidIndex(EyeRPart))
	{
		Parts[EyeRPart].Emissive = ScrapRig::ColRageEyes * 0.8f;
		Parts[EyeRPart].bDirty = true;
	}
	NextBarrageTime = Now() + 1.5f;
	KickWobble(30.f, 0.f);
	PlaySoundAt(ExplodeSound, HullBody->GetComponentLocation(), 0.6f, 0.5f);
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->Announce(TEXT("THE COLOSSUS IS FURIOUS! (AND LEAKING OIL)"), 3.f, FLinearColor(1.f, 0.15f, 0.05f));
		Director->AddHype(10.f);
	}
}

// ================================================================ death

void ABossWalker::Die(AActor* Killer)
{
	if (bDead)
	{
		return;
	}
	bDead = true;
	HP = 0.f;
	KillerActor = IsValid(Killer) ? Killer : LastDamageCauser.Get();
	CancelAttack();
	SetState(EBossWalkerState::Dead);
	DeathElapsed = 0.f;
	NextDeathBoom = 0.f;
	SetCanBeDamaged(false);
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->StopMovementImmediately();
		Move->DisableMovement(); // MOVE_None: also stops the Jedi's auto-targeting
	}
	EyeFlickerUntil = Now() + DeathSequenceTime + 1.f;
	KickWobble(-60.f, 50.f);
	PlaySoundAt(ExplodeSound, HullBody->GetComponentLocation(), 1.f, 0.7f);
}

void ABossWalker::TickDeath(float Dt)
{
	DeathElapsed += Dt;
	const float Total = FMath::Max(DeathSequenceTime, 0.1f);
	const float A = FMath::Clamp(DeathElapsed / Total, 0.f, 1.f);

	// Legs give out while it shakes itself to bits.
	CollapseAlpha = FMath::Max(CollapseAlpha, FMath::Min(1.f, A * 1.25f));
	PosePitchTarget = FMath::FRandRange(-6.f, 6.f) * A;
	PoseRollTarget = FMath::FRandRange(-8.f, 8.f) * A;
	PoseOffsetTarget = FVector::ZeroVector;
	PoseSpeed = 18.f;

	// A chain of small explosions.
	if (DeathElapsed >= NextDeathBoom && DeathElapsed < Total && Parts.Num() > 0)
	{
		NextDeathBoom = DeathElapsed + FMath::FRandRange(0.16f, 0.3f);
		for (int32 Try = 0; Try < 6; ++Try)
		{
			const int32 Index = FMath::RandRange(0, Parts.Num() - 1);
			if (Parts[Index].Mesh && !Parts[Index].bDetached)
			{
				const FVector P = Parts[Index].Mesh->Bounds.Origin + FMath::VRand() * 30.f;
				Sparks(P, 2, 1.2f);
				PlaySoundAt(ExplodeSound, P, 0.55f, FMath::FRandRange(0.9f, 1.4f));
				Flash(Index, FLinearColor(4.f, 2.5f, 1.f));
				KickWobble(FMath::FRandRange(-60.f, 60.f), FMath::FRandRange(-60.f, 60.f));
				EmitPuff(P, 0.8f);
				break;
			}
		}
	}

	// Loose bits pop off early.
	const FVector Core = HullPivot->GetComponentLocation();
	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		const FScrapPart& Part = Parts[i];
		if (!Part.bDetached && Part.DebrisDelay > 0.f && Part.DebrisDelay < Total && DeathElapsed >= Part.DebrisDelay)
		{
			PopPart(i, Core, 0.8f);
		}
	}

	if (DeathElapsed >= Total)
	{
		FinalBlast();
	}
}

void ABossWalker::FinalBlast()
{
	if (bFinalBlast)
	{
		return;
	}
	bFinalBlast = true;
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	const FVector Core = HullPivot->GetComponentLocation();
	const FVector Feet = GetActorLocation() - FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());

	// One last, very big boom.
	for (int32 i = 0; i < 6; ++i)
	{
		Sparks(Core + FMath::VRand() * FMath::FRandRange(40.f, 220.f), 2, 2.f);
	}
	PlaySoundAt(ExplodeSound, Core, 1.8f, 0.5f);
	PlaySoundAt(ExplodeSound, Core, 1.2f, 0.8f);
	PlaySoundAt(StompSound, Core, 1.2f, 0.45f);
	SpawnShockRing(Feet + FVector(0.f, 0.f, 10.f), 100.f, 1100.f, 0.6f, ScrapRig::ColShock);
	SpawnShockRing(Core, 50.f, 650.f, 0.45f, FLinearColor(1.f, 0.8f, 0.4f));
	Shake(Core, 800.f, 4000.f);
	ShockPlayer(Feet, 900.f, 0.f, 700.f, 400.f, false);
	HurtMinions(Feet, 900.f, 1.f, 900.f, 600.f);

	// Lights out.
	for (int32 i = 0; i < 2; ++i)
	{
		if (Parts.IsValidIndex(KneePart[i]))
		{
			Parts[KneePart[i]].Emissive = FLinearColor(0.3f, 0.05f, 0.f);
			Parts[KneePart[i]].Pulse = 1.f;
			Parts[KneePart[i]].bDirty = true;
		}
	}
	for (int32 Index : { EyeLPart, EyeRPart })
	{
		if (Parts.IsValidIndex(Index))
		{
			Parts[Index].Emissive = FLinearColor::Black;
			Parts[Index].bDirty = true;
		}
	}

	// Everything flies apart...
	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		if (!Parts[i].bDetached && Parts[i].DebrisDelay >= 0.f)
		{
			PopPart(i, Core, 1.f);
		}
	}
	// ...and the head (with its eyes) pops off and bounces.
	if (HullBody && Parts.IsValidIndex(HullPart) && HullBody->IsSimulatingPhysics())
	{
		HullBody->SetPhysicsLinearVelocity(FVector(FMath::FRandRange(-250.f, 250.f), FMath::FRandRange(-250.f, 250.f), 1500.f));
		HullBody->SetPhysicsAngularVelocityInDegrees(FVector(FMath::FRandRange(-200.f, 200.f), FMath::FRandRange(-300.f, 300.f), FMath::FRandRange(-150.f, 150.f)));
		HullBody->SetNotifyRigidBodyCollision(true);
		HullBody->OnComponentHit.AddDynamic(this, &ABossWalker::OnHeadHit);
		HeadPrevVelocity = FVector(0.f, 0.f, 1500.f);
	}

	ReportKO();
	SetLifeSpan(FMath::Max(DebrisLifetime, 1.f));
}

void ABossWalker::PopPart(int32 Index, const FVector& Origin, float Strength)
{
	if (!Parts.IsValidIndex(Index))
	{
		return;
	}
	FScrapPart& Part = Parts[Index];
	UStaticMeshComponent* PartMesh = Part.Mesh;
	if (!PartMesh || Part.bDetached)
	{
		return;
	}
	Part.bDetached = true;
	PartMesh->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
	PartMesh->SetCollisionProfileName(UCollisionProfile::PhysicsActor_ProfileName);
	PartMesh->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	PartMesh->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	PartMesh->SetGenerateOverlapEvents(false);
	PartMesh->SetSimulatePhysics(true);

	FVector Out = PartMesh->GetComponentLocation() - Origin;
	Out = Out.IsNearlyZero() ? FMath::VRand() : Out.GetSafeNormal();
	const FVector Velocity = (Out * FMath::FRandRange(300.f, 750.f) + FVector(0.f, 0.f, FMath::FRandRange(350.f, 850.f)) + FMath::VRand() * 120.f) * Strength;
	PartMesh->SetPhysicsLinearVelocity(Velocity);
	PartMesh->SetPhysicsAngularVelocityInDegrees(FMath::VRand() * FMath::FRandRange(90.f, 420.f));
}

void ABossWalker::OnHeadHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
	if (!HitComp || HeadBounces >= 3 || Now() - LastBounceTime < 0.2f)
	{
		return;
	}
	// Physics has already resolved the contact, so use the velocity from before the impact.
	const float ImpactSpeed = static_cast<float>(-HeadPrevVelocity.Z);
	if (ImpactSpeed < 300.f || Hit.ImpactNormal.Z < 0.5f)
	{
		return;
	}
	LastBounceTime = Now();
	++HeadBounces;
	HitComp->SetPhysicsLinearVelocity(FVector(HeadPrevVelocity.X * 0.7f, HeadPrevVelocity.Y * 0.7f, ImpactSpeed * 0.62f));
	HitComp->SetPhysicsAngularVelocityInDegrees(FMath::VRand() * 300.f, true);
	PlaySoundAt(ClangSound, Hit.ImpactPoint, 1.f, 0.4f + 0.12f * HeadBounces);
	Sparks(Hit.ImpactPoint, 2, 1.2f);
}

void ABossWalker::ReportKO()
{
	if (bKOReported)
	{
		return;
	}
	bKOReported = true;
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->NotifyKO(this, KillerActor.Get(), KOValue);
		Director->Announce(TEXT("COLOSSUS SCRAPPED!"), 3.5f, FLinearColor(1.f, 0.55f, 0.1f));
		Director->AddHype(40.f);
	}
}

// ================================================================ procedural animation

FVector ABossWalker::NeutralFoot(int32 Leg) const
{
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	return GetActorTransform().TransformPosition(FVector(ScrapRig::NeutralFootX, Legs[Leg].Side * ScrapRig::HipSpread, -HalfHeight));
}

FVector ABossWalker::LandingTarget(int32 Leg) const
{
	FVector Target = NeutralFoot(Leg);
	FVector Velocity = GetVelocity();
	Velocity.Z = 0.f;
	const float Speed = static_cast<float>(Velocity.Size());
	if (Speed > 5.f)
	{
		// Land ahead of the hip so the foot passes under it mid-stance.
		const float Reach = 0.3f * StrideLength * FMath::Clamp(Speed / 150.f, 0.f, 1.f);
		Target += Velocity / Speed * Reach;
	}
	return Target;
}

void ABossWalker::UpdateGait(float Dt)
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	FVector Velocity = GetVelocity();
	Velocity.Z = 0.f;
	const float Speed = static_cast<float>(Velocity.Size());
	WalkAlpha = FMath::FInterpTo(WalkAlpha, FMath::Clamp(Speed / FMath::Max(WalkSpeed, 1.f), 0.f, 1.f), Dt, 4.f);

	const float Yaw = static_cast<float>(GetActorRotation().Yaw);
	const float YawDelta = FMath::Abs(static_cast<float>(FMath::FindDeltaAngleDegrees(PrevYaw, Yaw)));
	PrevYaw = Yaw;

	if (Move && Move->IsFalling())
	{
		// Airborne (intro drop): legs dangle, toes down.
		for (int32 i = 0; i < 2; ++i)
		{
			FLegState& Leg = Legs[i];
			const FVector Hang = NeutralFoot(i) + GetActorForwardVector() * 35.f + FVector(0.f, 0.f, 90.f);
			Leg.FootPos = Hang;
			Leg.bSwinging = false;
			Leg.Ankle3D = Hang + FVector(0.f, 0.f, ScrapRig::AnkleHeight);
			Leg.FootPitch = -18.f;
		}
		return;
	}

	// Walk cycle phase is driven by distance travelled (and by turning on the spot), so planted feet never skate.
	float Advance = (Speed * Dt) / FMath::Max(StrideLength, 10.f) + YawDelta / FMath::Max(TurnStrideDegrees, 1.f);
	const bool bAnySwing = Legs[0].bSwinging || Legs[1].bSwinging;
	float MaxError = 0.f;
	for (int32 i = 0; i < 2; ++i)
	{
		MaxError = FMath::Max(MaxError, static_cast<float>(FVector::Dist2D(Legs[i].FootPos, NeutralFoot(i))));
	}
	const bool bCanRecentre = !bDead && State != EBossWalkerState::Collapsed;
	if (bAnySwing || (bCanRecentre && MaxError > 70.f))
	{
		Advance = FMath::Max(Advance, Dt / 1.3f); // finish a step in progress / tidy up stray feet
	}
	if (bGaitHold)
	{
		Advance = 0.f;
	}
	GaitPhase = FMath::Frac(GaitPhase + FMath::Min(Advance, 0.08f));

	const float Lift = bRage ? StepHeight * 1.15f : StepHeight;
	for (int32 i = 0; i < 2; ++i)
	{
		FLegState& Leg = Legs[i];
		if (Leg.bOverride)
		{
			Leg.Ankle3D = Leg.OverrideAnkle;
			continue;
		}
		const float LegPhase = FMath::Frac(GaitPhase + (i == 0 ? 0.f : 0.5f));
		const bool bShouldSwing = !bGaitHold && LegPhase < ScrapRig::SwingFraction;
		if (bShouldSwing && !Leg.bSwinging)
		{
			Leg.bSwinging = true;
			Leg.SwingFrom = Leg.FootPos;
		}
		else if (!bShouldSwing && Leg.bSwinging)
		{
			Leg.bSwinging = false;
			Leg.FootPos = LandingTarget(i);
			OnFootPlanted(i);
		}

		if (Leg.bSwinging)
		{
			const float U = FMath::Clamp(LegPhase / ScrapRig::SwingFraction, 0.f, 1.f);
			const float S = U * U * (3.f - 2.f * U);
			Leg.SwingTo = LandingTarget(i);
			const FVector P = FMath::Lerp(Leg.SwingFrom, Leg.SwingTo, S);
			Leg.Ankle3D = P + FVector(0.f, 0.f, ScrapRig::AnkleHeight + Lift * FMath::Sin(U * UE_PI));
			Leg.FootPitch = 14.f * FMath::Sin(U * UE_PI);
		}
		else
		{
			Leg.Ankle3D = Leg.FootPos + FVector(0.f, 0.f, ScrapRig::AnkleHeight);
			Leg.FootPitch = FMath::FInterpTo(Leg.FootPitch, 0.f, Dt, 10.f);
		}
	}
}

void ABossWalker::OnFootPlanted(int32 Leg)
{
	const FVector Foot = Legs[Leg].FootPos;
	const float T = Now();
	DipVel -= 90.f + 60.f * WalkAlpha;
	KickWobble(-6.f * WalkAlpha, Legs[Leg].Side * 10.f * WalkAlpha);
	// Heavy thud, plus the odd rattle of loose junk.
	PlaySoundAt(ExplodeSound, Foot, 0.18f + 0.12f * WalkAlpha, FMath::FRandRange(0.3f, 0.38f));
	if (FMath::FRand() < 0.35f)
	{
		PlaySoundAt(ClangSound, Foot + FVector(0.f, 0.f, 200.f), 0.25f, FMath::FRandRange(0.35f, 0.5f));
	}
	if (bRage)
	{
		Shake(Foot, 300.f, 1800.f);
	}

	// Every so often it trips over its own feet.
	if (State == EBossWalkerState::Roam && WalkAlpha > 0.6f && T >= NextStumbleTime)
	{
		NextStumbleTime = T + FMath::FRandRange(StumbleInterval.X, StumbleInterval.Y);
		StumbleUntil = T + 0.9f;
		KickWobble(-110.f, Legs[Leg].Side * 90.f);
		DipVel -= 420.f;
		PlaySoundAt(ClangSound, Foot + FVector(0.f, 0.f, 200.f), 0.9f, 0.42f);
		Sparks(GetKneeLocation(Leg), 2, 1.f);
		if (IsLive(ExhaustL))
		{
			EmitPuff(ExhaustL->GetComponentTransform().TransformPosition(FVector(0.f, 0.f, 55.f)), 1.3f);
		}
		if (AHordeDirector* Director = AHordeDirector::Get(this))
		{
			Director->AddHype(2.f); // the crowd laughs
		}
	}
}

void ABossWalker::UpdatePose(float Dt)
{
	// Ease the attack pose toward what the state asked for.
	PoseOffset = FMath::VInterpTo(PoseOffset, PoseOffsetTarget, Dt, PoseSpeed);
	PosePitch = FMath::FInterpTo(PosePitch, PosePitchTarget, Dt, PoseSpeed);
	PoseRoll = FMath::FInterpTo(PoseRoll, PoseRollTarget, Dt, PoseSpeed);
	if (State != EBossWalkerState::Collapsed && State != EBossWalkerState::Dead)
	{
		CollapseAlpha = FMath::FInterpTo(CollapseAlpha, 0.f, Dt, 3.f);
	}

	// Springs: a bouncy cockpit wobble and a hip dip on impacts.
	WobbleVel += (Wobble * -70.f - WobbleVel * 6.f) * Dt;
	Wobble += WobbleVel * Dt;
	Wobble.X = FMath::Clamp(Wobble.X, -35.0, 35.0);
	Wobble.Y = FMath::Clamp(Wobble.Y, -35.0, 35.0);
	DipVel += (-Dip * 90.f - DipVel * 11.f) * Dt;
	Dip = FMath::Clamp(Dip + DipVel * Dt, -140.f, 60.f);

	// Walk-cycle bob (lowest just after each foot lands) and sway toward the planted leg.
	const float Cycle = GaitPhase * UE_TWO_PI;
	const float Bob = BobAmount * (0.5f - (0.5f + 0.5f * FMath::Cos(2.f * (Cycle - 0.45f * UE_TWO_PI)))) * WalkAlpha;
	const float Sway = SwayDegrees * FMath::Sin(Cycle) * WalkAlpha;
	const float Waddle = 3.f * FMath::Sin(Cycle) * WalkAlpha;

	float HipZ = HipHeight + static_cast<float>(PoseOffset.Z) + Bob + Dip;
	HipZ = FMath::Lerp(HipZ, CollapsedHipHeight + Dip * 0.3f, CollapseAlpha);
	Pelvis->SetRelativeLocation(FVector(PoseOffset.X, 0.f, HipZ));

	// The cockpit looks at the player a little ahead of the body.
	float YawTarget = 0.f;
	if (!bDead && State != EBossWalkerState::Collapsed)
	{
		const ACharacter* Player = GetPlayer();
		if (IsTargetable(Player))
		{
			const float Desired = static_cast<float>((Player->GetActorLocation() - GetActorLocation()).Rotation().Yaw);
			YawTarget = FMath::Clamp(static_cast<float>(FMath::FindDeltaAngleDegrees(static_cast<float>(GetActorRotation().Yaw), Desired)), -35.f, 35.f);
		}
	}
	HullYaw = FMath::FInterpConstantTo(HullYaw, YawTarget, Dt, bRage ? 140.f : 90.f);

	const float Pitch = PosePitch + static_cast<float>(Wobble.X) - 4.f * WalkAlpha - 16.f * CollapseAlpha;
	const float Roll = PoseRoll + static_cast<float>(Wobble.Y) + Sway + 7.f * CollapseAlpha;
	HullPivot->SetRelativeRotation(FRotator(Pitch, HullYaw + Waddle, Roll));
}

void ABossWalker::SolveLegs()
{
	if (!Pelvis)
	{
		return;
	}
	const FTransform PelvisXf = Pelvis->GetComponentTransform();
	for (int32 i = 0; i < 2; ++i)
	{
		FLegState& Leg = Legs[i];
		if (!Leg.Hip || !Leg.Knee || !Leg.Ankle)
		{
			continue;
		}
		// Work in the pelvis frame (X forward, Z up); the leg bends in its own X/Z plane.
		const FVector Local = PelvisXf.InverseTransformPosition(Leg.Ankle3D);
		const FVector HipLocal = Leg.Hip->GetRelativeLocation();
		float ThighDeg = 0.f;
		float ShinDeg = 0.f;
		ScrapRig::SolveTwoBone(static_cast<float>(Local.X - HipLocal.X), static_cast<float>(Local.Z - HipLocal.Z), ThighDeg, ShinDeg);
		// Pitch P points a pivot's -Z axis along (sin P, 0, -cos P): exactly our "angle from straight down".
		Leg.Hip->SetRelativeRotation(FRotator(ThighDeg, 0.f, 0.f));
		Leg.Knee->SetRelativeRotation(FRotator(ShinDeg - ThighDeg, 0.f, 0.f));
		Leg.Ankle->SetRelativeRotation(FRotator(Leg.FootPitch - ShinDeg, 0.f, 0.f));
	}
}

void ABossWalker::UpdateDetails(float Dt)
{
	const float T = Now();

	// Radar dish: lazy sweep, frantic in rage, stalled when knocked down.
	const float RadarRate = (bDead || State == EBossWalkerState::Collapsed) ? 0.f : (bRage ? 320.f : 75.f);
	RadarYaw = FMath::Fmod(RadarYaw + RadarRate * Dt, 360.f);
	RadarPivot->SetRelativeRotation(FRotator(0.f, RadarYaw, 0.f));

	// Flag flaps harder while walking.
	FlagPivot->SetRelativeRotation(FRotator(0.f, (14.f + 16.f * WalkAlpha) * FMath::Sin(T * 7.f) + 6.f * FMath::Sin(T * 12.3f), 4.f * FMath::Sin(T * 5.1f)));

	// Hula bobblehead on the dashboard.
	HulaPivot->SetRelativeRotation(FRotator(6.f * FMath::Sin(T * 4.3f) + static_cast<float>(Wobble.X) * 1.5f, 0.f,
		(10.f + 12.f * WalkAlpha) * FMath::Sin(T * 5.7f) + static_cast<float>(Wobble.Y) * 2.f));
	if (IsLive(HulaHead))
	{
		HulaHead->SetRelativeLocation(HulaHeadBase + FVector(3.f * FMath::Sin(T * 7.3f), 3.f * FMath::Sin(T * 6.1f + 1.f), 1.5f * FMath::Sin(T * 11.f)));
	}

	// Cannon recoil and charge glow.
	for (int32 i = 0; i < 2; ++i)
	{
		Recoil[i] = FMath::FInterpTo(Recoil[i], 0.f, Dt, 9.f);
		UStaticMeshComponent* Cannon = i == 0 ? CannonL.Get() : CannonR.Get();
		if (IsLive(Cannon))
		{
			Cannon->SetRelativeLocation(CannonBase[i] - FVector(Recoil[i], 0.f, 0.f));
		}
		if (Parts.IsValidIndex(CannonPart[i]))
		{
			Parts[CannonPart[i]].Emissive = FLinearColor(1.f, 0.35f, 0.05f) * (CannonCharge * 16.f);
			Parts[CannonPart[i]].bDirty = true;
		}
	}

	// Missile rack.
	if (State != EBossWalkerState::Barrage)
	{
		RackOpen = FMath::FInterpTo(RackOpen, 0.f, Dt, 3.f);
		RackCharge = FMath::FInterpTo(RackCharge, 0.f, Dt, 3.f);
	}
	if (IsLive(MissileRack))
	{
		MissileRack->SetRelativeRotation(RackBaseRot + FRotator(28.f * RackOpen, 0.f, 0.f));
	}
	if (Parts.IsValidIndex(RackPart))
	{
		Parts[RackPart].Emissive = FLinearColor(1.f, 0.05f, 0.02f) * (RackCharge * 10.f);
		Parts[RackPart].bDirty = true;
	}

	// Knee weak points pulse (fast in rage, frantic while it is down).
	for (int32 i = 0; i < 2; ++i)
	{
		if (Parts.IsValidIndex(KneePart[i]))
		{
			FScrapPart& Knee = Parts[KneePart[i]];
			Knee.Pulse = State == EBossWalkerState::Collapsed ? 1.3f + 0.5f * FMath::Sin(T * 14.f)
				: 0.75f + 0.25f * FMath::Sin(T * (bRage ? 9.f : 4.f) + i * 1.7f);
			Knee.bDirty = true;
		}
	}

	// Eyes: blink, squint, flicker when zapped / dazed.
	if (T >= NextBlinkTime)
	{
		BlinkUntil = T + 0.12f;
		NextBlinkTime = T + FMath::FRandRange(2.5f, 6.f);
	}
	const bool bBlink = T < BlinkUntil;
	const float Squint = bBlink ? 0.12f : EyeSquint;
	EyeL->SetRelativeScale3D(EyeLBaseScale * FVector(1.f, 1.f, Squint));
	EyeR->SetRelativeScale3D(EyeRBaseScale * FVector(1.f, 1.f, bBlink ? 0.12f : Squint * (1.f + 0.08f * FMath::Sin(T * 3.f))));
	const bool bFlicker = T < EyeFlickerUntil;
	for (int32 Index : { EyeLPart, EyeRPart })
	{
		if (Parts.IsValidIndex(Index))
		{
			// Irregular sputter (not a per-frame strobe): the bulbs are loose.
			const bool bOff = FMath::Sin(T * 31.f + Index * 2.3f) + FMath::Sin(T * 17.f) > 0.6f;
			Parts[Index].Pulse = bFlicker ? (bOff ? 0.08f : 1.25f) : 1.f;
			Parts[Index].bDirty = true;
		}
	}
	EyeSquint = 1.f; // states set it again each tick

	// Exhaust stacks puff cartoon smoke (a lot more when angry or hurt).
	const float Interval = bDead ? 0.12f : State == EBossWalkerState::Collapsed ? 0.2f : bRage ? 0.45f : (WalkAlpha > 0.3f ? 0.9f : 1.6f);
	if (T >= NextPuffTime)
	{
		NextPuffTime = T + Interval * FMath::FRandRange(0.8f, 1.2f);
		PuffSide = 1 - PuffSide;
		UStaticMeshComponent* Pipe = PuffSide == 0 ? ExhaustL.Get() : ExhaustR.Get();
		if (Pipe)
		{
			EmitPuff(Pipe->GetComponentTransform().TransformPosition(FVector(0.f, 0.f, 55.f)), (bRage || State == EBossWalkerState::Collapsed) ? 1.1f : 0.8f);
			ExhaustKick[PuffSide] = 1.f;
		}
	}
	for (int32 i = 0; i < 2; ++i)
	{
		ExhaustKick[i] = FMath::FInterpTo(ExhaustKick[i], 0.f, Dt, 8.f);
		UStaticMeshComponent* Pipe = i == 0 ? ExhaustL.Get() : ExhaustR.Get();
		if (IsLive(Pipe))
		{
			const float K = ExhaustKick[i];
			Pipe->SetRelativeScale3D(ExhaustBaseScale[i] * FVector(1.f + 0.25f * K, 1.f + 0.25f * K, 1.f + 0.08f * K));
		}
	}
}

void ABossWalker::UpdateFlashes(float Dt)
{
	static const FName EmissiveName(TEXT("Emissive"));
	for (FScrapPart& Part : Parts)
	{
		if (Part.Flash > 0.f)
		{
			Part.Flash = FMath::Max(0.f, Part.Flash - Dt * 5.5f);
			Part.bDirty = true;
		}
		if (!Part.bDirty || !Part.MID)
		{
			continue;
		}
		Part.bDirty = false;
		Part.MID->SetVectorParameterValue(EmissiveName, Part.Emissive * Part.Pulse + Part.FlashColor * (Part.Flash * 3.f));
	}
}

// ================================================================ rings & puffs

int32 ABossWalker::AcquireRing()
{
	for (int32 i = 0; i < Rings.Num(); ++i)
	{
		if (!Rings[i].bActive && Rings[i].Mesh)
		{
			return i;
		}
	}
	if (!SphereMesh || Rings.Num() >= 20)
	{
		return INDEX_NONE;
	}
	UStaticMeshComponent* RingMesh = NewObject<UStaticMeshComponent>(this);
	RingMesh->SetStaticMesh(SphereMesh);
	RingMesh->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
	RingMesh->SetGenerateOverlapEvents(false);
	RingMesh->SetCastShadow(false);
	RingMesh->SetCanEverAffectNavigation(false);
	RingMesh->SetUsingAbsoluteLocation(true);
	RingMesh->SetUsingAbsoluteRotation(true);
	RingMesh->SetUsingAbsoluteScale(true);
	RingMesh->SetupAttachment(GetRootComponent());
	RingMesh->RegisterComponent();
	RingMesh->SetVisibility(false);

	FScrapRing Ring;
	Ring.Mesh = RingMesh;
	if (WaveMaterial)
	{
		Ring.MID = RingMesh->CreateDynamicMaterialInstance(0, WaveMaterial);
	}
	return Rings.Add(Ring);
}

int32 ABossWalker::ShowWarningRing(const FVector& Center, float Radius, float Duration, const FLinearColor& Color, int32& OutSerial)
{
	OutSerial = 0;
	const int32 Index = AcquireRing();
	if (Index == INDEX_NONE)
	{
		return INDEX_NONE;
	}
	FScrapRing& Ring = Rings[Index];
	Ring.bActive = true;
	Ring.bShockwave = false;
	Ring.Center = Center + FVector(0.f, 0.f, 4.f);
	Ring.Color = Color;
	Ring.Start = Now();
	Ring.Duration = FMath::Max(Duration, 0.05f);
	Ring.Radius0 = Radius * 1.35f; // closes in on the impact point
	Ring.Radius1 = Radius;
	Ring.Height0 = 8.f;
	Ring.Height1 = 8.f;
	Ring.Intensity = 7.f;
	Ring.Serial = ++RingSerialCounter;
	OutSerial = Ring.Serial;
	if (Ring.MID)
	{
		Ring.MID->SetVectorParameterValue(TEXT("WaveColor"), Color);
		Ring.MID->SetScalarParameterValue(TEXT("Fade"), 0.f);
	}
	Ring.Mesh->SetWorldLocationAndRotation(Ring.Center, FRotator::ZeroRotator);
	Ring.Mesh->SetWorldScale3D(FVector(Ring.Radius0 / 50.f, Ring.Radius0 / 50.f, Ring.Height0 / 100.f));
	Ring.Mesh->SetVisibility(true);
	return Index;
}

void ABossWalker::SpawnShockRing(const FVector& Center, float Radius0, float Radius1, float Duration, const FLinearColor& Color)
{
	const int32 Index = AcquireRing();
	if (Index == INDEX_NONE)
	{
		return;
	}
	FScrapRing& Ring = Rings[Index];
	Ring.bActive = true;
	Ring.bShockwave = true;
	Ring.Center = Center;
	Ring.Color = Color;
	Ring.Start = Now();
	Ring.Duration = FMath::Max(Duration, 0.05f);
	Ring.Radius0 = Radius0;
	Ring.Radius1 = Radius1;
	Ring.Height0 = 90.f;
	Ring.Height1 = 25.f;
	Ring.Intensity = 5.f;
	Ring.Serial = ++RingSerialCounter;
	if (Ring.MID)
	{
		Ring.MID->SetVectorParameterValue(TEXT("WaveColor"), Color);
		Ring.MID->SetScalarParameterValue(TEXT("Fade"), 1.f);
		Ring.MID->SetScalarParameterValue(TEXT("Intensity"), Ring.Intensity);
	}
	Ring.Mesh->SetWorldLocationAndRotation(Ring.Center, FRotator::ZeroRotator);
	Ring.Mesh->SetWorldScale3D(FVector(Radius0 / 50.f, Radius0 / 50.f, Ring.Height0 / 100.f));
	Ring.Mesh->SetVisibility(true);
}

void ABossWalker::ReleaseRing(int32 Index, int32 Serial)
{
	if (Rings.IsValidIndex(Index) && Rings[Index].bActive && Rings[Index].Serial == Serial)
	{
		Rings[Index].bActive = false;
		if (Rings[Index].Mesh)
		{
			Rings[Index].Mesh->SetVisibility(false);
		}
	}
}

void ABossWalker::UpdateRings()
{
	static const FName FadeName(TEXT("Fade"));
	static const FName IntensityName(TEXT("Intensity"));
	const float T = Now();
	for (FScrapRing& Ring : Rings)
	{
		if (!Ring.bActive || !Ring.Mesh)
		{
			continue;
		}
		const float A = (T - Ring.Start) / Ring.Duration;
		if (A >= 1.f)
		{
			Ring.bActive = false;
			Ring.Mesh->SetVisibility(false);
			continue;
		}
		float Radius = Ring.Radius1;
		float Height = Ring.Height0;
		float Fade = 1.f;
		float Intensity = Ring.Intensity;
		if (Ring.bShockwave)
		{
			// Expanding squashed dome, fading as it goes.
			const float E = 1.f - FMath::Pow(1.f - A, 3.f);
			Radius = FMath::Lerp(Ring.Radius0, Ring.Radius1, E);
			Height = FMath::Lerp(Ring.Height0, Ring.Height1, A);
			Fade = FMath::Square(1.f - A);
		}
		else
		{
			// Warning marker: closes in, pulses and brightens toward the impact.
			const float E = 1.f - FMath::Square(1.f - A);
			Radius = FMath::Lerp(Ring.Radius0, Ring.Radius1, E);
			Fade = FMath::Min(1.f, A * 6.f) * (0.55f + 0.45f * FMath::Sin(T * 20.f));
			Intensity = Ring.Intensity * (0.6f + 0.9f * A);
		}
		Ring.Mesh->SetWorldLocation(Ring.Center);
		Ring.Mesh->SetWorldScale3D(FVector(Radius / 50.f, Radius / 50.f, FMath::Max(Height, 1.f) / 100.f));
		if (Ring.MID)
		{
			Ring.MID->SetScalarParameterValue(FadeName, Fade);
			Ring.MID->SetScalarParameterValue(IntensityName, Intensity);
		}
	}
}

void ABossWalker::EmitPuff(const FVector& Location, float Size)
{
	if (Puffs.Num() == 0)
	{
		return;
	}
	const int32 i = NextPuff;
	NextPuff = (NextPuff + 1) % Puffs.Num();
	PuffStart[i] = Now();
	PuffOrigin[i] = Location;
	PuffSize[i] = Size;
	PuffDrift[i] = -GetActorForwardVector() * 70.f + FVector(FMath::FRandRange(-25.f, 25.f), FMath::FRandRange(-25.f, 25.f), 0.f);
	if (UStaticMeshComponent* Puff = Puffs[i])
	{
		Puff->SetWorldLocation(Location);
		Puff->SetWorldScale3D(FVector(0.2f * Size));
		Puff->SetVisibility(true);
	}
}

void ABossWalker::UpdatePuffs()
{
	const float Life = 1.1f;
	const float T = Now();
	for (int32 i = 0; i < Puffs.Num(); ++i)
	{
		UStaticMeshComponent* Puff = Puffs[i];
		if (!Puff || !Puff->IsVisible())
		{
			continue;
		}
		const float A = (T - PuffStart[i]) / Life;
		if (A >= 1.f)
		{
			Puff->SetVisibility(false);
			continue;
		}
		const float Grow = 0.25f + 0.85f * FMath::Sqrt(A);
		const float Shrink = A > 0.7f ? 1.f - (A - 0.7f) / 0.3f : 1.f;
		Puff->SetWorldLocation(PuffOrigin[i] + PuffDrift[i] * A + FVector(0.f, 0.f, 150.f * A));
		Puff->SetWorldScale3D(FVector(PuffSize[i] * Grow * Shrink * 0.9f));
	}
}
