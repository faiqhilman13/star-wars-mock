#include "HordeDirector.h"

#include "BossWalker.h"
#include "ColosseumArena.h"
#include "DropPod.h"
#include "HordeEnemy.h"
#include "JediCharacter.h"
#include "JediDamageable.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "UObject/UObjectIterator.h"
#include "GameFramework/Character.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

AHordeDirector::AHordeDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	DropPodClass = ADropPod::StaticClass();
	static ConstructorHelpers::FObjectFinder<USoundBase> Boom(TEXT("/Game/Jedi/Audio/SW_Force_Push.SW_Force_Push"));
	AnnounceSound = Boom.Object;
}

AHordeDirector* AHordeDirector::Get(const UObject* WorldContext)
{
	static TWeakObjectPtr<AHordeDirector> Cached;
	UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	if (!World)
	{
		return nullptr;
	}
	if (Cached.IsValid() && Cached->GetWorld() == World)
	{
		return Cached.Get();
	}
	Cached = nullptr;
	for (TActorIterator<AHordeDirector> It(World); It; ++It)
	{
		Cached = *It;
		break;
	}
	return Cached.Get();
}

AColosseumArena* AHordeDirector::Arena() const
{
	if (!CachedArena.IsValid())
	{
		for (TActorIterator<AColosseumArena> It(GetWorld()); It; ++It)
		{
			CachedArena = *It;
			break;
		}
	}
	return CachedArena.Get();
}

void AHordeDirector::BuildDefaultWaves()
{
	auto Group = [](TSubclassOf<AActor> Class, int32 Count, float Delay, bool bPod = false, const TCHAR* Say = TEXT(""))
	{
		FHordeSpawnGroup G;
		G.EnemyClass = Class;
		G.Count = Count;
		G.Delay = Delay;
		G.bDropPod = bPod;
		G.Announcement = Say;
		return G;
	};
	UClass* Clanker = AClankerDroid::StaticClass();
	UClass* Bulwark = ABulwarkTrooper::StaticClass();
	UClass* Roller = ABuzzRoller::StaticClass();
	UClass* Jet = AJetGhost::StaticClass();
	UClass* Warden = AMagnaWarden::StaticClass();
	UClass* Acolyte = LoadClass<AActor>(nullptr, TEXT("/Game/Jedi/Blueprints/BP_SithEnemy.BP_SithEnemy_C"));

	Waves.Reset();
	{
		FHordeWave W;
		W.Title = TEXT("Rattle & Roll");
		W.Groups = { Group(Clanker, 10, 0.f), Group(Clanker, 10, 4.f), Group(Clanker, 10, 9.f, true, TEXT("Drop pods inbound!")) };
		Waves.Add(W);
	}
	{
		FHordeWave W;
		W.Title = TEXT("Shields Up!");
		W.Groups = { Group(Clanker, 14, 0.f), Group(Bulwark, 4, 3.f, false, TEXT("BULWARK TROOPERS - break their shields with the Force!")),
			Group(Clanker, 12, 10.f, true), Group(Bulwark, 2, 14.f) };
		Waves.Add(W);
	}
	{
		FHordeWave W;
		W.Title = TEXT("Bowling Night");
		W.Groups = { Group(Roller, 4, 0.f, false, TEXT("BUZZ-ROLLERS - fry their shields with lightning!")), Group(Clanker, 18, 2.f),
			Group(Bulwark, 3, 8.f, true), Group(Roller, 3, 14.f) };
		Waves.Add(W);
	}
	{
		FHordeWave W;
		W.Title = TEXT("Death From Above");
		W.Groups = { Group(Jet, 5, 0.f, false, TEXT("JET GHOSTS - Force Pull them out of the sky!")), Group(Clanker, 20, 3.f, true),
			Group(Bulwark, 4, 8.f), Group(Jet, 3, 15.f), Group(Roller, 2, 18.f) };
		Waves.Add(W);
	}
	{
		FHordeWave W;
		W.Title = TEXT("The Warden's Gauntlet");
		W.Groups = { Group(Warden, 3, 0.f, false, TEXT("MAGNA WARDENS - parry their strikes!")), Group(Clanker, 24, 2.f),
			Group(Roller, 3, 9.f, true), Group(Warden, 2, 14.f) };
		if (Acolyte)
		{
			W.Groups.Add(Group(Acolyte, 2, 18.f, false, TEXT("Sith Acolytes join the fray!")));
		}
		Waves.Add(W);
	}
	{
		FHordeWave W;
		W.Title = TEXT("The Scrap Colossus");
		W.bBossWave = true;
		W.Groups = { Group(ABossWalker::StaticClass(), 1, 1.5f), Group(Clanker, 12, 5.f), Group(Jet, 2, 12.f) };
		Waves.Add(W);
	}
	TrickleGroup = Group(Clanker, 6, 0.f, true);
}

