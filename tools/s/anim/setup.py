SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
def run():
    out={}
    for p in ["/Game/Jedi/Anims","/Game/Jedi/Anims/Authoring"]:
        if not T("asset.exists", path=p): T("asset.create_folder", path=p)
    a = T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Dev/BP_GripTest", name="AnimRig_GripTest", xform=xf((-1000,400,100),(0,90,0)), parent=None, snap_to_ground=False)
    out["actor"]=a
    seq = X(SQ+"create_level_sequence", package_path="/Game/Jedi/Anims/Authoring", asset_name="LS_SaberAuthoring")
    out["seq"]=seq
    return out
