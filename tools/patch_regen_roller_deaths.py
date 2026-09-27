"""Health regen, static-mesh import command, custom Roller meshes, per-type death sounds."""
import sys

SRC = sys.argv[1]


def patch(p, pairs):
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:100])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


# ------------------------------------------------------------------ Jedi: health regen
patch(SRC + "/Public/JediCharacter.h", [
    ('	UPROPERTY(EditAnywhere, Category = "Jedi|Health") float MaxHP = 12.f;\n',
     '	UPROPERTY(EditAnywhere, Category = "Jedi|Health") float MaxHP = 12.f;\n'
     '	/** Health starts regenerating after this many seconds without taking damage... */\n'
     '	UPROPERTY(EditAnywhere, Category = "Jedi|Health") float HealthRegenDelay = 3.f;\n'
     '	/** ...at this many HP per second. */\n'
     '	UPROPERTY(EditAnywhere, Category = "Jedi|Health") float HealthRegenRate = 2.5f;\n'),
    ('	float Surge = 0.f;\n', '	float Surge = 0.f;\n	float LastDamageTime = -100.f;\n	float RegenBarAccum = 0.f;\n'),
])

C = SRC + "/Private/JediCharacter.cpp"
patch(C, [
    # remember when we were last hurt
    ('''	const float Applied = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);''',
     '''	const float Applied = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	LastDamageTime = Now();'''),
    # regen in Tick, next to the other per-frame systems
    ('''	SyncSecondaryBlades();
	TickLean(DeltaSeconds);''', '''	// Out of combat for a moment? Heal up.
	if (!bDead && CurrentHP < MaxHP && Now() - LastDamageTime >= HealthRegenDelay)
	{
		CurrentHP = FMath::Min(MaxHP, CurrentHP + HealthRegenRate * DeltaSeconds);
		RegenBarAccum += DeltaSeconds;
		if (RegenBarAccum >= 0.1f || CurrentHP >= MaxHP)
		{
			RegenBarAccum = 0.f;
			UpdateBars();
		}
	}
	SyncSecondaryBlades();
	TickLean(DeltaSeconds);'''),
    # static mesh import command (editor only), next to the skeletal one
    ('''AJediCharacter::AJediCharacter()
{''', '''#if WITH_EDITOR
// Editor helper: jedi.ImportStatic <FbxFile> <ContentFolder> <AssetName>
static FAutoConsoleCommand GJediImportStaticCmd(
	TEXT("jedi.ImportStatic"),
	TEXT("Imports an FBX as a static mesh (scene units converted to centimetres)."),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		if (Args.Num() < 3)
		{
			UE_LOG(LogTemp, Warning, TEXT("jedi.ImportStatic: need <FbxFile> <ContentFolder> <AssetName>"));
			return;
		}
		UFbxImportUI* UI = NewObject<UFbxImportUI>(GetTransientPackage());
		UI->bIsObjImport = false;
		UI->MeshTypeToImport = FBXIT_StaticMesh;
		UI->OriginalImportType = FBXIT_StaticMesh;
		UI->bImportAsSkeletal = false;
		UI->bImportMesh = true;
		UI->bImportAnimations = false;
		UI->bImportMaterials = false;
		UI->bImportTextures = false;
		UI->bAutomatedImportShouldDetectType = false;
		UI->StaticMeshImportData->bConvertScene = true;
		UI->StaticMeshImportData->bConvertSceneUnit = true;
		UI->StaticMeshImportData->bCombineMeshes = true;

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
		UObject* Asset = Factory->ImportObject(UStaticMesh::StaticClass(), Package, FName(*Args[2]), RF_Public | RF_Standalone,
			Args[0], nullptr, bCanceled);
		Factory->RemoveFromRoot();
		Task->RemoveFromRoot();
		if (Asset)
		{
			FAssetRegistryModule::AssetCreated(Asset);
			Package->MarkPackageDirty();
		}
		UE_LOG(LogTemp, Log, TEXT("jedi.ImportStatic: %s -> %s"), *Args[0], Asset ? *Asset->GetPathName() : TEXT("FAILED"));
	}));
#endif

AJediCharacter::AJediCharacter()
{'''),
])
s = open(C, encoding="utf-8").read()
if '#include "Factories/FbxStaticMeshImportData.h"' not in s:
    a = '#include "Factories/FbxSkeletalMeshImportData.h"\n'
    assert s.count(a) == 1
    s = s.replace(a, a + '#include "Factories/FbxStaticMeshImportData.h"\n#include "Engine/StaticMesh.h"\n')