void AHordeDirector::BeginPlay()
{
	Super::BeginPlay();
	if (Waves.Num() == 0)
	{
		BuildDefaultWaves();
	}
	else if (!TrickleGroup.EnemyClass)
	{
		TrickleGroup.EnemyClass = AClankerDroid::StaticClass();
		TrickleGroup.Count = 6;
		TrickleGroup.bDropPod = true;
	}
	StartTime = GetWorld()->GetTimeSeconds();
	NextWaveTime = StartTime + FirstWaveDelay;
	bBetweenWaves = true;
	Announce(TEXT("THE DUNEGLASS COLOSSEUM"), 3.f, FLinearColor(1.f, 0.78f, 0.35f));
	FTimerHandle Handle;
	GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateWeakLambda(this, [this]()
	{
		Announce(TEXT("One Jedi. Endless droids. Good luck!"), 2.5f);
	}), 1.6f, false);
}

void AHordeDirector::Announce(const FString& Text, float Duration, FLinearColor Color)
{
	const float T = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	Banners.Add({ Text, Color, T + Duration, T });
	while (Banners.Num() > 3)
	{
		Banners.RemoveAt(0);
	}
	if (AnnounceSound)
	{
		UGameplayStatics::PlaySound2D(this, AnnounceSound, 0.25f, 0.55f);
	}
}

void AHordeDirector::AddHype(float Amount)
{
	Hype = FMath::Clamp(Hype + Amount, 0.f, 100.f);
}

void AHordeDirector::RegisterEnemy(AActor* Enemy)
{
	if (IsValid(Enemy) && !Alive.Contains(Enemy))
	{
		Alive.Add(Enemy);
	}
}

void AHordeDirector::SetBoss(AActor* InBoss, const FString& InName)
{
	Boss = InBoss;
	BossName = InName;
	RegisterEnemy(InBoss);
}

void AHordeDirector::NotifyKO(AActor* Victim, AActor* Killer, int32 Value)
{
	Alive.Remove(Victim);
	++KOs;
	LastKOTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	AddHype(0.8f * Value);
	if (AJediCharacter* Jedi = Cast<AJediCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0)))
	{
		Jedi->AddSurge(Jedi->GetSurgePerKO() * Value);
	}
	if (KOs >= NextMilestone)
	{
		Announce(FString::Printf(TEXT("%d KO!"), NextMilestone), 2.f, FLinearColor(1.f, 0.55f, 0.15f));
		AddHype(20.f);
		NextMilestone += NextMilestone < 100 ? 50 : 100;
	}
}

bool AHordeDirector::RequestAttackToken(AActor* Enemy, bool bMelee, float Duration)
{
	const float T = GetWorld()->GetTimeSeconds();
	TMap<TWeakObjectPtr<AActor>, float>& Tokens = bMelee ? MeleeTokens : ShooterTokens;
	for (auto It = Tokens.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid() || It.Value() < T)
		{
			It.RemoveCurrent();
		}
	}
	if (float* Existing = Tokens.Find(Enemy))
	{
		*Existing = T + Duration;
		return true;
	}
	if (Tokens.Num() >= (bMelee ? MaxMeleeAttackers : MaxShooters))
	{
		return false;
	}
	Tokens.Add(Enemy, T + Duration);
	return true;
}

FString AHordeDirector::GetWaveTitle() const
{
	return Waves.IsValidIndex(WaveIndex) ? Waves[WaveIndex].Title : FString();
}

int32 AHordeDirector::GetAliveEnemies() const
{
	int32 N = 0;
	for (const TWeakObjectPtr<AActor>& A : Alive)
	{
		if (A.IsValid())
		{
			const IJediDamageable* D = Cast<IJediDamageable>(A.Get());
			if (!D || D->IsJediTargetAlive())
			{
				++N;
			}
		}
	}
	return N;
}

float AHordeDirector::GetElapsed() const
{
	const float T = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	return (EndTime > 0.f ? EndTime : T) - StartTime;
}

