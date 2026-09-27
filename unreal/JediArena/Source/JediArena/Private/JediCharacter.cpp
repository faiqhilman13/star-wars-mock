#include "JediCharacter.h"

#include "ProceduralMeshComponent.h"
#include "Animation/AnimMontage.h"

#include "BlasterBolt.h"
#include "Components/AudioComponent.h"
#include "SeveredLimb.h"
#include "HordeDirector.h"
#include "Engine/SkeletalMeshSocket.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/PointLightComponent.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "Engine/Texture2D.h"
#include "TrainingRemote.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Blueprint/UserWidget.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraShakeBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/WidgetComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputActionValue.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "TimerManager.h"

#if WITH_EDITOR
#include "Engine/Blueprint.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Factories/Factory.h"
#include "Factories/FbxFactory.h"
#include "AssetImportTask.h"
#include "Factories/FbxImportUI.h"
#include "Factories/FbxSkeletalMeshImportData.h"
#include "Animation/Skeleton.h"
#include "HAL/FileManager.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/PhysicsConstraintTemplate.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "Engine/SkeletalMesh.h"
#include "Misc/Paths.h"
#include "UObject/Package.h"
#include "UObject/UObjectIterator.h"
#endif

namespace
{
	/** Loosely-typed argument for calling Blueprint functions/events by name. */
	struct FBPArg
	{
		enum class EKind : uint8 { Number, Bool, Object, Vector, Color, Name };
		EKind Kind;
		double Number = 0.0;
		bool Bool = false;
		UObject* Object = nullptr;
		FVector Vector = FVector::ZeroVector;
		FLinearColor Color = FLinearColor::White;
		FName Name;

		FBPArg(double In) : Kind(EKind::Number), Number(In) {}
		FBPArg(float In) : Kind(EKind::Number), Number(In) {}
		FBPArg(bool In) : Kind(EKind::Bool), Bool(In) {}
		FBPArg(UObject* In) : Kind(EKind::Object), Object(In) {}
		FBPArg(const FVector& In) : Kind(EKind::Vector), Vector(In) {}
		FBPArg(const FLinearColor& In) : Kind(EKind::Color), Color(In) {}
		FBPArg(FName In) : Kind(EKind::Name), Name(In) {}
	};

	/**
	 * Calls a Blueprint-implemented function (interface message, custom event, BP function)
	 * by name, filling input parameters positionally. Returns false if the target doesn't have it.
	 */
	bool CallBP(UObject* Target, FName FuncName, std::initializer_list<FBPArg> Args = {})
	{
		if (!IsValid(Target))
		{
			return false;
		}
		UFunction* Func = Target->FindFunction(FuncName);
		if (!Func)
		{
			// Template Blueprints use display-style names ("Apply Damage", "Set Bar Color").
			Func = Target->FindFunction(FName(*FName::NameToDisplayString(FuncName.ToString(), false)));
		}
		if (!Func)
		{
			return false;
		}

		uint8* Params = static_cast<uint8*>(FMemory_Alloca(FMath::Max<int32>(Func->ParmsSize, 1)));
		FMemory::Memzero(Params, Func->ParmsSize);

		TArray<FProperty*> Inputs;
		for (TFieldIterator<FProperty> It(Func); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->InitializeValue_InContainer(Params);
			const bool bIsOutput = It->HasAnyPropertyFlags(CPF_ReturnParm) ||
				(It->HasAnyPropertyFlags(CPF_OutParm) && !It->HasAnyPropertyFlags(CPF_ReferenceParm));
			if (!bIsOutput)
			{
				Inputs.Add(*It);
			}
		}

		int32 Index = 0;
		for (const FBPArg& Arg : Args)
		{
			if (!Inputs.IsValidIndex(Index))
			{
				break;
			}
			FProperty* Prop = Inputs[Index++];
			void* Value = Prop->ContainerPtrToValuePtr<void>(Params);
			if (FDoubleProperty* D = CastField<FDoubleProperty>(Prop))
			{
				D->SetPropertyValue(Value, Arg.Number);
			}
			else if (FFloatProperty* F = CastField<FFloatProperty>(Prop))
			{
				F->SetPropertyValue(Value, static_cast<float>(Arg.Number));
			}
			else if (FIntProperty* I = CastField<FIntProperty>(Prop))
			{
				I->SetPropertyValue(Value, static_cast<int32>(Arg.Number));
			}
			else if (FBoolProperty* B = CastField<FBoolProperty>(Prop))
			{
				B->SetPropertyValue(Value, Arg.Bool);
			}
			else if (FNameProperty* N = CastField<FNameProperty>(Prop))
			{
				N->SetPropertyValue(Value, Arg.Name);
			}
			else if (FObjectPropertyBase* O = CastField<FObjectPropertyBase>(Prop))
			{
				O->SetObjectPropertyValue(Value, Arg.Object);
			}
			else if (FStructProperty* S = CastField<FStructProperty>(Prop))
			{
				if (S->Struct == TBaseStructure<FVector>::Get())
				{
					*static_cast<FVector*>(Value) = Arg.Vector;
				}
				else if (S->Struct == TBaseStructure<FLinearColor>::Get())
				{
					*static_cast<FLinearColor*>(Value) = Arg.Color;
				}
			}
		}

		Target->ProcessEvent(Func, Params);

		for (TFieldIterator<FProperty> It(Func); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->DestroyValue_InContainer(Params);
		}
		return true;
	}

	USceneComponent* FindSceneComponentByName(const AActor* Actor, const TCHAR* Name)
	{
		if (!Actor)
		{
			return nullptr;
		}
		TInlineComponentArray<USceneComponent*> Comps(Actor);
		for (USceneComponent* Comp : Comps)
		{
			if (Comp && Comp->GetName() == Name)
			{
				return Comp;
			}
		}
		return nullptr;
	}
}

#if WITH_EDITOR
// Editor helper: jedi.ImplementDamageable <BlueprintPath> <InterfaceClassPath>
static FAutoConsoleCommand GJediImplementInterfaceCmd(
	TEXT("jedi.ImplementInterface"),
	TEXT("Adds a Blueprint interface to a Blueprint asset and compiles it. Args: <BlueprintObjectPath> <InterfaceGeneratedClassPath>"),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		if (Args.Num() < 2)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImplementInterface: need <BlueprintPath> <InterfaceClassPath>"));
			return;
		}
		UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *Args[0]);
		UClass* Interface = LoadObject<UClass>(nullptr, *Args[1]);
		if (!BP || !Interface)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImplementInterface: failed to load %s / %s"), *Args[0], *Args[1]);
			return;
		}
		const bool bAdded = FBlueprintEditorUtils::ImplementNewInterface(BP, Interface->GetClassPathName());
		FKismetEditorUtilities::CompileBlueprint(BP);
		UE_LOG(LogTemp, Log, TEXT("jedi.ImplementInterface: %s -> %s added=%d"), *BP->GetName(), *Interface->GetName(), bAdded ? 1 : 0);
	}));
#endif

// Debug: jedi.CapeDebug -- logs where each cape bone and its physics body are relative to spine_05.
static FAutoConsoleCommand GJediCapeDebugCmd(
	TEXT("jedi.CapeDebug"),
	TEXT("Logs cape bone/body state for every Jedi in a game world."),
	FConsoleCommandDelegate::CreateLambda([]()
	{
		for (TObjectIterator<AJediCharacter> It; It; ++It)
		{
			AJediCharacter* J = *It;
			if (!IsValid(J) || !J->GetWorld() || !J->GetWorld()->IsGameWorld())
			{
				continue;
			}
			USkeletalMeshComponent* M = J->GetMesh();
			const FVector Spine = M->GetBoneLocation(TEXT("spine_05"));
			UE_LOG(LogTemp, Log, TEXT("CapeDebug %s: collision=%d constraints=%d spine_05=%s"), *J->GetName(),
				static_cast<int32>(M->GetCollisionEnabled()), M->Constraints.Num(), *Spine.ToCompactString());
			for (const TCHAR* Side : { TEXT("c"), TEXT("l") })
			{
				for (int32 i = 1; i <= 5; ++i)
				{
					const FName Bone(*FString::Printf(TEXT("cape_%s_%02d"), Side, i));
					const FBodyInstance* BI = M->GetBodyInstance(Bone);
					UE_LOG(LogTemp, Log, TEXT("CapeDebug   %s bone=%s body=%s sim=%d blend=%.2f"), *Bone.ToString(),
						*(M->GetBoneLocation(Bone) - Spine).ToCompactString(),
						BI ? *(BI->GetUnrealWorldTransform().GetLocation() - Spine).ToCompactString() : TEXT("none"),
						static_cast<int32>(M->IsSimulatingPhysics(Bone)), BI ? BI->PhysicsBlendWeight : -1.f);
				}
			}
		}
	}));

#if WITH_EDITOR
// Editor helper: jedi.FixCape <PhysicsAsset> <SkeletalMesh>
// Snaps every cape_* constraint frame to the skeleton (constraints made without a preview mesh
// default to identity frames, which collapses the whole chain onto spine_05), sets swing limits and
// keeps cape bodies from colliding with the rest of the body.
static FAutoConsoleCommand GJediFixCapeCmd(
	TEXT("jedi.FixCape"),
	TEXT("Fixes cape constraint frames/limits/collision in a physics asset."),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		UPhysicsAsset* PA = Args.Num() > 0 ? LoadObject<UPhysicsAsset>(nullptr, *Args[0]) : nullptr;
		USkeletalMesh* Mesh = Args.Num() > 1 ? LoadObject<USkeletalMesh>(nullptr, *Args[1]) : nullptr;
		if (!PA || !Mesh)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.FixCape: need <PhysicsAsset> <SkeletalMesh>"));
			return;
		}
		PA->Modify();
		PA->SetPreviewMesh(Mesh, true);
		int32 Fixed = 0;
		for (UPhysicsConstraintTemplate* CS : PA->ConstraintSetup)
		{
			FConstraintInstance& CI = CS->DefaultInstance;
			const FString Child = CI.GetChildBoneName().ToString();
			if (!Child.StartsWith(TEXT("cape_")))
			{
				continue;
			}
			CS->Modify();
			CI.SnapTransformsToDefault(EConstraintTransformComponentFlags::All, PA);
			const bool bFirst = Child.EndsWith(TEXT("_01"));
			CI.SetAngularSwing1Limit(EAngularConstraintMotion::ACM_Limited, bFirst ? 25.f : 32.f);
			CI.SetAngularSwing2Limit(EAngularConstraintMotion::ACM_Limited, bFirst ? 12.f : 16.f);
			CI.SetAngularTwistLimit(EAngularConstraintMotion::ACM_Limited, 5.f);
			CI.SetDisableCollision(true);
			CS->SetDefaultProfile(CI);
			++Fixed;
			const FTransform P = CI.GetRefFrame(EConstraintFrame::Frame2);
			UE_LOG(LogTemp, Log, TEXT("jedi.FixCape: %s -> %s parent frame %s"), *Child, *CI.GetParentBoneName().ToString(), *P.GetLocation().ToCompactString());
		}
		// Cape bodies only hang off their constraints: no contacts with the torso/legs or each other.
		int32 Disabled = 0;
		for (int32 A = 0; A < PA->SkeletalBodySetups.Num(); ++A)
		{
			if (!PA->SkeletalBodySetups[A]->BoneName.ToString().StartsWith(TEXT("cape_")))
			{
				continue;
			}
			for (int32 B = 0; B < PA->SkeletalBodySetups.Num(); ++B)
			{
				if (A != B)
				{
					PA->DisableCollision(A, B);
					++Disabled;
				}
			}
		}
		PA->MarkPackageDirty();
		UE_LOG(LogTemp, Log, TEXT("jedi.FixCape: %d constraints fixed, %d collision pairs disabled"), Fixed, Disabled);
	}));

