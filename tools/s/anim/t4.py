def run():
    P=(30,15,115); A=nrm(sub(P,SHOULDER_R))
    return {"want":hand_rot((0.3,0,0.95),A), "got":getw("hand_r_ik_ctrl",250), "BA":BA}
