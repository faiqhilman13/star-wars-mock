BPP = "/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi"
G = ref(BPP + ":EventGraph")
def info(n): return T("bp.get_node_infos", nodes=[n])[0]
def run():
    ev = info(T("bp.create_node", graph=G, type_id="AddEvent|EventApplyDamage", pos={"x": 0, "y": 0}))
    call = info(T("bp.create_node", graph=G, type_id="Jedi|ReceiveTemplateDamage", pos={"x": 450, "y": 0}))
    outs = {p["name"]: p for p in ev["output_pins"]}
    ins = {p["name"]: p for p in call["input_pins"]}
    res = {"ev_out": list(outs), "call_in": list(ins)}
    T("bp.connect_pins", output_pin=outs["then"]["pin_id"], input_pin=ins["execute"]["pin_id"])
    for src, dst in [("Damage", "Damage"), ("Damage Causer", "DamageCauser"), ("Damage Location", "DamageLocation"), ("Damage Impulse", "DamageImpulse")]:
        T("bp.connect_pins", output_pin=outs[src]["pin_id"], input_pin=ins[dst]["pin_id"])
    T("bp.compile_blueprint", blueprint=ref(BPP), warnings_as_errors=False)
    T("asset.save_assets", asset_paths=["/Game/Jedi/Blueprints/BP_Jedi"])
    res["dsl"] = T("bp.read_graph_dsl", graph=G)
    return res
