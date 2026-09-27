using UnrealBuildTool;

public class JediArena : ModuleRules
{
	public JediArena(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] {
			"Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "UMG", "Niagara", "ProceduralMeshComponent"
		});
		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "Kismet", "AssetRegistry" });
		}
	}
}
