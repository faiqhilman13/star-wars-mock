def run():
    out={}
    sab=ref(ACTOR+".Saber")
    props=json.loads(T("obj.list_properties", instance=sab))
    out["p"]=[k for k in props.keys() if "ttach" in k or "ocket" in k or "hild" in k]
    out["v"]=T("obj.get_properties", instance=sab, properties=[k for k in out["p"]])
    out["ca"]=T("obj.get_properties", instance=sab, properties=["childActor"])
    return out
