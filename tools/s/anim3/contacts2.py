# python contacts2.py anl.json clipsfile  -> strike windows, peak speed, chain time
import json, sys, math, os
H=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(sys.argv[1]))
ns={"ref":(lambda p:{"refPath":p}),"execute_tool":None,"T":(lambda *a,**k:False),"json":json}
exec("".join(open(os.path.join(H,p)).read()+chr(10) for p in ["lib3.py","eng3.py","clips3.py"]+sys.argv[2:]), ns)
ns["CAL"]=ns["CAL_OFF"]
VMIN=1500.0
res={}
for key,rows in d.items():
    c=ns["ALL"][key](); T=c.T
    ths=[c.pose(float(i))["th"] for i in range(T+1)]
    settle=0
    for i in range(T+1):
        if all(abs(ths[j]-ths[-1])<8.0 for j in range(i,T+1)): settle=i; break
    fr=[]; peak=(0,None,None)
    for r in rows:
        i=r[0]; hit=set()
        for k,sp,x,y,z in r[1:]:
            if sp>peak[0]: peak=(sp,i,k)
            if sp>=VMIN and x>40 and abs(math.degrees(math.atan2(y,x)))<55: hit.add(k)
        if hit: fr.append((i,hit))
    wins=[]
    for i,h in fr:
        if wins and i-wins[-1][1]<=1: wins[-1][1]=i; wins[-1][2].update(h)
        else: wins.append([i,i,set(h)])
    last=wins[-1][1] if wins else 0
    chain=min(T, max(last+3, settle+1 if settle>0 else 0))
    names={"Rb1":"R-blade1","Rb2":"R-blade2","Lb1":"L-saber"}
    res[c.name]={"frames":T,"len_s":round(T/30.0,3),
        "windows_s":[[round((a-1)/30.0,3),round(b/30.0,3),[names.get(x,x) for x in sorted(h)]] for a,b,h in wins],
        "peak_tip_cm_s":peak[0],"peak_frame":peak[1],"chain_frame":chain,"chain_s":round(chain/30.0,3)}
print(json.dumps(res,indent=1))
