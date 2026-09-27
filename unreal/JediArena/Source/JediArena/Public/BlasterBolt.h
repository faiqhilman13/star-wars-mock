#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BlasterBolt.generated.h"

class USphereComponent;
class UProjectileMovementComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UNiagaraSystem;
class USoundBase;

/** Red blaster bolt. Damages whatever it hits; a Jedi can deflect it (see AJediCharacter::TryDeflectBolt). */
UCLASS()
class JEDIARENA_API ABlasterBolt : public AActor
{
	GENERATED_BODY()

public:
	ABlasterBolt();

	/** Sends the bolt off in a new direction, now hostile to its original shooter. */
	void Deflect(const FVector& NewDirection, AActor* NewOwnerActor, float SpeedScale = 1.25f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Blaster") float Damage = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Blaster") float Speed = 2600.f;
	UPROPERTY(EditAnywhere, Category = "Blaster") TObjectPtr<UNiagaraSystem> ImpactFX;
	UPROPERTY(EditAnywhere, Category = "Blaster") TObjectPtr<USoundBase> ImpactSound;

	/** Who fired it (or who deflected it last). */
	UPROPERTY(BlueprintReadOnly, Category = "Blaster") TWeakObjectPtr<AActor> Shooter;
	UPROPERTY(BlueprintReadOnly, Category = "Blaster") bool bDeflected = false;

	FVector GetDirection() const;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USphereComponent> Collision;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Core;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UPointLightComponent> Light;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UProjectileMovementComponent> Movement;

private:
	UFUNCTION()
	void OnOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 BodyIndex, bool bFromSweep, const FHitResult& Sweep);

	UFUNCTION()
	void OnHit(UPrimitiveComponent* HitComp, AActor* Other, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);

	void Impact(const FVector& Location, const FVector& Normal);
	TSet<TWeakObjectPtr<AActor>> RecentlyIgnored;
};
