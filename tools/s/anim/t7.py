def run():
    for f,base in [("index",-65),("middle",-72),("ring",-78),("pinky",-82)]:
        cur=geteul(f+"_01_r_ctrl",250)["rotation"]
        setl(f+"_01_r_ctrl",250,(0,0,0),(cur["pitch"],base,cur["roll"]))
        setl(f+"_02_r_ctrl",250,(0,0,0),(0,-85,0))
        setl(f+"_03_r_ctrl",250,(0,0,0),(0,-55,0))
    show(250)
    return {}
