SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2"
BODY={"bindingId":"BF895B52-4243-5DF0-29DD-768D103845A0","sequence":ref(LS)}
RIG="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body"
def run():
    out={}
    out["name"]=X(SQ+"get_binding_name", binding=BODY)
    out["bound"]=X(SQ+"get_bound_objects", binding=BODY)
    out["trk"]=X(CR+"find_or_create_track", sequence=ref(LS), binding=BODY, control_rig_asset_path=RIG, is_layered=False)
    X(SQ+"set_display_rate", sequence=ref(LS), numerator=30, denominator=1)
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=2000)
    out["rate"]=X(SQ+"get_display_rate", sequence=ref(LS))
    out["tick"]=X(SQ+"get_tick_resolution", sequence=ref(LS))
    trk=json.loads(out["trk"])["track"]
    out["secs"]=X(SQ+"get_sections", track=ref(trk))
    return out
