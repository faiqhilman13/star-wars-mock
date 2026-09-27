#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "JediDamageable.h"
#include "BossWalker.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPrimitiveComponent;
class USoundBase;
class UNiagaraSystem;
class UCameraShakeBase;
class ABlasterBolt;

/** What the Scrap Colossus is currently busy doing. */
UENUM(BlueprintType)
enum class EBossWalkerState : uint8
{
	Intro,
	Roam,
	Volley,
	Stomp,
	Peck,
	Barrage,
	Stagger,
	Collapsed,
	Dead
};

/** One visible piece of scrap: mesh, its material instance, hit flash and death-debris bookkeeping. */
USTRUCT()
struct FScrapPart
{
	GENERATED_BODY()

	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Mesh = nullptr;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> MID = nullptr;

	/** Base glow (animated parts change this at runtime). */
	FLinearColor Emissive = FLinearColor::Black;
	/** Multiplier on Emissive (knee pulse, eye blink / flicker). */
	float Pulse = 1.f;
	FLinearColor FlashColor = FLinearColor::White;
	float Flash = 0.f;
	/** Seconds into the death sequence when this part pops off. 0 = at the final blast, < 0 = stays attached to its parent part. */
	float DebrisDelay = 0.f;
	bool bDetached = false;
	bool bDirty = true;
};

/** Pooled ground ring: stomp / missile warning markers and expanding shockwaves (M_ForceWave on a squashed sphere). */
USTRUCT()
struct FScrapRing
{
	GENERATED_BODY()

	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Mesh = nullptr;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> MID = nullptr;

	FVector Center = FVector::ZeroVector;
	FLinearColor Color = FLinearColor::Red;
	float Start = 0.f;
	float Duration = 1.f;
	float Radius0 = 100.f;
	float Radius1 = 100.f;
	float Height0 = 6.f;
	float Height1 = 6.f;
	float Intensity = 6.f;
	int32 Serial = 0;
	bool bShockwave = false;
	bool bActive = false;
};

/**
 * THE SCRAP COLOSSUS: a patched-together two-legged "chicken walker" boss built entirely from static mesh parts.
 * Procedural walk cycle (2-bone leg IK driven by distance travelled), glowing knee weak points, twin chin cannons,
 * stomp shockwaves, beak pecks, a rage-mode scrap-missile barrage, collapses every 25% HP and a very messy death.
 * No AI controller: it drives its own CharacterMovement (bRunPhysicsWithNoController) and rotation.
 * Spawn it anywhere inside the arena (a drop site is best): it drops in from the sky and registers itself with the HordeDirector.
 */
UCLASS()
class JEDIARENA_API ABossWalker : public ACharacter, public IJediDamageable
{
	GENERATED_BODY()

public:
	ABossWalker();

	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
	virtual void Landed(const FHitResult& Hit) override;

