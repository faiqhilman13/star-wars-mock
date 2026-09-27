# python contacts.py anl_out.json  -> contact windows / peak speeds per clip
import json, sys, math
d=json.load(open(sys.argv[1]))
VMIN=float(sys.argv[2]) if len(sys.argv)>2 else 900.0
res={}
for key,rows in d.items():
    T=rows[-1][0]
    fr=[]; peak=(0,None,None)
    for r in rows:
        i=r[0]; hit=[]
        for k,sp,x,y,z in r[1:]:
            if sp>peak[0]: peak=(sp,i,k)
            if sp>=VMIN and x>30 and abs(math.degrees(math.atan2(y,x)))<70 and z>-5: hit.append(k)
        if hit: fr.append((i,hit))
    # windows (merge 1-frame gaps)
    wins=[]
    for i,h in fr:
        if wins and i-wins[-1][1]<=2: wins[-1][1]=i; wins[-1][2].update(h)
        else: wins.append([i,i,set(h)])
    # drop 1-frame blips at speed barely over threshold? keep but mark
    out=[]
    for a,b,h in wins:
        out.append({"frames":[a,b],"sec":[round((a-1)/30.0,3),round(b/30.0,3)],"blades":sorted(h)})
    last=wins[-1][1] if wins else 0
    chain=min(T, last+3)
    res[key]={"frames":T,"len_s":round(T/30.0,3),"windows":out,"peak_cm_s":peak[0],"peak_at":[peak[1],peak[2]],"chain_frame":chain,"chain_s":round(chain/30.0,3)}
print(json.dumps(res,indent=1))
