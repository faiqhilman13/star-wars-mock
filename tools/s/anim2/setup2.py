SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2"
ACTOR="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDC10503_1201569079"
def run():
    out={}
    out["set"]=T("obj.set_properties", instance=ref(ACTOR), values=json.dumps({"TestLoc":{"x":-7,"y":2,"z":0},"TestRot":{"pitch":35,"yaw":0,"roll":180}}))
    out["p"]=T("obj.get_properties", instance=ref(ACTOR), properties=["TestLoc","TestRot"])
    out["add"]=X(SQ+"add_actors", actors=[ref(ACTOR)])
    b=X(SQ+"get_bindings", sequence=ref(LS))
    out["b"]=b
    out["kids"]=X(SQ+"get_child_possessables", binding=b[0])
    comps=T("actor.get_components", actor=ref(ACTOR), component_type=None)
    out["comps"]=comps
    return out