open(C, "w", encoding="utf-8").write(s)

# ------------------------------------------------------------------ Horde enemies: roller meshes + death sounds
patch(SRC + "/Public/HordeEnemy.h", [
    ("	UPROPERTY() TObjectPtr<USkeletalMesh> WardenModel;\n",
     "	UPROPERTY() TObjectPtr<USkeletalMesh> WardenModel;\n"
     "	UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> DeathSounds;\n"),
    ("	void Say(const TArray<const TCHAR*>& Lines, float Chance);\n",
     "	void Say(const TArray<const TCHAR*>& Lines, float Chance);\n"
     "	void PlayDeathSound();\n"),
])

E = SRC + "/Private/HordeEnemy.cpp"
s = open(E, encoding="utf-8").read()
start = s.index("	case EHordeType::Roller:\n	{\n		GetCapsuleComponent()->SetCapsuleSize(62.f, 62.f);")
end = s.index("		if (WaveMat)\n		{\n			ShieldMID = UMaterialInstanceDynamic::Create(WaveMat, this);\n			ShieldMID->SetVectorParameterValue(TEXT(\"WaveColor\"), FLinearColor(0.3f, 0.9f, 1.5f));")
new_roller = r'''	case EHordeType::Roller:
	{
		GetCapsuleComponent()->SetCapsuleSize(62.f, 62.f);
		M->SetSkeletalMeshAsset(nullptr);
		M->SetVisibility(false);
		M->SetComponentTickEnabled(false);
		UMaterialInstanceDynamic* Bronze = MakeMat(FLinearColor(0.5f, 0.3f, 0.12f), 0.35f, 0.9f);
		UMaterialInstanceDynamic* Dark = MakeMat(FLinearColor(0.04f, 0.035f, 0.03f), 0.4f, 0.8f);
		UMaterialInstanceDynamic* Eye = MakeMat(FLinearColor::Black, 0.4f, 0.f, FLinearColor(7.f, 0.3f, 0.1f));
		UMaterialInstanceDynamic* Gold = MakeMat(FLinearColor(0.75f, 0.6f, 0.35f), 0.3f, 0.9f);
		// Custom meshes (art/enemies/roller.py); the primitive build below is the fallback.
		UStaticMesh* BallModel = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Jedi/Enemies/Roller/SM_RollerBall.SM_RollerBall"));
		UStaticMesh* HeadModel = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Jedi/Enemies/Roller/SM_RollerHead.SM_RollerHead"));
		UStaticMesh* LegModel = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Jedi/Enemies/Roller/SM_RollerLeg.SM_RollerLeg"));
		auto Paint = [&](UStaticMeshComponent* C)
		{
			if (C)
			{
				UMaterialInterface* Slots[4] = { Bronze, Dark, Eye, Gold };
				for (int32 i = 0; i < C->GetNumMaterials(); ++i)
				{
					C->SetMaterial(i, Slots[FMath::Min(i, 3)]);
				}
			}
		};

		RollerTurret = NewObject<USceneComponent>(this);
		RollerTurret->RegisterComponent();
		RollerTurret->AttachToComponent(Root, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		RollerTurret->SetRelativeLocation(FVector(0.f, 0.f, 30.f));
		if (BallModel && HeadModel && LegModel)
		{
			RollerBall = AddPart(BallModel, Root, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, FVector(0.9f), Bronze);
			Paint(RollerBall);
			Paint(AddPart(HeadModel, RollerTurret, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, FVector(1.f), Bronze));
			Muzzle = AddPart(SphereMesh, RollerTurret, NAME_None, FVector(76.f, -30.f, 22.f), FRotator::ZeroRotator, FVector(0.05f), Dark);
			if (Muzzle)
			{
				Muzzle->SetVisibility(false);
			}
			for (int32 i = 0; i < 3; ++i)
			{
				const float Yaw = 60.f + i * 120.f;
				const FVector Dir = FRotator(0.f, Yaw, 0.f).Vector();
				UStaticMeshComponent* Leg = AddPart(LegModel, Root, NAME_None, Dir * 28.f + FVector(0.f, 0.f, -18.f), FRotator(0.f, Yaw, 0.f), FVector(1.f), Dark);
				Paint(Leg);
				RollerLegs.Add(Leg);
			}
		}
		else
		{
			RollerBall = AddPart(SphereMesh, Root, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, FVector(1.2f), Bronze);
			AddPart(CylinderMesh, RollerBall, NAME_None, FVector::ZeroVector, FRotator(90.f, 0.f, 0.f), FVector(1.24f, 1.24f, 0.1f), Dark);
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
		}
'''
s = s[:start] + new_roller + s[end:]

