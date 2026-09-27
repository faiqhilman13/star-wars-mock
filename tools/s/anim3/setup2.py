SQ="animation_toolset.toolsets.sequencer.SequencerTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V3.LS_SaberAuthoring_V3"
ACT={"bindingId":"9FA787AC-44A7-EBA8-9DB0-CD9BBC973698","sequence":ref(LS)}
BODY={"bindingId":"BF895B52-4243-5DF0-29DD-768D103845A0","sequence":ref(LS)}
A="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDCD0503_1297333191"
def run():
    out={}
    out["n_act"]=X(SQ+"get_binding_name", binding=ACT)
    out["n_body"]=X(SQ+"get_binding_name", binding=BODY)
    out["before_act"]=X(SQ+"get_bound_objects", binding=ACT)
    out["rep"]=X(SQ+"replace_binding_with_actors", actors=[ref(A)], binding=ACT)
    out["after_act"]=X(SQ+"get_bound_objects", binding=ACT)
    out["after_body"]=X(SQ+"get_bound_objects", binding=BODY)
    out["kids"]=X(SQ+"get_child_possessables", binding=ACT)
    return out
