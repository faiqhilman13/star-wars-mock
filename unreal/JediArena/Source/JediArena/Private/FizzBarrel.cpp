#include "FizzBarrel.h"

#include "ColosseumArena.h"
#include "HordeDirector.h"
#include "JediCharacter.h"

#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/OverlapResult.h"
#include "Engine/Scene.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/Controller.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

namespace FizzKit
{
	constexpr float BarrelDiameter = 70.f;
	constexpr float BlastDuration = 0.45f;
	constexpr float PopDuration = 0.3f;
	constexpr float FlashCandelas = 2500.f;

	float EaseOutBack(float X)
	{
		const float C1 = 1.70158f;
		const float C3 = C1 + 1.f;
		const float Xm = X - 1.f;
		return 1.f + C3 * Xm * Xm * Xm + C1 * Xm * Xm;
	}
}

AFizzBarrel::AFizzBarrel()
{
	PrimaryActorTick.bCanEverTick = true;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> SurfaceFinder(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MetalFinder(TEXT("/Game/Jedi/Materials/MI_ArenaMetal.MI_ArenaMetal"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> GlowFinder(TEXT("/Game/Jedi/Materials/MI_GlowBlue.MI_GlowBlue"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> WaveFinder(TEXT("/Game/Jedi/Materials/M_ForceWave.M_ForceWave"));
	static ConstructorHelpers::FObjectFinder<USoundBase> ExplodeFinder(TEXT("/Game/Jedi/Audio/Licensed/SW_Remote_Explode.SW_Remote_Explode"));
	static ConstructorHelpers::FObjectFinder<USoundBase> HissFinder(TEXT("/Game/Jedi/Audio/SW_Force_Push.SW_Force_Push"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> SparkFinder(TEXT("/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"));

	CylinderMesh = CylinderFinder.Object;
	SphereMesh = SphereFinder.Object;
	SurfaceMaterial = SurfaceFinder.Object;
	MetalMaterial = MetalFinder.Object;
	WaveMaterial = WaveFinder.Object;
	ExplodeSound = ExplodeFinder.Object;
	HissSound = HissFinder.Object;
	SparkFX = SparkFinder.Object;
	UMaterialInterface* GlowDefault = GlowFinder.Object;

	// Physics root: a 70 x 110 cm canister.
	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	RootComponent = Body;
	Body->SetMobility(EComponentMobility::Movable);
	Body->SetStaticMesh(CylinderMesh);
	const FVector BodyScale = FArenaKit::FitBox(CylinderMesh, FVector::ZeroVector, FVector(FizzKit::BarrelDiameter, FizzKit::BarrelDiameter, BarrelHalfHeight * 2.f)).GetScale3D();
	Body->SetRelativeScale3D(BodyScale);
	if (SurfaceMaterial)
	{
		Body->SetMaterial(0, SurfaceMaterial);
	}
	Body->SetCollisionProfileName(TEXT("PhysicsActor"));
	Body->SetSimulatePhysics(true);
	Body->SetNotifyRigidBodyCollision(true);
	Body->SetGenerateOverlapEvents(false);
	Body->SetCanEverAffectNavigation(false);
	Body->BodyInstance.SetMassOverride(BarrelMass, true);
	Body->BodyInstance.LinearDamping = 0.15f;
	Body->BodyInstance.AngularDamping = 0.6f;

	// Children inherit the body's scale: place them in plain centimetres and divide it back out.
	auto PlaceChild = [&BodyScale](UStaticMeshComponent* Child, const UStaticMesh* Mesh, const FVector& Offset, const FVector& Size)
	{
		const FTransform Xf = FArenaKit::FitBox(Mesh, Offset, Size);
		Child->SetRelativeLocation(Xf.GetLocation() / BodyScale);
		Child->SetRelativeScale3D(Xf.GetScale3D() / BodyScale);
	};

	Band = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Band"));
	Band->SetupAttachment(Body);
	Band->SetStaticMesh(CylinderMesh);
	FArenaKit::NoCollision(Band);
	if (GlowDefault)
	{
		Band->SetMaterial(0, GlowDefault);
	}
	PlaceChild(Band, CylinderMesh, FVector(0.f, 0.f, 4.f), FVector(FizzKit::BarrelDiameter + 6.f, FizzKit::BarrelDiameter + 6.f, 18.f));

	Cap = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Cap"));
	Cap->SetupAttachment(Body);
	Cap->SetStaticMesh(CylinderMesh);
	FArenaKit::NoCollision(Cap);
	if (MetalMaterial)
	{
		Cap->SetMaterial(0, MetalMaterial);
	}
	PlaceChild(Cap, CylinderMesh, FVector(0.f, 0.f, BarrelHalfHeight + 5.f), FVector(54.f, 54.f, 10.f));

	Valve = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Valve"));
	Valve->SetupAttachment(Body);
	Valve->SetStaticMesh(SphereMesh);
	FArenaKit::NoCollision(Valve);
	Valve->SetCastShadow(false);
	if (GlowDefault)
	{
		Valve->SetMaterial(0, GlowDefault);
	}
	PlaceChild(Valve, SphereMesh, FVector(0.f, 0.f, BarrelHalfHeight + 14.f), FVector(22.f, 22.f, 22.f));

	Blast = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Blast"));
	Blast->SetupAttachment(Body);
	Blast->SetUsingAbsoluteLocation(true);
	Blast->SetUsingAbsoluteRotation(true);
	Blast->SetUsingAbsoluteScale(true);
	Blast->SetStaticMesh(SphereMesh);
	if (WaveMaterial)
	{
		Blast->SetMaterial(0, WaveMaterial);
	}
	FArenaKit::NoCollision(Blast);
	Blast->SetCastShadow(false);
	Blast->SetVisibility(false);

	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(Body);
	Glow->IntensityUnits = ELightUnits::Candelas;
	Glow->SetIntensity(0.f);
	Glow->SetAttenuationRadius(ExplosionRadius * 1.6f);
	Glow->SetLightColor(FizzColor);
	Glow->SetCastShadows(false);
	Glow->SetVisibility(false);
}

float AFizzBarrel::TimeNow() const
{
	const UWorld* World = GetWorld();
	return World ? static_cast<float>(World->GetTimeSeconds()) : 0.f;
}

void AFizzBarrel::BeginPlay()
{
	Super::BeginPlay();

	Home = GetActorTransform();
	HomeScale = Body->GetComponentScale();
	BandBaseScale = Band->GetRelativeScale3D();
	if (SphereMesh)
	{
		BlastMeshExtent = FMath::Max(static_cast<float>(SphereMesh->GetBounds().BoxExtent.X), 1.f);
	}
	Body->OnComponentHit.AddUniqueDynamic(this, &AFizzBarrel::OnBodyHit);
	Body->SetMassOverrideInKg(NAME_None, BarrelMass, true);

	if (SurfaceMaterial)
	{
		if (UMaterialInstanceDynamic* Canister = FArenaKit::SharedSurfaceMID(SurfaceMaterial, FLinearColor(0.08f, 0.22f, 0.5f), FLinearColor(0.f, 0.02f, 0.05f), 0.3f, 0.7f))
		{
			Body->SetMaterial(0, Canister);
		}
		GlowOnMat = FArenaKit::SharedSurfaceMID(SurfaceMaterial, FLinearColor(0.1f, 0.7f, 1.f), FizzColor * 2.f, 0.3f, 0.f);
		GlowHotMat = FArenaKit::SharedSurfaceMID(SurfaceMaterial, FLinearColor::White, FLinearColor(6.f, 10.f, 12.f), 0.3f, 0.f);
	}
	if (!GlowOnMat)
	{
		GlowOnMat = Band->GetMaterial(0);
	}
	if (!GlowHotMat)
	{
		GlowHotMat = GlowOnMat;
	}
	SetGlowMaterial(GlowOnMat);
	State = EFizzState::Idle;
}

// ============================================================================ damage

float AFizzBarrel::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	if (DamageAmount <= 0.f || !IsJediTargetAlive())
	{
		return 0.f;
	}
	AActor* Credit = DamageCauser;
	if (EventInstigator && EventInstigator->GetPawn())
	{
		Credit = EventInstigator->GetPawn();
	}
	Ignite(Credit);
	return DamageAmount;
}

float AFizzBarrel::ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
{
	if (!IsJediTargetAlive())
	{
		return 0.f;
	}
	const bool bPhysics = Body && Body->IsSimulatingPhysics();

	// The Force just throws it around (it may go off when it slams into something).
	if (Kind == EJediHitKind::ForcePush || Kind == EJediHitKind::ForcePull)
	{
		if (bPhysics)
		{
			Body->AddImpulse(Impulse * 0.85f, NAME_None, true);
			Body->AddAngularImpulseInDegrees(FMath::VRand() * 360.f, NAME_None, true);
		}
		if (Causer)
		{
			FuseCauser = Causer;
		}
		return 0.f;
	}

	if (bPhysics && !Impulse.IsNearlyZero())
	{
		Body->AddImpulse(Impulse * 0.4f, NAME_None, true);
	}
	if (Damage > 0.f)
	{
		Ignite(Causer);
		return Damage;
	}
	return 0.f;
}

bool AFizzBarrel::IsJediTargetAlive() const
{
	return State == EFizzState::Idle || State == EFizzState::Fused;
}

bool AFizzBarrel::IsFused() const
{
	return State == EFizzState::Fused;
}

void AFizzBarrel::OnBodyHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
	if (State != EFizzState::Idle || ImpactDetonateSpeed <= 0.f)
	{
		return;
	}
	if (OtherActor && OtherActor->IsA(AJediCharacter::StaticClass()))
	{
		return; // bumping into the Jedi never sets it off
	}
	const float Mass = FMath::Max(Body->GetMass(), 1.f);
	const float DeltaV = static_cast<float>(NormalImpulse.Size()) / Mass;
	// Speed along the contact normal only: sliding across the floor doesn't count, slamming into a wall does.
	const float Approach = static_cast<float>(FMath::Abs(FVector::DotProduct(LastVelocity, Hit.ImpactNormal)));
	if (FMath::Max(DeltaV, Approach) >= ImpactDetonateSpeed)
	{
		Ignite(FuseCauser.Get(), 0.12f);
	}
}

void AFizzBarrel::Ignite(AActor* Causer, float FuseOverride)
{
	const float Now = TimeNow();
	if (State == EFizzState::Fused)
	{
		FuseEnd = FMath::Min(FuseEnd, Now + 0.15f);
		return;
	}
	if (State != EFizzState::Idle)
	{
		return;
	}
	State = EFizzState::Fused;
	FuseStart = Now;
	FuseEnd = Now + (FuseOverride > 0.f ? FuseOverride : FMath::FRandRange(FuseMin, FMath::Max(FuseMin, FuseMax)));
	if (Causer && Causer != this)
	{
		FuseCauser = Causer;
	}
	bFlashOn = false;
	if (Glow)
	{
		Glow->SetLightColor(FizzColor);
		Glow->SetIntensity(150.f);
		Glow->SetVisibility(true);
	}
	if (HissSound)
	{
		HissAudio = UGameplayStatics::SpawnSoundAttached(HissSound, Body, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator,
			EAttachLocation::KeepRelativeOffset, true, 0.45f, 2.3f);
	}
}

void AFizzBarrel::Explode()
{
	if (State == EFizzState::Gone || State == EFizzState::Popping)
	{
		return;
	}
	const float Now = TimeNow();
	State = EFizzState::Gone; // before the blast, so chain reactions can't hit us again
	const FVector At = Body->GetComponentLocation();
	AActor* Credit = FuseCauser.IsValid() ? FuseCauser.Get() : static_cast<AActor*>(this);
	StopHiss();
	Park();
	BlastDamage(At, Credit);

	if (SparkFX)
	{
		for (int32 i = 0; i < 3; ++i)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparkFX, At + FMath::VRand() * 30.f, FMath::VRand().Rotation(), FVector(1.6f));
		}
	}
	if (Blast)
	{
		if (!BlastMID && WaveMaterial)
		{
			BlastMID = UMaterialInstanceDynamic::Create(WaveMaterial, this);
			Blast->SetMaterial(0, BlastMID);
		}
		if (BlastMID)
		{
			BlastMID->SetVectorParameterValue(TEXT("WaveColor"), FizzColor);
			BlastMID->SetScalarParameterValue(TEXT("Intensity"), 4.f);
			BlastMID->SetScalarParameterValue(TEXT("Fade"), 0.9f);
		}
		Blast->SetWorldLocation(At);
		Blast->SetWorldScale3D(FVector(80.f / (2.f * BlastMeshExtent)));
		Blast->SetVisibility(true);
		BlastStart = Now;
	}
	if (Glow)
	{
		Glow->SetLightColor(FizzColor);
		Glow->SetIntensity(FizzKit::FlashCandelas);
		Glow->SetVisibility(true);
	}
	if (ExplodeSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ExplodeSound, At, 1.f, FMath::FRandRange(0.9f, 1.12f));
	}
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->AddHype(HypeOnExplode);
	}
	if (AColosseumArena* Arena = Cast<AColosseumArena>(GetOwner()))
	{
		Arena->CrowdCheer(0.2f);
	}
	GetWorldTimerManager().SetTimer(RespawnTimer, this, &AFizzBarrel::Respawn, FMath::Max(RespawnDelay, 1.f), false);
}

void AFizzBarrel::BlastDamage(const FVector& At, AActor* Credit)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	TArray<FOverlapResult> Overlaps;
	FCollisionObjectQueryParams ObjectParams;
	ObjectParams.AddObjectTypesToQuery(ECC_Pawn);
	ObjectParams.AddObjectTypesToQuery(ECC_PhysicsBody);
	ObjectParams.AddObjectTypesToQuery(ECC_WorldDynamic);
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(FizzBarrelBlast), false, this);
	World->OverlapMultiByObjectType(Overlaps, At, FQuat::Identity, ObjectParams, FCollisionShape::MakeSphere(ExplosionRadius), QueryParams);

	TSet<AActor*> Done;
	for (const FOverlapResult& Overlap : Overlaps)
	{
		AActor* Target = Overlap.GetActor();
		if (!IsValid(Target) || Target == this || Target->IsA(AJediCharacter::StaticClass()))
		{
			continue; // the Jedi is never hurt by fizz
		}
		FVector Dir = Target->GetActorLocation() - At;
		Dir.Z = 0.f;
		if (!Dir.Normalize())
		{
			Dir = FVector(FMath::FRandRange(-1.f, 1.f), FMath::FRandRange(-1.f, 1.f), 0.f).GetSafeNormal();
		}
		const FVector Kick = Dir * BlastOutSpeed + FVector(0.f, 0.f, BlastUpSpeed);

		if (IJediDamageable* Damageable = Cast<IJediDamageable>(Target))
		{
			if (!Done.Contains(Target))
			{
				Done.Add(Target);
				if (Damageable->IsJediTargetAlive())
				{
					Damageable->ReceiveJediHit(ExplosionDamage, Credit, Target->GetActorLocation(), Kick, EJediHitKind::Explosion);
				}
			}
		}
		else if (Target->IsA(ACharacter::StaticClass()))
		{
			if (!Done.Contains(Target))
			{
				Done.Add(Target);
				AJediCharacter::DamageActor(Target, ExplosionDamage, Credit, Target->GetActorLocation(), Kick, EJediHitKind::Explosion);
			}
		}
		else if (UPrimitiveComponent* Prim = Overlap.GetComponent())
		{
			if (Prim->IsSimulatingPhysics())
			{
				Prim->AddImpulse(Kick * 0.6f, NAME_None, true);
			}
		}
	}
}

