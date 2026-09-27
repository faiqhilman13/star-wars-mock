"""Horde-mode changes to AJediCharacter + ABlasterBolt: hit kinds routed through IJediDamageable,
dead-target filtering, combo counter, Force Surge meter + Force Storm super, heal/force pickups."""
import sys

SRC = sys.argv[1]  # .../Source/JediArena
H = SRC + "/Public/JediCharacter.h"
C = SRC + "/Private/JediCharacter.cpp"
B = SRC + "/Private/BlasterBolt.cpp"


def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, (path, n, old[:100])
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)


patch(H, [
    ('#include "GameFramework/Character.h"\n', '#include "GameFramework/Character.h"\n#include "JediDamageable.h"\n'),
    ('static void DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse);',
     'static void DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind = EJediHitKind::Generic);'),
    ('''	UFUNCTION(BlueprintPure, Category = "Jedi") int32 GetSaberStyleIndex() const { return StyleIndex; }
''', '''	UFUNCTION(BlueprintPure, Category = "Jedi") int32 GetSaberStyleIndex() const { return StyleIndex; }

	/** Musou super: when the Force Surge meter is full, a storm of Force blasts and lightning around you. */
	UFUNCTION(BlueprintCallable, Category = "Jedi") void ForceStorm();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void HealBy(float Amount);
	UFUNCTION(BlueprintCallable, Category = "Jedi") void RestoreForce(float Amount);
	UFUNCTION(BlueprintCallable, Category = "Jedi") void AddSurge(float Amount);
	UFUNCTION(BlueprintPure, Category = "Jedi") float GetSurgeFraction() const { return SurgeMax > 0.f ? Surge / SurgeMax : 0.f; }
	UFUNCTION(BlueprintPure, Category = "Jedi") int32 GetComboHits() const;
	UFUNCTION(BlueprintPure, Category = "Jedi") int32 GetMaxCombo() const { return MaxCombo; }
	UFUNCTION(BlueprintPure, Category = "Jedi") float GetHealthFraction() const { return MaxHP > 0.f ? CurrentHP / MaxHP : 0.f; }
	UFUNCTION(BlueprintPure, Category = "Jedi") bool IsStorming() const { return bStorming; }
'''),
    ('''	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> SaberStyleAction;
''', '''	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> SaberStyleAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> StormAction;

	// ---------- Force Surge / Force Storm ----------
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float SurgeMax = 100.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float SurgePerKO = 2.5f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float SurgePerHit = 0.6f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float StormRadius = 1500.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float StormDamage = 6.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float StormImpulse = 2200.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float StormLift = 900.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Surge") float ComboWindow = 2.5f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Surge") TObjectPtr<UAnimSequenceBase> StormAnim;
'''),
    ('void DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse);',
     'void DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse, EJediHitKind Kind = EJediHitKind::Generic);'),
    ('''	int32 StyleIndex = 0;
''', '''	int32 StyleIndex = 0;
	float Surge = 0.f;
	bool bSurgeAnnounced = false;
	int32 ComboHits = 0;
	float ComboLastTime = -100.f;
	int32 MaxCombo = 0;
	bool bStorming = false;
	void StormBlast(float RadiusScale);
	void RegisterComboHit();
'''),
])