void AHordeDirector::StartWave(int32 Index)
{
	WaveIndex = Index;
	bBetweenWaves = false;
	NextWaveTime = -1.f;
	const float T = GetWorld()->GetTimeSeconds();
	WaveStartTime = T;
	LastKOTime = T;
	Pending.Reset();
	const int32 Gates = Arena() ? FMath::Max(Arena()->NumGates(), 1) : 1;
	for (const FHordeSpawnGroup& G : Waves[Index].Groups)
	{
		if (G.EnemyClass && G.Count > 0)
		{
			Pending.Add({ &G, G.Count, T + G.Delay, false, (NextGate++) % Gates });
		}
	}
	const FHordeWave& Wave = Waves[Index];
	Announce(FString::Printf(TEXT("WAVE %d: %s"), Index + 1, *Wave.Title), 3.f, Wave.bBossWave ? FLinearColor(1.f, 0.25f, 0.2f) : FLinearColor(1.f, 0.8f, 0.3f));
	AddHype(10.f);
	NextTrickleTime = T + 20.f;
}

void AHordeDirector::SpawnFromGroup(FPendingGroup& P)
{
	const FHordeSpawnGroup& G = *P.Group;
	UWorld* World = GetWorld();
	AColosseumArena* A = Arena();
	ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const FVector PlayerLoc = Player ? Player->GetActorLocation() : FVector::ZeroVector;

	if (G.bDropPod && DropPodClass)
	{
		const int32 N = FMath::Min(P.Remaining, 5);
		FVector Site = A ? A->GetRandomDropSite() : PlayerLoc + FRotator(0.f, FMath::FRandRange(0.f, 360.f), 0.f).Vector() * 1200.f;
		// Land near the action but not on the Jedi's head.
		if (A && Player)
		{
			for (int32 Try = 0; Try < 6; ++Try)
			{
				const float D = FVector::Dist2D(Site, PlayerLoc);
				if (D > 700.f && D < 2600.f)
				{
					break;
				}
				Site = A->GetRandomDropSite();
			}
		}
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (ADropPod* Pod = World->SpawnActor<ADropPod>(DropPodClass, Site, FRotator::ZeroRotator, Params))
		{
			Pod->Launch(Site, G.EnemyClass, N);
		}
		P.Remaining -= N;
		P.NextTime = World->GetTimeSeconds() + 1.1f;
		return;
	}

	const bool bBoss = G.EnemyClass->IsChildOf(ABossWalker::StaticClass());
	FVector Loc;
	FRotator Rot;
	if (A && A->NumGates() > 0)
	{
		const FTransform Gate = A->GetGateSpawnTransform(P.Gate);
		Rot = Gate.Rotator();
		const FVector Right = FRotationMatrix(Rot).GetScaledAxis(EAxis::Y);
		const FVector Fwd = Rot.Vector();
		Loc = Gate.GetLocation() + Right * FMath::FRandRange(-170.f, 170.f) + Fwd * FMath::FRandRange(0.f, 200.f);
		if (bBoss)
		{
			Loc = Gate.GetLocation() + Fwd * 700.f;
		}
		A->OpenGate(P.Gate, bBoss ? 6.f : 3.f);
	}
	else
	{
		Rot = FRotator(0.f, FMath::FRandRange(0.f, 360.f), 0.f);
		Loc = PlayerLoc + Rot.Vector() * 2400.f;
		Rot = (PlayerLoc - Loc).GetSafeNormal2D().Rotation();
	}
	Loc.Z += bBoss ? 380.f : 100.f;
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	if (AActor* Enemy = World->SpawnActor<AActor>(G.EnemyClass, Loc, Rot, Params))
	{
		// Blueprint enemies (e.g. the template's Sith) need their AI controller when spawned from code.
		if (APawn* Pawn = Cast<APawn>(Enemy); Pawn && !Pawn->GetController() && Pawn->AIControllerClass)
		{
			Pawn->SpawnDefaultController();
		}
		RegisterEnemy(Enemy);
	}
	--P.Remaining;
	P.NextTime = World->GetTimeSeconds() + (bBoss ? 3.f : SpawnInterval);
}