void AFizzBarrel::Gobble()
{
	if (State == EFizzState::Gone || State == EFizzState::Popping)
	{
		return;
	}
	State = EFizzState::Gone;
	StopHiss();
	Park();
	if (Glow)
	{
		Glow->SetVisibility(false);
	}
	GetWorldTimerManager().SetTimer(RespawnTimer, this, &AFizzBarrel::Respawn, FMath::Max(RespawnDelay, 1.f), false);
}

// ============================================================================ state helpers

void AFizzBarrel::Park()
{
	Body->SetSimulatePhysics(false);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SetPartsVisible(false);
	Band->SetRelativeScale3D(BandBaseScale);
	SetGlowMaterial(GlowOnMat);
	bFlashOn = false;
	LastVelocity = FVector::ZeroVector;
}

void AFizzBarrel::SetPartsVisible(bool bVisible)
{
	Body->SetVisibility(bVisible, false);
	Band->SetVisibility(bVisible);
	Cap->SetVisibility(bVisible);
	Valve->SetVisibility(bVisible);
}

void AFizzBarrel::SetGlowMaterial(UMaterialInterface* Material)
{
	if (!Material)
	{
		return;
	}
	Band->SetMaterial(0, Material);
	Valve->SetMaterial(0, Material);
}

void AFizzBarrel::StopHiss()
{
	if (HissAudio)
	{
		HissAudio->Stop();
		HissAudio = nullptr;
	}
}

