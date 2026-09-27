#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "JediHUD.generated.h"

class UFont;

/**
 * Musou-style HUD drawn on the canvas: KO counter, combo hits, wave banner, Force Surge meter,
 * boss health bar, crowd hype and the director's centre-screen announcements.
 */
UCLASS()
class JEDIARENA_API AJediHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

private:
	void Text(const FString& S, float X, float Y, float Scale, const FLinearColor& Color, bool bCentre = false, UFont* Font = nullptr);
	void Bar(float X, float Y, float W, float H, float Fraction, const FLinearColor& Fill, const FLinearColor& Back = FLinearColor(0.f, 0.f, 0.f, 0.55f));

	int32 LastKOs = 0;
	float KOPulse = 0.f;
	int32 LastCombo = 0;
	float ComboPulse = 0.f;
	float LastDrawTime = 0.f;
};