bool AHordeDirector::WaveCleared() const
{
	if (Waves.IsValidIndex(WaveIndex) && Waves[WaveIndex].bBossWave)
	{
		// The boss wave ends when the boss falls (it has spawned once Boss was registered).
		const IJediDamageable* B = Cast<IJediDamageable>(Boss.Get());
		return !BossName.IsEmpty() && (!Boss.IsValid() || (B && !B->IsJediTargetAlive()));
	}
	for (const FPendingGroup& P : Pending)
	{
		if (P.Remaining > 0)
		{
			return false;
		}
	}
	return GetAliveEnemies() == 0;
}

void AHordeDirector::RoundUpStragglers()
{
	AColosseumArena* A = Arena();
	const ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	if (!A || !Player)
	{
		return;
	}
	const FVector PlayerLoc = Player->GetActorLocation();
	for (const TWeakObjectPtr<AActor>& W : Alive)
	{
		AActor* E = W.Get();
		if (!E || E->IsA(ABossWalker::StaticClass()))
		{
			continue;
		}
		FVector Site = A->GetRandomDropSite();
		for (int32 Try = 0; Try < 8; ++Try)
		{
			const float D = FVector::Dist2D(Site, PlayerLoc);
			if (D > 600.f && D < 1600.f)
			{
				break;
			}
			Site = A->GetRandomDropSite();
		}
		E->TeleportTo(Site + FVector(0.f, 0.f, 130.f), (PlayerLoc - Site).GetSafeNormal2D().Rotation());
	}
	Announce(TEXT("Stragglers dragged back into the fight!"), 2.5f, FLinearColor(1.f, 0.7f, 0.4f));
}

void AHordeDirector::Victory()
{
	bVictory = true;
	EndTime = GetWorld()->GetTimeSeconds();
	Pending.Reset();
	const int32 Secs = FMath::RoundToInt(GetElapsed());
	Announce(TEXT("ARENA CHAMPION!"), 8.f, FLinearColor(1.f, 0.85f, 0.3f));
	Announce(FString::Printf(TEXT("%d KO  -  %d:%02d"), KOs, Secs / 60, Secs % 60), 8.f);
	AddHype(100.f);
	// The leftovers short-circuit in shame.
	for (const TWeakObjectPtr<AActor>& A : Alive)
	{
		if (IJediDamageable* D = Cast<IJediDamageable>(A.Get()); D && D->IsJediTargetAlive())
		{
			D->ReceiveJediHit(9999.f, nullptr, A->GetActorLocation(), FVector(0.f, 0.f, 600.f), EJediHitKind::Environment);
		}
	}
}

void AHordeDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = GetWorld()->GetTimeSeconds();
	Banners.RemoveAll([T](const FBanner& B) { return B.Until < T; });

	// Enemies that vanished without reporting (e.g. template Blueprint enemies) still count as KOs.
	for (int32 i = Alive.Num() - 1; i >= 0; --i)
	{
		if (!Alive[i].IsValid())
		{
			Alive.RemoveAt(i);
			++KOs;
		}
	}

	Hype = FMath::Max(0.f, Hype - DeltaSeconds * 1.5f);
	if (AColosseumArena* A = Arena())
	{
		A->SetCrowdHype(Hype / 100.f);
	}
	if (bVictory || Waves.Num() == 0)
	{
		return;
	}

	if (bBetweenWaves)
	{
		if (NextWaveTime > 0.f && T >= NextWaveTime && Waves.IsValidIndex(WaveIndex + 1))
		{
			StartWave(WaveIndex + 1);
		}
		return;
	}

	const int32 AliveNow = GetAliveEnemies();
	for (FPendingGroup& P : Pending)
	{
		if (P.Remaining > 0 && T >= P.NextTime && AliveNow < MaxAlive)
		{
			if (!P.bAnnounced && !P.Group->Announcement.IsEmpty())
			{
				Announce(P.Group->Announcement, 3.f, FLinearColor(0.6f, 0.9f, 1.f));
			}
			P.bAnnounced = true;
			SpawnFromGroup(P);
		}
	}

	const FHordeWave& Wave = Waves[WaveIndex];
	if (Wave.bBossWave && Boss.IsValid() && T >= NextTrickleTime && AliveNow < MaxAlive / 2 && TrickleGroup.EnemyClass)
	{
		Pending.Add({ &TrickleGroup, TrickleGroup.Count, T, true, (NextGate++) % FMath::Max(Arena() ? Arena()->NumGates() : 1, 1) });
		NextTrickleTime = T + 14.f;
	}

	// Nobody likes a wave stuck on one enemy hiding behind a gate.
	bool bPendingDone = true;
	for (const FPendingGroup& P : Pending)
	{
		bPendingDone &= P.Remaining <= 0;
	}
	if (!Wave.bBossWave && bPendingDone && AliveNow > 0 && AliveNow <= 3 && T - LastKOTime > 25.f)
	{
		RoundUpStragglers();
		LastKOTime = T;
	}

	if (T - WaveStartTime > 2.f && WaveCleared())
	{
		if (!Waves.IsValidIndex(WaveIndex + 1))
		{
			Victory();
			return;
		}
		Announce(TEXT("WAVE CLEARED!"), 2.5f, FLinearColor(0.5f, 1.f, 0.5f));
		AddHype(15.f);
		bBetweenWaves = true;
		NextWaveTime = T + TimeBetweenWaves;
	}
}

