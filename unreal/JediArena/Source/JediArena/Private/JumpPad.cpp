#include "JumpPad.h"

#include "ColosseumArena.h"

#include "Components/CapsuleComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

namespace PadKit
{
	constexpr int32 NumChevrons = 3;
	constexpr float PadHeight = 30.f;
}

AJumpPad::AJumpPad()
{
	PrimaryActorTick.bCanEverTick = true;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> SurfaceFinder(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MetalFinder(TEXT("/Game/Jedi/Materials/MI_ArenaMetal.MI_ArenaMetal"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> GlowFinder(TEXT("/Game/Jedi/Materials/MI_Lava.MI_Lava"));
	static ConstructorHelpers::FObjectFinder<USoundBase> WhooshFinder(TEXT("/Game/Jedi/Audio/SW_Force_Push.SW_Force_Push"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> PadFXFinder(TEXT("/Game/LevelPrototyping/Interactable/JumpPad/Assets/NS_JumpPad.NS_JumpPad"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> SparkFinder(TEXT("/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"));

	CylinderMesh = CylinderFinder.Object;
	CubeMesh = CubeFinder.Object;
	SurfaceMaterial = SurfaceFinder.Object;
	MetalMaterial = MetalFinder.Object;
	LaunchSound = WhooshFinder.Object;
	PadFX = PadFXFinder.Object;
	LaunchFX = SparkFinder.Object;
	UMaterialInterface* GlowDefault = GlowFinder.Object;

	PadRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PadRoot"));
	PadRoot->SetMobility(EComponentMobility::Movable);
	RootComponent = PadRoot;

	PadBase = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PadBase"));
	PadBase->SetupAttachment(PadRoot);
	PadBase->SetStaticMesh(CylinderMesh);
	PadBase->SetCollisionProfileName(TEXT("BlockAll"));
	PadBase->SetGenerateOverlapEvents(false);
	PadBase->SetCanEverAffectNavigation(false);
	if (MetalMaterial)
	{
		PadBase->SetMaterial(0, MetalMaterial);
	}

	Rim = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Rim"));
	Rim->SetupAttachment(PadRoot);
	Rim->SetStaticMesh(CylinderMesh);
	FArenaKit::NoCollision(Rim);
	Rim->SetCastShadow(false);

	Core = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Core"));
	Core->SetupAttachment(PadRoot);
	Core->SetStaticMesh(CylinderMesh);
	FArenaKit::NoCollision(Core);
	Core->SetCastShadow(false);

	Chevrons = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Chevrons"));
	Chevrons->SetupAttachment(PadRoot);
	Chevrons->SetStaticMesh(CubeMesh);
	FArenaKit::NoCollision(Chevrons);
	Chevrons->SetCastShadow(false);

	if (GlowDefault)
	{
		Rim->SetMaterial(0, GlowDefault);
		Core->SetMaterial(0, GlowDefault);
		Chevrons->SetMaterial(0, GlowDefault);
	}

	Trigger = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Trigger"));
	Trigger->SetupAttachment(PadRoot);
	Trigger->SetCollisionProfileName(TEXT("Trigger"));
	Trigger->SetGenerateOverlapEvents(true);
	Trigger->SetCanEverAffectNavigation(false);
	Trigger->InitCapsuleSize(PadRadius * 0.85f, 130.f);

	PadEffect = CreateDefaultSubobject<UNiagaraComponent>(TEXT("PadEffect"));
	PadEffect->SetupAttachment(PadRoot);
	PadEffect->SetRelativeLocation(FVector(0.f, 0.f, PadKit::PadHeight + 2.f));
	if (PadFX)
	{
		PadEffect->SetAsset(PadFX);
	}
}

float AJumpPad::TimeNow() const
{
	const UWorld* World = GetWorld();
	return World ? static_cast<float>(World->GetTimeSeconds()) : 0.f;
}

void AJumpPad::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	Layout();
}

void AJumpPad::BeginPlay()
{
	Super::BeginPlay();
	Layout();
	if (SurfaceMaterial)
	{
		GlowMat = FArenaKit::SharedSurfaceMID(SurfaceMaterial, GlowColor, GlowColor * 3.f, 0.4f, 0.f);
		FlashMat = FArenaKit::SharedSurfaceMID(SurfaceMaterial, FLinearColor::White, GlowColor * 12.f, 0.4f, 0.f);
		if (GlowMat)
		{
			Rim->SetMaterial(0, GlowMat);
			Core->SetMaterial(0, GlowMat);
			Chevrons->SetMaterial(0, GlowMat);
		}
	}
	Trigger->OnComponentBeginOverlap.AddUniqueDynamic(this, &AJumpPad::OnTriggerBegin);
}

void AJumpPad::Layout()
{
	const float PadR = FMath::Max(PadRadius, 60.f);
	if (PadBase)
	{
		PadBase->SetRelativeTransform(FArenaKit::FitBox(PadBase->GetStaticMesh(), FVector(0.f, 0.f, PadKit::PadHeight * 0.5f), FVector(2.f * PadR, 2.f * PadR, PadKit::PadHeight)));
	}
	if (Rim)
	{
		Rim->SetRelativeTransform(FArenaKit::FitBox(Rim->GetStaticMesh(), FVector(0.f, 0.f, 7.f), FVector(2.f * PadR + 34.f, 2.f * PadR + 34.f, 14.f)));
	}
	if (Core)
	{
		Core->SetRelativeTransform(FArenaKit::FitBox(Core->GetStaticMesh(), FVector(0.f, 0.f, PadKit::PadHeight + 0.5f), FVector(1.25f * PadR, 1.25f * PadR, 3.f)));
	}
	if (Chevrons)
	{
		// Three ">" chevrons pointing along +X (the launch direction).
		Chevrons->ClearInstances();
		ChevronBase.Reset();
		const float ArmLen = PadR * 0.42f;
		for (int32 c = 0; c < PadKit::NumChevrons; ++c)
		{
			const float TipX = PadR * (-0.3f + 0.35f * c);
			for (int32 Side = -1; Side <= 1; Side += 2)
			{
				const FQuat ArmQ = FRotator(0.f, 180.f - 40.f * Side, 0.f).Quaternion();
				const FVector ArmCenter = FVector(TipX, 0.f, PadKit::PadHeight + 2.f) + ArmQ.GetForwardVector() * (ArmLen * 0.5f);
				const FTransform Xf = FArenaKit::FitBox(Chevrons->GetStaticMesh(), ArmCenter, FVector(ArmLen, 14.f, 3.f), ArmQ);
				ChevronBase.Add(Xf);
				Chevrons->AddInstance(Xf, false);
			}
		}
	}
	if (Trigger)
	{
		Trigger->SetCapsuleSize(PadR * 0.85f, 130.f, false);
		Trigger->SetRelativeLocation(FVector(0.f, 0.f, PadKit::PadHeight + 60.f));
	}
}

void AJumpPad::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float Now = TimeNow();

	// Re-check who is standing on the pad (so waiting out the cooldown on it still launches you).
	RecheckAccum += DeltaSeconds;
	if (RecheckAccum >= 0.15f && Trigger)
	{
		RecheckAccum = 0.f;
		TArray<AActor*> Standing;
		Trigger->GetOverlappingActors(Standing, ACharacter::StaticClass());
		for (AActor* Other : Standing)
		{
			Launch(Cast<ACharacter>(Other));
		}
	}

	// Chevrons ripple toward the launch direction.
	if (Chevrons && ChevronBase.Num() == Chevrons->GetInstanceCount())
	{
		for (int32 i = 0; i < ChevronBase.Num(); ++i)
		{
			const float Wave = FMath::Max(0.f, FMath::Sin(Now * 6.f - (i / 2) * 1.3f));
			FTransform Xf = ChevronBase[i];
			const FVector S = Xf.GetScale3D();
			Xf.SetScale3D(FVector(S.X, S.Y * (1.f + 0.6f * Wave), S.Z * (1.f + 2.f * Wave)));
			Chevrons->UpdateInstanceTransform(i, Xf, false, false, false);
		}
	}

	if (bFlashing && Now >= FlashUntil)
	{
		bFlashing = false;
		if (Core && GlowMat)
		{
			Core->SetMaterial(0, GlowMat);
		}
	}
}

void AJumpPad::OnTriggerBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (ACharacter* Hopper = Cast<ACharacter>(OtherActor))
	{
		Launch(Hopper);
	}
}

FVector AJumpPad::GetLaunchTargetWorld() const
{
	return GetActorTransform().TransformPosition(LaunchTarget);
}

bool AJumpPad::Launch(ACharacter* Character)
{
	if (!IsValid(Character))
	{
		return false;
	}
	UCharacterMovementComponent* Move = Character->GetCharacterMovement();
	if (!Move || Move->MovementMode == MOVE_None || Move->MovementMode == MOVE_Flying)
	{
		return false; // dead, disabled or hovering
	}
	const ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	if (!bLaunchEnemies && Character != Player)
	{
		return false;
	}
	const float Now = TimeNow();
	if (const float* Last = LastLaunch.Find(Character))
	{
		if (Now - *Last < Cooldown)
		{
			return false;
		}
	}
	LastLaunch.Add(Character, Now);
	if (LastLaunch.Num() > 48)
	{
		for (auto It = LastLaunch.CreateIterator(); It; ++It)
		{
			if (!It.Key().IsValid() || Now - It.Value() > Cooldown)
			{
				It.RemoveCurrent();
			}
		}
	}

	// Ballistic arc: fixed vertical speed, horizontal speed solved from the flight time to the landing point.
	const FVector Start = Character->GetActorLocation();
	FVector Target = GetLaunchTargetWorld();
	if (const UCapsuleComponent* Capsule = Character->GetCapsuleComponent())
	{
		Target.Z += Capsule->GetScaledCapsuleHalfHeight();
	}
	const float Gravity = FMath::Max(FMath::Abs(Move->GetGravityZ()), 1.f);
	const float Vz = LaunchUpSpeed;
	const float Apex = Vz * Vz / (2.f * Gravity);
	const float Drop = FMath::Max(static_cast<float>(Start.Z - Target.Z) + Apex, 1.f);
	const float FlightTime = Vz / Gravity + FMath::Sqrt(2.f * Drop / Gravity);
	FVector Horizontal = Target - Start;
	Horizontal.Z = 0.f;
	Character->LaunchCharacter(Horizontal / FlightTime + FVector(0.f, 0.f, Vz), true, true);

	if (LaunchSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, LaunchSound, Start, 0.8f, FMath::FRandRange(1.2f, 1.4f));
	}
	if (LaunchFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, LaunchFX, Start - FVector(0.f, 0.f, 80.f), FRotator(90.f, 0.f, 0.f), FVector(1.2f));
	}
	if (Core && FlashMat)
	{
		Core->SetMaterial(0, FlashMat);
		bFlashing = true;
		FlashUntil = Now + 0.25f;
	}
	return true;
}
