# (HitStart, HitEnd, ChainTime, PlayRate) in animation seconds
SW = [(0.20, 0.40, 0.44, 1.0), (0.20, 0.40, 0.44, 1.0), (0.35, 0.56, 0.68, 1.0)]
J = "/Game/Jedi/Blueprints/"
AN = "/Game/Jedi/Anims/"
UA = "/Game/Characters/Mannequins/Anims/"


def a(path):
    name = path.split("/")[-1]
    return path + "." + name


def run():
    out = {}
    bpp = J + "BP_Jedi"
    if not T("asset.exists", path=bpp):
        T("bp.create", folder_path="/Game/Jedi/Blueprints", asset_name="BP_Jedi", asset_type=ref("/Script/JediArena.JediCharacter"))
    bp = ref(bpp + ".BP_Jedi")
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)
    cdo = T("bp.get_default_object", blueprint=bp)

    mesh = T("actor.get_components", actor=cdo, component_type=ref("/Script/Engine.SkeletalMeshComponent"))[0]
    T("obj.set_properties", instance=mesh, values=json.dumps({
        "skeletalMeshAsset": a("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"),
        "animClass": "/Game/Variant_Combat/Anims/ABP_Manny_Combat.ABP_Manny_Combat_C"}))

    have = lambda p: T("asset.exists", path=p)
    def anim(p, fallback):
        return a(p) if have(p) else a(fallback)

    combo = [
        {"Anim": anim(AN + "AS_Saber_Swing1", UA + "Unarmed/Attack/MM_Attack_01"), "HitStart": SW[0][0], "HitEnd": SW[0][1], "ChainTime": SW[0][2], "DamageMultiplier": 1.0, "PlayRate": SW[0][3]},
        {"Anim": anim(AN + "AS_Saber_Swing2", UA + "Unarmed/Attack/MM_Attack_02"), "HitStart": SW[1][0], "HitEnd": SW[1][1], "ChainTime": SW[1][2], "DamageMultiplier": 1.0, "PlayRate": SW[1][3]},
        {"Anim": anim(AN + "AS_Saber_Swing3", UA + "Unarmed/Attack/MM_Attack_03"), "HitStart": SW[2][0], "HitEnd": SW[2][1], "ChainTime": SW[2][2], "DamageMultiplier": 1.75, "PlayRate": SW[2][3]},
    ]
    vals = {
        "MoveAction": a("/Game/Input/Actions/IA_Move"),
        "LookAction": a("/Game/Input/Actions/IA_Look"),
        "MouseLookAction": a("/Game/Input/Actions/IA_MouseLook"),
        "JumpAction": a("/Game/Input/Actions/IA_Jump"),
        "AttackAction": a("/Game/Jedi/Input/IA_SaberAttack"),
        "BlockAction": a("/Game/Jedi/Input/IA_Block"),
        "ForcePushAction": a("/Game/Jedi/Input/IA_ForcePush"),
        "ForcePullAction": a("/Game/Jedi/Input/IA_ForcePull"),
        "ForceLightningAction": a("/Game/Jedi/Input/IA_ForceLightning"),
        "DashAction": a("/Game/Jedi/Input/IA_ForceDash"),
        "SaberToggleAction": a("/Game/Jedi/Input/IA_SaberToggle"),
        "CameraSideAction": a("/Game/Variant_Combat/Input/Actions/IA_ToggleCameraSide"),
        "SaberClass": J + "BP_Lightsaber.BP_Lightsaber_C",
        "ForceWaveClass": J + "BP_ForceWave.BP_ForceWave_C",
        "LightningBoltClass": J + "BP_LightningBolt.BP_LightningBolt_C",
        "BarWidgetClass": "/Game/Variant_Combat/UI/UI_LifeBar.UI_LifeBar_C",
        "HitFX": a("/Game/Variant_Combat/VFX/NS_Damage"),
        "HitShake": "/Game/Variant_Combat/Blueprints/BP_CameraShake_Hit_Enemy.BP_CameraShake_Hit_Enemy_C",
        "HurtShake": "/Game/Variant_Combat/Blueprints/BP_CameraShake_Hit_Player.BP_CameraShake_Hit_Player_C",
        "Combo": combo,
        "BlockAnim": anim(AN + "AS_Saber_Block", UA + "Unarmed/MM_Idle"),
        "ParryAnim": anim(AN + "AS_Saber_Parry", UA + "Unarmed/Attack/MM_Attack_02"),
        "BlockHitAnim": anim(AN + "AS_Saber_Parry", UA + "Unarmed/Attack/MM_Attack_02"),
        "DashAnim": anim(AN + "AS_Force_Dash", UA + "Unarmed/Jump/MM_Fall_Loop"),
        "FlipAnim": anim(AN + "AS_Jump_Flip", UA + "Unarmed/Jump/MM_Jump"),
        "PushAnim": a(UA + "Unarmed/Attack/MM_Attack_02"),
        "PullAnim": a(UA + "Unarmed/Attack/MM_Attack_03"),
        "LightningAnim": a(UA + "Pistol/MF_Pistol_Idle_ADS"),
    }
    out["set"] = T("obj.set_properties", instance=cdo, values=json.dumps(vals))
    T("bp.compile_blueprint", blueprint=bp, warnings_as_errors=False)

    # respawn + game mode use the C++ Jedi
    node = ref("/Game/Variant_Combat/Blueprints/BP_CombatPlayerController.BP_CombatPlayerController:EventGraph.K2Node_SpawnActorFromClass_0")
    T("bp.set_pin_value", pin={"direction": "EGPD_Input", "index_id": 1, "node": node}, value=J + "BP_Jedi.BP_Jedi_C")
    T("bp.compile_blueprint", blueprint=ref("/Game/Variant_Combat/Blueprints/BP_CombatPlayerController.BP_CombatPlayerController"), warnings_as_errors=False)
    T("obj.set_properties", instance=T("bp.get_default_object", blueprint=ref(J + "BP_JediGameMode.BP_JediGameMode")),
      values=json.dumps({"DefaultPawnClass": J + "BP_Jedi.BP_Jedi_C"}))
    T("asset.save_assets", asset_paths=[bpp, J + "BP_JediGameMode", "/Game/Variant_Combat/Blueprints/BP_CombatPlayerController"])
    out["check"] = T("obj.get_properties", instance=cdo, properties=["Combo", "BlockAnim", "SaberClass"])[:1500]
    return out
