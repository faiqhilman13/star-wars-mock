def run():
    out={}
    for f in ["index","middle","ring","pinky","thumb"]:
        for i in ["01","02","03"]:
            c=f+"_"+i+"_r_ctrl"
            try: out[c]=geteul(c,250)["rotation"]
            except Exception as e: out[c]=str(e)[:80]
    X(CR+"set_anim_mode_hide_manips", hide=True)
    return out
