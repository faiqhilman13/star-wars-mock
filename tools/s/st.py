ST = "state_tree_toolset.toolsets.state_tree.StateTreeTools."
def X(t, **k):
    r = execute_tool(ST + t, json.dumps(k))
    try: return r["returnValue"]
    except Exception: return r
def run():
    st = ref("/Game/Variant_Combat/Blueprints/AI/ST_CombatEnemy.ST_CombatEnemy")
    out = {"globals": str(X("get_global_tasks", state_tree=st))[:600], "eval": str(X("get_evaluators", state_tree=st))[:400]}
    def walk(state, depth):
        if depth > 5: return
        name = str(state)
        info = {"conds": str(X("get_enter_conditions", state=state))[:400], "tasks": str(X("get_tasks", state=state))[:400]}
        out[name[-90:]] = info
        for c in X("get_children", state=state) or []:
            walk(c, depth + 1)
    for r in X("get_root_states", state_tree=st) or []:
        walk(r, 0)
    return out
