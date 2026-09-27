#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ColosseumArena.generated.h"

class UActorComponent;
class UBoxComponent;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UPointLightComponent;
class UPrimitiveComponent;
class USceneComponent;
class USoundBase;
class UStaticMesh;
class UStaticMeshComponent;
class AFizzBarrel;
class AJumpPad;
class ASandGobbler;

/** Small toolkit shared by the arena and its props (Gobbler, Fizz Barrels, Jump Pads). */
struct JEDIARENA_API FArenaKit
{
	/**
	 * Transform that makes Mesh's bounding box exactly fill a box of Size (cm), centred at Center, rotated by Rot.
	 * Pivot-agnostic, so it works for engine shapes and LevelPrototyping meshes alike.
	 */
	static FTransform FitBox(const UStaticMesh* Mesh, const FVector& Center, const FVector& Size, const FQuat& Rot = FQuat::Identity);

	/**
	 * Runtime-only MID of Parent (M_ArenaSurface: BaseColor / Emissive / Roughness / Metallic), cached per colour so
	 * every prop with the same colour shares one. Outer is the transient package: only use it on actors spawned at runtime.
	 */
	static UMaterialInstanceDynamic* SharedSurfaceMID(UMaterialInterface* Parent, const FLinearColor& Base, const FLinearColor& Emissive = FLinearColor::Black, float Roughness = 0.6f, float Metallic = 0.f);

	/** Writes the M_ArenaSurface parameters into a MID. */
	static void SetSurfaceParams(UMaterialInstanceDynamic* MID, const FLinearColor& Base, const FLinearColor& Emissive, float Roughness, float Metallic);

	/** Visual-only primitive: no collision, no overlaps, no navigation. */
	static void NoCollision(UPrimitiveComponent* Prim);
};

/** How a generated arena component collides. */
enum class EArenaCollision : uint8
{
	None,
	BlockAll,
	/** Invisible: blocks pawns and physics bodies only (keeps everyone inside the bowl). */
	PawnBarrier
};

/**
 * "The Duneglass Colosseum": builds the whole arena procedurally in OnConstruction (so it previews in the editor):
 * sunken sand floor with glassy ring inlays and glowing runes, a segmented ring wall with four portcullis gates,
 * tiered stands packed with a bouncing alien crowd, pennants, awnings, two announcer jumbotrons, braziers,
 * a raised central dais with a spinning crystal pylon and six cover columns. At BeginPlay it spawns the
 * Sand Gobbler, Fizz Barrel clusters and Jump Pads.
 *
 * Local frame: floor top at the actor's Z; gate 0 = North (+X), 1 = East (+Y), 2 = South (-X), 3 = West (-Y).
 * Place it unrotated and unscaled (the query API assumes scale 1).
 */
UCLASS()
class JEDIARENA_API AColosseumArena : public AActor
{
	GENERATED_BODY()

public:
	AColosseumArena();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;

	// ------------------------------------------------------------------ Horde director API

	/** Always 4 (N, E, S, W). */
	UFUNCTION(BlueprintPure, Category = "Arena")
	int32 NumGates() const;

	/**
	 * Floor-level point GateSpawnInset cm inside the gate, rotation (yaw only) facing the arena centre.
	 * No jitter is applied: callers add their own spread (use the rotation's right vector) and the capsule half-height.
	 * Out-of-range indices wrap.
	 */
	UFUNCTION(BlueprintPure, Category = "Arena")
	FTransform GetGateSpawnTransform(int32 Gate) const;

	/** Raises the gate's portcullis, keeps it up for HoldOpenSeconds, then lowers it. Re-calling extends the hold. */
	UFUNCTION(BlueprintCallable, Category = "Arena")
	void OpenGate(int32 Gate, float HoldOpenSeconds);

	/** Random open floor point (floor Z) for drop pods: not on the dais, pillars, pads, barrels or in the pit, and away from the wall. */
	UFUNCTION(BlueprintCallable, Category = "Arena")
	FVector GetRandomDropSite() const;

	/** 0..1. The crowd hops more (and starts a stadium wave) as hype rises. Cheap to call every frame. */
	UFUNCTION(BlueprintCallable, Category = "Arena")
	void SetCrowdHype(float Hype01);

