# offline weapon planner: python plan2.py <clipkey> [extra.py ...]
import json, math, sys, os
H=os.path.dirname(os.path.abspath(__file__))
def ref(p): return {"refPath":p}
def execute_tool(n,a): raise RuntimeError("no editor")
def T(*a,**k): return False
src=open(os.path.join(H,"lib3.py")).read()+open(os.path.join(H,"eng3.py")).read()+open(os.path.join(H,"clips3.py")).read()
for extra in sys.argv[2:]:
    src+=open(os.path.join(H,extra)).read()
exec(src)
CAL=CAL_OFF
def body_rows(p):
    br=CAL_OFF["L_body_ctrl"][1]
    return [bl_to_c(r) for r in Mr(br[0]+p["lean"], p["yaw"], br[2]+p["bend"])]
def torso_rows(p):
    br=CAL_OFF["L_body_ctrl"][1]
    return [bl_to_c(r) for r in Mr(br[0]+p["lean"]+2.5*p["slean"], p["yaw"]+3*p["syaw"], br[2]+p["bend"]+2.7*p["sbend"])]
def world_of(loc, rows, origin):
    return add(origin, add(add(mulv(rows[0],loc[0]),mulv(rows[1],loc[1])),mulv(rows[2],loc[2])))
def joints(p, Q):
    th=p["th"]
    b=add(CAL_OFF["W_body_ctrl"][0],(p["dfwd"],p["dside"],p["dz"]))
    rb=body_rows(p); rt=torso_rows(p)
    J={"body":b}
    for k in ["thigh_l","thigh_r"]: J[k]=world_of(JLOC[k],rb,b)
    for k in ["ua_r","ua_l","neck","head"]: J[k]=world_of(JLOC[k],rt,b)
    J={k:spinp(v,th,Q) for k,v in J.items()}
    c=CAL_OFF
    for s in "lr":
        pos,rot,pv=foot_target(s,p,c)
        J["ank_"+s]=spinp(pos,th,Q)
    return J
def seg_dist(p1,q1,p2,q2):
    d1=sub(q1,p1); d2=sub(q2,p2); r=sub(p1,p2)
    a=dot(d1,d1); e=dot(d2,d2); f=dot(d2,r)
    if a<1e-9 and e<1e-9: return vlen(sub(p1,p2))
    if a<1e-9: s=0.0; t=max(0,min(1,f/e))
    else:
        c=dot(d1,r)
        if e<1e-9: t=0.0; s=max(0,min(1,-c/a))
        else:
            b=dot(d1,d2); den=a*e-b*b
            s=max(0,min(1,(b*f-c*e)/den)) if den>1e-9 else 0.0
            t=(b*s+f)/e
            if t<0: t=0.0; s=max(0,min(1,-c/a))
            elif t>1: t=1.0; s=max(0,min(1,(b-c)/a))
    return vlen(sub(add(p1,mulv(d1,s)),add(p2,mulv(d2,t))))
def weapon_segs(kind, P, rr, D):
    O=saber_origin(P, rr)
    if kind=="staff":
        return {"b1":(add(O,mulv(D,19)),add(O,mulv(D,119))),"b2":(add(O,mulv(D,-37)),add(O,mulv(D,-137))),"hilt":(add(O,mulv(D,-37)),add(O,mulv(D,19)))}
    return {"b1":(add(O,mulv(D,19)),add(O,mulv(D,119))),"hilt":(add(O,mulv(D,-9)),add(O,mulv(D,19)))}
