#include "BlasterBolt.h"

#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "JediCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "UObject/ConstructorHelpers.h"

ABlasterBolt::ABlasterBolt()
{
	PrimaryActorTick.bCanEverTick = false;

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(10.f);
	Collision->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Collision->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
	Collision->SetGenerateOverlapEvents(true);
	Collision->SetNotifyRigidBodyCollision(true);
	RootComponent = Collision;

	Core = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Core"));
	Core->SetupAttachment(Collision);
	Core->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Core->SetCastShadow(false);
	// Engine cylinder is 100 cm tall along Z; lay it along X and stretch it into a bolt.
	Core->SetRelativeRotation(FRotator(90.f, 0.f, 0.f));
	Core->SetRelativeScale3D(FVector(0.045f, 0.045f, 0.7f));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Cyl.Succeeded())
	{
		Core->SetStaticMesh(Cyl.Object);
	}
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Red(TEXT("/Game/Jedi/Materials/MI_SaberCore_Red.MI_SaberCore_Red"));
	if (Red.Succeeded())
	{
		Core->SetMaterial(0, Red.Object);
	}

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Collision);
	Light->SetIntensity(1500.f);
	Light->SetAttenuationRadius(260.f);
	Light->SetLightColor(FLinearColor(1.f, 0.08f, 0.04f));
	Light->SetCastShadows(false);

	Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
	Movement->InitialSpeed = Speed;
	Movement->MaxSpeed = Speed * 2.f;
	Movement->ProjectileGravityScale = 0.f;
	Movement->bRotationFollowsVelocity = true;

	InitialLifeSpan = 4.f;
}

void ABlasterBolt::BeginPlay()
{
	Super::BeginPlay();
	Collision->OnComponentBeginOverlap.AddDynamic(this, &ABlasterBolt::OnOverlap);
	Collision->OnComponentHit.AddDynamic(this, &ABlasterBolt::OnHit);
	Movement->Velocity = GetActorForwardVector() * Speed;
	if (Shooter.IsValid())
	{
		Collision->IgnoreActorWhenMoving(Shooter.Get(), true);
	}
}

FVector ABlasterBolt::GetDirection() const
{
	return Movement->Velocity.GetSafeNormal();
}

void ABlasterBolt::Deflect(const FVector& NewDirection, AActor* NewOwnerActor, float SpeedScale)
{
	if (Shooter.IsValid())
	{
		Collision->IgnoreActorWhenMoving(Shooter.Get(), false);
		RecentlyIgnored.Remove(Shooter);
	}
	bDeflected = true;
	Shooter = NewOwnerActor;
	RecentlyIgnored.Add(NewOwnerActor);
	Collision->IgnoreActorWhenMoving(NewOwnerActor, true);
	Movement->Velocity = NewDirection.GetSafeNormal() * Speed * SpeedScale;
	SetActorRotation(NewDirection.Rotation());
	SetLifeSpan(4.f);
}

void ABlasterBolt::OnOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 BodyIndex, bool bFromSweep, const FHitResult& Sweep)
{
	if (!Other || Other == this || Other == Shooter.Get() || RecentlyIgnored.Contains(Other) || Other->IsA(ABlasterBolt::StaticClass()))
	{
		return;
	}
	// Sabers and other attached props are owned by their wielder.
	if (Other->GetOwner() && (Other->GetOwner() == Shooter.Get()))
	{
		return;
	}

	if (AJediCharacter* Jedi = Cast<AJediCharacter>(Other))
	{
		if (Jedi->TryDeflectBolt(this))
		{
			return;
		}
	}
	if (!Other->CanBeDamaged() && !Other->IsA(APawn::StaticClass()))
	{
		return; // pass through triggers, VFX actors, etc.
	}

	const FVector Loc = Sweep.bBlockingHit ? FVector(Sweep.ImpactPoint) : GetActorLocation();
	AJediCharacter::DamageActor(Other, Damage, Shooter.Get() ? Shooter.Get() : this, Loc, GetDirection() * 250.f + FVector(0.f, 0.f, 80.f));
	Impact(Loc, -GetDirection());
}

void ABlasterBolt::OnHit(UPrimitiveComponent* HitComp, AActor* Other, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
	Impact(Hit.ImpactPoint, Hit.ImpactNormal);
}

void ABlasterBolt::Impact(const FVector& Location, const FVector& Normal)
{
	if (ImpactFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ImpactFX, Location, Normal.Rotation());
	}
	if (ImpactSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ImpactSound, Location, 0.6f);
	}
	Destroy();
}
