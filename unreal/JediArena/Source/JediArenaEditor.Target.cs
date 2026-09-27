using UnrealBuildTool;

public class JediArenaEditorTarget : TargetRules
{
	public JediArenaEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("JediArena");
	}
}
