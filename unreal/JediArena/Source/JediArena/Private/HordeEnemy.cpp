#include "HordeEnemy.h"

#include "BlasterBolt.h"
#include "ColosseumArena.h"
#include "HordeDirector.h"
#include "JediCharacter.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraFunctionLibrary.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

TArray<TWeakObjectPtr<AHordeEnemy>> AHordeEnemy::AllEnemies;

namespace
{
	template <typename T>
	T* FindAsset(const TCHAR* Path)
	{
		ConstructorHelpers::FObjectFinder<T> Finder(Path);
		return Finder.Succeeded() ? Finder.Object : nullptr;
	}

	/** The colosseum (cached per world; tolerates levels without one). */
	AColosseumArena* FindArena(const UObject* Context)
	{
		static TWeakObjectPtr<AColosseumArena> Cached;
		static TWeakObjectPtr<UWorld> SearchedWorld;
		UWorld* World = Context ? Context->GetWorld() : nullptr;
		if (!World)
		{
			return nullptr;
		}
		if (Cached.IsValid() && Cached->GetWorld() == World)
		{
			return Cached.Get();
		}
		if (SearchedWorld.Get() != World)
		{
			SearchedWorld = World;
			Cached = nullptr;
			for (TActorIterator<AColosseumArena> It(World); It; ++It)
			{
				Cached = *It;
				break;
			}
		}
		return Cached.Get();
	}

	const TArray<const TCHAR*> ClankerSpawnLines = {
		TEXT("Uh oh."), TEXT("Is that a Jedi?"), TEXT("I'm too new for this!"), TEXT("Roger-dodger!"),
		TEXT("Surrender, Jedi! ...please?"), TEXT("Formation! Wait, which one?"), TEXT("Was that in the manual?"),
		TEXT("Blast him! Gently!"), TEXT("Ooh, shiny sword.") };
	const TArray<const TCHAR*> ClankerDeathLines = {
		TEXT("Ow."), TEXT("Tell my toaster I loved her."), TEXT("Worth it!"), TEXT("Not the face!"),
		TEXT("Reboot me..."), TEXT("Bzzzt."), TEXT("I regret nothing!") };
	const TArray<const TCHAR*> BulwarkBlockLines = { TEXT("Shields up!"), TEXT("Ha! Not today."), TEXT("Nice try, laser-boy.") };
	const TArray<const TCHAR*> BulwarkBreakLines = { TEXT("My shield!"), TEXT("That's coming out of my pay!") };
	const TArray<const TCHAR*> JetLines = { TEXT("Wheee!"), TEXT("Can't catch me!"), TEXT("Death from above!") };
	const TArray<const TCHAR*> JetPulledLines = { TEXT("Hey, put me down!"), TEXT("WHOA-OA-OA!"), TEXT("Not the jetpack!") };
	const TArray<const TCHAR*> WardenLines = { TEXT("Hmph."), TEXT("Come, Jedi."), TEXT("Your form is sloppy.") };
	const TArray<const TCHAR*> WardenParriedLines = { TEXT("Impossible!"), TEXT("Lucky block!") };
}

// ============================================================================ construction