// Editor helper: jedi.ImportSounds <DiskFolder> <ContentPath>   (e.g. C:/x/wav /Game/Jedi/Audio)
static FAutoConsoleCommand GJediImportSoundsCmd(
	TEXT("jedi.ImportSounds"),
	TEXT("Imports every .wav in a folder as SoundWave assets. Files with 'Loop' in the name are set to loop."),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		if (Args.Num() < 2)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImportSounds: need <DiskFolder> <ContentPath>"));
			return;
		}
		TArray<FString> Files;
		IFileManager::Get().FindFiles(Files, *FPaths::Combine(Args[0], TEXT("*.wav")), true, false);
		UClass* FactoryClass = nullptr;
		for (TObjectIterator<UClass> It; It; ++It)
		{
			if (It->IsChildOf(UFactory::StaticClass()) && !It->HasAnyClassFlags(CLASS_Abstract))
			{
				UFactory* CDO = It->GetDefaultObject<UFactory>();
				if (CDO->GetSupportedClass() == USoundWave::StaticClass() && CDO->bEditorImport && Files.Num() > 0
					&& CDO->FactoryCanImport(FPaths::Combine(Args[0], Files[0])))
				{
					FactoryClass = *It;
					break;
				}
			}
		}
		if (!FactoryClass)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImportSounds: no wav factory found (%d files)"), Files.Num());
			return;
		}
		for (const FString& File : Files)
		{
			const FString Base = FPaths::GetBaseFilename(File);
			const FString PackageName = Args[1] / Base;
			UPackage* Package = CreatePackage(*PackageName);
			UFactory* Factory = NewObject<UFactory>(GetTransientPackage(), FactoryClass);
			bool bCanceled = false;
			UObject* Asset = Factory->ImportObject(USoundWave::StaticClass(), Package, FName(*Base), RF_Public | RF_Standalone,
				FPaths::Combine(Args[0], File), nullptr, bCanceled);
			if (USoundWave* Wave = Cast<USoundWave>(Asset))
			{
				Wave->bLooping = Base.Contains(TEXT("Loop"));
				FAssetRegistryModule::AssetCreated(Wave);
				Package->MarkPackageDirty();
			}
			UE_LOG(LogTemp, Log, TEXT("jedi.ImportSounds: %s -> %s"), *File, Asset ? *Asset->GetPathName() : TEXT("FAILED"));
		}
	}));
#endif

#if WITH_EDITOR
// Editor helper: jedi.ImportTextures <DiskFolder> <ContentPath>
// Normal/ORM/Mask maps are imported linear (sRGB off) with the matching compression.
static FAutoConsoleCommand GJediImportTexturesCmd(
	TEXT("jedi.ImportTextures"),
	TEXT("Imports every .png in a folder as Texture2D assets (names containing Normal/ORM are set up as linear data)."),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		if (Args.Num() < 2)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImportTextures: need <DiskFolder> <ContentPath>"));
			return;
		}
		TArray<FString> Files;
		IFileManager::Get().FindFiles(Files, *FPaths::Combine(Args[0], TEXT("*.png")), true, false);
		UClass* FactoryClass = nullptr;
		for (TObjectIterator<UClass> It; It; ++It)
		{
			if (It->IsChildOf(UFactory::StaticClass()) && !It->HasAnyClassFlags(CLASS_Abstract))
			{
				UFactory* CDO = It->GetDefaultObject<UFactory>();
				if (CDO->bEditorImport && Files.Num() > 0 && CDO->GetSupportedClass() && CDO->GetSupportedClass()->IsChildOf(UTexture::StaticClass())
					&& CDO->FactoryCanImport(FPaths::Combine(Args[0], Files[0])))
				{
					FactoryClass = *It;
					break;
				}
			}
		}
		if (!FactoryClass)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImportTextures: no png factory found (%d files)"), Files.Num());
			return;
		}
		for (const FString& File : Files)
		{
			const FString Base = FPaths::GetBaseFilename(File);
			UPackage* Package = CreatePackage(*(Args[1] / Base));
			UFactory* Factory = NewObject<UFactory>(GetTransientPackage(), FactoryClass);
			bool bCanceled = false;
			UObject* Asset = Factory->ImportObject(UTexture2D::StaticClass(), Package, FName(*Base), RF_Public | RF_Standalone,
				FPaths::Combine(Args[0], File), nullptr, bCanceled);
			if (UTexture2D* Tex = Cast<UTexture2D>(Asset))
			{
				// Let any in-flight texture build finish before changing gamma/compression.
				Tex->PreEditChange(nullptr);
				if (Base.Contains(TEXT("Normal")))
				{
					Tex->SRGB = false;
					Tex->CompressionSettings = TC_Normalmap;
					Tex->LODGroup = TEXTUREGROUP_CharacterNormalMap;
				}
				else if (Base.Contains(TEXT("ORM")) || Base.Contains(TEXT("Mask")))
				{
					Tex->SRGB = false;
					Tex->CompressionSettings = TC_Masks;
					Tex->LODGroup = TEXTUREGROUP_CharacterSpecular;
				}
				else
				{
					Tex->LODGroup = TEXTUREGROUP_Character;
				}
				Tex->PostEditChange();
				FAssetRegistryModule::AssetCreated(Tex);
				Package->MarkPackageDirty();
			}
			UE_LOG(LogTemp, Log, TEXT("jedi.ImportTextures: %s -> %s"), *File, Asset ? *Asset->GetPathName() : TEXT("FAILED"));
		}
	}));
#endif

#if WITH_EDITOR
// Editor helper: jedi.ImportSkeletal <FbxFile> <ContentFolder> <AssetName> <SkeletonObjectPath>
// Imports a skeletal mesh onto an existing skeleton with FBX scene-unit conversion (metre FBX -> cm).
static FAutoConsoleCommand GJediImportSkeletalCmd(
	TEXT("jedi.ImportSkeletal"),
	TEXT("Imports an FBX skeletal mesh onto an existing skeleton, converting scene units to centimetres."),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		if (Args.Num() < 4)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImportSkeletal: need <FbxFile> <ContentFolder> <AssetName> <SkeletonPath>"));
			return;
		}
		USkeleton* Skeleton = LoadObject<USkeleton>(nullptr, *Args[3]);
		UFbxImportUI* UI = NewObject<UFbxImportUI>(GetTransientPackage());
		UI->bIsObjImport = false;
		UI->MeshTypeToImport = FBXIT_SkeletalMesh;
		UI->OriginalImportType = FBXIT_SkeletalMesh;
		UI->bImportAsSkeletal = true;
		UI->bImportMesh = true;
		UI->bImportAnimations = false;
		UI->bImportMaterials = false;
		UI->bImportTextures = false;
		UI->bCreatePhysicsAsset = false;
		UI->Skeleton = Skeleton;
		UI->bAutomatedImportShouldDetectType = false;
		UI->SkeletalMeshImportData->bConvertScene = true;
		UI->SkeletalMeshImportData->bConvertSceneUnit = true;
		UI->SkeletalMeshImportData->bUseT0AsRefPose = false;
		UI->SkeletalMeshImportData->bImportMeshesInBoneHierarchy = true;

		UAssetImportTask* Task = NewObject<UAssetImportTask>(GetTransientPackage());
		Task->AddToRoot();
		Task->Filename = Args[0];
		Task->DestinationPath = Args[1];
		Task->DestinationName = Args[2];
		Task->bAutomated = true;
		Task->bReplaceExisting = true;
		Task->bSave = false;
		Task->Options = UI;

		UFbxFactory* Factory = NewObject<UFbxFactory>(GetTransientPackage());
		Factory->AddToRoot();
		Factory->SetAssetImportTask(Task);
		Factory->SetDetectImportTypeOnImport(false);

		UPackage* Package = CreatePackage(*(Args[1] / Args[2]));
		bool bCanceled = false;
		UObject* Asset = Factory->ImportObject(USkeletalMesh::StaticClass(), Package, FName(*Args[2]), RF_Public | RF_Standalone,
			Args[0], nullptr, bCanceled);
		Factory->RemoveFromRoot();
		Task->RemoveFromRoot();
		if (Asset)
		{
			FAssetRegistryModule::AssetCreated(Asset);
			Package->MarkPackageDirty();
		}
		UE_LOG(LogTemp, Log, TEXT("jedi.ImportSkeletal: %s -> %s"), *Args[0], Asset ? *Asset->GetPathName() : TEXT("FAILED"));
	}));
#endif

AJediCharacter::AJediCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(35.f, 90.f);
	GetMesh()->SetRelativeLocationAndRotation(FVector(0.f, 0.f, -90.f), FRotator(0.f, -90.f, 0.f));

	bUseControllerRotationYaw = false;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, TurnRate, 0.f);
	Move->MaxWalkSpeed = WalkSpeed;
	Move->JumpZVelocity = 620.f;
	Move->AirControl = 0.35f;
	Move->MaxAcceleration = 2400.f;
	Move->BrakingDecelerationWalking = 2048.f;
	Move->GravityScale = 1.4f;
	JumpMaxCount = 1; // the second jump is the custom Force jump

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->SetRelativeLocation(FVector(0.f, 0.f, 60.f));
	CameraBoom->TargetArmLength = CameraDistance;
	CameraBoom->SocketOffset = FVector(0.f, ShoulderOffset, 20.f);
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 12.f;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	LifeBar = CreateDefaultSubobject<UWidgetComponent>(TEXT("LifeBar"));
	LifeBar->SetupAttachment(RootComponent);
	LifeBar->SetRelativeLocation(FVector(0.f, 0.f, 30.f));
	LifeBar->SetWidgetSpace(EWidgetSpace::Screen);
	LifeBar->SetDrawSize(FVector2D(300.f, 50.f));

	ForceBar = CreateDefaultSubobject<UWidgetComponent>(TEXT("ForceBar"));
	ForceBar->SetupAttachment(RootComponent);
	ForceBar->SetRelativeLocation(FVector(0.f, 0.f, 30.f));
	ForceBar->SetWidgetSpace(EWidgetSpace::Screen);
	ForceBar->SetDrawSize(FVector2D(300.f, 40.f));
	ForceBar->SetPivot(FVector2D(0.5f, -0.35f));

	SaberTrail = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("SaberTrail"));
	SaberTrail->SetupAttachment(RootComponent);
	SaberTrail->SetUsingAbsoluteLocation(true);
	SaberTrail->SetUsingAbsoluteRotation(true);
	SaberTrail->SetUsingAbsoluteScale(true);
	SaberTrail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SaberTrail->SetCastShadow(false);
	SaberTrail->bUseAsyncCooking = true;

	Tags.Add(TEXT("Player"));
}

