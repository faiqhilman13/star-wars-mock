def run():
    for f,base in [("index",-65),("middle",-72),("ring",-78),("pinky",-82)]:
        cur=geteul(f+"_01_l_ctrl",227)["rotation"]
        setl(f+"_01_l_ctrl",250,(0,0,0),(cur["pitch"],base,cur["roll"]))
        setl(f+"_02_l_ctrl",250,(0,0,0),(0,-85,0))
        setl(f+"_03_l_ctrl",250,(0,0,0),(0,-55,0))
    return {"r":geteul("index_01_l_ctrl",227)}