AHordeEnemy::AHordeEnemy()
{
	PrimaryActorTick.bCanEverTick = true;
	AutoPossessAI = EAutoPossessAI::Disabled;
	AIControllerClass = nullptr;
	bUseControllerRotationYaw = false;

	GetCapsuleComponent()->InitCapsuleSize(38.f, 92.f);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bRunPhysicsWithNoController = true;
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 540.f, 0.f);
	Move->MaxAcceleration = 2200.f;
	Move->BrakingDecelerationWalking = 1800.f;
	Move->MaxFlySpeed = 480.f;
	Move->BrakingDecelerationFlying = 1200.f;

	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -92.f));
	GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	GetMesh()->SetCollisionProfileName(TEXT("CharacterMesh"));

	MannyMesh = FindAsset<USkeletalMesh>(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
	QuinnMesh = FindAsset<USkeletalMesh>(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple"));
	static ConstructorHelpers::FClassFinder<UAnimInstance> AnimFinder(TEXT("/Game/Variant_Combat/Anims/ABP_Manny_Combat"));
	AnimClass = AnimFinder.Class;
	static ConstructorHelpers::FClassFinder<ABlasterBolt> BoltFinder(TEXT("/Game/Jedi/Blueprints/BP_BlasterBolt"));
	BoltClass = BoltFinder.Class;
	PickupClass = AHordePickup::StaticClass();

	SurfaceMat = FindAsset<UMaterialInterface>(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	WaveMat = FindAsset<UMaterialInterface>(TEXT("/Game/Jedi/Materials/M_ForceWave.M_ForceWave"));
	CubeMesh = FindAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Cube.Cube"));
	SphereMesh = FindAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	CylinderMesh = FindAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	ConeMesh = FindAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Cone.Cone"));

	AimAnim = FindAsset<UAnimSequenceBase>(TEXT("/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS.MF_Rifle_Idle_ADS"));
	FireAnim = FindAsset<UAnimSequenceBase>(TEXT("/Game/Characters/Mannequins/Anims/Rifle/MM_Rifle_Fire.MM_Rifle_Fire"));
	for (const TCHAR* Path : {
		TEXT("/Game/Characters/Mannequins/Anims/Rifle/HitReact/MM_HitReact_Front_Lgt_01.MM_HitReact_Front_Lgt_01"),
		TEXT("/Game/Characters/Mannequins/Anims/Rifle/HitReact/MM_HitReact_Front_Lgt_02.MM_HitReact_Front_Lgt_02"),
		TEXT("/Game/Characters/Mannequins/Anims/Rifle/HitReact/MM_HitReact_Front_Lgt_03.MM_HitReact_Front_Lgt_03"),
		TEXT("/Game/Characters/Mannequins/Anims/Rifle/HitReact/MM_HitReact_Front_Lgt_04.MM_HitReact_Front_Lgt_04") })
	{
		if (UAnimSequenceBase* A = FindAsset<UAnimSequenceBase>(Path)) { HitReactAnims.Add(A); }
	}
	for (const TCHAR* Path : {
		TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01.MM_Attack_01"),
		TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02.MM_Attack_02"),
		TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_03.MM_Attack_03") })
	{
		if (UAnimSequenceBase* A = FindAsset<UAnimSequenceBase>(Path)) { MeleeAnims.Add(A); }
	}
	FireSound = FindAsset<USoundBase>(TEXT("/Game/Jedi/Audio/Licensed/SW_Blaster_Fire_Wire.SW_Blaster_Fire_Wire"));
	ClangSound = FindAsset<USoundBase>(TEXT("/Game/Jedi/Audio/Licensed/SW_Saber_Clash_Rec2.SW_Saber_Clash_Rec2"));
	PopSound = FindAsset<USoundBase>(TEXT("/Game/Jedi/Audio/Licensed/SW_Remote_Explode.SW_Remote_Explode"));
	WhooshSound = FindAsset<USoundBase>(TEXT("/Game/Jedi/Audio/SW_Force_Push.SW_Force_Push"));
	SparkFX = FindAsset<UNiagaraSystem>(TEXT("/Game/Variant_Combat/VFX/NS_Damage.NS_Damage"));
}

AClankerDroid::AClankerDroid()
{
	Type = EHordeType::Clanker;
	MaxHP = 1.f; MoveSpeed = 380.f;
	PreferredMinRange = 550.f; PreferredMaxRange = 1250.f; AttackRange = 1900.f;
	FireIntervalMin = 3.4f; FireIntervalMax = 6.f; BoltDamage = 0.35f; BoltSpeed = 1900.f; Inaccuracy = 9.f;
	LaunchScale = 1.35f; KOValue = 1; PickupChance = 0.05f; BodyScale = 0.97f;
}

ABulwarkTrooper::ABulwarkTrooper()
{
	Type = EHordeType::Bulwark;
	MaxHP = 6.f; MoveSpeed = 280.f;
	PreferredMinRange = 700.f; PreferredMaxRange = 1450.f; AttackRange = 2100.f;
	FireIntervalMin = 2.0f; FireIntervalMax = 3.4f; BoltDamage = 0.75f; BoltSpeed = 2400.f; Inaccuracy = 3.5f;
	LaunchScale = 0.7f; KOValue = 3; PickupChance = 0.25f; BodyScale = 1.05f;
}

ABuzzRoller::ABuzzRoller()
{
	Type = EHordeType::Roller;
	MaxHP = 4.f; MoveSpeed = 950.f;
	PreferredMinRange = 0.f; PreferredMaxRange = 1100.f; AttackRange = 2200.f;
	FireIntervalMin = 1.5f; FireIntervalMax = 2.3f; BurstCount = 3; BoltDamage = 0.4f; BoltSpeed = 2700.f; Inaccuracy = 4.f;
	LaunchScale = 0.85f; KOValue = 4; PickupChance = 0.3f;
}

AJetGhost::AJetGhost()
{
	Type = EHordeType::JetGhost;
	MaxHP = 3.f; MoveSpeed = 480.f;
	PreferredMinRange = 900.f; PreferredMaxRange = 1250.f; AttackRange = 2600.f;
	FireIntervalMin = 3.0f; FireIntervalMax = 4.6f; BoltDamage = 1.5f; BoltSpeed = 1500.f; BoltScale = 2.2f; Inaccuracy = 3.f;
	LaunchScale = 1.f; KOValue = 4; PickupChance = 0.3f;
}

AMagnaWarden::AMagnaWarden()
{
	Type = EHordeType::Warden;
	MaxHP = 10.f; MoveSpeed = 420.f; AttackRange = 240.f;
	MeleeDamage = 1.5f; LaunchScale = 0.55f; KOValue = 8; PickupChance = 0.6f; BodyScale = 1.12f;
}

// ============================================================================ looks

UMaterialInstanceDynamic* AHordeEnemy::MakeMat(const FLinearColor& Color, float Roughness, float Metallic, const FLinearColor& Emissive)
{
	if (!SurfaceMat)
	{
		return nullptr;
	}
	UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(SurfaceMat, this);
	MID->SetVectorParameterValue(TEXT("BaseColor"), Color);
	MID->SetScalarParameterValue(TEXT("Roughness"), Roughness);
	MID->SetScalarParameterValue(TEXT("Metallic"), Metallic);
	MID->SetVectorParameterValue(TEXT("Emissive"), Emissive);
	return MID;
}

UStaticMeshComponent* AHordeEnemy::AddPart(UStaticMesh* PartMesh, USceneComponent* Parent, FName Socket, const FVector& Loc, const FRotator& Rot, const FVector& Scale, UMaterialInterface* Mat)
{
	if (!PartMesh || !Parent)
	{
		return nullptr;
	}
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetStaticMesh(PartMesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetGenerateOverlapEvents(false);
	C->SetCastShadow(Scale.GetMax() > 0.25f);
	C->RegisterComponent();
	// Placed in actor space relative to the bone's current (reference) pose, then attached keeping the
	// world transform, so parts follow the bone without depending on the bone's axis conventions.
	const FQuat ActorRot = GetActorQuat();
	const FVector Base = Socket.IsNone() ? Parent->GetComponentLocation() : Parent->GetSocketLocation(Socket);
	C->SetWorldLocationAndRotation(Base + ActorRot.RotateVector(Loc), ActorRot * Rot.Quaternion());
	C->SetWorldScale3D(Scale);
	C->AttachToComponent(Parent, FAttachmentTransformRules::KeepWorldTransform, Socket);
	if (Mat)
	{
		C->SetMaterial(0, Mat);
	}
	Parts.Add(C);
	return C;
}

void AHordeEnemy::BuildLooks()
{
	USkeletalMeshComponent* M = GetMesh();
	USceneComponent* Root = GetCapsuleComponent();
	const FRotator Forward(-90.f, 0.f, 0.f); // cylinder/cone Z axis -> actor forward

	auto SetBody = [&](USkeletalMesh* BodyMesh, const FVector& Scale, UMaterialInterface* Mat)
	{
		M->SetSkeletalMeshAsset(BodyMesh);
		if (AnimClass)
		{
			M->SetAnimInstanceClass(AnimClass);
		}
		M->SetRelativeScale3D(Scale);
		for (int32 i = 0; i < M->GetNumMaterials(); ++i)
		{
			M->SetMaterial(i, Mat);
		}
	};

	switch (Type)
	{
	case EHordeType::Clanker:
	{
		UMaterialInstanceDynamic* Tan = MakeMat(FLinearColor(0.55f, 0.42f, 0.24f), 0.45f, 0.6f);
		UMaterialInstanceDynamic* Dark = MakeMat(FLinearColor(0.05f, 0.05f, 0.06f), 0.4f, 0.7f);
		UMaterialInstanceDynamic* Eye = MakeMat(FLinearColor::Black, 0.5f, 0.f, FLinearColor(4.f, 2.6f, 0.3f));
		SetBody(QuinnMesh, FVector(0.72f, 0.8f, 1.f) * BodyScale, Tan);
		M->HideBoneByName(TEXT("head"), EPhysBodyOp::PBO_None);
		// Long skinny droid head: a snout on a small cranium, two lamp eyes.
		AddPart(SphereMesh, M, TEXT("head"), FVector(0.f, 0.f, 6.f), FRotator::ZeroRotator, FVector(0.17f, 0.15f, 0.17f), Tan);
		AddPart(CylinderMesh, M, TEXT("head"), FVector(14.f, 0.f, 3.f), Forward, FVector(0.11f, 0.11f, 0.34f), Tan);
		AddPart(SphereMesh, M, TEXT("head"), FVector(10.f, -5.f, 10.f), FRotator::ZeroRotator, FVector(0.045f), Eye);
		AddPart(SphereMesh, M, TEXT("head"), FVector(10.f, 5.f, 10.f), FRotator::ZeroRotator, FVector(0.045f), Eye);
		AddPart(CubeMesh, M, TEXT("spine_05"), FVector(-16.f, 0.f, -4.f), FRotator::ZeroRotator, FVector(0.14f, 0.26f, 0.3f), Tan);
		AddPart(CylinderMesh, M, TEXT("spine_05"), FVector(-18.f, 8.f, 28.f), FRotator::ZeroRotator, FVector(0.015f, 0.015f, 0.45f), Dark);
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(16.f, 0.f, 2.f), Forward, FVector(0.05f, 0.05f, 0.34f), Dark);
		break;
	}
	case EHordeType::Bulwark:
	{
		UMaterialInstanceDynamic* White = MakeMat(FLinearColor(0.82f, 0.82f, 0.86f), 0.22f, 0.1f);
		UMaterialInstanceDynamic* Black = MakeMat(FLinearColor(0.02f, 0.02f, 0.025f), 0.2f, 0.3f, FLinearColor(0.f, 0.05f, 0.12f));
		SetBody(MannyMesh, FVector(BodyScale), White);
		AddPart(SphereMesh, M, TEXT("head"), FVector(2.f, 0.f, 6.f), FRotator::ZeroRotator, FVector(0.3f, 0.29f, 0.3f), White);
		AddPart(CubeMesh, M, TEXT("head"), FVector(14.f, 0.f, 7.f), FRotator::ZeroRotator, FVector(0.04f, 0.2f, 0.06f), Black);
		AddPart(CubeMesh, M, TEXT("spine_05"), FVector(-15.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.14f, 0.34f, 0.36f), White);
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(24.f, 0.f, 2.f), Forward, FVector(0.065f, 0.065f, 0.6f), Black);
		if (WaveMat)
		{
			ShieldMID = UMaterialInstanceDynamic::Create(WaveMat, this);
			ShieldMID->SetVectorParameterValue(TEXT("WaveColor"), FLinearColor(0.2f, 0.75f, 1.6f));
			ShieldMID->SetScalarParameterValue(TEXT("Intensity"), 2.5f);
			ShieldMID->SetScalarParameterValue(TEXT("Fade"), 0.55f);
		}
		// Energy shield held square in front (attached to the capsule so it always faces forward).
		ShieldMesh = AddPart(CubeMesh, Root, NAME_None, FVector(72.f, 0.f, 5.f), FRotator::ZeroRotator, FVector(0.05f, 1.15f, 1.65f), ShieldMID);
		ShieldMesh->SetCastShadow(false);
		UMaterialInstanceDynamic* Frame = MakeMat(FLinearColor(0.1f, 0.1f, 0.12f), 0.3f, 0.8f, FLinearColor(0.2f, 1.2f, 3.f));
		AddPart(CylinderMesh, ShieldMesh, NAME_None, FVector(0.f, -57.f, 0.f), FRotator::ZeroRotator, FVector(0.05f, 0.05f, 1.7f), Frame);
		AddPart(CylinderMesh, ShieldMesh, NAME_None, FVector(0.f, 57.f, 0.f), FRotator::ZeroRotator, FVector(0.05f, 0.05f, 1.7f), Frame);
		break;
	}
	case EHordeType::Warden:
	{
		UMaterialInstanceDynamic* Armor = MakeMat(FLinearColor(0.03f, 0.03f, 0.035f), 0.3f, 0.6f);
		UMaterialInstanceDynamic* Crimson = MakeMat(FLinearColor(0.35f, 0.02f, 0.02f), 0.4f, 0.3f, FLinearColor(0.6f, 0.02f, 0.02f));
		UMaterialInstanceDynamic* Visor = MakeMat(FLinearColor::Black, 0.4f, 0.f, FLinearColor(6.f, 0.2f, 0.1f));
		UMaterialInstanceDynamic* Staff = MakeMat(FLinearColor(0.08f, 0.08f, 0.09f), 0.25f, 0.9f);
		UMaterialInstanceDynamic* Arc = MakeMat(FLinearColor(0.2f, 0.05f, 0.3f), 0.2f, 0.f, FLinearColor(3.f, 0.4f, 6.f));
		SetBody(MannyMesh, FVector(BodyScale), Armor);
		AddPart(CylinderMesh, M, TEXT("head"), FVector(1.f, 0.f, 8.f), FRotator::ZeroRotator, FVector(0.27f, 0.27f, 0.32f), Armor);
		AddPart(ConeMesh, M, TEXT("head"), FVector(1.f, 0.f, 30.f), FRotator::ZeroRotator, FVector(0.27f, 0.27f, 0.2f), Crimson);
		AddPart(CubeMesh, M, TEXT("head"), FVector(13.f, 0.f, 9.f), FRotator::ZeroRotator, FVector(0.03f, 0.18f, 0.025f), Visor);
		AddPart(CubeMesh, M, TEXT("upperarm_l"), FVector(0.f, 0.f, 6.f), FRotator(0.f, 0.f, 20.f), FVector(0.22f, 0.24f, 0.08f), Crimson);
		AddPart(CubeMesh, M, TEXT("upperarm_r"), FVector(0.f, 0.f, 6.f), FRotator(0.f, 0.f, -20.f), FVector(0.22f, 0.24f, 0.08f), Crimson);
		// Electrostaff held like a spear, crackling violet at both ends.
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(10.f, 0.f, 0.f), Forward, FVector(0.045f, 0.045f, 1.9f), Staff);
		AddPart(SphereMesh, M, TEXT("hand_r"), FVector(100.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.13f), Arc);
		AddPart(SphereMesh, M, TEXT("hand_r"), FVector(-80.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.13f), Arc);
		break;
	}
	case EHordeType::JetGhost:
	{
		UMaterialInstanceDynamic* Grey = MakeMat(FLinearColor(0.08f, 0.085f, 0.1f), 0.35f, 0.8f);
		UMaterialInstanceDynamic* Visor = MakeMat(FLinearColor::Black, 0.3f, 0.f, FLinearColor(5.f, 0.4f, 0.1f));
		UMaterialInstanceDynamic* Flame = MakeMat(FLinearColor(1.f, 0.4f, 0.05f), 0.5f, 0.f, FLinearColor(8.f, 2.5f, 0.4f));
		SetBody(QuinnMesh, FVector(BodyScale), Grey);
		AddPart(SphereMesh, M, TEXT("head"), FVector(2.f, 0.f, 6.f), FRotator::ZeroRotator, FVector(0.29f, 0.27f, 0.3f), Grey);
		AddPart(CubeMesh, M, TEXT("head"), FVector(14.f, 0.f, 8.f), FRotator::ZeroRotator, FVector(0.03f, 0.2f, 0.05f), Visor);
		for (const float Side : { -11.f, 11.f })
		{
			AddPart(CylinderMesh, M, TEXT("spine_05"), FVector(-22.f, Side, -8.f), FRotator::ZeroRotator, FVector(0.14f, 0.14f, 0.45f), Grey);
			if (UStaticMeshComponent* F = AddPart(ConeMesh, M, TEXT("spine_05"), FVector(-22.f, Side, -44.f), FRotator(180.f, 0.f, 0.f), FVector(0.12f, 0.12f, 0.32f), Flame))
			{
				F->SetCastShadow(false);
				JetFlames.Add(F);
			}
		}
		Muzzle = AddPart(CylinderMesh, M, TEXT("spine_05"), FVector(4.f, 22.f, 18.f), Forward, FVector(0.1f, 0.1f, 0.6f), Grey);
		break;
	}
	case EHordeType::Roller:
	{
		GetCapsuleComponent()->SetCapsuleSize(62.f, 62.f);
		M->SetSkeletalMeshAsset(nullptr);
		M->SetVisibility(false);
		M->SetComponentTickEnabled(false);
		UMaterialInstanceDynamic* Bronze = MakeMat(FLinearColor(0.5f, 0.3f, 0.12f), 0.35f, 0.9f);
		UMaterialInstanceDynamic* Dark = MakeMat(FLinearColor(0.04f, 0.035f, 0.03f), 0.4f, 0.8f);
		UMaterialInstanceDynamic* Eye = MakeMat(FLinearColor::Black, 0.4f, 0.f, FLinearColor(7.f, 0.3f, 0.1f));
		RollerBall = AddPart(SphereMesh, Root, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, FVector(1.2f), Bronze);
		AddPart(CylinderMesh, RollerBall, NAME_None, FVector::ZeroVector, FRotator(90.f, 0.f, 0.f), FVector(1.24f, 1.24f, 0.1f), Dark);

		RollerTurret = NewObject<USceneComponent>(this);
		RollerTurret->RegisterComponent();
		RollerTurret->AttachToComponent(Root, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		RollerTurret->SetRelativeLocation(FVector(0.f, 0.f, 30.f));
		AddPart(SphereMesh, RollerTurret, NAME_None, FVector(0.f, 0.f, 30.f), FRotator::ZeroRotator, FVector(0.75f, 0.75f, 0.5f), Bronze);
		AddPart(SphereMesh, RollerTurret, NAME_None, FVector(34.f, 0.f, 38.f), FRotator::ZeroRotator, FVector(0.1f), Eye);
		Muzzle = AddPart(CylinderMesh, RollerTurret, NAME_None, FVector(42.f, -15.f, 26.f), Forward, FVector(0.07f, 0.07f, 0.5f), Dark);
		AddPart(CylinderMesh, RollerTurret, NAME_None, FVector(42.f, 15.f, 26.f), Forward, FVector(0.07f, 0.07f, 0.5f), Dark);
		for (int32 i = 0; i < 3; ++i)
		{
			const float Yaw = 60.f + i * 120.f;
			const FVector Dir = FRotator(0.f, Yaw, 0.f).Vector();
			RollerLegs.Add(AddPart(CylinderMesh, Root, NAME_None, Dir * 42.f + FVector(0.f, 0.f, -28.f), FRotator(0.f, Yaw, 0.f) + FRotator(35.f, 0.f, 0.f),
				FVector(0.08f, 0.08f, 0.8f), Dark));
		}
		if (WaveMat)
		{
			ShieldMID = UMaterialInstanceDynamic::Create(WaveMat, this);
			ShieldMID->SetVectorParameterValue(TEXT("WaveColor"), FLinearColor(0.3f, 0.9f, 1.5f));
			ShieldMID->SetScalarParameterValue(TEXT("Intensity"), 1.6f);
			ShieldMID->SetScalarParameterValue(TEXT("Fade"), 0.45f);
		}
		ShieldMesh = AddPart(SphereMesh, Root, NAME_None, FVector(0.f, 0.f, 20.f), FRotator::ZeroRotator, FVector(2.5f), ShieldMID);
		ShieldMesh->SetCastShadow(false);
		ShieldHP = 4.f;
		SetRollerDeployed(0.f);
		break;
	}
	}

	Chatter = NewObject<UTextRenderComponent>(this);
	Chatter->RegisterComponent();
	Chatter->AttachToComponent(Root, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
	Chatter->SetRelativeLocation(FVector(0.f, 0.f, Type == EHordeType::Roller ? 110.f : 135.f));
	Chatter->SetHorizontalAlignment(EHTA_Center);
	Chatter->SetWorldSize(22.f);
	Chatter->SetTextRenderColor(FColor(255, 232, 120));
	Chatter->SetCastShadow(false);
	Chatter->SetVisibility(false);
}

void AHordeEnemy::SetRollerDeployed(float Alpha)
{
	DeployAlpha = Alpha;
	if (RollerBall)
	{
		RollerBall->SetVisibility(Alpha < 0.55f, true);
	}
	if (RollerTurret)
	{
		RollerTurret->SetVisibility(Alpha > 0.35f, true);
		RollerTurret->SetRelativeScale3D(FVector(FMath::Max(Alpha, 0.01f)));
	}
	for (UStaticMeshComponent* Leg : RollerLegs)
	{
		if (Leg)
		{
			Leg->SetVisibility(Alpha > 0.2f);
		}
	}
	if (ShieldMesh)
	{
		ShieldMesh->SetVisibility(Alpha > 0.8f && ShieldHP > 0.f, true);
	}
}

// ============================================================================ lifecycle

void AHordeEnemy::BeginPlay()
{
	Super::BeginPlay();
	HP = MaxHP;
	AllEnemies.Add(this);
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	GroundZ = GetActorLocation().Z - GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const float T = Now();
	NextFireTime = T + FMath::FRandRange(1.f, FireIntervalMax);
	NextStrafeFlip = T + FMath::FRandRange(2.f, 5.f);
	StrafeSign = FMath::RandBool() ? 1.f : -1.f;
	BuildLooks();

	switch (Type)
	{
	case EHordeType::Roller:
		State = EState::Rolling;
		break;
	case EHordeType::JetGhost:
		State = EState::Hover;
		HoverAltitude = FMath::FRandRange(420.f, 640.f);
		OrbitAngle = FMath::FRandRange(0.f, 2.f * PI);
		GetCharacterMovement()->SetMovementMode(MOVE_Flying);
		Say(JetLines, 0.3f);
		break;
	case EHordeType::Warden:
		Say(WardenLines, 0.4f);
		break;
	case EHordeType::Clanker:
		Say(ClankerSpawnLines, 0.12f);
		break;
	default:
		break;
	}
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->RegisterEnemy(this);
	}
}

void AHordeEnemy::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	AllEnemies.RemoveAll([this](const TWeakObjectPtr<AHordeEnemy>& E) { return !E.IsValid() || E.Get() == this; });
	Super::EndPlay(EndPlayReason);
}

float AHordeEnemy::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AHordeEnemy::Say(const TCHAR* Line, float Seconds)
{
	if (Chatter && Line)
	{
		Chatter->SetText(FText::FromString(Line));
		Chatter->SetVisibility(true);
		ChatterUntil = Now() + Seconds;
	}
}

void AHordeEnemy::Say(const TArray<const TCHAR*>& Lines, float Chance)
{
	if (Lines.Num() > 0 && FMath::FRand() < Chance)
	{
		Say(Lines[FMath::RandRange(0, Lines.Num() - 1)]);
	}
}

// ============================================================================ tick

void AHordeEnemy::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bDead)
	{
		return;
	}
	const float T = Now();
	if (Chatter && Chatter->IsVisible())
	{
		if (T > ChatterUntil)
		{
			Chatter->SetVisibility(false);
		}
		else if (APlayerCameraManager* Cam = UGameplayStatics::GetPlayerCameraManager(this, 0))
		{
			Chatter->SetWorldRotation((Cam->GetCameraLocation() - Chatter->GetComponentLocation()).Rotation());
		}
	}
	if (Type == EHordeType::Bulwark && ShieldMesh && ShieldDownUntil > 0.f && T > ShieldDownUntil)
	{
		ShieldDownUntil = 0.f;
		ShieldMesh->SetVisibility(true, true);
	}
	for (UStaticMeshComponent* F : JetFlames)
	{
		if (F)
		{
			FVector S = F->GetRelativeScale3D();
			S.Z = S.X * FMath::FRandRange(2.1f, 3.3f); // flicker the flame length, keep its width
			F->SetRelativeScale3D(S);
		}
	}

	ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const AJediCharacter* Jedi = Cast<AJediCharacter>(Player);
	if (!Player || (Jedi && Jedi->IsDead()))
	{
		return;
	}
	// Safety: never stay "airborne" forever if Landed didn't fire.
	if (State == EState::Airborne && T > StateUntil && GetCharacterMovement()->IsMovingOnGround())
	{
		State = Type == EHordeType::Roller ? EState::Rolling : EState::Approach;
	}

	switch (Type)
	{
	case EHordeType::Roller: TickRoller(DeltaSeconds, Player); break;
	case EHordeType::JetGhost: TickJet(DeltaSeconds, Player); break;
	default: TickGround(DeltaSeconds, Player); break;
	}
}