	// IJediDamageable
	virtual float ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind) override;
	virtual bool IsJediTargetAlive() const override { return !bDead; }
	virtual float GetJediHealthFraction() const override;

	UFUNCTION(BlueprintPure, Category = "Walker") float GetHP() const { return HP; }
	UFUNCTION(BlueprintPure, Category = "Walker") bool IsEnraged() const { return bRage; }
	UFUNCTION(BlueprintPure, Category = "Walker") bool IsCollapsed() const { return State == EBossWalkerState::Collapsed; }
	UFUNCTION(BlueprintPure, Category = "Walker") EBossWalkerState GetWalkerState() const { return State; }
	/** World position of a glowing knee weak point (0 = left, 1 = right). */
	UFUNCTION(BlueprintPure, Category = "Walker") FVector GetKneeLocation(int32 LegIndex) const;

	// ---------------------------------------------------------------- Health / weak points
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Walker|Health") float MaxHP = 160.f;
	/** Saber / bolt / generic hits landing within this distance of a knee count as weak-point hits. */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float WeakPointRadius = 90.f;
	/** Vertical distance to a knee is divided by this (the knee zone is a slightly tall ellipsoid, so low sweeps still count). */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float WeakPointVerticalStretch = 1.5f;
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float WeakPointMultiplier = 2.f;
	/** Anything that is not a knee: armour plating goes "tonk". */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float HullMultiplier = 0.35f;
	/** Every hit while it is down on its knees. */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float CollapsedMultiplier = 2.5f;
	/** Fraction of MaxHP lost between collapses. */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float CollapseStep = 0.25f;
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float CollapseDuration = 4.f;
	/** HP fraction at which it enters rage. */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") float RageThreshold = 0.5f;
	/** Ignore damage from other pawns (horde droids' bolts / explosions); only the player and non-pawn hazards hurt it. */
	UPROPERTY(EditAnywhere, Category = "Walker|Health") bool bIgnoreFriendlyFire = true;

	// ---------------------------------------------------------------- Movement / leash
	/** Stays within LeashRadius of this point (arena centre by default). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Walker|Movement") FVector LeashCenter = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Walker|Movement") float LeashRadius = 3600.f;
	/** Use the spawn location as LeashCenter instead. */
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") bool bLeashToSpawnPoint = false;
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") float WalkSpeed = 260.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") float RageWalkSpeed = 360.f;
	/** Body turn rate, degrees per second. */
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") float TurnRate = 60.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") float RageTurnRate = 100.f;
	/** Walks toward the player beyond this distance, strafes inside it. */
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") float ApproachRange = 1500.f;
	/** Shuffles backward when the player is closer than this. */
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") float BackOffRange = 520.f;
	/** Seconds between occasional comedic stumbles while walking (random range). */
	UPROPERTY(EditAnywhere, Category = "Walker|Movement") FVector2D StumbleInterval = FVector2D(10.f, 22.f);

	// ---------------------------------------------------------------- Procedural rig / gait
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float HipHeight = 400.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float CollapsedHipHeight = 160.f;
	/** Distance travelled per full walk cycle (both feet step once). */
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float StrideLength = 360.f;
	/** Turning in place: degrees of yaw per walk cycle. */
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float TurnStrideDegrees = 90.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float StepHeight = 70.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float BobAmount = 16.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Gait") float SwayDegrees = 3.5f;

	// ---------------------------------------------------------------- Attacks
	UPROPERTY(EditAnywhere, Category = "Walker|Attack") float AttackCooldown = 2.4f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack") float RageAttackCooldown = 1.5f;

	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") float VolleyTelegraph = 0.8f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") int32 VolleyShotsMin = 4;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") int32 VolleyShotsMax = 8;
	/** Extra shots per volley while enraged. */
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") int32 RageExtraShots = 4;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") float VolleyInterval = 0.16f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") float BoltDamage = 2.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") float BoltScale = 1.6f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") float BoltSpeed = 2300.f;
	/** Random aim error, degrees. */
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Volley") float BoltSpread = 2.5f;

	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompTelegraph = 0.6f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompTriggerRange = 750.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompRadius = 700.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompDamage = 2.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompLaunch = 1100.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompLift = 650.f;
	/** Damage dealt to its own (IJediDamageable) minions caught in a stomp. Oops. */
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Stomp") float StompMinionDamage = 0.5f;

	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Peck") float PeckTelegraph = 0.5f;
	/** Pecks when the player is closer than this (from the walker's centre) and in front. */
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Peck") float PeckRange = 480.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Peck") float PeckDamage = 2.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Peck") float PeckKnockback = 1300.f;
	/** Chance the beak gets stuck in the floor for a moment (free hits!). */
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Peck") float PeckStuckChance = 0.3f;

	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") int32 MissilesMin = 6;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") int32 MissilesMax = 10;
	/** Seconds from launch (and warning ring) to impact. */
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float MissileFlightTime = 1.2f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float MissileSpread = 550.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float MissileDamage = 1.5f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float MissileSplashDamage = 1.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float MissileSplashRadius = 260.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float MissileGravityScale = 1.5f;
	UPROPERTY(EditAnywhere, Category = "Walker|Attack|Barrage") float BarrageCooldown = 9.f;

	// ---------------------------------------------------------------- Intro / death
	/** Drop in from the sky on spawn (skipped automatically if there is a roof above the spawn point). */
	UPROPERTY(EditAnywhere, Category = "Walker|Intro") bool bDropIn = true;
	UPROPERTY(EditAnywhere, Category = "Walker|Intro") float DropHeight = 2200.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Death") float DeathSequenceTime = 2.5f;
	/** Debris lies around this long before the actor is destroyed. */
	UPROPERTY(EditAnywhere, Category = "Walker|Death") float DebrisLifetime = 15.f;
	UPROPERTY(EditAnywhere, Category = "Walker|Death") int32 KOValue = 50;

	// ---------------------------------------------------------------- Assets
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TSubclassOf<ABlasterBolt> BoltClass;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<UMaterialInterface> SurfaceMaterial;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<UMaterialInterface> WaveMaterial;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<UStaticMesh> SphereMesh;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<USoundBase> FireSound;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<USoundBase> ExplodeSound;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<USoundBase> StompSound;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<USoundBase> ClangSound;
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TObjectPtr<UNiagaraSystem> HitFX;
	/** Optional camera shake for stomps / landing. */
	UPROPERTY(EditAnywhere, Category = "Walker|Assets") TSubclassOf<UCameraShakeBase> StompShake;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// ---------------------------------------------------------------- Components (rig + scrap)
	/** Floor-level origin of the rig (capsule bottom). */
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USceneComponent> Rig;
	/** Hips: bobs up and down; legs hang from it. */
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USceneComponent> Pelvis;
	/** Cockpit pivot: sways, rolls, pecks, looks at the player. */
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USceneComponent> HullPivot;

	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> PelvisAxle;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> HullBody;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> EyeL;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> EyeR;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> HullRoof;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> SidePatch;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Beak;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> CannonL;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> CannonR;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Brow;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Antenna;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USceneComponent> FlagPivot;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> Flag;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USceneComponent> RadarPivot;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> RadarDish;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> ExhaustL;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> ExhaustR;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> MissileRack;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<USceneComponent> HulaPivot;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> HulaSkirt;
	UPROPERTY(VisibleAnywhere, Category = "Components") TObjectPtr<UStaticMeshComponent> HulaHead;

	// Legs: hip pivot -> thigh, knee pivot -> glowing knee + shin, ankle pivot -> foot + toe claw.
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<USceneComponent> HipPivotL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<USceneComponent> KneePivotL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<USceneComponent> AnklePivotL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> ThighL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> KneeJointL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> ShinL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> FootL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> ToeL;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<USceneComponent> HipPivotR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<USceneComponent> KneePivotR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<USceneComponent> AnklePivotR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> ThighR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> KneeJointR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> ShinR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> FootR;
	UPROPERTY(VisibleAnywhere, Category = "Components|Legs") TObjectPtr<UStaticMeshComponent> ToeR;

	UPROPERTY(Transient) TArray<FScrapPart> Parts;
	UPROPERTY(Transient) TArray<FScrapRing> Rings;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Puffs;

