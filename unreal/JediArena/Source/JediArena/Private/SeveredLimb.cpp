#include "SeveredLimb.h"

#include "Components/CapsuleComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "ReferenceSkeleton.h"

namespace
{
	/** A severable part: the bone that is cut, and the segment used to measure where the blade landed. */
	struct FCutRegion
	{
		const TCHAR* CutBone;
		const TCHAR* SegStart;
		const TCHAR* SegEnd;
		float Radius; // physics capsule radius of the severed piece
	};

	const FCutRegion GRegions[] = {
		{ TEXT("head"),       TEXT("neck_01"),    TEXT("head"),     11.f },
		{ TEXT("upperarm_l"), TEXT("upperarm_l"), TEXT("lowerarm_l"), 7.f },
		{ TEXT("lowerarm_l"), TEXT("lowerarm_l"), TEXT("hand_l"),     6.f },
		{ TEXT("upperarm_r"), TEXT("upperarm_r"), TEXT("lowerarm_r"), 7.f },
		{ TEXT("lowerarm_r"), TEXT("lowerarm_r"), TEXT("hand_r"),     6.f },
		{ TEXT("thigh_l"),    TEXT("thigh_l"),    TEXT("calf_l"),     10.f },
		{ TEXT("calf_l"),     TEXT("calf_l"),     TEXT("foot_l"),     8.f },
		{ TEXT("thigh_r"),    TEXT("thigh_r"),    TEXT("calf_r"),     10.f },
		{ TEXT("calf_r"),     TEXT("calf_r"),     TEXT("foot_r"),     8.f },
		{ TEXT("spine_03"),   TEXT("spine_01"),   TEXT("spine_04"),   18.f },
	};

	UStaticMesh* SphereMesh()
	{
		return LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	}

	bool IsInChain(const FReferenceSkeleton& Ref, int32 Bone, int32 Root)
	{
		for (int32 B = Bone; B != INDEX_NONE; B = Ref.GetParentIndex(B))
		{
			if (B == Root)
			{
				return true;
			}
		}
		return false;
	}

	const FCutRegion* FindRegion(FName CutBone)
	{
		for (const FCutRegion& R : GRegions)
		{
			if (CutBone == FName(R.CutBone))
			{
				return &R;
			}
		}
		return nullptr;
	}

	/** Segment endpoints for a region; the head segment is extended above the head bone. */
	bool RegionSegment(const USkeletalMeshComponent* Mesh, const FCutRegion& R, FVector& A, FVector& B)
	{
		if (Mesh->GetBoneIndex(R.SegStart) == INDEX_NONE || Mesh->GetBoneIndex(R.SegEnd) == INDEX_NONE)
		{
			return false;
		}
		A = Mesh->GetBoneLocation(R.SegStart);
		B = Mesh->GetBoneLocation(R.SegEnd);
		if (FName(R.CutBone) == TEXT("head"))
		{
			B += (B - A).GetSafeNormal() * 18.f;
		}
		return true;
	}
}

ASeveredLimb::ASeveredLimb()
{
	PrimaryActorTick.bCanEverTick = false;

	Body = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Body"));
	Body->InitCapsuleSize(8.f, 20.f);
	Body->SetCollisionProfileName(TEXT("PhysicsActor"));
	Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	Body->SetLinearDamping(0.2f);
	Body->SetAngularDamping(0.5f);
	RootComponent = Body;

	PartMesh = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("PartMesh"));
	PartMesh->SetupAttachment(Body);
	PartMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	Stump = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Stump"));
	Stump->SetupAttachment(Body);
	Stump->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Stump->SetCastShadow(false);

	InitialLifeSpan = 25.f;
}

FName ASeveredLimb::ChooseCutBone(const USkeletalMeshComponent* Mesh, const FVector& Point, float MaxDistance)
{
	if (!Mesh)
	{
		return NAME_None;
	}
	FName Best = NAME_None;
	float BestDist = MaxDistance;
	for (const FCutRegion& R : GRegions)
	{
		FVector A, B;
		if (!RegionSegment(Mesh, R, A, B) || const_cast<USkeletalMeshComponent*>(Mesh)->IsBoneHiddenByName(R.CutBone))
		{
			continue;
		}
		// Distance to the limb's surface rather than its bone line.
		const float Dist = FMath::PointDistToSegment(Point, A, B) - R.Radius;
		if (Dist < BestDist)
		{
			BestDist = Dist;
			Best = R.CutBone;
		}
	}
	return Best;
}