FVector AHordeEnemy::SteerAround(const FVector& Desired) const
{
	FVector Steer = Desired;
	const FVector Me = GetActorLocation();
	for (const TWeakObjectPtr<AHordeEnemy>& W : AllEnemies)
	{
		const AHordeEnemy* O = W.Get();
		if (!O || O == this || O->bDead)
		{
			continue;
		}
		FVector Delta = Me - O->GetActorLocation();
		Delta.Z = 0.f;
		const float Dist = Delta.Size();
		if (Dist > 1.f && Dist < 170.f)
		{
			Steer += Delta / Dist * ((170.f - Dist) / 170.f) * 1.3f;
		}
	}
	if (const AColosseumArena* Arena = FindArena(this))
	{
		FVector PitCenter;
		float PitRadius = 0.f;
		if (Arena->GetPitInfo(PitCenter, PitRadius))
		{
			FVector Away = Me - PitCenter;
			Away.Z = 0.f;
			const float Dist = Away.Size();
			if (Dist < PitRadius + 280.f)
			{
				Steer += Away.GetSafeNormal() * 1.6f * FMath::Clamp(1.f - (Dist - PitRadius) / 280.f, 0.f, 1.f);
			}
		}
		if (!Arena->IsInsideArena(Me, 350.f))
		{
			Steer += (Arena->GetArenaCenter() - Me).GetSafeNormal2D() * 1.5f;
		}
	}
	Steer.Z = 0.f;
	return Steer.Size() > 1.f ? Steer.GetSafeNormal() : Steer;
}

