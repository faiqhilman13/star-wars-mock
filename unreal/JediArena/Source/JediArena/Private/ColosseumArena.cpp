#include "ColosseumArena.h"

#include "FizzBarrel.h"
#include "JumpPad.h"
#include "SandGobbler.h"

#include "Components/BoxComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Scene.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Math/RotationMatrix.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/Package.h"

namespace ColArena
{
	/** Bump when the generator changes so saved arenas rebuild on their next construction. */
	constexpr uint32 BuildVersion = 4;

	constexpr int32 NumCrowdColors = 5;
	constexpr int32 NumFabrics = 3;
	constexpr int32 NumCrowdBins = 72;
	constexpr float CrowdBinDegrees = 360.f / NumCrowdBins;
	constexpr int32 NumPillars = 6;
	constexpr int32 NumPads = 4;
	constexpr int32 NumBarrelClusters = 4;
	constexpr int32 NumJumbos = 2;
	constexpr int32 NumBraziers = 8;
	constexpr float BrazierZ = 760.f;
	constexpr float PillarClearance = 420.f; // column + plinth + fallen drum
	constexpr float GateGlowIdle = 3.f;
	constexpr float GateGlowOpen = 14.f;

	const float PillarAngles[NumPillars] = { 25.f, 65.f, 205.f, 245.f, 295.f, 335.f };
	const float PadAngles[NumPads] = { 45.f, 135.f, 225.f, 315.f };
	const float BarrelAngles[NumBarrelClusters] = { 12.f, 102.f, 192.f, 282.f };
	const float JumboAngles[NumJumbos] = { 45.f, 225.f };
	const float InlayFractions[4] = { 0.3f, 0.48f, 0.67f, 0.86f };

	const FLinearColor SandColor(0.42f, 0.30f, 0.16f);
	const FLinearColor SandDarkColor(0.28f, 0.2f, 0.11f);
	const FLinearColor SandstoneColor(0.66f, 0.44f, 0.27f);
	const FLinearColor StoneLightColor(0.80f, 0.68f, 0.52f);
	const FLinearColor TerracottaColor(0.60f, 0.20f, 0.09f);
	const FLinearColor GlassColor(0.07f, 0.04f, 0.025f);
	const FLinearColor DaisColor(0.86f, 0.76f, 0.58f);
	const FLinearColor ScreenEmissive(0.05f, 0.18f, 0.55f);

	/** Spectator bodies: hot pink, lime, azure, tangerine, grape. */
	const FLinearColor BodyColors[NumCrowdColors] = {
		FLinearColor(0.95f, 0.10f, 0.45f), FLinearColor(0.35f, 0.90f, 0.05f), FLinearColor(0.05f, 0.55f, 1.00f),
		FLinearColor(1.00f, 0.45f, 0.02f), FLinearColor(0.50f, 0.12f, 0.95f) };
	/** Spectator heads (paired with the body colour of the same index). */
	const FLinearColor HeadColors[NumCrowdColors] = {
		FLinearColor(0.55f, 0.95f, 0.60f), FLinearColor(1.00f, 0.85f, 0.35f), FLinearColor(0.95f, 0.60f, 0.75f),
		FLinearColor(0.60f, 0.90f, 1.00f), FLinearColor(0.75f, 1.00f, 0.40f) };
	/** Pennants, awnings, drapes: cream, crimson, teal. */
	const FLinearColor FabricColors[NumFabrics] = {
		FLinearColor(0.95f, 0.85f, 0.60f), FLinearColor(0.80f, 0.10f, 0.12f), FLinearColor(0.05f, 0.45f, 0.75f) };
	/** Gate glow colours: N ember, E electric blue, S acid green, W violet. */
	const FLinearColor GateColors[4] = {
		FLinearColor(1.00f, 0.25f, 0.08f), FLinearColor(0.10f, 0.45f, 1.00f), FLinearColor(0.20f, 1.00f, 0.30f), FLinearColor(0.75f, 0.25f, 1.00f) };

	FName GeneratedTag()
	{
		static const FName Tag(TEXT("ArenaGen"));
		return Tag;
	}

	FVector Polar(float Radius, float Degrees, float Z)
	{
		float SinA = 0.f;
		float CosA = 1.f;
		FMath::SinCos(&SinA, &CosA, FMath::DegreesToRadians(Degrees));
		return FVector(CosA * Radius, SinA * Radius, Z);
	}

	FQuat YawQuat(float Degrees)
	{
		return FRotator(0.f, Degrees, 0.f).Quaternion();
	}

	/** Rotation about the local X axis (for diamonds / rods on radial-facing surfaces). */
	FQuat RollQuat(float Degrees)
	{
		return FQuat(FVector::ForwardVector, FMath::DegreesToRadians(Degrees));
	}

	float AngleDiff(float A, float B)
	{
		return FMath::Abs(FMath::FindDeltaAngleDegrees(A, B));
	}

	int32 AddBox(UInstancedStaticMeshComponent* ISM, const FVector& Center, const FVector& Size, const FQuat& Rot = FQuat::Identity)
	{
		return ISM ? ISM->AddInstance(FArenaKit::FitBox(ISM->GetStaticMesh(), Center, Size, Rot), false) : INDEX_NONE;
	}

	UStaticMesh* MeshOr(UStaticMesh* Preferred, const TCHAR* Path)
	{
		return Preferred ? Preferred : LoadObject<UStaticMesh>(nullptr, Path);
	}
}

// ============================================================================ FArenaKit

FTransform FArenaKit::FitBox(const UStaticMesh* Mesh, const FVector& Center, const FVector& Size, const FQuat& Rot)
{
	FVector Origin = FVector::ZeroVector;
	FVector Extent(50.0);
	if (Mesh)
	{
		const FBoxSphereBounds Bounds = Mesh->GetBounds();
		Origin = Bounds.Origin;
		Extent = Bounds.BoxExtent;
	}
	auto AxisScale = [](double Want, double Ext) { return Ext > 0.01 ? FMath::Max(Want, 0.1) / (2.0 * Ext) : 1.0; };
	const FVector Scale(AxisScale(Size.X, Extent.X), AxisScale(Size.Y, Extent.Y), AxisScale(Size.Z, Extent.Z));
	return FTransform(Rot, Center - Rot.RotateVector(Origin * Scale), Scale);
}

void FArenaKit::SetSurfaceParams(UMaterialInstanceDynamic* MID, const FLinearColor& Base, const FLinearColor& Emissive, float Roughness, float Metallic)
{
	if (!MID)
	{
		return;
	}
	MID->SetVectorParameterValue(TEXT("BaseColor"), Base);
	MID->SetVectorParameterValue(TEXT("Emissive"), Emissive);
	MID->SetScalarParameterValue(TEXT("Roughness"), Roughness);
	MID->SetScalarParameterValue(TEXT("Metallic"), Metallic);
}

UMaterialInstanceDynamic* FArenaKit::SharedSurfaceMID(UMaterialInterface* Parent, const FLinearColor& Base, const FLinearColor& Emissive, float Roughness, float Metallic)
{
	if (!Parent)
	{
		return nullptr;
	}
	static TMap<FString, TWeakObjectPtr<UMaterialInstanceDynamic>> Cache;
	const FString Key = FString::Printf(TEXT("%s|%.3f,%.3f,%.3f|%.3f,%.3f,%.3f|%.2f|%.2f"), *Parent->GetPathName(),
		Base.R, Base.G, Base.B, Emissive.R, Emissive.G, Emissive.B, Roughness, Metallic);
	if (const TWeakObjectPtr<UMaterialInstanceDynamic>* Found = Cache.Find(Key))
	{
		if (UMaterialInstanceDynamic* Existing = Found->Get())
		{
			return Existing;
		}
	}
	UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(Parent, GetTransientPackage());
	SetSurfaceParams(MID, Base, Emissive, Roughness, Metallic);
	Cache.Add(Key, MID);
	return MID;
}

void FArenaKit::NoCollision(UPrimitiveComponent* Prim)
{
	if (!Prim)
	{
		return;
	}
	Prim->SetCollisionProfileName(TEXT("NoCollision"));
	Prim->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Prim->SetGenerateOverlapEvents(false);
	Prim->SetCanEverAffectNavigation(false);
}

// ============================================================================ construction

AColosseumArena::AColosseumArena()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	ArenaRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ArenaRoot"));
	ArenaRoot->SetMobility(EComponentMobility::Movable);
	RootComponent = ArenaRoot;

#if WITH_EDITORONLY_DATA
	// Geometry is built in local space, so dragging the actor never needs a rebuild.
	bRunConstructionScriptOnDrag = false;
