import json, sys
STRIKE_END={"AS_Staff_Combo1":16,"AS_Staff_Combo2":22,"AS_Staff_Combo3":19,"AS_Staff_Combo4":15,
            "AS_Dual_Combo1":12,"AS_Dual_Combo2":10,"AS_Dual_Combo3":22,"AS_Dual_Combo4":11}
SETTLE={"AS_Staff_Combo2":20,"AS_Staff_Combo4":18,"AS_Dual_Combo3":24}
out={}
for fn in sys.argv[1:]:
    d=json.load(open(fn))
    for k,v in d.items():
        se=STRIKE_END[k]
        strikes=[w for w in v["windows_s"] if round(w[0]*30)+1<=se]
        rec=[w for w in v["windows_s"] if round(w[0]*30)+1>se]
        last=max([round(w[1]*30) for w in strikes] or [0])
        chain=min(v["frames"], max(last+3, SETTLE.get(k,0)))
        out[k]=dict(v, strikes=strikes, recovery=rec, chain_frame=chain, chain_s=round(chain/30.0,3))
json.dump(out,open("final_contacts.json","w"),indent=1)
for k,v in out.items():
    print(k, v["len_s"], "strikes:",[(a,b,"+".join(x)) for a,b,x in v["strikes"]], "recovery:",[(a,b) for a,b,x in v["recovery"]], "peak",v["peak_tip_cm_s"], "chain",v["chain_s"])
