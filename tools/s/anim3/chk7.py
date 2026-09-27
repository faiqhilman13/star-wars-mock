def run():
    out={}
    X(SQ+"set_section_range", section=ref(SEC), start_frame=0, end_frame=6000)
    out["r"]=X(SQ+"get_section_range", section=ref(SEC))
    show(2000)
    out["neck01_2000"]=geteul("neck_01_ctrl",2000)["rotation"]
    out["body_2000"]=geteul("body_ctrl",2000)
    return out