#endif

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> SurfaceFinder(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MetalFinder(TEXT("/Game/Jedi/Materials/MI_ArenaMetal.MI_ArenaMetal"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> LavaFinder(TEXT("/Game/Jedi/Materials/MI_Lava.MI_Lava"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ChamferFinder(TEXT("/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube"));
	static ConstructorHelpers::FObjectFinder<USoundBase> GateSoundFinder(TEXT("/Game/Jedi/Audio/Licensed/SW_Remote_Explode.SW_Remote_Explode"));

	SurfaceMaterial = SurfaceFinder.Object;
	MetalMaterial = MetalFinder.Object;
	LavaMaterial = LavaFinder.Object;
	CubeMesh = CubeFinder.Object;
	SphereMesh = SphereFinder.Object;
	CylinderMesh = CylinderFinder.Object;
	ConeMesh = ConeFinder.Object;
	ChamferCubeMesh = ChamferFinder.Object;
	GateSound = GateSoundFinder.Object;

	GobblerClass = ASandGobbler::StaticClass();
	BarrelClass = AFizzBarrel::StaticClass();
	JumpPadClass = AJumpPad::StaticClass();
}

void AColosseumArena::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	if (BuiltHash != ComputeBuildHash() || !IsBuildValid())
	{
		BuildArena();
	}
}

void AColosseumArena::RebuildArena()
{
	BuildArena();
	if (HasActorBegunPlay())
	{
		InitRuntime();
	}
}

void AColosseumArena::BeginPlay()
{
	Super::BeginPlay();
	if (!IsBuildValid())
	{
		BuildArena();
	}
	InitRuntime();
	if (bSpawnProps && HasAuthority())
	{
		SpawnProps();
	}
}

void AColosseumArena::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (EndPlayReason == EEndPlayReason::Destroyed)
	{
		for (AActor* Prop : SpawnedProps)
		{
			if (IsValid(Prop))
			{
				Prop->Destroy();
			}
		}
	}
	SpawnedProps.Reset();
	Super::EndPlay(EndPlayReason);
}

uint32 AColosseumArena::ComputeBuildHash() const
{
	uint32 H = GetTypeHash(ColArena::BuildVersion);
	auto Mix = [&H](uint32 V) { H = HashCombine(H, V); };
	Mix(GetTypeHash(ArenaRadius));
	Mix(GetTypeHash(WallHeight));
	Mix(GetTypeHash(WallThickness));
	Mix(GetTypeHash(WallSegments));
	Mix(GetTypeHash(GateWidth));
	Mix(GetTypeHash(GateHeight));
	Mix(GetTypeHash(StandTiers));
	Mix(GetTypeHash(TierDepth));
	Mix(GetTypeHash(TierRise));
	Mix(GetTypeHash(DaisRadius));
	Mix(GetTypeHash(DaisHeight));
	Mix(GetTypeHash(PillarRing));
	Mix(GetTypeHash(PitRadius));
	Mix(GetTypeHash(PitDistance));
	Mix(GetTypeHash(PitAngle));
	Mix(GetTypeHash(Seed));
	Mix(GetTypeHash(CrowdSpacing));
	Mix(GetTypeHash(CrowdFill));
	Mix(GetTypeHash(BrazierIntensity));
	Mix(GetTypeHash(BrazierRadius));
	Mix(GetTypeHash(PylonIntensity));
	Mix(GetTypeHash(JumpPadInset));
	Mix(GetTypeHash(GetPathNameSafe(SurfaceMaterial.Get())));
	Mix(GetTypeHash(GetPathNameSafe(MetalMaterial.Get())));
	Mix(GetTypeHash(GetPathNameSafe(LavaMaterial.Get())));
	Mix(GetTypeHash(GetPathNameSafe(CubeMesh.Get())));
	Mix(GetTypeHash(GetPathNameSafe(SphereMesh.Get())));
	Mix(GetTypeHash(GetPathNameSafe(CylinderMesh.Get())));
	Mix(GetTypeHash(GetPathNameSafe(ConeMesh.Get())));
	Mix(GetTypeHash(GetPathNameSafe(ChamferCubeMesh.Get())));
	return H;
}

bool AColosseumArena::IsBuildValid() const
{
	if (GateDoors.Num() != 4 || CrowdBodies.Num() == 0 || CrowdBodies.Num() != CrowdHeads.Num() || FabricISMs.Num() == 0)
	{
		return false;
	}
	for (const TObjectPtr<USceneComponent>& Door : GateDoors)
	{
		if (!IsValid(Door.Get()))
		{
			return false;
		}
	}
	for (int32 c = 0; c < CrowdBodies.Num(); ++c)
	{
		if (!IsValid(CrowdBodies[c].Get()) || !IsValid(CrowdHeads[c].Get()))
		{
			return false;
		}
	}
	for (const TObjectPtr<UInstancedStaticMeshComponent>& Fabric : FabricISMs)
	{
		if (!IsValid(Fabric.Get()))
		{
			return false;
		}
	}
	return IsValid(FlameISM.Get()) && IsValid(FaceISM.Get()) && IsValid(CrystalComp.Get()) && IsValid(RingAComp.Get())
		&& IsValid(RingBComp.Get()) && IsValid(MoonsComp.Get());
}

void AColosseumArena::ClearGenerated()
{
	TArray<UActorComponent*> ToDestroy;
	for (UActorComponent* Comp : GeneratedComponents)
	{
		if (IsValid(Comp))
		{
			ToDestroy.AddUnique(Comp);
		}
	}
	// Stragglers from older builds carry the tag too.
	TInlineComponentArray<UActorComponent*> Owned(this);
	for (UActorComponent* Comp : Owned)
	{
		if (IsValid(Comp) && Comp->ComponentHasTag(ColArena::GeneratedTag()))
		{
			ToDestroy.AddUnique(Comp);
		}
	}
	// Children were created after their parents: destroy in reverse.
	for (int32 i = ToDestroy.Num() - 1; i >= 0; --i)
	{
		if (IsValid(ToDestroy[i]))
		{
			ToDestroy[i]->DestroyComponent();
		}
	}

	GeneratedComponents.Reset();
	GeneratedMIDs.Reset();
	CrowdBodies.Reset();
	CrowdHeads.Reset();
	GateDoors.Reset();
	GateMIDs.Reset();
	FabricISMs.Reset();
	PennantCounts.Reset();
	BrazierLights.Reset();
	FlameISM = nullptr;
	FaceISM = nullptr;
	ScreenMID = nullptr;
	CrystalComp = nullptr;
	RingAComp = nullptr;
	RingBComp = nullptr;
	MoonsComp = nullptr;
	PylonLight = nullptr;

	Crowd.Reset();
	Hops.Reset();
	Pennants.Reset();
	FlameBase.Reset();
	FaceBase.Reset();
	bRuntimeReady = false;
}

void AColosseumArena::FinishComponent(UActorComponent* Comp)
{
	Comp->ComponentTags.AddUnique(ColArena::GeneratedTag());
	AddInstanceComponent(Comp);
	GeneratedComponents.Add(Comp);
}

void AColosseumArena::ApplyCollision(UPrimitiveComponent* Prim, EArenaCollision Collision) const
{
	switch (Collision)
	{
	case EArenaCollision::BlockAll:
		Prim->SetCollisionProfileName(TEXT("BlockAll"));
		Prim->SetGenerateOverlapEvents(false);
		break;
	case EArenaCollision::PawnBarrier:
		Prim->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Prim->SetCollisionObjectType(ECC_WorldStatic);
		Prim->SetCollisionResponseToAllChannels(ECR_Ignore);
		Prim->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
		Prim->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Block);
		Prim->SetGenerateOverlapEvents(false);
		break;
	default:
		FArenaKit::NoCollision(Prim);
		break;
	}
}

UMaterialInstanceDynamic* AColosseumArena::MakeMID(const FLinearColor& Base, const FLinearColor& Emissive, float Roughness, float Metallic)
{
	UMaterialInterface* Parent = SurfaceMaterial ? SurfaceMaterial.Get() : UMaterial::GetDefaultMaterial(MD_Surface);
	UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(Parent, this);
	FArenaKit::SetSurfaceParams(MID, Base, Emissive, Roughness, Metallic);
	GeneratedMIDs.Add(MID);
	return MID;
}

UInstancedStaticMeshComponent* AColosseumArena::MakeISM(const TCHAR* BaseName, UStaticMesh* Mesh, UMaterialInterface* Material, EArenaCollision Collision, bool bShadows, USceneComponent* Parent)
{
	UInstancedStaticMeshComponent* ISM = NewObject<UInstancedStaticMeshComponent>(this, UInstancedStaticMeshComponent::StaticClass(),
		MakeUniqueObjectName(this, UInstancedStaticMeshComponent::StaticClass(), FName(BaseName)), RF_Transactional);
	ISM->SetMobility(EComponentMobility::Movable);
	ISM->SetupAttachment(Parent ? Parent : ArenaRoot.Get());
	ISM->SetStaticMesh(Mesh);
	if (Material)
	{
		ISM->SetMaterial(0, Material);
	}
	ISM->SetCastShadow(bShadows);
	ApplyCollision(ISM, Collision);
	ISM->SetCanEverAffectNavigation(false);
	FinishComponent(ISM);
	return ISM;
}

UStaticMeshComponent* AColosseumArena::MakeMesh(const TCHAR* BaseName, UStaticMesh* Mesh, UMaterialInterface* Material, EArenaCollision Collision, const FTransform& RelativeXf)
{
	UStaticMeshComponent* SMC = NewObject<UStaticMeshComponent>(this, UStaticMeshComponent::StaticClass(),
		MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(), FName(BaseName)), RF_Transactional);
	SMC->SetMobility(EComponentMobility::Movable);
	SMC->SetupAttachment(ArenaRoot);
	SMC->SetStaticMesh(Mesh);
	if (Material)
	{
		SMC->SetMaterial(0, Material);
	}
	SMC->SetRelativeTransform(RelativeXf);
	ApplyCollision(SMC, Collision);
	SMC->SetCanEverAffectNavigation(false);
	FinishComponent(SMC);
	return SMC;
}

UPointLightComponent* AColosseumArena::MakeLight(const FVector& RelativeLocation, const FLinearColor& Color, float Candelas, float Radius)
{
	UPointLightComponent* Light = NewObject<UPointLightComponent>(this, UPointLightComponent::StaticClass(),
		MakeUniqueObjectName(this, UPointLightComponent::StaticClass(), FName(TEXT("ArenaLight"))), RF_Transactional);
	Light->SetMobility(EComponentMobility::Movable);
	Light->SetupAttachment(ArenaRoot);
	Light->SetRelativeLocation(RelativeLocation);
	Light->IntensityUnits = ELightUnits::Candelas;
	Light->SetIntensity(Candelas);
	Light->SetLightColor(Color);
	Light->SetAttenuationRadius(Radius);
	Light->SetCastShadows(false);
	FinishComponent(Light);
	return Light;
}