void AJediCharacter::BeginPlay()
{
	Super::BeginPlay();

	CurrentHP = MaxHP;
	ForcePower = MaxForce;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.f, TurnRate, 0.f);
	bUseControllerRotationYaw = false;
	BaseMeshRotation = GetMesh()->GetRelativeRotation().Quaternion();
	LastYaw = GetActorRotation().Yaw;
	if (TrailMaterial)
	{
		SaberTrail->SetMaterial(0, TrailMaterial);
	}
	SavedFriction = GetCharacterMovement()->GroundFriction;
	SavedBraking = GetCharacterMovement()->BrakingDecelerationWalking;
	SavedGravity = GetCharacterMovement()->GravityScale;
	CameraBoom->TargetArmLength = CameraDistance;
	CameraBoom->SocketOffset = FVector(0.f, ShoulderOffset, 20.f);
	FollowCamera->SetFieldOfView(BaseFOV);
	TargetFOV = BaseFOV;

	if (BarWidgetClass)
	{
		for (UWidgetComponent* Bar : { LifeBar.Get(), ForceBar.Get() })
		{
			Bar->SetWidgetClass(BarWidgetClass);
			Bar->InitWidget();
		}
		LifeWidget = LifeBar->GetUserWidgetObject();
		ForceWidget = ForceBar->GetUserWidgetObject();
		CallBP(LifeWidget.Get(), TEXT("SetBarColor"), { FLinearColor(0.f, 0.6f, 0.f, 1.f) });
		CallBP(ForceWidget.Get(), TEXT("SetBarColor"), { FLinearColor(0.08f, 0.4f, 1.f, 1.f) });
	}

	if (Styles.Num() > 0)
	{
		SetSaberStyle(0);
	}
	else if (SaberClass)
	{
		SpawnSabers(SaberClass, nullptr, NAME_None);
		if (Saber)
		{
			PlaySoundAt(IgniteSound, Saber->GetActorLocation(), 0.8f);
		}
	}
	UpdateBars();
	EnableCapePhysics();
}

void AJediCharacter::EnableCapePhysics()
{
	USkeletalMeshComponent* M = GetMesh();
	if (!M || bDead)
	{
		return;
	}
	bool bAny = false;
	for (const TCHAR* Root : { TEXT("cape_l_01"), TEXT("cape_c_01"), TEXT("cape_r_01") })
	{
		if (M->GetBoneIndex(Root) != INDEX_NONE && M->GetBodyInstance(Root))
		{
			if (!bAny)
			{
				// Bodies need physics collision to simulate; ignore pawns so the cape never shoves anyone.
				M->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
				M->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
				M->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
				bAny = true;
			}
			M->SetAllBodiesBelowSimulatePhysics(Root, true, true);
			M->SetAllBodiesBelowPhysicsBlendWeight(Root, 1.f, false, true);
			const int32 RootIndex = M->GetBoneIndex(Root);
			for (int32 B = 0; B < M->GetNumBones(); ++B)
			{
				if (B != RootIndex && !M->BoneIsChildOf(M->GetBoneName(B), Root))
				{
					continue;
				}
				if (FBodyInstance* BI = M->GetBodyInstance(M->GetBoneName(B)))
				{
					BI->SetResponseToAllChannels(ECR_Ignore);
					BI->LinearDamping = 1.0f;
					BI->AngularDamping = 2.5f;
					BI->UpdateDampingProperties();
				}
			}
		}
	}
}

void AJediCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		if (Held)
		{
			Held->Destroy();
		}
	}
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearAllTimersForObject(this);
		if (UGameplayStatics::GetGlobalTimeDilation(this) < 1.f)
		{
			UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
		}
	}
	Super::EndPlay(EndPlayReason);
}

// ---------------------------------------------------------------- input

void AJediCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		return;
	}
	auto Bind = [Input, this](UInputAction* Action, ETriggerEvent Event, void (AJediCharacter::*Func)())
	{
		if (Action)
		{
			Input->BindAction(Action, Event, this, Func);
		}
	};
	if (MoveAction) Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AJediCharacter::OnMove);
	if (LookAction) Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AJediCharacter::OnLook);
	if (MouseLookAction) Input->BindAction(MouseLookAction, ETriggerEvent::Triggered, this, &AJediCharacter::OnLook);
	Bind(JumpAction, ETriggerEvent::Started, &AJediCharacter::JediJump);
	Bind(JumpAction, ETriggerEvent::Completed, &ACharacter::StopJumping);
	Bind(AttackAction, ETriggerEvent::Started, &AJediCharacter::SaberAttack);
	Bind(BlockAction, ETriggerEvent::Started, &AJediCharacter::BlockStart);
	Bind(BlockAction, ETriggerEvent::Completed, &AJediCharacter::BlockStop);
	Bind(BlockAction, ETriggerEvent::Canceled, &AJediCharacter::BlockStop);
	Bind(ForcePushAction, ETriggerEvent::Started, &AJediCharacter::ForcePush);
	Bind(ForcePullAction, ETriggerEvent::Started, &AJediCharacter::ForcePull);
	Bind(ForceLightningAction, ETriggerEvent::Started, &AJediCharacter::LightningStart);
	Bind(ForceLightningAction, ETriggerEvent::Completed, &AJediCharacter::LightningStop);
	Bind(ForceLightningAction, ETriggerEvent::Canceled, &AJediCharacter::LightningStop);
	Bind(DashAction, ETriggerEvent::Started, &AJediCharacter::ForceDash);
	Bind(SaberToggleAction, ETriggerEvent::Started, &AJediCharacter::SaberToggle);
	Bind(CameraSideAction, ETriggerEvent::Started, &AJediCharacter::ToggleCameraSide);
	Bind(SaberStyleAction, ETriggerEvent::Started, &AJediCharacter::CycleSaberStyle);
	Bind(StormAction, ETriggerEvent::Started, &AJediCharacter::ForceStorm);
}

void AJediCharacter::OnMove(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	if (!Controller || bDead)
	{
		return;
	}
	const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
	AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::X), Axis.Y);
	AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Axis.X);
}

void AJediCharacter::OnLook(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddControllerYawInput(Axis.X);
	AddControllerPitchInput(Axis.Y);
}

// ---------------------------------------------------------------- helpers

float AJediCharacter::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

UAnimInstance* AJediCharacter::Anim() const
{
	return GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
}

void AJediCharacter::PlayAnim(UAnimSequenceBase* Seq, float Rate, int32 Loops, float BlendIn, float BlendOut)
{
	if (UAnimInstance* AI = Anim(); AI && Seq)
	{
		AI->PlaySlotAnimationAsDynamicMontage(Seq, TEXT("DefaultSlot"), BlendIn, BlendOut, Rate, Loops);
		StanceState = 0;
		StanceMontage = nullptr;
	}
}

void AJediCharacter::StopAnims(float BlendOut)
{
	if (UAnimInstance* AI = Anim())
	{
		AI->StopSlotAnimation(BlendOut, TEXT("DefaultSlot"));
	}
}

bool AJediCharacter::SpendForce(float Cost, bool bUseCooldown)
{
	if (bDead || ForcePower < Cost || (bUseCooldown && Now() - LastForceTime < ForceCooldown))
	{
		return false;
	}
	ForcePower -= Cost;
	if (bUseCooldown)
	{
		LastForceTime = Now();
	}
	return true;
}

FVector AJediCharacter::AimForwardFlat() const
{
	const FRotator Rot = Controller ? Controller->GetControlRotation() : GetActorRotation();
	return FRotator(0.f, Rot.Yaw, 0.f).Vector();
}

TArray<AActor*> AJediCharacter::CharactersInCone(float Range, float MinDot) const
{
	TArray<AActor*> Result;
	const FVector Loc = GetActorLocation();
	const FVector Fwd = AimForwardFlat();
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Other = *It;
		if (Other == this || !IsValid(Other))
		{
			continue;
		}
		const ATrainingRemote* Remote = Cast<ATrainingRemote>(Other);
		const IJediDamageable* Damageable = Cast<IJediDamageable>(Other);
		if (!Other->IsA(ACharacter::StaticClass()) && !(Remote && Remote->IsActive()) && !Damageable)
		{
			continue;
		}
		if (Damageable && !Damageable->IsJediTargetAlive())
		{
			continue;
		}
		const FVector Delta = Other->GetActorLocation() - Loc;
		if (Delta.Size() > Range)
		{
			continue;
		}
		if (FVector::DotProduct(Delta.GetSafeNormal2D(), Fwd) >= MinDot)
		{
			Result.Add(Other);
		}
	}
	return Result;
}

static ACharacter* NearestEnemy(const AJediCharacter* Self, float Range, float MinDotFromFacing)
{
	ACharacter* Best = nullptr;
	float BestDist = Range;
	const FVector Loc = Self->GetActorLocation();
	for (TActorIterator<ACharacter> It(Self->GetWorld()); It; ++It)
	{
		if (*It == Self || !IsValid(*It) || It->GetCharacterMovement()->MovementMode == MOVE_None)
		{
			continue;
		}
		if (const IJediDamageable* Damageable = Cast<IJediDamageable>(*It); Damageable && !Damageable->IsJediTargetAlive())
		{
			continue;
		}
		const FVector Delta = It->GetActorLocation() - Loc;
		const float Dist = Delta.Size();
		if (Dist < BestDist && FVector::DotProduct(Delta.GetSafeNormal2D(), Self->GetActorForwardVector()) >= MinDotFromFacing)
		{
			BestDist = Dist;
			Best = *It;
		}
	}
	return Best;
}

void AJediCharacter::DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
{
	if (Target != this)
	{
		DamageActor(Target, Damage, this, Location, Impulse, Kind);
	}
}

void AJediCharacter::DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
{
	if (!IsValid(Target))
	{
		return;
	}
	// Horde enemies, the boss and arena props take the full hit description.
	if (IJediDamageable* Damageable = Cast<IJediDamageable>(Target))
	{
		Damageable->ReceiveJediHit(Damage, Causer, Location, Impulse, Kind);
		return;
	}
	// Combat template actors implement BPI_Damageable::ApplyDamage (damage + knockback + hit FX).
	if (!CallBP(Target, TEXT("ApplyDamage"), { Damage, static_cast<UObject*>(Causer), Location, Impulse }))
	{
		APawn* CauserPawn = Cast<APawn>(Causer);
		UGameplayStatics::ApplyDamage(Target, Damage, CauserPawn ? CauserPawn->GetController() : nullptr, Causer, nullptr);
		if (UPrimitiveComponent* Prim = Cast<UPrimitiveComponent>(Target->GetRootComponent()); Prim && Prim->IsSimulatingPhysics())
		{
			Prim->AddImpulseAtLocation(Impulse * Prim->GetMass(), Location);
		}
	}
}

void AJediCharacter::NotifyDangerAhead()
{
	for (AActor* Other : CharactersInCone(350.f, 0.2f))
	{
		CallBP(Other, TEXT("NotifyDanger"), { GetActorLocation(), static_cast<UObject*>(this) });
	}
}

void AJediCharacter::SpawnWave(const FVector& Loc, const FRotator& Rot, float Scale)
{
	if (ForceWaveClass)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		GetWorld()->SpawnActor<AActor>(ForceWaveClass, FTransform(Rot, Loc, FVector(Scale)), Params);
	}
}