patch(C, [
    ('#include "SeveredLimb.h"\n', '#include "SeveredLimb.h"\n#include "HordeDirector.h"\n'),
    # damage routing
    ('''void AJediCharacter::DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse)
{
	if (Target != this)
	{
		DamageActor(Target, Damage, this, Location, Impulse);
	}
}''', '''void AJediCharacter::DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
{
	if (Target != this)
	{
		DamageActor(Target, Damage, this, Location, Impulse, Kind);
	}
}'''),
    ('''void AJediCharacter::DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse)
{
	if (!IsValid(Target))
	{
		return;
	}''', '''void AJediCharacter::DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind)
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
	}'''),
    # targeting: include damageable props, skip corpses
    ('''		const ATrainingRemote* Remote = Cast<ATrainingRemote>(Other);
		if (!Other->IsA(ACharacter::StaticClass()) && !(Remote && Remote->IsActive()))
		{
			continue;
		}''', '''		const ATrainingRemote* Remote = Cast<ATrainingRemote>(Other);
		const IJediDamageable* Damageable = Cast<IJediDamageable>(Other);
		if (!Other->IsA(ACharacter::StaticClass()) && !(Remote && Remote->IsActive()) && !Damageable)
		{
			continue;
		}
		if (Damageable && !Damageable->IsJediTargetAlive())
		{
			continue;
		}'''),
    ('''		if (*It == Self || !IsValid(*It) || It->GetCharacterMovement()->MovementMode == MOVE_None)
		{
			continue;
		}''', '''		if (*It == Self || !IsValid(*It) || It->GetCharacterMovement()->MovementMode == MOVE_None)
		{
			continue;
		}
		if (const IJediDamageable* Damageable = Cast<IJediDamageable>(*It); Damageable && !Damageable->IsJediTargetAlive())
		{
			continue;
		}'''),
    ('''		if (Prim && Prim->IsSimulatingPhysics() && !Prim->GetOwner()->IsA(ACharacter::StaticClass()))''',
     '''		if (Prim && Prim->IsSimulatingPhysics() && !Prim->GetOwner()->IsA(ACharacter::StaticClass()) && !Cast<IJediDamageable>(Prim->GetOwner()))'''),
    # hit kinds at the call sites
    ('DealDamage(Victim, Damage, Hit.ImpactPoint, SwingDir * SaberKnockback + FVector::UpVector * SaberLift);',
     'DealDamage(Victim, Damage, Hit.ImpactPoint, SwingDir * SaberKnockback + FVector::UpVector * SaberLift, EJediHitKind::Saber);\n\t\t\t\t\tRegisterComboHit();'),
    ('DealDamage(Other, PushDamage, Other->GetActorLocation(), Dir * PushImpulse + FVector::UpVector * PushLift);',
     'DealDamage(Other, PushDamage, Other->GetActorLocation(), Dir * PushImpulse + FVector::UpVector * PushLift, EJediHitKind::ForcePush);'),
    ('DealDamage(Best, PullDamage, TargetLoc, Dir * PullImpulse + FVector::UpVector * PullLift);',
     'DealDamage(Best, PullDamage, TargetLoc, Dir * PullImpulse + FVector::UpVector * PullLift, EJediHitKind::ForcePull);'),
    ('DealDamage(Other, LightningDamage, Other->GetActorLocation(), Dir * 140.f + FVector::UpVector * 60.f);',
     'DealDamage(Other, LightningDamage, Other->GetActorLocation(), Dir * 140.f + FVector::UpVector * 60.f, EJediHitKind::Lightning);'),
    # saber sweep: skip corpses, read HP through the interface
    ('''					SwingHits.Add(Victim);
					float HPBefore = -1.f;''', '''					if (const IJediDamageable* DV = Cast<IJediDamageable>(Victim); DV && !DV->IsJediTargetAlive())
					{
						continue; // don't farm hits (and hit-stop) off ragdolls
					}
					SwingHits.Add(Victim);
					float HPBefore = -1.f;
					if (const IJediDamageable* DV = Cast<IJediDamageable>(Victim))
					{
						HPBefore = DV->GetJediHealth();
					}'''),
    # invulnerable during the storm
    ('''	if (bDead || TryDefend(DamageCauser))
	{
		return;
	}
	// Knockback like the template character''', '''	if (bDead || bStorming || TryDefend(DamageCauser))
	{
		return;
	}
	// Knockback like the template character'''),
    ('''float AJediCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bDead)
	{
		return 0.f;
	}''', '''float AJediCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bDead || bStorming)
	{
		return 0.f;
	}'''),
    ('''	Bind(SaberStyleAction, ETriggerEvent::Started, &AJediCharacter::CycleSaberStyle);''',
     '''	Bind(SaberStyleAction, ETriggerEvent::Started, &AJediCharacter::CycleSaberStyle);
	Bind(StormAction, ETriggerEvent::Started, &AJediCharacter::ForceStorm);'''),
    # new functions, appended before CycleSaberStyle
    ('''void AJediCharacter::CycleSaberStyle()
{''', '''void AJediCharacter::HealBy(float Amount)
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
{'''),
])

patch(B, [
    ('#include "BlasterBolt.h"\n', '#include "BlasterBolt.h"\n#include "JediDamageable.h"\n'),
    ('''	if (!Other->CanBeDamaged() && !Other->IsA(APawn::StaticClass()))
	{
		return; // pass through triggers, VFX actors, etc.
	}''', '''	if (!Other->CanBeDamaged() && !Other->IsA(APawn::StaticClass()))
	{
		return; // pass through triggers, VFX actors, etc.
	}
	// Undeflected horde fire flies through the shooter's allies (droids don't shoot each other).
	if (!bDeflected && Shooter.IsValid() && Cast<IJediDamageable>(Shooter.Get()) && Cast<IJediDamageable>(Other))
	{
		return;
	}'''),
    ('AJediCharacter::DamageActor(Other, Damage, Shooter.Get() ? Shooter.Get() : this, Loc, GetDirection() * 250.f + FVector(0.f, 0.f, 80.f));',
     'AJediCharacter::DamageActor(Other, Damage, Shooter.Get() ? Shooter.Get() : this, Loc, GetDirection() * 250.f + FVector(0.f, 0.f, 80.f), EJediHitKind::Bolt);'),
])
print("patched")
