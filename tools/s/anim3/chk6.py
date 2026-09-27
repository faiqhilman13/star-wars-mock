def run():
    out={}
    X(SQ+"set_playhead_frame", frame=2000); X(SQ+"force_evaluate")
    out["ph"]=X(SQ+"get_playhead_frame")
    out["neck01_2000"]=geteul("neck_01_ctrl",2000)["rotation"]
    X(SQ+"set_playhead_frame", frame=1000); X(SQ+"force_evaluate")
    out["ph2"]=X(SQ+"get_playhead_frame")
    out["neck01_1000"]=geteul("neck_01_ctrl",1000)["rotation"]
    X(SQ+"set_view_range", sequence=ref(LS), start_time=0, end_time=200) if False else None
    return out
