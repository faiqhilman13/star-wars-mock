# offline planner: python plan.py <clipkey> [verbose]
import json, math, sys, os
H=os.path.dirname(os.path.abspath(__file__))
def ref(p): return {"refPath":p}
def execute_tool(n,a): raise RuntimeError("no editor")
def T(*a,**k): return False
src=open(os.path.join(H,"lib3.py")).read()+open(os.path.join(H,"eng3.py")).read()+open(os.path.join(H,"clips3.py")).read()
for extra in sys.argv[3:]:
    src+=open(os.path.join(H,extra)).read()
exec(src)
CAL=CAL_OFF
# idle reference points (char)
IDLE={"body":(-0.69,-1.49,99.83),"thigh_l":(3.23,-11.97,90.78),"thigh_r":(-5.35,8.62,90.35),
      "ua_r":(-4.76,16.99,142.19),"ua_l":(9.14,-18.52,141.83),"neck":(4.24,0.07,150.66),"head":(8.21,1.67,159.72)}
def body_rows(p):
    br=CAL_OFF["L_body_ctrl"][1]
    m=Mr(br[0]+p["lean"], p["yaw"]+p["th"], br[2]+p["bend"])
    return [bl_to_c(r) for r in m]
def torso_rows(p):
    br=CAL_OFF["L_body_ctrl"][1]
    m=Mr(br[0]+p["lean"]+2.5*p["slean"], p["yaw"]+p["th"]+3*p["syaw"], br[2]+p["bend"]+2.7*p["sbend"])
    return [bl_to_c(r) for r in m]
R0=None
def local_of(pt, rows0, origin):
    d=sub(pt,origin); return tuple(dot(d,r) for r in rows0)
def world_of(loc, rows, origin):
    return add(origin, add(add(mulv(rows[0],loc[0]),mulv(rows[1],loc[1])),mulv(rows[2],loc[2])))
p0=dict(DEF); p0.update({"lean":0.0,"yaw":22.492,"bend":0.0,"th":0.0,"slean":0.0,"syaw":0.0,"sbend":0.0})
RB0=body_rows(p0)
LOC={k:local_of(v,RB0,IDLE["body"]) for k,v in IDLE.items()}
def bodypos(p, Q):
    pw=CAL_OFF["W_body_ctrl"][0]
    return spinp(add(pw,(p["dfwd"],p["dside"],p["dz"])), p["th"], Q)
def joints(p, Q=(0,0,0)):
    b=bodypos(p,Q); rb=body_rows(p); rt=torso_rows(p)
    out={"body":b}
    for k in ["thigh_l","thigh_r"]: out[k]=world_of(LOC[k],rb,b)
    for k in ["ua_r","ua_l","neck","head"]: out[k]=world_of(LOC[k],rt,b)
    return out
THIGH=45.8; SHIN=41.7
def knee_flex(d):
    c=(THIGH**2+SHIN**2-d*d)/(2*THIGH*SHIN); c=max(-1,min(1,c))
    return 180.0-math.degrees(math.acos(c))
if __name__=="__main__":
    key=sys.argv[1]
    c=ALL[key]()
    rows=[]
    prevtip=None; prevl=None
    for i in range(c.T+1):
        p=c.pose(float(i)); J=joints(p,c.Q)
        line="%2d"%i
        for s in "lr":
            if p.get(s+"A") is not None:
                A=p[s+"A"]; hip=J["thigh_"+s]; d=vlen(sub(A,hip))
                line+=" %s:A(%5.1f,%5.1f,%5.1f) d=%5.1f%s kf=%3.0f fp=%4.0f"%(s,A[0],A[1],A[2],d,"!" if d>87.3 else " ",knee_flex(min(d,87.5)),p[s+"fp"])
        tor=sub(J["neck"],J["body"]); line+=" torso=%4.1f"%math.degrees(math.atan2(tor[0],tor[2]))
        S=J["ua_r"]
        psi=p["yaw"]+3*p["syaw"]+p["th"]
        if p.get("rR") is not None: rP=add(S,Rz(p["rR"],psi))
        else: rP=spinp(p["rP"],p["th"],c.Q)
        rD=nrm(Rz(p["rD"], p["th"]+p["rDt"]*(psi-p["th"])))
        P=clampP(rP,S,REACH)
        tip=add(P,mulv(rD,119)); sp=0 if prevtip is None else vlen(sub(tip,prevtip))*30; prevtip=tip
        line+=" P(%4.0f,%4.0f,%4.0f) tip(%4.0f,%4.0f,%4.0f) sp=%4.0f"%(P+tip+(sp,))
        if p.get("lR") is not None:
            SL=J["ua_l"]; lP=add(SL,Rz(p["lR"],psi))
            line+=" lH(%4.0f,%4.0f,%4.0f)"%lP
        if p.get("lD") is not None:
            SL=J["ua_l"]
            lP=add(SL,Rz(p["lRs"],psi)) if p.get("lRs") is not None else spinp(p["lP"],p["th"],c.Q)
            lD=nrm(Rz(p["lD"], p["th"]+p["lDt"]*(psi-p["th"])))
            lP=clampP(lP,SL,REACH); ltip=add(lP,mulv(lD,119))
            lsp=0 if prevl is None else vlen(sub(ltip,prevl))*30; prevl=ltip
            line+=" L(%4.0f,%4.0f,%4.0f) ltip(%4.0f,%4.0f,%4.0f) lsp=%4.0f"%(lP+ltip+(lsp,))
        print(line)
