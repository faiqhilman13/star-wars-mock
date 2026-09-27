#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TrainingRemote.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UAudioComponent;
class USoundBase;
class UNiagaraSystem;
class ABlasterBolt;

/** Floating training remote: orbits the player and fires blaster bolts to practise deflection. */
UCLASS()
class JEDIARENA_API ATrainingRemote : public AActor
{
	GENERATED_BODY()

public:
	ATrainingRemote();

	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	UFUNCTION(BlueprintPure, Category = "Remote") bool IsActive() const { return bActive; }

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USphereComponent> Collision;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Body;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Eye;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UPointLightComponent> Glow;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UAudioComponent> HumAudio;

	UPROPERTY(EditAnywhere, Category = "Remote") TSubclassOf<ABlasterBolt> BoltClass;
	UPROPERTY(EditAnywhere, Category = "Remote") TObjectPtr<USoundBase> FireSound;
	UPROPERTY(EditAnywhere, Category = "Remote") TObjectPtr<USoundBase> ExplodeSound;
	UPROPERTY(EditAnywhere, Category = "Remote") TObjectPtr<UNiagaraSystem> HitFX;

	UPROPERTY(EditAnywhere, Category = "Remote") float MaxHP = 3.f;
	UPROPERTY(EditAnywhere, Category = "Remote") float OrbitRadius = 650.f;
	UPROPERTY(EditAnywhere, Category = "Remote") float OrbitSpeed = 25.f; // degrees per second
	UPROPERTY(EditAnywhere, Category = "Remote") float HoverHeight = 170.f;
	UPROPERTY(EditAnywhere, Category = "Remote") float FireIntervalMin = 1.6f;
	UPROPERTY(EditAnywhere, Category = "Remote") float FireIntervalMax = 3.2f;
	UPROPERTY(EditAnywhere, Category = "Remote") float Inaccuracy = 2.5f; // degrees
	UPROPERTY(EditAnywhere, Category = "Remote") float RespawnDelay = 7.f;
	UPROPERTY(EditAnywhere, Category = "Remote") float StartDelay = 4.f;

private:
	void Fire();
	void Explode();
	void Respawn();
	void ScheduleFire(float Delay);

	float HP = 3.f;
	float OrbitAngle = 0.f;
	float BobTime = 0.f;
	bool bActive = true;
	FVector KnockVelocity = FVector::ZeroVector;
	FTimerHandle FireTimer, RespawnTimer;
};