def analyze(c, verbose=True):
    kind=c.extra.get("weapon","saber")
    prev={}; rows=[]
    for i in range(c.T+1):
        p=c.pose(float(i)); J=joints(p,c.Q); th=p["th"]
        S=J["ua_r"]; psi=p["yaw"]+3*p["syaw"]+th
        P,rD,rr,A,_=right_target(p,S,c.Q)
        segs={("R"+k):v for k,v in weapon_segs(kind,P,rr,rD).items()}
        info={"i":i}
        if p.get("lD") is not None or p.get("lR") is not None:
            SL=J["ua_l"]
            Pl,lrot,_=left_target(p,SL,P,rD,rr,c.Q)
            info["lreach"]=vlen(sub(Pl,SL))
            if p.get("lD") is not None:
                lD=nrm(Rz(p["lD"], th+p["lDt"]*(psi-th)))
                info["LDA"]=math.degrees(math.acos(max(-1,min(1,dot(lD,nrm(sub(Pl,SL)))))))
                segs.update({("L"+k):v for k,v in weapon_segs("saber",Pl,lrot,lD).items()})
        # body proxies
        tor=(J["body"],J["neck"]); head=add(J["head"],(3,0,3))
        legs=[(J["thigh_l"],J["ank_l"]),(J["thigh_r"],J["ank_r"])]
        clr_t=clr_h=clr_l=999; zmin=999; sp={}
        for k,(a,b) in segs.items():
            if k.endswith("hilt"): continue
            clr_t=min(clr_t, seg_dist(a,b,tor[0],tor[1])-17.0)
            clr_h=min(clr_h, seg_dist(a,b,head,head)-12.0)
            for L in legs: clr_l=min(clr_l, seg_dist(a,b,L[0],L[1])-9.0)
            zmin=min(zmin,a[2],b[2])
            tip=b
            if k in prev: sp[k]=vlen(sub(tip,prev[k]))*30.0
            prev[k]=tip
        info.update({"P":P,"tips":{k:v[1] for k,v in segs.items() if not k.endswith("hilt")},"sp":sp,"clr_t":clr_t,"clr_h":clr_h,"clr_l":clr_l,"zmin":zmin,
                     "DA":math.degrees(math.acos(max(-1,min(1,dot(rD,A))))),"reach":vlen(sub(P,S)),"th":th})
        rows.append(info)
    return rows
def contacts(rows, vmin=900.0, xmin=35.0):
    """frames where a blade tip moves fast and is in front of the character (actor space x>xmin, within 60deg of forward)"""
    fr=[]
    for r in rows:
        hit=[]
        for k,s in r["sp"].items():
            tip=r["tips"][k]
            if s>=vmin and tip[0]>xmin and abs(math.degrees(math.atan2(tip[1],tip[0])))<65: hit.append(k)
        if hit: fr.append((r["i"],hit))
    return fr
if __name__=="__main__":
    key=sys.argv[1]
    c=ALL[key]()
    rows=analyze(c)
    for r in rows:
        tips=" ".join("%s(%4.0f,%4.0f,%4.0f)"%((k,)+tuple(v)) for k,v in r["tips"].items())
        sps=" ".join("%s=%4.0f"%(k,v) for k,v in r["sp"].items())
        flag=("T!" if r["clr_t"]<3 else "  ")+("H!" if r["clr_h"]<3 else "  ")+("L!" if r["clr_l"]<2 else "  ")+("F!" if r["zmin"]<3 else "  ")+("A!" if r["DA"]<18 or r["DA"]>155 else "  ")+("a!" if r.get("LDA",90)<18 or r.get("LDA",90)>155 else "  ")+("R!" if r["reach"]>REACH+0.1 else "  ")
        print("%2d th=%5.0f clr t%4.0f h%4.0f l%4.0f z%4.0f DA%4.0f LDA%4.0f rch%3.0f lr%3.0f %s || P(%4.0f,%4.0f,%4.0f) %s | %s"%(r["i"],r["th"],r["clr_t"],r["clr_h"],r["clr_l"],r["zmin"],r["DA"],r.get("LDA",-1),r["reach"],r.get("lreach",-1),flag,r["P"][0],r["P"][1],r["P"][2],tips,sps))
    print("CONTACTS", contacts(rows))
