#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "JediDamageable.generated.h"

/** What kind of attack landed, so targets can react differently (shields, stagger, launch...). */
UENUM(BlueprintType)
enum class EJediHitKind : uint8
{
	Generic,
	Saber,
	ForcePush,
	ForcePull,
	Lightning,
	Bolt,
	Storm,
	Explosion,
	Environment
};

UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class UJediDamageable : public UInterface
{
	GENERATED_BODY()
};

/**
 * Anything the Jedi can hit with full hit information: horde enemies, the boss, arena props.
 * AJediCharacter::DamageActor routes to ReceiveJediHit when a target implements this.
 */
class JEDIARENA_API IJediDamageable
{
	GENERATED_BODY()

public:
	/**
	 * Apply a hit. Impulse is a velocity-style knockback (cm/s) the target may use to launch itself.
	 * Returns the damage actually taken (0 when blocked / immune).
	 */
	virtual float ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind) = 0;

	/** False once dead/destroyed-pending, so Force powers and the HUD skip it. */
	virtual bool IsJediTargetAlive() const { return true; }

	/** 0..1, for health bars (boss / officers). */
	virtual float GetJediHealthFraction() const { return 1.f; }

	/** Current HP, or < 0 if unknown (used to detect lethal saber blows for dismemberment). */
	virtual float GetJediHealth() const { return -1.f; }
};