# death sounds: load per type at BeginPlay, play (throttled) at death
a = "	BuildLooks();\n"
assert s.count(a) == 1
s = s.replace(a, a + r'''	{
		const TCHAR* Prefix = TEXT("Droid");
		int32 Count = 7;
		switch (Type)
		{
		case EHordeType::Bulwark: Prefix = TEXT("Trooper"); Count = 4; break;
		case EHordeType::JetGhost: Prefix = TEXT("Jet"); Count = 3; break;
		case EHordeType::Warden: Prefix = TEXT("Warden"); Count = 2; break;
		case EHordeType::Roller: Prefix = TEXT("Roller"); Count = 3; break;
		default: break;
		}
		for (int32 i = 1; i <= Count; ++i)
		{
			const FString Path = FString::Printf(TEXT("/Game/Jedi/Audio/Deaths/SW_Death_%s_%d.SW_Death_%s_%d"), Prefix, i, Prefix, i);
			if (USoundBase* Snd = LoadObject<USoundBase>(nullptr, *Path))
			{
				DeathSounds.Add(Snd);
			}
		}
	}
''')

a = '''void AHordeEnemy::Say(const TArray<const TCHAR*>& Lines, float Chance)'''
assert s.count(a) == 1
s = s.replace(a, r'''void AHordeEnemy::PlayDeathSound()
{
	if (DeathSounds.Num() == 0)
	{
		return;
	}
	// A Force Storm can drop thirty droids in one frame: let a few voices through, not a wall of noise.
	static TArray<double> Recent;
	const double T = Now();
	Recent.RemoveAll([T](double X) { return T - X > 0.35 || X > T; });
	const int32 Allowed = Type == EHordeType::Clanker ? 3 : 4;
	if (Recent.Num() >= Allowed)
	{
		return;
	}
	Recent.Add(T);
	USoundBase* Snd = DeathSounds[FMath::RandRange(0, DeathSounds.Num() - 1)];
	UGameplayStatics::PlaySoundAtLocation(this, Snd, GetActorLocation(), Type == EHordeType::Clanker ? 0.9f : 1.f, FMath::FRandRange(0.94f, 1.08f));
}

void AHordeEnemy::Say(const TArray<const TCHAR*>& Lines, float Chance)''')

a = '''	if (Type == EHordeType::Clanker)
	{
		Say(ClankerDeathLines, 0.22f);
	}
'''
assert s.count(a) == 1
s = s.replace(a, a + '''	PlayDeathSound();
''')
open(E, "w", encoding="utf-8").write(s)
print("patched")
