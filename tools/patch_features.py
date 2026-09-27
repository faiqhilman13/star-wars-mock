p = r"C:\Users\User\Documents\Unreal Projects\JediArena\Source\JediArena\Private\JediCharacter.cpp"
s = open(p, encoding="utf-8").read()


def rep(old, new, count=1):
    global s
    assert old in s, "missing anchor: " + old[:80]
    s = s.replace(old, new, count)


if "jedi.ImportSounds" in s:
    raise SystemExit("already patched")

# includes
rep('#include "JediCharacter.h"\n', '#include "JediCharacter.h"\n\n#include "BlasterBolt.h"\n#include "Components/AudioComponent.h"\n#include "SeveredHead.h"\n#include "Sound/SoundBase.h"\n#include "Sound/SoundWave.h"\n#include "TrainingRemote.h"\n')
rep('#include "Kismet2/KismetEditorUtilities.h"\n#endif', '#include "Kismet2/KismetEditorUtilities.h"\n#include "AssetRegistry/AssetRegistryModule.h"\n#include "Factories/Factory.h"\n#include "HAL/FileManager.h"\n#include "Misc/Paths.h"\n#include "UObject/Package.h"\n#include "UObject/UObjectIterator.h"\n#endif')

# editor: sound import command
rep('''AJediCharacter::AJediCharacter()''', '''#if WITH_EDITOR
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

AJediCharacter::AJediCharacter()''')

# DealDamage -> static DamageActor
rep('''void AJediCharacter::DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse)
{
	if (!IsValid(Target) || Target == this)
	{
		return;
	}
	// Combat template actors implement BPI_Damageable::ApplyDamage (damage + knockback + hit FX).
	if (!CallBP(Target, TEXT("ApplyDamage"), { Damage, static_cast<UObject*>(this), Location, Impulse }))
	{
		UGameplayStatics::ApplyDamage(Target, Damage, GetController(), this, nullptr);''', '''void AJediCharacter::DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse)
{
	if (Target != this)
	{
		DamageActor(Target, Damage, this, Location, Impulse);
	}
}

void AJediCharacter::DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse)
{
	if (!IsValid(Target))
	{
		return;
	}
	// Combat template actors implement BPI_Damageable::ApplyDamage (damage + knockback + hit FX).
	if (!CallBP(Target, TEXT("ApplyDamage"), { Damage, static_cast<UObject*>(Causer), Location, Impulse }))
	{
		APawn* CauserPawn = Cast<APawn>(Causer);
		UGameplayStatics::ApplyDamage(Target, Damage, CauserPawn ? CauserPawn->GetController() : nullptr, Causer, nullptr);''')

# CharactersInCone includes training remotes
rep('''	for (TActorIterator<ACharacter> It(GetWorld()); It; ++It)
	{
		ACharacter* Other = *It;
		if (Other == this || !IsValid(Other))
		{
			continue;
		}''', '''	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Other = *It;
		if (Other == this || !IsValid(Other))
		{
			continue;
		}
		const ATrainingRemote* Remote = Cast<ATrainingRemote>(Other);
		if (!Other->IsA(ACharacter::StaticClass()) && !(Remote && Remote->IsActive()))
		{
			continue;
		}''')

# helpers
rep('''void AJediCharacter::UpdateBars()''', '''void AJediCharacter::PlaySoundAt(USoundBase* Sound, const FVector& Location, float Volume, float Pitch)
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

void AJediCharacter::UpdateBars()''')

# BeginPlay: hum + ignite
rep('''			Saber->SetActorRelativeRotation(GripRot);
		}''', '''			Saber->SetActorRelativeRotation(GripRot);
			if (HumSound)
			{
				HumAudio = UGameplayStatics::SpawnSoundAttached(HumSound, Saber->GetRootComponent(), NAME_None, FVector(0.f, 0.f, 50.f),
					EAttachLocation::KeepRelativeOffset, true, 0.55f, 1.f, 0.f, nullptr, nullptr, false);
			}
			PlaySoundAt(IgniteSound, Saber->GetActorLocation(), 0.8f);
		}''')

# Tick: hum follows blade speed
rep('''	// FOV kick recovery (dash)''', '''	// Saber hum: pitch and volume follow blade-tip speed.
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
			HumAudio->SetVolumeMultiplier(FMath::Lerp(0.5f, 1.f, Alpha));
		}
	}

	// FOV kick recovery (dash)''')

# swing sound
rep('''	NotifyDangerAhead();
}''', '''	NotifyDangerAhead();
	if (bSaberOn && SwingSounds.Num() > 0 && Saber)
	{
		UGameplayStatics::SpawnSoundAttached(SwingSounds[Index % SwingSounds.Num()], Saber->GetRootComponent(), NAME_None, FVector(0.f, 0.f, 60.f),
			EAttachLocation::KeepRelativeOffset, true, 0.9f, FMath::FRandRange(0.94f, 1.06f));
	}
}''')