void AJediCharacter::SpawnBolt(const FVector& Start, const FVector& End)
{
	if (LightningBoltClass)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (AActor* Bolt = GetWorld()->SpawnActor<AActor>(LightningBoltClass, FTransform(Start), Params))
		{
			CallBP(Bolt, TEXT("Setup"), { Start, End });
		}
	}
}

void AJediCharacter::SlowMo(float Dilation, float Duration)
{
	UGameplayStatics::SetGlobalTimeDilation(this, Dilation);
	// Timer runs in dilated world time, so scale to get the intended real-time duration.
	GetWorldTimerManager().SetTimer(SlowMoTimer, [this]()
	{
		UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
	}, FMath::Max(Duration * Dilation, 0.001f), false);
}

void AJediCharacter::HitStop(AActor* Victim)
{
	if (HitStopTime <= 0.f)
	{
		return;
	}
	HitStopActors.Reset();
	HitStopActors.Add(this);
	HitStopActors.Add(Victim);
	for (const TWeakObjectPtr<AActor>& A : HitStopActors)
	{
		if (A.IsValid())
		{
			A->CustomTimeDilation = 0.05f;
		}
	}
	GetWorldTimerManager().SetTimer(HitStopTimer, [this]()
	{
		for (const TWeakObjectPtr<AActor>& A : HitStopActors)
		{
			if (A.IsValid())
			{
				A->CustomTimeDilation = 1.f;
			}
		}
	}, HitStopTime, false);
}

USoundBase* AJediCharacter::PickSound(USoundBase* Single, const TArray<TObjectPtr<USoundBase>>& Variants)
{
	return Variants.Num() > 0 ? Variants[FMath::RandRange(0, Variants.Num() - 1)].Get() : Single;
}

void AJediCharacter::PlaySoundAt(USoundBase* Sound, const FVector& Location, float Volume, float Pitch)
{
	if (Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, Location, Volume, Pitch);
	}
}

bool AJediCharacter::InSwingHitWindow() const
{
	if (!bAttacking || !Combo.IsValidIndex(ComboIndex))
	{
		return false;
	}
	const FSaberSwing& Swing = Combo[ComboIndex];
	const float T = (Now() - SwingStartTime) * FMath::Max(Swing.PlayRate, 0.05f);
	return T >= Swing.HitStart - 0.08f && T <= Swing.HitEnd + 0.05f;
}

void AJediCharacter::UpdateBars()
{
	// Screen-space widget components create their widget lazily; grab it once it exists.
	if (!LifeWidget.IsValid() && LifeBar)
	{
		LifeWidget = LifeBar->GetUserWidgetObject();
	}
	if (!ForceWidget.IsValid() && ForceBar)
	{
		ForceWidget = ForceBar->GetUserWidgetObject();
	}
	// Widgets finish constructing a frame or two after InitWidget, so keep the colours applied.
	const bool bColorOk = CallBP(LifeWidget.Get(), TEXT("SetBarColor"), { FLinearColor(0.f, 0.6f, 0.f, 1.f) });
	CallBP(ForceWidget.Get(), TEXT("SetBarColor"), { FLinearColor(0.08f, 0.4f, 1.f, 1.f) });
	static double LastLog = 0.0;
	if (!bColorOk && FPlatformTime::Seconds() - LastLog > 5.0)
	{
		LastLog = FPlatformTime::Seconds();
		UE_LOG(LogTemp, Warning, TEXT("JediCharacter: bar widget %s missing SetBarColor"), *GetNameSafe(LifeWidget.Get()));
	}
	CallBP(LifeWidget.Get(), TEXT("SetLifePercentage"), { MaxHP > 0.f ? CurrentHP / MaxHP : 0.f });
	CallBP(ForceWidget.Get(), TEXT("SetLifePercentage"), { GetForcePercent() });
}

// ---------------------------------------------------------------- tick

void AJediCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bDead)
	{
		return;
	}

	// Force meter
	if (bChanneling)
	{
		ForcePower = FMath::Max(0.f, ForcePower - LightningCost * DeltaSeconds);
		LightningAccum += DeltaSeconds;
		if (LightningAccum >= LightningInterval)
		{
			LightningAccum = 0.f;
			LightningZap();
		}
		if (ForcePower <= 0.f)
		{
			LightningStop();
		}
	}
	else if (!bBlocking)
	{
		ForcePower = FMath::Min(MaxForce, ForcePower + ForceRegen * DeltaSeconds);
	}

	if (bAttacking)
	{
		TickSwing();
	}

	// Soft lock while guarding: turn the guard towards the closest threat.
	if (bBlocking)
	{
		if (ACharacter* Threat = NearestEnemy(this, 450.f, -1.f))
		{
			const FRotator Want = (Threat->GetActorLocation() - GetActorLocation()).GetSafeNormal2D().Rotation();
			SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaSeconds, 14.f));
		}
	}

	// Saber hum: pitch and volume follow blade-tip speed.
	if (HumAudio && bSaberOn)
	{
		FVector HumBase, HumTip;
		if (GetBlade(HumBase, HumTip))
		{
			const float TipSpeed = bHaveHumTip && DeltaSeconds > 0.f ? FVector::Dist(HumTip, LastHumTip) / DeltaSeconds : 0.f;
			LastHumTip = HumTip;
			bHaveHumTip = true;
			const float Alpha = FMath::Clamp(TipSpeed / 1600.f, 0.f, 1.f);
			HumAudio->SetPitchMultiplier(FMath::Lerp(1.f, 1.35f, Alpha));
			const float Duck = Now() < HumDuckUntil ? 0.3f : 1.f;
			HumAudio->SetVolumeMultiplier(FMath::Lerp(HumIdleVolume, HumSwingVolume, Alpha) * Duck);
		}
	}

	SyncSecondaryBlades();
	TickLean(DeltaSeconds);
	TickStance();
	TickTrail();

	// FOV kick recovery (dash)
	if (FollowCamera)
	{
		const float FOV = FMath::FInterpTo(FollowCamera->FieldOfView, TargetFOV, DeltaSeconds, 8.f);
		FollowCamera->SetFieldOfView(FOV);
		TargetFOV = FMath::FInterpTo(TargetFOV, BaseFOV, DeltaSeconds, 6.f);
	}

	if (GetActorLocation().Z < KillZ)
	{
		Die();
	}
	UpdateBars();
}

// ---------------------------------------------------------------- saber

void AJediCharacter::SaberAttack()
{
	if (bDead || bBlocking || bDashing || Combo.Num() == 0)
	{
		return;
	}
	if (bChanneling)
	{
		LightningStop();
	}
	if (!bAttacking)
	{
		StartSwing(0);
		return;
	}
	// Buffer input once the current swing is under way.
	if (Now() - SwingStartTime > 0.12f)
	{
		bQueuedAttack = true;
	}
}

void AJediCharacter::StartSwing(int32 Index)
{
	const FSaberSwing& Swing = Combo[Index];
	bAttacking = true;
	bQueuedAttack = false;
	ComboIndex = Index;
	SwingStartTime = Now();
	SwingHits.Reset();
	bHaveLastBlade = false;

	const float Rate = FMath::Max(Swing.PlayRate, 0.05f);
	SwingLength = Swing.Anim ? Swing.Anim->GetPlayLength() / Rate : 0.6f;
	PlayAnim(Swing.Anim, Rate, 1, 0.06f, 0.18f);

	GetCharacterMovement()->MaxWalkSpeed = AttackMoveSpeed;
	GetCharacterMovement()->bOrientRotationToMovement = false;
	// No target: swing where the player is steering, else where the camera looks.
	FVector LungeDir = GetLastMovementInputVector().IsNearlyZero() ? AimForwardFlat() : GetLastMovementInputVector().GetSafeNormal2D();
	ACharacter* SoftTarget = NearestEnemy(this, 350.f, -1.f);
	UE_LOG(LogTemp, Log, TEXT("Jedi: SWING %d target=%s dist=%.0f"), Index, *GetNameSafe(SoftTarget),
		SoftTarget ? FVector::Dist(SoftTarget->GetActorLocation(), GetActorLocation()) : -1.f);
	if (ACharacter* Target = SoftTarget)
	{
		LungeDir = (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
	}
	FaceDirection(LungeDir);
	if (!GetCharacterMovement()->IsFalling())
	{
		LaunchCharacter(LungeDir * Swing.Lunge, true, false);
	}
	NotifyDangerAhead();
	if (bSaberOn && SwingSounds.Num() > 0 && Saber)
	{
		SwingAudio = UGameplayStatics::SpawnSoundAttached(SwingSounds[Index % SwingSounds.Num()], Saber->GetRootComponent(), NAME_None, FVector(0.f, 0.f, 60.f),
			EAttachLocation::KeepRelativeOffset, true, 0.9f, FMath::FRandRange(0.94f, 1.06f));
	}
}

void AJediCharacter::EndSwing()
{
	UE_LOG(LogTemp, Log, TEXT("Jedi: END SWING %d after %.2fs"), ComboIndex, Now() - SwingStartTime);
	bAttacking = false;
	bQueuedAttack = false;
	bHaveLastBlade = false;
	if (!bBlocking)
	{
		GetCharacterMovement()->bOrientRotationToMovement = true;
	}
	if (!bBlocking && !bChanneling)
	{
		GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	}
}

bool AJediCharacter::GetBlade(FVector& OutBase, FVector& OutTip) const
{
	const USceneComponent* Base = FindSceneComponentByName(Saber, TEXT("BladeRoot"));
	const USceneComponent* Tip = FindSceneComponentByName(Saber, TEXT("BladeTip"));
	if (!Base || !Tip)
	{
		return false;
	}
	OutBase = Base->GetComponentLocation();
	// BladeTip is scaled with the blade ignition; use its world location.
	OutTip = Tip->GetComponentLocation();
	return true;
}

int32 AJediCharacter::GetBlades(TArray<FVector>& OutBases, TArray<FVector>& OutTips) const
{
	OutBases.Reset();
	OutTips.Reset();
	for (const AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		for (const TCHAR* Suffix : { TEXT(""), TEXT("2") })
		{
			const USceneComponent* Base = FindSceneComponentByName(Held, *FString::Printf(TEXT("BladeRoot%s"), Suffix));
			const USceneComponent* Tip = FindSceneComponentByName(Held, *FString::Printf(TEXT("BladeTip%s"), Suffix));
			if (Base && Tip)
			{
				OutBases.Add(Base->GetComponentLocation());
				OutTips.Add(Tip->GetComponentLocation());
			}
		}
	}
	return OutBases.Num();
}

void AJediCharacter::SyncSecondaryBlades()
{
	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		USceneComponent* Main = FindSceneComponentByName(Held, TEXT("BladeRoot"));
		USceneComponent* Second = FindSceneComponentByName(Held, TEXT("BladeRoot2"));
		if (Main && Second)
		{
			Second->SetRelativeScale3D(Main->GetRelativeScale3D());
			if (Second->IsVisible() != Main->IsVisible())
			{
				Second->SetVisibility(Main->IsVisible(), true);
			}
		}
	}
}

