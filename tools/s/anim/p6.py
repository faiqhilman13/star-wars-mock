def run():
    out={}
    X(SQ+"set_display_rate", sequence=ref(LS), numerator=30, denominator=1)
    X(SQ+"set_playback_range", sequence=ref(LS), start_frame=0, end_frame=300)
    out["secs"]=X(SQ+"get_sections", track=ref(TRK))
    out["rate"]=X(SQ+"get_display_rate", sequence=ref(LS))
    out["tick"]=X(SQ+"get_tick_resolution", sequence=ref(LS))
    return out
