def run():
    out={}
    out["add"]=X(SQ+"add_actors", actors=[ref(ACTOR)])
    b=X(SQ+"get_bindings", sequence=ref(LS))
    out["b"]=b
    out["kids"]=X(SQ+"get_child_possessables", binding=b[0])
    return out
