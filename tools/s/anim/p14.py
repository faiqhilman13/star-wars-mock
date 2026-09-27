def run():
    ch=X(KF+"get_channel_names", section=ref(SEC))
    out={"n":len(ch),"body":[c for c in ch if "body_ctrl" in c or "arm_r_fk_ik" in c]}
    k=json.loads(X(KF+"get_keys", section=ref(SEC), channel_name=out["body"][0]))
    out["nk"]=len(k); out["last"]=k[-1] if k else None; out["first"]=k[0] if k else None
    return out