void AHordeEnemy::FaceToward(const FVector& Target, float Dt, float DegPerSec)
{
	FRotator Want = (Target - GetActorLocation()).Rotation();
	Want.Pitch = 0.f;
	Want.Roll = 0.f;
	SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(), Want, Dt, DegPerSec));
}

void AHordeEnemy::TickGround(float Dt, ACharacter* Player)
{
	const float T = Now();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const FVector Me = GetActorLocation();
	const FVector P = Player->GetActorLocation();
	FVector To = P - Me;
	To.Z = 0.f;
	const float D = To.Size();
	const FVector Dir = To.GetSafeNormal();

	switch (State)
	{
	case EState::Stagger:
	case EState::Stunned:
		if (T >= StateUntil)
		{
			State = EState::Approach;
		}
		return;
	case EState::Airborne:
		return;
	case EState::Aim:
	{
		Move->bOrientRotationToMovement = false;
		FaceToward(P, Dt, 540.f);
		if (T >= StateUntil && BurstLeft > 0 && T >= NextBurstShot)
		{
			FireAt(Player);
			--BurstLeft;
			NextBurstShot = T + 0.14f;
		}
		if (BurstLeft <= 0 && T >= NextBurstShot + 0.25f)
		{
			if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
			{
				AI->Montage_Stop(0.2f);
			}
			State = EState::Approach;
			NextFireTime = T + FMath::FRandRange(FireIntervalMin, FireIntervalMax);
		}
		return;
	}
	case EState::Melee:
		FaceToward(P, Dt, 300.f);
		if (MeleeHitTime > 0.f && T >= MeleeHitTime)
		{
			DoMeleeHit();
			MeleeHitTime = -1.f;
		}
		if (T >= StateUntil)
		{
			State = EState::Approach;
			Move->bOrientRotationToMovement = true;
		}
		return;
	default:
		break;
	}

	Move->bOrientRotationToMovement = true;
	FVector Want = FVector::ZeroVector;
	if (Type == EHordeType::Warden)
	{
		Want = D > 190.f ? Dir : FVector::CrossProduct(Dir, FVector::UpVector) * StrafeSign * 0.3f;
		if (D < AttackRange && T >= NextMeleeTime && MeleeAnims.Num() > 0)
		{
			AHordeDirector* Director = AHordeDirector::Get(this);
			if (!Director || Director->RequestAttackToken(this, true, 1.8f))
			{
				UAnimSequenceBase* Swing = MeleeAnims[FMath::RandRange(0, MeleeAnims.Num() - 1)];
				if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
				{
					AI->PlaySlotAnimationAsDynamicMontage(Swing, TEXT("DefaultSlot"), 0.1f, 0.2f, 1.1f);
				}
				State = EState::Melee;
				StateUntil = T + Swing->GetPlayLength() / 1.1f;
				MeleeHitTime = T + 0.38f;
				NextMeleeTime = T + FMath::FRandRange(1.5f, 2.6f);
				Move->StopMovementImmediately();
				Move->bOrientRotationToMovement = false;
				return;
			}
			NextMeleeTime = T + 0.5f;
		}
	}
	else
	{
		if (D > PreferredMaxRange)
		{
			Want = Dir;
		}
		else if (D < PreferredMinRange)
		{
			Want = -Dir * 0.7f;
		}
		else
		{
			Want = FVector::CrossProduct(FVector::UpVector, Dir) * StrafeSign * 0.55f;
		}
		if (T >= NextStrafeFlip)
		{
			StrafeSign = -StrafeSign;
			NextStrafeFlip = T + FMath::FRandRange(2.5f, 5.5f);
		}
		if (T >= NextFireTime && D < AttackRange)
		{
			AHordeDirector* Director = AHordeDirector::Get(this);
			if (!Director || Director->RequestAttackToken(this, false, 1.6f))
			{
				BeginAim();
				return;
			}
			NextFireTime = T + 0.6f;
		}
	}
	AddMovementInput(SteerAround(Want), 1.f);
}

