def dsl_all(path):
    bp = ref(path); r = {"parent": T("bp.get_parent", blueprint=bp)}
    for g in T("bp.list_graphs", blueprint=bp):
        try: r[g["refPath"].split(":")[-1]] = T("bp.read_graph_dsl", graph=g)
        except Exception as e: r[g["refPath"]] = "ERR "+str(e)
    return r
def run():
    out = {}
    imc = ref("/Game/Variant_Combat/Input/IMC_Combat.IMC_Combat")
    out["imc_props"] = T("obj.list_properties", instance=imc)
    out["imc"] = T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"])
    out["pc"] = dsl_all("/Game/Variant_Combat/Blueprints/BP_CombatPlayerController.BP_CombatPlayerController")
    out["gm"] = T("bp.get_parent", blueprint=ref("/Game/Variant_Combat/Blueprints/BP_CombatGameMode.BP_CombatGameMode"))
    out["enemy_parent"] = T("bp.get_parent", blueprint=ref("/Game/Variant_Combat/Blueprints/AI/BP_CombatEnemy.BP_CombatEnemy"))
    out["enemy_vars"] = T("bp.list_variables", blueprint=ref("/Game/Variant_Combat/Blueprints/AI/BP_CombatEnemy.BP_CombatEnemy"))
    mesh = ref("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple")
    out["sockets"] = T("skm.get_socket_names", mesh=mesh)
    out["assets_chars"] = T("asset.find_assets", folder_path="/Game/Characters", name="", recursive=True)
    return out