# saber hit: sound + decapitation
rep('''					SwingHits.Add(Victim);''', '''					SwingHits.Add(Victim);
					float HPBefore = -1.f;
					if (FProperty* HPProp = Victim->GetClass()->FindPropertyByName(TEXT("Current HP")))
					{
						if (const FDoubleProperty* D = CastField<FDoubleProperty>(HPProp)) { HPBefore = static_cast<float>(D->GetPropertyValue_InContainer(Victim)); }
						else if (const FFloatProperty* F = CastField<FFloatProperty>(HPProp)) { HPBefore = F->GetPropertyValue_InContainer(Victim); }
					}''')
rep('''					HitStop(Victim);''', '''					PlaySoundAt(bHasSaber ? HitSound.Get() : nullptr, Hit.ImpactPoint, 0.9f, FMath::FRandRange(0.92f, 1.08f));
					// Lethal saber blows on the backhand/finisher (or high cuts) take the head.
					ACharacter* VictimChar = Cast<ACharacter>(Victim);
					if (bDecapitation && bHasSaber && VictimChar && HPBefore > 0.f && HPBefore - Damage <= 0.f &&
						(ComboIndex >= 1 || Hit.ImpactPoint.Z > VictimChar->GetActorLocation().Z + 35.f || FMath::FRand() < DecapChance))
					{
						if (ASeveredHead::Decapitate(VictimChar, SwingDir * 520.f, StumpMaterial))
						{
							UE_LOG(LogTemp, Log, TEXT("Jedi: DECAPITATED %s"), *GetNameSafe(VictimChar));
							PlaySoundAt(ClashSound, Hit.ImpactPoint, 0.6f, 0.8f);
							SlowMo(0.25f, 0.4f);
						}
					}
					HitStop(Victim);''')

# toggle sounds
rep('''	CallBP(Saber, bSaberOn ? TEXT("Ignite") : TEXT("Retract"));''', '''	CallBP(Saber, bSaberOn ? TEXT("Ignite") : TEXT("Retract"));
	PlaySoundAt(bSaberOn ? IgniteSound.Get() : RetractSound.Get(), Saber->GetActorLocation(), 0.8f);
	if (HumAudio)
	{
		if (bSaberOn) { HumAudio->FadeIn(0.3f, 0.55f); } else { HumAudio->FadeOut(0.35f, 0.f); }
	}''')

# block/parry sounds
rep('''				Parry(DamageCauser);''', '''				Parry(DamageCauser);
				PlaySoundAt(ClashSound, GetActorLocation() + ToAttacker * 60.f + FVector(0.f, 0.f, 50.f), 1.f, 1.1f);''')
rep('''				ForcePower -= BlockForceCost;''', '''				ForcePower -= BlockForceCost;
				PlaySoundAt(ClashSound, GetActorLocation() + ToAttacker * 60.f + FVector(0.f, 0.f, 50.f), 0.8f, FMath::FRandRange(0.9f, 1.f));''')
rep('''	GetCharacterMovement()->AddImpulse(DamageImpulse, true);''', '''	GetCharacterMovement()->AddImpulse(DamageImpulse, true);
	PlaySoundAt(HitSound, DamageLocation, 0.8f, 0.8f);''')

# push / jump / dash sounds
rep('''	for (AActor* Other : CharactersInCone(PushRange, 0.3f))''', '''	PlaySoundAt(PushSound, Loc + Fwd * 100.f);
	for (AActor* Other : CharactersInCone(PushRange, 0.3f))''')
rep('''	PlayAnim(FlipAnim, 1.1f, 1, 0.05f, 0.2f);''', '''	PlayAnim(FlipAnim, 1.1f, 1, 0.05f, 0.2f);
	PlaySoundAt(PushSound, GetActorLocation(), 0.45f, 1.6f);''')
rep('''	PlayAnim(DashAnim, 1.f, 1, 0.04f, 0.15f);''', '''	PlayAnim(DashAnim, 1.f, 1, 0.04f, 0.15f);
	PlaySoundAt(SwingSounds.Num() > 0 ? SwingSounds[0].Get() : nullptr, GetActorLocation(), 0.8f, 0.6f);
	PlaySoundAt(PushSound, GetActorLocation(), 0.35f, 1.8f);''')

# lightning loop
rep('''	PlayAnim(LightningAnim, 1.f, 100, 0.15f, 0.2f);''', '''	PlayAnim(LightningAnim, 1.f, 100, 0.15f, 0.2f);
	if (LightningLoopSound && !LightningAudio)
	{
		LightningAudio = UGameplayStatics::SpawnSoundAttached(LightningLoopSound, GetMesh(), TEXT("hand_l"), FVector::ZeroVector,
			EAttachLocation::SnapToTarget, true, 0.8f, 1.f, 0.f, nullptr, nullptr, false);
	}''')
rep('''	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	StopAnims(0.2f);''', '''	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	StopAnims(0.2f);
	if (LightningAudio)
	{
		LightningAudio->FadeOut(0.15f, 0.f);
		LightningAudio = nullptr;
	}''')

# deflection
s += '''
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
'''
open(p, "w", encoding="utf-8").write(s)
print("cpp patched")