void AHordeEnemy::BeginAim()
{
	State = EState::Aim;
	StateUntil = Now() + (Type == EHordeType::Clanker ? 0.6f : 0.42f);
	BurstLeft = FMath::Max(1, BurstCount);
	NextBurstShot = StateUntil;
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->bOrientRotationToMovement = false;
	if (AimAnim)
	{
		if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
		{
			AI->PlaySlotAnimationAsDynamicMontage(AimAnim, TEXT("DefaultSlot"), 0.15f, 0.2f, 1.f, 10);
		}
	}
}

void AHordeEnemy::FireAt(ACharacter* Player)
{
	if (!BoltClass || !Player)
	{
		return;
	}
	const FVector From = Muzzle ? Muzzle->GetComponentLocation() + GetActorForwardVector() * 30.f : GetActorLocation() + GetActorForwardVector() * 60.f;
	const FVector Target = Player->GetActorLocation() + FVector(0.f, 0.f, 20.f)
		+ Player->GetVelocity() * (FVector::Dist(From, Player->GetActorLocation()) / FMath::Max(BoltSpeed, 1.f)) * 0.5f;
	FRotator Aim = (Target - From).Rotation();
	Aim.Pitch += FMath::FRandRange(-Inaccuracy, Inaccuracy) * 0.5f;
	Aim.Yaw += FMath::FRandRange(-Inaccuracy, Inaccuracy);
	const FTransform SpawnXf(Aim, From, FVector(BoltScale));
	if (ABlasterBolt* Bolt = GetWorld()->SpawnActorDeferred<ABlasterBolt>(BoltClass, SpawnXf, this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
	{
		Bolt->Shooter = this;
		Bolt->Damage = BoltDamage;
		Bolt->Speed = BoltSpeed;
		Bolt->ImpactFX = SparkFX;
		UGameplayStatics::FinishSpawningActor(Bolt, SpawnXf);
	}
	if (FireSound)
	{
		const float Pitch = Type == EHordeType::Clanker ? 1.18f : Type == EHordeType::Roller ? 1.35f : Type == EHordeType::JetGhost ? 0.62f : 1.f;
		UGameplayStatics::PlaySoundAtLocation(this, FireSound, From, 0.45f, Pitch * FMath::FRandRange(0.95f, 1.05f));
	}
	if (FireAnim && Type != EHordeType::Roller && Type != EHordeType::JetGhost)
	{
		if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
		{
			AI->PlaySlotAnimationAsDynamicMontage(FireAnim, TEXT("DefaultSlot"), 0.05f, 0.15f, 1.2f);
		}
	}
}

void AHordeEnemy::DoMeleeHit()
{
	ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	if (!Player)
	{
		return;
	}
	const FVector To = Player->GetActorLocation() - GetActorLocation();
	if (To.Size2D() > 290.f || FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) < 0.25f)
	{
		return;
	}
	const float Dealt = UGameplayStatics::ApplyDamage(Player, MeleeDamage, nullptr, this, nullptr);
	if (Dealt > 0.f)
	{
		Player->LaunchCharacter(To.GetSafeNormal2D() * 520.f + FVector(0.f, 0.f, 220.f), true, true);
	}
	if (SparkFX && Muzzle)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparkFX, Muzzle->GetComponentLocation() + GetActorForwardVector() * 80.f);
	}
}

