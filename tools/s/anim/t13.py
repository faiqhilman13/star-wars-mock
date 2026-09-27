def run():
    out={}
    show(305); out["ph"]=X(SQ+"get_playhead_frame")
    out["h"]=wpos("hand_r_ik_ctrl",305)
    out["hfk"]=wpos("hand_r_fk_ctrl",305)
    out["lower"]=wpos("lowerarm_r_fk_ctrl",305)
    return out
