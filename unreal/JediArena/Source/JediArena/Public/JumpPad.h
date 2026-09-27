#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "JumpPad.generated.h"

class ACharacter;
class UCapsuleComponent;
class UInstancedStaticMeshComponent;
class UMaterialInterface;
class UNiagaraComponent;
class UNiagaraSystem;
class UPrimitiveComponent;
class USceneComponent;
class USoundBase;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Glowing launch pad. Characters that step on it (the Jedi, and enemies for fun) are thrown on an arc that lands on
 * LaunchTarget. Chevrons on the pad point the way. Per-character cooldown so nobody gets juggled forever.
 */
UCLASS()
class JEDIARENA_API AJumpPad : public AActor
{
	GENERATED_BODY()

public:
	AJumpPad();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Throws Character toward LaunchTarget. Returns false when on cooldown / not launchable. */
	UFUNCTION(BlueprintCallable, Category = "Jump Pad")
	bool Launch(ACharacter* Character);

	UFUNCTION(BlueprintPure, Category = "Jump Pad")
	FVector GetLaunchTargetWorld() const;

	/** Landing point in the pad's local space (+X = the way the pad faces). Floor level. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump Pad", meta = (MakeEditWidget = true))
	FVector LaunchTarget = FVector(2500.f, 0.f, 0.f);

	/** Vertical launch speed (cm/s); the horizontal speed is solved so the arc lands on LaunchTarget. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump Pad", meta = (ClampMin = "300"))
	float LaunchUpSpeed = 1150.f;

	UPROPERTY(EditAnywhere, Category = "Jump Pad")
	bool bLaunchEnemies = true;

	/** Seconds before the same character can be launched again. */
	UPROPERTY(EditAnywhere, Category = "Jump Pad")
	float Cooldown = 0.9f;

	UPROPERTY(EditAnywhere, Category = "Jump Pad", meta = (ClampMin = "60"))
	float PadRadius = 150.f;

	UPROPERTY(EditAnywhere, Category = "Jump Pad")
	FLinearColor GlowColor = FLinearColor(1.f, 0.55f, 0.1f);

	UPROPERTY(EditAnywhere, Category = "Jump Pad|Audio")
	TObjectPtr<USoundBase> LaunchSound;

	/** Looping pad effect. */
	UPROPERTY(EditAnywhere, Category = "Jump Pad|FX")
	TObjectPtr<UNiagaraSystem> PadFX;

	/** One-shot burst under the launched character's feet. */
	UPROPERTY(EditAnywhere, Category = "Jump Pad|FX")
	TObjectPtr<UNiagaraSystem> LaunchFX;

	UPROPERTY(EditAnywhere, Category = "Jump Pad|Assets")
	TObjectPtr<UMaterialInterface> SurfaceMaterial;

	UPROPERTY(EditAnywhere, Category = "Jump Pad|Assets")
	TObjectPtr<UMaterialInterface> MetalMaterial;

	UPROPERTY(EditAnywhere, Category = "Jump Pad|Assets")
	TObjectPtr<UStaticMesh> CylinderMesh;

	UPROPERTY(EditAnywhere, Category = "Jump Pad|Assets")
	TObjectPtr<UStaticMesh> CubeMesh;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<USceneComponent> PadRoot;

	/** Walkable 30 cm plinth. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> PadBase;

	/** Glowing ring around the plinth's foot. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Rim;

	/** Glowing disc on top. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Core;

	/** Direction chevrons (animated). */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> Chevrons;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UCapsuleComponent> Trigger;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UNiagaraComponent> PadEffect;

	UFUNCTION()
	void OnTriggerBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

private:
	void Layout();
	float TimeNow() const;

	TMap<TWeakObjectPtr<AActor>, float> LastLaunch;
	TArray<FTransform> ChevronBase;
	float RecheckAccum = 0.f;
	float FlashUntil = 0.f;
	bool bFlashing = false;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> GlowMat;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> FlashMat;
};
