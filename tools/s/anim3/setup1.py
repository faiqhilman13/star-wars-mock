SQ="animation_toolset.toolsets.sequencer.SequencerTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS2="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2"
LS3="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V3"
def run():
    out={}
    if T("app.IsPIERunning"): return {"err":"PIE"}
    if not T("asset.exists", path=LS3):
        out["dup"]=T("asset.duplicate", path=LS2, new_path=LS3)
    a = T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Dev/BP_GripTest", name="AnimRig_V3", xform=xf((-1000,400,100),(0,90,0)), parent=None, snap_to_ground=False)
    out["actor"]=a
    T("actor.set_label", actor=a, label="AnimRig_V3")
    T("obj.set_properties", instance=a, values=json.dumps({"TestLoc":{"x":-7,"y":2,"z":0},"TestRot":{"pitch":35,"yaw":0,"roll":180}}))
    comps=T("actor.get_components", actor=a, component_type=None)
    out["comps"]=comps
    out["open"]=X(SQ+"open_sequence", sequence=ref(LS3+".LS_SaberAuthoring_V3"))
    b=X(SQ+"get_bindings", sequence=ref(LS3+".LS_SaberAuthoring_V3"))
    out["b"]=b
    return out
