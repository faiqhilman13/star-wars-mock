#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "JediDamageable.h"
#include "HordeEnemy.generated.h"

class ABlasterBolt;
class UStaticMesh;
class UStaticMeshComponent;
class UTextRenderComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class USoundBase;
class UAnimSequenceBase;
class UNiagaraSystem;
class USkeletalMesh;
class AHordePickup;
class UAnimMontage;
class UAudioComponent;

UENUM(BlueprintType)
enum class EHordeType : uint8
{
	Clanker,   // skinny battle droids: fodder, one hit, terrible aim, chatty
	Bulwark,   // troopers behind a frontal energy shield (break it with the Force or flank)
	Roller,    // rolling ball droids that unfurl into shielded turrets
	JetGhost,  // jetpack troopers hovering overhead firing rockets (Force Pull them down)
	Warden     // electrostaff melee elites that guard and must be parried
};

/**
 * A horde enemy for the colosseum. One C++ class drives all types (EHordeType); the small
 * subclasses below just pick a type. No AI controller: movement is steered directly
 * (CharacterMovement with bRunPhysicsWithNoController), with separation from other enemies,
 * pit avoidance and attack tokens from AHordeDirector so only a few attack at once.
 */
UCLASS()
class JEDIARENA_API AHordeEnemy : public ACharacter, public IJediDamageable
{
	GENERATED_BODY()

public:
	AHordeEnemy();

	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
	virtual void Landed(const FHitResult& Hit) override;

	// IJediDamageable
	virtual float ReceiveJediHit(float Damage, AActor* Causer, const FVector& Location, const FVector& Impulse, EJediHitKind Kind) override;
	virtual bool IsJediTargetAlive() const override { return !bDead; }
	virtual float GetJediHealthFraction() const override { return MaxHP > 0.f ? HP / MaxHP : 0.f; }
	virtual float GetJediHealth() const override { return bDead ? 0.f : HP; }

	bool IsDead() const { return bDead; }

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde") EHordeType Type = EHordeType::Clanker;
	UPROPERTY(EditAnywhere, Category = "Horde") float MaxHP = 1.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float MoveSpeed = 360.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float PreferredMinRange = 650.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float PreferredMaxRange = 1300.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float AttackRange = 1900.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float FireIntervalMin = 2.4f;
	UPROPERTY(EditAnywhere, Category = "Horde") float FireIntervalMax = 4.5f;
	UPROPERTY(EditAnywhere, Category = "Horde") int32 BurstCount = 1;
	UPROPERTY(EditAnywhere, Category = "Horde") float BoltDamage = 0.5f;
	UPROPERTY(EditAnywhere, Category = "Horde") float BoltSpeed = 2200.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float BoltScale = 1.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float Inaccuracy = 5.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float MeleeDamage = 1.5f;
	UPROPERTY(EditAnywhere, Category = "Horde") float LaunchScale = 1.f;
	UPROPERTY(EditAnywhere, Category = "Horde") int32 KOValue = 1;
	UPROPERTY(EditAnywhere, Category = "Horde") float PickupChance = 0.07f;
	UPROPERTY(EditAnywhere, Category = "Horde") float BodyScale = 1.f;
	UPROPERTY(EditAnywhere, Category = "Horde") TSubclassOf<ABlasterBolt> BoltClass;
	UPROPERTY(EditAnywhere, Category = "Horde") TSubclassOf<AHordePickup> PickupClass;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// ---------- shared assets (constructor-loaded) ----------
	UPROPERTY() TObjectPtr<USkeletalMesh> MannyMesh;
	UPROPERTY() TObjectPtr<USkeletalMesh> QuinnMesh;
	// Custom enemy models (Blender, rigged to the mannequin skeleton): art/enemies/*.py
	UPROPERTY() TObjectPtr<USkeletalMesh> ClankerModel;
	UPROPERTY() TObjectPtr<USkeletalMesh> BulwarkModel;
	UPROPERTY() TObjectPtr<USkeletalMesh> JetGhostModel;
	UPROPERTY() TObjectPtr<USkeletalMesh> WardenModel;
	UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> DeathSounds;
	/** Magna Warden: the Jedi saberstaff combo set (same grip, so the electrostaff moves like a saberstaff). */
	UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequenceBase>> StaffComboAnims;
	/** Jet Ghost: full-body loop while flying (stops the ground locomotion from jogging in mid-air). */
	UPROPERTY(Transient) TObjectPtr<UAnimSequenceBase> HoverAnim;
	UPROPERTY(Transient) TObjectPtr<USoundBase> JetLoopSound;
	UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> RocketSounds;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> EngineAudio;
	UPROPERTY() TObjectPtr<UClass> AnimClass;
	UPROPERTY() TObjectPtr<UMaterialInterface> SurfaceMat;
	UPROPERTY() TObjectPtr<UMaterialInterface> WaveMat;
	UPROPERTY() TObjectPtr<UStaticMesh> CubeMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> SphereMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> CylinderMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> ConeMesh;
	UPROPERTY() TObjectPtr<UAnimSequenceBase> AimAnim;
	UPROPERTY() TObjectPtr<UAnimSequenceBase> FireAnim;
	UPROPERTY() TArray<TObjectPtr<UAnimSequenceBase>> HitReactAnims;
	UPROPERTY() TArray<TObjectPtr<UAnimSequenceBase>> MeleeAnims;
	UPROPERTY() TObjectPtr<USoundBase> FireSound;
	UPROPERTY() TObjectPtr<USoundBase> ClangSound;
	UPROPERTY() TObjectPtr<USoundBase> PopSound;
	UPROPERTY() TObjectPtr<USoundBase> WhooshSound;
	UPROPERTY() TObjectPtr<UNiagaraSystem> SparkFX;