void AFizzBarrel::Respawn()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	// Don't pop into someone standing on the spot; try again shortly.
	FCollisionObjectQueryParams PawnsOnly;
	PawnsOnly.AddObjectTypesToQuery(ECC_Pawn);
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(FizzBarrelRespawn), false, this);
	if (World->OverlapAnyTestByObjectType(Home.GetLocation(), FQuat::Identity, PawnsOnly, FCollisionShape::MakeSphere(90.f), QueryParams))
	{
		GetWorldTimerManager().SetTimer(RespawnTimer, this, &AFizzBarrel::Respawn, 1.5f, false);
		return;
	}
	Body->SetWorldLocationAndRotation(Home.GetLocation(), Home.GetRotation(), false, nullptr, ETeleportType::ResetPhysics);
	Body->SetWorldScale3D(HomeScale * 0.05f);
	SetPartsVisible(true);
	SetGlowMaterial(GlowOnMat);
	FuseCauser = nullptr;
	State = EFizzState::Popping;
	PopStart = TimeNow();
	if (HissSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, HissSound, Home.GetLocation(), 0.35f, 2.4f);
	}
	if (SparkFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparkFX, Home.GetLocation(), FRotator(90.f, 0.f, 0.f), FVector(0.8f));
	}
}

// ============================================================================ tick

