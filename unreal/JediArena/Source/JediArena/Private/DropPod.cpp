#include "DropPod.h"

#include "HordeDirector.h"
#include "JediCharacter.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraFunctionLibrary.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	template <typename T>
	T* FindPodAsset(const TCHAR* Path)
	{
		ConstructorHelpers::FObjectFinder<T> Finder(Path);
		return Finder.Succeeded() ? Finder.Object : nullptr;
	}
}

ADropPod::ADropPod()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	PodPivot = CreateDefaultSubobject<USceneComponent>(TEXT("PodPivot"));
	PodPivot->SetupAttachment(Root);
	Marker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Marker"));
	Marker->SetupAttachment(Root);
	Marker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Marker->SetCastShadow(false);

	CubeMesh = FindPodAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Cube.Cube"));
	CylinderMesh = FindPodAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	ConeMesh = FindPodAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Cone.Cone"));
	SphereMesh = FindPodAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	SurfaceMat = FindPodAsset<UMaterialInterface>(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	WaveMat = FindPodAsset<UMaterialInterface>(TEXT("/Game/Jedi/Materials/M_ForceWave.M_ForceWave"));
	ImpactSound = FindPodAsset<USoundBase>(TEXT("/Game/Jedi/Audio/Licensed/SW_Remote_Explode.SW_Remote_Explode"));
	WhistleSound = FindPodAsset<USoundBase>(TEXT("/Game/Jedi/Audio/Licensed/SW_Saber_Swing5.SW_Saber_Swing5"));
	SparkFX = FindPodAsset<UNiagaraSystem>(TEXT("/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"));
}

UStaticMeshComponent* ADropPod::AddMesh(UStaticMesh* Mesh, USceneComponent* Parent, const FVector& Loc, const FRotator& Rot, const FVector& Scale, UMaterialInterface* Mat)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetStaticMesh(Mesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetupAttachment(Parent);
	C->SetRelativeLocationAndRotation(Loc, Rot);
	C->SetRelativeScale3D(Scale);
	if (Mat)
	{
		C->SetMaterial(0, Mat);
	}
	C->RegisterComponent();
	return C;
}

void ADropPod::Build()
{
	auto Mat = [this](const FLinearColor& Color, float Rough, float Metal, const FLinearColor& Emissive) -> UMaterialInterface*
	{
		if (!SurfaceMat)
		{
			return nullptr;
		}
		UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(SurfaceMat, this);
		MID->SetVectorParameterValue(TEXT("BaseColor"), Color);
		MID->SetScalarParameterValue(TEXT("Roughness"), Rough);
		MID->SetScalarParameterValue(TEXT("Metallic"), Metal);
		MID->SetVectorParameterValue(TEXT("Emissive"), Emissive);
		return MID;
	};
	UMaterialInterface* Hull = Mat(FLinearColor(0.32f, 0.3f, 0.28f), 0.4f, 0.9f, FLinearColor::Black);
	UMaterialInterface* Stripe = Mat(FLinearColor(0.7f, 0.35f, 0.05f), 0.5f, 0.3f, FLinearColor(0.4f, 0.12f, 0.f));
	UMaterialInterface* Fire = Mat(FLinearColor(1.f, 0.4f, 0.05f), 0.5f, 0.f, FLinearColor(12.f, 4.f, 0.6f));
	UMaterialInterface* Lamp = Mat(FLinearColor::Black, 0.5f, 0.f, FLinearColor(8.f, 0.3f, 0.1f));

	// Hull: a squat capsule with a cone nose (pointing down while falling), fins and a blinking lamp.
	AddMesh(CylinderMesh, PodPivot, FVector(0.f, 0.f, 150.f), FRotator::ZeroRotator, FVector(1.5f, 1.5f, 1.8f), Hull);
	AddMesh(SphereMesh, PodPivot, FVector(0.f, 0.f, 240.f), FRotator::ZeroRotator, FVector(1.5f, 1.5f, 0.9f), Hull);
	AddMesh(CylinderMesh, PodPivot, FVector(0.f, 0.f, 170.f), FRotator::ZeroRotator, FVector(1.56f, 1.56f, 0.18f), Stripe);
	AddMesh(SphereMesh, PodPivot, FVector(0.f, 0.f, 290.f), FRotator::ZeroRotator, FVector(0.18f), Lamp);
	for (int32 i = 0; i < 4; ++i)
	{
		const FRotator Yaw(0.f, 45.f + i * 90.f, 0.f);
		AddMesh(CubeMesh, PodPivot, Yaw.RotateVector(FVector(85.f, 0.f, 230.f)), Yaw, FVector(0.5f, 0.06f, 0.9f), Stripe);
	}
	// Petals around the base that swing open on landing.
	for (int32 i = 0; i < 4; ++i)
	{
		const FRotator Yaw(0.f, i * 90.f, 0.f);
		USceneComponent* Pivot = NewObject<USceneComponent>(this);
		Pivot->SetupAttachment(PodPivot);
		Pivot->SetRelativeLocationAndRotation(Yaw.RotateVector(FVector(72.f, 0.f, 70.f)), Yaw);
		Pivot->RegisterComponent();
		AddMesh(CubeMesh, Pivot, FVector(0.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.08f, 1.05f, 1.3f), Hull);
		PetalPivots.Add(Pivot);
	}
	Trail = AddMesh(ConeMesh, PodPivot, FVector(0.f, 0.f, 560.f), FRotator::ZeroRotator, FVector(1.3f, 1.3f, 5.5f), Fire);
	Trail->SetCastShadow(false);

	if (WaveMat)
	{
		MarkerMID = UMaterialInstanceDynamic::Create(WaveMat, this);
		MarkerMID->SetVectorParameterValue(TEXT("WaveColor"), FLinearColor(3.f, 0.15f, 0.05f));
		MarkerMID->SetScalarParameterValue(TEXT("Intensity"), 3.f);
		MarkerMID->SetScalarParameterValue(TEXT("Fade"), 0.8f);
		Marker->SetMaterial(0, MarkerMID);
	}
	Marker->SetStaticMesh(CylinderMesh);
	Marker->SetRelativeScale3D(FVector(ImpactRadius / 50.f, ImpactRadius / 50.f, 0.02f));
	Marker->SetRelativeLocation(FVector(0.f, 0.f, 3.f));
}

