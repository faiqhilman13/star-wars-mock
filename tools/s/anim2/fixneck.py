def run():
    e=geteul("neck_02_ctrl",BASEF); l=tup(e["location"]); r=tup(e["rotation"])
    for f in range(1500,1520):
        setl("neck_02_ctrl", f, l, r)
    return {"base":[l,r], "k1500":geteul("neck_02_ctrl",1500), "k800":geteul("neck_02_ctrl",800)}
