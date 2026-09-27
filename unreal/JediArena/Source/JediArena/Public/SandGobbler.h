#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SandGobbler.generated.h"

class ACharacter;
class AFizzBarrel;
class UInstancedStaticMeshComponent;
class UMaterialInterface;
class UNiagaraSystem;
class UPointLightComponent;
class USceneComponent;
class USoundBase;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * "The Gobbler": a sand-pit mouth sunk into the arena floor, ringed with gums and big curved teeth, with two
 * eye stalks that follow the Jedi around. Any horde member that ends up inside the mouth (usually courtesy of
 * Force Push) is chomped, pulled under and burped about. The Jedi is never eaten: the Gobbler spits them back
 * out with a small nip. Bosses are too big to swallow. Fizz Barrels give it hiccups.
 *
 * The pit is visual only (dark discs a few cm above the floor, which stays solid); victims lose collision and
 * are dragged down through the floor, then destroyed.
 */
UCLASS()
class JEDIARENA_API ASandGobbler : public AActor
{
	GENERATED_BODY()

public:
	ASandGobbler();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Snap the teeth (loud = with a crunch). */
	UFUNCTION(BlueprintCallable, Category = "Gobbler")
	void Chomp(bool bLoud = true);

	UFUNCTION(BlueprintPure, Category = "Gobbler")
	bool IsSwallowing(const AActor* Actor) const;

	/** Mouth radius (the arena sets this before spawning). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gobbler", meta = (ClampMin = "100"))
	float PitRadius = 420.f;

	/** Seconds between overlap scans. */
	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float ScanInterval = 0.1f;

	/** Only actors whose origin is at most this high above the pit get bitten (flying over is safe). */
	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float MaxBiteHeight = 240.f;

	/** Characters with a wider capsule than this are too big to swallow (they get spat out instead). */
	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float MaxSwallowRadius = 110.f;

	/** How long a victim takes to disappear down the gullet. */
	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float SwallowTime = 0.9f;

	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float SpitUpSpeed = 1200.f;

	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float SpitOutSpeed = 900.f;

	/** Damage for the Jedi when spat out. */
	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float PlayerSpitDamage = 1.f;

	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float HypePerGobble = 3.f;

	/** Minimum seconds between two banners of the same kind. */
	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float AnnounceCooldown = 6.f;

	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float IdleChompMin = 3.f;

	UPROPERTY(EditAnywhere, Category = "Gobbler")
	float IdleChompMax = 7.f;

	/** Crunch (played pitched down). */
	UPROPERTY(EditAnywhere, Category = "Gobbler|Audio")
	TObjectPtr<USoundBase> ChompSound;

	/** Burp (an explosion played way down). */
	UPROPERTY(EditAnywhere, Category = "Gobbler|Audio")
	TObjectPtr<USoundBase> BurpSound;

	/** Spit (a whoosh played up). */
	UPROPERTY(EditAnywhere, Category = "Gobbler|Audio")
	TObjectPtr<USoundBase> SpitSound;

	UPROPERTY(EditAnywhere, Category = "Gobbler|FX")
	TObjectPtr<UNiagaraSystem> SpitFX;

	UPROPERTY(EditAnywhere, Category = "Gobbler|Assets")
	TObjectPtr<UMaterialInterface> SurfaceMaterial;

	/** Glowing core deep in the throat. */
	UPROPERTY(EditAnywhere, Category = "Gobbler|Assets")
	TObjectPtr<UMaterialInterface> BellyMaterial;

	UPROPERTY(EditAnywhere, Category = "Gobbler|Assets")
	TObjectPtr<UStaticMesh> ConeMesh;

	UPROPERTY(EditAnywhere, Category = "Gobbler|Assets")
	TObjectPtr<UStaticMesh> CylinderMesh;

	UPROPERTY(EditAnywhere, Category = "Gobbler|Assets")
	TObjectPtr<UStaticMesh> SphereMesh;

	UPROPERTY(EditAnywhere, Category = "Gobbler|Assets")
	TObjectPtr<UStaticMesh> ChamferCubeMesh;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<USceneComponent> PitRoot;

	/** Dark outer disc of the mouth. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Throat;

	/** Pitch-black inner disc. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Gullet;

	/** Faint glowing core ("stomach"). */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Belly;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> Gums;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> Teeth;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> EyeStalks;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> Eyeballs;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> Pupils;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UPointLightComponent> BellyLight;

private:
	void BuildLayout();
	void ApplyRuntimeMaterials();
	void Scan();
	void HandleVictim(AActor* Victim);
	void BeginSwallow(AActor* Victim, float Now);
	void SpitOut(ACharacter* Spat, bool bIsPlayer);
	void FizzyBurp(AFizzBarrel* Barrel);
	void Burp();
	void Say(const FString& Text, float& LastTime, const FLinearColor& Color);
	void UpdateSwallows(float Now);
	void UpdateTeeth(float Bite01);
	void UpdateEyes(float Now);
	FTransform ToothTransform(int32 Index, float TiltDegrees) const;
	float TimeNow() const;

	struct FSwallow
	{
		TWeakObjectPtr<AActor> Actor;
		FVector StartLocation = FVector::ZeroVector;
		FVector StartScale = FVector::OneVector;
		float StartYaw = 0.f;
		float Start = 0.f;
		float Spin = 0.f;
	};
	TArray<FSwallow> Swallows;

	struct FTooth
	{
		float Angle = 0.f;
		float Height = 150.f;
		float Diameter = 80.f;
	};
	TArray<FTooth> ToothLayout;

	TMap<TWeakObjectPtr<AActor>, float> SpitCooldown;
	TArray<float> RecentGobbles;
	FVector EyeLocal[2] = { FVector::ZeroVector, FVector::ZeroVector };
	FVector BellyBaseScale = FVector::OneVector;
	float BellyLightIntensity = 150.f;
	float ScanAccum = 0.f;
	float ChompStart = -10.f;
	float NextIdleChomp = 0.f;
	float NextBlink = 0.f;
	float BlinkUntil = 0.f;
	float HappyUntil = 0.f;
	float BellyFlareUntil = 0.f;
	float LastGobbleAnnounce = -100.f;
	float LastBleghAnnounce = -100.f;
	float LastStreakAnnounce = -100.f;
	float LastFizzAnnounce = -100.f;
	bool bTeethAtRest = true;
	FTimerHandle BurpTimer;
};