void AHordeEnemy::TickRoller(float Dt, ACharacter* Player)
{
	const float T = Now();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const FVector Me = GetActorLocation();
	const FVector P = Player->GetActorLocation();
	FVector To = P - Me;
	To.Z = 0.f;
	const float D = To.Size();

	switch (State)
	{
	case EState::Airborne:
	case EState::Stagger:
		if (State == EState::Stagger && T >= StateUntil)
		{
			State = EState::Rolling;
		}
		return;
	case EState::Rolling:
	{
		Move->MaxWalkSpeed = MoveSpeed;
		Move->bOrientRotationToMovement = true;
		AddMovementInput(SteerAround(To.GetSafeNormal()), 1.f);
		RollAngle += GetVelocity().Size2D() * Dt / 60.f * (180.f / PI);
		if (RollerBall)
		{
			RollerBall->SetRelativeRotation(FRotator(-RollAngle, 0.f, 0.f));
		}
		if (D < PreferredMaxRange && Move->IsMovingOnGround())
		{
			State = EState::Deploying;
			Move->StopMovementImmediately();
			Move->MaxWalkSpeed = 0.f;
			if (WhooshSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, WhooshSound, Me, 0.35f, 1.6f);
			}
		}
		return;
	}
	case EState::Deploying:
		FaceToward(P, Dt, 360.f);
		SetRollerDeployed(FMath::Min(1.f, DeployAlpha + Dt / 0.7f));
		if (DeployAlpha >= 1.f)
		{
			State = EState::Deployed;
			NextFireTime = T + 0.5f;
		}
		return;
	case EState::Deployed:
	{
		Move->bOrientRotationToMovement = false;
		FaceToward(P, Dt, 200.f);
		if (D > 2000.f)
		{
			State = EState::Rolling;
			SetRollerDeployed(0.f);
			return;
		}
		if (BurstLeft <= 0 && T >= NextFireTime)
		{
			AHordeDirector* Director = AHordeDirector::Get(this);
			if (!Director || Director->RequestAttackToken(this, false, 1.2f))
			{
				BurstLeft = BurstCount;
				NextBurstShot = T;
			}
			NextFireTime = T + FMath::FRandRange(FireIntervalMin, FireIntervalMax);
		}
		if (BurstLeft > 0 && T >= NextBurstShot)
		{
			FireAt(Player);
			--BurstLeft;
			NextBurstShot = T + 0.11f;
		}
		return;
	}
	default:
		State = EState::Rolling;
		return;
	}
}

