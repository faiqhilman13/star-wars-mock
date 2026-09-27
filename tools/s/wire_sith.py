BPP = "/Game/Jedi/Blueprints/BP_SithEnemy.BP_SithEnemy"
G = ref(BPP + ":EventGraph")
def infos():
    return T("bp.get_node_infos", nodes=T("bp.find_nodes", graph=G, title="", node_class=None, entry_points_only=False))
def pin(i, n, out=True):
    return [p for p in (i["output_pins"] if out else i["input_pins"]) if p["name"] == n][0]
def run():
    d = {i["type_id"]: i for i in infos()}
    pos = d.get("AddEvent|EventPossessed") or T("bp.get_node_infos", nodes=[T("bp.create_node", graph=G, type_id="AddEvent|EventPossessed", pos={"x": 0, "y": -300})])[0]
    if not pin(pos, "then")["connected_pins"]:
        call = T("bp.get_node_infos", nodes=[T("bp.create_node", graph=G, type_id="CallFunction|SithInit", pos={"x": 400, "y": -300})])[0]
        T("bp.connect_pins", output_pin=pin(pos, "then")["pin_id"], input_pin=pin(call, "execute", False)["pin_id"])
    T("bp.compile_blueprint", blueprint=ref(BPP), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_SithEnemy"])
    return {"types": sorted(i["type_id"] for i in infos() if i["type_id"].startswith("AddEvent"))}