	/** Floor-level centre of the arena. */
	UFUNCTION(BlueprintPure, Category = "Arena")
	FVector GetArenaCenter() const;

	UFUNCTION(BlueprintPure, Category = "Arena")
	float GetArenaRadius() const;

	/** 2D test: within ArenaRadius - Margin of the centre. */
	UFUNCTION(BlueprintPure, Category = "Arena")
	bool IsInsideArena(const FVector& P, float Margin) const;

	/** A spot on the dais (south side, facing north). Z is capsule-centre height (dais top + 100 cm). */
	UFUNCTION(BlueprintPure, Category = "Arena")
	FVector GetPlayerStartLocation() const;

	/** The Gobbler pit (floor-level centre, mouth radius). False when props are disabled. */
	UFUNCTION(BlueprintPure, Category = "Arena")
	bool GetPitInfo(FVector& OutCenter, float& OutRadius) const;

	// ------------------------------------------------------------------ extras

	/** Burst of excited hopping; Strength01 = share of the crowd (0..1) that jumps up. */
	UFUNCTION(BlueprintCallable, Category = "Arena")
	void CrowdCheer(float Strength01 = 1.f);

	UFUNCTION(BlueprintPure, Category = "Arena")
	bool IsGateOpen(int32 Gate) const;

	/** Rotation for GetPlayerStartLocation (facing the north gate). */
	UFUNCTION(BlueprintPure, Category = "Arena")
	FRotator GetPlayerStartRotation() const;

	UFUNCTION(BlueprintPure, Category = "Arena")
	float GetFloorZ() const;

	/** Throws away and rebuilds all generated geometry. */
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "Arena")
	void RebuildArena();

	// ------------------------------------------------------------------ layout

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "1500"))
	float ArenaRadius = 4200.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "300"))
	float WallHeight = 1100.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "100"))
	float WallThickness = 300.f;

	/** Wall blocks around the ring (rounded down to a multiple of 4 so the gates line up). */
	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "16", ClampMax = "128"))
	int32 WallSegments = 48;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "200"))
	float GateWidth = 700.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "200"))
	float GateHeight = 800.f;

	/** How far inside the wall GetGateSpawnTransform places arrivals. */
	UPROPERTY(EditAnywhere, Category = "Arena|Layout")
	float GateSpawnInset = 350.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "1", ClampMax = "5"))
	int32 StandTiers = 4;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "200"))
	float TierDepth = 450.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "100"))
	float TierRise = 320.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "200"))
	float DaisRadius = 650.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "10", ClampMax = "140"))
	float DaisHeight = 60.f;

	/** Cover columns stand on this fraction of ArenaRadius. */
	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "0.3", ClampMax = "0.85"))
	float PillarRing = 0.63f;

	/** Gobbler mouth radius. */
	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "150"))
	float PitRadius = 420.f;

	/** Pit centre distance from the arena centre as a fraction of ArenaRadius. */
	UPROPERTY(EditAnywhere, Category = "Arena|Layout", meta = (ClampMin = "0.3", ClampMax = "0.8"))
	float PitDistance = 0.55f;

	/** Degrees, 0 = north gate direction (+X). Default sits between the East and South gates. */
	UPROPERTY(EditAnywhere, Category = "Arena|Layout")
	float PitAngle = 135.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Layout")
	int32 Seed = 1977;

	// ------------------------------------------------------------------ crowd

	/** Seat spacing along each row (cm). Smaller = bigger crowd. */
	UPROPERTY(EditAnywhere, Category = "Arena|Crowd", meta = (ClampMin = "80"))
	float CrowdSpacing = 125.f;

	/** Share of seats that are occupied. */
	UPROPERTY(EditAnywhere, Category = "Arena|Crowd", meta = (ClampMin = "0", ClampMax = "1"))
	float CrowdFill = 0.88f;

	/** Cap on simultaneously hopping spectators (random hops; the stadium wave may briefly exceed it). */
	UPROPERTY(EditAnywhere, Category = "Arena|Crowd")
	int32 MaxCrowdHops = 600;

	UPROPERTY(EditAnywhere, Category = "Arena|Crowd")
	float IdleHopsPerSecond = 25.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Crowd")
	float MaxHopsPerSecond = 900.f;

	/** Above this hype the crowd runs a stadium wave around the bowl. */
	UPROPERTY(EditAnywhere, Category = "Arena|Crowd", meta = (ClampMin = "0", ClampMax = "1"))
	float WaveHypeThreshold = 0.55f;

	/** Degrees per second. */
	UPROPERTY(EditAnywhere, Category = "Arena|Crowd")
	float WaveSpeed = 80.f;

	// ------------------------------------------------------------------ lighting

	/** Brazier point lights, candelas. */
	UPROPERTY(EditAnywhere, Category = "Arena|Lighting")
	float BrazierIntensity = 300.f;

	UPROPERTY(EditAnywhere, Category = "Arena|Lighting")
	float BrazierRadius = 2400.f;

	/** Crystal pylon light, candelas (scales up with hype). */
	UPROPERTY(EditAnywhere, Category = "Arena|Lighting")
	float PylonIntensity = 400.f;

	// ------------------------------------------------------------------ gates

	UPROPERTY(EditAnywhere, Category = "Arena|Gates")
	float GateOpenTime = 0.9f;

	UPROPERTY(EditAnywhere, Category = "Arena|Gates")
	float GateCloseTime = 1.4f;

	/** Rumble when a portcullis starts moving (played pitched way down). */
	UPROPERTY(EditAnywhere, Category = "Arena|Gates")
	TObjectPtr<USoundBase> GateSound;

	// ------------------------------------------------------------------ props (spawned at BeginPlay)

	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	bool bSpawnProps = true;

	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	TSubclassOf<ASandGobbler> GobblerClass;

	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	TSubclassOf<AFizzBarrel> BarrelClass;

	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	TSubclassOf<AJumpPad> JumpPadClass;

	/** Barrel clusters sit on this fraction of ArenaRadius. */
	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	float BarrelRing = 0.47f;

	/** Jump pads sit this far inside the wall, between the gates. */
	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	float JumpPadInset = 520.f;

	/** How far toward the centre the pads throw you (cm). */
	UPROPERTY(EditAnywhere, Category = "Arena|Props")
	float JumpPadThrowDistance = 2500.f;

	// ------------------------------------------------------------------ assets

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UMaterialInterface> SurfaceMaterial;

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UMaterialInterface> MetalMaterial;

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UMaterialInterface> LavaMaterial;

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UStaticMesh> CubeMesh;

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UStaticMesh> SphereMesh;

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UStaticMesh> CylinderMesh;

	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UStaticMesh> ConeMesh;

	/** Falls back to CubeMesh when missing. */
	UPROPERTY(EditAnywhere, Category = "Arena|Assets")
	TObjectPtr<UStaticMesh> ChamferCubeMesh;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<USceneComponent> ArenaRoot;

