G = ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi:EventGraph")
Q = ["ReceiveTemplateDamage", "ApplyDamage"]
def run():
    out = {}
    for q in Q:
        if q.startswith("="):
            try:
                info = T("bp.get_node_type_pins", graph=G, type_id=q[1:])
            except Exception as e:
                out[q] = "ERR " + str(e)[:200]; continue
            if isinstance(info, str): info = json.loads(info)

            fmt = lambda p: p["name"] + ":" + str(p["type_id"]) + ("=" + str(p["value"]) if p["value"] else "")
            out[q] = "IN[" + " | ".join(fmt(p) for p in info["input_pins"]) + "]  OUT[" + " | ".join(fmt(p) for p in info["output_pins"]) + "]"
        else:
            r = T("bp.find_node_types", graph=G, type_id_filter=q, context_pins=[])
            if isinstance(r, str): r = json.loads(r)
            out[q] = ", ".join(str(x) for x in r[:40])
    return out
