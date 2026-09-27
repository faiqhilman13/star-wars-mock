#include "JediHUD.h"

#include "HordeDirector.h"
#include "JediCharacter.h"
#include "JediDamageable.h"

#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

void AJediHUD::Text(const FString& S, float X, float Y, float Scale, const FLinearColor& Color, bool bCentre, UFont* Font)
{
	if (!Canvas || S.IsEmpty())
	{
		return;
	}
	FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(S), Font ? Font : GEngine->GetLargeFont(), Color);
	Item.Scale = FVector2D(Scale, Scale);
	Item.EnableShadow(FLinearColor(0.f, 0.f, 0.f, Color.A * 0.85f), FVector2D(2.f, 2.f));
	Item.bCentreX = bCentre;
	Canvas->DrawItem(Item);
}

void AJediHUD::Bar(float X, float Y, float W, float H, float Fraction, const FLinearColor& Fill, const FLinearColor& Back)
{
	if (!Canvas)
	{
		return;
	}
	FCanvasTileItem Bg(FVector2D(X - 2.f, Y - 2.f), FVector2D(W + 4.f, H + 4.f), Back);
	Bg.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Bg);
	FCanvasTileItem Fg(FVector2D(X, Y), FVector2D(W * FMath::Clamp(Fraction, 0.f, 1.f), H), Fill);
	Fg.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Fg);
}

void AJediHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas || !GEngine)
	{
		return;
	}
	const float T = GetWorld()->GetTimeSeconds();
	const float Dt = FMath::Clamp(T - LastDrawTime, 0.f, 0.1f);
	LastDrawTime = T;
	const float W = Canvas->ClipX;
	const float H = Canvas->ClipY;
	const float S = FMath::Max(H / 1080.f, 0.5f) * 1.6f; // UI scale (the engine's large font is small)

	const AJediCharacter* Jedi = Cast<AJediCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
	const AHordeDirector* Director = AHordeDirector::Get(this);

	// ---- KO counter + crowd hype (top right)
	if (Director)
	{
		const int32 KOs = Director->GetKOs();
		if (KOs != LastKOs)
		{
			KOPulse = 1.f;
			LastKOs = KOs;
		}
		KOPulse = FMath::Max(0.f, KOPulse - Dt * 4.f);
		const float KX = W - 330.f * S;
		Text(TEXT("KO"), KX, 38.f * S, 1.4f * S, FLinearColor(1.f, 0.75f, 0.3f));
		Text(FString::FromInt(KOs), KX + 70.f * S, 22.f * S, (2.6f + KOPulse * 0.6f) * S, FLinearColor(1.f, 1.f, 1.f));
		Text(TEXT("CROWD HYPE"), KX, 100.f * S, 0.75f * S, FLinearColor(1.f, 0.85f, 0.6f, 0.9f));
		const float Hype = Director->GetHype() / 100.f;
		const FLinearColor HypeCol = FLinearColor::LerpUsingHSV(FLinearColor(1.f, 0.8f, 0.2f), FLinearColor(1.f, 0.15f, 0.6f), Hype);
		Bar(KX, 124.f * S, 280.f * S, 9.f * S, Hype, HypeCol);

		// ---- Wave info (top left)
		if (Director->GetWaveNumber() > 0)
		{
			Text(FString::Printf(TEXT("WAVE %d / %d"), FMath::Min(Director->GetWaveNumber(), Director->GetWaveCount()), Director->GetWaveCount()),
				40.f * S, 30.f * S, 1.2f * S, FLinearColor(1.f, 0.8f, 0.35f));
			Text(Director->GetWaveTitle(), 40.f * S, 64.f * S, 0.9f * S, FLinearColor(1.f, 1.f, 1.f, 0.9f));
			Text(FString::Printf(TEXT("Enemies: %d"), Director->GetAliveEnemies()), 40.f * S, 94.f * S, 0.75f * S, FLinearColor(0.85f, 0.85f, 0.85f, 0.85f));
		}
		const int32 Secs = FMath::FloorToInt(Director->GetElapsed());
		Text(FString::Printf(TEXT("%d:%02d"), Secs / 60, Secs % 60), 40.f * S, 120.f * S, 0.75f * S, FLinearColor(0.85f, 0.85f, 0.85f, 0.7f));

		// ---- Boss bar (top centre)
		if (const AActor* Boss = Director->GetBoss())
		{
			if (const IJediDamageable* B = Cast<IJediDamageable>(Boss); B && B->IsJediTargetAlive())
			{
				const float BW = 760.f * S;
				Text(Director->GetBossName(), W * 0.5f, 26.f * S, 1.1f * S, FLinearColor(1.f, 0.35f, 0.25f), true);
				Bar(W * 0.5f - BW * 0.5f, 62.f * S, BW, 16.f * S, B->GetJediHealthFraction(), FLinearColor(0.95f, 0.18f, 0.1f, 0.95f));
			}
		}

		// ---- Announcements (centre)
		float BY = H * 0.26f;
		for (const AHordeDirector::FBanner& Banner : Director->GetBanners())
		{
			const float Age = T - Banner.Start;
			const float Left = Banner.Until - T;
			const float Pop = FMath::Clamp(1.f - Age / 0.18f, 0.f, 1.f);
			const float Alpha = FMath::Clamp(Left / 0.4f, 0.f, 1.f) * FMath::Clamp(Age / 0.08f, 0.f, 1.f);
			FLinearColor C = Banner.Color;
			C.A = Alpha;
			Text(Banner.Text, W * 0.5f, BY, (1.7f + Pop * 0.9f) * S, C, true);
			BY += 58.f * S;
		}

		if (Director->IsVictory())
		{
			Text(FString::Printf(TEXT("Max combo: %d"), Jedi ? Jedi->GetMaxCombo() : 0), W * 0.5f, H * 0.5f, 1.1f * S, FLinearColor::White, true);
		}
	}

	if (!Jedi)
	{
		return;
	}

	// ---- Combo hits (right middle)
	const int32 Combo = Jedi->GetComboHits();
	if (Combo != LastCombo)
	{
		if (Combo > LastCombo)
		{
			ComboPulse = 1.f;
		}
		LastCombo = Combo;
	}
	ComboPulse = FMath::Max(0.f, ComboPulse - Dt * 5.f);
	if (Combo >= 2)
	{
		const FLinearColor ComboCol = Combo >= 100 ? FLinearColor(1.f, 0.3f, 0.9f) : Combo >= 50 ? FLinearColor(1.f, 0.45f, 0.15f) : FLinearColor(0.55f, 0.85f, 1.f);
		Text(FString::FromInt(Combo), W - 250.f * S, H * 0.42f, (2.4f + ComboPulse * 0.8f) * S, ComboCol);
		Text(TEXT("HITS"), W - 250.f * S, H * 0.42f + 62.f * S, 1.f * S, FLinearColor(1.f, 1.f, 1.f, 0.9f));
	}

	// ---- Force Surge meter (bottom centre)
	const float SW = 460.f * S;
	const float SX = W * 0.5f - SW * 0.5f;
	const float SY = H - 70.f * S;
	const float Surge = Jedi->GetSurgeFraction();
	const bool bReady = Surge >= 1.f;
	const float Glow = bReady ? 0.6f + 0.4f * FMath::Abs(FMath::Sin(T * 5.f)) : 1.f;
	Bar(SX, SY, SW, 14.f * S, Surge, FLinearColor(0.25f * Glow, 0.65f * Glow, 1.f * Glow, 0.95f));
	Text(bReady ? TEXT("FORCE STORM READY  -  press C") : TEXT("FORCE SURGE"), W * 0.5f, SY - 30.f * S, 0.85f * S,
		bReady ? FLinearColor(0.6f, 0.9f, 1.f, Glow) : FLinearColor(0.75f, 0.85f, 1.f, 0.85f), true);
}
