import sys, math, json
sys.argv=["x","d_c1","clips_dual.py"]
exec(open("plan2.py").read().split('if __name__=="__main__":')[0])
bad=0
for key in ["d_idle","d_run","d_block","d_c1","d_c2","d_c3","d_c4"]:
    c=ALL[key]()
    for i in range(c.T+1):
        p=c.pose(float(i)); J=joints(p,c.Q)
        P,rD,rr,A,_=right_target(p,J["ua_r"],c.Q)
        Pl,lrot,lpv=left_target(p,J["ua_l"],P,rD,rr,c.Q)
        vals=list(P)+list(rr)+list(Pl)+list(lrot)+list(lpv)
        if any(v!=v for v in vals): bad+=1; print(key,i,"NaN",rr,lrot)
print("bad",bad)
c=ALL["d_c1"](); p=c.pose(0.0)
print({k:p[k] for k in ["lD","lP","lRs","lR","lg","ltw","lDt"] if k in p})