void AColosseumArena::BuildArena()
{
	ClearGenerated();

	UStaticMesh* Cube = ColArena::MeshOr(CubeMesh, TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* Sphere = ColArena::MeshOr(SphereMesh, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	UStaticMesh* Cylinder = ColArena::MeshOr(CylinderMesh, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	UStaticMesh* Cone = ColArena::MeshOr(ConeMesh, TEXT("/Engine/BasicShapes/Cone.Cone"));
	UStaticMesh* Chamfer = ChamferCubeMesh ? ChamferCubeMesh.Get() : Cube;
	if (!Cube || !Sphere || !Cylinder || !Cone || !ArenaRoot)
	{
		UE_LOG(LogTemp, Warning, TEXT("ColosseumArena: basic shape meshes are missing, nothing was built."));
		return;
	}

	FRandomStream Rng(Seed);
	const float R = ArenaRadius;
	const float T = WallThickness;
	const int32 Segs = SegmentCount();
	const float Step = 360.f / Segs;
	const float GapHalf = GateGapHalfAngle();
	const float SinHalfStep = FMath::Sin(FMath::DegreesToRadians(Step * 0.5f));
	const float OpenH = GateOpeningHeight();
	const float StandsInner = R + T;
	const float BackR = StandsInner + StandTiers * TierDepth;
	const float TopTierZ = TierTopZ(StandTiers - 1) + TierRise * 0.5f;
	const float BackTop = TopTierZ + 300.f;
	const float PoleH = 620.f;
	const FVector PitL = PitLocal();

	// ------------------------------------------------------------------ materials: one MID per colour, shared by all instances
	UMaterialInstanceDynamic* SandMID = MakeMID(ColArena::SandColor, FLinearColor::Black, 0.85f, 0.f);
	UMaterialInstanceDynamic* SandDarkMID = MakeMID(ColArena::SandDarkColor, FLinearColor::Black, 0.9f, 0.f);
	UMaterialInstanceDynamic* SandstoneMID = MakeMID(ColArena::SandstoneColor, FLinearColor::Black, 0.75f, 0.f);
	UMaterialInstanceDynamic* StoneMID = MakeMID(ColArena::StoneLightColor, FLinearColor::Black, 0.8f, 0.f);
	UMaterialInstanceDynamic* TerracottaMID = MakeMID(ColArena::TerracottaColor, FLinearColor::Black, 0.7f, 0.f);
	UMaterialInstanceDynamic* GlassMID = MakeMID(ColArena::GlassColor, FLinearColor(0.02f, 0.01f, 0.f), 0.06f, 0.35f);
	UMaterialInstanceDynamic* RuneMID = MakeMID(FLinearColor(0.05f, 0.25f, 0.3f), FLinearColor(0.3f, 2.2f, 3.f), 0.3f, 0.f);
	UMaterialInstanceDynamic* GoldMID = MakeMID(FLinearColor(1.f, 0.62f, 0.18f), FLinearColor(2.6f, 1.4f, 0.25f), 0.3f, 0.8f);
	UMaterialInstanceDynamic* DaisMID = MakeMID(ColArena::DaisColor, FLinearColor::Black, 0.35f, 0.05f);
	UMaterialInstanceDynamic* BlackMID = MakeMID(FLinearColor(0.004f, 0.003f, 0.004f), FLinearColor::Black, 1.f, 0.f);
	UMaterialInstanceDynamic* CrystalMID = MakeMID(FLinearColor(0.3f, 0.85f, 1.f), FLinearColor(0.5f, 2.f, 2.8f), 0.05f, 0.f);
	UMaterialInstanceDynamic* FlameMID = MakeMID(FLinearColor(1.f, 0.45f, 0.08f), FLinearColor(9.f, 3.f, 0.4f), 1.f, 0.f);
	UMaterialInstanceDynamic* FaceMID = MakeMID(FLinearColor(0.6f, 0.95f, 1.f), FLinearColor(1.5f, 4.f, 5.f), 0.5f, 0.f);
	ScreenMID = MakeMID(FLinearColor(0.01f, 0.02f, 0.05f), ColArena::ScreenEmissive, 0.2f, 0.f);
	UMaterialInterface* Metal = MetalMaterial ? MetalMaterial.Get() : static_cast<UMaterialInterface*>(MakeMID(FLinearColor(0.3f, 0.3f, 0.32f), FLinearColor::Black, 0.35f, 1.f));
	UMaterialInterface* Coals = LavaMaterial ? LavaMaterial.Get() : static_cast<UMaterialInterface*>(FlameMID);

	// ------------------------------------------------------------------ components
	MakeMesh(TEXT("ArenaFloor"), Cylinder, SandMID, EArenaCollision::BlockAll,
		FArenaKit::FitBox(Cylinder, FVector(0.f, 0.f, -100.f), FVector(2.f * (StandsInner + 80.f), 2.f * (StandsInner + 80.f), 200.f)));
	const float OuterR = BackR + 150.f + 3000.f;
	MakeMesh(TEXT("OuterGround"), Cylinder, SandDarkMID, EArenaCollision::BlockAll,
		FArenaKit::FitBox(Cylinder, FVector(0.f, 0.f, -60.f), FVector(2.f * OuterR, 2.f * OuterR, 100.f)));

	UInstancedStaticMeshComponent* GlassISM = MakeISM(TEXT("DuneGlass"), Cube, GlassMID, EArenaCollision::None, true);
	UInstancedStaticMeshComponent* RuneISM = MakeISM(TEXT("Runes"), Cube, RuneMID, EArenaCollision::None, false);
	UInstancedStaticMeshComponent* SandstoneISM = MakeISM(TEXT("Sandstone"), Chamfer, SandstoneMID, EArenaCollision::BlockAll, true);
	UInstancedStaticMeshComponent* TerracottaISM = MakeISM(TEXT("Terracotta"), Chamfer, TerracottaMID, EArenaCollision::None, true);
	UInstancedStaticMeshComponent* StandISM = MakeISM(TEXT("Stands"), Chamfer, StoneMID, EArenaCollision::BlockAll, true);
	UInstancedStaticMeshComponent* BarrierISM = MakeISM(TEXT("CrowdBarrier"), Cube, nullptr, EArenaCollision::PawnBarrier, false);
	BarrierISM->SetVisibility(false);
	BarrierISM->SetHiddenInGame(true);
	UInstancedStaticMeshComponent* TunnelISM = MakeISM(TEXT("GateTunnels"), Cube, BlackMID, EArenaCollision::BlockAll, false);
	UInstancedStaticMeshComponent* ColumnISM = MakeISM(TEXT("Columns"), Cylinder, SandstoneMID, EArenaCollision::BlockAll, true);
	UInstancedStaticMeshComponent* GlowBandISM = MakeISM(TEXT("GlowBands"), Cylinder, RuneMID, EArenaCollision::None, false);
	UInstancedStaticMeshComponent* MetalISM = MakeISM(TEXT("MetalWork"), Cylinder, Metal, EArenaCollision::None, true);
	UInstancedStaticMeshComponent* SpireISM = MakeISM(TEXT("Spires"), Cone, TerracottaMID, EArenaCollision::None, true);
	UInstancedStaticMeshComponent* GoldISM = MakeISM(TEXT("GoldTrim"), Cube, GoldMID, EArenaCollision::None, false);
	UInstancedStaticMeshComponent* ScreenISM = MakeISM(TEXT("JumboScreens"), Cube, ScreenMID, EArenaCollision::None, false);
	FaceISM = MakeISM(TEXT("JumboFaces"), Cube, FaceMID, EArenaCollision::None, false);
	UInstancedStaticMeshComponent* CoalISM = MakeISM(TEXT("BrazierCoals"), Sphere, Coals, EArenaCollision::None, false);
	FlameISM = MakeISM(TEXT("BrazierFlames"), Cone, FlameMID, EArenaCollision::None, false);
	UInstancedStaticMeshComponent* DaisISM = MakeISM(TEXT("DaisRamp"), Cube, DaisMID, EArenaCollision::BlockAll, true);
	UInstancedStaticMeshComponent* ShardISM = MakeISM(TEXT("CrystalShards"), Cone, CrystalMID, EArenaCollision::None, true);
	for (int32 f = 0; f < ColArena::NumFabrics; ++f)
	{
		FabricISMs.Add(MakeISM(TEXT("Fabric"), Cube, MakeMID(ColArena::FabricColors[f], FLinearColor::Black, 0.9f, 0.f), EArenaCollision::None, true));
	}
	PennantCounts.Init(0, ColArena::NumFabrics);
	for (int32 c = 0; c < ColArena::NumCrowdColors; ++c)
	{
		CrowdBodies.Add(MakeISM(TEXT("CrowdBodies"), Sphere, MakeMID(ColArena::BodyColors[c], ColArena::BodyColors[c] * 0.05f, 0.55f, 0.f), EArenaCollision::None, false));
		CrowdHeads.Add(MakeISM(TEXT("CrowdHeads"), Sphere, MakeMID(ColArena::HeadColors[c], FLinearColor::Black, 0.5f, 0.f), EArenaCollision::None, false));
	}

	// ------------------------------------------------------------------ floor: glassy ring inlays + glowing runes
	for (const float Frac : ColArena::InlayFractions)
	{
		const float RingR = R * Frac;
		const int32 N = FMath::Max(24, FMath::CeilToInt(2.f * PI * RingR / 260.f));
		const float Chord = 2.f * RingR * FMath::Sin(PI / N) * 1.04f;
		for (int32 k = 0; k < N; ++k)
		{
			const float A = (k + 0.5f) * 360.f / N;
			const FVector P = ColArena::Polar(RingR, A, 0.5f);
			if (!IsFloorSpotBlocked(P, 40.f))
			{
				ColArena::AddBox(GlassISM, P, FVector(70.f, Chord, 4.f), ColArena::YawQuat(A));
			}
		}
	}
	for (int32 s = 0; s < 8; ++s)
	{
		const float A = 22.5f + 45.f * s;
		const float R0 = R * 0.3f + 90.f;
		const float R1 = R * 0.48f - 90.f;
		const int32 Dashes = FMath::Max(2, FMath::FloorToInt((R1 - R0) / 150.f));
		for (int32 d = 0; d < Dashes; ++d)
		{
			const FVector P = ColArena::Polar(FMath::Lerp(R0, R1, (d + 0.5f) / Dashes), A, 0.5f);
			if (!IsFloorSpotBlocked(P, 20.f))
			{
				ColArena::AddBox(RuneISM, P, FVector(90.f, 16.f, 3.f), ColArena::YawQuat(A));
			}
		}
		const FVector Glyph = ColArena::Polar(R * 0.48f, A, 2.f);
		if (!IsFloorSpotBlocked(Glyph, 40.f))
		{
			ColArena::AddBox(RuneISM, Glyph, FVector(110.f, 110.f, 3.f), ColArena::YawQuat(A + 45.f));
			ColArena::AddBox(GlassISM, Glyph + FVector(0.f, 0.f, 0.5f), FVector(60.f, 60.f, 3.f), ColArena::YawQuat(A + 45.f));
		}
	}
	{
		const float FloorRuneR = DaisOuterRadius() + 90.f;
		for (int32 k = 0; k < 48; ++k)
		{
			const float A = k * 7.5f;
			ColArena::AddBox(RuneISM, ColArena::Polar(FloorRuneR, A, 0.5f), FVector(14.f, 2.f * PI * FloorRuneR / 48.f * 0.55f, 3.f), ColArena::YawQuat(A));
		}
		const float TopRuneR = DaisRadius - 70.f;
		for (int32 k = 0; k < 40; ++k)
		{
			const float A = k * 9.f;
			ColArena::AddBox(RuneISM, ColArena::Polar(TopRuneR, A, DaisHeight + 0.5f), FVector(12.f, 2.f * PI * TopRuneR / 40.f * 0.55f, 3.f), ColArena::YawQuat(A));
		}
	}

	// ------------------------------------------------------------------ ring wall (segmented, gaps at the four gates)
	const float OuterChord = 2.f * (R + T) * SinHalfStep * 1.02f;
	const float InnerChord = 2.f * R * SinHalfStep;
	for (int32 i = 0; i < Segs; ++i)
	{
		const float A = (i + 0.5f) * Step;
		const FQuat Q = ColArena::YawQuat(A);
		// Invisible barrier above the wall keeps jump-pad / double-jump antics inside the bowl.
		ColArena::AddBox(BarrierISM, ColArena::Polar(R + T * 0.5f, A, WallHeight + 1600.f), FVector(T + 200.f, OuterChord * 1.05f, 3200.f), Q);

		bool bGateGap = false;
		for (int32 g = 0; g < 4; ++g)
		{
			if (ColArena::AngleDiff(A, GateAngle(g)) < GapHalf - 0.01f)
			{
				bGateGap = true;
			}
		}
		if (bGateGap)
		{
			continue;
		}
		ColArena::AddBox(SandstoneISM, ColArena::Polar(R + T * 0.5f, A, WallHeight * 0.5f), FVector(T, OuterChord, WallHeight), Q);
		ColArena::AddBox(TerracottaISM, ColArena::Polar(R + T * 0.5f, A, WallHeight + 15.f), FVector(T + 40.f, OuterChord * 1.01f, 30.f), Q);
		for (int32 m = 0; m < 2; ++m)
		{
			const float MA = A + (m == 0 ? -0.25f : 0.25f) * Step;
			ColArena::AddBox(TerracottaISM, ColArena::Polar(R + T * 0.3f, MA, WallHeight + 90.f), FVector(T * 0.5f, InnerChord * 0.3f, 120.f), ColArena::YawQuat(MA));
		}
		ColArena::AddBox(GlassISM, ColArena::Polar(R - 15.f, A, 45.f), FVector(30.f, InnerChord * 1.02f, 90.f), Q);
		ColArena::AddBox(RuneISM, ColArena::Polar(R - 4.f, A, 420.f), FVector(8.f, InnerChord * 1.02f, 16.f), Q);
		if (i % 2 == 0)
		{
			ColArena::AddBox(GlassISM, ColArena::Polar(R - 6.f, A, 690.f), FVector(12.f, InnerChord * 0.62f, 380.f), Q);
		}
	}

	// ------------------------------------------------------------------ gates: towers, lintel, arch, emblem, tunnel, chevrons, portcullis
	{
		const float GapRad = FMath::DegreesToRadians(GapHalf);
		const float InnerX = R * FMath::Cos(GapRad);
		const float HalfW = GateWidth * 0.5f;
		const float TowerX0 = InnerX - 60.f;
		const float TowerX1 = R + T + 40.f;
		const float TowerY0 = HalfW;
		const float TowerY1 = FMath::Max((R + T) * FMath::Sin(GapRad) + 40.f, HalfW + 150.f);
		const float TowerH = WallHeight + 250.f;
		const float ArchR = HalfW + 110.f;
		const float ArchZ = OpenH - 20.f;
		const float ArchX = InnerX - 70.f;
		const int32 NumVoussoirs = 11;
		const float TunnelX = R + T - 40.f;
		const float EmblemZ = FMath::Min(OpenH + 160.f, WallHeight - 140.f);

		for (int32 g = 0; g < 4; ++g)
		{
			const FQuat GQ = ColArena::YawQuat(GateAngle(g));
			auto GP = [&GQ](float LX, float LY, float LZ) { return GQ.RotateVector(FVector(LX, LY, LZ)); };

			UMaterialInstanceDynamic* GateMID = MakeMID(ColArena::GateColors[g] * 0.25f, ColArena::GateColors[g] * ColArena::GateGlowIdle, 0.4f, 0.f);
			GateMIDs.Add(GateMID);
			UInstancedStaticMeshComponent* GateGlowISM = MakeISM(TEXT("GateGlow"), Cube, GateMID, EArenaCollision::None, false);

			for (int32 Side = -1; Side <= 1; Side += 2)
			{
				const float TY = Side * (TowerY0 + TowerY1) * 0.5f;
				const float TX = (TowerX0 + TowerX1) * 0.5f;
				ColArena::AddBox(SandstoneISM, GP(TX, TY, TowerH * 0.5f), FVector(TowerX1 - TowerX0, TowerY1 - TowerY0, TowerH), GQ);
				ColArena::AddBox(TerracottaISM, GP(TX, TY, TowerH + 20.f), FVector(TowerX1 - TowerX0 + 40.f, TowerY1 - TowerY0 + 40.f, 40.f), GQ);
				const float SpireD = FMath::Min(TowerX1 - TowerX0, TowerY1 - TowerY0) * 0.95f;
				ColArena::AddBox(SpireISM, GP(TX, TY, TowerH + 40.f + 190.f), FVector(SpireD, SpireD, 380.f), GQ);
				ColArena::AddBox(GateGlowISM, GP(TowerX0 - 5.f, TY, 420.f), FVector(8.f, 34.f, 640.f), GQ);
				ColArena::AddBox(GateGlowISM, GP(TowerX0 - 8.f, TY, OpenH + 130.f), FVector(10.f, 80.f, 80.f), GQ * ColArena::RollQuat(45.f));
			}

			// Lintel above the opening; the portcullis slides up into it.
			ColArena::AddBox(SandstoneISM, GP((InnerX + R + T) * 0.5f, 0.f, (OpenH + WallHeight) * 0.5f), FVector(R + T - InnerX, GateWidth + 60.f, WallHeight - OpenH), GQ);

			// Voussoir arch on the inner face, keystone glowing in the gate colour.
			for (int32 v = 0; v < NumVoussoirs; ++v)
			{
				const float Phi = PI * (v + 0.5f) / NumVoussoirs;
				const FVector Radial(0.f, FMath::Cos(Phi), FMath::Sin(Phi));
				const FVector StoneCenter = FVector(ArchX, 0.f, ArchZ) + Radial * ArchR;
				const FQuat StoneQ = FRotationMatrix::MakeFromXZ(FVector::ForwardVector, Radial).ToQuat();
				const bool bKey = v == NumVoussoirs / 2;
				const FVector StoneSize(bKey ? 110.f : 80.f, PI * ArchR / NumVoussoirs * 1.08f, bKey ? 230.f : 160.f);
				ColArena::AddBox(bKey ? GateGlowISM : TerracottaISM, GQ.RotateVector(StoneCenter), StoneSize, GQ * StoneQ);
			}

			// Diamond emblem on the lintel.
			ColArena::AddBox(GateGlowISM, GP(InnerX - 8.f, 0.f, EmblemZ), FVector(10.f, 190.f, 190.f), GQ * ColArena::RollQuat(45.f));
			ColArena::AddBox(GlassISM, GP(InnerX - 14.f, 0.f, EmblemZ), FVector(6.f, 110.f, 110.f), GQ * ColArena::RollQuat(45.f));

			// Pitch-black tunnel behind the bars... with something blinking in it.
			ColArena::AddBox(TunnelISM, GP(TunnelX, 0.f, OpenH * 0.5f), FVector(20.f, GateWidth + 60.f, OpenH + 20.f), GQ);
			for (int32 e = 0; e < 3; ++e)
			{
				const float EyeY = Rng.FRandRange(-HalfW + 80.f, HalfW - 80.f);
				const float EyeZ = Rng.FRandRange(110.f, OpenH * 0.6f);
				for (int32 Side = -1; Side <= 1; Side += 2)
				{
					ColArena::AddBox(GateGlowISM, GP(TunnelX - 12.f, EyeY + Side * 22.f, EyeZ), FVector(4.f, 18.f, 10.f), GQ);
				}
			}

			// Floor chevrons pointing into the arena: "stuff comes out of here".
			for (int32 c = 0; c < 3; ++c)
			{
				const float TipX = R - 700.f - c * 260.f;
				for (int32 Side = -1; Side <= 1; Side += 2)
				{
					const float ArmYaw = 40.f * Side;
					const FVector ArmDir = ColArena::YawQuat(ArmYaw).GetForwardVector();
					ColArena::AddBox(GateGlowISM, GQ.RotateVector(FVector(TipX, 0.f, 1.f) + ArmDir * 75.f), FVector(150.f, 26.f, 3.f), GQ * ColArena::YawQuat(ArmYaw));
				}
			}

			// Portcullis: a blocking box that slides up, carrying bars, cross-beams and spikes.
			UBoxComponent* Door = NewObject<UBoxComponent>(this, UBoxComponent::StaticClass(),
				MakeUniqueObjectName(this, UBoxComponent::StaticClass(), FName(TEXT("GateDoor"))), RF_Transactional);
			Door->SetMobility(EComponentMobility::Movable);
			Door->SetupAttachment(ArenaRoot);
			Door->SetBoxExtent(FVector(30.f, HalfW + 25.f, OpenH * 0.5f), false);
			Door->SetRelativeLocationAndRotation(DoorClosedLocal(g), GQ);
			Door->SetCollisionProfileName(TEXT("BlockAllDynamic"));
			Door->SetGenerateOverlapEvents(false);
			Door->SetCanEverAffectNavigation(false);
			Door->SetHiddenInGame(true);
			FinishComponent(Door);
			GateDoors.Add(Door);

			UInstancedStaticMeshComponent* BarsISM = MakeISM(TEXT("GateBars"), Cube, Metal, EArenaCollision::None, true, Door);
			const int32 NumBars = FMath::Max(3, FMath::RoundToInt(GateWidth / 85.f));
			for (int32 b = 0; b < NumBars; ++b)
			{
				const float BarY = FMath::Lerp(-HalfW + 35.f, HalfW - 35.f, static_cast<float>(b) / (NumBars - 1));
				ColArena::AddBox(BarsISM, FVector(0.f, BarY, 0.f), FVector(20.f, 20.f, OpenH));
				ColArena::AddBox(BarsISM, FVector(0.f, BarY, -OpenH * 0.5f - 10.f), FVector(16.f, 30.f, 30.f), ColArena::RollQuat(45.f));
			}
			const float CrossZs[4] = { -0.32f, 0.f, 0.32f, 0.48f };
			for (const float CZ : CrossZs)
			{
				ColArena::AddBox(BarsISM, FVector(0.f, 0.f, CZ * OpenH), FVector(26.f, GateWidth + 40.f, 24.f));
			}
		}
	}

	// ------------------------------------------------------------------ cover columns (some broken, with fallen drums)
	for (int32 p = 0; p < ColArena::NumPillars; ++p)
	{
		const FVector Foot = PillarLocal(p);
		const float PA = ColArena::PillarAngles[p];
		const bool bBroken = (p % 2) == 1;
		const float ShaftH = bBroken ? Rng.FRandRange(300.f, 480.f) : 720.f;
		ColArena::AddBox(SandstoneISM, Foot + FVector(0.f, 0.f, 35.f), FVector(320.f, 320.f, 70.f), ColArena::YawQuat(PA));
		ColArena::AddBox(ColumnISM, Foot + FVector(0.f, 0.f, 70.f + ShaftH * 0.5f), FVector(210.f, 210.f, ShaftH));
		ColArena::AddBox(GlowBandISM, Foot + FVector(0.f, 0.f, 70.f + 170.f), FVector(218.f, 218.f, 22.f));
		if (bBroken)
		{
			ColArena::AddBox(ColumnISM, Foot + FVector(20.f, -15.f, 70.f + ShaftH + 25.f), FVector(160.f, 160.f, 70.f), FRotator(14.f, PA, 9.f).Quaternion());
			const float DrumYaw = PA + Rng.FRandRange(60.f, 120.f);
			ColArena::AddBox(ColumnISM, Foot + ColArena::Polar(300.f, DrumYaw, 100.f), FVector(200.f, 200.f, 200.f), FRotator(90.f, DrumYaw + 90.f, 0.f).Quaternion());
		}
		else
		{
			ColArena::AddBox(SandstoneISM, Foot + FVector(0.f, 0.f, 70.f + ShaftH + 30.f), FVector(290.f, 290.f, 60.f), ColArena::YawQuat(PA));
			ColArena::AddBox(GoldISM, Foot + FVector(0.f, 0.f, 70.f + ShaftH + 70.f), FVector(120.f, 120.f, 20.f), ColArena::YawQuat(PA + 45.f));
		}
	}

	// ------------------------------------------------------------------ central dais with a sloped skirt and the crystal pylon
	MakeMesh(TEXT("Dais"), Cylinder, DaisMID, EArenaCollision::BlockAll,
		FArenaKit::FitBox(Cylinder, FVector(0.f, 0.f, DaisHeight * 0.5f), FVector(DaisRadius * 2.f, DaisRadius * 2.f, DaisHeight)));
	{
		const float SkirtW = DaisOuterRadius() - DaisRadius;
		const float SlopeLen = FMath::Sqrt(SkirtW * SkirtW + DaisHeight * DaisHeight);
		const float Alpha = FMath::Atan2(DaisHeight, SkirtW);
		const float Thick = 40.f;
		const int32 NumSkirt = 36;
		const float SkirtChord = 2.f * DaisOuterRadius() * FMath::Sin(PI / NumSkirt) * 1.08f;
		for (int32 k = 0; k < NumSkirt; ++k)
		{
			const float A = (k + 0.5f) * 360.f / NumSkirt;
			const FVector Mid = ColArena::Polar(DaisRadius + SkirtW * 0.5f - Thick * 0.5f * FMath::Sin(Alpha), A, DaisHeight * 0.5f - Thick * 0.5f * FMath::Cos(Alpha));
			ColArena::AddBox(DaisISM, Mid, FVector(SlopeLen + 12.f, SkirtChord, Thick), FRotator(-FMath::RadiansToDegrees(Alpha), A, 0.f).Quaternion());
		}
	}
	const float PedestalH = 160.f;
	ColArena::AddBox(ColumnISM, FVector(0.f, 0.f, DaisHeight + PedestalH * 0.5f), FVector(260.f, 260.f, PedestalH));
	ColArena::AddBox(GlowBandISM, FVector(0.f, 0.f, DaisHeight + PedestalH + 3.f), FVector(236.f, 236.f, 6.f));
	for (int32 k = 0; k < 7; ++k)
	{
		const float A = k * (360.f / 7.f) + Rng.FRandRange(-12.f, 12.f);
		const float ShardH = Rng.FRandRange(70.f, 150.f);
		const FVector ShardAxis = (FVector::UpVector + ColArena::Polar(0.45f, A, 0.f)).GetSafeNormal();
		const FVector ShardFoot = ColArena::Polar(95.f, A, DaisHeight + PedestalH);
		ColArena::AddBox(ShardISM, ShardFoot + ShardAxis * (ShardH * 0.5f), FVector(34.f, 34.f, ShardH), FRotationMatrix::MakeFromZ(ShardAxis).ToQuat());
	}
	CrystalBaseLocation = FVector(0.f, 0.f, DaisHeight + PedestalH + 70.f + 180.f);
	UInstancedStaticMeshComponent* CrystalISM = MakeISM(TEXT("Crystal"), Cone, CrystalMID, EArenaCollision::None, true);
	CrystalISM->SetRelativeLocation(CrystalBaseLocation);
	ColArena::AddBox(CrystalISM, FVector(0.f, 0.f, -90.f), FVector(170.f, 170.f, 180.f), ColArena::RollQuat(180.f));
	ColArena::AddBox(CrystalISM, FVector(0.f, 0.f, 210.f), FVector(170.f, 170.f, 420.f));
	CrystalComp = CrystalISM;

	UInstancedStaticMeshComponent* RingA = MakeISM(TEXT("PylonRingA"), Cube, GoldMID, EArenaCollision::None, false);
	RingA->SetRelativeLocation(CrystalBaseLocation + FVector(0.f, 0.f, 120.f));
	for (int32 k = 0; k < 28; ++k)
	{
		const float A = k * (360.f / 28.f);
		ColArena::AddBox(RingA, ColArena::Polar(330.f, A, 0.f), FVector(24.f, 2.f * PI * 330.f / 28.f * 0.62f, 24.f), ColArena::YawQuat(A));
	}
	RingAComp = RingA;
	UInstancedStaticMeshComponent* RingB = MakeISM(TEXT("PylonRingB"), Cube, RuneMID, EArenaCollision::None, false);
	RingB->SetRelativeLocation(CrystalBaseLocation + FVector(0.f, 0.f, 40.f));
	for (int32 k = 0; k < 20; ++k)
	{
		const float A = k * 18.f;
		ColArena::AddBox(RingB, ColArena::Polar(250.f, A, 0.f), FVector(18.f, 2.f * PI * 250.f / 20.f * 0.55f, 18.f), ColArena::YawQuat(A));
	}
	RingBComp = RingB;
	UInstancedStaticMeshComponent* Moons = MakeISM(TEXT("PylonMoons"), Sphere, GoldMID, EArenaCollision::None, false);
	Moons->SetRelativeLocation(CrystalBaseLocation);
	for (int32 k = 0; k < 3; ++k)
	{
		ColArena::AddBox(Moons, ColArena::Polar(520.f, k * 120.f, -60.f + 60.f * k), FVector(56.f, 56.f, 56.f));
	}
	MoonsComp = Moons;
	PylonLight = MakeLight(CrystalBaseLocation + FVector(0.f, 0.f, 120.f), FLinearColor(0.35f, 0.85f, 1.f), PylonIntensity, 2600.f);

	// ------------------------------------------------------------------ stands + crowd
	for (int32 k = 0; k < StandTiers; ++k)
	{
		const float Ri = StandsInner + k * TierDepth;
		const float Ro = Ri + TierDepth;
		const float TopZ = TierTopZ(k);
		const float ChordO = 2.f * Ro * SinHalfStep * 1.02f;
		const float ChordI = 2.f * Ri * SinHalfStep * 1.02f;
		for (int32 i = 0; i < Segs; ++i)
		{
			const float A = (i + 0.5f) * Step;
			const FQuat Q = ColArena::YawQuat(A);
			ColArena::AddBox(StandISM, ColArena::Polar(Ri + TierDepth * 0.5f, A, TopZ * 0.5f), FVector(TierDepth, ChordO, TopZ), Q);
			ColArena::AddBox(StandISM, ColArena::Polar(Ri + TierDepth * 0.75f, A, TopZ + TierRise * 0.25f), FVector(TierDepth * 0.5f, ChordO, TierRise * 0.5f), Q);
			ColArena::AddBox(TerracottaISM, ColArena::Polar(Ri + 20.f, A, TopZ + 8.f), FVector(40.f, ChordI, 16.f), Q);
		}
		for (int32 Row = 0; Row < 2; ++Row)
		{
			const float RowR = Ri + TierDepth * (Row == 0 ? 0.27f : 0.74f);
			const float SeatZ = TopZ + (Row == 0 ? 0.f : TierRise * 0.5f);
			const int32 Seats = FMath::Max(8, FMath::FloorToInt(2.f * PI * RowR / CrowdSpacing));
			const float SeatStep = 360.f / Seats;
			const float Offset = Rng.FRand() * SeatStep;
			for (int32 s = 0; s < Seats; ++s)
			{
				if (Rng.FRand() > CrowdFill)
				{
					continue;
				}
				const float A = Offset + s * SeatStep + Rng.FRandRange(-0.2f, 0.2f) * SeatStep;
				const FVector Seat = ColArena::Polar(RowR + Rng.FRandRange(-18.f, 18.f), A, SeatZ);
				const int32 C = Rng.RandRange(0, ColArena::NumCrowdColors - 1);
				const float BodyH = Rng.FRandRange(80.f, 125.f);
				const float BodyW = Rng.FRandRange(52.f, 74.f);
				const float HeadD = Rng.FRand() < 0.1f ? Rng.FRandRange(72.f, 92.f) : Rng.FRandRange(42.f, 60.f);
				ColArena::AddBox(CrowdBodies[C], Seat + FVector(0.f, 0.f, BodyH * 0.5f), FVector(BodyW, BodyW, BodyH));
				ColArena::AddBox(CrowdHeads[C], Seat + FVector(0.f, 0.f, BodyH * 0.88f + HeadD * 0.4f), FVector(HeadD, HeadD, HeadD * 0.92f));
			}
		}
	}

	// Back wall with coping.
	const float BackChord = 2.f * (BackR + 150.f) * SinHalfStep * 1.02f;
	for (int32 i = 0; i < Segs; ++i)
	{
		const float A = (i + 0.5f) * Step;
		ColArena::AddBox(SandstoneISM, ColArena::Polar(BackR + 75.f, A, BackTop * 0.5f), FVector(150.f, BackChord, BackTop), ColArena::YawQuat(A));
		ColArena::AddBox(TerracottaISM, ColArena::Polar(BackR + 75.f, A, BackTop + 15.f), FVector(190.f, BackChord * 1.01f, 30.f), ColArena::YawQuat(A));
	}
	auto NearJumbo = [](float Deg) { return ColArena::AngleDiff(Deg, ColArena::JumboAngles[0]) < 16.f || ColArena::AngleDiff(Deg, ColArena::JumboAngles[1]) < 16.f; };

	// Pennant poles: pennants MUST be the first instances in each fabric ISM (they're animated by index).
	for (int32 i = 0; i < Segs; i += 2)
	{
		const float A = i * Step;
		if (NearJumbo(A))
		{
			continue;
		}
		const FVector PoleBase = ColArena::Polar(BackR + 75.f, A, BackTop + 30.f);
		ColArena::AddBox(MetalISM, PoleBase + FVector(0.f, 0.f, PoleH * 0.5f), FVector(20.f, 20.f, PoleH));
		ColArena::AddBox(SpireISM, PoleBase + FVector(0.f, 0.f, PoleH + 25.f), FVector(44.f, 44.f, 50.f));
		const int32 F = (i / 2) % ColArena::NumFabrics;
		const FQuat PQ = ColArena::YawQuat(A + 90.f);
		ColArena::AddBox(FabricISMs[F], PoleBase + FVector(0.f, 0.f, PoleH - 70.f) + PQ.GetForwardVector() * 130.f, FVector(240.f, 5.f, 100.f), PQ);
		++PennantCounts[F];
	}
	// Striped awnings sloping in over the top tiers.
	const float SailLen = TierDepth * 1.8f;
	const float SailW = 2.f * BackR * FMath::Sin(FMath::DegreesToRadians(Step)) * 0.8f;
	for (int32 i = 1; i < Segs; i += 2)
	{
		const float A = i * Step;
		if (NearJumbo(A))
		{
			continue;
		}
		const FQuat SQ = FRotator(-14.f, A + 180.f, 0.f).Quaternion();
		const FVector Anchor = ColArena::Polar(BackR + 60.f, A, BackTop + PoleH - 40.f);
		ColArena::AddBox(FabricISMs[((i - 1) / 2) % 2], Anchor + SQ.GetForwardVector() * (SailLen * 0.5f), FVector(SailLen, SailW, 6.f), SQ);
	}
	// Drapes hanging on the inner wall face between the gates.
	for (int32 q = 0; q < 4; ++q)
	{
		for (int32 Side = -1; Side <= 1; Side += 2)
		{
			const float A = 45.f + 90.f * q + Side * 11.25f;
			const FQuat Q = ColArena::YawQuat(A);
			ColArena::AddBox(FabricISMs[(q + (Side > 0 ? 1 : 0)) % ColArena::NumFabrics], ColArena::Polar(R - 20.f, A, WallHeight - 330.f), FVector(6.f, 260.f, 600.f), Q);
			ColArena::AddBox(GoldISM, ColArena::Polar(R - 25.f, A, WallHeight - 300.f), FVector(4.f, 90.f, 90.f), Q * ColArena::RollQuat(45.f));
			ColArena::AddBox(MetalISM, ColArena::Polar(R - 26.f, A, WallHeight - 25.f), FVector(14.f, 14.f, 300.f), Q * ColArena::RollQuat(90.f));
		}
	}

	// ------------------------------------------------------------------ jumbotrons with an announcer-droid face
	for (int32 j = 0; j < ColArena::NumJumbos; ++j)
	{
		const float A = ColArena::JumboAngles[j];
		const FQuat JQ = FRotator(-8.f, A + 180.f, 0.f).Quaternion();
		const float JW = 1900.f;
		const float JH = 1050.f;
		const FVector JC = ColArena::Polar(BackR + 90.f, A, BackTop + 320.f + JH * 0.5f);
		auto AddJ = [&JQ, &JC](UInstancedStaticMeshComponent* TargetISM, const FVector& LocalPos, const FVector& BoxSize)
		{
			ColArena::AddBox(TargetISM, JC + JQ.RotateVector(LocalPos), BoxSize, JQ);
		};
		AddJ(GlassISM, FVector::ZeroVector, FVector(90.f, JW, JH));
		AddJ(ScreenISM, FVector(47.f, 0.f, 0.f), FVector(4.f, JW - 120.f, JH - 120.f));
		AddJ(GoldISM, FVector(50.f, 0.f, JH * 0.5f - 40.f), FVector(6.f, JW - 60.f, 18.f));
		AddJ(GoldISM, FVector(50.f, 0.f, -JH * 0.5f + 40.f), FVector(6.f, JW - 60.f, 18.f));
		AddJ(GoldISM, FVector(50.f, JW * 0.5f - 40.f, 0.f), FVector(6.f, 18.f, JH - 60.f));
		AddJ(GoldISM, FVector(50.f, -JW * 0.5f + 40.f, 0.f), FVector(6.f, 18.f, JH - 60.f));
		for (int32 m = 0; m < 14; ++m)
		{
			AddJ(GoldISM, FVector(20.f, FMath::Lerp(-JW * 0.45f, JW * 0.45f, m / 13.f), JH * 0.5f + 35.f), FVector(34.f, 34.f, 34.f));
		}
		// Face instances (3 per screen: left eye, right eye, mouth) are animated in TickDecor.
		AddJ(FaceISM, FVector(51.f, -360.f, 140.f), FVector(4.f, 220.f, 220.f));
		AddJ(FaceISM, FVector(51.f, 360.f, 140.f), FVector(4.f, 220.f, 220.f));
		AddJ(FaceISM, FVector(51.f, 0.f, -250.f), FVector(4.f, 700.f, 90.f));
		for (int32 Side = -1; Side <= 1; Side += 2)
		{
			const FVector LegTop = JC + JQ.RotateVector(FVector(0.f, Side * JW * 0.33f, -JH * 0.5f + 40.f));
			const float LegLen = FMath::Max(static_cast<float>(LegTop.Z) - BackTop, 50.f);
			ColArena::AddBox(MetalISM, FVector(LegTop.X, LegTop.Y, BackTop + LegLen * 0.5f), FVector(50.f, 50.f, LegLen));
		}
	}

	// ------------------------------------------------------------------ braziers on the wall (warm point lights)
	for (int32 b = 0; b < ColArena::NumBraziers; ++b)
	{
		const float A = 22.5f + 45.f * b;
		const FQuat Q = ColArena::YawQuat(A);
		const FVector Bowl = ColArena::Polar(R - 95.f, A, ColArena::BrazierZ);
		ColArena::AddBox(MetalISM, ColArena::Polar(R - 48.f, A, ColArena::BrazierZ - 45.f), FVector(22.f, 22.f, 110.f), Q * FQuat(FVector::RightVector, PI * 0.5f));
		ColArena::AddBox(MetalISM, Bowl, FVector(140.f, 140.f, 45.f));
		ColArena::AddBox(GoldISM, Bowl - FVector(0.f, 0.f, 25.f), FVector(90.f, 90.f, 10.f), Q * ColArena::YawQuat(45.f));
		ColArena::AddBox(CoalISM, Bowl + FVector(0.f, 0.f, 18.f), FVector(118.f, 118.f, 44.f));
		ColArena::AddBox(FlameISM, Bowl + FVector(0.f, 0.f, 102.f), FVector(95.f, 95.f, 160.f));
		BrazierLights.Add(MakeLight(Bowl + Q.RotateVector(FVector(-70.f, 0.f, 130.f)), FLinearColor(1.f, 0.55f, 0.22f), BrazierIntensity, BrazierRadius));
	}

	// ------------------------------------------------------------------ sun-baked rocks ringing the Gobbler pit
	for (int32 k = 0; k < 18; ++k)
	{
		const float A = k * 20.f + Rng.FRandRange(-6.f, 6.f);
		const float Dist = PitRadius + 230.f + Rng.FRandRange(-30.f, 40.f);
		const FVector RockSize(Rng.FRandRange(50.f, 90.f), Rng.FRandRange(40.f, 70.f), Rng.FRandRange(18.f, 30.f));
		const FRotator RockRot(Rng.FRandRange(-8.f, 8.f), Rng.FRandRange(0.f, 360.f), Rng.FRandRange(-8.f, 8.f));
		ColArena::AddBox(TerracottaISM, PitL + ColArena::Polar(Dist, A, 10.f), RockSize, RockRot.Quaternion());
	}

	// ------------------------------------------------------------------ register everything (parents were created before children)
	for (UActorComponent* Comp : GeneratedComponents)
	{
		if (Comp && !Comp->IsRegistered())
		{
			Comp->RegisterComponent();
		}
	}
	BuiltHash = ComputeBuildHash();
}

// ============================================================================ runtime

void AColosseumArena::InitRuntime()
{
	for (int32 g = 0; g < 4; ++g)
	{
		GateState[g] = FGateRuntime();
	}
	for (int32 g = 0; g < GateDoors.Num(); ++g)
	{
		if (GateDoors[g])
		{
			GateDoors[g]->SetRelativeLocation(DoorClosedLocal(g));
		}
	}
	for (int32 g = 0; g < GateMIDs.Num() && g < 4; ++g)
	{
		if (GateMIDs[g])
		{
			GateMIDs[g]->SetVectorParameterValue(TEXT("Emissive"), ColArena::GateColors[g] * ColArena::GateGlowIdle);
		}
	}

	// Crowd members come straight from the ISM instances, so this also works on a level saved with a previous build.
	Crowd.Reset();
	Hops.Reset();
	CrowdBins.SetNum(ColArena::NumCrowdBins);
	for (TArray<int32>& Bin : CrowdBins)
	{
		Bin.Reset();
	}
	const int32 NumColors = FMath::Min(CrowdBodies.Num(), CrowdHeads.Num());
	for (int32 c = 0; c < NumColors; ++c)
	{
		UInstancedStaticMeshComponent* BodyISM = CrowdBodies[c];
		UInstancedStaticMeshComponent* HeadISM = CrowdHeads[c];
		if (!BodyISM || !HeadISM)
		{
			continue;
		}
		const int32 N = FMath::Min(BodyISM->GetInstanceCount(), HeadISM->GetInstanceCount());
		for (int32 i = 0; i < N; ++i)
		{
			FCrowdMember Member;
			Member.Color = static_cast<uint8>(c);
			Member.Index = i;
			BodyISM->GetInstanceTransform(i, Member.Body, false);
			HeadISM->GetInstanceTransform(i, Member.Head, false);
			const FVector L = Member.Body.GetLocation();
			float Deg = static_cast<float>(FMath::RadiansToDegrees(FMath::Atan2(L.Y, L.X)));
			if (Deg < 0.f)
			{
				Deg += 360.f;
			}
			const int32 BinIndex = FMath::Clamp(FMath::FloorToInt(Deg / ColArena::CrowdBinDegrees), 0, ColArena::NumCrowdBins - 1);
			CrowdBins[BinIndex].Add(Crowd.Add(Member));
		}
	}

	Pennants.Reset();
	for (int32 f = 0; f < FabricISMs.Num(); ++f)
	{
		UInstancedStaticMeshComponent* FabricISM = FabricISMs[f];
		if (!FabricISM)
		{
			continue;
		}
		const FVector Ext = FabricISM->GetStaticMesh() ? FabricISM->GetStaticMesh()->GetBounds().BoxExtent : FVector(50.0);
		const int32 Count = PennantCounts.IsValidIndex(f) ? FMath::Min(PennantCounts[f], FabricISM->GetInstanceCount()) : 0;
		for (int32 i = 0; i < Count; ++i)
		{
			FTransform Xf;
			FabricISM->GetInstanceTransform(i, Xf, false);
			FPennant& Pen = Pennants.AddDefaulted_GetRef();
			Pen.Fabric = f;
			Pen.Index = i;
			Pen.Rot = Xf.GetRotation();
			Pen.Scale = Xf.GetScale3D();
			Pen.Pivot = Xf.GetLocation() - Pen.Rot.GetForwardVector() * (Pen.Scale.X * Ext.X);
			Pen.Offset = Xf.GetLocation() - Pen.Pivot;
			Pen.Phase = FMath::FRandRange(0.f, 2.f * PI);
		}
	}

	FlameBase.Reset();
	if (FlameISM)
	{
		for (int32 i = 0; i < FlameISM->GetInstanceCount(); ++i)
		{
			FTransform Xf;
			FlameISM->GetInstanceTransform(i, Xf, false);
			FlameBase.Add(Xf);
		}
	}
	FaceBase.Reset();
	if (FaceISM)
	{
		for (int32 i = 0; i < FaceISM->GetInstanceCount(); ++i)
		{
			FTransform Xf;
			FaceISM->GetInstanceTransform(i, Xf, false);
			FaceBase.Add(Xf);
		}
	}

	const UWorld* World = GetWorld();
	NextBlink = (World ? World->GetTimeSeconds() : 0.f) + 2.f;
	BlinkUntil = 0.f;
	bRuntimeReady = true;
}

void AColosseumArena::SpawnProps()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	const FQuat ActorQ = GetActorQuat();
	auto FacingCentre = [&ActorQ](const FVector& FromLocal) -> FQuat
	{
		return ActorQ * ColArena::YawQuat(static_cast<float>(FMath::RadiansToDegrees(FMath::Atan2(-FromLocal.Y, -FromLocal.X))));
	};

	if (GobblerClass)
	{
		const FVector PitL = PitLocal();
		const FTransform Xf(FacingCentre(PitL), LocalToWorld(PitL));
		if (ASandGobbler* Gobbler = World->SpawnActorDeferred<ASandGobbler>(GobblerClass, Xf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
		{
			Gobbler->PitRadius = PitRadius;
			Gobbler->FinishSpawning(Xf);
			SpawnedProps.Add(Gobbler);
		}
	}

	if (BarrelClass)
	{
		FRandomStream Rng(Seed + 101);
		FActorSpawnParameters Params;
		Params.Owner = this;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector ClusterOffsets[3] = { FVector(0.f, 0.f, 0.f), FVector(85.f, 48.f, 0.f), FVector(85.f, -48.f, 0.f) };
		for (int32 c = 0; c < ColArena::NumBarrelClusters; ++c)
		{
			const FVector ClusterL = BarrelClusterLocal(c);
			const int32 Count = Rng.RandRange(2, 3);
			const FQuat ClusterQ = ColArena::YawQuat(Rng.FRandRange(0.f, 360.f));
			for (int32 b = 0; b < Count; ++b)
			{
				const FVector BarrelL = ClusterL + ClusterQ.RotateVector(ClusterOffsets[b]) + FVector(0.f, 0.f, AFizzBarrel::BarrelHalfHeight + 2.f);
				const FTransform Xf(ActorQ * ColArena::YawQuat(Rng.FRandRange(0.f, 360.f)), LocalToWorld(BarrelL));
				if (AFizzBarrel* Barrel = World->SpawnActor<AFizzBarrel>(BarrelClass, Xf, Params))
				{
					SpawnedProps.Add(Barrel);
				}
			}
		}
	}

	if (JumpPadClass)
	{
		for (int32 p = 0; p < ColArena::NumPads; ++p)
		{
			const FVector PadL = JumpPadLocal(p);
			const FTransform Xf(FacingCentre(PadL), LocalToWorld(PadL));
			if (AJumpPad* Pad = World->SpawnActorDeferred<AJumpPad>(JumpPadClass, Xf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
			{
				Pad->LaunchTarget = FVector(JumpPadThrowDistance, 0.f, 0.f);
				Pad->FinishSpawning(Xf);
				SpawnedProps.Add(Pad);
			}
		}
	}
}

void AColosseumArena::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bRuntimeReady)
	{
		return;
	}
	const float Now = GetWorld()->GetTimeSeconds();
	TickGates(DeltaSeconds, Now);
	TickCrowd(DeltaSeconds, Now);
	TickDecor(DeltaSeconds, Now);
}

void AColosseumArena::TickGates(float Dt, float Now)
{
	const float Lift = GateOpeningHeight() + 30.f;
	for (int32 g = 0; g < 4 && g < GateDoors.Num(); ++g)
	{
		FGateRuntime& State = GateState[g];
		if (State.Phase == 0)
		{
			continue;
		}
		const float Prev = State.Open;
		if (State.Phase == 1)
		{
			State.Open = FMath::Min(1.f, State.Open + Dt / FMath::Max(GateOpenTime, 0.05f));
			if (State.Open >= 1.f)
			{
				State.Phase = 2;
			}
		}
		else if (State.Phase == 2)
		{
			if (Now >= State.HoldUntil)
			{
				State.Phase = 3;
			}
		}
		else
		{
			State.Open = FMath::Max(0.f, State.Open - Dt / FMath::Max(GateCloseTime, 0.05f));
			if (State.Open <= 0.f)
			{
				State.Phase = 0;
				if (GateSound)
				{
					UGameplayStatics::PlaySoundAtLocation(this, GateSound, LocalToWorld(DoorClosedLocal(g)), 0.3f, 0.6f);
				}
			}
		}
		if (State.Open != Prev)
		{
			const float Eased = FMath::SmoothStep(0.f, 1.f, State.Open);
			if (GateDoors[g])
			{
				GateDoors[g]->SetRelativeLocation(DoorClosedLocal(g) + FVector(0.f, 0.f, Eased * Lift));
			}
			if (GateMIDs.IsValidIndex(g) && GateMIDs[g])
			{
				GateMIDs[g]->SetVectorParameterValue(TEXT("Emissive"), ColArena::GateColors[g] * FMath::Lerp(ColArena::GateGlowIdle, ColArena::GateGlowOpen, Eased));
			}
		}
	}
}

void AColosseumArena::StartHop(int32 Member, float Now, float Height, float Duration)
{
	if (!Crowd.IsValidIndex(Member) || Crowd[Member].bHopping)
	{
		return;
	}
	Crowd[Member].bHopping = true;
	FCrowdHop& Hop = Hops.AddDefaulted_GetRef();
	Hop.Member = Member;
	Hop.Start = Now;
	Hop.Duration = FMath::Max(Duration, 0.1f);
	Hop.Height = Height;
}

void AColosseumArena::TickCrowd(float Dt, float Now)
{
	const int32 NumMembers = Crowd.Num();
	if (NumMembers == 0)
	{
		return;
	}
	CrowdHypeSmoothed = FMath::FInterpTo(CrowdHypeSmoothed, CrowdHypeTarget, Dt, 1.5f);
	const float Hype = FMath::Clamp(CrowdHypeSmoothed, 0.f, 1.f);

	// Random hoppers: a trickle when bored, a sea of bouncing heads when the Jedi is on a roll.
	HopAccumulator = FMath::Min(HopAccumulator + Dt * FMath::Lerp(IdleHopsPerSecond, MaxHopsPerSecond, Hype * Hype), 64.f);
	while (HopAccumulator >= 1.f)
	{
		HopAccumulator -= 1.f;
		if (Hops.Num() >= MaxCrowdHops)
		{
			HopAccumulator = 0.f;
			break;
		}
		StartHop(FMath::RandRange(0, NumMembers - 1), Now, FMath::Lerp(14.f, 55.f, Hype) * FMath::FRandRange(0.7f, 1.3f), FMath::Lerp(0.55f, 0.38f, Hype));
	}

	// Cheer bursts (CrowdCheer).
	if (PendingCheerHops >= 1.f)
	{
		const int32 Burst = FMath::Min(FMath::FloorToInt(PendingCheerHops), 90);
		PendingCheerHops -= Burst;
		for (int32 n = 0; n < Burst; ++n)
		{
			StartHop(FMath::RandRange(0, NumMembers - 1), Now + FMath::FRandRange(0.f, 0.15f), FMath::FRandRange(55.f, 90.f), 0.5f);
		}
	}

	// Stadium wave around the bowl when hype is high.
	if (CrowdBins.Num() == ColArena::NumCrowdBins && (Hype >= WaveHypeThreshold || (bWaveRunning && Hype >= WaveHypeThreshold - 0.1f)))
	{
		if (!bWaveRunning)
		{
			bWaveRunning = true;
			WaveAngle = FMath::FRandRange(0.f, 360.f);
		}
		const float PrevAngle = WaveAngle;
		WaveAngle += Dt * WaveSpeed;
		const int32 FirstBin = FMath::FloorToInt(PrevAngle / ColArena::CrowdBinDegrees) + 1;
		const int32 LastBin = FMath::FloorToInt(WaveAngle / ColArena::CrowdBinDegrees);
		for (int32 b = FirstBin; b <= LastBin && b - FirstBin < ColArena::NumCrowdBins; ++b)
		{
			for (const int32 M : CrowdBins[((b % ColArena::NumCrowdBins) + ColArena::NumCrowdBins) % ColArena::NumCrowdBins])
			{
				StartHop(M, Now, FMath::FRandRange(70.f, 95.f), 0.65f);
			}
		}
		if (WaveAngle > 3600.f)
		{
			WaveAngle -= 3600.f;
		}
	}
	else
	{
		bWaveRunning = false;
	}

	// Animate hops (instance updates flush incrementally; no render-state rebuild needed).
	for (int32 h = Hops.Num() - 1; h >= 0; --h)
	{
		const FCrowdHop& Hop = Hops[h];
		FCrowdMember& Member = Crowd[Hop.Member];
		UInstancedStaticMeshComponent* BodyISM = CrowdBodies.IsValidIndex(Member.Color) ? CrowdBodies[Member.Color].Get() : nullptr;
		UInstancedStaticMeshComponent* HeadISM = CrowdHeads.IsValidIndex(Member.Color) ? CrowdHeads[Member.Color].Get() : nullptr;
		const float Tn = (Now - Hop.Start) / Hop.Duration;
		if (Tn < 0.f)
		{
			continue;
		}
		if (Tn >= 1.f || !BodyISM || !HeadISM)
		{
			if (BodyISM)
			{
				BodyISM->UpdateInstanceTransform(Member.Index, Member.Body, false, false, false);
			}
			if (HeadISM)
			{
				HeadISM->UpdateInstanceTransform(Member.Index, Member.Head, false, false, false);
			}
			Member.bHopping = false;
			Hops.RemoveAtSwap(h, EAllowShrinking::No);
			continue;
		}
		const float Arc = 4.f * Tn * (1.f - Tn);
		const float Lift = Hop.Height * Arc;
		const float Stretch = 1.f + 0.18f * Arc;
		const float Squeeze = 1.f - 0.08f * Arc;
		const FVector BodyScale = Member.Body.GetScale3D();
		// Sphere mesh is 100 cm across: the body grows by this much when stretched.
		const float Grow = (Stretch - 1.f) * static_cast<float>(BodyScale.Z) * 100.f;
		FTransform BodyXf = Member.Body;
		BodyXf.SetScale3D(FVector(BodyScale.X * Squeeze, BodyScale.Y * Squeeze, BodyScale.Z * Stretch));
		BodyXf.AddToTranslation(FVector(0.f, 0.f, Lift + Grow * 0.5f));
		FTransform HeadXf = Member.Head;
		HeadXf.AddToTranslation(FVector(0.f, 0.f, Lift + Grow));
		BodyISM->UpdateInstanceTransform(Member.Index, BodyXf, false, false, false);
		HeadISM->UpdateInstanceTransform(Member.Index, HeadXf, false, false, false);
	}
}

void AColosseumArena::TickDecor(float Dt, float Now)
{
	const float Hype = FMath::Clamp(CrowdHypeSmoothed, 0.f, 1.f);

	// Crystal pylon: bobbing crystal, two tilted counter-rotating rings, orbiting moons. Spins faster with hype.
	PylonSpin = FMath::Fmod(PylonSpin + Dt * (16.f + 50.f * Hype), 36000.f);
	if (CrystalComp)
	{
		CrystalComp->SetRelativeLocationAndRotation(CrystalBaseLocation + FVector(0.f, 0.f, FMath::Sin(Now * 1.1f) * 22.f), FRotator(0.f, PylonSpin, 0.f));
	}
	if (RingAComp)
	{
		RingAComp->SetRelativeRotation(FQuat(FVector::ForwardVector, FMath::DegreesToRadians(16.f)) * ColArena::YawQuat(PylonSpin * 2.5f));
	}
	if (RingBComp)
	{
		RingBComp->SetRelativeRotation(FQuat(FVector::RightVector, FMath::DegreesToRadians(-24.f)) * ColArena::YawQuat(-PylonSpin * 3.5f));
	}
	if (MoonsComp)
	{
		MoonsComp->SetRelativeRotation(ColArena::YawQuat(PylonSpin * 1.2f));
	}
	if (PylonLight)
	{
		PylonLight->SetIntensity(PylonIntensity * (0.8f + 1.4f * Hype + 0.15f * FMath::Sin(Now * 3.f)));
	}

	// Pennants swing about their poles.
	for (const FPennant& Pen : Pennants)
	{
		UInstancedStaticMeshComponent* FabricISM = FabricISMs.IsValidIndex(Pen.Fabric) ? FabricISMs[Pen.Fabric].Get() : nullptr;
		if (!FabricISM)
		{
			continue;
		}
		const float Swing = FMath::DegreesToRadians(FMath::Sin(Now * 2.1f + Pen.Phase) * (8.f + 18.f * Hype));
		const float Flutter = FMath::DegreesToRadians(FMath::Sin(Now * 6.7f + Pen.Phase * 1.7f) * 9.f);
		const FQuat SwingQ(FVector::UpVector, Swing);
		const FQuat FlutterQ(Pen.Rot.GetForwardVector(), Flutter);
		FabricISM->UpdateInstanceTransform(Pen.Index, FTransform(SwingQ * FlutterQ * Pen.Rot, Pen.Pivot + SwingQ.RotateVector(Pen.Offset), Pen.Scale), false, false, false);
	}

	// Brazier flames flicker (bottom stays planted in the coals) and the lights flicker with them.
	if (FlameISM && FlameBase.Num() > 0)
	{
		const UStaticMesh* FlameMesh = FlameISM->GetStaticMesh();
		const FBoxSphereBounds FB = FlameMesh ? FlameMesh->GetBounds() : FBoxSphereBounds(FVector::ZeroVector, FVector(50.0), 50.0);
		const float BottomLocal = static_cast<float>(FB.Origin.Z - FB.BoxExtent.Z);
		for (int32 f = 0; f < FlameBase.Num(); ++f)
		{
			const FTransform& Base = FlameBase[f];
			const float Flick = FMath::Sin(Now * 13.f + f * 1.7f) * 0.5f + FMath::Sin(Now * 23.f + f * 3.1f) * 0.3f;
			const FVector S0 = Base.GetScale3D();
			const FVector S1(S0.X * (1.f + 0.06f * Flick), S0.Y * (1.f - 0.06f * Flick), S0.Z * (1.f + 0.22f * Flick + 0.1f * Hype));
			FTransform Xf = Base;
			Xf.SetScale3D(S1);
			Xf.AddToTranslation(FVector(0.f, 0.f, (S0.Z - S1.Z) * BottomLocal));
			FlameISM->UpdateInstanceTransform(f, Xf, false, false, false);
			if (BrazierLights.IsValidIndex(f) && BrazierLights[f])
			{
				BrazierLights[f]->SetIntensity(BrazierIntensity * (0.85f + 0.15f * Flick + 0.3f * Hype));
			}
		}
	}

	// Jumbotron announcer face: blinks, and the mouth "talks" when the crowd is loud.
	if (FaceISM && FaceBase.Num() > 0)
	{
		if (Now >= NextBlink)
		{
			BlinkUntil = Now + 0.14f;
			NextBlink = Now + FMath::FRandRange(2.5f, 5.5f);
		}
		const bool bBlink = Now < BlinkUntil;
		for (int32 i = 0; i < FaceBase.Num(); ++i)
		{
			FTransform Xf = FaceBase[i];
			FVector S = Xf.GetScale3D();
			if (i % 3 == 2)
			{
				S.Z *= 1.f + Hype * 1.4f * FMath::Abs(FMath::Sin(Now * 11.f + i));
			}
			else if (bBlink)
			{
				S.Z *= 0.08f;
			}
			else
			{
				S.Y *= 1.f + 0.12f * Hype;
				S.Z *= 1.f + 0.12f * Hype;
			}
			Xf.SetScale3D(S);
			FaceISM->UpdateInstanceTransform(i, Xf, false, false, false);
		}
	}
	if (ScreenMID)
	{
		ScreenMID->SetVectorParameterValue(TEXT("Emissive"), ColArena::ScreenEmissive * (1.f + 1.5f * Hype + 0.25f * FMath::Sin(Now * 2.4f)));
	}
}

// ============================================================================ director API

int32 AColosseumArena::NumGates() const
{
	return 4;
}

FTransform AColosseumArena::GetGateSpawnTransform(int32 Gate) const
{
	const float GA = GateAngle(Gate);
	const FVector Local = ColArena::Polar(ArenaRadius - GateSpawnInset, GA, 0.f);
	return FTransform(GetActorQuat() * ColArena::YawQuat(GA + 180.f), LocalToWorld(Local));
}

void AColosseumArena::OpenGate(int32 Gate, float HoldOpenSeconds)
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	const int32 G = ((Gate % 4) + 4) % 4;
	const float Now = World->GetTimeSeconds();
	FGateRuntime& State = GateState[G];
	const float TimeToOpen = (1.f - State.Open) * GateOpenTime;
	State.HoldUntil = FMath::Max(State.HoldUntil, Now + TimeToOpen + FMath::Max(HoldOpenSeconds, 0.f));
	if (State.Phase == 0 || State.Phase == 3)
	{
		if (State.Phase == 0)
		{
			if (GateSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, GateSound, LocalToWorld(DoorClosedLocal(G)), 0.35f, 0.4f);
			}
			CrowdCheer(0.15f);
		}
		State.Phase = 1;
	}
}

FVector AColosseumArena::GetRandomDropSite() const
{
	const float MinR = DaisOuterRadius() + 350.f;
	const float MaxR = FMath::Max(MinR + 200.f, ArenaRadius - 700.f);
	for (int32 Try = 0; Try < 40; ++Try)
	{
		const float Dist = FMath::Sqrt(FMath::FRandRange(MinR * MinR, MaxR * MaxR));
		const FVector L = ColArena::Polar(Dist, FMath::FRandRange(0.f, 360.f), 0.f);
		if (IsFloorSpotBlocked(L, 180.f))
		{
			continue;
		}
		const FVector W = LocalToWorld(L);
		bool bNearProp = false;
		for (const TObjectPtr<AActor>& Prop : SpawnedProps)
		{
			if (IsValid(Prop.Get()) && FVector::DistSquared2D(Prop->GetActorLocation(), W) < FMath::Square(260.f))
			{
				bNearProp = true;
				break;
			}
		}
		if (!bNearProp)
		{
			return W;
		}
	}
	// Fallback: halfway down the north lane (always clear).
	return LocalToWorld(ColArena::Polar((MinR + MaxR) * 0.5f, 0.f, 0.f));
}

void AColosseumArena::SetCrowdHype(float Hype01)
{
	CrowdHypeTarget = FMath::Clamp(Hype01, 0.f, 1.f);
}

void AColosseumArena::CrowdCheer(float Strength01)
{
	PendingCheerHops = FMath::Min(PendingCheerHops + FMath::Clamp(Strength01, 0.f, 1.f) * Crowd.Num() * 0.3f, 1500.f);
}

bool AColosseumArena::IsGateOpen(int32 Gate) const
{
	return GateState[((Gate % 4) + 4) % 4].Open > 0.85f;
}

FVector AColosseumArena::GetArenaCenter() const
{
	return GetActorLocation();
}

float AColosseumArena::GetArenaRadius() const
{
	return ArenaRadius;
}

float AColosseumArena::GetFloorZ() const
{
	return static_cast<float>(GetActorLocation().Z);
}

bool AColosseumArena::IsInsideArena(const FVector& P, float Margin) const
{
	return FVector::DistSquared2D(P, GetActorLocation()) <= FMath::Square(FMath::Max(ArenaRadius - Margin, 0.f));
}

FVector AColosseumArena::GetPlayerStartLocation() const
{
	return LocalToWorld(FVector(-DaisRadius * 0.6f, 0.f, DaisHeight + 100.f));
}

FRotator AColosseumArena::GetPlayerStartRotation() const
{
	return FRotator(0.f, GetActorRotation().Yaw, 0.f);
}

bool AColosseumArena::GetPitInfo(FVector& OutCenter, float& OutRadius) const
{
	OutCenter = LocalToWorld(PitLocal());
	OutRadius = PitRadius;
	return bSpawnProps && GobblerClass.Get() != nullptr;
}

// ============================================================================ layout queries

int32 AColosseumArena::SegmentCount() const
{
	return FMath::Max(16, (WallSegments / 4) * 4);
}

float AColosseumArena::GateAngle(int32 Gate) const
{
	return 90.f * (((Gate % 4) + 4) % 4);
}

float AColosseumArena::GateGapHalfAngle() const
{
	const float StepDeg = 360.f / SegmentCount();
	const float Need = FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp((GateWidth * 0.5f + 150.f) / FMath::Max(ArenaRadius, 1.f), 0.f, 0.95f)));
	return FMath::Max(1, FMath::CeilToInt(Need / StepDeg - 0.001f)) * StepDeg;
}

