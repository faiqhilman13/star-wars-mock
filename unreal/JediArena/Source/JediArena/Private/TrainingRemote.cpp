#include "TrainingRemote.h"

#include "BlasterBolt.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

ATrainingRemote::ATrainingRemote()
{
	PrimaryActorTick.bCanEverTick = true;

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(22.f);
	Collision->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Collision->SetCollisionObjectType(ECC_WorldDynamic);
	Collision->SetCanEverAffectNavigation(false);
	RootComponent = Collision;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Metal(TEXT("/Game/Jedi/Materials/MI_ArenaMetal.MI_ArenaMetal"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> RedGlow(TEXT("/Game/Jedi/Materials/MI_GlowRed.MI_GlowRed"));

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Collision);
	Body->SetRelativeScale3D(FVector(0.38f));
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Eye = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Eye"));
	Eye->SetupAttachment(Collision);
	Eye->SetRelativeLocation(FVector(17.f, 0.f, 0.f));
	Eye->SetRelativeScale3D(FVector(0.09f));
	Eye->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Eye->SetCastShadow(false);
	if (Sphere.Succeeded())
	{
		Body->SetStaticMesh(Sphere.Object);
		Eye->SetStaticMesh(Sphere.Object);
	}
	if (Metal.Succeeded())
	{
		Body->SetMaterial(0, Metal.Object);
	}
	if (RedGlow.Succeeded())
	{
		Eye->SetMaterial(0, RedGlow.Object);
	}

	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(Collision);
	Glow->SetRelativeLocation(FVector(25.f, 0.f, 0.f));
	Glow->SetIntensity(800.f);
	Glow->SetAttenuationRadius(220.f);
	Glow->SetLightColor(FLinearColor(1.f, 0.1f, 0.05f));
	Glow->SetCastShadows(false);

	HumAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("HumAudio"));
	HumAudio->SetupAttachment(Collision);
	HumAudio->bAutoActivate = true;
	HumAudio->bOverrideAttenuation = true;
	HumAudio->AttenuationOverrides.bAttenuate = true;
	HumAudio->AttenuationOverrides.bSpatialize = true;
	HumAudio->AttenuationOverrides.FalloffDistance = 900.f;
	HumAudio->AttenuationOverrides.AttenuationShapeExtents = FVector(150.f, 0.f, 0.f);
	HumAudio->SetVolumeMultiplier(0.35f);

	BoltClass = ABlasterBolt::StaticClass();
}

void ATrainingRemote::BeginPlay()
{
	Super::BeginPlay();
	HP = MaxHP;
	OrbitAngle = FMath::FRandRange(0.f, 360.f);
	BobTime = FMath::FRandRange(0.f, 10.f);
	ScheduleFire(StartDelay + FMath::FRandRange(0.f, 1.5f));
}

void ATrainingRemote::ScheduleFire(float Delay)
{
	GetWorldTimerManager().SetTimer(FireTimer, this, &ATrainingRemote::Fire, FMath::Max(Delay, 0.1f), false);
}

void ATrainingRemote::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bActive)
	{
		return;
	}
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Player)
	{
		return;
	}

	OrbitAngle += OrbitSpeed * DeltaSeconds;
	BobTime += DeltaSeconds;
	const float Rad = FMath::DegreesToRadians(OrbitAngle);
	const FVector Center = Player->GetActorLocation();
	FVector Goal = Center + FVector(FMath::Cos(Rad), FMath::Sin(Rad), 0.f) * OrbitRadius;
	Goal.Z = Center.Z + HoverHeight + FMath::Sin(BobTime * 1.7f) * 40.f;

	FVector Loc = FMath::VInterpTo(GetActorLocation(), Goal, DeltaSeconds, 1.6f);
	// Knockback from saber/Force hits decays over time.
	Loc += KnockVelocity * DeltaSeconds;
	KnockVelocity = FMath::VInterpTo(KnockVelocity, FVector::ZeroVector, DeltaSeconds, 3.f);
	SetActorLocation(Loc);

	const FRotator Face = (Player->GetActorLocation() + FVector(0.f, 0.f, 40.f) - Loc).Rotation();
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Face, DeltaSeconds, 6.f));
}

void ATrainingRemote::Fire()
{
	if (!bActive)
	{
		return;
	}
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (Player && BoltClass)
	{
		const FVector Muzzle = Eye->GetComponentLocation();
		const FVector Target = Player->GetActorLocation() + FVector(0.f, 0.f, 45.f);
		FRotator Aim = (Target - Muzzle).Rotation();
		Aim.Pitch += FMath::FRandRange(-Inaccuracy, Inaccuracy);
		Aim.Yaw += FMath::FRandRange(-Inaccuracy, Inaccuracy);

		FActorSpawnParameters Params;
		Params.Owner = this;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FTransform SpawnXf(Aim, Muzzle + Aim.Vector() * 20.f);
		if (ABlasterBolt* Bolt = GetWorld()->SpawnActorDeferred<ABlasterBolt>(BoltClass, SpawnXf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
		{
			Bolt->Shooter = this;
			Bolt->ImpactFX = HitFX;
			UGameplayStatics::FinishSpawningActor(Bolt, SpawnXf);
		}
		if (FireSound)
		{
			UGameplayStatics::PlaySoundAtLocation(this, FireSound, Muzzle, 0.7f, FMath::FRandRange(0.95f, 1.08f));
		}
	}
	ScheduleFire(FMath::FRandRange(FireIntervalMin, FireIntervalMax));
}

float ATrainingRemote::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (!bActive)
	{
		return 0.f;
	}
	Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	HP -= DamageAmount;
	if (DamageCauser)
	{
		KnockVelocity += (GetActorLocation() - DamageCauser->GetActorLocation()).GetSafeNormal() * 700.f;
	}
	if (HitFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, GetActorLocation());
	}
	if (HP <= 0.f)
	{
		Explode();
	}
	return DamageAmount;
}

void ATrainingRemote::Explode()
{
	bActive = false;
	GetWorldTimerManager().ClearTimer(FireTimer);
	if (ExplodeSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ExplodeSound, GetActorLocation());
	}
	if (HitFX)
	{
		for (int32 i = 0; i < 4; ++i)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, GetActorLocation() + FMath::VRand() * 20.f, FMath::VRand().Rotation());
		}
	}
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);
	HumAudio->Stop();
	GetWorldTimerManager().SetTimer(RespawnTimer, this, &ATrainingRemote::Respawn, RespawnDelay, false);
}

void ATrainingRemote::Respawn()
{
	HP = MaxHP;
	bActive = true;
	KnockVelocity = FVector::ZeroVector;
	OrbitAngle += 140.f;
	if (APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0))
	{
		const float Rad = FMath::DegreesToRadians(OrbitAngle);
		SetActorLocation(Player->GetActorLocation() + FVector(FMath::Cos(Rad), FMath::Sin(Rad), 0.f) * OrbitRadius + FVector(0.f, 0.f, HoverHeight + 400.f));
	}
	SetActorHiddenInGame(false);
	SetActorEnableCollision(true);
	HumAudio->Play();
	ScheduleFire(2.5f);
}
