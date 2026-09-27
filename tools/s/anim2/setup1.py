SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2"
def run():
    out={}
    a = T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Dev/BP_GripTest", name="AnimRig_GripTestV2", xform=xf((-1000,400,100),(0,90,0)), parent=None, snap_to_ground=False)
    out["actor"]=a
    if not T("asset.exists", path="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2"):
        out["seq"]=X(SQ+"create_level_sequence", package_path="/Game/Jedi/Anims/Authoring", asset_name="LS_SaberAuthoring_V2")
    out["open"]=X(SQ+"open_sequence", sequence=ref(LS))
    return out
