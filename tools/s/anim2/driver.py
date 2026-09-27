import json, subprocess, sys, time, os
D="C:/Users/User/PROJECTS/jedi-arena/tools"
UPY="C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
A=D+"/s/anim2/"
TS={"idle":60,"run":20,"c1":18,"c2":16,"c3":18,"c4":17,"c5":28,"block":30}
def pie():
    r=subprocess.run([UPY,D+"/ue.py","t","app.IsPIERunning","{}"],capture_output=True,text=True,cwd=D)
    return "true" in r.stdout
def wait_pie():
    t0=time.time()
    while pie():
        time.sleep(10)
    if time.time()-t0>1: print("  waited PIE %.0fs"%(time.time()-t0), flush=True)
def run_script(parts):
    src="".join(open(A+p,encoding="utf-8").read()+"\n" for p in parts)
    open(A+"_r.py","w",encoding="utf-8").write(src)
    r=subprocess.run([UPY,D+"/ue.py","script",A+"_r.py"],capture_output=True,text=True,cwd=D,timeout=620)
    return r.stdout+r.stderr
for name in sys.argv[1:]:
    lo,hi=(int(x) for x in os.environ.get("FR_"+name,"0,%d"%TS[name]).split(","))
    rem=list(range(lo,hi+1)); first=True; tries=0
    while rem:
        wait_pie()
        chunk=rem[:12]
        open(A+"_names.py","w").write("NAME=%r\nFRAMES=%r\nFIRST=%r\nPARTS=%r\n"%(name,chunk,first,os.environ.get("PARTS","bfa")))
        t0=time.time()
        out=run_script(["lib2.py","eng.py","clips.py","_names.py","bk.py"])
        try:
            j=json.loads(out[out.index("{"):out.rindex("}")+1])
        except Exception:
            print("  bad output:", out[-800:], flush=True); tries+=1
            if tries>5: sys.exit(1)
            time.sleep(15); continue
        done=j.get("done",[])
        if first and (done or not j.get("err")): first=False
        rem=[f for f in rem if f not in done]
        print("%s: done %s in %.0fs err=%s"%(name, done, time.time()-t0, j.get("err")), flush=True)
        if j.get("err") and "PIE" not in j["err"]:
            tries+=1
            if tries>5: print("giving up"); sys.exit(1)
    print("CLIP_OK", name, flush=True)
