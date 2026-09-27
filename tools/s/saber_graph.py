def run():
    bp = ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber")
    return {"eg": T("bp.read_graph_dsl", graph=ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber:EventGraph")),
            "parent": T("bp.get_parent_class", blueprint=bp) if False else None}
