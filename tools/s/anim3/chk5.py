def run():
    out={}
    for c in ["body_ctrl.Location.X","neck_01_ctrl.Rotation.X","clavicle_r_ctrl.Rotation.Z","neck_02_ctrl.Rotation.X","index_01_r_ctrl.Rotation.Z"]:
        try:
            k=json.loads(X(KF+"get_keys", section=ref(SEC), channel_name=c))
            out[c]=[len(k), k[-3:]]
        except Exception as e: out[c]=str(e)[:150]
    for f in [1000,1099,1100,2000]:
        out["neck01_%d"%f]=geteul("neck_01_ctrl",f)["rotation"]
        out["clav_%d"%f]=geteul("clavicle_r_ctrl",f)["rotation"]
    return out