void AHordeEnemy::TickJet(float Dt, ACharacter* Player)
{
	const float T = Now();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const FVector Me = GetActorLocation();
	const FVector P = Player->GetActorLocation();

	switch (State)
	{
	case EState::Airborne:
		return;
	case EState::Stunned:
		if (T >= StateUntil)
		{
			State = EState::Hover;
			Move->SetMovementMode(MOVE_Flying);
			LaunchCharacter(FVector(0.f, 0.f, 450.f), false, true);
			Say(JetLines, 0.4f);
		}
		return;
	default:
		break;
	}

	if (Move->MovementMode != MOVE_Flying)
	{
		Move->SetMovementMode(MOVE_Flying);
	}
	State = EState::Hover;
	Move->bOrientRotationToMovement = false;
	FaceToward(P, Dt, 300.f);
	if (T >= NextStrafeFlip)
	{
		StrafeSign = -StrafeSign;
		NextStrafeFlip = T + FMath::FRandRange(4.f, 8.f);
	}
	OrbitAngle += Dt * 0.35f * StrafeSign;
	FVector Goal = P + FVector(FMath::Cos(OrbitAngle), FMath::Sin(OrbitAngle), 0.f) * PreferredMaxRange;
	if (const AColosseumArena* Arena = FindArena(this))
	{
		const FVector C = Arena->GetArenaCenter();
		FVector Off = Goal - C;
		Off.Z = 0.f;
		const float MaxR = Arena->GetArenaRadius() - 500.f;
		if (Off.Size() > MaxR)
		{
			Goal = C + Off.GetSafeNormal() * MaxR;
		}
	}
	Goal.Z = GroundZ + HoverAltitude + FMath::Sin(T * 1.3f + OrbitAngle) * 40.f;
	const FVector Want = Goal - Me;
	if (Want.Size() > 40.f)
	{
		AddMovementInput(Want.GetSafeNormal(), FMath::Clamp(Want.Size() / 300.f, 0.25f, 1.f));
	}
	if (T >= NextFireTime && FVector::Dist(Me, P) < AttackRange)
	{
		AHordeDirector* Director = AHordeDirector::Get(this);
		if (!Director || Director->RequestAttackToken(this, false, 1.2f))
		{
			FireAt(Player);
			NextFireTime = T + FMath::FRandRange(FireIntervalMin, FireIntervalMax);
		}
		else
		{
			NextFireTime = T + 0.7f;
		}
	}
}

// ============================================================================ damage

float AHordeEnemy::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	return ReceiveJediHit(DamageAmount, DamageCauser, GetActorLocation(), FVector::ZeroVector, EJediHitKind::Generic);
}

float AHordeEnemy::ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
{
	if (bDead)
	{
		return 0.f;
	}
	const AActor* PlayerActor = UGameplayStatics::GetPlayerCharacter(this, 0);
	// No friendly fire between horde members (explosions and the environment still hurt everyone).
	if (Causer && Causer != PlayerActor && Causer != this && Kind != EJediHitKind::Explosion && Kind != EJediHitKind::Environment
		&& Causer->GetClass()->ImplementsInterface(UJediDamageable::StaticClass()))
	{
		return 0.f;
	}
	const float T = Now();
	const FVector FromDir = Causer ? (Causer->GetActorLocation() - GetActorLocation()).GetSafeNormal2D() : -GetActorForwardVector();
	const bool bFrontal = FVector::DotProduct(GetActorForwardVector(), FromDir) > 0.35f;
	const bool bForceBlast = Kind == EJediHitKind::ForcePush || Kind == EJediHitKind::Storm || Kind == EJediHitKind::Explosion;

	auto Clang = [&]()
	{
		if (SparkFX)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparkFX, Location, FromDir.Rotation());
		}
		if (ClangSound)
		{
			UGameplayStatics::PlaySoundAtLocation(this, ClangSound, Location, 0.45f, FMath::FRandRange(1.1f, 1.3f));
		}
	};

	// Bulwark energy shield: stops frontal saber/bolt/lightning; the Force (or flanking) breaks through.
	if (Type == EHordeType::Bulwark && ShieldMesh && ShieldDownUntil <= 0.f)
	{
		if (bForceBlast || Kind == EJediHitKind::ForcePull)
		{
			BreakShield(5.f);
		}
		else if (bFrontal)
		{
			if (Kind == EJediHitKind::Lightning)
			{
				LightningOnShield += Damage;
				if (LightningOnShield >= 1.f)
				{
					BreakShield(5.f);
					Stagger(1.f);
				}
			}
			Clang();
			if (Kind == EJediHitKind::Saber)
			{
				Say(BulwarkBlockLines, 0.2f);
			}
			return 0.f;
		}
	}
	// Buzz-Roller bubble shield while deployed: soaks damage until it pops (lightning shreds it).
	if (Type == EHordeType::Roller && ShieldHP > 0.f && (State == EState::Deployed || State == EState::Deploying) && !bForceBlast)
	{
		ShieldHP -= Kind == EJediHitKind::Lightning ? Damage * 5.f : FMath::Max(Damage, 0.5f);
		Clang();
		if (ShieldHP <= 0.f && ShieldMesh)
		{
			ShieldMesh->SetVisibility(false, true);
			if (PopSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, PopSound, GetActorLocation(), 0.35f, 1.9f);
			}
			Say(TEXT("*panicked beeping*"));
		}
		return 0.f;
	}
	// Magna Warden guard: blocks some frontal saber strikes unless busy attacking or staggered.
	if (Type == EHordeType::Warden && Kind == EJediHitKind::Saber && bFrontal && State != EState::Melee && State != EState::Stagger
		&& State != EState::Airborne && FMath::FRand() < 0.5f)
	{
		Clang();
		FaceToward(GetActorLocation() + FromDir * 100.f, 1.f, 720.f);
		return 0.f;
	}

	HP -= Damage;
	if (Causer)
	{
		LastHitter = Causer;
	}
	if (HP <= 0.f)
	{
		Die(Causer ? Causer : LastHitter.Get(), Impulse, Kind);
		return Damage;
	}

	if (Type == EHordeType::JetGhost && (Kind == EJediHitKind::ForcePull || bForceBlast))
	{
		Say(JetPulledLines, 0.7f);
		Launch(Impulse + (Kind == EJediHitKind::ForcePull ? FVector(0.f, 0.f, -350.f) : FVector::ZeroVector));
		return Damage;
	}
	if (bForceBlast || Kind == EJediHitKind::ForcePull || Impulse.Size() * LaunchScale > 380.f)
	{
		Launch(Impulse);
	}
	else if (Damage <= 0.f && Impulse.SizeSquared() > 1.f)
	{
		// A parried strike (zero-damage knockback from the Jedi): big opening.
		Stagger(Type == EHordeType::Warden ? 1.6f : 0.6f);
		if (Type == EHordeType::Warden)
		{
			Say(WardenParriedLines, 0.6f);
		}
	}
	else
	{
		Stagger(Type == EHordeType::Warden ? 0.25f : 0.35f);
	}
	return Damage;
}

void AHordeEnemy::BreakShield(float Seconds)
{
	ShieldDownUntil = Now() + Seconds;
	LightningOnShield = 0.f;
	if (ShieldMesh)
	{
		ShieldMesh->SetVisibility(false, true);
	}
	if (PopSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, PopSound, GetActorLocation(), 0.3f, 2.f);
	}
	Say(BulwarkBreakLines, 0.6f);
}

void AHordeEnemy::Stagger(float Seconds)
{
	if (Type == EHordeType::Roller && (State == EState::Deployed || State == EState::Deploying))
	{
		return; // turrets just shrug
	}
	State = EState::Stagger;
	StateUntil = Now() + Seconds;
	GetCharacterMovement()->StopMovementImmediately();
	if (HitReactAnims.Num() > 0 && Type != EHordeType::Roller)
	{
		if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
		{
			AI->PlaySlotAnimationAsDynamicMontage(HitReactAnims[FMath::RandRange(0, HitReactAnims.Num() - 1)], TEXT("DefaultSlot"), 0.05f, 0.2f, 1.2f);
		}
	}
}

