#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HordeDirector.generated.h"

class AHordeEnemy;
class AColosseumArena;
class ADropPod;
class USoundBase;

/** One group of enemies inside a wave. */
USTRUCT(BlueprintType)
struct FHordeSpawnGroup
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") TSubclassOf<AActor> EnemyClass;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") int32 Count = 8;
	/** Seconds after the wave starts before this group begins spawning. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") float Delay = 0.f;
	/** Arrive by drop pod from the sky instead of marching through a gate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") bool bDropPod = false;
	/** Announce this group when it arrives (officers, elites). Empty = silent. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") FString Announcement;
};

USTRUCT(BlueprintType)
struct FHordeWave
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") FString Title;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") TArray<FHordeSpawnGroup> Groups;
	/** Boss wave: the wave ends when the boss dies (fodder groups keep trickling in). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") bool bBossWave = false;
};

/**
 * Runs the Dynasty-Warriors style arena: waves of enemies through the colosseum gates and drop pods,
 * KO counting, attack tokens (only a few enemies shoot/strike at once), announcements and crowd hype.
 * Place one in the level; everything else finds it with AHordeDirector::Get().
 */
UCLASS()
class JEDIARENA_API AHordeDirector : public AActor
{
	GENERATED_BODY()

public:
	AHordeDirector();

	static AHordeDirector* Get(const UObject* WorldContext);

	/** An enemy died. Killer may be null (environment). Value = KOs it's worth. */
	void NotifyKO(AActor* Victim, AActor* Killer, int32 Value = 1);

	/** Big centre-screen banner. */
	void Announce(const FString& Text, float Duration = 2.5f, FLinearColor Color = FLinearColor::White);

	/** Crowd excitement (0..100); the arena's crowd bounces with it. */
	void AddHype(float Amount);

	/** Tracks a spawned enemy (horde enemies register themselves; others are registered by their spawner). */
	void RegisterEnemy(AActor* Enemy);

	/** Registers the current boss for the HUD boss bar. */
	void SetBoss(AActor* Boss, const FString& BossName);

	/** Attack tokens: only MaxShooters ranged / MaxMeleeAttackers melee enemies attack at once. */
	bool RequestAttackToken(AActor* Enemy, bool bMelee, float Duration);

	int32 GetKOs() const { return KOs; }
	int32 GetWaveNumber() const { return WaveIndex + 1; }
	int32 GetWaveCount() const { return Waves.Num(); }
	FString GetWaveTitle() const;
	int32 GetAliveEnemies() const;
	float GetHype() const { return Hype; }
	bool IsVictory() const { return bVictory; }
	float GetElapsed() const;
	AActor* GetBoss() const { return Boss.Get(); }
	const FString& GetBossName() const { return BossName; }

	struct FBanner { FString Text; FLinearColor Color; float Until; float Start; };
	const TArray<FBanner>& GetBanners() const { return Banners; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Horde") TArray<FHordeWave> Waves;
	UPROPERTY(EditAnywhere, Category = "Horde") int32 MaxAlive = 45;
	UPROPERTY(EditAnywhere, Category = "Horde") int32 MaxShooters = 5;
	UPROPERTY(EditAnywhere, Category = "Horde") int32 MaxMeleeAttackers = 3;
	UPROPERTY(EditAnywhere, Category = "Horde") float SpawnInterval = 0.35f;
	UPROPERTY(EditAnywhere, Category = "Horde") float TimeBetweenWaves = 4.f;
	UPROPERTY(EditAnywhere, Category = "Horde") float FirstWaveDelay = 3.f;
	UPROPERTY(EditAnywhere, Category = "Horde") TSubclassOf<ADropPod> DropPodClass;
	UPROPERTY(EditAnywhere, Category = "Horde") TObjectPtr<USoundBase> CrowdCheerSound;
	UPROPERTY(EditAnywhere, Category = "Horde") TObjectPtr<USoundBase> AnnounceSound;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	void StartWave(int32 Index);
	bool WaveCleared() const;
	void BuildDefaultWaves();
	AColosseumArena* Arena() const;

	struct FPendingGroup { const FHordeSpawnGroup* Group; int32 Remaining; float NextTime; bool bAnnounced; int32 Gate; };
	void SpawnFromGroup(FPendingGroup& Pending);
	void Victory();
	FHordeSpawnGroup TrickleGroup;
	float NextTrickleTime = 0.f;
	float LastKOTime = 0.f;
	void RoundUpStragglers();
	bool bBetweenWaves = true;
	TArray<FPendingGroup> Pending;
	TArray<TWeakObjectPtr<AActor>> Alive;
	TMap<TWeakObjectPtr<AActor>, float> ShooterTokens;
	TMap<TWeakObjectPtr<AActor>, float> MeleeTokens;
	TArray<FBanner> Banners;
	TWeakObjectPtr<AActor> Boss;
	FString BossName;
	mutable TWeakObjectPtr<AColosseumArena> CachedArena;

	int32 WaveIndex = -1;
	int32 KOs = 0;
	int32 NextMilestone = 50;
	float Hype = 0.f;
	float WaveStartTime = 0.f;
	float NextWaveTime = -1.f;
	float StartTime = 0.f;
	float EndTime = -1.f;
	bool bVictory = false;
	int32 NextGate = 0;
};
