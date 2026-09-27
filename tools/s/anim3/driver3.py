import json, subprocess, sys, time, os
D="C:/Users/User/PROJECTS/jedi-arena/tools"
UPY="C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
A=D+"/s/anim3/"
EXTRA=os.environ.get("EXTRA","").split()
def pie():
    r=subprocess.run([UPY,D+"/ue.py","t","app.IsPIERunning","{}"],capture_output=True,text=True,cwd=D)
    return "true" in r.stdout
def wait_pie():
    t0=time.time()
    while pie():
        time.sleep(10)
    if time.time()-t0>1: print("  waited PIE %.0fs"%(time.time()-t0), flush=True)
def run_script(parts, tag):
    src="".join(open(A+p,encoding="utf-8").read()+"\n" for p in parts)
    fn=A+"_r_%s.py"%tag
    open(fn,"w",encoding="utf-8").write(src)
    r=subprocess.run([UPY,D+"/ue.py","script",fn],capture_output=True,text=True,cwd=D,timeout=620)
    return r.stdout+r.stderr
CHUNK=int(os.environ.get("CHUNK","12"))
for name in sys.argv[1:]:
    T=int(os.environ.get("T_"+name,"0"))
    rng=os.environ.get("FR_"+name)
    if rng: lo,hi=(int(x) for x in rng.split(","))
    else:
        ns={"ref":(lambda p:{"refPath":p}),"execute_tool":None,"T":(lambda *a,**k:False),"json":json}
        exec("".join(open(A+p,encoding="utf-8").read()+chr(10) for p in ["lib3.py","eng3.py","clips3.py"]+EXTRA), ns)
        ns["CAL"]=ns["CAL_OFF"]
        lo,hi=0,ns["ALL"][name]().T
    rem=list(range(lo,hi+1)); first=os.environ.get("NOFIRST") is None; tries=0
    while rem:
        wait_pie()
        chunk=rem[:CHUNK]
        open(A+"_names_%s.py"%name,"w").write("NAME=%r\nFRAMES=%r\nFIRST=%r\nPARTS=%r\n"%(name,chunk,first,os.environ.get("PARTS","bfa")))
        t0=time.time()
        try:
            out=run_script(["lib3.py","eng3.py","clips3.py"]+EXTRA+["_names_%s.py"%name,"bk3.py"], name)
        except subprocess.TimeoutExpired:
            print("  timeout", flush=True); tries+=1; time.sleep(20); continue
        try:
            j=json.loads(out[out.index("{"):out.rindex("}")+1])
        except Exception:
            print("  bad output:", out[-800:], flush=True); tries+=1
            if tries>6: sys.exit(1)
            time.sleep(15); continue
        done=j.get("done",[])
        if first and (done or not j.get("err")): first=False
        rem=[f for f in rem if f not in done]
        print("%s: done %s in %.0fs err=%s"%(name, done, time.time()-t0, j.get("err")), flush=True)
        if j.get("err") and "PIE" not in j["err"]:
            tries+=1
            if tries>6: print("giving up"); sys.exit(1)
    print("CLIP_OK", name, flush=True)
