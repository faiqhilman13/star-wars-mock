#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SeveredLimb.generated.h"

class UCapsuleComponent;
class UPoseableMeshComponent;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UMaterialInterface;

/**
 * A body part cut off a character: a poseable copy of the victim's mesh with every bone outside
 * the severed chain collapsed, riding on a physics capsule shaped to the part.
 */
UCLASS()
class JEDIARENA_API ASeveredLimb : public AActor
{
	GENERATED_BODY()

public:
	ASeveredLimb();

	/**
	 * Picks the part of Victim closest to Point (head, upper/lower arms, thighs, calves or the
	 * torso at the waist). Returns NAME_None if nothing is within MaxDistance.
	 */
	static FName ChooseCutBone(const USkeletalMeshComponent* Mesh, const FVector& Point, float MaxDistance = 90.f);

	/**
	 * Severs CutBone (and everything below it) from Victim: hides it on the body, caps the wound,
	 * spawns the flying part and moves any actors held by that part (e.g. a saber) onto it.
	 */
	static ASeveredLimb* Sever(ACharacter* Victim, FName CutBone, const FVector& Impulse, UMaterialInterface* StumpMaterial);

protected:
	void Init(USkeletalMeshComponent* Source, FName CutBone, const FVector& Impulse, UMaterialInterface* StumpMaterial);

	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UCapsuleComponent> Body;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UPoseableMeshComponent> PartMesh;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Stump;
};
