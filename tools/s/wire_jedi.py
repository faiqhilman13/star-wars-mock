G = ref("/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter:EventGraph")
def nodes_by_type():
    ns = T("bp.find_nodes", graph=G, title="", node_class=None, entry_points_only=False)
    d = {}
    for i in T("bp.get_node_infos", nodes=ns):
        d.setdefault(i["type_id"], []).append(i)
    return d
def pin(info, name, out=True):
    for p in (info["output_pins"] if out else info["input_pins"]):
        if p["name"] == name: return p
    raise RuntimeError("no pin %s on %s: %s" % (name, info["type_id"], [p["name"] for p in (info["output_pins"] if out else info["input_pins"])]))
def info_of(node):
    return T("bp.get_node_infos", nodes=[node])[0]
def mk(type_id, x, y):
    return info_of(T("bp.create_node", graph=G, type_id=type_id, pos={"x": x, "y": y}))
def link(src_info, src_pin, dst_info, dst_pin="execute"):
    T("bp.connect_pins", output_pin=pin(src_info, src_pin)["pin_id"], input_pin=pin(dst_info, dst_pin, False)["pin_id"])
def run():
    out = {}
    d = nodes_by_type()
    out["types"] = sorted(d.keys())
    # Remove any BeginPlay override (parent's BeginPlay must run); init from Possessed instead
    for n in d.get("AddEvent|EventBeginPlay", []):
        T("bp.delete_node", node=n["node"])
    pos = d["AddEvent|EventPossessed"][0] if "AddEvent|EventPossessed" in d else mk("AddEvent|EventPossessed", 0, -400)
    if not pin(pos, "then")["connected_pins"]:
        link(pos, "then", mk("CallFunction|JediInit", 400, -400))
    # Input events
    y = 3000
    for ia, wires in [("IA_ForcePush", [("Started", "ForcePush")]), ("IA_ForcePull", [("Started", "ForcePull")]),
                      ("IA_ForceLightning", [("Started", "LightningStart"), ("Completed", "LightningStop"), ("Canceled", "LightningStop")]),
                      ("IA_SaberToggle", [("Started", "SaberToggle")])]:
        tid = "Input|EnhancedActionEvents|EnhancedInputAction" + ia
        ev = d[tid][0] if tid in d else mk("Input|EnhancedActionEvents|" + ia, -400, y)
        for k, (pn, fn) in enumerate(wires):
            if not pin(ev, pn)["connected_pins"]:
                link(ev, pn, mk("CallFunction|" + fn, 0, y + k * 120))
        y += 500
    out["compile"] = T("bp.compile_blueprint", blueprint=ref("/Game/Jedi/Blueprints/BP_JediCharacter.BP_JediCharacter"), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_JediCharacter"])
    ev = nodes_by_type()["Input|EnhancedActionEvents|EnhancedInputActionIA_ForceLightning"][0]
    out["lightning_pins"] = [(p["name"], len(p["connected_pins"])) for p in ev["output_pins"]]
    return out
