def run():
    c=ALL[NAME]()
    if FIRST:
        guard()
        curl = (NAME=="block")
        if NAME!="c4":
            for f in (c.S, c.S+c.T): fingers("l", f, curl)
        else:
            fingers("l", c.S, False); fingers("l", c.S+3, True); fingers("l", c.S+13, True); fingers("l", c.S+c.T, False)
        fingers("r", c.S, True); fingers("r", c.S+c.T, True)
    return bake(c, frames=FRAMES, parts=PARTS)