void AFizzBarrel::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float Now = TimeNow();
	switch (State)
	{
	case EFizzState::Idle:
		LastVelocity = (Body->IsSimulatingPhysics() && Body->IsAnyRigidBodyAwake()) ? Body->GetPhysicsLinearVelocity() : FVector::ZeroVector;
		if (GetActorLocation().Z < Home.GetLocation().Z - 3000.f)
		{
			Gobble(); // fell out of the world somehow: quietly come back later
		}
		break;
	case EFizzState::Fused:
		TickFuse(Now);
		break;
	case EFizzState::Popping:
		TickPop(Now);
		break;
	default:
		break;
	}
	TickBlast(Now);
}

void AFizzBarrel::TickFuse(float Now)
{
	// Blink faster and faster between the normal glow and white-hot, band swelling.
	const float Total = FMath::Max(FuseEnd - FuseStart, 0.05f);
	const float Progress = FMath::Clamp((Now - FuseStart) / Total, 0.f, 1.f);
	const float Freq = FMath::Lerp(7.f, 24.f, Progress);
	const bool bOn = FMath::Sin((Now - FuseStart) * Freq * 2.f * PI) > 0.f;
	if (bOn != bFlashOn)
	{
		bFlashOn = bOn;
		SetGlowMaterial(bOn ? GlowHotMat.Get() : GlowOnMat.Get());
		if (Glow)
		{
			Glow->SetIntensity(bOn ? 900.f : 150.f);
		}
	}
	const float Swell = 1.f + 0.12f * Progress + 0.05f * FMath::Sin(Now * 60.f);
	Band->SetRelativeScale3D(FVector(BandBaseScale.X * Swell, BandBaseScale.Y * Swell, BandBaseScale.Z));
	if (Now >= FuseEnd)
	{
		Explode();
	}
}

