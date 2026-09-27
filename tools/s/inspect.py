def run():
    bp = ref("/Game/Variant_Combat/Blueprints/BP_CombatCharacter.BP_CombatCharacter")
    out = {"parent": T("bp.get_parent", blueprint=bp), "graphs": T("bp.list_graphs", blueprint=bp),
           "vars": T("bp.list_variables", blueprint=bp)}
    dsl = {}
    for g in out["graphs"]:
        try:
            dsl[g["refPath"]] = T("bp.read_graph_dsl", graph=g)
        except Exception as e:
            dsl[g["refPath"]] = "ERR " + str(e)
    out["dsl"] = dsl
    return out