private:
	// ---- building
	void BuildArena();
	void ClearGenerated();
	bool IsBuildValid() const;
	uint32 ComputeBuildHash() const;
	UInstancedStaticMeshComponent* MakeISM(const TCHAR* BaseName, UStaticMesh* Mesh, UMaterialInterface* Material, EArenaCollision Collision, bool bShadows, USceneComponent* Parent = nullptr);
	UStaticMeshComponent* MakeMesh(const TCHAR* BaseName, UStaticMesh* Mesh, UMaterialInterface* Material, EArenaCollision Collision, const FTransform& RelativeXf);
	UPointLightComponent* MakeLight(const FVector& RelativeLocation, const FLinearColor& Color, float Candelas, float Radius);
	UMaterialInstanceDynamic* MakeMID(const FLinearColor& Base, const FLinearColor& Emissive, float Roughness, float Metallic);
	void ApplyCollision(UPrimitiveComponent* Prim, EArenaCollision Collision) const;
	void FinishComponent(UActorComponent* Comp);

	// ---- runtime
	void InitRuntime();
	void SpawnProps();
	void TickGates(float Dt, float Now);
	void TickCrowd(float Dt, float Now);
	void TickDecor(float Dt, float Now);
	void StartHop(int32 Member, float Now, float Height, float Duration);

	// ---- layout queries (actor-local space, floor at Z = 0)
	int32 SegmentCount() const;
	float GateAngle(int32 Gate) const;
	float GateGapHalfAngle() const;
	/** Portcullis opening height (kept below the wall top). */
	float GateOpeningHeight() const;
	FVector DoorClosedLocal(int32 Gate) const;
	FVector PitLocal() const;
	FVector PillarLocal(int32 Index) const;
	FVector JumpPadLocal(int32 Index) const;
	FVector BarrelClusterLocal(int32 Index) const;
	float DaisOuterRadius() const;
	float TierTopZ(int32 Tier) const;
	/** True when a floor point (local) is too close to the pit, a pillar, a pad or the dais. */
	bool IsFloorSpotBlocked(const FVector& Local, float Pad) const;
	FVector LocalToWorld(const FVector& Local) const;

	// ---- generated components (serialized so they survive save / PIE duplication)
	UPROPERTY()
	TArray<TObjectPtr<UActorComponent>> GeneratedComponents;

	UPROPERTY()
	TArray<TObjectPtr<UMaterialInstanceDynamic>> GeneratedMIDs;

	UPROPERTY()
	TArray<TObjectPtr<UInstancedStaticMeshComponent>> CrowdBodies;

	UPROPERTY()
	TArray<TObjectPtr<UInstancedStaticMeshComponent>> CrowdHeads;

	UPROPERTY()
	TArray<TObjectPtr<USceneComponent>> GateDoors;

	UPROPERTY()
	TArray<TObjectPtr<UMaterialInstanceDynamic>> GateMIDs;

	UPROPERTY()
	TArray<TObjectPtr<UInstancedStaticMeshComponent>> FabricISMs;

	/** Leading instances of each fabric ISM that are waving pennants. */
	UPROPERTY()
	TArray<int32> PennantCounts;

	UPROPERTY()
	TObjectPtr<UInstancedStaticMeshComponent> FlameISM;

	UPROPERTY()
	TObjectPtr<UInstancedStaticMeshComponent> FaceISM;

	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> ScreenMID;

	UPROPERTY()
	TObjectPtr<USceneComponent> CrystalComp;

	UPROPERTY()
	TObjectPtr<USceneComponent> RingAComp;

	UPROPERTY()
	TObjectPtr<USceneComponent> RingBComp;

	UPROPERTY()
	TObjectPtr<USceneComponent> MoonsComp;

	UPROPERTY()
	TObjectPtr<UPointLightComponent> PylonLight;

	UPROPERTY()
	TArray<TObjectPtr<UPointLightComponent>> BrazierLights;

	UPROPERTY()
	FVector CrystalBaseLocation = FVector::ZeroVector;

	UPROPERTY()
	uint32 BuiltHash = 0;

	UPROPERTY(Transient)
	TArray<TObjectPtr<AActor>> SpawnedProps;

	// ---- runtime state (rebuilt in InitRuntime)
	struct FGateRuntime
	{
		float Open = 0.f;
		float HoldUntil = 0.f;
		uint8 Phase = 0; // 0 closed, 1 opening, 2 holding, 3 closing
	};
	FGateRuntime GateState[4];

	struct FCrowdMember
	{
		FTransform Body;
		FTransform Head;
		int32 Index = 0;
		uint8 Color = 0;
		bool bHopping = false;
	};
	struct FCrowdHop
	{
		int32 Member = 0;
		float Start = 0.f;
		float Duration = 0.5f;
		float Height = 30.f;
	};
	TArray<FCrowdMember> Crowd;
	TArray<FCrowdHop> Hops;
	TArray<TArray<int32>> CrowdBins;
	float CrowdHypeTarget = 0.1f;
	float CrowdHypeSmoothed = 0.1f;
	float HopAccumulator = 0.f;
	float PendingCheerHops = 0.f;
	float WaveAngle = 0.f;
	bool bWaveRunning = false;

	struct FPennant
	{
		int32 Fabric = 0;
		int32 Index = 0;
		FVector Pivot = FVector::ZeroVector;
		FVector Offset = FVector::ZeroVector;
		FQuat Rot = FQuat::Identity;
		FVector Scale = FVector::OneVector;
		float Phase = 0.f;
	};
	TArray<FPennant> Pennants;
	TArray<FTransform> FlameBase;
	TArray<FTransform> FaceBase;
	float PylonSpin = 0.f;
	float NextBlink = 0.f;
	float BlinkUntil = 0.f;
	bool bRuntimeReady = false;
};
