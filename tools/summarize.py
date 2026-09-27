import json,sys,glob
for f in sorted(glob.glob("schemas/*.txt")):
    d=json.load(open(f,encoding="utf-8"))
    print("##",d["name"])
    for t in d["tools"]:
        props=t["inputSchema"].get("properties",{})
        ps=", ".join(f"{k}:{v.get('title') or v.get('type')}" for k,v in props.items())
        print(" -",t["name"].split(".")[-1],"(",ps,")","::",t["description"].strip().split("\n")[0][:110])