private:
	/** Runtime state of one leg (component pointers are owned by the UPROPERTYs above). */
	struct FLegState
	{
		USceneComponent* Hip = nullptr;
		USceneComponent* Knee = nullptr;
		USceneComponent* Ankle = nullptr;
		UStaticMeshComponent* KneeJoint = nullptr;
		float Side = -1.f;          // -1 left, +1 right
		FVector FootPos = FVector::ZeroVector;    // planted ground point (world)
		FVector SwingFrom = FVector::ZeroVector;
		FVector SwingTo = FVector::ZeroVector;
		FVector Ankle3D = FVector::ZeroVector;    // final IK target for the ankle (world)
		float FootPitch = 0.f;
		bool bSwinging = false;
		bool bOverride = false;     // stomp: ankle driven by the attack, not the gait
		FVector OverrideAnkle = FVector::ZeroVector;
	};

	struct FScrapMissile
	{
		TWeakObjectPtr<ABlasterBolt> Bolt;
		FVector Target = FVector::ZeroVector;
		FVector LastPos = FVector::ZeroVector;
		float ImpactTime = 0.f;
		int32 Ring = INDEX_NONE;
		int32 RingSerial = 0;
	};

	// construction helpers
	UStaticMeshComponent* MakePart(const TCHAR* Name, USceneComponent* Parent, UStaticMesh* ShapeMesh, const FVector& Loc, const FRotator& Rot, const FVector& Scale);
	USceneComponent* MakePivot(const TCHAR* Name, USceneComponent* Parent, const FVector& Loc);
	static void MakeHittable(UStaticMeshComponent* Comp);

	// setup
	void BuildParts();
	int32 AddPart(UStaticMeshComponent* PartMesh, const FLinearColor& Base, float Roughness, float Metallic, const FLinearColor& Emissive, float DebrisDelay);
	void CreatePuffs();

	// brain
	float Now() const;
	ACharacter* GetPlayer() const;
	bool IsTargetable(const ACharacter* Player) const;
	/** Still attached to the walker (not yet flying off as debris). */
	bool IsLive(const UStaticMeshComponent* Comp) const;
	void SetState(EBossWalkerState NewState);
	void NextStep();
	void FinishAttack(float ExtraCooldown = 0.f);
	void CancelAttack();
	void TurnToward(const FVector& Target, float Rate, float Dt);
	float CurrentTurnRate() const { return bRage ? RageTurnRate : TurnRate; }
	void ChooseAttack(ACharacter* Player, float Dist);

	void TickIntro(float Dt);
	void IntroImpact();
	void TickRoam(float Dt, ACharacter* Player);
	void TickVolley(float Dt, ACharacter* Player);
	void TickStomp(float Dt, ACharacter* Player);
	void TickPeck(float Dt, ACharacter* Player);
	void TickBarrage(float Dt, ACharacter* Player);
	void TickStagger(float Dt);
	void TickCollapse(float Dt);
	void TickDeath(float Dt);

	// attacks
	void FireCannon(int32 Side, ACharacter* Player);
	ABlasterBolt* SpawnBolt(const FVector& From, const FRotator& Aim, float Damage, float Scale, float Speed);
	void LaunchMissile(ACharacter* Player, int32 Index);
	void UpdateMissiles();
	void ExplodeMissile(const FVector& Where);
	void StompImpact(const FVector& Center, float Radius, float PlayerDamage, float MinionDamage);
	/** Hurts / launches the player around Center. Returns true if the player was caught. */
	bool ShockPlayer(const FVector& Center, float Radius, float Damage, float Launch, float Lift, bool bAirborneImmune);
	/** Flattens IJediDamageable minions (and shoves physics props) around Center. Returns how many minions got hit. */
	int32 HurtMinions(const FVector& Center, float Radius, float Damage, float Push, float Lift);
	FVector GroundBelow(const FVector& Point) const;

	// damage
	bool IsWeakPointHit(const FVector& Location, int32* OutLeg = nullptr) const;
	/** Damage from another enemy (or a bolt one of them fired). */
	bool IsFriendlyFire(const AActor* Causer) const;
	FVector EstimateHitLocation(AActor* Causer) const;
	/** WeakLeg = knee that was hit (0/1), or INDEX_NONE for a hull hit. */
	void HitFeedback(const FVector& Location, EJediHitKind Kind, int32 WeakLeg, float Damage);
	void TryStagger(const FVector& Impulse, bool bForce);
	void StartCollapse();
	void EnterRage();
	void Die(AActor* Killer);
	void FinalBlast();
	void PopPart(int32 Index, const FVector& Origin, float Strength);
	void ReportKO();
	int32 FindNearestPart(const FVector& Location) const;
	void Flash(int32 PartIndex, const FLinearColor& Color, float Amount = 1.f);

	// animation
	FVector NeutralFoot(int32 Leg) const;
	FVector LandingTarget(int32 Leg) const;
	void UpdateGait(float Dt);
	void OnFootPlanted(int32 Leg);
	void UpdatePose(float Dt);
	void SolveLegs();
	void UpdateDetails(float Dt);
	void UpdateFlashes(float Dt);
	void KickWobble(float PitchVel, float RollVel);
	void KickWobbleFrom(const FVector& WorldDir, float Strength);

	// fx
	int32 AcquireRing();
	int32 ShowWarningRing(const FVector& Center, float Radius, float Duration, const FLinearColor& Color, int32& OutSerial);
	void SpawnShockRing(const FVector& Center, float Radius0, float Radius1, float Duration, const FLinearColor& Color);
	void ReleaseRing(int32 Index, int32 Serial);
	void UpdateRings();
	void EmitPuff(const FVector& Location, float Size);
	void UpdatePuffs();
	void Sparks(const FVector& Location, int32 Count = 1, float Scale = 1.f);
	void PlaySoundAt(USoundBase* Sound, const FVector& Location, float Volume = 1.f, float Pitch = 1.f);
	void Shake(const FVector& Where, float Inner, float Outer);

	UFUNCTION()
	void OnHeadHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);

	// ---------------------------------------------------------------- state
	EBossWalkerState State = EBossWalkerState::Intro;
	EBossWalkerState LastAttack = EBossWalkerState::Roam;
	float StateTime = 0.f;
	float StepTime = 0.f;
	int32 StateStep = 0;

	float HP = 160.f;
	bool bDead = false;
	bool bRage = false;
	bool bRagePending = false;
	bool bKOReported = false;
	bool bFinalBlast = false;
	bool bIntroFalling = false;
	bool bIntroImpactDone = false;
	int32 CollapsesDone = 0;
	TWeakObjectPtr<AActor> LastDamageCauser;
	TWeakObjectPtr<AActor> KillerActor;

	float NextAttackTime = 0.f;
	float NextBarrageTime = 0.f;
	float StaggerImmuneUntil = 0.f;
	float SavedGravityScale = 1.f;

	// attack scratch
	int32 ShotsLeft = 0;
	int32 ShotIndex = 0;
	float NextShotTime = 0.f;
	int32 StompLeg = 0;
	FVector StompFrom = FVector::ZeroVector;
	FVector StompTo = FVector::ZeroVector;
	int32 StompRing = INDEX_NONE;
	int32 StompRingSerial = 0;
	bool bPeckStruck = false;
	bool bPeckStuck = false;
	bool bPeckParried = false;
	int32 MissilesLeft = 0;
	int32 MissileIndex = 0;
	float NextMissileTime = 0.f;
	TArray<FScrapMissile> Missiles;

	// locomotion
	FLegState Legs[2];
	float GaitPhase = 0.45f;
	float PrevYaw = 0.f;
	bool bGaitHold = false;
	float WalkAlpha = 0.f;
	float StrafeSign = 1.f;
	float NextStrafeFlip = 0.f;
	float NextStumbleTime = 0.f;
	float StumbleUntil = 0.f;

	// pose (targets are set by the state logic every tick, current values ease toward them)
	FVector PoseOffset = FVector::ZeroVector;
	FVector PoseOffsetTarget = FVector::ZeroVector;
	float PosePitch = 0.f;
	float PoseRoll = 0.f;
	float PosePitchTarget = 0.f;
	float PoseRollTarget = 0.f;
	float PoseSpeed = 6.f;
	float HullYaw = 0.f;
	float CollapseAlpha = 0.f;
	FVector2D Wobble = FVector2D::ZeroVector;      // pitch, roll (degrees)
	FVector2D WobbleVel = FVector2D::ZeroVector;
	float Dip = 0.f;
	float DipVel = 0.f;

	// details
	float RadarYaw = 0.f;
	float NextBlinkTime = 0.f;
	float BlinkUntil = 0.f;
	float EyeFlickerUntil = 0.f;
	float EyeSquint = 1.f;
	float CannonCharge = 0.f;
	float RackCharge = 0.f;
	float RackOpen = 0.f;
	float Recoil[2] = { 0.f, 0.f };
	float ExhaustKick[2] = { 0.f, 0.f };
	float NextPuffTime = 0.f;
	int32 PuffSide = 0;
	int32 NextPuff = 0;
	TArray<float> PuffStart;
	TArray<FVector> PuffOrigin;
	TArray<FVector> PuffDrift;
	TArray<float> PuffSize;
	float LastClangTime = -10.f;
	float LastSparkTime = -10.f;
	float LastFriendlyFireBanner = -100.f;

	// cached rest transforms for animated parts
	FVector CannonBase[2];
	FVector ExhaustBaseScale[2];
	FVector EyeLBaseScale = FVector::OneVector;
	FVector EyeRBaseScale = FVector::OneVector;
	FVector HulaHeadBase = FVector::ZeroVector;
	FRotator RackBaseRot = FRotator::ZeroRotator;

	// part indices into Parts
	int32 HullPart = INDEX_NONE;
	int32 EyeLPart = INDEX_NONE;
	int32 EyeRPart = INDEX_NONE;
	int32 CannonPart[2] = { INDEX_NONE, INDEX_NONE };
	int32 ExhaustPart[2] = { INDEX_NONE, INDEX_NONE };
	int32 KneePart[2] = { INDEX_NONE, INDEX_NONE };
	int32 RackPart = INDEX_NONE;
	int32 RingSerialCounter = 0;

	// death
	float DeathElapsed = 0.f;
	float NextDeathBoom = 0.f;
	int32 HeadBounces = 0;
	float LastBounceTime = -10.f;
	FVector HeadPrevVelocity = FVector::ZeroVector;
};