float AColosseumArena::GateOpeningHeight() const
{
	return FMath::Max(150.f, FMath::Min(GateHeight, WallHeight - 150.f));
}

FVector AColosseumArena::DoorClosedLocal(int32 Gate) const
{
	return ColArena::YawQuat(GateAngle(Gate)).RotateVector(FVector(ArenaRadius + 45.f, 0.f, GateOpeningHeight() * 0.5f));
}

FVector AColosseumArena::PitLocal() const
{
	return ColArena::Polar(ArenaRadius * PitDistance, PitAngle, 0.f);
}

FVector AColosseumArena::PillarLocal(int32 Index) const
{
	return ColArena::Polar(ArenaRadius * PillarRing, ColArena::PillarAngles[((Index % ColArena::NumPillars) + ColArena::NumPillars) % ColArena::NumPillars], 0.f);
}

FVector AColosseumArena::JumpPadLocal(int32 Index) const
{
	return ColArena::Polar(ArenaRadius - JumpPadInset, ColArena::PadAngles[((Index % ColArena::NumPads) + ColArena::NumPads) % ColArena::NumPads], 0.f);
}

FVector AColosseumArena::BarrelClusterLocal(int32 Index) const
{
	return ColArena::Polar(ArenaRadius * BarrelRing, ColArena::BarrelAngles[((Index % ColArena::NumBarrelClusters) + ColArena::NumBarrelClusters) % ColArena::NumBarrelClusters], 0.f);
}

