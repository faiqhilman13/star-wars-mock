#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "JediDamageable.h"
#include "FizzBarrel.generated.h"

class UAudioComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UNiagaraSystem;
class UPointLightComponent;
class UPrimitiveComponent;
class USoundBase;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Volatile blue "fizz" canister. Physics-simulated. Any damaging hit (saber, bolt, lightning, explosion, storm...)
 * lights a short hissing fuse, then it pops: every IJediDamageable within ExplosionRadius (other barrels too, so they
 * chain) takes an Explosion hit with an outward + upward knockback. Never hurts the Jedi. Force Push / Pull just shove
 * it around; a shoved barrel that slams into something hard at speed goes off on impact. Respawns at its original
 * spot after RespawnDelay.
 */
UCLASS()
class JEDIARENA_API AFizzBarrel : public AActor, public IJediDamageable
{
	GENERATED_BODY()

public:
	AFizzBarrel();

	/** Half the canister height (the root is centred), for placing barrels on the floor. */
	static constexpr float BarrelHalfHeight = 55.f;

	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	// IJediDamageable
	virtual float ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind) override;
	virtual bool IsJediTargetAlive() const override;

	/** Lights the fuse (FuseOverride <= 0 = random FuseMin..FuseMax). A burning fuse just gets shorter. */
	UFUNCTION(BlueprintCallable, Category = "Fizz")
	void Ignite(AActor* Causer, float FuseOverride = -1.f);

	UFUNCTION(BlueprintCallable, Category = "Fizz")
	void Explode();

	/** Eaten by the Sand Gobbler: vanish without a blast and respawn later. */
	UFUNCTION(BlueprintCallable, Category = "Fizz")
	void Gobble();

	UFUNCTION(BlueprintPure, Category = "Fizz")
	bool IsFused() const;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float ExplosionRadius = 500.f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float ExplosionDamage = 6.f;

	/** Knockback (cm/s) away from the blast... */
	UPROPERTY(EditAnywhere, Category = "Fizz")
	float BlastOutSpeed = 900.f;

	/** ...and up. */
	UPROPERTY(EditAnywhere, Category = "Fizz")
	float BlastUpSpeed = 700.f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float FuseMin = 0.3f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float FuseMax = 0.6f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float RespawnDelay = 20.f;

	/** Speed into a surface (cm/s) that sets off a flung barrel. <= 0 disables impact detonation. */
	UPROPERTY(EditAnywhere, Category = "Fizz")
	float ImpactDetonateSpeed = 1100.f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float HypeOnExplode = 2.f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	float BarrelMass = 60.f;

	UPROPERTY(EditAnywhere, Category = "Fizz")
	FLinearColor FizzColor = FLinearColor(0.2f, 1.2f, 2.f);

	UPROPERTY(EditAnywhere, Category = "Fizz|Audio")
	TObjectPtr<USoundBase> ExplodeSound;

	/** Fuse hiss (a whoosh pitched way up). */
	UPROPERTY(EditAnywhere, Category = "Fizz|Audio")
	TObjectPtr<USoundBase> HissSound;

	UPROPERTY(EditAnywhere, Category = "Fizz|FX")
	TObjectPtr<UNiagaraSystem> SparkFX;

	UPROPERTY(EditAnywhere, Category = "Fizz|Assets")
	TObjectPtr<UMaterialInterface> SurfaceMaterial;

	UPROPERTY(EditAnywhere, Category = "Fizz|Assets")
	TObjectPtr<UMaterialInterface> MetalMaterial;

	/** Expanding blast sphere (M_ForceWave: WaveColor / Fade / Intensity). */
	UPROPERTY(EditAnywhere, Category = "Fizz|Assets")
	TObjectPtr<UMaterialInterface> WaveMaterial;

	UPROPERTY(EditAnywhere, Category = "Fizz|Assets")
	TObjectPtr<UStaticMesh> CylinderMesh;

	UPROPERTY(EditAnywhere, Category = "Fizz|Assets")
	TObjectPtr<UStaticMesh> SphereMesh;

protected:
	virtual void BeginPlay() override;

	/** Physics root: the canister itself. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Band;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Cap;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Valve;

	/** World-space blast sphere (absolute transform, hidden until the pop). */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Blast;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UPointLightComponent> Glow;

	UFUNCTION()
	void OnBodyHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);

private:
	enum class EFizzState : uint8 { Idle, Fused, Gone, Popping };

	void Park();
	void SetPartsVisible(bool bVisible);
	void SetGlowMaterial(UMaterialInterface* Material);
	void StopHiss();
	void BlastDamage(const FVector& At, AActor* Credit);
	void Respawn();
	void TickFuse(float Now);
	void TickPop(float Now);
	void TickBlast(float Now);
	float TimeNow() const;

	EFizzState State = EFizzState::Idle;
	TWeakObjectPtr<AActor> FuseCauser;
	FTransform Home = FTransform::Identity;
	FVector HomeScale = FVector::OneVector;
	FVector BandBaseScale = FVector::OneVector;
	FVector LastVelocity = FVector::ZeroVector;
	float FuseStart = 0.f;
	float FuseEnd = 0.f;
	float PopStart = 0.f;
	float BlastStart = -1.f;
	float BlastMeshExtent = 50.f;
	bool bFlashOn = false;
	FTimerHandle RespawnTimer;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> GlowOnMat;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> GlowHotMat;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> BlastMID;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> HissAudio;
};
