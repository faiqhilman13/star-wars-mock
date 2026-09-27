import time
SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
KF="animation_toolset.toolsets.keyframing.SequencerKeyframingTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2"
RIG="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body"
SEC="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2:MovieScene_0.MovieSceneControlRigParameterTrack_0.MovieSceneControlRigParameterSection_0"
def run():
    out={}
    t0=time.time()
    for i in range(20): X(SQ+"get_display_rate", sequence=ref(LS))
    out["t_trivial"]=(time.time()-t0)/20
    t0=time.time()
    for i in range(20): X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name="arm_r_fk_ik_switch", frame=100)
    out["t_getbool"]=(time.time()-t0)/20
    t0=time.time()
    for i in range(20): X(KF+"add_key_float", section=ref(SEC), channel_name="neck_02_ctrl.Rotation.X", frame=1500+i, value=0.0, interpolation="cubic")
    out["t_addkey"]=(time.time()-t0)/20
    t0=time.time()
    for i in range(10): X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name="upperarm_r_fk_ctrl", frame=100)
    out["t_getw"]=(time.time()-t0)/10
    return out