void AFizzBarrel::TickPop(float Now)
{
	const float Tn = FMath::Clamp((Now - PopStart) / FizzKit::PopDuration, 0.f, 1.f);
	Body->SetWorldScale3D(HomeScale * FMath::Max(FizzKit::EaseOutBack(Tn), 0.05f));
	if (Tn >= 1.f)
	{
		Body->SetWorldScale3D(HomeScale);
		Body->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Body->SetSimulatePhysics(true);
		Body->WakeRigidBody();
		State = EFizzState::Idle;
	}
}

void AFizzBarrel::TickBlast(float Now)
{
	if (BlastStart < 0.f)
	{
		return;
	}
	const float Age = Now - BlastStart;
	if (Age >= FizzKit::BlastDuration)
	{
		BlastStart = -1.f;
		if (Blast)
		{
			Blast->SetVisibility(false);
		}
		if (Glow && State != EFizzState::Fused)
		{
			Glow->SetVisibility(false);
		}
		return;
	}
	const float Tn = Age / FizzKit::BlastDuration;
	const float EaseOut = 1.f - FMath::Square(1.f - Tn);
	const float Diameter = FMath::Lerp(80.f, ExplosionRadius * 1.9f, EaseOut);
	if (Blast)
	{
		Blast->SetWorldScale3D(FVector(Diameter / (2.f * BlastMeshExtent)));
	}
	if (BlastMID)
	{
		BlastMID->SetScalarParameterValue(TEXT("Fade"), 0.9f * (1.f - Tn));
	}
	if (Glow)
	{
		Glow->SetIntensity(FizzKit::FlashCandelas * FMath::Square(1.f - Tn));
	}
}
