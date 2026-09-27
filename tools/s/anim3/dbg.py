import sys
sys.argv=["x","s_c1","clips_staff.py"]
exec(open("plan2.py").read().split('if __name__=="__main__":')[0])
c=ALL["s_c1"]()
for i in [0,8,12,15]:
    p=c.pose(float(i)); J=joints(p,c.Q)
    print(i, "S",[round(x) for x in J["ua_r"]], "SL",[round(x) for x in J["ua_l"]], "neck",[round(x) for x in J["neck"]], "head",[round(x) for x in J["head"]], "body",[round(x) for x in J["body"]], "yaw",round(p["yaw"]), "syaw", round(p["syaw"]))
