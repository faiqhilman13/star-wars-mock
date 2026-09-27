"""Adds saber styles (single / dual wield / saberstaff) to AJediCharacter: multi-blade sweeps,
off-hand saber with a mirrored grip, second-blade ignition sync, per-blade trails."""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)


# includes
rep('#include "SeveredLimb.h"\n',
    '#include "SeveredLimb.h"\n#include "Engine/SkeletalMeshSocket.h"\n#include "Materials/MaterialInstanceDynamic.h"\n#include "Components/PointLightComponent.h"\n')

# BeginPlay: spawn through the style system
a = s.index("\tif (SaberClass)\n\t{\n\t\tFActorSpawnParameters Params;")
b = s.index("\tUpdateBars();\n\tEnableCapePhysics();\n}")
s = s[:a] + '''	if (Styles.Num() > 0)
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
''' + s[b:]

# EndPlay: destroy both sabers
rep('''	if (Saber)
	{
		Saber->Destroy();
	}
	if (UWorld* World = GetWorld())''', '''	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		if (Held)
		{
			Held->Destroy();
		}
	}
	if (UWorld* World = GetWorld())''')

# Death: retract every saber
rep('''	if (Saber)
	{
		CallBP(Saber, TEXT("Retract"));
	}
	// The Combat player controller''', '''	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		CallBP(Held, TEXT("Retract"));
	}
	// The Combat player controller''')

# Toggle: all sabers
rep('''	bSaberOn = !bSaberOn;
	CallBP(Saber, bSaberOn ? TEXT("Ignite") : TEXT("Retract"));''', '''	bSaberOn = !bSaberOn;
	for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
	{
		CallBP(Held, bSaberOn ? TEXT("Ignite") : TEXT("Retract"));
	}''')

# Input binding
rep('''	Bind(CameraSideAction, ETriggerEvent::Started, &AJediCharacter::ToggleCameraSide);''',
    '''	Bind(CameraSideAction, ETriggerEvent::Started, &AJediCharacter::ToggleCameraSide);
	Bind(SaberStyleAction, ETriggerEvent::Started, &AJediCharacter::CycleSaberStyle);''')

# New functions, placed before TickSwing
rep('''void AJediCharacter::TickSwing()
{''', '''int32 AJediCharacter::GetBlades(TArray<FVector>& OutBases, TArray<FVector>& OutTips) const
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
{''')

# TickSwing: sweep every blade
rep('''		FVector Base = FVector::ZeroVector, Tip = FVector::ZeroVector;
		const bool bHasSaber = bSaberOn && GetBlade(Base, Tip);
		if (!bHasSaber)
		{
			// Unarmed fallback: short punch reach from the hand.
			Base = GetMesh()->GetSocketLocation(SaberSocket);
			Tip = Base + GetActorForwardVector() * 60.f;
		}
		if (bHaveLastBlade && TPrev <= Swing.HitEnd && T >= Swing.HitStart)
		{''', '''		TArray<FVector> Bases, Tips;
		const bool bHasSaber = bSaberOn && GetBlades(Bases, Tips) > 0;
		if (!bHasSaber)
		{
			// Unarmed fallback: short punch reach from the hand.
			Bases = { GetMesh()->GetSocketLocation(SaberSocket) };
			Tips = { Bases[0] + GetActorForwardVector() * 60.f };
		}
		if (bHaveLastBlade && LastBladeBases.Num() == Bases.Num() && TPrev <= Swing.HitEnd && T >= Swing.HitStart)
		{''')
rep('''			if (Saber)
			{
				Query.AddIgnoredActor(Saber);
			}
''', '''			for (AActor* Held : { Saber.Get(), OffhandSaber.Get() })
			{
				if (Held)
				{
					Query.AddIgnoredActor(Held);
				}
			}
''')
rep('''* Swing.DamageMultiplier * (bRiposte ? RiposteMultiplier : 1.f);
			const int32 Samples = 6;
			for (int32 S = 0; S <= Samples; ++S)
			{
				const float A = static_cast<float>(S) / Samples;
				const FVector From = FMath::Lerp(LastBladeBase, LastBladeTip, A);
				const FVector To = FMath::Lerp(Base, Tip, A);''', '''* Swing.DamageMultiplier * StyleDamageMultiplier * (bRiposte ? RiposteMultiplier : 1.f);
			const int32 Samples = 6;
			for (int32 BladeIdx = 0; BladeIdx < Bases.Num(); ++BladeIdx)
			for (int32 S = 0; S <= Samples; ++S)
			{
				const float A = static_cast<float>(S) / Samples;
				const FVector From = FMath::Lerp(LastBladeBases[BladeIdx], LastBladeTips[BladeIdx], A);
				const FVector To = FMath::Lerp(Bases[BladeIdx], Tips[BladeIdx], A);''')
rep('''		LastBladeBase = Base;
		LastBladeTip = Tip;
		bHaveLastBlade = true;''', '''		LastBladeBases = Bases;
		LastBladeTips = Tips;
		bHaveLastBlade = true;''')

# Tick: keep staff blades in sync (before the trail samples them)
rep('''	TickLean(DeltaSeconds);
	TickStance();
	TickTrail();''', '''	SyncSecondaryBlades();
	TickLean(DeltaSeconds);
	TickStance();
	TickTrail();''')

# Trail: one ribbon (mesh section) per blade, tinted with that blade's light colour
a = s.index("void AJediCharacter::TickTrail()")
b = s.index("\tSaberTrail->CreateMeshSection_LinearColor(0, Verts, Tris, Normals, UVs, Colors, Tangents, false);\n}", a)
b = s.index("}", b + 10) + 1
s = s[:a] + '''void AJediCharacter::TickTrail()
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
}''' + s[b:]

open(p, "w", encoding="utf-8").write(s)
print("patched")
