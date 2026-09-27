SQ="animation_toolset.toolsets.sequencer.SequencerTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
A="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCD0503_1297333191"
def run():
    out={}
    body=ref(A+".Body")
    T("obj.set_properties", instance=body, values=json.dumps({"skeletalMeshAsset": "/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden.SKM_GreyWarden"}))
    out["body"]=T("obj.get_properties", instance=body, properties=["skeletalMeshAsset","animationMode"])
    X(SQ+"set_playhead_frame", frame=228); X(SQ+"force_evaluate")
    X(SQ+"set_playhead_frame", frame=227); X(SQ+"force_evaluate")
    return out