void AHordeEnemy::Launch(const FVector& Impulse)
{
	if (UAnimInstance* AI = GetMesh()->GetAnimInstance())
	{
		AI->Montage_Stop(0.1f);
	}
	State = EState::Airborne;
	StateUntil = Now() + 3.f;
	if (Type == EHordeType::Roller)
	{
		SetRollerDeployed(0.f);
	}
	GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	FVector V = Impulse * LaunchScale;
	V.Z = FMath::Max(V.Z, 250.f);
	LaunchCharacter(V, true, true);
}

void AHordeEnemy::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);
	if (bDead || State != EState::Airborne)
	{
		return;
	}
	switch (Type)
	{
	case EHordeType::JetGhost:
		State = EState::Stunned;
		StateUntil = Now() + 2.6f;
		break;
	case EHordeType::Roller:
		State = EState::Rolling;
		break;
	default:
		State = EState::Stagger;
		StateUntil = Now() + 0.5f;
		break;
	}
}

void AHordeEnemy::Die(AActor* Killer, const FVector& Impulse, EJediHitKind Kind)
{
	bDead = true;
	HP = 0.f;
	State = EState::Dead;
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->NotifyKO(this, Killer, KOValue);
	}
	if (Type == EHordeType::Clanker)
	{
		Say(ClankerDeathLines, 0.22f);
	}

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->StopMovementImmediately();
	Move->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	for (UStaticMeshComponent* F : JetFlames)
	{
		if (F)
		{
			F->SetVisibility(false);
		}
	}
	if (ShieldMesh)
	{
		ShieldMesh->SetVisibility(false, true);
	}

	FVector Fling = Impulse.GetClampedToMaxSize(2600.f) * FMath::Max(LaunchScale, 0.8f);
	Fling.Z = FMath::Max(Fling.Z, 300.f);

	auto BreakOff = [&](UStaticMeshComponent* Part, const FVector& Kick)
	{
		if (!Part)
		{
			return;
		}
		Part->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
		Part->SetCollisionProfileName(TEXT("PhysicsActor"));
		Part->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
		Part->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
		Part->SetSimulatePhysics(true);
		Part->AddImpulse(Kick, NAME_None, true);
		Part->AddAngularImpulseInDegrees(FMath::VRand() * 900.f, NAME_None, true);
	};

	if (Type == EHordeType::Roller)
	{
		// Rollers burst into bouncing scrap.
		for (UStaticMeshComponent* Part : Parts)
		{
			if (Part && Part != ShieldMesh && Part->IsVisible())
			{
				BreakOff(Part, Fling * 0.4f + FMath::VRand() * 500.f + FVector(0.f, 0.f, 400.f));
			}
		}
	}
	else
	{
		USkeletalMeshComponent* M = GetMesh();
		if (UAnimInstance* AI = M->GetAnimInstance())
		{
			AI->Montage_Stop(0.f);
		}
		M->SetCollisionProfileName(TEXT("Ragdoll"));
		M->SetAllBodiesSimulatePhysics(true);
		M->SetSimulatePhysics(true);
		M->WakeAllRigidBodies();
		M->SetAllPhysicsLinearVelocity(Fling);
		M->AddAngularImpulseInDegrees(FMath::VRand() * 600.f, TEXT("pelvis"), true);
		// Droids come apart: the head (first part) pops off sometimes.
		if (Type == EHordeType::Clanker && Parts.Num() > 0 && FMath::FRand() < 0.4f)
		{
			BreakOff(Parts[0], Fling * 0.3f + FVector(0.f, 0.f, 650.f));
			if (Parts.IsValidIndex(1))
			{
				BreakOff(Parts[1], Fling * 0.3f + FVector(0.f, 0.f, 600.f));
			}
		}
	}

	const bool bDroid = Type == EHordeType::Clanker || Type == EHordeType::Roller;
	if (SparkFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparkFX, GetActorLocation(), Fling.Rotation());
	}
	if (bDroid && PopSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, PopSound, GetActorLocation(), 0.18f, FMath::FRandRange(1.7f, 2.1f));
	}
	if (PickupClass && FMath::FRand() < PickupChance)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (AHordePickup* Orb = GetWorld()->SpawnActor<AHordePickup>(PickupClass, GetActorLocation() + FVector(0.f, 0.f, 40.f), FRotator::ZeroRotator, Params))
		{
			Orb->Init(FMath::FRand() < 0.55f);
		}
	}
	SetLifeSpan(Type == EHordeType::Roller ? 4.f : 6.f);
}

// ============================================================================ pickup

AHordePickup::AHordePickup()
{
	PrimaryActorTick.bCanEverTick = true;
	Orb = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Orb"));
	RootComponent = Orb;
	Orb->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Orb->SetCastShadow(false);
	Orb->SetRelativeScale3D(FVector(0.26f));
	Orb->SetStaticMesh(FindAsset<UStaticMesh>(TEXT("/Engine/BasicShapes/Sphere.Sphere")));
	SurfaceMat = FindAsset<UMaterialInterface>(TEXT("/Game/Jedi/Materials/M_ArenaSurface.M_ArenaSurface"));
	CollectSound = FindAsset<USoundBase>(TEXT("/Game/Jedi/Audio/Licensed/SW_Saber_Ignite.SW_Saber_Ignite"));
}

void AHordePickup::Init(bool bHealth)
{
	bIsHealth = bHealth;
	BaseLoc = GetActorLocation();
	if (SurfaceMat)
	{
		UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(SurfaceMat, this);
		MID->SetVectorParameterValue(TEXT("BaseColor"), FLinearColor::Black);
		MID->SetVectorParameterValue(TEXT("Emissive"), bHealth ? FLinearColor(0.3f, 4.f, 0.6f) : FLinearColor(0.4f, 1.4f, 6.f));
		Orb->SetMaterial(0, MID);
	}
}

void AHordePickup::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Age += DeltaSeconds;
	if (Age > 14.f)
	{
		Destroy();
		return;
	}
	AJediCharacter* Jedi = Cast<AJediCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
	FVector Loc = GetActorLocation();
	if (Jedi && !Jedi->IsDead())
	{
		const FVector Target = Jedi->GetActorLocation();
		const float Dist = FVector::Dist(Loc, Target);
		if (Dist < 90.f)
		{
			if (bIsHealth)
			{
				Jedi->HealBy(HealAmount);
			}
			else
			{
				Jedi->RestoreForce(ForceAmount);
			}
			if (CollectSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, CollectSound, Loc, 0.3f, 2.2f);
			}
			Destroy();
			return;
		}
		if (Dist < MagnetRange)
		{
			Loc = FMath::VInterpConstantTo(Loc, Target, DeltaSeconds, 700.f + Age * 150.f);
			BaseLoc = Loc;
			SetActorLocation(Loc);
			return;
		}
	}
	SetActorLocation(BaseLoc + FVector(0.f, 0.f, 12.f * FMath::Sin(Age * 3.f)));
	SetActorScale3D(FVector(0.26f * (1.f + 0.12f * FMath::Sin(Age * 7.f))));
}