// Debug: jedi.HordeDebug -- lists the enemies the director still counts as alive.
static FAutoConsoleCommand GJediHordeDebugCmd(
	TEXT("jedi.HordeDebug"),
	TEXT("Logs the horde director's live enemy list."),
	FConsoleCommandDelegate::CreateLambda([]()
	{
		for (TObjectIterator<AHordeDirector> It; It; ++It)
		{
			AHordeDirector* D = *It;
			if (!IsValid(D) || !D->GetWorld() || !D->GetWorld()->IsGameWorld())
			{
				continue;
			}
			UE_LOG(LogTemp, Log, TEXT("HordeDebug: wave %d alive %d KOs %d"), D->GetWaveNumber(), D->GetAliveEnemies(), D->GetKOs());
			for (TActorIterator<AActor> A(D->GetWorld()); A; ++A)
			{
				if (A->IsA(ACharacter::StaticClass()) && !A->IsA(AJediCharacter::StaticClass()))
				{
					const IJediDamageable* Dm = Cast<IJediDamageable>(*A);
					UE_LOG(LogTemp, Log, TEXT("HordeDebug:   %s at %s alive=%d"), *A->GetName(), *A->GetActorLocation().ToCompactString(), Dm ? (Dm->IsJediTargetAlive() ? 1 : 0) : -1);
				}
			}
		}
	}));

// Debug: jedi.SpawnEnemy <Clanker|Bulwark|Roller|Jet|Warden|Boss> [distance] [count] -- spawns enemies in front of the Jedi.
static FAutoConsoleCommand GJediSpawnEnemyCmd(
	TEXT("jedi.SpawnEnemy"),
	TEXT("jedi.SpawnEnemy <Clanker|Bulwark|Roller|Jet|Warden|Boss> [distance] [count]"),
	FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
	{
		const FString Kind = Args.Num() > 0 ? Args[0] : TEXT("Clanker");
		const float Dist = Args.Num() > 1 ? FCString::Atof(*Args[1]) : 400.f;
		const int32 Count = Args.Num() > 2 ? FMath::Max(1, FCString::Atoi(*Args[2])) : 1;
		UClass* Class = AClankerDroid::StaticClass();
		if (Kind == TEXT("Bulwark")) { Class = ABulwarkTrooper::StaticClass(); }
		else if (Kind == TEXT("Roller")) { Class = ABuzzRoller::StaticClass(); }
		else if (Kind == TEXT("Jet")) { Class = AJetGhost::StaticClass(); }
		else if (Kind == TEXT("Warden")) { Class = AMagnaWarden::StaticClass(); }
		else if (Kind == TEXT("Boss")) { Class = ABossWalker::StaticClass(); }
		for (TObjectIterator<AJediCharacter> It; It; ++It)
		{
			AJediCharacter* Jedi = *It;
			if (!IsValid(Jedi) || !Jedi->GetWorld() || !Jedi->GetWorld()->IsGameWorld())
			{
				continue;
			}
			const FVector Fwd = Jedi->GetControlRotation().Vector().GetSafeNormal2D();
			const FVector Right = FVector::CrossProduct(FVector::UpVector, Fwd);
			for (int32 i = 0; i < Count; ++i)
			{
				const FVector Loc = Jedi->GetActorLocation() + Fwd * Dist + Right * ((i - (Count - 1) * 0.5f) * 180.f) + FVector(0.f, 0.f, 60.f);
				FActorSpawnParameters Params;
				Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
				Jedi->GetWorld()->SpawnActor<AActor>(Class, Loc, (-Fwd).Rotation(), Params);
			}
			break;
		}
	}));
