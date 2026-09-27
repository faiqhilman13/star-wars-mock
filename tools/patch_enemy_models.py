"""Switch AHordeEnemy to the custom Blender enemy models (art/enemies)."""
import sys

SRC = sys.argv[1]


def patch(p, pairs):
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:90])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


patch(SRC + "/Public/HordeEnemy.h", [
    ("	UPROPERTY() TObjectPtr<USkeletalMesh> QuinnMesh;\n",
     "	UPROPERTY() TObjectPtr<USkeletalMesh> QuinnMesh;\n"
     "	// Custom enemy models (Blender, rigged to the mannequin skeleton): art/enemies/*.py\n"
     "	UPROPERTY() TObjectPtr<USkeletalMesh> ClankerModel;\n"
     "	UPROPERTY() TObjectPtr<USkeletalMesh> BulwarkModel;\n"
     "	UPROPERTY() TObjectPtr<USkeletalMesh> JetGhostModel;\n"
     "	UPROPERTY() TObjectPtr<USkeletalMesh> WardenModel;\n"),
])

p = SRC + "/Private/HordeEnemy.cpp"
s = open(p, encoding="utf-8").read()
a = '	QuinnMesh = FindAsset<USkeletalMesh>(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple"));\n'
assert s.count(a) == 1
s = s.replace(a, a +
              '	ClankerModel = FindAsset<USkeletalMesh>(TEXT("/Game/Jedi/Enemies/Clanker/SKM_Clanker.SKM_Clanker"));\n'
              '	BulwarkModel = FindAsset<USkeletalMesh>(TEXT("/Game/Jedi/Enemies/Bulwark/SKM_Bulwark.SKM_Bulwark"));\n'
              '	JetGhostModel = FindAsset<USkeletalMesh>(TEXT("/Game/Jedi/Enemies/JetGhost/SKM_JetGhost.SKM_JetGhost"));\n'
              '	WardenModel = FindAsset<USkeletalMesh>(TEXT("/Game/Jedi/Enemies/Warden/SKM_Warden.SKM_Warden"));\n')