	// ---------- per-type parts ----------
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Parts;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Muzzle;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> ShieldMesh;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RollerBall;
	UPROPERTY(Transient) TObjectPtr<USceneComponent> RollerTurret;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> RollerLegs;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> JetFlames;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> ShieldMID;
	UPROPERTY(Transient) TObjectPtr<UTextRenderComponent> Chatter;

private:
	enum class EState : uint8 { Approach, Aim, Melee, Stagger, Airborne, Rolling, Deploying, Deployed, Hover, Stunned, Dead };
	enum class EJetMode : uint8 { Cruise, SwoopIn, SwoopOut, HoverShot };

	void BuildLooks();
	UMaterialInstanceDynamic* MakeMat(const FLinearColor& Color, float Roughness, float Metallic, const FLinearColor& Emissive = FLinearColor::Black);
	UStaticMeshComponent* AddPart(UStaticMesh* PartMesh, USceneComponent* Parent, FName Socket, const FVector& Loc, const FRotator& Rot, const FVector& Scale, UMaterialInterface* Mat);

	void TickGround(float Dt, ACharacter* Player);
	void TickRoller(float Dt, ACharacter* Player);
	void TickJet(float Dt, ACharacter* Player);
	void TickWarden(float Dt, ACharacter* Player);
	void StartWardenSwing(int32 Index, bool bFast, bool bChained);
	void UpdateJetVisuals(float Dt);
	void FireBolt(ACharacter* Player, float Damage, float Speed, float Scale, float Spread, USoundBase* Sound, float Volume, float Pitch);
	FVector SteerAround(const FVector& Desired) const;
	void FaceToward(const FVector& Target, float Dt, float DegPerSec);
	void BeginAim();
	void FireAt(ACharacter* Player);
	void DoMeleeHit();
	void Stagger(float Seconds);
	void Launch(const FVector& Impulse);
	void Die(AActor* Killer, const FVector& Impulse, EJediHitKind Kind);
	void BreakShield(float Seconds);
	void Say(const TCHAR* Line, float Seconds = 1.6f);
	void Say(const TArray<const TCHAR*>& Lines, float Chance);
	void PlayDeathSound();
	void SetRollerDeployed(float Alpha);
	float Now() const;

