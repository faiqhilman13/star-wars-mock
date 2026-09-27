def run():
    bp = ref("/Game/Jedi/Blueprints/BP_LightsaberRed.BP_LightsaberRed")
    out = {"graphs": T("bp.list_graphs", blueprint=bp)}
    for g in out["graphs"]:
        out[g["refPath"].split(":")[-1]] = T("bp.read_graph_dsl", graph=g)
    return out