float AColosseumArena::DaisOuterRadius() const
{
	return DaisRadius + FMath::Max(DaisHeight * 3.2f, 120.f);
}

float AColosseumArena::TierTopZ(int32 Tier) const
{
	return WallHeight + 60.f + Tier * TierRise;
}

bool AColosseumArena::IsFloorSpotBlocked(const FVector& Local, float Pad) const
{
	const FVector2D P2(Local.X, Local.Y);
	if (P2.Size() < DaisOuterRadius() + Pad)
	{
		return true;
	}
	if (FVector2D::Distance(P2, FVector2D(PitLocal())) < PitRadius + 250.f + Pad)
	{
		return true;
	}
	for (int32 i = 0; i < ColArena::NumPillars; ++i)
	{
		if (FVector2D::Distance(P2, FVector2D(PillarLocal(i))) < ColArena::PillarClearance + Pad)
		{
			return true;
		}
	}
	for (int32 i = 0; i < ColArena::NumPads; ++i)
	{
		if (FVector2D::Distance(P2, FVector2D(JumpPadLocal(i))) < 180.f + Pad)
		{
			return true;
		}
	}
	return false;
}

FVector AColosseumArena::LocalToWorld(const FVector& Local) const
{
	return GetActorTransform().TransformPosition(Local);
}
