SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2"
RIG="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body"
SEC="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2:MovieScene_0.MovieSceneControlRigParameterTrack_0.MovieSceneControlRigParameterSection_0"
def run():
    out={}
    out["load"]=X(CR+"load_anim_into_rig", cr_section=ref(SEC), anim_sequence_path="/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle", start_frame=0, reset_controls=True, key_reduce=False, tolerance=0.001)
    X(SQ+"set_playhead_frame", frame=0); X(SQ+"force_evaluate")
    for c in ["arm_r_fk_ik_switch","arm_l_fk_ik_switch","spine_fk_ik_switch","leg_r_fk_ik_switch","leg_l_fk_ik_switch","arm_r_stretch_switch","leg_r_stretch_switch"]:
        out[c]=X(CR+"get_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name=c, frame=0)
    return out