void ADropPod::Launch(const FVector& Site, TSubclassOf<AActor> EnemyClass, int32 Count)
{
	LandSite = Site;
	Cargo = EnemyClass;
	CargoCount = FMath::Max(Count, 0);
	SetActorLocation(Site);
	Build();
	PodPivot->SetRelativeLocation(FVector(0.f, 0.f, DropHeight));
	PodPivot->SetRelativeRotation(FRotator(0.f, FMath::FRandRange(0.f, 360.f), 0.f));
	Phase = EPhase::Warning;
	PhaseStart = GetWorld()->GetTimeSeconds();
	if (WhistleSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, WhistleSound, Site + FVector(0.f, 0.f, 800.f), 0.6f, 0.45f);
	}
}

void ADropPod::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = GetWorld()->GetTimeSeconds();
	const float Age = T - PhaseStart;
	switch (Phase)
	{
	case EPhase::Warning:
		if (MarkerMID)
		{
			MarkerMID->SetScalarParameterValue(TEXT("Fade"), 0.4f + 0.4f * FMath::Abs(FMath::Sin(Age * 14.f)));
		}
		if (Age >= WarnTime)
		{
			Phase = EPhase::Falling;
			PhaseStart = T;
		}
		break;
	case EPhase::Falling:
	{
		const float A = FMath::Clamp(Age / FallTime, 0.f, 1.f);
		PodPivot->SetRelativeLocation(FVector(0.f, 0.f, DropHeight * (1.f - A * A)));
		if (A >= 1.f)
		{
			Impact();
		}
		break;
	}
	case EPhase::Opening:
	{
		const float A = FMath::Clamp(Age / 0.35f, 0.f, 1.f);
		for (USceneComponent* Pivot : PetalPivots)
		{
			FRotator R = Pivot->GetRelativeRotation();
			R.Pitch = -FMath::Lerp(0.f, 110.f, FMath::InterpEaseOut(0.f, 1.f, A, 3.f));
			Pivot->SetRelativeRotation(R);
		}
		if (A >= 1.f)
		{
			Phase = EPhase::Unloading;
			PhaseStart = T;
			NextSpawn = T;
		}
		break;
	}
	case EPhase::Unloading:
		if (Spawned >= CargoCount)
		{
			Phase = EPhase::Lingering;
			PhaseStart = T;
		}
		else if (T >= NextSpawn)
		{
			SpawnPassenger(Spawned++);
			NextSpawn = T + 0.16f;
		}
		break;
	case EPhase::Lingering:
		// Sink into the sand and go away.
		if (Age > 8.f)
		{
			PodPivot->AddRelativeLocation(FVector(0.f, 0.f, -60.f * DeltaSeconds));
		}
		if (Age > 14.f)
		{
			Destroy();
		}
		break;
	default:
		break;
	}
}

void ADropPod::Impact()
{
	Phase = EPhase::Opening;
	PhaseStart = GetWorld()->GetTimeSeconds();
	PodPivot->SetRelativeLocation(FVector::ZeroVector);
	if (Trail)
	{
		Trail->SetVisibility(false);
	}
	Marker->SetVisibility(false);
	if (ImpactSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ImpactSound, LandSite, 0.9f, 0.7f);
	}
	if (SparkFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparkFX, LandSite + FVector(0.f, 0.f, 40.f));
	}
	if (ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0))
	{
		const FVector To = Player->GetActorLocation() - LandSite;
		if (To.Size2D() < ImpactRadius)
		{
			UGameplayStatics::ApplyDamage(Player, 1.f, nullptr, this, nullptr);
			Player->LaunchCharacter(To.GetSafeNormal2D() * 900.f + FVector(0.f, 0.f, 500.f), true, true);
		}
	}
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->AddHype(2.f);
	}
}

void ADropPod::SpawnPassenger(int32 Index)
{
	if (!Cargo)
	{
		return;
	}
	const float Angle = (Index * 360.f / FMath::Max(CargoCount, 1)) + FMath::FRandRange(-12.f, 12.f);
	const FVector Dir = FRotator(0.f, Angle, 0.f).Vector();
	const FVector Loc = LandSite + Dir * FMath::FRandRange(170.f, 240.f) + FVector(0.f, 0.f, 100.f);
	FRotator Facing = Dir.Rotation();
	if (const ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0))
	{
		Facing = (Player->GetActorLocation() - Loc).GetSafeNormal2D().Rotation();
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	if (AActor* Enemy = GetWorld()->SpawnActor<AActor>(Cargo, Loc, Facing, Params))
	{
		if (APawn* Pawn = Cast<APawn>(Enemy); Pawn && !Pawn->GetController() && Pawn->AIControllerClass)
		{
			Pawn->SpawnDefaultController();
		}
		if (AHordeDirector* Director = AHordeDirector::Get(this))
		{
			Director->RegisterEnemy(Enemy);
		}
	}
}
