#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "JediCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UWidgetComponent;
class UInputAction;
class UAnimSequenceBase;
class UNiagaraSystem;
class UCameraShakeBase;
class USoundBase;
class UAudioComponent;
class UMaterialInterface;
class ABlasterBolt;
class UProceduralMeshComponent;
class UAnimMontage;
struct FInputActionValue;

/** One step of the saber combo. Times are in seconds of the (unscaled) animation. */
USTRUCT(BlueprintType)
struct FSaberSwing
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	TObjectPtr<UAnimSequenceBase> Anim = nullptr;

	/** Blade damage window. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float HitStart = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float HitEnd = 0.4f;

	/** Time after which a queued attack chains into the next swing. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float ChainTime = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float DamageMultiplier = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float PlayRate = 1.f;

	/** Forward burst at the start of the swing (cm/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Saber")
	float Lunge = 380.f;
};

/**
 * Third-person Jedi: saber combos with blade sweep traces, block/parry,
 * Force Push/Pull/Lightning, Force Dash and a Force double jump.
 * Enemies are the Combat template's Blueprint enemies; they are damaged through
 * their BPI_Damageable "ApplyDamage" implementation when available.
 */
UCLASS(Abstract)
class JEDIARENA_API AJediCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AJediCharacter();

	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
	virtual void Landed(const FHitResult& Hit) override;

	/** Called by blaster bolts that reach us. Returns true if the bolt was deflected. */
	bool TryDeflectBolt(ABlasterBolt* Bolt);

	/** Damages any actor: Combat-template BPI_Damageable actors get knockback via "Apply Damage", others get ApplyDamage + physics impulse. */
	static void DamageActor(AActor* Target, float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse);

	/** Entry point for the Combat template's BPI_Damageable "Apply Damage" (wired in BP_Jedi). */
	UFUNCTION(BlueprintCallable, Category = "Jedi")
	void ReceiveTemplateDamage(float Damage, AActor* DamageCauser, FVector DamageLocation, FVector DamageImpulse);

	UFUNCTION(BlueprintPure, Category = "Jedi")
	float GetForcePercent() const { return MaxForce > 0.f ? ForcePower / MaxForce : 0.f; }

	UFUNCTION(BlueprintPure, Category = "Jedi")
	bool IsBlocking() const { return bBlocking; }

	UFUNCTION(BlueprintPure, Category = "Jedi")
	bool IsDead() const { return bDead; }

	// Ability entry points (also callable from console with "ke * ForcePush" etc.)
	UFUNCTION(BlueprintCallable, Category = "Jedi") void SaberAttack();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void BlockStart();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void BlockStop();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void ForcePush();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void ForcePull();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void LightningStart();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void LightningStop();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void ForceDash();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void JediJump();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void SaberToggle();
	UFUNCTION(BlueprintCallable, Category = "Jedi") void ToggleCameraSide();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// ---------- Components ----------
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UCameraComponent> FollowCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UWidgetComponent> LifeBar;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UWidgetComponent> ForceBar;

	/** World-space ribbon following the blade. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UProceduralMeshComponent> SaberTrail;

	// ---------- Input ----------
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> LookAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> MouseLookAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> JumpAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> AttackAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> BlockAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> ForcePushAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> ForcePullAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> ForceLightningAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> DashAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> SaberToggleAction;
	UPROPERTY(EditDefaultsOnly, Category = "Input") TObjectPtr<UInputAction> CameraSideAction;

	// ---------- Assets ----------
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TSubclassOf<AActor> SaberClass;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TSubclassOf<AActor> ForceWaveClass;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TSubclassOf<AActor> LightningBoltClass;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TSubclassOf<UUserWidget> BarWidgetClass;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TObjectPtr<UNiagaraSystem> HitFX;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TSubclassOf<UCameraShakeBase> HitShake;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Assets") TSubclassOf<UCameraShakeBase> HurtShake;

	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> HumSound;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> IgniteSound;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> RetractSound;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TArray<TObjectPtr<USoundBase>> SwingSounds;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> HitSound;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> ClashSound;
	/** Optional variations; one is picked at random per impact (otherwise HitSound / ClashSound). */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TArray<TObjectPtr<USoundBase>> HitSoundVariants;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TArray<TObjectPtr<USoundBase>> ClashSoundVariants;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> DeflectSound;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> PushSound;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Sound") TObjectPtr<USoundBase> LightningLoopSound;
	/** Hum level with the blade at rest and at full swing speed (on top of the sound's own volume). */
	UPROPERTY(EditAnywhere, Category = "Jedi|Sound") float HumIdleVolume = 0.35f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Sound") float HumSwingVolume = 0.9f;
	/** Saber-on-body impact loudness. The hum and the swing whoosh duck under it for HitDuckTime. */
	UPROPERTY(EditAnywhere, Category = "Jedi|Sound") float HitVolume = 1.6f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Sound") float HitDuckTime = 0.3f;

	/** Lethal saber blows sever whatever part the blade connected with (head, arm, leg, torso). */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Gore") bool bDecapitation = true;
	/** Chance a lethal saber blow dismembers (1 = always). */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Gore") float DecapChance = 1.f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Gore") TObjectPtr<UMaterialInterface> StumpMaterial;

	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TArray<FSaberSwing> Combo;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> BlockAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> ParryAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> BlockHitAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> DashAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> FlipAnim;
	/** Optional full-body stance loops layered over the locomotion blueprint (saber-in-hand idle/run). */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> StanceIdleAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> StanceRunAnim;
	/** Ground speed at which the run loop plays at 1x. */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") float StanceRunReferenceSpeed = 650.f;

	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") TObjectPtr<UMaterialInterface> TrailMaterial;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") float TrailLifetime = 0.14f;
	/** Tip speed (cm/s) where the trail starts to appear / reaches full strength. */
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") float TrailMinSpeed = 350.f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Trail") float TrailFullSpeed = 1600.f;

	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Movement") float TurnRate = 720.f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Movement") float MaxLeanDegrees = 14.f;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> PushAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> PullAnim;
	UPROPERTY(EditDefaultsOnly, Category = "Jedi|Anims") TObjectPtr<UAnimSequenceBase> LightningAnim;

	// ---------- Tuning ----------
	UPROPERTY(EditAnywhere, Category = "Jedi|Health") float MaxHP = 12.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Health") float RespawnTime = 3.f;

	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") FVector GripLoc = FVector(-7.f, 2.f, 0.f);
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") FRotator GripRot = FRotator(35.f, 0.f, 180.f);
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") FName SaberSocket = TEXT("hand_r");
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float SaberDamage = 2.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float FistDamage = 1.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float SaberKnockback = 420.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float SaberLift = 250.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float BladeTraceRadius = 14.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float AttackLunge = 380.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float AttackMoveSpeed = 160.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float HitStopTime = 0.06f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Saber") float RiposteMultiplier = 2.5f;

	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float ParryWindow = 0.28f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float BlockForceCost = 8.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float BlockAngleDot = 0.1f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float BlockMoveSpeed = 180.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float ParryForceGain = 15.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float ParryStagger = 750.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float RiposteWindow = 1.2f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float DeflectForceCost = 3.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Block") float DeflectSpreadDegrees = 7.f;

	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float MaxForce = 100.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float ForceRegen = 14.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float ForceCooldown = 0.45f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PushCost = 30.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PushRange = 850.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PushImpulse = 1900.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PushLift = 550.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PushDamage = 1.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PullCost = 20.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PullRange = 2200.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PullImpulse = 1500.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PullLift = 450.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float PullDamage = 0.5f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float LightningCost = 28.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float LightningRange = 1100.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float LightningDamage = 0.25f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Force") float LightningInterval = 0.12f;

	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float WalkSpeed = 500.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float DashCost = 15.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float DashSpeed = 2600.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float DashDuration = 0.18f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float DashCooldown = 0.35f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float DoubleJumpZ = 950.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float DoubleJumpCost = 8.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Movement") float KillZ = -60.f;

	UPROPERTY(EditAnywhere, Category = "Jedi|Camera") float CameraDistance = 280.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Camera") float ShoulderOffset = 55.f;
	UPROPERTY(EditAnywhere, Category = "Jedi|Camera") float BaseFOV = 90.f;

	// ---------- Runtime state ----------
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Jedi|State") float CurrentHP = 0.f;
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Jedi|State") float ForcePower = 0.f;
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Jedi|State") TObjectPtr<AActor> Saber;

