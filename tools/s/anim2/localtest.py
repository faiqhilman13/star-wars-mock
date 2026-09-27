import json, math, sys
def ref(p): return {"refPath":p}
def execute_tool(n,a): raise RuntimeError("no editor")
def T(*a,**k): return False
src=open("lib2.py").read()+open("eng.py").read()+open("clips.py").read()
exec(src)
CAL={"L_body_ctrl":((1.491,-3.499,-3.75),(-2.46,22.492,4.338)),
     "L_spine_01_ctrl":((0,0.426,1.757),(1.034,0.013,4.723)),"L_spine_02_ctrl":((0,-0.046,-0.385),(0.683,-0.025,1.276)),
     "L_spine_03_ctrl":((0,0.02,-0.327),(0.68,-0.054,3.411)),"L_head_ctrl":((0.021,-0.303,-0.789),(2.579,-15.149,7.168)),
     "W_body_ctrl":((-0.69,-1.49,99.83),(-2.46,112.49,4.34)),"W_foot_l_ik_ctrl":((11.03,-20.55,8.48),(-2.05,101.58,1.94)),
     "W_foot_r_ik_ctrl":((-19.86,10.36,8.14),(-1.06,129.82,2.05)),"W_leg_l_pv_ik_ctrl":((57.98,-14.64,57.96),(0,0,0)),"W_leg_r_pv_ik_ctrl":((29.41,37.19,45.0),(0,0,0))}
name=sys.argv[1]
c=ALL[name]()
for i in range(c.T+1):
    p=c.pose(float(i)); th=p["th"]
    P=spinp(p["rP"],th,c.Q); D=nrm(Rz(p["rD"],th)); tip=add(P,mulv(D,100))
    az=math.degrees(math.atan2(D[1],D[0]))
    print(i, "th=%.0f yaw=%.0f dz=%.1f"%(th,p["yaw"],p["dz"]), "P",[round(x) for x in P],"tip",[round(x) for x in tip],"az=%.0f"%az, "lf",[round(x,1) for x in p["lf"]], "rf",[round(x,1) for x in p["rf"]], "lg=%.2f"%p["lg"])
prev=None
sp=[]
for i in range(c.T+1):
    p=c.pose(float(i)); th=p["th"]
    P=spinp(p["rP"],th,c.Q); D=nrm(Rz(p["rD"],th)); tip=add(P,mulv(D,100))
    if prev: sp.append((i,int(vlen(sub(tip,prev))*30)))
    prev=tip
print("SPEEDS",sp)
