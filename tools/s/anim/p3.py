def run():
    out={}
    out["open"]=X(SQ+"open_sequence", sequence=ref(LS))
    out["cur"]=X(SQ+"get_current_sequence")
    out["b0"]=X(SQ+"get_bindings", sequence=ref(LS))
    return out