FTransform AJediCharacter::MirroredOffhandGrip(FName OffhandSocket) const
{
	const USkeletalMesh* SK = GetMesh() ? GetMesh()->GetSkeletalMeshAsset() : nullptr;
	if (!SK)
	{
		return FTransform::Identity;
	}
	const FReferenceSkeleton& Ref = SK->GetRefSkeleton();
	auto BoneRefCS = [&Ref](FName Bone)
	{
		FTransform T = FTransform::Identity;
		for (int32 B = Ref.FindBoneIndex(Bone); B != INDEX_NONE; B = Ref.GetParentIndex(B))
		{
			T = T * Ref.GetRefBonePose()[B];
		}
		return T;
	};
	auto SocketRefCS = [&](FName Name)
	{
		if (const USkeletalMeshSocket* Socket = SK->FindSocket(Name))
		{
			return Socket->GetSocketLocalTransform() * BoneRefCS(Socket->BoneName);
		}
		return BoneRefCS(Name);
	};
	// Right-hand grip in component space, mirrored across the body's left/right plane
	// (mesh X for the UE mannequin skeleton, which faces +Y), then expressed relative to the left hand.
	const FTransform RightCS = FTransform(GripRot, GripLoc) * SocketRefCS(SaberSocket);
	FVector P = RightCS.GetLocation();
	P.X = -P.X;
	const FQuat Q = RightCS.GetRotation();
	const FTransform LeftCS(FQuat(Q.X, -Q.Y, -Q.Z, Q.W), P);
	return LeftCS.GetRelativeTransform(SocketRefCS(OffhandSocket));
}

void AJediCharacter::SpawnSabers(TSubclassOf<AActor> MainClass, TSubclassOf<AActor> OffhandClass, FName OffhandSocket)
{
	for (AActor* Old : { Saber.Get(), OffhandSaber.Get() })
	{
		if (Old)
		{
			Old->Destroy(); // also takes the hum/swing audio attached to it
		}
	}
	Saber = nullptr;
	OffhandSaber = nullptr;
	HumAudio = nullptr;
	SwingAudio = nullptr;

	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	auto SpawnHeld = [&](TSubclassOf<AActor> Class, FName Socket, const FTransform& Grip) -> AActor*
	{
		AActor* Held = Class ? GetWorld()->SpawnActor<AActor>(Class, GetActorTransform(), Params) : nullptr;
		if (Held)
		{
			Held->AttachToComponent(GetMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, Socket);
			Held->SetActorRelativeTransform(Grip);
			if (!bSaberOn)
			{
				CallBP(Held, TEXT("Retract"));
			}
		}
		return Held;
	};
	Saber = SpawnHeld(MainClass, SaberSocket, FTransform(GripRot, GripLoc));
	if (OffhandClass)
	{
		const FTransform OffGrip = MirroredOffhandGrip(OffhandSocket);
		OffhandSaber = SpawnHeld(OffhandClass, OffhandSocket, OffGrip);
		UE_LOG(LogTemp, Log, TEXT("Jedi: offhand grip on %s loc %s rot %s"), *OffhandSocket.ToString(),
			*OffGrip.GetLocation().ToCompactString(), *OffGrip.Rotator().ToCompactString());
	}
	if (Saber && HumSound)
	{
		HumAudio = UGameplayStatics::SpawnSoundAttached(HumSound, Saber->GetRootComponent(), NAME_None, FVector(0.f, 0.f, 50.f),
			EAttachLocation::KeepRelativeOffset, true, bSaberOn ? HumIdleVolume : 0.f, 1.f, 0.f, nullptr, nullptr, false);
	}
	bHaveLastBlade = false;
	LastBladeBases.Reset();
	LastBladeTips.Reset();
	BladeTrails.Reset();
	if (SaberTrail)
	{
		SaberTrail->ClearAllMeshSections();
	}
}

void AJediCharacter::HealBy(float Amount)
{
	if (!bDead)
	{
		CurrentHP = FMath::Min(MaxHP, CurrentHP + Amount);
		UpdateBars();
	}
}

void AJediCharacter::RestoreForce(float Amount)
{
	if (!bDead)
	{
		ForcePower = FMath::Min(MaxForce, ForcePower + Amount);
		UpdateBars();
	}
}

void AJediCharacter::AddSurge(float Amount)
{
	if (bDead || bStorming)
	{
		return;
	}
	Surge = FMath::Clamp(Surge + Amount, 0.f, SurgeMax);
	if (Surge >= SurgeMax && !bSurgeAnnounced)
	{
		bSurgeAnnounced = true;
		if (AHordeDirector* Director = AHordeDirector::Get(this))
		{
			Director->Announce(TEXT("FORCE STORM READY"), 2.f, FLinearColor(0.35f, 0.75f, 1.f));
		}
	}
}

void AJediCharacter::RegisterComboHit()
{
	const float T = Now();
	if (T - ComboLastTime > ComboWindow)
	{
		ComboHits = 0;
	}
	++ComboHits;
	ComboLastTime = T;
	MaxCombo = FMath::Max(MaxCombo, ComboHits);
	AddSurge(SurgePerHit);
}

int32 AJediCharacter::GetComboHits() const
{
	return Now() - ComboLastTime <= ComboWindow ? ComboHits : 0;
}

void AJediCharacter::ForceStorm()
{
	if (bDead || bStorming || Surge < SurgeMax)
	{
		return;
	}
	Surge = 0.f;
	bSurgeAnnounced = false;
	bStorming = true;
	if (bAttacking) { EndSwing(); }
	if (bBlocking) { BlockStop(); }
	if (bChanneling) { LightningStop(); }
	PlayAnim(StormAnim ? StormAnim.Get() : PushAnim.Get(), 0.8f, 1, 0.08f, 0.3f);
	LaunchCharacter(FVector(0.f, 0.f, 520.f), false, true);
	if (AHordeDirector* Director = AHordeDirector::Get(this))
	{
		Director->Announce(TEXT("FORCE STORM!"), 1.8f, FLinearColor(0.45f, 0.8f, 1.f));
		Director->AddHype(20.f);
	}
	SlowMo(0.35f, 0.45f);
	FTimerHandle First, Second, Done;
	GetWorldTimerManager().SetTimer(First, FTimerDelegate::CreateWeakLambda(this, [this]() { StormBlast(1.f); }), 0.3f, false);
	GetWorldTimerManager().SetTimer(Second, FTimerDelegate::CreateWeakLambda(this, [this]() { StormBlast(1.35f); }), 0.7f, false);
	GetWorldTimerManager().SetTimer(Done, FTimerDelegate::CreateWeakLambda(this, [this]() { bStorming = false; }), 1.3f, false);
}

void AJediCharacter::StormBlast(float RadiusScale)
{
	if (bDead)
	{
		return;
	}
	const FVector Loc = GetActorLocation();
	const float Radius = StormRadius * RadiusScale;
	for (int32 i = 0; i < 8; ++i)
	{
		const FVector Dir = FRotator(0.f, i * 45.f + RadiusScale * 20.f, 0.f).Vector();
		SpawnWave(Loc + Dir * 120.f - FVector(0.f, 0.f, 60.f), Dir.Rotation(), 1.6f * RadiusScale);
	}
	PlaySoundAt(PushSound, Loc, 1.f, 0.65f);
	if (HitShake)
	{
		UGameplayStatics::PlayWorldCameraShake(this, HitShake, Loc, 0.f, 3000.f, 1.f);
	}
	const FVector Hand = GetMesh()->GetSocketLocation(TEXT("hand_l"));
	int32 Bolts = 0;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Other = *It;
		if (Other == this || !IsValid(Other))
		{
			continue;
		}
		const IJediDamageable* Damageable = Cast<IJediDamageable>(Other);
		if (!Damageable && !Other->IsA(ACharacter::StaticClass()))
		{
			continue;
		}
		if (Damageable && !Damageable->IsJediTargetAlive())
		{
			continue;
		}
		const FVector Delta = Other->GetActorLocation() - Loc;
		const float Dist = Delta.Size();
		if (Dist > Radius)
		{
			continue;
		}
		const float Falloff = FMath::Lerp(1.f, 0.55f, Dist / Radius);
		const FVector Dir = Delta.GetSafeNormal2D();
		DealDamage(Other, StormDamage * Falloff, Other->GetActorLocation(), Dir * StormImpulse * Falloff + FVector::UpVector * StormLift, EJediHitKind::Storm);
		if (Bolts < 12)
		{
			SpawnBolt(Hand, Other->GetActorLocation());
			++Bolts;
		}
		RegisterComboHit();
	}
}

void AJediCharacter::CycleSaberStyle()
{
	if (Styles.Num() > 1)
	{
		SetSaberStyle((StyleIndex + 1) % Styles.Num());
	}
}

void AJediCharacter::SetSaberStyle(int32 Index)
{
	if (!Styles.IsValidIndex(Index) || bDead)
	{
		return;
	}
	if (bAttacking)
	{
		EndSwing();
	}
	if (bBlocking)
	{
		BlockStop();
	}
	StyleIndex = Index;
	const FSaberStyle& Style = Styles[Index];
	if (Style.Combo.Num() > 0)
	{
		Combo = Style.Combo;
	}
	if (Style.IdleAnim) { StanceIdleAnim = Style.IdleAnim; }
	if (Style.RunAnim) { StanceRunAnim = Style.RunAnim; }
	if (Style.BlockAnim) { BlockAnim = Style.BlockAnim; }
	StyleDamageMultiplier = Style.DamageMultiplier;
	ComboIndex = 0;

	// Restart the stance loop so the new idle/run takes over immediately.
	if (UAnimInstance* AI = Anim())
	{
		if (StanceMontage && AI->Montage_IsPlaying(StanceMontage))
		{
			AI->Montage_Stop(0.15f, StanceMontage);
		}
	}
	StanceMontage = nullptr;
	StanceState = 0;

	SpawnSabers(Style.MainSaberClass ? Style.MainSaberClass : SaberClass, Style.OffhandSaberClass, Style.OffhandSocket);
	if (bSaberOn && Saber)
	{
		PlaySoundAt(IgniteSound, Saber->GetActorLocation(), 0.8f);
	}
	UE_LOG(LogTemp, Log, TEXT("Jedi: STYLE %d %s"), Index, *Style.DisplayName.ToString());
	if (GEngine && IsPlayerControlled())
	{
		GEngine->AddOnScreenDebugMessage(0x5AB3, 2.5f, FColor(140, 200, 255), FString::Printf(TEXT("Saber style: %s"), *Style.DisplayName.ToString()));
	}
}