	EState State = EState::Approach;
	float HP = 1.f;
	bool bDead = false;
	float StateUntil = 0.f;
	float NextFireTime = 0.f;
	float NextMeleeTime = 0.f;
	float MeleeHitTime = -1.f;
	int32 BurstLeft = 0;
	float NextBurstShot = 0.f;
	float StrafeSign = 1.f;
	float NextStrafeFlip = 0.f;
	float ChatterUntil = 0.f;
	float GroundZ = 0.f;
	float HoverAltitude = 520.f;
	float OrbitAngle = 0.f;
	float ShieldHP = 0.f;
	float ShieldDownUntil = 0.f;
	float LightningOnShield = 0.f;
	float DeployAlpha = 0.f;
	float RollAngle = 0.f;
	TWeakObjectPtr<AActor> LastHitter;

	// Jet Ghost flight
	EJetMode JetMode = EJetMode::Cruise;
	float JetModeUntil = 0.f;
	FVector SwoopTarget = FVector::ZeroVector;
	FVector SwoopExit = FVector::ZeroVector;
	int32 SwoopShots = 0;
	float NextSwoopShot = 0.f;
	bool bRocketFired = false;
	float OrbitRadius = 1100.f;
	float LeanPitch = 0.f;
	float LeanRoll = 0.f;
	FVector MeshBaseLoc = FVector::ZeroVector;
	FQuat MeshBaseRot = FQuat::Identity;
	float SputterUntil = 0.f;

	// Magna Warden melee
	TWeakObjectPtr<UAnimMontage> SwingMontage;
	TArray<float> SwingHits;   // anim-time (s) of each strike in the current swing
	int32 NextSwingHit = 0;
	int32 ComboStep = 0;
	int32 CombosLeft = 0;
	float SwingRate = 1.f;
	float SwingChainPos = 0.f;
	float SwingStart = 0.f;
	float SwingTellUntil = 0.f;
	bool bSwingCommitted = false;
	bool bLeapPending = false;
	bool bRiposte = false;
	float NextLeapTime = 0.f;

	static TArray<TWeakObjectPtr<AHordeEnemy>> AllEnemies;
};

UCLASS() class JEDIARENA_API AClankerDroid : public AHordeEnemy { GENERATED_BODY() public: AClankerDroid(); };
UCLASS() class JEDIARENA_API ABulwarkTrooper : public AHordeEnemy { GENERATED_BODY() public: ABulwarkTrooper(); };
UCLASS() class JEDIARENA_API ABuzzRoller : public AHordeEnemy { GENERATED_BODY() public: ABuzzRoller(); };
UCLASS() class JEDIARENA_API AJetGhost : public AHordeEnemy { GENERATED_BODY() public: AJetGhost(); };
UCLASS() class JEDIARENA_API AMagnaWarden : public AHordeEnemy { GENERATED_BODY() public: AMagnaWarden(); };

/** Glowing orb dropped by enemies: green heals, blue restores Force. Drifts to the Jedi when close. */
UCLASS()
class JEDIARENA_API AHordePickup : public AActor
{
	GENERATED_BODY()

public:
	AHordePickup();
	virtual void Tick(float DeltaSeconds) override;
	void Init(bool bHealth);

	UPROPERTY(EditAnywhere, Category = "Pickup") float HealAmount = 2.f;
	UPROPERTY(EditAnywhere, Category = "Pickup") float ForceAmount = 25.f;
	UPROPERTY(EditAnywhere, Category = "Pickup") float MagnetRange = 500.f;

protected:
	UPROPERTY(VisibleAnywhere, Category = "Pickup") TObjectPtr<UStaticMeshComponent> Orb;
	UPROPERTY() TObjectPtr<UMaterialInterface> SurfaceMat;
	UPROPERTY() TObjectPtr<USoundBase> CollectSound;

private:
	bool bIsHealth = true;
	float Age = 0.f;
	FVector BaseLoc;
};
