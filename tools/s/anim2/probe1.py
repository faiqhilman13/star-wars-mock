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
    ch=X(KF+"get_channel_names", section=ref(SEC))
    out={"n":len(ch),"body":[c for c in ch if "body_ctrl" in c][:12], "sample":ch[:5]}
    k=json.loads(X(KF+"get_keys", section=ref(SEC), channel_name=out["body"][0]))
    out["nk"]=len(k); out["last"]=k[-1] if k else None; out["first"]=k[0] if k else None
    t0=time.time()
    for i in range(20):
        X(CR+"get_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name="body_ctrl", frame=227)
    out["t_get"]=(time.time()-t0)/20
    t0=time.time()
    for i in range(20):
        X(CR+"set_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name="neck_02_ctrl", frame=1500+i, location_x=0,location_y=0,location_z=0,rotation_pitch=0,rotation_yaw=0,rotation_roll=0,scale_x=1,scale_y=1,scale_z=1,set_key=True)
    out["t_set"]=(time.time()-t0)/20
    t0=time.time()
    for i in range(10):
        X(SQ+"set_playhead_frame", frame=1500+i); X(SQ+"force_evaluate")
    out["t_show"]=(time.time()-t0)/10
    return out
