CRT="animation_toolset.toolsets.controlrig.ControlRigTools."
def run():
    out={}
    cr=ref(RIG+".CR_Mannequin_Body")
    for tp,n in [("Bone","hand_r"),("Bone","hand_l"),("Control","hand_r_ik_ctrl"),("Control","hand_l_ik_ctrl"),("Bone","lowerarm_r"),("Bone","lowerarm_l"),("Bone","upperarm_r"),("Bone","upperarm_l")]:
        out[n]=X(CRT+"get_global_transform", control_rig=cr, item={"type":tp,"name":n}, initial=True)
    return out
