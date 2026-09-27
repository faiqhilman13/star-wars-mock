#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DropPod.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class USoundBase;
class UNiagaraSystem;

/**
 * A reinforcement pod: a red target ring appears on the floor, the pod plummets from the sky trailing
 * fire, slams down (knocking the Jedi back if too close), its petals burst open and a squad pops out.
 */
UCLASS()
class JEDIARENA_API ADropPod : public AActor
{
	GENERATED_BODY()

public:
	ADropPod();
	virtual void Tick(float DeltaSeconds) override;

	/** Starts the drop onto Site (floor point) carrying Count enemies of EnemyClass. */
	void Launch(const FVector& Site, TSubclassOf<AActor> EnemyClass, int32 Count);

	UPROPERTY(EditAnywhere, Category = "DropPod") float DropHeight = 6000.f;
	UPROPERTY(EditAnywhere, Category = "DropPod") float WarnTime = 0.9f;
	UPROPERTY(EditAnywhere, Category = "DropPod") float FallTime = 0.6f;
	UPROPERTY(EditAnywhere, Category = "DropPod") float ImpactRadius = 320.f;

protected:
	UPROPERTY(VisibleAnywhere, Category = "DropPod") TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere, Category = "DropPod") TObjectPtr<USceneComponent> PodPivot;
	UPROPERTY(VisibleAnywhere, Category = "DropPod") TObjectPtr<UStaticMeshComponent> Marker;
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> PetalPivots;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Trail;

	UPROPERTY() TObjectPtr<UStaticMesh> CubeMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> CylinderMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> ConeMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> SphereMesh;
	UPROPERTY() TObjectPtr<UMaterialInterface> SurfaceMat;
	UPROPERTY() TObjectPtr<UMaterialInterface> WaveMat;
	UPROPERTY() TObjectPtr<USoundBase> ImpactSound;
	UPROPERTY() TObjectPtr<USoundBase> WhistleSound;
	UPROPERTY() TObjectPtr<UNiagaraSystem> SparkFX;

private:
	void Build();
	void Impact();
	void SpawnPassenger(int32 Index);
	UStaticMeshComponent* AddMesh(UStaticMesh* Mesh, USceneComponent* Parent, const FVector& Loc, const FRotator& Rot, const FVector& Scale, UMaterialInterface* Mat);

	enum class EPhase : uint8 { Idle, Warning, Falling, Opening, Unloading, Lingering };
	EPhase Phase = EPhase::Idle;
	float PhaseStart = 0.f;
	FVector LandSite = FVector::ZeroVector;
	TSubclassOf<AActor> Cargo;
	int32 CargoCount = 0;
	int32 Spawned = 0;
	float NextSpawn = 0.f;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> MarkerMID;
};