void AJediCharacter::TickSwing()
{
	const FSaberSwing& Swing = Combo[ComboIndex];
	const float Rate = FMath::Max(Swing.PlayRate, 0.05f);
	const float T = (Now() - SwingStartTime) * Rate; // time in animation seconds
	const float TPrev = T - GetWorld()->GetDeltaSeconds() * Rate;

	// Track the blade every tick; sweep whenever this frame's interval overlaps the damage window,
	// so hits still land at low frame rates.
	{
		TArray<FVector> Bases, Tips;
		const bool bHasSaber = bSaberOn && GetBlades(Bases, Tips) > 0;
		if (!bHasSaber)
		{
			// Unarmed fallback: short punch reach from the hand.
			Bases = { GetMesh()->GetSocketLocation(SaberSocket) };
			Tips = { Bases[0] + GetActorForwardVector() * 60.f };
		}
		if (bHaveLastBlade && LastBladeBases.Num() == Bases.Num() && TPrev <= Swing.HitEnd && T >= Swing.HitStart)
		{
			FCollisionObjectQueryParams Objects;
			Objects.AddObjectTypesToQuery(ECC_Pawn);
			Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
			Objects.AddObjectTypesToQuery(ECC_PhysicsBody);
			FCollisionQueryParams Query(SCENE_QUERY_STAT(SaberSweep), false, this);
			for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
			{
				if (Held)
				{
					Query.AddIgnoredActor(Held);
				}
			}

			const bool bRiposte = Now() < RiposteUntil;
			const float Damage = (bHasSaber ? SaberDamage : FistDamage) * Swing.DamageMultiplier * StyleDamageMultiplier * (bRiposte ? RiposteMultiplier : 1.f);
			const int32 Samples = 6;
			for (int32 BladeIdx = 0; BladeIdx < Bases.Num(); ++BladeIdx)
			for (int32 S = 0; S <= Samples; ++S)
			{
				const float A = static_cast<float>(S) / Samples;
				const FVector From = FMath::Lerp(LastBladeBases[BladeIdx], LastBladeTips[BladeIdx], A);
				const FVector To = FMath::Lerp(Bases[BladeIdx], Tips[BladeIdx], A);
				TArray<FHitResult> Hits;
				GetWorld()->SweepMultiByObjectType(Hits, From, To + (To - From).GetSafeNormal() * 0.1f, FQuat::Identity, Objects,
					FCollisionShape::MakeSphere(BladeTraceRadius), Query);
				for (const FHitResult& Hit : Hits)
				{
					AActor* Victim = Hit.GetActor();
					if (!Victim || Victim == this || Victim->IsA(GetClass()) || SwingHits.Contains(Victim))
					{
						continue;
					}
					if (Victim->GetOwner() && Victim->GetOwner()->IsA(ACharacter::StaticClass()))
					{
						continue; // other sabers/attached props
					}
					if (const IJediDamageable* DV = Cast<IJediDamageable>(Victim); DV && !DV->IsJediTargetAlive())
					{
						continue; // don't farm hits (and hit-stop) off ragdolls
					}
					SwingHits.Add(Victim);
					float HPBefore = -1.f;
					if (const IJediDamageable* DV = Cast<IJediDamageable>(Victim))
					{
						HPBefore = DV->GetJediHealth();
					}
					if (FProperty* HPProp = Victim->GetClass()->FindPropertyByName(TEXT("Current HP")))
					{
						if (const FDoubleProperty* D = CastField<FDoubleProperty>(HPProp)) { HPBefore = static_cast<float>(D->GetPropertyValue_InContainer(Victim)); }
						else if (const FFloatProperty* F = CastField<FFloatProperty>(HPProp)) { HPBefore = F->GetPropertyValue_InContainer(Victim); }
					}
					
					const FVector SwingDir = ((To - From).GetSafeNormal2D() + (Victim->GetActorLocation() - GetActorLocation()).GetSafeNormal2D()).GetSafeNormal();
					DealDamage(Victim, Damage, Hit.ImpactPoint, SwingDir * SaberKnockback + FVector::UpVector * SaberLift, EJediHitKind::Saber);
					RegisterComboHit();
					if (HitFX)
					{
						UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, Hit.ImpactPoint, SwingDir.Rotation());
					}
					if (HitShake)
					{
						UGameplayStatics::PlayWorldCameraShake(this, HitShake, Hit.ImpactPoint, 300.f, 1500.f);
					}
					UE_LOG(LogTemp, Log, TEXT("Jedi: SABER HIT %s dmg %.1f hpBefore %.1f swing %d"), *GetNameSafe(Victim), Damage, HPBefore, ComboIndex);
					if (bHasSaber)
					{
						// Every connecting blow gets a clear impact: duck the hum and cut the whoosh short under it.
						PlaySoundAt(PickSound(HitSound, HitSoundVariants), Hit.ImpactPoint, HitVolume, FMath::FRandRange(0.94f, 1.06f));
						HumDuckUntil = Now() + HitDuckTime;
						if (SwingAudio.IsValid())
						{
							SwingAudio->FadeOut(0.12f, 0.f);
						}
					}
					// Lethal saber blows sever whatever the blade connected with.
					ACharacter* VictimChar = Cast<ACharacter>(Victim);
					if (bDecapitation && bHasSaber && VictimChar && HPBefore > 0.f && HPBefore - Damage <= 0.f && FMath::FRand() <= DecapChance)
					{
						// Where did the blade cross the body? Closest point on this frame's blade sweep.
						const FVector BodyCenter = VictimChar->GetActorLocation();
						const FVector CutPoint = FMath::ClosestPointOnSegment(Hit.ImpactPoint, From, To);
						const FVector Probe = FVector::Dist(CutPoint, BodyCenter) < FVector::Dist(Hit.ImpactPoint, BodyCenter) ? CutPoint : FVector(Hit.ImpactPoint);
						const FName CutBone = ASeveredLimb::ChooseCutBone(VictimChar->GetMesh(), Probe);
						if (ASeveredLimb::Sever(VictimChar, CutBone, SwingDir * 480.f, StumpMaterial))
						{
							UE_LOG(LogTemp, Log, TEXT("Jedi: SEVERED %s of %s"), *CutBone.ToString(), *GetNameSafe(VictimChar));
							PlaySoundAt(PickSound(ClashSound, ClashSoundVariants), Hit.ImpactPoint, 0.6f, 0.8f);
							SlowMo(0.25f, 0.4f);
						}
					}
					HitStop(Victim);
					if (bRiposte)
					{
						RiposteUntil = -1.f;
					}
				}
			}
		}
		LastBladeBases = Bases;
		LastBladeTips = Tips;
		bHaveLastBlade = true;
	}

	const float Elapsed = Now() - SwingStartTime;
	if (bQueuedAttack && T >= Swing.ChainTime)
	{
		StartSwing((ComboIndex + 1) % Combo.Num());
		return;
	}
	if (Elapsed >= SwingLength)
	{
		EndSwing();
	}
}

void AJediCharacter::SaberToggle()
{
	if (!Saber || bDead)
	{
		return;
	}
	bSaberOn = !bSaberOn;
	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		CallBP(Held, bSaberOn ? TEXT("Ignite") : TEXT("Retract"));
	}
	PlaySoundAt(bSaberOn ? IgniteSound.Get() : RetractSound.Get(), Saber->GetActorLocation(), 0.8f);
	if (HumAudio)
	{
		if (bSaberOn) { HumAudio->FadeIn(0.3f, 1.f); } else { HumAudio->FadeOut(0.35f, 0.f); }
	}
}

// ---------------------------------------------------------------- block / parry

void AJediCharacter::BlockStart()
{
	if (bDead || bDashing || !bSaberOn)
	{
		return;
	}
	if (bAttacking)
	{
		EndSwing();
	}
	if (bChanneling)
	{
		LightningStop();
	}
	bBlocking = true;
	BlockStartTime = Now();
	GetCharacterMovement()->bOrientRotationToMovement = false;
	FaceDirection(AimForwardFlat());
	GetCharacterMovement()->MaxWalkSpeed = BlockMoveSpeed;
	PlayAnim(BlockAnim, 1.f, 1000, 0.08f, 0.15f);
}

void AJediCharacter::BlockStop()
{
	if (!bBlocking)
	{
		return;
	}
	bBlocking = false;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	StopAnims(0.15f);
}

void AJediCharacter::Parry(AActor* Attacker)
{
	PlayAnim(ParryAnim ? ParryAnim.Get() : BlockHitAnim.Get(), 1.2f, 1, 0.03f, 0.1f);
	ForcePower = FMath::Min(MaxForce, ForcePower + ParryForceGain);
	RiposteUntil = Now() + RiposteWindow;

	if (IsValid(Attacker))
	{
		const FVector Away = (Attacker->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		// Zero-damage hit: interrupts their attack montage and knocks them back.
		DealDamage(Attacker, 0.f, Attacker->GetActorLocation(), Away * ParryStagger + FVector::UpVector * 200.f);
		if (HitFX)
		{
			const FVector Spark = GetActorLocation() + Away * 60.f + FVector(0.f, 0.f, 50.f);
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, Spark, Away.Rotation());
		}
	}
	if (HitShake)
	{
		UGameplayStatics::PlayWorldCameraShake(this, HitShake, GetActorLocation(), 300.f, 1500.f);
	}
	SlowMo(0.25f, 0.35f);

	// Return to guard after the flick if block is still held.
	FTimerHandle Back;
	GetWorldTimerManager().SetTimer(Back, [this]()
	{
		if (bBlocking)
		{
			PlayAnim(BlockAnim, 1.f, 1000, 0.1f, 0.15f);
		}
	}, 0.3f, false);
}

bool AJediCharacter::TryDefend(AActor* DamageCauser)
{
	if (bDashing && DamageCauser && DamageCauser->IsA(ACharacter::StaticClass()))
	{
		return true; // dash i-frames against melee
	}
	// Block / parry anything coming from in front of us.
	if (bBlocking && DamageCauser && DamageCauser != this)
	{
		const FVector ToAttacker = (DamageCauser->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		if (FVector::DotProduct(ToAttacker, GetActorForwardVector()) >= BlockAngleDot)
		{
			if (Now() - BlockStartTime <= ParryWindow)
			{
				UE_LOG(LogTemp, Log, TEXT("Jedi: PARRY vs %s"), *GetNameSafe(DamageCauser));
				Parry(DamageCauser);
				PlaySoundAt(PickSound(ClashSound, ClashSoundVariants), GetActorLocation() + ToAttacker * 60.f + FVector(0.f, 0.f, 50.f), 1.f, 1.1f);
				return true;
			}
			if (ForcePower >= BlockForceCost)
			{
				ForcePower -= BlockForceCost;
				PlaySoundAt(PickSound(ClashSound, ClashSoundVariants), GetActorLocation() + ToAttacker * 60.f + FVector(0.f, 0.f, 50.f), 0.8f, FMath::FRandRange(0.9f, 1.f));
				UE_LOG(LogTemp, Log, TEXT("Jedi: BLOCK vs %s (force %.0f)"), *GetNameSafe(DamageCauser), ForcePower);
				PlayAnim(BlockHitAnim ? BlockHitAnim.Get() : ParryAnim.Get(), 1.4f, 1, 0.03f, 0.1f);
				LaunchCharacter(-ToAttacker * 350.f, true, false);
				if (HitFX)
				{
					UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, GetActorLocation() + ToAttacker * 60.f + FVector(0.f, 0.f, 50.f), ToAttacker.Rotation());
				}
				FTimerHandle Back;
				GetWorldTimerManager().SetTimer(Back, [this]()
				{
					if (bBlocking)
					{
						PlayAnim(BlockAnim, 1.f, 1000, 0.1f, 0.15f);
					}
				}, 0.25f, false);
				return true;
			}
			// Guard broken: out of Force.
			BlockStop();
		}
	}

	return false;
}

