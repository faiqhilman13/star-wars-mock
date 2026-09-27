def run():
    return {"cs": T("bp.read_graph_dsl", graph=ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber:UserConstructionScript")),
            "vars": T("bp.list_variables", blueprint=ref("/Game/Jedi/Blueprints/BP_Lightsaber.BP_Lightsaber"))}