private:
	// input glue
	void OnMove(const FInputActionValue& Value);
	void OnLook(const FInputActionValue& Value);

	// helpers
	float Now() const;
	UAnimInstance* Anim() const;
	void PlayAnim(UAnimSequenceBase* Seq, float Rate = 1.f, int32 Loops = 1, float BlendIn = 0.08f, float BlendOut = 0.2f);
	void StopAnims(float BlendOut = 0.15f);
	bool SpendForce(float Cost, bool bUseCooldown);
	FVector AimForwardFlat() const;
	TArray<AActor*> CharactersInCone(float Range, float MinDot) const;
	void DealDamage(AActor* Target, float Damage, const FVector& Location, const FVector& Impulse);
	void NotifyDangerAhead();
	void SpawnWave(const FVector& Loc, const FRotator& Rot, float Scale = 1.f);
	void SpawnBolt(const FVector& Start, const FVector& End);
	void SlowMo(float Dilation, float Duration);
	void HitStop(AActor* Victim);
	void UpdateBars();
	void Die();

	// saber
	void StartSwing(int32 Index);
	void EndSwing();
	void TickSwing();
	bool GetBlade(FVector& OutBase, FVector& OutTip) const;
	void LightningZap();
	void EndDash();
	void Parry(AActor* Attacker);
	/** Block/parry/dash filtering. Returns true when the hit was fully absorbed. */
	bool TryDefend(AActor* DamageCauser);
	void ResetHitReaction();
	/** Puts the cape_* bone chains (if the mesh has them) under physics simulation. */
	void EnableCapePhysics();

	// fluid movement
	void FaceDirection(const FVector& Dir);
	void TickLean(float DeltaSeconds);
	void TickStance();
	void TickTrail();

	struct FTrailSample { float Time; FVector Base; FVector Tip; float Strength; };
	TArray<FTrailSample> TrailSamples;
	FQuat BaseMeshRotation = FQuat::Identity;
	FRotator CurrentLean = FRotator::ZeroRotator;
	float LastYaw = 0.f;
	int32 StanceState = 0; // 0 none, 1 idle, 2 run
	UPROPERTY(Transient) TObjectPtr<UAnimMontage> StanceMontage;

	bool bAttacking = false;
	bool bQueuedAttack = false;
	int32 ComboIndex = 0;
	float SwingStartTime = 0.f;
	float SwingLength = 0.f;
	bool bHaveLastBlade = false;
	FVector LastBladeBase, LastBladeTip;
	TSet<TWeakObjectPtr<AActor>> SwingHits;
	float RiposteUntil = -1.f;

	bool bBlocking = false;
	float BlockStartTime = -10.f;

	bool bChanneling = false;
	float LightningAccum = 0.f;
	float LastForceTime = -10.f;

	bool bDashing = false;
	bool bAirDashUsed = false;
	bool bDoubleJumpUsed = false;
	float LastDashTime = -10.f;
	float SavedFriction = 8.f;
	float SavedBraking = 2048.f;
	float SavedGravity = 1.f;

	bool bSaberOn = true;
	bool bDead = false;
	bool bSkipDefence = false;
	bool bRightShoulder = true;
	float TargetFOV = 90.f;

	FTimerHandle DashTimer, SlowMoTimer, HitStopTimer, HitReactTimer;
	TArray<TWeakObjectPtr<AActor>> HitStopActors;
	TWeakObjectPtr<UUserWidget> LifeWidget, ForceWidget;

	UPROPERTY(Transient) TObjectPtr<UAudioComponent> HumAudio;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> LightningAudio;
	FVector LastHumTip = FVector::ZeroVector;
	bool bHaveHumTip = false;
	TWeakObjectPtr<UAudioComponent> SwingAudio;
	float HumDuckUntil = -1.f;

	void PlaySoundAt(USoundBase* Sound, const FVector& Location, float Volume = 1.f, float Pitch = 1.f);
	static USoundBase* PickSound(USoundBase* Single, const TArray<TObjectPtr<USoundBase>>& Variants);
	bool InSwingHitWindow() const;
};