old_start = s.index("	switch (Type)\n	{\n	case EHordeType::Clanker:\n	{\n		UMaterialInstanceDynamic* Tan")
old_end = s.index("	case EHordeType::Roller:\n	{\n		GetCapsuleComponent()->SetCapsuleSize(62.f, 62.f);")
new_looks = r'''	// Custom models use four material slots: 0 main plating, 1 undersuit/joints, 2 eyes/visor (glowing), 3 trim.
	auto SetModel = [&](USkeletalMesh* Model, float Scale, UMaterialInterface* S0, UMaterialInterface* S1, UMaterialInterface* S2, UMaterialInterface* S3)
	{
		M->SetSkeletalMeshAsset(Model);
		if (AnimClass)
		{
			M->SetAnimInstanceClass(AnimClass);
		}
		M->SetRelativeScale3D(FVector(Scale));
		UMaterialInterface* Slots[4] = { S0, S1, S2, S3 };
		for (int32 i = 0; i < M->GetNumMaterials(); ++i)
		{
			M->SetMaterial(i, Slots[FMath::Min(i, 3)]);
		}
	};

	switch (Type)
	{
	case EHordeType::Clanker:
	{
		UMaterialInstanceDynamic* Tan = MakeMat(FLinearColor(0.55f, 0.42f, 0.24f), 0.45f, 0.6f);
		UMaterialInstanceDynamic* Dark = MakeMat(FLinearColor(0.05f, 0.05f, 0.06f), 0.4f, 0.7f);
		UMaterialInstanceDynamic* Eye = MakeMat(FLinearColor::Black, 0.5f, 0.f, FLinearColor(4.f, 2.6f, 0.3f));
		UMaterialInstanceDynamic* Rust = MakeMat(FLinearColor(0.5f, 0.2f, 0.06f), 0.55f, 0.35f);
		if (ClankerModel)
		{
			SetModel(ClankerModel, BodyScale, Tan, Dark, Eye, Rust);
		}
		else
		{
			SetBody(QuinnMesh, FVector(0.72f, 0.8f, 1.f) * BodyScale, Tan);
		}
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(16.f, 0.f, 2.f), Forward, FVector(0.05f, 0.05f, 0.34f), Dark);
		AddPart(CubeMesh, M, TEXT("hand_r"), FVector(6.f, 0.f, -3.f), FRotator::ZeroRotator, FVector(0.1f, 0.04f, 0.08f), Rust);
		break;
	}
	case EHordeType::Bulwark:
	{
		UMaterialInstanceDynamic* White = MakeMat(FLinearColor(0.82f, 0.82f, 0.86f), 0.22f, 0.1f);
		UMaterialInstanceDynamic* Suit = MakeMat(FLinearColor(0.02f, 0.02f, 0.025f), 0.6f, 0.f);
		UMaterialInstanceDynamic* Visor = MakeMat(FLinearColor(0.01f, 0.01f, 0.015f), 0.1f, 0.3f, FLinearColor(0.f, 0.08f, 0.18f));
		UMaterialInstanceDynamic* Trim = MakeMat(FLinearColor(0.3f, 0.31f, 0.35f), 0.4f, 0.6f);
		if (BulwarkModel)
		{
			SetModel(BulwarkModel, BodyScale, White, Suit, Visor, Trim);
		}
		else
		{
			SetBody(MannyMesh, FVector(BodyScale), White);
		}
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(24.f, 0.f, 2.f), Forward, FVector(0.065f, 0.065f, 0.6f), Suit);
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
		UMaterialInstanceDynamic* Armor = MakeMat(FLinearColor(0.03f, 0.03f, 0.035f), 0.3f, 0.75f);
		UMaterialInstanceDynamic* Crimson = MakeMat(FLinearColor(0.3f, 0.02f, 0.02f), 0.7f, 0.f, FLinearColor(0.15f, 0.f, 0.f));
		UMaterialInstanceDynamic* Visor = MakeMat(FLinearColor::Black, 0.4f, 0.f, FLinearColor(7.f, 0.25f, 0.1f));
		UMaterialInstanceDynamic* Gold = MakeMat(FLinearColor(0.75f, 0.52f, 0.15f), 0.3f, 0.95f);
		UMaterialInstanceDynamic* Staff = MakeMat(FLinearColor(0.08f, 0.08f, 0.09f), 0.25f, 0.9f);
		UMaterialInstanceDynamic* Arc = MakeMat(FLinearColor(0.2f, 0.05f, 0.3f), 0.2f, 0.f, FLinearColor(3.f, 0.4f, 6.f));
		if (WardenModel)
		{
			SetModel(WardenModel, 1.04f, Armor, Crimson, Visor, Gold);
		}
		else
		{
			SetBody(MannyMesh, FVector(BodyScale), Armor);
		}
		// Electrostaff held like a spear, crackling violet at both ends.
		Muzzle = AddPart(CylinderMesh, M, TEXT("hand_r"), FVector(10.f, 0.f, 0.f), Forward, FVector(0.045f, 0.045f, 1.9f), Staff);
		AddPart(SphereMesh, M, TEXT("hand_r"), FVector(100.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.13f), Arc);
		AddPart(SphereMesh, M, TEXT("hand_r"), FVector(-80.f, 0.f, 0.f), FRotator::ZeroRotator, FVector(0.13f), Arc);
		break;
	}
	case EHordeType::JetGhost:
	{
		UMaterialInstanceDynamic* Grey = MakeMat(FLinearColor(0.12f, 0.125f, 0.14f), 0.35f, 0.8f);
		UMaterialInstanceDynamic* Suit = MakeMat(FLinearColor(0.03f, 0.028f, 0.025f), 0.7f, 0.f);
		UMaterialInstanceDynamic* Visor = MakeMat(FLinearColor::Black, 0.3f, 0.f, FLinearColor(5.f, 0.4f, 0.1f));
		UMaterialInstanceDynamic* Gold = MakeMat(FLinearColor(0.7f, 0.45f, 0.08f), 0.35f, 0.85f);
		UMaterialInstanceDynamic* Flame = MakeMat(FLinearColor(1.f, 0.4f, 0.05f), 0.5f, 0.f, FLinearColor(8.f, 2.5f, 0.4f));
		if (JetGhostModel)
		{
			SetModel(JetGhostModel, BodyScale, Grey, Suit, Visor, Gold);
		}
		else
		{
			SetBody(QuinnMesh, FVector(BodyScale), Grey);
		}
		// Flames under the modelled thrusters; the modelled shoulder launcher fires from a hidden muzzle marker.
		for (const float Side : { -11.f, 11.f })
		{
			if (UStaticMeshComponent* F = AddPart(ConeMesh, M, TEXT("spine_05"), FVector(-23.f, Side, -52.f), FRotator(180.f, 0.f, 0.f), FVector(0.12f, 0.12f, 0.32f), Flame))
			{
				F->SetCastShadow(false);
				JetFlames.Add(F);
			}
		}
		Muzzle = AddPart(SphereMesh, M, TEXT("spine_05"), FVector(33.f, 18.f, 13.f), FRotator::ZeroRotator, FVector(0.05f), Grey);
		if (Muzzle && JetGhostModel)
		{
			Muzzle->SetVisibility(false);
		}
		break;
	}
'''
s = s[:old_start] + new_looks + s[old_end:]

old_die = '''		// Droids come apart: the head (first part) pops off sometimes.
		if (Type == EHordeType::Clanker && Parts.Num() > 0 && FMath::FRand() < 0.4f)
		{
			BreakOff(Parts[0], Fling * 0.3f + FVector(0.f, 0.f, 650.f));
			if (Parts.IsValidIndex(1))
			{
				BreakOff(Parts[1], Fling * 0.3f + FVector(0.f, 0.f, 600.f));
			}
		}'''
new_die = '''		// Droids come apart: the head pops off sometimes (unless a saber already took something off).
		if (Type == EHordeType::Clanker && ClankerModel && FMath::FRand() < 0.35f && !M->IsBoneHiddenByName(TEXT("head")))
		{
			ASeveredLimb::Sever(this, TEXT("head"), Fling * 0.3f + FVector(0.f, 0.f, 650.f), nullptr);
		}'''
assert s.count(old_die) == 1
s = s.replace(old_die, new_die)
inc = '#include "JediCharacter.h"\n'
assert s.count(inc) == 1
s = s.replace(inc, inc + '#include "SeveredLimb.h"\n')
open(p, "w", encoding="utf-8").write(s)
print("patched")