void ASeveredLimb::Init(USkeletalMeshComponent* Source, FName CutBone, const FVector& Impulse, UMaterialInterface* StumpMaterial)
{
	USkeletalMesh* Mesh = Source ? Source->GetSkeletalMeshAsset() : nullptr;
	const FCutRegion* Region = FindRegion(CutBone);
	FVector SegA, SegB;
	if (!Mesh || !Region || !RegionSegment(Source, *Region, SegA, SegB))
	{
		Destroy();
		return;
	}
	const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
	const int32 CutIndex = Ref.FindBoneIndex(CutBone);
	if (CutIndex == INDEX_NONE)
	{
		Destroy();
		return;
	}

	// For the torso cut the severed piece is the whole upper body; measure it from the waist up to the head.
	FVector PartA = Source->GetBoneLocation(CutBone);
	FVector PartB = SegB;
	if (CutBone == TEXT("spine_03") && Source->GetBoneIndex(TEXT("head")) != INDEX_NONE)
	{
		PartB = Source->GetBoneLocation(TEXT("head"));
	}
	else if (CutBone == TEXT("head"))
	{
		PartA = SegA;
	}
	const FVector Axis = (PartB - PartA).GetSafeNormal();
	const float Length = FMath::Max(FVector::Dist(PartA, PartB), Region->Radius * 2.f);

	// Poseable copy of the victim, collapsed to just this chain.
	PartMesh->SetSkinnedAssetAndUpdate(Mesh);
	for (int32 i = 0; i < Source->GetNumMaterials(); ++i)
	{
		PartMesh->SetMaterial(i, Source->GetMaterial(i));
	}
	PartMesh->SetWorldTransform(Source->GetComponentTransform());
	PartMesh->CopyPoseFromSkeletalComponent(Source);

	TArray<FName> KeepNames;
	TArray<FTransform> KeepCS;
	for (int32 i = 0; i < Ref.GetNum(); ++i)
	{
		if (IsInChain(Ref, i, CutIndex))
		{
			KeepNames.Add(Ref.GetBoneName(i));
			KeepCS.Add(PartMesh->GetBoneTransformByName(Ref.GetBoneName(i), EBoneSpaces::ComponentSpace));
		}
	}
	for (int32 i = 0; i < Ref.GetNum(); ++i)
	{
		if (!IsInChain(Ref, i, CutIndex))
		{
			const FName Name = Ref.GetBoneName(i);
			FTransform CS = PartMesh->GetBoneTransformByName(Name, EBoneSpaces::ComponentSpace);
			CS.SetScale3D(FVector(0.002f));
			PartMesh->SetBoneTransformByName(Name, CS, EBoneSpaces::ComponentSpace);
		}
	}
	for (int32 k = 0; k < KeepNames.Num(); ++k)
	{
		PartMesh->SetBoneTransformByName(KeepNames[k], KeepCS[k], EBoneSpaces::ComponentSpace);
	}

	// Physics capsule along the part (capsule axis is Z).
	const FTransform MeshWorld = PartMesh->GetComponentTransform();
	Body->SetCapsuleSize(Region->Radius, FMath::Max(Length * 0.5f, Region->Radius + 1.f));
	SetActorLocationAndRotation((PartA + PartB) * 0.5f, FRotationMatrix::MakeFromZ(Axis).Rotator());
	PartMesh->SetWorldTransform(MeshWorld);

	if (UStaticMesh* S = SphereMesh())
	{
		Stump->SetStaticMesh(S);
	}
	if (StumpMaterial)
	{
		Stump->SetMaterial(0, StumpMaterial);
	}
	Stump->SetWorldLocation(PartA);
	Stump->SetWorldScale3D(FVector(Region->Radius / 50.f));

	Body->SetSimulatePhysics(true);
	Body->AddImpulse(Impulse + FVector(0.f, 0.f, 300.f), NAME_None, true);
	Body->AddAngularImpulseInDegrees(FMath::VRand() * 700.f, NAME_None, true);
}

ASeveredLimb* ASeveredLimb::Sever(ACharacter* Victim, FName CutBone, const FVector& Impulse, UMaterialInterface* StumpMaterial)
{
	if (!IsValid(Victim) || !Victim->GetMesh() || CutBone.IsNone())
	{
		return nullptr;
	}
	USkeletalMeshComponent* Mesh = Victim->GetMesh();
	if (Mesh->GetBoneIndex(CutBone) == INDEX_NONE || Mesh->IsBoneHiddenByName(CutBone))
	{
		return nullptr;
	}
	const FReferenceSkeleton& Ref = Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
	const int32 CutIndex = Ref.FindBoneIndex(CutBone);
	const FName ParentBone = Ref.GetBoneName(Ref.GetParentIndex(CutIndex));

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASeveredLimb* Part = Victim->GetWorld()->SpawnActor<ASeveredLimb>(ASeveredLimb::StaticClass(), Mesh->GetSocketTransform(CutBone), Params);
	if (!Part)
	{
		return nullptr;
	}
	Part->Init(Mesh, CutBone, Impulse, StumpMaterial);

	// Anything held by the severed part (a saber in the cut hand) goes with it.
	TArray<AActor*> Attached;
	Victim->GetAttachedActors(Attached);
	for (AActor* Held : Attached)
	{
		USceneComponent* HeldRoot = Held ? Held->GetRootComponent() : nullptr;
		if (!HeldRoot || HeldRoot->GetAttachParent() != Mesh)
		{
			continue;
		}
		const int32 SocketBone = Mesh->GetBoneIndex(HeldRoot->GetAttachSocketName());
		if (SocketBone != INDEX_NONE && IsInChain(Ref, SocketBone, CutIndex))
		{
			Held->AttachToComponent(Part->PartMesh, FAttachmentTransformRules::KeepWorldTransform, HeldRoot->GetAttachSocketName());
		}
	}

	// Hide the part on the body and cauterize the wound.
	const FVector Wound = Mesh->GetBoneLocation(CutBone);
	Mesh->HideBoneByName(CutBone, EPhysBodyOp::PBO_Term);
	if (UStaticMesh* S = SphereMesh())
	{
		UStaticMeshComponent* Cap = NewObject<UStaticMeshComponent>(Victim);
		Cap->SetStaticMesh(S);
		if (StumpMaterial)
		{
			Cap->SetMaterial(0, StumpMaterial);
		}
		Cap->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Cap->SetCastShadow(false);
		Cap->SetupAttachment(Mesh, ParentBone);
		Cap->RegisterComponent();
		Cap->SetWorldLocation(Wound);
		const FCutRegion* Region = FindRegion(CutBone);
		Cap->SetWorldScale3D(FVector((Region ? Region->Radius : 8.f) / 50.f));
	}
	return Part;
}