void AJediCharacter::ReceiveTemplateDamage(float Damage, AActor* DamageCauser, FVector DamageLocation, FVector DamageImpulse)
{
	// Template melee traces report one hit per physics body; count one hit per attacker per swing.
	static TMap<TPair<TWeakObjectPtr<AActor>, TWeakObjectPtr<AActor>>, double> LastHitTimes;
	const TPair<TWeakObjectPtr<AActor>, TWeakObjectPtr<AActor>> Key(this, DamageCauser);
	if (const double* Last = LastHitTimes.Find(Key); Last && Now() - *Last < 0.35)
	{
		return;
	}
	LastHitTimes.Add(Key, Now());

	if (bDead || bStorming || !CanBeDamaged() || TryDefend(DamageCauser))
	{
		return;
	}
	// Knockback like the template character, then the regular damage path (HP, hit react, death).
	GetCharacterMovement()->AddImpulse(DamageImpulse, true);
	PlaySoundAt(PickSound(HitSound, HitSoundVariants), DamageLocation, 0.8f, 0.8f);
	if (HitFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, DamageLocation, DamageImpulse.Rotation());
	}
	bSkipDefence = true;
	UGameplayStatics::ApplyDamage(this, Damage, nullptr, DamageCauser, nullptr);
	bSkipDefence = false;
}

float AJediCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bDead || bStorming || !CanBeDamaged())
	{
		return 0.f;
	}

	if (!bSkipDefence && TryDefend(DamageCauser))
	{
		return 0.f;
	}

	const float Applied = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	UE_LOG(LogTemp, Log, TEXT("Jedi: HIT by %s for %.2f (blocking=%d)"), *GetNameSafe(DamageCauser), DamageAmount, bBlocking ? 1 : 0);
	CurrentHP = FMath::Max(0.f, CurrentHP - DamageAmount);
	if (HurtShake)
	{
		UGameplayStatics::PlayWorldCameraShake(this, HurtShake, GetActorLocation(), 0.f, 500.f);
	}
	if (CurrentHP <= 0.f)
	{
		Die();
		return Applied;
	}

	// Hit reaction: partial ragdoll on the upper body for a moment. Ranged chip damage doesn't cancel swings.
	const bool bRangedHit = DamageCauser && DamageCauser->IsA(ATrainingRemote::StaticClass());
	if (bAttacking && !bRangedHit)
	{
		EndSwing();
		StopAnims(0.1f);
	}
	GetMesh()->SetAllBodiesBelowSimulatePhysics(TEXT("spine_01"), true, true);
	GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(TEXT("spine_01"), 0.4f, false, true);
	GetWorldTimerManager().SetTimer(HitReactTimer, this, &AJediCharacter::ResetHitReaction, 0.35f, false);
	UpdateBars();
	return Applied;
}

void AJediCharacter::ResetHitReaction()
{
	if (!bDead && GetMesh())
	{
		GetMesh()->SetAllBodiesBelowSimulatePhysics(TEXT("spine_01"), false, true);
		GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(TEXT("spine_01"), 0.f, false, true);
		EnableCapePhysics();
	}
}

void AJediCharacter::Die()
{
	if (bDead)
	{
		return;
	}
	bDead = true;
	bUseControllerRotationYaw = false;
	CurrentHP = 0.f;
	bChanneling = false;
	bBlocking = false;
	bAttacking = false;
	UpdateBars();
	GetWorldTimerManager().ClearTimer(HitReactTimer);

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		DisableInput(PC);
	}
	LifeBar->SetHiddenInGame(true);
	ForceBar->SetHiddenInGame(true);
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetMesh()->SetCollisionProfileName(TEXT("Ragdoll"));
	GetMesh()->SetSimulatePhysics(true);
	CameraBoom->TargetArmLength = 450.f;
	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		CallBP(Held, TEXT("Retract"));
	}
	// The Combat player controller respawns the pawn when it is destroyed.
	SetLifeSpan(RespawnTime);
}

void AJediCharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);
	bAirDashUsed = false;
	bDoubleJumpUsed = false;
}

// ---------------------------------------------------------------- movement abilities

void AJediCharacter::JediJump()
{
	if (bDead || bBlocking)
	{
		return;
	}
	UCharacterMovementComponent* Move = GetCharacterMovement();
	if (!Move->IsFalling())
	{
		Jump();
		return;
	}
	if (bDoubleJumpUsed || !SpendForce(DoubleJumpCost, false))
	{
		return;
	}
	bDoubleJumpUsed = true;
	const FVector Vel = Move->Velocity;
	LaunchCharacter(FVector(Vel.X, Vel.Y, DoubleJumpZ), true, true);
	PlayAnim(FlipAnim, 1.1f, 1, 0.05f, 0.2f);
	PlaySoundAt(PushSound, GetActorLocation(), 0.45f, 1.6f);
	SpawnWave(GetActorLocation() - FVector(0.f, 0.f, 80.f), FRotator(-90.f, 0.f, 0.f), 0.6f);
}

void AJediCharacter::ForceDash()
{
	if (bDead || bDashing || Now() - LastDashTime < DashCooldown)
	{
		return;
	}
	UCharacterMovementComponent* Move = GetCharacterMovement();
	const bool bInAir = Move->IsFalling();
	if (bInAir && bAirDashUsed)
	{
		return;
	}
	if (!SpendForce(DashCost, false))
	{
		return;
	}
	if (bBlocking)
	{
		BlockStop();
	}
	if (bAttacking)
	{
		EndSwing();
	}

	FVector Dir = GetLastMovementInputVector().GetSafeNormal2D();
	if (Dir.IsNearlyZero())
	{
		Dir = AimForwardFlat();
	}
	bDashing = true;
	LastDashTime = Now();
	bAirDashUsed |= bInAir;

	Move->GroundFriction = 0.f;
	Move->BrakingDecelerationWalking = 0.f;
	Move->GravityScale = 0.f;
	LaunchCharacter(Dir * DashSpeed, true, true);
	PlayAnim(DashAnim, 1.f, 1, 0.04f, 0.15f);
	PlaySoundAt(SwingSounds.Num() > 0 ? SwingSounds[0].Get() : nullptr, GetActorLocation(), 0.8f, 0.6f);
	PlaySoundAt(PushSound, GetActorLocation(), 0.35f, 1.8f);
	SpawnWave(GetActorLocation() - Dir * 60.f, (-Dir).Rotation(), 0.45f);
	TargetFOV = BaseFOV + 14.f;
	GetWorldTimerManager().SetTimer(DashTimer, this, &AJediCharacter::EndDash, DashDuration, false);
}

void AJediCharacter::EndDash()
{
	bDashing = false;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->GroundFriction = SavedFriction;
	Move->BrakingDecelerationWalking = SavedBraking;
	Move->GravityScale = SavedGravity;
	Move->Velocity = Move->Velocity.GetClampedToMaxSize(WalkSpeed * 1.3f);
}

void AJediCharacter::ToggleCameraSide()
{
	bRightShoulder = !bRightShoulder;
	CameraBoom->SocketOffset.Y = bRightShoulder ? ShoulderOffset : -ShoulderOffset;
}

// ---------------------------------------------------------------- Force powers

void AJediCharacter::ForcePush()
{
	if (bBlocking || !SpendForce(PushCost, true))
	{
		return;
	}
	if (bAttacking)
	{
		EndSwing();
	}
	FaceDirection(AimForwardFlat());
	const FVector Loc = GetActorLocation();
	const FVector Fwd = AimForwardFlat();
	PlayAnim(PushAnim, 1.5f, 1, 0.06f, 0.25f);
	SpawnWave(Loc + Fwd * 90.f, Fwd.Rotation());
	if (HitShake)
	{
		UGameplayStatics::PlayWorldCameraShake(this, HitShake, Loc, 500.f, 1500.f);
	}
	PlaySoundAt(PushSound, Loc + Fwd * 100.f);
	for (AActor* Other : CharactersInCone(PushRange, 0.3f))
	{
		const FVector Dir = (Other->GetActorLocation() - Loc).GetSafeNormal2D();
		DealDamage(Other, PushDamage, Other->GetActorLocation(), Dir * PushImpulse + FVector::UpVector * PushLift, EJediHitKind::ForcePush);
	}
	// Physics props in the cone too.
	TArray<FOverlapResult> Overlaps;
	FCollisionObjectQueryParams Objects;
	Objects.AddObjectTypesToQuery(ECC_PhysicsBody);
	Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
	GetWorld()->OverlapMultiByObjectType(Overlaps, Loc, FQuat::Identity, Objects, FCollisionShape::MakeSphere(PushRange));
	for (const FOverlapResult& O : Overlaps)
	{
		UPrimitiveComponent* Prim = O.GetComponent();
		if (Prim && Prim->IsSimulatingPhysics() && !Prim->GetOwner()->IsA(ACharacter::StaticClass()) && !Cast<IJediDamageable>(Prim->GetOwner()))
		{
			const FVector Dir = (Prim->GetComponentLocation() - Loc).GetSafeNormal2D();
			if (FVector::DotProduct(Dir, Fwd) > 0.3f)
			{
				Prim->AddImpulse((Dir * PushImpulse + FVector::UpVector * PushLift) * 0.7f, NAME_None, true);
			}
		}
	}
	SlowMo(0.3f, 0.23f);
}

void AJediCharacter::ForcePull()
{
	if (bBlocking || bDead)
	{
		return;
	}
	const FVector Eye = GetActorLocation() + FVector(0.f, 0.f, 60.f);
	const FVector Aim = Controller ? Controller->GetControlRotation().Vector() : GetActorForwardVector();
	AActor* Best = nullptr;
	float BestScore = 0.9f;
	for (TActorIterator<ACharacter> It(GetWorld()); It; ++It)
	{
		if (*It == this)
		{
			continue;
		}
		if (const IJediDamageable* Damageable = Cast<IJediDamageable>(*It); Damageable && !Damageable->IsJediTargetAlive())
		{
			continue;
		}
		const FVector To = It->GetActorLocation() - Eye;
		const float Score = FVector::DotProduct(To.GetSafeNormal(), Aim);
		if (To.Size() < PullRange && Score > BestScore)
		{
			BestScore = Score;
			Best = *It;
		}
	}
	if (!Best || !SpendForce(PullCost, true))
	{
		return;
	}
	const FVector TargetLoc = Best->GetActorLocation();
	const FVector Dir = (GetActorLocation() - TargetLoc).GetSafeNormal2D();
	PlayAnim(PullAnim, 1.4f, 1, 0.06f, 0.25f);
	SpawnWave(TargetLoc, Dir.Rotation(), 0.5f);
	DealDamage(Best, PullDamage, TargetLoc, Dir * PullImpulse + FVector::UpVector * PullLift, EJediHitKind::ForcePull);
}

void AJediCharacter::LightningStart()
{
	if (bDead || bBlocking || ForcePower < 10.f)
	{
		return;
	}
	if (bAttacking)
	{
		EndSwing();
	}
	bChanneling = true;
	LightningAccum = LightningInterval;
	GetCharacterMovement()->MaxWalkSpeed = 170.f;
	PlayAnim(LightningAnim, 1.f, 100, 0.15f, 0.2f);
	if (LightningLoopSound && !LightningAudio)
	{
		LightningAudio = UGameplayStatics::SpawnSoundAttached(LightningLoopSound, GetMesh(), TEXT("hand_l"), FVector::ZeroVector,
			EAttachLocation::SnapToTarget, true, 0.8f, 1.f, 0.f, nullptr, nullptr, false);
	}
}

void AJediCharacter::LightningStop()
{
	if (!bChanneling)
	{
		return;
	}
	bChanneling = false;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	StopAnims(0.2f);
	if (LightningAudio)
	{
		LightningAudio->FadeOut(0.15f, 0.f);
		LightningAudio = nullptr;
	}
}

