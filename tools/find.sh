#!/bin/bash
# usage: find.sh <graph_refpath> "filter1" "filter2" ...   (prefix filter with = to get pins for exact type id)
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
G="$1"; shift
Q=$(printf '%s\n' "$@" | "$PY" -c "import sys,json;print(json.dumps([l.rstrip('\n') for l in sys.stdin if l.strip()]))")
cat > s/_find.py <<PYEOF
G = ref("$G")
Q = $Q
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
PYEOF
"$PY" ue.py script s/_find.py