void AJediCharacter::LightningZap()
{
	const FVector Hand = GetMesh()->GetSocketLocation(TEXT("hand_l"));
	const FVector Fwd = AimForwardFlat();
	int32 Hits = 0;
	for (AActor* Other : CharactersInCone(LightningRange, 0.55f))
	{
		const FVector Target = Other->GetActorLocation() + FVector(0.f, 0.f, FMath::FRandRange(-30.f, 40.f));
		SpawnBolt(Hand, Target);
		const FVector Dir = (Other->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		DealDamage(Other, LightningDamage, Other->GetActorLocation(), Dir * 140.f + FVector::UpVector * 60.f, EJediHitKind::Lightning);
		++Hits;
	}
	if (Hits == 0)
	{
		for (int32 i = 0; i < 2; ++i)
		{
			SpawnBolt(Hand, Hand + Fwd * 450.f + FMath::VRand() * 160.f);
		}
	}
}

// ---------------------------------------------------------------- blaster deflection

bool AJediCharacter::TryDeflectBolt(ABlasterBolt* Bolt)
{
	if (!Bolt || bDead || !bSaberOn || Bolt->Shooter.Get() == this)
	{
		return false;
	}
	const bool bSwingDeflect = InSwingHitWindow();
	if (!bBlocking && !bSwingDeflect)
	{
		return false;
	}
	const FVector Incoming = -Bolt->GetDirection();
	if (FVector::DotProduct(Incoming.GetSafeNormal2D(), GetActorForwardVector()) < BlockAngleDot)
	{
		return false; // came from behind
	}

	const bool bPerfect = bSwingDeflect || (Now() - BlockStartTime <= ParryWindow);
	FVector Dir;
	AActor* Shooter = Bolt->Shooter.Get();
	if (bPerfect && IsValid(Shooter))
	{
		Dir = (Shooter->GetActorLocation() - Bolt->GetActorLocation()).GetSafeNormal();
	}
	else
	{
		const FVector Aim = Controller ? Controller->GetControlRotation().Vector() : GetActorForwardVector();
		Dir = FMath::VRandCone(Aim, FMath::DegreesToRadians(DeflectSpreadDegrees));
		ForcePower = FMath::Max(0.f, ForcePower - DeflectForceCost);
	}
	Bolt->Deflect(Dir, this, bPerfect ? 1.5f : 1.2f);
	UE_LOG(LogTemp, Log, TEXT("Jedi: DEFLECT%s"), bPerfect ? TEXT(" (perfect)") : TEXT(""));

	PlaySoundAt(DeflectSound, Bolt->GetActorLocation(), 1.f, FMath::FRandRange(0.95f, 1.1f));
	if (HitFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, HitFX, Bolt->GetActorLocation(), Dir.Rotation());
	}
	if (bBlocking && !bAttacking)
	{
		PlayAnim(BlockHitAnim ? BlockHitAnim.Get() : ParryAnim.Get(), 1.6f, 1, 0.02f, 0.1f);
		FTimerHandle Back;
		GetWorldTimerManager().SetTimer(Back, [this]()
		{
			if (bBlocking)
			{
				PlayAnim(BlockAnim, 1.f, 1000, 0.08f, 0.15f);
			}
		}, 0.2f, false);
	}
	return true;
}

// ---------------------------------------------------------------- fluid movement

void AJediCharacter::FaceDirection(const FVector& Dir)
{
	const FVector Flat = Dir.GetSafeNormal2D();
	if (!Flat.IsNearlyZero())
	{
		SetActorRotation(Flat.Rotation());
	}
}

void AJediCharacter::TickLean(float DeltaSeconds)
{
	USkeletalMeshComponent* M = GetMesh();
	if (!M || bDead || DeltaSeconds <= 0.f)
	{
		return;
	}
	// Bank into turns and lean forward with speed, like a sprinting duelist.
	const float Yaw = GetActorRotation().Yaw;
	const float YawRate = FMath::FindDeltaAngleDegrees(LastYaw, Yaw) / DeltaSeconds;
	LastYaw = Yaw;
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const float Speed01 = Move->IsMovingOnGround() ? FMath::Clamp(GetVelocity().Size2D() / FMath::Max(WalkSpeed, 1.f), 0.f, 1.3f) : 0.f;

	FRotator Want;
	Want.Pitch = -Speed01 * MaxLeanDegrees * 0.55f;
	Want.Roll = FMath::Clamp(YawRate * 0.02f * Speed01, -MaxLeanDegrees, MaxLeanDegrees);
	Want.Yaw = 0.f;
	if (bAttacking || bBlocking || bDashing)
	{
		Want = FRotator::ZeroRotator;
	}
	CurrentLean = FMath::RInterpTo(CurrentLean, Want, DeltaSeconds, 7.f);
	// Lean is applied in actor space around the feet (mesh origin).
	M->SetRelativeRotation(FQuat(CurrentLean) * BaseMeshRotation);
}

void AJediCharacter::TickStance()
{
	UAnimInstance* AI = Anim();
	if (!AI || bDead || !StanceIdleAnim)
	{
		return;
	}
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const bool bBusy = bAttacking || bBlocking || bChanneling || bDashing;
	int32 Want = 0;
	float Rate = 1.f;
	if (!bBusy && Move->IsMovingOnGround())
	{
		const float Speed = GetVelocity().Size2D();
		if (StanceRunAnim && Speed > WalkSpeed * 0.45f)
		{
			Want = 2;
			Rate = FMath::Clamp(Speed / FMath::Max(StanceRunReferenceSpeed, 1.f), 0.6f, 1.5f);
		}
		else if (Speed < 60.f)
		{
			Want = 1;
		}
		else
		{
			Want = 0; // slow walking: let the locomotion blueprint handle foot placement
		}
	}

	// Another montage took the slot (attack, parry, flip...)? Wait until it's done.
	if (StanceState == 0 && AI->IsAnyMontagePlaying() && !bBusy && Want != 0)
	{
		UAnimMontage* Active = AI->GetCurrentActiveMontage();
		if (Active && Active != StanceMontage && AI->Montage_GetPosition(Active) < Active->GetPlayLength() - 0.2f)
		{
			return;
		}
	}

	if (Want != StanceState)
	{
		if (Want == 0)
		{
			if (StanceMontage && AI->Montage_IsPlaying(StanceMontage))
			{
				AI->Montage_Stop(0.2f, StanceMontage);
			}
			StanceMontage = nullptr;
		}
		else
		{
			UAnimSequenceBase* Seq = Want == 2 ? StanceRunAnim.Get() : StanceIdleAnim.Get();
			StanceMontage = AI->PlaySlotAnimationAsDynamicMontage(Seq, TEXT("DefaultSlot"), 0.22f, 0.22f, Rate, 100000);
		}
		StanceState = Want;
	}
	else if (StanceState == 2 && StanceMontage)
	{
		AI->Montage_SetPlayRate(StanceMontage, Rate);
	}
}

void AJediCharacter::TickTrail()
{
	if (!SaberTrail)
	{
		return;
	}
	const float T = Now();
	TArray<FVector> Bases, Tips;
	const int32 NumBlades = (bSaberOn && !bDead) ? GetBlades(Bases, Tips) : 0;
	if (BladeTrails.Num() < NumBlades)
	{
		BladeTrails.SetNum(NumBlades);
	}
	// Blade colours for tinting, in GetBlades order (main, main blade 2, off-hand, off-hand blade 2).
	TArray<FLinearColor> BladeColors;
	for (const AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		for (const TCHAR* Suffix : { TEXT(""), TEXT("2") })
		{
			if (FindSceneComponentByName(Held, *FString::Printf(TEXT("BladeRoot%s"), Suffix)))
			{
				const UPointLightComponent* Light = Held ? Cast<UPointLightComponent>(FindSceneComponentByName(Held, *FString::Printf(TEXT("BladeLight%s"), Suffix))) : nullptr;
				BladeColors.Add(Light ? Light->GetLightColor() : FLinearColor(0.1f, 0.45f, 1.f));
			}
		}
	}

	static const float RowAt[3] = { 0.45f, 0.78f, 1.f };
	static const float RowAlpha[3] = { 0.f, 0.45f, 1.f };
	for (int32 Blade = 0; Blade < BladeTrails.Num(); ++Blade)
	{
		TArray<FTrailSample>& Samples = BladeTrails[Blade];
		if (Blade < NumBlades)
		{
			float Strength = 0.f;
			if (Samples.Num() > 0)
			{
				const FTrailSample& Prev = Samples.Last();
				const float Dt = FMath::Max(T - Prev.Time, 1e-3f);
				const float Speed = FVector::Dist(Tips[Blade], Prev.Tip) / Dt;
				Strength = FMath::Clamp((Speed - TrailMinSpeed) / FMath::Max(TrailFullSpeed - TrailMinSpeed, 1.f), 0.f, 1.f);
			}
			Samples.Add({ T, Bases[Blade], Tips[Blade], Strength });
		}
		Samples.RemoveAll([&](const FTrailSample& S) { return T - S.Time > TrailLifetime; });

		float MaxStrength = 0.f;
		for (const FTrailSample& S : Samples)
		{
			MaxStrength = FMath::Max(MaxStrength, S.Strength);
		}
		if (Samples.Num() < 2 || MaxStrength <= 0.01f)
		{
			SaberTrail->ClearMeshSection(Blade);
			continue;
		}

		// Three rows per sample (mid-blade -> 3/4 -> tip): brightest at the tip, fading toward the hilt and with age.
		TArray<FVector> Verts;
		TArray<int32> Tris;
		TArray<FVector> Normals;
		TArray<FVector2D> UVs;
		TArray<FLinearColor> Colors;
		TArray<FProcMeshTangent> Tangents;
		const int32 N = Samples.Num();
		for (int32 i = 0; i < N; ++i)
		{
			const FTrailSample& S = Samples[i];
			const float Age = FMath::Clamp((T - S.Time) / TrailLifetime, 0.f, 1.f);
			const float A = FMath::Square(1.f - Age) * S.Strength;
			for (int32 r = 0; r < 3; ++r)
			{
				Verts.Add(FMath::Lerp(S.Base, S.Tip, RowAt[r]));
				Colors.Add(FLinearColor(1.f, 1.f, 1.f, A * RowAlpha[r]));
				UVs.Add(FVector2D(Age, RowAt[r]));
				Normals.Add(FVector::UpVector);
			}
			if (i > 0)
			{
				for (int32 r = 0; r < 2; ++r)
				{
					const int32 P0 = (i - 1) * 3 + r, P1 = P0 + 1, C0 = i * 3 + r, C1 = C0 + 1;
					Tris.Append({ P0, C0, P1, P1, C0, C1 });
				}
			}
		}
		SaberTrail->CreateMeshSection_LinearColor(Blade, Verts, Tris, Normals, UVs, Colors, Tangents, false);
		if (TrailMaterial)
		{
			UMaterialInstanceDynamic* MID = Cast<UMaterialInstanceDynamic>(SaberTrail->GetMaterial(Blade));
			if (!MID || MID->Parent != TrailMaterial)
			{
				MID = UMaterialInstanceDynamic::Create(TrailMaterial, this);
				SaberTrail->SetMaterial(Blade, MID);
			}
			if (BladeColors.IsValidIndex(Blade))
			{
				MID->SetVectorParameterValue(TEXT("BladeColor"), BladeColors[Blade]);
			}
		}
	}
}
